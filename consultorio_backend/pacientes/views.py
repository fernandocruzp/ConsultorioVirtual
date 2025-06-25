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
from portal.decorators import group_required

@login_required
@group_required('Medicos')
def lista_pacientes(request):
    query = request.GET.get('q', '')
    if query:
        pacientes_list = Paciente.objects.filter(
            Q(nombre__icontains=query) | 
            Q(apellidos__icontains=query) | 
            Q(email__icontains=query) |
            Q(telefono__icontains=query)
        ).order_by('apellidos', 'nombre')
    else:
        pacientes_list = Paciente.objects.all().order_by('apellidos', 'nombre')
    
    paginator = Paginator(pacientes_list, 10)  # 10 pacientes por página
    page = request.GET.get('page')
    pacientes = paginator.get_page(page)
    
    return render(request, 'pacientes/lista_pacientes.html', {
        'pacientes': pacientes,
        'is_paginated': pacientes.has_other_pages(),
        'page_obj': pacientes,
    })

@login_required
@group_required('Medicos')
def detalle_paciente(request, paciente_id):
    paciente = get_object_or_404(Paciente, id=paciente_id)
    consultas = Consulta.objects.filter(paciente=paciente).select_related('plan').order_by('-fecha')
    citas = Cita.objects.filter(paciente=paciente, estado='programada').order_by('fecha_hora')
    
    # Obtener la última consulta para mostrar datos recientes
    ultima_consulta = consultas.first()
    
    return render(request, 'pacientes/detalle_paciente.html', {
        'paciente': paciente,
        'consultas': consultas,
        'citas': citas,
        'ultima_consulta': ultima_consulta,
    })

@login_required
@group_required('Medicos')
def nuevo_paciente(request):
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
@group_required('Medicos')
def editar_paciente(request, paciente_id):
    paciente = get_object_or_404(Paciente, id=paciente_id)
    
    if request.method == 'POST':
        form = PacienteForm(request.POST, instance=paciente)
        if form.is_valid():
            form.save()
            messages.success(request, f'Información de {paciente.nombre} {paciente.apellidos} actualizada correctamente.')
            return redirect('detalle_paciente', paciente_id=paciente.id)
    else:
        form = PacienteForm(instance=paciente)
    
    return render(request, 'pacientes/form_paciente.html', {
        'form': form,
        'paciente': paciente,
    })

@login_required
@group_required('Medicos')
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
    return render(request, 'pacientes/historial.html', {
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
