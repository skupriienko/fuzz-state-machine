---
name: fuzz-state-machine
type: Skill
description: Mandatory planning validator and execution sequence fuzzer. Enforces formal state machine invariants (2<=states<=32, single start, stable terminals, reachability, zero deadlocks) and stochastic path fuzzing on any multi-step AI plan. Generates Golden Execution Sequences.
version: 1.0.0
status: stable
tags:
  - plan-validation
  - state-machine
  - fuzzing
  - invariants
  - golden-sequences
  - planning-safety
disable-slash-command: false
---

# Skill: Fuzz State Machine Engine (Mandatory Planning Validator)

Validates state machines declared inside AI agent planning documents (`plan.md`, `tasks.md`, PRDs) using 7 formal mathematical invariants and 100+ random path fuzzing trials. Eliminates planning confabulation, unreachable states, and runaway recursive execution loops.

---

## 1. Mandatory Planning Invariant

Every planning step executed by an AI coding assistant **MUST** declare a compact state machine block and pass validation:

```yaml
states: [draft, review, approved]
start: draft
terminals: [approved]
transitions:
  - { from: draft, to: review }
  - { from: review, to: approved }
```

Validation command required before proceeding to implementation:
```bash
fsm-engine validate <path_to_plan.md>
```
Output must confirm: `PLAN_FUZZ:100/100 EXIT:0`.

---

## 2. The 7 Formal Invariants

1. **State count:** $2 \le N \le 32$ states (prevents state space explosion).
2. **Single start state:** Exactly 1 initial entry state.
3. **Valid terminals:** At least 1 absorbing terminal state.
4. **No ghost states:** Every transition connects declared states.
5. **No deadlocks:** Every non-terminal state has an outgoing transition.
6. **Terminal stability:** Terminal states have zero outgoing transitions.
7. **Reachability:** Every declared state is reachable from the start state.

---

## 3. CLI Usage

```bash
# 1. Validate a plan markdown file with 100 path fuzzing trials:
fsm-engine validate plan.md

# 2. Stress fuzz with 1,000 trials:
fsm-engine validate plan.md --trials 1000

# 3. Generate a golden execution sequence for an intent:
fsm-engine generate --intent investigation
fsm-engine generate --intent refactoring --mutate

# 4. View reliability benchmark:
fsm-engine benchmark
```
