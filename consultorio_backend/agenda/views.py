from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.core.paginator import Paginator
from django.utils import timezone
from .models import Cita
from .forms import CitaForm
from pacientes.models import Paciente
from consultas.models import Consulta
import json

@login_required
def lista_citas(request):
    query = request.GET.get('q', '')
    
    # Obtener todas las citas para el calendario
    todas_citas = Cita.objects.all().select_related('paciente')

    eventos_calendario = []
    for cita in todas_citas:
        eventos_calendario.append({
            'title': f'{cita.paciente.nombre} {cita.paciente.apellidos}',
            'start': cita.fecha_hora.isoformat(),
            'url': f'/agenda/cita/{cita.id}/',
            'className': f'estado-{cita.estado}',
            'extendedProps': {
                'motivo': cita.motivo if cita.motivo else '',
                'estado': cita.estado.capitalize()
            }
        })
    # Convertimos la lista de Python a un string JSON seguro
    citas_json = json.dumps(eventos_calendario)
    
    # Filtrar citas para la lista
    if query:
        citas_list = Cita.objects.filter(
            Q(paciente__nombre__icontains=query) | 
            Q(paciente__apellidos__icontains=query) |
            Q(motivo__icontains=query)
        ).select_related('paciente').order_by('fecha_hora')
    else:
        # Por defecto, mostrar solo citas futuras o del día actual
        hoy = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        citas_list = Cita.objects.filter(
            fecha_hora__gte=hoy
        ).select_related('paciente').order_by('fecha_hora')
    
    paginator = Paginator(citas_list, 10)  # 10 citas por página
    page = request.GET.get('page')
    citas = paginator.get_page(page)
    
    return render(request, 'agenda/lista_citas.html', {
        'citas': citas,
        'todas_citas': todas_citas,
        'is_paginated': citas.has_other_pages(),
        'page_obj': citas,
        'citasJson': citas_json,
    })

@login_required
def detalle_cita(request, cita_id):
    cita = get_object_or_404(Cita, id=cita_id)
    
    # Obtener consultas del paciente
    consultas = Consulta.objects.filter(paciente=cita.paciente).order_by('-fecha')[:5]
    
    # Obtener otras citas del paciente
    otras_citas = Cita.objects.filter(paciente=cita.paciente).exclude(id=cita_id).order_by('fecha_hora')[:5]
    
    return render(request, 'agenda/detalle_cita.html', {
        'cita': cita,
        'consultas': consultas,
        'otras_citas': otras_citas,
    })

@login_required
def nueva_cita(request, paciente_id=None):
    paciente = None
    if paciente_id:
        paciente = get_object_or_404(Paciente, id=paciente_id)
    
    if request.method == 'POST':
        form = CitaForm(request.POST)
        if form.is_valid():
            cita = form.save(commit=False)
            if paciente:
                cita.paciente = paciente
            cita.save()
            messages.success(request, f'Cita para {cita.paciente.nombre} {cita.paciente.apellidos} programada correctamente.')
            return redirect('detalle_cita', cita_id=cita.id)
    else:
        initial_data = {}
        if paciente:
            initial_data['paciente'] = paciente
        
        form = CitaForm(initial=initial_data)
        
        # Si hay un paciente seleccionado, no mostrar el campo de selección de paciente
        if paciente:
            form.fields['paciente'].widget = form.fields['paciente'].hidden_widget()
    
    return render(request, 'agenda/form_cita.html', {
        'form': form,
        'paciente': paciente,
    })

@login_required
def editar_cita(request, cita_id):
    cita = get_object_or_404(Cita, id=cita_id)
    
    # Solo permitir editar citas programadas
    if cita.estado != 'programada':
        messages.warning(request, f'No se puede editar una cita que ya ha sido {cita.estado}.')
        return redirect('detalle_cita', cita_id=cita.id)
    
    if request.method == 'POST':
        form = CitaForm(request.POST, instance=cita)
        if form.is_valid():
            form.save()
            messages.success(request, f'Cita para {cita.paciente.nombre} {cita.paciente.apellidos} actualizada correctamente.')
            return redirect('detalle_cita', cita_id=cita.id)
    else:
        form = CitaForm(instance=cita)
        # No permitir cambiar el paciente
        form.fields['paciente'].widget.attrs['readonly'] = True
    
    return render(request, 'agenda/form_cita.html', {
        'form': form,
        'cita': cita,
    })

@login_required
def completar_cita(request, cita_id):
    cita = get_object_or_404(Cita, id=cita_id)
    
    # Solo permitir completar citas programadas
    if cita.estado != 'programada':
        messages.warning(request, f'Esta cita ya ha sido {cita.estado}.')
        return redirect('detalle_cita', cita_id=cita.id)
    
    cita.estado = 'completada'
    cita.save()
    
    messages.success(request, f'Cita para {cita.paciente.nombre} {cita.paciente.apellidos} marcada como completada.')
    return redirect('detalle_cita', cita_id=cita.id)

@login_required
def cancelar_cita(request, cita_id):
    cita = get_object_or_404(Cita, id=cita_id)
    
    # Solo permitir cancelar citas programadas
    if cita.estado != 'programada':
        messages.warning(request, f'Esta cita ya ha sido {cita.estado}.')
        return redirect('detalle_cita', cita_id=cita.id)
    
    cita.estado = 'cancelada'
    cita.save()
    
    messages.success(request, f'Cita para {cita.paciente.nombre} {cita.paciente.apellidos} cancelada.')
    return redirect('detalle_cita', cita_id=cita.id)
