#!/usr/bin/env python3
"""validator.py — Plan State-Machine Invariant & Fuzzing Sensor.

Parses state machines embedded in plan Markdown or YAML files and enforces:
1. 2 <= len(states) <= 32 (Bounded state space)
2. Exactly 1 start state (start in states)
3. >= 1 terminal state (all terminals in states)
4. Transitions connect valid declared states (no ghost states)
5. Non-terminal states have at least one outgoing transition (no dead ends)
6. Terminal states have no outgoing transitions (terminal stability)
7. All declared states are reachable from start state
8. Fuzzes 100+ legal random paths from start to terminal (deadlock & cycle check)
"""

from __future__ import annotations

import random
import re
from pathlib import Path
from typing import Any


def extract_yaml_from_markdown(content: str) -> str:
    """Extract YAML code blocks that define states/transitions."""
    yaml_blocks = re.findall(r"```(?:yaml|yml)?\s*\n(.*?)\n```", content, re.DOTALL)
    for block in yaml_blocks:
        if "states:" in block and ("transitions:" in block or "start:" in block):
            return block
    return content


def simple_yaml_parse(text: str) -> dict[str, Any]:
    """Lightweight pure-python parser for state machine yaml structures."""
    try:
        import yaml
        res = yaml.safe_load(text)
        if isinstance(res, dict):
            return res
    except Exception:
        pass

    data: dict[str, Any] = {"states": [], "start": None, "terminals": [], "transitions": []}
    lines = text.splitlines()

    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        if stripped.startswith("states:"):
            val = stripped[len("states:") :].strip()
            if val.startswith("[") and val.endswith("]"):
                items = [x.strip() for x in val[1:-1].split(",") if x.strip()]
                data["states"].extend(items)
        elif stripped.startswith("start:"):
            data["start"] = stripped[len("start:") :].strip()
        elif stripped.startswith("terminals:"):
            val = stripped[len("terminals:") :].strip()
            if val.startswith("[") and val.endswith("]"):
                items = [x.strip() for x in val[1:-1].split(",") if x.strip()]
                data["terminals"].extend(items)
        elif "- { from:" in stripped or "- {from:" in stripped:
            m = re.search(r"from:\s*([A-Za-z0-9_-]+).*?to:\s*([A-Za-z0-9_-]+)", stripped)
            if m:
                data["transitions"].append({"from": m.group(1), "to": m.group(2)})

    return data


class PlanFuzzValidator:
    """Rigorous state machine invariant checker and stochastic path fuzzer."""

    def __init__(self, spec: dict[str, Any] | str | Path):
        if isinstance(spec, (str, Path)) and Path(spec).exists():
            content = Path(spec).read_text(encoding="utf-8")
            yaml_text = extract_yaml_from_markdown(content)
            self.data = simple_yaml_parse(yaml_text)
        elif isinstance(spec, str):
            yaml_text = extract_yaml_from_markdown(spec)
            self.data = simple_yaml_parse(yaml_text)
        elif isinstance(spec, dict):
            self.data = spec
        else:
            raise ValueError(f"Invalid state machine specification: {spec}")

        self.states = list(self.data.get("states", []))
        self.start = self.data.get("start")
        self.terminals = list(self.data.get("terminals", []))
        self.transitions = list(self.data.get("transitions", []))

    def validate_invariants(self) -> tuple[bool, list[str]]:
        """Validate all 7 formal state machine invariants."""
        errors = []

        # 1. State count
        if not (2 <= len(self.states) <= 32):
            errors.append(f"Invariant 1 violated: state count {len(self.states)} not in [2..32]")

        # 2. Single start state
        if not self.start:
            errors.append("Invariant 2 violated: start state is missing")
        elif self.start not in self.states:
            errors.append(f"Invariant 2 violated: start state '{self.start}' not in declared states")

        # 3. >= 1 terminal state
        if not self.terminals:
            errors.append("Invariant 3 violated: terminals list is empty")
        for t in self.terminals:
            if t not in self.states:
                errors.append(f"Invariant 3 violated: terminal state '{t}' not in declared states")

        # 4. Transitions connect valid states
        adj: dict[str, list[str]] = {s: [] for s in self.states}
        for tr in self.transitions:
            frm = tr.get("from")
            to = tr.get("to")
            if frm not in self.states:
                errors.append(f"Invariant 4 violated: transition from unknown state '{frm}'")
            if to not in self.states:
                errors.append(f"Invariant 4 violated: transition to unknown state '{to}'")
            if frm in adj and to:
                adj[frm].append(to)

        # 5. Non-terminal states must have at least one outgoing transition
        for s in self.states:
            if s not in self.terminals and not adj.get(s):
                errors.append(f"Invariant 5 violated: non-terminal state '{s}' has no outgoing transitions (deadlock)")

        # 6. Terminal states cannot leave terminal
        for t in self.terminals:
            if adj.get(t):
                errors.append(f"Invariant 6 violated: terminal state '{t}' has outgoing transitions (not terminal)")

        # 7. Reachability from start
        reachable = set()
        if self.start and self.start in self.states:
            queue = [self.start]
            reachable.add(self.start)
            while queue:
                curr = queue.pop(0)
                for nxt in adj.get(curr, []):
                    if nxt not in reachable:
                        reachable.add(nxt)
                        queue.append(nxt)

        for s in self.states:
            if s not in reachable:
                errors.append(f"Invariant 7 violated: state '{s}' is unreachable from start '{self.start}'")

        return len(errors) == 0, errors

    def fuzz_paths(self, trials: int = 100) -> tuple[bool, int, str]:
        """Fuzz random path walks to detect cycles and verify reaching terminals."""
        adj: dict[str, list[str]] = {s: [] for s in self.states}
        for tr in self.transitions:
            frm, to = tr.get("from"), tr.get("to")
            if frm in adj and to in self.states:
                adj[frm].append(to)

        completed_walks = 0
        max_steps = max(len(self.states) * 3, 20)

        for _ in range(trials):
            curr = self.start
            visited = [curr]
            steps = 0
            while curr not in self.terminals and steps < max_steps:
                neighbors = adj.get(curr, [])
                if not neighbors:
                    break
                curr = random.choice(neighbors)
                visited.append(curr)
                steps += 1

            if curr in self.terminals:
                completed_walks += 1
            else:
                return False, completed_walks, f"Fuzz path exceeded step limit without reaching terminal: {' -> '.join(visited)}"

        return True, completed_walks, f"Successfully fuzzed {completed_walks}/{trials} random walks to terminal."
