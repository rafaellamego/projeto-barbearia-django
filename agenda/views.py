import datetime
import re
import json
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from .models import Agendamento, Usuario, Barbeiro, Servico, EscalaBarbeiro


from django.utils import timezone
from .models import EscalaBarbeiro
from .forms import EscalaFormSet
# ==================== CADASTRO ====================
def cadastrar(request):
    if request.method == 'POST':
        nome = request.POST.get("nome")
        telefone = re.sub(r'\D', '', request.POST.get("telefone", ""))
        data_nascimento = request.POST.get("data_nascimento")
        senha = request.POST.get("senha")

        if Usuario.objects.filter(telefone=telefone).exists():
            messages.error(request, "Este telefone já está cadastrado!")
            return render(request, 'agenda/cadastrar.html', {'nome': nome})

        if len(telefone) != 11:
            messages.error(request, "Telefone deve ter 11 números (DDD + número)")
            return render(request, 'agenda/cadastrar.html')
        
        elif len(senha) < 4:
            messages.error(request, "Senha muito curta")
            return render(request, 'agenda/cadastrar.html')

        else:
            Usuario.objects.create(
                nome=nome,
                telefone=telefone,
                data_nascimento=data_nascimento,
                senha=senha
            )
            messages.success(request, "Cadastro efetuado com sucesso!")
            return redirect('login')

    return render(request, 'agenda/cadastrar.html')


# ==================== LOGIN ====================
def login_view(request, tipo='cliente'): 
    if request.method == 'POST':
        telefone_limpo = re.sub(r'\D', '', request.POST.get('telefone', ""))
        senha = request.POST.get('senha')

        try:
            if tipo == 'barbeiro':
                # Verifica primeiro o usuário de teste fixo para o barbeiro
                if telefone_limpo == "11922223333" and senha == "ad123":
                    barbeiro = Barbeiro.objects.filter(telefone=telefone_limpo).first()
                    if barbeiro:
                        request.session['barbeiro_id'] = barbeiro.id
                        request.session['tipo_usuario'] = 'barbeiro'
                        return redirect('home_barbeiro')
                
                # Login normal para outros barbeiros
                barbeiro = Barbeiro.objects.get(telefone=telefone_limpo, senha=senha)
                request.session['barbeiro_id'] = barbeiro.id
                request.session['tipo_usuario'] = 'barbeiro'
                return redirect('home_barbeiro')
            
            else:
                # Login para Clientes (Tabela Usuario)
                usuario = Usuario.objects.get(telefone=telefone_limpo, senha=senha)
                request.session['usuario_id'] = usuario.id
                request.session['user_nome'] = usuario.nome
                request.session['tipo_usuario'] = 'cliente'
                return redirect('home_cliente')
                
        except (Usuario.DoesNotExist, Barbeiro.DoesNotExist):
            messages.error(request, "Telefone ou senha inválidos")
            return render(request, 'agenda/login.html', {'tipo': tipo})
    
    return render(request, 'agenda/login.html', {'tipo': tipo})


# ==================== HOME CLIENTE ====================
def home_cliente(request):
    if 'usuario_id' not in request.session:
        return redirect('login')
    
    nome_cliente = request.session.get('user_nome', 'Cliente')
    return render(request, 'agenda/home_cliente.html', {'nome_cliente': nome_cliente})


# ==================== TELA DE AGENDAMENTO ====================
def agendamento(request):
    if 'usuario_id' not in request.session:
        return redirect('login')
    
    barbeiros = Barbeiro.objects.all()
    servicos = Servico.objects.all()
    return render(request, 'agenda/agendar.html', {
        'barbeiros': barbeiros,
        'servicos': servicos,
    })

def cancelar_agendamento(request, agendamento_id):
    if 'usuario_id' not in request.session:
        return redirect('login')
    
    # Busca o agendamento garantindo que pertence ao usuário logado
    agendamento = get_object_or_404(Agendamento, id=agendamento_id, usuario_id=request.session['usuario_id'])
    
    agendamento.delete()
    messages.success(request, "Agendamento cancelado com sucesso!")
    return redirect('meus_agendamentos')


# ==================== AJAX DETALHE — CLIENTE ====================
def detalhe_agendamento_cliente(request, agendamento_id):
    """AJAX GET: retorna JSON com detalhes de um agendamento do cliente logado."""
    usuario_id = request.session.get('usuario_id')
    if not usuario_id:
        return JsonResponse({'error': 'Sessão expirada.'}, status=401)

    ag = get_object_or_404(Agendamento, pk=agendamento_id, usuario_id=usuario_id)

    # Horários disponíveis para edição (exclui o horário atual do próprio ag)
    escala = EscalaBarbeiro.objects.filter(
        barbeiro=ag.barbeiro, dia_semana=ag.data.weekday()
    ).first()
    if escala and escala.ativo:
        inicio = escala.horario_inicio or datetime.time(8, 0)
        fim    = escala.horario_fim    or datetime.time(18, 0)
    else:
        inicio, fim = datetime.time(8, 0), datetime.time(18, 0)

    ocupados = set(
        Agendamento.objects.filter(barbeiro=ag.barbeiro, data=ag.data)
        .exclude(pk=agendamento_id)
        .values_list('hora', flat=True)
    )
    intervalo = ag.servico.duracao_minutos if ag.servico else 30
    horarios = []
    loop = datetime.datetime.combine(ag.data, inicio)
    limite = datetime.datetime.combine(ag.data, fim)
    while loop <= limite:
        h = loop.time()
        horarios.append({'valor': h.strftime('%H:%M'), 'ocupado': h in ocupados})
        loop += datetime.timedelta(minutes=intervalo)

    # Status legível
    status_labels = {
        'pendente':   'Pendente',
        'confirmado': 'Confirmado',
        'execucao':   'Em atendimento',
        'concluido':  'Concluído',
        'cancelado':  'Cancelado',
    }

    pode_editar = ag.status in ('pendente', 'confirmado')

    return JsonResponse({
        'id':            ag.id,
        'servico_id':    ag.servico_id,
        'servico_nome':  ag.servico.nome if ag.servico else '—',
        'servico_preco': str(ag.servico.valor) if ag.servico else '',
        'barbeiro_id':   ag.barbeiro_id,
        'barbeiro_nome': ag.barbeiro.nome if ag.barbeiro else '—',
        'data':          ag.data.strftime('%Y-%m-%d'),
        'data_display':  ag.data.strftime('%d/%m/%Y'),
        'hora':          ag.hora.strftime('%H:%M'),
        'status':        ag.status,
        'status_label':  status_labels.get(ag.status, ag.status),
        'observacao':    ag.observacao or '',
        'pode_editar':   pode_editar,
        'horarios_disponiveis': horarios,
        'servicos': list(Servico.objects.values('id', 'nome', 'duracao_minutos')),
    })


# ==================== EDITAR AGENDAMENTO — CLIENTE ====================
def editar_agendamento_cliente(request, agendamento_id):
    """POST: cliente pode alterar serviço, data e hora (apenas se pendente ou confirmado)."""
    usuario_id = request.session.get('usuario_id')
    if not usuario_id:
        return redirect('login')

    ag = get_object_or_404(Agendamento, pk=agendamento_id, usuario_id=usuario_id)

    if ag.status not in ('pendente', 'confirmado'):
        messages.error(request, 'Só é possível editar agendamentos pendentes ou confirmados.')
        return redirect('meus_agendamentos')

    if request.method != 'POST':
        return redirect('meus_agendamentos')

    servico_id = request.POST.get('servico_id')
    data_str   = request.POST.get('data', '')
    hora_str   = request.POST.get('horario', '')
    observacao = request.POST.get('observacao', '').strip()

    try:
        servico = Servico.objects.get(pk=servico_id)
        data    = datetime.datetime.strptime(data_str, '%Y-%m-%d').date()
        hora    = datetime.datetime.strptime(hora_str, '%H:%M').time()
    except (Servico.DoesNotExist, TypeError, ValueError):
        messages.error(request, 'Dados inválidos. Verifique serviço, data e horário.')
        return redirect('meus_agendamentos')

    if data < datetime.date.today():
        messages.error(request, 'Não é possível agendar para uma data passada.')
        return redirect('meus_agendamentos')

    # Conflito de horário (ignora o próprio agendamento)
    if Agendamento.objects.filter(
        barbeiro=ag.barbeiro, data=data, hora=hora
    ).exclude(pk=ag.pk).exists():
        messages.error(request, 'Este horário já está ocupado. Escolha outro.')
        return redirect('meus_agendamentos')

    ag.servico    = servico
    ag.data       = data
    ag.hora       = hora
    ag.observacao = observacao or None
    ag.save()

    messages.success(request, 'Agendamento atualizado com sucesso!')
    return redirect('meus_agendamentos')


# ==================== BUSCAR BARBEIROS DISPONÍVEIS (AJAX) ====================
def get_barbeiros_disponiveis(request):
    """Retorna lista de barbeiros que atendem na data informada, considerando a EscalaBarbeiro."""
    if 'usuario_id' not in request.session:
        return JsonResponse({'error': 'Sessão expirada.'}, status=401)

    data_str = request.GET.get('data', '')
    try:
        data = datetime.datetime.strptime(data_str, '%Y-%m-%d').date()
    except ValueError:
        return JsonResponse({'error': 'Data inválida.'}, status=400)

    # Monta um dicionário {barbeiro_id: ativo} para o dia da semana da data
    escalas = dict(
        EscalaBarbeiro.objects.filter(dia_semana=data.weekday())
        .values_list('barbeiro_id', 'ativo')
    )

    barbeiros = []
    for barbeiro in Barbeiro.objects.all().order_by('nome'):
        # Se há escala cadastrada, respeita o campo ativo; se não há, considera
        # ativo por padrão exceto no domingo (weekday 6)
        ativo = escalas.get(barbeiro.id, data.weekday() != 6)
        if ativo:
            barbeiros.append({'id': barbeiro.id, 'nome': barbeiro.nome})

    return JsonResponse({'barbeiros': barbeiros, 'data': data.isoformat()})


# ==================== BUSCAR HORÁRIOS (AJAX) ====================
def get_horarios_disponiveis(request):
    # Aceita sessão de cliente OU de barbeiro (para o modal de edição)
    if 'usuario_id' not in request.session and 'barbeiro_id' not in request.session:
        return JsonResponse({'error': 'Sessão expirada.'}, status=401)

    barbeiro_id = request.GET.get('barbeiro_id')
    data_str = request.GET.get('data')
    servico_id = request.GET.get('servico_id')  # usado para calcular o intervalo entre slots

    if not barbeiro_id or not data_str:
        return JsonResponse({'error': 'Parâmetros faltando'}, status=400)

    try:
        data_selecionada = datetime.datetime.strptime(data_str, '%Y-%m-%d').date()
    except ValueError:
        return JsonResponse({'error': 'Formato de data inválido'}, status=400)

    # 1. DURAÇÃO DO SERVIÇO — define o intervalo entre os slots
    # Se não vier servico_id ou o serviço não existir, usa 30 min como padrão
    intervalo_minutos = 30
    if servico_id:
        try:
            servico = Servico.objects.get(pk=servico_id)
            intervalo_minutos = servico.duracao_minutos
        except Servico.DoesNotExist:
            pass  # mantém 30 min

    # 2. ESCALA DO BARBEIRO PARA O DIA DA SEMANA
    dia_semana = data_selecionada.weekday()  # 0=Segunda, 6=Domingo
    escala = EscalaBarbeiro.objects.filter(barbeiro_id=barbeiro_id, dia_semana=dia_semana).first()

    if escala:
        if not escala.ativo:
            return JsonResponse({'horarios': [], 'folga': True})
        escala_inicio = escala.horario_inicio or datetime.time(8, 0)
        escala_fim = escala.horario_fim or datetime.time(18, 0)
    else:
        # Sem escala cadastrada: padrão segunda a sábado, folga no domingo
        if dia_semana == 6:
            return JsonResponse({'horarios': [], 'folga': True})
        escala_inicio = datetime.time(8, 0)
        escala_fim = datetime.time(18, 0)

    # 3. HORÁRIOS JÁ RESERVADOS NO BANCO
    horarios_reservados = set(
        Agendamento.objects.filter(
            barbeiro_id=barbeiro_id,
            data=data_selecionada,
        ).values_list('hora', flat=True)
    )
    horarios_reservados_str = {h.strftime('%H:%M') for h in horarios_reservados}

    # 4. HORA ATUAL (para bloquear horários passados no dia de hoje)
    agora = timezone.localtime(timezone.now())
    hoje = agora.date()
    hora_atual = agora.time()

    horarios_disponiveis = []
    hora_loop = datetime.datetime.combine(data_selecionada, escala_inicio)
    hora_limite = datetime.datetime.combine(data_selecionada, escala_fim)

    # 5. GERA OS SLOTS COM INTERVALO BASEADO NA DURAÇÃO DO SERVIÇO
    while hora_loop <= hora_limite:
        slot = hora_loop.time()
        horario_str = slot.strftime('%H:%M')

        nao_reservado = horario_str not in horarios_reservados_str
        no_futuro = slot > hora_atual if data_selecionada == hoje else True

        if nao_reservado and no_futuro:
            horarios_disponiveis.append(horario_str)

        hora_loop += datetime.timedelta(minutes=intervalo_minutos)

    return JsonResponse({'horarios': horarios_disponiveis, 'folga': False})




"""def get_horarios_disponiveis(request):
    barbeiro_id = request.GET.get('barbeiro_id')
    data = request.GET.get('data')
    
    if not barbeiro_id or not data:
        return JsonResponse({'error': 'Parâmetros faltando'}, status=400)
    
    horarios_reservados = Agendamento.objects.filter(
        barbeiro_id=barbeiro_id,
        data=data
    ).values_list('hora', flat=True)
    
    horarios_reservados_str = [h.strftime('%H:%M') for h in horarios_reservados]
    
    horarios_disponiveis = []
    hora_atual = datetime.datetime.strptime('09:00', '%H:%M')
    hora_fim = datetime.datetime.strptime('19:00', '%H:%M')
    
    while hora_atual <= hora_fim:
        horario_str = hora_atual.strftime('%H:%M')
        if horario_str not in horarios_reservados_str:
            horarios_disponiveis.append(horario_str)
        hora_atual += datetime.timedelta(minutes=30)
    
    return JsonResponse({'horarios': horarios_disponiveis}) """


# ==================== SALVAR AGENDAMENTO ====================
def salvar_agendamento(request):
    if request.method == 'POST':
        usuario_id = request.session.get('usuario_id')
        if not usuario_id:
            return redirect('login')

        barbeiro_id = request.POST.get('barbeiro_id')
        servico_id = request.POST.get('servico_id')
        data_str = request.POST.get('data')
        hora = request.POST.get('horario')

        # Valida se o barbeiro existe
        try:
            barbeiro = Barbeiro.objects.get(pk=barbeiro_id)
        except (Barbeiro.DoesNotExist, TypeError, ValueError):
            messages.error(request, 'Barbeiro inválido.')
            return redirect('agendamento')

        # Valida se a data é válida
        try:
            data = datetime.datetime.strptime(data_str, '%Y-%m-%d').date()
        except (TypeError, ValueError):
            messages.error(request, 'Data inválida.')
            return redirect('agendamento')

        # Valida se o barbeiro atende neste dia (escala)
        dia_semana = data.weekday()
        escala = EscalaBarbeiro.objects.filter(
            barbeiro=barbeiro, dia_semana=dia_semana
        ).first()
        if escala and not escala.ativo:
            messages.error(request, f'{barbeiro.nome} não atende neste dia.')
            return redirect('agendamento')
        # Sem escala cadastrada: domingo é folga padrão
        if not escala and dia_semana == 6:
            messages.error(request, f'{barbeiro.nome} não atende aos domingos.')
            return redirect('agendamento')

        # Valida horário duplicado
        if Agendamento.objects.filter(barbeiro=barbeiro, data=data, hora=hora).exists():
            messages.error(request, 'Este horário já foi reservado!')
            return redirect('agendamento')

        Agendamento.objects.create(
            usuario_id=usuario_id,
            barbeiro=barbeiro,
            servico_id=servico_id,
            data=data,
            hora=hora,
        )

        messages.success(request, 'Agendamento realizado com sucesso!')
        return redirect('meus_agendamentos')

    return redirect('agendamento')


# ==================== MEUS AGENDAMENTOS ====================
def meus_agendamentos(request):
    if 'usuario_id' not in request.session:
        return redirect('login')
    
    agendamentos = Agendamento.objects.filter(
        usuario_id=request.session['usuario_id']
    ).select_related('barbeiro', 'servico').order_by('-data', '-hora')
    
    return render(request, 'agenda/meus_agendamentos.html', {'agendamentos': agendamentos})


# ==================== HOME BARBEIRO (KANBAN) ====================
def home_barbeiro(request):
    barbeiro_id = request.session.get('barbeiro_id')
    if not barbeiro_id: 
        return redirect('login')

    try:
        barbeiro_logado = Barbeiro.objects.get(id=barbeiro_id)
        agendamentos = Agendamento.objects.filter(barbeiro=barbeiro_logado)

        context = {
            'barbeiro': barbeiro_logado,
            'pendentes': agendamentos.filter(status='pendente'), # Ajustado para bater com seu banco
            'confirmado': agendamentos.filter(status='confirmado'),
            'execucao': agendamentos.filter(status='execucao'),
            'concluidos': agendamentos.filter(status='concluido'),
        }
        return render(request, 'agenda/home_barbeiro.html', context)
    except Barbeiro.DoesNotExist:
        return redirect('login')

# GERENCIA ==========================================================
def gerencia(request):
    #def gerencia(request):
    # 1. Busca o barbeiro logado na sessão
    barbeiro_id = request.session.get('barbeiro_id')
    if not barbeiro_id: 
        return redirect('login')

    try:
        barbeiro_logado = Barbeiro.objects.get(id=barbeiro_id)
    except Barbeiro.DoesNotExist:
        return redirect('login')
    
    # 2. Busca as escalas já existentes para este barbeiro
    queryset_escala = EscalaBarbeiro.objects.filter(barbeiro=barbeiro_logado).order_by('dia_semana')
    
    # 3. Se ele ainda não tiver os 7 dias cadastrados no banco, cria com horários padrão
    if queryset_escala.count() < 7:
        dias_existentes = queryset_escala.values_list('dia_semana', flat=True)
        for dia in range(7):
            if dia not in dias_existentes:
                EscalaBarbeiro.objects.create(
                    barbeiro=barbeiro_logado,
                    dia_semana=dia,
                    horario_inicio="08:00",  # Horário padrão inicial
                    horario_fim="18:00",     # Horário padrão final
                    ativo=(dia != 6)         # Padrão: segunda a sábado; domingo de folga
                )
        # Atualiza a lista após criar os dias que faltavam
        queryset_escala = EscalaBarbeiro.objects.filter(barbeiro=barbeiro_logado).order_by('dia_semana')

    # 4. Processa o salvamento quando o barbeiro clica em "Salvar"
    if request.method == 'POST':
        formset = EscalaFormSet(request.POST, queryset=queryset_escala)
        if formset.is_valid():
            formset.save()
            messages.success(request, "Sua escala de trabalho foi salva com sucesso!")
            return redirect('gerencia_barbeiro') # Recarrega a página atualizando os dados
    else:
        # Se for um acesso normal (GET), apenas carrega os dados atuais do banco
        formset = EscalaFormSet(queryset=queryset_escala)

    # CORRIGIDO: Agora enviamos o 'formset' e os dados do 'barbeiro' dentro do contexto para o HTML
    context = {
        'formset': formset,
        'barbeiro': barbeiro_logado
    }
    return render(request, 'agenda/gerencia.html', context)







# ==================== AJAX PARA O KANBAN ====================
@csrf_exempt
def atualizar_status_agendamento(request):
    if request.method == 'POST':
        try:
            dados = json.loads(request.body)
            agendamento = Agendamento.objects.get(id=dados['id'])
            agendamento.status = dados['status']
            agendamento.save()
            return JsonResponse({'status': 'sucesso'})
        except Exception as e:
            return JsonResponse({'status': 'erro', 'message': str(e)}, status=400)


# ==================== LOGOUT ====================
def logout_cliente(request):
    request.session.flush()
    messages.success(request, "Você saiu do sistema!")
    return redirect('login')


# ==================== CRUD DE AGENDAMENTOS PELO BARBEIRO ====================

def _barbeiro_logado_ou_401(request):
    """Retorna o Barbeiro logado ou None se não autenticado."""
    barbeiro_id = request.session.get('barbeiro_id')
    if not barbeiro_id:
        return None
    try:
        return Barbeiro.objects.get(pk=barbeiro_id)
    except Barbeiro.DoesNotExist:
        return None


def novo_agendamento_barbeiro(request):
    """GET: exibe formulário. POST: salva novo agendamento."""
    barbeiro = _barbeiro_logado_ou_401(request)
    if not barbeiro:
        return redirect('login')

    servicos = Servico.objects.all().order_by('nome')
    hoje = timezone.localdate()
    ctx = {
        'barbeiro': barbeiro,
        'servicos': servicos,
        'data_minima': hoje.isoformat(),
        'data_maxima': (hoje + datetime.timedelta(days=30)).isoformat(),
    }

    if request.method != 'POST':
        return render(request, 'agenda/novo_agendamento_barbeiro.html', ctx)

    # -- Leitura dos dados do formulário --
    tipo_cliente = request.POST.get('tipo_cliente', 'avulso')
    nome_avulso = request.POST.get('nome_avulso', '').strip()
    telefone_busca = re.sub(r'\D', '', request.POST.get('telefone_cliente', ''))
    servico_id = request.POST.get('servico_id')
    data_str = request.POST.get('data', '')
    hora_str = request.POST.get('horario', '')
    observacao = request.POST.get('observacao', '').strip()

    # -- Resolve o cliente --
    usuario = None
    if tipo_cliente == 'cadastrado':
        try:
            usuario = Usuario.objects.get(telefone=telefone_busca)
        except Usuario.DoesNotExist:
            messages.error(request, 'Cliente não encontrado. Verifique o telefone ou use o campo de nome avulso.')
            return render(request, 'agenda/novo_agendamento_barbeiro.html', ctx)
        nome_avulso = None
    else:
        if not nome_avulso:
            messages.error(request, 'Informe o nome do cliente.')
            return render(request, 'agenda/novo_agendamento_barbeiro.html', ctx)

    # -- Valida serviço, data e hora --
    try:
        servico = Servico.objects.get(pk=servico_id)
        data = datetime.datetime.strptime(data_str, '%Y-%m-%d').date()
        hora = datetime.datetime.strptime(hora_str, '%H:%M').time()
    except (Servico.DoesNotExist, TypeError, ValueError):
        messages.error(request, 'Selecione um serviço, data e horário válidos.')
        return render(request, 'agenda/novo_agendamento_barbeiro.html', ctx)

    # Bloqueia datas no passado
    if data < timezone.localdate():
        messages.error(request, 'Não é possível agendar para uma data que já passou.')
        return render(request, 'agenda/novo_agendamento_barbeiro.html', ctx)

    # -- Valida escala do barbeiro --
    dia_semana = data.weekday()
    escala = EscalaBarbeiro.objects.filter(barbeiro=barbeiro, dia_semana=dia_semana).first()
    if escala and not escala.ativo:
        messages.error(request, 'Você não atende neste dia conforme sua escala.')
        return render(request, 'agenda/novo_agendamento_barbeiro.html', ctx)
    if not escala and dia_semana == 6:
        messages.error(request, 'Sem escala cadastrada, o padrão é folga no domingo.')
        return render(request, 'agenda/novo_agendamento_barbeiro.html', ctx)

    # -- Valida conflito de horário --
    if Agendamento.objects.filter(barbeiro=barbeiro, data=data, hora=hora).exists():
        messages.error(request, 'Este horário já está ocupado na sua agenda.')
        return render(request, 'agenda/novo_agendamento_barbeiro.html', ctx)

    Agendamento.objects.create(
        usuario=usuario,
        nome_avulso=nome_avulso,
        barbeiro=barbeiro,
        servico=servico,
        data=data,
        hora=hora,
        observacao=observacao or None,
        status='pendente',
    )
    messages.success(request, 'Agendamento criado com sucesso!')
    return redirect('home_barbeiro')


def buscar_cliente_por_telefone(request):
    """AJAX: retorna dados do cliente pelo telefone para preencher o formulário."""
    barbeiro = _barbeiro_logado_ou_401(request)
    if not barbeiro:
        return JsonResponse({'error': 'Sessão expirada.'}, status=401)

    telefone = re.sub(r'\D', '', request.GET.get('telefone', ''))
    if len(telefone) < 10:
        return JsonResponse({'encontrado': False})

    try:
        usuario = Usuario.objects.get(telefone=telefone)
        return JsonResponse({'encontrado': True, 'nome': usuario.nome, 'id': usuario.id})
    except Usuario.DoesNotExist:
        return JsonResponse({'encontrado': False})


def detalhe_agendamento_barbeiro(request, agendamento_id):
    """AJAX GET: retorna JSON com os detalhes de um agendamento para o pop-up."""
    barbeiro = _barbeiro_logado_ou_401(request)
    if not barbeiro:
        return JsonResponse({'error': 'Sessão expirada.'}, status=401)

    ag = get_object_or_404(Agendamento, pk=agendamento_id, barbeiro=barbeiro)

    # Horários disponíveis para o dia (para o select de edição no pop-up)
    escala = EscalaBarbeiro.objects.filter(
        barbeiro=barbeiro, dia_semana=ag.data.weekday()
    ).first()
    if escala:
        inicio = escala.horario_inicio or datetime.time(8, 0)
        fim = escala.horario_fim or datetime.time(18, 0)
    else:
        inicio, fim = datetime.time(8, 0), datetime.time(18, 0)

    ocupados = set(
        Agendamento.objects.filter(barbeiro=barbeiro, data=ag.data)
        .exclude(pk=agendamento_id)
        .values_list('hora', flat=True)
    )
    horarios = []
    loop = datetime.datetime.combine(ag.data, inicio)
    limite = datetime.datetime.combine(ag.data, fim)
    intervalo = ag.servico.duracao_minutos if ag.servico else 30
    while loop <= limite:
        h = loop.time()
        horarios.append({'valor': h.strftime('%H:%M'), 'ocupado': h in ocupados})
        loop += datetime.timedelta(minutes=intervalo)

    return JsonResponse({
        'id': ag.id,
        'nome_cliente': ag.nome_cliente(),
        'telefone': ag.usuario.telefone if ag.usuario else '',
        'servico_id': ag.servico_id,
        'servico_nome': ag.servico.nome if ag.servico else '',
        'data': ag.data.strftime('%Y-%m-%d'),
        'data_display': ag.data.strftime('%d/%m/%Y'),
        'hora': ag.hora.strftime('%H:%M'),
        'status': ag.status,
        'observacao': ag.observacao or '',
        'horarios_disponiveis': horarios,
        'servicos': list(Servico.objects.values('id', 'nome', 'duracao_minutos')),
    })


def editar_agendamento_barbeiro(request, agendamento_id):
    """POST: atualiza serviço, data, hora e observação de um agendamento."""
    barbeiro = _barbeiro_logado_ou_401(request)
    if not barbeiro:
        return JsonResponse({'error': 'Sessão expirada.'}, status=401)

    ag = get_object_or_404(Agendamento, pk=agendamento_id, barbeiro=barbeiro)

    if request.method != 'POST':
        return JsonResponse({'error': 'Método não permitido.'}, status=405)

    servico_id = request.POST.get('servico_id')
    data_str = request.POST.get('data', '')
    hora_str = request.POST.get('horario', '')
    observacao = request.POST.get('observacao', '').strip()

    try:
        servico = Servico.objects.get(pk=servico_id)
        data = datetime.datetime.strptime(data_str, '%Y-%m-%d').date()
        hora = datetime.datetime.strptime(hora_str, '%H:%M').time()
    except (Servico.DoesNotExist, TypeError, ValueError):
        messages.error(request, 'Dados inválidos. Verifique serviço, data e horário.')
        return redirect('home_barbeiro')

    # Bloqueia datas no passado
    if data < timezone.localdate():
        messages.error(request, 'Não é possível agendar para uma data que já passou.')
        return redirect('home_barbeiro')

    # Conflito de horário (ignora o próprio agendamento)
    if Agendamento.objects.filter(barbeiro=barbeiro, data=data, hora=hora).exclude(pk=ag.pk).exists():
        messages.error(request, 'Você já tem um agendamento neste horário.')
        return redirect('home_barbeiro')

    ag.servico = servico
    ag.data = data
    ag.hora = hora
    ag.observacao = observacao or None
    ag.save()

    messages.success(request, 'Agendamento atualizado com sucesso!')
    return redirect('home_barbeiro')


def excluir_agendamento_barbeiro(request, agendamento_id):
    """POST: exclui um agendamento pertencente ao barbeiro logado."""
    barbeiro = _barbeiro_logado_ou_401(request)
    if not barbeiro:
        return redirect('login')

    ag = get_object_or_404(Agendamento, pk=agendamento_id, barbeiro=barbeiro)

    if request.method != 'POST':
        return redirect('home_barbeiro')

    ag.delete()
    messages.success(request, 'Agendamento excluído.')
    return redirect('home_barbeiro')


# ==================== AJAX: AGENDAMENTOS POR DATA (CALENDÁRIO) ====================
def agendamentos_por_data(request):
    """AJAX GET: retorna agendamentos do barbeiro logado para uma data específica."""
    barbeiro = _barbeiro_logado_ou_401(request)
    if not barbeiro:
        return JsonResponse({'error': 'Sessão expirada.'}, status=401)

    data_str = request.GET.get('data', '')
    try:
        data = datetime.datetime.strptime(data_str, '%Y-%m-%d').date()
    except ValueError:
        return JsonResponse({'error': 'Data inválida.'}, status=400)

    status_labels = {
        'pendente':   'Pendente',
        'confirmado': 'Confirmado',
        'execucao':   'Em atendimento',
        'concluido':  'Concluído',
        'cancelado':  'Cancelado',
    }

    agendamentos = (
        Agendamento.objects
        .filter(barbeiro=barbeiro, data=data)
        .select_related('servico', 'usuario')
        .order_by('hora')
    )

    resultado = []
    for ag in agendamentos:
        resultado.append({
            'id':           ag.id,
            'nome_cliente': ag.nome_cliente(),
            'hora':         ag.hora.strftime('%H:%M'),
            'servico_nome': ag.servico.nome if ag.servico else '—',
            'status':       ag.status,
            'status_label': status_labels.get(ag.status, ag.status),
        })

    return JsonResponse({
        'data_display': data.strftime('%d/%m/%Y'),
        'agendamentos': resultado,
    })


# ==================== SSE: STREAM DE STATUS DO CLIENTE ====================
import time
from django.http import StreamingHttpResponse

def _status_snapshot(usuario_id):
    """Retorna dict {ag_id: status} para todos os agendamentos do cliente."""
    return {
        str(ag.id): ag.status
        for ag in Agendamento.objects.filter(usuario_id=usuario_id).only('id', 'status')
    }


def agendamentos_stream(request):
    """
    SSE: mantém conexão aberta e envia um evento 'status_update' sempre que
    algum agendamento do cliente logado mudar de status.
    Faz poll leve no banco a cada 3 s (sem dependências externas).
    """
    usuario_id = request.session.get('usuario_id')
    if not usuario_id:
        return StreamingHttpResponse(status=401)

    status_labels = {
        'pendente':   'Pendente',
        'confirmado': 'Confirmado',
        'execucao':   'Em atendimento',
        'concluido':  'Concluído',
        'cancelado':  'Cancelado',
    }

    def event_stream():
        anterior = _status_snapshot(usuario_id)
        # Heartbeat inicial para confirmar conexão
        yield 'event: ping\ndata: ok\n\n'

        inicio = time.time()
        while time.time() - inicio < 1800:
            time.sleep(3)
            try:
                atual = _status_snapshot(usuario_id)
            except Exception:
                break

            mudancas = []
            for ag_id, status in atual.items():
                if anterior.get(ag_id) != status:
                    mudancas.append({
                        'id':           ag_id,
                        'status':       status,
                        'status_label': status_labels.get(status, status),
                    })

            if mudancas:
                payload = json.dumps(mudancas)
                yield f'event: status_update\ndata: {payload}\n\n'
                anterior = atual
            else:
                yield ': ping\n\n'

    response = StreamingHttpResponse(event_stream(), content_type='text/event-stream')
    response['Cache-Control'] = 'no-cache'
    response['X-Accel-Buffering'] = 'no'   # desativa buffer no Nginx
    return response


# ==================== AJAX: SNAPSHOT DE STATUS (cliente) ====================
def agendamentos_snapshot(request):
    """
    AJAX GET: retorna {id: status} de todos os agendamentos do cliente logado.
    Usado pelo cliente para recuperar o estado atual após reconexão do SSE.
    """
    usuario_id = request.session.get('usuario_id')
    if not usuario_id:
        return JsonResponse({'error': 'Sessão expirada.'}, status=401)

    snapshot = _status_snapshot(usuario_id)
    return JsonResponse({'snapshot': snapshot})


# ==================== SSE: STREAM DO KANBAN DO BARBEIRO ====================

def _kanban_snapshot(barbeiro_id):
    """
    Retorna dict {ag_id: dados} com todos os agendamentos do barbeiro.
    'dados' contém os campos relevantes para detectar qualquer mudança.
    """
    resultado = {}
    ags = (
        Agendamento.objects
        .filter(barbeiro_id=barbeiro_id)
        .select_related('servico', 'usuario')
        .only('id', 'status', 'data', 'hora', 'nome_avulso',
              'servico__nome', 'usuario__nome')
    )
    for ag in ags:
        resultado[str(ag.id)] = {
            'status':       ag.status,
            'data':         ag.data.strftime('%d/%m/%Y'),
            'hora':         ag.hora.strftime('%H:%M'),
            'nome_cliente': ag.nome_cliente(),
            'servico_nome': ag.servico.nome if ag.servico else '—',
        }
    return resultado


def barbeiro_kanban_stream(request):
    """
    SSE: mantém conexão aberta e emite eventos ao kanban do barbeiro logado
    sempre que um cliente cria, edita ou cancela um agendamento.

    Eventos emitidos:
      - card_new    → novo agendamento criado pelo cliente
      - card_update → agendamento editado (data, hora, serviço)
      - card_remove → agendamento cancelado/excluído
    """
    barbeiro_id = request.session.get('barbeiro_id')
    if not barbeiro_id:
        return StreamingHttpResponse(status=401)

    def event_stream():
        anterior = _kanban_snapshot(barbeiro_id)
        yield 'event: ping\ndata: ok\n\n'

        inicio = time.time()
        while time.time() - inicio < 1800:
            time.sleep(3)
            try:
                atual = _kanban_snapshot(barbeiro_id)
            except Exception:
                break

            eventos = []

            # Novos agendamentos
            for ag_id, dados in atual.items():
                if ag_id not in anterior:
                    eventos.append({
                        'tipo': 'card_new',
                        'id':   ag_id,
                        **dados,
                    })

            # Agendamentos removidos (cancelados pelo cliente)
            for ag_id in anterior:
                if ag_id not in atual:
                    eventos.append({'tipo': 'card_remove', 'id': ag_id})

            # Agendamentos editados (qualquer campo mudou)
            for ag_id, dados in atual.items():
                if ag_id in anterior and dados != anterior[ag_id]:
                    eventos.append({
                        'tipo': 'card_update',
                        'id':   ag_id,
                        **dados,
                    })

            if eventos:
                payload = json.dumps(eventos)
                yield f'event: kanban_update\ndata: {payload}\n\n'
                anterior = atual
            else:
                yield ': ping\n\n'

    response = StreamingHttpResponse(event_stream(), content_type='text/event-stream')
    response['Cache-Control'] = 'no-cache'
    response['X-Accel-Buffering'] = 'no'
    return response