from datetime import date
from rest_framework import serializers
from .models import *

class CodeSerializer(serializers.ModelSerializer):
    def validate_code(self, value):
        value=value.strip().lower()
        if self.instance and isinstance(self.instance,(Location,TechnicalModel)) and self.instance.source_ref and value!=self.instance.code:
            raise serializers.ValidationError('El código original del catálogo se conserva para asegurar la trazabilidad. Puedes editar sus datos descriptivos.')
        qs=self.Meta.model.objects.filter(code__iexact=value)
        if self.instance: qs=qs.exclude(pk=self.instance.pk)
        if qs.exists(): raise serializers.ValidationError('Este código ya está registrado.')
        return value

class LocationSerializer(CodeSerializer):
    class Meta:
        model = Location
        fields = '__all__'
        read_only_fields = ['source_ref']
class TechnicalModelSerializer(CodeSerializer):
    class Meta:
        model = TechnicalModel
        fields = '__all__'
        read_only_fields = ['source_ref']
class SupplierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = '__all__'
class AssetSerializer(CodeSerializer):
    location_name = serializers.CharField(source='location.name', read_only=True, default='Sin ubicación')
    location_code = serializers.CharField(source='location.code', read_only=True, default='')
    brand = serializers.CharField(source='model.brand', read_only=True, default='Por identificar')
    model_code = serializers.CharField(source='model.code', read_only=True, default='')
    capacity_btu = serializers.IntegerField(source='model.capacity_btu', read_only=True, allow_null=True)
    class Meta:
        model = Asset
        fields = '__all__'
        read_only_fields = ['legacy_id','source_ref']
    def validate(self, attrs):
        def value(k): return attrs.get(k, getattr(self.instance,k,None))
        if value('acquired_on') and value('warranty_until') and value('warranty_until') < value('acquired_on'):
            raise serializers.ValidationError({'warranty_until':'La garantía no puede terminar antes de la adquisición.'})
        return attrs
class AcquisitionSerializer(serializers.ModelSerializer):
    supplier_name = serializers.CharField(source='supplier.name', read_only=True, default='Sin proveedor')
    class Meta:
        model = Acquisition
        fields = '__all__'
class WorkOrderSerializer(serializers.ModelSerializer):
    asset_code = serializers.CharField(source='asset.code', read_only=True)
    location_name = serializers.CharField(source='asset.location.name', read_only=True, default='Sin ubicación')
    class Meta:
        model = WorkOrder
        fields = '__all__'
        read_only_fields = ['source_ref']
    def validate(self, attrs):
        status = attrs.get('status', getattr(self.instance,'status','open'))
        if self.instance and self.instance.status == 'completed':
            raise serializers.ValidationError('Una orden cerrada conserva su historial. Registra una nueva orden para correcciones.')
        if status == 'completed':
            done = attrs.get('completed_on', getattr(self.instance,'completed_on',None))
            resolution = attrs.get('resolution', getattr(self.instance,'resolution',''))
            if not done or not resolution.strip():
                raise serializers.ValidationError('Para cerrar la orden indica fecha de terminación y trabajo realizado.')
            from django.utils import timezone
            if done > timezone.localdate():
                raise serializers.ValidationError({'completed_on':'No puede ser una fecha futura.'})
        if 'checklist' in attrs:
            items=attrs['checklist']
            if not isinstance(items,list) or len(items)>50 or any(not isinstance(item,dict) or not isinstance(item.get('label'),str) or not isinstance(item.get('done'),bool) for item in items):
                raise serializers.ValidationError({'checklist':'Usa una lista de hasta 50 tareas con texto y estado de verificación.'})
        return attrs
class SourceRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = SourceRecord
        fields = '__all__'
        read_only_fields = ['key','category','page','legacy_id','raw_text','proposed','reviewed_by','reviewed_at']
    def validate(self, attrs):
        if attrs.get('status') in ['verified','duplicate'] and not attrs.get('review_note',getattr(self.instance,'review_note','')).strip():
            raise serializers.ValidationError({'review_note':'Documenta la comparación con el original antes de resolver el registro.'})
        return attrs
class AuditEventSerializer(serializers.ModelSerializer):
    actor_name = serializers.CharField(source='actor.username',read_only=True,default='Sistema')
    class Meta:
        model = AuditEvent
        fields = '__all__'

class HistoricalServiceSerializer(serializers.ModelSerializer):
    asset_code=serializers.CharField(source='asset.code',read_only=True)
    location_name=serializers.CharField(source='asset.location.name',read_only=True,default='Sin ubicación')
    class Meta:
        model=HistoricalService
        fields='__all__'
