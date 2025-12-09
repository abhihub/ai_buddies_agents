Task: Build a project called AI Buddies. Its easy to use AI Agents that sit on your computer.  

Concept: "AI Buddies: your laptop just grew personalities — a cast of customizable agents that feel like characters, not chat boxes. They observe moments where assistance is needed (with permission) and provide supportive actions. Swap looks and skills, remix them like mods, and share Buddy Packs with friends. It’s utility with culture."

Tech: Keep it as simple CLI commands. Agent should live in the CLI. e.g. it could be AIBuddies -new "doctor". You can use the Claude Agent SDK. And any voice API. And any other APIs as needed. We give a 2-4 agents to choose from. But user can create their own agents by choosing some simple params. e.g. example params: -BuddyPrompt, -AutoRunTime (1min, 2min, 5min, 1hr, 2hrs, 5hrs), -Screenshot (yes, no).

Examples of buddies:
- Gym coach
- Physics tutor
- Doctor
- Financial planner
- Crypto trader

Here’s a clean split for the CLI with verbs for each side.

  Part 1: Buddy Management (admin layer)

  - aibuddies list — show buddies, status (running/stopped), last run, mode (manual/interval).
  - aibuddies create --name "Doctor" --from preset/blank --prompt "…" --every 1h --screenshot off --voice off --docs off
  - aibuddies edit --buddy Doctor --prompt "…" --every manual --screenshot on --allow-cloud-with-docs false
  - aibuddies delete --buddy Doctor
  - aibuddies run --buddy Doctor --every 1h — start background loop (or --once).
  - aibuddies stop --buddy Doctor / stop --all
  - aibuddies status — show running buddies, next tick, doc counts, offline/online mode.
  - aibuddies logs --buddy Doctor --tail 50
  - aibuddies pack export --buddy Doctor --out doctor_pack.zip (no docs unless --include-docs)
  - aibuddies pack import doctor_pack.zip
  - aibuddies config set api_key=…, config show, config privacy --screenshots off --clipboard off

  Part 2: Buddy Interaction (runtime layer)

  - aibuddies chat --buddy Doctor — starts interactive chat with the running instance (or spins one up transiently).
  - aibuddies ask --buddy Doctor "Should I take zinc for this cold?" — one-shot, returns answer.
  - aibuddies docs add --buddy Doctor ~/med_history.pdf (with redact/offline prompts), docs list/remove/clear/status/reindex.
  - aibuddies voice --buddy Doctor --mic — STT → Agent → TTS back.
  - aibuddies send --buddy Doctor --context "I’m traveling next week, adjust plan" --file plan.pdf — pushes a message + optional file to the running
    agent.
  - aibuddies notify --buddy GymCoach "start session now" — send a nudge/trigger to a running buddy.
  - aibuddies actions --buddy Doctor — show pending/last actions, confirm/deny queued ones in headless mode.



  
• Built a Python CLI skeleton with management + interaction commands and doc support stubs. Key files: src/aibuddies/cli.py, src/aibuddies/config.py, src/
  aibuddies/buddies.py, src/aibuddies/docs.py, src/aibuddies/runtime.py, src/aibuddies/__main__.py.

  What it does now

  - Management: list, create, edit, delete, run, stop, status, config set/show.
  - Interaction: chat (inline loop), ask one-shot, send (same as ask stub), docs (add/list/remove/clear/status).
  - Storage: JSON-backed config/buddy store under ~/.aibuddies; docs saved per buddy in ~/.aibuddies/docs/<buddy>/.
  - Runtime stub: tracks running buddies; run prints intent to start and notes that chat should open in a new terminal window. New-window spawning is not
    implemented yet—chat works via aibuddies chat --name <Buddy> in another terminal.

  How to try (stub)

  - python -m aibuddies create --name Doctor --prompt "You are a cautious doctor." --docs
  - python -m aibuddies run --name Doctor (prints stub and reminder to open chat)
  - In another terminal: python -m aibuddies chat --name Doctor
  - python -m aibuddies docs add --name Doctor ~/med_history.pdf then docs list/status.

  Next steps

  1. Implement real runtime/daemon + IPC, and actually spawn a new terminal window/tab for chat (macOS: osascript/open, or tmux/screen fallback).
  2. Wire Claude/OpenAI client, replace runtime.ask/send with real Agent calls, and add tool routing + safety gates.
  3. Flesh out doc indexing/retrieval (PII redaction, embeddings, offline mode), pack import/export, and voice commands.


› Where do I enter the keys for Claude Agent SDK ?


• I'm outlining how to use the config set command with an example, noting that config is stored in /.aibuddies/config.json, and mentioning placeholders
  clearly and concisely.

─ Worked for 3s ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

• Use the CLI config command (stored in ~/.aibuddies/config.json):

  - python -m aibuddies config set claude_api_key YOUR_KEY
  - To verify: python -m aibuddies config show

  That’s it—runtime will read from ~/.aibuddies/config.json when we wire the SDK. If you also need OpenAI, add openai_api_key YOUR_KEY the same way.