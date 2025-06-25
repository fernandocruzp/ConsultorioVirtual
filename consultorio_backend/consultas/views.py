from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.core.paginator import Paginator
from django.http import HttpResponse
from .models import Consulta, PlanNutricional, Receta
from .forms import ConsultaForm, PlanNutricionalForm, RecetaForm
from pacientes.models import Paciente
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
import json
import os
from portal.decorators import group_required

@login_required
@group_required('Medicos')
def lista_consultas(request):
    query = request.GET.get('q', '')
    if query:
        consultas_list = Consulta.objects.filter(
            Q(paciente__nombre__icontains=query) | 
            Q(paciente__apellidos__icontains=query)
        ).select_related('paciente', 'plan').order_by('-fecha')
    else:
        consultas_list = Consulta.objects.all().select_related('paciente', 'plan').order_by('-fecha')
    
    paginator = Paginator(consultas_list, 10)  # 10 consultas por página
    page = request.GET.get('page')
    consultas = paginator.get_page(page)
    
    return render(request, 'consultas/lista_consultas.html', {
        'consultas': consultas,
        'is_paginated': consultas.has_other_pages(),
        'page_obj': consultas,
    })

@login_required
@group_required('Medicos')
def detalle_consulta(request, consulta_id):
    consulta = get_object_or_404(Consulta, id=consulta_id)
    
    # Obtener historial de consultas del paciente
    historial_consultas = Consulta.objects.filter(
        paciente=consulta.paciente
    ).exclude(id=consulta_id).order_by('-fecha')
    
    return render(request, 'consultas/detalle_consulta.html', {
        'consulta': consulta,
        'historial_consultas': historial_consultas,
    })

@login_required
@group_required('Medicos')
def historial_completo(request, consulta_id):
    consulta = get_object_or_404(Consulta, id=consulta_id)
    
    # Obtener historial de consultas del paciente
    historial_consultas = Consulta.objects.filter(
        paciente=consulta.paciente
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
    return render(request, 'consultas/historial_completo.html', {
        'consulta': consulta,
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
def nueva_consulta(request, paciente_id=None):
    print(paciente_id)
    paciente = None
    if paciente_id:
        paciente = get_object_or_404(Paciente, id=paciente_id)
    
    if request.method == 'POST':
        form = ConsultaForm(request.POST)
        if form.is_valid():
            consulta = form.save(commit=False)
            if paciente:
                consulta.paciente = paciente
            consulta.save()
            messages.success(request, f'Consulta para {consulta.paciente.nombre} {consulta.paciente.apellidos} registrada correctamente.')
            return redirect('detalle_consulta', consulta_id=consulta.id)
    else:
        initial_data = {}
        if paciente:
            initial_data['paciente'] = paciente
            # Obtener la última consulta para pre-llenar la altura
            ultima_consulta = Consulta.objects.filter(paciente=paciente).order_by('-fecha').first()
            if ultima_consulta:
                initial_data['altura'] = ultima_consulta.altura
        
        form = ConsultaForm(initial=initial_data)
        
        # Si hay un paciente seleccionado, no mostrar el campo de selección de paciente
        #if paciente:
         #   form.fields['paciente'].widget = form.fields['paciente'].hidden_widget()
    
    return render(request, 'consultas/form_consulta.html', {
        'form': form,
        'paciente': paciente,
    })

@login_required
@group_required('Medicos')
def detalle_plan(request, plan_id):
    plan = get_object_or_404(PlanNutricional, id=plan_id)
    return render(request, 'consultas/plan_nutricional.html', {
        'plan': plan,
    })

@login_required
@group_required('Medicos')
def nuevo_plan(request, consulta_id):
    consulta = get_object_or_404(Consulta, id=consulta_id)
    
    # Verificar si ya existe un plan para esta consulta
    if hasattr(consulta, 'plan'):
        messages.warning(request, 'Esta consulta ya tiene un plan nutricional.')
        return redirect('detalle_plan', plan_id=consulta.plan.id)
    
    if request.method == 'POST':
        form = PlanNutricionalForm(request.POST)
        if form.is_valid():
            plan = form.save(commit=False)
            plan.consulta = consulta
            plan.save()
            messages.success(request, f'Plan nutricional para {consulta.paciente.nombre} {consulta.paciente.apellidos} creado correctamente.')
            return redirect('detalle_plan', plan_id=plan.id)
    else:
        form = PlanNutricionalForm()
    
    return render(request, 'consultas/form_plan.html', {
        'form': form,
        'consulta': consulta,
    })

@login_required
@group_required('Medicos')
def editar_plan(request, plan_id):
    plan = get_object_or_404(PlanNutricional, id=plan_id)
    
    if request.method == 'POST':
        form = PlanNutricionalForm(request.POST, instance=plan)
        if form.is_valid():
            form.save()
            messages.success(request, f'Plan nutricional para {plan.consulta.paciente.nombre} {plan.consulta.paciente.apellidos} actualizado correctamente.')
            return redirect('detalle_plan', plan_id=plan.id)
    else:
        form = PlanNutricionalForm(instance=plan)
    
    return render(request, 'consultas/form_plan.html', {
        'form': form,
        'plan': plan,
        'consulta': plan.consulta,
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

    story.append(Spacer(1, 0.5*inch)) 

    style_aclaraciones = styles['BodyText']
    style_aclaraciones.fontSize = 10
    style_aclaraciones.leading = 12

    texto_aclaraciones1 = """
    Debe de comer cada 3-4 hrs. Debe de tomar 2-3 litros de agua. 
    Solo consuma frutos del monje. Consumir poca cantidad de sal o sal vegetal o rosa.
    """
    story.append(Paragraph(texto_aclaraciones1, style_aclaraciones))
    story.append(Spacer(1, 0.1*inch))

    texto_equivalentes_final = "<b>Equivalentes de cereales:</b> 0-2, <b>lácteos:</b> 0, <b>fruta:</b> 1 pza o 1 taza."
    story.append(Paragraph(texto_equivalentes_final, style_aclaraciones))
    story.append(Spacer(1, 0.2*inch))
    texto_advertencia = '<font color="red"><b>NO LÁCTEOS, NO CARNES ROJAS, NO FRIJOLES</b></font>'
    story.append(Paragraph(texto_advertencia, styles['h2']))

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
@group_required('Medicos')
def generar_pdf_plan(request, plan_id):
    plan = get_object_or_404(PlanNutricional, id=plan_id)
    paciente = plan.consulta.paciente
    buffer = generar_pdf(plan_id)
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="Plan_Nutricional_{paciente.apellidos}.pdf"'
    return response

@login_required
@group_required('Medicos')
def enviar_plan_email(request, plan_id):
    user = request.user
    plan = get_object_or_404(PlanNutricional, id=plan_id)
    paciente = plan.consulta.paciente
    buffer= generar_pdf(plan_id)
    email = EmailMessage(
        subject=f'Plan Nutricional - Pineda IntegralMedic',
        body=f'Estimado/a {paciente.nombre},\n\nAdjunto encontrará su plan nutricional personalizado.\n\nSaludos cordiales,\nPineda IntegralMedic',
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[paciente.email],
    )
    email.attach(f'Plan_Nutricional_{paciente.apellidos}.pdf', buffer.getvalue(), 'application/pdf')
    
    try:
        email.send()
        messages.success(request, f'Plan nutricional enviado correctamente a {paciente.email}.')
    except Exception as e:
        messages.error(request, f'Error al enviar el correo: {str(e)}')
    
    return redirect('detalle_plan', plan_id=plan.id)


@login_required
@group_required('Medicos')
def generar_pdf_historial(request, consulta_id):
    consulta = get_object_or_404(Consulta, id=consulta_id)
    
    # Obtener historial de consultas del paciente
    historial_consultas = Consulta.objects.filter(
        paciente=consulta.paciente
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
    p.drawString(2*inch, height - 2.5*inch, f"{consulta.paciente.nombre} {consulta.paciente.apellidos}")
    p.setFont("Helvetica-Bold", 12)
    p.drawString(inch, height - 2.7*inch, "Para más información usa el siguiente enlace:")
    p.setFont("Helvetica", 12)
    p.drawString(inch, height - 2.9*inch, "https://pinedaintegralmedic.onrender.com/portal/")
    p.setFont("Helvetica-Bold", 12)
    p.drawString(inch, height - 3.1*inch, "Llave de acceso:")
    p.drawString(2.5*inch, height - 3.1*inch, f"{consulta.paciente.llave_unica}")
    
    
    # Contenido del historial
    data = [[
        h.fecha.strftime('%d/%m/%Y'),                 
        f"{h.circunferencia_cintura} cm",
        f"{h.circunferencia_cadera} cm",
        f"{h.circunferencia_pecho} cm",
        f"{h.tratamiento}",
        f"{h.tension_arterial}",
        f"{h.peso} kg",               
        f"{h.altura} cm",             
        f"{h.imc:.2f}"
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
    
    # Obtener el valor del buffer y crear la respuesta HTTP
    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="Carnet_{consulta.paciente.apellidos}.pdf"'
    
    return response

@login_required
@group_required('Medicos')
def enviar_historial_email(request, consulta_id):
    consulta = get_object_or_404(Consulta, id=consulta_id)
    
    # Obtener historial de consultas del paciente
    historial_consultas = Consulta.objects.filter(
        paciente=consulta.paciente
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
    p.drawString(2*inch, height - 2.5*inch, f"{consulta.paciente.nombre} {consulta.paciente.apellidos}")
    p.setFont("Helvetica-Bold", 12)
    p.drawString(inch, height - 2.7*inch, "Para más información usa el siguiente enlace:")
    p.setFont("Helvetica", 12)
    p.drawString(inch, height - 2.9*inch, "https://pinedaintegralmedic.onrender.com/portal/")
    p.setFont("Helvetica-Bold", 12)
    p.drawString(inch, height - 3.1*inch, "Llave de acceso:")
    p.drawString(2.5*inch, height - 3.1*inch, f"{consulta.paciente.llave_unica}")
    
    # Contenido del historial
    data = [[
        h.fecha.strftime('%d/%m/%Y'),                 
        f"{h.circunferencia_cintura} cm",
        f"{h.circunferencia_cadera} cm",
        f"{h.circunferencia_pecho} cm",
        f"{h.tratamiento}",
        f"{h.tension_arterial}",
        f"{h.peso} kg",               
        f"{h.altura} cm",             
        f"{h.imc:.2f}"
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
    
    # Obtener el valor del buffer y crear la respuesta HTTP
    buffer.seek(0)
    email = EmailMessage(
        subject=f'Carnet - Pineda IntegralMedic',
        body=f'Estimado/a {consulta.paciente.nombre},\n\nAdjunto encontrará su carnet actualizado.\n\nSaludos cordiales,\nPineda IntegralMedic',
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[consulta.paciente.email],
    )
    email.attach(f'Carnet_{consulta.paciente.apellidos}.pdf', buffer.getvalue(), 'application/pdf')
    
    try:
        email.send()
        messages.success(request, f'Plan nutricional enviado correctamente a {consulta.paciente.email}.')
    except Exception as e:
        messages.error(request, f'Error al enviar el correo: {str(e)}')
    
    return redirect('historial_completo',consulta.id)

# Nuevas vistas para recetas
@login_required
@group_required('Medicos')
def detalle_receta(request, receta_id):
    receta = get_object_or_404(Receta, id=receta_id)
    return render(request, 'consultas/receta.html', {
        'receta': receta,
    })

@login_required
@group_required('Medicos')
def nueva_receta(request, consulta_id):
    consulta = get_object_or_404(Consulta, id=consulta_id)
    
    # Verificar si ya existe una receta para esta consulta
    if hasattr(consulta, 'receta'):
        messages.warning(request, 'Esta consulta ya tiene una receta médica.')
        return redirect('detalle_receta', receta_id=consulta.receta.id)
    
    if request.method == 'POST':
        form = RecetaForm(request.POST)
        if form.is_valid():
            receta = form.save(commit=False)
            receta.consulta = consulta
            receta.save()
            messages.success(request, f'Receta para {consulta.paciente.nombre} {consulta.paciente.apellidos} creada correctamente.')
            return redirect('detalle_receta', receta_id=receta.id)
    else:
        form = RecetaForm()
    
    return render(request, 'consultas/form_receta.html', {
        'form': form,
        'consulta': consulta,
    })

@login_required
@group_required('Medicos')
def editar_receta(request, receta_id):
    receta = get_object_or_404(Receta, id=receta_id)
    
    if request.method == 'POST':
        form = RecetaForm(request.POST, instance=receta)
        if form.is_valid():
            form.save()
            messages.success(request, f'Receta para {receta.consulta.paciente.nombre} {receta.consulta.paciente.apellidos} actualizada correctamente.')
            return redirect('detalle_receta', receta_id=receta.id)
    else:
        form = RecetaForm(instance=receta)
    
    return render(request, 'consultas/form_receta.html', {
        'form': form,
        'receta': receta,
    })

@login_required
@group_required('Medicos')
def generar_pdf_receta(request, receta_id):
    receta = get_object_or_404(Receta, id=receta_id)
    
    buffer = io.BytesIO()

    # NUEVO: Definir tamaño de media página (Half US Letter)
    receta_size = (8.5 * inch, 5.5 * inch)
    p = canvas.Canvas(buffer, pagesize=receta_size)
    width, height = receta_size

    # --- ENCABEZADO ---
    # Cargar la ruta del logo
    logo_path = None
    try:
        logo_filename = "Logo3.png" 
        logo_path_full = os.path.join(settings.STATICFILES_DIRS[0], 'img', logo_filename)
        if os.path.exists(logo_path_full):
            logo_path = logo_path_full
    except (IndexError, AttributeError):
        pass

    # Columna Izquierda: Logo
    if logo_path:
        p.drawImage(logo_path, x=0.5*inch, y=4*inch, width=2*inch, preserveAspectRatio=True)
    # Estilos para los párrafos del encabezado
    styles = getSampleStyleSheet()
    style_center = ParagraphStyle(name='Center', alignment=TA_CENTER, parent=styles['Normal'], fontSize=9, leading=11)
    style_left_small = ParagraphStyle(name='LeftSmall', alignment=TA_LEFT, parent=styles['Normal'], fontSize=9, leading=11)

    # Columna Central: Información del Doctor
    texto_centro_html = """
        <b>DR. VICTOR M. PINEDA RAMIREZ</b><br/>
        Medico Cirujano - Nutrición - Medicina Estética<br/>
        Ced. PROFESIONAL 2026134<br/>
        UNAM
    """
    para_centro = Paragraph(texto_centro_html, style_center)
    # Definimos el área para el párrafo central y lo dibujamos
    para_centro.wrapOn(p, 3 * inch, 1.5 * inch)
    para_centro.drawOn(p, 2.75 * inch, height - 1.2 * inch)


    # Columna Derecha: Contacto
    texto_derecha_html = """
        <b>TEL .</b> 646 176 5422<br/>
        <b>CEL.</b> 646 171 6178<br/>
        vpineda136@hotmail.com<br/>
        pinedamedic@gmail.com
    """
    para_derecha = Paragraph(texto_derecha_html, style_left_small)
    # Definimos el área para el párrafo derecho y lo dibujamos
    para_derecha.wrapOn(p, 2 * inch, 1.5 * inch)
    para_derecha.drawOn(p, 6 * inch, height - 1.2 * inch)


    # Línea separadora después del encabezado
    p.line(0.5 * inch, height - 1.5 * inch, width - 0.5 * inch, height - 1.5 * inch)

    # --- CUERPO ---
    y_position = height - 1.9 * inch # Posición inicial debajo de la línea

    # Información del paciente
    p.setFont("Helvetica-Bold", 11)
    p.drawString(0.5 * inch, y_position, "Paciente:")
    p.setFont("Helvetica", 11)
    p.drawString(1.5 * inch, y_position, f"{receta.consulta.paciente.nombre} {receta.consulta.paciente.apellidos}")
    y_position -= 0.3 * inch
    
    p.setFont("Helvetica-Bold", 11)
    p.drawString(0.5 * inch, y_position, "Fecha:")
    p.setFont("Helvetica", 11)
    p.drawString(1.5 * inch, y_position, receta.fecha_creacion.strftime("%d/%m/%Y"))
    y_position -= 0.6 * inch
     
    # Contenido de la receta (sin título)
    styles = getSampleStyleSheet()
    style_normal = styles['Normal']
    style_normal.leading = 14
    style_normal.fontSize = 11

    contenido_html = receta.medicamentos.replace('\n', '<br/>')
    medicamentos_paragraph = Paragraph(contenido_html, style_normal)

    # Lógica para evitar que el texto invada el pie de página
    footer_margin = 1.0 * inch
    available_height = y_position - footer_margin
    w_para, h_para = medicamentos_paragraph.wrapOn(p, width - inch, available_height)
    medicamentos_paragraph.drawOn(p, 0.5 * inch, y_position - h_para)
     
    # --- PIE DE PÁGINA ---
    # Línea separadora antes del pie de página
    p.line(0.5 * inch, 0.75 * inch, width - 0.5 * inch, 0.75 * inch)
    
    # Texto del pie de página
    p.setFont("Helvetica-Oblique", 9)
    p.drawCentredString(width / 2, 0.5 * inch, "Calle Mina No. 30-1, Fracc Bahía C.P 22880 Ensenada, B.C., México")
     
    # --- FINALIZAR ---
    p.showPage()
    p.save()
    
    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="Receta_{receta.consulta.paciente.apellidos}.pdf"'
    
    return response
