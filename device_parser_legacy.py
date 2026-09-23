#!/usr/bin/env python3
"""Fast deterministic Cisco IOS/IOS-XE parser for the prototype."""
import re

def _block(raw, start):
    m=re.search(rf"(?mi)^\s*{re.escape(start)}\s*$", raw)
    if not m: return ""
    tail=raw[m.end():]
    n=re.search(r"(?m)^\S", tail)
    return tail[:n.start()] if n else tail

def parse_config(text):
    if not text or not text.strip(): raise ValueError("Configuration is empty.")
    lines=text.splitlines()
    r={"vendor":"Cisco","device_type":"Router","hostname":None,"ios_version":None,
       "management_access":{"ssh_enabled":False,"telnet_enabled":False,"http_enabled":False,"https_enabled":False},
       "authentication":{"local_login":False,"password_encryption":False,"enable_secret_configured":False,"users":[]},
       "interfaces":[],"access_lists":[],"logging":{"hosts":[],"settings":[]},
       "aaa":{"new_model":False,"authentication":[],"accounting":[]},
       "snmp":{"communities":[],"servers":[],"groups":[],"users":[]},
       "ntp_servers":[],"ntp":{"authenticate":False,"keys":[],"trusted_keys":[],"source":None},
       "line_vty":[],"line_console":[],"line_aux":[],"banners":{},
       "routing":{"protocols":[],"static_routes":[],"ospf":[],"eigrp":[],"bgp":[]},"other_notable":[]}
    current=None; block=[]
    def finish():
        nonlocal current,block
        if not current:return
        if current.lower().startswith("interface "):
            item={"name":current.split(None,1)[1]}
            for raw in block:
                t=raw.strip(); tl=t.lower()
                if tl.startswith("description "):item["description"]=t[12:].strip()
                m=re.match(r"ip address (\S+) (\S+)",t,re.I)
                if m:item.update(ip_address=m.group(1),subnet_mask=m.group(2))
                if tl=="shutdown":item["admin_status"]="down"
                if tl=="no shutdown":item["admin_status"]="up"
                if tl=="no ip proxy-arp":item["proxy_arp"]=False
                m=re.match(r"ip access-group\s+(\S+)\s+in",t,re.I)
                if m:item["inbound_acl"]=m.group(1)
                if tl.startswith("ip verify unicast source reachable-via"):item["urpf"]=t
            r["interfaces"].append(item)
        elif current.lower().startswith("line vty"):r["line_vty"].append({"range":current[8:].strip(),"config":block.copy()})
        elif current.lower().startswith("line console"):r["line_console"].append({"range":current[12:].strip(),"config":block.copy()})
        elif current.lower().startswith("line aux"):r["line_aux"].append({"range":current[8:].strip(),"config":block.copy()})
        elif current.lower().startswith("router ospf"):r["routing"]["ospf"].append({"header":current,"config":block.copy()})
        elif current.lower().startswith("router eigrp"):r["routing"]["eigrp"].append({"header":current,"config":block.copy()})
        elif current.lower().startswith("router bgp"):r["routing"]["bgp"].append({"header":current,"config":block.copy()})
        current=None;block=[]
    section_re=re.compile(r"^(interface |line |router |key chain )",re.I)
    for raw in lines:
        t=raw.strip()
        if not t or t.startswith("!"):continue
        if not raw.startswith((" ","\t")) and section_re.match(t):
            finish();current=t;block=[];continue
        if current is not None and raw.startswith((" ","\t")):
            block.append(raw);continue
        if current is not None:finish()
        m=re.match(r"hostname\s+(\S+)",t,re.I)
        if m:r["hostname"]=m.group(1)
        m=re.match(r"version\s+(\S+)",t,re.I)
        if m:r["ios_version"]=m.group(1)
        tl=t.lower()
        if tl=="aaa new-model":r["aaa"]["new_model"]=True
        if tl.startswith("aaa authentication"):r["aaa"]["authentication"].append(t)
        if tl.startswith("aaa accounting"):r["aaa"]["accounting"].append(t)
        if tl.startswith("username "):
            m=re.match(r"username\s+(\S+)(?:\s+privilege\s+(\d+))?\s+(.*)",t,re.I)
            if m:r["authentication"]["users"].append({"username":m.group(1),"privilege":m.group(2),"credential":m.group(3)})
        if tl=="service password-encryption":r["authentication"]["password_encryption"]=True
        if tl.startswith("enable secret"):r["authentication"]["enable_secret_configured"]=True
        if tl=="ip http server":r["management_access"]["http_enabled"]=True
        if tl=="ip http secure-server":r["management_access"]["https_enabled"]=True
        if tl.startswith("transport input"):
            r["management_access"]["ssh_enabled"]|="ssh" in tl;r["management_access"]["telnet_enabled"]|="telnet" in tl
        if tl=="login local":r["authentication"]["local_login"]=True
        if tl.startswith("access-list") or tl.startswith("ip access-list"):r["access_lists"].append(t)
        if tl.startswith("logging "):
            r["logging"]["settings"].append(t)
            m=re.match(r"logging\s+(\d+\.\d+\.\d+\.\d+)$",t,re.I)
            if m:r["logging"]["hosts"].append(m.group(1))
        if tl.startswith("snmp-server community"):r["snmp"]["communities"].append(t)
        if tl.startswith("snmp-server host"):r["snmp"]["servers"].append(t)
        if tl.startswith("snmp-server group"):r["snmp"]["groups"].append(t)
        if tl.startswith("snmp-server user"):r["snmp"]["users"].append(t)
        if tl.startswith("ntp server"):r["ntp_servers"].append(t)
        if tl=="ntp authenticate":r["ntp"]["authenticate"]=True
        if tl.startswith("ntp authentication-key"):r["ntp"]["keys"].append(t)
        if tl.startswith("ntp trusted-key"):r["ntp"]["trusted_keys"].append(t)
        if tl.startswith("ntp source"):r["ntp"]["source"]=t
        m=re.match(r"banner\s+(exec|login|motd|webauth)\s+(.+)",t,re.I)
        if m:r["banners"][m.group(1).lower()]=m.group(2)
        if tl.startswith("ip route "):
            r["routing"]["static_routes"].append(t)
        if tl.startswith(("router ospf","router eigrp","router bgp")):r["routing"]["protocols"].append(t.split()[1].lower())
        if any(k in tl for k in ["ip tcp adjust-mss","ip redirects","ip unreachables","ip tcp synwait-time","service pad","cdp run"]):r["other_notable"].append(t)
    finish()
    if not r["hostname"]:r.pop("hostname")
    if not r["ios_version"]:r.pop("ios_version")
    return r

def normalize_config(raw_text, client=None): return parse_config(raw_text), []
def parse_config_with_gemini(raw_text, client=None): return normalize_config(raw_text, client)

def chunk_config(text,max_chars=3500):
    chunks=[]; cur=[]; size=0
    for line in text.splitlines():
        extra=len(line)+1
        if cur and size+extra>max_chars: chunks.append("\n".join(cur));cur=[];size=0
        cur.append(line);size+=extra
    return chunks or [text]

def deep_merge(a,b):
    if isinstance(a,dict) and isinstance(b,dict):
        out=dict(a)
        for k,v in b.items(): out[k]=deep_merge(out[k],v) if k in out else v
        return out
    if isinstance(a,list) and isinstance(b,list):
        out=[]
        for x in a+b:
            if x not in out:out.append(x)
        return out
    return b
