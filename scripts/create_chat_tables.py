#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script pour créer les tables du chat interne
"""

import sys
from pathlib import Path

# Ajouter le répertoire parent au path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app import app, db
from models import ChatRoom, ChatRoomMember, ChatMessage, ChatAttachment, ChatMessageRead

def create_chat_tables():
    """Créer les tables du chat si elles n'existent pas"""
    with app.app_context():
        try:
            print("🔄 Création des tables du chat interne...")
            
            # Créer toutes les tables (SQLAlchemy détectera automatiquement les modèles)
            db.create_all()
            
            print("✅ Tables du chat créées avec succès!")
            print("\nTables créées:")
            print("  - chat_rooms")
            print("  - chat_room_members")
            print("  - chat_messages")
            print("  - chat_attachments")
            print("  - chat_message_reads")
            
            return True
        except Exception as e:
            print(f"❌ Erreur lors de la création des tables: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == '__main__':
    success = create_chat_tables()
    sys.exit(0 if success else 1)

