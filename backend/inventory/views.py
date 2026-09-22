import csv, io, json
from datetime import date, timedelta
from decimal import Decimal
from django.contrib.auth import authenticate, login, logout
from django.db import transaction
from django.db.models import Count, Sum, F, DecimalField, Q
from django.http import JsonResponse, HttpResponse, FileResponse
from django.middleware.csrf import get_token
from django.utils import timezone
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_http_methods
from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework.exceptions import ValidationError
from .models import *
from .serializers import *
from .permissions import OperationalPermission

def profile(user):
    role = 'Administración' if user.is_superuser else (user.groups.values_list('name',flat=True).first() or 'Consulta')
    return {'id':user.id,'username':user.username,'name':user.get_full_name() or user.username,'role':role,'can_manage_users':user.is_superuser}

@require_http_methods(['GET'])
def csrf(request): return JsonResponse({'csrfToken':get_token(request)})
class LoginThrottle(AnonRateThrottle): scope='login'
@csrf_protect
@require_http_methods(['POST'])
def sign_in(request):
    throttle = LoginThrottle()
    if not throttle.allow_request(request,None): return JsonResponse({'detail':'Demasiados intentos. Intenta más tarde.'},status=429)
    try: data = json.loads(request.body)
    except (ValueError,UnicodeDecodeError): return JsonResponse({'detail':'Solicitud inválida.'},status=400)
    if not isinstance(data,dict): return JsonResponse({'detail':'Solicitud inválida.'},status=400)
    user = authenticate(request,username=data.get('username',''),password=data.get('password',''))
    if not user: return JsonResponse({'detail':'Usuario o contraseña incorrectos.'},status=400)
    login(request,user)
    return JsonResponse(profile(user))
@api_view(['GET'])
def me(request): return Response(profile(request.user))
@api_view(['POST'])
def sign_out(request):
    logout(request)
    return Response({'detail':'Sesión cerrada.'})
@api_view(['GET'])
@permission_classes([AllowAny])
def health(request):
    from django.db import connection
    with connection.cursor() as c: c.execute('SELECT 1')
    return Response({'status':'ok','service':'modeloac'})

class BaseViewSet(viewsets.ModelViewSet):
    permission_classes = [OperationalPermission]
    http_method_names = ['get','post','patch','head','options']
    ordering_fields = ['id','created_at','updated_at']
    ordering = ['-id']
    filter_fields = []
    def get_queryset(self):
        qs = super().get_queryset()
        for field in self.filter_fields:
            value = self.request.query_params.get(field)
            if value:
                if field == 'needs_review': value = value.lower() == 'true'
                if field in ['asset','location','model'] and not value.isdigit(): raise ValidationError({field:'Referencia inválida.'})
                qs = qs.filter(**{field:value})
        return qs
    def save_record(self, serializer):
        with transaction.atomic():
            def normalize(value):
                if hasattr(value,'pk'):return value.pk
                if value is None or isinstance(value,(str,int,float,bool,list,dict)):return value
                return str(value)
            changes={key:{'before':normalize(getattr(serializer.instance,key,None)) if serializer.instance else None,'after':normalize(value)} for key,value in serializer.validated_data.items()}
            obj = serializer.save()
            AuditEvent.objects.create(actor=self.request.user,action='update' if self.action=='partial_update' else 'create',resource=self.resource_name,object_id=str(obj.pk),detail={'changes':changes})
            if isinstance(obj, WorkOrder) and obj.status == 'completed' and obj.kind == 'preventive':
                asset = Asset.objects.select_for_update().get(pk=obj.asset_id)
                next_date = obj.completed_on + timedelta(days=asset.maintenance_interval_days)
                if not asset.next_maintenance or next_date > asset.next_maintenance:
                    asset.next_maintenance = next_date
                    asset.save(update_fields=['next_maintenance','updated_at'])
            if isinstance(obj,SourceRecord):
                obj.reviewed_by=self.request.user; obj.reviewed_at=timezone.now();obj.save(update_fields=['reviewed_by','reviewed_at'])
    def perform_create(self,serializer): self.save_record(serializer)
    def perform_update(self,serializer): self.save_record(serializer)

class LocationViewSet(BaseViewSet):
    queryset=Location.objects.all();serializer_class=LocationSerializer;resource_name='locations'
    search_fields=['code','name','building','level'];filter_fields=['building','level','needs_review']
class ModelViewSet(BaseViewSet):
    queryset=TechnicalModel.objects.all();serializer_class=TechnicalModelSerializer;resource_name='models'
    search_fields=['code','brand','indoor_model','outdoor_model'];filter_fields=['brand','needs_review']
class SupplierViewSet(BaseViewSet):
    queryset=Supplier.objects.all();serializer_class=SupplierSerializer;resource_name='suppliers';search_fields=['name','contact','tax_id']
class AssetViewSet(BaseViewSet):
    queryset=Asset.objects.select_related('model','location','supplier');serializer_class=AssetSerializer;resource_name='assets'
    search_fields=['code','serial_number','location__name','location__code','model__brand','model__code']
    filter_fields=['status','location','model','criticality','needs_review']
    def get_queryset(self):
        qs=super().get_queryset()
        if self.request.query_params.get('due')=='true': qs=qs.filter(next_maintenance__lte=timezone.localdate()).exclude(status='retired')
        return qs
class AcquisitionViewSet(BaseViewSet):
    queryset=Acquisition.objects.select_related('supplier','model','location');serializer_class=AcquisitionSerializer;resource_name='acquisitions'
    search_fields=['reference','invoice','supplier__name','justification'];filter_fields=['status']
class WorkOrderViewSet(BaseViewSet):
    queryset=WorkOrder.objects.select_related('asset__location','supplier');serializer_class=WorkOrderSerializer;resource_name='work-orders'
    search_fields=['title','asset__code','technician','asset__location__name'];filter_fields=['status','kind','priority','asset']
    def get_queryset(self):
        qs=super().get_queryset()
        for param,lookup in [('from','scheduled_on__gte'),('to','scheduled_on__lte')]:
            if self.request.query_params.get(param):
                try: date.fromisoformat(self.request.query_params[param])
                except ValueError: raise ValidationError({param:'Fecha inválida.'})
                qs=qs.filter(**{lookup:self.request.query_params[param]})
        return qs
class SourceViewSet(BaseViewSet):
    queryset=SourceRecord.objects.all();serializer_class=SourceRecordSerializer;resource_name='sources'
    http_method_names=['get','patch','head','options']
    search_fields=['raw_text','key','review_note'];filter_fields=['category','status']
class AuditViewSet(viewsets.ReadOnlyModelViewSet):
    queryset=AuditEvent.objects.select_related('actor');serializer_class=AuditEventSerializer
    search_fields=['resource','action','actor__username']

@api_view(['GET'])
def dashboard(request):
    today=timezone.localdate();assets=Asset.objects.all();orders=WorkOrder.objects.all()
    known=orders.filter(status='completed',cost__isnull=False)
    return Response({
      'assets':assets.count(),'locations':Location.objects.count(),'models':TechnicalModel.objects.count(),
      'operational':assets.filter(status='operational').count(),'unknown':assets.filter(status='unknown').count(),
      'failed':assets.filter(status='failed').count(),
      'overdue':assets.filter(next_maintenance__lt=today).exclude(status='retired').count(),
      'unscheduled':assets.filter(next_maintenance__isnull=True).exclude(status='retired').count(),
      'open_orders':orders.exclude(status__in=['completed','cancelled']).count(),
      'pending_review':SourceRecord.objects.filter(status='pending').count(),
      'maintenance_cost':known.aggregate(total=Sum('cost'))['total'] or 0,
      'cost_records':known.count(),
      'warranty_expiring':assets.filter(warranty_until__range=[today,today+timedelta(days=60)]).count(),
      'by_status':list(assets.values('status').annotate(total=Count('id')).order_by('-total')),
      'by_building':list(assets.values('location__building').annotate(total=Count('id')).order_by('-total')),
      'by_brand':list(assets.values('model__brand').annotate(total=Count('id')).order_by('-total')),
      'upcoming':WorkOrderSerializer(orders.exclude(status__in=['completed','cancelled']).order_by('scheduled_on')[:8],many=True).data,
      'recent':AuditEventSerializer(AuditEvent.objects.select_related('actor')[:6],many=True).data,
    })

@api_view(['GET'])
def report(request):
    from openpyxl import Workbook
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet
    from xml.sax.saxutils import escape
    kind=request.query_params.get('kind','inventory');fmt=request.query_params.get('format','csv')
    if fmt not in ['csv','xlsx','pdf']: return Response({'detail':'Formato no válido.'},status=400)
    today=timezone.localdate()
    if kind in ['inventory','maintenance','warranty','quality']:
        qs=Asset.objects.select_related('model','location').order_by('code')
        if kind=='maintenance': qs=qs.exclude(status='retired').filter(Q(next_maintenance__lte=today+timedelta(days=30))|Q(next_maintenance__isnull=True))
        if kind=='warranty': qs=qs.filter(warranty_until__range=[today,today+timedelta(days=60)])
        if kind=='quality': qs=qs.filter(Q(needs_review=True)|Q(model=None)|Q(location=None))
        if request.query_params.get('building'): qs=qs.filter(location__building=request.query_params['building'])
        headers=['Código','Ubicación','Marca','Modelo','BTU','Estado','Próx. servicio','Garantía','Revisión']
        rows=[[a.code,str(a.location or ''),a.model.brand if a.model else '',a.model.code if a.model else '',a.model.capacity_btu if a.model else '',a.get_status_display(),a.next_maintenance,a.warranty_until,'Pendiente' if a.needs_review else 'No'] for a in qs]
    elif kind=='costs':
        qs=WorkOrder.objects.select_related('asset').order_by('-scheduled_on')
        for param,lookup in [('from','scheduled_on__gte'),('to','scheduled_on__lte')]:
            v=request.query_params.get(param)
            if v:
                try: date.fromisoformat(v)
                except ValueError: return Response({'detail':'Fecha inválida.'},status=400)
                qs=qs.filter(**{lookup:v})
        headers=['Orden','Equipo','Tipo','Estado','Programada','Terminada','Costo MXN','Técnico']
        rows=[[f'OT-{o.id}',o.asset.code,o.get_kind_display(),o.get_status_display(),o.scheduled_on,o.completed_on,o.cost,o.technician] for o in qs]
    elif kind=='historical':
        headers=['Registro','Equipo','Concepto','Fecha','Costo literal (moneda no indicada)','Posible repetido de']
        rows=[[h.legacy_id,h.asset.code,h.description,h.performed_on,h.recorded_cost,h.possible_duplicate_of] for h in HistoricalService.objects.select_related('asset').order_by('legacy_id')]
    elif kind=='acquisitions':
        headers=['Referencia','Proveedor','Cantidad','Costo unitario MXN','Total MXN','Estado','Fecha']
        rows=[[a.reference,str(a.supplier or ''),a.quantity,a.unit_cost,a.quantity*a.unit_cost,a.get_status_display(),a.requested_on] for a in Acquisition.objects.select_related('supplier')]
    else: return Response({'detail':'Reporte no válido.'},status=400)
    def safe(value):
        if value is None: return ''
        if isinstance(value,str) and value.lstrip().startswith(('=','+','-','@')): return "'"+value
        return value
    rows=[[safe(v) for v in row] for row in rows]
    if fmt=='csv':
        response=HttpResponse(content_type='text/csv; charset=utf-8');response.write('﻿');writer=csv.writer(response);writer.writerow(headers);writer.writerows(rows)
    elif fmt=='xlsx':
        wb=Workbook();ws=wb.active;ws.title='Escuela Modelo';ws.append(headers)
        for row in rows: ws.append(row)
        ws.freeze_panes='A2';ws.auto_filter.ref=ws.dimensions
        for col in ws.columns: ws.column_dimensions[col[0].column_letter].width=24
        buf=io.BytesIO();wb.save(buf);response=HttpResponse(buf.getvalue(),content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    else:
        buf=io.BytesIO();styles=getSampleStyleSheet();styles['BodyText'].fontSize=7;styles['BodyText'].leading=9
        table=Table([[Paragraph(escape(str(v if v is not None else '')),styles['BodyText']) for v in row] for row in [headers]+rows],repeatRows=1,colWidths=[770/len(headers)]*len(headers))
        table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e6edf7')),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#f4f6f9')]),('VALIGN',(0,0),(-1,-1),'TOP'),('BOTTOMPADDING',(0,0),(-1,-1),6)]))
        SimpleDocTemplate(buf,pagesize=landscape(A4),leftMargin=30,rightMargin=30).build([Paragraph('Escuela Modelo · Control de climatización',styles['Title']),Paragraph(f'Reporte: {kind} · {today} · {len(rows)} registros. Campos vacíos = sin información.',styles['BodyText']),Spacer(1,15),table])
        response=HttpResponse(buf.getvalue(),content_type='application/pdf')
    response['Content-Disposition']=f'attachment; filename="modeloac-{kind}-{today}.{fmt}"'
    return response

@api_view(['GET'])
def source_document(request, page):
    from django.conf import settings
    from pathlib import Path
    if page < 1 or page > 14: return Response(status=404)
    name = 'complemento.jpeg' if page == 14 else f'page-{page:02d}.jpg'
    path = Path(settings.BASE_DIR).parent / 'data' / 'sources' / name
    if not path.is_file(): return Response(status=404)
    response=FileResponse(path.open('rb'),content_type='image/jpeg')
    response['Cache-Control']='private, no-store'
    return response

class HistoricalServiceViewSet(viewsets.ReadOnlyModelViewSet):
    queryset=HistoricalService.objects.select_related('asset__location')
    serializer_class=HistoricalServiceSerializer
    search_fields=['asset__code','description','work_code','asset__location__name']
    def get_queryset(self):
        qs=super().get_queryset()
        value=self.request.query_params.get('asset')
        if value:
            if not value.isdigit():raise ValidationError({'asset':'Referencia inválida.'})
            qs=qs.filter(asset_id=value)
        return qs

@api_view(['POST'])
def change_password(request):
    from django.contrib.auth.password_validation import validate_password
    from django.contrib.auth import update_session_auth_hash
    from django.core.exceptions import ValidationError as DjangoValidationError
    old=request.data.get('old_password','');new=request.data.get('new_password','')
    if not isinstance(old,str) or not isinstance(new,str):return Response({'detail':'Solicitud inválida.'},status=400)
    if not request.user.check_password(old):return Response({'detail':'La contraseña actual no es correcta.'},status=400)
    try:validate_password(new,request.user)
    except DjangoValidationError as exc:return Response({'detail':' '.join(exc.messages)},status=400)
    request.user.set_password(new);request.user.save(update_fields=['password'])
    update_session_auth_hash(request,request.user)
    AuditEvent.objects.create(actor=request.user,action='password_change',resource='account',object_id=str(request.user.pk))
    return Response({'detail':'Contraseña actualizada.'})
