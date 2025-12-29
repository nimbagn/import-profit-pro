#!/usr/bin/env python3
"""
Script pour activer tous les articles inactifs
"""
import sys
import os

# Ajouter le répertoire parent au path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from models import Article

def activate_all_articles():
    """Active tous les articles inactifs"""
    with app.app_context():
        inactive_articles = Article.query.filter_by(is_active=False).all()
        
        if not inactive_articles:
            print("✅ Tous les articles sont déjà actifs!")
            return
        
        print(f"📦 {len(inactive_articles)} article(s) inactif(s) trouvé(s):")
        for article in inactive_articles:
            print(f"   - {article.name} (ID: {article.id})")
        
        # Activer tous les articles
        for article in inactive_articles:
            article.is_active = True
        
        try:
            db.session.commit()
            print(f"\n✅ {len(inactive_articles)} article(s) activé(s) avec succès!")
            print("\n💡 Ces articles sont maintenant visibles dans les simulations.")
        except Exception as e:
            db.session.rollback()
            print(f"❌ Erreur lors de l'activation: {e}")
            return

if __name__ == "__main__":
    activate_all_articles()

