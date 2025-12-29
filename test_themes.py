#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de test pour le système de thèmes personnalisables
"""

from app import app
from models import db, User, UserPreference
from werkzeug.security import generate_password_hash

def test_themes_system():
    """Test du système de thèmes"""
    print("🧪 TEST DU SYSTÈME DE THÈMES PERSONNALISABLES")
    print("=" * 60)
    
    with app.app_context():
        # Test 1: Vérifier que le modèle existe
        print("\n1️⃣ Test du modèle UserPreference...")
        try:
            # Vérifier que la table peut être créée
            db.create_all()
            print("   ✅ Table user_preferences peut être créée")
        except Exception as e:
            print(f"   ⚠️ Erreur lors de la création: {e}")
        
        # Test 2: Vérifier qu'un utilisateur peut avoir des préférences
        print("\n2️⃣ Test de création de préférences...")
        try:
            # Chercher un utilisateur existant
            user = User.query.first()
            if user:
                print(f"   ✅ Utilisateur trouvé: {user.username}")
                
                # Vérifier ou créer les préférences
                preference = UserPreference.query.filter_by(user_id=user.id).first()
                if not preference:
                    preference = UserPreference(
                        user_id=user.id,
                        theme_name='hapag-lloyd',
                        color_mode='light'
                    )
                    db.session.add(preference)
                    db.session.commit()
                    print("   ✅ Préférences créées avec succès")
                else:
                    print(f"   ✅ Préférences existantes: thème={preference.theme_name}, mode={preference.color_mode}")
            else:
                print("   ⚠️ Aucun utilisateur trouvé dans la base")
        except Exception as e:
            print(f"   ⚠️ Erreur: {e}")
        
        # Test 3: Vérifier les routes
        print("\n3️⃣ Test des routes...")
        try:
            from themes import themes_bp
            routes = []
            for rule in app.url_map.iter_rules():
                if 'themes' in rule.rule:
                    routes.append(rule.rule)
            
            if routes:
                print("   ✅ Routes trouvées:")
                for route in routes:
                    print(f"      - {route}")
            else:
                print("   ⚠️ Aucune route trouvée")
        except Exception as e:
            print(f"   ⚠️ Erreur: {e}")
        
        # Test 4: Vérifier les fichiers statiques
        print("\n4️⃣ Test des fichiers statiques...")
        import os
        files_to_check = [
            'static/css/themes.css',
            'static/js/themes.js',
            'templates/themes/settings.html'
        ]
        
        for file_path in files_to_check:
            if os.path.exists(file_path):
                size = os.path.getsize(file_path)
                print(f"   ✅ {file_path} ({size} octets)")
            else:
                print(f"   ❌ {file_path} introuvable")
        
        print("\n" + "=" * 60)
        print("✅ Tests terminés!")
        print("\n📝 Pour tester manuellement:")
        print("   1. Démarrez l'application: python app.py")
        print("   2. Connectez-vous")
        print("   3. Allez dans le menu utilisateur → Apparence")
        print("   4. Testez les différents thèmes et modes")

if __name__ == '__main__':
    test_themes_system()

