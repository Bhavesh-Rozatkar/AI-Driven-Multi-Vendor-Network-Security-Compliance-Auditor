# Troubleshooting

## The application starts but AI is unavailable

Check whether the optional AI dependencies and API key are configured. The system is designed to keep deterministic functionality available when AI is unavailable.

## Benchmark upload fails

Check that the file is a PDF and within the configured upload-size limit. If PDF text extraction fails, inspect the PDF for encryption, image-only pages, or unusual formatting.

## A benchmark has no useful controls

Review the extracted controls. The application does not invent missing controls. For image-only or highly structured PDFs, a future OCR/table extraction layer may be required.

## Capability check fails

Verify the VM is reachable, SSH is enabled, the port is correct, the credentials are valid, and the account has the permissions needed by the adapter.

## Compliance result is UNCERTAIN

This is intentional when the evidence is insufficient for a deterministic decision. Add or review the control's deterministic evidence rather than forcing a PASS or FAIL.

## Remediation AI returns MANUAL_REVIEW

The remediation layer could not establish a sufficiently safe remediation. Do not bypass the result. Review the finding and implement a controlled manual remediation or improve the remediation mapping.

## Real execution has not been tested

This development environment cannot reach the user's private pfSense VM. Run the live-device testing sequence in `TESTING.md` against the controlled VM.
