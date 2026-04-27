from django.db import models

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

class Agendamento(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    barbeiro = models.ForeignKey(Barbeiro, on_delete=models.CASCADE, null=True, blank=True)
    data = models.DateField()
    hora = models.TimeField()
    # CAMPO NOVO PARA O KANBAN
    status = models.CharField(max_length=20, default='pendentes') 

    def __str__(self):
        prof = self.barbeiro.nome if self.barbeiro else "Não definido"
        return f"{self.usuario.nome} com {prof} - {self.data} {self.hora}"