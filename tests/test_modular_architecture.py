from backend.compliance.pdf_extractor import heuristic_extract
from backend.remediation.safety import SafetyValidator

def test_benchmark_heuristic():
    controls=heuristic_extract("1.1.1 Configure host name\n1.1.2 Configure SSH\n")
    assert [x['rule_id'] for x in controls]==['1.1.1','1.1.2']

def test_safety_blocks_shell_chaining():
    r=SafetyValidator().validate(["configctl foo && reboot"],{"ok":True})
    assert not r['safe']

def test_safety_allows_known_family():
    r=SafetyValidator().validate(["configctl service restart sshd"],{"ok":True})
    assert r['safe']
