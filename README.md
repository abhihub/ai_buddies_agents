# AI Buddies (CLI stub)

CLI wrapper around Claude Agent SDK/OpenAI with “Buddy” presets that run locally. Current state is a stub with basic commands; wiring to Claude Agents is partly implemented with fallbacks.

## Why
Let non-technical users spin up an AI agent with a single prompt and a couple of optional toggles. The agent picks sane defaults (models, tools, privacy, schedules) based on the prompt so users don’t have to configure anything beyond their intent.

## Features (current)
- Create/list/edit/delete buddies with persona + shared system prompt.
- Run a buddy; opens a terminal window for chat (macOS/Terminal or falls back to manual).
- Chat/ask one-shot; docs add/list/remove/clear per buddy.
- JSON storage in `~/.aibuddies`; CLI entrypoint `python -m aibuddies`.
- LLM adapter: prefers Claude (Agent SDK if present), then OpenAI, else Dummy echo. Default model: `claude-3-5-sonnet-20240620` (override with `--model`). Falls back through haiku/opus if a model is not found.
- Context sources (stub): pass `--context` (e.g., `screenshot window clipboard docs`) and they’re included as a text block until real collectors are wired.
- Proactive loop (minimal): `run` starts a scheduler that triggers a proactive check-in based on `--every` (1m/2m/5m/1h/2h/5h). Cron flag is stubbed.

## Quick start
```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
python -m pip install anthropic   # for Claude Agents
# python -m pip install openai    # optional

python -m aibuddies config set claude_api_key YOUR_KEY
python -m aibuddies create --name Doctor --prompt "You are a cautious doctor." --docs
python -m aibuddies run --name Doctor   # opens chat window if possible
# or manually:
python -m aibuddies chat --name Doctor

# proactive interval (e.g., 1h check-ins)
python -m aibuddies run --name GymCoach --every 1h

Run tests (stdlib unittest, no deps):
PYTHONPATH=src python -m unittest
```

## CLI commands (stub)
- Management: `list`, `create`, `edit`, `delete`, `run`, `stop`, `status`, `config set/show`.
- Interaction: `chat`, `ask`, `send`.
- Docs: `docs add/list/remove/clear/status`.

## Architecture (aligned to Claude Agent SDK)
- System prompt (shared) + buddy prompt → combined for each turn.
- Claude Agent SDK used when available; falls back to Claude messages or Dummy.
- Plan: register tools (notify, open_url allowlisted, retrieve_docs, context_snapshot) per buddy; use SDK for memory instead of manual compaction when possible.
- Context sources per buddy (screenshot/clipboard/active window/docs) will be opt-in and passed as structured tool results.
- Scheduler for autorun loops will gather context → call agent → execute tool calls with confirmations.

## Next steps
1) Wire Claude Agent SDK tools and stateful conversations; use agent memory instead of local history where available.
2) Add context collectors (screenshot OCR, active window, clipboard) with per-buddy allowlists + privacy toggles.
3) Implement doc retrieval (embeddings or agent-native retrieval), redaction, offline-only flag when sensitive docs present.
4) Add IPC/daemon for persistent sessions; improve terminal spawning across OSes.
5) Tests/CI: add basic CLI/unit tests with mocked LLM, and enable them in GitHub Actions.

## GitHub Actions
- See `.github/workflows/ci.yml` (placeholder) to run lint/tests once added.
