# Change Log

## Modular prototype documentation update

- Added professional project documentation.
- Added a two-part prototype guide: short overview and detailed developer explanation.
- Documented benchmark upload/review/activation and multi-version behavior.
- Documented pfSense SSH capability checks and live-device testing boundary.
- Documented two-layer AI architecture.
- Documented remediation safety and approval boundaries.
- Documented API surface, testing, security, extension, troubleshooting, limitations, and contribution practices.

## 2026-09-27 — CIS PDF extraction correction

- Reworked CIS-style PDF ingestion to use page-aware recommendation boundary detection.
- Preserves CIS recommendation IDs, titles, assessment status, profile, audit/remediation text, defaults, references, and source pages.
- Prevents table-of-contents entries, section headings, and appendix summary rows from being treated as controls.
- AI extraction is now enrichment-only and cannot replace the deterministic control boundaries.
- Updated Benchmark Review UI to show CIS assessment status and structured source information.
- Added regression tests for the supplied CIS pfSense Firewall Benchmark v1.1.0 (33 recommendations).

## Multi-page UI update

- Added prototype login page with hardcoded `admin` / `admin@123` credentials.
- Split the UI into connection, compliance, assessment, and remediation pages.
- Added session-based page gating and logout.
- Added shared UI stylesheet and browser-state helper script.
- Preserved the analyst-first, information-dense visual language and square/no-radius components.
