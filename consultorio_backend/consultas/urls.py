from django.urls import path
from . import views

urlpatterns = [
    # Consultas
    path('', views.lista_consultas, name='lista_consultas'),
    path('nuevo/', views.nueva_consulta, name='nueva_consulta'),
    path('nuevo/<int:paciente_id>/', views.nueva_consulta, name='nueva_consulta_paciente'),
    path('<int:consulta_id>/', views.detalle_consulta, name='detalle_consulta'),
    
    # Planes nutricionales
    path('plan/<int:plan_id>/', views.detalle_plan, name='detalle_plan'),
    path('plan/nuevo/<int:consulta_id>/', views.nuevo_plan, name='nuevo_plan'),
    path('plan/<int:plan_id>/editar/', views.editar_plan, name='editar_plan'),
    path('plan/<int:plan_id>/pdf/', views.generar_pdf_plan, name='generar_pdf_plan'),
    path('plan/<int:plan_id>/email/', views.enviar_plan_email, name='enviar_plan_email'),
    path('plan/<int:plan_id>/whatsapp/', views.enviar_plan_whatsapp, name='enviar_plan_whatsapp'),
    
    # Recetas
    path('receta/<int:receta_id>/', views.detalle_receta, name='detalle_receta'),
    path('receta/nueva/<int:consulta_id>/', views.nueva_receta, name='nueva_receta'),
    path('receta/<int:receta_id>/editar/', views.editar_receta, name='editar_receta'),
    path('receta/<int:receta_id>/pdf/', views.generar_pdf_receta, name='generar_pdf_receta'),

    #Historial
    path('historial/<int:consulta_id>/', views.historial_completo, name='historial_completo'),
    path('historial/<int:consulta_id>/pdf/', views.generar_pdf_historial, name='generar_pdf_historial'),
    path('historial/<int:consulta_id>/email/', views.enviar_historial_email, name='enviar_historial_email'),
    path('historial/<int:consulta_id>/whatsapp/', views.enviar_historial_whatsapp, name='enviar_historial_whatsapp'),
]
