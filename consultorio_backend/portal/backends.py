from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.models import User, Group
from pacientes.models import Paciente
import uuid

class LlaveUnicaBackend(BaseBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        llave_ingresada = password 

        try:
            uuid.UUID(llave_ingresada, version=4)
            paciente = Paciente.objects.get(llave_unica=llave_ingresada)
        except (ValueError, Paciente.DoesNotExist):
            return None

        if paciente.usuario:
            return paciente.usuario
        else:
            username = f"paciente_{paciente.id}"
            if User.objects.filter(username=username).exists():
                pass
            user = User.objects.create_user(username=username, password=llave_ingresada)
            try:
                grupo_pacientes = Group.objects.get(name='Pacientes')
                user.groups.add(grupo_pacientes)
            except Group.DoesNotExist:
                pass
            
            paciente.usuario = user
            paciente.save()
            return user

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
