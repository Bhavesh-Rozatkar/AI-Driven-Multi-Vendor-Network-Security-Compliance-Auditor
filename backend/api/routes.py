import json,os
from flask import Blueprint,jsonify,request,make_response
from backend.compliance.benchmark_store import BenchmarkStore
from backend.compliance.pdf_extractor import build_extraction_prompt,parse_ai_json
from backend.compliance.engine import ComplianceEngine
from backend.device.service import DeviceService
from backend.intelligence.remediation_ai import RemediationAI
from backend.intelligence.semantic import deterministic_vendor_detection, run_ai_semantic, run_ai_uncertain_review
from backend.intelligence.risk import analyze_risks
from backend.remediation.service import RemediationService
from backend.verification.service import VerificationService
from backend.audit.logger import AuditLogger
from backend.reporting.pdf import build_pdf
from cisco_config_to_json import parse_config as parse_cisco_config
from backend.core.settings import MAX_UPLOAD_MB,BENCHMARK_DIR
bp=Blueprint('api',__name__);store=BenchmarkStore();device_service=DeviceService();compliance=ComplianceEngine();auditlog=AuditLogger()
def ai_client():
 # AI is enrichment only. It is never on the compliance decision path.
 # If a key is configured, the UI can request semantic review after the deterministic audit.
 if not os.getenv('GEMINI_API_KEY'):return None
 if os.getenv('ENABLE_SEMANTIC_AI','1').strip().lower() not in {'1','true','yes','on'}:return None
 try:
  from gemini_client import GeminiClient;return GeminiClient()
 except Exception:return None
@bp.get('/health')
def health():return jsonify({'status':'ok','modular':True,'benchmarks':len(store.list())})
@bp.get('/benchmarks')
def benchmarks():return jsonify({'benchmarks':store.list()})
@bp.post('/benchmarks/upload')
def benchmark_upload():
 f=request.files.get('file')
 if not f or not f.filename.lower().endswith('.pdf'):return jsonify({'error':'Upload a benchmark PDF.'}),400
 data=f.read()
 if len(data)>MAX_UPLOAD_MB*1024*1024:return jsonify({'error':f'PDF exceeds {MAX_UPLOAD_MB} MB limit.'}),413
 try:item,text=store.upload_pdf(f.filename,data)
 except Exception as exc:return jsonify({'error':f'PDF extraction failed: {exc}'}),400
 controls=store.controls(item['id']);client=ai_client();ai=None
 if client:
  try:
   ai=parse_ai_json(client.generate_json_free('Enrich the already extracted CIS controls. Never create, merge, delete, rename, or change rule IDs. Return JSON only.',json.dumps(build_extraction_prompt(text)),max_output_tokens=6000))
   enrich={str(x.get('rule_id')):x for x in ai.get('controls',[]) if isinstance(x,dict)}
   for c in controls:
    e=enrich.get(str(c.get('rule_id')), {})
    for k in ('description','rationale','audit','remediation','default_value','references','additional_information'):
     if not c.get(k) and e.get(k): c[k]=e[k]
  except Exception as exc:ai={'error':str(exc)}
 payload=store.get_payload(item['id']);payload['controls']=controls;payload['extraction']={'method':'CIS-structured+AI-enrichment' if ai and not ai.get('error') else 'CIS-structured','review_required':True,'control_count':len(controls),'ai':ai};(BENCHMARK_DIR/(item['id']+'.json')).write_text(json.dumps(payload,indent=2),encoding='utf-8')
 item['extraction']=payload['extraction'];item['control_count']=len(controls);return jsonify({'benchmark':item,'controls':controls,'review_required':True})
@bp.get('/benchmarks/<bid>')
def benchmark_detail(bid):
 p=store.get_payload(bid)
 if not p:return jsonify({'error':'Benchmark not found'}),404
 return jsonify(p)
@bp.post('/benchmarks/<bid>/activate')
def activate(bid):
 data=request.get_json(silent=True) or {};controls=data.get('controls')
 if not isinstance(controls,list) or not controls:return jsonify({'error':'Reviewed controls are required.'}),400
 for c in controls:
  if 'rule_id' not in c or 'title' not in c:return jsonify({'error':'Each control requires rule_id and title.'}),400
 return jsonify({'benchmark':store.update_controls(bid,controls,{'reviewed':True})})
@bp.post('/devices/capability-check')
def capability():
 data=request.get_json(silent=True) or {}
 try:a=device_service.adapter(data);result=a.capability_check();a.close();return jsonify(result)
 except Exception as exc:return jsonify({'ok':False,'error':str(exc)}),400
@bp.post('/audit/config')
def config_audit():
 data=request.form.to_dict()
 uploaded=request.files.get('file')
 if not uploaded or not uploaded.filename:
  return jsonify({'error':'Choose a configuration file first.'}),400
 try:
  raw=uploaded.read().decode('utf-8-sig',errors='replace')
 except Exception as exc:
  return jsonify({'error':f'Configuration file could not be read: {exc}'}),400
 if not raw.strip():
  return jsonify({'error':'Configuration file is empty.'}),400
 vendor=str(data.get('vendor') or 'auto').strip().lower()
 detection=deterministic_vendor_detection(raw)
 if vendor in {'auto',''}: vendor=detection.get('vendor','Unknown').lower()
 if vendor not in {'cisco','cisco ios','ios','ios-xe'}:
  return jsonify({'error':'Configuration-file auditing currently supports Cisco IOS/IOS-XE files. Live device assessment remains available for pfSense.'}),400
 bid=data.get('benchmark_id')
 controls=store.controls(bid)
 if not controls:
  return jsonify({'error':'Select an active Cisco benchmark before auditing the file.'}),400
 try:
  normalized=parse_cisco_config(raw)
  _,warnings,result=compliance.evaluate(raw,controls,'cisco')
  unknown_items=list((normalized or {}).get('other_notable',[])[:20])
  semantic=run_ai_semantic(ai_client(),raw,unknown_items,detection,controls)
  risk=analyze_risks(normalized,result.get('results',[]),raw_text=raw)
  hostname=(normalized or {}).get('hostname','')
  device={'vendor':'Cisco','device_type':(normalized or {}).get('device_type','Router'),'os':'IOS/IOS-XE','host':'Configuration file','port':None,'hostname':hostname,'source':'configuration_file','filename':uploaded.filename}
  return jsonify({'result':{'device':device,'configuration':normalized,'compliance':result,'warnings':warnings,'capability':{'ok':True,'message':'Configuration file parsed successfully.'},'raw_configuration':raw,'semantic':semantic,'risk':risk,'source':'configuration_file','source_filename':uploaded.filename,'vendor_detection':detection}})
 except Exception as exc:
  return jsonify({'error':f'Configuration audit failed: {exc}'}),422

@bp.post('/audit/live')
def live_audit():
 data=request.get_json(silent=True) or {};controls=store.controls(data.get('benchmark_id'))
 if not controls:return jsonify({'error':'Select an activated benchmark.'}),400
 adapter=device_service.adapter(data)
 try:
  cap=adapter.capability_check()
  if not cap.get('ok'):return jsonify({'error':'Connection capability check failed.','capability':cap}),400
  raw=adapter.collect_configuration();normalized,warnings,result=compliance.evaluate(raw,controls,'pfsense')
  detection=deterministic_vendor_detection(raw)
  unknown_items=[]
  if normalized.get('webgui_protocol','').lower() not in {'https'}: unknown_items.append('webgui protocol')
  if not normalized.get('hostname'): unknown_items.append('hostname')
  semantic=run_ai_semantic(ai_client(),raw,unknown_items,detection,controls)
  risk=analyze_risks(normalized,result.get('results',[]),raw_text=raw)
  device={'vendor':'pfSense','device_type':'Firewall','os':'pfSense','host':data.get('host'),'port':data.get('port',22),'hostname':normalized.get('hostname','')}
  return jsonify({'result':{'device':device,'configuration':normalized,'compliance':result,'warnings':warnings,'capability':cap,'raw_configuration':raw,'semantic':semantic,'risk':risk,'source':'live_device','benchmark_id':data.get('benchmark_id')}})
 except Exception as exc:return jsonify({'error':str(exc)}),502
 finally:adapter.close()
@bp.post('/audit/ai-review')
def audit_ai_review():
 data=request.get_json(silent=True) or {}
 raw=str(data.get('raw_configuration') or '')
 uncertain=data.get('uncertain_controls') or []
 if not raw or not isinstance(uncertain,list):
  return jsonify({'error':'Configuration text and uncertain controls are required.'}),400
 try:
  review=run_ai_uncertain_review(ai_client(),raw,uncertain)
  return jsonify({'review':review})
 except Exception as exc:
  return jsonify({'error':f'AI interpretation failed safely: {exc}'}),200

@bp.post('/audit/verify-interpretation')
def verify_interpretation():
 data=request.get_json(silent=True) or {}
 rid=str(data.get('rule_id') or '').strip()
 decision=str(data.get('decision') or '').strip().upper()
 explanation=str(data.get('admin_explanation') or '').strip()
 if not rid or decision not in {'VERIFIED','REJECTED'}:
  return jsonify({'error':'Control ID and a VERIFIED or REJECTED decision are required.'}),400
 if len(explanation)>2000:
  return jsonify({'error':'Administrator explanation must be 2000 characters or less.'}),400
 path=BENCHMARK_DIR / 'admin_interpretation_reviews.json'
 try:
  existing=json.loads(path.read_text(encoding='utf-8')) if path.exists() else {}
  if not isinstance(existing,dict): existing={}
 except Exception:
  existing={}
 existing[rid]={'rule_id':rid,'decision':decision,'admin_explanation':explanation,'reviewed_by':'admin','reviewed_at':__import__('datetime').datetime.now().isoformat(timespec='seconds')}
 path.write_text(json.dumps(existing,indent=2),encoding='utf-8')
 auditlog.write({'type':'admin_interpretation_review','control_id':rid,'decision':decision,'admin_explanation':explanation})
 return jsonify({'ok':True,'review':existing[rid]})

@bp.post('/remediation/plan')
def remediation_plan():
 data=request.get_json(silent=True) or {};return jsonify(RemediationAI(ai_client()).generate(data.get('finding',{}),data.get('device',{}),data.get('current_config',''),data.get('control',{})))
@bp.post('/remediation/validate')
def remediation_validate():
 data=request.get_json(silent=True) or {};return jsonify(RemediationService(None).validator.validate(data.get('commands',[]),data.get('capability')))
@bp.post('/remediation/execute')
def remediation_execute():
 data=request.get_json(silent=True) or {};adapter=device_service.adapter(data);service=RemediationService(adapter)
 try:
  cap=adapter.capability_check();result=service.execute(data.get('commands',[]),cap);result['audit']=auditlog.write({'type':'remediation_execution','device':{k:data.get(k) for k in ('host','port','username')},'result':result,'commands':data.get('commands',[])})
  return jsonify(result),(200 if result.get('status') not in ('BLOCKED','FAILED') else 400)
 except Exception as exc:return jsonify({'error':str(exc)}),502
 finally:adapter.close()
@bp.post('/verification/live')
def verify_live():
 data=request.get_json(silent=True) or {};controls=store.controls(data.get('benchmark_id'));adapter=device_service.adapter(data)
 try:result=VerificationService(adapter).run(compliance,controls);result['audit']=auditlog.write({'type':'post_change_verification','device':data.get('host'),'result':result});return jsonify(result)
 except Exception as exc:return jsonify({'error':str(exc)}),502
 finally:adapter.close()
@bp.get('/audit/history')
def history():return jsonify({'events':auditlog.list()})
@bp.post('/report/pdf')
def report():
 data=request.get_json(silent=True) or {};r=make_response(build_pdf(data.get('result',data)));r.headers['Content-Type']='application/pdf';r.headers['Content-Disposition']='attachment; filename="compliance-remediation-report.pdf"';return r
