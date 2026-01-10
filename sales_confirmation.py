#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module Confirmation des Ventes - Import Profit Pro
Gestion de la confirmation des ventes par les superviseurs
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from datetime import datetime, date, UTC, timedelta
from decimal import Decimal
from sqlalchemy import func, and_, or_, desc
from sqlalchemy.orm import joinedload
from models import (
    db, CommercialOrder, CommercialOrderClient, CommercialOrderItem,
    CommercialSale, CommercialSaleItem, User, StockItem, SalesObjective, SalesObjectiveItem,
    PromotionTeam, LockisteTeam, VendeurTeam, DepotStock, VehicleStock, Depot, Vehicle
)
from auth import has_permission
from utils_region_filter import (
    get_user_region_id, filter_commercial_orders_by_region,
    filter_commercial_sales_by_region
)

# Créer le blueprint
sales_confirmation_bp = Blueprint('sales_confirmation', __name__, url_prefix='/sales')

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

def get_supervisor_global_objectives(supervisor_user, start_date=None, end_date=None):
    """
    Calcule l'objectif global du superviseur en agrégant les objectifs de tous ses commerciaux
    Retourne un dictionnaire {stock_item_id: {'target_quantity': qty, 'target_value': value}}
    """
    supervised_commercials = get_supervised_commercials(supervisor_user)
    
    if supervised_commercials is None:
        # Admin voit tout
        objectives_query = SalesObjective.query
    elif supervised_commercials:
        objectives_query = SalesObjective.query.filter(SalesObjective.commercial_id.in_(supervised_commercials))
    else:
        objectives_query = SalesObjective.query.filter_by(supervisor_id=supervisor_user.id)
    
    # Filtrer par période si fournie
    if start_date:
        objectives_query = objectives_query.filter(SalesObjective.period_start <= end_date if end_date else date.today())
    if end_date:
        objectives_query = objectives_query.filter(SalesObjective.period_end >= start_date if start_date else date.today())
    
    objectives = objectives_query.options(
        joinedload(SalesObjective.items).joinedload(SalesObjectiveItem.stock_item)
    ).all()
    
    # Agrégation par article
    global_objectives = {}
    for objective in objectives:
        for item in objective.items:
            stock_item_id = item.stock_item_id
            if stock_item_id not in global_objectives:
                global_objectives[stock_item_id] = {
                    'stock_item': item.stock_item,
                    'target_quantity': Decimal('0'),
                    'target_value': Decimal('0')
                }
            global_objectives[stock_item_id]['target_quantity'] += item.target_quantity
            global_objectives[stock_item_id]['target_value'] += item.target_value
    
    return global_objectives

def get_supervisor_global_sales(supervisor_user, start_date=None, end_date=None):
    """
    Calcule les ventes globales du superviseur en agrégant les ventes de tous ses commerciaux
    Retourne un dictionnaire {stock_item_id: {'sold_quantity': qty, 'sold_value': value}}
    """
    supervised_commercials = get_supervised_commercials(supervisor_user)
    
    sales_query = CommercialSale.query.filter_by(status='confirmed')
    
    # Filtrer par commerciaux supervisés
    if supervised_commercials is not None:
        sales_query = sales_query.filter(CommercialSale.commercial_id.in_(supervised_commercials))
    elif not has_permission(supervisor_user, 'admin'):
        sales_query = sales_query.filter_by(supervisor_id=supervisor_user.id)
    
    # Filtrer par période si fournie
    if start_date:
        sales_query = sales_query.filter(CommercialSale.sale_date >= start_date)
    if end_date:
        sales_query = sales_query.filter(CommercialSale.sale_date <= end_date)
    
    sales = sales_query.options(
        joinedload(CommercialSale.items).joinedload(CommercialSaleItem.stock_item)
    ).all()
    
    # Agrégation par article
    global_sales = {}
    for sale in sales:
        for item in sale.items:
            stock_item_id = item.stock_item_id
            if stock_item_id not in global_sales:
                global_sales[stock_item_id] = {
                    'stock_item': item.stock_item,
                    'sold_quantity': Decimal('0'),
                    'sold_value': Decimal('0')
                }
            global_sales[stock_item_id]['sold_quantity'] += item.quantity
            global_sales[stock_item_id]['sold_value'] += item.total_price_gnf
    
    return global_sales

def check_stock_availability(order, available_stock):
    """
    Vérifie si le stock est disponible pour tous les articles de la commande
    Retourne (is_available, missing_items)
    """
    missing_items = []
    
    for order_client in order.clients:
        for item in order_client.items:
            required_qty = Decimal(str(item.quantity))
            available_qty = available_stock.get(item.stock_item_id, Decimal('0'))
            
            if required_qty > available_qty:
                missing_items.append({
                    'item': item.stock_item,
                    'required': float(required_qty),
                    'available': float(available_qty),
                    'missing': float(required_qty - available_qty)
                })
    
    return len(missing_items) == 0, missing_items

@sales_confirmation_bp.route('/orders-to-confirm')
@login_required
def orders_to_confirm():
    """Liste des commandes validées à confirmer"""
    if not has_permission(current_user, 'sales.confirm'):
        flash("Vous n'avez pas la permission de confirmer des ventes.", "error")
        return redirect(url_for('index'))
    
    # Récupérer les commandes validées non confirmées
    query = CommercialOrder.query.filter_by(
        status='validated',
        sale_confirmed=False
    )
    
    # Filtrer par région
    query = filter_commercial_orders_by_region(query)
    
    # Filtrer par commerciaux supervisés si nécessaire
    supervised_commercials = get_supervised_commercials(current_user)
    if supervised_commercials is not None:
        query = query.filter(CommercialOrder.commercial_id.in_(supervised_commercials))
    
    orders = query.options(
        joinedload(CommercialOrder.commercial),
        joinedload(CommercialOrder.clients).joinedload(CommercialOrderClient.items).joinedload(CommercialOrderItem.stock_item)
    ).order_by(desc(CommercialOrder.order_date)).all()
    
    return render_template('sales_confirmation/orders_to_confirm.html', orders=orders)

@sales_confirmation_bp.route('/confirm/<int:order_id>', methods=['GET', 'POST'])
@login_required
def confirm_sale(order_id):
    """Confirmer une commande en tant que vente"""
    if not has_permission(current_user, 'sales.confirm'):
        flash("Vous n'avez pas la permission de confirmer des ventes.", "error")
        return redirect(url_for('index'))
    
    order = CommercialOrder.query.options(
        joinedload(CommercialOrder.commercial),
        joinedload(CommercialOrder.clients).joinedload(CommercialOrderClient.items).joinedload(CommercialOrderItem.stock_item)
    ).get_or_404(order_id)
    
    # Vérifier que la commande est validée et non confirmée
    if order.status != 'validated':
        flash("Seules les commandes validées peuvent être confirmées.", "error")
        return redirect(url_for('sales_confirmation.orders_to_confirm'))
    
    if order.sale_confirmed:
        # Récupérer la première vente confirmée pour cette commande
        first_sale = CommercialSale.query.filter_by(order_id=order.id, status='confirmed').first()
        if first_sale:
            return redirect(url_for('sales_confirmation.sale_detail', id=first_sale.id))
        else:
            return redirect(url_for('sales_confirmation.confirmed_sales'))
    
    # Vérifier que le commercial est supervisé
    supervised_commercials = get_supervised_commercials(current_user)
    if supervised_commercials is not None and order.commercial_id not in supervised_commercials:
        flash("Vous ne pouvez confirmer que les ventes de vos commerciaux.", "error")
        return redirect(url_for('sales_confirmation.orders_to_confirm'))
    
    if request.method == 'POST':
        try:
            # Vérifier le stock disponible AVANT de confirmer
            available_stock = get_available_stock_for_commercial(order.commercial)
            is_available, missing_items = check_stock_availability(order, available_stock)
            
            if not is_available:
                error_msg = "Stock insuffisant pour confirmer cette vente:\n"
                for missing in missing_items:
                    error_msg += f"- {missing['item'].name}: Requis {missing['required']}, Disponible {missing['available']}, Manquant {missing['missing']}\n"
                flash(error_msg, "error")
                # Recharger le formulaire avec les informations de stock
                from datetime import date
                return render_template('sales_confirmation/confirm_sale_form.html', 
                                     order=order, today=date.today(), 
                                     available_stock=available_stock, 
                                     missing_items=missing_items)
            
            # Récupérer les données du formulaire
            invoice_number = request.form.get('invoice_number')
            invoice_date = datetime.strptime(request.form.get('invoice_date'), '%Y-%m-%d').date()
            sale_date = datetime.strptime(request.form.get('sale_date'), '%Y-%m-%d').date()
            total_amount_gnf = Decimal(request.form.get('total_amount_gnf'))
            payment_method = request.form.get('payment_method')
            payment_status = request.form.get('payment_status')
            payment_due_date = datetime.strptime(request.form.get('payment_due_date'), '%Y-%m-%d').date() if request.form.get('payment_due_date') else None
            notes = request.form.get('notes')
            
            # Pour chaque client de la commande
            for order_client in order.clients:
                # Calculer le montant total pour ce client
                client_total = Decimal('0')
                for item in order_client.items:
                    quantity = Decimal(str(item.quantity))
                    unit_price = Decimal(str(item.unit_price_gnf)) if item.unit_price_gnf else Decimal('0')
                    client_total += quantity * unit_price
                
                # Créer la vente confirmée
                sale = CommercialSale(
                    order_id=order.id,
                    order_client_id=order_client.id,
                    commercial_id=order.commercial_id,
                    supervisor_id=current_user.id,
                    invoice_number=f"{invoice_number}-{order_client.id}" if len(order.clients) > 1 else invoice_number,
                    invoice_date=invoice_date,
                    sale_date=sale_date,
                    total_amount_gnf=client_total if len(order.clients) > 1 else total_amount_gnf,
                    payment_method=payment_method,
                    payment_status=payment_status,
                    payment_due_date=payment_due_date,
                    notes=notes,
                    status='confirmed'
                )
                db.session.add(sale)
                db.session.flush()
                
                # Créer les détails de la vente
                for item in order_client.items:
                    quantity = Decimal(str(item.quantity))
                    unit_price = Decimal(str(item.unit_price_gnf)) if item.unit_price_gnf else Decimal('0')
                    total_price = quantity * unit_price
                    
                    sale_item = CommercialSaleItem(
                        sale_id=sale.id,
                        stock_item_id=item.stock_item_id,
                        quantity=quantity,
                        unit_price_gnf=unit_price,
                        total_price_gnf=total_price
                    )
                    db.session.add(sale_item)
            
            # Mettre à jour la commande
            order.sale_confirmed = True
            order.sale_confirmed_at = datetime.now(UTC)
            order.sale_confirmed_by_id = current_user.id
            
            db.session.commit()
            flash("Vente confirmée avec succès!", "success")
            return redirect(url_for('sales_confirmation.confirmed_sales'))
        except Exception as e:
            db.session.rollback()
            flash(f"Erreur lors de la confirmation: {str(e)}", "error")
    
    # Récupérer le stock disponible pour le commercial
    available_stock = get_available_stock_for_commercial(order.commercial)
    is_available, missing_items = check_stock_availability(order, available_stock)
    
    from datetime import date
    return render_template('sales_confirmation/confirm_sale_form.html', 
                         order=order, today=date.today(),
                         available_stock=available_stock,
                         missing_items=missing_items if not is_available else [])

@sales_confirmation_bp.route('/confirmed')
@login_required
def confirmed_sales():
    """Liste des ventes confirmées"""
    if not has_permission(current_user, 'sales.view_confirmed'):
        flash("Vous n'avez pas la permission de voir les ventes confirmées.", "error")
        return redirect(url_for('index'))
    
    # Récupérer les filtres
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    commercial_id = request.args.get('commercial_id', type=int)
    payment_status = request.args.get('payment_status')
    order_id = request.args.get('order_id', type=int)
    
    query = CommercialSale.query.filter_by(status='confirmed')
    # Filtrer par région (sauf admin/supervisor)
    query = filter_commercial_sales_by_region(query)
    
    # Filtrer par commerciaux supervisés
    supervised_commercials = get_supervised_commercials(current_user)
    if supervised_commercials is not None:
        query = query.filter(CommercialSale.commercial_id.in_(supervised_commercials))
    elif not has_permission(current_user, 'admin'):
        query = query.filter_by(supervisor_id=current_user.id)
    
    # Appliquer les filtres
    if date_from:
        query = query.filter(CommercialSale.sale_date >= datetime.strptime(date_from, '%Y-%m-%d').date())
    if date_to:
        query = query.filter(CommercialSale.sale_date <= datetime.strptime(date_to, '%Y-%m-%d').date())
    if commercial_id:
        query = query.filter_by(commercial_id=commercial_id)
    if payment_status:
        query = query.filter_by(payment_status=payment_status)
    if order_id:
        query = query.filter_by(order_id=order_id)
    
    sales = query.options(
        joinedload(CommercialSale.commercial),
        joinedload(CommercialSale.supervisor),
        joinedload(CommercialSale.items).joinedload(CommercialSaleItem.stock_item)
    ).order_by(desc(CommercialSale.sale_date)).all()
    
    # Calculer les statistiques
    total_amount = sum(sale.total_amount_gnf for sale in sales)
    total_count = len(sales)
    
    # Récupérer les commerciaux pour le filtre
    if supervised_commercials:
        commercials = User.query.filter(User.id.in_(supervised_commercials)).all()
    else:
        commercials = User.query.join(CommercialSale, User.id == CommercialSale.commercial_id).distinct().all()
    
    return render_template('sales_confirmation/confirmed_sales_list.html',
                         sales=sales, total_amount=total_amount, total_count=total_count,
                         commercials=commercials, date_from=date_from, date_to=date_to,
                         commercial_id=commercial_id, payment_status=payment_status, order_id=order_id)

@sales_confirmation_bp.route('/<int:id>')
@login_required
def sale_detail(id):
    """Détails d'une vente confirmée"""
    if not has_permission(current_user, 'sales.view_confirmed'):
        flash("Vous n'avez pas la permission de voir les ventes confirmées.", "error")
        return redirect(url_for('index'))
    
    sale = CommercialSale.query.options(
        joinedload(CommercialSale.commercial),
        joinedload(CommercialSale.supervisor),
        joinedload(CommercialSale.order),
        joinedload(CommercialSale.order_client),
        joinedload(CommercialSale.items).joinedload(CommercialSaleItem.stock_item)
    ).get_or_404(id)
    
    return render_template('sales_confirmation/sale_detail.html', sale=sale)

@sales_confirmation_bp.route('/<int:id>/cancel', methods=['POST'])
@login_required
def cancel_sale(id):
    """Annuler une vente confirmée"""
    if not has_permission(current_user, 'sales.confirm'):
        flash("Vous n'avez pas la permission d'annuler des ventes.", "error")
        return redirect(url_for('index'))
    
    sale = CommercialSale.query.get_or_404(id)
    
    # Vérifier que c'est le superviseur qui a confirmé ou un admin
    if sale.supervisor_id != current_user.id and not has_permission(current_user, 'admin'):
        flash("Vous ne pouvez annuler que les ventes que vous avez confirmées.", "error")
        return redirect(url_for('sales_confirmation.sale_detail', id=id))
    
    try:
        sale.status = 'cancelled'
        sale.order.sale_confirmed = False
        sale.order.sale_confirmed_at = None
        sale.order.sale_confirmed_by_id = None
        db.session.commit()
        flash("Vente annulée avec succès!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Erreur lors de l'annulation: {str(e)}", "error")
    
    return redirect(url_for('sales_confirmation.confirmed_sales'))

@sales_confirmation_bp.route('/supervisor/dashboard')
@login_required
def supervisor_dashboard():
    """Dashboard superviseur avec statistiques"""
    if not has_permission(current_user, 'sales.view_confirmed'):
        flash("Vous n'avez pas la permission d'accéder à cette page.", "error")
        return redirect(url_for('index'))
    
    # Période par défaut : dernier mois
    end_date = date.today()
    start_date = end_date - timedelta(days=30)
    
    # Récupérer les filtres
    date_from = request.args.get('date_from', start_date.strftime('%Y-%m-%d'))
    date_to = request.args.get('date_to', end_date.strftime('%Y-%m-%d'))
    
    if date_from:
        start_date = datetime.strptime(date_from, '%Y-%m-%d').date()
    if date_to:
        end_date = datetime.strptime(date_to, '%Y-%m-%d').date()
    
    # Récupérer les commerciaux supervisés
    supervised_commercials = get_supervised_commercials(current_user)
    
    # Commandes à confirmer
    orders_to_confirm_query = CommercialOrder.query.filter_by(
        status='validated',
        sale_confirmed=False
    )
    if supervised_commercials is not None:
        orders_to_confirm_query = orders_to_confirm_query.filter(CommercialOrder.commercial_id.in_(supervised_commercials))
    orders_to_confirm = orders_to_confirm_query.count()
    
    # Ventes confirmées récentes
    recent_sales_query = CommercialSale.query.filter_by(status='confirmed').filter(
        CommercialSale.sale_date >= start_date,
        CommercialSale.sale_date <= end_date
    )
    if supervised_commercials is not None:
        recent_sales_query = recent_sales_query.filter(CommercialSale.commercial_id.in_(supervised_commercials))
    elif not has_permission(current_user, 'admin'):
        recent_sales_query = recent_sales_query.filter_by(supervisor_id=current_user.id)
    
    recent_sales = recent_sales_query.options(
        joinedload(CommercialSale.commercial)
    ).order_by(desc(CommercialSale.sale_date)).limit(10).all()
    
    # Statistiques globales
    total_sales_amount = recent_sales_query.with_entities(func.sum(CommercialSale.total_amount_gnf)).scalar() or Decimal('0')
    total_sales_count = recent_sales_query.count()
    
    # Top commerciaux
    top_commercials_query = recent_sales_query.with_entities(
        CommercialSale.commercial_id,
        User.full_name,
        func.sum(CommercialSale.total_amount_gnf).label('total_amount'),
        func.count(CommercialSale.id).label('sale_count')
    ).join(User, CommercialSale.commercial_id == User.id).group_by(
        CommercialSale.commercial_id, User.full_name
    ).order_by(desc('total_amount')).limit(5)
    
    top_commercials = top_commercials_query.all()
    
    # Progression objectifs
    objectives = SalesObjective.query.filter(
        SalesObjective.period_start <= end_date,
        SalesObjective.period_end >= start_date
    )
    if supervised_commercials is not None:
        objectives = objectives.filter(SalesObjective.commercial_id.in_(supervised_commercials))
    elif not has_permission(current_user, 'admin'):
        objectives = objectives.filter_by(supervisor_id=current_user.id)
    
    objectives = objectives.options(
        joinedload(SalesObjective.commercial)
    ).all()
    
    # Calculer la progression pour chaque objectif
    objectives_progress = []
    for obj in objectives:
        achieved_amount = recent_sales_query.filter_by(commercial_id=obj.commercial_id).with_entities(
            func.sum(CommercialSale.total_amount_gnf)
        ).scalar() or Decimal('0')
        
        progress_pct = (achieved_amount / obj.target_amount_gnf * 100) if obj.target_amount_gnf > 0 else 0
        
        objectives_progress.append({
            'objective': obj,
            'achieved_amount': achieved_amount,
            'progress_pct': float(progress_pct)
        })
    
    # Calculer l'objectif global du superviseur (agrégation par article)
    global_objectives = get_supervisor_global_objectives(current_user, start_date, end_date)
    
    # Calculer les ventes globales du superviseur (agrégation par article)
    global_sales = get_supervisor_global_sales(current_user, start_date, end_date)
    
    # Combiner objectifs et ventes pour calculer la progression globale par article
    global_progress_by_item = []
    all_item_ids = set(global_objectives.keys()) | set(global_sales.keys())
    
    for item_id in all_item_ids:
        objective_data = global_objectives.get(item_id, {
            'stock_item': global_sales[item_id]['stock_item'] if item_id in global_sales else None,
            'target_quantity': Decimal('0'),
            'target_value': Decimal('0')
        })
        sales_data = global_sales.get(item_id, {
            'stock_item': objective_data['stock_item'],
            'sold_quantity': Decimal('0'),
            'sold_value': Decimal('0')
        })
        
        # Utiliser le stock_item de l'objectif ou des ventes
        stock_item = objective_data['stock_item'] or sales_data['stock_item']
        if not stock_item:
            continue
        
        target_qty = objective_data['target_quantity']
        target_val = objective_data['target_value']
        sold_qty = sales_data['sold_quantity']
        sold_val = sales_data['sold_value']
        
        # Calculer les pourcentages de progression
        progress_pct_qty = (float(sold_qty / target_qty * 100)) if target_qty > 0 else (100.0 if sold_qty > 0 else 0)
        progress_pct_val = (float(sold_val / target_val * 100)) if target_val > 0 else (100.0 if sold_val > 0 else 0)
        
        global_progress_by_item.append({
            'stock_item': stock_item,
            'target_quantity': float(target_qty),
            'target_value': float(target_val),
            'sold_quantity': float(sold_qty),
            'sold_value': float(sold_val),
            'progress_pct_quantity': progress_pct_qty,
            'progress_pct_value': progress_pct_val,
            'remaining_quantity': float(target_qty - sold_qty),
            'remaining_value': float(target_val - sold_val)
        })
    
    # Trier par valeur cible décroissante
    global_progress_by_item.sort(key=lambda x: x['target_value'], reverse=True)
    
    # Calculer les totaux globaux
    total_global_target_amount = sum(item['target_value'] for item in global_progress_by_item)
    total_global_sold_amount = sum(item['sold_value'] for item in global_progress_by_item)
    total_global_target_quantity = sum(item['target_quantity'] for item in global_progress_by_item)
    total_global_sold_quantity = sum(item['sold_quantity'] for item in global_progress_by_item)
    
    total_global_progress_pct = (float(total_global_sold_amount / total_global_target_amount * 100)) if total_global_target_amount > 0 else 0
    
    return render_template('sales_confirmation/supervisor_dashboard.html',
                         orders_to_confirm=orders_to_confirm,
                         recent_sales=recent_sales,
                         total_sales_amount=total_sales_amount,
                         total_sales_count=total_sales_count,
                         top_commercials=top_commercials,
                         objectives_progress=objectives_progress,
                         global_progress_by_item=global_progress_by_item,
                         total_global_target_amount=total_global_target_amount,
                         total_global_sold_amount=total_global_sold_amount,
                         total_global_target_quantity=total_global_target_quantity,
                         total_global_sold_quantity=total_global_sold_quantity,
                         total_global_progress_pct=total_global_progress_pct,
                         date_from=date_from,
                         date_to=date_to)

