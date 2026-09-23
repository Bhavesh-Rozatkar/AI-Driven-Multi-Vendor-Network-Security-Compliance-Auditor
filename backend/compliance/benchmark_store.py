import json, hashlib, uuid
from datetime import datetime, timezone
from pypdf import PdfReader
from backend.core.settings import BENCHMARK_DIR, UPLOAD_DIR
class BenchmarkStore:
    def __init__(self): self.index=BENCHMARK_DIR/"index.json"; self._ensure()
    def _ensure(self):
        if not self.index.exists(): self.index.write_text("[]",encoding="utf-8")
    def list(self): return json.loads(self.index.read_text(encoding="utf-8"))
    def _save(self,items): self.index.write_text(json.dumps(items,indent=2),encoding="utf-8")
    def upload_pdf(self,filename,data):
        bid="bench-"+uuid.uuid4().hex[:12]; path=UPLOAD_DIR/(bid+".pdf"); path.write_bytes(data)
        reader=PdfReader(str(path)); text="\n".join((p.extract_text() or "") for p in reader.pages)
        item={"id":bid,"filename":filename,"path":str(path),"sha256":hashlib.sha256(data).hexdigest(),"pages":len(reader.pages),"status":"PENDING_REVIEW","uploaded_at":datetime.now(timezone.utc).isoformat(),"controls":[],"metadata":{"raw_text_length":len(text)}}
        (BENCHMARK_DIR/(bid+".json")).write_text(json.dumps({"metadata":item,"raw_text":text,"controls":[]},indent=2),encoding="utf-8")
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
