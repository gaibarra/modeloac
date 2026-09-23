import {Row} from './resources';
export type MaintenanceEntry={key:string;resource:'historical'|'work-orders';row:Row;reference:string;title:string;date:string;status:string};
export function mergeMaintenance(orders:Row[],historical:Row[]):MaintenanceEntry[]{
 return [
  ...orders.map(row=>({key:`order-${row.id}`,resource:'work-orders' as const,row,reference:`OT-${row.id}`,title:String(row.title||''),date:String(row.completed_on||row.scheduled_on||''),status:String(row.status)})),
  ...historical.map(row=>({key:`historical-${row.id}`,resource:'historical' as const,row,reference:`Original #${row.legacy_id}`,title:String(row.description||''),date:String(row.performed_on||''),status:'completed'}))
 ].sort((a,b)=>b.date.localeCompare(a.date)||a.key.localeCompare(b.key));
}
export function filterMaintenance(entries:MaintenanceEntry[],search:string,origin:string,status:string){
 const normalize=(s:string)=>s.normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase();
 const query=normalize(search.trim());
 return entries.filter(e=>(!origin||e.resource===origin)&&(!status||e.status===status)&&normalize([e.reference,e.title,e.row.asset_code,e.row.location_name,e.row.technician,e.row.work_code].join(' ')).includes(query));
}
export async function loadMaintenance(fetchPage:(path:string)=>Promise<{results:Row[];next:unknown}>){
 const all=async(resource:string)=>{let rows:Row[]=[];for(let page=1;;page++){const data=await fetchPage(`${resource}/?page=${page}`);rows=rows.concat(data.results);if(!data.next)return rows;}};
 const [orders,historical]=await Promise.all([all('work-orders'),all('historical')]);
 return mergeMaintenance(orders,historical);
}
