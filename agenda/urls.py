from django.urls import path
from . import views

urlpatterns = [
    # --- LOGIN E CADASTRO ---
    path('', views.login_view, name='login'),
    path('cadastrar/', views.cadastrar, name='cadastrar'),
    path('logout_cliente/', views.logout_cliente, name='logout_cliente'),

    # --- ROTAS DO CLIENTE ---
    path('home/', views.home_cliente, name='home_cliente'),
    path('agendamento/', views.agendamento, name='agendamento'),
    path('salvar-agendamento/', views.salvar_agendamento, name='salvar_agendamento'),
    path('meus-agendamentos/', views.meus_agendamentos, name='meus_agendamentos'),
    path('get-horarios/', views.get_horarios_disponiveis, name='get_horarios'),

    # --- ROTAS DO BARBEIRO ---
    path('home/barbeiro/', views.home_barbeiro, name='home_barbeiro'),
    path('atualizar_status_agendamento/', views.atualizar_status_agendamento, name='atualizar_status_agendamento'),
    # --- AJAX (KANBAN) ---
    # Essa rota é essencial para o JavaScript conseguir salvar a mudança de coluna no banco!
    path('atualizar_status_agendamento/', views.atualizar_status_agendamento, name='atualizar_status_agendamento'),
]
