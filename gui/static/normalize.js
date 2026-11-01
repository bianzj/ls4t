"use strict";
const $=id=>document.getElementById(id);
const kind=location.pathname.split('/').filter(Boolean).pop();
const title={time:'时间归一化',space:'空间归一化',batch:'归一化（批处理）'}[kind];
const route=kind==='batch'?'normalization-batch':kind;
let jobs=[], provenance=null, result=null, revision=0;
document.title='LS4T · '+title;$('tool-title').textContent=title;
$('tool-description').textContent=LS4T.normalization.tools.find(t=>t[0]===kind)[2];
$('run-normalize').textContent='开始'+title;
for(const key of ['time','space','batch']){
  const element=$(key+'-fields');element.hidden=key!==kind;
  element.querySelectorAll('input').forEach(e=>e.disabled=key!==kind);
}
$('rows-input').hidden=kind==='batch';$('observations-text').disabled=kind==='batch';$('job-list').hidden=kind!=='batch';
$('input-title').textContent=kind==='batch'?'待处理配置':'观测数据';
$('columns-label').textContent=kind==='time'?'每行：LST (K), 观测地方太阳时 (h)':'每行：LST (K), 目标行号, 目标列号, 权重';
$('input-note').textContent='用逗号、制表符或空格分隔，无表头。可从表格复制粘贴；最多 4096 行。';
function message(s){$('error').hidden=!s;$('error').textContent=s;}
function invalidate(){revision++;result=null;$('results').replaceChildren();$('status').textContent='配置已更新，等待运行';message('');}
function number(id){const s=$(id).value.trim();if(!s||!Number.isFinite(Number(s)))throw Error('请填写有效数值');return Number(s);}
function config(){
  if(kind==='batch')return {route,jobs};
  const rows=$('observations-text').value.trim().split(/\r?\n/).filter(s=>s.trim()).map((s,i)=>{
    const fields=s.trim().split(/[,，\t ]+/);
    if(fields.length!==(kind==='time'?2:4)||fields.some(x=>!x||!Number.isFinite(Number(x))))throw Error(`第 ${i+1} 行列数或数值无效`);
    const v=fields.map(Number);return kind==='time'?{lst_k:v[0],hour:v[1]}:{lst_k:v[0],row:v[1],column:v[2],weight:v[3]};
  });
  return kind==='time'?{route,reference_hour:number('reference-hour'),amplitude_k:number('amplitude'),peak_hour:number('peak-hour'),observations:rows,provenance}:{route,target_shape:[number('grid-rows'),number('grid-columns')],observations:rows,provenance};
}
function showJobs(){
  $('job-list').replaceChildren();
  jobs.forEach((job,i)=>{
    const div=document.createElement('p'), button=document.createElement('button');
    div.append(`${i+1}. ${job?.name||job?.route||'无效配置'} `);button.type='button';button.textContent='移除';
    button.onclick=()=>{jobs.splice(i,1);invalidate();showJobs();};div.append(button);$('job-list').append(div);
  });
  if(!jobs.length)$('job-list').textContent='选择配置文件或加载演示样例。';
}
function apply(p){
  if(!p||typeof p!=='object'||p.route!==route)throw Error('配置不属于当前功能，请进入对应页面导入');
  if(kind==='batch'){
    if(!Array.isArray(p.jobs)||p.jobs.length>64)throw Error('批处理配置需要 jobs 数组，最多 64 项');
    jobs=p.jobs;showJobs();
  }else{
    if(!Array.isArray(p.observations)||p.observations.length>4096||p.observations.some(o=>!o||typeof o!=='object'))throw Error('观测配置无效');
    const required=kind==='time'?['lst_k','hour']:['lst_k','row','column','weight'];
    if(p.observations.some(o=>required.some(k=>!Number.isFinite(o[k]))))throw Error('观测中存在缺失或无效数值');
    if(kind==='time'){
      if(['reference_hour','amplitude_k','peak_hour'].some(k=>!Number.isFinite(p[k])))throw Error('时间参数无效');
      $('reference-hour').value=p.reference_hour;$('amplitude').value=p.amplitude_k;$('peak-hour').value=p.peak_hour;
    }else{
      if(!Array.isArray(p.target_shape)||p.target_shape.length!==2||p.target_shape.some(x=>!Number.isInteger(x)||x<1||x>256))throw Error('目标网格维数无效');
      $('grid-rows').value=p.target_shape[0];$('grid-columns').value=p.target_shape[1];
    }
    $('observations-text').value=p.observations.map(o=>required.map(k=>o[k]).join(', ')).join('\n');
  }
  provenance=p.provenance||null;$('provenance-label').textContent=provenance?.label||'用户配置';invalidate();
}
function example(){
  const time={route:'time',reference_hour:13.5,amplitude_k:10,peak_hour:14,observations:[{lst_k:295,hour:9},{lst_k:303,hour:12},{lst_k:304,hour:15}]};
  const space={route:'space',target_shape:[2,2],observations:[{lst_k:300,row:0,column:0,weight:1},{lst_k:304,row:0,column:0,weight:3},{lst_k:296,row:1,column:1,weight:1}]};
  apply({...({time,space,batch:{route,jobs:[{...time,name:'时间演示'},{...space,name:'空间演示'}]}}[kind]),provenance:{label:'受控演示数据 · 用于功能测试，不代表真实卫星检验结果'}});
}
function download(name,value){const url=URL.createObjectURL(new Blob([JSON.stringify(value,null,2)],{type:'application/json'}));const a=document.createElement('a');a.href=url;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}
function table(headers, rows){
  const wrap=document.createElement('div');wrap.className='table-wrap';const t=document.createElement('table'), head=document.createElement('thead'),body=document.createElement('tbody');
  const tr=document.createElement('tr');headers.forEach(h=>{const c=document.createElement('th');c.textContent=h;tr.append(c);});head.append(tr);
  for(const row of rows){const tr=document.createElement('tr');for(const x of row){const c=document.createElement('td');c.textContent=x??'缺测';tr.append(c);}body.append(tr);}
  t.append(head,body);wrap.append(t);return wrap;
}
function render(r,p){
  $('results').replaceChildren();const h=document.createElement('h2');h.textContent=title+'结果';$('results').append(h);
  const exportButton=document.createElement('button');exportButton.textContent='导出本次结果';exportButton.onclick=()=>download(`ls4t-${route}-result.json`,{input:p,result:r});$('results').append(exportButton);
  const fmt=x=>x==null?'缺测':Number(x).toFixed(3);
  if(kind==='time')$('results').append(table(['观测时刻 / h','输入 LST / K','修正量 / K','归一化 LST / K'],r.observations.map(o=>[o.hour,fmt(o.lst_k),fmt(o.correction_k),fmt(o.normalized_k)])));
  if(kind==='space'){
    const rows=[];r.grid_k.forEach((row,i)=>row.forEach((v,j)=>rows.push([i,j,fmt(v),r.support[i][j]])));
    $('results').append(table(['目标行号','目标列号','聚合 LST / K','权重和'],rows));
  }
  if(kind==='batch')$('results').append(table(['任务','状态','说明'],r.jobs.map(j=>[j.name,j.status==='done'?'已完成':'失败',j.error||'结果已纳入统一导出'])));
  for(const w of r.warnings||[]){const e=document.createElement('p');e.textContent=w;$('results').append(e);}
}
$('normalize-form').addEventListener('input',invalidate);
$('normalize-form').onsubmit=async e=>{
  e.preventDefault();const rev=revision;message('');result=null;$('results').replaceChildren();
  try{
    const p=config();$('run-normalize').disabled=true;$('status').textContent='正在计算…';
    const response=await fetch(kind==='batch'?'/api/normalization/batch':`/api/${kind}/run`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(p)});
    const r=await response.json();if(!response.ok)throw Error(r.error||'计算失败');if(rev!==revision)return;
    result={input:p,result:r};render(r,p);$('status').textContent=kind==='batch'?`完成 ${r.done} 项，失败 ${r.failed} 项`:'计算完成';
  }catch(e){if(rev===revision){message(e.message);$('status').textContent='未完成，请检查输入';}}
  finally{$('run-normalize').disabled=false;}
};
$('example').onclick=example;$('export-config').onclick=()=>{try{download(`ls4t-${route}-config.json`,config());}catch(e){message(e.message);}};
$('import').onclick=()=>$('config-file').click();
$('config-file').onchange=async e=>{try{const f=e.target.files[0];if(f){if(f.size>2e6)throw Error('配置文件超过 2 MB');apply(JSON.parse(await f.text()));}}catch(e){message(e.message);}finally{$('config-file').value='';}};
$('batch-files').onchange=async e=>{
  try{const files=[...e.target.files];if(jobs.length+files.length>64)throw Error('最多支持 64 个配置');const incoming=[];
    for(const f of files){if(f.size>2e6)throw Error(f.name+' 超过 2 MB');const p=JSON.parse(await f.text());if(!p||!['time','space','normalization'].includes(p.route))throw Error(f.name+' 不是独立归一化配置');incoming.push({...p,name:p.name||f.name});}
    jobs.push(...incoming);invalidate();showJobs();provenance=null;$('provenance-label').textContent='用户导入配置';
  }catch(e){message(e.message);}finally{e.target.value='';}
};
$('clear-jobs').onclick=()=>{jobs=[];invalidate();showJobs();};
// Preserve raw values too, so an incomplete draft survives workspace navigation.
window.addEventListener('pagehide',()=>{try{sessionStorage.setItem('ls4t-tool-'+route,JSON.stringify({fields:[...document.querySelectorAll('#normalize-form input:not([type=file]),textarea')].map(e=>[e.id,e.value]),jobs,provenance,result}));}catch{}});
try{
  const saved=JSON.parse(sessionStorage.getItem('ls4t-tool-'+route)||'null');
  if(saved){saved.fields.forEach(([id,value])=>$(id).value=value);jobs=saved.jobs;provenance=saved.provenance;result=saved.result;showJobs();$('provenance-label').textContent=provenance?.label||'已恢复配置';if(result)render(result.result,result.input);}
  else if(kind==='batch')showJobs();else example();
}catch{example();}
