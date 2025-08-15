# -*- coding: utf-8 -*-
"""
Serveur de test simple pour diagnostiquer les problèmes de connexion
"""
import http.server
import socketserver
import socket
from datetime import datetime

def test_port(port):
    """Teste si un port est disponible"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex(('127.0.0.1', port))
        sock.close()
        return result != 0  # True si le port est libre
    except:
        return False

def start_simple_server():
    """Démarre un serveur HTTP simple"""
    port = 8000
    
    print("🔍 Test de diagnostic du serveur...")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 50)
    
    # Test du port
    if test_port(port):
        print(f"✅ Port {port} est disponible")
    else:
        print(f"❌ Port {port} est déjà utilisé")
        port = 8001
        print(f"🔄 Essai avec le port {port}")
    
    try:
        # Créer un serveur HTTP simple
        handler = http.server.SimpleHTTPRequestHandler
        
        class CustomHandler(handler):
            def do_GET(self):
                if self.path == '/':
                    self.send_response(200)
                    self.send_header('Content-type', 'text/html; charset=utf-8')
                    self.end_headers()
                    html = """
                    <!DOCTYPE html>
                    <html>
                    <head>
                        <meta charset="utf-8">
                        <title>Romain Assistant - Test Server</title>
                    </head>
                    <body>
                        <h1>🚀 Serveur de test Romain Assistant</h1>
                        <p>✅ Le serveur fonctionne correctement!</p>
                        <p>📅 """ + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + """</p>
                        <p>🔗 <a href="/health">Test Health Check</a></p>
                    </body>
                    </html>
                    """
                    self.wfile.write(html.encode('utf-8'))
                elif self.path == '/health':
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    response = '{"status": "ok", "message": "Serveur de test fonctionnel"}'
                    self.wfile.write(response.encode('utf-8'))
                else:
                    super().do_GET()
        
        with socketserver.TCPServer(("127.0.0.1", port), CustomHandler) as httpd:
            print(f"🌐 Serveur démarré sur: http://127.0.0.1:{port}")
            print(f"🔗 Test disponible sur: http://127.0.0.1:{port}/health")
            print("⏹️  Appuyez sur Ctrl+C pour arrêter")
            print("-" * 50)
            httpd.serve_forever()
            
    except KeyboardInterrupt:
        print("\n👋 Serveur arrêté par l'utilisateur")
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    start_simple_server()
