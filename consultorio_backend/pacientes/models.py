from django.db import models
from django.contrib.auth.models import User
import uuid

class Paciente(models.Model):
    # Información personal básica
    nombre = models.CharField(max_length=100)
    apellidos = models.CharField(max_length=100)
    fecha_nacimiento = models.DateField()
    email = models.EmailField()
    telefono = models.CharField(max_length=15)
    fecha_registro = models.DateTimeField(auto_now_add=True)
    
    # Nuevos campos personales
    ESTADO_CIVIL_CHOICES = [
        ('soltero', 'Soltero'),
        ('casado', 'Casado'),
        ('divorciado', 'Divorciado'),
        ('viudo', 'Viudo'),
    ]
    estado_civil = models.CharField(max_length=20, choices=ESTADO_CIVIL_CHOICES, blank=True)
    
    ESCOLARIDAD_CHOICES = [
        ('primaria', 'Primaria'),
        ('secundaria', 'Secundaria'),
        ('preparatoria', 'Preparatoria'),
        ('licenciatura', 'Licenciatura'),
        ('especialidad', 'Especialidad'),
    ]
    escolaridad = models.CharField(max_length=20, choices=ESCOLARIDAD_CHOICES, blank=True)
    
    ocupacion = models.CharField(max_length=100, blank=True)
    rfc = models.CharField(max_length=13, blank=True, verbose_name="RFC")
    
    # Antecedentes médicos
    diabetes = models.BooleanField(default=False)
    hipertension_arterial = models.BooleanField(default=False, verbose_name="Hipertensión arterial")
    obesidad = models.BooleanField(default=False)
    cancer = models.BooleanField(default=False, verbose_name="Cáncer")
    otra_enfermedad = models.TextField(blank=True, verbose_name="Otra enfermedad")
    medicamentos = models.TextField(blank=True)
    
    # Hábitos
    fuma = models.BooleanField(default=False)
    bebe = models.BooleanField(default=False)
    actividad_fisica = models.BooleanField(default=False, verbose_name="Actividad física")
    
    # Horarios de alimentación
    horario_desayuno = models.TimeField(null=True, blank=True)
    horario_comida = models.TimeField(null=True, blank=True)
    horario_cena = models.TimeField(null=True, blank=True)
    
    # Síntomas digestivos
    distension_despues_comer = models.BooleanField(default=False, verbose_name="Distensión después de comer")
    dolor_estomago = models.BooleanField(default=False, verbose_name="Dolor en la boca del estómago")
    estrenimiento = models.BooleanField(default=False, verbose_name="Estreñimiento")
    
    # Campos médicos básicos (existentes)
    alergias = models.TextField(blank=True)
    antecedentes = models.TextField(blank=True)

    llave_unica = models.UUIDField(
    default=uuid.uuid4, 
    editable=False, 
    unique=True,
    verbose_name="Llave Única de Acceso"
    )
    usuario = models.OneToOneField(
        User, 
        on_delete=models.SET_NULL, # Si se borra el usuario, el paciente no se borra
        null=True, 
        blank=True,
        related_name='paciente_profile'
    )
   
    def __str__(self):
        return f"{self.nombre} {self.apellidos}"
    
    def calcular_edad(self):
        from datetime import date
        today = date.today()
        return today.year - self.fecha_nacimiento.year - ((today.month, today.day) < (self.fecha_nacimiento.month, self.fecha_nacimiento.day))
