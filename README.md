# 💈 Agenda Aí - Sistema de Agendamento para Barbearia

Projeto Integrador (PI) da **Univesp**. Aplicação web em **Python/Django** para agendamento de horários em barbearia: o cliente escolhe o serviço, a data, o barbeiro e o horário, e o barbeiro administra a própria agenda.

🌐 **Aplicação no ar:** http://147.15.102.248

## 🚀 Funcionalidades

**Cliente**
- **Cadastro e login** por telefone e senha
- **Agendamento em etapas:** serviço → data → barbeiro → horário → confirmação. Só aparecem os barbeiros que atendem na data escolhida e os horários livres, buscados no servidor com JavaScript, sem recarregar a página
- **Meus agendamentos:** ver detalhes, editar e cancelar
- **Atualização em tempo real:** quando o barbeiro muda o status, a tela do cliente se atualiza sozinha
- **Calendário limitado:** de hoje até 30 dias à frente, sem horários que já passaram

**Barbeiro**
- **Quadro de agendamentos** em 4 colunas (Pendente, Confirmado, Em execução, Concluído), movidos arrastando com o mouse e com filtro por data
- **Agendamento manual:** para cliente cadastrado (busca pelo telefone) ou cliente avulso, sem cadastro
- **Ver, editar e excluir** agendamentos
- **Escala de trabalho (tela Gerência):** dias de trabalho, horário de início e fim e dias de folga. Barbeiro que ainda não configurou atende de segunda a sábado, das 8h às 18h
- **Atualização em tempo real:** novos agendamentos e cancelamentos aparecem no quadro sem recarregar a página

**Acessibilidade**
- Botões A-, A e A+ em todas as telas para ajustar o tamanho da letra, com a escolha lembrada pelo navegador

## 🛠️ Tecnologias

| Camada | Tecnologia |
| --- | --- |
| Backend | Python 3 e Django 4.2 |
| Frontend | HTML5, CSS3, JavaScript, jQuery, SortableJS e FontAwesome |
| Tempo real | Server-Sent Events (SSE) |
| Banco de dados | MySQL 8.0 no servidor; SQLite no desenvolvimento local |
| Servidor | Docker Compose, Gunicorn (workers com threads) e Nginx numa VM da Oracle Cloud |

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

**Usuários de teste** (só no ambiente local, carregados pelo `inicial.json`)

| Perfil | Telefone | Senha |
| --- | --- | --- |
| Cliente | `15900020002` | `cliente` |
| Barbeiro (cortefino) | `11900010001` | `agenda@123` |
| Barbeiro (Barbeiroteste) | `11922223333` | `ad123` |

Ao trocar de branch, apague o `db.sqlite3` e rode de novo o `migrate` e o `loaddata`, porque cada branch pode ter migrações diferentes.

## ✅ Testes automáticos

O projeto tem 30 testes cobrindo agendamento, cancelamento, busca de barbeiros e horários, e as telas do barbeiro:

```bash
python manage.py test agenda
```

## 🤝 Como a equipe trabalha

- O **GitHub é a única fonte do código**. Só o responsável pelo servidor atualiza a VM da Oracle, a partir do branch `integracao-oracle`.
- Sempre `git pull` antes de começar, e traga o `integracao-oracle` para o branch da sua equipe com `git merge origin/integracao-oracle`.
- Cada equipe trabalha no seu branch e envia as mudanças por pull request para o `integracao-oracle`.
- Mudanças no `models.py` são combinadas no grupo antes. Quem altera um model gera a migração e envia as duas coisas juntas.
- Status de agendamento: use só `pendente`, `confirmado`, `execucao`, `concluido` e `cancelado`.
- Nunca envie o `.env`, a pasta `venv` ou o `db.sqlite3`.

## 🚢 Atualização do servidor (responsável pela VM)

```bash
cd ~/barbearia
bash ~/backup-barbearia.sh        # backup do banco antes de tudo
git pull
docker compose up -d --build      # reconstrói e aplica as migrações
docker compose logs web --tail=40 # conferir: migrações OK e "Using worker: gthread"
```

O servidor tem um **banco próprio**, separado dos dados de teste. Nunca rode `loaddata inicial.json` no servidor: ele sobrescreveria clientes e barbeiros reais. Dados obrigatórios (como os serviços) devem ser cadastrados pelo `/admin`, pelo shell do Django ou por uma migração de dados.

## 📸 Demonstração do Sistema

### Tela de Login (Cliente / Barbeiro)
![Tela de Login do Usuário/Barbeiro](<img width="1804" height="952" alt="image" src="https://github.com/user-attachments/assets/60393bc7-eecc-4fbe-b4da-32f1c7d40449" />)

### Tela de Cadastro (Usuário)
![Tela de Cadastro](<img width="1804" height="952" alt="image" src="https://github.com/user-attachments/assets/49bc34fa-3267-45a7-999c-f5fd0c4fc985" />)
