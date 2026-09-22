from django.contrib import admin
from .models import Location,TechnicalModel,Supplier,Asset,Acquisition,WorkOrder,SourceRecord,AuditEvent
admin.site.site_header='Escuela Modelo · Administración AC'
for model in [Location,TechnicalModel,Supplier,Asset,Acquisition,WorkOrder,SourceRecord,AuditEvent]:
    class ReadOnlyAdmin(admin.ModelAdmin):
        def has_add_permission(self,request): return False
        def has_change_permission(self,request,obj=None): return False
        def has_delete_permission(self,request,obj=None): return False
    admin.site.register(model,ReadOnlyAdmin)
