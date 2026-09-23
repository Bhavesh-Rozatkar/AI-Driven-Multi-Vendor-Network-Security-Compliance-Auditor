import json,re
class RemediationAI:
    def __init__(self,client=None):self.client=client
    def generate(self,finding,device,current_config,control):
        if not self.client:return {"status":"MANUAL_REVIEW","summary":"Remediation AI is unavailable. Execution is blocked.","commands":[],"warnings":["AI provider is not configured."],"confidence":0.0,"manual_review_required":True}
        prompt={"task":"Generate a conservative pfSense remediation plan for one compliance finding.","rules":["Do not invent unsupported pfSense commands.","Never disable security controls as a shortcut.","If safe exact remediation cannot be established, return MANUAL_REVIEW with no commands.","Commands must be shell commands that can be validated before SSH execution."],"device":device,"finding":finding,"control":control,"current_config_excerpt":current_config[:12000]}
        try:
            text=self.client.generate_json_free("You are the remediation planning layer. Be conservative and return JSON only.",json.dumps(prompt),max_output_tokens=1600)
            try:data=json.loads(text)
            except Exception:
                m=re.search(r"\{.*\}",text,re.S);data=json.loads(m.group(0)) if m else {}
            commands=data.get("commands",[]) if isinstance(data.get("commands",[]),list) else []
            status="READY" if str(data.get("status"))=="READY" and commands else "MANUAL_REVIEW"
            return {"status":status,"summary":str(data.get("summary","")),"commands":[str(x).strip() for x in commands if str(x).strip()],"preconditions":[str(x) for x in data.get("preconditions",[])][:10],"warnings":[str(x) for x in data.get("warnings",[])][:10],"confidence":max(0,min(1,float(data.get("confidence",0)))),"manual_review_required":status!="READY"}
        except Exception as exc:return {"status":"MANUAL_REVIEW","summary":"Remediation AI failed; execution is blocked.","commands":[],"warnings":[str(exc)],"confidence":0.0,"manual_review_required":True}
