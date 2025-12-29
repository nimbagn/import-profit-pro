#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script pour créer le fichier .env avec une secret key générée
"""

import secrets
import os

def create_env_file():
    """Crée le fichier .env avec une secret key générée"""
    env_content = f"""# Configuration Import Profit Pro
# Généré automatiquement - Modifiez selon vos besoins

# Sécurité - Secret key générée automatiquement
SECRET_KEY={secrets.token_urlsafe(32)}

# Base de données MySQL
DB_HOST=127.0.0.1
DB_PORT=3306
DB_NAME=import_profit
DB_USER=root
DB_PASSWORD=password

# Configuration Flask
FLASK_DEBUG=1
FLASK_ENV=development

# Cache Redis (optionnel - utilisez 'memory://' si Redis n'est pas installé)
REDIS_URL=memory://
CACHE_TYPE=simple

# Session (en secondes - 2 heures)
PERMANENT_SESSION_LIFETIME=7200

# Rate Limiting
RATELIMIT_ENABLED=True
RATELIMIT_STORAGE_URL=memory://

# Upload
MAX_CONTENT_MB=25
"""
    
    env_path = '.env'
    
    if os.path.exists(env_path):
        print(f"⚠️  Le fichier {env_path} existe déjà.")
        response = input("Voulez-vous le remplacer? (o/N): ")
        if response.lower() != 'o':
            print("Annulé.")
            return
    
    with open(env_path, 'w') as f:
        f.write(env_content)
    
    print(f"✅ Fichier {env_path} créé avec succès!")
    print(f"🔑 Secret key générée automatiquement")
    print(f"\n⚠️  IMPORTANT: Modifiez les valeurs dans .env selon votre configuration")

if __name__ == '__main__':
    create_env_file()

