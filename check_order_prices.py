#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script pour vérifier et mettre à jour les prix manquants dans les commandes
"""

import sys
from decimal import Decimal
from datetime import date

# Ajouter le répertoire parent au path
sys.path.insert(0, '/Users/dantawi/Documents/mini_flask_import_profitability')

from app import app, db
from models import CommercialOrder, CommercialOrderItem, StockItem, PriceList, PriceListItem

def check_order_prices(order_id):
    """Vérifier les prix d'une commande spécifique"""
    with app.app_context():
        order = CommercialOrder.query.get(order_id)
        if not order:
            print(f"❌ Commande {order_id} non trouvée")
            return
        
        print(f"\n{'='*80}")
        print(f"📋 COMMANDE: {order.reference} (ID: {order.id})")
        print(f"   Statut: {order.status}")
        print(f"   Date: {order.order_date}")
        print(f"   Commercial: {order.commercial.full_name if order.commercial else 'N/A'}")
        print(f"{'='*80}\n")
        
        total_order = Decimal('0')
        clients_with_missing_prices = []
        
        for client in order.clients:
            print(f"👤 CLIENT: {client.client_name} (ID: {client.id})")
            print(f"   Statut: {client.status}")
            
            client_total = Decimal('0')
            items_with_missing_prices = []
            
            if not client.items:
                print(f"   ⚠️  Aucun article pour ce client")
            else:
                for item in client.items:
                    qty = item.quantity or Decimal('0')
                    price = item.unit_price_gnf or Decimal('0')
                    line_total = qty * price
                    client_total += line_total
                    
                    status = "✅" if price > 0 else "❌"
                    print(f"   {status} Article: {item.stock_item.name if item.stock_item else 'N/A'}")
                    print(f"      - ID Item: {item.id}")
                    print(f"      - SKU: {item.stock_item.sku if item.stock_item else 'N/A'}")
                    print(f"      - Quantité: {qty}")
                    print(f"      - Prix unitaire: {price} GNF {'(NULL)' if item.unit_price_gnf is None else ''}")
                    print(f"      - Total ligne: {line_total} GNF")
                    
                    if price <= 0:
                        items_with_missing_prices.append({
                            'item': item,
                            'stock_item': item.stock_item,
                            'quantity': qty
                        })
            
            print(f"   💰 TOTAL CLIENT: {client_total} GNF\n")
            total_order += client_total
            
            if items_with_missing_prices:
                clients_with_missing_prices.append({
                    'client': client,
                    'items': items_with_missing_prices
                })
        
        print(f"{'='*80}")
        print(f"💰 TOTAL COMMANDE: {total_order} GNF")
        print(f"{'='*80}\n")
        
        if clients_with_missing_prices:
            print(f"⚠️  {len(clients_with_missing_prices)} client(s) avec des prix manquants\n")
            return clients_with_missing_prices
        else:
            print("✅ Tous les articles ont des prix définis\n")
            return []

def update_missing_prices(order_id, dry_run=True):
    """Mettre à jour les prix manquants d'une commande"""
    with app.app_context():
        order = CommercialOrder.query.get(order_id)
        if not order:
            print(f"❌ Commande {order_id} non trouvée")
            return
        
        print(f"\n{'='*80}")
        print(f"🔄 MISE À JOUR DES PRIX - Commande {order.reference}")
        if dry_run:
            print("   MODE DRY-RUN (simulation, aucune modification)")
        print(f"{'='*80}\n")
        
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
            print(f"📋 Fiche de prix active: {active_price_list.name}")
            for price_item in active_price_list.items:
                if price_item.article:
                    price = price_item.wholesale_price or price_item.retail_price
                    if price:
                        prices_by_name[price_item.article.name.lower()] = float(price)
            print(f"   {len(prices_by_name)} prix trouvés dans la fiche\n")
        else:
            print("⚠️  Aucune fiche de prix active trouvée\n")
        
        updated_count = 0
        total_updated_value = Decimal('0')
        
        for client in order.clients:
            if client.status == 'rejected':
                continue
                
            for item in client.items:
                if not item.unit_price_gnf or item.unit_price_gnf <= 0:
                    stock_item = item.stock_item
                    new_price = None
                    source = None
                    
                    # 1. Chercher dans la fiche de prix active
                    if stock_item and stock_item.name:
                        item_name_lower = stock_item.name.lower()
                        if item_name_lower in prices_by_name:
                            new_price = Decimal(str(prices_by_name[item_name_lower]))
                            source = "Fiche de prix active"
                    
                    # 2. Sinon utiliser le prix d'achat
                    if not new_price and stock_item and stock_item.purchase_price_gnf:
                        new_price = stock_item.purchase_price_gnf
                        source = "Prix d'achat de l'article"
                    
                    # 3. Sinon utiliser 0
                    if not new_price:
                        new_price = Decimal('0')
                        source = "Valeur par défaut (0)"
                    
                    old_price = item.unit_price_gnf or Decimal('0')
                    line_value = (new_price - old_price) * (item.quantity or Decimal('0'))
                    total_updated_value += line_value
                    
                    print(f"📝 Article: {stock_item.name if stock_item else 'N/A'}")
                    print(f"   - Ancien prix: {old_price} GNF")
                    print(f"   - Nouveau prix: {new_price} GNF ({source})")
                    print(f"   - Quantité: {item.quantity}")
                    print(f"   - Impact: {line_value} GNF")
                    
                    if not dry_run:
                        item.unit_price_gnf = new_price
                        updated_count += 1
                    
                    print()
        
        if dry_run:
            print(f"{'='*80}")
            print(f"📊 RÉSUMÉ (SIMULATION)")
            print(f"   Articles à mettre à jour: {updated_count}")
            print(f"   Impact sur le total: {total_updated_value} GNF")
            print(f"\n💡 Pour appliquer les modifications, relancez avec dry_run=False")
        else:
            try:
                db.session.commit()
                print(f"{'='*80}")
                print(f"✅ MISE À JOUR TERMINÉE")
                print(f"   Articles mis à jour: {updated_count}")
                print(f"   Impact sur le total: {total_updated_value} GNF")
            except Exception as e:
                db.session.rollback()
                print(f"❌ Erreur lors de la mise à jour: {e}")
        
        print(f"{'='*80}\n")

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Vérifier et mettre à jour les prix des commandes')
    parser.add_argument('order_id', type=int, help='ID de la commande')
    parser.add_argument('--update', action='store_true', help='Mettre à jour les prix manquants')
    parser.add_argument('--dry-run', action='store_true', default=True, help='Mode simulation (par défaut)')
    parser.add_argument('--apply', action='store_true', help='Appliquer les modifications (désactive dry-run)')
    
    args = parser.parse_args()
    
    if args.apply:
        args.dry_run = False
    
    # Vérifier d'abord
    missing_prices = check_order_prices(args.order_id)
    
    # Mettre à jour si demandé
    if args.update or args.apply:
        update_missing_prices(args.order_id, dry_run=args.dry_run)
        
        # Vérifier à nouveau après mise à jour
        if not args.dry_run:
            print("\n" + "="*80)
            print("📋 VÉRIFICATION APRÈS MISE À JOUR")
            print("="*80)
            check_order_prices(args.order_id)

