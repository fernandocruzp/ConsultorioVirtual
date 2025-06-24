# portal/urls.py
from django.urls import path
from . import views

app_name = 'portal'

urlpatterns = [
    path('', views.inicio_portal, name='inicio_portal'),
    path('dashboard/', views.portal_dashboard, name='portal_dashboard'),
]
