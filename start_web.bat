@echo off
echo 🎨 Démarrage du serveur Romain Assistant Web...
echo.
cd apps\web
echo 📍 Répertoire: %CD%
echo 📍 Web sera disponible sur: http://127.0.0.1:5173
echo ⏹️  Appuyez sur Ctrl+C pour arrêter
echo.
npm run dev
pause
