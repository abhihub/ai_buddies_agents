# AI Buddies (CLI)

CLI wrapper around Claude Agent SDK/OpenAI. Create a “buddy” with a prompt, and it will chat and proactively message you on a schedule. All state lives under `~/.aibuddies`.

## TL;DR
- `python -m aibuddies create --name GymCoach --prompt "You are an upbeat gym coach."`
- `python -m aibuddies run --name GymCoach` (opens chat; default 1h interval, AI-generated schedule if empty)
- `python -m aibuddies chat --name GymCoach` (manual chat if window didn’t open)
- `python -m aibuddies schedule show --name GymCoach`
- `python -m aibuddies status`

## Install
```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
python -m pip install anthropic   # Claude Agents
# python -m pip install openai    # optional
```

Set keys:
```bash
python -m aibuddies config set claude_api_key YOUR_KEY
# or openai_api_key YOUR_KEY
```

## Running buddies
- Create: `python -m aibuddies create --name Doctor --prompt "You are a cautious doctor." --docs`
- Run (starts scheduler, opens chat): `python -m aibuddies run --name Doctor`
- Interval override: `python -m aibuddies run --name GymCoach --every 2h` (default 1h)
- Fixed times: `python -m aibuddies run --name GymCoach --schedule "06:00|Wake up" "14:00|Lunch check"`
- Auto-schedule: if no schedule exists, the AI proposes HH:MM|Message lines; if it fails/no key, schedule stays empty.
- Show schedule: `python -m aibuddies schedule show --name GymCoach`
- Status (persisted across shells): `python -m aibuddies status`

## Behavior
- LLM selection: Claude (Agent SDK if available, cached per buddy/model) → OpenAI → Dummy.
- Default model: `claude-3-5-sonnet-20240620` (override with `--model`); falls back through haiku/opus if not found.
- Proactive loop: checks every minute; fires interval prompts (1m/2m/5m/1h/2h/5h) and fixed-time HH:MM entries. Cron flag is stubbed.
- Context: `--context` (screenshot/window/clipboard/docs) is stubbed; currently just included as text.
- Schedules and running state are persisted in `~/.aibuddies`.

## Commands
- Management: `list`, `create`, `edit`, `delete`, `run`, `stop`, `status`, `config set/show`.
- Interaction: `chat`, `ask`, `send`.
- Docs: `docs add/list/remove/clear/status`.
- Schedule: `schedule show --name <Buddy>`

## Tests
```bash
PYTHONPATH=src python -m unittest
```

## TODO
- Wire Claude Agent SDK tools (notify/open_url/retrieve_docs/context) and richer memory.
- Add real context collectors (screenshot OCR, active window, clipboard) with privacy toggles.
- Doc retrieval with redaction/offline-only.
- Better daemon/IPC and terminal spawning.
- CI: real tests/lint in GitHub Actions.
