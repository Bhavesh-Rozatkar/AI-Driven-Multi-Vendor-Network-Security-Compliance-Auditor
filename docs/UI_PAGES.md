# Multi-Page Prototype UI

## Page map

The prototype now uses separate pages instead of one large index screen:

1. `/login` — prototype administrator login.
2. `/connection` — pfSense SSH target configuration and connection capability check.
3. `/compliance` — benchmark PDF upload, multi-version inventory, control review, and activation.
4. `/assessment` — live assessment dashboard, metrics, evidence, findings, and remediation routing.
5. `/remediation` — AI remediation plan, safety validation, real execution approval, post-change verification, report download, and audit history.

## Prototype authentication

Credentials are intentionally hardcoded in `backend/app_factory.py`:

- Username: `admin`
- Password: `admin@123`

This exists only to visualize the authentication flow. It is not a production authentication design.

## Browser state

The prototype stores the current pfSense target, selected benchmark ID, assessment result, and selected finding in browser `localStorage` / `sessionStorage` so the separate pages can participate in one demonstration workflow.

## Workflow

```text
/login
   |
   v
/connection
   |
   v
/compliance
   |
   v
/assessment
   |
   v
/remediation
   |
   +--> audit history / report
```

## Important implementation boundary

The page split is a UI architecture change. The existing modular backend remains the source of truth for benchmark storage, compliance evaluation, device access, remediation safety, verification, audit logging, and PDF reporting.
