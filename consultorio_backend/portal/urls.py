# portal/urls.py
from django.urls import path
from . import views

app_name = 'portal'

urlpatterns = [
    path('', views.inicio_portal, name='inicio_portal'),
    path('dashboard/', views.portal_dashboard, name='portal_dashboard'),
    path('historial/', views.historial_completo, name='historial_paciente'),
    path('consultas/<int:consulta_id>/', views.detalle_consulta, name='detalle_consulta'),
    path('consultas/plan/<int:plan_id>/', views.detalle_plan, name='detalle_plan'),
    path('consultas/plan/<int:plan_id>/pdf/', views.generar_pdf_plan, name='generar_plan_pdf'),
    path('cita/<int:cita_id>/', views.detalle_cita, name='detalle_cita'),
]
