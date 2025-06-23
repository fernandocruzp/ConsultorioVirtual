from django import forms
from .models import Paciente

class PacienteForm(forms.ModelForm):
    class Meta:
        model = Paciente
        fields = [
            # Información personal básica
            'nombre', 'apellidos', 'fecha_nacimiento', 'email', 'telefono',
            # Nuevos campos personales
            'estado_civil', 'escolaridad', 'ocupacion', 'rfc',
            # Antecedentes médicos
            'diabetes', 'hipertension_arterial', 'obesidad', 'cancer',
            'otra_enfermedad', 'medicamentos',
            # Hábitos
            'fuma', 'bebe', 'actividad_fisica',
            # Horarios de alimentación
            'horario_desayuno', 'horario_comida', 'horario_cena',
            # Síntomas digestivos
            'distension_despues_comer', 'dolor_estomago', 'estrenimiento',
            # Campos médicos básicos
            'alergias', 'antecedentes'
        ]
        widgets = {
            'fecha_nacimiento': forms.DateInput(attrs={'type': 'date'}),
            'horario_desayuno': forms.TimeInput(attrs={'type': 'time'}),
            'horario_comida': forms.TimeInput(attrs={'type': 'time'}),
            'horario_cena': forms.TimeInput(attrs={'type': 'time'}),
            'alergias': forms.Textarea(attrs={'rows': 3}),
            'antecedentes': forms.Textarea(attrs={'rows': 3}),
            'otra_enfermedad': forms.Textarea(attrs={'rows': 3}),
            'medicamentos': forms.Textarea(attrs={'rows': 3}),
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Añadir clases Bootstrap a todos los campos
        for field_name, field in self.fields.items():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs['class'] = 'form-check-input'
            elif isinstance(field.widget, (forms.Select, forms.RadioSelect)):
                field.widget.attrs['class'] = 'form-select'
            else:
                field.widget.attrs['class'] = 'form-control'
