# Generated by Django 5.2 on 2025-06-25 04:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("consultas", "0002_consulta_circunferencia_cadera_and_more"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="plannutricional",
            name="contenido",
        ),
        migrations.AddField(
            model_name="plannutricional",
            name="contenido_cena",
            field=models.TextField(default=""),
        ),
        migrations.AddField(
            model_name="plannutricional",
            name="contenido_colacion",
            field=models.TextField(default=""),
        ),
        migrations.AddField(
            model_name="plannutricional",
            name="contenido_comida",
            field=models.TextField(default=""),
        ),
        migrations.AddField(
            model_name="plannutricional",
            name="contenido_desayuno",
            field=models.TextField(default=""),
        ),
    ]
