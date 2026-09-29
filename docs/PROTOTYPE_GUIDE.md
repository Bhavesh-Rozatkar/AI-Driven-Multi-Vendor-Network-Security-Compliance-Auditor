# Prototype Guide — Simple + Detailed

## Part I — Short version

### What this prototype is

This prototype is a modular network security compliance platform. It connects to a live network device, reads its current configuration, checks that configuration against an administrator-selected security benchmark, explains failed controls, proposes remediation, validates the proposed change, asks the administrator for approval, pushes the approved change, and checks the device again.

For the current prototype, the main target is a **pfSense firewall** and the benchmark is provided by the administrator as a **PDF upload**. Multiple benchmark PDFs and versions can be stored at the same time.

### Main flow

```text
Upload Benchmark PDF
        ↓
Extract Controls
        ↓
Administrator Reviews Controls
        ↓
Activate Benchmark
        ↓
Connect to pfSense over SSH
        ↓
Capability Check
        ↓
Collect Live Configuration
        ↓
Normalize Configuration
        ↓
Run CIS / Benchmark Checks
        ↓
Find PASS / FAIL / UNCERTAIN
        ↓
Explain Finding
        ↓
Remediation AI
        ↓
Safety Validator
        ↓
Administrator Approval
        ↓
Configuration Backup
        ↓
Push Approved Change
        ↓
Collect New State
        ↓
Re-check Compliance + Health
        ↓
Audit + Report
```

### Two AI layers

There are intentionally two separate AI responsibilities:

1. **Semantic AI** — helps understand ambiguous or unfamiliar configuration information. It is not the authority for deterministic compliance PASS/FAIL decisions.
2. **Remediation AI** — receives a specific finding and current device context and proposes a remediation plan/commands. If it cannot establish a safe remediation, it returns `MANUAL_REVIEW` instead of inventing an executable change.

### What makes the architecture modular

The application is divided into independent modules:

- `device` — talks to devices.
- `parsing` — converts device data into normalized information.
- `compliance` — evaluates benchmark controls.
- `intelligence` — semantic and remediation AI.
- `remediation` — validates, approves, backs up, and executes changes.
- `verification` — checks the device after a change.
- `audit` — records important events.
- `reporting` — creates reports.
- `api` — connects modules to the UI or other clients.
- `shared` — stable models and contracts between modules.

A developer can work on one module without needing to understand the internals of the others.

### Important truth about the current build

The project does **not invent CIS controls**. The benchmark PDF is the source input. For the supplied CIS pfSense v1.1.0 document, the parser identifies 33 recommendations and preserves their CIS assessment status; the supplied recommendations are marked Manual in the benchmark. Manual controls without an explicitly reviewed deterministic check remain `UNCERTAIN` rather than being guessed.

The live pfSense VM is external to this development environment. The SSH adapter is implemented, but live connection, backup, and real command execution must be tested against the user's actual VM before production-like use.

---

# Part II — Detailed developer explanation

## 1. What we are building

The project is a proof-of-concept for an AI-assisted, vendor-neutral network compliance and controlled remediation platform. The final concept is broader than the prototype, but the prototype deliberately narrows the implementation to pfSense as the live device target and uploaded CIS benchmark documents as the compliance source.

The important architectural idea is that **device-specific behavior is isolated from benchmark logic**. pfSense is handled by a device adapter. The compliance engine works on normalized information and benchmark controls. Remediation is handled by a separate service. This prevents the application from becoming one large vendor-specific script.

## 2. End-to-end lifecycle

### Stage A — Benchmark onboarding

The administrator uploads a benchmark PDF. For CIS-style PDFs, the server first performs page-aware structural extraction of recommendation IDs, titles, assessment status, profile, description, rationale, audit procedure, remediation procedure, defaults, references, and source pages. AI is optional and is used only to enrich already identified controls; it cannot create, merge, rename, or activate controls. The result is explicitly marked for review.

The administrator can review, edit, select, and activate controls. Multiple benchmark versions can remain stored simultaneously. The activated benchmark is then referenced by its benchmark ID when an assessment is started.

The system intentionally does not treat AI extraction as authoritative. The review step exists because a benchmark document is a compliance source and extraction errors must not silently become executable policy.

### Stage B — Device onboarding and capability checking

The administrator supplies connection information such as host, SSH port, username, and authentication information. The pfSense adapter establishes an SSH session and performs a capability check before an assessment or remediation.

The capability check is intended to answer practical questions such as whether the device can be reached, whether configuration can be read, whether required commands are available, and whether the session has the permissions needed for later operations.

A failed capability check should stop the workflow rather than allowing the application to assume that execution will work.

### Stage C — Configuration collection

The pfSense adapter retrieves the relevant live configuration. The collected state is passed into the parsing/normalization layer.

The objective is to move from:

```text
Vendor-specific raw device state
```

to:

```text
Common normalized security state
```

The compliance engine should not need to know how SSH was implemented or where the raw configuration came from.

### Stage D — Compliance evaluation

The compliance engine loads the selected benchmark controls and evaluates them against the normalized configuration.

Each control should produce a result such as:

```text
PASS
FAIL
UNCERTAIN
NOT_APPLICABLE
```

The result should include evidence and enough context for an administrator to understand why the decision was made.

Deterministic checks are preferred for authoritative compliance results. AI may assist with interpretation, but it should not silently replace the benchmark logic.

### Stage E — Semantic AI

The first AI layer is the semantic layer. Its purpose is understanding rather than direct configuration execution.

It can help with:

- unfamiliar syntax;
- ambiguous configuration;
- semantic interpretation;
- security meaning;
- candidate mappings to normalized concepts.

If the AI provider is unavailable, the application should continue using the deterministic path wherever possible. AI failure must not cause the entire compliance application to fail.

### Stage F — Remediation AI

The second AI layer is intentionally separate.

It receives a specific finding, the current device state, the benchmark control, and relevant context. It produces a structured remediation proposal rather than a free-form instruction to execute arbitrary text.

The remediation AI should distinguish between situations it can confidently remediate and situations requiring manual review.

When confidence is insufficient, the expected behavior is:

```text
MANUAL_REVIEW
```

The system must not convert uncertainty into an executable configuration change.

### Stage G — Safety validation

The safety validator sits between remediation generation and execution.

The intended control boundary is:

```text
AI proposal
    ↓
Safety validation
    ↓
Administrator approval
    ↓
Backup/checkpoint
    ↓
Execution
```

The safety validator is not the same thing as AI confidence. It is a separate engineering control.

The validator should check the structure of the proposed commands, execution capability, and known safety constraints. It should reject malformed, empty, unsupported, or otherwise unsafe proposals rather than attempting to repair them automatically.

### Stage H — Administrator approval

Even a valid remediation proposal does not execute automatically. The administrator must be able to see what is going to happen and explicitly approve it.

This creates a human control point before a real firewall configuration is changed.

### Stage I — Backup and execution

After approval, the remediation service can create a configuration backup/checkpoint before the change and then execute the validated operation through the pfSense adapter.

The execution layer should remain device-aware. The remediation AI does not need to know how an SSH session is opened. It only supplies the structured remediation plan; the device adapter is responsible for the actual device interaction.

### Stage J — Verification

A successful SSH command is not enough to declare remediation successful.

The system retrieves the new state and performs verification. Verification should include the relevant compliance check and, where possible, a basic operational/health check.

The desired result is:

```text
Before: FAIL
Change: approved and executed
After:  PASS
Device: operational
```

If the change executes but the control remains failed, the system should report that fact instead of claiming success.

### Stage K — Audit and reporting

Important events are recorded so the system can explain what happened later.

An audit record should connect:

```text
Device
Benchmark
Finding
Remediation proposal
Safety decision
Administrator approval
Backup
Execution result
Verification result
Final compliance state
```

The reporting module converts the collected result into a human-readable compliance/remediation report.

## 3. How the folders map to the architecture

### `backend/device/`

Contains device connectivity and device-specific adapters. The current important adapter is pfSense over SSH. Cisco remains as a secondary/legacy adapter path.

### `backend/parsing/`

Transforms raw device information into normalized information used by the rest of the platform.

### `backend/compliance/`

Contains benchmark storage, PDF extraction, benchmark handling, and the common compliance engine.

The benchmark itself is data-driven. This is important because the user can upload multiple benchmark versions without rewriting the compliance engine.

### `backend/intelligence/`

Contains the two AI responsibilities: semantic analysis and remediation generation.

### `backend/remediation/`

Contains safety validation and controlled execution. This module is intentionally separated from AI.

### `backend/verification/`

Runs post-change collection and re-evaluation.

### `backend/audit/`

Stores audit events needed to trace actions.

### `backend/reporting/`

Creates PDF reports from structured results.

### `backend/api/`

Exposes the application capabilities through HTTP endpoints. The frontend should call these endpoints instead of importing backend internals directly.

### `shared/`

Contains contracts, models, and interfaces that modules use to communicate. This is one of the most important folders for parallel development.

## 4. Why shared contracts matter

If multiple developers are working at the same time, they should agree on data shapes rather than directly depending on internal implementation details.

Conceptually, the flow is:

```text
Device Adapter
      ↓
ConfigurationSnapshot
      ↓
NormalizedConfiguration
      ↓
ComplianceResult
      ↓
Finding
      ↓
RemediationPlan
      ↓
SafetyResult
      ↓
ExecutionResult
      ↓
VerificationResult
      ↓
AuditRecord
```

A developer can replace the SSH implementation without changing the compliance engine as long as the adapter still satisfies its interface.

Likewise, a new AI provider can replace the existing provider as long as it satisfies the AI contract expected by the intelligence module.

## 5. How to extend the project

### Add another device vendor

Create a new device adapter under:

```text
backend/device/adapters/<vendor>/
```

Implement the common device interface. Add vendor-specific parsing only where required. Do not copy the whole compliance engine.

### Add another benchmark

Store the benchmark through the benchmark store and make sure its controls can be represented by the shared control model. If a benchmark needs specialized evaluation logic, add it behind the compliance engine rather than embedding it into the device adapter.

### Add another CIS version

Upload the new PDF as a separate benchmark record. Do not overwrite the previous version. Review and activate the new version independently.

### Add another AI provider

Keep provider-specific code behind an AI client/interface. The semantic and remediation modules should not depend on provider-specific SDK details.

### Add another remediation mechanism

Keep remediation planning separate from device execution. A plan can remain device-neutral until it reaches the device adapter/executor boundary.

## 6. Development order for future work

A sensible development sequence is:

1. Validate the shared models/contracts.
2. Validate pfSense SSH capability checking against the actual VM.
3. Validate live configuration collection.
4. Upload the actual CIS pfSense benchmark PDF.
5. Review extracted controls and correct extraction issues.
6. Implement deterministic checks for the selected controls.
7. Validate PASS/FAIL/UNCERTAIN behavior.
8. Validate semantic AI failure fallback.
9. Implement and test remediation AI against known findings.
10. Strengthen safety validation.
11. Test backup and real remediation on a non-production VM.
12. Run post-change verification.
13. Validate audit trail and PDF reporting.
14. Improve the frontend around the complete lifecycle.

## 7. What not to do

Do not put all logic back into `app.py`.

Do not let the AI directly execute arbitrary SSH commands.

Do not treat a generated command as safe simply because an AI model produced it.

Do not mark a CIS control as PASS or FAIL when the available evidence is insufficient.

Do not hard-code one benchmark version into the application when the benchmark upload system already supports multiple versions.

Do not assume the live pfSense VM behaves exactly like a demo configuration. Live-device testing is required before real remediation.

## 8. Current boundary of the prototype

The prototype demonstrates the architecture and provides the major software components. Some behavior still depends on external inputs or live infrastructure.

The most important external dependency is the actual benchmark PDF and the user's pfSense VM. The application can ingest the benchmark PDF, but benchmark-specific deterministic checks should be reviewed rather than fabricated.

The real SSH path must be tested in the user's environment because this development environment cannot reach the private VM.

## 9. Mental model for future developers

Think of the application as five big questions:

```text
1. What device am I talking to?
2. What is the device currently configured to do?
3. Does that state satisfy the selected benchmark?
4. If not, what safe change can bring it into compliance?
5. After the change, did the device actually become compliant and remain operational?
```

Everything in the repository exists to answer one of those questions without mixing responsibilities between modules.

## UI Design System

The prototype frontend uses the provided reference HTML as the visual baseline. The UI uses an Inter-style system font stack, a dark technical console, and a subtle custom white dotted-wave technology background. The wave artwork is stored locally at `frontend/static/tech-waves.svg`; it does not depend on an external image URL or the watermarked reference image.

All UI components use square corners (`border-radius: 0`) to keep the interface visually consistent with the requested technical style. Do not reintroduce rounded cards, buttons, tabs, badges, inputs, or panels when extending the UI.
