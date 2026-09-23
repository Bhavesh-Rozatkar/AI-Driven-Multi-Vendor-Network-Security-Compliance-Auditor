# Prototype architecture

The prototype combines a fast deterministic compliance core with an optional AI semantic layer.

1. Upload raw configuration and compute SHA-256 traceability.
2. Detect vendor/OS deterministically; if Gemini is enabled, it can enrich the detection.
3. Parse the configuration using the line-oriented approach from the supplied CiscoParser source.
4. Build a vendor-aware intermediate JSON representation with source evidence.
5. Identify ambiguity and uncovered configuration items.
6. Send only the small semantic-enrichment payload to Gemini 3.6 Flash when a key is configured. AI can interpret unknown syntax, infer security behavior, and suggest candidate benchmark controls. AI never directly changes authoritative CIS PASS/FAIL results.
7. Map interpreted behavior into vendor-neutral security concepts.
8. Evaluate the supplied Cisco CIS benchmark deterministically.
9. Analyze uncovered/high-risk settings separately.
10. Produce evidence-based remediation and a unified report.

## Failure isolation

Gemini is wrapped in a failure boundary. Missing key, invalid key, rate limit, timeout, unavailable model, SDK failure, or malformed JSON causes `SAFE FALLBACK`. The parser, CIS evaluator, risk engine, and report still execute. This gives the presentation both an AI story and a reliable offline demo path.
