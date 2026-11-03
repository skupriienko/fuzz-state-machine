#!/usr/bin/env python3
"""engine.py — Fuzz State Machine Engine (FSME) for AI Execution Sequences.

Generates state sequences, enforces safety and progress invariants,
and generates Golden State sequences for agent planning.
"""

from __future__ import annotations

import random
from enum import StrEnum
from typing import Any


class TaskState(StrEnum):
    IDLE = "STATE_IDLE"
    REASONING = "STATE_REASONING"
    DOC_RESOLUTION = "STATE_DOC_RESOLUTION"
    SANDBOX_COMPUTE = "STATE_SANDBOX_COMPUTE"
    CRITIQUE_GATE = "STATE_CRITIQUE_GATE"
    MUTATION_PREPARE = "STATE_MUTATION_PREPARE"
    MEMORY_PERSIST = "STATE_MEMORY_PERSIST"
    SYNTHESIS = "STATE_SYNTHESIS"


VALID_TRANSITIONS: dict[TaskState, list[TaskState]] = {
    TaskState.IDLE: [TaskState.REASONING, TaskState.DOC_RESOLUTION, TaskState.SANDBOX_COMPUTE],
    TaskState.REASONING: [
        TaskState.DOC_RESOLUTION,
        TaskState.SANDBOX_COMPUTE,
        TaskState.CRITIQUE_GATE,
    ],
    TaskState.DOC_RESOLUTION: [TaskState.SANDBOX_COMPUTE, TaskState.REASONING, TaskState.SYNTHESIS],
    TaskState.SANDBOX_COMPUTE: [
        TaskState.CRITIQUE_GATE,
        TaskState.SYNTHESIS,
        TaskState.DOC_RESOLUTION,
    ],
    TaskState.CRITIQUE_GATE: [TaskState.MUTATION_PREPARE, TaskState.SYNTHESIS, TaskState.REASONING],
    TaskState.MUTATION_PREPARE: [TaskState.MEMORY_PERSIST, TaskState.SYNTHESIS],
    TaskState.MEMORY_PERSIST: [TaskState.SYNTHESIS],
    TaskState.SYNTHESIS: [],
}


class FSMOracle:
    """Verifies that a state sequence conforms to safety and progress invariants."""

    @staticmethod
    def validate_sequence(
        sequence: list[TaskState], is_mutation_task: bool = False
    ) -> tuple[bool, str]:
        if not sequence:
            return False, "Sequence cannot be empty"

        # Rule 1: Mutation must ALWAYS be preceded by CRITIQUE_GATE
        if TaskState.MUTATION_PREPARE in sequence:
            mut_idx = sequence.index(TaskState.MUTATION_PREPARE)
            crit_idx = [i for i, s in enumerate(sequence) if s == TaskState.CRITIQUE_GATE]
            if not crit_idx or not any(c < mut_idx for c in crit_idx):
                return False, "Safety Violation: MUTATION_PREPARE without prior CRITIQUE_GATE"

        # Rule 2: Non-mutation tasks should not enter MUTATION_PREPARE
        if not is_mutation_task and TaskState.MUTATION_PREPARE in sequence:
            return False, "Scope Violation: Read-only task entered MUTATION_PREPARE"

        # Rule 3: Must terminate at SYNTHESIS
        if sequence[-1] != TaskState.SYNTHESIS:
            return False, f"Sequence does not terminate at SYNTHESIS (ends with {sequence[-1]})"

        # Rule 4: Maximum sequence length limit
        if len(sequence) > 10:
            return False, f"Runaway loop detected: sequence length {len(sequence)} > 10"

        return True, "VALID_SEQUENCE"


class FSMSequenceEngine:
    """Stochastic generator and golden sequence evaluator."""

    def __init__(self, seed: int | None = None):
        if seed is not None:
            random.seed(seed)

    def generate_sequence(
        self, intent: str = "investigation", is_mutation: bool = False, max_fuzz_attempts: int = 50
    ) -> dict[str, Any]:
        """Fuzz a valid state sequence matching the requested intent."""
        # Fast path: Golden sequences
        if intent == "docs_lookup":
            states = [TaskState.DOC_RESOLUTION, TaskState.SANDBOX_COMPUTE, TaskState.SYNTHESIS]
            return {
                "intent": intent,
                "sequence": [s.value for s in states],
                "status": "GOLDEN_SEQUENCE",
                "verified": True,
            }
        elif intent == "refactoring":
            states = [
                TaskState.REASONING,
                TaskState.SANDBOX_COMPUTE,
                TaskState.CRITIQUE_GATE,
                TaskState.MUTATION_PREPARE,
                TaskState.SYNTHESIS,
            ]
            return {
                "intent": intent,
                "sequence": [s.value for s in states],
                "status": "GOLDEN_SEQUENCE",
                "verified": True,
            }

        # Stochastic Fuzzing
        for attempt in range(1, max_fuzz_attempts + 1):
            curr = random.choice([TaskState.REASONING, TaskState.DOC_RESOLUTION])
            seq = [curr]
            while curr != TaskState.SYNTHESIS and len(seq) < 8:
                choices = VALID_TRANSITIONS.get(curr, [])
                if not choices:
                    break
                filtered = (
                    [c for c in choices if c != TaskState.MUTATION_PREPARE]
                    if not is_mutation
                    else choices
                )
                curr = random.choice(filtered or choices)
                seq.append(curr)

            valid, _reason = FSMOracle.validate_sequence(seq, is_mutation_task=is_mutation)
            if valid:
                return {
                    "intent": intent,
                    "sequence": [s.value for s in seq],
                    "status": "FUZZ_VALIDATED",
                    "attempts": attempt,
                    "verified": True,
                }

        fallback = [
            TaskState.REASONING,
            TaskState.SANDBOX_COMPUTE,
            TaskState.CRITIQUE_GATE,
            TaskState.SYNTHESIS,
        ]
        return {
            "intent": intent,
            "sequence": [s.value for s in fallback],
            "status": "FALLBACK_SEQUENCE",
            "attempts": max_fuzz_attempts,
            "verified": True,
        }
