from pathlib import Path
from cisco_config_to_json import parse_config
from compliance.benchmark_loader import load_benchmark
from compliance.cis_auditor import evaluate_controls,summarize
from risk.risk_analyzer import analyze_risks
ROOT=Path(__file__).resolve().parents[1]
def load_raw(name): return (ROOT/'demo_configs'/name).read_text()
def test_parser_extracts_core_fields():
 n=parse_config('hostname R1\nservice password-encryption\ninterface GigabitEthernet0/0\n ip address 10.0.0.1 255.255.255.0\n no shutdown\n!\n')
 assert n['hostname']=='R1'; assert n['authentication']['password_encryption']; assert n['interfaces'][0]['ip_address']=='10.0.0.1'
def test_benchmark_has_controls(): assert len(load_benchmark(ROOT/'data/cis_benchmark.json')['controls'])>=80
def test_fail_config_has_failures():
 raw=load_raw('02_compliance_fail.txt'); n=parse_config(raw); b=load_benchmark(ROOT/'data/cis_benchmark.json'); c=summarize(evaluate_controls(n,b['controls'],raw_text=raw)); assert c['failed']>=10
def test_unknown_risk():
 raw=load_raw('03_unknown_configuration.txt'); n=parse_config(raw); r=analyze_risks(n,[],raw_text=raw); assert isinstance(r['items'],list)

def test_ai_fallback_without_client():
    from ai_semantic import run_ai_semantic, deterministic_vendor_detection
    raw = "hostname R1\nip tcp synwait-time 30\n"
    result = run_ai_semantic(None, raw, ["ip tcp synwait-time 30"], deterministic_vendor_detection(raw))
    assert result["status"] == "FALLBACK"
    assert result["mappings"] == []


def test_ai_enrichment_uses_one_client_call():
    from ai_semantic import run_ai_semantic, deterministic_vendor_detection
    class FakeClient:
        def __init__(self): self.calls = 0
        def generate_json(self, system, content, max_output_tokens=1200):
            self.calls += 1
            return '{"vendor":"Cisco","device_type":"Router","os":"IOS-XE","confidence":0.99,"mappings":[{"configuration_item":"ip redirects","security_behavior":"ICMP redirect generation","confidence":0.9,"reason":"The supplied command enables redirects."}]}'
    fake = FakeClient()
    raw = "hostname R1\nip redirects\n"
    result = run_ai_semantic(fake, raw, ["ip redirects"], deterministic_vendor_detection(raw))
    assert fake.calls == 1
    assert result["status"] == "AI_ENRICHED"
    assert result["mappings"][0]["configuration_item"] == "ip redirects"
