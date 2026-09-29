import io
from app import app

def test_cisco_configuration_audit_endpoint():
    client=app.test_client()
    with client.session_transaction() as sess: sess["user"]="admin"
    raw=open("demo_configs/02_compliance_fail.txt",encoding="utf-8").read()
    r=client.post("/api/audit/config",data={"vendor":"auto","benchmark_id":"builtin-cisco-cis","file":(io.BytesIO(raw.encode()),"cisco-fail.txt")},content_type="multipart/form-data")
    assert r.status_code==200
    result=r.get_json()["result"]
    assert result["source"]=="configuration_file"
    assert result["semantic"]["vendor_detection"]["vendor"]=="Cisco"
    assert result["compliance"]["failed"]>0
