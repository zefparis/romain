# -*- coding: utf-8 -*-
"""
Script pour vérifier l'encodage des fichiers dans le projet
"""
import os
import glob
from pathlib import Path

def check_bom(file_path):
    """Vérifie si un fichier contient un BOM UTF-8"""
    try:
        with open(file_path, 'rb') as f:
            first_bytes = f.read(3)
            return first_bytes == b'\xef\xbb\xbf'
    except Exception as e:
        print(f"Erreur lors de la lecture de {file_path}: {e}")
        return False

def check_utf8_declaration(file_path):
    """Vérifie si un fichier Python contient une déclaration d'encodage UTF-8"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            first_line = f.readline().strip()
            second_line = f.readline().strip()
            
            # Vérifier les deux premières lignes pour la déclaration d'encodage
            encoding_patterns = [
                '# -*- coding: utf-8 -*-',
                '# coding: utf-8',
                '# coding=utf-8'
            ]
            
            return any(pattern in first_line or pattern in second_line 
                      for pattern in encoding_patterns)
    except Exception as e:
        print(f"Erreur lors de la lecture de {file_path}: {e}")
        return False

def main():
    """Fonction principale pour vérifier l'encodage"""
    project_root = Path(__file__).parent
    
    # Extensions de fichiers à vérifier
    extensions = ['*.py', '*.js', '*.jsx', '*.ts', '*.tsx', '*.json', '*.html', '*.css', '*.md']
    
    print("🔍 Vérification de l'encodage des fichiers...")
    print("=" * 50)
    
    bom_files = []
    python_files_without_encoding = []
    
    for ext in extensions:
        for file_path in project_root.rglob(ext):
            # Ignorer les dossiers node_modules, .git, .venv, etc.
            if any(part in str(file_path) for part in ['node_modules', '.git', '.venv', '__pycache__']):
                continue
                
            # Vérifier BOM
            if check_bom(file_path):
                bom_files.append(str(file_path))
            
            # Vérifier déclaration d'encodage pour les fichiers Python
            if file_path.suffix == '.py':
                if not check_utf8_declaration(file_path):
                    python_files_without_encoding.append(str(file_path))
    
    # Rapport
    print(f"📊 Résultats de la vérification:")
    print(f"   - Fichiers avec BOM: {len(bom_files)}")
    print(f"   - Fichiers Python sans déclaration UTF-8: {len(python_files_without_encoding)}")
    
    if bom_files:
        print("\n❌ Fichiers avec BOM détectés:")
        for file_path in bom_files:
            print(f"   - {file_path}")
    
    if python_files_without_encoding:
        print("\n⚠️  Fichiers Python sans déclaration d'encodage UTF-8:")
        for file_path in python_files_without_encoding:
            print(f"   - {file_path}")
    
    if not bom_files and not python_files_without_encoding:
        print("\n✅ Tous les fichiers sont correctement encodés!")
    
    print("\n" + "=" * 50)

if __name__ == "__main__":
    main()
