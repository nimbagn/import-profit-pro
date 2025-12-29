#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script interactif pour configurer le fichier .env avec les bonnes credentials MySQL
"""

import secrets
import os
import sys

def test_mysql_connection(host, port, user, password, database):
    """Teste la connexion MySQL"""
    try:
        import pymysql
        connection = pymysql.connect(
            host=host,
            port=int(port),
            user=user,
            password=password,
            database=database,
            charset='utf8mb4'
        )
        connection.close()
        return True
    except Exception as e:
        print(f"❌ Erreur de connexion: {e}")
        return False

def create_env_file():
    """Crée le fichier .env avec les credentials MySQL"""
    
    print("=" * 70)
    print("🔧 CONFIGURATION DU FICHIER .env")
    print("=" * 70)
    print()
    
    # Valeurs par défaut
    defaults = {
        'DB_HOST': '127.0.0.1',
        'DB_PORT': '3306',
        'DB_NAME': 'madargn',  # Base de données probable d'après les scripts
        'DB_USER': 'root',
        'DB_PASSWORD': '',
    }
    
    # Demander les valeurs
    print("📝 Entrez les informations MySQL (appuyez sur Entrée pour utiliser les valeurs par défaut):")
    print()
    
    db_host = input(f"🌐 Host MySQL [{defaults['DB_HOST']}]: ").strip() or defaults['DB_HOST']
    db_port = input(f"🔌 Port MySQL [{defaults['DB_PORT']}]: ").strip() or defaults['DB_PORT']
    db_name = input(f"📦 Nom de la base de données [{defaults['DB_NAME']}]: ").strip() or defaults['DB_NAME']
    db_user = input(f"👤 Utilisateur MySQL [{defaults['DB_USER']}]: ").strip() or defaults['DB_USER']
    db_password = input(f"🔐 Mot de passe MySQL (masqué): ").strip() or defaults['DB_PASSWORD']
    
    print()
    print("🔍 Test de la connexion MySQL...")
    
    # Tester la connexion
    if test_mysql_connection(db_host, db_port, db_user, db_password, db_name):
        print(f"✅ Connexion réussie à la base de données '{db_name}'!")
    else:
        print("⚠️  Connexion échouée. Voulez-vous continuer quand même? (o/N): ", end='')
        response = input().strip().lower()
        if response != 'o':
            print("❌ Configuration annulée.")
            return False
    
    # Générer une secret key
    secret_key = secrets.token_urlsafe(32)
    
    # Créer le contenu du fichier .env
    env_content = f"""# Configuration Import Profit Pro
# Généré automatiquement - Modifiez selon vos besoins

# Sécurité - Secret key générée automatiquement
SECRET_KEY={secret_key}

# Base de données MySQL
DB_HOST={db_host}
DB_PORT={db_port}
DB_NAME={db_name}
DB_USER={db_user}
DB_PASSWORD={db_password}

# Configuration Flask
FLASK_DEBUG=1
FLASK_ENV=development

# Cache Redis (optionnel - utilisez 'memory://' si Redis n'est pas installé)
REDIS_URL=memory://
CACHE_TYPE=simple
CACHE_TIMEOUT=3600

# Session (en secondes - 2 heures)
PERMANENT_SESSION_LIFETIME=7200

# Rate Limiting
RATELIMIT_ENABLED=True
RATELIMIT_STORAGE_URL=memory://

# Upload
MAX_CONTENT_MB=25
"""
    
    env_path = '.env'
    
    # Vérifier si le fichier existe déjà
    if os.path.exists(env_path):
        print()
        print(f"⚠️  Le fichier {env_path} existe déjà.")
        response = input("Voulez-vous le remplacer? (o/N): ").strip().lower()
        if response != 'o':
            print("❌ Configuration annulée.")
            return False
    
    # Écrire le fichier
    with open(env_path, 'w') as f:
        f.write(env_content)
    
    print()
    print("=" * 70)
    print("✅ FICHIER .env CRÉÉ AVEC SUCCÈS!")
    print("=" * 70)
    print()
    print(f"📁 Fichier: {os.path.abspath(env_path)}")
    print(f"🔑 Secret key générée automatiquement")
    print(f"🗄️  Base de données: {db_name}")
    print(f"👤 Utilisateur: {db_user}")
    print()
    print("⚠️  IMPORTANT: Le fichier .env contient des informations sensibles.")
    print("   Ne le partagez jamais et ajoutez-le à .gitignore!")
    print()
    
    return True

if __name__ == '__main__':
    try:
        create_env_file()
    except KeyboardInterrupt:
        print("\n\n❌ Configuration annulée par l'utilisateur.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        sys.exit(1)

