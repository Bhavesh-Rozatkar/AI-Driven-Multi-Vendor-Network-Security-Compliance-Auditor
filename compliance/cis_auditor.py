"""Deterministic CIS evaluator for the hackathon prototype."""
import re
ALLOWED={"PASS","FAIL","NOT_APPLICABLE","UNCERTAIN"}
def _safe(c,status,reason,evidence=""):
 return {"rule_id":str(c["rule_id"]),"title":str(c["title"]),"status":status if status in ALLOWED else "UNCERTAIN","reason":reason,"evidence":evidence}
def _has(raw,pat): return re.search(pat,raw,re.I|re.M) is not None
def _block(raw,start):
 m=re.search(rf"(?mi)^\s*{re.escape(start)}\s*$",raw)
 if not m:return ""
 tail=raw[m.end():]; n=re.search(r"(?m)^\S",tail); return tail[:n.start()] if n else tail
def _timeout_ok(block):
 vals=re.findall(r"exec-timeout\s+(\d+)(?:\s+(\d+))?",block,re.I)
 return bool(vals) and all(int(m)<=10 for m,s in vals)
def evaluate_one(raw,c):
 rid=c["rule_id"]
 checks={
 "1.1.1":(_has(raw,r"^aaa new-model$"),"aaa new-model is configured","aaa new-model"),
 "1.1.2":(_has(raw,r"^aaa authentication login\s+\S+"),"AAA login authentication is configured","aaa authentication login"),
 "1.1.3":(_has(raw,r"^aaa authentication enable default\s+.+"),"AAA enable authentication is configured","aaa authentication enable default"),
 "1.1.4":(_has(_block(raw,"line vty 0 4"),r"login authentication\s+\S+"),"VTY login authentication is configured","line vty + login authentication"),
 "1.1.5":(_has(raw,r"^ip http authentication default\b"),"HTTP authentication is configured","ip http authentication default"),
 "1.1.6":(_has(raw,r"^aaa accounting commands\s+15\s+\S+\s+start-stop"),"Privileged command accounting is configured","aaa accounting commands 15 ... start-stop"),
 "1.1.7":(_has(raw,r"^aaa accounting connection\s+\S+.*start-stop"),"Connection accounting is configured","aaa accounting connection ... start-stop"),
 "1.1.8":(_has(raw,r"^aaa accounting exec\s+\S+.*start-stop"),"EXEC accounting is configured","aaa accounting exec ... start-stop"),
 "1.1.9":(_has(raw,r"^aaa accounting network\s+\S+.*start-stop"),"Network accounting is configured","aaa accounting network ... start-stop"),
 "1.1.10":(_has(raw,r"^aaa accounting system\s+\S+.*start-stop"),"System accounting is configured","aaa accounting system ... start-stop"),
 "1.2.2":(_has(raw,r"^\s+transport input\s+ssh\s*$"),"VTY accepts SSH transport","transport input ssh"),
 "1.2.3":(_has(_block(raw,"line aux 0"),r"^\s+no exec$"),"AUX line has no exec","line aux 0 + no exec"),
 "1.2.5":(_has(raw,r"^\s+access-class\s+\S+\s+in\s*$"),"VTY access-class is configured","access-class <vty_acl> in"),
 "1.2.6":(_timeout_ok(_block(raw,"line aux 0")),"AUX exec-timeout is 10 minutes or less","exec-timeout"),
 "1.2.7":(_timeout_ok(_block(raw,"line con 0")) or _timeout_ok(_block(raw,"line console 0")),"Console exec-timeout is 10 minutes or less","exec-timeout"),
 "1.2.8":(_timeout_ok(_block(raw,"line vty 0 4")),"VTY exec-timeout is 10 minutes or less","exec-timeout"),
 "1.2.9":(_has(raw,r"^ip http max-connections\s+2\b"),"HTTP/HTTPS maximum connections is set to 2","ip http max-connections 2"),
 "1.3.1":(_has(raw,r"^banner exec\s"),"EXEC banner is configured","banner exec"),"1.3.2":(_has(raw,r"^banner login\s"),"Login banner is configured","banner login"),"1.3.3":(_has(raw,r"^banner motd\s"),"MOTD banner is configured","banner motd"),"1.3.4":(_has(raw,r"^banner webauth\s"),"Webauth banner is configured","banner webauth"),
 "1.4.1":(_has(raw,r"^enable secret\s"),"Enable secret is configured","enable secret"),"1.4.2":(_has(raw,r"^service password-encryption$"),"Password encryption service is enabled","service password-encryption"),"1.4.3":(_has(raw,r"^username\s+\S+\s+.*\bsecret\b"),"Local users use secret credentials","username ... secret"),
 "1.5.2":(not _has(raw,r"^snmp-server community\s+private\b"),"Private SNMP community is absent","no private community"),"1.5.3":(not _has(raw,r"^snmp-server community\s+public\b"),"Public SNMP community is absent","no public community"),"1.5.7":(_has(raw,r"^snmp-server host\s"),"SNMP host is configured","snmp-server host"),"1.5.8":(_has(raw,r"^snmp-server enable traps snmp\s+authentication\s+linkup\s+linkdown\s+coldstart\b"),"SNMP traps are enabled","snmp-server enable traps snmp authentication linkup linkdown coldstart"),"1.5.9":(_has(raw,r"^snmp-server group\s+\S+\s+v3\s+priv\b"),"SNMPv3 group uses privacy","snmp-server group ... v3 priv"),
 "2.1.1.1.1":(_has(raw,r"^hostname\s+\S+"),"Hostname is configured","hostname"),"2.1.1.1.2":(_has(raw,r"^ip domain-name\s+\S+"),"IP domain-name is configured","ip domain-name"),"2.1.1.1.4":(_has(raw,r"^ip ssh time-out\s+(\d+)\b") and int(re.search(r"^ip ssh time-out\s+(\d+)",raw,re.I|re.M).group(1))<=60,"SSH timeout is 60 seconds or lower","ip ssh time-out"),"2.1.1.1.5":(_has(raw,r"^ip ssh authentication-retries\s+(\d+)\b") and int(re.search(r"^ip ssh authentication-retries\s+(\d+)",raw,re.I|re.M).group(1))<=3,"SSH authentication retries are 3 or lower","ip ssh authentication-retries"),
 "2.1.3":(_has(raw,r"^no ip bootp server$"),"BOOTP server is disabled","no ip bootp server"),"2.1.4":(_has(raw,r"^no service dhcp$"),"DHCP service is disabled","no service dhcp"),"2.1.5":(_has(raw,r"^service tcp-keepalives-in$"),"Inbound TCP keepalives are enabled","service tcp-keepalives-in"),"2.1.6":(_has(raw,r"^service tcp-keepalives-out$"),"Outbound TCP keepalives are enabled","service tcp-keepalives-out"),"2.1.7":(_has(raw,r"^no service pad$"),"PAD is disabled","no service pad"),
 "2.2.1":(_has(raw,r"^logging (on|enable)$"),"Logging is enabled","logging on/enable"),"2.2.2":(_has(raw,r"^logging buffered\s+\d+"),"Buffered logging is configured","logging buffered <buffer-size>"),"2.2.3":(_has(raw,r"^logging console critical$"),"Console logging is limited to critical","logging console critical"),"2.2.4":(_has(raw,r"^logging\s+(?:host\s+)?\d+\.\d+\.\d+\.\d+$"),"A logging host is configured","logging host <syslog-server-IP>"),"2.2.5":(_has(raw,r"^logging trap informational$"),"Logging trap level is informational","logging trap informational"),"2.2.6":(_has(raw,r"^service timestamps debug datetime msec show-timezone$"),"Debug timestamps are configured","service timestamps debug datetime msec show-timezone"),"2.2.7":(_has(raw,r"^logging source-interface\s+\S+"),"Logging source interface is configured","logging source-interface"),"2.2.8":(_has(raw,r"^login on-failure log$") and _has(raw,r"^login on-success log$"),"Login success and failure logging are enabled","login on-failure log + login on-success log"),
 "2.3.1.1":(_has(raw,r"^ntp authenticate$"),"NTP authentication is enabled","ntp authenticate"),"2.3.1.2":(_has(raw,r"^ntp authentication-key\s+\S+\s+md5\s+\S+"),"NTP authentication key is configured","ntp authentication-key"),"2.3.1.3":(_has(raw,r"^ntp trusted-key\s+\S+"),"Trusted NTP key is configured","ntp trusted-key"),"2.3.2":(_has(raw,r"^ntp server\s+\d+\.\d+\.\d+\.\d+\b"),"NTP server is configured by IP address","ntp server <IP-address>"),"2.4.1":(_has(raw,r"^interface Loopback0$") and _has(_block(raw,"interface Loopback0"),r"^\s+ip address\s+\S+\s+\S+"),"Loopback0 with an IP address is configured","interface Loopback0 + ip address"),"2.4.3":(_has(raw,r"^ntp source loopback\s*\d+$"),"NTP source is a loopback interface","ntp source loopback")}
 if rid in {"1.3.4"} and not _has(raw,r"^banner webauth\s"):
  return _safe(c,"NOT_APPLICABLE","No webauth banner is configured in the supplied configuration.")
 if rid in {"1.5.7","1.5.8","1.5.9"} and not _has(raw,r"^snmp-server\s"):
  return _safe(c,"NOT_APPLICABLE","SNMP is not configured in the supplied configuration.")
 if rid == "2.2.1" and _has(raw,r"^logging\s+(buffered|console|trap|source-interface)|^logging\s+\d+\.\d+\.\d+\.\d+$"):
  return _safe(c,"PASS","Logging configuration is present.","logging configuration")
 if rid in checks:
  ok,reason,evidence=checks[rid]
  if rid in {"1.1.5","1.2.9"} and not _has(raw,r"^ip http (server|secure-server)$"): return _safe(c,"NOT_APPLICABLE","HTTP/HTTPS management is not enabled in the supplied configuration.")
  return _safe(c,"PASS" if ok else "FAIL",reason if ok else f"Expected {c['expected_configuration']} was not found in the supplied configuration.",evidence)
 return _safe(c,"UNCERTAIN","This control is manual or requires evidence not safely inferable from the configuration alone.",c.get("audit_command",""))
def evaluate_controls(normalized,controls,client=None,max_workers=1,raw_text=None): return [evaluate_one(raw_text or normalized.get("_raw_config",""),c) for c in controls]
def summarize(results):
 counts={k:0 for k in ALLOWED}
 for r in results: counts[r["status"]]+=1
 return {"total_controls":len(results),"passed":counts["PASS"],"failed":counts["FAIL"],"uncertain":counts["UNCERTAIN"],"not_applicable":counts["NOT_APPLICABLE"],"results":results}
