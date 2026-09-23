# Benchmark Workflow

## Goal

The benchmark system lets administrators upload and maintain multiple benchmark PDF versions without hard-coding one benchmark into the application.

## Lifecycle

```text
PDF Upload
   ↓
Text Extraction
   ↓
Heuristic Control Extraction
   ↓
Optional AI Structuring
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

A PDF parser or AI model can misunderstand formatting, headings, tables, or control language. The system therefore treats extracted controls as candidate data until the administrator reviews and activates them.

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
