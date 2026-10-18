# 💈 Agenda Aí - Sistema de Agendamento para Barbearia

Projeto Integrador (PI) da **Univesp**. Aplicação web em **Python/Django** para agendamento de horários em barbearia: o cliente escolhe o serviço, o barbeiro, o dia e o horário, e o barbeiro administra a própria agenda.

🌐 **Aplicação no ar:** http://147.15.102.248

## 🚀 Funcionalidades

**Já disponíveis**
- **Login e cadastro** separados para clientes e barbeiros
- **Agendamento pelo cliente:** escolha de serviço, barbeiro, dia e horário. Os horários livres são buscados no servidor com JavaScript, sem recarregar a página
- **Meus agendamentos:** o cliente acompanha o status de cada agendamento e pode cancelar
- **Calendário limitado:** agendamentos de hoje até 30 dias à frente, sem horários que já passaram
- **Escala do barbeiro (tela Gerência):** dias de trabalho, horário de início e fim, e dias de folga. Barbeiro que ainda não configurou atende de segunda a sábado, das 8h às 18h
- **Quadro do barbeiro:** agendamentos em 4 colunas (Pendente, Confirmado, Em execução, Concluído), movidos arrastando com o mouse
- **Acessibilidade:** botões A-, A e A+ para ajustar o tamanho da letra

**Em desenvolvimento (entrega em 06/11/2026)**
- Agendamento em etapas (serviço → barbeiro → dia → horário), mostrando só os barbeiros que atendem no dia escolhido
- Acessibilidade revisada em todas as telas

## 🛠️ Tecnologias

| Camada | Tecnologia |
| --- | --- |
| Backend | Python 3 e Django 4.2 |
| Frontend | HTML5, CSS3, JavaScript, jQuery, SortableJS e FontAwesome |
| Banco de dados | MySQL 8.0 no servidor; SQLite no desenvolvimento local |
| Servidor | Docker Compose, Gunicorn e Nginx numa VM da Oracle Cloud |

## 🔧 Como rodar na sua máquina

Não é preciso instalar MySQL nem Docker: localmente o projeto usa SQLite.

**1. Baixe o projeto**
```bash
git clone -b integracao-oracle https://github.com/rafaellamego/projeto-barbearia-django.git agenda-ai
cd agenda-ai
```

**2. Crie o ambiente e instale as dependências**

Windows:
```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Linux ou Mac:
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

**3. Edite o arquivo `.env`**, mudando duas linhas:
- `DJANGO_DEBUG=False` → `DJANGO_DEBUG=True`
- `# DB_ENGINE=sqlite` → `DB_ENGINE=sqlite`

**4. Crie o banco e rode**
```bash
python manage.py migrate
python manage.py loaddata inicial.json
python manage.py runserver
```

Acesse http://127.0.0.1:8000.

**Usuários de teste**

| Perfil | Telefone | Senha |
| --- | --- | --- |
| Cliente | `15900020002` | `cliente` |
| Barbeiro (cortefino) | `11900010001` | `agenda@123` |
| Barbeiro (Barbeiroteste) | `11922223333` | `ad123` |

Ao trocar de branch, apague o `db.sqlite3` e rode de novo o `migrate` e o `loaddata`, porque cada branch pode ter migrações diferentes.

## 🤝 Como a equipe trabalha

- O **GitHub é a única fonte do código**. Só o responsável pelo servidor atualiza a VM da Oracle, a partir do branch `integracao-oracle`.
- Sempre `git pull` antes de começar, e traga o `integracao-oracle` para o branch da sua equipe com `git merge origin/integracao-oracle`.
- Cada equipe trabalha no seu branch (`equipe-barbeiro`, `equipe-cliente`, `equipe-agendamento`) e envia as mudanças por pull request para o `integracao-oracle`.
- Mudanças no `models.py` são combinadas no grupo antes. Quem altera um model gera a migração e envia as duas coisas juntas.
- Status de agendamento: use só `pendente`, `confirmado`, `execucao`, `concluido` e `cancelado`.
- Nunca envie o `.env`, a pasta `venv` ou o `db.sqlite3`.

## 📸 Demonstração do Sistema

### Tela de Login (Cliente / Barbeiro)
![Tela de Login do Usuário/Barbeiro](screenshots/Tela_login.png)

### Tela de Cadastro (Usuário)
![Tela de Cadastro](screenshots/Tela_cadastro.png)
