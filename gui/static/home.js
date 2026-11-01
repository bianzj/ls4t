"use strict";
const section=location.pathname.replaceAll('/','');
const groups=LS4T[section]?[section]:['retrieval','normalization'];
if(LS4T[section]){
  document.getElementById('home-title').textContent=LS4T[section].title;
  document.getElementById('home-description').textContent=LS4T[section].description;
  document.title='LS4T · '+LS4T[section].title;
  document.getElementById('directory').style.gridTemplateColumns='minmax(0, 1fr)';
}
for(const group of groups){
  const info=LS4T[group], panel=document.createElement('section');panel.className='directory-group';
  panel.innerHTML=`<h2><a href="/${group}">${info.title}</a></h2><p>${info.description}</p><ul class="directory-tools">${info.tools.map(([key,title,description])=>`<li><a href="/${group}/${key}"><strong>${title}</strong><span>${description}</span></a></li>`).join('')}</ul>`;
  document.getElementById('directory').append(panel);
}
