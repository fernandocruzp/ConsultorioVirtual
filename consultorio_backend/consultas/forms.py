from django import forms
from .models import Consulta, PlanNutricional, Receta
from pacientes.models import Paciente

class ConsultaForm(forms.ModelForm):
    paciente = forms.ModelChoiceField(
        queryset=Paciente.objects.all().order_by('apellidos', 'nombre'),
        empty_label="Seleccione un paciente",
        required=True
    )
    
    class Meta:
        model = Consulta
        fields = [
            'paciente', 
            'peso', 
            'altura', 
            'circunferencia_cintura',
            'circunferencia_cadera',
            'circunferencia_pecho',
            'tension_arterial',
            'tratamiento',
            'observaciones'
        ]
        widgets = {
            'tratamiento': forms.Textarea(attrs={'rows': 3}),
            'observaciones': forms.Textarea(attrs={'rows': 5}),
        }

class PlanNutricionalForm(forms.ModelForm):
    class Meta:
        model = PlanNutricional
        fields = [
            'contenido_desayuno', 'horario_desayuno',
            'contenido_colacion', 'horario_colacion1', 'horario_colacion2',
            'contenido_comida', 'horario_comida',
            'contenido_cena', 'horario_cena'
        ]
        widgets = {
            'contenido_desayuno': forms.Textarea(attrs={'rows': 15}),
            'contenido_colacion': forms.Textarea(attrs={'rows': 15}),
            'contenido_comida': forms.Textarea(attrs={'rows': 15}),
            'contenido_cena': forms.Textarea(attrs={'rows': 15}),
            'horario_desayuno': forms.TimeInput(attrs={'type': 'time'}),
            'horario_colacion1': forms.TimeInput(attrs={'type': 'time'}),
            'horario_colacion2': forms.TimeInput(attrs={'type': 'time'}),
            'horario_comida': forms.TimeInput(attrs={'type': 'time'}),
            'horario_cena': forms.TimeInput(attrs={'type': 'time'}),
        }

class RecetaForm(forms.ModelForm):
    class Meta:
        model = Receta
        fields = ['medicamentos']
        widgets = {
            'medicamentos': forms.Textarea(attrs={'rows': 10}),
        }
