# Security & Operational Notes

## Credentials

Never commit SSH passwords, private keys, API keys, or session secrets. Use environment variables or an appropriate secret-management mechanism.

## Uploaded benchmarks

Benchmark PDFs are application inputs. Validate file type and size, store them in a controlled directory, and do not execute file contents.

## AI input

Do not send unnecessary secrets or unrelated device credentials to an external AI provider. Minimize the configuration context sent for semantic analysis and remediation.

## AI output

AI output is untrusted input. Parse and validate structured output before using it anywhere in the remediation path.

## SSH commands

Never construct an unrestricted shell command by blindly concatenating AI text. Commands should be represented structurally and validated before execution.

## Audit logs

Audit logs should contain enough information to trace actions without unnecessarily storing credentials or other secrets.

## Network exposure

Do not expose the Flask development server directly to an untrusted network. Use network controls and an appropriate production server for any deployment beyond local testing.
