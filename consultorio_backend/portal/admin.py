from django.contrib import admin
from .models import Paciente

@admin.register(Paciente)
class PacienteAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'apellidos', 'email', 'telefono', 'fecha_registro')
    search_fields = ('nombre', 'apellidos', 'email', 'telefono')
    list_filter = ('fecha_registro',)
    date_hierarchy = 'fecha_registro'
    readonly_fields = ('llave_unica',)
