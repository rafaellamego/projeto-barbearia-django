import datetime

from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from .models import Agendamento, Barbeiro, EscalaBarbeiro, Servico, Usuario


@override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage')
class AgendamentoFlowTests(TestCase):
    def setUp(self):
        self.cliente = Usuario.objects.create(
            nome='Cliente de Teste',
            telefone='11987654321',
            data_nascimento=datetime.date(1990, 1, 1),
            senha='test-password',
        )
        self.barbeiro = Barbeiro.objects.create(
            nome='Barbeiro de Teste',
            telefone='11912345678',
            senha='test-password',
        )
        self.servico = Servico.objects.create(
            nome='Corte',
            descricao='',
            duracao_minutos=30,
            valor='35.00',
        )

    def data_futura(self):
        data = timezone.localdate() + datetime.timedelta(days=1)
        while data.weekday() == 6:
            data += datetime.timedelta(days=1)
        return data

    def login_cliente(self):
        session = self.client.session
        session['usuario_id'] = self.cliente.id
        session['tipo_usuario'] = 'cliente'
        session.save()

    def login_barbeiro(self):
        session = self.client.session
        session['barbeiro_id'] = self.barbeiro.id
        session['tipo_usuario'] = 'barbeiro'
        session.save()

    def test_filtro_retorna_apenas_barbeiros_que_trabalham_na_data(self):
        data = self.data_futura()
        folguista = Barbeiro.objects.create(
            nome='Barbeiro de Folga', telefone='11911112222', senha='test-password'
        )
        EscalaBarbeiro.objects.create(
            barbeiro=self.barbeiro,
            dia_semana=data.weekday(),
            horario_inicio='09:00',
            horario_fim='18:00',
            ativo=True,
        )
        EscalaBarbeiro.objects.create(
            barbeiro=folguista,
            dia_semana=data.weekday(),
            horario_inicio='09:00',
            horario_fim='18:00',
            ativo=False,
        )
        self.login_cliente()

        response = self.client.get(reverse('get_barbeiros'), {'data': data.isoformat()})

        self.assertEqual(response.status_code, 200)
        ids = {item['id'] for item in response.json()['barbeiros']}
        self.assertIn(self.barbeiro.id, ids)
        self.assertNotIn(folguista.id, ids)

    def test_filtro_usa_padrao_de_segunda_a_sabado_quando_nao_ha_escala(self):
        self.login_cliente()
        data = self.data_futura()

        response = self.client.get(reverse('get_barbeiros'), {'data': data.isoformat()})

        self.assertEqual(response.status_code, 200)
        ids = {item['id'] for item in response.json()['barbeiros']}
        self.assertIn(self.barbeiro.id, ids)

    def test_cliente_nao_consulta_horarios_sem_autenticacao(self):
        response = self.client.get(reverse('get_horarios'), {'barbeiro_id': self.barbeiro.id, 'data': self.data_futura()})
        self.assertEqual(response.status_code, 401)

    def test_agendamento_publico_recusa_barbeiro_de_folga(self):
        data = self.data_futura()
        EscalaBarbeiro.objects.create(
            barbeiro=self.barbeiro,
            dia_semana=data.weekday(),
            horario_inicio='09:00',
            horario_fim='18:00',
            ativo=False,
        )
        self.login_cliente()

        response = self.client.post(reverse('salvar_agendamento'), {
            'servico_id': self.servico.id,
            'barbeiro_id': self.barbeiro.id,
            'data': data.isoformat(),
            'horario': '10:00',
        })

        self.assertRedirects(response, reverse('agendamento'))
        self.assertEqual(Agendamento.objects.count(), 0)

    @override_settings(MANUAL_CLIENT_DEFAULT_PASSWORD='temporary-test-password')
    def test_barbeiro_agenda_cliente_novo_com_status_pendente(self):
        data = self.data_futura()
        EscalaBarbeiro.objects.create(
            barbeiro=self.barbeiro,
            dia_semana=data.weekday(),
            horario_inicio='09:00',
            horario_fim='18:00',
            ativo=True,
        )
        self.login_barbeiro()

        response = self.client.post(reverse('agendamento_manual'), {
            'tipo_cliente': 'novo',
            'nome': 'Pessoa Nova',
            'telefone': '11999998888',
            'data_nascimento': '1995-04-12',
            'servico_id': self.servico.id,
            'data': data.isoformat(),
            'horario': '10:00',
        })

        self.assertRedirects(response, reverse('home_barbeiro'))
        novo_cliente = Usuario.objects.get(telefone='11999998888')
        agendamento = Agendamento.objects.get(usuario=novo_cliente)
        self.assertEqual(novo_cliente.senha, 'temporary-test-password')
        self.assertEqual(agendamento.barbeiro, self.barbeiro)
        self.assertEqual(agendamento.status, 'pendente')

    def test_barbeiro_agenda_cliente_existente(self):
        data = self.data_futura()
        self.login_barbeiro()

        response = self.client.post(reverse('agendamento_manual'), {
            'tipo_cliente': 'existente',
            'usuario_id': self.cliente.id,
            'servico_id': self.servico.id,
            'data': data.isoformat(),
            'horario': '10:00',
        })

        self.assertRedirects(response, reverse('home_barbeiro'))
        agendamento = Agendamento.objects.get(usuario=self.cliente)
        self.assertEqual(agendamento.barbeiro, self.barbeiro)
        self.assertEqual(agendamento.status, 'pendente')

    @override_settings(MANUAL_CLIENT_DEFAULT_PASSWORD='')
    def test_cadastro_manual_de_cliente_novo_requer_configuracao_local_da_senha(self):
        data = self.data_futura()
        self.login_barbeiro()

        response = self.client.post(reverse('agendamento_manual'), {
            'tipo_cliente': 'novo',
            'nome': 'Pessoa Nova',
            'telefone': '11999998888',
            'data_nascimento': '1995-04-12',
            'servico_id': self.servico.id,
            'data': data.isoformat(),
            'horario': '10:00',
        })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Usuario.objects.count(), 1)
        self.assertEqual(Agendamento.objects.count(), 0)

    def test_tela_de_agendamento_tem_etapas_e_rotulos_associados(self):
        self.login_cliente()

        response = self.client.get(reverse('agendamento'))

        self.assertContains(response, 'Etapa 1 — escolha o serviço')
        self.assertContains(response, 'Etapa 2 — escolha o barbeiro')
        self.assertContains(response, 'Etapa 3 — escolha o dia')
        self.assertContains(response, 'Etapa 4 — escolha o horário')
        self.assertContains(response, 'aria-label="Controles de tamanho do texto"')
        self.assertContains(response, 'for="servico"')
