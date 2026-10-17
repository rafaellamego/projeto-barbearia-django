
from datetime import datetime, timedelta
from pyexpat.errors import messages

from django.core.exceptions import ValidationError
from django.utils import timezone
from django.db import models
import re

from django.http import JsonResponse #esse módulo trabalha com padrões de texto, como buscar, validar, extrair ou substituir partes de string ex.: texto="Meu númeri é 11987654321" resultado = re.search(r"\d+",texto) \d+ = pega uma seqência de números

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

#Tabela com os serviços oferecidos (Corte, Barba, etc)
class Servico(models.Model):
    nome = models.CharField(max_length=100)  # Nome do serviço (ex: "Corte Simples")
    descricao = models.TextField(blank=True, null=True)  # Descrição detalhada (opcional)
    duracao_minutos = models.IntegerField()  # Quanto tempo dura (ex: 30 minutos)
    valor = models.DecimalField(max_digits=10, decimal_places=2)  # Preço (ex: 35.00)
    


# TABELA AGENDAMENTO (A reserva em si)
class Agendamento(models.Model):
    # Opções de status (como um menu de escolhas)
    STATUS_CHOICES = [
        ('pendentes', 'Pendente'),    # Aguardando confirmação
        ('confirmado', 'Confirmado'),  # Confirmado pelo barbeiro
        ('execucao', 'Em Execução'),
        ('concluidos', 'Concluído'),  # Cancelado pelo cliente
        ('cancelado', 'Cancelado'),
        
    ]
    
    # Ligações com outras tabelas (Foreign Keys = Chaves Estrangeiras)
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)  # Qual cliente agendou
    barbeiro = models.ForeignKey(Barbeiro, on_delete=models.CASCADE, null=True, blank=True)  # Qual barbeiro vai atender
    servico = models.ForeignKey(Servico, on_delete=models.CASCADE, null=True, blank=True)  # Qual serviço foi escolhido
    
    # Dados do agendamento
    data = models.DateField()  # Dia do agendamento
    hora = models.TimeField()  # Horário do agendamento
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pendentes')  # Situação atual
    
    # Metadados (informações automáticas)
    observacao = models.TextField(blank=True, null=True)  # Recado do cliente (opcional)
    
    class Meta:
        # Impede o mesmo barbeiro de ter dois agendamentos no mesmo dia/hora
        unique_together = ['barbeiro', 'data', 'hora']

    def clean(self):
        """Validações de regras de negócio antes de salvar"""
        super().clean()

        if not self.data or not self.hora:
            return 

# 1. IMPEDIR AGENDAMENTOS EM HORÁRIOS PASSADOS
        # Combina a data e hora do agendamento para comparar com o momento atual
        fuso_horario_atual = timezone.localtime(timezone.now())
        data_hora_agendamento = timezone.make_aware(
            datetime.combine(self.data, self.hora),
            fuso_horario_atual.tzinfo
        )

        if data_hora_agendamento < fuso_horario_atual:
            raise ValidationError("Não é possível realizar um agendamento em uma data ou horário que já passou.")

        # 2. VALIDAR SE O HORÁRIO ESTÁ DENTRO DA ESCALA DO BARBEIRO
        if self.barbeiro:
            # Descobre o dia da semana do agendamento (0 = Segunda, 6 = Domingo)
            dia_semana_agendamento = self.data.weekday()
            
            # Busca a escala do barbeiro para aquele dia da semana
            escala = EscalaBarbeiro.objects.filter(
                barbeiro=self.barbeiro, 
                dia_semana=dia_semana_agendamento
            ).first()

            # Se não houver escala cadastrada ou se o barbeiro estiver de folga (ativo=False)
            #if not escala or not escala.ativo:
            #    raise ValidationError(f"O barbeiro {self.barbeiro.nome} não trabalha neste dia da semana.")

            # Verifica se o horário escolhido está fora do expediente dele
            horario_valido = True
            if escala.horario_inicio and self.hora < escala.horario_inicio:
                horario_valido = False
            if escala.horario_fim and self.hora > escala.horario_fim:
                horario_valido = False

            #if not horario_valido:
            #    inicio = escala.horario_inicio.strftime('%H:%M') if escala.horario_inicio else "00:00"
            #    fim = escala.horario_fim.strftime('%H:%M') if escala.horario_fim else "23:59"
            #    raise ValidationError(
             #       f"Horário fora de escala. O barbeiro {self.barbeiro.nome} trabalha das {inicio} às {fim} neste dia."
             #   )

    #def save(self, *args, **kwargs):
        # Garante que o método clean() seja executado antes de salvar no banco de dados
     #   self.full_clean()
      #  super().save(*args, **kwargs)




    
    def __str__(self):
        """Como o agendamento aparece no admin/shell"""
        servico_nome = self.servico.nome if self.servico else "Sem serviço"
        barbeiro_nome = self.barbeiro.nome if self.barbeiro else "Sem barbeiro"
        return f"{self.usuario.nome} - {servico_nome} com {barbeiro_nome} - {self.data} {self.hora} ({self.status})"

# Escala Barbeiro
class EscalaBarbeiro(models.Model):
    DIAS_SEMANA = [
        (0, 'Segunda-feira'),
        (1, 'Terça-feira'),
        (2, 'Quarta-feira'),
        (3, 'Quinta-feira'),
        (4, 'Sexta-feira'),
        (5, 'Sábado'),
        (6, 'Domingo'),
    ]
    barbeiro = models.ForeignKey(Barbeiro, on_delete=models.CASCADE, related_name='escalas')
    dia_semana = models.IntegerField(choices=DIAS_SEMANA)
    horario_inicio = models.TimeField(null=True, blank=True, help_text="Início do expediente")
    horario_fim = models.TimeField(null=True, blank=True, help_text="Fim do expediente")
    
    # Campo para Ativo/Folga (True = Trabalha, False = Folga)
    ativo = models.BooleanField(default=True, verbose_name="Disponível para trabalho")

    class Meta:
        # Evita duplicar o mesmo dia da semana para o mesmo barbeiro
        unique_together = ['barbeiro', 'dia_semana']
        verbose_name = "Escala do Barbeiro"
        verbose_name_plural = "Escalas dos Barbeiros"

    def __str__(self):
        status = "Ativo" if self.ativo else "Folga"
        return f"{self.barbeiro.nome} - {self.get_dia_semana_display()} ({status})" 
