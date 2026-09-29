# UI Design Guidelines

## Purpose

The prototype UI is designed for a security analyst/operator rather than a generic SaaS dashboard. The interface prioritizes live device state, CIS control outcomes, evidence, remediation decisions, safety validation, and audit traceability.

## Visual rules

- Operational information takes priority over decoration.
- Tables are the primary structure for detailed controls, findings, evidence, and audit events.
- Component size follows information importance; critical findings receive more space than secondary metadata.
- Dashboard layout is intentionally asymmetric where it improves hierarchy.
- Color has functional meaning: cyan for active/system actions, green for pass/safe, red for failure/blocking, amber for uncertain/warning, muted tones for secondary information.
- Icons use a consistent simple line/utility treatment and are secondary to labels.
- Borders and separators define information groups without decorative cards or heavy shadows.
- Navigation and controls are compact and task-oriented.
- Important security information must be scannable without opening secondary panels.
- Actual pfSense/CIS domain terminology is preferred over generic placeholder content.
- Whitespace separates workflow regions; it is not used to make every component oversized.
- Controls may have different structures when their jobs differ.
- No gradients, glassmorphism, glow effects, or decorative charting are used as primary visual devices.
- No rounded UI containers are used in the current prototype.

## Workflow structure

1. Environment setup — establish the pfSense SSH session and benchmark selection.
2. Posture dashboard — summarize the current assessment and surface failed controls.
3. Assessment details — provide the full control/evidence table.
4. Benchmark review — review extracted controls before activation.
5. Remediation — inspect the finding, proposed commands, safety result, and approval path.
6. Audit history — inspect the chronological event trail.

## Density rules

The interface should become more information-dense as the analyst moves deeper into the workflow. The dashboard summarizes; assessment and benchmark review expose details; remediation focuses on decision evidence and commands; audit history favors tabular traceability.
