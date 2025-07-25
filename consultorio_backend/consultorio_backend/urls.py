"""
URL configuration for consultorio_backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.views.generic import RedirectView
from django.conf import settings
from django.conf.urls.static import static
from . import views
#from debug_toolbar.toolbar import debug_toolbar_urls

urlpatterns = [
    # Admin
    path("admin/", admin.site.urls),
    
    # Menú
    path("", views.dashboard, name="dashboard"),
    
    # Autenticación
    path("login/", auth_views.LoginView.as_view(template_name="base/login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(next_page="/login/"), name="logout"),
    path("cambiar-password/", views.cambiar_password, name="cambiar_password"),
    path("cambiar-correo/", views.cambiar_correo, name="cambiar_correo"),
    # Apps
    path("pacientes/", include("pacientes.urls")),
    path("consultas/", include("consultas.urls")),
    path("agenda/", include("agenda.urls")),
    path("portal/", include("portal.urls")),
    
    # Redirección para compatibilidad con Electron
    path("favicon.ico", RedirectView.as_view(url="/static/img/favicon.ico")),
]

# Servir archivos estáticos y de medios en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
