<<<<<<< HEAD
#AQUI FICAM AS TABELAS DO BANCO!

from datetime import datetime, timedelta
from pyexpat.errors import messages

from django.db import models
import re

from django.http import JsonResponse #esse módulo trabalha com padrões de texto, como buscar, validar, extrair ou substituir partes de string ex.: texto="Meu númeri é 11987654321" resultado = re.search(r"\d+",texto) \d+ = pega uma seqência de números
=======
from django.db import models
>>>>>>> de6dd1e325a0b573f26f48be6076f527350fba23

class Usuario(models.Model):
    nome = models.CharField(max_length=150)
    telefone = models.CharField(max_length=11, unique=True)
    data_nascimento = models.DateField()
    senha = models.CharField(max_length=255)

    def __str__(self):
        return self.nome

class Barbeiro(models.Model):
    nome = models.CharField(max_length=150)
    telefone = models.CharField(max_length=11, unique=True)
    senha = models.CharField(max_length=255) 
    especialidade = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"Barbeiro: {self.nome}"

<<<<<<< HEAD
#Tabela com os serviços oferecidos (Corte, Barba, etc)
class Servico(models.Model):
    nome = models.CharField(max_length=100)  # Nome do serviço (ex: "Corte Simples")
    descricao = models.TextField(blank=True, null=True)  # Descrição detalhada (opcional)
    duracao_minutos = models.IntegerField()  # Quanto tempo dura (ex: 30 minutos)
    valor = models.DecimalField(max_digits=10, decimal_places=2)  # Preço (ex: 35.00)
    
=======
class Agendamento(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    barbeiro = models.ForeignKey(Barbeiro, on_delete=models.CASCADE, null=True, blank=True)
    data = models.DateField()
    hora = models.TimeField()
    # CAMPO NOVO PARA O KANBAN
    status = models.CharField(max_length=20, default='pendentes') 

>>>>>>> de6dd1e325a0b573f26f48be6076f527350fba23
    def __str__(self):
        return f"{self.nome} - R$ {self.valor} ({self.duracao_minutos}min)"


# TABELA AGENDAMENTO (A reserva em si)
class Agendamento(models.Model):
    # Opções de status (como um menu de escolhas)
    STATUS_CHOICES = [
        ('pendente', 'Pendente'),    # Aguardando confirmação
        ('confirmado', 'Confirmado'),  # Confirmado pelo barbeiro
        ('cancelado', 'Cancelado'),   # Cancelado pelo cliente
    ]
    
    # Ligações com outras tabelas (Foreign Keys = Chaves Estrangeiras)
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)  # Qual cliente agendou
    barbeiro = models.ForeignKey(Barbeiro, on_delete=models.CASCADE, null=True, blank=True)  # Qual barbeiro vai atender
    servico = models.ForeignKey(Servico, on_delete=models.CASCADE, null=True, blank=True)  # Qual serviço foi escolhido
    
    # Dados do agendamento
    data = models.DateField()  # Dia do agendamento
    hora = models.TimeField()  # Horário do agendamento
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pendente')  # Situação atual
    
    # Metadados (informações automáticas)
    observacao = models.TextField(blank=True, null=True)  # Recado do cliente (opcional)
    
    class Meta:
        # Impede o mesmo barbeiro de ter dois agendamentos no mesmo dia/hora
        unique_together = ['barbeiro', 'data', 'hora']
    
    def __str__(self):
        """Como o agendamento aparece no admin/shell"""
        servico_nome = self.servico.nome if self.servico else "Sem serviço"
        barbeiro_nome = self.barbeiro.nome if self.barbeiro else "Sem barbeiro"
        return f"{self.usuario.nome} - {servico_nome} com {barbeiro_nome} - {self.data} {self.hora} ({self.status})"
