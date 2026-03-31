# 💈 Sistema de Agendamento - Agenda Aí

Este é um sistema de gerenciamento de barbearia desenvolvido com **Django** e **MySQL**. O projeto permite o cadastro e acesso de clientes, profissionais (barbeiros) e, em breve, a reserva de horários.

## 🚀 Funcionalidades Atuais
- **Painel do Cliente:** Tela de agendamento com interface moderna (Glassmorphism).
- **Painel do Barbeiro:** Área restrita para profissionais visualizarem sua agenda.
- **Autenticação:** Sistema de login diferenciado para clientes e barbeiros.
- **Banco de Dados:** Integração completa com MySQL.

## 🛠️ Tecnologias Utilizadas
- **Backend:** Python 3.x e Django 4.x
- **Frontend:** HTML5, CSS3 (Design de vidro roxo) e FontAwesome para ícones.
- **Banco de Dados:** MySQL 8.0
- **Ambiente de Desenvolvimento:** Windows 7 / VS Code

## 🔧 Como rodar o projeto localmente

1. **Clone o repositório:**
   bash
   git clone [https://github.com/rafaellamego/projeto-barbearia-django.git](https://github.com/rafaellamego/projeto-barbearia-django)

2. **Instale as dependências:**
    bash
    pip install -r requirements.txt

3. **Configure o Banco de Dados:**
    Crie um banco de dados no MySQL chamado barbearia_agenda.
    Ajuste as credenciais no arquivo settings.py (USER e PASSWORD).

4. **Execute as migrações do Django:**
    bash
    python manage.py migrate

5. **Inicie o servidor:**
    python manage.py runserver