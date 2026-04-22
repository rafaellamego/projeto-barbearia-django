from django.urls import path
from . import views

urlpatterns = [
    # ==================== LOGIN E AUTENTICAÇÃO ====================
    path('', views.login_view, name='login'),  # Página inicial (login do cliente)
    path('barbeiro/', views.login_view, {'tipo': 'barbeiro'}, name='login_barbeiro'),  # Login do barbeiro
    path('cadastrar/', views.cadastrar, name='cadastrar'),  # Cadastro de novo cliente
    path('logout-cliente/', views.logout_cliente, name='logout_cliente'),  # Logout do sistema
    
    # ==================== PÁGINAS PRINCIPAIS ====================
    path('home/', views.home_cliente, name='home_cliente'),  # Home do cliente
    path('home/barbeiro/', views.home_barbeiro, name='home_barbeiro'),  # Painel do barbeiro
    
    # ==================== AGENDAMENTO ====================
    path('agendar/', views.agendamento, name='agendamento'),  # Tela de agendamento
    path('salvar-agendamento/', views.salvar_agendamento, name='salvar_agendamento'),  # Salvar agendamento
    path('meus-agendamentos/', views.meus_agendamentos, name='meus_agendamentos'),  # Lista de agendamentos do cliente
    
    # ==================== API E UTILITÁRIOS ====================
    path('get-horarios/', views.get_horarios_disponiveis, name='get_horarios'),  # API para buscar horários disponíveis
]
