from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.core.paginator import Paginator
from .models import Paciente
from .forms import PacienteForm
from consultas.models import Consulta
from agenda.models import Cita
import json

@login_required
def login(request):
    if request.method == 'POST':
        form = PacienteForm(request.POST)
        if form.is_valid():
            paciente = form.save()
            messages.success(request, f'Paciente {paciente.nombre} {paciente.apellidos} creado correctamente.')
            return redirect('detalle_paciente', paciente_id=paciente.id)
    else:
        form = PacienteForm()
    
    return render(request, 'pacientes/form_paciente.html', {
        'form': form,
    })

@login_required
def detalle_paciente(request, paciente_id):
    paciente = get_object_or_404(Paciente, id=paciente_id)
    consultas = Consulta.objects.filter(paciente=paciente).order_by('-fecha')
    citas = Cita.objects.filter(paciente=paciente, estado='programada').order_by('fecha_hora')
    
    # Obtener la última consulta para mostrar datos recientes
    ultima_consulta = consultas.first()
    
    return render(request, 'portal/detalle_paciente.html', {
        'paciente': paciente,
        'consultas': consultas,
        'citas': citas,
        'ultima_consulta': ultima_consulta,
    })

@login_required
def historial_completo(request, paciente_id):
    paciente = get_object_or_404(Paciente, id=paciente_id)
    
    # Obtener historial de consultas del paciente
    historial_consultas = Consulta.objects.filter(
        paciente=paciente
    ).order_by('-fecha')

    historial_grafica= list(historial_consultas.reverse())

    #Obtenemos datos separados
    fechas=[c.fecha.strftime('%d/%m/%Y') for c in historial_grafica]
    cadera=[c.circunferencia_cadera if c.circunferencia_cadera else 0 for c in historial_grafica]
    cintura=[c.circunferencia_cintura if c.circunferencia_cintura else 0 for c in historial_grafica]
    pecho=[c.circunferencia_pecho if c.circunferencia_pecho else 0 for c in historial_grafica]
    ta=[c.tension_arterial if c.tension_arterial else 0 for c in historial_grafica]
    peso=[c.peso if c.peso else 0 for c in historial_grafica]
    imc=[round(c.imc,2) if c.imc else 0 for c in historial_grafica]
    return render(request, 'portal/historial.html', {
        'paciente': paciente,
        'historial_consultas': historial_consultas,
        'fechas_json': json.dumps(fechas),
        'cadera_json': json.dumps(cadera),
        'cintura_json': json.dumps(cintura),
        'pecho_json': json.dumps(pecho),
        'ta_json': json.dumps(ta),
        'peso_json': json.dumps(peso),
        'imc_json': json.dumps(imc),
    })
