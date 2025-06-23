from django.urls import path
from . import views

urlpatterns = [
    path('', views.lista_citas, name='lista_citas'),
    path('nueva/', views.nueva_cita, name='nueva_cita'),
    path('nueva/<int:paciente_id>/', views.nueva_cita, name='nueva_cita_paciente'),
    path('cita/<int:cita_id>/', views.detalle_cita, name='detalle_cita'),
    path('cita/<int:cita_id>/editar/', views.editar_cita, name='editar_cita'),
    path('cita/<int:cita_id>/completar/', views.completar_cita, name='completar_cita'),
    path('cita/<int:cita_id>/cancelar/', views.cancelar_cita, name='cancelar_cita'),
]
