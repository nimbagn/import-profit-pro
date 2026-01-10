#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Routes pour déclencher manuellement les notifications automatiques
"""

from flask import Blueprint, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from auth import has_permission

notifications_bp = Blueprint('notifications', __name__, url_prefix='/notifications')

@notifications_bp.route('/inventaire-stock', methods=['POST'])
@login_required
def envoyer_inventaire_stock():
    """Déclencher l'envoi de l'inventaire de stock"""
    if not has_permission(current_user, 'stocks.read'):
        flash('Vous n\'avez pas la permission d\'envoyer des notifications', 'error')
        return redirect(url_for('index'))
    
    try:
        from notifications_automatiques import notifications_automatiques
        
        depot_id = request.form.get('depot_id', type=int) or None
        
        success = notifications_automatiques.notifier_inventaire_stock(depot_id=depot_id)
        
        if success:
            flash('Inventaire de stock envoyé avec succès', 'success')
        else:
            flash('Erreur lors de l\'envoi de l\'inventaire', 'error')
    except Exception as e:
        flash(f'Erreur: {str(e)}', 'error')
        import traceback
        traceback.print_exc()
    
    return redirect(request.referrer or url_for('index'))

@notifications_bp.route('/situation-stock', methods=['POST'])
@login_required
def envoyer_situation_stock():
    """Déclencher l'envoi de la situation de stock par période"""
    if not has_permission(current_user, 'stocks.read'):
        flash('Vous n\'avez pas la permission d\'envoyer des notifications', 'error')
        return redirect(url_for('index'))
    
    try:
        from notifications_automatiques import notifications_automatiques
        
        depot_id = request.form.get('depot_id', type=int) or None
        period = request.form.get('period', 'all')
        start_date = request.form.get('start_date') or None
        end_date = request.form.get('end_date') or None
        vehicle_id = request.form.get('vehicle_id', type=int) or None
        stock_item_id = request.form.get('stock_item_id', type=int) or None
        
        success = notifications_automatiques.notifier_situation_stock_periode(
            depot_id=depot_id,
            period=period,
            start_date=start_date,
            end_date=end_date,
            vehicle_id=vehicle_id,
            stock_item_id=stock_item_id
        )
        
        if success:
            period_display = period if period != 'all' else 'Toutes périodes'
            flash(f'Situation de stock ({period_display}) envoyée avec succès par WhatsApp', 'success')
        else:
            flash('Erreur lors de l\'envoi de la situation de stock. Vérifiez les logs pour plus de détails.', 'error')
    except Exception as e:
        flash(f'Erreur: {str(e)}', 'error')
        import traceback
        traceback.print_exc()
    
    return redirect(request.referrer or url_for('stocks.stock_summary'))

@notifications_bp.route('/rappels-vehicules', methods=['POST'])
@login_required
def envoyer_rappels_vehicules():
    """Déclencher l'envoi des rappels véhicules"""
    if not has_permission(current_user, 'vehicles.read'):
        flash('Vous n\'avez pas la permission d\'envoyer des notifications', 'error')
        return redirect(url_for('index'))
    
    try:
        from flotte_notifications import envoyer_rappels_vehicules
        
        nb_rappels = envoyer_rappels_vehicules()
        
        if nb_rappels > 0:
            flash(f'{nb_rappels} rappel(s) véhicules envoyé(s) avec succès', 'success')
        else:
            flash('Aucun rappel à envoyer', 'info')
    except Exception as e:
        flash(f'Erreur: {str(e)}', 'error')
        import traceback
        traceback.print_exc()
    
    return redirect(request.referrer or url_for('index'))

