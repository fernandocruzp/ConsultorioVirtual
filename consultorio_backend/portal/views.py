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
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle, Image, PageBreak
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

def generar_pdf(plan_id):
    plan = get_object_or_404(PlanNutricional, id=plan_id)
    paciente = plan.consulta.paciente
    
    buffer = io.BytesIO()
    
    # 1. Usamos SimpleDocTemplate en lugar de canvas. Define márgenes y tamaño de página.
    doc = SimpleDocTemplate(buffer, pagesize=letter,
                            rightMargin=inch, leftMargin=inch,
                            topMargin=inch, bottomMargin=inch)

    # 2. "Story" es una lista que contendrá todos los elementos de nuestro PDF en orden.
    story = []
    styles = getSampleStyleSheet()

    logo_path = None
    try:
        logo_filename = 'Logo3.png'
        logo_path_full = os.path.join(settings.STATICFILES_DIRS[0], 'img', logo_filename)
        if os.path.exists(logo_path_full):
            logo_path = logo_path_full
    except (IndexError, AttributeError):
        pass

    # --- PÁGINA 1: BIENVENIDA ---
    if logo_path:
        logo = Image(logo_path, width=2*inch, height=1.5*inch)
        logo.hAlign = 'LEFT'
        story.append(logo)
    
    story.append(Spacer(1, 0.15*inch)) # Un espacio en blanco

    texto_bienvenida = """
    Pineda Integralmedic te da la bienvenida y te felicita por el paso que has dado a
    cambiar tu estilo de vida, nosotros te ayudaremos a que tu cambio de hábitos sea más fácil, con la
    ayuda de las herramientas médicas que tenemos a la mano. El método que utilizamos en la Clínica está
    comprobado, con más de 20 años de experiencia. Cada tratamiento será individualizado para cada
    paciente dependiendo su edad, estado de salud y medicamentos que estén tomando. El método que
    utilizamos no contamos calorías, lo que contamos son carbohidratos, motivo por el cual bajaras de peso
    de una forma más rápida que con las dietas convencionales donde solo se cuentan calorías; con nuestro
    método podrás comer la cantidad que gustes de carnes blancas y verduras, con la condición de que te
    sirvas siempre en platos pequeños una cantidad de carne blanca ( proteína) y el doble de verdura , pero
    podrás repetir esa porción cuantas veces gustes siempre y cuando te pares a servirte, para de esta forma
    ir rompiendo la compulsión a seguir comiendo a la que estamos acostumbrados. Te daremos una tabla
    de equivalentes de cereales ( carbohidratos) los cuales trataras de evitar poco a poco, teniendo en
    cuenta que entre menos cereales consumas, más rápido bajaras de peso; es muy importante el consumo
    de agua natural, por lo que tendrás que consumir un mínimo de 2 litros de agua por día, así como
    evitar a toda costa el azúcar, pero podrás consumir sustitutos tales como stevia o splenda para
    endulzar tus alimentos.
    <br/><br/>
    La primera etapa del plan de dieta consiste en una desintoxicación de tu cuerpo, por lo que No
    debes de comer Lácteos ( leche, yogurt, quesos), evitar Carnes rojas ( res, puerco, chivo) y no consumir
    leguminosas ( frijol, lenteja) .Podrás consumir leche de almendra o coco para el suplemento que
    manejamos. También podrás consumir la cantidad que gustes de carnes blancas ( pescado, pollo,
    mariscos, conejo, pavo). Si no te has desparasitado durante este año es conveniente hacerlo , así como
    eliminar hongos de la flora intestinal y reforzarlo con lactobacilos, tu medico te guiara como hacerlo
    para que logres una desintoxicación exitosa. 
    <br/><br/>
    En las consultas subsecuentes al menú se le irán agregando todos los grupos de alimentos, para
    que al final de tu proceso estés comiendo de todo pero en las cantidades adecuadas y seguir bajando de
    peso y mantenerte al final en tu peso deseado.
    <br/><br/>
    Durante el desarrollo de tu dieta es muy importante que trates de comer cada 3-4 hrs donde
    podrás comer todos los alimentos que ahí se te indican si tienes mucho apetito o tu elegir alguno de la
    lista sin no tienes tanto apetito, pero por ningún motivo omitas tus colaciones.
    <br/><br/>
    Estamos seguros que lograras tus metas y llegaras a tu peso deseado, logrando pasar las tres
    etapas del tratamiento: aceleración del metabolismo, estabilización y mantenimiento, para que no
    recuperes el peso perdido. No suspendas tu tratamiento repentinamente sin antes estabilizarte para
    evitar los famosos rebotes.
    <br/><br/>
    En la parte trasera de tu carnet se encuentra el Whatsaap de tu Medico al cual podrás contactar en
    cualquier momento si presentas alguna duda o malestar durante tu tratamiento.
    <br/><br/>
    <b>Pineda Integralmedic</b>
    """
    story.append(Paragraph(texto_bienvenida, styles['Normal']))

    # Forzamos un salto a una nueva página
    story.append(PageBreak())

    # --- PÁGINA 2: EQUIVALENTES ---
    if logo_path:
        story.append(Image(logo_path, width=2*inch, height=1.5*inch, hAlign='CENTER'))


    linea_texto = '_' * 80 
    linea_separadora = Paragraph(linea_texto, styles['Normal'])
    story.append(linea_separadora)
    
    story.append(Spacer(1, 0.25*inch))
    story.append(Paragraph("EQUIVALENTES DE CEREALES", styles['h1']))
    story.append(Spacer(1, 0.2*inch))

    texto_equivalentes = """
        1. UNA TORTILLA DE MAIZ<br/>
        2. 4 TORETILLAS DE NOPAL 20 KCAL<br/>
        3. 3 TORTILLAS DE TOMATE DE 30 KCAL<br/>
        4. UNA REBANADA DE PAN INTEGRAL<br/>
        5. 2 PIEZAS DE PAN DE 45 KCAL ( SARALEE)<br/>
        6. 1/2 TAZA DE ARROZ INTEGRAL<br/>
        7. 1/2 TAZA DE QUINOA<br/>
        8. 1/2 PAPA COCIDA<br/>
        9. 1/2 TAZA DE ELOTES<br/>
        10. 1/2 TAZA DE AVENA<br/>
        11. 5 GALLETAS HABANERA INTEGRALES<br/>
        12. 1 PAQUETE DE TOSTADAS (SALMA)<br/>
        13. 2 CUCHARADAS DE GRANOLA<br/>
        14. 1/2 TAZA DE PASTA INTEGRAL
    """
    story.append(Paragraph(texto_equivalentes, styles['Normal']))

    # Forzamos otro salto de página
    story.append(PageBreak())

    # --- PÁGINA 3: PLAN NUTRICIONAL PERSONALIZADO ---
    if logo_path:
        story.append(Image(logo_path, width=2*inch, height=1.5*inch, hAlign='CENTER'))
        
    linea_texto = '_' * 80 
    linea_separadora = Paragraph(linea_texto, styles['Normal'])

    # Y simplemente añádelo a tu historia donde quieras la línea
    story.append(linea_separadora)
    story.append(Paragraph("Plan Nutricional", styles['h1']))
    story.append(Spacer(1, 0.2*inch))
    
    info_paciente = f"""
        <b>Paciente:</b> {paciente.nombre} {paciente.apellidos}<br/>
        <b>Fecha:</b> {plan.fecha_creacion.strftime('%d/%m/%Y')}<br/>
        <b>Mediciones:</b> Peso: {plan.consulta.peso} kg | Altura: {plan.consulta.altura} cm | IMC: {plan.consulta.imc:.2f}
    """
    story.append(Paragraph(info_paciente, styles['Normal']))
    story.append(Spacer(1, 0.3*inch))

    story.append(Paragraph("<b><u>Plan Nutricional:</u></b>", styles['Normal']))
    story.append(Spacer(1, 0.2*inch))
    secciones_plan = [
    ('Desayuno', plan.contenido_desayuno),
    ('Colación', plan.contenido_colacion),
    ('Comida', plan.contenido_comida),
    ('Colación', plan.contenido_colacion), 
    ('Cena', plan.contenido_cena)
    ]

    # Definimos estilos para los títulos y el contenido de las comidas
    style_titulo_comida = styles['h3']
    style_contenido_comida = styles['BodyText']
    
    for titulo, contenido in secciones_plan:
        if contenido and contenido.strip():        
            story.append(Paragraph(titulo, style_titulo_comida))
            contenido_html = contenido.replace('\n', '<br/>')
            story.append(Paragraph(contenido_html, style_contenido_comida))
            story.append(Spacer(1, 0.2*inch))

    def pie_de_pagina(canvas, doc):
        canvas.saveState()
        canvas.setFont('Helvetica-Oblique', 9)
        canvas.setFillColor(colors.HexColor('#0000FF')) # Color azul

        text_object = canvas.beginText()
        text_object.setTextOrigin(inch, 0.75 * inch)
        text_object.setLeading(12)
        text_object.textLine("Tel. (646) 176-5422 Cel. (646) 171-6178")
        text_object.textLine("vpineda138@hotmail.com pinedamedic@gmail.com www.pinedaintegralmedic.com")
        text_object.textLine("www.pinedamedic.com Pineda Integralmedic")
        canvas.drawText(text_object)
        
        canvas.restoreState()
    
    # 3. Construimos el PDF. Platypus hace toda la magia de la paginación.
    doc.build(story, onFirstPage=pie_de_pagina, onLaterPages=pie_de_pagina)
    
    # --- Devolver la respuesta ---
    buffer.seek(0)
    return buffer

@login_required
@group_required('Pacientes')
def generar_pdf_plan(request, plan_id):
    plan = get_object_or_404(PlanNutricional, id=plan_id)    
    buffer = generar_pdf(plan_id)
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
