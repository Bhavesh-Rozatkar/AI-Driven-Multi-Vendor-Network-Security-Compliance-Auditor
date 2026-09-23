from dataclasses import dataclass,field
@dataclass
class DeviceInfo: name:str='';vendor:str='Unknown';device_type:str='Unknown';os:str='Unknown';version:str='Unknown';host:str='';port:int=22
@dataclass
class ConfigurationSnapshot: snapshot_id:str='';raw_config:str='';source:str='';created_at:str='';sha256:str='';device:dict=field(default_factory=dict)
@dataclass
class ComplianceFinding: rule_id:str='';title:str='';status:str='UNCERTAIN';reason:str='';evidence:str='';severity:str=''
@dataclass
class RemediationPlan: finding_id:str='';status:str='MANUAL_REVIEW';summary:str='';commands:list=field(default_factory=list);confidence:float=0.0
