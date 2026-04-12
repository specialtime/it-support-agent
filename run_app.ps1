$ErrorActionPreference = "Stop"

$pythonPath = "C:\Users\crist\AppData\Local\Programs\Python\Python310\python.exe"

Write-Host "Iniciando FastAPI Backend (uvicorn)..."
Start-Process -FilePath $pythonPath -ArgumentList "-m uvicorn api.main:app --host 0.0.0.0 --port 8000" -PassThru

Write-Host "Pausando 3 segundos para que levante el backend..."
Start-Sleep -Seconds 3

Write-Host "Iniciando Streamlit..."
& $pythonPath -m streamlit run ui/app.py
