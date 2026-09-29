# Architecture

## 1. Architectural goal

The prototype is an AI-assisted, vendor-neutral compliance and controlled remediation platform. The implementation target is currently pfSense Firewall + uploaded CIS benchmark PDFs, while the module boundaries are designed for additional vendors and benchmarks.

## 2. Logical architecture

```text
                           Web UI / API Client
                                  |
                                  v
                         +-------------------+
                         |    API Layer      |
                         +---------+---------+
                                   |
          +------------------------+-------------------------+
          |                        |                         |
          v                        v                         v
   +-------------+          +-------------+           +-------------+
   |   Device    |          | Compliance  |           | Intelligence |
   |   Module    |          |   Module    |           |    Module    |
   +------+------+          +------+------+           +------+------+ 
          |                        |                         |
          v                        v                         v
   Device Adapter          Benchmark + Rules        Semantic / Remed.
          |                        |                         |
          +------------------------+-------------------------+
                                   |
                                   v
                            +--------------+
                            | Remediation  |
                            | + Safety     |
                            +------+-------+
                                   |
                                   v
                              Admin Approval
                                   |
                                   v
                             Device Execution
                                   |
                                   v
                             Verification
                                   |
                                   v
                                Audit
                                   |
                                   v
                               Reporting
```

## 3. Module responsibilities

| Module | Responsibility | Must not own |
|---|---|---|
| `device` | Connect, capability checks, collect state, execute device-specific operations | CIS policy logic |
| `parsing` | Parse and normalize device information | Remediation approval |
| `compliance` | Load benchmark controls and evaluate evidence | SSH implementation |
| `intelligence` | Semantic interpretation and remediation proposals | Direct command execution |
| `remediation` | Safety validation, approval boundary, backup, execution orchestration | Benchmark extraction |
| `verification` | Recollect state and re-evaluate after changes | AI prompt design |
| `audit` | Record traceable events | Device parsing |
| `reporting` | Turn structured results into reports | Device execution |
| `api` | Expose stable application operations | Business logic duplication |
| `shared` | Contracts and common models | Vendor-specific behavior |

## 4. Data flow

```text
Benchmark PDF
    -> extraction
    -> review
    -> activation
    -> benchmark store

pfSense
    -> SSH capability check
    -> live configuration
    -> parsing/normalization
    -> compliance engine
    -> findings
    -> remediation AI
    -> safety validator
    -> administrator approval
    -> backup
    -> execution
    -> verification
    -> audit/report
```

## 5. Design principles

- Prefer deterministic compliance decisions where the benchmark can be expressed deterministically.
- Treat AI as an assisting layer, not an unrestricted executor.
- Make uncertainty explicit.
- Keep benchmark data separate from application code.
- Keep device-specific behavior inside adapters.
- Use shared contracts for module boundaries.
- Fail closed for real remediation when safety or confidence requirements are not met.
- Preserve evidence and auditability.

## Multi-page UI architecture

The frontend is now split by analyst task rather than rendered as a single index page:

- `login.html` — authentication entry point.
- `connection.html` — device onboarding and SSH capability validation.
- `compliance.html` — benchmark ingestion, review, and activation.
- `assessment.html` — live assessment and findings.
- `remediation.html` — remediation, safety, execution, verification, audit, and report actions.

The pages share `static/app.css` and `static/app.js`. Browser storage carries prototype workflow state between pages. The backend modules remain independently usable and are not coupled to a particular page.
