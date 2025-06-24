from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from .decorators import group_required
def inicio_portal(request):
    if request.user.is_authenticated and hasattr(request.user, 'paciente_profile'):
        return redirect('portal:portal_dashboard')

    if request.method == 'POST':
        llave = request.POST.get('password')
        user = authenticate(request, username=None, password=llave)
        
        if user is not None:
            login(request, user)
            return redirect('portal:portal_dashboard')
        else:
            messages.error(request, 'La llave de acceso no es válida. Por favor, verifíquela.')

    return render(request, 'portal/login.html')



@login_required
@group_required('Pacientes')
def portal_dashboard(request):
    paciente = request.user.paciente_profile
    context = {
        'paciente': paciente
    }
    return render(request, 'portal/base.html')
