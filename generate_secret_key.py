#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script pour générer une SECRET_KEY sécurisée pour la production
"""

import secrets

def generate_secret_key():
    """Génère une clé secrète sécurisée"""
    key = secrets.token_urlsafe(32)
    print("=" * 60)
    print("🔐 GÉNÉRATION DE SECRET_KEY")
    print("=" * 60)
    print(f"\nVotre SECRET_KEY :\n")
    print(key)
    print(f"\n" + "=" * 60)
    print("⚠️  IMPORTANT :")
    print("   1. Copiez cette clé et gardez-la secrète")
    print("   2. Ajoutez-la dans les variables d'environnement de Render")
    print("   3. Ne la commitez JAMAIS dans Git")
    print("=" * 60)
    return key

if __name__ == '__main__':
    generate_secret_key()

