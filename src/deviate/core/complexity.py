from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ClassificationResult:
    level: str
    execution_mode: str


class ComplexityGate:
    _STUB_MAP = {
        "LOW": ClassificationResult(level="LOW", execution_mode="DIRECT"),
        "MEDIUM": ClassificationResult(level="MEDIUM", execution_mode="DIRECT"),
        "HIGH": ClassificationResult(level="HIGH", execution_mode="TDD"),
    }

    @classmethod
    def classify(
        cls,
        description: str,
        _stub: str | None = None,
    ) -> ClassificationResult:
        if _stub is not None:
            if _stub not in cls._STUB_MAP:
                raise ValueError(f"Unknown stub value: {_stub}")
            return cls._STUB_MAP[_stub]

        return cls._STUB_MAP["LOW"]
