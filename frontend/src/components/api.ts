export async function api(path:string, options:RequestInit={}) {
 const headers:Record<string,string>={'Content-Type':'application/json',...(options.headers as Record<string,string>||{})};
 if(options.method && options.method!=='GET') {
  const r=await fetch('/api/csrf/',{credentials:'same-origin'});
  if(!r.ok) throw new Error('No se pudo validar la sesión.');
  headers['X-CSRFToken']=(await r.json()).csrfToken;
 }
 const r=await fetch(`/api/${path}`,{...options,headers,credentials:'same-origin',cache:'no-store'});
 if(!r.ok){const d=await r.json().catch(()=>({detail:'No se pudo conectar con el servidor.'}));throw new Error(typeof d.detail==='string'?d.detail:Object.entries(d).map(([key,value])=>`${key}: ${Array.isArray(value)?value.join(' '):String(value)}`).join(' · '));}
 if(r.status===204)return null;
 return r.json();
}
