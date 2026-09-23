import json,os
from flask import Blueprint,jsonify,request,make_response
from backend.compliance.benchmark_store import BenchmarkStore
from backend.compliance.pdf_extractor import heuristic_extract,build_extraction_prompt,parse_ai_json
from backend.compliance.engine import ComplianceEngine
from backend.device.service import DeviceService
from backend.intelligence.remediation_ai import RemediationAI
from backend.remediation.service import RemediationService
from backend.verification.service import VerificationService
from backend.audit.logger import AuditLogger
from backend.reporting.pdf import build_pdf
from backend.core.settings import MAX_UPLOAD_MB,BENCHMARK_DIR
bp=Blueprint('api',__name__);store=BenchmarkStore();device_service=DeviceService();compliance=ComplianceEngine();auditlog=AuditLogger()
def ai_client():
 if not os.getenv('GEMINI_API_KEY'):return None
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
 controls=heuristic_extract(text);client=ai_client();ai=None
 if client:
  try:ai=parse_ai_json(client.generate_json_free('Extract benchmark controls conservatively. Never invent controls. Return JSON only.',json.dumps(build_extraction_prompt(text)),max_output_tokens=6000));controls=ai.get('controls') or controls
  except Exception as exc:ai={'error':str(exc)}
 payload=store.get_payload(item['id']);payload['controls']=controls;payload['extraction']={'method':'AI+heuristic' if ai and not ai.get('error') else 'heuristic','review_required':True,'control_count':len(controls),'ai':ai};(BENCHMARK_DIR/(item['id']+'.json')).write_text(json.dumps(payload,indent=2),encoding='utf-8')
 item['extraction']=payload['extraction'];item['heuristic_control_count']=len(controls);return jsonify({'benchmark':item,'controls':controls,'review_required':True})
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
@bp.post('/audit/live')
def live_audit():
 data=request.get_json(silent=True) or {};controls=store.controls(data.get('benchmark_id'))
 if not controls:return jsonify({'error':'Select an activated benchmark.'}),400
 adapter=device_service.adapter(data)
 try:
  cap=adapter.capability_check()
  if not cap.get('ok'):return jsonify({'error':'Connection capability check failed.','capability':cap}),400
  raw=adapter.collect_configuration();normalized,warnings,result=compliance.evaluate(raw,controls,'pfsense');device={'vendor':'pfSense','device_type':'Firewall','os':'pfSense','host':data.get('host'),'port':data.get('port',22),'hostname':normalized.get('hostname','')}
  return jsonify({'result':{'device':device,'configuration':normalized,'compliance':result,'warnings':warnings,'capability':cap,'raw_configuration':raw}})
 except Exception as exc:return jsonify({'error':str(exc)}),502
 finally:adapter.close()
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
