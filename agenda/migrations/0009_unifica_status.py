# Unifica os nomes de status no singular e converte registros antigos.
from django.db import migrations, models


def unificar(apps, schema_editor):
    Agendamento = apps.get_model('agenda', 'Agendamento')
    Agendamento.objects.filter(status='pendentes').update(status='pendente')
    Agendamento.objects.filter(status='concluidos').update(status='concluido')


class Migration(migrations.Migration):

    dependencies = [
        ('agenda', '0008_alter_agendamento_status'),
    ]

    operations = [
        migrations.AlterField(
            model_name='agendamento',
            name='status',
            field=models.CharField(choices=[('pendente', 'Pendente'), ('confirmado', 'Confirmado'), ('execucao', 'Em Execução'), ('concluido', 'Concluído'), ('cancelado', 'Cancelado')], default='pendente', max_length=20),
        ),
        migrations.RunPython(unificar, migrations.RunPython.noop),
    ]
