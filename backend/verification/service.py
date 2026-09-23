class VerificationService:
    def __init__(self,adapter):self.adapter=adapter
    def run(self,compliance_engine,controls):
        raw_after=self.adapter.collect_configuration();normalized,warnings,result=compliance_engine.evaluate(raw_after,controls,"pfsense");health=self.adapter.health_check()
        return {"status":"VERIFIED" if health.get("ok") else "HEALTH_CHECK_FAILED","health":health,"raw_after":raw_after,"compliance":result,"warnings":warnings}
