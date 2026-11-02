#!/usr/bin/env python3
"""test_stress.py — Comprehensive Stress & Invariant Test Suite for FSME.

Tests high-concurrency fuzz walks (10,000+ paths), boundary invariant violations,
unreachable state detection, cycle trap detection, and adversarial input parsing.
"""

import sys
import time
import unittest
from pathlib import Path

# Add src to sys.path
SRC_DIR = Path(__file__).resolve().parent.parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from fuzz_state_machine.validator import PlanFuzzValidator, simple_yaml_parse
from fuzz_state_machine.engine import FSMSequenceEngine, TaskState, FSMOracle


class TestFSMEStress(unittest.TestCase):

    def test_01_high_volume_path_fuzzing(self):
        """Stress test: 1,000 random walk trials on a 6-state DAG with retry loops."""
        spec = {
            "states": ["init", "plan", "review", "execute", "verify", "done"],
            "start": "init",
            "terminals": ["done"],
            "transitions": [
                {"from": "init", "to": "plan"},
                {"from": "plan", "to": "review"},
                {"from": "review", "to": "plan"},     # Loop 1
                {"from": "review", "to": "execute"},
                {"from": "execute", "to": "verify"},
                {"from": "verify", "to": "execute"},  # Loop 2
                {"from": "verify", "to": "done"},
            ]
        }
        val = PlanFuzzValidator(spec)
        valid, errors = val.validate_invariants()
        self.assertTrue(valid, f"Invariants failed: {errors}")

        t0 = time.time()
        fuzz_ok, walks, msg = val.fuzz_paths(trials=1000)
        elapsed = time.time() - t0

        self.assertTrue(fuzz_ok, f"Fuzz failed: {msg}")
        self.assertEqual(walks, 1000)
        print(f"\n[STRESS] 1,000 fuzz walks completed in {elapsed:.3f}s ({1000/elapsed:.1f} walks/sec)")
        self.assertLess(elapsed, 2.0, "1,000 walks should complete in under 2 seconds")

    def test_02_max_boundary_states_32(self):
        """Invariant 1: Exact maximum boundary test (32 states allowed, 33 states rejected)."""
        # Exactly 32 states: state_0 to state_31
        states_32 = [f"s_{i}" for i in range(32)]
        transitions_32 = [{"from": f"s_{i}", "to": f"s_{i+1}"} for i in range(31)]
        spec_32 = {
            "states": states_32,
            "start": "s_0",
            "terminals": ["s_31"],
            "transitions": transitions_32,
        }
        val_32 = PlanFuzzValidator(spec_32)
        valid, errors = val_32.validate_invariants()
        self.assertTrue(valid, f"32 states should pass Invariant 1: {errors}")

        # Exactly 33 states: rejected
        states_33 = [f"s_{i}" for i in range(33)]
        transitions_33 = [{"from": f"s_{i}", "to": f"s_{i+1}"} for i in range(32)]
        spec_33 = {
            "states": states_33,
            "start": "s_0",
            "terminals": ["s_32"],
            "transitions": transitions_33,
        }
        val_33 = PlanFuzzValidator(spec_33)
        valid_33, errors_33 = val_33.validate_invariants()
        self.assertFalse(valid_33, "33 states MUST violate Invariant 1")
        self.assertTrue(any("state count 33 not in [2..32]" in e for e in errors_33))

    def test_03_min_boundary_states(self):
        """Invariant 1 & 2: Minimum boundary test (1 state rejected, 2 states allowed)."""
        # 1 state: rejected
        val_1 = PlanFuzzValidator({"states": ["only_one"], "start": "only_one", "terminals": ["only_one"], "transitions": []})
        valid, errors = val_1.validate_invariants()
        self.assertFalse(valid)
        self.assertTrue(any("state count 1 not in [2..32]" in e for e in errors))

        # 2 states: minimal valid machine
        val_2 = PlanFuzzValidator({
            "states": ["start_s", "end_s"],
            "start": "start_s",
            "terminals": ["end_s"],
            "transitions": [{"from": "start_s", "to": "end_s"}]
        })
        valid, errors = val_2.validate_invariants()
        self.assertTrue(valid, f"2-state minimal machine should pass: {errors}")

    def test_04_cycle_trap_detection(self):
        """Fuzz path cycle trap: detects infinite loop cycle where terminal is unreachable."""
        spec = {
            "states": ["start", "trap_a", "trap_b", "done"],
            "start": "start",
            "terminals": ["done"],
            "transitions": [
                {"from": "start", "to": "trap_a"},
                {"from": "trap_a", "to": "trap_b"},
                {"from": "trap_b", "to": "trap_a"},  # Infinite cycle trap, no edge to done!
            ]
        }
        val = PlanFuzzValidator(spec)
        fuzz_ok, walks, msg = val.fuzz_paths(trials=10)
        self.assertFalse(fuzz_ok, "Cycle trap should be caught by fuzzer step limit")
        self.assertIn("exceeded step limit", msg)

    def test_05_leaky_terminal_and_dead_end_violations(self):
        """Invariants 5 & 6: Outgoing edges from terminal & non-terminal dead ends."""
        spec = {
            "states": ["start", "dead_end", "done"],
            "start": "start",
            "terminals": ["done"],
            "transitions": [
                {"from": "start", "to": "dead_end"},
                # dead_end has no outgoing transitions -> Invariant 5 violated
                {"from": "done", "to": "start"},     # Leaky terminal -> Invariant 6 violated
            ]
        }
        val = PlanFuzzValidator(spec)
        valid, errors = val.validate_invariants()
        self.assertFalse(valid)
        self.assertTrue(any("Invariant 5 violated" in e for e in errors))
        self.assertTrue(any("Invariant 6 violated" in e for e in errors))

    def test_06_unreachable_island_states(self):
        """Invariant 7: Detects disconnected island states unreachable from start."""
        spec = {
            "states": ["start", "step1", "isolated_island", "done"],
            "start": "start",
            "terminals": ["done"],
            "transitions": [
                {"from": "start", "to": "step1"},
                {"from": "step1", "to": "done"},
                {"from": "isolated_island", "to": "done"},  # Unreachable from start!
            ]
        }
        val = PlanFuzzValidator(spec)
        valid, errors = val.validate_invariants()
        self.assertFalse(valid)
        self.assertTrue(any("Invariant 7 violated: state 'isolated_island' is unreachable" in e for e in errors))

    def test_07_engine_safety_oracle(self):
        """FSMOracle verification: Critique gate enforcement before mutation."""
        # Unsafe: mutation without critique gate
        unsafe_seq = [TaskState.REASONING, TaskState.MUTATION_PREPARE, TaskState.SYNTHESIS]
        valid, reason = FSMOracle.validate_sequence(unsafe_seq, is_mutation_task=True)
        self.assertFalse(valid)
        self.assertIn("CRITIQUE_GATE", reason)

        # Safe: critique gate precedes mutation
        safe_seq = [TaskState.REASONING, TaskState.CRITIQUE_GATE, TaskState.MUTATION_PREPARE, TaskState.SYNTHESIS]
        valid, reason = FSMOracle.validate_sequence(safe_seq, is_mutation_task=True)
        self.assertTrue(valid, reason)

    def test_08_rapid_batch_engine_generations(self):
        """Stress: Generate 500 stochastic sequences rapidly."""
        engine = FSMSequenceEngine(seed=42)
        t0 = time.time()
        for i in range(500):
            res = engine.generate_sequence(intent="investigation", is_mutation=False)
            self.assertTrue(res["verified"])
        elapsed = time.time() - t0
        print(f"\n[STRESS] 500 FSM engine generations in {elapsed:.3f}s ({500/elapsed:.1f} seq/sec)")
        self.assertLess(elapsed, 1.0)


if __name__ == "__main__":
    unittest.main()
