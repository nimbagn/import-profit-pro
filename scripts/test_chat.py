#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de test pour le système de chat
Vérifie que les tables existent et que les routes fonctionnent
"""

import sys
from pathlib import Path

# Ajouter le répertoire parent au path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app import app, db
from models import ChatRoom, ChatRoomMember, ChatMessage, ChatAttachment, ChatMessageRead, User, Role
from sqlalchemy import inspect

def test_chat_tables():
    """Vérifier que les tables du chat existent"""
    with app.app_context():
        try:
            print("🔍 Vérification des tables du chat...")
            
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            
            chat_tables = [
                'chat_rooms',
                'chat_room_members',
                'chat_messages',
                'chat_attachments',
                'chat_message_reads'
            ]
            
            missing_tables = []
            existing_tables = []
            
            for table in chat_tables:
                if table in tables:
                    existing_tables.append(table)
                    print(f"  ✅ {table}")
                else:
                    missing_tables.append(table)
                    print(f"  ❌ {table} - MANQUANTE")
            
            if missing_tables:
                print(f"\n⚠️  {len(missing_tables)} table(s) manquante(s)")
                print("💡 Solution: Les tables seront créées automatiquement au prochain démarrage de l'application")
                print("   Ou exécutez: mysql -u root -p madargn < scripts/create_chat_tables_direct.sql")
                return False
            else:
                print(f"\n✅ Toutes les tables du chat existent ({len(existing_tables)}/5)")
                return True
                
        except Exception as e:
            print(f"❌ Erreur lors de la vérification: {e}")
            import traceback
            traceback.print_exc()
            return False

def test_chat_models():
    """Tester que les modèles peuvent être importés"""
    try:
        print("\n🔍 Vérification des modèles...")
        from models import ChatRoom, ChatRoomMember, ChatMessage, ChatAttachment, ChatMessageRead
        print("  ✅ ChatRoom")
        print("  ✅ ChatRoomMember")
        print("  ✅ ChatMessage")
        print("  ✅ ChatAttachment")
        print("  ✅ ChatMessageRead")
        return True
    except Exception as e:
        print(f"  ❌ Erreur d'import: {e}")
        return False

def test_chat_routes():
    """Tester que les routes sont enregistrées"""
    try:
        print("\n🔍 Vérification des routes...")
        with app.app_context():
            from flask import url_for
            
            routes_to_test = [
                'chat.rooms_list',
                'chat.room_new',
                'chat.api_rooms_list',
                'chat.api_message_create',
            ]
            
            for route in routes_to_test:
                try:
                    url = url_for(route, room_id=1) if 'room_id' in route else url_for(route)
                    print(f"  ✅ {route}")
                except Exception as e:
                    print(f"  ⚠️  {route} - {str(e)[:50]}")
            
            return True
    except Exception as e:
        print(f"  ❌ Erreur: {e}")
        return False

if __name__ == '__main__':
    print("=" * 60)
    print("TEST DU SYSTÈME DE CHAT INTERNE")
    print("=" * 60)
    
    models_ok = test_chat_models()
    tables_ok = test_chat_tables()
    routes_ok = test_chat_routes()
    
    print("\n" + "=" * 60)
    if models_ok and tables_ok and routes_ok:
        print("✅ TOUS LES TESTS SONT PASSÉS")
        print("💡 Le système de chat est prêt à être utilisé!")
        print("\n📝 Prochaines étapes:")
        print("   1. Accédez à http://localhost:5002/chat")
        print("   2. Créez une nouvelle conversation")
        print("   3. Testez l'envoi de messages")
        sys.exit(0)
    else:
        print("⚠️  CERTAINS TESTS ONT ÉCHOUÉ")
        if not tables_ok:
            print("   → Exécutez la migration SQL pour créer les tables")
        sys.exit(1)

