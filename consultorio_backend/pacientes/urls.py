from django.urls import path
from . import views

urlpatterns = [
    path('', views.lista_pacientes, name='lista_pacientes'),
    path('nuevo/', views.nuevo_paciente, name='nuevo_paciente'),
    path('historial/<int:paciente_id>/', views.historial_completo, name='historial_completo'),
    path('historial/<int:paciente_id>/pdf/', views.generar_pdf_historial, name='generar_pdf_historial'),
    path('historial/<int:paciente_id>/email/', views.enviar_historial_email, name='enviar_historial_email'),
    path('<int:paciente_id>/', views.detalle_paciente, name='detalle_paciente'),
    path('<int:paciente_id>/editar/', views.editar_paciente, name='editar_paciente'),
    
]
