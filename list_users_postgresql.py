#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script pour lister tous les utilisateurs de la base de données PostgreSQL
Utilisable sur Render ou en local
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app import app
from models import db, User, Role, Region
from datetime import datetime

def list_users():
    """Lister tous les utilisateurs avec leurs informations"""
    try:
        with app.app_context():
            print("=" * 80)
            print("📋 LISTE DES UTILISATEURS")
            print("=" * 80)
            print()
            
            # Récupérer tous les utilisateurs avec leurs relations
            users = User.query.order_by(User.created_at.desc(), User.id.desc()).all()
            
            if not users:
                print("❌ Aucun utilisateur trouvé dans la base de données")
                return
            
            # Statistiques
            total = len(users)
            active = sum(1 for u in users if u.is_active)
            inactive = total - active
            
            print(f"📊 Statistiques:")
            print(f"   Total: {total} utilisateur(s)")
            print(f"   Actifs: {active}")
            print(f"   Inactifs: {inactive}")
            print()
            print("=" * 80)
            print()
            
            # Afficher chaque utilisateur
            for i, user in enumerate(users, 1):
                print(f"👤 Utilisateur #{i}")
                print(f"   ID: {user.id}")
                print(f"   Username: {user.username}")
                print(f"   Email: {user.email}")
                print(f"   Nom complet: {user.full_name or 'N/A'}")
                print(f"   Téléphone: {user.phone or 'N/A'}")
                
                # Rôle
                if user.role:
                    print(f"   Rôle: {user.role.name} ({user.role.code})")
                elif user.role_id:
                    print(f"   Rôle ID: {user.role_id} (rôle non trouvé)")
                else:
                    print(f"   Rôle: Aucun")
                
                # Région
                if user.region:
                    print(f"   Région: {user.region.name}")
                elif user.region_id:
                    print(f"   Région ID: {user.region_id} (région non trouvée)")
                else:
                    print(f"   Région: Aucune")
                
                # Statut
                status = "✅ Actif" if user.is_active else "❌ Inactif"
                print(f"   Statut: {status}")
                
                # Mot de passe
                if user.password_hash:
                    pwd_length = len(user.password_hash)
                    if pwd_length >= 20:
                        print(f"   Mot de passe: ✅ Hash présent ({pwd_length} caractères)")
                    else:
                        print(f"   Mot de passe: ⚠️ Hash trop court ({pwd_length} caractères)")
                else:
                    print(f"   Mot de passe: ❌ Aucun hash")
                
                # Dates
                if user.last_login:
                    print(f"   Dernière connexion: {user.last_login.strftime('%Y-%m-%d %H:%M:%S')}")
                else:
                    print(f"   Dernière connexion: Jamais")
                
                if user.created_at:
                    print(f"   Créé le: {user.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
                
                if user.updated_at:
                    print(f"   Modifié le: {user.updated_at.strftime('%Y-%m-%d %H:%M:%S')}")
                
                print()
            
            print("=" * 80)
            print("✅ Liste complète affichée")
            print("=" * 80)
            
    except Exception as e:
        print(f"❌ Erreur lors de la récupération des utilisateurs: {e}")
        import traceback
        traceback.print_exc()
        return False

def list_users_simple():
    """Version simplifiée - tableau compact"""
    try:
        with app.app_context():
            users = User.query.order_by(User.id).all()
            
            if not users:
                print("❌ Aucun utilisateur trouvé")
                return
            
            print("\n📋 LISTE DES UTILISATEURS (Format Tableau)")
            print("=" * 100)
            print(f"{'ID':<5} {'Username':<20} {'Email':<30} {'Rôle':<15} {'Région':<15} {'Statut':<10}")
            print("-" * 100)
            
            for user in users:
                role_name = user.role.name if user.role else "N/A"
                region_name = user.region.name if user.region else "N/A"
                status = "✅ Actif" if user.is_active else "❌ Inactif"
                
                print(f"{user.id:<5} {user.username:<20} {user.email:<30} {role_name:<15} {region_name:<15} {status:<10}")
            
            print("=" * 100)
            print(f"Total: {len(users)} utilisateur(s)")
            
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()

def list_users_by_role():
    """Lister les utilisateurs groupés par rôle"""
    try:
        with app.app_context():
            roles = Role.query.order_by(Role.name).all()
            
            print("\n📋 UTILISATEURS PAR RÔLE")
            print("=" * 80)
            
            for role in roles:
                users = User.query.filter_by(role_id=role.id).all()
                print(f"\n🔹 {role.name} ({role.code}) - {len(users)} utilisateur(s)")
                
                if users:
                    for user in users:
                        status = "✅" if user.is_active else "❌"
                        print(f"   {status} {user.username} ({user.email})")
                else:
                    print("   (Aucun utilisateur)")
            
            # Utilisateurs sans rôle
            users_no_role = User.query.filter_by(role_id=None).all()
            if users_no_role:
                print(f"\n🔹 Sans rôle - {len(users_no_role)} utilisateur(s)")
                for user in users_no_role:
                    status = "✅" if user.is_active else "❌"
                    print(f"   {status} {user.username} ({user.email})")
            
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    import sys
    
    # Vérifier les arguments
    if len(sys.argv) > 1:
        mode = sys.argv[1].lower()
        
        if mode == 'simple':
            list_users_simple()
        elif mode == 'by-role':
            list_users_by_role()
        elif mode == 'help':
            print("Usage:")
            print("  python3 list_users_postgresql.py          # Liste détaillée (par défaut)")
            print("  python3 list_users_postgresql.py simple    # Liste en tableau")
            print("  python3 list_users_postgresql.py by-role  # Liste par rôle")
        else:
            print(f"❌ Mode inconnu: {mode}")
            print("Utilisez: simple, by-role, ou help")
    else:
        # Mode par défaut: liste détaillée
        list_users()

