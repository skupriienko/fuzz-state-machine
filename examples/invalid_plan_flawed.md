# Flawed Plan with Deadlocks and Ghost States (Negative Example)

## State Machine
```yaml
states: [draft, review, dead_end_state, done]
start: draft
terminals: [done]
transitions:
  - { from: draft, to: review }
  - { from: review, to: ghost_state }
  - { from: draft, to: dead_end_state }
  - { from: done, to: draft }
```
