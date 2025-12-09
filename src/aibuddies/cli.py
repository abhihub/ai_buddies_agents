"""
AI Buddies CLI entrypoint (stub implementation).

Split into:
- Management commands: list/create/edit/delete/run/stop/status/pack/config.
- Interaction commands: chat/ask/docs/voice/send.

Note: Runtime + chat are stubs; "run" currently logs intent to open a new terminal window
for chat. Replace with real daemon + IPC + terminal spawning per OS.
"""
from pathlib import Path
import argparse
import sys
from typing import Optional

from .buddies import Buddy, BuddyStore
from .docs import DocIndex
from .runtime import RuntimeManager
from .config import get_config, set_config


runtime = RuntimeManager()
docs_index = DocIndex()
store = BuddyStore()


def cmd_list(args: argparse.Namespace) -> None:
    buddies = store.list()
    if not buddies:
        print("No buddies found. Use `aibuddies create --name Name --prompt \"...\"`.")
        return
    for b in buddies:
        running = "running" if b.name in runtime.running else "stopped"
        print(f"- {b.name} {b.emoji} [{running}] interval={b.autorun_interval} docs={'on' if b.docs_enabled else 'off'}")


def cmd_create(args: argparse.Namespace) -> None:
    if store.get(args.name):
        print(f"Buddy {args.name} already exists.")
        return
    buddy = Buddy(
        name=args.name,
        system_prompt=args.system_prompt or Buddy.system_prompt,
        persona_prompt=args.prompt or "You are a helpful buddy.",
        model=args.model,
        emoji=args.emoji,
        autorun_interval=args.every,
        screenshot=args.screenshot,
        clipboard=args.clipboard,
        context_sources=args.context or [],
        docs_enabled=args.docs,
    )
    store.create(buddy)
    print(f"Created buddy {buddy.name} ({buddy.emoji}).")


def cmd_delete(args: argparse.Namespace) -> None:
    if store.delete(args.name):
        print(f"Deleted buddy {args.name}.")
    else:
        print(f"Buddy {args.name} not found.")


def cmd_edit(args: argparse.Namespace) -> None:
    updates = {}
    for field in ("prompt", "system_prompt", "model", "every", "screenshot", "clipboard", "docs", "context"):
        val = getattr(args, field)
        if val is not None:
            key = "persona_prompt" if field == "prompt" else (
                "system_prompt" if field == "system_prompt" else (
                "autorun_interval" if field == "every" else (
                "context_sources" if field == "context" else field
            )))
            updates[key] = val
    if not updates:
        print("No updates provided.")
        return
    ok = store.update(args.name, updates)
    if ok:
        print(f"Updated buddy {args.name}.")
    else:
        print(f"Buddy {args.name} not found.")


def cmd_run(args: argparse.Namespace) -> None:
    buddy = store.get(args.name)
    if not buddy:
        print(f"Buddy {args.name} not found.")
        return
    if args.every:
        buddy.autorun_interval = args.every
        store.update(buddy.name, {"autorun_interval": args.every})
    if args.cron:
        buddy.autorun_cron = args.cron
        store.update(buddy.name, {"autorun_cron": args.cron})
    if args.schedule:
        buddy.schedule = args.schedule
        store.update(buddy.name, {"schedule": args.schedule})
    note = runtime.start(buddy, every=args.every, once=args.once)
    print(note)


def cmd_stop(args: argparse.Namespace) -> None:
    if args.name == "all":
        stopped = list(runtime.running.keys())
        runtime.running.clear()
        if stopped:
            print("Stopped: " + ", ".join(stopped))
        else:
            print("No buddies were running.")
        return
    if runtime.stop(args.name):
        print(f"Stopped {args.name}.")
    else:
        print(f"{args.name} was not running.")


def cmd_status(_: argparse.Namespace) -> None:
    statuses = runtime.status()
    if not statuses:
        print("No running buddies.")
        return
    for name, state in statuses.items():
        print(f"- {name}: {state}")


def cmd_chat(args: argparse.Namespace) -> None:
    buddy = store.get(args.name)
    if not buddy:
        print(f"Buddy {args.name} not found.")
        return
    # Ensure runtime knows about this buddy for ask() logic.
    runtime.running.setdefault(buddy.name, buddy)
    runtime._ensure_scheduler()
    print(f"Chatting with {buddy.name} {buddy.emoji}. Ctrl+C to exit.")
    import threading
    import time as _time

    def drain_printer() -> None:
        while True:
            msgs = runtime.drain_queue(buddy.name)
            for m in msgs:
                print(f"[{buddy.name}] {m}")
            _time.sleep(5)

    t = threading.Thread(target=drain_printer, daemon=True)
    t.start()
    try:
        while True:
            user_text = input("> ").strip()
            if not user_text:
                continue
            reply = runtime.ask(buddy.name, user_text)
            print(reply)
    except (KeyboardInterrupt, EOFError):
        print("\nBye.")


def cmd_ask(args: argparse.Namespace) -> None:
    buddy = store.get(args.name)
    if not buddy:
        print(f"Buddy {args.name} not found.")
        return
    runtime.running.setdefault(buddy.name, buddy)
    reply = runtime.ask(buddy.name, args.text)
    print(reply)


def cmd_docs_add(args: argparse.Namespace) -> None:
    buddy = store.get(args.name)
    if not buddy:
        print(f"Buddy {args.name} not found.")
        return
    src = Path(args.path).expanduser()
    if not src.exists():
        print(f"File not found: {src}")
        return
    msg = docs_index.add(buddy.name, src)
    print(msg)


def cmd_docs_list(args: argparse.Namespace) -> None:
    files = docs_index.list(args.name)
    if not files:
        print("No docs stored.")
        return
    for f in files:
        print(f"- {f}")


def cmd_docs_remove(args: argparse.Namespace) -> None:
    if docs_index.remove(args.name, args.file):
        print(f"Removed {args.file} for {args.name}.")
    else:
        print(f"File {args.file} not found for {args.name}.")


def cmd_docs_clear(args: argparse.Namespace) -> None:
    count = docs_index.clear(args.name)
    print(f"Cleared {count} file(s) for {args.name}.")


def cmd_docs_status(args: argparse.Namespace) -> None:
    status = docs_index.status(args.name)
    print(f"Docs: {status['count']} file(s). {status['files']}")


def cmd_config_set(args: argparse.Namespace) -> None:
    set_config(args.key, args.value)
    print(f"Set {args.key}.")


def cmd_config_show(_: argparse.Namespace) -> None:
    cfg = get_config()
    if not cfg:
        print("No config set.")
        return
    for k, v in cfg.items():
        print(f"{k}={v}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="aibuddies", description="AI Buddies CLI (stub).")
    sub = parser.add_subparsers(dest="command")

    # Management
    p_list = sub.add_parser("list", help="List buddies")
    p_list.set_defaults(func=cmd_list)

    p_create = sub.add_parser("create", help="Create a new buddy")
    p_create.add_argument("--name", required=True)
    p_create.add_argument("--prompt", required=True, help="Persona prompt")
    p_create.add_argument("--system-prompt", dest="system_prompt", help="Override system prompt (default shared prompt)")
    p_create.add_argument("--model", default="claude-3.5-sonnet")
    p_create.add_argument("--emoji", default="🤖")
    p_create.add_argument("--every", default="manual", help="Autorun interval (manual, 1m, 5m, 1h, etc)")
    p_create.add_argument("--screenshot", action="store_true", help="Enable screenshots")
    p_create.add_argument("--clipboard", action="store_true", help="Enable clipboard access")
    p_create.add_argument("--context", nargs="+", help="Context sources (e.g., screenshot window clipboard docs)")
    p_create.add_argument("--docs", action="store_true", help="Enable docs for this buddy")
    p_create.set_defaults(func=cmd_create)

    p_delete = sub.add_parser("delete", help="Delete a buddy")
    p_delete.add_argument("--name", required=True)
    p_delete.set_defaults(func=cmd_delete)

    p_edit = sub.add_parser("edit", help="Edit a buddy")
    p_edit.add_argument("--name", required=True)
    p_edit.add_argument("--prompt")
    p_edit.add_argument("--system-prompt", dest="system_prompt")
    p_edit.add_argument("--model")
    p_edit.add_argument("--every")
    p_edit.add_argument("--screenshot", type=bool)
    p_edit.add_argument("--clipboard", type=bool)
    p_edit.add_argument("--docs", type=bool)
    p_edit.add_argument("--context", nargs="+", help="Replace context sources list")
    p_edit.set_defaults(func=cmd_edit)

    p_run = sub.add_parser("run", help="Run a buddy (starts loop)")
    p_run.add_argument("--name", required=True)
    p_run.add_argument("--every", help="Override interval")
    p_run.add_argument("--cron", help="Experimental cron string (not implemented)")
    p_run.add_argument("--schedule", nargs="+", help='Fixed times, format "HH:MM|Message"')
    p_run.add_argument("--once", action="store_true", help="Run a single cycle")
    p_run.set_defaults(func=cmd_run)

    p_stop = sub.add_parser("stop", help="Stop a running buddy")
    p_stop.add_argument("--name", required=True, help="'all' to stop everything")
    p_stop.set_defaults(func=cmd_stop)

    p_status = sub.add_parser("status", help="Show running buddies")
    p_status.set_defaults(func=cmd_status)

    # Interaction
    p_chat = sub.add_parser("chat", help="Chat with a buddy")
    p_chat.add_argument("--name", required=True)
    p_chat.set_defaults(func=cmd_chat)

    p_ask = sub.add_parser("ask", help="One-shot question to a buddy")
    p_ask.add_argument("--name", required=True)
    p_ask.add_argument("text")
    p_ask.set_defaults(func=cmd_ask)

    p_send = sub.add_parser("send", help="Send a message/context to a buddy")
    p_send.add_argument("--name", required=True)
    p_send.add_argument("text")
    p_send.set_defaults(func=cmd_ask)

    # Docs
    p_docs = sub.add_parser("docs", help="Manage docs for a buddy")
    docs_sub = p_docs.add_subparsers(dest="docs_cmd")

    d_add = docs_sub.add_parser("add", help="Add a document")
    d_add.add_argument("--name", required=True, help="Buddy name")
    d_add.add_argument("path")
    d_add.set_defaults(func=cmd_docs_add)

    d_list = docs_sub.add_parser("list", help="List documents")
    d_list.add_argument("--name", required=True)
    d_list.set_defaults(func=cmd_docs_list)

    d_rm = docs_sub.add_parser("remove", help="Remove a document")
    d_rm.add_argument("--name", required=True)
    d_rm.add_argument("--file", required=True)
    d_rm.set_defaults(func=cmd_docs_remove)

    d_clear = docs_sub.add_parser("clear", help="Clear documents")
    d_clear.add_argument("--name", required=True)
    d_clear.set_defaults(func=cmd_docs_clear)

    d_status = docs_sub.add_parser("status", help="Docs status")
    d_status.add_argument("--name", required=True)
    d_status.set_defaults(func=cmd_docs_status)

    # Config
    p_cfg = sub.add_parser("config", help="Set or show config")
    cfg_sub = p_cfg.add_subparsers(dest="cfg_cmd")
    c_set = cfg_sub.add_parser("set", help="Set a config key")
    c_set.add_argument("key")
    c_set.add_argument("value")
    c_set.set_defaults(func=cmd_config_set)
    c_show = cfg_sub.add_parser("show", help="Show config")
    c_show.set_defaults(func=cmd_config_show)

    return parser


def main(argv: Optional[list] = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not hasattr(args, "func"):
        parser.print_help()
        sys.exit(1)
    args.func(args)


if __name__ == "__main__":
    main()
