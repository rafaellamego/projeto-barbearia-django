from django.shortcuts import render, redirect
from django.contrib import messages
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
        
        if len(senha) < 4:
            messages.error(request, "Senha muito curta")
            return render(request, 'agenda/cadastrar.html')

        Usuario.objects.create(nome=nome, telefone=telefone, data_nascimento=data_nascimento, senha=senha)
        messages.success(request, "Cadastro efetuado!")
        return redirect('login') # Redireciona para o name='login' do seu urls.py

    return render(request, 'agenda/cadastrar.html')

# LOGIN
def login_view(request, tipo='cliente'): 
    if request.method == 'POST':
        telefone = re.sub(r'\D', '', request.POST.get('telefone', ""))
        senha = request.POST.get('senha')

        try:
            if tipo == 'barbeiro':
                user = Barbeiro.objects.get(telefone=telefone, senha=senha)
                request.session['barbeiro_id'] = user.id
                return redirect('home_barbeiro')
            else:
                user = Usuario.objects.get(telefone=telefone, senha=senha)
                request.session['usuario_id'] = user.id
                return redirect('home') # 'home' é o agendar no seu urls.py
        except:
            messages.error(request, "Dados inválidos")
    
    return render(request, 'agenda/login.html', {'tipo': tipo})

# HOME BARBEIRO (KANBAN)
def home_barbeiro(request):
    barbeiro_id = request.session.get('barbeiro_id')
    if not barbeiro_id: 
        return redirect('login_barbeiro')

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
        return redirect('login_barbeiro')

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

# TELA DE AGENDAMENTO (CLIENTE)
def agendar(request):
    usuario_id = request.session.get('usuario_id')
    if not usuario_id:
        return redirect('login')

    if request.method == 'POST':
        barbeiro_id = request.POST.get('barbeiro')
        data_hora = request.POST.get('data')
        
        try:
            # Busca as instâncias dos objetos
            cliente = Usuario.objects.get(id=usuario_id)
            barbeiro = Barbeiro.objects.get(id=barbeiro_id)
            
            # Cria o agendamento no banco
            Agendamento.objects.create(
                usuario=cliente,
                barbeiro=barbeiro,
                data=data_hora,
                status='pendentes' # Começa sempre como pendente para o Kanban
            )
            messages.success(request, "Agendamento realizado com sucesso!")
            return redirect('home')
        except Exception as e:
            messages.error(request, f"Erro ao agendar: {e}")

    # Puxa os barbeiros para aparecerem na tela
    barbeiros = Barbeiro.objects.all()
    return render(request, 'agenda/agendar.html', {'barbeiros': barbeiros})