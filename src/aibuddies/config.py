import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional


DEFAULT_HOME = Path(os.path.expanduser("~")) / ".aibuddies"


@dataclass
class Paths:
    """Filesystem layout for AI Buddies."""

    home: Path = DEFAULT_HOME
    config_file: Path = field(init=False)
    buddies_file: Path = field(init=False)
    logs_dir: Path = field(init=False)
    docs_dir: Path = field(init=False)
    running_file: Path = field(init=False)

    def __post_init__(self) -> None:
        self.config_file = self.home / "config.json"
        self.buddies_file = self.home / "buddies.json"
        self.logs_dir = self.home / "logs"
        self.docs_dir = self.home / "docs"
        self.running_file = self.home / "running.json"

    def ensure(self) -> None:
        self.home.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        self.docs_dir.mkdir(parents=True, exist_ok=True)
        self.running_file.parent.mkdir(parents=True, exist_ok=True)


def load_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {}


def save_json(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def get_config(paths: Optional[Paths] = None) -> Dict[str, Any]:
    paths = paths or Paths()
    paths.ensure()
    return load_json(paths.config_file)


def set_config(k: str, v: Any, paths: Optional[Paths] = None) -> None:
    paths = paths or Paths()
    paths.ensure()
    cfg = load_json(paths.config_file)
    cfg[k] = v
    save_json(paths.config_file, cfg)
