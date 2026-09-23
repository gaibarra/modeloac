#!/usr/bin/env python3
import hashlib,json,subprocess,sys
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
root=Path(__file__).resolve().parent.parent
baseline=root/'.work/deploy'
errors=[]
for name,entry in json.loads((baseline/'nginx-before.json').read_text()).items():
    if entry.get('unreadable'):continue
    p=Path(name)
    if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest()!=entry['sha256']:
        errors.append(f'Configuración distinta: {name}')
    elif (str(p.readlink()) if p.is_symlink() else None)!=entry['symlink']:
        errors.append(f'Enlace distinto: {name}')
rows=json.loads((baseline/'http-before.json').read_text())
def check(row):
    r=subprocess.run(['curl','-sS','--max-time','15','-o','/dev/null','-w','%{http_code}|%{redirect_url}|%{ssl_verify_result}',row['url']],capture_output=True,text=True)
    return {'url':row['url'],'result':r.stdout,'returncode':r.returncode,'unchanged':r.stdout==row['result'] and r.returncode==row['returncode']}
with ThreadPoolExecutor(max_workers=6) as pool:results=list(pool.map(check,rows))
for row in results:
    if not row['unchanged']:errors.append(f'Respuesta diferente: {row["url"]} -> {row["result"]}')
(baseline/'http-latest.json').write_text(json.dumps(results,indent=2))
if errors:
    print('\n'.join(errors),file=sys.stderr);sys.exit(1)
print(f'Configuraciones de otros sitios intactas; {len(results)} respuestas coinciden con el estado previo.')
