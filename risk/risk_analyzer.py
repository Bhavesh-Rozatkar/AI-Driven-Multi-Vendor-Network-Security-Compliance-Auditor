"""Fast deterministic risk assessment for uncovered security-relevant settings."""
import re
def severity_for_score(score):
 score=max(0,min(100,int(score))); return "Low" if score<=20 else "Moderate" if score<=40 else "Medium" if score<=60 else "High" if score<=80 else "Critical"
def analyze_risks(normalized,compliance_results,client=None,raw_text=None):
 raw=raw_text or normalized.get("_raw_config",""); items=[]
 def add(item,score,reason,evidence): items.append({"configuration_item":item,"risk_status":"RISK","risk_score":score,"severity":severity_for_score(score),"reason":reason,"confidence":"High","evidence":evidence})
 patterns=[
 (r"^\s*transport input\s+.*telnet",85,"Telnet management access","Telnet permits clear-text remote management."),
 (r"^\s*username\s+\S+\s+privilege\s+15\s+password\s",75,"Privileged local user with password","A privilege-15 local account uses a password instead of a secret."),
 (r"^enable password\s",70,"Enable password without enable secret","An enable password is configured; review use of an enable secret."),
 (r"^\s*ip redirects$",45,"IP redirects enabled","This uncovered setting should be reviewed for intended control-plane behavior."),
 (r"^\s*ip unreachables$",35,"IP unreachables enabled","This uncovered setting should be reviewed for intended behavior."),
 (r"^\s*ip tcp synwait-time\s",25,"Custom TCP SYN wait time","This setting is outside the supplied CIS controls."),
 (r"^\s*service pad$",65,"PAD service enabled","PAD is explicitly prohibited by the supplied benchmark.")]
 for pat,score,item,reason in patterns:
  m=re.search(pat,raw,re.I|re.M)
  if m:add(item,score,reason,m.group(0).strip())
 return {"items":items,"overall_risk_score":max((x["risk_score"] for x in items),default=0)}
