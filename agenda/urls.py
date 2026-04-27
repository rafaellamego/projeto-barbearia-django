from django.urls import path
from . import views # Importar assim facilita a manutenção

urlpatterns = [
    # --- LOGIN E CADASTRO ---
    path('', views.login_view, name='login'), # Login padrão (cliente)
    path('barbeiro/', views.login_view, {'tipo': 'barbeiro'}, name='login_barbeiro'),
    path('cadastrar/', views.cadastrar, name='cadastrar'),

    # --- ROTAS DO CLIENTE ---
    path('home/', views.agendar, name='home'),

    # --- ROTAS DO BARBEIRO ---
    path('home/barbeiro/', views.home_barbeiro, name='home_barbeiro'),
    
    # --- AJAX (KANBAN) ---
    # Essa rota é essencial para o JavaScript conseguir salvar a mudança de coluna no banco!
    path('atualizar_status_agendamento/', views.atualizar_status_agendamento, name='atualizar_status_agendamento'),
]