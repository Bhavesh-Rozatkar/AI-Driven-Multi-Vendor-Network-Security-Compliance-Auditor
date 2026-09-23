import re
from compliance.cis_auditor import evaluate_controls, summarize
from backend.parsing.normalize import normalize

class ComplianceEngine:
    def _reviewed_check(self, raw, control):
        """Only uses explicit fields present in the reviewed benchmark record.
        No AI inference is treated as compliance evidence."""
        pattern=control.get('check_pattern')
        contains=control.get('required_text')
        absent=control.get('forbidden_text')
        if pattern:
            try:
                ok=re.search(str(pattern),raw,re.I|re.M) is not None
            except re.error:
                return 'UNCERTAIN','Invalid reviewed check_pattern.',''
            return ('PASS' if ok else 'FAIL'), ('Reviewed benchmark pattern matched.' if ok else 'Reviewed benchmark pattern was not found.'), str(pattern)
        if contains:
            vals=contains if isinstance(contains,list) else [contains]
            missing=[str(x) for x in vals if str(x).lower() not in raw.lower()]
            return ('PASS' if not missing else 'FAIL'), ('Required benchmark evidence is present.' if not missing else 'Required benchmark evidence is missing.'), ', '.join(str(x) for x in vals)
        if absent:
            vals=absent if isinstance(absent,list) else [absent]
            found=[str(x) for x in vals if str(x).lower() in raw.lower()]
            return ('PASS' if not found else 'FAIL'), ('Forbidden benchmark evidence is absent.' if not found else 'Forbidden benchmark evidence is present.'), ', '.join(str(x) for x in vals)
        return 'UNCERTAIN','No explicit deterministic check was supplied in the reviewed benchmark record.',''

    def evaluate(self, raw, controls, vendor='pfsense'):
        normalized,warnings=normalize(raw,vendor)
        if vendor.lower()=='pfsense':
            results=[]
            for c in controls:
                status,reason,evidence=self._reviewed_check(raw,c)
                results.append({'rule_id':str(c.get('rule_id','')),'title':str(c.get('title','')),'status':status,'reason':reason,'evidence':evidence,'remediation':c.get('remediation','')})
            return normalized,warnings,summarize(results)
        return normalized,warnings,summarize(evaluate_controls(normalized,controls,raw_text=raw))
