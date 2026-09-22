import csv,io,json
from datetime import date,timedelta
from pathlib import Path
from django.test import TestCase
from django.contrib.auth.models import User,Group
from django.core.management import call_command
from django.conf import settings
from rest_framework.test import APIClient
from .models import Asset,Location,TechnicalModel,WorkOrder,SourceRecord,AuditEvent,HistoricalService

class InventoryTests(TestCase):
    def setUp(self):
        self.admin=User.objects.create_superuser('admin',password='local-test-password-123')
        self.viewer=User.objects.create_user('viewer',password='local-test-password-123')
        self.tech=User.objects.create_user('tech',password='local-test-password-123')
        self.tech.groups.add(Group.objects.create(name='Mantenimiento'))
        self.client=APIClient();self.client.force_authenticate(self.admin)
        self.asset=Asset.objects.create(code='TEST-ee1',maintenance_interval_days=90)
    def test_all_operational_endpoints_require_auth(self):
        client=APIClient()
        for url in ['assets/','locations/','models/','suppliers/','work-orders/','acquisitions/','sources/','audit/','dashboard/','historical/','reports/','source-document/1/']:
            self.assertIn(client.get('/api/'+url).status_code,[401,403],url)
    def test_permissions_are_enforced_in_backend(self):
        self.client.force_authenticate(self.viewer)
        self.assertEqual(self.client.get('/api/assets/').status_code,200)
        self.assertEqual(self.client.post('/api/assets/',{'code':'NO'}).status_code,403)
        self.client.force_authenticate(self.tech)
        self.assertEqual(self.client.patch(f'/api/assets/{self.asset.pk}/',{'status':'retired'}).status_code,403)
        self.assertEqual(self.client.post('/api/work-orders/',{'asset':self.asset.id,'title':'Revisión','scheduled_on':date.today().isoformat()}).status_code,201)
    def test_duplicate_asset_rejected_and_deletion_disabled(self):
        self.assertEqual(self.client.post('/api/assets/',{'code':self.asset.code}).status_code,400)
        self.assertEqual(self.client.delete(f'/api/assets/{self.asset.pk}/').status_code,405)
    def test_closing_preventive_sets_next_date_and_audit(self):
        done=date.today()-timedelta(days=1)
        payload={'asset':self.asset.pk,'title':'Preventivo','kind':'preventive','status':'completed','scheduled_on':done.isoformat(),'completed_on':done.isoformat(),'resolution':'Limpieza y prueba','cost':'250.50'}
        r=self.client.post('/api/work-orders/',payload,format='json');self.assertEqual(r.status_code,201,r.data)
        self.asset.refresh_from_db();self.assertEqual(self.asset.next_maintenance,done+timedelta(days=90));self.assertEqual(self.asset.status,'unknown')
        self.assertTrue(AuditEvent.objects.filter(resource='work-orders').exists())
        self.assertEqual(self.client.patch(f"/api/work-orders/{r.data['id']}/",{'cost':'1.00'}).status_code,400)
    def test_cannot_close_without_date_and_resolution(self):
        r=self.client.post('/api/work-orders/',{'asset':self.asset.pk,'title':'Incompleta','status':'completed','scheduled_on':date.today().isoformat()})
        self.assertEqual(r.status_code,400)
        self.assertEqual(WorkOrder.objects.count(),0)
    def test_invalid_dates_and_negative_cost_rejected(self):
        for payload in [{'purchase_cost':'-1'},{'acquired_on':'0000-00-00'},{'maintenance_interval_days':0},{'acquired_on':'2026-09-22','warranty_until':'2025-01-01'}]:
            r=self.client.patch(f'/api/assets/{self.asset.pk}/',payload);self.assertEqual(r.status_code,400,r.data)
        self.assertEqual(self.client.get('/api/work-orders/?from=not-a-date').status_code,400)
    def test_exports_formats_and_formula_neutralization(self):
        self.asset.code='=HYPERLINK("https://example.invalid")';self.asset.save()
        for kind in ['inventory','maintenance','warranty','quality','costs','acquisitions','historical']:
            for fmt in ['csv','xlsx','pdf']:
                r=self.client.get(f'/api/reports/?kind={kind}&format={fmt}');self.assertEqual(r.status_code,200,(kind,fmt))
                if fmt=='pdf':self.assertTrue(r.content.startswith(b'%PDF'))
                if fmt=='xlsx':self.assertTrue(r.content.startswith(b'PK'))
        r=self.client.get('/api/reports/?kind=inventory&format=csv')
        self.assertIn("'=HYPERLINK",r.content.decode())
    def test_source_review_requires_evidence(self):
        obj=SourceRecord.objects.create(key='test',category='assets',page=4,raw_text='Original')
        self.assertEqual(self.client.patch(f'/api/sources/{obj.id}/',{'status':'verified'}).status_code,400)
        r=self.client.patch(f'/api/sources/{obj.id}/',{'status':'verified','review_note':'Comparado con original y corregido'});self.assertEqual(r.status_code,200)
        obj.refresh_from_db();self.assertEqual(obj.reviewed_by,self.admin)
    def test_import_is_idempotent_preserves_edits_and_unknowns(self):
        path=Path(settings.BASE_DIR).parent/'data/initial_inventory.json'
        call_command('import_inventory',str(path),dry_run=True,stdout=io.StringIO())
        self.assertEqual(Location.objects.count(),0)
        call_command('import_inventory',str(path),stdout=io.StringIO())
        self.assertEqual(Asset.objects.filter(legacy_id__isnull=False).count(),318)
        self.assertEqual(Location.objects.count(),134);self.assertEqual(TechnicalModel.objects.count(),37)
        a=Asset.objects.get(code='ee452');self.assertIsNone(a.location);self.assertTrue(a.needs_review)
        self.assertEqual(Asset.objects.filter(legacy_id__isnull=False,purchase_cost__isnull=False).count(),0)
        a=Asset.objects.get(code='ee1');a.notes='Verificado en campo';a.save()
        call_command('import_inventory',str(path),stdout=io.StringIO())
        a.refresh_from_db();self.assertEqual(a.notes,'Verificado en campo');self.assertEqual(Asset.objects.count(),319)
        self.assertEqual(Location.objects.filter(code='k202').count(),1)
        self.assertEqual(HistoricalService.objects.count(),90)
        self.assertEqual(HistoricalService.objects.filter(possible_duplicate_of__isnull=False).count(),11)
        self.assertFalse(HistoricalService.objects.filter(legacy_id=91).exists())
    def test_login_csrf_and_logout(self):
        client=APIClient(enforce_csrf_checks=True)
        self.assertEqual(client.post('/api/login/',{'username':'admin','password':'local-test-password-123'},format='json').status_code,403)
        token=client.get('/api/csrf/').json()['csrfToken']
        r=client.post('/api/login/',{'username':'admin','password':'local-test-password-123'},format='json',HTTP_X_CSRFTOKEN=token);self.assertEqual(r.status_code,200)
        self.assertEqual(client.get('/api/me/').status_code,200)
        self.assertEqual(client.post('/api/logout/').status_code,403)
        token=client.get('/api/csrf/').json()['csrfToken']
        self.assertEqual(client.post('/api/logout/',HTTP_X_CSRFTOKEN=token).status_code,200)
        self.assertEqual(client.get('/api/me/').status_code,403)

    def test_password_change_requires_current_and_valid_new_password(self):
        r=self.client.post('/api/password/',{'old_password':'wrong','new_password':'Another-pass-12345'});self.assertEqual(r.status_code,400)
        r=self.client.post('/api/password/',{'old_password':'local-test-password-123','new_password':'123'});self.assertEqual(r.status_code,400)
        r=self.client.post('/api/password/',{'old_password':'local-test-password-123','new_password':'Another-pass-12345'});self.assertEqual(r.status_code,200)
        self.admin.refresh_from_db();self.assertTrue(self.admin.check_password('Another-pass-12345'))
    def test_codes_are_unique_ignoring_case(self):
        self.assertEqual(self.client.post('/api/assets/',{'code':'TEST-EE1'}).status_code,400)

    def test_import_preserves_renamed_asset_history(self):
        path=Path(settings.BASE_DIR).parent/'data/initial_inventory.json'
        call_command('import_inventory',str(path),stdout=io.StringIO())
        a=Asset.objects.get(code='ee209');a.code='ee209-verificado';a.save()
        call_command('import_inventory',str(path),stdout=io.StringIO())
        self.assertEqual(HistoricalService.objects.get(legacy_id=1).asset_id,a.pk)
        self.assertEqual(HistoricalService.objects.count(),90)
    def test_invalid_checklist_rejected(self):
        r=self.client.post('/api/work-orders/',{'asset':self.asset.pk,'title':'Test','scheduled_on':date.today().isoformat(),'checklist':[None]},format='json')
        self.assertEqual(r.status_code,400)
