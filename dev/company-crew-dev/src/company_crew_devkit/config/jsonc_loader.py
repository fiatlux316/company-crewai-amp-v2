from __future__ import annotations

import json
from pathlib import Path
import re
from typing import Any


_COMMENT_RE = re.compile(r"(^|[^:])//.*?$|/\*.*?\*/", re.MULTILINE | re.DOTALL)


def load_jsonc(path: str | Path) -> dict[str, Any]:
    """Small JSONC loader for controlled config files.

    For production, replace with a dedicated JSONC parser if configs contain comment-like text in strings.
    """
    text = Path(path).read_text(encoding="utf-8")
    text = _COMMENT_RE.sub(lambda m: m.group(1) if m.group(1) else "", text)
    return json.loads(text)
