#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de test pour vérifier la sauvegarde d'une commande avec Articles
"""

import sys
from decimal import Decimal

sys.path.insert(0, '/Users/dantawi/Documents/mini_flask_import_profitability')

from app import app, db
from models import (
    CommercialOrder, CommercialOrderClient, CommercialOrderItem,
    Article, StockItem, User
)

def test_order_save():
    """Test de sauvegarde d'une commande avec Articles"""
    with app.app_context():
        try:
            # Trouver un utilisateur commercial
            commercial = User.query.filter_by(username='commercial_test').first()
            if not commercial:
                print("❌ Utilisateur 'commercial_test' non trouvé")
                return False
            
            # Trouver un Article
            article = Article.query.filter_by(is_active=True).first()
            if not article:
                print("❌ Aucun Article actif trouvé")
                return False
            
            print(f"\n{'='*60}")
            print(f"📋 TEST DE SAUVEGARDE DE COMMANDE")
            print(f"{'='*60}\n")
            print(f"📦 Article sélectionné: {article.name} (ID: {article.id})")
            
            # Trouver le StockItem correspondant par nom
            stock_item = StockItem.query.filter(
                StockItem.name.ilike(article.name),
                StockItem.is_active == True
            ).first()
            
            if not stock_item:
                print(f"⚠️  Aucun StockItem trouvé pour l'article '{article.name}'")
                print(f"   La sauvegarde échouera si aucun StockItem correspondant n'existe")
                return False
            
            print(f"✅ StockItem correspondant trouvé: {stock_item.name} (ID: {stock_item.id})")
            
            # Créer une commande de test
            order = CommercialOrder(
                commercial_id=commercial.id,
                status='draft',
                order_date=db.func.now()
            )
            db.session.add(order)
            db.session.flush()
            
            # Créer un client
            order_client = CommercialOrderClient(
                order_id=order.id,
                client_name="Client Test Final",
                client_phone="+224 123 456 789",
                payment_type='cash'
            )
            db.session.add(order_client)
            db.session.flush()
            
            # Créer un article de commande (utiliser l'ID de l'Article mais stocker le stock_item_id)
            order_item = CommercialOrderItem(
                order_client_id=order_client.id,
                stock_item_id=stock_item.id,  # Utiliser le stock_item_id pour la sauvegarde
                quantity=Decimal('2'),
                unit_price_gnf=Decimal('680000'),
                notes="Article de test depuis script"
            )
            db.session.add(order_item)
            
            # Sauvegarder
            db.session.commit()
            
            print(f"\n✅ COMMANDE CRÉÉE AVEC SUCCÈS")
            print(f"   - Commande ID: {order.id}")
            print(f"   - Référence: {order.reference}")
            print(f"   - Client: {order_client.client_name}")
            print(f"   - Article: {article.name} (Article ID: {article.id}, StockItem ID: {stock_item.id})")
            print(f"   - Quantité: 2")
            print(f"   - Prix unitaire: 680,000 GNF")
            print(f"   - Total ligne: 1,360,000 GNF")
            
            # Vérifier que la commande est bien sauvegardée
            saved_order = CommercialOrder.query.get(order.id)
            if saved_order and saved_order.clients:
                client = saved_order.clients[0]
                if client.items:
                    item = client.items[0]
                    print(f"\n✅ VÉRIFICATION:")
                    print(f"   - Commande trouvée: {saved_order.reference}")
                    print(f"   - Client trouvé: {client.client_name}")
                    print(f"   - Article trouvé: {item.stock_item.name}")
                    print(f"   - Quantité: {item.quantity}")
                    print(f"   - Prix: {item.unit_price_gnf:,.2f} GNF")
                    print(f"   - Total: {item.quantity * item.unit_price_gnf:,.2f} GNF")
                    
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
    success = test_order_save()
    sys.exit(0 if success else 1)

