from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models

class Tracked(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        abstract = True
        ordering = ['-id']

class Location(Tracked):
    code = models.CharField(max_length=40, unique=True)
    building = models.CharField(max_length=100, blank=True)
    level = models.CharField(max_length=100, blank=True)
    position = models.CharField(max_length=80, blank=True)
    name = models.CharField(max_length=250)
    notes = models.TextField(blank=True)
    source_ref = models.CharField(max_length=250, blank=True)
    needs_review = models.BooleanField(default=False)
    def __str__(self): return f'{self.code} · {self.name}'

class TechnicalModel(Tracked):
    code = models.CharField(max_length=40, unique=True)
    brand = models.CharField(max_length=100)
    indoor_model = models.CharField(max_length=150, blank=True)
    outdoor_model = models.CharField(max_length=150, blank=True)
    capacity_btu = models.PositiveIntegerField(null=True, blank=True)
    inverter = models.BooleanField(null=True, blank=True)
    equipment_type = models.CharField(max_length=80, blank=True)
    refrigerant = models.CharField(max_length=40, blank=True)
    voltage = models.CharField(max_length=50, blank=True)
    rated_power_kw = models.DecimalField(max_digits=7, decimal_places=3, null=True, blank=True, validators=[MinValueValidator(0)])
    manual_url = models.URLField(blank=True)
    notes = models.TextField(blank=True)
    source_ref = models.CharField(max_length=250, blank=True)
    needs_review = models.BooleanField(default=False)
    def __str__(self): return f'{self.code} · {self.brand} {self.indoor_model}'

class Supplier(Tracked):
    name = models.CharField(max_length=200, unique=True)
    contact = models.CharField(max_length=200, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=50, blank=True)
    tax_id = models.CharField(max_length=20, blank=True)
    notes = models.TextField(blank=True)
    def __str__(self): return self.name

class Asset(Tracked):
    STATUS = [('unknown','Por verificar'),('operational','Operativo'),('maintenance','En mantenimiento'),('failed','Fuera de servicio'),('retired','Baja')]
    code = models.CharField(max_length=50, unique=True)
    legacy_id = models.PositiveIntegerField(null=True, blank=True, unique=True)
    model = models.ForeignKey(TechnicalModel, on_delete=models.PROTECT, null=True, blank=True)
    location = models.ForeignKey(Location, on_delete=models.PROTECT, null=True, blank=True)
    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT, null=True, blank=True)
    serial_number = models.CharField(max_length=160, blank=True)
    status = models.CharField(max_length=20, choices=STATUS, default='unknown')
    acquired_on = models.DateField(null=True, blank=True)
    installed_on = models.DateField(null=True, blank=True)
    warranty_until = models.DateField(null=True, blank=True)
    purchase_cost = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(0)])
    maintenance_interval_days = models.PositiveIntegerField(default=90, validators=[MinValueValidator(1)])
    next_maintenance = models.DateField(null=True, blank=True)
    criticality = models.CharField(max_length=15, choices=[('low','Baja'),('medium','Media'),('high','Alta')], default='medium')
    notes = models.TextField(blank=True)
    source_ref = models.CharField(max_length=250, blank=True)
    needs_review = models.BooleanField(default=False)
    def __str__(self): return self.code

class Acquisition(Tracked):
    reference = models.CharField(max_length=80, unique=True)
    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT, null=True, blank=True)
    model = models.ForeignKey(TechnicalModel, on_delete=models.PROTECT, null=True, blank=True)
    location = models.ForeignKey(Location, on_delete=models.PROTECT, null=True, blank=True)
    quantity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    unit_cost = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    requested_on = models.DateField()
    expected_on = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=[('requested','Solicitada'),('approved','Aprobada'),('ordered','En compra'),('received','Recibida'),('cancelled','Cancelada')],default='requested')
    invoice = models.CharField(max_length=120, blank=True)
    justification = models.TextField()
    notes = models.TextField(blank=True)
    def __str__(self): return self.reference

class WorkOrder(Tracked):
    asset = models.ForeignKey(Asset, on_delete=models.PROTECT, related_name='work_orders')
    title = models.CharField(max_length=250)
    kind = models.CharField(max_length=20, choices=[('preventive','Preventivo'),('corrective','Correctivo'),('installation','Instalación'),('inspection','Inspección')],default='preventive')
    status = models.CharField(max_length=20, choices=[('open','Abierta'),('scheduled','Programada'),('in_progress','En proceso'),('completed','Completada'),('cancelled','Cancelada')],default='open')
    priority = models.CharField(max_length=20, choices=[('low','Baja'),('medium','Media'),('high','Alta'),('urgent','Urgente')],default='medium')
    scheduled_on = models.DateField()
    completed_on = models.DateField(null=True, blank=True)
    technician = models.CharField(max_length=180, blank=True)
    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT, null=True, blank=True)
    cost = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(0)])
    diagnosis = models.TextField(blank=True)
    resolution = models.TextField(blank=True)
    checklist = models.JSONField(default=list, blank=True)
    source_ref = models.CharField(max_length=250, blank=True)
    needs_review = models.BooleanField(default=False)
    def __str__(self): return f'OT-{self.pk} · {self.title}'

class SourceRecord(Tracked):
    key = models.CharField(max_length=120, unique=True)
    category = models.CharField(max_length=40)
    page = models.PositiveIntegerField()
    legacy_id = models.CharField(max_length=40, blank=True)
    raw_text = models.TextField()
    proposed = models.JSONField(default=dict)
    status = models.CharField(max_length=20, choices=[('pending','Pendiente'),('verified','Verificado'),('duplicate','Duplicado')],default='pending')
    review_note = models.TextField(blank=True)
    reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    reviewed_at = models.DateTimeField(null=True, blank=True)

class AuditEvent(models.Model):
    at = models.DateTimeField(auto_now_add=True)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    action = models.CharField(max_length=40)
    resource = models.CharField(max_length=80)
    object_id = models.CharField(max_length=80)
    detail = models.JSONField(default=dict)
    class Meta:
        ordering = ['-id']


class HistoricalService(Tracked):
    legacy_id = models.PositiveIntegerField(unique=True)
    asset = models.ForeignKey(Asset, on_delete=models.PROTECT, related_name='historical_services')
    work_code = models.CharField(max_length=40)
    description = models.TextField()
    performed_on = models.DateField()
    recorded_cost = models.DecimalField(max_digits=12, decimal_places=2)
    possible_duplicate_of = models.PositiveIntegerField(null=True, blank=True)
    source_ref = models.CharField(max_length=250)
