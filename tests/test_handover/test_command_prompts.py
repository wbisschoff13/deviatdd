"""Tests for AC-ADHOC-012-13 + AC-ADHOC-013: 19 phase command prompts each carry a Write instruction.

Scenario 012-13 from ``specs/adhoc/issues/012-deviate-content.md`` —
each ``src/deviate/prompts/commands/<name>.md`` for the 15 listed
phase commands contains a one-sentence Write instruction that references
the canonical ``handover_path()`` target. Extended per FR-ADHOC-013
to cover the 4 Product-layer commands (``deviate-constitution``,
``deviate-flows``, ``deviate-architecture``, ``deviate-release``) for a
total of 19 entries.

Canonical list per ``specs/plans/deviate-content.md:79-87`` (extended):

* Micro layer (10 commands): ``deviate-red``, ``deviate-green``,
  ``deviate-yellow``, ``deviate-judge``, ``deviate-refactor``,
  ``deviate-execute``, ``deviate-e2e``, ``deviate-hotfix``,
  ``deviate-prune``, ``deviate-review``
* Macro layer (5 commands): ``deviate-research``, ``deviate-prd``,
  ``deviate-shard``, ``deviate-plan``, ``deviate-tasks``
* Product layer (4 commands, AC-ADHOC-013): ``deviate-constitution``,
  ``deviate-flows``, ``deviate-architecture``, ``deviate-release``

The instruction uses the deterministic marker ``handover_path()`` so
the append operation is idempotent against repeated re-runs (per
``specs/adhoc/issues/012-deviate-content.md`` Edge Cases and
Boundaries: "Re-running the implementation against an updated 15-skill
list: The append operation must be idempotent. ... Use a deterministic
marker (e.g., the literal string ``handover_path()``) to detect
presence."). Product-layer commands emit to the sentinel path
``.deviate/content/handovers/_product/<skill-name>/<skill-name>.yaml`` per
``handover_path("_product", "<skill-name>", "<skill-name>")``.

The instruction lives inside the terminal-contract section of each
command — either the ``## Handover Persistence (FLOW-11)`` heading inside
the ``<output_format_schemas>`` block (14 of 19 commands) or the
``<handover_persistence>`` XML tag (``deviate-review``).
"""

from __future__ import annotations

import pytest

from deviate.core.commands import resolve_command


# Canonical list per specs/plans/deviate-content.md:79-87.
# Extended to 19 entries per FR-ADHOC-013 (Product-layer commands).
# Total: 19 commands (10 micro + 5 macro + 4 product).
PHASE_COMMANDS: list[str] = [
    # Micro layer (10 commands)
    "deviate-red",
    "deviate-green",
    "deviate-yellow",
    "deviate-judge",
    "deviate-refactor",
    "deviate-execute",
    "deviate-e2e",
    "deviate-hotfix",
    "deviate-prune",
    "deviate-review",
    # Macro layer (5 commands)
    "deviate-research",
    "deviate-prd",
    "deviate-shard",
    "deviate-plan",
    "deviate-tasks",
    # Product layer (4 commands)
    "deviate-constitution",
    "deviate-flows",
    "deviate-architecture",
    "deviate-release",
]

_MICRO_COMMANDS: list[str] = [
    "deviate-red",
    "deviate-green",
    "deviate-yellow",
    "deviate-judge",
    "deviate-refactor",
    "deviate-execute",
    "deviate-e2e",
    "deviate-hotfix",
    "deviate-prune",
    "deviate-review",
]

_MACRO_COMMANDS: list[str] = [
    "deviate-research",
    "deviate-prd",
    "deviate-shard",
    "deviate-plan",
    "deviate-tasks",
]

_PRODUCT_COMMANDS: list[str] = [
    "deviate-constitution",
    "deviate-flows",
    "deviate-architecture",
    "deviate-release",
]


def _extract_terminal_section(text: str) -> str | None:
    """Return the substring that hosts the Write instruction.

    Returns ``None`` when no recognized terminal-contract marker is
    present. The function never raises — callers assert on the return
    value. Recognized section shapes:

    * ``<handover_persistence>...</handover_persistence>`` (deviate-review)
    * ``<output_format_schemas>...</output_format_schemas>``
    * ``<output_format_schemas_design_md>...</output_format_schemas_design_md>``
      (deviate-research — paired design/data-model schema blocks)
    * ``<output_format_schemas_data_model_md>...</output_format_schemas_data_model_md>``
    * Markdown heading ``## Handover Persistence (FLOW-11)`` when no XML
      wrapper exists (deviate-refactor, deviate-e2e, deviate-prune).
    """
    # Prefer XML-tag-wrapped sections (most specific). Match both the
    # singular form and the design/data-model suffixed forms.
    xml_open_tags = (
        "<handover_persistence>",
        "<output_format_schemas>",
        "<output_format_schemas_design_md>",
        "<output_format_schemas_data_model_md>",
    )
    xml_close_tags = (
        "</handover_persistence>",
        "</output_format_schemas>",
        "</output_format_schemas_design_md>",
        "</output_format_schemas_data_model_md>",
    )
    for open_tag, close_tag in zip(xml_open_tags, xml_close_tags, strict=True):
        if open_tag in text and close_tag in text:
            start = text.find(open_tag)
            end = text.find(close_tag, start)
            if start < end:
                return text[start:end]
    # Fallback: markdown heading without XML wrapper.
    if "## Handover Persistence (FLOW-11)" in text:
        start = text.find("## Handover Persistence (FLOW-11)")
        return text[start:]
    return None


class TestCommandPromptHandoverInstruction:
    """AC-ADHOC-012-13 + AC-ADHOC-013 — all 19 listed phase commands carry the Write instruction.

    The instruction must reference the canonical ``handover_path()``
    target at ``.deviate/content/handovers/<epic>/<issue>/[<task>/]<phase>.yaml``.
    Product-layer commands target the sentinel path
    ``.deviate/content/handovers/_product/<skill-name>/<skill-name>.yaml``.
    """

    @pytest.mark.parametrize("command_name", PHASE_COMMANDS)
    def test_command_has_write_instruction(self, command_name: str) -> None:
        """Each phase command file contains the Write tool reference."""
        path = resolve_command(command_name)
        text = path.read_text(encoding="utf-8")
        assert "Write tool" in text, (
            f"Skill '{command_name}' at {path} is missing the Write tool reference"
        )
        assert "handover_path()" in text, (
            f"Skill '{command_name}' at {path} is missing the deterministic "
            f"marker 'handover_path()'"
        )

    @pytest.mark.parametrize("command_name", PHASE_COMMANDS)
    def test_command_references_canonical_handover_path(
        self, command_name: str
    ) -> None:
        """Each phase command references the canonical handover path format.

        The instruction must show the ``.deviate/content/handovers/<epic>/<issue>/
        [<task>/]<phase>.yaml`` shape so the command actor can construct
        the destination without ambiguity.
        """
        path = resolve_command(command_name)
        text = path.read_text(encoding="utf-8")
        assert ".deviate/content/handovers/" in text, (
            f"Skill '{command_name}' does not reference the .deviate/content/handovers/ path"
        )
        for placeholder in ("<epic>", "<issue>", "<phase>"):
            assert placeholder in text, (
                f"Skill '{command_name}' is missing path placeholder '{placeholder}'"
            )

    @pytest.mark.parametrize("command_name", PHASE_COMMANDS)
    def test_command_instruction_lives_in_terminal_contract_section(
        self, command_name: str
    ) -> None:
        """The Write instruction sits inside the terminal-contract section.

        Two accepted shapes:

        * ``## Handover Persistence (FLOW-11)`` heading inside the
          ``<output_format_schemas>`` block (most commands).
        * ``<handover_persistence>`` XML tag (``deviate-review``).
        """
        path = resolve_command(command_name)
        text = path.read_text(encoding="utf-8")

        section = _extract_terminal_section(text)
        assert section is not None, (
            f"Skill '{command_name}' is missing the terminal-contract section "
            "for the handover Write instruction "
            "(expected '## Handover Persistence (FLOW-11)' heading or "
            "'<handover_persistence>' XML tag)"
        )
        assert "Write tool" in section, (
            f"Skill '{command_name}': Write tool reference not located inside "
            "the terminal-contract section"
        )
        assert "handover_path()" in section, (
            f"Skill '{command_name}': 'handover_path()' marker not located "
            "inside the terminal-contract section"
        )

    @pytest.mark.parametrize("command_name", PHASE_COMMANDS)
    def test_command_instruction_is_idempotent(self, command_name: str) -> None:
        """The deterministic marker appears exactly once per command.

        Re-running the append operation against an already-instrumented
        command must be a no-op. The contract requires ``handover_path()``
        to occur exactly once; duplicates indicate a non-idempotent
        implementation.
        """
        path = resolve_command(command_name)
        text = path.read_text(encoding="utf-8")
        marker_count = text.count("handover_path()")
        assert marker_count == 1, (
            f"Skill '{command_name}' carries 'handover_path()' {marker_count} "
            "times; expected exactly one occurrence (idempotent append "
            "contract)."
        )


class TestCommandPromptHandoverCoverage:
    """Sanity coverage for the canonical 19-command list."""

    def test_canonical_command_list_has_exactly_nineteen(self) -> None:
        assert len(PHASE_COMMANDS) == 19, (
            f"Expected 19 phase commands, got {len(PHASE_COMMANDS)}: {PHASE_COMMANDS}"
        )

    def test_canonical_command_list_has_no_duplicates(self) -> None:
        assert len(PHASE_COMMANDS) == len(set(PHASE_COMMANDS)), (
            f"Duplicate command names in canonical list: {PHASE_COMMANDS}"
        )

    def test_micro_layer_covers_ten_commands(self) -> None:
        for name in _MICRO_COMMANDS:
            assert name in PHASE_COMMANDS, f"Missing micro command: {name}"
        assert len(_MICRO_COMMANDS) == 10
        assert sum(1 for s in PHASE_COMMANDS if s in set(_MICRO_COMMANDS)) == 10

    def test_macro_layer_covers_five_commands(self) -> None:
        for name in _MACRO_COMMANDS:
            assert name in PHASE_COMMANDS, f"Missing macro command: {name}"
        assert len(_MACRO_COMMANDS) == 5
        assert sum(1 for s in PHASE_COMMANDS if s in set(_MACRO_COMMANDS)) == 5

    def test_product_layer_covers_four_commands(self) -> None:
        """AC-ADHOC-013-03 — the Product layer contributes exactly 4 commands.

        Verifies that the canonical list extends from 15 to 19 entries
        by appending ``deviate-constitution``, ``deviate-flows``,
        ``deviate-architecture``, ``deviate-release``. The sentinel
        ``handover_path("_product", ...)`` invocation pattern targets
        ``.deviate/content/handovers/_product/<skill-name>/<skill-name>.yaml``.
        """
        for name in _PRODUCT_COMMANDS:
            assert name in PHASE_COMMANDS, f"Missing product command: {name}"
        assert len(_PRODUCT_COMMANDS) == 4, (
            f"Expected 4 product commands, got {len(_PRODUCT_COMMANDS)}: "
            f"{_PRODUCT_COMMANDS}"
        )
        assert sum(1 for s in PHASE_COMMANDS if s in set(_PRODUCT_COMMANDS)) == 4
        # Layer totals must sum to the canonical list size
        assert len(_MICRO_COMMANDS) + len(_MACRO_COMMANDS) + len(
            _PRODUCT_COMMANDS
        ) == len(PHASE_COMMANDS)

    @pytest.mark.parametrize("command_name", PHASE_COMMANDS)
    def test_command_file_resolves_and_exists(self, command_name: str) -> None:
        """Each canonical command resolves to an existing .md file on disk."""
        path = resolve_command(command_name)
        assert path.exists(), f"Command file not found: {path}"
        assert path.suffix == ".md"
        assert path.stem == command_name


class TestCommandPromptHandoverNonRegressions:
    """Append is the only allowed modification — no other content drift."""

    @pytest.mark.parametrize("command_name", PHASE_COMMANDS)
    def test_command_keeps_frontmatter_name(self, command_name: str) -> None:
        """Each command's frontmatter still declares ``name: <command>``."""
        path = resolve_command(command_name)
        text = path.read_text(encoding="utf-8")
        assert f"name: {command_name}" in text, (
            f"Skill '{command_name}' frontmatter is missing "
            f"'name: {command_name}' (frontmatter regression?)"
        )

    @pytest.mark.parametrize("command_name", PHASE_COMMANDS)
    def test_command_keeps_output_format_schemas_close_tag(
        self, command_name: str
    ) -> None:
        """For commands that wrap their terminal contract in an
        ``<output_format_schemas>`` block, the closing tag must remain
        present so the append stays inside the existing structure.
        Commands that use ``<handover_persistence>``, plural-form
        ``<output_format_schemas_*_md>`` blocks, or no XML wrapper at
        all are unaffected.
        """
        path = resolve_command(command_name)
        text = path.read_text(encoding="utf-8")
        if "<output_format_schemas>" in text:
            assert "</output_format_schemas>" in text, (
                f"Skill '{command_name}' opened an <output_format_schemas> "
                "block but lost its closing tag — the append must be inside "
                "the existing block, not after it."
            )


# Per-command phase name used to look up the canonical anchor field map in
# ``src/deviate/core/synthesis.py::PHASE_NARRATIVE_ANCHOR_FIELDS``. The
# command file name is ``deviate-<phase>``; the map key is ``<phase>``.
def _phase_key(command_name: str) -> str:
    return command_name.removeprefix("deviate-")


class TestCommandPromptNarrativeAnchors:
    """Slice A — per-phase narrative_anchor field guidance is present in each hook.

    Each of the 19 phase commands carries a `## Narrative Anchors (FLOW-11)`
    block right after its existing `## Handover Persistence (FLOW-11)` block.
    The block lists the phase-specific fields from
    ``src/deviate/core.synthesis.PHASE_NARRATIVE_ANCHOR_FIELDS`` so the
    actor knows which keys to populate on the YAML manifest's
    ``narrative_anchor:`` block.

    Canonical source: ``specs/plans/deviate-content.md:52-67`` § Narrative
    anchor field (extended to the 4 additional phases
    execute / hotfix / prune / review per AC-ADHOC-013 / Slice A scope).
    """

    @pytest.mark.parametrize("command_name", PHASE_COMMANDS)
    def test_command_has_narrative_anchor_block(self, command_name: str) -> None:
        """Each phase command carries the `## Narrative Anchors (FLOW-11)` heading."""
        path = resolve_command(command_name)
        text = path.read_text(encoding="utf-8")
        assert "## Narrative Anchors (FLOW-11)" in text, (
            f"Skill '{command_name}' at {path} is missing the "
            "'## Narrative Anchors (FLOW-11)' heading"
        )

    @pytest.mark.parametrize("command_name", PHASE_COMMANDS)
    def test_command_narrative_anchor_marker_is_idempotent(
        self, command_name: str
    ) -> None:
        """The deterministic marker `narrative_anchor_fields` appears exactly once.

        Re-running the append operation against an already-instrumented
        command must be a no-op. The contract requires `narrative_anchor_fields`
        to occur exactly once; duplicates indicate a non-idempotent append.
        Mirrors the contract for `handover_path()` at lines 226-233 above.
        """
        path = resolve_command(command_name)
        text = path.read_text(encoding="utf-8")
        marker_count = text.count("narrative_anchor_fields")
        assert marker_count == 1, (
            f"Skill '{command_name}' carries 'narrative_anchor_fields' "
            f"{marker_count} times; expected exactly one occurrence "
            "(idempotent append contract)."
        )

    @pytest.mark.parametrize("command_name", PHASE_COMMANDS)
    def test_command_block_references_canonical_source(self, command_name: str) -> None:
        """Each Narrative Anchors block references the canonical plan document."""
        path = resolve_command(command_name)
        text = path.read_text(encoding="utf-8")
        assert "specs/plans/deviate-content.md" in text, (
            f"Skill '{command_name}' Narrative Anchors block must reference "
            "specs/plans/deviate-content.md as the canonical source"
        )

    @pytest.mark.parametrize("command_name", PHASE_COMMANDS)
    def test_command_block_lives_inside_terminal_contract(
        self, command_name: str
    ) -> None:
        """The block sits inside the same terminal-contract section as Handover Persistence.

        Mirrors the contract enforced by ``test_command_instruction_lives_in_terminal_contract_section``
        for the Handover Persistence block: the Narrative Anchors block must
        share the terminal-contract wrapping so it stays adjacent to the
        YAML manifest schema it augments.
        """
        path = resolve_command(command_name)
        text = path.read_text(encoding="utf-8")
        section = _extract_terminal_section(text)
        assert section is not None, (
            f"Skill '{command_name}' is missing the terminal-contract section"
        )
        assert "## Narrative Anchors (FLOW-11)" in section, (
            f"Skill '{command_name}': '## Narrative Anchors (FLOW-11)' "
            "heading not located inside the terminal-contract section"
        )
        assert "narrative_anchor_fields" in section, (
            f"Skill '{command_name}': 'narrative_anchor_fields' marker not "
            "located inside the terminal-contract section"
        )

    @pytest.mark.parametrize("command_name", PHASE_COMMANDS)
    def test_command_block_lists_phase_specific_anchor_fields(
        self, command_name: str
    ) -> None:
        """Each block surfaces the anchor fields declared for its phase in PHASE_NARRATIVE_ANCHOR_FIELDS.

        Cross-references ``src/deviate.core.synthesis.PHASE_NARRATIVE_ANCHOR_FIELDS``
        so the prompts and the synthesis layer never drift: every anchor
        field the synthesis layer reads for a given phase must be named in
        that phase's hook, and vice versa.
        """
        from deviate.core.synthesis import PHASE_NARRATIVE_ANCHOR_FIELDS

        phase = _phase_key(command_name)
        expected_fields = PHASE_NARRATIVE_ANCHOR_FIELDS.get(phase)
        assert expected_fields is not None, (
            f"PHASE_NARRATIVE_ANCHOR_FIELDS has no entry for phase '{phase}' "
            f"(command '{command_name}'). Update the synthesis map AND this test together."
        )
        path = resolve_command(command_name)
        text = path.read_text(encoding="utf-8")
        for field in expected_fields:
            assert f"`{field}`" in text, (
                f"Skill '{command_name}' (phase '{phase}') is missing the "
                f"phase-specific anchor field '{field}' in its "
                "'## Narrative Anchors (FLOW-11)' block"
            )
