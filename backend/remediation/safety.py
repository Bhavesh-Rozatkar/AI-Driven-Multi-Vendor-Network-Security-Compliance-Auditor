import re
class SafetyValidator:
    BLOCKED=(r"\brm\s+-rf\b",r"\bshutdown\b",r"\breboot\b",r"\bpoweroff\b",r"\bhalt\b",r"\bpfctl\s+-d\b",r"\bkill\s+-9\b",r"\bmkfs\b",r"\bdd\s+if=",r"\bchmod\s+777\b")
    ALLOWED_PREFIX=("configctl ","/usr/local/bin/","php ","service ","sysrc ","echo ","cp ","mv ")
    def validate(self,commands,capability=None):
        errors=[]
        if not commands:errors.append("No remediation commands were supplied.")
        for cmd in commands:
            c=cmd.strip()
            if len(c)>500:errors.append("Command exceeds 500 characters.")
            if any(re.search(p,c,re.I) for p in self.BLOCKED):errors.append(f"Blocked dangerous command pattern: {c[:100]}")
            if any(x in c for x in (";","&&","||","\n","`","$(")):errors.append(f"Shell chaining/substitution is not allowed: {c[:100]}")
            if not c.startswith(self.ALLOWED_PREFIX):errors.append(f"Command is not in the approved pfSense command family: {c[:100]}")
        if capability and not capability.get("ok"):errors.append("Device capability check did not pass minimum required checks.")
        return {"safe":not errors,"errors":errors,"warnings":[]}
