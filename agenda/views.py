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

        messages.success(request, '✅ Agendamento realizado com sucesso!')
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