# Device & SSH Guide

## Current target

The primary live target is pfSense Firewall accessed over SSH.

## Connection flow

```text
Connection details
      ↓
SSH adapter
      ↓
Capability check
      ↓
Collect configuration
      ↓
Normalize
```

## Capability check

The application should check capability before attempting remediation. The exact checks depend on what the adapter requires, but the design is intended to distinguish connection/read/write/command capability rather than assuming all permissions exist.

## Live-device testing

The development sandbox cannot reach the user's private pfSense VM. Therefore the live SSH path, backup operation, and real command execution must be tested on the user's controlled VM.

## Credentials

Do not hard-code passwords or private keys. Do not commit them to Git. Prefer short-lived or appropriately scoped credentials and a dedicated testing account.

## Real execution

The remediation path is intentionally gated by safety validation and administrator approval. Do not bypass those controls for convenience during development.
