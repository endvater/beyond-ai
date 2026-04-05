"""Shared confidence primitives for Beyond AI."""

from enum import StrEnum


class ConfidenceLevel(StrEnum):
    """Small shared confidence scale for model, retrieval and correlation signals."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

    @property
    def rank(self) -> int:
        return {
            ConfidenceLevel.LOW: 0,
            ConfidenceLevel.MEDIUM: 1,
            ConfidenceLevel.HIGH: 2,
        }[self]

    def at_least(self, minimum: "ConfidenceLevel") -> bool:
        return self.rank >= minimum.rank

    @classmethod
    def from_score(cls, score: float) -> "ConfidenceLevel":
        if not 0.0 <= score <= 1.0:
            raise ValueError("score must be between 0.0 and 1.0")
        if score >= 0.85:
            return cls.HIGH
        if score >= 0.60:
            return cls.MEDIUM
        return cls.LOW


__all__ = ["ConfidenceLevel"]
