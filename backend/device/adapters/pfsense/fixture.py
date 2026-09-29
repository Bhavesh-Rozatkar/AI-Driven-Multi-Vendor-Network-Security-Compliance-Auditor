import hashlib
from pathlib import Path
from datetime import datetime, timezone
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[4]
FIXTURE_DIR = ROOT / "data" / "fixtures"
CONFIG = FIXTURE_DIR / "pfsense_config.xml"

class PfSenseFixtureAdapter:
    """Local pfSense-compatible adapter used when explicitly enabled by environment.

    It mirrors the live adapter contract so the full assessment/remediation loop can
    be exercised deterministically without changing a real network device.
    """
    def __init__(self, *args, **kwargs):
        FIXTURE_DIR.mkdir(parents=True, exist_ok=True)
        self.client = True
        self.timeout = 2

    def _read(self):
        return CONFIG.read_text(encoding="utf-8")

    @classmethod
    def reset(cls):
        baseline=FIXTURE_DIR / "pfsense_config.baseline.xml"
        if baseline.exists(): CONFIG.write_text(baseline.read_text(encoding="utf-8"),encoding="utf-8")

    def capability_check(self):
        return {
            "ok": True,
            "checks": [
                {"name":"ssh_command_execution","ok":True,"output":"capability-ok","error":""},
                {"name":"pfsense_version","ok":True,"output":"2.7.2-RELEASE","error":""},
                {"name":"config_read","ok":True,"output":"readable","error":""},
                {"name":"config_write","ok":True,"output":"writable","error":""},
                {"name":"backup_tool","ok":True,"output":"/bin/cp","error":""},
                {"name":"configctl","ok":True,"output":"/usr/local/sbin/configctl","error":""},
                {"name":"privilege","ok":True,"output":"0","error":""},
            ],
            "message":"Required device capabilities are available."
        }

    def collect_configuration(self):
        return self._read()

    def backup(self):
        stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
        backup=FIXTURE_DIR / f"config.xml.compliance-backup-{stamp}"
        backup.write_text(self._read(), encoding="utf-8")
        return str(backup)

    def execute(self, commands):
        raw=self._read()
        tree=ET.fromstring(raw)
        applied=[]
        for cmd in commands:
            c=cmd.strip()
            if c == "configctl system webgui enable-https":
                node=tree.find("./system/webgui/protocol")
                if node is None:
                    webgui=tree.find("./system/webgui")
                    if webgui is None:
                        system=tree.find("./system")
                        webgui=ET.SubElement(system,"webgui")
                    node=ET.SubElement(webgui,"protocol")
                node.text="https"
                applied.append(cmd)
            elif c == "configctl system session-timeout 10":
                node=tree.find("./system/session_timeout")
                if node is None:
                    system=tree.find("./system")
                    node=ET.SubElement(system,"session_timeout")
                node.text="10"
                applied.append(cmd)
            elif c == "configctl system dns 1.1.1.1":
                dns=tree.find("./system/dnsserver")
                if dns is None:
                    system=tree.find("./system")
                    dns=ET.SubElement(system,"dnsserver")
                dns.text="1.1.1.1"
                applied.append(cmd)
            else:
                return {"status":"FAILED","results":[{"command":cmd,"code":1,"output":"","error":"Unsupported fixture command"}]}
        CONFIG.write_text(ET.tostring(tree, encoding="unicode"), encoding="utf-8")
        return {"status":"EXECUTED","results":[{"command":c,"code":0,"output":"applied","error":""} for c in applied]}

    def health_check(self):
        return {"ok":True,"output":"health-ok","error":""}

    def close(self):
        self.client=None
