from django.contrib import admin
from .models import Cita

@admin.register(Cita)
class CitaAdmin(admin.ModelAdmin):
    list_display = ('paciente', 'fecha_hora', 'motivo', 'estado')
    search_fields = ('paciente__nombre', 'paciente__apellidos', 'motivo')
    list_filter = ('estado', 'fecha_hora')
    date_hierarchy = 'fecha_hora'
