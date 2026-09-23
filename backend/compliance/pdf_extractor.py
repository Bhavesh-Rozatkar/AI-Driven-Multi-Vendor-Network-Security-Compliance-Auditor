import json,re

def heuristic_extract(text):
    controls=[]
    lines=[x.strip() for x in text.splitlines() if x.strip()]
    for i,line in enumerate(lines):
        m=re.match(r"^((?:\d+\.)+\d+)\s+(.+)$",line)
        if not m: continue
        rid,title=m.groups()
        if len(title)<3 or len(title)>240: continue
        context=" ".join(lines[i:i+5])
        controls.append({"rule_id":rid,"title":title,"description":"","expected_configuration":"","audit_command":"","remediation":"","severity":"","source_excerpt":context[:1200]})
    seen=set(); out=[]
    for c in controls:
        if c["rule_id"] not in seen: seen.add(c["rule_id"]); out.append(c)
    return out

def build_extraction_prompt(text):
    return {"task":"Extract benchmark controls from the supplied PDF text. Do not invent values. Return controls exactly as stated when possible.","text":text[:50000],"schema":{"benchmark_name":"string","version":"string","vendor":"string","device":"string","controls":[{"rule_id":"string","title":"string","description":"string","audit_command":"string","expected_configuration":"string","remediation":"string","severity":"string","source_excerpt":"string"}]}}

def parse_ai_json(text):
    text=(text or "").strip()
    try:return json.loads(text)
    except Exception:
        m=re.search(r"\{.*\}",text,re.S)
        return json.loads(m.group(0)) if m else {}
