# Documentation Index

This directory contains the project documentation for the modular Network Compliance & Remediation Prototype.

## Core documents

- [Prototype Guide](PROTOTYPE_GUIDE.md) — one file containing a short explanation and a detailed developer-oriented explanation of the whole prototype.
- [Architecture](ARCHITECTURE.md) — module boundaries, data flow, and extension model.
- [Developer Guide](DEVELOPER_GUIDE.md) — how to set up, run, test, extend, and debug the project.
- [API Reference](API_REFERENCE.md) — HTTP endpoints, inputs, outputs, and integration contracts.
- [Benchmark Workflow](BENCHMARK_WORKFLOW.md) — PDF upload, AI extraction, review, activation, versioning, and benchmark use.
- [Device & SSH Guide](DEVICE_SSH_GUIDE.md) — pfSense connection flow, capability checks, collection, and live-device requirements.
- [Remediation Safety](REMEDIATION_SAFETY.md) — remediation AI, safety validation, approval, backup, execution, rollback boundaries, and verification.
- [Testing Guide](TESTING.md) — automated tests, demo testing, and live pfSense validation.
- [Security & Operational Notes](SECURITY.md) — credentials, secrets, logging, uploads, and safe operation.
- [Extension Guide](EXTENSION_GUIDE.md) — adding vendors, benchmarks, controls, AI providers, and UI modules.
- [Troubleshooting](TROUBLESHOOTING.md) — common setup and runtime problems.
- [Limitations & Roadmap](LIMITATIONS_AND_ROADMAP.md) — what is implemented, what requires live infrastructure, and what remains intentionally incomplete.
- [Contribution Guide](CONTRIBUTING.md) — modular development and collaboration conventions.
- [Change Log](CHANGELOG.md) — project-level changes in this prototype iteration.

## Scope

The current prototype is centered on **pfSense Firewall + uploaded CIS benchmark PDFs**, while retaining the existing Cisco implementation as a secondary/legacy path. The architecture is deliberately modular so additional vendors and benchmarks can be added without rewriting the core orchestration layer.
