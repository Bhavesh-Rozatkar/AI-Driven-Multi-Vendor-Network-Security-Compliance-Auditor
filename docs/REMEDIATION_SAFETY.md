# Remediation Safety

## Control boundary

The remediation architecture is:

```text
Finding
  ↓
Remediation AI
  ↓
Structured remediation proposal
  ↓
Safety Validator
  ↓
Administrator approval
  ↓
Backup/checkpoint
  ↓
Execution
  ↓
Verification
```

## AI behavior

The remediation AI is not an execution engine. It proposes a structured plan. It must return `MANUAL_REVIEW` when it cannot establish a safe remediation.

## Safety validator

The validator should reject proposals that are malformed, empty, unsupported, or incompatible with the current capability state. It should not silently transform unsafe commands into different commands.

## Administrator approval

Approval is a mandatory human gate before a real change.

## Backup

A configuration backup/checkpoint should be created before a real configuration change where the device adapter supports it.

## Verification

Execution success is not equivalent to compliance success. The system must recollect the state and rerun the relevant checks.

## Failure handling

If validation fails, stop.

If the administrator rejects the proposal, stop.

If backup fails, stop unless an explicitly designed policy permits another safe recovery path.

If execution fails, record the failure and do not report the change as successful.

If verification fails, report the actual post-change state and require follow-up rather than claiming compliance.
