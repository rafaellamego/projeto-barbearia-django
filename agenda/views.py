from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Usuario, Barbeiro
import re

# VIEW DE CADASTRO
def cadastrar(request):
    if request.method == 'POST':
        nome = request.POST.get("nome")
        telefone = request.POST.get("telefone")
        data_nascimento = request.POST.get("data_nascimento")
        senha = request.POST.get("senha")

        if not telefone.isdigit() or len(telefone) != 11:
            messages.error(request, "Telefone deve ter 11 números (DDD + número)")
            return render(request, 'agenda/cadastrar.html', request.POST)
        
        elif len(senha) < 4 or len(senha) > 12 or not re.search(r'\d', senha) or not re.search(r'[!@#$%^&*(),.?":{}|<>]', senha):
            messages.error(request, "Senha deve ter entre 4 e 12 caracteres, 1 número e 1 caractere especial")
            return render(request, 'agenda/cadastrar.html', request.POST)

        elif Usuario.objects.filter(telefone=telefone).exists():
            messages.error(request, "Usuário já cadastrado")
            return render(request, 'agenda/cadastrar.html', request.POST)

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

def home_barbeiro(request):
 #   agendamentos = Agendamento.objects.filter(barbeiro=request.user.barbeiro).order_by('horario')
    
  #  context = {
   #     'agendamentos': agendamentos,
   #     'total_hoje': agendamentos.count(),
   # }




    return render(request, 'agenda/home_barbeiro.html')
# Marcel 15/04
#from django.shortcuts import render
#from .models import Agendamento # Supondo que você tenha este model

#def home_barbeiro(request):
    # Filtra agendamentos do dia para o barbeiro logado
    agendamentos = Agendamento.objects.filter(barbeiro=request.user.barbeiro).order_by('horario')
    
   # context = {
    #    'agendamentos': agendamentos,
    #    'total_hoje': agendamentos.count(),
    #}
    return render(request, 'agenda/home_barbeiro.html', context)





# VIEW DE LOGIN COM ACESSO DIRETO PARA O BARBEIRO ADMIN
def login_view(request, tipo='cliente'): 
    if request.method == 'POST':
        telefone = request.POST.get('telefone')
        senha = request.POST.get('senha')

        # --- INÍCIO DA ALTERAÇÃO: LOGIN FIXO DO BARBEIRO ---
        # Removendo parênteses e traços caso o usuário digite com máscara
        telefone_limpo = re.sub(r'\D', '', telefone) 
        
        if telefone_limpo == "99999999999" and senha == "admin":
            return redirect('home_barbeiro')
        # --- FIM DA ALTERAÇÃO ---

        try:
            if tipo == 'barbeiro':
                # Busca na tabela de Barbeiros (para outros barbeiros cadastrados no DB)
                barbeiro = Barbeiro.objects.get(telefone=telefone, senha=senha)
                return redirect('home_barbeiro')  
            else:
                # Busca na tabela de Clientes
                usuario = Usuario.objects.get(telefone=telefone, senha=senha)
                return redirect('home')
                
        except (Usuario.DoesNotExist, Barbeiro.DoesNotExist):
            messages.error(request, "Telefone ou senha inválidos")
            return render(request, 'agenda/login.html', {'tipo': tipo})
    
    return render(request, 'agenda/login.html', {'tipo': tipo})

def agendar(request):
    return render(request, 'agenda/agendar.html')

