import {test,expect} from '@playwright/test';
import {mergeMaintenance,filterMaintenance,loadMaintenance} from '../src/components/maintenance';
test('Conserva ambos orígenes, IDs coincidentes y posibles repeticiones',()=>{
 const entries=mergeMaintenance([{id:1,title:'Servicio nuevo',completed_on:'2026-09-22',status:'completed'},{id:2,title:'Pendiente',scheduled_on:'2026-10-01',status:'scheduled'}],[{id:1,legacy_id:10,description:'Limpieza',performed_on:'2026-08-10',asset_code:'ee452',location_name:'Salón',possible_duplicate_of:9}]);
 expect(entries).toHaveLength(3);expect(new Set(entries.map(e=>e.key)).size).toBe(3);
 expect(filterMaintenance(entries,'','','completed')).toHaveLength(2);
 expect(filterMaintenance(entries,'salon','historical','completed')[0].row.possible_duplicate_of).toBe(9);
 expect(filterMaintenance(entries,'ee452','work-orders','')).toHaveLength(0);
 expect(entries[0].reference).toBe('OT-2');
});
test('Carga todas las páginas sin truncar el histórico y no oculta fallos',async()=>{
 const calls:string[]=[];
 const rows=await loadMaintenance(async path=>{calls.push(path);return path.startsWith('work-orders')?{results:[],next:null}:path.endsWith('page=1')?{results:[{id:1}],next:'page2'}:{results:[{id:2}],next:null};});
 expect(rows).toHaveLength(2);expect(calls).toContain('historical/?page=2');
 await expect(loadMaintenance(async()=>{throw Error('Sin conexión')})).rejects.toThrow('Sin conexión');
});
