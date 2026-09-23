from datetime import datetime,timezone
import shlex
try:import paramiko
except ImportError:paramiko=None
class PfSenseSSHAdapter:
 def __init__(self,host,port=22,username='',password=None,key_path=None,timeout=12):self.host=host;self.port=int(port);self.username=username;self.password=password;self.key_path=key_path;self.timeout=timeout;self.client=None
 def connect(self):
  if paramiko is None:raise RuntimeError('paramiko is not installed; SSH support is unavailable.')
  if self.client:return
  c=paramiko.SSHClient();c.set_missing_host_key_policy(paramiko.AutoAddPolicy());kw=dict(hostname=self.host,port=self.port,username=self.username,timeout=self.timeout,look_for_keys=False,allow_agent=False)
  kw['key_filename']=self.key_path if self.key_path else None
  if not self.key_path:kw.pop('key_filename');kw['password']=self.password
  c.connect(**kw);self.client=c
 def run(self,cmd):
  self.connect();_,out,err=self.client.exec_command(cmd,timeout=self.timeout);code=out.channel.recv_exit_status();return code,out.read().decode(errors='replace'),err.read().decode(errors='replace')
 def capability_check(self):
  checks=[]
  for name,cmd in [('ssh_command_execution','printf capability-ok'),('pfsense_version','cat /etc/version'),('config_read','test -r /cf/conf/config.xml'),('config_write','test -w /cf/conf/config.xml'),('backup_tool','command -v cp'),('configctl','command -v configctl'),('privilege','id -u')]:
   try:c,o,e=self.run(cmd);checks.append({'name':name,'ok':c==0,'output':o.strip()[:500],'error':e.strip()[:300]})
   except Exception as ex:checks.append({'name':name,'ok':False,'output':'','error':str(ex)})
  return {'ok':all(x['ok'] for x in checks if x['name'] in {'ssh_command_execution','pfsense_version','config_read'}),'checks':checks}
 def collect_configuration(self):
  c,o,e=self.run('cat /cf/conf/config.xml')
  if c or not o.strip():raise RuntimeError(f'Unable to read pfSense configuration: {e or o}')
  return o
 def backup(self):
  stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ');remote=f'/cf/conf/config.xml.compliance-backup-{stamp}';c,o,e=self.run(f'cp /cf/conf/config.xml {shlex.quote(remote)}')
  if c:raise RuntimeError(f'Backup failed: {e or o}')
  return remote
 def execute(self,commands):
  results=[]
  for cmd in commands:
   c,o,e=self.run(cmd);results.append({'command':cmd,'code':c,'output':o[-4000:],'error':e[-2000:]})
   if c:return {'status':'FAILED','results':results}
  return {'status':'EXECUTED','results':results}
 def health_check(self):c,o,e=self.run('echo health-ok');return {'ok':c==0 and o.strip()=='health-ok','output':o.strip(),'error':e.strip()}
 def close(self):
  if self.client:self.client.close();self.client=None
