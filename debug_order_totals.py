#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Script de debug pour vérifier les totaux d'une commande"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app import app
from models import db, CommercialOrder, CommercialOrderClient, CommercialOrderItem

def debug_order(order_id):
    """Debug les totaux d'une commande"""
    with app.app_context():
        order = CommercialOrder.query.get(order_id)
        if not order:
            print(f"❌ Commande {order_id} non trouvée")
            return
        
        print(f"\n{'='*60}")
        print(f"🔍 DEBUG COMMANDE {order.reference} (ID: {order_id})")
        print(f"{'='*60}\n")
        
        print(f"📋 Statut: {order.status}")
        print(f"👤 Commercial: {order.commercial.full_name if order.commercial else 'N/A'}")
        print(f"📅 Date: {order.order_date}")
        print(f"👥 Nombre de clients: {len(order.clients)}\n")
        
        total_order = 0
        for i, client in enumerate(order.clients, 1):
            print(f"{'─'*60}")
            print(f"👤 CLIENT {i}: {client.client_name}")
            print(f"   Statut: {client.status}")
            print(f"   Téléphone: {client.client_phone or 'N/A'}")
            print(f"   Articles: {len(client.items)}")
            
            client_total = 0
            for j, item in enumerate(client.items, 1):
                qty = float(item.quantity) if item.quantity is not None else 0
                price = float(item.unit_price_gnf) if item.unit_price_gnf is not None else 0
                line_total = qty * price
                client_total += line_total
                
                print(f"   ├─ Article {j}: {item.stock_item.name if item.stock_item else 'N/A'}")
                print(f"   │  Quantité: {qty} (type: {type(item.quantity).__name__}, valeur: {item.quantity})")
                print(f"   │  Prix unit.: {price} GNF (type: {type(item.unit_price_gnf).__name__}, valeur: {item.unit_price_gnf})")
                print(f"   │  Total ligne: {line_total:,.0f} GNF")
            
            print(f"   └─ TOTAL CLIENT: {client_total:,.0f} GNF")
            
            if client.status != 'rejected':
                total_order += client_total
            else:
                print(f"   ⚠️  Client rejeté - exclu du total global")
        
        print(f"\n{'='*60}")
        print(f"💰 TOTAL GLOBAL DE LA COMMANDE: {total_order:,.0f} GNF")
        print(f"{'='*60}\n")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python debug_order_totals.py <order_id>")
        sys.exit(1)
    
    order_id = int(sys.argv[1])
    debug_order(order_id)

