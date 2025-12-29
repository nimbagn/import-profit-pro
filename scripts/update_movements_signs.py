#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script pour mettre à jour les anciens mouvements de stock
et les convertir au nouveau format avec signes (entrées positives, sorties négatives)
"""

import sys
import os
from pathlib import Path

# Ajouter le répertoire parent au path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app import app
from models import db, StockMovement, StockItem, Depot, Vehicle
from decimal import Decimal
from datetime import datetime

def update_movements():
    """Met à jour les mouvements existants pour utiliser le nouveau format avec signes"""
    
    with app.app_context():
        print("=" * 80)
        print("MISE À JOUR DES MOUVEMENTS DE STOCK")
        print("=" * 80)
        print()
        
        # Statistiques
        stats = {
            'transfers_updated': 0,
            'transfers_created': 0,
            'receptions_updated': 0,
            'adjustments_updated': 0,
            'errors': []
        }
        
        # 1. Traiter les transferts (movement_type = 'transfer')
        print("📦 Traitement des transferts...")
        transfers = StockMovement.query.filter_by(movement_type='transfer').all()
        
        for movement in transfers:
            try:
                # Vérifier si c'est un ancien format (a from_depot/vehicle ET to_depot/vehicle)
                has_source = movement.from_depot_id or movement.from_vehicle_id
                has_dest = movement.to_depot_id or movement.to_vehicle_id
                
                if has_source and has_dest:
                    # Ancien format : un seul mouvement avec source et destination
                    # Il faut le diviser en deux mouvements
                    
                    quantity = abs(float(movement.quantity))  # Prendre la valeur absolue
                    reference = movement.reference
                    movement_date = movement.movement_date
                    stock_item_id = movement.stock_item_id
                    user_id = movement.user_id
                    reason = movement.reason
                    
                    # Supprimer l'ancien mouvement
                    db.session.delete(movement)
                    
                    # Créer le mouvement SORTIE (négatif)
                    movement_out = StockMovement(
                        reference=reference,
                        movement_type='transfer',
                        movement_date=movement_date,
                        stock_item_id=stock_item_id,
                        quantity=Decimal(str(-quantity)),  # NÉGATIF
                        user_id=user_id,
                        from_depot_id=movement.from_depot_id,
                        from_vehicle_id=movement.from_vehicle_id,
                        to_depot_id=None,
                        to_vehicle_id=None,
                        reason=reason
                    )
                    db.session.add(movement_out)
                    
                    # Créer le mouvement ENTRÉE (positif)
                    movement_in = StockMovement(
                        reference=reference,
                        movement_type='transfer',
                        movement_date=movement_date,
                        stock_item_id=stock_item_id,
                        quantity=Decimal(str(quantity)),  # POSITIF
                        user_id=user_id,
                        from_depot_id=None,
                        from_vehicle_id=None,
                        to_depot_id=movement.to_depot_id,
                        to_vehicle_id=movement.to_vehicle_id,
                        reason=reason
                    )
                    db.session.add(movement_in)
                    
                    stats['transfers_updated'] += 1
                    stats['transfers_created'] += 2
                    
                    print(f"  ✅ Transfert {reference} divisé en 2 mouvements (SORTIE: -{quantity}, ENTRÉE: +{quantity})")
                    
                elif has_source and not has_dest:
                    # Déjà au nouveau format (sortie uniquement)
                    if movement.quantity > 0:
                        # Corriger le signe si nécessaire
                        movement.quantity = -abs(movement.quantity)
                        print(f"  ✅ Transfert {movement.reference} corrigé (SORTIE: {movement.quantity})")
                        stats['transfers_updated'] += 1
                        
                elif has_dest and not has_source:
                    # Déjà au nouveau format (entrée uniquement)
                    if movement.quantity < 0:
                        # Corriger le signe si nécessaire
                        movement.quantity = abs(movement.quantity)
                        print(f"  ✅ Transfert {movement.reference} corrigé (ENTRÉE: {movement.quantity})")
                        stats['transfers_updated'] += 1
                        
            except Exception as e:
                error_msg = f"Erreur sur transfert ID {movement.id}: {str(e)}"
                stats['errors'].append(error_msg)
                print(f"  ❌ {error_msg}")
        
        print()
        
        # 2. Traiter les réceptions (movement_type = 'reception')
        print("📥 Traitement des réceptions...")
        receptions = StockMovement.query.filter_by(movement_type='reception').all()
        
        for movement in receptions:
            try:
                # Les réceptions doivent être positives (entrées)
                if movement.quantity < 0:
                    movement.quantity = abs(movement.quantity)
                    stats['receptions_updated'] += 1
                    print(f"  ✅ Réception {movement.reference} corrigée (ENTRÉE: {movement.quantity})")
                    
                # S'assurer qu'il n'y a pas de source (from_depot/vehicle)
                if movement.from_depot_id or movement.from_vehicle_id:
                    movement.from_depot_id = None
                    movement.from_vehicle_id = None
                    stats['receptions_updated'] += 1
                    print(f"  ✅ Réception {movement.reference} nettoyée (source supprimée)")
                    
            except Exception as e:
                error_msg = f"Erreur sur réception ID {movement.id}: {str(e)}"
                stats['errors'].append(error_msg)
                print(f"  ❌ {error_msg}")
        
        print()
        
        # 3. Traiter les ajustements (movement_type = 'adjustment')
        print("🔧 Traitement des ajustements...")
        adjustments = StockMovement.query.filter_by(movement_type='adjustment').all()
        
        for movement in adjustments:
            try:
                has_source = movement.from_depot_id or movement.from_vehicle_id
                has_dest = movement.to_depot_id or movement.to_vehicle_id
                
                if has_dest and not has_source:
                    # Ajustement positif (ajout) - doit être positif
                    if movement.quantity < 0:
                        movement.quantity = abs(movement.quantity)
                        stats['adjustments_updated'] += 1
                        print(f"  ✅ Ajustement {movement.reference} corrigé (AJOUT: {movement.quantity})")
                        
                elif has_source and not has_dest:
                    # Ajustement négatif (retrait) - doit être négatif
                    if movement.quantity > 0:
                        movement.quantity = -abs(movement.quantity)
                        stats['adjustments_updated'] += 1
                        print(f"  ✅ Ajustement {movement.reference} corrigé (RETRAIT: {movement.quantity})")
                        
            except Exception as e:
                error_msg = f"Erreur sur ajustement ID {movement.id}: {str(e)}"
                stats['errors'].append(error_msg)
                print(f"  ❌ {error_msg}")
        
        print()
        
        # Valider les modifications
        try:
            db.session.commit()
            print("=" * 80)
            print("✅ MISE À JOUR TERMINÉE AVEC SUCCÈS")
            print("=" * 80)
            print(f"📦 Transferts traités: {stats['transfers_updated']} (création de {stats['transfers_created']} nouveaux mouvements)")
            print(f"📥 Réceptions corrigées: {stats['receptions_updated']}")
            print(f"🔧 Ajustements corrigés: {stats['adjustments_updated']}")
            if stats['errors']:
                print(f"❌ Erreurs: {len(stats['errors'])}")
                for error in stats['errors']:
                    print(f"   - {error}")
            print()
            print("💡 Les mouvements ont été mis à jour avec succès!")
            print("   - Entrées: quantités positives (+)")
            print("   - Sorties: quantités négatives (-)")
            print("   - Transferts: divisés en 2 mouvements (sortie + entrée)")
            
        except Exception as e:
            db.session.rollback()
            print("=" * 80)
            print("❌ ERREUR LORS DE LA MISE À JOUR")
            print("=" * 80)
            print(f"Erreur: {str(e)}")
            print("Les modifications ont été annulées (rollback)")
            return False
        
        return True

if __name__ == '__main__':
    print()
    print("🚀 Démarrage de la mise à jour des mouvements...")
    print()
    
    success = update_movements()
    
    if success:
        print()
        print("✅ Script terminé avec succès!")
        sys.exit(0)
    else:
        print()
        print("❌ Script terminé avec des erreurs")
        sys.exit(1)

