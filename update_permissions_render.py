#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script Python pour mettre à jour les permissions du rôle magasinier sur Render
À exécuter directement dans le Shell Render: python3 update_permissions_render.py
"""

import sys
import os

# Configuration du path pour Render
if os.path.exists('/opt/render/project/src'):
    # Sur Render
    sys.path.insert(0, '/opt/render/project/src')
else:
    # Localement
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from app import app, db
    from models import Role
except ImportError as e:
    print(f"❌ Erreur d'import: {e}")
    print("   Assurez-vous d'être dans le bon répertoire")
    sys.exit(1)

def update_warehouse_permissions():
    """Met à jour toutes les permissions du rôle magasinier"""
    
    with app.app_context():
        print("=" * 70)
        print("MISE À JOUR DES PERMISSIONS DU RÔLE MAGASINIER")
        print("=" * 70)
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
        print(f"📋 Permissions actuelles: {len(current_perms)} modules")
        if current_perms:
            for module, actions in sorted(current_perms.items()):
                print(f"   - {module}: {actions}")
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
        updated_perms = current_perms.copy() if isinstance(current_perms, dict) else {}
        
        print("🔄 Analyse et mise à jour des permissions:")
        print("-" * 70)
        
        changes_made = False
        for module, actions in required_permissions.items():
            if module not in updated_perms:
                updated_perms[module] = actions
                print(f"✅ {module}: AJOUTÉ {actions}")
                changes_made = True
            else:
                # Fusionner les actions (garder les existantes, ajouter les manquantes)
                existing_actions = updated_perms[module] if isinstance(updated_perms[module], list) else []
                if not isinstance(existing_actions, list):
                    existing_actions = []
                
                new_actions = [a for a in actions if a not in existing_actions]
                if new_actions:
                    updated_perms[module] = list(set(existing_actions + actions))
                    print(f"✅ {module}: Actions ajoutées: {new_actions} (avait: {existing_actions})")
                    changes_made = True
                else:
                    print(f"ℹ️  {module}: Déjà complet ({existing_actions})")
        
        print()
        
        if not changes_made:
            print("ℹ️  Aucune modification nécessaire. Toutes les permissions sont déjà à jour.")
            print()
            print("📋 Permissions actuelles (complètes):")
            for module, actions in sorted(updated_perms.items()):
                print(f"   - {module}: {actions}")
            return True
        
        # Mettre à jour dans la base de données
        try:
            print("💾 Sauvegarde dans la base de données...")
            warehouse_role.permissions = updated_perms
            db.session.commit()
            
            print()
            print("=" * 70)
            print("✅ PERMISSIONS MISES À JOUR AVEC SUCCÈS")
            print("=" * 70)
            print()
            print("📋 Nouvelles permissions complètes:")
            print("-" * 70)
            for module, actions in sorted(updated_perms.items()):
                print(f"   ✅ {module}: {actions}")
            print()
            print("🎉 Le magasinier a maintenant accès à toutes les fonctionnalités!")
            print()
            return True
            
        except Exception as e:
            db.session.rollback()
            print()
            print("=" * 70)
            print(f"❌ ERREUR lors de la mise à jour: {e}")
            print("=" * 70)
            import traceback
            traceback.print_exc()
            return False

if __name__ == '__main__':
    try:
        print()
        print("🚀 Démarrage de la mise à jour des permissions...")
        print()
        success = update_warehouse_permissions()
        print()
        if success:
            print("✅ Script terminé avec succès!")
        else:
            print("❌ Script terminé avec des erreurs")
        print()
        sys.exit(0 if success else 1)
    except Exception as e:
        print()
        print("=" * 70)
        print(f"❌ ERREUR FATALE: {e}")
        print("=" * 70)
        import traceback
        traceback.print_exc()
        print()
        sys.exit(1)

