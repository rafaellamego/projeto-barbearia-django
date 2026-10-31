import datetime
import json

from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from .models import Agendamento, Barbeiro, EscalaBarbeiro, Servico, Usuario


# ---------------------------------------------------------------------------
# Helpers compartilhados entre os testes
# ---------------------------------------------------------------------------

def proxima_data_util():
    """Retorna amanhã ou o próximo dia que não seja domingo (folga padrão)."""
    data = timezone.localdate() + datetime.timedelta(days=1)
    while data.weekday() == 6:
        data += datetime.timedelta(days=1)
    return data


@override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage')
class BaseTestCase(TestCase):
    """Cria os objetos básicos reutilizados por todos os testes."""

    def setUp(self):
        self.cliente = Usuario.objects.create(
            nome='Cliente Teste',
            telefone='11987654321',
            data_nascimento=datetime.date(1990, 6, 15),
            senha='senha123',
        )
        self.barbeiro = Barbeiro.objects.create(
            nome='Barbeiro Teste',
            telefone='11912345678',
            senha='senha123',
        )
        self.servico_30min = Servico.objects.create(
            nome='Corte',
            descricao='Corte simples',
            duracao_minutos=30,
            valor='30.00',
        )
        self.servico_20min = Servico.objects.create(
            nome='Barba',
            descricao='Barba completa',
            duracao_minutos=20,
            valor='20.00',
        )
        self.servico_50min = Servico.objects.create(
            nome='Corte e Barba',
            descricao='Combo',
            duracao_minutos=50,
            valor='45.00',
        )

    # -- Atalhos de sessão --

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

    def cria_escala(self, barbeiro=None, data=None, ativo=True,
                    inicio='08:00', fim='18:00'):
        """Cria uma EscalaBarbeiro para o dia da semana de `data`."""
        if barbeiro is None:
            barbeiro = self.barbeiro
        if data is None:
            data = proxima_data_util()
        return EscalaBarbeiro.objects.create(
            barbeiro=barbeiro,
            dia_semana=data.weekday(),
            horario_inicio=inicio,
            horario_fim=fim,
            ativo=ativo,
        )


# ===========================================================================
# 1. get_barbeiros_disponiveis
# ===========================================================================

class GetBarbeirosDisponiveisTests(BaseTestCase):

    def test_retorna_barbeiros_ativos_na_data(self):
        """Barbeiro com escala ativa deve aparecer na resposta."""
        data = proxima_data_util()
        self.cria_escala(ativo=True, data=data)
        self.login_cliente()

        response = self.client.get(
            reverse('get_barbeiros'), {'data': data.isoformat()}
        )

        self.assertEqual(response.status_code, 200)
        ids = [b['id'] for b in response.json()['barbeiros']]
        self.assertIn(self.barbeiro.id, ids)

    def test_nao_retorna_barbeiros_de_folga(self):
        """Barbeiro com escala marcada como folga não deve aparecer."""
        data = proxima_data_util()
        folguista = Barbeiro.objects.create(
            nome='Folguista', telefone='11900000001', senha='senha123'
        )
        self.cria_escala(barbeiro=self.barbeiro, data=data, ativo=True)
        self.cria_escala(barbeiro=folguista, data=data, ativo=False)
        self.login_cliente()

        response = self.client.get(
            reverse('get_barbeiros'), {'data': data.isoformat()}
        )

        ids = [b['id'] for b in response.json()['barbeiros']]
        self.assertIn(self.barbeiro.id, ids)
        self.assertNotIn(folguista.id, ids)

    def test_sem_escala_retorna_barbeiro_em_dia_util(self):
        """Sem escala cadastrada, o barbeiro aparece de segunda a sábado."""
        data = proxima_data_util()  # nunca domingo por definição do helper
        self.login_cliente()

        response = self.client.get(
            reverse('get_barbeiros'), {'data': data.isoformat()}
        )

        ids = [b['id'] for b in response.json()['barbeiros']]
        self.assertIn(self.barbeiro.id, ids)

    def test_sem_escala_nao_retorna_barbeiro_no_domingo(self):
        """Sem escala, o padrão é folga no domingo."""
        # Encontra o próximo domingo
        data = timezone.localdate() + datetime.timedelta(days=1)
        while data.weekday() != 6:
            data += datetime.timedelta(days=1)
        self.login_cliente()

        response = self.client.get(
            reverse('get_barbeiros'), {'data': data.isoformat()}
        )

        ids = [b['id'] for b in response.json()['barbeiros']]
        self.assertNotIn(self.barbeiro.id, ids)

    def test_exige_sessao_ativa(self):
        """Sem login, deve retornar 401."""
        data = proxima_data_util()

        response = self.client.get(
            reverse('get_barbeiros'), {'data': data.isoformat()}
        )

        self.assertEqual(response.status_code, 401)

    def test_data_invalida_retorna_400(self):
        """Data com formato errado deve retornar 400."""
        self.login_cliente()

        response = self.client.get(
            reverse('get_barbeiros'), {'data': 'nao-e-data'}
        )

        self.assertEqual(response.status_code, 400)


# ===========================================================================
# 2. get_horarios_disponiveis — slots dinâmicos por serviço
# ===========================================================================

class GetHorariosDisponiveisTests(BaseTestCase):

    def test_slots_de_30_minutos_para_servico_de_30min(self):
        """Com serviço de 30 min, os slots devem ser a cada 30 min."""
        data = proxima_data_util()
        self.cria_escala(data=data, inicio='08:00', fim='10:00')
        self.login_cliente()

        response = self.client.get(reverse('get_horarios'), {
            'barbeiro_id': self.barbeiro.id,
            'data': data.isoformat(),
            'servico_id': self.servico_30min.id,
        })

        horarios = response.json()['horarios']
        self.assertIn('08:00', horarios)
        self.assertIn('08:30', horarios)
        self.assertIn('09:00', horarios)
        # 08:20 não deve existir (intervalo é 30 min)
        self.assertNotIn('08:20', horarios)

    def test_slots_de_20_minutos_para_servico_de_20min(self):
        """Com serviço de 20 min, os slots devem ser a cada 20 min."""
        data = proxima_data_util()
        self.cria_escala(data=data, inicio='08:00', fim='09:00')
        self.login_cliente()

        response = self.client.get(reverse('get_horarios'), {
            'barbeiro_id': self.barbeiro.id,
            'data': data.isoformat(),
            'servico_id': self.servico_20min.id,
        })

        horarios = response.json()['horarios']
        self.assertIn('08:00', horarios)
        self.assertIn('08:20', horarios)
        self.assertIn('08:40', horarios)
        self.assertNotIn('08:30', horarios)

    def test_slots_de_50_minutos_para_servico_de_50min(self):
        """Com serviço de 50 min, os slots devem ser a cada 50 min."""
        data = proxima_data_util()
        self.cria_escala(data=data, inicio='08:00', fim='10:00')
        self.login_cliente()

        response = self.client.get(reverse('get_horarios'), {
            'barbeiro_id': self.barbeiro.id,
            'data': data.isoformat(),
            'servico_id': self.servico_50min.id,
        })

        horarios = response.json()['horarios']
        self.assertIn('08:00', horarios)
        self.assertIn('08:50', horarios)
        self.assertNotIn('08:30', horarios)

    def test_slots_padrao_de_30min_sem_servico_id(self):
        """Sem servico_id, o intervalo padrão deve ser 30 minutos."""
        data = proxima_data_util()
        self.cria_escala(data=data, inicio='08:00', fim='09:00')
        self.login_cliente()

        response = self.client.get(reverse('get_horarios'), {
            'barbeiro_id': self.barbeiro.id,
            'data': data.isoformat(),
        })

        horarios = response.json()['horarios']
        self.assertIn('08:00', horarios)
        self.assertIn('08:30', horarios)
        self.assertNotIn('08:20', horarios)

    def test_horario_reservado_nao_aparece(self):
        """Slot já agendado não deve ser listado."""
        data = proxima_data_util()
        self.cria_escala(data=data, inicio='08:00', fim='10:00')
        Agendamento.objects.create(
            usuario=self.cliente,
            barbeiro=self.barbeiro,
            servico=self.servico_30min,
            data=data,
            hora=datetime.time(8, 0),
        )
        self.login_cliente()

        response = self.client.get(reverse('get_horarios'), {
            'barbeiro_id': self.barbeiro.id,
            'data': data.isoformat(),
            'servico_id': self.servico_30min.id,
        })

        self.assertNotIn('08:00', response.json()['horarios'])

    def test_folga_retorna_lista_vazia_e_flag_folga(self):
        """Dia de folga deve retornar horarios=[] e folga=True."""
        data = proxima_data_util()
        self.cria_escala(data=data, ativo=False)
        self.login_cliente()

        response = self.client.get(reverse('get_horarios'), {
            'barbeiro_id': self.barbeiro.id,
            'data': data.isoformat(),
        })

        body = response.json()
        self.assertEqual(body['horarios'], [])
        self.assertTrue(body['folga'])

    def test_exige_barbeiro_e_data(self):
        """Sem barbeiro_id ou data, deve retornar 400."""
        self.login_cliente()

        response = self.client.get(reverse('get_horarios'), {'data': proxima_data_util().isoformat()})
        self.assertEqual(response.status_code, 400)

        response = self.client.get(reverse('get_horarios'), {'barbeiro_id': self.barbeiro.id})
        self.assertEqual(response.status_code, 400)


# ===========================================================================
# 3. salvar_agendamento — fluxo do cliente
# ===========================================================================

class SalvarAgendamentoTests(BaseTestCase):

    def test_agendamento_criado_com_sucesso(self):
        """POST com dados válidos deve criar o agendamento e redirecionar."""
        data = proxima_data_util()
        self.cria_escala(data=data, inicio='08:00', fim='18:00')
        self.login_cliente()

        response = self.client.post(reverse('salvar_agendamento'), {
            'servico_id': self.servico_30min.id,
            'barbeiro_id': self.barbeiro.id,
            'data': data.isoformat(),
            'horario': '10:00',
        })

        self.assertRedirects(response, reverse('meus_agendamentos'))
        self.assertEqual(Agendamento.objects.count(), 1)
        ag = Agendamento.objects.first()
        self.assertEqual(ag.usuario, self.cliente)
        self.assertEqual(ag.barbeiro, self.barbeiro)
        self.assertEqual(ag.servico, self.servico_30min)
        self.assertEqual(ag.status, 'pendente')

    def test_horario_duplicado_nao_cria_segundo_agendamento(self):
        """Tentar agendar no mesmo barbeiro/data/hora já ocupado deve falhar."""
        data = proxima_data_util()
        self.cria_escala(data=data, inicio='08:00', fim='18:00')
        # Primeiro agendamento (de outro cliente)
        outro_cliente = Usuario.objects.create(
            nome='Outro Cliente',
            telefone='11900000099',
            data_nascimento=datetime.date(1992, 3, 10),
            senha='senha123',
        )
        Agendamento.objects.create(
            usuario=outro_cliente,
            barbeiro=self.barbeiro,
            servico=self.servico_30min,
            data=data,
            hora=datetime.time(10, 0),
        )
        self.login_cliente()

        response = self.client.post(reverse('salvar_agendamento'), {
            'servico_id': self.servico_30min.id,
            'barbeiro_id': self.barbeiro.id,
            'data': data.isoformat(),
            'horario': '10:00',
        })

        # Deve redirecionar de volta com mensagem de erro, sem criar novo agendamento
        self.assertRedirects(response, reverse('agendamento'))
        self.assertEqual(Agendamento.objects.count(), 1)

    def test_barbeiro_de_folga_nao_aceita_agendamento(self):
        """Agendamento com barbeiro em folga deve ser recusado."""
        data = proxima_data_util()
        self.cria_escala(data=data, ativo=False)
        self.login_cliente()

        response = self.client.post(reverse('salvar_agendamento'), {
            'servico_id': self.servico_30min.id,
            'barbeiro_id': self.barbeiro.id,
            'data': data.isoformat(),
            'horario': '10:00',
        })

        self.assertRedirects(response, reverse('agendamento'))
        self.assertEqual(Agendamento.objects.count(), 0)

    def test_sem_sessao_redireciona_para_login(self):
        """Sem login, deve redirecionar para a tela de login."""
        data = proxima_data_util()

        response = self.client.post(reverse('salvar_agendamento'), {
            'servico_id': self.servico_30min.id,
            'barbeiro_id': self.barbeiro.id,
            'data': data.isoformat(),
            'horario': '10:00',
        })

        self.assertRedirects(response, reverse('login'))
        self.assertEqual(Agendamento.objects.count(), 0)

    def test_barbeiro_invalido_redireciona_com_erro(self):
        """barbeiro_id inexistente deve redirecionar para agendamento."""
        self.login_cliente()
        data = proxima_data_util()

        response = self.client.post(reverse('salvar_agendamento'), {
            'servico_id': self.servico_30min.id,
            'barbeiro_id': 99999,
            'data': data.isoformat(),
            'horario': '10:00',
        })

        self.assertRedirects(response, reverse('agendamento'))
        self.assertEqual(Agendamento.objects.count(), 0)


# ===========================================================================
# 4. cancelar_agendamento
# ===========================================================================

class CancelarAgendamentoTests(BaseTestCase):

    def cria_agendamento(self, usuario=None, barbeiro=None, servico=None):
        """Cria um agendamento simples para usar nos testes."""
        data = proxima_data_util()
        return Agendamento.objects.create(
            usuario=usuario or self.cliente,
            barbeiro=barbeiro or self.barbeiro,
            servico=servico or self.servico_30min,
            data=data,
            hora=datetime.time(10, 0),
        )

    def test_cliente_cancela_proprio_agendamento(self):
        """Cliente logado deve conseguir cancelar seu próprio agendamento."""
        ag = self.cria_agendamento()
        self.login_cliente()

        response = self.client.get(
            reverse('cancelar_agendamento', args=[ag.id])
        )

        self.assertRedirects(response, reverse('meus_agendamentos'))
        self.assertFalse(Agendamento.objects.filter(id=ag.id).exists())

    def test_cliente_nao_cancela_agendamento_de_outro(self):
        """Cliente não pode cancelar o agendamento de outro cliente (deve 404)."""
        outro_cliente = Usuario.objects.create(
            nome='Outro',
            telefone='11900000002',
            data_nascimento=datetime.date(1985, 1, 1),
            senha='senha123',
        )
        ag = self.cria_agendamento(usuario=outro_cliente)
        self.login_cliente()

        response = self.client.get(
            reverse('cancelar_agendamento', args=[ag.id])
        )

        self.assertEqual(response.status_code, 404)
        self.assertTrue(Agendamento.objects.filter(id=ag.id).exists())

    def test_sem_sessao_redireciona_para_login(self):
        """Sem login, deve redirecionar para login."""
        ag = self.cria_agendamento()

        response = self.client.get(
            reverse('cancelar_agendamento', args=[ag.id])
        )

        self.assertRedirects(response, reverse('login'))
        self.assertTrue(Agendamento.objects.filter(id=ag.id).exists())

    def test_agendamento_inexistente_retorna_404(self):
        """ID que não existe deve retornar 404."""
        self.login_cliente()

        response = self.client.get(
            reverse('cancelar_agendamento', args=[99999])
        )

        self.assertEqual(response.status_code, 404)


# ===========================================================================
# 5. Tela de agendamento — HTML e listagem de serviços
# ===========================================================================

class TelaAgendamentoTests(BaseTestCase):

    def test_tela_exige_login(self):
        """Sem sessão, deve redirecionar para login."""
        response = self.client.get(reverse('agendamento'))
        self.assertRedirects(response, reverse('login'))

    def test_tela_carrega_com_status_200(self):
        """Com sessão ativa, deve retornar HTTP 200."""
        self.login_cliente()
        response = self.client.get(reverse('agendamento'))
        self.assertEqual(response.status_code, 200)

    def test_tela_lista_todos_os_servicos_com_nome_e_preco(self):
        """Todos os serviços cadastrados devem aparecer na tela com nome e valor."""
        self.login_cliente()

        response = self.client.get(reverse('agendamento'))

        self.assertContains(response, 'Corte')
        self.assertContains(response, 'Barba')
        self.assertContains(response, 'Corte e Barba')
        # Django com locale pt-br formata decimais com vírgula: 30,00 / 20,00 / 45,00
        self.assertContains(response, '30,00')
        self.assertContains(response, '20,00')
        self.assertContains(response, '45,00')

    def test_tela_tem_campo_servico_id_no_formulario(self):
        """O select de serviço deve ter name='servico_id'."""
        self.login_cliente()

        response = self.client.get(reverse('agendamento'))

        self.assertContains(response, 'name="servico_id"')

    def test_tela_tem_campo_barbeiro_id_no_formulario(self):
        """O select de barbeiro deve ter name='barbeiro_id'."""
        self.login_cliente()

        response = self.client.get(reverse('agendamento'))

        self.assertContains(response, 'name="barbeiro_id"')

    def test_tela_tem_campo_data_no_formulario(self):
        """O input de data deve ter name='data'."""
        self.login_cliente()

        response = self.client.get(reverse('agendamento'))

        self.assertContains(response, 'name="data"')

    def test_tela_tem_campo_oculto_para_horario(self):
        """O campo hidden de horário selecionado deve estar presente."""
        self.login_cliente()

        response = self.client.get(reverse('agendamento'))

        self.assertContains(response, 'name="horario"')

    def test_tela_sem_servicos_nao_quebra(self):
        """Sem serviços cadastrados, a tela deve carregar normalmente."""
        Servico.objects.all().delete()
        self.login_cliente()

        response = self.client.get(reverse('agendamento'))

        self.assertEqual(response.status_code, 200)
