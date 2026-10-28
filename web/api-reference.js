import {escapeHTML as esc} from './charts.js';
const root=document.querySelector('#api-endpoints');
try{
  const contract=await (await fetch('/api/openapi.json')).json();
  root.innerHTML=Object.entries(contract.paths).flatMap(([path,operations])=>Object.entries(operations).map(([method,op])=>{
    const content=op.requestBody?.content;
    return `<section class="card card-padding" style="margin:16px 0"><h2><span class="badge teal">${esc(method.toUpperCase())}</span> <code>${esc(path)}</code></h2><p class="text-small muted" style="margin-top:10px">${esc(op.summary||'')}${op.description?' · '+esc(op.description):''}</p>${op.parameters?.length?`<details class="advanced-options"><summary>Parâmetros</summary><div class="table-container"><table><thead><tr><th>Nome</th><th>Local</th><th>Obrigatório</th><th>Esquema</th></tr></thead><tbody>${op.parameters.map(p=>`<tr><td>${esc(p.name)}</td><td>${esc(p.in)}</td><td>${p.required?'Sim':'Não'}</td><td><code>${esc(JSON.stringify(p.schema))}</code></td></tr>`).join('')}</tbody></table></div></details>`:''}${content?`<details class="advanced-options"><summary>Corpo da requisição</summary><pre>${esc(JSON.stringify(content,null,2))}</pre></details>`:''}<details class="advanced-options"><summary>Respostas</summary><pre>${esc(JSON.stringify(op.responses,null,2))}</pre></details></section>`;
  })).join('')+`<section class="card card-padding"><h2>Esquemas dos dados</h2><pre>${esc(JSON.stringify(contract.components?.schemas||{},null,2))}</pre></section>`;
}catch{root.innerHTML='<div class="notice danger">Não foi possível carregar o contrato. Confira se a aplicação está aberta.</div>';}
