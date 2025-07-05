# Consultorio Virtual

Aplicación web para la gestión de un consultorio nutricional, desarrollada con Django.

## Características

- Gestión de pacientes
- Registro de consultas y mediciones
- Planes nutricionales personalizados
- Agenda de citas
- Generación de reportes y gráficas
- Envío de documentos por correo electrónico

## Requisitos

- Python 3.8+

## Instalación

1. Clonar el repositorio:
```
git clone <url-del-repositorio>
cd ConsultorioVirtual
```

2. Configurar el entorno virtual de Python:
```
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. Iniciar la aplicación:
```
cd consultorio_backend
python manage.py runserver
```

## Estructura del proyecto

- `consultorio_backend/`: Backend Django
  - `pacientes/`: App para gestión de pacientes
  - `consultas/`: App para registro de consultas
  - `agenda/`: App para gestión de citas
- `templates/`: Plantillas HTML
- `static/`: Archivos estáticos (CSS, JS, imágenes)

## Desarrollo

Para ejecutar el servidor Django en modo desarrollo:
```
cd consultorio_backend
python manage.py runserver
```

La aplicación estará disponible en http://127.0.0.1:8000/
