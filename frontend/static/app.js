const $=id=>document.getElementById(id);
const esc=v=>String(v??'').replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;');
async function api(path,options={}){
 const controller=new AbortController();
 const timeoutMs=Number(options.timeoutMs||20000);
 const timer=setTimeout(()=>controller.abort(),timeoutMs);
 const requestOptions={...options,signal:controller.signal};
 delete requestOptions.timeoutMs;
 try{
  const r=await fetch('/api'+path,requestOptions);let d={};try{d=await r.json()}catch{}
  if(!r.ok)throw new Error(d.error||JSON.stringify(d));return d;
 }catch(e){
  if(e&&e.name==='AbortError')throw new Error('The request timed out. The assessment path was stopped safely; please try again.');
  throw e;
 }finally{clearTimeout(timer)}
}
function saveDevice(){const d={vendor:'pfSense',host:$('host')?.value.trim(),port:+($('port')?.value||22),username:$('username')?.value.trim(),password:$('password')?.value||''};localStorage.setItem('pfsenseDevice',JSON.stringify(d));return d}
function getDevice(){try{return JSON.parse(localStorage.getItem('pfsenseDevice')||'{}')}catch{return {}}}
function loadDevice(){const d=getDevice();for(const k of ['host','port','username','password'])if($(k)&&d[k]!==undefined)$(k).value=d[k]}
function saveBenchmark(id){if(id)localStorage.setItem('activeBenchmark',id)}
function getBenchmark(){return localStorage.getItem('activeBenchmark')||''}
function saveResult(r){localStorage.setItem('assessmentResult',JSON.stringify(r))}
function getResult(){try{return JSON.parse(localStorage.getItem('assessmentResult')||'null')}catch{return null}}
function navActive(){const p=location.pathname.split('/').filter(Boolean)[0]||'connection';const dashboard= p==='assessment' && !location.hash;document.querySelectorAll('.nav a').forEach(a=>{let active=a.dataset.page===p;if(p==='assessment' && a.dataset.page==='dashboard')active=dashboard;if(p==='assessment' && a.dataset.page==='assessment')active=!dashboard;a.classList.toggle('active',active)})}
function shellUser(){const u=sessionStorage.getItem('sihUser');document.querySelectorAll('[data-user]').forEach(x=>x.textContent=u||'admin');const now=new Date();document.querySelectorAll('[data-current-date]').forEach(x=>x.textContent=now.toLocaleDateString(undefined,{month:'short',day:'numeric',year:'numeric'}));document.querySelectorAll('[data-current-time]').forEach(x=>x.textContent=now.toLocaleTimeString(undefined,{hour:'2-digit',minute:'2-digit'}))}
function logout(){sessionStorage.removeItem('sihUser');location.href='/login'}
function requireLogin(){if(!sessionStorage.getItem('sihUser')){location.href='/login';return false}shellUser();navActive();return true}
function escJson(v){return esc(JSON.stringify(v,null,2))}

function setBusy(button, busy, label){
 if(!button)return;
 if(busy){
  if(!button.dataset.originalText)button.dataset.originalText=button.innerHTML;
  button.disabled=true;button.innerHTML='<span class="spinner" aria-hidden="true"></span>'+esc(label||'Processing…');
 }else{button.disabled=false;button.innerHTML=button.dataset.originalText||button.innerHTML;delete button.dataset.originalText;}
}
function showLoading(message='Processing…',steps=[]){
 let el=$('globalLoading');
 if(!el){el=document.createElement('div');el.id='globalLoading';el.className='loading-overlay';document.body.appendChild(el);}
 const rows=steps.length?steps.map((x,i)=>`<div class="loading-step ${i===0?'active':''}" data-load-step="${i}"><span class="step-icon">${i+1}</span><span>${esc(x)}</span></div>`).join(''):'';
 el.innerHTML=`<div class="loading-card"><div class="spinner large"></div><div class="loading-title">${esc(message)}</div><div class="loading-sub">Please wait while the workflow completes.</div>${rows?`<div class="loading-steps">${rows}</div>`:''}</div>`;
 el.classList.add('visible');
 return {next(i){document.querySelectorAll('[data-load-step]').forEach((x,n)=>x.classList.toggle('active',n===i));},hide(){el.classList.remove('visible');}};
}
