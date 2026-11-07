# SmartGrades-AI

Sistema de gestão de classificações escolares e distribuição individualizada de notificações por e-mail.

## Estado atual

Versão inicial em desenvolvimento. Inclui:
- Interface gráfica inicial com CustomTkinter.
- Base de dados SQLite com tabelas de alunos, classificações e histórico de e-mails.
- Modo de envio predefinido em **simulação**; a aplicação não envia e-mails nesta fase.
- Regras de exclusão para impedir a publicação acidental de credenciais, tokens e dados escolares.

## Requisitos

- Windows 11 (ou outro sistema compatível com Python).
- Python 3.11 ou superior recomendado.

## Instalação

1. Clonar o repositório:
   `git clone https://github.com/smpsandro1239/SmartGrades-AI.git`
2. Entrar na pasta:
   `cd SmartGrades-AI`
3. Criar e ativar um ambiente virtual:
   `py -m venv .venv`
   `..venv\Scripts\Activate.ps1`
4. Instalar dependências:
   `python -m pip install --upgrade pip`
   `pip install -r requirements.txt`
5. Iniciar:
   `python app.py`

A base de dados local é criada automaticamente em `runtime_data/` na primeira execução.

## Testes

Executar:
`python -m pytest`

## Segurança e privacidade

- Não adicionar ao GitHub ficheiros de alunos, classificações, exportações, bases de dados reais ou registos com dados pessoais.
- Não adicionar `credentials.json`, `token.json`, segredos OAuth ou ficheiros `.env`.
- A integração Gmail será feita com OAuth 2.0; nunca serão guardadas palavras-passe.
- O envio real permanecerá desativado até existirem validação de destinatários, pré-visualização, confirmação explícita e registo de auditoria.
- Antes de usar dados reais, confirmar as regras e a base legal aplicáveis na instituição de ensino.

## Licença

Ainda não definida.
