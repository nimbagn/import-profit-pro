#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script pour vérifier le stock d'une équipe dans la base de données
"""

import sys
import os

# Ajouter le répertoire parent au path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from models import db, PromotionTeamStock, PromotionTeam, PromotionGamme

def verify_team_stock(team_id):
    """Vérifier le stock d'une équipe"""
    with app.app_context():
        # Vérifier si l'équipe existe
        team = PromotionTeam.query.get(team_id)
        if not team:
            print(f"❌ Équipe {team_id} n'existe pas")
            return
        
        print(f"✅ Équipe trouvée: {team.name} (ID: {team.id})")
        
        # Vérifier le stock
        stocks = PromotionTeamStock.query.filter_by(team_id=team_id).all()
        
        if not stocks:
            print(f"⚠️ Aucun stock enregistré pour l'équipe {team_id}")
            print("\nVérification de la table promotion_team_stock:")
            try:
                from sqlalchemy import text
                result = db.session.execute(text("SELECT COUNT(*) as count FROM promotion_team_stock"))
                count = result.fetchone()[0]
                print(f"   Total d'enregistrements dans la table: {count}")
                
                if count > 0:
                    result = db.session.execute(text("SELECT * FROM promotion_team_stock LIMIT 5"))
                    print("\n   Premiers enregistrements:")
                    for row in result:
                        print(f"   - Team ID: {row[1]}, Gamme ID: {row[2]}, Quantity: {row[3]}")
            except Exception as e:
                print(f"   Erreur: {e}")
            return
        
        print(f"\n📦 Stock trouvé: {len(stocks)} type(s) de gammes")
        print("\nDétails du stock:")
        for stock in stocks:
            gamme = PromotionGamme.query.get(stock.gamme_id)
            gamme_name = gamme.name if gamme else f"Gamme ID {stock.gamme_id} (non trouvée)"
            print(f"  - {gamme_name}: {stock.quantity} unité(s)")
            if hasattr(stock, 'last_updated') and stock.last_updated:
                print(f"    Dernière mise à jour: {stock.last_updated}")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python scripts/verify_team_stock.py <team_id>")
        sys.exit(1)
    
    team_id = int(sys.argv[1])
    verify_team_stock(team_id)

