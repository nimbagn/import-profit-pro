#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script pour tester le calcul du total comme le fait le template
"""

import sys
sys.path.insert(0, '/Users/dantawi/Documents/mini_flask_import_profitability')

from app import app, db
from models import CommercialOrder
from sqlalchemy.orm import joinedload
from decimal import Decimal

def test_template_calculation(order_id):
    """Tester le calcul comme le fait le template"""
    with app.app_context():
        order = CommercialOrder.query.options(
            joinedload(CommercialOrder.commercial),
            joinedload(CommercialOrder.validator),
            joinedload(CommercialOrder.region),
            joinedload(CommercialOrder.clients).joinedload(CommercialOrderClient.items).joinedload(CommercialOrderItem.stock_item),
            joinedload(CommercialOrder.clients).joinedload(CommercialOrderClient.rejected_by)
        ).get(order_id)
        
        if not order:
            print(f"❌ Commande {order_id} non trouvée")
            return
        
        print(f"\n{'='*80}")
        print(f"🧮 TEST CALCUL TEMPLATE - Commande {order.reference}")
        print(f"{'='*80}\n")
        
        # Calcul comme dans l'en-tête (order_total_preview)
        order_total_preview = Decimal('0')
        print("📊 CALCUL EN-TÊTE (order_total_preview):")
        for client in order.clients:
            if client.status != 'rejected':
                print(f"  👤 Client: {client.client_name} (status: {client.status})")
                for item in client.items:
                    if item.quantity is not None and item.quantity > 0:
                        qty = float(item.quantity)
                        price = float(item.unit_price_gnf) if item.unit_price_gnf is not None else 0.0
                        item_line_total = qty * price
                        order_total_preview += Decimal(str(item_line_total))
                        print(f"    - Article: {item.stock_item.name if item.stock_item else 'N/A'}")
                        print(f"      Quantité: {qty} (type: {type(item.quantity).__name__}, valeur: {item.quantity})")
                        print(f"      Prix: {price} GNF (type: {type(item.unit_price_gnf).__name__}, valeur: {item.unit_price_gnf})")
                        print(f"      Total ligne: {item_line_total} GNF")
        
        print(f"\n  💰 TOTAL EN-TÊTE: {order_total_preview} GNF")
        
        # Calcul comme en bas de page (order_total)
        order_total = Decimal('0')
        print(f"\n📊 CALCUL BAS DE PAGE (order_total):")
        for client in order.clients:
            if client.status != 'rejected':
                for item in client.items:
                    if item.quantity is not None and item.quantity > 0:
                        qty = float(item.quantity)
                        price = float(item.unit_price_gnf) if item.unit_price_gnf is not None else 0.0
                        item_line_total = qty * price
                        order_total += Decimal(str(item_line_total))
        
        print(f"  💰 TOTAL BAS DE PAGE: {order_total} GNF")
        
        print(f"\n{'='*80}")
        print(f"✅ RÉSULTAT: Les deux calculs donnent {order_total} GNF")
        print(f"{'='*80}\n")
        
        # Vérifier le format_number
        from app import format_number
        formatted = format_number(float(order_total), 0)
        print(f"📝 Formaté avec format_number: {formatted} GNF\n")

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Tester le calcul du template')
    parser.add_argument('order_id', type=int, help='ID de la commande')
    args = parser.parse_args()
    
    from models import CommercialOrderClient, CommercialOrderItem
    test_template_calculation(args.order_id)

