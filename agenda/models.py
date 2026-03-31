#AQUI FICAM AS TABELAS DO BANCO!

from django.db import models
import re #esse módulo trabalha com padrões de texto, como buscar, validar, extrair ou substituir partes de string ex.: texto="Meu númeri é 11987654321" resultado = re.search(r"\d+",texto) \d+ = pega uma seqência de números

class Usuario(models.Model):
    nome = models.CharField(max_length=150)
    telefone = models.CharField(max_length=11, unique=True)
    data_nascimento = models.DateField()
    senha = models.CharField(max_length=255)

    def __str__(self):
        return self.nome

# NOVA TABELA: Para os profissionais da barbearia
class Barbeiro(models.Model):
    nome = models.CharField(max_length=150)
    # Telefone será o "login" dele, assim como o do cliente
    telefone = models.CharField(max_length=11, unique=True)
    # Senha para ele acessar o sistema (mesmas regras de caracteres)
    senha = models.CharField(max_length=255) 
    
    # Opcional: caso queira saber o que ele faz (Corte, Barba, etc.)
    especialidade = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"Barbeiro: {self.nome}"

class Agendamento(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    # ADICIONADO: Vincula o agendamento a um barbeiro específico
    barbeiro = models.ForeignKey(Barbeiro, on_delete=models.CASCADE, null=True, blank=True)
    data = models.DateField()
    hora = models.TimeField()

    def __str__(self):
        prof = self.barbeiro.nome if self.barbeiro else "Não definido"
        return f"{self.usuario.nome} com {prof} - {self.data} {self.hora}"