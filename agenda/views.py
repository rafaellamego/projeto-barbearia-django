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
    barbeiro_id = request.session.get('barbeiro_id')
    
    if not barbeiro_id:
        return redirect('login_barbeiro')

    from .models import Agendamento, Barbeiro
    barbeiro_logado = Barbeiro.objects.get(id=barbeiro_id)
    
    agendamentos = Agendamento.objects.filter(barbeiro=barbeiro_logado).order_by('hora')
    
    context = {
        'barbeiro': barbeiro_logado,
        'agendamentos': agendamentos,
        'total_hoje': agendamentos.count(),
    }
    return render(request, 'agenda/home_barbeiro.html', context)
    # REMOVA OU COMENTE TUDO QUE ESTIVER ABAIXO DESSE RETURN DENTRO DA FUNÇÃO
    
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
# VIEW DE LOGIN AJUSTADA
def login_view(request, tipo='cliente'): 
    if request.method == 'POST':
        telefone = request.POST.get('telefone')
        senha = request.POST.get('senha')

        # ERRO 1: Você precisa definir o telefone_limpo aqui dentro!
        import re
        telefone_limpo = re.sub(r'\D', '', telefone) if telefone else ""
        
        # 1. TESTE DO LOGIN FIXO (Para agilizar seu teste na UNIVESP)
        if telefone_limpo == "11922223333" and senha == "ad123":
            barbeiro = Barbeiro.objects.filter(telefone=telefone_limpo).first()
            if barbeiro:
                request.session['barbeiro_id'] = barbeiro.id
                # Forçamos o tipo para barbeiro no login fixo
                return redirect('home_barbeiro')
            else:
                messages.error(request, "Barbeiro teste não encontrado no banco. Crie-o no shell!")

        # 2. AUTENTICAÇÃO DINÂMICA
        try:
            if tipo == 'barbeiro':
                barbeiro = Barbeiro.objects.get(telefone=telefone_limpo, senha=senha)
                request.session['barbeiro_id'] = barbeiro.id
                return redirect('home_barbeiro')
            else:
                usuario = Usuario.objects.get(telefone=telefone_limpo, senha=senha)
                request.session['usuario_id'] = usuario.id
                return redirect('home')
                
        except (Usuario.DoesNotExist, Barbeiro.DoesNotExist):
            messages.error(request, "Telefone ou senha inválidos")
            # Se deu erro, volta para a mesma tela de login mantendo o tipo
            return render(request, 'agenda/login.html', {'tipo': tipo})
    
    return render(request, 'agenda/login.html', {'tipo': tipo})

def agendar(request):
    return render(request, 'agenda/agendar.html')

