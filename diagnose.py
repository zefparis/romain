# -*- coding: utf-8 -*-
"""
Script de diagnostic pour identifier les problèmes de serveur
"""
import sys
import socket
import subprocess
import os
from pathlib import Path

def check_python():
    """Vérifie la version de Python"""
    print(f"🐍 Python: {sys.version}")
    return True

def check_packages():
    """Vérifie les packages installés"""
    packages = ['fastapi', 'uvicorn', 'python-dotenv']
    missing = []
    
    for package in packages:
        try:
            __import__(package)
            print(f"✅ {package}: Installé")
        except ImportError:
            print(f"❌ {package}: Manquant")
            missing.append(package)
    
    return missing

def check_ports():
    """Vérifie les ports disponibles"""
    ports = [8000, 8001, 5173, 3000]
    available = []
    
    for port in ports:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex(('127.0.0.1', port))
            sock.close()
            
            if result != 0:
                print(f"✅ Port {port}: Disponible")
                available.append(port)
            else:
                print(f"❌ Port {port}: Occupé")
        except Exception as e:
            print(f"⚠️  Port {port}: Erreur - {e}")
    
    return available

def check_files():
    """Vérifie les fichiers nécessaires"""
    files = [
        'apps/api/app/main.py',
        'apps/api/requirements.txt',
        'apps/api/.env',
        'apps/web/package.json'
    ]
    
    for file_path in files:
        full_path = Path(file_path)
        if full_path.exists():
            print(f"✅ {file_path}: Existe")
        else:
            print(f"❌ {file_path}: Manquant")

def install_missing_packages(missing_packages):
    """Installe les packages manquants"""
    if not missing_packages:
        return True
    
    print(f"\n📦 Installation des packages manquants: {', '.join(missing_packages)}")
    try:
        cmd = [sys.executable, '-m', 'pip', 'install'] + missing_packages
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Installation réussie")
            return True
        else:
            print(f"❌ Erreur d'installation: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Erreur lors de l'installation: {e}")
        return False

def start_minimal_server():
    """Démarre un serveur minimal pour tester"""
    try:
        import uvicorn
        from fastapi import FastAPI
        
        app = FastAPI(title="Test Romain Assistant")
        
        @app.get("/")
        def read_root():
            return {"message": "Serveur de test fonctionnel!", "status": "ok"}
        
        @app.get("/health")
        def health_check():
            return {"ok": True, "message": "Test réussi"}
        
        print("\n🚀 Démarrage du serveur de test...")
        print("📍 URL: http://127.0.0.1:8000")
        print("🔗 Test: http://127.0.0.1:8000/health")
        
        uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")
        
    except Exception as e:
        print(f"❌ Erreur lors du démarrage: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Fonction principale de diagnostic"""
    print("🔍 DIAGNOSTIC SERVEUR ROMAIN ASSISTANT")
    print("=" * 50)
    
    # Vérifications
    print("\n1️⃣ Vérification Python:")
    check_python()
    
    print("\n2️⃣ Vérification des packages:")
    missing = check_packages()
    
    print("\n3️⃣ Vérification des ports:")
    available_ports = check_ports()
    
    print("\n4️⃣ Vérification des fichiers:")
    check_files()
    
    # Installation des packages manquants
    if missing:
        install_missing_packages(missing)
        print("\n5️⃣ Re-vérification des packages:")
        missing = check_packages()
    
    # Démarrage du serveur de test
    if not missing and available_ports:
        print("\n6️⃣ Test du serveur:")
        input("Appuyez sur Entrée pour démarrer le serveur de test...")
        start_minimal_server()
    else:
        print("\n❌ Impossible de démarrer le serveur:")
        if missing:
            print(f"   - Packages manquants: {', '.join(missing)}")
        if not available_ports:
            print("   - Aucun port disponible")

if __name__ == "__main__":
    main()
