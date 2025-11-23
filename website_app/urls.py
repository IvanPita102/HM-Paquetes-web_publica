from django.urls import path
from . import views

app_name = 'website_app'

urlpatterns = [
    path('', views.index, name='index'),
    path('index', views.index, name='index'),
    path('about', views.about, name='about'),
    path('services', views.services, name='services'),
    path('goods-storage', views.goods_storage, name='goods_storage'),
    path('air-freight-service', views.air_freight_service, name='air_freight_service'),
    path('land_transport_service', views.land_transport_service, name='land_transport_service'),
    path('sea_freight_service', views.sea_freight_service,name='sea_freight_service'),
    path('contact', views.contact, name='contact'),
    path('shipmentDetails/<str:cod>/', views.shipment_details, name='shipment_details'),
    path('insertar-cotizacion', views.insertar_cotizacion, name='insertar_cotizacion')
]