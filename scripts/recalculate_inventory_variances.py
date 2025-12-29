#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de migration pour recalculer les écarts d'inventaire
Formule corrigée : ÉCART = stock actuel - (QUANTITÉ COMPTÉE + PILE)
"""

import sys
import os
from decimal import Decimal

# Ajouter le répertoire parent au path pour importer les modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configuration de la base de données (même logique que app.py)
try:
    import pymysql
    from config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD_RAW
    
    # Utiliser la variable d'environnement DB_NAME si disponible, sinon utiliser la valeur par défaut
    db_name = os.getenv('DB_NAME', DB_NAME)
    db_uri = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD_RAW}@{DB_HOST}:{DB_PORT}/{db_name}?charset=utf8mb4"
    print(f"✅ Configuration MySQL: {DB_HOST}:{DB_PORT}/{db_name}")
except Exception as e:
    # Fallback vers SQLite
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'instance', 'app.db')
    db_uri = f'sqlite:///{db_path}'
    print(f"⚠️ Fallback vers SQLite: {e}")

from flask import Flask
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_pre_ping': True,
    'pool_recycle': 300,
    'connect_args': {'charset': 'utf8mb4'} if 'mysql' in db_uri else {}
}

from models import db, InventoryDetail
db.init_app(app)

def recalculate_variances():
    """Recalcule tous les écarts d'inventaire avec la nouvelle formule"""
    
    with app.app_context():
        print("🔄 Recalcul des écarts d'inventaire...")
        print("=" * 60)
        
        # Récupérer tous les détails d'inventaire
        details = InventoryDetail.query.all()
        total = len(details)
        
        if total == 0:
            print("✅ Aucun détail d'inventaire à recalculer")
            return
        
        print(f"📊 {total} détails d'inventaire trouvés")
        print("-" * 60)
        
        updated_count = 0
        errors = []
        
        for detail in details:
            try:
                # Ancien écart (pour affichage)
                old_variance = detail.variance
                
                # Nouveau calcul : ÉCART = stock actuel - (QUANTITÉ COMPTÉE + PILE)
                # La quantité comptée inclut déjà la pile si elle a été calculée
                new_variance = detail.system_quantity - detail.counted_quantity
                
                # Mettre à jour seulement si différent
                if old_variance != new_variance:
                    detail.variance = new_variance
                    updated_count += 1
                    
                    print(f"✅ Session #{detail.session_id} - Article #{detail.stock_item_id}")
                    print(f"   Stock système: {detail.system_quantity}")
                    print(f"   Quantité comptée: {detail.counted_quantity}")
                    print(f"   Ancien écart: {old_variance} → Nouvel écart: {new_variance}")
                    print()
            except Exception as e:
                error_msg = f"Session #{detail.session_id} - Article #{detail.stock_item_id}: {e}"
                errors.append(error_msg)
                print(f"⚠️ Erreur: {error_msg}")
                    
        # Commit des modifications
        if updated_count > 0:
            try:
                db.session.commit()
                print("=" * 60)
                print(f"✅ {updated_count} écarts mis à jour avec succès")
                print(f"📊 {total - updated_count} écarts déjà corrects")
                print("=" * 60)
            except Exception as e:
                db.session.rollback()
                print(f"❌ Erreur lors de la sauvegarde: {e}")
                return False
        else:
            print("=" * 60)
            print("✅ Tous les écarts sont déjà corrects")
            print("=" * 60)
        
        if errors:
            print(f"\n⚠️ {len(errors)} erreurs rencontrées:")
            for error in errors:
                print(f"   - {error}")
        
        return True

if __name__ == '__main__':
    print("🚀 Script de recalcul des écarts d'inventaire")
    print("=" * 60)
    
    try:
        success = recalculate_variances()
        if success:
            print("\n✅ Migration terminée avec succès")
            sys.exit(0)
        else:
            print("\n❌ Migration échouée")
            sys.exit(1)
    except Exception as e:
        print(f"\n❌ Erreur fatale: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

