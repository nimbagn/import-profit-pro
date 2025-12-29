#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script pour ajouter automatiquement un article de test à une commande
"""

import sys
from decimal import Decimal
from datetime import date

sys.path.insert(0, '/Users/dantawi/Documents/mini_flask_import_profitability')

from app import app, db
from models import CommercialOrder, CommercialOrderClient, CommercialOrderItem, StockItem, PriceList, PriceListItem

def add_test_item_to_order(order_id, stock_item_id=None, quantity=1, dry_run=True):
    """Ajouter un article de test à une commande"""
    with app.app_context():
        order = CommercialOrder.query.get(order_id)
        if not order:
            print(f"❌ Commande {order_id} non trouvée")
            return False
        
        print(f"\n{'='*80}")
        print(f"➕ AJOUT D'ARTICLE DE TEST - Commande {order.reference}")
        if dry_run:
            print("   MODE DRY-RUN (simulation, aucune modification)")
        print(f"{'='*80}\n")
        
        # Trouver un client sans articles ou utiliser le premier client
        client_without_items = None
        for client in order.clients:
            if not client.items or len(client.items) == 0:
                client_without_items = client
                break
        
        if not client_without_items and order.clients:
            client_without_items = order.clients[0]
            print(f"⚠️  Le client {client_without_items.client_name} a déjà des articles")
            print(f"   L'article sera ajouté quand même\n")
        
        if not client_without_items:
            print("❌ Aucun client trouvé dans la commande")
            return False
        
        print(f"👤 Client sélectionné: {client_without_items.client_name} (ID: {client_without_items.id})\n")
        
        # Trouver un article de stock
        if stock_item_id:
            stock_item = StockItem.query.get(stock_item_id)
        else:
            # Prendre le premier article actif disponible
            stock_item = StockItem.query.filter_by(is_active=True).first()
        
        if not stock_item:
            print("❌ Aucun article de stock disponible")
            return False
        
        print(f"📦 Article sélectionné: {stock_item.name} (ID: {stock_item.id})")
        print(f"   SKU: {stock_item.sku}")
        print(f"   Prix d'achat: {stock_item.purchase_price_gnf} GNF\n")
        
        # Déterminer le prix à utiliser
        unit_price = None
        source = None
        
        # 1. Chercher dans la fiche de prix active
        today = date.today()
        active_price_list = PriceList.query.filter(
            PriceList.is_active == True,
            PriceList.start_date <= today,
            db.or_(
                PriceList.end_date.is_(None),
                PriceList.end_date >= today
            )
        ).order_by(PriceList.start_date.desc()).first()
        
        if active_price_list:
            for price_item in active_price_list.items:
                if price_item.article and price_item.article.name.lower() == stock_item.name.lower():
                    unit_price = price_item.wholesale_price or price_item.retail_price
                    if unit_price:
                        source = f"Fiche de prix active ({active_price_list.name})"
                        break
        
        # 2. Sinon utiliser le prix d'achat
        if not unit_price and stock_item.purchase_price_gnf:
            unit_price = stock_item.purchase_price_gnf
            source = "Prix d'achat de l'article"
        
        # 3. Sinon utiliser un prix par défaut
        if not unit_price:
            unit_price = Decimal('100000')  # Prix par défaut de 100,000 GNF
            source = "Prix par défaut (100,000 GNF)"
        
        line_total = unit_price * Decimal(str(quantity))
        
        print(f"💰 Prix unitaire: {unit_price} GNF ({source})")
        print(f"📊 Quantité: {quantity}")
        print(f"💵 Total ligne: {line_total} GNF\n")
        
        if not dry_run:
            # Créer l'article de commande
            order_item = CommercialOrderItem(
                order_client_id=client_without_items.id,
                stock_item_id=stock_item.id,
                quantity=Decimal(str(quantity)),
                unit_price_gnf=unit_price,
                notes="Article ajouté automatiquement par script de test"
            )
            
            try:
                db.session.add(order_item)
                db.session.commit()
                
                print(f"{'='*80}")
                print(f"✅ ARTICLE AJOUTÉ AVEC SUCCÈS")
                print(f"   - Article: {stock_item.name}")
                print(f"   - Client: {client_without_items.client_name}")
                print(f"   - Quantité: {quantity}")
                print(f"   - Prix unitaire: {unit_price} GNF")
                print(f"   - Total ligne: {line_total} GNF")
                print(f"{'='*80}\n")
                
                # Calculer le nouveau total de la commande
                total_order = Decimal('0')
                for client in order.clients:
                    if client.status != 'rejected':
                        for item in client.items:
                            if item.unit_price_gnf and item.quantity:
                                total_order += item.unit_price_gnf * item.quantity
                
                print(f"💰 NOUVEAU TOTAL DE LA COMMANDE: {total_order} GNF\n")
                return True
                
            except Exception as e:
                db.session.rollback()
                print(f"❌ Erreur lors de l'ajout: {e}\n")
                return False
        else:
            print(f"{'='*80}")
            print(f"📊 SIMULATION - Aucune modification effectuée")
            print(f"   Pour appliquer, relancez avec --apply")
            print(f"{'='*80}\n")
            return True

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Ajouter un article de test à une commande')
    parser.add_argument('order_id', type=int, help='ID de la commande')
    parser.add_argument('--stock-item-id', type=int, help='ID de l\'article de stock (optionnel)')
    parser.add_argument('--quantity', type=int, default=1, help='Quantité (défaut: 1)')
    parser.add_argument('--dry-run', action='store_true', default=True, help='Mode simulation (par défaut)')
    parser.add_argument('--apply', action='store_true', help='Appliquer les modifications (désactive dry-run)')
    
    args = parser.parse_args()
    
    if args.apply:
        args.dry_run = False
    
    success = add_test_item_to_order(
        args.order_id, 
        stock_item_id=args.stock_item_id,
        quantity=args.quantity,
        dry_run=args.dry_run
    )
    
    if success and not args.dry_run:
        # Vérifier le résultat
        print("\n" + "="*80)
        print("📋 VÉRIFICATION APRÈS AJOUT")
        print("="*80)
        from check_order_prices import check_order_prices
        check_order_prices(args.order_id)

