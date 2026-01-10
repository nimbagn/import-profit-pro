#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module Gestion des Objectifs de Vente - Import Profit Pro
Gestion des objectifs de vente pour les commerciaux
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from datetime import datetime, date, UTC
from decimal import Decimal
from sqlalchemy import func, and_, desc
from sqlalchemy.orm import joinedload
from models import (
    db, SalesObjective, SalesObjectiveItem, User, CommercialSale, CommercialSaleItem,
    PromotionTeam, LockisteTeam, VendeurTeam, StockItem, Forecast,
    DepotStock, VehicleStock, Depot, Vehicle
)
from auth import has_permission
from utils_region_filter import (
    get_user_region_id, filter_depots_by_region, filter_vehicles_by_region,
    filter_sales_objectives_by_region
)

# Créer le blueprint
sales_objectives_bp = Blueprint('sales_objectives', __name__, url_prefix='/objectives')

def get_supervised_commercials(user):
    """Récupère les commerciaux supervisés par l'utilisateur"""
    supervised_commercials = []
    
    # Vérifier si l'utilisateur supervise une équipe promotion
    if user.supervised_team_type == 'promotion':
        teams = PromotionTeam.query.filter_by(supervisor_id=user.id).all()
        for team in teams:
            for member in team.members:
                if member.user_id:
                    supervised_commercials.append(member.user_id)
    
    # Vérifier si l'utilisateur supervise une équipe lockiste
    if user.supervised_team_type == 'lockiste':
        teams = LockisteTeam.query.filter_by(supervisor_id=user.id).all()
        for team in teams:
            for member in team.members:
                if member.user_id:
                    supervised_commercials.append(member.user_id)
    
    # Vérifier si l'utilisateur supervise une équipe vendeur
    if user.supervised_team_type == 'vendeur':
        teams = VendeurTeam.query.filter_by(supervisor_id=user.id).all()
        for team in teams:
            for member in team.members:
                if member.user_id:
                    supervised_commercials.append(member.user_id)
    
    # Superviseur général voit tous les commerciaux
    if user.supervised_team_type == 'general' or has_permission(user, 'admin'):
        supervised_commercials = None  # None signifie tous les commerciaux
    
    return supervised_commercials

def get_available_stock_for_commercial(commercial_user):
    """
    Récupère le stock réel disponible pour un commercial
    Retourne un dictionnaire {stock_item_id: available_quantity}
    """
    if not commercial_user or not commercial_user.region_id:
        return {}
    
    # Récupérer les dépôts de la région du commercial
    depots_query = Depot.query.filter_by(region_id=commercial_user.region_id, is_active=True)
    depots = depots_query.all()
    depot_ids = [d.id for d in depots]
    
    # Récupérer les véhicules de la région du commercial
    vehicles_query = Vehicle.query.filter_by(region_id=commercial_user.region_id, status='active')
    vehicles = vehicles_query.all()
    vehicle_ids = [v.id for v in vehicles]
    
    # Calculer le stock total par article (dépôts + véhicules)
    stock_by_item = {}
    
    # Stock dans les dépôts
    if depot_ids:
        depot_stocks = db.session.query(
            DepotStock.stock_item_id,
            func.sum(DepotStock.quantity).label('total_quantity')
        ).filter(
            DepotStock.depot_id.in_(depot_ids)
        ).group_by(DepotStock.stock_item_id).all()
        
        for stock_item_id, total_qty in depot_stocks:
            if stock_item_id not in stock_by_item:
                stock_by_item[stock_item_id] = Decimal('0')
            stock_by_item[stock_item_id] += Decimal(str(total_qty))
    
    # Stock dans les véhicules
    if vehicle_ids:
        vehicle_stocks = db.session.query(
            VehicleStock.stock_item_id,
            func.sum(VehicleStock.quantity).label('total_quantity')
        ).filter(
            VehicleStock.vehicle_id.in_(vehicle_ids)
        ).group_by(VehicleStock.stock_item_id).all()
        
        for stock_item_id, total_qty in vehicle_stocks:
            if stock_item_id not in stock_by_item:
                stock_by_item[stock_item_id] = Decimal('0')
            stock_by_item[stock_item_id] += Decimal(str(total_qty))
    
    return stock_by_item

def get_stock_items_with_availability(commercial_user):
    """
    Récupère les articles de stock avec leur disponibilité pour un commercial
    Retourne une liste de tuples (stock_item, available_quantity)
    """
    # Récupérer tous les articles actifs
    stock_items = StockItem.query.filter_by(is_active=True).order_by(StockItem.name).all()
    
    # Récupérer le stock disponible pour le commercial
    available_stock = get_available_stock_for_commercial(commercial_user)
    
    # Combiner les données
    items_with_stock = []
    for item in stock_items:
        available_qty = available_stock.get(item.id, Decimal('0'))
        # Ne retourner que les articles avec du stock disponible
        if available_qty > 0:
            items_with_stock.append({
                'item': item,
                'available_quantity': float(available_qty)
            })
    
    return items_with_stock

@sales_objectives_bp.route('/')
@login_required
def objectives_list():
    """Liste des objectifs de vente"""
    if not has_permission(current_user, 'objectives.read'):
        flash("Vous n'avez pas la permission d'accéder à cette page.", "error")
        return redirect(url_for('index'))
    
    # Récupérer les filtres
    commercial_id = request.args.get('commercial_id', type=int)
    period_start = request.args.get('period_start')
    period_end = request.args.get('period_end')
    
    query = SalesObjective.query
    
    # Filtrer par région (sauf admin/supervisor)
    query = filter_sales_objectives_by_region(query)
    
    # Filtrer par commerciaux supervisés
    supervised_commercials = get_supervised_commercials(current_user)
    if supervised_commercials is not None:
        query = query.filter(SalesObjective.commercial_id.in_(supervised_commercials))
    elif not has_permission(current_user, 'admin'):
        query = query.filter_by(supervisor_id=current_user.id)
    
    # Appliquer les filtres
    if commercial_id:
        query = query.filter_by(commercial_id=commercial_id)
    if period_start:
        query = query.filter(SalesObjective.period_start >= datetime.strptime(period_start, '%Y-%m-%d').date())
    if period_end:
        query = query.filter(SalesObjective.period_end <= datetime.strptime(period_end, '%Y-%m-%d').date())
    
    objectives = query.options(
        joinedload(SalesObjective.commercial),
        joinedload(SalesObjective.supervisor)
    ).order_by(desc(SalesObjective.period_start)).all()
    
    # Calculer la progression pour chaque objectif
    objectives_with_progress = []
    for obj in objectives:
        achieved_amount = CommercialSale.query.filter_by(
            commercial_id=obj.commercial_id,
            status='confirmed'
        ).filter(
            CommercialSale.sale_date >= obj.period_start,
            CommercialSale.sale_date <= obj.period_end
        ).with_entities(func.sum(CommercialSale.total_amount_gnf)).scalar() or Decimal('0')
        
        achieved_quantity = None
        if obj.target_quantity:
            achieved_quantity = CommercialSaleItem.query.join(
                CommercialSale, CommercialSaleItem.sale_id == CommercialSale.id
            ).filter(
                CommercialSale.commercial_id == obj.commercial_id,
                CommercialSale.status == 'confirmed',
                CommercialSale.sale_date >= obj.period_start,
                CommercialSale.sale_date <= obj.period_end
            ).with_entities(func.sum(CommercialSaleItem.quantity)).scalar() or Decimal('0')
        
        progress_pct_amount = (achieved_amount / obj.target_amount_gnf * 100) if obj.target_amount_gnf > 0 else 0
        progress_pct_quantity = (achieved_quantity / obj.target_quantity * 100) if obj.target_quantity and obj.target_quantity > 0 else None
        
        objectives_with_progress.append({
            'objective': obj,
            'achieved_amount': achieved_amount,
            'achieved_quantity': achieved_quantity,
            'progress_pct_amount': float(progress_pct_amount),
            'progress_pct_quantity': float(progress_pct_quantity) if progress_pct_quantity else None
        })
    
    # Récupérer les commerciaux pour le filtre
    if supervised_commercials:
        commercials = User.query.filter(User.id.in_(supervised_commercials)).all()
    else:
        commercials = User.query.join(SalesObjective, User.id == SalesObjective.commercial_id).distinct().all()
    
    return render_template('sales_objectives/objectives_list.html',
                         objectives_with_progress=objectives_with_progress,
                         commercials=commercials,
                         commercial_id=commercial_id,
                         period_start=period_start,
                         period_end=period_end)

@sales_objectives_bp.route('/new', methods=['GET', 'POST'])
@login_required
def objective_new():
    """Créer un nouvel objectif"""
    if not has_permission(current_user, 'objectives.write'):
        flash("Vous n'avez pas la permission de créer un objectif.", "error")
        return redirect(url_for('sales_objectives.objectives_list'))
    
    if request.method == 'POST':
        try:
            # Récupérer le forecast_id si fourni
            forecast_id = request.form.get('forecast_id')
            forecast_id = int(forecast_id) if forecast_id else None
            
            # Calculer le montant total depuis les articles
            article_ids = request.form.getlist('article_ids[]')
            quantities = request.form.getlist('quantities[]')
            prices = request.form.getlist('prices[]')
            
            total_amount = Decimal('0')
            total_quantity = Decimal('0')
            
            for i, article_id in enumerate(article_ids):
                if article_id and i < len(quantities) and i < len(prices):
                    qty = Decimal(quantities[i]) if quantities[i] else Decimal('0')
                    price = Decimal(prices[i]) if prices[i] else Decimal('0')
                    total_amount += qty * price
                    total_quantity += qty
            
            # Utiliser le montant total calculé ou celui fourni dans le formulaire
            target_amount = Decimal(request.form.get('target_amount_gnf')) if request.form.get('target_amount_gnf') else total_amount
            
            objective = SalesObjective(
                commercial_id=int(request.form.get('commercial_id')),
                supervisor_id=current_user.id,
                forecast_id=forecast_id,
                period_start=datetime.strptime(request.form.get('period_start'), '%Y-%m-%d').date(),
                period_end=datetime.strptime(request.form.get('period_end'), '%Y-%m-%d').date(),
                target_amount_gnf=target_amount,
                target_quantity=total_quantity if total_quantity > 0 else None
            )
            db.session.add(objective)
            db.session.flush()  # Pour obtenir l'ID
            
            # Ajouter les articles
            for i, article_id in enumerate(article_ids):
                if article_id and i < len(quantities) and i < len(prices):
                    item = SalesObjectiveItem(
                        objective_id=objective.id,
                        stock_item_id=int(article_id),
                        target_quantity=Decimal(quantities[i]) if quantities[i] else Decimal('0'),
                        selling_price_gnf=Decimal(prices[i]) if prices[i] else Decimal('0')
                    )
                    db.session.add(item)
            
            db.session.commit()
            flash("Objectif créé avec succès!", "success")
            return redirect(url_for('sales_objectives.objective_progress', id=objective.id))
        except Exception as e:
            db.session.rollback()
            flash(f"Erreur lors de la création: {str(e)}", "error")
    
    # Récupérer les commerciaux supervisés
    supervised_commercials = get_supervised_commercials(current_user)
    if supervised_commercials:
        commercials = User.query.filter(User.id.in_(supervised_commercials)).all()
    else:
        commercials = User.query.filter_by(is_active=True).all()
    
    # Récupérer les forecasts disponibles
    forecasts = Forecast.query.filter_by(status='active').order_by(Forecast.start_date.desc()).all()
    
    # Pour le formulaire initial, on ne peut pas filtrer par commercial
    # On retournera tous les articles actifs, mais le JavaScript filtrera selon le commercial sélectionné
    stock_items = StockItem.query.filter_by(is_active=True).order_by(StockItem.name).all()
    
    return render_template('sales_objectives/objective_form.html',
                         objective=None, commercials=commercials, stock_items=stock_items, 
                         forecasts=forecasts, available_stock={})

@sales_objectives_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def objective_edit(id):
    """Modifier un objectif"""
    if not has_permission(current_user, 'objectives.write'):
        flash("Vous n'avez pas la permission de modifier un objectif.", "error")
        return redirect(url_for('sales_objectives.objectives_list'))
    
    objective = SalesObjective.query.get_or_404(id)
    
    # Vérifier que c'est le superviseur qui a créé l'objectif ou un admin
    if objective.supervisor_id != current_user.id and not has_permission(current_user, 'admin'):
        flash("Vous ne pouvez modifier que les objectifs que vous avez créés.", "error")
        return redirect(url_for('sales_objectives.objectives_list'))
    
    if request.method == 'POST':
        try:
            # Récupérer le forecast_id si fourni
            forecast_id = request.form.get('forecast_id')
            forecast_id = int(forecast_id) if forecast_id else None
            
            # Supprimer les articles existants
            SalesObjectiveItem.query.filter_by(objective_id=objective.id).delete()
            
            # Calculer le montant total depuis les articles
            article_ids = request.form.getlist('article_ids[]')
            quantities = request.form.getlist('quantities[]')
            prices = request.form.getlist('prices[]')
            
            total_amount = Decimal('0')
            total_quantity = Decimal('0')
            
            for i, article_id in enumerate(article_ids):
                if article_id and i < len(quantities) and i < len(prices):
                    qty = Decimal(quantities[i]) if quantities[i] else Decimal('0')
                    price = Decimal(prices[i]) if prices[i] else Decimal('0')
                    total_amount += qty * price
                    total_quantity += qty
                    
                    item = SalesObjectiveItem(
                        objective_id=objective.id,
                        stock_item_id=int(article_id),
                        target_quantity=qty,
                        selling_price_gnf=price
                    )
                    db.session.add(item)
            
            # Utiliser le montant total calculé ou celui fourni dans le formulaire
            target_amount = Decimal(request.form.get('target_amount_gnf')) if request.form.get('target_amount_gnf') else total_amount
            
            objective.commercial_id = int(request.form.get('commercial_id'))
            objective.forecast_id = forecast_id
            objective.period_start = datetime.strptime(request.form.get('period_start'), '%Y-%m-%d').date()
            objective.period_end = datetime.strptime(request.form.get('period_end'), '%Y-%m-%d').date()
            objective.target_amount_gnf = target_amount
            objective.target_quantity = total_quantity if total_quantity > 0 else None
            
            db.session.commit()
            flash("Objectif modifié avec succès!", "success")
            return redirect(url_for('sales_objectives.objective_progress', id=objective.id))
        except Exception as e:
            db.session.rollback()
            flash(f"Erreur lors de la modification: {str(e)}", "error")
    
    # Récupérer les commerciaux supervisés
    supervised_commercials = get_supervised_commercials(current_user)
    if supervised_commercials:
        commercials = User.query.filter(User.id.in_(supervised_commercials)).all()
    else:
        commercials = User.query.filter_by(is_active=True).all()
    
    # Récupérer les forecasts disponibles
    forecasts = Forecast.query.filter_by(status='active').order_by(Forecast.start_date.desc()).all()
    
    # Récupérer le stock disponible pour le commercial de cet objectif
    commercial_user = objective.commercial
    available_stock = get_available_stock_for_commercial(commercial_user) if commercial_user else {}
    
    # Récupérer tous les articles actifs
    stock_items = StockItem.query.filter_by(is_active=True).order_by(StockItem.name).all()
    
    return render_template('sales_objectives/objective_form.html',
                         objective=objective, commercials=commercials, stock_items=stock_items, 
                         forecasts=forecasts, available_stock=available_stock)

@sales_objectives_bp.route('/api/stock/<int:commercial_id>')
@login_required
def api_commercial_stock(commercial_id):
    """API pour récupérer le stock disponible d'un commercial"""
    if not has_permission(current_user, 'objectives.read'):
        return jsonify({'error': 'Permission denied'}), 403
    
    commercial = User.query.get_or_404(commercial_id)
    available_stock = get_available_stock_for_commercial(commercial)
    
    # Convertir Decimal en float pour JSON
    stock_data = {str(k): float(v) for k, v in available_stock.items()}
    
    return jsonify({
        'commercial_id': commercial_id,
        'commercial_name': commercial.full_name or commercial.username,
        'available_stock': stock_data
    })

@sales_objectives_bp.route('/<int:id>/progress')
@login_required
def objective_progress(id):
    """Suivi de progression d'un objectif"""
    if not has_permission(current_user, 'objectives.read'):
        flash("Vous n'avez pas la permission d'accéder à cette page.", "error")
        return redirect(url_for('index'))
    
    objective = SalesObjective.query.options(
        joinedload(SalesObjective.commercial),
        joinedload(SalesObjective.supervisor)
    ).get_or_404(id)
    
    # Calculer les ventes réalisées
    sales = CommercialSale.query.filter_by(
        commercial_id=objective.commercial_id,
        status='confirmed'
    ).filter(
        CommercialSale.sale_date >= objective.period_start,
        CommercialSale.sale_date <= objective.period_end
    ).options(
        joinedload(CommercialSale.items).joinedload(CommercialSaleItem.stock_item)
    ).order_by(desc(CommercialSale.sale_date)).all()
    
    # Calculer les totaux
    achieved_amount = sum(sale.total_amount_gnf for sale in sales)
    achieved_quantity = None
    if objective.target_quantity:
        achieved_quantity = CommercialSaleItem.query.join(
            CommercialSale, CommercialSaleItem.sale_id == CommercialSale.id
        ).filter(
            CommercialSale.commercial_id == objective.commercial_id,
            CommercialSale.status == 'confirmed',
            CommercialSale.sale_date >= objective.period_start,
            CommercialSale.sale_date <= objective.period_end
        ).with_entities(func.sum(CommercialSaleItem.quantity)).scalar() or Decimal('0')
    
    progress_pct_amount = (achieved_amount / objective.target_amount_gnf * 100) if objective.target_amount_gnf > 0 else 0
    progress_pct_quantity = (achieved_quantity / objective.target_quantity * 100) if objective.target_quantity and objective.target_quantity > 0 and achieved_quantity else None
    
    # Calculer les jours restants
    today = date.today()
    days_remaining = (objective.period_end - today).days if today <= objective.period_end else 0
    days_elapsed = (today - objective.period_start).days if today >= objective.period_start else 0
    total_days = (objective.period_end - objective.period_start).days + 1
    
    # Calculer le rythme nécessaire
    remaining_amount = objective.target_amount_gnf - achieved_amount
    daily_rate_needed = remaining_amount / days_remaining if days_remaining > 0 else Decimal('0')
    
    return render_template('sales_objectives/objective_progress.html',
                         objective=objective,
                         sales=sales,
                         achieved_amount=achieved_amount,
                         achieved_quantity=achieved_quantity,
                         progress_pct_amount=float(progress_pct_amount),
                         progress_pct_quantity=float(progress_pct_quantity) if progress_pct_quantity else None,
                         days_remaining=days_remaining,
                         days_elapsed=days_elapsed,
                         total_days=total_days,
                         daily_rate_needed=daily_rate_needed)

