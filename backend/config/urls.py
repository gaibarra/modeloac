from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from inventory import views
router=DefaultRouter()
for prefix,view in [('historical',views.HistoricalServiceViewSet),('locations',views.LocationViewSet),('models',views.ModelViewSet),('suppliers',views.SupplierViewSet),('assets',views.AssetViewSet),('acquisitions',views.AcquisitionViewSet),('work-orders',views.WorkOrderViewSet),('sources',views.SourceViewSet),('audit',views.AuditViewSet)]:router.register(prefix,view,basename=prefix)
urlpatterns=[path('api/password/',views.change_password),path('api/source-document/<int:page>/',views.source_document),path('admin/',admin.site.urls),path('api/csrf/',views.csrf),path('api/login/',views.sign_in),path('api/logout/',views.sign_out),path('api/me/',views.me),path('api/health/',views.health),path('api/dashboard/',views.dashboard),path('api/reports/',views.report),path('api/',include(router.urls))]
