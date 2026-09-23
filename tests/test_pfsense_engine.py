from backend.compliance.engine import ComplianceEngine

def test_reviewed_required_text_check():
    _,_,r=ComplianceEngine().evaluate('<ssh><port>22</port></ssh>',[{'rule_id':'1.1','title':'SSH','required_text':'<port>22</port>'}],'pfsense')
    assert r['passed']==1

def test_unknown_control_stays_uncertain():
    _,_,r=ComplianceEngine().evaluate('<system/>',[{'rule_id':'1.2','title':'Unknown'}],'pfsense')
    assert r['uncertain']==1
