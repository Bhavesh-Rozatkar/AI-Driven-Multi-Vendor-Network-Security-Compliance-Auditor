"""Optional AI semantic layer.

AI is deliberately NOT on the critical compliance path. A single Gemini call can
classify vendor/OS and explain unknown configuration items. If it fails, the
application keeps deterministic parsing, CIS evaluation, and risk analysis.
"""
import json
import re
from typing import Any


def _extract_json(text: str) -> dict:
    text = (text or "").strip()
    try:
        value = json.loads(text)
        return value if isinstance(value, dict) else {}
    except Exception:
        m = re.search(r"\{.*\}", text, re.S)
        if not m:
            return {}
        try:
            value = json.loads(m.group(0))
            return value if isinstance(value, dict) else {}
        except Exception:
            return {}


def deterministic_vendor_detection(raw: str) -> dict:
    """Fast fallback vendor/OS detector. It is intentionally conservative."""
    text = raw.lower()
    if re.search(r"^\s*hostname\s+\S+", raw, re.M) and (
        "aaa new-model" in text or "ip ssh version 2" in text or "line vty" in text
    ):
        return {"vendor": "Cisco", "device_type": "Router", "os": "IOS/IOS-XE", "confidence": 0.99, "method": "deterministic"}
    if "set system host-name" in text or "set interfaces" in text:
        return {"vendor": "Juniper", "device_type": "Network Device", "os": "Junos", "confidence": 0.95, "method": "deterministic"}
    if "management api http-commands" in text or re.search(r"^hostname\s+", raw, re.M) and "daemon" in text:
        return {"vendor": "Arista", "device_type": "Network Device", "os": "EOS", "confidence": 0.75, "method": "deterministic"}
    if "config system global" in text or "config firewall" in text:
        return {"vendor": "Fortinet", "device_type": "Firewall", "os": "FortiOS", "confidence": 0.95, "method": "deterministic"}
    return {"vendor": "Unknown", "device_type": "Unknown", "os": "Unknown", "confidence": 0.20, "method": "deterministic"}


def run_ai_semantic(client, raw: str, unknown_items: list[str], deterministic_detection: dict, controls: list[dict] | None = None) -> dict:
    """Use at most one small Gemini request. Never raises for normal AI failures."""
    if client is None:
        return {
            "enabled": False,
            "status": "FALLBACK",
            "method": "deterministic",
            "message": "Gemini is not configured; deterministic pipeline remains active.",
            "vendor_detection": deterministic_detection,
            "mappings": [],
        }

    items = unknown_items[:20]
    catalog = [
        {"rule_id": c.get("rule_id"), "title": c.get("title")}
        for c in (controls or [])
    ]
    prompt = {
        "task": "vendor-agnostic semantic security enrichment for a compliance auditor",
        "constraints": [
            "Do not invent configuration values or device settings.",
            "Only interpret text supplied in the input.",
            "If an item cannot be interpreted confidently, mark it uncertain.",
            "Return one compact JSON object and no markdown.",
            "This output assists the deterministic engine; it does not override authoritative compliance evidence.",
        ],
        "deterministic_detection": deterministic_detection,
        "unknown_configuration_items": items,
        "raw_configuration_excerpt": raw[:7000],
        "available_controls": catalog,
        "schema": {
            "vendor": "string",
            "device_type": "string",
            "os": "string",
            "confidence": "0..1",
            "mappings": [
                {"configuration_item": "string", "security_behavior": "string", "confidence": "0..1", "reason": "string", "candidate_control_ids": ["string"]}
            ],
        },
    }
    system = (
        "You are the semantic understanding layer of a vendor-agnostic network compliance auditor. "
        "Infer vendor, platform and security behavior only from supplied configuration text. "
        "Be conservative and return compact JSON. The deterministic compliance engine remains authoritative."
    )
    try:
        data = _extract_json(client.generate_json(system, json.dumps(prompt), max_output_tokens=1200))
        mappings = data.get("mappings", []) if isinstance(data.get("mappings", []), list) else []
        clean = []
        allowed = set(items)
        for m in mappings:
            if not isinstance(m, dict):
                continue
            item = str(m.get("configuration_item", "")).strip()
            if item and (not allowed or item in allowed):
                try: conf = max(0.0, min(1.0, float(m.get("confidence", 0))))
                except Exception: conf = 0.0
                candidates = m.get("candidate_control_ids", []) if isinstance(m.get("candidate_control_ids", []), list) else []
                clean.append({"configuration_item": item, "security_behavior": str(m.get("security_behavior", "Uncertain")), "confidence": conf, "reason": str(m.get("reason", "")), "candidate_control_ids": [str(x) for x in candidates[:5]]})
        return {
            "enabled": True,
            "status": "AI_ENRICHED",
            "method": f"Gemini {getattr(client, 'last_model', getattr(client, 'model', 'Flash'))}",
            "message": "AI semantic enrichment completed. Deterministic CIS results remain authoritative.",
            "vendor_detection": {
                "vendor": str(data.get("vendor") or deterministic_detection["vendor"]),
                "device_type": str(data.get("device_type") or deterministic_detection["device_type"]),
                "os": str(data.get("os") or deterministic_detection["os"]),
                "confidence": float(data.get("confidence", deterministic_detection.get("confidence", 0.0))),
                "method": "ai+deterministic",
            },
            "mappings": clean,
        }
    except Exception as exc:
        return {
            "enabled": True,
            "status": "FALLBACK",
            "method": "deterministic",
            "message": f"Gemini temporarily unavailable; deterministic pipeline continued. ({type(exc).__name__}: {str(exc)[:320]})",
            "vendor_detection": deterministic_detection,
            "mappings": [],
        }
