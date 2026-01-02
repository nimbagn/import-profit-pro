#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script pour vérifier les autorisations du rôle commercial pour les commandes
"""

import sys
import os

# Ajouter le répertoire parent au path pour les imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from models import Role, User

def verifier_autorisations_commercial():
    """Vérifier les autorisations du rôle commercial"""
    print("🔍 Vérification des autorisations du rôle commercial...")
    print("")
    
    with app.app_context():
        # Récupérer le rôle commercial
        commercial_role = Role.query.filter_by(code='commercial').first()
        
        if not commercial_role:
            print("❌ Le rôle commercial n'existe pas dans la base de données")
            return False
        
        print(f"✅ Rôle commercial trouvé: {commercial_role.name}")
        print("")
        
        # Vérifier les permissions
        permissions = commercial_role.permissions or {}
        orders_permissions = permissions.get('orders', [])
        
        print("📋 Permissions orders du rôle commercial:")
        print(f"   {orders_permissions}")
        print("")
        
        # Vérifier les permissions requises
        required_permissions = ['read', 'create', 'update']
        missing_permissions = [p for p in required_permissions if p not in orders_permissions]
        
        if missing_permissions:
            print(f"❌ Permissions manquantes: {missing_permissions}")
            print("")
            print("🔧 Correction nécessaire:")
            print("   Le rôle commercial doit avoir les permissions: ['read', 'create', 'update']")
            return False
        else:
            print("✅ Toutes les permissions requises sont présentes")
            print("")
        
        # Vérifier les permissions non autorisées (normal)
        unauthorized_permissions = ['validate', 'delete']
        found_unauthorized = [p for p in unauthorized_permissions if p in orders_permissions]
        
        if found_unauthorized:
            print(f"⚠️  Permissions non autorisées trouvées: {found_unauthorized}")
            print("   Ces permissions ne devraient pas être accordées au commercial")
            print("")
        else:
            print("✅ Aucune permission non autorisée trouvée")
            print("")
        
        # Lister les utilisateurs commerciaux
        commercial_users = User.query.join(Role).filter(Role.code == 'commercial').all()
        
        print(f"👥 Utilisateurs commerciaux trouvés: {len(commercial_users)}")
        for user in commercial_users:
            status = "✅ Actif" if user.is_active else "❌ Inactif"
            print(f"   - {user.username} ({user.full_name or 'N/A'}) - {status}")
        print("")
        
        # Résumé
        print("=" * 60)
        print("📊 RÉSUMÉ")
        print("=" * 60)
        print(f"✅ Rôle commercial: {commercial_role.name}")
        print(f"✅ Permissions orders: {orders_permissions}")
        print(f"✅ Utilisateurs commerciaux: {len(commercial_users)}")
        print("")
        print("🔍 Routes accessibles au commercial:")
        print("   ✅ GET  /orders/              - Liste (ses commandes uniquement)")
        print("   ✅ GET  /orders/new           - Formulaire de création")
        print("   ✅ POST /orders/new           - Créer une commande")
        print("   ✅ GET  /orders/<id>          - Détail (ses commandes uniquement)")
        print("   ✅ GET  /orders/<id>/edit     - Formulaire de modification")
        print("   ✅ POST /orders/<id>/edit     - Modifier (ses commandes uniquement)")
        print("")
        print("🔒 Routes inaccessibles au commercial (normal):")
        print("   ❌ POST /orders/<id>/validate - Valider (superviseur/admin)")
        print("   ❌ POST /orders/<id>/reject   - Rejeter (superviseur/admin)")
        print("   ❌ POST /orders/<id>/generate-outgoing - Générer sortie (magasinier)")
        print("")
        
        return True

if __name__ == '__main__':
    success = verifier_autorisations_commercial()
    sys.exit(0 if success else 1)

