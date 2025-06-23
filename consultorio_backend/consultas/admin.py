from django.contrib import admin
from .models import Consulta, PlanNutricional

@admin.register(Consulta)
class ConsultaAdmin(admin.ModelAdmin):
    list_display = ('paciente', 'fecha', 'peso', 'altura', 'imc')
    search_fields = ('paciente__nombre', 'paciente__apellidos')
    list_filter = ('fecha',)
    date_hierarchy = 'fecha'

@admin.register(PlanNutricional)
class PlanNutricionalAdmin(admin.ModelAdmin):
    list_display = ('consulta', 'fecha_creacion')
    search_fields = ('consulta__paciente__nombre', 'consulta__paciente__apellidos')
    list_filter = ('fecha_creacion',)
