from django.urls import path
from .views import login_view, cadastrar, agendar, home_barbeiro

urlpatterns = [
    path('', login_view, name='login'), # Login padrão (cliente)
    path('barbeiro/', login_view, {'tipo': 'barbeiro'}, name='login_barbeiro'), # Login barbeiro
    path('cadastrar/', cadastrar, name='cadastrar'),

    #Rota do cliente
    path('home/', agendar, name='home'),
    #Rota do barbeiro
    path('home/barbeiro/', home_barbeiro, name='home_barbeiro'),
    
]