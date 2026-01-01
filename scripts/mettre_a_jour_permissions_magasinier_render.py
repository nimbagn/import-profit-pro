#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script pour mettre à jour les permissions du rôle magasinier dans la base de données
À exécuter sur Render ou localement
"""

import sys
import os

# Ajouter le répertoire parent au path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from models import Role

def update_warehouse_permissions():
    """Met à jour toutes les permissions du rôle magasinier"""
    
    with app.app_context():
        print("=" * 60)
        print("MISE À JOUR DES PERMISSIONS DU RÔLE MAGASINIER")
        print("=" * 60)
        print()
        
        # Récupérer le rôle magasinier
        warehouse_role = Role.query.filter_by(code='warehouse').first()
        
        if not warehouse_role:
            print("❌ ERREUR: Le rôle magasinier (warehouse) n'existe pas")
            print("   Veuillez d'abord créer le rôle via l'interface d'administration")
            return False
        
        print(f"✅ Rôle trouvé: {warehouse_role.name} (ID: {warehouse_role.id})")
        
        # Permissions actuelles
        current_perms = warehouse_role.permissions or {}
        print(f"📋 Permissions actuelles: {current_perms}")
        print()
        
        # Permissions complètes requises
        required_permissions = {
            'stocks': ['read', 'create', 'update'],
            'movements': ['read', 'create'],
            'inventory': ['read', 'create', 'update'],
            'receptions': ['read', 'create', 'update'],
            'outgoings': ['read', 'create', 'update'],
            'returns': ['read', 'create', 'update'],
            'vehicles': ['read'],
            'regions': ['read'],
            'depots': ['read'],
            'families': ['read'],
            'stock_items': ['read'],
            'orders': ['read'],
            'stock_loading': ['read', 'verify', 'load']
        }
        
        # Fusionner les permissions (garder les existantes, ajouter les manquantes)
        updated_perms = current_perms.copy()
        
        print("🔄 Mise à jour des permissions:")
        print("-" * 60)
        
        changes_made = False
        for module, actions in required_permissions.items():
            if module not in updated_perms:
                updated_perms[module] = actions
                print(f"✅ {module}: Ajouté {actions}")
                changes_made = True
            else:
                # Fusionner les actions (garder les existantes, ajouter les manquantes)
                existing_actions = updated_perms[module] if isinstance(updated_perms[module], list) else []
                new_actions = [a for a in actions if a not in existing_actions]
                if new_actions:
                    updated_perms[module] = list(set(existing_actions + actions))
                    print(f"✅ {module}: Actions ajoutées: {new_actions}")
                    changes_made = True
                else:
                    print(f"ℹ️  {module}: Déjà complet ({existing_actions})")
        
        print()
        
        if not changes_made:
            print("ℹ️  Aucune modification nécessaire. Toutes les permissions sont déjà à jour.")
            return True
        
        # Mettre à jour dans la base de données
        try:
            warehouse_role.permissions = updated_perms
            db.session.commit()
            
            print("=" * 60)
            print("✅ PERMISSIONS MISES À JOUR AVEC SUCCÈS")
            print("=" * 60)
            print()
            print("📋 Nouvelles permissions:")
            for module, actions in sorted(updated_perms.items()):
                print(f"   - {module}: {actions}")
            print()
            
            return True
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ ERREUR lors de la mise à jour: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == '__main__':
    try:
        success = update_warehouse_permissions()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"❌ ERREUR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

