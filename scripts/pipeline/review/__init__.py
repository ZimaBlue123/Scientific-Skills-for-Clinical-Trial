"""Review stage: document diffing, cross-reference auditing, and consistency checks."""

from .hybrid_diff import generate_numbered_diff

__all__ = ["generate_numbered_diff"]
