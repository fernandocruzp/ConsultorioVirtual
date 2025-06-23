#!/usr/bin/env python
"""
Script para crear el usuario doctor automáticamente.
Este script se ejecutará solo la primera vez que se inicie la aplicación.
"""

import os
import sys
import django

# Configurar el entorno de Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'consultorio_backend.settings')
django.setup()

from django.contrib.auth.models import User
from django.db.utils import IntegrityError

# Ruta al archivo de bandera que indica si el usuario doctor ya ha sido creado
FLAG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.doctor_created')

def create_doctor_user():
    """Crear el usuario doctor si no existe y crear el archivo de bandera."""
    # Verificar si el archivo de bandera existe
    if os.path.exists(FLAG_FILE):
        print("El usuario doctor ya ha sido creado anteriormente.")
        return
    
    try:
        # Verificar si el usuario ya existe en la base de datos
        if User.objects.filter(username='DrVicPineda').exists():
            print("El usuario doctor ya existe en la base de datos.")
        else:
            # Crear el usuario doctor
            user = User.objects.create_superuser(
                username='DrVicPineda',
                email='doctor@consultoriovirtual.com',
                password='password'
            )
            print(f"Usuario doctor creado exitosamente: {user.username}")
        
        # Crear el archivo de bandera para indicar que el usuario ha sido creado
        with open(FLAG_FILE, 'w') as f:
            f.write('El usuario doctor ha sido creado.')
        
        print("Archivo de bandera creado.")
    
    except IntegrityError:
        print("Error: El usuario ya existe.")
    except Exception as e:
        print(f"Error al crear el usuario doctor: {e}")

if __name__ == "__main__":
    create_doctor_user()
