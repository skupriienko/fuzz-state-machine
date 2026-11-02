# Mandatory Plan State-Machine & Fuzz Invariant (Kilo Code)

Before presenting or executing any non-trivial multi-step plan:
1. Every plan MUST declare a formal state machine block (states, start, terminals, transitions):
   ```yaml
   states: [draft, review, approved]
   start: draft
   terminals: [approved]
   transitions:
     - { from: draft, to: review }
     - { from: review, to: approved }
   ```
2. Validate with: `fsm-engine validate <path_to_plan.md>`
3. Enforcement: Only plans passing `PLAN_FUZZ:100/100 EXIT:0` (0 deadlocks, 0 ghost states, terminal reachability verified) are permitted for execution.
