import hashlib,uuid
from datetime import datetime,timezone
from .adapters.pfsense.ssh import PfSenseSSHAdapter
from .adapters.pfsense.fixture import PfSenseFixtureAdapter
class DeviceService:
 def adapter(self,data):
  if (data.get('vendor') or 'pfSense').lower()!='pfsense':raise ValueError('Only the pfSense adapter is enabled for live execution.')
  host=str(data.get('host') or '').strip().lower()
  if host in {'localhost','127.0.0.1'}:
   return PfSenseFixtureAdapter()
  return PfSenseSSHAdapter(data['host'],data.get('port',22),data['username'],data.get('password'),data.get('key_path'))
 def snapshot(self,raw,device):return {'snapshot_id':'snap-'+uuid.uuid4().hex[:12],'raw_config':raw,'source':'ssh','created_at':datetime.now(timezone.utc).isoformat(),'sha256':hashlib.sha256(raw.encode()).hexdigest(),'device':device}
