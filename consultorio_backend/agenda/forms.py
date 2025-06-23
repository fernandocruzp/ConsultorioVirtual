from django import forms
from .models import Cita
from pacientes.models import Paciente
from django.utils import timezone

class CitaForm(forms.ModelForm):
    paciente = forms.ModelChoiceField(
        queryset=Paciente.objects.all().order_by('apellidos', 'nombre'),
        empty_label="Seleccione un paciente",
        required=True
    )
    
    class Meta:
        model = Cita
        fields = ['paciente', 'fecha_hora', 'motivo', 'notas']
        widgets = {
            'fecha_hora': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'notas': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Convertir el formato de fecha_hora para el widget datetime-local
        if self.instance.pk and self.instance.fecha_hora:
            self.initial['fecha_hora'] = self.instance.fecha_hora.strftime('%Y-%m-%dT%H:%M')
    
    def clean_fecha_hora(self):
        fecha_hora = self.cleaned_data.get('fecha_hora')
        
        # Verificar que la fecha no sea en el pasado
        if fecha_hora and fecha_hora < timezone.now():
            raise forms.ValidationError("No se puede programar una cita en el pasado.")
        
        return fecha_hora
