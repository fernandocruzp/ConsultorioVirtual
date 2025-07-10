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
from django.http import HttpResponse
import io
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from django.core.mail import EmailMessage
from django.conf import settings
import os
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet

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

@login_required
@group_required('Medicos')
def generar_pdf_historial(request, paciente_id):
    paciente = get_object_or_404(Paciente, id=paciente_id)
    
    # Obtener historial de consultas del paciente
    historial_consultas = Consulta.objects.filter(
        paciente=paciente
    ).order_by('-fecha')
    
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
        logo_filename = 'Logo3.png' 
        logo_path_full = os.path.join(settings.STATICFILES_DIRS[0], 'img', logo_filename)
        if os.path.exists(logo_path_full):
            logo_path = logo_path_full
    except (IndexError, AttributeError):
        pass

    # --- ENCABEZADO ---
    y_position = height - inch 

    if logo_path:
        p.drawImage(logo_path, x=2.6*inch, y=height - 1.50*inch, width=2.8*inch, preserveAspectRatio=True, mask='auto')

    p.line(inch, height - 1.2*inch, width - inch, height - 1.2*inch)
    
    # Título
    p.setFont("Helvetica-Bold", 18)
    p.drawCentredString(width/2, height - 1.8*inch, "HISTORIAL")
    
    # Información del paciente
    p.setFont("Helvetica-Bold", 12)
    p.drawString(inch, height - 2.5*inch, "Paciente:")
    p.setFont("Helvetica", 12)
    p.drawString(2*inch, height - 2.5*inch, f"{paciente.nombre} {paciente.apellidos}")
    p.setFont("Helvetica-Bold", 12)
    p.drawString(inch, height - 2.7*inch, "Para más información usa el siguiente enlace:")
    p.setFont("Helvetica", 12)
    p.drawString(inch, height - 2.9*inch, "https://pinedaintegralmedic.onrender.com/portal/")
    p.setFont("Helvetica-Bold", 12)
    p.drawString(inch, height - 3.1*inch, "Llave de acceso:")
    p.drawString(2.5*inch, height - 3.1*inch, f"{paciente.llave_unica}")
    
    # Tabla de historial
    y_position = height - 3.5*inch
    
    # Encabezados de la tabla
    p.setFont("Helvetica-Bold", 10)
    p.drawString(inch, y_position, "Fecha")
    p.drawString(inch + 1.2*inch, y_position, "Peso (kg)")
    p.drawString(inch + 2.4*inch, y_position, "IMC")
    p.drawString(inch + 3.6*inch, y_position, "Cintura (cm)")
    p.drawString(inch + 4.8*inch, y_position, "Cadera (cm)")
    
    # Línea debajo de los encabezados
    y_position -= 0.2*inch
    p.line(inch, y_position, width - inch, y_position)
    
    # Datos de la tabla
    y_position -= 0.3*inch
    p.setFont("Helvetica", 10)
    
    for consulta in historial_consultas:
        if y_position < 2*inch:  # Si estamos cerca del final de la página, crear una nueva
            p.showPage()
            y_position = height - inch
            
            # Repetir encabezados en la nueva página
            p.setFont("Helvetica-Bold", 10)
            p.drawString(inch, y_position, "Fecha")
            p.drawString(inch + 1.2*inch, y_position, "Peso (kg)")
            p.drawString(inch + 2.4*inch, y_position, "IMC")
            p.drawString(inch + 3.6*inch, y_position, "Cintura (cm)")
            p.drawString(inch + 4.8*inch, y_position, "Cadera (cm)")
            
            # Línea debajo de los encabezados
            y_position -= 0.2*inch
            p.line(inch, y_position, width - inch, y_position)
            y_position -= 0.3*inch
            p.setFont("Helvetica", 10)
        
        p.drawString(inch, y_position, consulta.fecha.strftime('%d/%m/%Y'))
        p.drawString(inch + 1.2*inch, y_position, str(consulta.peso) if consulta.peso else "-")
        p.drawString(inch + 2.4*inch, y_position, f"{consulta.imc:.2f}" if consulta.imc else "-")
        p.drawString(inch + 3.6*inch, y_position, str(consulta.circunferencia_cintura) if consulta.circunferencia_cintura else "-")
        p.drawString(inch + 4.8*inch, y_position, str(consulta.circunferencia_cadera) if consulta.circunferencia_cadera else "-")
        
        y_position -= 0.25*inch
    
    # Pie de página
    p.showPage()
    p.save()
    
    # Preparar la respuesta
    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="Historial_{paciente.apellidos}.pdf"'
    
    return response

@login_required
@group_required('Medicos')
def enviar_historial_email(request, paciente_id):
    paciente = get_object_or_404(Paciente, id=paciente_id)
    
    # Obtener historial de consultas del paciente
    historial_consultas = Consulta.objects.filter(
        paciente=paciente
    ).order_by('-fecha')
    
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
        logo_filename = 'Logo3.png' 
        logo_path_full = os.path.join(settings.STATICFILES_DIRS[0], 'img', logo_filename)
        if os.path.exists(logo_path_full):
            logo_path = logo_path_full
    except (IndexError, AttributeError):
        pass

    # --- ENCABEZADO ---
    y_position = height - inch 

    if logo_path:
        p.drawImage(logo_path, x=2.6*inch, y=height - 1.50*inch, width=2.8*inch, preserveAspectRatio=True, mask='auto')

    p.line(inch, height - 1.2*inch, width - inch, height - 1.2*inch)
    
    # Título
    p.setFont("Helvetica-Bold", 18)
    p.drawCentredString(width/2, height - 1.8*inch, "HISTORIAL")
    
    # Información del paciente
    p.setFont("Helvetica-Bold", 12)
    p.drawString(inch, height - 2.5*inch, "Paciente:")
    p.setFont("Helvetica", 12)
    p.drawString(2*inch, height - 2.5*inch, f"{paciente.nombre} {paciente.apellidos}")
    p.setFont("Helvetica-Bold", 12)
    p.drawString(inch, height - 2.7*inch, "Para más información usa el siguiente enlace:")
    p.setFont("Helvetica", 12)
    p.drawString(inch, height - 2.9*inch, "https://pinedaintegralmedic.onrender.com/portal/")
    p.setFont("Helvetica-Bold", 12)
    p.drawString(inch, height - 3.1*inch, "Llave de acceso:")
    p.drawString(2.5*inch, height - 3.1*inch, f"{paciente.llave_unica}")
    
    # Tabla de historial
    y_position = height - 3.5*inch
    
    # Encabezados de la tabla
    p.setFont("Helvetica-Bold", 10)
    p.drawString(inch, y_position, "Fecha")
    p.drawString(inch + 1.2*inch, y_position, "Peso (kg)")
    p.drawString(inch + 2.4*inch, y_position, "IMC")
    p.drawString(inch + 3.6*inch, y_position, "Cintura (cm)")
    p.drawString(inch + 4.8*inch, y_position, "Cadera (cm)")
    
    # Línea debajo de los encabezados
    y_position -= 0.2*inch
    p.line(inch, y_position, width - inch, y_position)
    
    # Datos de la tabla
    y_position -= 0.3*inch
    p.setFont("Helvetica", 10)
    
    for consulta in historial_consultas:
        if y_position < 2*inch:  # Si estamos cerca del final de la página, crear una nueva
            p.showPage()
            y_position = height - inch
            
            # Repetir encabezados en la nueva página
            p.setFont("Helvetica-Bold", 10)
            p.drawString(inch, y_position, "Fecha")
            p.drawString(inch + 1.2*inch, y_position, "Peso (kg)")
            p.drawString(inch + 2.4*inch, y_position, "IMC")
            p.drawString(inch + 3.6*inch, y_position, "Cintura (cm)")
            p.drawString(inch + 4.8*inch, y_position, "Cadera (cm)")
            
            # Línea debajo de los encabezados
            y_position -= 0.2*inch
            p.line(inch, y_position, width - inch, y_position)
            y_position -= 0.3*inch
            p.setFont("Helvetica", 10)
        
        p.drawString(inch, y_position, consulta.fecha.strftime('%d/%m/%Y'))
        p.drawString(inch + 1.2*inch, y_position, str(consulta.peso) if consulta.peso else "-")
        p.drawString(inch + 2.4*inch, y_position, f"{consulta.imc:.2f}" if consulta.imc else "-")
        p.drawString(inch + 3.6*inch, y_position, str(consulta.circunferencia_cintura) if consulta.circunferencia_cintura else "-")
        p.drawString(inch + 4.8*inch, y_position, str(consulta.circunferencia_cadera) if consulta.circunferencia_cadera else "-")
        
        y_position -= 0.25*inch
    
    # Pie de página
    p.showPage()
    p.save()
    
    # Preparar el correo electrónico
    buffer.seek(0)
    
    # Verificar si el paciente tiene correo electrónico
    if not paciente.email:
        messages.error(request, "El paciente no tiene un correo electrónico registrado.")
        return redirect('pacientes:historial_completo', paciente_id=paciente.id)
    
    # Enviar el correo
    email = EmailMessage(
        f'Historial Médico - {paciente.nombre} {paciente.apellidos}',
        f'Estimado/a {paciente.nombre},\n\nAdjunto encontrará su historial médico.\n\nAtentamente,\nPineda Integralmedic',
        settings.DEFAULT_FROM_EMAIL,
        [paciente.email],
    )
    email.attach(f'Historial_{paciente.apellidos}.pdf', buffer.getvalue(), 'application/pdf')
    
    try:
        email.send()
        messages.success(request, f"El historial ha sido enviado a {paciente.email}")
    except Exception as e:
        messages.error(request, f"Error al enviar el correo: {str(e)}")
    
    return redirect('pacientes:historial_completo', paciente_id=paciente.id)
@login_required
@group_required('Medicos')
def generar_pdf_historial(request, paciente_id):
    buffer, paciente = generar_pdf_historial_buffer(paciente_id)
    
    # Preparar la respuesta HTTP
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="Historial_{paciente.apellidos}.pdf"'
    
    return response

@login_required
@group_required('Medicos')
def enviar_historial_email(request, paciente_id):
    buffer, paciente = generar_pdf_historial_buffer(paciente_id)
    
    # Verificar si el paciente tiene correo electrónico
    if not paciente.email:
        messages.error(request, "El paciente no tiene un correo electrónico registrado.")
        return redirect(f'/pacientes/historial/{paciente_id}/')
    
    # Enviar el correo
    email = EmailMessage(
        subject=f'Historial Médico - Pineda IntegralMedic',
        body=f'Estimado/a {paciente.nombre},\n\nAdjunto encontrará su historial médico.\n\nSaludos cordiales,\nPineda IntegralMedic',
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[paciente.email],
    )
    email.attach(f'Historial_{paciente.apellidos}.pdf', buffer.getvalue(), 'application/pdf')
    
    try:
        email.send()
        messages.success(request, f'Historial médico enviado correctamente a {paciente.email}.')
    except Exception as e:
        messages.error(request, f'Error al enviar el correo: {str(e)}')
    
    return redirect(f'/pacientes/historial/{paciente_id}/')
def generar_pdf_historial_buffer(paciente_id):
    """
    Función refactorizada para generar el buffer del PDF del historial.
    Esta función puede ser reutilizada por diferentes vistas.
    """
    paciente = get_object_or_404(Paciente, id=paciente_id)
    
    # Obtener historial de consultas del paciente
    historial_consultas = Consulta.objects.filter(
        paciente=paciente
    ).order_by('-fecha')
    
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
        logo_filename = 'Logo3.png' 
        logo_path_full = os.path.join(settings.STATICFILES_DIRS[0], 'img', logo_filename)
        if os.path.exists(logo_path_full):
            logo_path = logo_path_full
    except (IndexError, AttributeError):
        pass

    # --- ENCABEZADO ---
    y_position = height - inch 

    if logo_path:
        p.drawImage(logo_path, x=2.6*inch, y=height - 1.50*inch, width=2.8*inch, preserveAspectRatio=True, mask='auto')

    p.line(inch, height - 1.2*inch, width - inch, height - 1.2*inch)
    
    # Título
    p.setFont("Helvetica-Bold", 18)
    p.drawCentredString(width/2, height - 1.8*inch, "HISTORIAL")
    
    # Información del paciente
    p.setFont("Helvetica-Bold", 12)
    p.drawString(inch, height - 2.5*inch, "Paciente:")
    p.setFont("Helvetica", 12)
    p.drawString(2*inch, height - 2.5*inch, f"{paciente.nombre} {paciente.apellidos}")
    p.setFont("Helvetica-Bold", 12)
    p.drawString(inch, height - 2.7*inch, "Para más información usa el siguiente enlace:")
    p.setFont("Helvetica", 12)
    p.drawString(inch, height - 2.9*inch, "https://pinedaintegralmedic.onrender.com/portal/")
    p.setFont("Helvetica-Bold", 12)
    p.drawString(inch, height - 3.1*inch, "Llave de acceso:")
    p.drawString(2.5*inch, height - 3.1*inch, f"{paciente.llave_unica}")
    
    # Contenido del historial
    data = [[
        h.fecha.strftime('%d/%m/%Y'),                 
        f"{h.circunferencia_cintura} cm" if h.circunferencia_cintura else "-",
        f"{h.circunferencia_cadera} cm" if h.circunferencia_cadera else "-",
        f"{h.circunferencia_pecho} cm" if h.circunferencia_pecho else "-",
        f"{h.tratamiento}" if hasattr(h, 'tratamiento') and h.tratamiento else "-",
        f"{h.tension_arterial}" if h.tension_arterial else "-",
        f"{h.peso} kg" if h.peso else "-",               
        f"{h.altura} cm" if h.altura else "-",             
        f"{h.imc:.2f}" if h.imc else "-"
    ]
    for h in historial_consultas]

    data.insert(0,["Fecha" , "Cintura", "Cadera", "Pecho", "Tx", "T/A","Peso", "Altura", "IMC"])

    plan_table = Table(data, colWidths=[1.0*inch, 0.75*inch,0.75*inch,0.75*inch, 0.5*inch,0.75*inch,0.75*inch,0.75*inch,0.5*inch])

    style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4F81BD')), # Color de fondo para la cabecera
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke), # Color de texto para la cabecera
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'), # Alineación centrada para toda la tabla
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'), # Alineación vertical centrada
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'), # Fuente en negrita para la cabecera
        ('FONTSIZE', (0, 0), (-1, 0), 12), # Tamaño de fuente para la cabecera
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12), # Padding inferior para la cabecera
        
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige), # Color de fondo para las filas de datos
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black), # Color de texto para los datos
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'), # Fuente para los datos
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.black) # Dibuja una cuadrícula en toda la tabla
    ])
    plan_table.setStyle(style)

    y_position = height - 4*inch
    ancho_necesario, alto_necesario = plan_table.wrapOn(p, width - 2*inch, 0)
    plan_table.drawOn(p, inch, y_position - alto_necesario)
           
    # Pie de página
    p.line(inch, 1.1*inch, width - inch, 1.1*inch)
    p.setFont("Helvetica-Oblique", 10)
    p.drawCentredString(width/2, inch, "Pineda IntegralMedic - Historial")
    
    # Cerrar el PDF
    p.showPage()
    p.save()
    
    # Obtener el valor del buffer
    buffer.seek(0)
    return buffer, paciente
@login_required
@group_required('Medicos')
def enviar_historial_whatsapp(request, paciente_id):
    """
    Función para abrir WhatsApp Web para enviar el historial.
    Compatible con entornos de servidor web.
    """
    paciente = get_object_or_404(Paciente, id=paciente_id)
    
    # Verificar si el paciente tiene teléfono
    if not paciente.telefono:
        messages.error(request, "El paciente no tiene un número de teléfono registrado.")
        return redirect(f'/pacientes/historial/{paciente_id}/')
    
    import urllib.parse
    import re
    
    # Formatear el número de teléfono (eliminar caracteres no numéricos)
    telefono = re.sub(r'\D', '', paciente.telefono)
    
    # Si el número no tiene código de país, agregar +52 (México)
    if len(telefono) == 10:  # Número mexicano sin código de país
        telefono = "52" + telefono
    
    # Preparar mensaje para WhatsApp
    mensaje = f"Hola {paciente.nombre}, te comparto tu historial médico de Pineda IntegralMedic."
    mensaje_codificado = urllib.parse.quote(mensaje)
    
    # URL de WhatsApp Web
    whatsapp_url = f"https://web.whatsapp.com/send?phone={telefono}&text={mensaje_codificado}"
    
    # Mostrar mensaje al usuario
    messages.success(request, f"Para enviar el historial a {paciente.nombre} por WhatsApp: 1) Descargue primero el PDF usando el botón 'Guardar PDF', 2) Se abrirá WhatsApp Web en una nueva pestaña para enviar el mensaje.")
    
    # Devolver una respuesta que incluya JavaScript para abrir WhatsApp Web en una nueva pestaña
    from django.http import HttpResponse
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Redirigiendo a WhatsApp</title>
        <script>
            // Abrir WhatsApp Web en una nueva pestaña
            window.open("{whatsapp_url}", "_blank");
            
            // Redirigir de vuelta a la página del historial
            window.location.href = "/pacientes/historial/{paciente_id}/";
        </script>
    </head>
    <body>
        <p>Redirigiendo a WhatsApp Web...</p>
    </body>
    </html>
    """
    
    return HttpResponse(html)
