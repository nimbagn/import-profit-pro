#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script pour ajouter des articles à une commande existante
"""

import sys
from decimal import Decimal
from datetime import date

sys.path.insert(0, '/Users/dantawi/Documents/mini_flask_import_profitability')

from app import app, db
from models import CommercialOrder, CommercialOrderClient, CommercialOrderItem, StockItem, PriceList, PriceListItem

def list_available_stock_items():
    """Lister les articles de stock disponibles"""
    with app.app_context():
        items = StockItem.query.filter_by(is_active=True).order_by(StockItem.name).all()
        print(f"\n📦 ARTICLES DISPONIBLES ({len(items)} articles):")
        print("="*80)
        for item in items:
            price_info = f"Prix d'achat: {item.purchase_price_gnf} GNF" if item.purchase_price_gnf else "Pas de prix d'achat"
            print(f"  [{item.id}] {item.name} (SKU: {item.sku}) - {price_info}")
        print("="*80)
        return items

def add_items_to_order(order_id, dry_run=True):
    """Ajouter des articles à une commande"""
    with app.app_context():
        order = CommercialOrder.query.get(order_id)
        if not order:
            print(f"❌ Commande {order_id} non trouvée")
            return
        
        print(f"\n{'='*80}")
        print(f"➕ AJOUT D'ARTICLES - Commande {order.reference}")
        if dry_run:
            print("   MODE DRY-RUN (simulation, aucune modification)")
        print(f"{'='*80}\n")
        
        # Lister les clients
        print("👥 CLIENTS DE LA COMMANDE:")
        for idx, client in enumerate(order.clients, 1):
            items_count = len(client.items) if client.items else 0
            print(f"  [{idx}] {client.client_name} (ID: {client.id}) - {items_count} article(s)")
        print()
        
        # Récupérer la fiche de prix active
        today = date.today()
        active_price_list = PriceList.query.filter(
            PriceList.is_active == True,
            PriceList.start_date <= today,
            db.or_(
                PriceList.end_date.is_(None),
                PriceList.end_date >= today
            )
        ).order_by(PriceList.start_date.desc()).first()
        
        prices_by_name = {}
        if active_price_list:
            for price_item in active_price_list.items:
                if price_item.article:
                    price = price_item.wholesale_price or price_item.retail_price
                    if price:
                        prices_by_name[price_item.article.name.lower()] = float(price)
        
        # Lister les articles disponibles
        stock_items = list_available_stock_items()
        
        if not stock_items:
            print("❌ Aucun article disponible")
            return
        
        # Exemple d'ajout (à adapter selon vos besoins)
        print("\n💡 EXEMPLE D'UTILISATION:")
        print("   Pour ajouter des articles, modifiez ce script ou utilisez l'interface web")
        print("   pour modifier la commande via: /orders/{}/edit".format(order_id))
        print()
        
        # Afficher les clients sans articles
        clients_without_items = [c for c in order.clients if not c.items or len(c.items) == 0]
        if clients_without_items:
            print("⚠️  CLIENTS SANS ARTICLES:")
            for client in clients_without_items:
                print(f"   - {client.client_name} (ID: {client.id})")
            print()
            print("💡 Pour ajouter des articles à ces clients:")
            print("   1. Allez sur http://localhost:5002/orders/{}/edit".format(order_id))
            print("   2. Ajoutez des articles aux clients via l'interface")
            print("   3. Les prix seront automatiquement remplis depuis la fiche de prix active")
            print()

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Ajouter des articles à une commande')
    parser.add_argument('order_id', type=int, help='ID de la commande')
    parser.add_argument('--list-items', action='store_true', help='Lister les articles disponibles')
    parser.add_argument('--dry-run', action='store_true', default=True, help='Mode simulation')
    
    args = parser.parse_args()
    
    if args.list_items:
        list_available_stock_items()
    else:
        add_items_to_order(args.order_id, dry_run=args.dry_run)

