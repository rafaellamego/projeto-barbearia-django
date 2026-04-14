from django.contrib import admin
from .models import Barbeiro, Usuario, Agendamento

# Isso faz com que as tabelas apareçam na tela azul do navegador
admin.site.register(Barbeiro)
admin.site.register(Usuario)
admin.site.register(Agendamento)