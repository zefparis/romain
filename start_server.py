# -*- coding: utf-8 -*-
"""
Script de démarrage simple pour le serveur FastAPI
"""
import uvicorn
import os
import sys

# Ajouter le répertoire API au path
api_path = os.path.join(os.path.dirname(__file__), 'apps', 'api')
sys.path.insert(0, api_path)

if __name__ == "__main__":
    print("🚀 Démarrage du serveur Romain Assistant...")
    print("📍 API sera disponible sur: http://127.0.0.1:8000")
    print("📖 Documentation sur: http://127.0.0.1:8000/docs")
    print("⏹️  Appuyez sur Ctrl+C pour arrêter")
    print("-" * 50)
    
    try:
        uvicorn.run(
            "app.main:app",
            host="127.0.0.1",
            port=8000,
            reload=True,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n👋 Serveur arrêté par l'utilisateur")
    except Exception as e:
        print(f"❌ Erreur lors du démarrage: {e}")
        import traceback
        traceback.print_exc()
