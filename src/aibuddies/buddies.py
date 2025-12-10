from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from .config import Paths, load_json, save_json


@dataclass
class Buddy:
    name: str
    persona_prompt: str
    system_prompt: str = (
        "You are AI Buddies runtime. Be concise, helpful, and safe. "
        "Always confirm risky actions. Stay on-task for this buddy's role."
    )
    model: str = "claude-3-5-sonnet-20240620"
    emoji: str = "🤖"
    autorun_interval: str = "1h"
    autorun_cron: str = ""  # optional cron-like string, e.g., "0 9 * * *"
    schedule: List[str] = field(default_factory=list)  # entries like "06:00|Good morning"
    screenshot: bool = False
    clipboard: bool = False
    context_sources: List[str] = field(default_factory=list)
    docs_enabled: bool = False
    doc_privacy: Dict[str, Any] = field(default_factory=lambda: {
        "redact_pii_default": True,
        "allow_cloud_with_docs": False,
        "export_allowed": False,
        "doc_quota_mb": 50,
    })
    tools_allowed: List[str] = field(default_factory=lambda: ["retrieve_docs", "notify"])
    safety_rules: Dict[str, Any] = field(default_factory=lambda: {
        "confirm_commands": True,
        "allowlist_paths": [],
        "allowlist_domains": [],
        "auto_action": False,
    })
    style: Dict[str, Any] = field(default_factory=lambda: {"color": "cyan"})
    pack_meta: Dict[str, Any] = field(default_factory=lambda: {"author": "AI Buddies", "version": "0.1.0"})

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "Buddy":
        return Buddy(**data)

    def to_dict(self) -> Dict[str, Any]:
        return self.__dict__


class BuddyStore:
    """Simple JSON-backed buddy store."""

    def __init__(self, paths: Optional[Paths] = None) -> None:
        self.paths = paths or Paths()
        self.paths.ensure()
        self.buddies: Dict[str, Buddy] = {}
        self._load()

    def _load(self) -> None:
        data = load_json(self.paths.buddies_file)
        self.buddies = {name: Buddy.from_dict(cfg) for name, cfg in data.get("buddies", {}).items()}

    def _save(self) -> None:
        save_json(self.paths.buddies_file, {"buddies": {name: b.to_dict() for name, b in self.buddies.items()}})

    def list(self) -> List[Buddy]:
        return list(self.buddies.values())

    def get(self, name: str) -> Optional[Buddy]:
        return self.buddies.get(name)

    def create(self, buddy: Buddy) -> None:
        self.buddies[buddy.name] = buddy
        self._save()

    def delete(self, name: str) -> bool:
        existed = name in self.buddies
        if existed:
            self.buddies.pop(name)
            self._save()
        return existed

    def update(self, name: str, updates: Dict[str, Any]) -> bool:
        buddy = self.buddies.get(name)
        if not buddy:
            return False
        for k, v in updates.items():
            if hasattr(buddy, k):
                setattr(buddy, k, v)
        self._save()
        return True
