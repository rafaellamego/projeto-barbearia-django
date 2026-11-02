from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('agenda', '0009_unifica_status'),
    ]

    operations = [
        # Torna usuario nullable (permite clientes avulsos sem cadastro)
        migrations.AlterField(
            model_name='agendamento',
            name='usuario',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to='agenda.usuario',
            ),
        ),
        # Adiciona campo para nome do cliente avulso (sem cadastro no sistema)
        migrations.AddField(
            model_name='agendamento',
            name='nome_avulso',
            field=models.CharField(blank=True, max_length=150, null=True),
        ),
    ]
