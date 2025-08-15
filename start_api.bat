@echo off
echo 🚀 Démarrage du serveur Romain Assistant API...
echo.
cd apps\api
echo 📍 Répertoire: %CD%
echo 📍 API sera disponible sur: http://127.0.0.1:8000
echo 📖 Documentation sur: http://127.0.0.1:8000/docs
echo ⏹️  Appuyez sur Ctrl+C pour arrêter
echo.
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
pause
