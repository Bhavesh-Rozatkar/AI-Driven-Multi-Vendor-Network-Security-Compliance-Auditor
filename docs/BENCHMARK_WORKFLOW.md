# Benchmark Workflow

## Goal

The benchmark system lets administrators upload and maintain multiple benchmark PDF versions without hard-coding one benchmark into the application.

## Lifecycle

```text
PDF Upload
   ↓
Page-aware PDF Text Extraction
   ↓
CIS Recommendation Boundary Detection
   ↓
Structured Control Extraction
   ↓
Optional AI Enrichment
   ↓
Review Required
   ↓
Administrator Edits/Selects Controls
   ↓
Activation
   ↓
Available for Assessment
```

## Why review is mandatory

A PDF parser or AI model can misunderstand formatting, headings, tables, or control language. The CIS extractor therefore preserves the document-defined control boundaries and assessment status first, then treats the extracted records as candidate policy until the administrator reviews and activates them. AI enrichment cannot change control IDs or boundaries.

## Multiple versions

Each uploaded PDF is stored as a separate benchmark record. Do not overwrite an older version when a new version is uploaded.

## Deterministic checks

A reviewed control can contain explicit deterministic evidence fields such as:

- `check_pattern`
- `required_text`
- `forbidden_text`

Controls that lack sufficient deterministic evidence should remain `UNCERTAIN` rather than being guessed.

## Extending the extractor

If future benchmark formats need table extraction, page-aware parsing, OCR, or richer control metadata, add those capabilities behind the benchmark extraction interface rather than coupling them to the compliance engine.

## Current CIS pfSense benchmark behavior

The supplied `CIS pfSense Firewall Benchmark v1.1.0` is 92 pages and contains 33 recommendations. The benchmark labels these recommendations as Manual. The importer preserves that status. It does not invent deterministic checks for Manual recommendations. A human can explicitly add a reviewed `check_pattern`, `required_text`, or `forbidden_text` when there is a safe machine-checkable representation; otherwise the compliance engine reports the control as `UNCERTAIN`.
