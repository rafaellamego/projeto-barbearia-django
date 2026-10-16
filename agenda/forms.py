import re
from django import forms
from django.core.exceptions import ValidationError
from django.forms import modelformset_factory
from .models import EscalaBarbeiro



class CadastroBarbeiroForm(forms.Form):
    nome_completo = forms.CharField(max_length=150, widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control'}))
    cpf = forms.CharField(max_length=14, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '000.000.000-00'}))
    celular = forms.CharField(max_length=15, widget=forms.TextInput(attrs={'class': 'form-control'}))
    endereco = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}))
    senha = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    confirmar_senha = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))

    def clean_senha(self):
        senha = self.cleaned_data.get('senha')
        # Regras: Mínimo 8 caracteres e pelo menos 1 caractere especial
        if len(senha) < 8:
            raise ValidationError("A senha deve ter no mínimo 8 caracteres.")
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", senha):
            raise ValidationError("A senha deve conter pelo menos um caractere especial.")
        return senha

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get("senha") != cleaned_data.get("confirmar_senha"):
            raise ValidationError("As senhas não conferem.")

class EscalaBarbeiroForm(forms.ModelForm):
    class Meta:
        model = EscalaBarbeiro
        fields = ['dia_semana', 'horario_inicio', 'horario_fim', 'ativo']
        widgets = {
            # Oculta ou desabilita o select do dia para o barbeiro não alterar o dia da linha
            'dia_semana': forms.HiddenInput(),
           #'dia_semana': forms.Select(attrs={'class': 'form-control', 'readonly': 'readonly'}),
            'horario_inicio': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'horario_fim': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'ativo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

# Criamos um Formset que gerencia exatamente 7 formulários (um para cada dia da semana)
# Desabilitamos a opção de excluir ou adicionar novas linhas dinamicamente
EscalaFormSet = modelformset_factory(
    EscalaBarbeiro, 
    form=EscalaBarbeiroForm,
    extra=0,
    can_delete=False
)