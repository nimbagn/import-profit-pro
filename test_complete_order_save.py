#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test complet de sauvegarde d'une commande avec Articles
"""

import sys
from decimal import Decimal

sys.path.insert(0, '/Users/dantawi/Documents/mini_flask_import_profitability')

from app import app, db
from models import (
    CommercialOrder, CommercialOrderClient, CommercialOrderItem,
    Article, StockItem, User
)

def test_complete_order_save():
    """Test complet de sauvegarde"""
    with app.app_context():
        try:
            # Trouver un utilisateur commercial
            commercial = User.query.filter_by(username='commercial_test').first()
            if not commercial:
                print("❌ Utilisateur 'commercial_test' non trouvé")
                return False
            
            # Trouver un Article avec un StockItem correspondant
            articles = Article.query.filter_by(is_active=True).all()
            article = None
            stock_item = None
            
            for art in articles:
                si = StockItem.query.filter(
                    StockItem.name.ilike(art.name),
                    StockItem.is_active == True
                ).first()
                if si:
                    article = art
                    stock_item = si
                    break
            
            if not article or not stock_item:
                print("❌ Aucun Article avec StockItem correspondant trouvé")
                return False
            
            print(f"\n{'='*60}")
            print(f"📋 TEST COMPLET DE SAUVEGARDE")
            print(f"{'='*60}\n")
            print(f"📦 Article: {article.name} (ID: {article.id})")
            print(f"📦 StockItem: {stock_item.name} (ID: {stock_item.id}, SKU: {stock_item.sku})")
            
            # Créer une commande de test
            order = CommercialOrder(
                commercial_id=commercial.id,
                status='draft',
                order_date=db.func.now()
            )
            db.session.add(order)
            db.session.flush()
            
            print(f"✅ Commande créée: ID {order.id}, Référence: {order.reference}")
            
            # Créer un client
            order_client = CommercialOrderClient(
                order_id=order.id,
                client_name="Client Test Complet",
                client_phone="+224 123 456 789",
                payment_type='cash'
            )
            db.session.add(order_client)
            db.session.flush()
            
            print(f"✅ Client créé: {order_client.client_name} (ID: {order_client.id})")
            
            # Créer un article de commande
            # IMPORTANT: item_id dans le formulaire est l'ID de l'Article
            # Mais on doit sauvegarder avec stock_item_id
            order_item = CommercialOrderItem(
                order_client_id=order_client.id,
                stock_item_id=stock_item.id,  # Utiliser stock_item_id pour la sauvegarde
                quantity=Decimal('3'),
                unit_price_gnf=Decimal('500000'),
                notes="Test complet de sauvegarde"
            )
            db.session.add(order_item)
            
            # Sauvegarder
            db.session.commit()
            
            print(f"✅ Article de commande créé:")
            print(f"   - StockItem ID: {order_item.stock_item_id}")
            print(f"   - Quantité: {order_item.quantity}")
            print(f"   - Prix unitaire: {order_item.unit_price_gnf:,.2f} GNF")
            print(f"   - Total ligne: {order_item.quantity * order_item.unit_price_gnf:,.2f} GNF")
            
            # Vérifier que la commande est bien sauvegardée
            saved_order = CommercialOrder.query.options(
                db.joinedload(CommercialOrder.clients).joinedload(CommercialOrderClient.items)
            ).get(order.id)
            
            if saved_order and saved_order.clients:
                client = saved_order.clients[0]
                if client.items:
                    item = client.items[0]
                    print(f"\n✅ VÉRIFICATION FINALE:")
                    print(f"   - Commande: {saved_order.reference} (ID: {saved_order.id})")
                    print(f"   - Client: {client.client_name}")
                    print(f"   - Article StockItem: {item.stock_item.name} (ID: {item.stock_item.id})")
                    print(f"   - Quantité: {item.quantity}")
                    print(f"   - Prix: {item.unit_price_gnf:,.2f} GNF")
                    print(f"   - Total: {item.quantity * item.unit_price_gnf:,.2f} GNF")
                    
                    # Calculer le total de la commande
                    total_order = Decimal('0')
                    for c in saved_order.clients:
                        if c.status != 'rejected':
                            for i in c.items:
                                price = i.unit_price_gnf if i.unit_price_gnf else Decimal('0')
                                qty = i.quantity if i.quantity else Decimal('0')
                                total_order += price * qty
                    
                    print(f"   - TOTAL COMMANDE: {total_order:,.2f} GNF")
                    
                    # Nettoyer - supprimer la commande de test
                    db.session.delete(item)
                    db.session.delete(client)
                    db.session.delete(saved_order)
                    db.session.commit()
                    print(f"\n🧹 Commande de test supprimée")
                    return True
                else:
                    print(f"❌ Aucun article trouvé dans la commande sauvegardée")
                    return False
            else:
                print(f"❌ Commande non trouvée après sauvegarde")
                return False
                
        except Exception as e:
            db.session.rollback()
            print(f"❌ Erreur lors du test: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == '__main__':
    success = test_complete_order_save()
    sys.exit(0 if success else 1)

