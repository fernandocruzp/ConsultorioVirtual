from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.utils import timezone
from datetime import timedelta
from pacientes.models import Paciente
from consultas.models import Consulta
from agenda.models import Cita
from .forms import UserEmailChangeForm

@login_required
def dashboard(request):
    # Obtener estadísticas
    total_pacientes = Paciente.objects.count()
    
    # Consultas del mes actual
    hoy = timezone.now()
    primer_dia_mes = hoy.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    consultas_mes = Consulta.objects.filter(fecha__gte=primer_dia_mes).count()
    
    # Citas pendientes
    citas_pendientes = Cita.objects.filter(estado='programada').count()
    
    # Citas para hoy
    inicio_dia = hoy.replace(hour=0, minute=0, second=0, microsecond=0)
    fin_dia = inicio_dia + timedelta(days=1)
    citas_hoy = Cita.objects.filter(fecha_hora__gte=inicio_dia, fecha_hora__lt=fin_dia).count()
    
    # Próximas citas
    proximas_citas = Cita.objects.filter(
        estado='programada',
        fecha_hora__gte=hoy
    ).order_by('fecha_hora')[:5]
    
    # Últimas consultas
    ultimas_consultas = Consulta.objects.all().order_by('-fecha')[:5]
    
    context = {
        'total_pacientes': total_pacientes,
        'consultas_mes': consultas_mes,
        'citas_pendientes': citas_pendientes,
        'citas_hoy': citas_hoy,
        'proximas_citas': proximas_citas,
        'ultimas_consultas': ultimas_consultas,
    }
    
    return render(request, 'base/dashboard.html', context)

@login_required
def cambiar_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Importante para mantener la sesión activa
            messages.success(request, 'Su contraseña ha sido actualizada correctamente.')
            return redirect('cambiar_password')
        else:
            messages.error(request, 'Por favor corrija los errores indicados.')
    else:
        form = PasswordChangeForm(request.user)
    
    return render(request, 'base/cambiar_password.html', {
        'form': form
    })

@login_required
def cambiar_correo(request):
    usuario= request.user
    if request.method == 'POST':
        form = UserEmailChangeForm(request.POST,instance=usuario)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Importante para mantener la sesión activa
            messages.success(request, 'Su correo ha sido actualizado correctamente.')
            return redirect('cambiar_correo')
        else:
            messages.error(request, 'Por favor corrija los errores indicados.')
    else:
        form = UserEmailChangeForm(instance=usuario)
    
    return render(request, 'base/cambiar_correo.html', {
        'form': form
    })
