#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test final de sauvegarde d'une commande avec Articles
"""

import sys
from decimal import Decimal

sys.path.insert(0, '/Users/dantawi/Documents/mini_flask_import_profitability')

from app import app, db
from models import (
    CommercialOrder, CommercialOrderClient, CommercialOrderItem,
    Article, StockItem, User
)
from orders import generate_order_reference

def test_final_order_save():
    """Test final de sauvegarde"""
    with app.app_context():
        try:
            print(f"\n{'='*60}")
            print(f"📋 TEST FINAL DE SAUVEGARDE COMPLÈTE")
            print(f"{'='*60}\n")
            
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
                print("   Création d'un StockItem pour le premier Article...")
                article = articles[0] if articles else None
                if article:
                    from models import Family
                    family = Family.query.first()
                    if not family:
                        family = Family(name='Divers', description='Famille par défaut')
                        db.session.add(family)
                        db.session.commit()
                    
                    stock_item = StockItem(
                        sku=f'STK-{article.id:04d}',
                        name=article.name,
                        family_id=family.id,
                        purchase_price_gnf=170000,
                        is_active=True
                    )
                    db.session.add(stock_item)
                    db.session.commit()
                    print(f"✅ StockItem créé: {stock_item.name} (ID: {stock_item.id})")
                else:
                    return False
            
            print(f"📦 Article: {article.name} (ID: {article.id})")
            print(f"📦 StockItem: {stock_item.name} (ID: {stock_item.id}, SKU: {stock_item.sku})")
            
            # Générer la référence
            reference = generate_order_reference()
            print(f"📋 Référence générée: {reference}")
            
            # Créer une commande de test
            from datetime import datetime, UTC
            order = CommercialOrder(
                reference=reference,
                commercial_id=commercial.id,
                region_id=commercial.region_id,
                status='draft',
                order_date=datetime.now(UTC),
                user_id=commercial.id
            )
            db.session.add(order)
            db.session.flush()
            
            print(f"✅ Commande créée: ID {order.id}, Référence: {order.reference}")
            
            # Créer un client
            order_client = CommercialOrderClient(
                order_id=order.id,
                client_name="Client Test Final",
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
                quantity=Decimal('5'),
                unit_price_gnf=Decimal('500000'),
                notes="Test final de sauvegarde"
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
            from sqlalchemy.orm import joinedload
            saved_order = CommercialOrder.query.options(
                joinedload(CommercialOrder.clients).joinedload(CommercialOrderClient.items).joinedload(CommercialOrderItem.stock_item)
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
                    print(f"\n{'='*60}")
                    print(f"✅ TEST RÉUSSI - TOUT FONCTIONNE CORRECTEMENT")
                    print(f"{'='*60}\n")
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
    success = test_final_order_save()
    sys.exit(0 if success else 1)

