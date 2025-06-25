from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from .decorators import group_required
from consultas.models import Consulta, PlanNutricional
from agenda.models import Cita
from pacientes.models import Paciente
import json
from django.http import HttpResponse
import io
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from django.core.mail import EmailMessage
from django.conf import settings
from django.contrib.auth import get_user_model
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
import os

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
@group_required('Pacientes')
def historial_completo(request):
    paciente = request.user.paciente_profile
    
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

@login_required
@group_required('Pacientes')
def detalle_consulta(request, consulta_id):
    consulta = get_object_or_404(Consulta, id=consulta_id)
    
    # Obtener historial de consultas del paciente
    historial_consultas = Consulta.objects.filter(
        paciente=consulta.paciente
    ).exclude(id=consulta_id).order_by('-fecha')
    
    return render(request, 'portal/detalle_consulta.html', {
        'consulta': consulta,
        'historial_consultas': historial_consultas,
    })

@login_required
@group_required('Pacientes')
def detalle_plan(request, plan_id):
    plan = get_object_or_404(PlanNutricional, id=plan_id)
    return render(request, 'portal/plan_nutricional.html', {
        'plan': plan,
    })

@login_required
@group_required('Pacientes')
def generar_pdf_plan(request, plan_id):
    
    plan = get_object_or_404(PlanNutricional, id=plan_id)
    
    # Crear un buffer para el PDF
    buffer = io.BytesIO()

    
    # Crear el objeto PDF usando ReportLab
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    # Define estilos para los párrafos
    styles = getSampleStyleSheet()
    style_normal = styles['Normal']
    style_normal.leading = 14
    style_bold = styles['h2']

    # --- ENCABEZADO ---
    logo_path = None
    try:
        # CORRECCIÓN: Usar el nombre de TU archivo "lavado"
        logo_filename = 'Logo2.png' 
        logo_path_full = os.path.join(settings.STATICFILES_DIRS[0], 'img', logo_filename)
        if os.path.exists(logo_path_full):
            logo_path = logo_path_full
    except (IndexError, AttributeError):
        pass

    # --- ENCABEZADO ---
    y_position = height - inch 

    if logo_path:
        p.drawImage(logo_path, x=2.6*inch, y=height - 2.50*inch, width=3.5*inch, preserveAspectRatio=True, mask='auto')

    p.line(inch, height - 1.2*inch, width - inch, height - 1.2*inch)
    
    # Título
    p.setFont("Helvetica-Bold", 18)
    p.drawCentredString(width/2, height - 1.5*inch, "Plan Nutricional")
    
    # Información del paciente
    p.setFont("Helvetica-Bold", 12)
    p.drawString(inch, height - 2*inch, "Paciente:")
    p.setFont("Helvetica", 12)
    p.drawString(2*inch, height - 2*inch, f"{plan.consulta.paciente.nombre} {plan.consulta.paciente.apellidos}")
    
    p.setFont("Helvetica-Bold", 12)
    p.drawString(inch, height - 2.5*inch, "Fecha:")
    p.setFont("Helvetica", 12)
    p.drawString(2*inch, height - 2.5*inch, plan.fecha_creacion.strftime("%d/%m/%Y"))
    
    # Mediciones
    p.setFont("Helvetica-Bold", 12)
    p.drawString(inch, height - 3*inch, "Mediciones:")
    p.setFont("Helvetica", 12)
    p.drawString(2*inch, height - 3*inch, 
                f"Peso: {plan.consulta.peso} kg | Altura: {plan.consulta.altura} cm | IMC: {plan.consulta.imc:.2f}")
    
    # Contenido del plan
    p.setFont("Helvetica-Bold", 14)
    p.drawString(inch, height - 4*inch, "Plan Nutricional:")

    contenido_html = plan.contenido.replace('\n', '<br/>')

    plan_paragraph = Paragraph(contenido_html, style_normal)

    plan_paragraph.wrapOn(p, width - 2*inch, height - 5*inch)
    plan_paragraph.drawOn(p, inch, height - 4.5*inch - plan_paragraph.height)
           
    # Pie de página
    p.line(inch, 1.1*inch, width - inch, 1.1*inch)
    p.setFont("Helvetica-Oblique", 10)
    p.drawCentredString(width / 2, 0.25 * inch, "Pineda IntegralMedic - Plan Nutricional Personalizado")
    
    # Cerrar el PDF
    p.showPage()
    p.save()
    
    # Obtener el valor del buffer y crear la respuesta HTTP
    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="Plan_Nutricional_{plan.consulta.paciente.apellidos}.pdf"'
    
    return response


@login_required
@group_required('Pacientes')
def detalle_cita(request, cita_id):
    cita = get_object_or_404(Cita, id=cita_id)
    
    # Obtener consultas del paciente
    consultas = Consulta.objects.filter(paciente=cita.paciente).order_by('-fecha')[:5]
    
    # Obtener otras citas del paciente
    otras_citas = Cita.objects.filter(paciente=cita.paciente).exclude(id=cita_id).order_by('fecha_hora')[:5]
    
    return render(request, 'portal/detalle_cita.html', {
        'cita': cita,
        'consultas': consultas,
        'otras_citas': otras_citas,
    })
