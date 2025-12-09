import os
import platform
import shlex
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional

from .buddies import Buddy
from .config import get_config, Paths, load_json, save_json
from .context import gather_context
from .llm import build_client


class RuntimeManager:
    """
    Placeholder runtime controller.

    Real implementation should:
    - Spawn background processes or threads per buddy for autorun/scheduling.
    - Provide IPC (e.g., local socket) for chat/ask/voice commands.
    - Route tool calls to OS actions with safety checks.
    - Launch a new terminal window/tab to host the chat UX when a buddy starts.
    """

    def __init__(self, paths: Optional[Paths] = None) -> None:
        self.running: Dict[str, Buddy] = {}
        self.paths = paths or Paths()
        self.paths.ensure()
        self._scheduler_thread = None
        self._stop_scheduler = False
        self._last_tick: Dict[str, float] = {}
        self._message_queue: Dict[str, List[str]] = {}
        self._schedule_sent: Dict[str, Dict[str, str]] = {}  # buddy -> time_str -> yyyymmdd
        self._running_state = self._load_running()

    def start(self, buddy: Buddy, every: Optional[str] = None, once: bool = False) -> str:
        self.running[buddy.name] = buddy
        mode = "once" if once else every or buddy.autorun_interval
        spawn_note = self._open_chat_window(buddy.name)
        if not once:
            self._ensure_scheduler()
        self._mark_running(buddy, source="run")
        return f"Started {buddy.name} with interval={mode}. {spawn_note}"

    def stop(self, name: str) -> bool:
        if name in self.running:
            self.running.pop(name)
        removed = self._running_state.pop(name, None) is not None
        self._save_running()
        return name in self.running or removed

    def status(self) -> Dict[str, str]:
        # Combine in-process running and persisted running file
        all_states = dict(self._running_state)
        for name, buddy in self.running.items():
            all_states[name] = {
                "interval": buddy.autorun_interval,
                "schedule_len": len(buddy.schedule),
                "source": "current",
            }
        return {
            name: f"running (interval={info.get('interval')}, schedule={info.get('schedule_len')} entries, source={info.get('source')})"
            for name, info in all_states.items()
        }

    def send_message(self, buddy_name: str, text: str) -> str:
        return f"[stub] sent message to {buddy_name}: {text}"

    def ask(self, buddy_name: str, text: str) -> str:
        buddy = self.running.get(buddy_name) or None
        cfg = get_config(self.paths)
        # If buddy not running, try to load from store? For now, require running.
        if not buddy:
            return f"{buddy_name} is not running. Start it with `aibuddies run --name {buddy_name}`."
        client = build_client(cfg, buddy.model)
        context = gather_context(buddy)
        context_block = ""
        if context:
            lines = [f"- {k}: {v}" for k, v in context.items()]
            context_block = "Context:\n" + "\n".join(lines) + "\n\n"
        system_plus_persona = f"{buddy.system_prompt}\n\n{buddy.persona_prompt}"
        user_payload = context_block + text
        return client.ask(buddy_name, system_plus_persona, user_payload)

    def enqueue(self, buddy_name: str, message: str) -> None:
        self._message_queue.setdefault(buddy_name, []).append(message)

    def drain_queue(self, buddy_name: str) -> List[str]:
        msgs = self._message_queue.get(buddy_name, [])
        self._message_queue[buddy_name] = []
        return msgs

    def proactive_tick(self) -> None:
        """
        Iterate running buddies and trigger proactive prompts based on interval.
        This is minimal: supports autorun_interval (manual/1m/5m/1h/2h/5h).
        Cron-like strings are not implemented yet.
        """
        now = time.time()
        today = time.strftime("%Y%m%d", time.localtime(now))
        for buddy in list(self.running.values()):
            interval = buddy.autorun_interval
            if interval in ("manual", "", None):
                pass
            else:
                seconds = self._interval_to_seconds(interval)
                if seconds is not None:
                    last = self._last_tick.get(buddy.name, 0)
                    if now - last >= seconds:
                        prompt = "It's time to check in. Share a quick update or I'll suggest something."
                        self.enqueue(buddy.name, prompt)
                        self._last_tick[buddy.name] = now

            # Fixed schedule entries HH:MM|text
            if buddy.schedule:
                sent_map = self._schedule_sent.setdefault(buddy.name, {})
                hhmm_now = time.strftime("%H:%M", time.localtime(now))
                for entry in buddy.schedule:
                    if "|" in entry:
                        ts, msg = entry.split("|", 1)
                    else:
                        ts, msg = entry, entry
                    ts = ts.strip()
                    if ts == hhmm_now:
                        last_sent_date = sent_map.get(ts, "")
                        if last_sent_date != today:
                            self.enqueue(buddy.name, msg.strip())
                            sent_map[ts] = today

    @staticmethod
    def _interval_to_seconds(interval: str) -> Optional[int]:
        mapping = {
            "1m": 60,
            "2m": 120,
            "5m": 300,
            "1h": 3600,
            "2h": 7200,
            "5h": 18000,
        }
        return mapping.get(interval)

    def _ensure_scheduler(self) -> None:
        if self._scheduler_thread:
            return
        import threading

        def loop() -> None:
            while not self._stop_scheduler:
                try:
                    self.proactive_tick()
                finally:
                    time.sleep(60)  # check every minute

        self._scheduler_thread = threading.Thread(target=loop, daemon=True)
        self._scheduler_thread.start()

    def _load_running(self) -> Dict[str, Dict[str, str]]:
        data = load_json(self.paths.running_file)
        return data.get("running", {})

    def _save_running(self) -> None:
        save_json(self.paths.running_file, {"running": self._running_state})

    def _mark_running(self, buddy: Buddy, source: str) -> None:
        self._running_state[buddy.name] = {
            "interval": buddy.autorun_interval,
            "schedule_len": len(buddy.schedule),
            "source": source,
            "pid": str(os.getpid()),
            "started_at": str(time.time()),
        }
        self._save_running()

    def _open_chat_window(self, buddy_name: str) -> str:
        """
        Try to open a new terminal window/tab running the chat command.
        Falls back to printing the command if no terminal launcher is available.
        """
        repo_root = Path(__file__).resolve().parents[2]
        python_exec = shlex.quote(sys.executable)

        # If running in a venv, source it to ensure module resolution.
        venv = os.environ.get("VIRTUAL_ENV")
        activate = f"source {shlex.quote(venv + '/bin/activate')}; " if venv else ""

        chat_cmd = (
            f"cd {shlex.quote(str(repo_root))} && "
            f"{activate}{python_exec} -m aibuddies chat --name {shlex.quote(buddy_name)}"
        )
        system = platform.system()

        # macOS: use osascript with Terminal
        if system == "Darwin":
            osa = (
                'tell application "Terminal"\n'
                '  if not (exists window 1) then reopen\n'
                f'  do script "{chat_cmd}"\n'
                "  activate\n"
                "end tell"
            )
            try:
                subprocess.run(["osascript", "-e", osa], check=True)
                return f"Opened Terminal for chat. If you don't see it, run manually: {chat_cmd}"
            except Exception:
                # Try iTerm2 as a fallback
                try:
                    osa_iterm = (
                        'tell application "iTerm"\n'
                        "  create window with default profile\n"
                        f'  tell current session of current window to write text "{chat_cmd}"\n'
                        "  activate\n"
                        "end tell"
                    )
                    subprocess.run(["osascript", "-e", osa_iterm], check=True)
                    return f"Opened iTerm for chat. If you don't see it, run manually: {chat_cmd}"
                except Exception:
                    pass

        # Linux common terminals
        for term in ("gnome-terminal", "konsole", "xfce4-terminal", "xterm"):
            if shutil.which(term):
                try:
                    subprocess.Popen([term, "--", "bash", "-lc", chat_cmd])
                    return f"Opened {term} for chat. If you don't see it, run manually: {chat_cmd}"
                except Exception:
                    continue

        # Windows fallback
        if system == "Windows":
            try:
                subprocess.Popen(["start", "cmd", "/k", chat_cmd], shell=True)
                return f"Opened cmd for chat. If you don't see it, run manually: {chat_cmd}"
            except Exception:
                pass

        return f"Could not auto-open terminal. Run this in another window: {chat_cmd}"
