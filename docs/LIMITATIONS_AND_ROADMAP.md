# Limitations & Roadmap

## Current limitations

- The live pfSense VM is external to this development environment and cannot be reached from here.
- The repository does not fabricate the CIS pfSense benchmark controls.
- Benchmark extraction from complex PDFs may require further OCR/table-aware extraction.
- Deterministic PASS/FAIL requires sufficiently structured control evidence.
- Real remediation must be validated on the user's VM before operational use.
- The current UI is a prototype and should be hardened before deployment.

## Near-term work

- Test the SSH adapter against the actual pfSense VM.
- Upload and review the real CIS pfSense benchmark PDF.
- Build deterministic checks for the selected benchmark controls.
- Expand the remediation safety policy.
- Improve administrator approval and change preview UX.
- Add stronger post-change health checks.

## Longer-term work

- More vendor adapters.
- More benchmark families.
- Richer vendor-neutral security representation.
- Stronger policy/dependency analysis.
- More robust rollback workflows.
- Enterprise authentication and authorization.
- Persistent database-backed audit storage.
- Production-grade secret management.
- Distributed device orchestration.
