from django.shortcuts import render

# Create your views here.

def inicio_portal(request):
    return render(request, 'portal/login.html')
