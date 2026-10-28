export const escapeHTML = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
export const money = cents => new Intl.NumberFormat('pt-BR', {style:'currency',currency:'BRL'}).format((cents || 0) / 100);
const shortMoney = cents => new Intl.NumberFormat('pt-BR', {notation:'compact',maximumFractionDigits:1}).format(cents / 100);
export const dateLabel = iso => iso ? new Intl.DateTimeFormat('pt-BR',{day:'2-digit',month:'short'}).format(new Date(iso.slice(0,10) + 'T12:00:00')) : '—';
export function barChart(rows, forecast = false) {
  if (!rows.length || !rows.some(r=>r.receitas_centavos || r.despesas_centavos)) return `<div class="chart-empty">Seu fluxo de caixa vai aparecer aqui<br><small>Importe uma planilha ou registre sua primeira movimentação.</small></div>`;
  const w=720,h=252,left=58,right=16,top=22,bottom=36,pw=w-left-right,ph=h-top-bottom;
  const maximum = Math.max(...rows.flatMap(r=>[r.receitas_centavos,r.despesas_centavos]),100);
  const magnitude = Math.pow(10, Math.floor(Math.log10(maximum)));
  const max = Math.ceil(maximum / magnitude * 2) / 2 * magnitude;
  const y = value => top + ph - value/max*ph;
  let svg='';
  for(let i=0;i<=4;i++) { const value=max*i/4; svg+=`<line x1="${left}" x2="${w-right}" y1="${y(value)}" y2="${y(value)}" stroke="#edf0ef"/><text x="${left-14}" y="${y(value)+4}" text-anchor="end" fill="#919b97" font-size="11">${shortMoney(value)}</text>`; }
  const slot=pw/rows.length,bw=Math.min(22,slot*.22),gap=6;
  rows.forEach((row,i)=>{
    const x=left+slot*(i+.5),label=row.label || new Intl.DateTimeFormat('pt-BR',{month:'short'}).format(new Date(row.mes+'-15T12:00:00')).replace('.','');
    svg+=`<g><rect x="${x-bw-gap/2}" y="${y(row.receitas_centavos)}" width="${bw}" height="${Math.max(0,row.receitas_centavos/max*ph)}" rx="4" fill="${forecast?'#66b9a9':'#2e9c8d'}"><title>${escapeHTML(label)} · Entradas: ${money(row.receitas_centavos)}</title></rect><rect x="${x+gap/2}" y="${y(row.despesas_centavos)}" width="${bw}" height="${Math.max(0,row.despesas_centavos/max*ph)}" rx="4" fill="#dce3e0"><title>${escapeHTML(label)} · Saídas: ${money(row.despesas_centavos)}</title></rect><text x="${x}" y="${h-10}" text-anchor="middle" fill="#7d8982" font-size="12">${escapeHTML(label)}</text></g>`;
  });
  return `<svg class="bar-chart" viewBox="0 0 ${w} ${h}" role="img" aria-label="Gráfico de entradas e saídas ${forecast?'previstas':'realizadas'} por período">${svg}</svg>`;
}
export function weeklyForecast(series) {
  const groups=[];
  series.forEach((row,i)=>{const n=Math.floor(i/7);if(!groups[n])groups[n]={label:dateLabel(row.data),receitas_centavos:0,despesas_centavos:0};groups[n].receitas_centavos+=row.receitas_centavos;groups[n].despesas_centavos+=row.despesas_centavos;});
  return groups;
}
export function lineChart(series, small = false, label = 'Evolução do saldo previsto') {
  if(!series.length)return '';
  const w=small?240:880,h=small?72:280,left=small?4:72,right=small?4:20,top=small?8:20,bottom=small?5:38;
  const values=series.map(r=>r.saldo_centavos),low=Math.min(...values),high=Math.max(...values),padding=Math.max((high-low)*.12,100),min=low-padding,max=high+padding,range=max-min;
  const x=i=>left+i/Math.max(series.length-1,1)*(w-left-right),y=v=>top+(1-(v-min)/range)*(h-top-bottom);
  const d=series.map((r,i)=>`${i?'L':'M'}${x(i).toFixed(2)},${y(r.saldo_centavos).toFixed(2)}`).join(' ');
  let axes='';
  if(!small){
    for(let i=0;i<4;i++){const value=min+range*i/3;axes+=`<line x1="${left}" x2="${w-right}" y1="${y(value)}" y2="${y(value)}" stroke="#edf0ef"/><text x="${left-12}" y="${y(value)+4}" text-anchor="end" fill="#8b9690" font-size="11">${shortMoney(value)}</text>`;}
    const indices=[0,Math.floor((series.length-1)/3),Math.floor((series.length-1)*2/3),series.length-1];
    indices.forEach(i=>axes+=`<text x="${x(i)}" y="${h-10}" text-anchor="middle" fill="#8b9690" font-size="11">${dateLabel(series[i].data)}</text>`);
  }
  return `<svg class="${small?'spark-chart':'line-chart'}" viewBox="0 0 ${w} ${h}" role="img" aria-label="${escapeHTML(label)}"><defs><linearGradient id="area-${small?'small':'large'}" x1="0" y1="0" x2="0" y2="1"><stop stop-color="#4cac96" stop-opacity="${small?'.16':'.2'}"/><stop offset="1" stop-color="#4cac96" stop-opacity="0"/></linearGradient></defs>${axes}<path d="${d} L${x(series.length-1)},${h-bottom} L${left},${h-bottom} Z" fill="url(#area-${small?'small':'large'})"/><path d="${d}" fill="none" stroke="#2e9c8d" stroke-width="${small?2:2.5}" stroke-linejoin="round" stroke-linecap="round"/>${small?'':series.filter((_,i)=>i%Math.max(1,Math.floor(series.length/12))===0).map(r=>{const i=series.indexOf(r);return `<circle cx="${x(i)}" cy="${y(r.saldo_centavos)}" r="3" fill="#2e9c8d"><title>${dateLabel(r.data)}: ${money(r.saldo_centavos)}</title></circle>`;}).join('')}</svg>`;
}
