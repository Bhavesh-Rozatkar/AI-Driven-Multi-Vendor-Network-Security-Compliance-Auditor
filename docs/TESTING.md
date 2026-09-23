# Testing Guide

## Automated tests

Run:

```bash
pytest -q
```

Tests should cover:

- module imports and boundaries;
- benchmark storage;
- benchmark extraction fallback;
- deterministic compliance behavior;
- AI failure fallback;
- remediation validation;
- API behavior;
- reporting;
- audit logging.

## Live pfSense test sequence

Use a dedicated test VM or snapshot before testing real remediation.

1. Confirm SSH access manually.
2. Run `/devices/capability-check`.
3. Collect configuration without changing anything.
4. Upload the benchmark PDF.
5. Review and activate controls.
6. Run `/audit/live`.
7. Select one controlled failing finding.
8. Generate a remediation proposal.
9. Run safety validation.
10. Review the exact proposed change.
11. Approve it.
12. Confirm backup/checkpoint exists.
13. Execute.
14. Run verification.
15. Confirm the final compliance result reflects the actual device state.
16. Inspect audit history and the generated report.

## Do not use production first

The prototype performs real configuration changes. Validate it against a disposable or isolated VM before any production use.
