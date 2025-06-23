from django.urls import path
from . import views

urlpatterns = [
    path('', views.login, name='log_in'),
    path('historial/<int:paciente_id>/', views.historial_completo, name='historial_completo'),
    path('<int:paciente_id>/', views.detalle_paciente, name='detalle_paciente'),
    path("logout/", auth_views.LogoutView.as_view(next_page=''), name="logout"),
    path('consulta/<int:consulta_id>/', views.detalle_consulta, name='deralle_consulta'),
]
