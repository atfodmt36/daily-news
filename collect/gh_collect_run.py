#!/usr/bin/env python3
"""AI Radar Claude Code collect — GitHub Actions driver (TRIAL).

Ported 2026-11-11 from ~/workspace/ai-radar/claude_collect_run.py, which
drives Claude Code on the owner's home PC over SSH. This version is
self-contained in the daily-news repo and runs `claude` LOCALLY (the
GitHub Actions runner). Everything else mirrors the original:

- Prompt rendered from prompts/common.md + collect-sources.md +
  prompts/task.md (placeholders FROM/TO/DATE/GENERATED_AT; window =
  previous day 08:00 JST -> today 08:00 JST).
- Claude returns one JSON object {date, generatedAt, checked[15],
  items[]}; it is validated by claude_collect_validate.py (same file).
- On validation errors: ONE fix attempt (prompts/fix.md + error list +
  previous JSON). Item-level errors that survive are salvaged by
  dropping the bad items; file-level errors fail the run.

Outputs (under <repo root>/claude-collect/):
  YYYY-MM-DD.json           envelope for the digest (same shape as the PC run)
  YYYY-MM-DD.coverage.json  checked[] + warnings of the accepted run
  YYYY-MM-DD.raw.txt/.raw2.txt, .prompt.md, .log, .ok (success marker)

With --commit, on success the envelope is ALSO merged (by url) into
inputs_muse/<window-end YYYYMMDD>/claude-code.json in the working tree,
with collected_at stamped on new items — the same write the Muse cron
performs after the PC run. The workflow's commit step does the git part.
Without --commit nothing outside claude-collect/ is touched.

Exit codes (same as the original): 0 ok (incl. already-collected skip
and salvaged runs), 3 = Claude Code auth failure, 4 = no parseable JSON,
5 = transport failure (claude missing / subprocess failure),
6 = validation failed after the fix attempt.
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parent))
from claude_collect_validate import validate  # noqa: E402

JST = ZoneInfo("Asia/Tokyo")
COLLECT_DIR = Path(__file__).resolve().parent
REPO_ROOT = COLLECT_DIR.parent
OUTDIR = REPO_ROOT / "claude-collect"
PROMPTS = COLLECT_DIR / "prompts"
SOURCES = COLLECT_DIR / "collect-sources.md"
MODEL = os.environ.get("COLLECT_MODEL", "opus")
EFFORT = os.environ.get("COLLECT_EFFORT", "high")
TIMEOUT_MAIN = int(os.environ.get("COLLECT_TIMEOUT_MAIN", "1800"))
TIMEOUT_FIX = int(os.environ.get("COLLECT_TIMEOUT_FIX", "1200"))
AUTH_MARKERS = ("not logged in", "401", "unauthorized", "invalid api key", "/login")


def render(parts, subs):
    text = ""
    for p in parts:
        text += Path(p).read_text(encoding="utf-8") + "\n\n"
    for k, v in subs.items():
        text = text.replace("{{" + k + "}}", v)
    return text


def run_claude(prompt, timeout, log):
    cmd = [
        "claude", "-p", "--model", MODEL, "--effort", EFFORT,
        "--allowedTools", "WebSearch WebFetch",
        "--output-format", "text",
    ]
    try:
        r = subprocess.run(cmd, input=prompt.encode("utf-8"),
                           capture_output=True, timeout=timeout)
        raw = r.stdout.decode("utf-8", errors="replace")
        err = r.stderr.decode("utf-8", errors="replace")
        log(f"claude exit={r.returncode} raw_bytes={len(r.stdout)}")
        if err.strip():
            log("stderr: " + err.strip()[:2000])
        return raw, err, r.returncode
    except subprocess.TimeoutExpired as e:
        raw = (e.stdout or b"").decode("utf-8", errors="replace")
        err = (e.stderr or b"").decode("utf-8", errors="replace")
        log(f"claude TIMEOUT after {timeout}s (partial raw {len(raw)} chars)")
        return raw, err, 124
    except OSError as e:
        log(f"claude subprocess failed to start: {e}")
        return "", str(e), 127


def extract_json(raw):
    """First JSON object in the text that looks like a collection result."""
    import json as _json
    dec = _json.JSONDecoder()
    for i, ch in enumerate(raw):
        if ch != "{":
            continue
        try:
            obj, _ = dec.raw_decode(raw[i:])
        except ValueError:
            continue
        if isinstance(obj, dict) and ("items" in obj or "checked" in obj):
            return obj
    return None


def has_auth_marker(text):
    low = text.lower()
    return any(m in low for m in AUTH_MARKERS)


def write_inputs_envelope(envelope, run_at):
    """Merge the envelope into inputs_muse/<window-end date>/claude-code.json.

    Mirrors what the Muse cron does with the PC run's envelope: items
    are merged by url (existing items win, keeping their collected_at),
    new items are stamped with collected_at = run time, itemCount is
    refreshed. Returns (repo-relative path, number of items added).
    """
    win_to = datetime.fromisoformat(envelope["window"]["to"])
    folder = REPO_ROOT / "inputs_muse" / win_to.strftime("%Y%m%d")
    target = folder / "claude-code.json"
    stamp = run_at.isoformat(timespec="seconds")
    new_items = []
    for it in envelope["items"]:
        it = dict(it)
        it.setdefault("collected_at", stamp)
        new_items.append(it)
    if target.exists():
        out = json.loads(target.read_text(encoding="utf-8"))
        merged = list(out.get("items", []))
        seen = {it.get("url") for it in merged if isinstance(it, dict)}
        added = 0
        for it in new_items:
            if it.get("url") not in seen:
                merged.append(it)
                seen.add(it.get("url"))
                added += 1
        out["items"] = merged
        out["itemCount"] = len(merged)
    else:
        out = dict(envelope)
        out["items"] = new_items
        out["itemCount"] = len(new_items)
        added = len(new_items)
    folder.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(out, ensure_ascii=False, indent=2),
                      encoding="utf-8")
    return target.relative_to(REPO_ROOT).as_posix(), added


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--from", dest="win_from", help="window start ISO (default: yesterday 08:00 JST)")
    ap.add_argument("--to", dest="win_to", help="window end ISO (default: today 08:00 JST)")
    ap.add_argument("--force", action="store_true", help="re-collect even if a valid run exists")
    ap.add_argument("--commit", action="store_true",
                    help="on success, also merge the envelope into inputs_muse/<window-end date>/claude-code.json")
    ap.add_argument("--render-only", action="store_true",
                    help="render the prompt, write it to claude-collect/<date>.prompt.md, and exit without calling claude")
    args = ap.parse_args()

    now = datetime.now(JST)
    if args.win_to:
        win_to = datetime.fromisoformat(args.win_to)
    else:
        # Window basis is 08:00 JST, same as the PC pipeline: the run
        # covers the full, already-closed 08:00 -> 08:00 window.
        win_to = now.replace(hour=8, minute=0, second=0, microsecond=0)
    if args.win_from:
        win_from = datetime.fromisoformat(args.win_from)
    else:
        win_from = win_to - timedelta(days=1)
    date_str = win_to.date().isoformat()

    OUTDIR.mkdir(parents=True, exist_ok=True)
    out_json = OUTDIR / f"{date_str}.json"
    coverage_json = OUTDIR / f"{date_str}.coverage.json"
    ok_marker = OUTDIR / f"{date_str}.ok"
    log_path = OUTDIR / f"{date_str}.log"

    def log(msg):
        line = f"[{datetime.now(JST).strftime('%F %T')}] {msg}"
        print(line, file=sys.stderr)
        with log_path.open("a", encoding="utf-8") as f:
            f.write(line + "\n")

    log(f"collect start window {win_from.isoformat()} -> {win_to.isoformat()} model={MODEL}")

    if ok_marker.exists() and not args.force:
        log("already collected successfully for this date (skip; --force to redo)")
        print(json.dumps({"status": "skipped", "date": date_str}))
        return 0

    subs = {
        "FROM": win_from.isoformat(),
        "TO": win_to.isoformat(),
        "DATE": date_str,
        "GENERATED_AT": now.isoformat(timespec="seconds"),
    }
    prompt = render([PROMPTS / "common.md", SOURCES, PROMPTS / "task.md"], subs)
    (OUTDIR / f"{date_str}.prompt.md").write_text(prompt, encoding="utf-8")

    if args.render_only:
        log(f"render-only: prompt written ({len(prompt)} chars); claude not called")
        print(json.dumps({"status": "rendered", "date": date_str,
                          "window": {"from": win_from.isoformat(),
                                     "to": win_to.isoformat()},
                          "prompt_chars": len(prompt)}, ensure_ascii=False))
        return 0

    if shutil.which("claude") is None:
        log("result: transport_failed (claude CLI not found on PATH)")
        return 5

    raw, err, rc = run_claude(prompt, TIMEOUT_MAIN, log)
    (OUTDIR / f"{date_str}.raw.txt").write_text(raw, encoding="utf-8")
    if rc != 0 and not raw.strip():
        if has_auth_marker(err + raw):
            log("result: auth_failed (transport)")
            return 3
        log("result: transport_failed")
        return 5

    data = extract_json(raw)
    if data is None:
        if has_auth_marker(raw + err):
            log("result: auth_failed (no JSON, auth markers)")
            return 3
        log("result: no_json")
        return 4

    result = validate(data, win_from, win_to)
    fixed = False
    salvaged = 0
    if result["errors"]:
        errs_text = "\n".join(f"- {msg}" for _scope, msg in result["errors"])
        log(f"validation failed ({len(result['errors'])} errors); running ONE fix attempt")
        for _scope, msg in result["errors"]:
            log("error: " + msg)
        fix_subs = dict(subs)
        fix_subs["ERRORS"] = errs_text
        fix_subs["PREV_JSON"] = json.dumps(data, ensure_ascii=False, indent=2)[:60000]
        fix_prompt = render([PROMPTS / "common.md", PROMPTS / "fix.md"], fix_subs)
        raw2, err2, rc2 = run_claude(fix_prompt, TIMEOUT_FIX, log)
        (OUTDIR / f"{date_str}.raw2.txt").write_text(raw2, encoding="utf-8")
        data2 = extract_json(raw2) if raw2.strip() else None
        if data2 is not None:
            result2 = validate(data2, win_from, win_to)
            if len(result2["errors"]) <= len(result["errors"]):
                data, result, fixed = data2, result2, True
                log(f"fix attempt result: {len(result['errors'])} errors remain")
            else:
                log("fix attempt made things worse; keeping first result")
        else:
            log("fix attempt returned no JSON; keeping first result")

    if result["errors"]:
        item_idx = {scope[1] for scope, _ in result["errors"] if scope[0] == "item"}
        file_errs = [msg for scope, msg in result["errors"] if scope[0] != "item"]
        if item_idx and not file_errs:
            # salvage: drop the offending items and re-validate
            data = dict(data)
            data["items"] = [it for i, it in enumerate(data.get("items", []))
                             if i not in item_idx]
            result = validate(data, win_from, win_to)
            salvaged = len(item_idx)
            log(f"salvaged by dropping {salvaged} bad item(s); errors now {len(result['errors'])}")
        if result["errors"]:
            for _scope, msg in result["errors"]:
                log("error: " + msg)
            log("result: validation_failed")
            return 6

    for w in result["warnings"]:
        log("warning: " + w)

    envelope = {
        "date": win_to.strftime("%Y/%m/%d"),
        "timezone": "Asia/Tokyo",
        "window": {"from": win_from.isoformat(), "to": win_to.isoformat()},
        "source": "claude-code",
        "itemCount": len(result["items"]),
        "items": result["items"],
    }
    out_json.write_text(json.dumps(envelope, ensure_ascii=False, indent=2),
                        encoding="utf-8")
    coverage = {
        "date": date_str,
        "window": {"from": win_from.isoformat(), "to": win_to.isoformat()},
        "generatedAt": data.get("generatedAt"),
        "checked": result["checked"],
        "warnings": result["warnings"],
        "itemCount": len(result["items"]),
        "fixed": fixed,
        "salvaged": salvaged,
    }
    coverage_json.write_text(json.dumps(coverage, ensure_ascii=False, indent=2),
                             encoding="utf-8")
    ok_marker.write_text(
        f"{datetime.now(JST).isoformat(timespec='seconds')} kept={len(result['items'])}\n",
        encoding="utf-8")
    unconf = [c.get("key") for c in result["checked"]
              if isinstance(c, dict) and c.get("status") == "未確認"]
    log(f"result: ok kept={len(result['items'])} unconfirmed_targets={unconf}")
    summary = {
        "status": "ok", "kept": len(result["items"]),
        "unconfirmed_targets": unconf, "warnings": result["warnings"],
        "fixed": fixed, "salvaged": salvaged,
    }
    if args.commit:
        rel_path, added = write_inputs_envelope(envelope, datetime.now(JST))
        summary["inputs_path"] = rel_path
        summary["inputs_added"] = added
        log(f"inputs envelope merged: {rel_path} (+{added} items)")
    print(json.dumps(summary, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
