import os
import platform
import shlex
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict, Optional

from .buddies import Buddy
from .config import get_config, Paths
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

    def start(self, buddy: Buddy, every: Optional[str] = None, once: bool = False) -> str:
        self.running[buddy.name] = buddy
        mode = "once" if once else every or buddy.autorun_interval
        spawn_note = self._open_chat_window(buddy.name)
        return f"Started {buddy.name} with interval={mode}. {spawn_note}"

    def stop(self, name: str) -> bool:
        if name in self.running:
            self.running.pop(name)
            return True
        return False

    def status(self) -> Dict[str, str]:
        return {name: f"running (interval={b.autorun_interval})" for name, b in self.running.items()}

    def send_message(self, buddy_name: str, text: str) -> str:
        return f"[stub] sent message to {buddy_name}: {text}"

    def ask(self, buddy_name: str, text: str) -> str:
        buddy = self.running.get(buddy_name) or None
        cfg = get_config(self.paths)
        # If buddy not running, try to load from store? For now, require running.
        if not buddy:
            return f"{buddy_name} is not running. Start it with `aibuddies run --name {buddy_name}`."
        client = build_client(cfg, buddy.model)
        system_plus_persona = f"{buddy.system_prompt}\n\n{buddy.persona_prompt}"
        return client.ask(buddy_name, system_plus_persona, text)

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
