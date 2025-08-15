@echo off
echo 🔍 DIAGNOSTIC SERVEUR ROMAIN ASSISTANT
echo =====================================
echo.

echo 1️⃣ Vérification Python:
python --version
if errorlevel 1 (
    echo ❌ Python non trouvé
    goto :error
) else (
    echo ✅ Python installé
)
echo.

echo 2️⃣ Vérification pip:
pip --version
if errorlevel 1 (
    echo ❌ pip non trouvé
) else (
    echo ✅ pip installé
)
echo.

echo 3️⃣ Vérification des packages:
pip show fastapi >nul 2>&1
if errorlevel 1 (
    echo ❌ FastAPI manquant - Installation...
    pip install fastapi
) else (
    echo ✅ FastAPI installé
)

pip show uvicorn >nul 2>&1
if errorlevel 1 (
    echo ❌ Uvicorn manquant - Installation...
    pip install uvicorn[standard]
) else (
    echo ✅ Uvicorn installé
)
echo.

echo 4️⃣ Vérification des fichiers:
if exist "apps\api\app\main.py" (
    echo ✅ main.py existe
) else (
    echo ❌ main.py manquant
)

if exist "apps\api\.env" (
    echo ✅ .env existe
) else (
    echo ❌ .env manquant
)
echo.

echo 5️⃣ Test de démarrage du serveur:
echo 📍 Tentative de démarrage sur http://127.0.0.1:8000
echo ⏹️  Appuyez sur Ctrl+C pour arrêter le serveur
echo.
cd apps\api
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

goto :end

:error
echo.
echo ❌ Erreur critique: Python n'est pas installé ou accessible
echo 💡 Veuillez installer Python depuis https://python.org
echo.

:end
pause
