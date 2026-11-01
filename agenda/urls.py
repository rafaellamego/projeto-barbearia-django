from django.urls import path
from . import views

urlpatterns = [
    # --- LOGIN E CADASTRO ---
    path('', views.login_view, name='login'),
    # ADICIONE ESTA LINHA ABAIXO:
    path('barbeiro/', views.login_view, {'tipo': 'barbeiro'}, name='login_barbeiro'),
    
    path('cadastrar/', views.cadastrar, name='cadastrar'),
    path('logout_cliente/', views.logout_cliente, name='logout_cliente'),

    # --- ROTAS DO CLIENTE ---
    path('home/', views.home_cliente, name='home_cliente'),
    path('agendamento/', views.agendamento, name='agendamento'),
    path('salvar-agendamento/', views.salvar_agendamento, name='salvar_agendamento'),
    path('meus-agendamentos/', views.meus_agendamentos, name='meus_agendamentos'),
    path('get-barbeiros/', views.get_barbeiros_disponiveis, name='get_barbeiros'),
    path('get-horarios/', views.get_horarios_disponiveis, name='get_horarios'),
    path('cancelar-agendamento/<int:agendamento_id>/', views.cancelar_agendamento, name='cancelar_agendamento'),
    path('agendamento/<int:agendamento_id>/detalhe/', views.detalhe_agendamento_cliente, name='detalhe_agendamento_cliente'),
    path('agendamento/<int:agendamento_id>/editar/', views.editar_agendamento_cliente, name='editar_agendamento_cliente'),

    # --- SSE: ATUALIZAÇÕES EM TEMPO REAL (cliente) ---
    path('agendamentos/stream/', views.agendamentos_stream, name='agendamentos_stream'),
    path('agendamentos/snapshot/', views.agendamentos_snapshot, name='agendamentos_snapshot'),

    # --- ROTAS DO BARBEIRO ---
    path('gerencia/', views.gerencia, name='gerencia_barbeiro'),
    path('home/barbeiro/', views.home_barbeiro, name='home_barbeiro'),
    path('atualizar_status_agendamento/', views.atualizar_status_agendamento, name='atualizar_status_agendamento'),

    # --- CRUD DE AGENDAMENTOS PELO BARBEIRO ---
    path('barbeiro/novo-agendamento/', views.novo_agendamento_barbeiro, name='novo_agendamento_barbeiro'),
    path('barbeiro/buscar-cliente/', views.buscar_cliente_por_telefone, name='buscar_cliente_barbeiro'),
    path('barbeiro/agendamento/<int:agendamento_id>/detalhe/', views.detalhe_agendamento_barbeiro, name='detalhe_agendamento_barbeiro'),
    path('barbeiro/agendamento/<int:agendamento_id>/editar/', views.editar_agendamento_barbeiro, name='editar_agendamento_barbeiro'),
    path('barbeiro/agendamento/<int:agendamento_id>/excluir/', views.excluir_agendamento_barbeiro, name='excluir_agendamento_barbeiro'),
    path('barbeiro/agendamentos-por-data/', views.agendamentos_por_data, name='agendamentos_por_data'),
    path('barbeiro/kanban/stream/', views.barbeiro_kanban_stream, name='barbeiro_kanban_stream'),
]