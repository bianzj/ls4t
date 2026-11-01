"use strict";
// All pages share the same two-level product hierarchy.
window.LS4T = {
  retrieval: {title:'反演工作台', description:'从热红外观测反演地表温度与组分温度。', tools:[
    ['surface','地表温度反演','双通道亮温与已知参数，输出逐观测 LST。'],
    ['components','地表组分温度反演','多视角观测，求解土壤与植被组分温度。'],
    ['batch','地表温度批处理（全链路）','按目录与年份管理解压、重整、LST 和组分反演任务。']]},
  normalization: {title:'归一化工作台', description:'将已有地表温度转换到统一的时间、角度或空间尺度。', tools:[
    ['time','时间归一化','给定日变化参数，转换到参考地方太阳时。'],
    ['angle','角度归一化','标定或输入角度系数，转换到参考观测方向。'],
    ['space','空间归一化','按目标网格映射与权重聚合已有温度。'],
    ['batch','归一化（批处理）','导入多个配置，独立运行并汇总各任务结果。']]}
};
(() => {
  const path=location.pathname.replace(/\/$/,'')||'/';
  const group=path.startsWith('/normalization')?'normalization':path.startsWith('/retrieval')||path==='/batch.html'||path==='/workbench.html'?'retrieval':null;
  const selected=path==='/batch.html'?'batch':path==='/workbench.html'?'components':path.split('/')[2];
  const host=document.getElementById('site-navigation');
  host.innerHTML=`<header class="site-header"><a class="site-brand" href="/">LS4T<span>地表温度反演与归一化工作台</span></a><nav aria-label="工作台"><a href="/retrieval" ${group==='retrieval'?'aria-current="true"':''}>反演工作台</a><a href="/normalization" ${group==='normalization'?'aria-current="true"':''}>归一化工作台</a></nav></header>`;
  if(group){
    const nav=document.createElement('nav');nav.className='tool-navigation';nav.setAttribute('aria-label',LS4T[group].title+'功能');
    for(const [key,title] of LS4T[group].tools){
      const a=document.createElement('a');a.href=`/${group}/${key}`;a.textContent=title;
      if(key===selected)a.setAttribute('aria-current','page');nav.append(a);
    }
    host.append(nav);
  }
})();
