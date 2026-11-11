# Claude Code collect — GitHub Actions trial

This folder is a **trial port** of the AI Radar "Claude Code collect" to
GitHub Actions. The production run still lives on the owner's home PC
(Claude Code over SSH, driven from Muse every morning ~08:09 JST for the
previous 08:00 → 08:00 JST window); this port mirrors it as faithfully as
possible so the two can be compared:

- Same prompt: `prompts/common.md` + `collect-sources.md` +
  `prompts/task.md`, rendered by `gh_collect_run.py` with the same
  FROM/TO/DATE/GENERATED_AT placeholders and the same 08:00 JST window.
- Same validator: `claude_collect_validate.py` is an unmodified copy of
  the production validator (15 checked targets, item rules, coverage).
- Same recovery: one fix attempt with the validation errors attached
  (`prompts/fix.md`), then salvage by dropping bad items.
- Same outputs: a digest envelope + coverage record, written to
  `claude-collect/` at the repo root and uploaded as a workflow artifact.

The only real difference is transport: the driver runs `claude -p`
locally on the Actions runner instead of over SSH to the PC.

## The secret (required before the first run)

The workflow authenticates Claude Code with the owner's Claude
subscription via an OAuth token. On any machine where `claude` is logged
in to that subscription:

```sh
claude setup-token
```

Then store the token it prints as a repository secret named
**`CLAUDE_CODE_OAUTH_TOKEN`** (repo → Settings → Secrets and variables →
Actions → New repository secret). Without it, the workflow fails fast in
its preflight step with an explanation. Never commit the token anywhere.

## Running the trial

Actions tab → **Claude Code collect (trial)** → Run workflow.

- `commit` (default **false**): leave the results only in the workflow
  artifact — nothing in the repo changes. Set it to **true** only for a
  deliberate live test: the envelope is then also merged by URL into
  `inputs_muse/<window-end date>/claude-code.json` and pushed.
- `from` / `to` (optional): override the collection window (ISO 8601).
  Empty = the usual previous-day 08:00 → today 08:00 JST window.
- Download the `claude-collect-output` artifact to inspect the envelope
  (`YYYY-MM-DD.json`), the coverage record, the rendered prompt, the raw
  Claude replies, and the run log.

Exit codes mirror production: 0 ok, 3 auth failure, 4 no parseable JSON,
5 claude/transport failure, 6 validation failed after the fix attempt.

## Not yet

The `on:` trigger is **`workflow_dispatch` only** — there is
intentionally no schedule yet. A cron trigger (and retiring the PC run)
comes only after a manual trial produces output comparable to the PC
pipeline.
