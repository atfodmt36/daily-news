#!/usr/bin/env python3
"""Validate Claude Code's collection output for the AI Radar collect run.

Mirrors the original daily-news-collector's `validate daily`:
- errors  = schema/rule violations (the run fails or goes to the fix loop)
- warnings = pass, but noted (unconfirmed targets, count mismatches)

Input is the parsed JSON object Claude returned:
  {date, generatedAt, checked: [{key, status, count, note, sources}],
   items: [{id, topic, headline, summary, url, source, published_at,
            unconfirmed, status?, tags?, related_urls?}]}

validate(data, win_from, win_to) -> {
  "errors":   [(scope, message)],  scope: ("file", None) | ("checked", key) | ("item", index)
  "warnings": [message],
  "items":    [normalized envelope items],
  "checked":  [checked entries as given],
}
"""
import re
from datetime import datetime, time as dtime
from urllib.parse import urlparse
from zoneinfo import ZoneInfo

JST = ZoneInfo("Asia/Tokyo")

# (key, topic label, required) — checked order = priority order
TARGETS = [
    ("microsoft-365-copilot", "Microsoft 365 Copilot", True),
    ("anthropic", "Claude", True),
    ("claude-code", "Claude Code", True),
    ("openai", "ChatGPT", True),
    ("codex", "Codex", True),
    ("jp-gov", "日本政府・行政", True),
    ("google", "Gemini", True),
    ("microsoft-foundry", "Microsoft Foundry", True),
    ("construction-ai", "建設×AI", True),
    ("3d-model-ai", "3Dモデル×AI", True),
    ("3dgs-ai", "3DGS×AI", True),
    ("jp-models", "国産モデル", True),
    ("ai-business", "AIビジネス", True),
    ("github-copilot", "GitHub Copilot", False),
    ("gemini-cli", "Gemini CLI", False),
]
KEY2TOPIC = {k: t for k, t, _ in TARGETS}
TOPICS = set(KEY2TOPIC.values()) | {"その他"}
STATUSES = {"ga", "preview", "beta", "announced", "deprecated", "policy", "other"}
CHECK_STATUSES = {"確認済み", "未確認"}
ID_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
MAX_ITEMS = 30


def parse_dt(s):
    if not isinstance(s, str) or not s:
        return None
    try:
        dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=JST)
    return dt


def is_https_url(s):
    if not isinstance(s, str) or not s.startswith("https://") or " " in s:
        return False
    try:
        return bool(urlparse(s).netloc)
    except ValueError:
        return False


def is_http_url(s):
    if not isinstance(s, str) or " " in s:
        return False
    if not (s.startswith("https://") or s.startswith("http://")):
        return False
    try:
        return bool(urlparse(s).netloc)
    except ValueError:
        return False


def validate(data, win_from, win_to):
    errors = []
    warnings = []
    items_out = []

    if not isinstance(data, dict):
        return {"errors": [(("file", None), "トップレベルが JSON オブジェクトではありません")],
                "warnings": [], "items": [], "checked": []}

    # ---- header
    want_date = win_to.date().isoformat()
    if data.get("date") != want_date:
        errors.append((("file", None),
                       f"date が {data.get('date')!r} です（{want_date} のはず）"))
    if parse_dt(data.get("generatedAt")) is None:
        errors.append((("file", None), "generatedAt が ISO 8601 の日時ではありません"))

    # ---- items (validate first; checked counts compare against these)
    raw_items = data.get("items")
    if not isinstance(raw_items, list):
        errors.append((("file", None), "items が配列ではありません"))
        raw_items = []
    if len(raw_items) > MAX_ITEMS:
        errors.append((("file", None),
                       f"items が {len(raw_items)} 件あります（上限 {MAX_ITEMS} 件）"))

    seen_ids = {}
    seen_urls = {}
    per_topic = {}
    for i, it in enumerate(raw_items):
        scope = ("item", i)
        if not isinstance(it, dict):
            errors.append((scope, f"items[{i}] がオブジェクトではありません"))
            continue
        ok = True
        iid = it.get("id")
        if not isinstance(iid, str) or not ID_RE.match(iid):
            errors.append((scope, f"items[{i}] の id が kebab-case ではありません: {iid!r}"))
            ok = False
        elif iid in seen_ids:
            errors.append((scope, f"id「{iid}」が重複しています（{seen_ids[iid]} 番目と同じ）"))
            ok = False
        else:
            seen_ids[iid] = i
        topic = it.get("topic")
        if topic not in TOPICS:
            errors.append((scope, f"items[{i}] の topic が対象外です: {topic!r}"))
            ok = False
        for field in ("headline", "summary", "source"):
            if not isinstance(it.get(field), str) or not it[field].strip():
                errors.append((scope, f"items[{i}] の {field} が空です"))
                ok = False
        url = it.get("url")
        if not is_https_url(url):
            errors.append((scope, f"items[{i}] の url が https の完全な URL ではありません: {url!r}"))
            ok = False
        elif url in seen_urls:
            warnings.append(
                f"items[{i}] の url が items[{seen_urls[url]}] と同一です（{url}）。"
                "同じページを指すアイテムは、別々の発表でも下流で重複に見えます")
        else:
            seen_urls[url] = i
        pub = parse_dt(it.get("published_at"))
        if pub is None:
            errors.append((scope, f"items[{i}] の published_at が日時として読めません: {it.get('published_at')!r}"))
            ok = False
        else:
            pub_jst = pub.astimezone(JST)
            in_window = win_from <= pub <= win_to
            date_only = (pub_jst.time() == dtime(0, 0)
                         and pub_jst.date() in (win_from.date(), win_to.date()))
            if not in_window and not date_only:
                errors.append((scope,
                               f"items[{i}] の published_at {it.get('published_at')} が"
                               f"期間（{win_from.isoformat()} 〜 {win_to.isoformat()}）の外です"))
                ok = False
        unc = it.get("unconfirmed", False)
        if not isinstance(unc, bool):
            errors.append((scope, f"items[{i}] の unconfirmed が真偽値ではありません"))
            ok = False
        st = it.get("status")
        if st is not None and st not in STATUSES:
            errors.append((scope, f"items[{i}] の status が不正です: {st!r}"))
            ok = False
        tags = it.get("tags")
        if tags is not None and not (isinstance(tags, list)
                                     and all(isinstance(t, str) and t for t in tags)):
            errors.append((scope, f"items[{i}] の tags が文字列の配列ではありません"))
            ok = False
        rel = it.get("related_urls")
        if rel is not None and not (isinstance(rel, list)
                                    and all(is_http_url(u) for u in rel)):
            errors.append((scope, f"items[{i}] の related_urls に不正な URL があります"))
            ok = False
        if ok:
            per_topic[topic] = per_topic.get(topic, 0) + 1
            norm = {
                "topic": topic,
                "headline": it["headline"],
                "summary": it["summary"],
                "url": url,
                "source": it["source"],
                "published_at": it["published_at"],
                "unconfirmed": bool(unc),
            }
            if st is not None:
                norm["status"] = st
            if tags:
                norm["tags"] = tags
            if rel:
                norm["related_urls"] = rel
            items_out.append(norm)

    # ---- checked
    raw_checked = data.get("checked")
    if not isinstance(raw_checked, list):
        errors.append((("file", None), "checked が配列ではありません"))
        raw_checked = []
    by_key = {}
    for c in raw_checked:
        if isinstance(c, dict) and isinstance(c.get("key"), str):
            if c["key"] in by_key:
                errors.append((("checked", c["key"]), f"checked の対象「{c['key']}」が重複しています"))
            by_key[c["key"]] = c
    unconfirmed_keys = []
    for key, topic, _required in TARGETS:
        c = by_key.get(key)
        if c is None:
            errors.append((("checked", key), f"checked に監視対象「{key}」がありません"))
            continue
        scope = ("checked", key)
        st = c.get("status")
        if st not in CHECK_STATUSES:
            errors.append((scope, f"checked「{key}」の status が不正です: {st!r}"))
            continue
        cnt = c.get("count")
        if not isinstance(cnt, int) or isinstance(cnt, bool) or cnt < 0:
            errors.append((scope, f"checked「{key}」の count が 0 以上の整数ではありません"))
            cnt = None
        if st == "確認済み":
            srcs = c.get("sources")
            if not (isinstance(srcs, list) and len(srcs) >= 1
                    and all(is_http_url(u) for u in srcs)):
                errors.append((scope,
                               f"checked「{key}」が確認済みですが、確認した情報源（sources）がありません"))
        else:
            unconfirmed_keys.append(key)
            if not (isinstance(c.get("note"), str) and c["note"].strip()):
                errors.append((scope, f"checked「{key}」が未確認ですが、理由（note）がありません"))
        if cnt is not None and cnt != per_topic.get(topic, 0):
            warnings.append(
                f"checked「{key}」の count（{cnt}）と items の topic「{topic}」の件数"
                f"（{per_topic.get(topic, 0)}）が一致しません")
    if unconfirmed_keys:
        warnings.append(f"未確認の監視対象: {', '.join(unconfirmed_keys)}")

    return {"errors": errors, "warnings": warnings,
            "items": items_out, "checked": raw_checked}
