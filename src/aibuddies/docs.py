from pathlib import Path
from typing import Dict, List, Optional

from .config import Paths


class DocIndex:
    """Stubbed doc index to attach per-buddy files."""

    def __init__(self, paths: Optional[Paths] = None) -> None:
        self.paths = paths or Paths()
        self.paths.ensure()

    def buddy_dir(self, buddy: str) -> Path:
        return self.paths.docs_dir / buddy

    def add(self, buddy: str, source_path: Path) -> str:
        dest_dir = self.buddy_dir(buddy)
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest_path = dest_dir / source_path.name
        dest_path.write_bytes(source_path.read_bytes())
        return f"Stored {source_path} for {buddy} at {dest_path}"

    def list(self, buddy: str) -> List[str]:
        dir_path = self.buddy_dir(buddy)
        if not dir_path.exists():
            return []
        return [p.name for p in dir_path.iterdir() if p.is_file()]

    def remove(self, buddy: str, filename: str) -> bool:
        target = self.buddy_dir(buddy) / filename
        if target.exists():
            target.unlink()
            return True
        return False

    def clear(self, buddy: str) -> int:
        dir_path = self.buddy_dir(buddy)
        if not dir_path.exists():
            return 0
        count = 0
        for p in dir_path.iterdir():
            if p.is_file():
                p.unlink()
                count += 1
        return count

    def status(self, buddy: str) -> Dict[str, str]:
        files = self.list(buddy)
        return {
            "count": str(len(files)),
            "files": ", ".join(files) if files else "none",
        }
