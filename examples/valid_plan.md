# Valid Feature Implementation Plan

## State Machine
```yaml
states: [draft, spec_review, test_locked, implementation, security_audit, completed]
start: draft
terminals: [completed]
transitions:
  - { from: draft, to: spec_review }
  - { from: spec_review, to: test_locked }
  - { from: test_locked, to: implementation }
  - { from: implementation, to: security_audit }
  - { from: security_audit, to: completed }
  - { from: security_audit, to: implementation }
```

## Plan Steps
1. Draft specification and blast radius.
2. Review contract and acceptance criteria.
3. Lock characterization tests.
4. Implement code.
5. Run automated security audit.
6. Complete delivery.
