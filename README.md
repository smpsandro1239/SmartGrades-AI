# SmartGrades-AI

Aplicação de ambiente de trabalho para Windows para preparar e distribuir documentos escolares individualizados por e-mail, com validação, pré-visualização e histórico.

> **Plataforma de execução:** Windows 11. Esta é uma aplicação desktop Python/CustomTkinter, não uma aplicação Web. A Vercel não é utilizada para executar nem publicar esta aplicação.

## Estado do desenvolvimento

A aplicação encontra-se em desenvolvimento. A versão atual inclui:
- Interface gráfica inicial com CustomTkinter.
- Base de dados SQLite inicial.
- Importação e validação de ficheiros Excel (.xlsx/.xlsm) e CSV através do serviço de importação.
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

## Executar em modo de desenvolvimento

Requisitos: Windows 11 e Python 3.11 ou superior.

```powershell
git clone https://github.com/smpsandro1239/SmartGrades-AI.git
cd SmartGrades-AI
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python app.py
```

## Gerar o executável Windows

Com Python 3.11 instalado, abre PowerShell na pasta do projeto e executa:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\build_windows.ps1
```

O script instala as dependências de compilação, executa os testes e só gera o executável se os testes passarem. O ficheiro será criado em:

`dist\SmartGrades-AI.exe`

O executável é gerado para Windows x64. Para o utilizar noutro computador, copia o EXE para esse computador. Não é necessário instalar Python nesse computador.

### Gerar automaticamente através do GitHub

1. Abre o separador **Actions** deste repositório.
2. Seleciona **Build Windows EXE**.
3. Clica em **Run workflow** e escolhe a branch pretendida.
4. Aguarda que os testes e a compilação terminem com sucesso.
5. Abre a execução concluída e descarrega o artefacto `SmartGrades-AI-Windows-x64`.
6. Extrai o ZIP e executa `SmartGrades-AI.exe` no Windows.

Também é gerado um executável quando é publicada uma tag cujo nome começa por `v`, por exemplo `v0.1.0`. Em Pull Requests para `main`, o workflow executa os testes, mas não publica o executável.

## Localização dos dados da aplicação

A base de dados e os registos são guardados fora da pasta temporária do PyInstaller, em:

`%LOCALAPPDATA%\SmartGrades-AI\runtime_data\`

Esta localização permite que os dados persistam entre execuções do EXE. Faz cópias de segurança desta pasta quando começar a conter dados importantes.

## Testes

```powershell
python -m pip install -r requirements.txt
python -m pytest -q
```

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
