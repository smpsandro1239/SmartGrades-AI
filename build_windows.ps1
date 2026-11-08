$ErrorActionPreference = "Stop"

Write-Host "[1/4] A preparar o ambiente..."
if (-not (Test-Path ".venv")) {
    py -3.11 -m venv .venv
}
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements-build.txt

Write-Host "[2/4] A executar os testes..."
.\.venv\Scripts\python.exe -m pytest

Write-Host "[3/4] A gerar SmartGrades-AI.exe..."
.\.venv\Scripts\python.exe -m PyInstaller --noconfirm --clean --onefile --windowed --name SmartGrades-AI --collect-all customtkinter --collect-all darkdetect app.py

Write-Host "[4/4] Concluído."
Write-Host "Executável: $((Resolve-Path 'dist\SmartGrades-AI.exe').Path)"
