"use strict";
const $ = id => document.getElementById(id);
const pathname = location.pathname.replace(/\/+$/, '');
let config = null, result = null, resultInput = null, mode = pathname.includes("/normalization/") ? "normalization" : pathname.endsWith("/surface") ? "surface" : "retrieval", revision = 0;
const drafts = {};
const clone = value => JSON.parse(JSON.stringify(value));
const numeric = id => {
  const value = $(id).value.trim();
  if (!value || !Number.isFinite(Number(value))) throw new Error("请填写有效数值：" + id);
  return Number(value);
};
function node(tag, attrs = {}, ...children) {
  const e = document.createElement(tag);
  for (const [key,value] of Object.entries(attrs)) {
    if (key.startsWith("on")) e.addEventListener(key.slice(2), value);
    else if (key === "text") e.textContent = value;
    else if (key === "class") e.className = value;
    else if (value !== false && value != null) e.setAttribute(key, value === true ? "" : value);
  }
  for (const c of children.flat()) if(c != null) e.append(c);
  return e;
}
async function api(path, body) {
  const r = await fetch(path, body ? {method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(body)} : {});
  const data = await r.json();
  if (!r.ok) throw new Error(data.error || "请求失败");
  return data;
}
function error(message) { $("error").hidden = !message; $("error").textContent = message; }
function invalidate() {
  revision++;
  result = null;
  $("results").classList.add("stale");
  const exportButton = $("export-result");
  if (exportButton) exportButton.disabled = true;
  $("run-state").textContent = "输入已更新，请重新计算";
}
function collect() {
  if (!config) throw new Error("请先加载样例或导入配置");
  const p = clone(config);
  p.route = mode;
  if (mode === "normalization") {
    p.reference_vza=numeric("reference_vza");
    p.coefficient_mode=$("coefficient_mode").value;
    if(p.coefficient_mode==='supplied') p.coefficient_k=numeric("coefficient_k");
    else delete p.coefficient_k;
    return p;
  }
  p.fixed={...p.fixed,lai:numeric("lai"),tcwv_cm:numeric("tcwv_cm"),soil_emissivity:[numeric("soil1"),numeric("soil2")],vegetation_emissivity:[numeric("veg1"),numeric("veg2")],hotspot:numeric("hotspot")};
  if(mode==='surface') {
    for(const key of ['components','prior_strength','prior_sigma_k','prior_k','optimize','reference_vza','reference_raa'])delete p[key];
    return p;
  }
  for(const key of ["components","prior_strength","prior_sigma_k"])p[key]=numeric(key);
  p.prior_k=$("prior_k").value.split(/[,，]/).map(v=>v.trim()?Number(v):NaN);
  if(p.prior_k.length!==p.components || p.prior_k.some(v=>!Number.isFinite(v)))throw new Error("温度先验数量需与组分数一致");
  p.optimize=$("optimize").checked;
  delete p.reference_vza;delete p.reference_raa;
  return p;
}
function emptyResult(){
  $("results").classList.remove("stale");
  $("results").replaceChildren(node("div",{class:"empty-result"},node("h2",{text:mode==='surface'?"地表温度反演结果":mode==='retrieval'?"组分反演结果":"角度归一化结果"}),node("p",{text:"本路线尚未计算。配置输入后点击运行。"})));
}
function showConfig(p, restoreDraft = false) {
  if(!p || typeof p!=='object' || !Array.isArray(p.observations) || (!restoreDraft && p.observations.length<(mode==='retrieval'?2:1)) || p.observations.length>64)throw new Error("请提供当前路线的有效观测配置");
  if(p.route && p.route!==mode)throw new Error("配置属于另一条路线，请先切换路线再导入");
  if(!p.observations.every(o=>o && ['SLSTR','AHI'].includes(o.sensor)))throw new Error("请检查观测传感器");
  if(mode!=='normalization' && (!p.fixed || !['soil_emissivity','vegetation_emissivity'].every(k=>Array.isArray(p.fixed[k]) && p.fixed[k].length===2) || !['lai','tcwv_cm'].every(k=>Number.isFinite(p.fixed[k])) || (p.prior_k!=null&&!Array.isArray(p.prior_k))))throw new Error("请检查固定参数、发射率和温度先验");
  if(!restoreDraft && mode==='normalization' && !p.observations.every(o=>Number.isFinite(o.lst_k)))throw new Error("归一化路线需要已有 LST，不能直接输入亮温");
  invalidate();config=clone(p);config.route=mode;
  if(mode!=='normalization'){
    const f=p.fixed;
    for(const key of ['lai','tcwv_cm','hotspot'])$(key).value=f[key]??.2;
    ['soil1','soil2','veg1','veg2'].forEach((key,i)=>$(key).value=i<2?f.soil_emissivity[i]:f.vegetation_emissivity[i-2]);
    for(const key of ['components','prior_strength','prior_sigma_k'])$(key).value=p[key]??({components:2,prior_sigma_k:10}[key]||0);
    $("prior_k").value=(p.prior_k||Array(Number($("components").value)).fill(280)).join(', ');
    $("optimize").checked=p.optimize!==false;
  }else{
    $("reference_vza").value=p.reference_vza??0;
    $("coefficient_mode").value=p.coefficient_mode||'fit';
    $("coefficient_k").value=p.coefficient_k??0;
  }
  $("source-label").textContent=p.provenance?.label||"用户配置 · 当前路线独立运行";
  $("sample-note").hidden=!p.provenance?.limitations;
  $("sample-note").textContent=mode!=='normalization'?"真实亮温样例；植被发射率为设定值，时间与水汽沿用归档编码假设。仅用于流程测试。":"已有 LST 样例；SLSTR 双视角标定单角度系数，向 AHI 迁移仅作探索性检验，不是地面精度验证。";
  $("provenance").textContent=JSON.stringify(p.provenance||{},null,2);
  routeLayout();renderObservations();emptyResult();
  $("advanced-json").value=JSON.stringify(p,null,2);
}
function routeLayout(){
  const angular=mode==='normalization';
  for(const [id,hidden]of [['fixed-section',angular],['optimization-section',mode!=='retrieval'],['angular-section',!angular]]){
    $(id).hidden=hidden;$(id).querySelectorAll('input,select').forEach(e=>e.disabled=hidden);
  }
  $("coefficient-field").hidden=$("coefficient_mode").value!=='supplied';
  $("coefficient_k").disabled=!angular||$("coefficient_mode").value!=='supplied';
  const surface=mode==='surface';
  $('observations-title').textContent=surface?'热红外观测':'多视角观测';
  $('fixed-hint').textContent=surface?'双波段参数用于分裂窗大气校正。传感器独立发射率可在高级配置中指定。':'双波段输入用于大气校正；组分分解使用波段 1。传感器独立发射率可在高级配置中指定。';
  $('components').closest('label').hidden=surface;$('components').disabled=surface||angular;
  $('hotspot').closest('label').hidden=surface;
  $("route-title").textContent=angular?'角度归一化':surface?'地表温度反演':'地表组分温度反演';
  document.title='LS4T · '+$('route-title').textContent;
  $("route-description").textContent=angular?'直接处理已有 LST，独立标定或输入角度系数，转换到参考天顶角。':surface?'已知 LAI、水汽和双波段发射率，由亮温反演地表温度。':'固定已知参数，求解土壤与植被温度；优化设置仅用于本路线。';
  $("run").textContent=$("run-top").textContent=angular?'开始角度归一化':surface?'开始地表温度反演':'开始组分反演';
  $("observation-hint").textContent=angular?'输入已有 LST。标定观测需同地表、同传感器、近同时；已有系数模式可处理单条观测。':surface?'逐观测独立计算 LST，已有 LST 输入保留原值。':'参与拟合的观测求解组分温度；留出观测仅检验。观测应同地表且时间跨度不超过 10 分钟。';
  document.querySelectorAll('[data-mode]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.mode===mode)));
}
async function switchRoute(next){
  if(next===mode)return;
  if(config)drafts[mode]={config:clone(config),fields:[...$("parameters-form").querySelectorAll('input,select')].map(e=>({id:e.id,value:e.value,checked:e.checked})),result,resultInput};
  revision++;mode=next;config=null;result=null;resultInput=null;error('');routeLayout();emptyResult();$("observation-list").replaceChildren();
  if(drafts[next]){
    // Internal drafts may be incomplete; validate only when importing or running.
    const saved=drafts[next];showConfig(saved.config, true);
    saved.fields.forEach(f=>{if($(f.id)){$(f.id).value=f.value;$(f.id).checked=f.checked;}});
    routeLayout();renderObservations();result=saved.result;resultInput=saved.resultInput;
    if(result)renderResult(result,resultInput);
    $("run-state").textContent=result?'已恢复本路线结果':'已恢复本路线配置';
  }else await loadSample();
}
function inputField(obs, key, text, options={}) {
  const display = options.text || obs[key] == null ? (obs[key] ?? "") : Number(Number(obs[key]).toPrecision(9));
  const input = node("input", {type:options.text ? "text":"number", step:"any", value:display, "aria-label":`${obs.name || obs.sensor} ${text}`});
  input.addEventListener("input",()=>{
    obs[key] = options.text ? input.value : (input.value.trim() ? Number(input.value) : null);
    invalidate();
  });
  return node("label",{class:options.wide || ""},text,input);
}
function renderObservations() {
  $("observation-list").replaceChildren(...config.observations.map((o,i)=>{
    const fit = node("input",{type:"checkbox",checked:o.use_for_fit!==false,"aria-label":`${o.name || o.sensor} ${mode==='retrieval'?'参与拟合':'参与标定'}`});
    fit.addEventListener("change",()=>{o.use_for_fit=fit.checked;invalidate();});
    const name = node("input",{value:o.name || o.sensor,"aria-label":`观测 ${i+1} 名称`});
    name.addEventListener("input",()=>{o.name=name.value;invalidate();});
    const remove=node("button",{class:"remove",text:"移除",onclick:()=>{config.observations.splice(i,1);renderObservations();invalidate();}});
    const sensor=node("select",{"aria-label":`观测 ${i+1} 传感器`},...['SLSTR','AHI'].map(s=>node("option",{value:s,text:s,selected:o.sensor===s})));
    sensor.addEventListener("change",()=>{o.sensor=sensor.value;o.wavelength_um=sensor.value==='AHI'?10.4:10.85;o.coefficient_file='';renderObservations();invalidate();});
    const isLst=o.lst_k != null;
    const kind=node("select",{"aria-label":`观测 ${i+1} 输入类型`},node("option",{value:"bt",text:"双通道亮温",selected:!isLst}),node("option",{value:"lst",text:"已有 LST",selected:isLst}));
    kind.addEventListener("change",()=>{if(kind.value==='bt'){delete o.lst_k;o.bt1_k??=280;o.bt2_k??=279;}else{o.lst_k=280;}renderObservations();invalidate();});
    const fields=mode==='normalization'?node("div",{class:"obs-fields"},node("label",{},"传感器",sensor),inputField(o,"lst_k","LST / K"),inputField(o,"vza","观测天顶角 °"),inputField(o,"sigma_k","不确定度 K"),inputField(o,"time_utc","观测时间（带时区）",{text:true,wide:"span2"})):node("div",{class:"obs-fields"},node("label",{},"传感器",sensor),node("label",{},"输入类型",kind),
      inputField(o,"vza","观测天顶角 °"),...(mode==='surface'?[]:[inputField(o,"sza","太阳天顶角 °"),inputField(o,"raa","相对方位角 °"),inputField(o,"wavelength_um","波长 µm")]),
      ...(isLst ? [inputField(o,"lst_k","LST / K",{wide:"span2"})]:[inputField(o,"bt1_k","BT1 / K"),inputField(o,"bt2_k","BT2 / K")]),
      inputField(o,"sigma_k","不确定度 K"),inputField(o,"time_utc","观测时间（带时区）",{text:true,wide:"span3"}));
    if(mode!=='normalization' && !isLst) fields.append(inputField(o,"coefficient_file","该传感器的分裂窗系数 NPZ",{text:true,wide:"span3"}));
    return node("div",{class:"observation"},node("div",{class:"obs-head"},name,(mode==='retrieval'||(mode==='normalization'&&$('coefficient_mode').value==='fit')?node("label",{class:"check"},fit,mode==='retrieval'?'参与拟合':'参与标定'):null),remove),fields);
  }));
}
function download(filename, value) {
  const url=URL.createObjectURL(new Blob([JSON.stringify(value,null,2)],{type:"application/json"}));
  const a=node("a",{href:url,download:filename});a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
}
const fmt = n => n == null ? "—" : Number(n).toFixed(3);
function renderResult(r, request) {
  if(r.route==='surface'){
    const table=node('table',{},node('thead',{},node('tr',{},...['观测','传感器','LST / K','计算说明'].map(t=>node('th',{text:t})))),node('tbody',{},...r.observations.map(o=>node('tr',{},...[o.name||o.sensor,o.sensor,fmt(o.lst_k),o.method].map(v=>node('td',{text:v}))))));
    $('results').classList.remove('stale');$('results').replaceChildren(node('div',{class:'result-top'},node('h2',{text:'地表温度反演结果'}),node('button',{id:'export-result',text:'导出本路线结果',onclick:()=>download('ls4t-surface-result.json',{input:request,result:r})})),node('div',{class:'table-wrap'},table),node('ul',{class:'warnings'},...r.warnings.map(t=>node('li',{text:t}))));return;
  }
  const angular=r.route==='normalization';
  const metrics=angular?[node("div",{class:"metric"},node("span",{text:"角度系数 c"}),node("strong",{text:fmt(r.coefficient_k)}),node("small",{text:"K"})),node("div",{class:"metric"},node("span",{text:"参考天顶角"}),node("strong",{text:r.reference_vza+'°'}))]:r.temperature_k.map((t,i)=>node("div",{class:`metric ${i===r.temperature_k.length-1?'leaf':'soil'}`},node("span",{text:r.component_names[i]}),node("strong",{text:t.toFixed(2)}),node("small",{text:"K"}),node("span",{text:`初始反演 ${r.baseline_temperature_k[i].toFixed(2)} K`})));
  if(r.heldout_count)metrics.push(node("div",{class:"metric"},node("span",{text:"留出一致性 RMSE"}),node("strong",{text:fmt(r.heldout_rmse_k)}),node("small",{text:"K"})));
  const header=angular?['观测','观测角 °','输入 LST / K','修正量 / K','归一化 LST / K']:['观测','用途','LST / K','模型 / K','残差 / K'];
  const table=node("table",{},node("thead",{},node("tr",{},...header.map(t=>node("th",{text:t})))),node("tbody",{},...r.observations.map(o=>node("tr",{},...(angular?[o.name||o.sensor,fmt(o.vza),fmt(o.lst_k),fmt(o.correction_k),fmt(o.normalized_k)]:[o.name||o.sensor,o.use_for_fit===false?'留出':'拟合',fmt(o.lst_k),fmt(o.predicted_k),fmt(o.residual_k)]).map((v,i)=>node("td",{text:v,class:angular&&i===4?'normalized':''}))))));
  $("results").classList.remove("stale");
  $("results").replaceChildren(node("div",{class:"result-top"},node("h2",{text:angular?'角度归一化结果':'组分温度结果'}),node("button",{id:"export-result",text:"导出本路线结果",onclick:()=>download(`ls4t-${r.route}-result.json`,{input:request,result:r})})),node("div",{class:"metrics"},...metrics),node("div",{class:"diagnostics"},node("span",{text:`${angular?'标定':'拟合'} RMSE ${fmt(r.fit_rmse_k)} K`}),node("span",{text:`条件数 ${fmt(r.condition_number)}`}),node("span",{text:`${angular?'标定':'拟合'}观测 ${r.fit_count} 条`})),node("div",{class:"table-wrap"},table),node("ul",{class:"warnings"},...r.warnings.map(t=>node("li",{text:t}))));
}
async function run(event) {
  event.preventDefault();error("");
  const rev=revision;
  try {
    const payload=collect();
    $("run").disabled=true;$("run-top").disabled=true;$("run-state").textContent='正在计算…';
    const data=await api(`/api/${mode}/run`,payload);
    if(rev!==revision)return;
    result=data;resultInput=payload;renderResult(data,payload);$("run-state").textContent='计算完成';
  }catch(e){if(rev===revision){error(e.message);$("run-state").textContent="未完成，请检查输入";}}
  finally{$("run").disabled=false;$("run-top").disabled=false;}
}
async function loadSample(){
  const route=mode;
  try{error("");const p=await api(route!=='normalization'?'/api/workbench/sample':'/api/normalization/sample');if(route!==mode)return;if(route==='surface'){p.route='surface';for(const key of ['components','prior_strength','prior_sigma_k','prior_k','optimize'])delete p[key];}showConfig(p);$("run-state").textContent="本路线样例已载入，等待计算";}catch(e){if(route===mode)error(e.message);}
}
$("parameters-form").addEventListener("submit",run);
$("run-top").onclick=()=>$("parameters-form").requestSubmit();
$("parameters-form").addEventListener("input",invalidate);
$("components").addEventListener("change",()=>{$("prior_k").value=Array(numeric("components")).fill(280).join(", ");invalidate();});
$("nadir").onclick=()=>{$("reference_vza").value=0;invalidate();};
$("load-sample").onclick=loadSample;
$("export").onclick=()=>{try{download(`ls4t-${mode}-config.json`,collect());}catch(e){error(e.message);}};
$("import").onclick=()=>$("import-file").click();
$("import-file").onchange=async e=>{try{const f=e.target.files[0];if(f){if(f.size>2e6)throw new Error("配置文件超过 2 MB");showConfig(JSON.parse(await f.text()));error("");}}catch(err){error(err.message);}finally{e.target.value="";}};
$("apply-json").onclick=()=>{try{showConfig(JSON.parse($("advanced-json").value));error("");}catch(e){error(e.message);}};
document.querySelector(".advanced").addEventListener("toggle",e=>{if(e.target.open)try{$("advanced-json").value=JSON.stringify(collect(),null,2);}catch(err){error(err.message);}});
$("add-observation").onclick=()=>{if(!config)return;if(config.observations.length>=64){error("最多支持 64 条观测");return;}config.observations.push({sensor:"AHI",name:"新增观测",lst_k:280,vza:40,sza:40,raa:90,wavelength_um:10.4,sigma_k:1,use_for_fit:false,time_utc:config.observations[0]?.time_utc || ""});renderObservations();invalidate();};
$("coefficient_mode").addEventListener('change',()=>{routeLayout();renderObservations();invalidate();});
document.querySelectorAll("[data-mode]").forEach(button=>button.addEventListener('click',()=>switchRoute(button.dataset.mode)));
window.addEventListener('pagehide',()=>{
  if(!config)return;
  try{sessionStorage.setItem('ls4t-tool-'+mode,JSON.stringify({config,fields:[...$('parameters-form').querySelectorAll('input,select')].map(e=>({id:e.id,value:e.value,checked:e.checked})),result,resultInput}));}catch{}
});
routeLayout();emptyResult();
try{
  const saved=JSON.parse(sessionStorage.getItem('ls4t-tool-'+mode)||'null');
  if(saved){showConfig(saved.config,true);saved.fields.forEach(f=>{if($(f.id)){$(f.id).value=f.value;$(f.id).checked=f.checked;}});routeLayout();renderObservations();result=saved.result;resultInput=saved.resultInput;if(result)renderResult(result,resultInput);$('run-state').textContent=result?'已恢复本路线结果':'已恢复本路线配置';}
  else loadSample();
}catch{loadSample();}
