from xml.etree import ElementTree as ET
def pfsense_normalize(raw):
 r={'vendor':'pfSense','device_type':'Firewall','hostname':'','os':'pfSense','version':'Unknown','management_access':{},'interfaces':[],'raw_format':'xml'}
 try:
  root=ET.fromstring(raw)
  def txt(path,d=''):
   n=root.find(path);return (n.text or '').strip() if n is not None and n.text else d
  r['hostname']=txt('./system/hostname');r['domain']=txt('./system/domain');r['webgui_protocol']=txt('./system/webgui/protocol');r['version']=txt('./version','Unknown')
  for n in root.findall('.//interfaces/*'):
   x={'name':n.tag};x.update({c.tag:(c.text or '').strip() for c in n});r['interfaces'].append(x)
  for path in ('./system/ssh','./system/webgui'):
   n=root.find(path)
   if n is not None:r['management_access'][path.rsplit('/',1)[-1]]={c.tag:(c.text or '').strip() for c in n}
  return r,[]
 except ET.ParseError:return dict(r,parse_status='INVALID_XML'),['pfSense configuration was not valid XML; affected controls must remain uncertain.']
def normalize(raw,vendor='pfsense'):
 return pfsense_normalize(raw) if vendor.lower()=='pfsense' else ({'vendor':vendor,'raw':raw},[])
