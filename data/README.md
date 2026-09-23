# CIS benchmark data

The bundled `cis_benchmark.json` contains the detailed CIS Cisco Router Benchmark controls supplied for this project.

The application expects:

```json
{
  "benchmark_name": "...",
  "controls": [
    {
      "rule_id": "...",
      "title": "...",
      "type": "Automated",
      "audit_command": "show ...",
      "expected_configuration": "..."
    }
  ]
}
```

The benchmark file preserves the detailed controls from the supplied document. The document summary says 83 controls, while the detailed tables contain 84 uniquely identified controls; the prototype preserves all 84 detailed controls.
