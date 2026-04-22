import datetime
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Agendamento, Usuario, Barbeiro, Servico
import re

# ==================== CADASTRO ====================
def cadastrar(request):
    if request.method == 'POST':
        nome = request.POST.get("nome")
        telefone = request.POST.get("telefone")
        data_nascimento = request.POST.get("data_nascimento")
        senha = request.POST.get("senha")

        if not telefone.isdigit() or len(telefone) != 11:
            messages.error(request, "Telefone deve ter 11 números")
            return render(request, 'agenda/cadastrar.html')
        
        elif len(senha) < 4:
            messages.error(request, "Senha deve ter pelo menos 4 caracteres")
            return render(request, 'agenda/cadastrar.html')

        elif Usuario.objects.filter(telefone=telefone).exists():
            messages.error(request, "Usuário já cadastrado")
            return render(request, 'agenda/cadastrar.html')

        else:
            Usuario.objects.create(
                nome=nome,
                telefone=telefone,
                data_nascimento=data_nascimento,
                senha=senha
            )
            messages.success(request, "Cadastro efetuado com sucesso!")
            return redirect('login_view', tipo='cliente')

    return render(request, 'agenda/cadastrar.html')


# ==================== HOME BARBEIRO ====================
def home_barbeiro(request):
    barbeiro_id = request.session.get('barbeiro_id')
    
    if not barbeiro_id:
        return redirect('login_view', tipo='barbeiro')

    try:
        barbeiro_logado = Barbeiro.objects.get(id=barbeiro_id)
    except Barbeiro.DoesNotExist:
        return redirect('login_view', tipo='barbeiro')
    
    agendamentos = Agendamento.objects.filter(barbeiro=barbeiro_logado).order_by('hora')
    
    context = {
        'barbeiro': barbeiro_logado,
        'agendamentos': agendamentos,
        'total_hoje': agendamentos.count(),
    }
    return render(request, 'agenda/home_barbeiro.html', context)


# ==================== HOME CLIENTE ====================
def home_cliente(request):
    if 'usuario_id' not in request.session:
        return redirect('login_view', tipo='cliente')
    
    nome_cliente = request.session.get('user_nome', 'Cliente')
    
    context = {
        'nome_cliente': nome_cliente,
    }
    return render(request, 'agenda/home_cliente.html', context)


# ==================== LOGIN ====================
def login_view(request, tipo='cliente'): 
    if request.method == 'POST':
        telefone = request.POST.get('telefone')
        senha = request.POST.get('senha')

        telefone_limpo = re.sub(r'\D', '', telefone) if telefone else ""
        
        if telefone_limpo == "11922223333" and senha == "ad123":
            barbeiro = Barbeiro.objects.filter(telefone=telefone_limpo).first()
            if barbeiro:
                request.session['barbeiro_id'] = barbeiro.id
                request.session['tipo_usuario'] = 'barbeiro'
                print(f"SESSÃO CRIADA: tipo_usuario = barbeiro")  # Debug
                return redirect('home_barbeiro')
            else:
                messages.error(request, "Barbeiro teste não encontrado no banco.")

        try:
            if tipo == 'barbeiro':
                barbeiro = Barbeiro.objects.get(telefone=telefone_limpo, senha=senha)
                request.session['barbeiro_id'] = barbeiro.id
                request.session['tipo_usuario'] = 'barbeiro'
                print(f"SESSÃO CRIADA: tipo_usuario = barbeiro")
                return redirect('home_barbeiro')
            else:
                usuario = Usuario.objects.get(telefone=telefone_limpo, senha=senha)
                request.session['usuario_id'] = usuario.id
                request.session['user_nome'] = usuario.nome
                request.session['tipo_usuario'] = 'cliente'
                print(f"SESSÃO CRIADA: tipo_usuario = cliente")
                return redirect('home_cliente')
                
        except (Usuario.DoesNotExist, Barbeiro.DoesNotExist):
            messages.error(request, "Telefone ou senha inválidos")
            return render(request, 'agenda/login.html', {'tipo': tipo})
    
    return render(request, 'agenda/login.html', {'tipo': tipo})
    
    return render(request, 'agenda/login.html', {'tipo': tipo})



# ==================== BUSCAR HORÁRIOS ====================
def get_horarios_disponiveis(request):
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
    
    return JsonResponse({'horarios': horarios_disponiveis})


# ==================== SALVAR AGENDAMENTO ====================
def salvar_agendamento(request):
    if request.method == 'POST':
        usuario_id = request.session.get('usuario_id')
        
        barbeiro_id = request.POST.get('barbeiro_id')
        servico_id = request.POST.get('servico_id')
        data = request.POST.get('data')
        hora = request.POST.get('horario')
        
        if not usuario_id:
            return redirect('login_view', tipo='cliente')
        
        if Agendamento.objects.filter(barbeiro_id=barbeiro_id, data=data, hora=hora).exists():
            messages.error(request, 'Este horário já foi reservado!')
            return redirect('agendamento')
        
        Agendamento.objects.create(
            usuario_id=usuario_id,
            barbeiro_id=barbeiro_id,
            servico_id=servico_id,
            data=data,
            hora=hora
        )
        
        messages.success(request, '✅ Agendamento realizado com sucesso!')
        return redirect('meus_agendamentos')
    
    return redirect('agendamento')


# ==================== MEUS AGENDAMENTOS ====================
def meus_agendamentos(request):
    if 'usuario_id' not in request.session:
        return redirect('login_view', tipo='cliente')
    
    agendamentos = Agendamento.objects.filter(
        usuario_id=request.session['usuario_id']
    ).select_related('barbeiro', 'servico').order_by('-data', '-hora')
    
    return render(request, 'agenda/meus_agendamentos.html', {
        'agendamentos': agendamentos
    })



# ==================== TELA DE AGENDAMENTO ====================
def agendamento(request):
    if 'usuario_id' not in request.session:
        return redirect('login_view', tipo='cliente')
    
    barbeiros = Barbeiro.objects.all()
    servicos = Servico.objects.all()
    
    return render(request, 'agenda/agendar.html', {
        'barbeiros': barbeiros,
        'servicos': servicos,
    })



# ==================== LOGOUT ====================
def logout_cliente(request):
    request.session.flush()
    messages.success(request, "Você saiu do sistema!")
    storage = messages.get_messages(request)
    for _ in storage:
            pass
    return redirect('login')

