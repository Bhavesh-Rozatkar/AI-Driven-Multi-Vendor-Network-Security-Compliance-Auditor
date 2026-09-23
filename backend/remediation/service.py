from .safety import SafetyValidator
class RemediationService:
    def __init__(self,adapter):self.adapter=adapter;self.validator=SafetyValidator()
    def plan_validation(self,commands,capability):return self.validator.validate(commands,capability)
    def execute(self,commands,capability):
        validation=self.plan_validation(commands,capability)
        if not validation["safe"]:return {"status":"BLOCKED","validation":validation}
        backup=self.adapter.backup();result=self.adapter.execute(commands);result["backup_path"]=backup;result["validation"]=validation;return result
