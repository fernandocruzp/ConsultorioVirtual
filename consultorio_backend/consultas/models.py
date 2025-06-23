from django.db import models

class Consulta(models.Model):
    paciente = models.ForeignKey('pacientes.Paciente', on_delete=models.CASCADE, related_name='consultas')
    fecha = models.DateTimeField(auto_now_add=True)
    
    # Mediciones antropométricas
    peso = models.FloatField(help_text="Peso en kilogramos")
    altura = models.FloatField(help_text="Altura en centímetros")
    imc = models.FloatField(editable=False)  # Calculado automáticamente
    circunferencia_cintura = models.FloatField(null=True, blank=True, verbose_name="Cintura (cm)")
    circunferencia_cadera = models.FloatField(null=True, blank=True, verbose_name="Cadera (cm)")
    circunferencia_pecho = models.FloatField(null=True, blank=True, verbose_name="Pecho (cm)")
    
    # Signos vitales
    tension_arterial = models.CharField(max_length=10, null=True, blank=True, verbose_name="T/A")
    
    # Tratamiento
    tratamiento = models.TextField(null=True, blank=True, verbose_name="TX")
    
    # Observaciones
    observaciones = models.TextField(blank=True)
    
    def save(self, *args, **kwargs):
        # Calcular IMC automáticamente
        self.imc = self.peso / ((self.altura/100) ** 2)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Consulta de {self.paciente} - {self.fecha.strftime('%d/%m/%Y')}"


class PlanNutricional(models.Model):
    consulta = models.OneToOneField('consultas.Consulta', on_delete=models.CASCADE, related_name='plan')
    contenido = models.TextField()
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Plan nutricional - {self.consulta.paciente} - {self.fecha_creacion.strftime('%d/%m/%Y')}"


class Receta(models.Model):
    consulta = models.OneToOneField('consultas.Consulta', on_delete=models.CASCADE, related_name='receta')
    medicamentos = models.TextField(help_text="Lista de medicamentos recetados")
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Receta - {self.consulta.paciente} - {self.fecha_creacion.strftime('%d/%m/%Y')}"
