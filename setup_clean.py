#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de nettoyage et configuration du projet Import Profit Pro
"""

import os
import sys
import shutil
from pathlib import Path

def clean_project():
    """Nettoyer le projet des fichiers en doublons"""
    print("🧹 Nettoyage du projet...")
    
    # Supprimer les dossiers temporaires
    temp_dirs = ['__pycache__', '.pytest_cache', '.mypy_cache']
    for dir_name in temp_dirs:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
            print(f"✅ Supprimé: {dir_name}")
    
    # Supprimer les fichiers de test
    test_files = [f for f in os.listdir('.') if f.startswith('test_') and f.endswith('.py')]
    for file in test_files:
        os.remove(file)
        print(f"✅ Supprimé: {file}")
    
    # Supprimer les fichiers de backup
    backup_files = [f for f in os.listdir('.') if f.endswith('.sql') or f.endswith('.md')]
    for file in backup_files:
        os.remove(file)
        print(f"✅ Supprimé: {file}")
    
    print("✅ Nettoyage terminé")

def setup_database():
    """Configurer la base de données MySQL"""
    print("🗄️ Configuration de la base de données...")
    
    # Vérifier la connexion MySQL
    try:
        import pymysql
        from config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD_RAW
        
        connection = pymysql.connect(
            host=DB_HOST,
            port=int(DB_PORT),
            user=DB_USER,
            password=DB_PASSWORD_RAW,
            charset='utf8mb4'
        )
        
        print(f"✅ Connexion MySQL réussie: {DB_HOST}:{DB_PORT}")
        
        # Créer la base de données si elle n'existe pas
        with connection.cursor() as cursor:
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            print(f"✅ Base de données '{DB_NAME}' créée/vérifiée")
        
        connection.close()
        return True
        
    except Exception as e:
        print(f"❌ Erreur de connexion MySQL: {e}")
        print("🔄 Utilisation de SQLite en fallback")
        return False

def create_clean_app():
    """Créer une version nettoyée de l'application"""
    print("🚀 Création de l'application nettoyée...")
    
    # Lire le fichier app_unified.py
    with open('app_unified.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Créer une version optimisée
    optimized_content = content.replace(
        "app.run(host='0.0.0.0', port=5001, debug=True)",
        "app.run(host='0.0.0.0', port=5001, debug=False)"
    )
    
    # Écrire la version optimisée
    with open('app_clean.py', 'w', encoding='utf-8') as f:
        f.write(optimized_content)
    
    print("✅ Application nettoyée créée: app_clean.py")

def main():
    """Fonction principale"""
    print("🚀 IMPORT PROFIT PRO - NETTOYAGE ET CONFIGURATION")
    print("=" * 60)
    
    # Nettoyer le projet
    clean_project()
    
    # Configurer la base de données
    db_connected = setup_database()
    
    # Créer l'application nettoyée
    create_clean_app()
    
    print("=" * 60)
    print("✅ PROJET NETTOYÉ ET CONFIGURÉ")
    print("🌐 Base de données:", "MySQL" if db_connected else "SQLite")
    print("📁 Fichiers nettoyés et optimisés")
    print("🚀 Prêt à démarrer avec: python3 app_clean.py")
    print("=" * 60)

if __name__ == "__main__":
    main()
