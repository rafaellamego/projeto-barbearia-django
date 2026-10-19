import datetime
import re
import json
from django.conf import settings
from django.db import IntegrityError, transaction
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


def _data_dentro_do_periodo(data):
    hoje = timezone.localdate()
    return hoje <= data <= hoje + datetime.timedelta(days=30)


def _barbeiro_atende_no_dia(barbeiro, data):
    escala = EscalaBarbeiro.objects.filter(
        barbeiro=barbeiro,
        dia_semana=data.weekday(),
    ).first()
    if escala:
        return escala.ativo
    return data.weekday() != 6


def _horarios_do_barbeiro(barbeiro, data):
    if not _data_dentro_do_periodo(data) or not _barbeiro_atende_no_dia(barbeiro, data):
        return []

    escala = EscalaBarbeiro.objects.filter(
        barbeiro=barbeiro,
        dia_semana=data.weekday(),
    ).first()
    if escala:
        inicio = escala.horario_inicio or datetime.time(9, 0)
        fim = escala.horario_fim or datetime.time(19, 0)
    else:
        inicio = datetime.time(8, 0)
        fim = datetime.time(18, 0)

    reservados = set(
        Agendamento.objects.filter(
            barbeiro=barbeiro,
            data=data,
        ).values_list('hora', flat=True)
    )
    agora = timezone.localtime()
    hora_loop = datetime.datetime.combine(data, inicio)
    hora_limite = datetime.datetime.combine(data, fim)
    disponiveis = []

    while hora_loop <= hora_limite:
        horario = hora_loop.time()
        if horario not in reservados and (data != agora.date() or horario > agora.time()):
            disponiveis.append(horario.strftime('%H:%M'))
        hora_loop += datetime.timedelta(minutes=30)
    return disponiveis


def _contexto_agendamento_manual(barbeiro):
    hoje = timezone.localdate()
    return {
        'barbeiro': barbeiro,
        'servicos': Servico.objects.all().order_by('nome'),
        'clientes': Usuario.objects.all().order_by('nome'),
        'data_minima': hoje.isoformat(),
        'data_maxima': (hoje + datetime.timedelta(days=30)).isoformat(),
    }

def cancelar_agendamento(request, agendamento_id):
    if 'usuario_id' not in request.session:
        return redirect('login')
    
    # Busca o agendamento garantindo que pertence ao usuário logado
    agendamento = get_object_or_404(Agendamento, id=agendamento_id, usuario_id=request.session['usuario_id'])
    
    agendamento.delete()
    messages.success(request, "Agendamento cancelado com sucesso!")
    return redirect('meus_agendamentos')


# ==================== DISPONIBILIDADE DE BARBEIROS E HORÁRIOS ====================
def get_barbeiros_disponiveis(request):
    if 'usuario_id' not in request.session:
        return JsonResponse({'error': 'Sessão expirada.'}, status=401)

    data_str = request.GET.get('data', '')
    try:
        data = datetime.datetime.strptime(data_str, '%Y-%m-%d').date()
    except ValueError:
        return JsonResponse({'error': 'Data inválida.'}, status=400)
    if not _data_dentro_do_periodo(data):
        return JsonResponse({'error': 'Escolha uma data entre hoje e os próximos 30 dias.'}, status=400)

    escalas = dict(EscalaBarbeiro.objects.filter(
        dia_semana=data.weekday(),
    ).values_list('barbeiro_id', 'ativo'))
    barbeiros = [
        {'id': barbeiro.id, 'nome': barbeiro.nome}
        for barbeiro in Barbeiro.objects.all().order_by('nome')
        if escalas.get(barbeiro.id, data.weekday() != 6)
    ]
    return JsonResponse({'barbeiros': barbeiros, 'data': data.isoformat()})


def get_horarios_disponiveis(request):
    if 'usuario_id' not in request.session and 'barbeiro_id' not in request.session:
        return JsonResponse({'error': 'Sessão expirada.'}, status=401)

    barbeiro_id = request.GET.get('barbeiro_id')
    data_str = request.GET.get('data')
    if not barbeiro_id or not data_str:
        return JsonResponse({'error': 'Informe barbeiro e data.'}, status=400)
    if 'barbeiro_id' in request.session and str(request.session['barbeiro_id']) != str(barbeiro_id):
        return JsonResponse({'error': 'Você só pode consultar sua própria agenda.'}, status=403)

    try:
        data = datetime.datetime.strptime(data_str, '%Y-%m-%d').date()
        barbeiro = Barbeiro.objects.get(pk=barbeiro_id)
    except (ValueError, Barbeiro.DoesNotExist):
        return JsonResponse({'error': 'Barbeiro ou data inválidos.'}, status=400)
    if not _data_dentro_do_periodo(data):
        return JsonResponse({'error': 'Escolha uma data entre hoje e os próximos 30 dias.'}, status=400)
    if not _barbeiro_atende_no_dia(barbeiro, data):
        return JsonResponse({'horarios': [], 'folga': True})
    return JsonResponse({'horarios': _horarios_do_barbeiro(barbeiro, data), 'folga': False})


def _validar_dados_agendamento(barbeiro, servico_id, data_str, hora_str):
    try:
        servico = Servico.objects.get(pk=servico_id)
        data = datetime.datetime.strptime(data_str, '%Y-%m-%d').date()
        hora = datetime.datetime.strptime(hora_str, '%H:%M').time()
    except (TypeError, ValueError, Servico.DoesNotExist):
        return None, 'Selecione um serviço, data e horário válidos.'

    if not _data_dentro_do_periodo(data):
        return None, 'Escolha uma data entre hoje e os próximos 30 dias.'
    if not _barbeiro_atende_no_dia(barbeiro, data):
        return None, 'Este barbeiro não atende na data escolhida.'
    if hora_str not in _horarios_do_barbeiro(barbeiro, data):
        return None, 'Este horário não está mais disponível. Escolha outro.'
    return (servico, data, hora), None


# ==================== SALVAR AGENDAMENTO DO CLIENTE ====================
def salvar_agendamento(request):
    if request.method != 'POST':
        return redirect('agendamento')
    usuario_id = request.session.get('usuario_id')
    if not usuario_id:
        return redirect('login')

    try:
        barbeiro = Barbeiro.objects.get(pk=request.POST.get('barbeiro_id'))
    except (TypeError, ValueError, Barbeiro.DoesNotExist):
        messages.error(request, 'Selecione um barbeiro válido.')
        return redirect('agendamento')

    dados, erro = _validar_dados_agendamento(
        barbeiro,
        request.POST.get('servico_id'),
        request.POST.get('data', ''),
        request.POST.get('horario', ''),
    )
    if erro:
        messages.error(request, erro)
        return redirect('agendamento')
    servico, data, hora = dados

    try:
        with transaction.atomic():
            Agendamento.objects.create(
                usuario_id=usuario_id,
                barbeiro=barbeiro,
                servico=servico,
                data=data,
                hora=hora,
            )
    except IntegrityError:
        messages.error(request, 'Este horário acabou de ser reservado. Escolha outro.')
        return redirect('agendamento')

    messages.success(request, 'Agendamento realizado com sucesso!')
    return redirect('meus_agendamentos')


# ==================== AGENDAMENTO MANUAL DO BARBEIRO ====================
def agendamento_manual(request):
    barbeiro_id = request.session.get('barbeiro_id')
    if not barbeiro_id:
        return redirect('login')
    try:
        barbeiro = Barbeiro.objects.get(pk=barbeiro_id)
    except Barbeiro.DoesNotExist:
        return redirect('login')

    contexto = _contexto_agendamento_manual(barbeiro)
    if request.method != 'POST':
        return render(request, 'agenda/agendamento_manual.html', contexto)

    tipo_cliente = request.POST.get('tipo_cliente', 'existente')
    usuario = None
    dados_novo_cliente = None
    if tipo_cliente == 'existente':
        try:
            usuario = Usuario.objects.get(pk=request.POST.get('usuario_id'))
        except (TypeError, ValueError, Usuario.DoesNotExist):
            messages.error(request, 'Selecione um cliente cadastrado.')
            contexto['form_data'] = request.POST
            return render(request, 'agenda/agendamento_manual.html', contexto)
    elif tipo_cliente == 'novo':
        nome = request.POST.get('nome', '').strip()
        telefone = re.sub(r'\D', '', request.POST.get('telefone', ''))
        nascimento_str = request.POST.get('data_nascimento', '')
        try:
            nascimento = datetime.datetime.strptime(nascimento_str, '%Y-%m-%d').date()
        except ValueError:
            nascimento = None
        if not nome or len(telefone) != 11 or not nascimento or nascimento > timezone.localdate():
            messages.error(request, 'Informe nome, telefone com DDD e uma data de nascimento válida.')
            contexto['form_data'] = request.POST
            return render(request, 'agenda/agendamento_manual.html', contexto)
        if Usuario.objects.filter(telefone=telefone).exists():
            messages.error(request, 'Este telefone já pertence a um cliente. Selecione-o na lista de cadastrados.')
            contexto['form_data'] = request.POST
            return render(request, 'agenda/agendamento_manual.html', contexto)
        if not settings.MANUAL_CLIENT_DEFAULT_PASSWORD:
            messages.error(request, 'A senha temporária não está configurada no ambiente da aplicação.')
            contexto['form_data'] = request.POST
            return render(request, 'agenda/agendamento_manual.html', contexto)
        dados_novo_cliente = (nome, telefone, nascimento)
    else:
        messages.error(request, 'Tipo de cliente inválido.')
        contexto['form_data'] = request.POST
        return render(request, 'agenda/agendamento_manual.html', contexto)

    dados, erro = _validar_dados_agendamento(
        barbeiro,
        request.POST.get('servico_id'),
        request.POST.get('data', ''),
        request.POST.get('horario', ''),
    )
    if erro:
        messages.error(request, erro)
        contexto['form_data'] = request.POST
        return render(request, 'agenda/agendamento_manual.html', contexto)
    servico, data, hora = dados

    try:
        with transaction.atomic():
            if dados_novo_cliente:
                nome, telefone, nascimento = dados_novo_cliente
                usuario = Usuario.objects.create(
                    nome=nome,
                    telefone=telefone,
                    data_nascimento=nascimento,
                    senha=settings.MANUAL_CLIENT_DEFAULT_PASSWORD,
                )
            Agendamento.objects.create(
                usuario=usuario,
                barbeiro=barbeiro,
                servico=servico,
                data=data,
                hora=hora,
            )
    except IntegrityError:
        messages.error(request, 'Não foi possível salvar: o cliente ou horário já foi cadastrado.')
        contexto['form_data'] = request.POST
        return render(request, 'agenda/agendamento_manual.html', contexto)

    messages.success(request, f'Agendamento para {usuario.nome} criado como pendente.')
    return redirect('home_barbeiro')


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
