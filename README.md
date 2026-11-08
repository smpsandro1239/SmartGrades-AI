# SmartGrades-AI

Sistema Windows para preparar e distribuir documentos escolares individualizados por e-mail, com validação, pré-visualização e histórico.

## Estado do desenvolvimento

A aplicação encontra-se em desenvolvimento. A versão atual inclui:
- Interface gráfica inicial com CustomTkinter.
- Base de dados SQLite inicial.
- Importação e validação de ficheiros Excel (.xlsx/.xlsm) e CSV.
- Colunas obrigatórias: `E-mail`, `ID_Aluno` e `Escola`.
- Localização do documento Word `.docx` através de `documents/<Escola>/<ID_Aluno>.docx`.
- Preparação de pré-visualização HTML individual.
- Testes iniciais para validação de importação e correspondência dos documentos.
- Envio de e-mails mantido desativado; a aplicação não envia mensagens nesta fase.

## Estrutura esperada dos documentos

Coloca os documentos localmente (não os envies para o GitHub):

```text
documents/
├── Escola A/
│   ├── 12345.docx
│   └── 12346.docx
└── Escola B/
    └── 54321.docx
```

O nome do ficheiro deve ser exatamente o ID do aluno, com extensão `.docx`. O nome da pasta deve corresponder ao valor da coluna `Escola`.

## Modelo do ficheiro de alunos

Consulta `docs/modelo_alunos.csv` para um exemplo. No Excel, cria uma folha com estas três colunas:

| E-mail | ID_Aluno | Escola |
|---|---|---|
| encarregado@example.com | 12345 | Escola A |

Cada ID deve ser único no ficheiro. Cada linha deve ter um e-mail válido, um ID e uma escola.

## Instalação

Requisitos: Windows 11 e Python 3.11 ou superior.

```powershell
git clone https://github.com/smpsandro1239/SmartGrades-AI.git
cd SmartGrades-AI
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python app.py
```

## Testes

```powershell
python -m pytest
```

Os testes devem ser executados no ambiente Windows de destino antes de usar dados reais.

## Segurança e privacidade

- Não adicionar ao GitHub ficheiros de alunos, classificações, documentos Word, folhas Excel reais, bases de dados ou registos com dados pessoais.
- Não adicionar `credentials.json`, `token.json`, segredos OAuth ou ficheiros `.env`.
- Os documentos e folhas de cálculo devem permanecer no computador autorizado da escola.
- A integração Gmail será feita com OAuth 2.0; nunca serão guardadas palavras-passe.
- O envio real permanecerá desativado até existirem validação completa, pré-visualização, confirmação explícita, limites de envio e registo de auditoria.
- Antes de utilizar dados reais, confirmar as regras e a base legal aplicáveis na instituição de ensino.

## Próximas etapas

1. Integrar a importação e correspondência de documentos na interface gráfica.
2. Apresentar uma grelha de validação com documentos encontrados/em falta.
3. Implementar o modo de simulação e histórico persistente.
4. Integrar Gmail API com OAuth 2.0 e conta de teste.
5. Testar integralmente com destinatários e documentos fictícios.
6. Só depois avaliar a ativação do envio real e a conta institucional Google Workspace.

Licença ainda não definida.
