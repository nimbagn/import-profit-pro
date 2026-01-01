#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script pour vérifier les prix d'achat des articles de stock dans la base de données
"""

import sys
import os

# Ajouter le répertoire parent au path pour les imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from models import StockItem

def verifier_prix():
    """Vérifier les prix d'achat des articles de stock"""
    print("🔍 Vérification des prix d'achat des articles de stock...")
    print("")
    
    with app.app_context():
        # Récupérer tous les articles de stock
        stock_items = StockItem.query.order_by(StockItem.name).limit(20).all()
        
        if not stock_items:
            print("❌ Aucun article de stock trouvé dans la base de données")
            return
        
        print(f"📊 Affichage des {len(stock_items)} premiers articles :")
        print("")
        print(f"{'SKU':<20} {'Nom':<40} {'Prix Achat (GNF)':<20} {'Prix présent':<15}")
        print("-" * 95)
        
        count_with_price = 0
        count_without_price = 0
        
        for item in stock_items:
            prix = item.purchase_price_gnf
            has_price = prix is not None and prix > 0
            
            if has_price:
                count_with_price += 1
                prix_str = f"{prix:,.0f}"
            else:
                count_without_price += 1
                prix_str = "Aucun"
            
            print(f"{item.sku:<20} {item.name[:38]:<40} {prix_str:<20} {'✅' if has_price else '❌':<15}")
        
        print("-" * 95)
        print("")
        print(f"📈 Statistiques :")
        print(f"   - Articles avec prix : {count_with_price}")
        print(f"   - Articles sans prix : {count_without_price}")
        print(f"   - Total vérifié : {len(stock_items)}")
        print("")
        
        # Vérifier les articles récemment importés (derniers 10)
        print("📋 Articles récemment créés/modifiés (derniers 10) :")
        recent_items = StockItem.query.order_by(StockItem.created_at.desc()).limit(10).all()
        
        for item in recent_items:
            prix = item.purchase_price_gnf
            has_price = prix is not None and prix > 0
            created = item.created_at.strftime('%Y-%m-%d %H:%M') if item.created_at else 'N/A'
            
            print(f"   - {item.sku} | {item.name[:30]:<30} | Prix: {prix:,.0f if has_price else 'Aucun':<15} | Créé: {created}")

if __name__ == '__main__':
    verifier_prix()

