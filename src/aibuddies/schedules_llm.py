import re
from typing import List

from .buddies import Buddy
from .config import get_config
from .llm import build_client


def generate_schedule(buddy: Buddy) -> List[str]:
    """
    Ask the LLM to propose a daily schedule (HH:MM|Message).
    Returns empty list if AI call fails or no API key configured.
    """
    cfg = get_config()
    client = build_client(cfg, buddy.model)
    prompt = (
        "Generate a concise daily schedule for this buddy. "
        "Output 3-6 lines, format HH:MM|Message, 24h time, local day cadence. "
        "Keep messages short and actionable. No extra text."
    )
    try:
        raw = client.ask(buddy.name, buddy.persona_prompt, prompt)
    except Exception:
        return []
    lines = [ln.strip() for ln in raw.splitlines() if ln.strip()]
    schedule: List[str] = []
    pattern = re.compile(r"^(\d{1,2}:\d{2})\s*[|-]\s*(.+)$")
    for ln in lines:
        m = pattern.match(ln)
        if m:
            hhmm = m.group(1)
            # normalize HH:MM
            parts = hhmm.split(":")
            hh = int(parts[0]) if parts and parts[0].isdigit() else 0
            mm = parts[1]
            hhmm_norm = f"{hh:02d}:{mm}"
            msg = m.group(2).strip()
            schedule.append(f"{hhmm_norm}|{msg}")
        if len(schedule) >= 6:
            break
    return schedule
