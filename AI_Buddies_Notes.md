# AI Buddies Notes (Stub CLI)
python3 -m venv .venv
  - source .venv/bin/activate
  - python -m pip install -e .
  - Then run: python -m aibuddies create --name Doctor --prompt "You are a cautious doctor." --docs
  
## What exists now
- Python package under `src/aibuddies/` with CLI entrypoint (`python -m aibuddies`).
- Commands (stubs): manage buddies (`list`, `create`, `edit`, `delete`, `run`, `stop`, `status`, `config set/show`), interact (`chat`, `ask`, `send`), docs (`docs add/list/remove/clear/status`).
- Storage: `~/.aibuddies/config.json` for config; `~/.aibuddies/buddies.json` for buddies; docs per buddy in `~/.aibuddies/docs/<buddy>/`.
- Runtime: stub `RuntimeManager` starts buddies and tries to open a new terminal window for `chat` (macOS via `osascript`, Linux via common terminals). Falls back to printing the command if it can’t auto-open.
- LLM: prefers Claude if `claude_api_key` is set, then OpenAI if `openai_api_key` is set; otherwise falls back to `DummyLLM`. Claude path uses Agent SDK if available in the `anthropic` client; otherwise plain messages. Install `anthropic` or `openai` SDKs for real calls. System prompt + buddy prompt are combined before sending. Default model: `claude-3-5-sonnet-20240620` (override via `--model`); falls back through haiku/opus if a model is not found.
- Context: `context_sources` per buddy (e.g., screenshot/window/clipboard/docs) currently stubbed; included as text in the user payload.
- Proactive loop: scheduler ticks every minute; fires proactive check-ins based on `autorun_interval` (1m/2m/5m/1h/2h/5h). Cron stub not implemented yet.
- Fixed schedule: `schedule` entries like `HH:MM|Message` enqueue messages once per day when the time matches; chat loop prints them via a background thread.
- Auto-schedule: if no schedule is set, we ask the AI to propose HH:MM|Message lines. If the AI call fails or there is no API key, schedule stays empty.
- Status: persisted running file tracks buddies started via run/chat; `status` reads it across processes.

## Setup
- From repo root: `python -m pip install -e .` (uses `pyproject.toml` with src/ layout).
- Or without install: run with `PYTHONPATH=src python -m aibuddies ...` from repo root.
- To use real LLMs, install SDKs: `python -m pip install anthropic` for Claude, `python -m pip install openai` for OpenAI (in your virtualenv).

## Key files
- `src/aibuddies/cli.py` — argument parsing and command handlers (stubs).
- `src/aibuddies/buddies.py` — Buddy model and JSON-backed store.
- `src/aibuddies/docs.py` — per-buddy doc storage stubs.
- `src/aibuddies/runtime.py` — runtime controller stub (tracks running buddies, opens chat window). `status` reports running buddies.
- `src/aibuddies/llm.py` — LLM adapter (Claude/OpenAI preference with Dummy fallback).
- `src/aibuddies/context.py` — stub context collector.
- `src/aibuddies/buddies.py` — buddy schema (now includes autorun_cron stub).
- `src/aibuddies/config.py` — config load/save helpers.
- `src/aibuddies/__main__.py` — CLI entrypoint.

## CLI usage (stub)
- Create: `python -m aibuddies create --name Doctor --prompt "You are a cautious doctor." --docs`
- Run (prints stub): `python -m aibuddies run --name Doctor`
- Chat (separate terminal): `python -m aibuddies chat --name Doctor`
- Ask once: `python -m aibuddies ask --name Doctor "Should I take zinc?"`
- Docs: `python -m aibuddies docs add --name Doctor ~/med_history.pdf`; list/status/remove/clear via subcommands.
- Config keys (API keys, etc.): `python -m aibuddies config set claude_api_key YOUR_KEY`; show with `python -m aibuddies config show`.
- Tests: `PYTHONPATH=src python3 -m unittest`

## Pending work
- Real runtime/daemon + IPC; auto-open a new terminal window/tab for chat on `run`.
- Hook Claude Agents/OpenAI clients into `runtime.ask/send` and add tool routing/safety.
- Proper doc indexing/retrieval (PII redaction, embeddings, offline mode), pack import/export, voice commands.
