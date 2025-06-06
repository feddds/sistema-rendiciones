# Generated by Django 5.2 on 2025-04-23 12:40

import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0007_rendicion_beneficiario_real_rendicion_es_titular'),
    ]

    operations = [
        migrations.RenameField(
            model_name='rendicion',
            old_name='es_titular',
            new_name='cerrada',
        ),
        migrations.RemoveField(
            model_name='rendicion',
            name='beneficiario_real',
        ),
        migrations.RemoveField(
            model_name='rendicion',
            name='egresos',
        ),
        migrations.RemoveField(
            model_name='rendicion',
            name='fecha',
        ),
        migrations.RemoveField(
            model_name='rendicion',
            name='ingresos',
        ),
        migrations.RemoveField(
            model_name='rendicion',
            name='tipo_servicio',
        ),
        migrations.AddField(
            model_name='rendicion',
            name='fecha_cierre',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='rendicion',
            name='fecha_creacion',
            field=models.DateField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.CreateModel(
            name='Viaje',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tipo_servicio', models.CharField(choices=[('UBER', 'Uber'), ('CABIFY', 'Cabify'), ('EXTRA', 'Extra')], max_length=10)),
                ('ingresos', models.DecimalField(decimal_places=2, max_digits=10)),
                ('egresos', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('es_titular', models.BooleanField(default=False)),
                ('beneficiario_real', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='core.chofer')),
                ('rendicion', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='viajes', to='core.rendicion')),
            ],
        ),
    ]
