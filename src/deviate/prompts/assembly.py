from __future__ import annotations

import importlib.resources as resources
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def load_template(template_name: str) -> str:
    package_dir = resources.files("deviate.prompts.auto")
    template_path = package_dir / f"{template_name}.md"
    if not template_path.is_file():
        raise FileNotFoundError(
            f"Template '{template_name}' not found at {template_path}"
        )
    return template_path.read_text(encoding="utf-8")


def inject_constitution(
    prompt: str,
    constitution_path: Path,
    claude_path: Path,
) -> str:
    prefix_parts = []

    try:
        constitution_content = constitution_path.read_text(encoding="utf-8")
        prefix_parts.append(constitution_content)
    except OSError as exc:
        logger.warning("CONSTITUTION_MISSING: %s: %s", constitution_path, exc)

    if claude_path.exists():
        claude_content = claude_path.read_text(encoding="utf-8")
        prefix_parts.append(claude_content)

    if not prefix_parts:
        return prompt

    prefix = "\n\n".join(prefix_parts)
    return f"{prefix}\n\n{prompt}"


def assemble_prompt(
    template_name: str,
    context: dict[str, str],
    constitution_path: Path,
    claude_path: Path,
) -> str:
    template = load_template(template_name)
    prompt = inject_constitution(template, constitution_path, claude_path)
    for key, value in context.items():
        prompt = prompt.replace(f"${{{key}}}", value)
    return prompt
