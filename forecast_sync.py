#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module de synchronisation entre les commandes validées et les prévisions de ventes
"""

from decimal import Decimal
from datetime import date, datetime
from models import (
    db, CommercialOrder, CommercialOrderClient, CommercialOrderItem,
    Forecast, ForecastItem, StockItem
)
from sqlalchemy import and_, or_


def update_forecasts_from_order(order):
    """
    Met à jour les prévisions de ventes basées sur une commande validée
    
    Args:
        order: CommercialOrder validée
        
    Returns:
        dict: Statistiques de mise à jour
    """
    if order.status != 'validated':
        return {'updated': 0, 'forecasts': [], 'message': 'Commande non validée'}
    
    # Convertir order_date en date si c'est un datetime
    order_date = order.order_date
    if isinstance(order_date, datetime):
        order_date = order_date.date()
    
    # Trouver toutes les prévisions actives qui couvrent la date de la commande
    active_forecasts = Forecast.query.filter(
        and_(
            Forecast.status == 'active',
            Forecast.start_date <= order_date,
            Forecast.end_date >= order_date
        )
    ).all()
    
    if not active_forecasts:
        return {'updated': 0, 'forecasts': [], 'message': 'Aucune prévision active trouvée pour cette date'}
    
    updated_forecasts = []
    total_items_updated = 0
    
    # Pour chaque prévision active
    for forecast in active_forecasts:
        forecast_updated = False
        forecast_total_realized = Decimal('0')
        
        # Pour chaque client de la commande (non rejeté)
        for client in order.clients:
            if client.status == 'rejected':
                continue
                
            # Pour chaque article de la commande
            for order_item in client.items:
                if not order_item.quantity or order_item.quantity <= 0:
                    continue
                
                # Trouver le ForecastItem correspondant (même StockItem)
                forecast_item = ForecastItem.query.filter_by(
                    forecast_id=forecast.id,
                    stock_item_id=order_item.stock_item_id
                ).first()
                
                if forecast_item:
                    # Mettre à jour les réalisations
                    # Ajouter la quantité et la valeur (pas remplacer, car il peut y avoir plusieurs commandes)
                    forecast_item.realized_quantity += order_item.quantity
                    
                    # Calculer la valeur réalisée
                    item_value = order_item.quantity * (order_item.unit_price_gnf or Decimal('0'))
                    forecast_item.realized_value_gnf += item_value
                    
                    # Recalculer le pourcentage de réalisation
                    if forecast_item.forecast_quantity > 0:
                        forecast_item.realization_percentage = (
                            (forecast_item.realized_quantity / forecast_item.forecast_quantity) * 100
                        )
                    
                    forecast_total_realized += item_value
                    forecast_updated = True
                    total_items_updated += 1
        
        # Mettre à jour le total réalisé de la prévision
        if forecast_updated:
            # Recalculer le total depuis tous les items
            forecast.total_realized_value = Decimal('0')
            for item in forecast.items:
                forecast.total_realized_value += item.realized_value_gnf
            
            updated_forecasts.append({
                'id': forecast.id,
                'name': forecast.name,
                'total_realized': float(forecast.total_realized_value)
            })
    
    if updated_forecasts:
        db.session.commit()
    
    return {
        'updated': len(updated_forecasts),
        'items_updated': total_items_updated,
        'forecasts': updated_forecasts,
        'message': f'{len(updated_forecasts)} prévision(s) mise(s) à jour'
    }


def recalculate_all_forecasts_from_orders(start_date=None, end_date=None):
    """
    Recalcule toutes les prévisions basées sur les commandes validées
    
    Args:
        start_date: Date de début (optionnel)
        end_date: Date de fin (optionnel)
        
    Returns:
        dict: Statistiques de recalcul
    """
    # Réinitialiser toutes les réalisations
    forecast_items = ForecastItem.query.join(Forecast).filter(
        Forecast.status == 'active'
    ).all()
    
    for item in forecast_items:
        item.realized_quantity = Decimal('0')
        item.realized_value_gnf = Decimal('0')
        item.realization_percentage = Decimal('0')
    
    # Récupérer toutes les commandes validées dans la période
    query = CommercialOrder.query.filter(
        CommercialOrder.status == 'validated'
    )
    
    if start_date:
        query = query.filter(CommercialOrder.order_date >= start_date)
    if end_date:
        query = query.filter(CommercialOrder.order_date <= end_date)
    
    validated_orders = query.all()
    
    updated_forecasts = set()
    total_items_updated = 0
    
    # Traiter chaque commande
    for order in validated_orders:
        result = update_forecasts_from_order(order)
        if result['updated'] > 0:
            for forecast_info in result['forecasts']:
                updated_forecasts.add(forecast_info['id'])
            total_items_updated += result['items_updated']
    
    # Recalculer les totaux de toutes les prévisions mises à jour
    for forecast_id in updated_forecasts:
        forecast = Forecast.query.get(forecast_id)
        if forecast:
            forecast.total_realized_value = Decimal('0')
            for item in forecast.items:
                forecast.total_realized_value += item.realized_value_gnf
    
    db.session.commit()
    
    return {
        'orders_processed': len(validated_orders),
        'forecasts_updated': len(updated_forecasts),
        'items_updated': total_items_updated,
        'message': f'{len(validated_orders)} commande(s) traitée(s), {len(updated_forecasts)} prévision(s) mise(s) à jour'
    }


def get_forecast_realization_from_orders(forecast_id):
    """
    Calcule les réalisations d'une prévision spécifique basées sur les commandes validées
    
    Args:
        forecast_id: ID de la prévision
        
    Returns:
        dict: Détails des réalisations
    """
    forecast = Forecast.query.get_or_404(forecast_id)
    
    # Récupérer toutes les commandes validées dans la période de la prévision
    validated_orders = CommercialOrder.query.filter(
        and_(
            CommercialOrder.status == 'validated',
            CommercialOrder.order_date >= forecast.start_date,
            CommercialOrder.order_date <= forecast.end_date
        )
    ).all()
    
    items_realization = {}
    total_realized_value = Decimal('0')
    
    # Pour chaque article de la prévision
    for forecast_item in forecast.items:
        item_realized_qty = Decimal('0')
        item_realized_value = Decimal('0')
        orders_count = 0
        
        # Parcourir toutes les commandes validées
        for order in validated_orders:
            for client in order.clients:
                if client.status == 'rejected':
                    continue
                
                for order_item in client.items:
                    if order_item.stock_item_id == forecast_item.stock_item_id:
                        item_realized_qty += order_item.quantity
                        item_realized_value += order_item.quantity * (order_item.unit_price_gnf or Decimal('0'))
                        orders_count += 1
        
        items_realization[forecast_item.id] = {
            'stock_item_id': forecast_item.stock_item_id,
            'stock_item_name': forecast_item.stock_item.name if forecast_item.stock_item else 'N/A',
            'forecast_quantity': float(forecast_item.forecast_quantity),
            'realized_quantity': float(item_realized_qty),
            'realized_value': float(item_realized_value),
            'orders_count': orders_count
        }
        
        total_realized_value += item_realized_value
    
    return {
        'forecast_id': forecast_id,
        'forecast_name': forecast.name,
        'start_date': forecast.start_date.isoformat(),
        'end_date': forecast.end_date.isoformat(),
        'orders_count': len(validated_orders),
        'total_realized_value': float(total_realized_value),
        'items': items_realization
    }

