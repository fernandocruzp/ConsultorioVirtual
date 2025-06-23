# Consultorio Virtual

Aplicación de escritorio para la gestión de un consultorio nutricional, desarrollada con Django y Electron.

## Características

- Gestión de pacientes
- Registro de consultas y mediciones
- Planes nutricionales personalizados
- Agenda de citas
- Generación de reportes y gráficas
- Envío de documentos por correo electrónico

## Requisitos

- Python 3.8+
- Node.js 14+
- npm o yarn

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

3. Instalar dependencias de Electron:
```
cd electron_frontend
npm install
```

4. Iniciar la aplicación:
```
npm start
```

## Estructura del proyecto

- `consultorio_backend/`: Backend Django
  - `pacientes/`: App para gestión de pacientes
  - `consultas/`: App para registro de consultas
  - `agenda/`: App para gestión de citas
- `electron_frontend/`: Frontend Electron
  - `main.js`: Punto de entrada de Electron
  - `src/`: Código fuente del frontend

## Desarrollo

Para ejecutar el servidor Django en modo desarrollo:
```
cd consultorio_backend
python manage.py runserver
```

Para ejecutar la aplicación Electron:
```
cd electron_frontend
npm start
```
