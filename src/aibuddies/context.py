from typing import Dict, List

from .buddies import Buddy


def gather_context(buddy: Buddy) -> Dict[str, str]:
    """
    Stub context collector. In future, map each source to a real collector:
    - screenshot: capture + OCR
    - window: active window title/app
    - clipboard: current clipboard text
    - docs: recent doc snippets
    """
    ctx: Dict[str, str] = {}
    for src in buddy.context_sources:
        if src == "screenshot":
            ctx[src] = "[screenshot OCR not implemented]"
        elif src == "window":
            ctx[src] = "[active window not implemented]"
        elif src == "clipboard":
            ctx[src] = "[clipboard not implemented]"
        elif src == "docs":
            ctx[src] = "[docs retrieval not implemented]"
        else:
            ctx[src] = "[unknown source]"
    return ctx
