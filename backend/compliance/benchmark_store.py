import json, hashlib, uuid
from datetime import datetime, timezone
from pypdf import PdfReader
from backend.compliance.pdf_extractor import extract_cis_controls_from_pdf
from backend.core.settings import BENCHMARK_DIR, UPLOAD_DIR
class BenchmarkStore:
    def __init__(self):
        self.index=BENCHMARK_DIR/"index.json"
        self._ensure()

    def _ensure(self):
        if not self.index.exists(): self.index.write_text("[]",encoding="utf-8")
        self._ensure_pfSense_benchmark()
        self._ensure_cisco_benchmark()

    def _ensure_pfSense_benchmark(self):
        """Keep a reviewed pfSense benchmark available for the bundled workflow.

        The control titles come from the supplied benchmark extraction. The explicit
        machine checks are reviewed machine mappings used by the deterministic
        evaluator; they do not depend on a remote AI service.
        """
        fixture=BENCHMARK_DIR.parent / "fixtures" / "pfsense_benchmark.json"
        if not fixture.exists(): return
        items=self.list()
        active=next((x for x in items if x.get("id")=="builtin-pfsense-cis"),None)
        if active: return
        data=json.loads(fixture.read_text(encoding="utf-8"))
        metadata=dict(data.get("metadata",{}))
        metadata.update({"id":"builtin-pfsense-cis","status":"ACTIVE","control_count":len(data.get("controls",[])),"reviewed":True})
        payload={"metadata":metadata,"controls":data.get("controls",[]),"raw_text":""}
        (BENCHMARK_DIR/("builtin-pfsense-cis"+".json")).write_text(json.dumps(payload,indent=2),encoding="utf-8")
        items.append(metadata)
        self._save(items)

    def _ensure_cisco_benchmark(self):
        """Keep the bundled Cisco CIS controls available for configuration-file audits."""
        fixture=BENCHMARK_DIR.parent / "cis_benchmark.json"
        if not fixture.exists(): return
        items=self.list()
        active=next((x for x in items if x.get("id")=="builtin-cisco-cis"),None)
        if active: return
        data=json.loads(fixture.read_text(encoding="utf-8"))
        controls=data.get("controls",[])
        metadata={
            "id":"builtin-cisco-cis",
            "filename":"Cisco CIS Benchmark (bundled)",
            "status":"ACTIVE",
            "control_count":len(controls),
            "reviewed":True,
            "vendor":"Cisco",
            "device_type":"Router / Switch",
            "framework":data.get("framework","CIS")
        }
        (BENCHMARK_DIR/"builtin-cisco-cis.json").write_text(
            json.dumps({"metadata":metadata,"controls":controls,"raw_text":""},indent=2),encoding="utf-8"
        )
        items.append(metadata)
        self._save(items)

    def list(self): return json.loads(self.index.read_text(encoding="utf-8"))
    def _save(self,items): self.index.write_text(json.dumps(items,indent=2),encoding="utf-8")
    def upload_pdf(self,filename,data):
        bid="bench-"+uuid.uuid4().hex[:12]; path=UPLOAD_DIR/(bid+".pdf"); path.write_bytes(data)
        reader=PdfReader(str(path)); controls,text=extract_cis_controls_from_pdf(reader)
        item={"id":bid,"filename":filename,"path":str(path),"sha256":hashlib.sha256(data).hexdigest(),"pages":len(reader.pages),"status":"PENDING_REVIEW","uploaded_at":datetime.now(timezone.utc).isoformat(),"controls":controls,"control_count":len(controls),"metadata":{"raw_text_length":len(text)}}
        (BENCHMARK_DIR/(bid+".json")).write_text(json.dumps({"metadata":item,"raw_text":text,"controls":controls},indent=2),encoding="utf-8")
        items=self.list();items.append(item);self._save(items);return item,text
    def get(self,bid): return next((x for x in self.list() if x["id"]==bid),None)
    def get_payload(self,bid):
        p=BENCHMARK_DIR/(bid+".json");return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None
    def update_controls(self,bid,controls,metadata=None):
        item=self.get(bid)
        if not item: raise ValueError("Benchmark not found")
        payload=self.get_payload(bid) or {};payload["controls"]=controls;payload["metadata"]=dict(payload.get("metadata",{}),**(metadata or {}))
        (BENCHMARK_DIR/(bid+".json")).write_text(json.dumps(payload,indent=2),encoding="utf-8")
        items=self.list()
        for x in items:
            if x["id"]==bid:x.update({"controls":controls,"status":"ACTIVE","control_count":len(controls)})
        self._save(items);return self.get(bid)
    def controls(self,bid): return (self.get_payload(bid) or {}).get("controls",[])
