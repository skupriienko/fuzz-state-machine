"""Fuzz State Machine Engine (FSME) — Deterministic Invariant Fuzzing & Planning Validator.

Validates plan state machines, generates Golden Execution Sequences, and eliminates
AI agent planning hallucinations and runaway loops via stochastic path fuzzing.
"""

__version__ = "1.0.0"
__all__ = ["PlanFuzzValidator", "FSMSequenceEngine", "TaskState", "FSMOracle"]

from .validator import PlanFuzzValidator
from .engine import FSMSequenceEngine, TaskState, FSMOracle
