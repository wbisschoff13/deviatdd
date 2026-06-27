"""Best-effort YAML repair helpers for FLOW-11 handover YAMLs.

A skill actor's emitted manifest may contain unquoted scalar values that
include ``: `` — a colon followed by a space — which ``yaml.safe_load``
rejects. ``repair_yaml_text()`` wraps those scalars in double quotes so
the loader can parse the document. Repairs are intentionally narrow so
the YAML structure stays byte-identical when no repair is needed.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml


_COLON_SCALAR_RE = re.compile(
    r"^(?P<indent>\s*)(?P<key>[A-Za-z_][\w\-]*): (?P<value>[^\n\"'].*?:.*?)$",
    re.MULTILINE,
)


def repair_yaml_text(text: str) -> str:
    """Wrap any unquoted scalar value containing ``: `` in double quotes.

    Only the leading ``key: value`` line is touched when the value
    contains a colon-space and is not already quoted. Otherwise the text
    is returned unchanged.
    """
    return _COLON_SCALAR_RE.sub(
        lambda m: f'{m.group("indent")}{m.group("key")}: "{m.group("value")}"',
        text,
    )


def safe_load_yaml(path: Path) -> dict | None:
    """Parse a YAML file, falling back to colon-repair once.

    Returns ``None`` when the document still cannot be parsed or when
    the top-level node is not a mapping. Stderr warnings describe the
    skip reason so a single corrupt file does not block synthesis.
    """
    raw_text = path.read_text(encoding="utf-8")
    try:
        loaded = yaml.safe_load(raw_text)
        if isinstance(loaded, dict):
            return loaded
    except yaml.YAMLError:
        pass
    try:
        loaded = yaml.safe_load(repair_yaml_text(raw_text))
        if isinstance(loaded, dict):
            return loaded
    except yaml.YAMLError as exc:
        print(
            f"warning: skipping malformed handover {path}: {exc}",
            file=sys.stderr,
        )
        return None
    print(
        f"warning: skipping non-mapping handover {path}",
        file=sys.stderr,
    )
    return None


__all__ = ["repair_yaml_text", "safe_load_yaml"]
