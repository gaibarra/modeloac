#!/usr/bin/env python3
"""Prueba HTTPS con cuentas efímeras; no imprime ni conserva credenciales."""
import http.cookiejar,json,secrets,ssl,subprocess,urllib.request,urllib.error,re,sys
from pathlib import Path
root=Path(__file__).resolve().parent.parent
compose=['docker','compose','--env-file',str(root/'.env.production'),'-f',str(root/'compose.production.yml')]
base='https://modeloac.online'
nonce=secrets.token_hex(6);names=['deploy_admin_'+nonce,'deploy_viewer_'+nonce];password=secrets.token_urlsafe(32)
def db(code,payload):
    setup="import os;os.environ.setdefault('DJANGO_SETTINGS_MODULE','config.settings');import django;django.setup();import sys,json;from django.contrib.auth.models import User;data=json.load(sys.stdin);"
    subprocess.run(compose+['exec','-T','backend','python','-c',setup+code],input=json.dumps(payload),text=True,check=True,stdout=subprocess.DEVNULL)
def request(opener,path,method='GET',payload=None,headers=None):
    req=urllib.request.Request(base+path,data=None if payload is None else json.dumps(payload).encode(),method=method,headers={'Content-Type':'application/json',**(headers or {})})
    try:
        with opener.open(req,timeout=60) as r:return r.status,r.read(),r.headers
    except urllib.error.HTTPError as e:return e.code,e.read(),e.headers
class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs):return None
for origin in ['http://modeloac.online','http://www.modeloac.online','https://www.modeloac.online']:
    opener=urllib.request.build_opener(NoRedirect)
    try:opener.open(origin+'/api/health/?prueba=1',timeout=20);raise AssertionError('Se esperaba redirección')
    except urllib.error.HTTPError as r:
        assert r.code==301 and r.headers['Location']==base+'/api/health/?prueba=1',(origin,r.code)
public=urllib.request.build_opener()
assert request(public,'/')[0]==200
assert request(public,'/api/health/')[0]==200
assert request(public,'/django-static/admin/css/base.css')[0]==200
assert request(public,'/Modelo.jpg')[0]==200
assert request(public,'/api/assets/')[0]==403
assert request(public,'/api/source-document/1/')[0]==403
code,html,_=request(public,'/')
script=re.search(r'src="(/_next/static/[^\"]+\.js)"',html.decode())
assert script and request(public,script.group(1))[0]==200
created=False
try:
    db("from django.db import transaction;\nwith transaction.atomic():\n for i,name in enumerate(data['names']):\n  User.objects.create_user(name,password=data['password'],is_superuser=i==0,is_staff=i==0)\n",{'names':names,'password':password});created=True
    for idx,name in enumerate(names):
        cookies=http.cookiejar.CookieJar();opener=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookies))
        _,body,_=request(opener,'/api/csrf/');csrf=json.loads(body)['csrfToken']
        status,_,_=request(opener,'/api/login/','POST',{'username':name,'password':password},{'X-CSRFToken':csrf,'Origin':base});assert status==200,status
        assert any(c.name=='modeloac_session' and c.secure for c in cookies)
        assert any(c.name=='modeloac_csrf' and c.secure for c in cookies)
        status,body,_=request(opener,'/api/assets/');assert status==200 and json.loads(body)['count']>=318
        assert request(opener,'/api/historical/')[0]==200
        assert request(opener,'/api/source-document/1/')[0]==200
        assert request(opener,'/api/logout/','POST',{}, {'X-CSRFToken':'invalid','Origin':base})[0]==403
        _,body,_=request(opener,'/api/csrf/');csrf=json.loads(body)['csrfToken']
        if idx==1:
            assert request(opener,'/api/assets/','POST',{'code':'forbidden-'+nonce},{'X-CSRFToken':csrf,'Origin':base})[0]==403
        else:
            for fmt,magic in [('pdf',b'%PDF'),('xlsx',b'PK'),('csv',b'\xef\xbb\xbf')]:
                status,body,_=request(opener,'/api/reports/?kind=inventory&format='+fmt)
                assert status==200 and body.startswith(magic),fmt
        assert request(opener,'/api/logout/','POST',{}, {'X-CSRFToken':csrf,'Origin':base})[0]==200
        assert request(opener,'/api/me/')[0]==403
    print('HTTPS, redirecciones, estáticos, sesión segura, CSRF, roles, datos y PDF/Excel/CSV: correctos.')
finally:
    if created:db("User.objects.filter(username__in=data['names']).delete()",{'names':names})
