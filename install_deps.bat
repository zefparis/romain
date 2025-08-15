@echo off
echo 📦 Installation des dépendances Romain Assistant...
echo.

echo 🔧 Installation des packages Python essentiels...
pip install pydantic-settings
pip install openai
pip install jinja2
pip install reportlab
pip install python-docx
pip install openpyxl
pip install pandas
pip install weasyprint
pip install docxtpl
pip install xlsxwriter
pip install httpx
pip install tenacity
pip install sqlalchemy
pip install asyncpg
pip install psycopg[binary]
pip install pgvector
pip install redis
pip install rq
pip install boto3

echo.
echo ✅ Installation terminée!
echo.
echo 🚀 Tentative de démarrage du serveur...
cd apps\api
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

pause
