import json,uuid
from datetime import datetime,timezone
from backend.core.settings import AUDIT_DIR
class AuditLogger:
    def write(self,event):
        eid="audit-"+uuid.uuid4().hex[:12];event=dict(event);event.update({"audit_id":eid,"timestamp":datetime.now(timezone.utc).isoformat()});(AUDIT_DIR/(eid+".json")).write_text(json.dumps(event,indent=2,default=str),encoding="utf-8");return event
    def list(self):return [json.loads(p.read_text(encoding="utf-8")) for p in sorted(AUDIT_DIR.glob("audit-*.json"),reverse=True)]
