# API Reference

The API is exposed under the Flask application. The exact host/port is determined by the runtime configuration.

## Health

`GET /health`

Returns application status and the number of stored benchmarks.

## Benchmarks

`GET /benchmarks`

Lists stored benchmark records.

`POST /benchmarks/upload`

Multipart upload of a PDF benchmark. The result includes extracted controls and indicates that administrator review is required.

`GET /benchmarks/<benchmark_id>`

Returns the stored benchmark payload and controls.

`POST /benchmarks/<benchmark_id>/activate`

Activates reviewed controls for a benchmark version.

## Device

`POST /devices/capability-check`

Runs the pfSense SSH capability check using the supplied connection data.

## Assessment

`POST /audit/live`

Runs a live assessment using an activated benchmark and a live pfSense connection.

## Remediation

`POST /remediation/plan`

Generates a structured remediation proposal using the remediation AI layer.

`POST /remediation/validate`

Runs the safety validator against a proposed command set and device capability result.

`POST /remediation/execute`

Executes an approved, validated remediation through the device adapter. Real execution must be tested against a controlled VM before operational use.

## Verification

`POST /verification/live`

Collects the post-change state and reruns the configured compliance checks.

## Audit

`GET /audit/history`

Returns recorded audit events.

## Reports

`POST /report/pdf`

Builds a PDF report from a structured result payload.

## Contract expectations

API payloads should be treated as external interfaces. If a response structure must change, update tests and the documentation at the same time.
