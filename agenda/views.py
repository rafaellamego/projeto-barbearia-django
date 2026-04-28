import datetime
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Agendamento, Usuario, Barbeiro, Servico
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Usuario, Barbeiro, Agendamento
import re
import json

# CADASTRO
def cadastrar(request):
    if request.method == 'POST':
        nome = request.POST.get("nome")
        telefone = request.POST.get("telefone")
        data_nascimento = request.POST.get("data_nascimento")
        senha = request.POST.get("senha")

        # Evita o erro de UNIQUE constraint (telefone duplicado)
        if Usuario.objects.filter(telefone=telefone).exists():
            messages.error(request, "Este telefone já está cadastrado!")
            return render(request, 'agenda/cadastrar.html', {'nome': nome})

        if not telefone.isdigit() or len(telefone) != 11:
            messages.error(request, "Telefone deve ter 11 números")
            return render(request, 'agenda/cadastrar.html')
        
        elif len(senha) < 4:
            messages.error(request, "Senha muito curta")
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
            return redirect('login')

    return render(request, 'agenda/cadastrar.html')




# ==================== HOME CLIENTE ====================
def home_cliente(request):
    if 'usuario_id' not in request.session:
        return redirect('login')
    
    nome_cliente = request.session.get('user_nome', 'Cliente')
    
    context = {
        'nome_cliente': nome_cliente,
    }
    return render(request, 'agenda/home_cliente.html', context)


# ==================== LOGIN ====================
def login_view(request, tipo='cliente'): 
    if request.method == 'POST':
        telefone = re.sub(r'\D', '', request.POST.get('telefone', ""))
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

# HOME BARBEIRO (KANBAN)
def home_barbeiro(request):
    barbeiro_id = request.session.get('barbeiro_id')
    if not barbeiro_id: 
        return redirect('login')

    try:
        barbeiro_logado = Barbeiro.objects.get(id=barbeiro_id)
        agendamentos = Agendamento.objects.filter(barbeiro=barbeiro_logado)

        context = {
            'barbeiro': barbeiro_logado,
            'pendentes': agendamentos.filter(status='pendentes'),
            'execucao': agendamentos.filter(status='execucao'),
            'concluidos': agendamentos.filter(status='concluidos'),
        }
        return render(request, 'agenda/home_barbeiro.html', context)
    except Barbeiro.DoesNotExist:
        return redirect('login')

# AJAX PARA O KANBAN
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


