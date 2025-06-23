from django.db import models

class Cita(models.Model):
    ESTADO_CHOICES = [
        ('programada', 'Programada'),
        ('completada', 'Completada'),
        ('cancelada', 'Cancelada')
    ]
    
    paciente = models.ForeignKey('pacientes.Paciente', on_delete=models.CASCADE, related_name='citas')
    fecha_hora = models.DateTimeField()
    motivo = models.CharField(max_length=200)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='programada')
    notas = models.TextField(blank=True)
    
    def __str__(self):
        return f"Cita: {self.paciente} - {self.fecha_hora.strftime('%d/%m/%Y %H:%M')}"
    
    class Meta:
        ordering = ['fecha_hora']
