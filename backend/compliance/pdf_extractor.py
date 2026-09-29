"""Conservative extraction of benchmark recommendation records from PDF files.

For CIS-style benchmarks we parse the document structure first. AI may enrich the
already identified records, but it is never allowed to create/merge controls or
become the source of truth for rule boundaries.
"""
import json
import re
from typing import Any

ID_PREFIX = re.compile(r"^\s*((?:\d+\.)+\d+)\s+(.*)$")
STATUS = re.compile(r"\((Manual|Automated)\)\s*$", re.I)
FIELD_NAMES = {
    "Profile Applicability:": "profile",
    "Description:": "description",
    "Rationale:": "rationale",
    "Impact:": "impact",
    "Audit:": "audit",
    "Remediation:": "remediation",
    "Default Value:": "default_value",
    "References:": "references",
    "Additional Information:": "additional_information",
}


def _clean(line: str) -> str:
    return re.sub(r"\s+", " ", line or "").strip()


def _is_field(line: str) -> bool:
    return any(line.lower() == k.lower() for k in FIELD_NAMES)


def _is_section_heading(line: str) -> bool:
    line = _clean(line)
    return bool(re.match(r"^\d+(?:\.\d+)*\s+[A-Za-z].*$", line)) and not STATUS.search(line)


def _candidate(lines: list[tuple[int, str]], i: int):
    """Return (rule_id, title, status, consumed_lines) for a CIS recommendation start."""
    m = ID_PREFIX.match(lines[i][1])
    if not m:
        return None
    rid, first = m.groups()
    # Recommendation IDs in this benchmark always have at least one dot and
    # the title contains an explicit (Manual)/(Automated) status.
    parts = [first]
    for j in range(i, min(i + 4, len(lines))):
        if j > i:
            # A new numbered heading/recommendation before an assessment-status
            # marker means the original line was a section heading, not a control.
            if ID_PREFIX.match(lines[j][1]):
                return None
            parts.append(lines[j][1])
        joined = _clean(" ".join(parts))
        sm = STATUS.search(joined)
        if sm:
            title = STATUS.sub("", joined).strip()
            if len(title) >= 3 and not title.lower().startswith(("establish and", "maintain ")):
                return rid, title, sm.group(1).upper(), j - i + 1
            return None
        # Stop if another obvious field starts before a status.
        if j > i and _is_field(lines[j][1]):
            break
    return None


def _parse_fields(block: list[str]) -> dict[str, Any]:
    fields: dict[str, Any] = {}
    current = None
    for raw in block:
        line = _clean(raw)
        if not line:
            continue
        key = next((k for k in FIELD_NAMES if line.lower() == k.lower()), None)
        if key:
            current = FIELD_NAMES[key]
            fields.setdefault(current, [])
            continue
        if line.lower().startswith("cis controls:"):
            current = "cis_controls"
            fields.setdefault(current, [])
            continue
        if current:
            fields.setdefault(current, []).append(line)
    for k in list(fields):
        vals = fields[k]
        if k in {"profile", "references", "cis_controls"}:
            fields[k] = vals
        else:
            fields[k] = " ".join(vals).strip()
    return fields


def extract_cis_controls_from_pdf(reader) -> tuple[list[dict], str]:
    lines: list[tuple[int, str]] = []
    page_text = []
    page_lines = {}
    for page_no, page in enumerate(reader.pages, start=1):
        raw_lines = (page.extract_text() or "").splitlines()
        cleaned = []
        for raw in raw_lines:
            line = _clean(raw)
            if not line or re.fullmatch(r"Page \d+", line, re.I):
                continue
            cleaned.append(line)
        page_lines[page_no] = cleaned
        page_text.append("\n".join(cleaned))

    # CIS benchmark recommendation pages sit between the Recommendations section
    # and the Appendix summary. This avoids interpreting CIS Controls table rows
    # in the appendix as new recommendations.
    recommendation_start = next((p for p, ls in page_lines.items() if any(x.lower() == "recommendations" for x in ls) and any(x.startswith("1 General Setting Policy") for x in ls)), 1)
    appendix_page = next((p for p, ls in page_lines.items() if p > recommendation_start and any(x.lower().startswith("appendix: summary table") for x in ls)), len(page_lines) + 1)
    for page_no in range(recommendation_start, appendix_page):
        for line in page_lines.get(page_no, []):
            lines.append((page_no, line))

    starts = []
    i = 0
    while i < len(lines):
        hit = _candidate(lines, i)
        if hit:
            rid, title, status, consumed = hit
            starts.append((i, rid, title, status, consumed))
            i += consumed
        else:
            i += 1

    controls = []
    for n, (start, rid, title, status, consumed) in enumerate(starts):
        end = starts[n + 1][0] if n + 1 < len(starts) else len(lines)
        # A CIS section heading marks the end of the preceding recommendation
        # even when the next recommendation begins on a later page.
        for pos in range(start + consumed, end):
            if _is_section_heading(lines[pos][1]):
                end = pos
                break
        block = [line for _, line in lines[start + consumed:end]]
        fields = _parse_fields(block)
        pages = sorted(set(p for p, _ in lines[start:end]))
        control = {
            "rule_id": rid,
            "title": title,
            "assessment_status": status,
            "profile": fields.get("profile", []),
            "description": fields.get("description", ""),
            "rationale": fields.get("rationale", ""),
            "impact": fields.get("impact", ""),
            "audit": fields.get("audit", ""),
            "remediation": fields.get("remediation", ""),
            "default_value": fields.get("default_value", ""),
            "references": fields.get("references", []),
            "additional_information": fields.get("additional_information", ""),
            "cis_controls": fields.get("cis_controls", []),
            "source_pages": pages,
            "source_excerpt": " ".join([lines[start][1]] + block[:10])[:1800],
            # These fields must be explicitly reviewed before deterministic enforcement.
            "check_pattern": "",
            "required_text": "",
            "forbidden_text": "",
        }
        controls.append(control)

    # Deduplicate by recommendation ID while preserving document order.
    seen = set()
    final = []
    for c in controls:
        if c["rule_id"] in seen:
            continue
        seen.add(c["rule_id"])
        final.append(c)
    return final, "\n\n".join(page_text)


def heuristic_extract(text: str):
    """Text-only fallback for non-CIS PDFs (legacy-compatible)."""
    lines = [_clean(x) for x in text.splitlines() if _clean(x)]
    out = []
    for i, line in enumerate(lines):
        m = re.match(r"^((?:\d+\.)+\d+)\s+(.+)$", line)
        if not m:
            continue
        rid, title = m.groups()
        if len(title) < 3 or len(title) > 240:
            continue
        status_match = STATUS.search(title)
        status = status_match.group(1).upper() if status_match else "UNKNOWN"
        if status_match:
            title = STATUS.sub("", title).strip()
        out.append({
            "rule_id": rid, "title": title, "assessment_status": status,
            "description": "", "rationale": "", "audit": "", "remediation": "",
            "default_value": "", "references": [], "profile": [], "source_pages": [],
            "source_excerpt": " ".join(lines[i:i + 5])[:1200],
            "check_pattern": "", "required_text": "", "forbidden_text": ""
        })
    seen = set(); unique = []
    for c in out:
        if c["rule_id"] not in seen:
            seen.add(c["rule_id"]); unique.append(c)
    return unique


def build_extraction_prompt(text):
    return {
        "task": "Enrich already structurally extracted benchmark controls. Never create, delete, merge, rename, or change rule IDs. Never invent values. Preserve the supplied recommendation boundaries.",
        "text": text[:50000],
        "schema": {
            "controls": [{
                "rule_id": "string",
                "description": "string",
                "rationale": "string",
                "audit": "string",
                "remediation": "string",
                "default_value": "string",
                "references": ["string"],
                "additional_information": "string"
            }]
        }
    }


def parse_ai_json(text):
    text = (text or "").strip()
    try:
        return json.loads(text)
    except Exception:
        m = re.search(r"\{.*\}", text, re.S)
        return json.loads(m.group(0)) if m else {}
