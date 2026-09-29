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
# Seven controls are intentionally routed to semantic AI + administrator review.
# They are the controls where syntax alone can be ambiguous or where context matters.
AI_REVIEW_IDS = {
    "2.1.1.1.3",  # RSA modulus / key evidence
    "2.1.1.2",    # SSH version
    "2.1.2",      # CDP global state
    "3.1.2",      # proxy ARP across interfaces
    "3.1.4",      # unicast RPF semantics
    "3.2.1",      # private/reserved source filtering
    "3.2.2",      # external-interface inbound ACL
}

def _line(raw, pattern):
    return re.search(pattern, raw, re.I | re.M) is not None

def _generic_reviewed_result(raw, c):
    """Conservative deterministic checks for controls outside the seven AI-review controls.
    This never replaces the seven semantic-review controls with a guessed PASS/FAIL.
    """
    rid=str(c.get("rule_id","")); title=str(c.get("title","")); expected=str(c.get("expected_configuration","")).lower()
    low=raw.lower()
    # Context-dependent protocol controls: N/A when the protocol is absent.
    proto = None
    for name in ("eigrp", "ospf", "bgp"):
        if name in title.lower() or name in expected:
            proto=name; break
    if proto and proto not in low:
        return _safe(c,"NOT_APPLICABLE",f"{proto.upper()} is not configured in the supplied configuration.")
    if rid.startswith("1.5.") and rid not in {"1.5.1","1.5.2","1.5.3"} and "snmp-server" not in low:
        return _safe(c,"NOT_APPLICABLE","SNMP is not configured in the supplied configuration.")
    if rid in {"1.2.10","2.4.2","2.4.4"}:
        if rid=="1.2.10" and not re.search(r"^ip http (server|secure-server)$",raw,re.I|re.M):
            return _safe(c,"NOT_APPLICABLE","HTTP/HTTPS management is not enabled in the supplied configuration.")
        if rid=="2.4.2" and not re.search(r"^aaa\s+",raw,re.I|re.M):
            return _safe(c,"NOT_APPLICABLE","AAA is not configured in the supplied configuration.")
        if rid=="2.4.4" and "tftp" not in low:
            return _safe(c,"NOT_APPLICABLE","TFTP is not used in the supplied configuration.")
    # Direct absence/presence controls.
    if rid=="1.2.1":
        users=re.findall(r"^username\s+\S+\s+.*$",raw,re.I|re.M)
        ok=bool(users) and all(not re.search(r"\bprivilege\s+(?!1\b)\d+",u,re.I) for u in users)
        return _safe(c,"PASS" if ok else "FAIL","All local users are privilege 1." if ok else "At least one local user is above privilege 1.","username privilege")
    if rid=="1.2.4":
        ok=bool(re.search(r"^ip access-list (standard|extended)\s+\S+|^access-list\s+\d+",raw,re.I|re.M)) and bool(re.search(r"access-class\s+\S+\s+in",raw,re.I))
        return _safe(c,"PASS" if ok else "FAIL","A management ACL is present and applied to VTY lines." if ok else "A VTY management ACL is not evidenced.","ACL + access-class")
    if rid=="1.5.4":
        ok=not bool(re.search(r"^snmp-server community\s+\S+\s+rw\b",raw,re.I|re.M))
        return _safe(c,"PASS" if ok else "FAIL","No read-write SNMP community is configured." if ok else "A read-write SNMP community is configured.","snmp-server community ... rw")
    if rid in {"1.5.5","1.5.6"}:
        communities=re.findall(r"^snmp-server community\s+\S+(?:\s+(?:ro|rw))?(?:\s+\S+)?",raw,re.I|re.M)
        ok=not communities or all(len(x.split())>=5 for x in communities)
        return _safe(c,"PASS" if ok else "FAIL","SNMP communities have ACL context." if ok else "An SNMP community lacks ACL evidence.","snmp-server community")
    if rid=="1.5.10":
        ok=bool(re.search(r"^snmp-server user\s+\S+\s+\S+\s+v3\s+auth\s+\S+\s+\S+\s+priv\s+(?:aes\s+128|aes\s+192|aes\s+256)",raw,re.I|re.M))
        return _safe(c,"PASS" if ok else "FAIL","SNMPv3 privacy uses AES or stronger." if ok else "No AES-128-or-stronger SNMPv3 user evidence was found.","snmp-server user ... v3 ... priv aes")
    if rid=="2.3.1.4":
        servers=re.findall(r"^ntp server\s+\S+(.*)$",raw,re.I|re.M)
        ok=bool(servers) and all(re.search(r"\bkey\s+\d+\b",x,re.I) for x in servers)
        return _safe(c,"PASS" if ok else "FAIL","Every NTP server uses a key." if ok else "At least one NTP server lacks a key.","ntp server ... key")
    if rid=="3.1.1":
        ok=bool(re.search(r"^no ip source-route$",raw,re.I|re.M))
        return _safe(c,"PASS" if ok else "FAIL","IP source routing is disabled." if ok else "IP source routing is enabled or not explicitly disabled.","no ip source-route")
    if rid=="3.1.3":
        tunnels=re.findall(r"^interface\s+Tunnel\S+",raw,re.I|re.M)
        return _safe(c,"PASS" if not tunnels else "FAIL","No tunnel interfaces are configured." if not tunnels else "Tunnel interfaces are configured and require review.","interface Tunnel")
    if rid.startswith("3.3.1."):
        patterns={
            "3.3.1.1":r"^key chain\s+\S+", "3.3.1.2":r"^\s+key\s+\d+", "3.3.1.3":r"^\s+key-string\s+\S+",
            "3.3.1.4":r"address-family ipv4 autonomous-system\s+\d+", "3.3.1.5":r"af-interface default",
            "3.3.1.6":r"authentication key-chain\s+\S+", "3.3.1.7":r"authentication mode md5",
            "3.3.1.8":r"ip authentication key-chain eigrp", "3.3.1.9":r"ip authentication mode eigrp .* md5"
        }
        pat=patterns.get(rid,r"$^$" ); ok=bool(re.search(pat,raw,re.I|re.M))
        return _safe(c,"PASS" if ok else "FAIL", "Required EIGRP authentication configuration is present." if ok else "Required EIGRP authentication configuration is missing.",pat)
    if rid in {"3.3.2.1","3.3.2.2"}:
        pat=r"area\s+\S+\s+authentication message-digest" if rid.endswith(".1") else r"ip ospf message-digest-key\s+\d+\s+md5"
        ok=bool(re.search(pat,raw,re.I|re.M))
        return _safe(c,"PASS" if ok else "FAIL","Required OSPF message-digest authentication is present." if ok else "Required OSPF message-digest authentication is missing.",pat)
    if rid=="3.3.3.1":
        ok=bool(re.search(r"^\s*neighbor\s+\S+\s+password\s+\S+",raw,re.I|re.M))
        return _safe(c,"PASS" if ok else "FAIL","BGP neighbor password is configured." if ok else "BGP neighbor password is missing.","neighbor <IP> password")
    # Generic reviewed benchmark text check for simple controls.
    if expected.startswith("no "):
        token=expected.strip()
        ok=token in low
        return _safe(c,"PASS" if ok else "FAIL",f"{token} is present." if ok else f"{token} is missing.",token)
    return _safe(c,"FAIL","No deterministic evidence matched the reviewed control requirement.",expected)

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
 if rid in AI_REVIEW_IDS:
  return _safe(c,"UNCERTAIN","Configuration evidence requires semantic interpretation and administrator verification.",c.get("audit_command",c.get("expected_configuration","")))
 return _generic_reviewed_result(raw,c)
def evaluate_controls(normalized,controls,client=None,max_workers=1,raw_text=None): return [evaluate_one(raw_text or normalized.get("_raw_config",""),c) for c in controls]
def summarize(results):
 counts={k:0 for k in ALLOWED}
 for r in results: counts[r["status"]]+=1
 return {"total_controls":len(results),"passed":counts["PASS"],"failed":counts["FAIL"],"uncertain":counts["UNCERTAIN"],"not_applicable":counts["NOT_APPLICABLE"],"results":results}
