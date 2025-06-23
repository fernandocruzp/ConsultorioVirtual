from django import forms
from django.contrib.auth import get_user_model

User = get_user_model()

class UserEmailChangeForm(forms.ModelForm):
    """
    Un ModelForm para que un usuario cambie su propia dirección de correo.
    """
    class Meta:
        model = User
        fields = ['email']

    def clean_email(self):
        """
        Añadimos una validación personalizada para el campo 'email'.
        """
        new_email = self.cleaned_data.get('email')
        if User.objects.filter(email__iexact=new_email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("Esta dirección de correo electrónico ya está registrada por otro usuario.")
        return new_email
