#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module Gestion des Stocks - Import Profit Pro
Gestion des stocks par dépôt et véhicule, mouvements de stock
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, make_response
from flask_login import login_required, current_user  # type: ignore
from datetime import datetime, UTC, timedelta
from decimal import Decimal, InvalidOperation
from io import BytesIO
import time
from models import (
    db, DepotStock, VehicleStock, StockMovement, StockItem, 
    Depot, Vehicle, Reception, ReceptionDetail, User,
    StockOutgoing, StockOutgoingDetail, StockReturn, StockReturnDetail,
    StockLoadingSummary, StockLoadingSummaryItem, CommercialOrder, CommercialOrderClient, Role
)
from auth import has_permission
from sqlalchemy.orm import joinedload
from sqlalchemy import or_, and_

# Créer le blueprint
stocks_bp = Blueprint('stocks', __name__, url_prefix='/stocks')

def generate_movement_reference(movement_type='transfer', existing_references=None):
    """Génère une référence unique pour un mouvement de stock"""
    from datetime import datetime, UTC
    prefix_map = {
        'transfer': 'TRANS',
        'reception': 'REC',
        'reception_return': 'RET-REC',  # Retour fournisseur (mouvement inverse de réception)
        'adjustment': 'AJUST',
        'inventory': 'INV'
    }
    prefix = prefix_map.get(movement_type, 'MV')
    date_str = datetime.now().strftime('%Y%m%d')
    
    # Chercher le dernier mouvement du jour avec ce préfixe
    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    last_movement = StockMovement.query.filter(
        StockMovement.reference.like(f'{prefix}-{date_str}-%'),
        StockMovement.created_at >= today_start
    ).order_by(StockMovement.id.desc()).first()
    
    # Déterminer le numéro de départ
    if last_movement and last_movement.reference:
        # Extraire le numéro séquentiel
        try:
            last_num = int(last_movement.reference.split('-')[-1])
            next_num = last_num + 1
        except (ValueError, IndexError):
            next_num = 1
    else:
        next_num = 1
    
    # Si des références existent déjà dans cette transaction, trouver le prochain numéro disponible
    if existing_references:
        used_nums = set()
        for ref in existing_references:
            if ref and ref.startswith(f'{prefix}-{date_str}-'):
                try:
                    num = int(ref.split('-')[-1])
                    used_nums.add(num)
                except (ValueError, IndexError):
                    pass
        
        # Trouver le premier numéro non utilisé
        while next_num in used_nums:
            next_num += 1
    
    return f"{prefix}-{date_str}-{next_num:04d}"

def get_movement_form_data():
    """Helper pour récupérer les données du formulaire de mouvement (filtrées par région)"""
    try:
        from utils_region_filter import filter_depots_by_region, filter_vehicles_by_region
        
        depots_query = Depot.query.filter_by(is_active=True)
        depots_query = filter_depots_by_region(depots_query)
        
        vehicles_query = Vehicle.query.filter_by(status='active')
        vehicles_query = filter_vehicles_by_region(vehicles_query)
        
        return {
            'stock_items': StockItem.query.filter_by(is_active=True).order_by(StockItem.name).all(),
            'depots': depots_query.order_by(Depot.name).all(),
            'vehicles': vehicles_query.order_by(Vehicle.plate_number).all()
        }
    except Exception as e:
        import traceback
        error_msg = f"Erreur dans get_movement_form_data(): {str(e)}\n{traceback.format_exc()}"
        print(f"❌ {error_msg}")
        # Retourner des données vides en cas d'erreur pour éviter un crash complet
        return {
            'stock_items': [],
            'depots': [],
            'vehicles': []
        }

# =========================================================
# STOCKS DÉPÔT
# =========================================================

@stocks_bp.route('/depot/<int:depot_id>')
@login_required
def depot_stock(depot_id):
    """Stock d'un dépôt avec vérification d'accès par région"""
    if not has_permission(current_user, 'stocks.read'):
        flash('Vous n\'avez pas la permission d\'accéder à cette page', 'error')
        return redirect(url_for('index'))
    
    depot = Depot.query.get_or_404(depot_id)
    
    # Vérifier que l'utilisateur peut accéder à ce dépôt (même région)
    from utils_region_filter import can_access_depot
    if not can_access_depot(depot_id):
        flash('Vous n\'avez pas accès à ce dépôt', 'error')
        return redirect(url_for('stocks.depots_list'))
    # Optimisation N+1 : charger stock_item en une seule requête
    stocks = DepotStock.query.filter_by(depot_id=depot_id).options(
        joinedload(DepotStock.stock_item)
    ).all()
    
    # Calculer les totaux
    from auth import can_view_stock_values
    can_view_values = can_view_stock_values(current_user)
    total_value = sum(float(stock.quantity * stock.stock_item.purchase_price_gnf) for stock in stocks) if can_view_values else 0
    total_items = len(stocks)
    low_stock_items = [s for s in stocks if s.quantity < s.stock_item.min_stock_depot]
    
    return render_template('stocks/depot_stock.html', 
                         depot=depot, 
                         stocks=stocks,
                         total_value=total_value,
                         total_items=total_items,
                         low_stock_items=low_stock_items,
                         can_view_stock_values=can_view_values)

@stocks_bp.route('/depot/<int:depot_id>/low')
@login_required
def depot_low_stock(depot_id):
    """Alertes mini-stock d'un dépôt avec vérification d'accès par région"""
    if not has_permission(current_user, 'stocks.read'):
        flash('Vous n\'avez pas la permission d\'accéder à cette page', 'error')
        return redirect(url_for('index'))
    
    depot = Depot.query.get_or_404(depot_id)
    
    # Vérifier que l'utilisateur peut accéder à ce dépôt (même région)
    from utils_region_filter import can_access_depot
    if not can_access_depot(depot_id):
        flash('Vous n\'avez pas accès à ce dépôt', 'error')
        return redirect(url_for('stocks.depots_list'))
    
    # Optimisation N+1 : charger stock_item en une seule requête
    stocks = DepotStock.query.filter_by(depot_id=depot_id).options(
        joinedload(DepotStock.stock_item)
    ).all()
    low_stock_items = [s for s in stocks if s.quantity < s.stock_item.min_stock_depot]
    
    return render_template('stocks/low_stock.html', 
                         depot=depot,
                         low_stock_items=low_stock_items,
                         stock_type='depot')

# =========================================================
# STOCKS VÉHICULE
# =========================================================

@stocks_bp.route('/vehicle/<int:vehicle_id>')
@login_required
def vehicle_stock(vehicle_id):
    """Stock d'un véhicule avec vérification d'accès par région"""
    if not has_permission(current_user, 'stocks.read'):
        flash('Vous n\'avez pas la permission d\'accéder à cette page', 'error')
        return redirect(url_for('index'))
    
    vehicle = Vehicle.query.get_or_404(vehicle_id)
    
    # Vérifier que l'utilisateur peut accéder à ce véhicule (même région)
    from utils_region_filter import can_access_vehicle
    if not can_access_vehicle(vehicle_id):
        flash('Vous n\'avez pas accès à ce véhicule', 'error')
        return redirect(url_for('referentiels.vehicles_list'))
    # Optimisation N+1 : charger stock_item en une seule requête
    stocks = VehicleStock.query.filter_by(vehicle_id=vehicle_id).options(
        joinedload(VehicleStock.stock_item)
    ).all()
    
    # Calculer les totaux
    from auth import can_view_stock_values
    can_view_values = can_view_stock_values(current_user)
    total_value = sum(float(stock.quantity * stock.stock_item.purchase_price_gnf) for stock in stocks) if can_view_values else 0
    total_items = len(stocks)
    low_stock_items = [s for s in stocks if s.quantity < s.stock_item.min_stock_vehicle]
    
    return render_template('stocks/vehicle_stock.html', 
                         vehicle=vehicle, 
                         stocks=stocks,
                         total_value=total_value,
                         total_items=total_items,
                         low_stock_items=low_stock_items,
                         can_view_stock_values=can_view_values)

@stocks_bp.route('/vehicle/<int:vehicle_id>/low')
@login_required
def vehicle_low_stock(vehicle_id):
    """Alertes mini-stock d'un véhicule"""
    if not has_permission(current_user, 'stocks.read'):
        flash('Vous n\'avez pas la permission d\'accéder à cette page', 'error')
        return redirect(url_for('index'))
    
    vehicle = Vehicle.query.get_or_404(vehicle_id)
    stocks = VehicleStock.query.filter_by(vehicle_id=vehicle_id).all()
    low_stock_items = [s for s in stocks if s.quantity < s.stock_item.min_stock_vehicle]
    
    return render_template('stocks/low_stock.html', 
                         vehicle=vehicle,
                         low_stock_items=low_stock_items,
                         stock_type='vehicle')

# =========================================================
# MOUVEMENTS DE STOCK
# =========================================================

@stocks_bp.route('/movements')
@login_required
def movements_list():
    """Liste des mouvements de stock avec pagination et filtres"""
    if not has_permission(current_user, 'movements.read'):
        flash('Vous n\'avez pas la permission d\'accéder à cette page', 'error')
        return redirect(url_for('index'))
    
    from sqlalchemy import or_, and_
    from datetime import datetime, timedelta
    from utils_region_filter import filter_stock_movements_by_region
    
    # Paramètres de pagination
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    
    # Filtres
    movement_type = request.args.get('type', '')
    search = request.args.get('search', '').strip()
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    stock_item_id = request.args.get('stock_item_id', type=int)
    depot_id = request.args.get('depot_id', type=int)
    vehicle_id = request.args.get('vehicle_id', type=int)
    user_id = request.args.get('user_id', type=int)
    
    # Construire la requête avec optimisation N+1
    query = StockMovement.query.options(
        joinedload(StockMovement.stock_item),
        joinedload(StockMovement.from_depot),
        joinedload(StockMovement.to_depot),
        joinedload(StockMovement.from_vehicle),
        joinedload(StockMovement.to_vehicle),
        joinedload(StockMovement.user)
    )
    
    # Filtrer par région de l'utilisateur AVANT d'appliquer les autres filtres
    query = filter_stock_movements_by_region(query)
    
    # Appliquer les filtres
    if movement_type:
        query = query.filter(StockMovement.movement_type == movement_type)
    
    if search:
        search_pattern = f'%{search}%'
        # Joindre StockItem uniquement pour la recherche si nécessaire
        # Utiliser outerjoin pour ne pas exclure les mouvements sans article
        query = query.outerjoin(StockItem, StockMovement.stock_item_id == StockItem.id)
        query = query.filter(
            or_(
                StockMovement.reference.like(search_pattern),
                StockMovement.supplier_name.like(search_pattern),
                StockMovement.bl_number.like(search_pattern),
                StockItem.name.like(search_pattern),
                StockItem.sku.like(search_pattern)
            )
        )
    
    if date_from:
        try:
            date_from_obj = datetime.strptime(date_from, '%Y-%m-%d')
            query = query.filter(StockMovement.movement_date >= date_from_obj)
        except ValueError:
            pass
    
    if date_to:
        try:
            date_to_obj = datetime.strptime(date_to, '%Y-%m-%d') + timedelta(days=1)
            query = query.filter(StockMovement.movement_date < date_to_obj)
        except ValueError:
            pass
    
    if stock_item_id:
        query = query.filter(StockMovement.stock_item_id == stock_item_id)
    
    if depot_id:
        query = query.filter(
            or_(
                StockMovement.from_depot_id == depot_id,
                StockMovement.to_depot_id == depot_id
            )
        )
    
    if vehicle_id:
        query = query.filter(
            or_(
                StockMovement.from_vehicle_id == vehicle_id,
                StockMovement.to_vehicle_id == vehicle_id
            )
        )
    
    if user_id:
        query = query.filter(StockMovement.user_id == user_id)
    
    # Pagination
    pagination = query.order_by(StockMovement.movement_date.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    movements = pagination.items
    
    # Statistiques globales
    total_movements = StockMovement.query.count()
    movements_by_type = {}
    for mtype in ['transfer', 'reception', 'adjustment', 'inventory']:
        movements_by_type[mtype] = StockMovement.query.filter_by(movement_type=mtype).count()
    
    # Statistiques pour graphiques (30 derniers jours) - Limité à 1000 pour performance
    from datetime import datetime, timedelta
    from utils_region_filter import filter_stock_movements_by_region
    thirty_days_ago = datetime.now() - timedelta(days=30)
    recent_movements_query = StockMovement.query.filter(
        StockMovement.movement_date >= thirty_days_ago
    )
    # Filtrer par région
    recent_movements_query = filter_stock_movements_by_region(recent_movements_query)
    # Limiter à 1000 mouvements pour éviter de charger trop de données en mémoire
    recent_movements = recent_movements_query.order_by(StockMovement.movement_date.desc()).limit(1000).all()
    
    # Préparer les données pour le graphique de tendance
    movements_by_date = {}
    for movement in recent_movements:
        date_key = movement.movement_date.strftime('%Y-%m-%d') if movement.movement_date else ''
        if date_key:
            if date_key not in movements_by_date:
                movements_by_date[date_key] = {'transfer': 0, 'reception': 0, 'adjustment': 0, 'inventory': 0, 'total': 0}
            movements_by_date[date_key][movement.movement_type] = movements_by_date[date_key].get(movement.movement_type, 0) + 1
            movements_by_date[date_key]['total'] += 1
    
    # Trier par date
    sorted_dates = sorted(movements_by_date.keys())
    chart_labels = sorted_dates
    chart_transfer = [movements_by_date[d].get('transfer', 0) for d in sorted_dates]
    chart_reception = [movements_by_date[d].get('reception', 0) for d in sorted_dates]
    chart_adjustment = [movements_by_date[d].get('adjustment', 0) for d in sorted_dates]
    chart_inventory = [movements_by_date[d].get('inventory', 0) for d in sorted_dates]
    chart_total = [movements_by_date[d].get('total', 0) for d in sorted_dates]
    
    # Récupérer les données pour les filtres (filtrées par région)
    from utils_region_filter import filter_depots_by_region, filter_vehicles_by_region
    stock_items = StockItem.query.filter_by(is_active=True).order_by(StockItem.name).all()
    depots_query = Depot.query.filter_by(is_active=True)
    depots_query = filter_depots_by_region(depots_query)
    depots = depots_query.order_by(Depot.name).all()
    vehicles_query = Vehicle.query.filter_by(status='active')
    vehicles_query = filter_vehicles_by_region(vehicles_query)
    vehicles = vehicles_query.order_by(Vehicle.plate_number).all()
    users = User.query.order_by(User.username).all()
    
    return render_template('stocks/movements_list.html', 
                         movements=movements,
                         pagination=pagination,
                         movement_type=movement_type,
                         search=search,
                         date_from=date_from,
                         date_to=date_to,
                         stock_item_id=stock_item_id,
                         depot_id=depot_id,
                         vehicle_id=vehicle_id,
                         user_id=user_id,
                         per_page=per_page,
                         total_movements=total_movements,
                         movements_by_type=movements_by_type,
                         stock_items=stock_items,
                         depots=depots,
                         vehicles=vehicles,
                         users=users,
                         chart_labels=chart_labels,
                         chart_transfer=chart_transfer,
                         chart_reception=chart_reception,
                         chart_adjustment=chart_adjustment,
                         chart_inventory=chart_inventory,
                         chart_total=chart_total)

@stocks_bp.route('/movements/export/excel')
@login_required
def movements_export_excel():
    """Export Excel des mouvements avec filtres appliqués"""
    if not has_permission(current_user, 'movements.read'):
        flash("Vous n'avez pas la permission d'exporter les données.", "error")
        return redirect(url_for('stocks.movements_list'))
    
    import pandas as pd
    from sqlalchemy import or_
    
    # Récupérer les mêmes filtres que movements_list
    movement_type = request.args.get('type', '')
    search = request.args.get('search', '').strip()
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    stock_item_id = request.args.get('stock_item_id', type=int)
    depot_id = request.args.get('depot_id', type=int)
    vehicle_id = request.args.get('vehicle_id', type=int)
    user_id = request.args.get('user_id', type=int)
    
    try:
        # Construire la requête (même logique que movements_list)
        query = StockMovement.query.options(
            joinedload(StockMovement.stock_item),
            joinedload(StockMovement.from_depot),
            joinedload(StockMovement.to_depot),
            joinedload(StockMovement.from_vehicle),
            joinedload(StockMovement.to_vehicle),
            joinedload(StockMovement.user)
        )
        
        # Appliquer les filtres
        if movement_type:
            query = query.filter(StockMovement.movement_type == movement_type)
        
        if search:
            query = query.filter(
                or_(
                    StockMovement.reference.like(f'%{search}%'),
                    StockMovement.supplier_name.like(f'%{search}%'),
                    StockMovement.bl_number.like(f'%{search}%')
                )
            )
        
        if date_from:
            try:
                date_from_obj = datetime.strptime(date_from, '%Y-%m-%d')
                query = query.filter(StockMovement.movement_date >= date_from_obj)
            except ValueError:
                pass
        
        if date_to:
            try:
                date_to_obj = datetime.strptime(date_to, '%Y-%m-%d') + timedelta(days=1)
                query = query.filter(StockMovement.movement_date < date_to_obj)
            except ValueError:
                pass
        
        if stock_item_id:
            query = query.filter(StockMovement.stock_item_id == stock_item_id)
        
        if depot_id:
            query = query.filter(
                or_(
                    StockMovement.from_depot_id == depot_id,
                    StockMovement.to_depot_id == depot_id
                )
            )
        
        if vehicle_id:
            query = query.filter(
                or_(
                    StockMovement.from_vehicle_id == vehicle_id,
                    StockMovement.to_vehicle_id == vehicle_id
                )
            )
        
        if user_id:
            query = query.filter(StockMovement.user_id == user_id)
        
        # Récupérer tous les mouvements (sans pagination pour l'export)
        movements = query.order_by(StockMovement.movement_date.desc()).all()
        
        # Préparer les données pour Excel
        data = []
        for movement in movements:
            source = ''
            if movement.from_depot:
                source = f"Dépôt: {movement.from_depot.name}"
            elif movement.from_vehicle:
                source = f"Véhicule: {movement.from_vehicle.plate_number}"
            
            destination = ''
            if movement.to_depot:
                destination = f"Dépôt: {movement.to_depot.name}"
            elif movement.to_vehicle:
                destination = f"Véhicule: {movement.to_vehicle.plate_number}"
            elif movement.supplier_name:
                destination = f"Fournisseur: {movement.supplier_name}"
            
            data.append({
                'Date': movement.movement_date.strftime('%d/%m/%Y %H:%M') if movement.movement_date else '',
                'Référence': movement.reference or '',
                'Type': movement.movement_type.title() if movement.movement_type else '',
                'Article (SKU)': movement.stock_item.sku if movement.stock_item else '',
                'Article': movement.stock_item.name if movement.stock_item else '',
                'Quantité': float(movement.quantity),
                'Source': source,
                'Destination': destination,
                'Utilisateur': movement.user.username if movement.user else '',
                'BL/Fournisseur': movement.bl_number or movement.supplier_name or '',
                'Raison': movement.reason or ''
            })
        
        # Créer le DataFrame
        df = pd.DataFrame(data)
        
        # Ajouter une ligne de totaux
        if len(df) > 0:
            total_row = pd.DataFrame([{
                'Date': 'TOTAL',
                'Référence': '',
                'Type': '',
                'Article (SKU)': '',
                'Article': '',
                'Quantité': df['Quantité'].sum(),
                'Source': '',
                'Destination': '',
                'Utilisateur': '',
                'BL/Fournisseur': '',
                'Raison': ''
            }])
            df = pd.concat([df, total_row], ignore_index=True)
        
        # Créer le fichier Excel
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Mouvements', index=False)
            
            # Formater les colonnes
            worksheet = writer.sheets['Mouvements']
            for idx, col in enumerate(df.columns, 1):
                max_length = max(
                    df[col].astype(str).map(len).max(),
                    len(str(col))
                )
                worksheet.column_dimensions[chr(64 + idx)].width = min(max_length + 2, 40)
        
        output.seek(0)
        filename = f'mouvements_stock_{datetime.now(UTC).strftime("%Y%m%d_%H%M%S")}.xlsx'
        
        response = make_response(output.getvalue())
        response.headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"❌ Erreur lors de l'export Excel: {e}")
        flash(f'Erreur lors de l\'export Excel: {str(e)}', 'error')
        return redirect(url_for('stocks.movements_list'))

@stocks_bp.route('/movements/<reference>')
@login_required
def movement_detail_by_reference(reference):
    """Détail d'un mouvement par sa référence"""
    if not has_permission(current_user, 'movements.read'):
        flash('Vous n\'avez pas la permission d\'accéder à cette page', 'error')
        return redirect(url_for('stocks.movements_list'))
    
    movements = StockMovement.query.filter_by(reference=reference).order_by(StockMovement.id).all()
    
    if not movements:
        flash(f'Aucun mouvement trouvé avec la référence {reference}', 'error')
        return redirect(url_for('stocks.movements_list'))
    
    # Le premier mouvement contient les infos principales (source/destination communes)
    main_movement = movements[0]
    
    return render_template('stocks/movement_detail.html',
                         reference=reference,
                         movements=movements,
                         main_movement=main_movement)

@stocks_bp.route('/movements/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def movement_edit(id):
    """Modifier un mouvement (admin et magasinier)"""
    # Permettre aux admins et aux magasiniers de modifier les mouvements
    from auth import is_admin
    can_edit = is_admin(current_user) or (hasattr(current_user, 'role') and current_user.role and current_user.role.code == 'warehouse')
    if not can_edit:
        flash('Vous n\'avez pas la permission de modifier un mouvement', 'error')
        return redirect(url_for('stocks.movements_list'))
    
    movement = StockMovement.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            # Récupérer les données du formulaire
            movement_date_str = request.form.get('movement_date')
            quantity_str = request.form.get('quantity')
            reason = request.form.get('reason')
            supplier_name = request.form.get('supplier_name')
            bl_number = request.form.get('bl_number')
            
            # Validation
            if not movement_date_str or not quantity_str:
                flash('Veuillez remplir tous les champs obligatoires', 'error')
                form_data = get_movement_form_data()
                return render_template('stocks/movement_edit.html', movement=movement, **form_data)
            
            try:
                movement_date = datetime.strptime(movement_date_str, '%Y-%m-%d')
                quantity = Decimal(quantity_str)
            except (ValueError, TypeError):
                flash('Date ou quantité invalide', 'error')
                form_data = get_movement_form_data()
                return render_template('stocks/movement_edit.html', movement=movement, **form_data)
            
            # Préserver le signe de la quantité selon le type de mouvement
            # Si c'était une sortie (négative), garder le signe négatif
            if movement.quantity < 0:
                signed_quantity = -abs(quantity)
            else:
                signed_quantity = abs(quantity)
            
            # Calculer l'ancienne quantité pour ajuster le stock
            old_quantity = movement.quantity
            quantity_diff = signed_quantity - old_quantity
            
            # Mettre à jour le mouvement
            movement.movement_date = movement_date
            movement.quantity = signed_quantity
            movement.reason = reason if reason else movement.reason
            movement.supplier_name = supplier_name if supplier_name else movement.supplier_name
            movement.bl_number = bl_number if bl_number else movement.bl_number
            
            # Ajuster le stock si nécessaire
            if quantity_diff != 0:
                # Vérifier le stock disponible avant modification
                if movement.from_depot_id:
                    depot_stock = DepotStock.query.filter_by(
                        depot_id=movement.from_depot_id,
                        stock_item_id=movement.stock_item_id
                    ).first()
                    if depot_stock:
                        # Si on augmente la sortie (quantity_diff négatif), vérifier le stock
                        if quantity_diff < 0:
                            new_quantity = depot_stock.quantity - quantity_diff  # quantity_diff est négatif, donc soustraction
                            if new_quantity < 0:
                                flash(f'Stock insuffisant après modification pour {movement.stock_item.name if movement.stock_item else "l\'article"}', 'error')
                                form_data = get_movement_form_data()
                                return render_template('stocks/movement_edit.html', movement=movement, **form_data)
                
                if movement.from_vehicle_id:
                    vehicle_stock = VehicleStock.query.filter_by(
                        vehicle_id=movement.from_vehicle_id,
                        stock_item_id=movement.stock_item_id
                    ).first()
                    if vehicle_stock:
                        # Si on augmente la sortie (quantity_diff négatif), vérifier le stock
                        if quantity_diff < 0:
                            new_quantity = vehicle_stock.quantity - quantity_diff  # quantity_diff est négatif, donc soustraction
                            if new_quantity < 0:
                                flash(f'Stock insuffisant après modification pour {movement.stock_item.name if movement.stock_item else "l\'article"}', 'error')
                                form_data = get_movement_form_data()
                                return render_template('stocks/movement_edit.html', movement=movement, **form_data)
                
                # Si le mouvement a une destination (entrée)
                if movement.to_depot_id:
                    depot_stock = DepotStock.query.filter_by(
                        depot_id=movement.to_depot_id,
                        stock_item_id=movement.stock_item_id
                    ).first()
                    if not depot_stock:
                        depot_stock = DepotStock(
                            depot_id=movement.to_depot_id,
                            stock_item_id=movement.stock_item_id,
                            quantity=Decimal('0')
                        )
                        db.session.add(depot_stock)
                    depot_stock.quantity += quantity_diff
                
                if movement.to_vehicle_id:
                    vehicle_stock = VehicleStock.query.filter_by(
                        vehicle_id=movement.to_vehicle_id,
                        stock_item_id=movement.stock_item_id
                    ).first()
                    if not vehicle_stock:
                        vehicle_stock = VehicleStock(
                            vehicle_id=movement.to_vehicle_id,
                            stock_item_id=movement.stock_item_id,
                            quantity=Decimal('0')
                        )
                        db.session.add(vehicle_stock)
                    vehicle_stock.quantity += quantity_diff
                
                # Si le mouvement a une source (sortie)
                if movement.from_depot_id:
                    depot_stock = DepotStock.query.filter_by(
                        depot_id=movement.from_depot_id,
                        stock_item_id=movement.stock_item_id
                    ).first()
                    if not depot_stock:
                        depot_stock = DepotStock(
                            depot_id=movement.from_depot_id,
                            stock_item_id=movement.stock_item_id,
                            quantity=Decimal('0')
                        )
                        db.session.add(depot_stock)
                    depot_stock.quantity -= quantity_diff  # Inverser car c'est une sortie
                
                if movement.from_vehicle_id:
                    vehicle_stock = VehicleStock.query.filter_by(
                        vehicle_id=movement.from_vehicle_id,
                        stock_item_id=movement.stock_item_id
                    ).first()
                    if not vehicle_stock:
                        vehicle_stock = VehicleStock(
                            vehicle_id=movement.from_vehicle_id,
                            stock_item_id=movement.stock_item_id,
                            quantity=Decimal('0')
                        )
                        db.session.add(vehicle_stock)
                    vehicle_stock.quantity -= quantity_diff  # Inverser car c'est une sortie
            
            db.session.commit()
            flash('Mouvement modifié avec succès', 'success')
            return redirect(url_for('stocks.movement_detail_by_reference', reference=movement.reference))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur lors de la modification: {str(e)}', 'error')
            form_data = get_movement_form_data()
            return render_template('stocks/movement_edit.html', movement=movement, **form_data)
    
    form_data = get_movement_form_data()
    return render_template('stocks/movement_edit.html', movement=movement, **form_data)

@stocks_bp.route('/movements/<int:id>/delete', methods=['POST'])
@login_required
def movement_delete(id):
    """Supprimer un mouvement (admin uniquement)"""
    from auth import is_admin
    if not is_admin(current_user):
        flash('Vous n\'avez pas la permission de supprimer un mouvement', 'error')
        return redirect(url_for('stocks.movements_list'))
    
    movement = StockMovement.query.get_or_404(id)
    reference = movement.reference
    
    try:
        # Vérifier si le mouvement est lié à une réception, sortie ou retour
        # Les mouvements liés à ces opérations ne doivent pas être supprimés directement
        # car cela créerait une incohérence dans les données
        from models import Reception, ReceptionDetail, StockOutgoing, StockOutgoingDetail, StockReturn, StockReturnDetail
        
        # Vérifier si c'est un mouvement de réception
        if movement.movement_type == 'reception' and movement.bl_number:
            reception = Reception.query.filter_by(bl_number=movement.bl_number).first()
            if reception:
                flash('Ce mouvement est lié à une réception. Supprimez d\'abord la réception.', 'error')
                return redirect(url_for('stocks.movement_detail_by_reference', reference=reference))
        
        # Vérifier si c'est un mouvement de sortie (via reason avec marqueur [SORTIE_CLIENT])
        if movement.reason and ('[SORTIE_CLIENT]' in movement.reason or 'Sortie client' in movement.reason):
            # Extraire la référence de sortie depuis le reason si disponible
            import re
            ref_match = re.search(r'Référence sortie: ([A-Z0-9-]+)', movement.reason)
            if ref_match:
                outgoing_ref = ref_match.group(1)
                outgoing = StockOutgoing.query.filter_by(reference=outgoing_ref).first()
                if outgoing:
                    flash(f'Ce mouvement est lié à la sortie "{outgoing_ref}". Supprimez d\'abord la sortie.', 'error')
                    return redirect(url_for('stocks.movement_detail_by_reference', reference=reference))
            else:
                # Chercher une sortie correspondante par date et article
                outgoing = StockOutgoing.query.filter_by(
                    outgoing_date=movement.movement_date.date() if movement.movement_date else None
                ).join(StockOutgoingDetail).filter(
                    StockOutgoingDetail.stock_item_id == movement.stock_item_id
                ).first()
                if outgoing:
                    flash('Ce mouvement est lié à une sortie client. Supprimez d\'abord la sortie.', 'error')
                    return redirect(url_for('stocks.movement_detail_by_reference', reference=reference))
        
        # Vérifier si c'est un mouvement de retour (via reason avec marqueur [RETOUR_CLIENT])
        if movement.reason and ('[RETOUR_CLIENT]' in movement.reason or 'Retour client' in movement.reason):
            # Extraire la référence de retour depuis le reason si disponible
            import re
            ref_match = re.search(r'Référence retour: ([A-Z0-9-]+)', movement.reason)
            if ref_match:
                return_ref = ref_match.group(1)
                return_ = StockReturn.query.filter_by(reference=return_ref).first()
                if return_:
                    flash(f'Ce mouvement est lié au retour "{return_ref}". Supprimez d\'abord le retour.', 'error')
                    return redirect(url_for('stocks.movement_detail_by_reference', reference=reference))
            else:
                # Chercher un retour correspondant par date et article
                return_ = StockReturn.query.filter_by(
                    return_date=movement.movement_date.date() if movement.movement_date else None
                ).join(StockReturnDetail).filter(
                    StockReturnDetail.stock_item_id == movement.stock_item_id
                ).first()
                if return_:
                    flash('Ce mouvement est lié à un retour client. Supprimez d\'abord le retour.', 'error')
                    return redirect(url_for('stocks.movement_detail_by_reference', reference=reference))
        
        # Ajuster le stock en sens inverse
        if movement.quantity > 0:
            # C'était une entrée, on doit diminuer le stock
            if movement.to_depot_id:
                depot_stock = DepotStock.query.filter_by(
                    depot_id=movement.to_depot_id,
                    stock_item_id=movement.stock_item_id
                ).first()
                if depot_stock:
                    depot_stock.quantity -= movement.quantity
            
            if movement.to_vehicle_id:
                vehicle_stock = VehicleStock.query.filter_by(
                    vehicle_id=movement.to_vehicle_id,
                    stock_item_id=movement.stock_item_id
                ).first()
                if vehicle_stock:
                    vehicle_stock.quantity -= movement.quantity
        else:
            # C'était une sortie, on doit augmenter le stock
            if movement.from_depot_id:
                depot_stock = DepotStock.query.filter_by(
                    depot_id=movement.from_depot_id,
                    stock_item_id=movement.stock_item_id
                ).first()
                if depot_stock:
                    depot_stock.quantity += abs(movement.quantity)
            
            if movement.from_vehicle_id:
                vehicle_stock = VehicleStock.query.filter_by(
                    vehicle_id=movement.from_vehicle_id,
                    stock_item_id=movement.stock_item_id
                ).first()
                if vehicle_stock:
                    vehicle_stock.quantity += abs(movement.quantity)
        
        # Supprimer le mouvement
        db.session.delete(movement)
        db.session.commit()
        
        flash('Mouvement supprimé avec succès', 'success')
        return redirect(url_for('stocks.movements_list'))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Erreur lors de la suppression: {str(e)}', 'error')
        return redirect(url_for('stocks.movement_detail_by_reference', reference=reference))

@stocks_bp.route('/api/movements/<reference>')
@login_required
def api_movement_by_reference(reference):
    """API pour récupérer un mouvement par sa référence"""
    movements = StockMovement.query.filter_by(reference=reference).all()
    
    if not movements:
        return jsonify({
            'found': False,
            'message': f'Aucun mouvement trouvé avec la référence {reference}'
        }), 404
    
    result = {
        'found': True,
        'reference': reference,
        'count': len(movements),
        'movements': []
    }
    
    for m in movements:
        movement_data = {
            'id': m.id,
            'reference': m.reference,
            'type': m.movement_type,
            'date': m.movement_date.isoformat() if m.movement_date else None,
            'created_at': m.created_at.isoformat() if m.created_at else None,
            'article': {
                'id': m.stock_item_id,
                'sku': m.stock_item.sku if m.stock_item else None,
                'name': m.stock_item.name if m.stock_item else None
            } if m.stock_item else None,
            'quantity': float(m.quantity),
            'source': {
                'depot': {
                    'id': m.from_depot_id,
                    'name': m.from_depot.name if m.from_depot else None
                } if m.from_depot else None,
                'vehicle': {
                    'id': m.from_vehicle_id,
                    'plate_number': m.from_vehicle.plate_number if m.from_vehicle else None
                } if m.from_vehicle else None
            },
            'destination': {
                'depot': {
                    'id': m.to_depot_id,
                    'name': m.to_depot.name if m.to_depot else None
                } if m.to_depot else None,
                'vehicle': {
                    'id': m.to_vehicle_id,
                    'plate_number': m.to_vehicle.plate_number if m.to_vehicle else None
                } if m.to_vehicle else None
            },
            'user': {
                'id': m.user_id,
                'username': m.user.username if m.user else None
            } if m.user else None,
            'supplier_name': m.supplier_name,
            'bl_number': m.bl_number,
            'reason': m.reason
        }
        result['movements'].append(movement_data)
    
    return jsonify(result)

@stocks_bp.route('/movements/new', methods=['GET', 'POST'])
@login_required
def movement_new():
    """Créer un nouveau mouvement"""
    # Vérifier la permission movements.create OU le rôle warehouse
    has_create_permission = has_permission(current_user, 'movements.create')
    is_warehouse = current_user.role and current_user.role.code == 'warehouse'
    
    if not has_create_permission and not is_warehouse:
        flash('Vous n\'avez pas la permission de créer un mouvement', 'error')
        return redirect(url_for('stocks.movements_list'))
    
    movement_type = request.args.get('type', 'transfer')
    
    if request.method == 'POST':
        movement_type = request.form.get('movement_type')
        
        # Source
        from_depot_id = request.form.get('from_depot_id') or None
        from_vehicle_id = request.form.get('from_vehicle_id') or None
        
        # Destination
        to_depot_id = request.form.get('to_depot_id') or None
        to_vehicle_id = request.form.get('to_vehicle_id') or None
        
        # Réception
        supplier_name = request.form.get('supplier_name')
        bl_number = request.form.get('bl_number')
        
        # Ajustement
        reason = request.form.get('reason')
        
        # Notes sur l'opération (pour tous les types de mouvements)
        operation_notes = request.form.get('operation_notes', '').strip()
        # Si des notes sont fournies, les ajouter à la raison (ou utiliser comme raison si reason est vide)
        if operation_notes:
            if reason:
                reason = f"{reason}\n\nNotes: {operation_notes}"
            else:
                reason = operation_notes
        
        # Traitement selon le type
        try:
            if movement_type == 'transfer':
                # TRANSFERT : Déplacer le stock d'un dépôt/véhicule à un autre
                # 
                # ⚠️ RÈGLE IMPORTANTE : Les transferts N'AUGMENTENT JAMAIS le stock global
                # - Le stock est DÉPLACÉ du point de départ (diminue)
                # - Le stock AUGMENTE dans le dépôt/véhicule de destination de l'équivalent
                # - Impact global : -X + X = 0 (stock global inchangé)
                #
                # Crée 2 mouvements : SORTIE (négatif) depuis la source + ENTRÉE (positif) vers la destination
                
                # Validation : Les dépôts sont obligatoires, les véhicules sont facultatifs
                if not from_depot_id:
                    flash('Le dépôt source est obligatoire', 'error')
                    form_data = get_movement_form_data()
                    return render_template('stocks/movement_form.html', movement_type=movement_type, **form_data)
                
                if not to_depot_id:
                    flash('Le dépôt destination est obligatoire', 'error')
                    form_data = get_movement_form_data()
                    return render_template('stocks/movement_form.html', movement_type=movement_type, **form_data)
                
                # Validation : source et destination ne peuvent pas être identiques
                if (from_depot_id and to_depot_id and int(from_depot_id) == int(to_depot_id)) or \
                   (from_vehicle_id and to_vehicle_id and int(from_vehicle_id) == int(to_vehicle_id)) or \
                   (from_depot_id and to_vehicle_id and int(from_depot_id) == int(to_vehicle_id)) or \
                   (from_vehicle_id and to_depot_id and int(from_vehicle_id) == int(to_depot_id)):
                    flash('La source et la destination ne peuvent pas être identiques', 'error')
                    form_data = get_movement_form_data()
                    return render_template('stocks/movement_form.html', movement_type=movement_type, **form_data)
                
                # Pour les transferts, récupérer plusieurs articles
                stock_item_ids = request.form.getlist('stock_item_ids[]')
                quantities = request.form.getlist('quantities[]')
                
                if not stock_item_ids or len(stock_item_ids) == 0:
                    flash('Veuillez ajouter au moins un article', 'error')
                    form_data = get_movement_form_data()
                    return render_template('stocks/movement_form.html', movement_type=movement_type, **form_data)
                
                movements_created = 0
                errors = []
                generated_references = []  # Pour éviter les doublons dans la même transaction
                
                # Transaction atomique : traiter tous les articles ou aucun
                try:
                    # Traiter chaque article
                    for i, stock_item_id_str in enumerate(stock_item_ids):
                        if i >= len(quantities):
                            continue
                        
                        try:
                            stock_item_id = int(stock_item_id_str)
                            quantity = Decimal(quantities[i])
                            
                            if quantity <= 0:
                                errors.append(f"Quantité invalide pour l'article {i+1}")
                                continue
                            
                            # Vérifier le stock source et créer s'il n'existe pas
                            source_stock = None
                            
                            if from_depot_id:
                                # Récupérer le stock du dépôt (source principale)
                                source_stock = DepotStock.query.filter_by(
                                    depot_id=int(from_depot_id), 
                                    stock_item_id=stock_item_id
                                ).first()
                                
                                # Si le stock n'existe pas, le créer avec quantité 0
                                if not source_stock:
                                    source_stock = DepotStock(
                                        depot_id=int(from_depot_id),
                                        stock_item_id=stock_item_id,
                                        quantity=Decimal('0')
                                    )
                                    db.session.add(source_stock)
                                    # Flush pour s'assurer que l'objet est dans la session
                                    db.session.flush()
                                
                                # Rafraîchir l'objet depuis la base de données pour avoir la valeur la plus récente
                                db.session.refresh(source_stock)
                                
                                # Utiliser directement la quantité de DepotStock
                                available_quantity = source_stock.quantity or Decimal('0')
                                
                                # Debug: afficher les valeurs pour diagnostic
                                print(f"🔍 DEBUG Stock - Dépôt: {from_depot_id}, Article: {stock_item_id}, Disponible: {available_quantity}, Requis: {quantity}")
                                
                                # Vérifier le stock disponible avec arrondi pour éviter les problèmes de précision
                                quantity_decimal = Decimal(str(quantity)).quantize(Decimal('0.0001'))
                                available_decimal = available_quantity.quantize(Decimal('0.0001'))
                                
                                if available_decimal < quantity_decimal:
                                    item = StockItem.query.get(stock_item_id)
                                    item_name = item.name if item else f"ID {stock_item_id}"
                                    # Formater les quantités pour l'affichage (éviter les décimales inutiles)
                                    available_display = f"{available_quantity:.4f}".rstrip('0').rstrip('.')
                                    quantity_display = f"{quantity:.4f}".rstrip('0').rstrip('.')
                                    errors.append(f"Stock insuffisant à la source pour {item_name} (disponible: {available_display}, requis: {quantity_display})")
                                    continue
                                
                                # Déduire la quantité du stock source
                                source_stock.quantity -= quantity_decimal
                            
                            elif from_vehicle_id:
                                source_stock = VehicleStock.query.filter_by(
                                    vehicle_id=int(from_vehicle_id), 
                                    stock_item_id=stock_item_id
                                ).first()
                                if not source_stock:
                                    # Créer le stock avec quantité 0
                                    source_stock = VehicleStock(
                                        vehicle_id=int(from_vehicle_id),
                                        stock_item_id=stock_item_id,
                                        quantity=Decimal('0')
                                    )
                                    db.session.add(source_stock)
                                # Vérifier le stock disponible
                                if source_stock.quantity < quantity:
                                    item = StockItem.query.get(stock_item_id)
                                    item_name = item.name if item else f"ID {stock_item_id}"
                                    errors.append(f"Stock insuffisant à la source pour {item_name} (disponible: {source_stock.quantity}, requis: {quantity})")
                                    continue
                                # Déduire la quantité du stock source
                                source_stock.quantity -= quantity
                            
                            else:
                                # Aucune source définie (ne devrait pas arriver pour un transfert)
                                errors.append(f"Aucune source définie pour le transfert de l'article {stock_item_id}")
                                continue
                            
                            # Mettre à jour le stock destination
                            if to_depot_id:
                                dest_stock = DepotStock.query.filter_by(
                                    depot_id=int(to_depot_id), 
                                    stock_item_id=stock_item_id
                                ).first()
                                if not dest_stock:
                                    dest_stock = DepotStock(
                                        depot_id=int(to_depot_id),
                                        stock_item_id=stock_item_id,
                                        quantity=Decimal('0')
                                    )
                                    db.session.add(dest_stock)
                                dest_stock.quantity += quantity
                            
                            elif to_vehicle_id:
                                dest_stock = VehicleStock.query.filter_by(
                                    vehicle_id=int(to_vehicle_id), 
                                    stock_item_id=stock_item_id
                                ).first()
                                if not dest_stock:
                                    dest_stock = VehicleStock(
                                        vehicle_id=int(to_vehicle_id),
                                        stock_item_id=stock_item_id,
                                        quantity=Decimal('0')
                                    )
                                    db.session.add(dest_stock)
                                dest_stock.quantity += quantity
                            
                            # Générer une référence de base pour ce transfert
                            base_reference = generate_movement_reference(movement_type, generated_references)
                            generated_references.append(base_reference)
                            
                            # LOGIQUE MÉTIER : TRANSFERT = Déplacement entre dépôts/véhicules
                            # Créer les mouvements avec signe :
                            # - SORTIE (source) : quantité NÉGATIVE (diminue le stock source)
                            # - ENTRÉE (destination) : quantité POSITIVE (augmente le stock destination)
                            
                            # Récupérer la date du mouvement depuis le formulaire
                            movement_date_str = request.form.get('movement_date')
                            if movement_date_str:
                                try:
                                    # Format datetime-local: YYYY-MM-DDTHH:MM
                                    if 'T' in movement_date_str:
                                        movement_date = datetime.strptime(movement_date_str, '%Y-%m-%dT%H:%M')
                                    else:
                                        # Format date seulement: YYYY-MM-DD
                                        movement_date = datetime.strptime(movement_date_str, '%Y-%m-%d')
                                except:
                                    movement_date = datetime.now()
                            else:
                                movement_date = datetime.now()
                            
                            # Générer des références uniques pour chaque mouvement
                            # Pour les transferts, nous créons deux mouvements (sortie et entrée)
                            # avec des références différentes pour éviter la contrainte unique
                            reference_out = f"{base_reference}-OUT"
                            reference_in = f"{base_reference}-IN"
                            
                            # Vérifier et ajuster si nécessaire pour éviter les doublons
                            counter = 1
                            while StockMovement.query.filter_by(reference=reference_out).first():
                                reference_out = f"{base_reference}-OUT-{counter}"
                                counter += 1
                            
                            counter = 1
                            while StockMovement.query.filter_by(reference=reference_in).first():
                                reference_in = f"{base_reference}-IN-{counter}"
                                counter += 1
                            
                            # Mouvement SORTIE (si source existe)
                            if from_depot_id or from_vehicle_id:
                                movement_out = StockMovement(
                                    reference=reference_out,
                                    movement_type=movement_type,
                                    movement_date=movement_date,
                                    stock_item_id=stock_item_id,
                                    quantity=-quantity,  # NÉGATIF pour sortie
                                    user_id=current_user.id,
                                    from_depot_id=int(from_depot_id) if from_depot_id else None,
                                    from_vehicle_id=int(from_vehicle_id) if from_vehicle_id else None,
                                    to_depot_id=None,
                                    to_vehicle_id=None,
                                    reason=reason
                                )
                                db.session.add(movement_out)
                                movements_created += 1
                                print(f"✅ Mouvement SORTIE créé: {reference_out} - Article {stock_item_id} - Quantité: -{quantity} (Dépôt/Véhicule source: {from_depot_id or from_vehicle_id})")
                            
                            # Mouvement ENTRÉE (si destination existe)
                            if to_depot_id or to_vehicle_id:
                                movement_in = StockMovement(
                                    reference=reference_in,
                                    movement_type=movement_type,
                                    movement_date=movement_date,
                                    stock_item_id=stock_item_id,
                                    quantity=quantity,  # POSITIF pour entrée
                                    user_id=current_user.id,
                                    from_depot_id=None,
                                    from_vehicle_id=None,
                                    to_depot_id=int(to_depot_id) if to_depot_id else None,
                                    to_vehicle_id=int(to_vehicle_id) if to_vehicle_id else None,
                                    reason=reason
                                )
                                db.session.add(movement_in)
                                movements_created += 1
                            print(f"✅ Mouvement ENTRÉE créé: {reference_in} - Article {stock_item_id} - Quantité: +{quantity} (Dépôt/Véhicule destination: {to_depot_id or to_vehicle_id})")
                            
                        except (ValueError, IndexError) as e:
                            errors.append(f"Erreur lors du traitement de l'article {i+1}: {str(e)}")
                            continue
                
                    if errors:
                        db.session.rollback()
                        flash(f'Erreurs: {"; ".join(errors)}', 'error')
                        form_data = get_movement_form_data()
                        return render_template('stocks/movement_form.html', movement_type=movement_type, **form_data)
                    
                    if movements_created == 0:
                        db.session.rollback()
                        flash('Aucun mouvement créé', 'error')
                        form_data = get_movement_form_data()
                        return render_template('stocks/movement_form.html', movement_type=movement_type, **form_data)
                    
                    db.session.commit()
                    flash(f'{movements_created} mouvement(s) de transfert créé(s) avec succès', 'success')
                    return redirect(url_for('stocks.movements_list'))
                except Exception as e:
                    db.session.rollback()
                    flash(f'Erreur lors de la création du transfert: {str(e)}', 'error')
                    form_data = get_movement_form_data()
                    return render_template('stocks/movement_form.html', movement_type=movement_type, **form_data)
            
            else:
                # Pour réception et ajustement, traitement simple (un seul article)
                stock_item_id_str = request.form.get('stock_item_id')
                quantity_str = request.form.get('quantity')
                
                # Validation
                if not stock_item_id_str or not quantity_str:
                    flash('Veuillez sélectionner un article et une quantité valide', 'error')
                    form_data = get_movement_form_data()
                    return render_template('stocks/movement_form.html', movement_type=movement_type, **form_data)
                
                try:
                    stock_item_id = int(stock_item_id_str)
                    quantity = Decimal(quantity_str)
                except (ValueError, TypeError):
                    flash('Veuillez sélectionner un article et une quantité valide', 'error')
                    form_data = get_movement_form_data()
                    return render_template('stocks/movement_form.html', movement_type=movement_type, **form_data)
                
                if quantity <= 0:
                    flash('La quantité doit être supérieure à 0', 'error')
                    form_data = get_movement_form_data()
                    return render_template('stocks/movement_form.html', movement_type=movement_type, **form_data)
                
                if movement_type == 'reception':
                    # Réception : incrémenter dépôt
                    if not to_depot_id:
                        flash('Veuillez sélectionner un dépôt de destination', 'error')
                        form_data = get_movement_form_data()
                        return render_template('stocks/movement_form.html', movement_type=movement_type, **form_data)
                    
                    dest_stock = DepotStock.query.filter_by(
                        depot_id=int(to_depot_id), 
                        stock_item_id=stock_item_id
                    ).first()
                    if not dest_stock:
                        dest_stock = DepotStock(
                            depot_id=int(to_depot_id),
                            stock_item_id=stock_item_id,
                            quantity=Decimal('0')
                        )
                        db.session.add(dest_stock)
                    dest_stock.quantity += quantity
                
                elif movement_type == 'adjustment':
                    # Ajustement : calculer la différence AVANT de mettre à jour le stock
                    depot_id = to_depot_id or from_depot_id
                    vehicle_id = to_vehicle_id or from_vehicle_id
                    
                    old_quantity = Decimal('0')
                    if depot_id:
                        stock = DepotStock.query.filter_by(
                            depot_id=int(depot_id), 
                            stock_item_id=stock_item_id
                        ).first()
                        if stock:
                            old_quantity = stock.quantity
                        else:
                            stock = DepotStock(
                                depot_id=int(depot_id),
                                stock_item_id=stock_item_id,
                                quantity=Decimal('0')
                            )
                            db.session.add(stock)
                    elif vehicle_id:
                        stock = VehicleStock.query.filter_by(
                            vehicle_id=int(vehicle_id), 
                            stock_item_id=stock_item_id
                        ).first()
                        if stock:
                            old_quantity = stock.quantity
                        else:
                            stock = VehicleStock(
                                vehicle_id=int(vehicle_id),
                                stock_item_id=stock_item_id,
                                quantity=Decimal('0')
                            )
                            db.session.add(stock)
                    
                    # Calculer la différence
                    adjustment_diff = quantity - old_quantity
                    # Mettre à jour le stock (cache)
                    stock.quantity = quantity
                
                # Générer une référence unique pour ce mouvement
                reference = generate_movement_reference(movement_type)
                
                # Récupérer la date du mouvement depuis le formulaire
                movement_date_str = request.form.get('movement_date')
                if movement_date_str:
                    try:
                        # Format datetime-local: YYYY-MM-DDTHH:MM
                        if 'T' in movement_date_str:
                            movement_date = datetime.strptime(movement_date_str, '%Y-%m-%dT%H:%M')
                        else:
                            # Format date seulement: YYYY-MM-DD
                            movement_date = datetime.strptime(movement_date_str, '%Y-%m-%d')
                    except:
                        movement_date = datetime.now()
                else:
                    movement_date = datetime.now()
                
                # Déterminer le signe de la quantité selon le type de mouvement
                if movement_type == 'reception':
                    # LOGIQUE MÉTIER : RÉCEPTION = Augmentation du stock
                    # Réception = ENTRÉE = quantité POSITIVE (augmente le stock)
                    signed_quantity = quantity
                    # Créer le mouvement ENTRÉE
                    movement = StockMovement(
                        reference=reference,
                        movement_type=movement_type,
                        movement_date=movement_date,
                        stock_item_id=stock_item_id,
                        quantity=signed_quantity,  # POSITIF
                        user_id=current_user.id,
                        from_depot_id=None,
                        from_vehicle_id=None,
                        to_depot_id=int(to_depot_id) if to_depot_id else None,
                        to_vehicle_id=int(to_vehicle_id) if to_vehicle_id else None,
                        supplier_name=supplier_name,
                        bl_number=bl_number,
                        reason=reason
                    )
                elif movement_type == 'adjustment':
                    # Ajustement : utiliser la différence calculée précédemment
                    depot_id = to_depot_id or from_depot_id
                    vehicle_id = to_vehicle_id or from_vehicle_id
                    
                    # Utiliser la différence calculée (positif si augmentation, négatif si diminution)
                    signed_quantity = adjustment_diff if 'adjustment_diff' in locals() else quantity
                    
                    if signed_quantity > 0:
                        # Ajustement positif (ajout)
                        movement = StockMovement(
                            reference=reference,
                            movement_type=movement_type,
                            movement_date=movement_date,
                            stock_item_id=stock_item_id,
                            quantity=signed_quantity,  # POSITIF
                            user_id=current_user.id,
                            from_depot_id=None,
                            from_vehicle_id=None,
                            to_depot_id=int(to_depot_id) if to_depot_id else None,
                            to_vehicle_id=int(to_vehicle_id) if to_vehicle_id else None,
                            supplier_name=supplier_name,
                            bl_number=bl_number,
                            reason=reason
                        )
                    elif signed_quantity < 0:
                        # Ajustement négatif (retrait)
                        movement = StockMovement(
                            reference=reference,
                            movement_type=movement_type,
                            movement_date=movement_date,
                            stock_item_id=stock_item_id,
                            quantity=signed_quantity,  # NÉGATIF
                            user_id=current_user.id,
                            from_depot_id=int(from_depot_id) if from_depot_id else None,
                            from_vehicle_id=int(from_vehicle_id) if from_vehicle_id else None,
                            to_depot_id=None,
                            to_vehicle_id=None,
                            supplier_name=supplier_name,
                            bl_number=bl_number,
                            reason=reason
                        )
                    else:
                        # Aucun ajustement nécessaire (quantité identique)
                        flash('Aucun ajustement nécessaire (quantité identique)', 'info')
                        form_data = get_movement_form_data()
                        return render_template('stocks/movement_form.html', movement_type=movement_type, **form_data)
                else:
                    # Par défaut, positif (ne devrait pas arriver ici normalement)
                    movement = StockMovement(
                        reference=reference,
                        movement_type=movement_type,
                        movement_date=movement_date,
                        stock_item_id=stock_item_id,
                        quantity=quantity,
                        user_id=current_user.id,
                        from_depot_id=int(from_depot_id) if from_depot_id else None,
                        from_vehicle_id=int(from_vehicle_id) if from_vehicle_id else None,
                        to_depot_id=int(to_depot_id) if to_depot_id else None,
                        to_vehicle_id=int(to_vehicle_id) if to_vehicle_id else None,
                        supplier_name=supplier_name,
                        bl_number=bl_number,
                        reason=reason
                    )
                
                db.session.add(movement)
                db.session.commit()
                
                flash(f'Mouvement de type "{movement_type}" créé avec succès', 'success')
                return redirect(url_for('stocks.movements_list'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur lors de la création du mouvement: {str(e)}', 'error')
            form_data = get_movement_form_data()
            return render_template('stocks/movement_form.html', movement_type=movement_type, **form_data)
    
    form_data = get_movement_form_data()
    # Générer une référence prévisualisée
    preview_reference = generate_movement_reference(movement_type)
    return render_template('stocks/movement_form.html', 
                         movement_type=movement_type,
                         current_user=current_user,
                         preview_reference=preview_reference,
                         **form_data)

# =========================================================
# RÉCEPTIONS
# =========================================================

@stocks_bp.route('/receptions')
@login_required
def receptions_list():
    """Liste des réceptions avec pagination et filtres"""
    if not has_permission(current_user, 'receptions.read'):
        flash('Vous n\'avez pas la permission d\'accéder à cette page', 'error')
        return redirect(url_for('index'))
    
    from sqlalchemy import or_
    from datetime import datetime, timedelta
    from utils_region_filter import filter_depots_by_region
    
    # Paramètres de pagination
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    
    # Filtres
    search = request.args.get('search', '').strip()
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    depot_id = request.args.get('depot_id', type=int)
    supplier_name = request.args.get('supplier_name', '').strip()
    
    # Construire la requête avec optimisation N+1
    query = Reception.query.options(
        joinedload(Reception.depot),
        joinedload(Reception.user),
        joinedload(Reception.details).joinedload(ReceptionDetail.stock_item)
    )
    
    # Filtrer par région : seules les réceptions des dépôts accessibles
    accessible_depot_ids = [d.id for d in filter_depots_by_region(Depot.query).all()]
    if accessible_depot_ids:
        query = query.filter(Reception.depot_id.in_(accessible_depot_ids))
    else:
        # Aucun dépôt accessible, retourner une requête vide
        query = query.filter(False)
    
    # Appliquer les filtres
    if search:
        query = query.filter(
            or_(
                Reception.reference.like(f'%{search}%'),
                Reception.bl_number.like(f'%{search}%'),
                Reception.supplier_name.like(f'%{search}%')
            )
        )
    
    if date_from:
        try:
            date_from_obj = datetime.strptime(date_from, '%Y-%m-%d')
            query = query.filter(Reception.reception_date >= date_from_obj)
        except ValueError:
            pass
    
    if date_to:
        try:
            date_to_obj = datetime.strptime(date_to, '%Y-%m-%d') + timedelta(days=1)
            query = query.filter(Reception.reception_date < date_to_obj)
        except ValueError:
            pass
    
    if depot_id:
        query = query.filter(Reception.depot_id == depot_id)
    
    if supplier_name:
        query = query.filter(Reception.supplier_name.like(f'%{supplier_name}%'))
    
    # Pagination
    pagination = query.order_by(Reception.reception_date.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    receptions = pagination.items
    
    # Statistiques
    total_receptions = Reception.query.count()
    
    # Données pour filtres (filtrées par région)
    depots_query = Depot.query.filter_by(is_active=True)
    depots_query = filter_depots_by_region(depots_query)
    depots = depots_query.order_by(Depot.name).all()
    
    return render_template('stocks/receptions_list.html', 
                         receptions=receptions,
                         pagination=pagination,
                         search=search,
                         date_from=date_from,
                         date_to=date_to,
                         depot_id=depot_id,
                         supplier_name=supplier_name,
                         per_page=per_page,
                         total_receptions=total_receptions,
                         depots=depots)

@stocks_bp.route('/receptions/export/excel')
@login_required
def receptions_export_excel():
    """Export Excel des réceptions avec filtres appliqués"""
    if not has_permission(current_user, 'receptions.read'):
        flash("Vous n'avez pas la permission d'exporter les données.", "error")
        return redirect(url_for('stocks.receptions_list'))
    
    import pandas as pd
    from sqlalchemy import or_
    
    # Récupérer les mêmes filtres que receptions_list
    search = request.args.get('search', '').strip()
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    depot_id = request.args.get('depot_id', type=int)
    supplier_name = request.args.get('supplier_name', '').strip()
    
    try:
        # Construire la requête (même logique que receptions_list)
        query = Reception.query.options(
            joinedload(Reception.depot),
            joinedload(Reception.user),
            joinedload(Reception.details).joinedload(ReceptionDetail.stock_item)
        )
        
        # Appliquer les filtres
        if search:
            query = query.filter(
                or_(
                    Reception.reference.like(f'%{search}%'),
                    Reception.bl_number.like(f'%{search}%'),
                    Reception.supplier_name.like(f'%{search}%')
                )
            )
        
        if date_from:
            try:
                date_from_obj = datetime.strptime(date_from, '%Y-%m-%d')
                query = query.filter(Reception.reception_date >= date_from_obj)
            except ValueError:
                pass
        
        if date_to:
            try:
                date_to_obj = datetime.strptime(date_to, '%Y-%m-%d') + timedelta(days=1)
                query = query.filter(Reception.reception_date < date_to_obj)
            except ValueError:
                pass
        
        if depot_id:
            query = query.filter(Reception.depot_id == depot_id)
        
        if supplier_name:
            query = query.filter(Reception.supplier_name.like(f'%{supplier_name}%'))
        
        # Récupérer toutes les réceptions (sans pagination pour l'export)
        receptions = query.order_by(Reception.reception_date.desc()).all()
        
        # Préparer les données pour Excel
        data = []
        for reception in receptions:
            # Une ligne par détail de réception
            if reception.details:
                for detail in reception.details:
                    data.append({
                        'Date': reception.reception_date.strftime('%d/%m/%Y') if reception.reception_date else '',
                        'Référence': reception.reference or '',
                        'Dépôt': reception.depot.name if reception.depot else '',
                        'Fournisseur': reception.supplier_name or '',
                        'BL': reception.bl_number or '',
                        'Article (SKU)': detail.stock_item.sku if detail.stock_item else '',
                        'Article': detail.stock_item.name if detail.stock_item else '',
                        'Quantité': float(detail.quantity),
                        'Prix Unitaire (GNF)': float(detail.unit_price_gnf) if detail.unit_price_gnf else 0,
                        'Montant Total (GNF)': float(detail.quantity * detail.unit_price_gnf) if detail.unit_price_gnf else 0,
                        'Utilisateur': reception.user.username if reception.user else '',
                        'Statut': reception.status or 'draft',
                        'Notes': reception.notes or ''
                    })
            else:
                # Réception sans détails
                data.append({
                    'Date': reception.reception_date.strftime('%d/%m/%Y') if reception.reception_date else '',
                    'Référence': reception.reference or '',
                    'Dépôt': reception.depot.name if reception.depot else '',
                    'Fournisseur': reception.supplier_name or '',
                    'BL': reception.bl_number or '',
                    'Article (SKU)': '',
                    'Article': '',
                    'Quantité': 0,
                    'Prix Unitaire (GNF)': 0,
                    'Montant Total (GNF)': 0,
                    'Utilisateur': reception.user.username if reception.user else '',
                    'Statut': reception.status or 'draft',
                    'Notes': reception.notes or ''
                })
        
        # Créer le DataFrame
        df = pd.DataFrame(data)
        
        # Ajouter une ligne de totaux
        if len(df) > 0:
            total_row = pd.DataFrame([{
                'Date': 'TOTAL',
                'Référence': '',
                'Dépôt': '',
                'Fournisseur': '',
                'BL': '',
                'Article (SKU)': '',
                'Article': '',
                'Quantité': df['Quantité'].sum(),
                'Prix Unitaire (GNF)': '',
                'Montant Total (GNF)': df['Montant Total (GNF)'].sum(),
                'Utilisateur': '',
                'Statut': '',
                'Notes': ''
            }])
            df = pd.concat([df, total_row], ignore_index=True)
        
        # Créer le fichier Excel
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Réceptions', index=False)
            
            # Formater les colonnes
            worksheet = writer.sheets['Réceptions']
            for idx, col in enumerate(df.columns, 1):
                max_length = max(
                    df[col].astype(str).map(len).max(),
                    len(str(col))
                )
                worksheet.column_dimensions[chr(64 + idx)].width = min(max_length + 2, 40)
        
        output.seek(0)
        filename = f'receptions_stock_{datetime.now(UTC).strftime("%Y%m%d_%H%M%S")}.xlsx'
        
        response = make_response(output.getvalue())
        response.headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"❌ Erreur lors de l'export Excel: {e}")
        flash(f'Erreur lors de l\'export Excel: {str(e)}', 'error')
        return redirect(url_for('stocks.receptions_list'))

@stocks_bp.route('/receptions/new', methods=['GET', 'POST'])
@login_required
def reception_new():
    """Créer une nouvelle réception avec plusieurs articles"""
    if not has_permission(current_user, 'receptions.create'):
        flash('Vous n\'avez pas la permission de créer une réception', 'error')
        return redirect(url_for('stocks.receptions_list'))
    
    if request.method == 'POST':
        depot_id = int(request.form.get('depot_id'))
        supplier_name = request.form.get('supplier_name')
        bl_number = request.form.get('bl_number')
        reception_date = request.form.get('reception_date') or datetime.now(UTC)
        notes = request.form.get('notes')
        
        if not depot_id or not supplier_name or not bl_number:
            flash('Veuillez remplir tous les champs obligatoires', 'error')
            depots = Depot.query.filter_by(is_active=True).all()
            stock_items = StockItem.query.filter_by(is_active=True).order_by(StockItem.name).all()
            return render_template('stocks/reception_form.html', depots=depots, stock_items=stock_items)
        
        # Générer une référence unique avec UUID pour éviter les collisions
        import uuid
        date_str = datetime.now().strftime('%Y%m%d')
        reference = f"REC-{date_str}-{uuid.uuid4().hex[:8].upper()}"
        # Vérifier l'unicité (très peu probable avec UUID mais sécurité)
        counter = 0
        while Reception.query.filter_by(reference=reference).first() and counter < 10:
            reference = f"REC-{date_str}-{uuid.uuid4().hex[:8].upper()}"
            counter += 1
        if counter >= 10:
            flash('Erreur lors de la génération de la référence. Veuillez réessayer.', 'error')
            depots = Depot.query.filter_by(is_active=True).all()
            stock_items = StockItem.query.filter_by(is_active=True).order_by(StockItem.name).all()
            return render_template('stocks/reception_form.html', depots=depots, stock_items=stock_items)
        
        # Créer la réception
        reception = Reception(
            reference=reference,
            depot_id=depot_id,
            supplier_name=supplier_name,
            bl_number=bl_number,
            reception_date=datetime.strptime(reception_date, '%Y-%m-%d') if isinstance(reception_date, str) else reception_date,
            user_id=current_user.id,
            notes=notes,
            status='draft'
        )
        db.session.add(reception)
        db.session.flush()  # Pour obtenir l'ID
        
        # Traiter les articles (format: item_id,quantity,unit_price)
        items_data = request.form.getlist('items[]')
        if not items_data:
            flash('Veuillez ajouter au moins un article', 'error')
            db.session.rollback()
            depots = Depot.query.filter_by(is_active=True).all()
            stock_items = StockItem.query.filter_by(is_active=True).order_by(StockItem.name).all()
            return render_template('stocks/reception_form.html', depots=depots, stock_items=stock_items)
        
        # Créer les détails
        for item_data in items_data:
            if item_data:
                parts = item_data.split(',')
                if len(parts) >= 2:
                    item_id = int(parts[0])
                    qty = Decimal(parts[1])
                    # Récupérer le prix unitaire depuis le formulaire ou utiliser le prix d'achat du StockItem
                    unit_price = None
                    if len(parts) > 2 and parts[2] and parts[2].strip():
                        try:
                            unit_price = Decimal(parts[2])
                        except (ValueError, InvalidOperation):
                            unit_price = None
                    
                    # Si le prix n'est pas fourni, utiliser le prix d'achat du StockItem
                    if unit_price is None or unit_price == 0:
                        stock_item = StockItem.query.get(item_id)
                        if stock_item and stock_item.purchase_price_gnf:
                            unit_price = stock_item.purchase_price_gnf
                        else:
                            # Si aucun prix n'est disponible, utiliser 0 comme valeur par défaut
                            unit_price = Decimal('0')
                    
                    detail = ReceptionDetail(
                        reception_id=reception.id,
                        stock_item_id=item_id,
                        quantity=qty,
                        unit_price_gnf=unit_price
                    )
                    db.session.add(detail)
                    
                    # Mettre à jour le stock du dépôt (cache)
                    depot_stock = DepotStock.query.filter_by(
                        depot_id=depot_id,
                        stock_item_id=item_id
                    ).first()
                    if not depot_stock:
                        depot_stock = DepotStock(
                            depot_id=depot_id,
                            stock_item_id=item_id,
                            quantity=Decimal('0')
                        )
                        db.session.add(depot_stock)
                    depot_stock.quantity += qty
                    
                    # LOGIQUE MÉTIER : RÉCEPTION = Augmentation du stock (entrée externe)
                    # Créer le mouvement de stock (ENTRÉE = quantité POSITIVE)
                    movement_ref = generate_movement_reference('reception')
                    # Convertir reception_date si c'est une string
                    reception_date = reception.reception_date
                    if isinstance(reception_date, str):
                        try:
                            reception_date = datetime.strptime(reception_date, '%Y-%m-%d')
                        except:
                            reception_date = datetime.now()
                    
                    movement = StockMovement(
                        reference=movement_ref,
                        movement_type='reception',
                        movement_date=reception_date,
                        stock_item_id=item_id,
                        quantity=qty,  # POSITIF pour entrée
                        user_id=current_user.id,
                        from_depot_id=None,
                        from_vehicle_id=None,
                        to_depot_id=depot_id,
                        to_vehicle_id=None,
                        supplier_name=supplier_name,
                        bl_number=bl_number
                    )
                    db.session.add(movement)
        
        reception.status = 'completed'
        db.session.commit()
        
        flash(f'Réception "{reference}" créée avec succès', 'success')
        return redirect(url_for('stocks.reception_detail', id=reception.id))
    
    depots = Depot.query.filter_by(is_active=True).all()
    stock_items = StockItem.query.filter_by(is_active=True).order_by(StockItem.name).all()
    return render_template('stocks/reception_form.html', depots=depots, stock_items=stock_items)

@stocks_bp.route('/receptions/<int:id>')
@login_required
def reception_detail(id):
    """Détails d'une réception"""
    if not has_permission(current_user, 'receptions.read'):
        flash('Vous n\'avez pas la permission d\'accéder à cette page', 'error')
        return redirect(url_for('stocks.receptions_list'))
    
    reception = Reception.query.get_or_404(id)
    return render_template('stocks/reception_detail.html', reception=reception)

@stocks_bp.route('/receptions/<int:id>/preview')
@login_required
def reception_preview(id):
    """Prévisualisation d'une réception avant export PDF"""
    if not has_permission(current_user, 'receptions.read'):
        flash('Vous n\'avez pas la permission d\'accéder à cette page', 'error')
        return redirect(url_for('stocks.receptions_list'))
    
    reception = Reception.query.get_or_404(id)
    return render_template('stocks/reception_preview.html', reception=reception)

@stocks_bp.route('/receptions/<int:id>/pdf')
@login_required
def reception_pdf(id):
    """Générer un PDF pour une réception"""
    if not has_permission(current_user, 'receptions.read'):
        flash('Vous n\'avez pas la permission d\'accéder à cette page', 'error')
        return redirect(url_for('stocks.receptions_list'))
    
    from pdf_generator import PDFGenerator
    from flask import make_response
    
    try:
        reception = Reception.query.get_or_404(id)
        pdf_gen = PDFGenerator()
        pdf_buffer = pdf_gen.generate_reception_pdf(reception)
        
        filename = f'reception_{reception.reference}_{datetime.now(UTC).strftime("%Y%m%d_%H%M%S")}.pdf'
        response = make_response(pdf_buffer.getvalue())
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"❌ Erreur lors de la génération du PDF: {e}")
        flash(f'Erreur lors de la génération du PDF: {str(e)}', 'error')
        return redirect(url_for('stocks.reception_detail', id=id))

# =========================================================
# SORTIES DE STOCK (VENTES)
# =========================================================

@stocks_bp.route('/outgoings')
@login_required
def outgoings_list():
    """Liste des sorties avec pagination et filtres"""
    if not has_permission(current_user, 'outgoings.read'):
        flash('Vous n\'avez pas la permission d\'accéder à cette page', 'error')
        return redirect(url_for('index'))
    
    from sqlalchemy import or_
    from datetime import datetime, timedelta
    from utils_region_filter import filter_depots_by_region, filter_vehicles_by_region
    
    # Paramètres de pagination
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    
    # Filtres
    search = request.args.get('search', '').strip()
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    depot_id = request.args.get('depot_id', type=int)
    vehicle_id = request.args.get('vehicle_id', type=int)
    client_name = request.args.get('client_name', '').strip()
    
    # Construire la requête avec optimisation N+1
    query = StockOutgoing.query.options(
        joinedload(StockOutgoing.depot),
        joinedload(StockOutgoing.vehicle),
        joinedload(StockOutgoing.commercial),
        joinedload(StockOutgoing.user),
        joinedload(StockOutgoing.details).joinedload(StockOutgoingDetail.stock_item)
    )
    
    # IMPORTANT: Filtrer selon le rôle de l'utilisateur
    # - Commercial : voit uniquement SES sorties (commercial_id == current_user.id)
    # - Admin : voit toutes les sorties
    # - Autres rôles : filtrer par région
    if current_user.role and current_user.role.code == 'commercial':
        query = query.filter(StockOutgoing.commercial_id == current_user.id)
    elif current_user.role and current_user.role.code in ['admin', 'superadmin']:
        # Admin voit toutes les sorties sans filtre supplémentaire
        pass
    else:
        # Filtrer par région : seules les sorties des dépôts/véhicules accessibles
        accessible_depot_ids = [d.id for d in filter_depots_by_region(Depot.query).all()]
        accessible_vehicle_ids = [v.id for v in filter_vehicles_by_region(Vehicle.query).all()]
        
        if accessible_depot_ids or accessible_vehicle_ids:
            query = query.filter(
                or_(
                    StockOutgoing.depot_id.in_(accessible_depot_ids) if accessible_depot_ids else False,
                    StockOutgoing.vehicle_id.in_(accessible_vehicle_ids) if accessible_vehicle_ids else False
                )
            )
        else:
            # Aucun dépôt/véhicule accessible, retourner une requête vide
            query = query.filter(False)
    
    # Appliquer les filtres
    if search:
        query = query.filter(
            or_(
                StockOutgoing.reference.like(f'%{search}%'),
                StockOutgoing.client_name.like(f'%{search}%'),
                StockOutgoing.client_phone.like(f'%{search}%')
            )
        )
    
    if date_from:
        try:
            date_from_obj = datetime.strptime(date_from, '%Y-%m-%d')
            query = query.filter(StockOutgoing.outgoing_date >= date_from_obj)
        except ValueError:
            pass
    
    if date_to:
        try:
            date_to_obj = datetime.strptime(date_to, '%Y-%m-%d') + timedelta(days=1)
            query = query.filter(StockOutgoing.outgoing_date < date_to_obj)
        except ValueError:
            pass
    
    if depot_id:
        query = query.filter(StockOutgoing.depot_id == depot_id)
    
    if vehicle_id:
        query = query.filter(StockOutgoing.vehicle_id == vehicle_id)
    
    if client_name:
        query = query.filter(StockOutgoing.client_name.like(f'%{client_name}%'))
    
    # Pagination
    pagination = query.order_by(StockOutgoing.outgoing_date.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    outgoings = pagination.items
    
    # Statistiques
    total_outgoings = StockOutgoing.query.count()
    
    # Données pour filtres (filtrées par région)
    depots_query = Depot.query.filter_by(is_active=True)
    depots_query = filter_depots_by_region(depots_query)
    depots = depots_query.order_by(Depot.name).all()
    vehicles_query = Vehicle.query.filter_by(status='active')
    vehicles_query = filter_vehicles_by_region(vehicles_query)
    vehicles = vehicles_query.order_by(Vehicle.plate_number).all()
    
    return render_template('stocks/outgoings_list.html', 
                         outgoings=outgoings,
                         pagination=pagination,
                         search=search,
                         date_from=date_from,
                         date_to=date_to,
                         depot_id=depot_id,
                         vehicle_id=vehicle_id,
                         client_name=client_name,
                         per_page=per_page,
                         total_outgoings=total_outgoings,
                         depots=depots,
                         vehicles=vehicles)

@stocks_bp.route('/outgoings/export/excel')
@login_required
def outgoings_export_excel():
    """Export Excel des sorties avec filtres appliqués"""
    if not has_permission(current_user, 'outgoings.read'):
        flash("Vous n'avez pas la permission d'exporter les données.", "error")
        return redirect(url_for('stocks.outgoings_list'))
    
    import pandas as pd
    from sqlalchemy import or_
    
    # Récupérer les mêmes filtres que outgoings_list
    search = request.args.get('search', '').strip()
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    depot_id = request.args.get('depot_id', type=int)
    vehicle_id = request.args.get('vehicle_id', type=int)
    client_name = request.args.get('client_name', '').strip()
    
    try:
        # Construire la requête (même logique que outgoings_list)
        query = StockOutgoing.query.options(
            joinedload(StockOutgoing.depot),
            joinedload(StockOutgoing.vehicle),
            joinedload(StockOutgoing.commercial),
            joinedload(StockOutgoing.user),
            joinedload(StockOutgoing.details).joinedload(StockOutgoingDetail.stock_item)
        )
        
        # IMPORTANT: Filtrer selon le rôle de l'utilisateur (même logique que outgoings_list)
        from utils_region_filter import filter_depots_by_region, filter_vehicles_by_region
        if current_user.role and current_user.role.code == 'commercial':
            query = query.filter(StockOutgoing.commercial_id == current_user.id)
        elif current_user.role and current_user.role.code not in ['admin', 'superadmin']:
            # Filtrer par région pour les autres rôles
            accessible_depot_ids = [d.id for d in filter_depots_by_region(Depot.query).all()]
            accessible_vehicle_ids = [v.id for v in filter_vehicles_by_region(Vehicle.query).all()]
            if accessible_depot_ids or accessible_vehicle_ids:
                query = query.filter(
                    or_(
                        StockOutgoing.depot_id.in_(accessible_depot_ids) if accessible_depot_ids else False,
                        StockOutgoing.vehicle_id.in_(accessible_vehicle_ids) if accessible_vehicle_ids else False
                    )
                )
            else:
                query = query.filter(False)
        
        # Appliquer les filtres
        if search:
            query = query.filter(
                or_(
                    StockOutgoing.reference.like(f'%{search}%'),
                    StockOutgoing.client_name.like(f'%{search}%'),
                    StockOutgoing.client_phone.like(f'%{search}%')
                )
            )
        
        if date_from:
            try:
                date_from_obj = datetime.strptime(date_from, '%Y-%m-%d')
                query = query.filter(StockOutgoing.outgoing_date >= date_from_obj)
            except ValueError:
                pass
        
        if date_to:
            try:
                date_to_obj = datetime.strptime(date_to, '%Y-%m-%d') + timedelta(days=1)
                query = query.filter(StockOutgoing.outgoing_date < date_to_obj)
            except ValueError:
                pass
        
        if depot_id:
            query = query.filter(StockOutgoing.depot_id == depot_id)
        
        if vehicle_id:
            query = query.filter(StockOutgoing.vehicle_id == vehicle_id)
        
        if client_name:
            query = query.filter(StockOutgoing.client_name.like(f'%{client_name}%'))
        
        # Récupérer toutes les sorties (sans pagination pour l'export)
        outgoings = query.order_by(StockOutgoing.outgoing_date.desc()).all()
        
        # Préparer les données pour Excel
        data = []
        for outgoing in outgoings:
            # Une ligne par détail de sortie
            if outgoing.details:
                for detail in outgoing.details:
                    data.append({
                        'Date': outgoing.outgoing_date.strftime('%d/%m/%Y') if outgoing.outgoing_date else '',
                        'Référence': outgoing.reference or '',
                        'Client': outgoing.client_name or '',
                        'Téléphone': outgoing.client_phone or '',
                        'Dépôt': outgoing.depot.name if outgoing.depot else '',
                        'Véhicule': outgoing.vehicle.plate_number if outgoing.vehicle else '',
                        'Commercial': outgoing.commercial.username if outgoing.commercial else '',
                        'Article (SKU)': detail.stock_item.sku if detail.stock_item else '',
                        'Article': detail.stock_item.name if detail.stock_item else '',
                        'Quantité': float(detail.quantity),
                        'Prix Unitaire (GNF)': float(detail.unit_price_gnf) if detail.unit_price_gnf else 0,
                        'Montant Total (GNF)': float(detail.quantity * detail.unit_price_gnf) if detail.unit_price_gnf else 0,
                        'Utilisateur': outgoing.user.username if outgoing.user else '',
                        'Statut': outgoing.status or 'draft',
                        'Notes': outgoing.notes or ''
                    })
            else:
                # Sortie sans détails
                data.append({
                    'Date': outgoing.outgoing_date.strftime('%d/%m/%Y') if outgoing.outgoing_date else '',
                    'Référence': outgoing.reference or '',
                    'Client': outgoing.client_name or '',
                    'Téléphone': outgoing.client_phone or '',
                    'Dépôt': outgoing.depot.name if outgoing.depot else '',
                    'Véhicule': outgoing.vehicle.plate_number if outgoing.vehicle else '',
                    'Commercial': outgoing.commercial.username if outgoing.commercial else '',
                    'Article (SKU)': '',
                    'Article': '',
                    'Quantité': 0,
                    'Prix Unitaire (GNF)': 0,
                    'Montant Total (GNF)': 0,
                    'Utilisateur': outgoing.user.username if outgoing.user else '',
                    'Statut': outgoing.status or 'draft',
                    'Notes': outgoing.notes or ''
                })
        
        # Créer le DataFrame
        df = pd.DataFrame(data)
        
        # Ajouter une ligne de totaux
        if len(df) > 0:
            total_row = pd.DataFrame([{
                'Date': 'TOTAL',
                'Référence': '',
                'Client': '',
                'Téléphone': '',
                'Dépôt': '',
                'Véhicule': '',
                'Commercial': '',
                'Article (SKU)': '',
                'Article': '',
                'Quantité': df['Quantité'].sum(),
                'Prix Unitaire (GNF)': '',
                'Montant Total (GNF)': df['Montant Total (GNF)'].sum(),
                'Utilisateur': '',
                'Statut': '',
                'Notes': ''
            }])
            df = pd.concat([df, total_row], ignore_index=True)
        
        # Créer le fichier Excel
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Sorties', index=False)
            
            # Formater les colonnes
            worksheet = writer.sheets['Sorties']
            for idx, col in enumerate(df.columns, 1):
                max_length = max(
                    df[col].astype(str).map(len).max(),
                    len(str(col))
                )
                worksheet.column_dimensions[chr(64 + idx)].width = min(max_length + 2, 40)
        
        output.seek(0)
        filename = f'sorties_stock_{datetime.now(UTC).strftime("%Y%m%d_%H%M%S")}.xlsx'
        
        response = make_response(output.getvalue())
        response.headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"❌ Erreur lors de l'export Excel: {e}")
        flash(f'Erreur lors de l\'export Excel: {str(e)}', 'error')
        return redirect(url_for('stocks.outgoings_list'))

@stocks_bp.route('/outgoings/new', methods=['GET', 'POST'])
@login_required
def outgoing_new():
    """Créer une nouvelle sortie de stock"""
    if not has_permission(current_user, 'outgoings.create'):
        flash('Vous n\'avez pas la permission de créer une sortie', 'error')
        return redirect(url_for('stocks.outgoings_list'))
    
    if request.method == 'POST':
        client_name = request.form.get('client_name')
        client_phone = request.form.get('client_phone')
        commercial_id = request.form.get('commercial_id') or None
        vehicle_id = request.form.get('vehicle_id') or None
        depot_id = request.form.get('depot_id') or None
        outgoing_date = request.form.get('outgoing_date') or datetime.now(UTC)
        notes = request.form.get('notes')
        
        if not client_name:
            flash('Le nom du client est obligatoire', 'error')
            return render_template('stocks/outgoing_form.html', **get_outgoing_form_data())
        
        # Générer une référence unique avec UUID pour éviter les collisions
        import uuid
        date_str = datetime.now().strftime('%Y%m%d')
        reference = f"OUT-{date_str}-{uuid.uuid4().hex[:8].upper()}"
        # Vérifier l'unicité (très peu probable avec UUID mais sécurité)
        counter = 0
        while StockOutgoing.query.filter_by(reference=reference).first() and counter < 10:
            reference = f"OUT-{date_str}-{uuid.uuid4().hex[:8].upper()}"
            counter += 1
        if counter >= 10:
            flash('Erreur lors de la génération de la référence. Veuillez réessayer.', 'error')
            return render_template('stocks/outgoing_form.html', **get_outgoing_form_data())
        
        outgoing = StockOutgoing(
            reference=reference,
            client_name=client_name,
            client_phone=client_phone,
            commercial_id=int(commercial_id) if commercial_id else None,
            vehicle_id=int(vehicle_id) if vehicle_id else None,
            depot_id=int(depot_id) if depot_id else None,
            outgoing_date=datetime.strptime(outgoing_date, '%Y-%m-%d') if isinstance(outgoing_date, str) else outgoing_date,
            user_id=current_user.id,
            notes=notes,
            status='draft'
        )
        db.session.add(outgoing)
        db.session.flush()
        
        # Traiter les articles
        items_data = request.form.getlist('items[]')
        if not items_data:
            flash('Veuillez ajouter au moins un article', 'error')
            db.session.rollback()
            return render_template('stocks/outgoing_form.html', **get_outgoing_form_data())
        
        # Créer les détails et décrémenter les stocks
        for item_data in items_data:
            if item_data:
                parts = item_data.split(',')
                if len(parts) >= 2:
                    item_id = int(parts[0])
                    qty = Decimal(parts[1])
                    unit_price = Decimal(parts[2]) if len(parts) > 2 and parts[2] else None
                    
                    # Décrémenter le stock (cache)
                    if vehicle_id:
                        stock = VehicleStock.query.filter_by(vehicle_id=int(vehicle_id), stock_item_id=item_id).first()
                        if not stock or stock.quantity < qty:
                            flash(f'Stock insuffisant pour {StockItem.query.get(item_id).name}', 'error')
                            db.session.rollback()
                            return render_template('stocks/outgoing_form.html', **get_outgoing_form_data())
                        stock.quantity -= qty
                        
                        # Créer le mouvement de stock (SORTIE = négatif)
                        # Utiliser 'transfer' comme type mais avec reason détaillé pour distinguer les sorties clients
                        movement_ref = generate_movement_reference('transfer')
                        # Convertir outgoing_date si c'est une string
                        outgoing_date = outgoing.outgoing_date
                        if isinstance(outgoing_date, str):
                            try:
                                outgoing_date = datetime.strptime(outgoing_date, '%Y-%m-%d')
                            except:
                                outgoing_date = datetime.now()
                        
                        movement = StockMovement(
                            reference=movement_ref,
                            movement_type='transfer',  # Type 'transfer' mais reason indique 'Sortie client'
                            movement_date=outgoing_date,
                            stock_item_id=item_id,
                            quantity=-qty,  # NÉGATIF pour sortie
                            user_id=current_user.id,
                            from_depot_id=None,
                            from_vehicle_id=int(vehicle_id),
                            to_depot_id=None,
                            to_vehicle_id=None,
                            reason=f'[SORTIE_CLIENT] Sortie client: {client_name} - Référence sortie: {outgoing.reference}'
                        )
                        db.session.add(movement)
                    elif depot_id:
                        stock = DepotStock.query.filter_by(depot_id=int(depot_id), stock_item_id=item_id).first()
                        if not stock or stock.quantity < qty:
                            flash(f'Stock insuffisant pour {StockItem.query.get(item_id).name}', 'error')
                            db.session.rollback()
                            return render_template('stocks/outgoing_form.html', **get_outgoing_form_data())
                        stock.quantity -= qty
                        
                        # Créer le mouvement de stock (SORTIE = négatif)
                        # Utiliser 'transfer' comme type mais avec reason détaillé pour distinguer les sorties clients
                        movement_ref = generate_movement_reference('transfer')
                        # Convertir outgoing_date si c'est une string
                        outgoing_date = outgoing.outgoing_date
                        if isinstance(outgoing_date, str):
                            try:
                                outgoing_date = datetime.strptime(outgoing_date, '%Y-%m-%d')
                            except:
                                outgoing_date = datetime.now()
                        
                        movement = StockMovement(
                            reference=movement_ref,
                            movement_type='transfer',  # Type 'transfer' mais reason indique 'Sortie client'
                            movement_date=outgoing_date,
                            stock_item_id=item_id,
                            quantity=-qty,  # NÉGATIF pour sortie
                            user_id=current_user.id,
                            from_depot_id=int(depot_id),
                            from_vehicle_id=None,
                            to_depot_id=None,
                            to_vehicle_id=None,
                            reason=f'[SORTIE_CLIENT] Sortie client: {client_name} - Référence sortie: {outgoing.reference}'
                        )
                        db.session.add(movement)
                    
                    detail = StockOutgoingDetail(
                        outgoing_id=outgoing.id,
                        stock_item_id=item_id,
                        quantity=qty,
                        unit_price_gnf=unit_price
                    )
                    db.session.add(detail)
        
        outgoing.status = 'completed'
        db.session.commit()
        
        flash(f'Sortie "{reference}" créée avec succès', 'success')
        return redirect(url_for('stocks.outgoing_detail', id=outgoing.id))
    
    return render_template('stocks/outgoing_form.html', **get_outgoing_form_data())

def get_outgoing_form_data():
    """Helper pour récupérer les données du formulaire de sortie"""
    from models import Role
    commercial_role = Role.query.filter_by(code='commercial').first()
    commercials = User.query.filter_by(role_id=commercial_role.id, is_active=True).all() if commercial_role else []
    
    return {
        'stock_items': StockItem.query.filter_by(is_active=True).order_by(StockItem.name).all(),
        'depots': Depot.query.filter_by(is_active=True).order_by(Depot.name).all(),
        'vehicles': Vehicle.query.filter_by(status='active').order_by(Vehicle.plate_number).all(),
        'commercials': commercials
    }

@stocks_bp.route('/outgoings/<int:id>')
@login_required
def outgoing_detail(id):
    """Détails d'une sortie"""
    if not has_permission(current_user, 'outgoings.read'):
        flash('Vous n\'avez pas la permission d\'accéder à cette page', 'error')
        return redirect(url_for('stocks.outgoings_list'))
    
    outgoing = StockOutgoing.query.get_or_404(id)
    
    # IMPORTANT: Vérifier les permissions d'accès selon le rôle
    # - Commercial : accède uniquement à SES sorties
    # - Admin : accès à toutes les sorties
    # - Autres rôles : vérifier l'accès par région
    if current_user.role and current_user.role.code == 'commercial':
        if outgoing.commercial_id != current_user.id:
            flash('Vous n\'avez pas accès à cette sortie. Vous ne pouvez voir que vos propres sorties.', 'error')
            return redirect(url_for('stocks.outgoings_list'))
    elif current_user.role and current_user.role.code not in ['admin', 'superadmin']:
        # Vérifier l'accès par région pour les autres rôles
        from utils_region_filter import can_access_depot, can_access_vehicle
        can_access = False
        if outgoing.depot_id:
            can_access = can_access_depot(outgoing.depot_id)
        elif outgoing.vehicle_id:
            can_access = can_access_vehicle(outgoing.vehicle_id)
        
        if not can_access:
            flash('Vous n\'avez pas accès à cette sortie.', 'error')
            return redirect(url_for('stocks.outgoings_list'))
    
    return render_template('stocks/outgoing_detail.html', outgoing=outgoing)

@stocks_bp.route('/outgoings/<int:id>/preview')
@login_required
def outgoing_preview(id):
    """Prévisualisation d'une sortie avant export PDF"""
    if not has_permission(current_user, 'outgoings.read'):
        flash('Vous n\'avez pas la permission d\'accéder à cette page', 'error')
        return redirect(url_for('stocks.outgoings_list'))
    
    outgoing = StockOutgoing.query.get_or_404(id)
    
    # Vérifier les permissions d'accès (même logique que outgoing_detail)
    if current_user.role and current_user.role.code == 'commercial':
        if outgoing.commercial_id != current_user.id:
            flash('Vous n\'avez pas accès à cette sortie.', 'error')
            return redirect(url_for('stocks.outgoings_list'))
    elif current_user.role and current_user.role.code not in ['admin', 'superadmin']:
        from utils_region_filter import can_access_depot, can_access_vehicle
        can_access = False
        if outgoing.depot_id:
            can_access = can_access_depot(outgoing.depot_id)
        elif outgoing.vehicle_id:
            can_access = can_access_vehicle(outgoing.vehicle_id)
        if not can_access:
            flash('Vous n\'avez pas accès à cette sortie.', 'error')
            return redirect(url_for('stocks.outgoings_list'))
    
    return render_template('stocks/outgoing_preview.html', outgoing=outgoing)

@stocks_bp.route('/outgoings/<int:id>/pdf')
@login_required
def outgoing_pdf(id):
    """Générer un PDF pour une sortie"""
    if not has_permission(current_user, 'outgoings.read'):
        flash('Vous n\'avez pas la permission d\'accéder à cette page', 'error')
        return redirect(url_for('stocks.outgoings_list'))
    
    outgoing = StockOutgoing.query.get_or_404(id)
    
    # Vérifier les permissions d'accès (même logique que outgoing_detail)
    if current_user.role and current_user.role.code == 'commercial':
        if outgoing.commercial_id != current_user.id:
            flash('Vous n\'avez pas accès à cette sortie.', 'error')
            return redirect(url_for('stocks.outgoings_list'))
    elif current_user.role and current_user.role.code not in ['admin', 'superadmin']:
        from utils_region_filter import can_access_depot, can_access_vehicle
        can_access = False
        if outgoing.depot_id:
            can_access = can_access_depot(outgoing.depot_id)
        elif outgoing.vehicle_id:
            can_access = can_access_vehicle(outgoing.vehicle_id)
        if not can_access:
            flash('Vous n\'avez pas accès à cette sortie.', 'error')
        return redirect(url_for('stocks.outgoings_list'))
    
    from pdf_generator import PDFGenerator
    from flask import make_response
    
    try:
        outgoing = StockOutgoing.query.get_or_404(id)
        pdf_gen = PDFGenerator()
        pdf_buffer = pdf_gen.generate_outgoing_pdf(outgoing)
        
        filename = f'sortie_{outgoing.reference}_{datetime.now(UTC).strftime("%Y%m%d_%H%M%S")}.pdf'
        response = make_response(pdf_buffer.getvalue())
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"❌ Erreur lors de la génération du PDF: {e}")
        flash(f'Erreur lors de la génération du PDF: {str(e)}', 'error')
        return redirect(url_for('stocks.outgoing_detail', id=id))

# =========================================================
# RETOURS DE STOCK
# =========================================================

@stocks_bp.route('/returns')
@login_required
def returns_list():
    """Liste des retours avec pagination et filtres"""
    if not has_permission(current_user, 'returns.read'):
        flash('Vous n\'avez pas la permission d\'accéder à cette page', 'error')
        return redirect(url_for('index'))
    
    from sqlalchemy import or_
    from datetime import datetime, timedelta
    from utils_region_filter import filter_depots_by_region, filter_vehicles_by_region
    
    # Paramètres de pagination
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    
    # Filtres
    search = request.args.get('search', '').strip()
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    depot_id = request.args.get('depot_id', type=int)
    vehicle_id = request.args.get('vehicle_id', type=int)
    client_name = request.args.get('client_name', '').strip()
    
    try:
        # Construire la requête avec optimisation N+1
        # Utiliser load_only pour éviter de charger la colonne 'reason' qui n'existe pas en MySQL
        from sqlalchemy.orm import load_only
        query = StockReturn.query.options(
            load_only(
                StockReturn.id, StockReturn.reference, StockReturn.return_date,
                StockReturn.return_type, StockReturn.client_name, StockReturn.client_phone,
                StockReturn.original_outgoing_id, StockReturn.original_order_id,
                StockReturn.supplier_name, StockReturn.original_reception_id,
                StockReturn.commercial_id, StockReturn.vehicle_id, StockReturn.depot_id,
                StockReturn.user_id, StockReturn.notes, StockReturn.status,
                StockReturn.created_at, StockReturn.updated_at
            ),
            joinedload(StockReturn.depot),
            joinedload(StockReturn.vehicle),
            joinedload(StockReturn.commercial),
            joinedload(StockReturn.user),
            joinedload(StockReturn.details).joinedload(StockReturnDetail.stock_item)
        )
        
        # IMPORTANT: Filtrer selon le rôle de l'utilisateur
        # - Commercial : voit uniquement SES retours (commercial_id == current_user.id)
        # - Admin : voit tous les retours
        # - Autres rôles : filtrer par région
        if current_user.role and current_user.role.code == 'commercial':
            query = query.filter(StockReturn.commercial_id == current_user.id)
        elif current_user.role and current_user.role.code in ['admin', 'superadmin']:
            # Admin voit tous les retours sans filtre supplémentaire
            pass
        else:
            # Filtrer par région : seuls les retours des dépôts/véhicules accessibles
            accessible_depot_ids = [d.id for d in filter_depots_by_region(Depot.query).all()]
            accessible_vehicle_ids = [v.id for v in filter_vehicles_by_region(Vehicle.query).all()]
            
            if accessible_depot_ids or accessible_vehicle_ids:
                query = query.filter(
                    or_(
                        StockReturn.depot_id.in_(accessible_depot_ids) if accessible_depot_ids else False,
                        StockReturn.vehicle_id.in_(accessible_vehicle_ids) if accessible_vehicle_ids else False
                    )
                )
            else:
                # Aucun dépôt/véhicule accessible, retourner une requête vide
                query = query.filter(False)
        
        # Appliquer les filtres
        if search:
            query = query.filter(
                or_(
                    StockReturn.reference.like(f'%{search}%'),
                    StockReturn.client_name.like(f'%{search}%'),
                    StockReturn.client_phone.like(f'%{search}%')
                )
            )
        
        if date_from:
            try:
                date_from_obj = datetime.strptime(date_from, '%Y-%m-%d')
                query = query.filter(StockReturn.return_date >= date_from_obj)
            except ValueError:
                pass
        
        if date_to:
            try:
                date_to_obj = datetime.strptime(date_to, '%Y-%m-%d') + timedelta(days=1)
                query = query.filter(StockReturn.return_date < date_to_obj)
            except ValueError:
                pass
        
        if depot_id:
            query = query.filter(StockReturn.depot_id == depot_id)
        
        if vehicle_id:
            query = query.filter(StockReturn.vehicle_id == vehicle_id)
        
        if client_name:
            query = query.filter(StockReturn.client_name.like(f'%{client_name}%'))
        
        # Pagination
        pagination = query.order_by(StockReturn.return_date.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        returns = pagination.items
        
        # Statistiques
        total_returns = StockReturn.query.count()
        
        # Données pour filtres (filtrées par région)
        depots_query = Depot.query.filter_by(is_active=True)
        depots_query = filter_depots_by_region(depots_query)
        depots = depots_query.order_by(Depot.name).all()
        vehicles_query = Vehicle.query.filter_by(status='active')
        vehicles_query = filter_vehicles_by_region(vehicles_query)
        vehicles = vehicles_query.order_by(Vehicle.plate_number).all()
        
        return render_template('stocks/returns_list.html', 
                             returns=returns,
                             pagination=pagination,
                             search=search,
                             date_from=date_from,
                             date_to=date_to,
                             depot_id=depot_id,
                             vehicle_id=vehicle_id,
                             client_name=client_name,
                             per_page=per_page,
                             total_returns=total_returns,
                             depots=depots,
                             vehicles=vehicles)
    
    except Exception as e:
        print(f"⚠️ Erreur lors de la récupération des retours: {e}")
        # Si l'erreur est due à original_outgoing_id, utiliser une requête SQL directe
        if 'original_outgoing_id' in str(e):
            try:
                from sqlalchemy import text, inspect
                # Vérifier quelles colonnes existent dans la table
                inspector = inspect(db.engine)
                columns = [col['name'] for col in inspector.get_columns('stock_returns')]
                
                # Construire la liste des colonnes à sélectionner (sans original_outgoing_id)
                select_cols = []
                for col in ['id', 'reference', 'return_date', 'client_name', 'client_phone',
                           'commercial_id', 'vehicle_id', 'depot_id', 'user_id', 'reason',
                           'notes', 'status', 'created_at', 'updated_at']:
                    if col in columns:
                        select_cols.append(col)
                
                # Paramètres de pagination
                page = request.args.get('page', 1, type=int)
                per_page = request.args.get('per_page', 50, type=int)
                offset = (page - 1) * per_page
                
                if select_cols:
                    cols_str = ', '.join(select_cols)
                    # Compter le total
                    count_result = db.session.execute(text("SELECT COUNT(*) FROM stock_returns")).scalar()
                    total_returns = count_result
                    
                    # Requête paginée
                    result = db.session.execute(text(f"""
                        SELECT {cols_str}
                        FROM stock_returns 
                        ORDER BY return_date DESC
                        LIMIT :limit OFFSET :offset
                    """), {'limit': per_page, 'offset': offset})
                    
                    # Créer des objets StockReturn à partir des résultats
                    returns = []
                    for row in result:
                        ret = StockReturn()
                        col_idx = 0
                        for col in select_cols:
                            if hasattr(ret, col):
                                value = row[col_idx]
                                if col == 'status' and value is None:
                                    value = 'draft'
                                setattr(ret, col, value)
                            col_idx += 1
                        returns.append(ret)
                    
                    # Créer un objet pagination simulé
                    from math import ceil
                    pagination = type('Pagination', (), {
                        'items': returns,
                        'page': page,
                        'per_page': per_page,
                        'total': total_returns,
                        'pages': ceil(total_returns / per_page) if per_page > 0 else 1,
                        'has_prev': page > 1,
                        'has_next': page < ceil(total_returns / per_page) if per_page > 0 else False,
                        'prev_num': page - 1 if page > 1 else None,
                        'next_num': page + 1 if page < ceil(total_returns / per_page) else None
                    })()
                    
                    # Données pour filtres
                    depots = Depot.query.filter_by(is_active=True).order_by(Depot.name).all()
                    vehicles = Vehicle.query.filter_by(status='active').order_by(Vehicle.plate_number).all()
                    
                    return render_template('stocks/returns_list.html', 
                                         returns=returns,
                                         pagination=pagination,
                                         search=request.args.get('search', ''),
                                         date_from=request.args.get('date_from', ''),
                                         date_to=request.args.get('date_to', ''),
                                         depot_id=request.args.get('depot_id', type=int),
                                         vehicle_id=request.args.get('vehicle_id', type=int),
                                         client_name=request.args.get('client_name', ''),
                                         per_page=per_page,
                                         total_returns=total_returns,
                                         depots=depots,
                                         vehicles=vehicles)
                else:
                    returns = []
                    pagination = None
            except Exception as e2:
                print(f"⚠️ Erreur lors de la récupération SQL directe: {e2}")
                returns = []
                pagination = None
        else:
            returns = []
            pagination = None
        
        # Fallback avec données minimales
        depots = Depot.query.filter_by(is_active=True).order_by(Depot.name).all()
        vehicles = Vehicle.query.filter_by(status='active').order_by(Vehicle.plate_number).all()
        
        return render_template('stocks/returns_list.html', 
                             returns=returns or [],
                             pagination=pagination,
                             search='',
                             date_from='',
                             date_to='',
                             depot_id=None,
                             vehicle_id=None,
                             client_name='',
                             per_page=50,
                             total_returns=0,
                             depots=depots,
                             vehicles=vehicles)
    except Exception as e:
        print(f"⚠️ Erreur lors de la récupération des retours: {e}")
        # Si l'erreur est due à original_outgoing_id, utiliser une requête SQL directe
        if 'original_outgoing_id' in str(e):
            try:
                from sqlalchemy import text, inspect
                # Vérifier quelles colonnes existent dans la table
                inspector = inspect(db.engine)
                columns = [col['name'] for col in inspector.get_columns('stock_returns')]
                
                # Construire la liste des colonnes à sélectionner (sans original_outgoing_id)
                select_cols = []
                for col in ['id', 'reference', 'return_date', 'client_name', 'client_phone',
                           'commercial_id', 'vehicle_id', 'depot_id', 'user_id', 'reason',
                           'notes', 'status', 'created_at', 'updated_at']:
                    if col in columns:
                        select_cols.append(col)
                
                if select_cols:
                    cols_str = ', '.join(select_cols)
                    result = db.session.execute(text(f"""
                        SELECT {cols_str}
                        FROM stock_returns 
                        ORDER BY return_date DESC
                        LIMIT 50
                    """))
                    # Créer des objets StockReturn à partir des résultats
                    returns = []
                    for row in result:
                        ret = StockReturn()
                        col_idx = 0
                        for col in select_cols:
                            if hasattr(ret, col):
                                value = row[col_idx]
                                if col == 'status' and value is None:
                                    value = 'draft'
                                setattr(ret, col, value)
                            col_idx += 1
                        # Charger les détails
                        try:
                            ret.details = StockReturnDetail.query.filter_by(return_id=ret.id).all()
                        except:
                            ret.details = []
                        returns.append(ret)
                    print(f"✅ {len(returns)} retours récupérés via SQL direct")
                else:
                    returns = []
            except Exception as e2:
                print(f"⚠️ Erreur lors de la récupération SQL directe des retours: {e2}")
                import traceback
                traceback.print_exc()
                returns = []
        else:
            returns = []
    
    return render_template('stocks/returns_list.html', 
                         returns=returns,
                         pagination=None,
                         search='',
                         date_from='',
                         date_to='',
                         depot_id=None,
                         vehicle_id=None,
                         client_name='',
                         per_page=50,
                         total_returns=len(returns) if returns else 0,
                         depots=Depot.query.filter_by(is_active=True).order_by(Depot.name).all(),
                         vehicles=Vehicle.query.filter_by(status='active').order_by(Vehicle.plate_number).all())

@stocks_bp.route('/returns/export/excel')
@login_required
def returns_export_excel():
    """Export Excel des retours avec filtres appliqués"""
    if not has_permission(current_user, 'returns.read'):
        flash("Vous n'avez pas la permission d'exporter les données.", "error")
        return redirect(url_for('stocks.returns_list'))
    
    import pandas as pd
    from sqlalchemy import or_
    
    # Récupérer les mêmes filtres que returns_list
    search = request.args.get('search', '').strip()
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    depot_id = request.args.get('depot_id', type=int)
    vehicle_id = request.args.get('vehicle_id', type=int)
    client_name = request.args.get('client_name', '').strip()
    
    try:
        # Construire la requête (même logique que returns_list)
        # Utiliser load_only pour éviter de charger la colonne 'reason' qui n'existe pas en MySQL
        from sqlalchemy.orm import load_only
        from utils_region_filter import filter_depots_by_region, filter_vehicles_by_region
        query = StockReturn.query.options(
            load_only(
                StockReturn.id, StockReturn.reference, StockReturn.return_date,
                StockReturn.return_type, StockReturn.client_name, StockReturn.client_phone,
                StockReturn.original_outgoing_id, StockReturn.original_order_id,
                StockReturn.supplier_name, StockReturn.original_reception_id,
                StockReturn.commercial_id, StockReturn.vehicle_id, StockReturn.depot_id,
                StockReturn.user_id, StockReturn.notes, StockReturn.status,
                StockReturn.created_at, StockReturn.updated_at
            ),
            joinedload(StockReturn.depot),
            joinedload(StockReturn.vehicle),
            joinedload(StockReturn.commercial),
            joinedload(StockReturn.user),
            joinedload(StockReturn.details).joinedload(StockReturnDetail.stock_item)
        )
        
        # IMPORTANT: Filtrer selon le rôle de l'utilisateur (même logique que returns_list)
        if current_user.role and current_user.role.code == 'commercial':
            query = query.filter(StockReturn.commercial_id == current_user.id)
        elif current_user.role and current_user.role.code not in ['admin', 'superadmin']:
            # Filtrer par région pour les autres rôles
            accessible_depot_ids = [d.id for d in filter_depots_by_region(Depot.query).all()]
            accessible_vehicle_ids = [v.id for v in filter_vehicles_by_region(Vehicle.query).all()]
            if accessible_depot_ids or accessible_vehicle_ids:
                query = query.filter(
                    or_(
                        StockReturn.depot_id.in_(accessible_depot_ids) if accessible_depot_ids else False,
                        StockReturn.vehicle_id.in_(accessible_vehicle_ids) if accessible_vehicle_ids else False
                    )
                )
            else:
                query = query.filter(False)
        
        # Appliquer les filtres
        if search:
            query = query.filter(
                or_(
                    StockReturn.reference.like(f'%{search}%'),
                    StockReturn.client_name.like(f'%{search}%'),
                    StockReturn.client_phone.like(f'%{search}%')
                )
            )
        
        if date_from:
            try:
                date_from_obj = datetime.strptime(date_from, '%Y-%m-%d')
                query = query.filter(StockReturn.return_date >= date_from_obj)
            except ValueError:
                pass
        
        if date_to:
            try:
                date_to_obj = datetime.strptime(date_to, '%Y-%m-%d') + timedelta(days=1)
                query = query.filter(StockReturn.return_date < date_to_obj)
            except ValueError:
                pass
        
        if depot_id:
            query = query.filter(StockReturn.depot_id == depot_id)
        
        if vehicle_id:
            query = query.filter(StockReturn.vehicle_id == vehicle_id)
        
        if client_name:
            query = query.filter(StockReturn.client_name.like(f'%{client_name}%'))
        
        # Récupérer tous les retours (sans pagination pour l'export)
        returns = query.order_by(StockReturn.return_date.desc()).all()
        
        # Préparer les données pour Excel
        data = []
        for return_ in returns:
            # Une ligne par détail de retour
            if return_.details:
                for detail in return_.details:
                    data.append({
                        'Date': return_.return_date.strftime('%d/%m/%Y') if return_.return_date else '',
                        'Référence': return_.reference or '',
                        'Client': return_.client_name or '',
                        'Téléphone': return_.client_phone or '',
                        'Dépôt': return_.depot.name if return_.depot else '',
                        'Véhicule': return_.vehicle.plate_number if return_.vehicle else '',
                        'Commercial': return_.commercial.username if return_.commercial else '',
                        'Article (SKU)': detail.stock_item.sku if detail.stock_item else '',
                        'Article': detail.stock_item.name if detail.stock_item else '',
                        'Quantité': float(detail.quantity),
                        'Raison': getattr(return_, 'reason', None) or '',
                        'Utilisateur': return_.user.username if return_.user else '',
                        'Statut': return_.status or 'draft',
                        'Notes': return_.notes or ''
                    })
            else:
                # Retour sans détails
                data.append({
                    'Date': return_.return_date.strftime('%d/%m/%Y') if return_.return_date else '',
                    'Référence': return_.reference or '',
                    'Client': return_.client_name or '',
                    'Téléphone': return_.client_phone or '',
                    'Dépôt': return_.depot.name if return_.depot else '',
                    'Véhicule': return_.vehicle.plate_number if return_.vehicle else '',
                    'Commercial': return_.commercial.username if return_.commercial else '',
                    'Article (SKU)': '',
                    'Article': '',
                    'Quantité': 0,
                    'Raison': getattr(return_, 'reason', None) or '',
                    'Utilisateur': return_.user.username if return_.user else '',
                    'Statut': return_.status or 'draft',
                    'Notes': return_.notes or ''
                })
        
        # Créer le DataFrame
        df = pd.DataFrame(data)
        
        # Ajouter une ligne de totaux
        if len(df) > 0:
            total_row = pd.DataFrame([{
                'Date': 'TOTAL',
                'Référence': '',
                'Client': '',
                'Téléphone': '',
                'Dépôt': '',
                'Véhicule': '',
                'Commercial': '',
                'Article (SKU)': '',
                'Article': '',
                'Quantité': df['Quantité'].sum(),
                'Raison': '',
                'Utilisateur': '',
                'Statut': '',
                'Notes': ''
            }])
            df = pd.concat([df, total_row], ignore_index=True)
        
        # Créer le fichier Excel
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Retours', index=False)
            
            # Formater les colonnes
            worksheet = writer.sheets['Retours']
            for idx, col in enumerate(df.columns, 1):
                max_length = max(
                    df[col].astype(str).map(len).max(),
                    len(str(col))
                )
                worksheet.column_dimensions[chr(64 + idx)].width = min(max_length + 2, 40)
        
        output.seek(0)
        filename = f'retours_stock_{datetime.now(UTC).strftime("%Y%m%d_%H%M%S")}.xlsx'
        
        response = make_response(output.getvalue())
        response.headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"❌ Erreur lors de l'export Excel: {e}")
        flash(f'Erreur lors de l\'export Excel: {str(e)}', 'error')
        return redirect(url_for('stocks.returns_list'))

@stocks_bp.route('/returns/new', methods=['GET', 'POST'])
@login_required
def return_new():
    """Créer un nouveau retour de stock (client ou fournisseur)"""
    if not has_permission(current_user, 'returns.create'):
        flash('Vous n\'avez pas la permission de créer un retour', 'error')
        return redirect(url_for('stocks.returns_list'))
    
    if request.method == 'POST':
        # Déterminer le type de retour
        return_type = request.form.get('return_type', 'client')  # 'client' ou 'supplier'
        
        # Champs communs
        return_date = request.form.get('return_date') or datetime.now(UTC)
        reason = request.form.get('reason')
        notes = request.form.get('notes')
        commercial_id = request.form.get('commercial_id') or None
        vehicle_id = request.form.get('vehicle_id') or None
        depot_id = request.form.get('depot_id') or None
        
        # Champs spécifiques selon le type
        if return_type == 'supplier':
            # Retour fournisseur (mouvement inverse de réception)
            supplier_name = request.form.get('supplier_name')
            original_reception_id = request.form.get('original_reception_id') or None
            
            if not supplier_name:
                flash('Le nom du fournisseur est obligatoire pour un retour fournisseur', 'error')
                return render_template('stocks/return_form.html', **get_return_form_data())
            
            if not depot_id:
                flash('Le dépôt source est obligatoire pour un retour fournisseur', 'error')
                return render_template('stocks/return_form.html', **get_return_form_data())
        else:
            # Retour client (logique actuelle)
            client_name = request.form.get('client_name')
            client_phone = request.form.get('client_phone')
            original_outgoing_id = request.form.get('original_outgoing_id') or None
            
            if not client_name:
                flash('Le nom du client est obligatoire', 'error')
                return render_template('stocks/return_form.html', **get_return_form_data())
        
        # Générer une référence unique avec UUID pour éviter les collisions
        import uuid
        date_str = datetime.now().strftime('%Y%m%d')
        reference = f"RET-{date_str}-{uuid.uuid4().hex[:8].upper()}"
        # Vérifier l'unicité (très peu probable avec UUID mais sécurité)
        try:
            counter = 0
            while StockReturn.query.filter_by(reference=reference).first() and counter < 10:
                reference = f"RET-{date_str}-{uuid.uuid4().hex[:8].upper()}"
                counter += 1
            if counter >= 10:
                flash('Erreur lors de la génération de la référence. Veuillez réessayer.', 'error')
                return render_template('stocks/return_form.html', **get_return_form_data())
        except Exception as ref_check_error:
            if 'reference' not in str(ref_check_error):
                # Si l'erreur n'est pas liée à reference, on continue quand même
                print(f"⚠️ Erreur lors de la vérification de l'unicité de la référence: {ref_check_error}")
        
        # Construire les données du retour
        return_data = {
            'reference': reference,
            'return_type': return_type,
            'commercial_id': int(commercial_id) if commercial_id else None,
            'vehicle_id': int(vehicle_id) if vehicle_id else None,
            'depot_id': int(depot_id) if depot_id else None,
            'return_date': datetime.strptime(return_date, '%Y-%m-%d') if isinstance(return_date, str) else return_date,
            'user_id': current_user.id,
            'notes': notes,
            'status': 'draft'
        }
        
        # Ajouter les champs spécifiques selon le type
        if return_type == 'supplier':
            return_data['supplier_name'] = supplier_name
            if original_reception_id:
                return_data['original_reception_id'] = int(original_reception_id)
        else:
            return_data['client_name'] = client_name
            return_data['client_phone'] = client_phone
            if original_outgoing_id:
                return_data['original_outgoing_id'] = int(original_outgoing_id)
        
        # Vérifier si la colonne reason existe dans la base de données
        reason_column_exists = False
        try:
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('stock_returns')]
            reason_column_exists = 'reason' in columns
            if not reason_column_exists:
                print("⚠️ Colonne 'reason' n'existe pas dans stock_returns, elle sera omise")
        except Exception as e:
            # Si la vérification échoue, on assume que reason n'existe pas pour être sûr
            print(f"⚠️ Impossible de vérifier la colonne reason: {e}. On assume qu'elle n'existe pas.")
            reason_column_exists = False
        
        # Ajouter reason seulement si la colonne existe
        if reason_column_exists:
            return_data['reason'] = reason
        
        # Créer l'objet StockReturn
        return_ = StockReturn(**return_data)
        
        # Si reason n'existe pas dans la base mais est dans le modèle,
        # le retirer de __dict__ avant l'insertion pour éviter qu'il soit inclus dans l'INSERT
        if not reason_column_exists:
            try:
                # Retirer reason de __dict__ pour éviter qu'il soit inclus dans l'INSERT SQL
                if hasattr(return_, '__dict__') and 'reason' in return_.__dict__:
                    del return_.__dict__['reason']
                # Aussi retirer de _sa_instance_state si présent
                if hasattr(return_, '_sa_instance_state'):
                    state = return_._sa_instance_state
                    if hasattr(state, 'unmodified') and 'reason' in state.unmodified:
                        state.unmodified = tuple(k for k in state.unmodified if k != 'reason')
            except Exception as e:
                print(f"⚠️ Impossible de retirer reason de l'objet: {e}")
        
        db.session.add(return_)
        
        # Gérer l'erreur si reason cause un problème lors du flush
        try:
            db.session.flush()
        except Exception as flush_error:
            # Si l'erreur est due à reason, réessayer sans reason
            error_str = str(flush_error).lower()
            if 'reason' in error_str or 'unknown column' in error_str:
                db.session.rollback()
                # Retirer reason de return_data et recréer l'objet
                return_data.pop('reason', None)
                return_ = StockReturn(**return_data)
                # Retirer reason de l'objet si présent
                if hasattr(return_, '__dict__') and 'reason' in return_.__dict__:
                    del return_.__dict__['reason']
                db.session.add(return_)
                db.session.flush()
            else:
                raise
        
        # Traiter les articles
        items_data = request.form.getlist('items[]')
        if not items_data:
            flash('Veuillez ajouter au moins un article', 'error')
            db.session.rollback()
            return render_template('stocks/return_form.html', **get_return_form_data())
        
        # Créer les détails et gérer les stocks selon le type de retour
        for item_data in items_data:
            if item_data:
                parts = item_data.split(',')
                if len(parts) >= 2:
                    item_id = int(parts[0])
                    qty = Decimal(parts[1])
                    
                    # Convertir return_date si c'est une string
                    return_date_obj = return_.return_date
                    if isinstance(return_date_obj, str):
                        try:
                            return_date_obj = datetime.strptime(return_date_obj, '%Y-%m-%d')
                        except:
                            return_date_obj = datetime.now()
                    
                    if return_type == 'supplier':
                        # RETOUR FOURNISSEUR : Mouvement inverse de réception
                        # Diminue le stock (quantité NÉGATIVE)
                        if depot_id:
                            # Vérifier que le stock est suffisant
                            stock = DepotStock.query.filter_by(depot_id=int(depot_id), stock_item_id=item_id).first()
                            if not stock or stock.quantity < qty:
                                item = StockItem.query.get(item_id)
                                item_name = item.name if item else f"ID {item_id}"
                                available = stock.quantity if stock else Decimal('0')
                                flash(f'Stock insuffisant pour {item_name} (disponible: {available}, requis: {qty})', 'error')
                                db.session.rollback()
                                return render_template('stocks/return_form.html', **get_return_form_data())
                            
                            # Diminuer le stock
                            stock.quantity -= qty
                            
                            # Créer le mouvement de stock (SORTIE = négatif)
                            movement_ref = generate_movement_reference('reception_return')
                            movement = StockMovement(
                                reference=movement_ref,
                                movement_type='reception_return',  # Type dédié pour retours fournisseurs
                                movement_date=return_date_obj,
                                stock_item_id=item_id,
                                quantity=-qty,  # NÉGATIF pour diminuer le stock
                                user_id=current_user.id,
                                from_depot_id=int(depot_id),  # Source = dépôt
                                from_vehicle_id=None,
                                to_depot_id=None,  # Pas de destination (retour externe)
                                to_vehicle_id=None,
                                supplier_name=supplier_name,
                                reason=f'[RETOUR_FOURNISSEUR] Retour vers {supplier_name} - Référence retour: {return_.reference}' + 
                                       (f' - Référence réception: {return_.original_reception.reference}' if return_.original_reception else '')
                            )
                            db.session.add(movement)
                        else:
                            flash('Le dépôt source est obligatoire pour un retour fournisseur', 'error')
                            db.session.rollback()
                            return render_template('stocks/return_form.html', **get_return_form_data())
                    else:
                        # RETOUR CLIENT : Augmente le stock (quantité POSITIVE)
                        if vehicle_id:
                            stock = VehicleStock.query.filter_by(vehicle_id=int(vehicle_id), stock_item_id=item_id).first()
                            if not stock:
                                stock = VehicleStock(vehicle_id=int(vehicle_id), stock_item_id=item_id, quantity=Decimal('0'))
                                db.session.add(stock)
                            stock.quantity += qty
                            
                            # Créer le mouvement de stock (ENTRÉE = positif)
                            movement_ref = generate_movement_reference('transfer')
                            movement = StockMovement(
                                reference=movement_ref,
                                movement_type='transfer',  # Type 'transfer' pour retours clients
                                movement_date=return_date_obj,
                                stock_item_id=item_id,
                                quantity=qty,  # POSITIF pour entrée
                                user_id=current_user.id,
                                from_depot_id=None,
                                from_vehicle_id=None,
                                to_depot_id=None,
                                to_vehicle_id=int(vehicle_id),
                                reason=f'[RETOUR_CLIENT] Retour client: {client_name} - Référence retour: {return_.reference}'
                            )
                            db.session.add(movement)
                        elif depot_id:
                            stock = DepotStock.query.filter_by(depot_id=int(depot_id), stock_item_id=item_id).first()
                            if not stock:
                                stock = DepotStock(depot_id=int(depot_id), stock_item_id=item_id, quantity=Decimal('0'))
                                db.session.add(stock)
                            stock.quantity += qty
                            
                            # Créer le mouvement de stock (ENTRÉE = positif)
                            movement_ref = generate_movement_reference('transfer')
                            movement = StockMovement(
                                reference=movement_ref,
                                movement_type='transfer',  # Type 'transfer' pour retours clients
                                movement_date=return_date_obj,
                                stock_item_id=item_id,
                                quantity=qty,  # POSITIF pour entrée
                                user_id=current_user.id,
                                from_depot_id=None,
                                from_vehicle_id=None,
                                to_depot_id=int(depot_id),
                                to_vehicle_id=None,
                                reason=f'[RETOUR_CLIENT] Retour client: {client_name} - Référence retour: {return_.reference}'
                            )
                            db.session.add(movement)
                    
                    detail = StockReturnDetail(
                        return_id=return_.id,
                        stock_item_id=item_id,
                        quantity=qty
                    )
                    db.session.add(detail)
        
        return_.status = 'completed'
        db.session.commit()
        
        flash(f'Retour "{reference}" créé avec succès', 'success')
        return redirect(url_for('stocks.return_detail', id=return_.id))
    
    return render_template('stocks/return_form.html', **get_return_form_data())

def get_return_form_data():
    """Helper pour récupérer les données du formulaire de retour"""
    from models import Role
    commercial_role = Role.query.filter_by(code='commercial').first()
    commercials = User.query.filter_by(role_id=commercial_role.id, is_active=True).all() if commercial_role else []
    
    return {
        'stock_items': StockItem.query.filter_by(is_active=True).order_by(StockItem.name).all(),
        'depots': Depot.query.filter_by(is_active=True).order_by(Depot.name).all(),
        'vehicles': Vehicle.query.filter_by(status='active').order_by(Vehicle.plate_number).all(),
        'outgoings': StockOutgoing.query.filter_by(status='completed').order_by(StockOutgoing.outgoing_date.desc()).limit(100).all(),
        'receptions': Reception.query.filter_by(status='completed').order_by(Reception.reception_date.desc()).limit(100).all(),
        'commercials': commercials
    }

@stocks_bp.route('/returns/<int:id>')
@login_required
def return_detail(id):
    """Détails d'un retour"""
    if not has_permission(current_user, 'returns.read'):
        flash('Vous n\'avez pas la permission d\'accéder à cette page', 'error')
        return redirect(url_for('stocks.returns_list'))
    
    try:
        return_ = StockReturn.query.get_or_404(id)
    except Exception as e:
        print(f"⚠️ Erreur lors de la récupération du retour {id}: {e}")
        # Si l'erreur est due à original_outgoing_id, utiliser une requête SQL directe
        if 'original_outgoing_id' in str(e):
            try:
                from sqlalchemy import text, inspect
                inspector = inspect(db.engine)
                columns = [col['name'] for col in inspector.get_columns('stock_returns')]
                
                select_cols = []
                for col in ['id', 'reference', 'return_date', 'client_name', 'client_phone',
                           'commercial_id', 'vehicle_id', 'depot_id', 'user_id', 'reason',
                           'notes', 'status', 'created_at', 'updated_at']:
                    if col in columns:
                        select_cols.append(col)
                
                if select_cols and 'id' in select_cols:
                    cols_str = ', '.join(select_cols)
                    result = db.session.execute(text(f"""
                        SELECT {cols_str}
                        FROM stock_returns 
                        WHERE id = :id
                    """), {'id': id}).first()
                    
                    if not result:
                        flash('Retour non trouvé', 'error')
                        return redirect(url_for('stocks.returns_list'))
                    
                    return_ = StockReturn()
                    col_idx = 0
                    for col in select_cols:
                        if hasattr(return_, col):
                            value = result[col_idx]
                            if col == 'status' and value is None:
                                value = 'draft'
                            setattr(return_, col, value)
                        col_idx += 1
                    
                    # Charger les détails
                    try:
                        return_.details = StockReturnDetail.query.filter_by(return_id=return_.id).all()
                    except:
                        return_.details = []
                else:
                    flash('Retour non trouvé', 'error')
                    return redirect(url_for('stocks.returns_list'))
            except Exception as e2:
                print(f"⚠️ Erreur lors de la récupération SQL directe: {e2}")
                flash('Erreur lors de la récupération du retour', 'error')
                return redirect(url_for('stocks.returns_list'))
        else:
            flash('Erreur lors de la récupération du retour', 'error')
            return redirect(url_for('stocks.returns_list'))
    
    # IMPORTANT: Vérifier les permissions d'accès selon le rôle
    # - Commercial : accède uniquement à SES retours
    # - Admin : accès à tous les retours
    # - Autres rôles : vérifier l'accès par région
    if current_user.role and current_user.role.code == 'commercial':
        if return_.commercial_id != current_user.id:
            flash('Vous n\'avez pas accès à ce retour. Vous ne pouvez voir que vos propres retours.', 'error')
            return redirect(url_for('stocks.returns_list'))
    elif current_user.role and current_user.role.code not in ['admin', 'superadmin']:
        # Vérifier l'accès par région pour les autres rôles
        from utils_region_filter import can_access_depot, can_access_vehicle
        can_access = False
        if return_.depot_id:
            can_access = can_access_depot(return_.depot_id)
        elif return_.vehicle_id:
            can_access = can_access_vehicle(return_.vehicle_id)
        
        if not can_access:
            flash('Vous n\'avez pas accès à ce retour.', 'error')
            return redirect(url_for('stocks.returns_list'))
    
    return render_template('stocks/return_detail.html', return_=return_)

@stocks_bp.route('/returns/<int:id>/preview')
@login_required
def return_preview(id):
    """Prévisualisation d'un retour avant export PDF"""
    if not has_permission(current_user, 'returns.read'):
        flash('Vous n\'avez pas la permission d\'accéder à cette page', 'error')
        return redirect(url_for('stocks.returns_list'))
    
    return_ = StockReturn.query.get_or_404(id)
    
    # Vérifier les permissions d'accès (même logique que return_detail)
    if current_user.role and current_user.role.code == 'commercial':
        if return_.commercial_id != current_user.id:
            flash('Vous n\'avez pas accès à ce retour.', 'error')
            return redirect(url_for('stocks.returns_list'))
    elif current_user.role and current_user.role.code not in ['admin', 'superadmin']:
        from utils_region_filter import can_access_depot, can_access_vehicle
        can_access = False
        if return_.depot_id:
            can_access = can_access_depot(return_.depot_id)
        elif return_.vehicle_id:
            can_access = can_access_vehicle(return_.vehicle_id)
        if not can_access:
            flash('Vous n\'avez pas accès à ce retour.', 'error')
            return redirect(url_for('stocks.returns_list'))
    
    return render_template('stocks/return_preview.html', return_=return_)

@stocks_bp.route('/returns/<int:id>/pdf')
@login_required
def return_pdf(id):
    """Générer un PDF pour un retour"""
    if not has_permission(current_user, 'returns.read'):
        flash('Vous n\'avez pas la permission d\'accéder à cette page', 'error')
        return redirect(url_for('stocks.returns_list'))
    
    from pdf_generator import PDFGenerator
    from flask import make_response
    
    try:
        return_ = StockReturn.query.get_or_404(id)
        
        # Vérifier les permissions d'accès (même logique que return_detail)
        if current_user.role and current_user.role.code == 'commercial':
            if return_.commercial_id != current_user.id:
                flash('Vous n\'avez pas accès à ce retour.', 'error')
                return redirect(url_for('stocks.returns_list'))
        elif current_user.role and current_user.role.code not in ['admin', 'superadmin']:
            from utils_region_filter import can_access_depot, can_access_vehicle
            can_access = False
            if return_.depot_id:
                can_access = can_access_depot(return_.depot_id)
            elif return_.vehicle_id:
                can_access = can_access_vehicle(return_.vehicle_id)
            if not can_access:
                flash('Vous n\'avez pas accès à ce retour.', 'error')
                return redirect(url_for('stocks.returns_list'))
        pdf_gen = PDFGenerator()
        pdf_buffer = pdf_gen.generate_return_pdf(return_)
        
        filename = f'retour_{return_.reference}_{datetime.now(UTC).strftime("%Y%m%d_%H%M%S")}.pdf'
        response = make_response(pdf_buffer.getvalue())
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"❌ Erreur lors de la génération du PDF: {e}")
        flash(f'Erreur lors de la génération du PDF: {str(e)}', 'error')
        return redirect(url_for('stocks.return_detail', id=id))

# =========================================================
# RÉCAPITULATIF STOCK RESTANT
# =========================================================

@stocks_bp.route('/summary/preview')
@login_required
def stock_summary_preview():
    """Prévisualisation avant export PDF/Excel avec quantités restantes"""
    if not has_permission(current_user, 'stocks.read'):
        flash('Vous n\'avez pas la permission d\'accéder à cette page', 'error')
        return redirect(url_for('index'))
    
    from flask import render_template, request
    from datetime import datetime, UTC, timedelta
    from sqlalchemy import func, and_, or_
    
    # Récupérer les paramètres de filtre
    period = request.args.get('period', 'all')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    stock_item_id = request.args.get('stock_item_id', type=int)
    depot_id = request.args.get('depot_id', type=int)
    vehicle_id = request.args.get('vehicle_id', type=int)
    
    # Calculer les dates selon la période (même logique que stock_summary)
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    period_start_date = None
    period_end_date = None
    
    if period == 'today':
        period_start_date = today
        period_end_date = datetime.now(UTC)
    elif period == 'week':
        week_start = today - timedelta(days=today.weekday())
        period_start_date = week_start
        period_end_date = datetime.now(UTC)
    elif period == 'month':
        month_start = today.replace(day=1)
        period_start_date = month_start
        period_end_date = datetime.now(UTC)
    elif period == 'year':
        year_start = today.replace(month=1, day=1)
        period_start_date = year_start
        period_end_date = datetime.now(UTC)
    elif period == 'custom' and start_date and end_date:
        try:
            start = datetime.strptime(start_date, '%Y-%m-%d')
            end = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
            period_start_date = start.replace(tzinfo=UTC) if start.tzinfo is None else start
            period_end_date = end.replace(tzinfo=UTC) if end.tzinfo is None else end
        except:
            pass
    
    # Récupérer les données filtrées par région
    from utils_region_filter import filter_depots_by_region, filter_stock_movements_by_region
    depots_query = Depot.query.filter_by(is_active=True)
    depots_query = filter_depots_by_region(depots_query)
    accessible_depots = depots_query.all()
    
    stock_items = StockItem.query.filter_by(is_active=True).order_by(StockItem.name).all()
    
    # Préparer les données pour la prévisualisation avec quantités restantes
    preview_data = []
    depot_name = 'Tous les dépôts'
    if depot_id:
        depot = next((d for d in accessible_depots if d.id == depot_id), None)
        if depot:
            depot_name = depot.name
    
    # Calculer les quantités restantes pour chaque article (même logique que stock_summary)
    for item in stock_items:
        if stock_item_id and item.id != stock_item_id:
            continue
        
        # Calculer le stock initial (avant la période)
        initial_stock = Decimal('0')
        if period_start_date:
            if depot_id:
                initial_movements_query = StockMovement.query.filter_by(stock_item_id=item.id).filter(
                    or_(
                        StockMovement.to_depot_id == depot_id,
                        StockMovement.from_depot_id == depot_id
                    )
                )
                initial_movements_query = filter_stock_movements_by_region(initial_movements_query)
                period_start_naive = period_start_date.replace(tzinfo=None) if period_start_date.tzinfo else period_start_date
                initial_movements_query = initial_movements_query.filter(StockMovement.movement_date < period_start_naive)
                initial_movements = initial_movements_query.all()
                
                balance = Decimal('0')
                for m in initial_movements:
                    if m.to_depot_id == depot_id:
                        balance += m.quantity
                    elif m.from_depot_id == depot_id:
                        balance -= abs(m.quantity)
                initial_stock = balance
            elif vehicle_id:
                initial_movements_query = StockMovement.query.filter_by(stock_item_id=item.id).filter(
                    or_(
                        StockMovement.to_vehicle_id == vehicle_id,
                        StockMovement.from_vehicle_id == vehicle_id
                    )
                )
                initial_movements_query = filter_stock_movements_by_region(initial_movements_query)
                period_start_naive = period_start_date.replace(tzinfo=None) if period_start_date.tzinfo else period_start_date
                initial_movements_query = initial_movements_query.filter(StockMovement.movement_date < period_start_naive)
                initial_movements = initial_movements_query.all()
                
                balance = Decimal('0')
                for m in initial_movements:
                    if m.to_vehicle_id == vehicle_id:
                        balance += m.quantity
                    elif m.from_vehicle_id == vehicle_id:
                        balance -= abs(m.quantity)
                initial_stock = balance
            else:
                initial_movements_query = StockMovement.query.filter_by(stock_item_id=item.id)
                initial_movements_query = filter_stock_movements_by_region(initial_movements_query)
                period_start_naive = period_start_date.replace(tzinfo=None) if period_start_date.tzinfo else period_start_date
                initial_movements_query = initial_movements_query.filter(StockMovement.movement_date < period_start_naive)
                initial_movements = initial_movements_query.all()
                for m in initial_movements:
                    initial_stock += m.quantity
        
        # Calculer les mouvements dans la période
        movements_query = StockMovement.query.filter_by(stock_item_id=item.id)
        movements_query = filter_stock_movements_by_region(movements_query)
        if period_start_date:
            period_start_naive = period_start_date.replace(tzinfo=None) if period_start_date.tzinfo else period_start_date
            movements_query = movements_query.filter(StockMovement.movement_date >= period_start_naive)
        if period_end_date:
            period_end_naive = period_end_date.replace(tzinfo=None) if period_end_date.tzinfo else period_end_date
            movements_query = movements_query.filter(StockMovement.movement_date <= period_end_naive)
        if depot_id:
            movements_query = movements_query.filter(
                or_(
                    StockMovement.from_depot_id == depot_id,
                    StockMovement.to_depot_id == depot_id
                )
            )
        if vehicle_id:
            movements_query = movements_query.filter(
                or_(
                    StockMovement.from_vehicle_id == vehicle_id,
                    StockMovement.to_vehicle_id == vehicle_id
                )
            )
        
        movements = movements_query.all()
        entries = sum(float(m.quantity) for m in movements if float(m.quantity) > 0)
        exits = sum(abs(float(m.quantity)) for m in movements if float(m.quantity) < 0)
        final_stock_calculated = float(initial_stock) + entries - exits
        
        # Calculer le stock actuel (balance totale)
        if depot_id:
            depot_movements_query = StockMovement.query.filter_by(stock_item_id=item.id).filter(
                or_(
                    StockMovement.to_depot_id == depot_id,
                    StockMovement.from_depot_id == depot_id
                )
            )
            depot_movements_query = filter_stock_movements_by_region(depot_movements_query)
            depot_movements = depot_movements_query.all()
            balance = Decimal('0')
            for m in depot_movements:
                if m.to_depot_id == depot_id:
                    balance += m.quantity
                elif m.from_depot_id == depot_id:
                    balance -= abs(m.quantity)
            current_stock = float(balance)
        elif vehicle_id:
            vehicle_movements_query = StockMovement.query.filter_by(stock_item_id=item.id).filter(
                or_(
                    StockMovement.to_vehicle_id == vehicle_id,
                    StockMovement.from_vehicle_id == vehicle_id
                )
            )
            vehicle_movements_query = filter_stock_movements_by_region(vehicle_movements_query)
            vehicle_movements = vehicle_movements_query.all()
            balance = Decimal('0')
            for m in vehicle_movements:
                if m.to_vehicle_id == vehicle_id:
                    balance += m.quantity
                elif m.from_vehicle_id == vehicle_id:
                    balance -= abs(m.quantity)
            current_stock = float(balance)
        else:
            all_movements_query = StockMovement.query.filter_by(stock_item_id=item.id)
            all_movements_query = filter_stock_movements_by_region(all_movements_query)
            all_movements = all_movements_query.all()
            current_stock = float(sum(m.quantity for m in all_movements))
        
        # N'afficher que les articles avec du stock restant (stock actuel > 0)
        if current_stock > 0:
            preview_data.append({
                'item': item,
                'initial_stock': float(initial_stock),
                'entries': entries,
                'exits': exits,
                'final_stock_calculated': final_stock_calculated,
                'current_stock': current_stock,
                'movements_count': len(movements),
                'depot_name': depot_name
            })
    
    return render_template('stocks/stock_preview.html',
                         preview_data=preview_data,
                         period=period,
                         start_date=start_date,
                         end_date=end_date,
                         stock_item_id=stock_item_id,
                         depot_id=depot_id,
                         vehicle_id=vehicle_id,
                         depots=accessible_depots,
                         stock_items=stock_items,
                         current_time=datetime.now(UTC))

def generate_stock_summary_pdf_data(depot_id=None, period='all', currency='GNF', start_date=None, end_date=None, stock_item_id=None, vehicle_id=None):
    """
    Fonction utilitaire pour générer les données du PDF de récapitulatif de stock
    Peut être utilisée par les rapports automatiques
    """
    from datetime import datetime, UTC, timedelta
    from sqlalchemy import func, and_, or_
    from decimal import Decimal
    
    # Calculer les dates selon la période
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    period_start_date = None
    period_end_date = None
    
    if period == 'today':
        period_start_date = today
        period_end_date = datetime.now(UTC)
    elif period == 'week':
        week_start = today - timedelta(days=today.weekday())
        period_start_date = week_start
        period_end_date = datetime.now(UTC)
    elif period == 'month':
        month_start = today.replace(day=1)
        period_start_date = month_start
        period_end_date = datetime.now(UTC)
    elif period == 'year':
        year_start = today.replace(month=1, day=1)
        period_start_date = year_start
        period_end_date = datetime.now(UTC)
    elif period == 'custom' and start_date and end_date:
        try:
            if isinstance(start_date, str):
                start = datetime.strptime(start_date, '%Y-%m-%d')
            else:
                start = start_date
            if isinstance(end_date, str):
                end = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
            else:
                end = end_date + timedelta(days=1)
            period_start_date = start.replace(tzinfo=UTC) if start.tzinfo is None else start
            period_end_date = end.replace(tzinfo=UTC) if end.tzinfo is None else end
        except:
            pass
    
    # Récupérer les données de stock
    from utils_region_filter import filter_depots_by_region, filter_stock_movements_by_region
    depots_query = Depot.query.filter_by(is_active=True)
    depots_query = filter_depots_by_region(depots_query)
    accessible_depots = depots_query.all()
    
    stock_items = StockItem.query.filter_by(is_active=True).order_by(StockItem.name).all()
    
    # Préparer les données pour le PDF
    depot_name = 'Tous les dépôts'
    if depot_id:
        depot = next((d for d in accessible_depots if d.id == depot_id), None)
        if depot:
            depot_name = depot.name
    
        stock_data = {
        'depot_name': depot_name,
        'period': period,
        'start_date': period_start_date,
        'end_date': period_end_date,
            'items': []
        }
        
    # Calculer les quantités restantes pour chaque article
    for item in stock_items:
        if stock_item_id and item.id != stock_item_id:
            continue
        
        # Calculer le stock initial (avant la période)
        initial_stock = Decimal('0')
        if period_start_date:
            if depot_id:
                initial_movements_query = StockMovement.query.filter_by(stock_item_id=item.id).filter(
                    or_(
                        StockMovement.to_depot_id == depot_id,
                        StockMovement.from_depot_id == depot_id
                    )
                )
                initial_movements_query = filter_stock_movements_by_region(initial_movements_query)
                period_start_naive = period_start_date.replace(tzinfo=None) if period_start_date.tzinfo else period_start_date
                initial_movements_query = initial_movements_query.filter(StockMovement.movement_date < period_start_naive)
                initial_movements = initial_movements_query.all()
                
                balance = Decimal('0')
                for m in initial_movements:
                    if m.to_depot_id == depot_id:
                        balance += m.quantity
                    elif m.from_depot_id == depot_id:
                        balance -= abs(m.quantity)
                initial_stock = balance
            elif vehicle_id:
                initial_movements_query = StockMovement.query.filter_by(stock_item_id=item.id).filter(
                    or_(
                        StockMovement.to_vehicle_id == vehicle_id,
                        StockMovement.from_vehicle_id == vehicle_id
                    )
                )
                initial_movements_query = filter_stock_movements_by_region(initial_movements_query)
                period_start_naive = period_start_date.replace(tzinfo=None) if period_start_date.tzinfo else period_start_date
                initial_movements_query = initial_movements_query.filter(StockMovement.movement_date < period_start_naive)
                initial_movements = initial_movements_query.all()
                
                balance = Decimal('0')
                for m in initial_movements:
                    if m.to_vehicle_id == vehicle_id:
                        balance += m.quantity
                    elif m.from_vehicle_id == vehicle_id:
                        balance -= abs(m.quantity)
                initial_stock = balance
            else:
                initial_movements_query = StockMovement.query.filter_by(stock_item_id=item.id)
                initial_movements_query = filter_stock_movements_by_region(initial_movements_query)
                period_start_naive = period_start_date.replace(tzinfo=None) if period_start_date.tzinfo else period_start_date
                initial_movements_query = initial_movements_query.filter(StockMovement.movement_date < period_start_naive)
                initial_movements = initial_movements_query.all()
                for m in initial_movements:
                    initial_stock += m.quantity
        
        # Calculer les mouvements dans la période
        movements_query = StockMovement.query.filter_by(stock_item_id=item.id)
        movements_query = filter_stock_movements_by_region(movements_query)
        if period_start_date:
            period_start_naive = period_start_date.replace(tzinfo=None) if period_start_date.tzinfo else period_start_date
            movements_query = movements_query.filter(StockMovement.movement_date >= period_start_naive)
        if period_end_date:
            period_end_naive = period_end_date.replace(tzinfo=None) if period_end_date.tzinfo else period_end_date
            movements_query = movements_query.filter(StockMovement.movement_date <= period_end_naive)
        if depot_id:
            movements_query = movements_query.filter(
                or_(
                    StockMovement.from_depot_id == depot_id,
                    StockMovement.to_depot_id == depot_id
                )
            )
        if vehicle_id:
            movements_query = movements_query.filter(
                or_(
                    StockMovement.from_vehicle_id == vehicle_id,
                    StockMovement.to_vehicle_id == vehicle_id
                )
            )
        
        movements = movements_query.all()
        entries = sum(float(m.quantity) for m in movements if float(m.quantity) > 0)
        exits = sum(abs(float(m.quantity)) for m in movements if float(m.quantity) < 0)
        final_stock_calculated = float(initial_stock) + entries - exits
        
        # Calculer le stock actuel (balance totale)
        if depot_id:
            depot_movements_query = StockMovement.query.filter_by(stock_item_id=item.id).filter(
                or_(
                    StockMovement.to_depot_id == depot_id,
                    StockMovement.from_depot_id == depot_id
                )
            )
            depot_movements_query = filter_stock_movements_by_region(depot_movements_query)
            depot_movements = depot_movements_query.all()
            balance = Decimal('0')
            for m in depot_movements:
                if m.to_depot_id == depot_id:
                    balance += m.quantity
                elif m.from_depot_id == depot_id:
                    balance -= abs(m.quantity)
            current_stock = float(balance)
        elif vehicle_id:
            vehicle_movements_query = StockMovement.query.filter_by(stock_item_id=item.id).filter(
                or_(
                    StockMovement.to_vehicle_id == vehicle_id,
                    StockMovement.from_vehicle_id == vehicle_id
                )
            )
            vehicle_movements_query = filter_stock_movements_by_region(vehicle_movements_query)
            vehicle_movements = vehicle_movements_query.all()
            balance = Decimal('0')
            for m in vehicle_movements:
                if m.to_vehicle_id == vehicle_id:
                    balance += m.quantity
                elif m.from_vehicle_id == vehicle_id:
                    balance -= abs(m.quantity)
            current_stock = float(balance)
        else:
            all_movements_query = StockMovement.query.filter_by(stock_item_id=item.id)
            all_movements_query = filter_stock_movements_by_region(all_movements_query)
            all_movements = all_movements_query.all()
            current_stock = float(sum(m.quantity for m in all_movements))
        
        stock_data['items'].append({
            'article_name': item.name,
            'sku': item.sku or '',
            'initial_stock': float(initial_stock),
            'entries': entries,
            'exits': exits,
            'final_stock_calculated': final_stock_calculated,
            'current_stock': current_stock,
            'movements_count': len(movements)
        })
    
    return stock_data

@stocks_bp.route('/summary/pdf')
@login_required
def stock_summary_pdf():
    """Générer un PDF pour le récapitulatif de stock avec quantités restantes"""
    if not has_permission(current_user, 'stocks.read'):
        flash('Vous n\'avez pas la permission d\'accéder à cette page', 'error')
        return redirect(url_for('index'))
    
    from pdf_generator import PDFGenerator
    from flask import send_file, request
    from datetime import datetime, UTC, timedelta
    from sqlalchemy import func, and_, or_
    
    # Récupérer la devise sélectionnée (par défaut GNF)
    currency = request.args.get('currency', 'GNF').upper()
    if currency not in ['GNF', 'USD', 'EUR', 'XOF']:
        currency = 'GNF'
    
    try:
        # Récupérer les paramètres de filtre
        period = request.args.get('period', 'all')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        stock_item_id = request.args.get('stock_item_id', type=int)
        depot_id = request.args.get('depot_id', type=int)
        vehicle_id = request.args.get('vehicle_id', type=int)
        
        # Calculer les dates selon la période (même logique que stock_summary)
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        period_start_date = None
        period_end_date = None
        
        if period == 'today':
            period_start_date = today
            period_end_date = datetime.now(UTC)
        elif period == 'week':
            week_start = today - timedelta(days=today.weekday())
            period_start_date = week_start
            period_end_date = datetime.now(UTC)
        elif period == 'month':
            month_start = today.replace(day=1)
            period_start_date = month_start
            period_end_date = datetime.now(UTC)
        elif period == 'year':
            year_start = today.replace(month=1, day=1)
            period_start_date = year_start
            period_end_date = datetime.now(UTC)
        elif period == 'custom' and start_date and end_date:
            try:
                start = datetime.strptime(start_date, '%Y-%m-%d')
                end = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
                period_start_date = start.replace(tzinfo=UTC) if start.tzinfo is None else start
                period_end_date = end.replace(tzinfo=UTC) if end.tzinfo is None else end
            except:
                pass
        
        # Utiliser la fonction utilitaire pour générer les données
        stock_data = generate_stock_summary_pdf_data(
            depot_id=depot_id,
            period=period,
            currency=currency,
            start_date=start_date,
            end_date=end_date,
            stock_item_id=stock_item_id,
            vehicle_id=vehicle_id
        )
        
        # Déterminer le taux de change
        exchange_rate = None
        if currency == 'USD':
            exchange_rate = 8500.0
        elif currency == 'EUR':
            exchange_rate = 9200.0
        elif currency == 'XOF':
            exchange_rate = 14.0
        
        # Générer le PDF avec la devise sélectionnée
        pdf_gen = PDFGenerator()
        pdf_buffer = pdf_gen.generate_stock_summary_pdf(stock_data, currency=currency, exchange_rate=exchange_rate)
        
        # Retourner le PDF
        filename = f'stock_summary_{datetime.now(UTC).strftime("%Y%m%d_%H%M%S")}.pdf'
        
        from flask import make_response
        response = make_response(pdf_buffer.getvalue())
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"❌ Erreur lors de la génération du PDF: {e}")
        flash(f'Erreur lors de la génération du PDF: {str(e)}', 'error')
        return redirect(url_for('stocks.stock_summary'))

@stocks_bp.route('/summary/excel')
@login_required
def stock_summary_excel():
    """Générer un Excel pour le récapitulatif de stock"""
    if not has_permission(current_user, 'stocks.read'):
        flash('Vous n\'avez pas la permission d\'accéder à cette page', 'error')
        return redirect(url_for('index'))
    
    from flask import send_file, request
    from datetime import datetime, UTC
    import pandas as pd
    from io import BytesIO
    
    # Récupérer la devise sélectionnée (par défaut GNF)
    currency = request.args.get('currency', 'GNF').upper()
    if currency not in ['GNF', 'USD', 'EUR', 'XOF']:
        currency = 'GNF'
    
    # Déterminer le taux de change pour la conversion
    exchange_rate = None
    if currency == 'USD':
        exchange_rate = 8500.0  # Taux par défaut, peut être récupéré depuis config
    elif currency == 'EUR':
        exchange_rate = 9200.0
    elif currency == 'XOF':
        exchange_rate = 14.0  # Taux approximatif XOF/GNF
    
    def convert_amount(amount_gnf, rate):
        """Convertit un montant GNF vers la devise cible"""
        if currency == 'GNF' or not rate or rate == 0:
            return amount_gnf
        return amount_gnf / rate
    
    try:
        # Récupérer les paramètres de filtre
        period = request.args.get('period', 'all')
        stock_item_id = request.args.get('stock_item_id', type=int)
        depot_id = request.args.get('depot_id', type=int)
        
        # Récupérer les données
        stock_items = StockItem.query.filter_by(is_active=True).order_by(StockItem.name).all()
        depots = Depot.query.filter_by(is_active=True).order_by(Depot.name).all()
        
        # Optimisation : Charger tous les stocks en une seule requête pour éviter N+1
        stock_item_ids = [item.id for item in stock_items]
        if stock_item_id:
            stock_item_ids = [stock_item_id]
        
        # Charger tous les stocks de dépôt en une requête
        if depot_id:
            all_depot_stocks = DepotStock.query.filter(
                DepotStock.stock_item_id.in_(stock_item_ids),
                DepotStock.depot_id == depot_id
            ).all()
        else:
            all_depot_stocks = DepotStock.query.filter(
                DepotStock.stock_item_id.in_(stock_item_ids)
            ).all()
        
        # Charger tous les stocks de véhicule en une requête
        all_vehicle_stocks = VehicleStock.query.filter(
            VehicleStock.stock_item_id.in_(stock_item_ids)
        ).all() if not depot_id else []
        
        # Grouper par stock_item_id en mémoire
        depot_stocks_by_item = {}
        for ds in all_depot_stocks:
            if ds.stock_item_id not in depot_stocks_by_item:
                depot_stocks_by_item[ds.stock_item_id] = []
            depot_stocks_by_item[ds.stock_item_id].append(ds)
        
        vehicle_stocks_by_item = {}
        for vs in all_vehicle_stocks:
            if vs.stock_item_id not in vehicle_stocks_by_item:
                vehicle_stocks_by_item[vs.stock_item_id] = []
            vehicle_stocks_by_item[vs.stock_item_id].append(vs)
        
        # Préparer les données pour Excel
        data = []
        depot_name = 'Tous les dépôts'
        if depot_id:
            depot = Depot.query.get(depot_id)
            if depot:
                depot_name = depot.name
        
        for item in stock_items:
            if stock_item_id and item.id != stock_item_id:
                continue
            
            # Calculer le stock total depuis les données groupées
            total_stock = Decimal('0')
            depot_stock = Decimal('0')
            
            if depot_id:
                depot_stocks = depot_stocks_by_item.get(item.id, [])
                depot_stock = sum(Decimal(str(ds.quantity)) for ds in depot_stocks)
                total_stock = depot_stock
            else:
                depot_stocks = depot_stocks_by_item.get(item.id, [])
                depot_stock = sum(Decimal(str(ds.quantity)) for ds in depot_stocks)
                vehicle_stocks = vehicle_stocks_by_item.get(item.id, [])
                vehicle_stock = sum(Decimal(str(vs.quantity)) for vs in vehicle_stocks)
                total_stock = depot_stock + vehicle_stock
            
            if total_stock > 0:
                value_gnf = float(total_stock) * float(item.purchase_price_gnf or 0)
                
                # Utiliser la fonction convert_amount définie au début
                unit_price = convert_amount(float(item.purchase_price_gnf or 0), exchange_rate)
                value = convert_amount(value_gnf, exchange_rate)
                
                data.append({
                    'Article': item.name,
                    'Dépôt': depot_name,
                    'Quantité': float(total_stock),
                    f'Prix Unitaire ({currency})': unit_price,
                    f'Valeur ({currency})': value
                })
        
        # Créer le DataFrame
        df = pd.DataFrame(data)
        
        # Ajouter une ligne de total
        if len(df) > 0:
            total_row = pd.DataFrame([{
                'Article': 'TOTAL',
                'Dépôt': '',
                'Quantité': df['Quantité'].sum(),
                f'Prix Unitaire ({currency})': '',
                f'Valeur ({currency})': df[f'Valeur ({currency})'].sum()
            }])
            df = pd.concat([df, total_row], ignore_index=True)
        
        # Créer le fichier Excel
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Stock', index=False)
        
        output.seek(0)
        filename = f'stock_summary_{datetime.now(UTC).strftime("%Y%m%d_%H%M%S")}.xlsx'
        
        from flask import make_response
        response = make_response(output.getvalue())
        response.headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"❌ Erreur lors de la génération Excel: {e}")
        flash(f'Erreur lors de la génération Excel: {str(e)}', 'error')
        return redirect(url_for('stocks.stock_summary'))

@stocks_bp.route('/summary/api')
@login_required
def stock_summary_api():
    """API JSON pour le récapitulatif du stock (pour mise à jour en temps réel)"""
    if not has_permission(current_user, 'stocks.read'):
        return jsonify({'error': 'Permission refusée'}), 403
    
    from datetime import datetime, UTC, timedelta
    from sqlalchemy import func, and_, or_
    
    # Récupérer les paramètres de filtre
    period = request.args.get('period', 'all')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    depot_id = request.args.get('depot_id', type=int)
    vehicle_id = request.args.get('vehicle_id', type=int)
    stock_item_id = request.args.get('stock_item_id', type=int)
    
    # Calculer les dates selon la période (même logique que stock_summary)
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    date_filter = None
    
    if period == 'today':
        date_filter = and_(StockMovement.movement_date >= today)
    elif period == 'week':
        week_start = today - timedelta(days=today.weekday())
        date_filter = and_(StockMovement.movement_date >= week_start)
    elif period == 'month':
        month_start = today.replace(day=1)
        date_filter = and_(StockMovement.movement_date >= month_start)
    elif period == 'year':
        year_start = today.replace(month=1, day=1)
        date_filter = and_(StockMovement.movement_date >= year_start)
    elif period == 'custom' and start_date and end_date:
        try:
            start = datetime.strptime(start_date, '%Y-%m-%d')
            end = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
            date_filter = and_(StockMovement.movement_date >= start, StockMovement.movement_date < end)
        except:
            pass
    
    # Récupérer tous les articles de stock actifs
    stock_items = StockItem.query.filter_by(is_active=True).order_by(StockItem.name).all()
    
    # Calculer le stock restant pour chaque article (même logique que stock_summary)
    stock_summary = []
    for item in stock_items:
        if stock_item_id and item.id != stock_item_id:
            continue
        
        # Calculer la balance du stock à partir des mouvements (filtrés par région)
        from utils_region_filter import filter_stock_movements_by_region
        movements_query = StockMovement.query.filter_by(stock_item_id=item.id)
        movements_query = filter_stock_movements_by_region(movements_query)
        if date_filter is not None:
            movements_query = movements_query.filter(date_filter)
        movements = movements_query.all()
        
        # Balance par dépôt
        depot_balances = {}
        vehicle_balances = {}
        total_stock = Decimal('0')
        total_depot_stock = Decimal('0')
        total_vehicle_stock = Decimal('0')
        entries = Decimal('0')
        exits = Decimal('0')
        
        for movement in movements:
            qty = Decimal(str(movement.quantity))
            
            # Entrées : réceptions et mouvements positifs
            if movement.movement_type == 'reception':
                entries += abs(qty)
            elif movement.movement_type in ['transfer', 'adjustment', 'inventory']:
                if qty < 0:
                    exits += abs(qty)  # Sorties : transferts sortants, ajustements négatifs
                else:
                    entries += qty  # Entrées : transferts entrants, ajustements positifs
            elif movement.movement_type == 'reception_return':
                # Retours fournisseurs : sorties (quantité négative)
                exits += abs(qty)
            
            # Calculer par dépôt
            if movement.to_depot_id:
                depot_id_key = movement.to_depot_id
                if depot_id_key not in depot_balances:
                    depot_balances[depot_id_key] = Decimal('0')
                depot_balances[depot_id_key] += qty
                total_depot_stock += qty if qty > 0 else 0
            
            if movement.from_depot_id:
                depot_id_key = movement.from_depot_id
                if depot_id_key not in depot_balances:
                    depot_balances[depot_id_key] = Decimal('0')
                depot_balances[depot_id_key] -= abs(qty)
            
            # Calculer par véhicule
            if movement.to_vehicle_id:
                vehicle_id_key = movement.to_vehicle_id
                if vehicle_id_key not in vehicle_balances:
                    vehicle_balances[vehicle_id_key] = Decimal('0')
                vehicle_balances[vehicle_id_key] += qty
                total_vehicle_stock += qty if qty > 0 else 0
            
            if movement.from_vehicle_id:
                vehicle_id_key = movement.from_vehicle_id
                if vehicle_id_key not in vehicle_balances:
                    vehicle_balances[vehicle_id_key] = Decimal('0')
                vehicle_balances[vehicle_id_key] -= abs(qty)
            
            total_stock += qty
        
        # NOTE: Ne pas ajouter les stocks depuis DepotStock et VehicleStock ici
        # car ils sont déjà calculés depuis les mouvements ci-dessus
        # Cela éviterait le double comptage
        # Les stocks DepotStock/VehicleStock sont des caches et doivent être cohérents avec les mouvements
        
        stock_summary.append({
            'item_id': item.id,
            'item_name': item.name,
            'item_sku': item.sku,
            'total_stock': float(total_stock),
            'depot_stock': float(total_depot_stock),
            'vehicle_stock': float(total_vehicle_stock),
            'entries': float(entries),
            'exits': float(exits),
            'value': float(float(total_stock) * float(item.purchase_price_gnf) if total_stock > 0 else 0),
            'depot_balances': {str(k): float(v) for k, v in depot_balances.items()},
            'vehicle_balances': {str(k): float(v) for k, v in vehicle_balances.items()}
        })
    
    # Calculer les totaux
    total_items = len(stock_summary)
    total_quantity = sum(s['total_stock'] for s in stock_summary)
    total_value = sum(s['value'] for s in stock_summary)
    
    # Calculer les statistiques par dépôt (similaire à stock_summary)
    from utils_region_filter import filter_depots_by_region
    depots_query = Depot.query.filter_by(is_active=True)
    depots_query = filter_depots_by_region(depots_query)
    depots = depots_query.order_by(Depot.name).all()
    
    depot_stats = []
    total_receptions_all = Decimal('0')
    total_entries_all = Decimal('0')
    total_exits_all = Decimal('0')
    total_transfers_all = Decimal('0')
    
    for depot in depots:
        if depot_id and depot.id != depot_id:
            continue
            
        # Filtrer les mouvements pour ce dépôt (filtrés par région)
        from utils_region_filter import filter_stock_movements_by_region
        depot_movements_query = StockMovement.query.filter(
            or_(
                StockMovement.to_depot_id == depot.id,
                StockMovement.from_depot_id == depot.id
            )
        )
        depot_movements_query = filter_stock_movements_by_region(depot_movements_query)
        
        # Appliquer le filtre de date si spécifié
        if date_filter is not None:
            depot_movements_query = depot_movements_query.filter(date_filter)
        
        depot_movements = depot_movements_query.all()
        
        # Calculer les statistiques
        total_receptions = Decimal('0')
        total_exits = Decimal('0')
        total_transfers_in = Decimal('0')
        total_transfers_out = Decimal('0')
        total_stock_depot = Decimal('0')
        
        for movement in depot_movements:
            qty = Decimal(str(movement.quantity))
            
            if movement.movement_type == 'reception' and movement.to_depot_id == depot.id:
                total_receptions += abs(qty)
                total_stock_depot += abs(qty)
            elif movement.movement_type == 'transfer':
                if movement.to_depot_id == depot.id:
                    total_transfers_in += abs(qty)
                    total_stock_depot += abs(qty)
                elif movement.from_depot_id == depot.id:
                    total_transfers_out += abs(qty)
                    total_stock_depot -= abs(qty)
            elif qty < 0 and movement.from_depot_id == depot.id:
                total_exits += abs(qty)
                total_stock_depot -= abs(qty)
        
        # Ajouter les stocks depuis DepotStock (filtrés par région)
        from utils_region_filter import filter_depot_stocks_by_region
        depot_stocks_query = DepotStock.query.filter_by(depot_id=depot.id)
        depot_stocks_query = filter_depot_stocks_by_region(depot_stocks_query)
        depot_stocks = depot_stocks_query.all()
        for ds in depot_stocks:
            total_stock_depot += Decimal(str(ds.quantity))
        
        depot_stats.append({
            'depot_id': depot.id,
            'depot_name': depot.name,
            'total_receptions': float(total_receptions),
            'total_exits': float(total_exits),
            'total_transfers': float(total_transfers_in - total_transfers_out),
            'total_stock': float(total_stock_depot),
            'movements_count': len(depot_movements)
        })
        
        total_receptions_all += total_receptions
        total_exits_all += total_exits
        total_transfers_all += (total_transfers_in - total_transfers_out)
    
    total_stock_all_depots = sum(s['total_stock'] for s in depot_stats)
    
    # Récupérer les dernières opérations pour l'API aussi
    # Charger toutes les relations nécessaires pour éviter N+1
    # Appliquer les filtres régionaux AVANT limit() et joinedload()
    from utils_region_filter import filter_stock_movements_by_region
    recent_movements_query_api = StockMovement.query
    recent_movements_query_api = filter_stock_movements_by_region(recent_movements_query_api)
    
    # Ensuite appliquer les options et le limit
    recent_movements_query_api = recent_movements_query_api.options(
        joinedload(StockMovement.stock_item),
        joinedload(StockMovement.from_depot),
        joinedload(StockMovement.to_depot),
        joinedload(StockMovement.from_vehicle),
        joinedload(StockMovement.to_vehicle),
        joinedload(StockMovement.user)
    ).order_by(StockMovement.created_at.desc()).limit(20)
    
    # Appliquer les filtres si spécifiés
    if depot_id:
        recent_movements_query_api = recent_movements_query_api.filter(
            or_(
                StockMovement.from_depot_id == depot_id,
                StockMovement.to_depot_id == depot_id
            )
        )
    if vehicle_id:
        recent_movements_query_api = recent_movements_query_api.filter(
            or_(
                StockMovement.from_vehicle_id == vehicle_id,
                StockMovement.to_vehicle_id == vehicle_id
            )
        )
    if stock_item_id:
        recent_movements_query_api = recent_movements_query_api.filter_by(stock_item_id=stock_item_id)
    
    recent_movements_api = recent_movements_query_api.all()
    
    # Préparer les données JSON pour les dernières opérations
    recent_movements_json = []
    for m in recent_movements_api:
        recent_movements_json.append({
            'id': m.id,
            'reference': m.reference,
            'movement_type': m.movement_type,
            'movement_date': m.movement_date.isoformat() if m.movement_date else None,
            'created_at': m.created_at.isoformat() if m.created_at else None,
            'stock_item_id': m.stock_item_id,
            'stock_item_name': m.stock_item.name if m.stock_item else None,
            'stock_item_sku': m.stock_item.sku if m.stock_item and m.stock_item.sku else None,
            'quantity': float(m.quantity),
            'from_depot_id': m.from_depot_id,
            'from_depot_name': m.from_depot.name if m.from_depot else None,
            'from_vehicle_id': m.from_vehicle_id,
            'from_vehicle_plate': m.from_vehicle.plate_number if m.from_vehicle else None,
            'to_depot_id': m.to_depot_id,
            'to_depot_name': m.to_depot.name if m.to_depot else None,
            'to_vehicle_id': m.to_vehicle_id,
            'to_vehicle_plate': m.to_vehicle.plate_number if m.to_vehicle else None,
            'supplier_name': m.supplier_name,
            'user_id': m.user_id,
            'user_username': m.user.username if m.user else None,
            'reason': m.reason
        })
    
    return jsonify({
        'stock_summary': stock_summary,
        'depot_stats': depot_stats,
        'total_items': total_items,
        'total_quantity': float(total_quantity),
        'total_value': float(total_value),
        'total_receptions_all': float(total_receptions_all),
        'total_exits_all': float(total_exits_all),
        'total_transfers_all': float(total_transfers_all),
        'total_stock_all_depots': float(total_stock_all_depots),
        'recent_movements': recent_movements_json,
        'last_update': datetime.now(UTC).isoformat()
    })

@stocks_bp.route('/summary')
@login_required
def stock_summary():
    """Récapitulatif du stock restant avec filtres par période"""
    if not has_permission(current_user, 'stocks.read'):
        flash('Vous n\'avez pas la permission d\'accéder à cette page', 'error')
        return redirect(url_for('index'))
    
    from datetime import datetime, UTC, timedelta
    from sqlalchemy import func, and_, or_
    
    # Récupérer les paramètres de filtre
    period = request.args.get('period', 'all')  # all, today, week, month, year, custom
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    depot_id = request.args.get('depot_id', type=int)
    vehicle_id = request.args.get('vehicle_id', type=int)
    stock_item_id = request.args.get('stock_item_id', type=int)
    
    # Calculer les dates selon la période
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    date_filter = None
    period_start_date = None
    period_end_date = None
    
    if period == 'today':
        period_start_date = today
        period_end_date = datetime.now(UTC)
        date_filter = and_(StockMovement.movement_date >= today)
    elif period == 'week':
        week_start = today - timedelta(days=today.weekday())
        period_start_date = week_start
        period_end_date = datetime.now(UTC)
        date_filter = and_(StockMovement.movement_date >= week_start)
    elif period == 'month':
        month_start = today.replace(day=1)
        period_start_date = month_start
        period_end_date = datetime.now(UTC)
        date_filter = and_(StockMovement.movement_date >= month_start)
    elif period == 'year':
        year_start = today.replace(month=1, day=1)
        period_start_date = year_start
        period_end_date = datetime.now(UTC)
        date_filter = and_(StockMovement.movement_date >= year_start)
    elif period == 'custom' and start_date and end_date:
        try:
            start = datetime.strptime(start_date, '%Y-%m-%d')
            end = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
            period_start_date = start.replace(tzinfo=UTC) if start.tzinfo is None else start
            period_end_date = end.replace(tzinfo=UTC) if end.tzinfo is None else end
            date_filter = and_(StockMovement.movement_date >= start, StockMovement.movement_date < end)
        except:
            pass
    
    # Récupérer les dépôts et véhicules filtrés par région (pour les calculs)
    from utils_region_filter import filter_depots_by_region, filter_vehicles_by_region, filter_stock_movements_by_region
    depots_query = Depot.query.filter_by(is_active=True)
    depots_query = filter_depots_by_region(depots_query)
    accessible_depots = depots_query.all()
    accessible_depot_ids = [d.id for d in accessible_depots]
    
    vehicles_query = Vehicle.query.filter_by(status='active')
    vehicles_query = filter_vehicles_by_region(vehicles_query)
    accessible_vehicles = vehicles_query.all()
    accessible_vehicle_ids = [v.id for v in accessible_vehicles]
    
    # Récupérer tous les articles de stock actifs
    stock_items = StockItem.query.filter_by(is_active=True).order_by(StockItem.name).all()
    
    # Calculer le stock restant pour chaque article
    stock_summary = []
    for item in stock_items:
        # Filtrer par article si spécifié
        if stock_item_id and item.id != stock_item_id:
            continue
        
        # Calculer la balance du stock à partir des mouvements (méthode recommandée)
        # Balance = somme de tous les mouvements (entrées positives + sorties négatives)
        
        # Balance par dépôt
        depot_balances = {}
        if depot_id:
            # Vérifier que l'utilisateur a accès à ce dépôt
            if depot_id not in accessible_depot_ids:
                continue  # Skip cet article si le dépôt n'est pas accessible
            
            # Balance pour un dépôt spécifique
            depot_movements_query = StockMovement.query.filter_by(stock_item_id=item.id).filter(
                or_(
                    StockMovement.to_depot_id == depot_id,
                    StockMovement.from_depot_id == depot_id
                )
            )
            depot_movements_query = filter_stock_movements_by_region(depot_movements_query)
            depot_movements = depot_movements_query.all()
            
            # Calculer la balance : entrées (to_depot) - sorties (from_depot)
            balance = Decimal('0')
            for m in depot_movements:
                if m.to_depot_id == depot_id:
                    balance += m.quantity  # Entrée (positif)
                elif m.from_depot_id == depot_id:
                    # Sortie : forcer négatif pour garantir la cohérence
                    balance -= abs(m.quantity)  # Sortie (soustraire la valeur absolue)
            
            depot_balances[depot_id] = float(balance)
            total_depot_stock = float(balance)
        else:
            # Balance pour tous les dépôts accessibles
            for depot in accessible_depots:
                depot_movements_query = StockMovement.query.filter_by(stock_item_id=item.id).filter(
                    or_(
                        StockMovement.to_depot_id == depot.id,
                        StockMovement.from_depot_id == depot.id
                    )
                )
                depot_movements_query = filter_stock_movements_by_region(depot_movements_query)
                depot_movements = depot_movements_query.all()
                
                balance = Decimal('0')
                for m in depot_movements:
                    if m.to_depot_id == depot.id:
                        balance += m.quantity  # Entrée
                    elif m.from_depot_id == depot.id:
                        # Sortie : forcer négatif pour garantir la cohérence
                        balance -= abs(m.quantity)  # Sortie (soustraire la valeur absolue)
                
                depot_balances[depot.id] = float(balance)
            
            total_depot_stock = sum(depot_balances.values())
        
        # Balance par véhicule
        vehicle_balances = {}
        if vehicle_id:
            # Vérifier que l'utilisateur a accès à ce véhicule
            if vehicle_id not in accessible_vehicle_ids:
                continue  # Skip cet article si le véhicule n'est pas accessible
            
            vehicle_movements_query = StockMovement.query.filter_by(stock_item_id=item.id).filter(
                or_(
                    StockMovement.to_vehicle_id == vehicle_id,
                    StockMovement.from_vehicle_id == vehicle_id
                )
            )
            vehicle_movements_query = filter_stock_movements_by_region(vehicle_movements_query)
            vehicle_movements = vehicle_movements_query.all()
            
            balance = Decimal('0')
            for m in vehicle_movements:
                if m.to_vehicle_id == vehicle_id:
                    balance += m.quantity  # Entrée
                elif m.from_vehicle_id == vehicle_id:
                    # Sortie : forcer négatif pour garantir la cohérence
                    balance -= abs(m.quantity)  # Sortie (soustraire la valeur absolue)
            
            vehicle_balances[vehicle_id] = float(balance)
            total_vehicle_stock = float(balance)
        else:
            # Balance pour tous les véhicules accessibles
            for vehicle in accessible_vehicles:
                vehicle_movements_query = StockMovement.query.filter_by(stock_item_id=item.id).filter(
                    or_(
                        StockMovement.to_vehicle_id == vehicle.id,
                        StockMovement.from_vehicle_id == vehicle.id
                    )
                )
                vehicle_movements_query = filter_stock_movements_by_region(vehicle_movements_query)
                vehicle_movements = vehicle_movements_query.all()
                
                balance = Decimal('0')
                for m in vehicle_movements:
                    if m.to_vehicle_id == vehicle.id:
                        balance += m.quantity  # Entrée
                    elif m.from_vehicle_id == vehicle.id:
                        # Sortie : forcer négatif pour garantir la cohérence
                        balance -= abs(m.quantity)  # Sortie (soustraire la valeur absolue)
                
                vehicle_balances[vehicle.id] = float(balance)
            
            total_vehicle_stock = sum(vehicle_balances.values())
        
        # Stock total (balance globale)
        total_stock = total_depot_stock + total_vehicle_stock
        
        # Mouvements dans la période (filtrés par région)
        movements_query = StockMovement.query.filter_by(stock_item_id=item.id)
        movements_query = filter_stock_movements_by_region(movements_query)
        if date_filter is not None:
            movements_query = movements_query.filter(date_filter)
        if depot_id:
            movements_query = movements_query.filter(
                or_(
                    StockMovement.from_depot_id == depot_id,
                    StockMovement.to_depot_id == depot_id
                )
            )
        if vehicle_id:
            movements_query = movements_query.filter(
                or_(
                    StockMovement.from_vehicle_id == vehicle_id,
                    StockMovement.to_vehicle_id == vehicle_id
                )
            )
        
        movements = movements_query.order_by(StockMovement.movement_date.desc()).all()
        
        # Calculer les entrées et sorties dans la période
        # Entrées = quantités positives
        entries = sum(float(m.quantity) for m in movements if float(m.quantity) > 0)
        # Sorties = quantités négatives (on prend la valeur absolue pour l'affichage)
        exits = sum(abs(float(m.quantity)) for m in movements if float(m.quantity) < 0)
        
        # Calculer le stock initial (avant la période sélectionnée)
        initial_stock = Decimal('0')
        if period_start_date:
            # Stock initial = balance calculée jusqu'à period_start_date
            # Utiliser la même logique que pour le stock total mais limitée aux mouvements avant la période
            if depot_id:
                # Balance initiale pour un dépôt spécifique
                initial_depot_movements_query = StockMovement.query.filter_by(stock_item_id=item.id).filter(
                    or_(
                        StockMovement.to_depot_id == depot_id,
                        StockMovement.from_depot_id == depot_id
                    )
                )
                initial_depot_movements_query = filter_stock_movements_by_region(initial_depot_movements_query)
                period_start_naive = period_start_date.replace(tzinfo=None) if period_start_date.tzinfo else period_start_date
                initial_depot_movements_query = initial_depot_movements_query.filter(StockMovement.movement_date < period_start_naive)
                initial_depot_movements = initial_depot_movements_query.all()
                
                balance = Decimal('0')
                for m in initial_depot_movements:
                    if m.to_depot_id == depot_id:
                        balance += m.quantity  # Entrée
                    elif m.from_depot_id == depot_id:
                        balance -= abs(m.quantity)  # Sortie
                initial_stock = balance
            elif vehicle_id:
                # Balance initiale pour un véhicule spécifique
                initial_vehicle_movements_query = StockMovement.query.filter_by(stock_item_id=item.id).filter(
                    or_(
                        StockMovement.to_vehicle_id == vehicle_id,
                        StockMovement.from_vehicle_id == vehicle_id
                    )
                )
                initial_vehicle_movements_query = filter_stock_movements_by_region(initial_vehicle_movements_query)
                period_start_naive = period_start_date.replace(tzinfo=None) if period_start_date.tzinfo else period_start_date
                initial_vehicle_movements_query = initial_vehicle_movements_query.filter(StockMovement.movement_date < period_start_naive)
                initial_vehicle_movements = initial_vehicle_movements_query.all()
                
                balance = Decimal('0')
                for m in initial_vehicle_movements:
                    if m.to_vehicle_id == vehicle_id:
                        balance += m.quantity  # Entrée
                    elif m.from_vehicle_id == vehicle_id:
                        balance -= abs(m.quantity)  # Sortie
                initial_stock = balance
            else:
                # Balance initiale pour tous les dépôts et véhicules accessibles
                initial_all_movements_query = StockMovement.query.filter_by(stock_item_id=item.id)
                initial_all_movements_query = filter_stock_movements_by_region(initial_all_movements_query)
                period_start_naive = period_start_date.replace(tzinfo=None) if period_start_date.tzinfo else period_start_date
                initial_all_movements_query = initial_all_movements_query.filter(StockMovement.movement_date < period_start_naive)
                initial_all_movements = initial_all_movements_query.all()
                
                # Calculer la balance globale initiale
                for m in initial_all_movements:
                    initial_stock += m.quantity
        else:
            # Si pas de période, le stock initial est 0
            initial_stock = Decimal('0')
        
        # Stock final calculé = stock initial + entrées - sorties
        final_stock_calculated = float(initial_stock) + entries - exits
        
        # N'afficher que les articles avec du stock restant (stock actuel > 0)
        if total_stock > 0:
            stock_summary.append({
                'item': item,
                'total_stock': total_stock,
                'depot_stock': total_depot_stock,
                'vehicle_stock': total_vehicle_stock,
                'depot_balances': depot_balances,  # Balance par dépôt
                'vehicle_balances': vehicle_balances,  # Balance par véhicule
                'entries': entries,
                'exits': exits,
                'movements_count': len(movements),
                'value': (total_stock * float(item.purchase_price_gnf) if total_stock > 0 and item.purchase_price_gnf else 0),
                'initial_stock': float(initial_stock),
                'final_stock_calculated': final_stock_calculated
            })
    
    # Utiliser les dépôts et véhicules déjà filtrés par région pour les filtres
    depots = sorted(accessible_depots, key=lambda d: d.name)
    vehicles = sorted(accessible_vehicles, key=lambda v: v.plate_number)
    
    # Calculer les totaux
    total_items = len(stock_summary)
    total_quantity = sum(s['total_stock'] for s in stock_summary)
    
    # Vérifier si l'utilisateur peut voir les valeurs de stock
    from auth import can_view_stock_values
    can_view_values = can_view_stock_values(current_user)
    
    # Calculer total_value seulement si l'utilisateur peut voir les valeurs
    total_value = Decimal('0')
    if can_view_values:
        total_value = sum(s['value'] for s in stock_summary)
    
    # Calculer les statistiques par dépôt (entrées, sorties, transferts)
    depot_stats = []
    for depot in depots:
        # Filtrer les mouvements pour ce dépôt (avec filtrage par région)
        depot_movements_query = StockMovement.query.filter(
            or_(
                StockMovement.to_depot_id == depot.id,
                StockMovement.from_depot_id == depot.id
            )
        )
        depot_movements_query = filter_stock_movements_by_region(depot_movements_query)
        
        # Appliquer le filtre de date si spécifié
        if date_filter is not None:
            depot_movements_query = depot_movements_query.filter(date_filter)
        
        depot_movements = depot_movements_query.all()
        
        # Calculer les statistiques
        total_receptions = Decimal('0')  # Réceptions (entrées externes)
        total_exits = Decimal('0')    # Sorties (quantités négatives depuis ce dépôt)
        total_transfers_in = Decimal('0')  # Transferts entrants (depuis un autre dépôt)
        total_transfers_out = Decimal('0')  # Transferts sortants (vers un autre dépôt)
        total_stock_depot = Decimal('0')  # Stock total du dépôt
        
        for movement in depot_movements:
            qty = movement.quantity
            
            # Si c'est une entrée dans ce dépôt
            if movement.to_depot_id == depot.id:
                if qty > 0:
                    # Distinguer les réceptions des transferts
                    if movement.movement_type == 'reception':
                        # Réception = entrée externe (pas de from_depot_id)
                        total_receptions += qty
                    elif movement.movement_type == 'transfer' and movement.from_depot_id is not None:
                        # Transfert depuis un autre dépôt
                        total_transfers_in += qty
                    else:
                        # Autres types d'entrées (ajustements positifs, retours, etc.)
                        total_receptions += qty
                total_stock_depot += qty
            
            # Si c'est une sortie de ce dépôt
            elif movement.from_depot_id == depot.id:
                if qty < 0:
                    # Sorties : ventes, transferts sortants, ajustements négatifs, retours fournisseurs
                    total_exits += abs(qty)
                    # Si c'est un transfert vers un autre dépôt
                    if movement.movement_type == 'transfer' and movement.to_depot_id is not None:
                        total_transfers_out += abs(qty)
                    # Si c'est un retour fournisseur
                    elif movement.movement_type == 'reception_return':
                        # Retour fournisseur = sortie (déjà compté dans total_exits)
                        pass
                total_stock_depot += qty
        
        # Total des entrées = réceptions + transferts entrants
        total_entries = total_receptions + total_transfers_in
        
        # Calculer le stock total du dépôt (tous les articles, toutes périodes) avec filtrage par région
        all_depot_movements_query = StockMovement.query.filter(
            or_(
                StockMovement.to_depot_id == depot.id,
                StockMovement.from_depot_id == depot.id
            )
        )
        all_depot_movements_query = filter_stock_movements_by_region(all_depot_movements_query)
        all_depot_movements = all_depot_movements_query.all()
        
        depot_total_stock = Decimal('0')
        for m in all_depot_movements:
            if m.to_depot_id == depot.id:
                depot_total_stock += m.quantity
            elif m.from_depot_id == depot.id:
                depot_total_stock += m.quantity
        
        depot_stats.append({
            'depot': depot,
            'total_receptions': float(total_receptions),
            'total_entries': float(total_entries),
            'total_exits': float(total_exits),
            'total_transfers_in': float(total_transfers_in),
            'total_transfers_out': float(total_transfers_out),
            'total_transfers': float(total_transfers_in + total_transfers_out),
            'total_stock': float(depot_total_stock),
            'movements_count': len(depot_movements)
        })
    
    # Calculer les totaux globaux par dépôt
    total_receptions_all = sum(s['total_receptions'] for s in depot_stats)
    total_entries_all = sum(s['total_entries'] for s in depot_stats)
    total_exits_all = sum(s['total_exits'] for s in depot_stats)
    total_transfers_all = sum(s['total_transfers'] for s in depot_stats)
    total_stock_all_depots = sum(s['total_stock'] for s in depot_stats)
    
    # Récupérer les dernières opérations de stock (20 dernières)
    # Charger toutes les relations nécessaires avec joinedload pour éviter N+1
    recent_movements_query = StockMovement.query.options(
        joinedload(StockMovement.stock_item),
        joinedload(StockMovement.from_depot),
        joinedload(StockMovement.to_depot),
        joinedload(StockMovement.from_vehicle),
        joinedload(StockMovement.to_vehicle),
        joinedload(StockMovement.user)
    ).order_by(StockMovement.created_at.desc())
    
    # Appliquer les filtres régionaux si nécessaire
    recent_movements_query = filter_stock_movements_by_region(recent_movements_query)
    
    # Appliquer les filtres de dépôt/véhicule si spécifiés
    if depot_id:
        recent_movements_query = recent_movements_query.filter(
            or_(
                StockMovement.from_depot_id == depot_id,
                StockMovement.to_depot_id == depot_id
            )
        )
    if vehicle_id:
        recent_movements_query = recent_movements_query.filter(
            or_(
                StockMovement.from_vehicle_id == vehicle_id,
                StockMovement.to_vehicle_id == vehicle_id
            )
        )
    if stock_item_id:
        recent_movements_query = recent_movements_query.filter_by(stock_item_id=stock_item_id)
    
    # Appliquer le LIMIT après tous les filtres
    recent_movements = recent_movements_query.limit(20).all()
    
    # Récupérer les commandes validées en attente de chargement
    # Pour le magasinier : toutes les commandes validées sans bon de sortie
    # Pour les autres : commandes avec récapitulatif en statut "pending" ou "stock_checked"
    pending_orders = []
    if has_permission(current_user, 'orders.read'):
        # Si c'est un magasinier, récupérer toutes les commandes validées sans bon de sortie
        if current_user.role and current_user.role.code == 'warehouse':
            # Récupérer toutes les commandes validées
            validated_orders = CommercialOrder.query.options(
                joinedload(CommercialOrder.commercial),
                joinedload(CommercialOrder.region),
                joinedload(CommercialOrder.validator),
                joinedload(CommercialOrder.clients).joinedload(CommercialOrderClient.items)
            ).filter(
                CommercialOrder.status == 'validated'
            ).order_by(CommercialOrder.validated_at.desc()).all()
            
            # Filtrer celles qui n'ont pas de bon de sortie
            # Les bons de sortie ont la référence de la commande dans leurs notes
            for order in validated_orders:
                # Vérifier si un bon de sortie existe pour cette commande en cherchant dans les notes
                outgoing = StockOutgoing.query.filter(
                    StockOutgoing.notes.like(f'%commande {order.reference}%')
                ).first()
                if not outgoing:
                    # Récupérer le récapitulatif de chargement si il existe
                    summary = StockLoadingSummary.query.filter_by(order_id=order.id).first()
                    
                    # Compter le nombre de clients et d'articles
                    total_clients = len(order.clients) if order.clients else 0
                    total_items = sum(len(client.items) for client in order.clients) if order.clients else 0
                    total_quantity = sum(
                        sum(item.quantity for item in client.items)
                        for client in order.clients
                    ) if order.clients else Decimal('0')
                    
                    # Déterminer le dépôt source
                    source_depot = None
                    if summary and summary.source_depot:
                        source_depot = summary.source_depot
                    elif order.region:
                        # Prendre le premier dépôt de la région
                        source_depot = Depot.query.filter_by(region_id=order.region.id, is_active=True).first()
                    
                    # Calculer les jours d'attente
                    days_waiting = 0
                    if order.validated_at:
                        now = datetime.now(UTC)
                        validated_at = order.validated_at
                        # S'assurer que validated_at est aware (avec timezone)
                        if validated_at.tzinfo is None:
                            validated_at = validated_at.replace(tzinfo=UTC)
                        days_waiting = (now - validated_at).days
                    
                    pending_orders.append({
                        'order': order,
                        'summary': summary,
                        'source_depot': source_depot,
                        'total_clients': total_clients,
                        'total_items': total_items,
                        'total_quantity': float(total_quantity) if isinstance(total_quantity, Decimal) else total_quantity,
                        'days_waiting': days_waiting
                    })
        else:
            # Pour les autres rôles, utiliser la logique avec récapitulatifs
            pending_loading_summaries = StockLoadingSummary.query.options(
                joinedload(StockLoadingSummary.order).joinedload(CommercialOrder.commercial),
                joinedload(StockLoadingSummary.order).joinedload(CommercialOrder.region),
                joinedload(StockLoadingSummary.order).joinedload(CommercialOrder.validator),
                joinedload(StockLoadingSummary.source_depot)
            ).filter(
                StockLoadingSummary.status.in_(['pending', 'stock_checked'])
            ).order_by(StockLoadingSummary.created_at.desc()).all()
            
            # Pour chaque récapitulatif, vérifier si un bon de sortie existe déjà
            for summary in pending_loading_summaries:
                # Vérifier si un bon de sortie existe pour cette commande
                # Les bons de sortie ont la référence de la commande dans leurs notes
                if summary.order:
                    outgoing = StockOutgoing.query.filter(
                        StockOutgoing.notes.like(f'%commande {summary.order.reference}%')
                    ).first()
                else:
                    outgoing = None
                if not outgoing:
                    # Compter le nombre de clients et d'articles
                    total_clients = len(summary.order.clients) if summary.order else 0
                    total_items = sum(len(client.items) for client in summary.order.clients) if summary.order else 0
                    total_quantity = sum(
                        sum(item.quantity for item in client.items)
                        for client in summary.order.clients
                    ) if summary.order else 0
                    
                    # Calculer les jours d'attente
                    days_waiting = 0
                    if summary.order and summary.order.validated_at:
                        now = datetime.now(UTC)
                        validated_at = summary.order.validated_at
                        # S'assurer que validated_at est aware (avec timezone)
                        if validated_at.tzinfo is None:
                            validated_at = validated_at.replace(tzinfo=UTC)
                        days_waiting = (now - validated_at).days
                    
                    pending_orders.append({
                        'order': summary.order,
                        'summary': summary,
                        'source_depot': summary.source_depot,
                        'total_clients': total_clients,
                        'total_items': total_items,
                        'total_quantity': float(total_quantity) if isinstance(total_quantity, Decimal) else total_quantity,
                        'days_waiting': days_waiting
                    })
    
    return render_template('stocks/stock_summary.html',
                         stock_summary=stock_summary,
                         depots=depots,
                         vehicles=vehicles,
                         stock_items=stock_items,
                         period=period,
                         start_date=start_date,
                         end_date=end_date,
                         selected_depot_id=depot_id,
                         selected_vehicle_id=vehicle_id,
                         selected_stock_item_id=stock_item_id,
                         total_items=total_items,
                         total_quantity=total_quantity,
                         total_value=total_value,
                         depot_stats=depot_stats,
                         can_view_stock_values=can_view_values,
                         total_receptions_all=total_receptions_all,
                         total_entries_all=total_entries_all,
                         total_exits_all=total_exits_all,
                         total_transfers_all=total_transfers_all,
                         total_stock_all_depots=total_stock_all_depots,
                         recent_movements=recent_movements,
                         pending_orders=pending_orders)

# =========================================================
# HISTORIQUE DES MOUVEMENTS PAR ARTICLE
# =========================================================

@stocks_bp.route('/update-movements-signs', methods=['GET', 'POST'])
@login_required
def update_movements_signs():
    """Route admin pour mettre à jour les anciens mouvements avec les nouveaux signes"""
    from auth import is_admin
    if not is_admin(current_user):
        flash('Vous n\'avez pas la permission d\'accéder à cette page', 'error')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        stats = {
            'transfers_updated': 0,
            'transfers_created': 0,
            'receptions_updated': 0,
            'adjustments_updated': 0,
            'errors': []
        }
        
        try:
            # 1. Traiter les transferts
            transfers = StockMovement.query.filter_by(movement_type='transfer').all()
            
            # Stocker les données avant suppression
            transfers_to_split = []
            for movement in transfers:
                try:
                    has_source = movement.from_depot_id or movement.from_vehicle_id
                    has_dest = movement.to_depot_id or movement.to_vehicle_id
                    
                    if has_source and has_dest:
                        # Ancien format : diviser en 2 mouvements
                        # Stocker les données avant suppression
                        transfers_to_split.append({
                            'id': movement.id,
                            'quantity': abs(float(movement.quantity)),
                            'reference': movement.reference,
                            'movement_date': movement.movement_date,
                            'stock_item_id': movement.stock_item_id,
                            'user_id': movement.user_id,
                            'reason': movement.reason,
                            'from_depot_id': movement.from_depot_id,
                            'from_vehicle_id': movement.from_vehicle_id,
                            'to_depot_id': movement.to_depot_id,
                            'to_vehicle_id': movement.to_vehicle_id
                        })
                        # Supprimer l'ancien
                        db.session.delete(movement)
                        stats['transfers_updated'] += 1
                        
                    elif has_source and not has_dest:
                        # Corriger signe sortie
                        if movement.quantity > 0:
                            movement.quantity = -abs(movement.quantity)
                            stats['transfers_updated'] += 1
                            
                    elif has_dest and not has_source:
                        # Corriger signe entrée
                        if movement.quantity < 0:
                            movement.quantity = abs(movement.quantity)
                            stats['transfers_updated'] += 1
                            
                except Exception as e:
                    stats['errors'].append(f"Transfert ID {movement.id}: {str(e)}")
            
            # Flush pour supprimer les anciens mouvements AVANT de créer les nouveaux
            db.session.flush()
            
            # Maintenant créer les nouveaux mouvements (après le flush)
            for data in transfers_to_split:
                try:
                    # Vérifier si la référence originale existe déjà
                    original_ref = data['reference']
                    ref_out = None
                    ref_in = None
                    
                    # Vérifier si la référence originale existe déjà dans la base
                    existing = StockMovement.query.filter_by(reference=original_ref).first()
                    if existing:
                        # Générer des références uniques
                        date_str = data['movement_date'].strftime('%Y%m%d') if data['movement_date'] else datetime.now().strftime('%Y%m%d')
                        base_ref = original_ref.split('-')[0] if '-' in original_ref else 'TRANS'
                        
                        # Chercher des références uniques
                        counter = 1
                        while True:
                            ref_out = f"{base_ref}-{date_str}-{counter:04d}-OUT"
                            ref_in = f"{base_ref}-{date_str}-{counter:04d}-IN"
                            
                            # Vérifier si ces références existent déjà
                            if not StockMovement.query.filter_by(reference=ref_out).first() and \
                               not StockMovement.query.filter_by(reference=ref_in).first():
                                break
                            counter += 1
                            
                            # Sécurité : éviter une boucle infinie
                            if counter > 9999:
                                # Utiliser un timestamp pour garantir l'unicité
                                timestamp = int(time.time())
                                ref_out = f"{base_ref}-{date_str}-{timestamp}-OUT"
                                ref_in = f"{base_ref}-{date_str}-{timestamp}-IN"
                                break
                    else:
                        # Utiliser la référence originale avec suffixe
                        ref_out = f"{original_ref}-OUT"
                        ref_in = f"{original_ref}-IN"
                        
                        # Vérifier si ces références existent déjà
                        if StockMovement.query.filter_by(reference=ref_out).first() or \
                           StockMovement.query.filter_by(reference=ref_in).first():
                            # Générer des références uniques
                            date_str = data['movement_date'].strftime('%Y%m%d') if data['movement_date'] else datetime.now().strftime('%Y%m%d')
                            base_ref = original_ref.split('-')[0] if '-' in original_ref else 'TRANS'
                            timestamp = int(time.time())
                            ref_out = f"{base_ref}-{date_str}-{timestamp}-OUT"
                            ref_in = f"{base_ref}-{date_str}-{timestamp}-IN"
                    
                    # Créer SORTIE (négatif)
                    movement_out = StockMovement(
                        reference=ref_out,
                        movement_type='transfer',
                        movement_date=data['movement_date'],
                        stock_item_id=data['stock_item_id'],
                        quantity=Decimal(str(-data['quantity'])),
                        user_id=data['user_id'],
                        from_depot_id=data['from_depot_id'],
                        from_vehicle_id=data['from_vehicle_id'],
                        to_depot_id=None,
                        to_vehicle_id=None,
                        reason=data['reason']
                    )
                    db.session.add(movement_out)
                    db.session.flush()
                    
                    # Créer ENTRÉE (positif)
                    movement_in = StockMovement(
                        reference=ref_in,
                        movement_type='transfer',
                        movement_date=data['movement_date'],
                        stock_item_id=data['stock_item_id'],
                        quantity=Decimal(str(data['quantity'])),
                        user_id=data['user_id'],
                        from_depot_id=None,
                        from_vehicle_id=None,
                        to_depot_id=data['to_depot_id'],
                        to_vehicle_id=data['to_vehicle_id'],
                        reason=data['reason']
                    )
                    db.session.add(movement_in)
                    db.session.flush()
                    
                    stats['transfers_created'] += 2
                except Exception as e:
                    stats['errors'].append(f"Création transfert {data.get('reference', 'N/A')}: {str(e)}")
                    db.session.rollback()
                    # Continuer avec le prochain transfert
                    continue
            
            # 2. Traiter les réceptions
            receptions = StockMovement.query.filter_by(movement_type='reception').all()
            
            for movement in receptions:
                try:
                    if movement.quantity < 0:
                        movement.quantity = abs(movement.quantity)
                        stats['receptions_updated'] += 1
                    
                    if movement.from_depot_id or movement.from_vehicle_id:
                        movement.from_depot_id = None
                        movement.from_vehicle_id = None
                        stats['receptions_updated'] += 1
                        
                except Exception as e:
                    stats['errors'].append(f"Réception ID {movement.id}: {str(e)}")
            
            # 3. Traiter les ajustements
            adjustments = StockMovement.query.filter_by(movement_type='adjustment').all()
            
            for movement in adjustments:
                try:
                    has_source = movement.from_depot_id or movement.from_vehicle_id
                    has_dest = movement.to_depot_id or movement.to_vehicle_id
                    
                    if has_dest and not has_source:
                        # Ajustement positif
                        if movement.quantity < 0:
                            movement.quantity = abs(movement.quantity)
                            stats['adjustments_updated'] += 1
                            
                    elif has_source and not has_dest:
                        # Ajustement négatif
                        if movement.quantity > 0:
                            movement.quantity = -abs(movement.quantity)
                            stats['adjustments_updated'] += 1
                            
                except Exception as e:
                    stats['errors'].append(f"Ajustement ID {movement.id}: {str(e)}")
            
            try:
                db.session.commit()
                
                error_msg = ""
                if stats['errors']:
                    error_msg = f"<br>❌ Erreurs ({len(stats['errors'])}):<br>" + "<br>".join(stats['errors'][:10])
                    if len(stats['errors']) > 10:
                        error_msg += f"<br>... et {len(stats['errors']) - 10} autres erreurs"
                
                flash(f"""
                    ✅ Mise à jour terminée !<br>
                    📦 Transferts: {stats['transfers_updated']} traités ({stats['transfers_created']} nouveaux mouvements créés)<br>
                    📥 Réceptions: {stats['receptions_updated']} corrigées<br>
                    🔧 Ajustements: {stats['adjustments_updated']} corrigés{error_msg}
                """, 'success' if not stats['errors'] else 'warning')
                
                return redirect(url_for('stocks.movements_list'))
                
            except Exception as commit_error:
                db.session.rollback()
                import traceback
                error_details = traceback.format_exc()
                print(f"❌ Erreur lors du commit: {error_details}")
                flash(f'Erreur lors du commit: {str(commit_error)}', 'error')
                return redirect(url_for('stocks.update_movements_signs'))
            
        except Exception as e:
            db.session.rollback()
            import traceback
            error_details = traceback.format_exc()
            print(f"❌ Erreur lors de la mise à jour: {error_details}")
            flash(f'Erreur lors de la mise à jour: {str(e)}', 'error')
            return redirect(url_for('stocks.update_movements_signs'))
    
    # GET : Afficher la page de confirmation
    transfers_count = StockMovement.query.filter_by(movement_type='transfer').count()
    receptions_count = StockMovement.query.filter_by(movement_type='reception').count()
    adjustments_count = StockMovement.query.filter_by(movement_type='adjustment').count()
    
    return render_template('stocks/update_movements_signs.html',
                         transfers_count=transfers_count,
                         receptions_count=receptions_count,
                         adjustments_count=adjustments_count)

@stocks_bp.route('/history')
@login_required
def stock_history():
    """Historique des mouvements de stock par article et par période"""
    if not has_permission(current_user, 'stocks.read'):
        flash('Vous n\'avez pas la permission d\'accéder à cette page', 'error')
        return redirect(url_for('index'))
    
    from datetime import datetime, UTC, timedelta
    from sqlalchemy import and_, or_
    
    # Récupérer les paramètres de filtre
    period = request.args.get('period', 'month')  # today, week, month, year, all, custom
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    stock_item_id = request.args.get('stock_item_id', type=int)
    movement_type = request.args.get('movement_type')
    depot_id = request.args.get('depot_id', type=int)
    vehicle_id = request.args.get('vehicle_id', type=int)
    
    # Calculer les dates selon la période
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    date_filter = None
    
    if period == 'today':
        date_filter = and_(StockMovement.movement_date >= today)
    elif period == 'week':
        week_start = today - timedelta(days=today.weekday())
        date_filter = and_(StockMovement.movement_date >= week_start)
    elif period == 'month':
        month_start = today.replace(day=1)
        date_filter = and_(StockMovement.movement_date >= month_start)
    elif period == 'year':
        year_start = today.replace(month=1, day=1)
        date_filter = and_(StockMovement.movement_date >= year_start)
    elif period == 'custom' and start_date and end_date:
        try:
            start = datetime.strptime(start_date, '%Y-%m-%d')
            end = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
            date_filter = and_(StockMovement.movement_date >= start, StockMovement.movement_date < end)
        except:
            pass
    
    # Construire la requête
    movements_query = StockMovement.query
    
    # Appliquer les filtres
    if date_filter is not None:
        movements_query = movements_query.filter(date_filter)
    
    if stock_item_id:
        movements_query = movements_query.filter_by(stock_item_id=stock_item_id)
    
    if movement_type:
        movements_query = movements_query.filter_by(movement_type=movement_type)
    
    if depot_id:
        movements_query = movements_query.filter(
            or_(
                StockMovement.from_depot_id == depot_id,
                StockMovement.to_depot_id == depot_id
            )
        )
    
    if vehicle_id:
        movements_query = movements_query.filter(
            or_(
                StockMovement.from_vehicle_id == vehicle_id,
                StockMovement.to_vehicle_id == vehicle_id
            )
        )
    
    # Appliquer le filtrage par région aux mouvements
    from utils_region_filter import filter_stock_movements_by_region
    movements_query = filter_stock_movements_by_region(movements_query)
    
    # Récupérer les mouvements avec optimisation N+1
    movements = movements_query.options(
        joinedload(StockMovement.stock_item),
        joinedload(StockMovement.from_depot),
        joinedload(StockMovement.to_depot),
        joinedload(StockMovement.from_vehicle),
        joinedload(StockMovement.to_vehicle),
        joinedload(StockMovement.user)
    ).order_by(StockMovement.movement_date.asc()).limit(1000).all()  # Ordre croissant pour calculer le solde progressif
    
    # Grouper par article
    movements_by_item = {}
    for movement in movements:
        item_id = movement.stock_item_id
        if item_id not in movements_by_item:
            movements_by_item[item_id] = {
                'item': movement.stock_item,
                'movements': []
            }
        movements_by_item[item_id]['movements'].append(movement)
    
    # Calculer le stock initial (avant la période filtrée) et le solde progressif
    for item_id, data in movements_by_item.items():
        stock_item = data['item']
        
        # Calculer le stock initial : somme de tous les mouvements AVANT la période filtrée
        # IMPORTANT : Appliquer les mêmes filtres que les mouvements affichés (sauf la date)
        initial_stock_query = StockMovement.query.filter_by(stock_item_id=item_id)
        
        # Appliquer le filtrage par région
        initial_stock_query = filter_stock_movements_by_region(initial_stock_query)
        
        # Appliquer les mêmes filtres que les mouvements affichés (sauf la date)
        if movement_type:
            initial_stock_query = initial_stock_query.filter_by(movement_type=movement_type)
        
        if depot_id:
            initial_stock_query = initial_stock_query.filter(
                or_(
                    StockMovement.from_depot_id == depot_id,
                    StockMovement.to_depot_id == depot_id
                )
            )
        
        if vehicle_id:
            initial_stock_query = initial_stock_query.filter(
                or_(
                    StockMovement.from_vehicle_id == vehicle_id,
                    StockMovement.to_vehicle_id == vehicle_id
                )
            )
        
        # Récupérer la date de début du filtre
        filter_start = None
        
        if period == 'today':
            filter_start = today
        elif period == 'week':
            filter_start = today - timedelta(days=today.weekday())
        elif period == 'month':
            filter_start = today.replace(day=1)
        elif period == 'year':
            filter_start = today.replace(month=1, day=1)
        elif period == 'custom' and start_date:
            try:
                filter_start = datetime.strptime(start_date, '%Y-%m-%d')
            except:
                filter_start = None
        # Si period == 'all', filter_start reste None (pas de limite)
        
        if filter_start:
            # Stock initial = somme de tous les mouvements avant la date de début
            # (avec les mêmes filtres de dépôt/véhicule/type)
            initial_movements = initial_stock_query.filter(
                StockMovement.movement_date < filter_start
            ).all()
            initial_stock = sum(Decimal(str(m.quantity)) for m in initial_movements)
        else:
            # Pas de filtre de date (period == 'all'), stock initial = 0
            initial_stock = Decimal('0')
        
        data['initial_stock'] = float(initial_stock)
        
        # Trier les mouvements par date croissante (du plus ancien au plus récent) pour calculer le solde progressif
        data['movements'].sort(key=lambda m: (m.movement_date, m.id))
        
        # Calculer le solde progressif pour chaque mouvement dans l'ordre chronologique
        running_balance = initial_stock
        for movement in data['movements']:
            running_balance += Decimal(str(movement.quantity))
            movement.running_balance = float(running_balance)
        
        # Stock final
        data['final_stock'] = float(running_balance)
        
        # Calculer les totaux par article
        # Entrées : mouvements positifs (réceptions, transferts entrants, retours clients)
        entries = sum(float(m.quantity) for m in data['movements'] if float(m.quantity) > 0)
        # Sorties : mouvements négatifs (ventes, transferts sortants, retours fournisseurs)
        exits = sum(abs(float(m.quantity)) for m in data['movements'] if float(m.quantity) < 0)
        data['total_entries'] = entries
        data['total_exits'] = exits
        data['net'] = entries - exits
        
        # Inverser l'ordre pour l'affichage : du plus récent au plus ancien
        data['movements'].reverse()
    
    # Récupérer les données pour les filtres (filtrées par région)
    from utils_region_filter import filter_depots_by_region, filter_vehicles_by_region
    stock_items = StockItem.query.filter_by(is_active=True).order_by(StockItem.name).all()
    depots_query = Depot.query.filter_by(is_active=True)
    depots_query = filter_depots_by_region(depots_query)
    depots = depots_query.order_by(Depot.name).all()
    vehicles_query = Vehicle.query.filter_by(status='active')
    vehicles_query = filter_vehicles_by_region(vehicles_query)
    vehicles = vehicles_query.order_by(Vehicle.plate_number).all()
    
    # Calculer les totaux globaux
    total_movements = len(movements)
    total_entries = sum(float(m.quantity) for m in movements if float(m.quantity) > 0)
    total_exits = sum(abs(float(m.quantity)) for m in movements if float(m.quantity) < 0)
    
    return render_template('stocks/stock_history.html',
                         movements_by_item=movements_by_item,
                         stock_items=stock_items,
                         depots=depots,
                         vehicles=vehicles,
                         period=period,
                         start_date=start_date,
                         end_date=end_date,
                         selected_stock_item_id=stock_item_id,
                         selected_movement_type=movement_type,
                         selected_depot_id=depot_id,
                         selected_vehicle_id=vehicle_id,
                         total_movements=total_movements,
                         total_entries=total_entries,
                         total_exits=total_exits)

# =========================================================
# DASHBOARD MAGASINIER - RÉCAPITULATIFS DE CHARGEMENT
# =========================================================

@stocks_bp.route('/warehouse/dashboard')
@login_required
def warehouse_dashboard():
    """Dashboard magasinier avec récapitulatifs de chargement"""
    if not has_permission(current_user, 'stocks.read'):
        flash('Vous n\'avez pas la permission d\'accéder à cette page', 'error')
        return redirect(url_for('index'))
    
    from sqlalchemy import func, and_, or_
    
    # Filtres
    status_filter = request.args.get('status', 'all')
    commercial_filter = request.args.get('commercial_id', type=int)
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    
    # Requête de base (filtrée par région)
    from utils_region_filter import filter_commercial_orders_by_region, filter_depots_by_region, filter_stock_movements_by_region, filter_depot_stocks_by_region
    query = StockLoadingSummary.query.options(
        joinedload(StockLoadingSummary.order),
        joinedload(StockLoadingSummary.commercial),
        joinedload(StockLoadingSummary.source_depot),
        joinedload(StockLoadingSummary.commercial_depot),
        joinedload(StockLoadingSummary.commercial_vehicle),
        joinedload(StockLoadingSummary.items).joinedload(StockLoadingSummaryItem.stock_item)
    )
    
    # Filtrer par région via la commande commerciale
    orders_query = CommercialOrder.query
    orders_query = filter_commercial_orders_by_region(orders_query)
    accessible_order_ids = [o.id for o in orders_query.all()]
    if accessible_order_ids:
        query = query.filter(StockLoadingSummary.order_id.in_(accessible_order_ids))
    else:
        # Aucune commande accessible, retourner une requête vide
        query = query.filter(False)
    
    # Appliquer les filtres
    if status_filter != 'all':
        query = query.filter(StockLoadingSummary.status == status_filter)
    
    if commercial_filter:
        query = query.filter(StockLoadingSummary.commercial_id == commercial_filter)
    
    if date_from:
        try:
            date_from_obj = datetime.strptime(date_from, '%Y-%m-%d')
            query = query.filter(StockLoadingSummary.created_at >= date_from_obj)
        except ValueError:
            pass
    
    if date_to:
        try:
            date_to_obj = datetime.strptime(date_to, '%Y-%m-%d')
            query = query.filter(StockLoadingSummary.created_at <= date_to_obj)
        except ValueError:
            pass
    
    # Pagination
    page = request.args.get('page', 1, type=int)
    per_page = 20
    summaries = query.order_by(StockLoadingSummary.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    # Statistiques (filtrées par région)
    stats_query_base = StockLoadingSummary.query
    if accessible_order_ids:
        stats_query_base = stats_query_base.filter(StockLoadingSummary.order_id.in_(accessible_order_ids))
    else:
        stats_query_base = stats_query_base.filter(False)
    
    stats = {
        'pending': stats_query_base.filter_by(status='pending').count(),
        'stock_checked': stats_query_base.filter_by(status='stock_checked').count(),
        'loading_in_progress': stats_query_base.filter_by(status='loading_in_progress').count(),
        'completed': stats_query_base.filter_by(status='completed').count(),
    }
    
    # Calculer les commandes validées sans récapitulatif (urgentes) - filtrées par région
    validated_orders_query = CommercialOrder.query.filter_by(
        status='validated'
    ).options(
        joinedload(CommercialOrder.commercial),
        joinedload(CommercialOrder.region),
        joinedload(CommercialOrder.clients)
    )
    # Filtrer par région : IMPORTANT - aucune région ne doit voir les commandes des autres régions
    validated_orders_query = filter_commercial_orders_by_region(validated_orders_query)
    
    # Vérification supplémentaire : s'assurer que le filtrage est bien appliqué
    # Si l'utilisateur n'est pas admin, on doit avoir un filtre par région
    from utils_region_filter import get_user_region_id
    region_id = get_user_region_id()
    if region_id is not None:
        # Double vérification : filtrer explicitement par région
        validated_orders_query = validated_orders_query.filter(CommercialOrder.region_id == region_id)
    
    validated_orders_without_summary = validated_orders_query.all()
    
    urgent_orders = []
    for order in validated_orders_without_summary:
        # Vérifier si un récapitulatif existe
        summary = StockLoadingSummary.query.filter_by(order_id=order.id).first()
        if not summary:
            # Vérifier si un bon de sortie existe
            outgoing = StockOutgoing.query.filter(
                StockOutgoing.notes.like(f'%commande {order.reference}%')
            ).first()
            if not outgoing:
                # Calculer les jours d'attente
                days_waiting = 0
                if order.validated_at:
                    now = datetime.now(UTC)
                    validated_at = order.validated_at
                    if validated_at.tzinfo is None:
                        validated_at = validated_at.replace(tzinfo=UTC)
                    days_waiting = (now - validated_at).days
                
                urgent_orders.append({
                    'order': order,
                    'days_waiting': days_waiting,
                    'total_clients': len(order.clients) if order.clients else 0,
                    'total_items': sum(len(client.items) for client in order.clients) if order.clients else 0,
                })
    
    # Trier par priorité (jours d'attente décroissant)
    urgent_orders.sort(key=lambda x: x['days_waiting'], reverse=True)
    urgent_orders = urgent_orders[:10]  # Limiter à 10 les plus urgents
    
    # Calculer le total des commandes urgentes
    stats['urgent'] = len(urgent_orders)
    
    # Récupérer les commerciaux pour le filtre
    commercial_role = Role.query.filter_by(code='commercial').first()
    commercials = User.query.filter_by(role_id=commercial_role.id, is_active=True).all() if commercial_role else []
    
    # =========================================================
    # TABLEAU RÉCAPITULATIF PAR ARTICLE AVEC QUANTITÉS RESTANTES
    # =========================================================
    # Filtres pour le tableau récapitulatif
    stock_period = request.args.get('stock_period', 'all')  # all, today, week, month, year, custom
    stock_date_from = request.args.get('stock_date_from', '')
    stock_date_to = request.args.get('stock_date_to', '')
    stock_depot_id = request.args.get('stock_depot_id', type=int)
    
    # Calculer les dates pour le calcul des stocks
    stock_start_date = None
    stock_end_date = None
    
    if stock_period == 'today':
        stock_start_date = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
        stock_end_date = datetime.now(UTC)
    elif stock_period == 'week':
        stock_end_date = datetime.now(UTC)
        stock_start_date = stock_end_date - timedelta(days=7)
    elif stock_period == 'month':
        stock_end_date = datetime.now(UTC)
        stock_start_date = stock_end_date - timedelta(days=30)
    elif stock_period == 'year':
        stock_end_date = datetime.now(UTC)
        stock_start_date = stock_end_date - timedelta(days=365)
    elif stock_period == 'custom':
        if stock_date_from:
            try:
                stock_start_date = datetime.strptime(stock_date_from, '%Y-%m-%d').replace(tzinfo=UTC)
            except ValueError:
                pass
        if stock_date_to:
            try:
                stock_end_date = datetime.strptime(stock_date_to, '%Y-%m-%d').replace(hour=23, minute=59, second=59, tzinfo=UTC)
            except ValueError:
                pass
    
    # Récupérer tous les articles de stock actifs
    stock_items = StockItem.query.filter_by(is_active=True).order_by(StockItem.name).all()
    
    # Calculer les quantités restantes pour chaque article
    stock_summary = []
    for item in stock_items:
        # Calculer le stock initial (avant la période) - filtré par région
        initial_stock = Decimal('0')
        if stock_start_date:
            # Stock initial = somme des mouvements jusqu'à stock_start_date (filtrés par région)
            initial_movements_query = StockMovement.query.filter(
                StockMovement.stock_item_id == item.id,
                StockMovement.movement_date < stock_start_date
            )
            initial_movements_query = filter_stock_movements_by_region(initial_movements_query)
            initial_movements = db.session.query(func.sum(StockMovement.quantity)).filter(
                StockMovement.id.in_([m.id for m in initial_movements_query.all()])
            ).scalar() or Decimal('0')
            initial_stock = initial_movements
        
        # Calculer les mouvements dans la période (filtrés par région)
        movements_query = StockMovement.query.filter(
            StockMovement.stock_item_id == item.id
        )
        movements_query = filter_stock_movements_by_region(movements_query)
        
        if stock_start_date:
            movements_query = movements_query.filter(StockMovement.movement_date >= stock_start_date)
        if stock_end_date:
            movements_query = movements_query.filter(StockMovement.movement_date <= stock_end_date)
        if stock_depot_id:
            # Filtrer par dépôt (source ou destination)
            movements_query = movements_query.filter(
                or_(
                    StockMovement.from_depot_id == stock_depot_id,
                    StockMovement.to_depot_id == stock_depot_id
                )
            )
        
        movements = movements_query.all()
        total_entries = sum(Decimal(str(m.quantity)) for m in movements if m.quantity > 0)
        total_exits = abs(sum(Decimal(str(m.quantity)) for m in movements if m.quantity < 0))
        
        # Stock final = stock initial + entrées - sorties
        final_stock = initial_stock + total_entries - total_exits
        
        # Récupérer le stock actuel depuis DepotStock (si disponible) - filtré par région
        current_stock = Decimal('0')
        if stock_depot_id:
            # Vérifier que le dépôt est accessible
            if stock_depot_id in [d.id for d in depots]:
                depot_stock = DepotStock.query.filter_by(
                    stock_item_id=item.id,
                    depot_id=stock_depot_id
                ).first()
                if depot_stock:
                    current_stock = Decimal(str(depot_stock.quantity))
        else:
            # Stock total de tous les dépôts accessibles (filtrés par région)
            depot_stocks_query = DepotStock.query.filter_by(stock_item_id=item.id)
            depot_stocks_query = filter_depot_stocks_by_region(depot_stocks_query)
            depot_stocks = depot_stocks_query.all()
            current_stock = sum(Decimal(str(ds.quantity)) for ds in depot_stocks)
        
        stock_summary.append({
            'item': item,
            'initial_stock': initial_stock,
            'total_entries': total_entries,
            'total_exits': total_exits,
            'final_stock': final_stock,
            'current_stock': current_stock,
            'movements_count': len(movements)
        })
    
    # Trier par quantité restante décroissante
    stock_summary.sort(key=lambda x: x['current_stock'], reverse=True)
    
    # Récupérer les dépôts pour le filtre
    from utils_region_filter import filter_depots_by_region
    depots_query = Depot.query.filter_by(is_active=True)
    depots_query = filter_depots_by_region(depots_query)
    depots = depots_query.order_by(Depot.name).all()
    
    return render_template('stocks/warehouse_dashboard.html',
                         summaries=summaries,
                         stats=stats,
                         urgent_orders=urgent_orders,
                         status_filter=status_filter,
                         commercial_filter=commercial_filter,
                         date_from=date_from,
                         date_to=date_to,
                         commercials=commercials,
                         stock_summary=stock_summary,
                         stock_period=stock_period,
                         stock_date_from=stock_date_from,
                         stock_date_to=stock_date_to,
                         stock_depot_id=stock_depot_id,
                         depots=depots)

@stocks_bp.route('/warehouse/loading/<int:id>')
@login_required
def loading_summary_detail(id):
    """Détail d'un récapitulatif de chargement"""
    # Le magasinier peut accéder même sans permission stocks.read
    if not has_permission(current_user, 'stocks.read') and not (current_user.role and current_user.role.code == 'warehouse'):
        flash('Vous n\'avez pas la permission d\'accéder à cette page', 'error')
        return redirect(url_for('stocks.warehouse_dashboard'))
    
    summary = StockLoadingSummary.query.options(
        joinedload(StockLoadingSummary.order).joinedload(CommercialOrder.clients),
        joinedload(StockLoadingSummary.commercial),
        joinedload(StockLoadingSummary.source_depot),
        joinedload(StockLoadingSummary.commercial_depot),
        joinedload(StockLoadingSummary.commercial_vehicle),
        joinedload(StockLoadingSummary.items).joinedload(StockLoadingSummaryItem.stock_item)
    ).get_or_404(id)
    
    # Récupérer le stock actuel du dépôt commercial (si défini)
    commercial_stocks = {}
    if summary.commercial_depot_id:
        depot_stocks = DepotStock.query.filter_by(depot_id=summary.commercial_depot_id).all()
        commercial_stocks = {ds.stock_item_id: ds.quantity for ds in depot_stocks}
    elif summary.commercial_vehicle_id:
        vehicle_stocks = VehicleStock.query.filter_by(vehicle_id=summary.commercial_vehicle_id).all()
        commercial_stocks = {vs.stock_item_id: vs.quantity for vs in vehicle_stocks}
    
    # Récupérer les dépôts et véhicules disponibles pour le chargement
    commercial_region_id = summary.commercial.region_id if summary.commercial else None
    depots = []
    vehicles = []
    
    if commercial_region_id:
        depots = Depot.query.filter_by(is_active=True, region_id=commercial_region_id).order_by(Depot.name).all()
        vehicles = Vehicle.query.filter_by(status='active').join(User).filter(User.region_id == commercial_region_id).order_by(Vehicle.plate_number).all()
    else:
        # Si pas de région, prendre tous les dépôts et véhicules actifs
        depots = Depot.query.filter_by(is_active=True).order_by(Depot.name).all()
        vehicles = Vehicle.query.filter_by(status='active').order_by(Vehicle.plate_number).all()
    
    # Récupérer les stocks du dépôt source pour chaque article
    source_stocks = {}
    if summary.source_depot_id:
        source_depot_stocks = DepotStock.query.filter_by(depot_id=summary.source_depot_id).all()
        source_stocks = {ds.stock_item_id: ds.quantity for ds in source_depot_stocks}
    
    return render_template('stocks/loading_summary_detail.html',
                         summary=summary,
                         commercial_stocks=commercial_stocks,
                         source_stocks=source_stocks,
                         depots=depots,
                         vehicles=vehicles)

@stocks_bp.route('/warehouse/loading/<int:id>/verify-pre', methods=['POST'])
@login_required
def loading_verify_pre(id):
    """Vérifier le stock avant chargement"""
    # Le magasinier peut vérifier le stock même sans permission stocks.update
    if not has_permission(current_user, 'stocks.update') and not (current_user.role and current_user.role.code == 'warehouse'):
        flash('Vous n\'avez pas la permission de vérifier le stock', 'error')
        return redirect(url_for('stocks.loading_summary_detail', id=id))
    
    summary = StockLoadingSummary.query.options(
        joinedload(StockLoadingSummary.items)
    ).get_or_404(id)
    
    if summary.status != 'pending':
        flash('Ce récapitulatif ne peut plus être modifié', 'error')
        return redirect(url_for('stocks.loading_summary_detail', id=id))
    
    # Récupérer les stocks restants depuis le formulaire
    stock_remaining = {}
    for item in summary.items:
        remaining_key = f'item_{item.id}_remaining'
        remaining_value = request.form.get(remaining_key, type=str)
        if remaining_value:
            try:
                stock_remaining[item.id] = Decimal(remaining_value)
            except (ValueError, TypeError):
                pass
    
    # Vérifier le stock actuel du dépôt/véhicule commercial
    commercial_depot_id = request.form.get('commercial_depot_id', type=int)
    commercial_vehicle_id = request.form.get('commercial_vehicle_id', type=int)
    
    if not commercial_depot_id and not commercial_vehicle_id:
        flash('Veuillez sélectionner un dépôt ou un véhicule commercial', 'error')
        return redirect(url_for('stocks.loading_summary_detail', id=id))
    
    # Vérifier que le stock est à zéro ou pointer le stock restant
    has_remaining_stock = False
    for item in summary.items:
        if commercial_depot_id:
            stock = DepotStock.query.filter_by(depot_id=commercial_depot_id, stock_item_id=item.stock_item_id).first()
            current_qty = stock.quantity if stock else Decimal('0')
        else:
            stock = VehicleStock.query.filter_by(vehicle_id=commercial_vehicle_id, stock_item_id=item.stock_item_id).first()
            current_qty = stock.quantity if stock else Decimal('0')
        
        if current_qty > 0:
            has_remaining_stock = True
            # Mettre à jour le stock restant dans l'item
            if item.id in stock_remaining:
                item.pre_loading_stock_remaining = stock_remaining[item.id]
            else:
                item.pre_loading_stock_remaining = current_qty
    
    # Mettre à jour le récapitulatif
    summary.commercial_depot_id = commercial_depot_id
    summary.commercial_vehicle_id = commercial_vehicle_id
    summary.pre_loading_stock_verified = True
    summary.pre_loading_stock_verified_at = datetime.now(UTC)
    summary.pre_loading_stock_verified_by_id = current_user.id
    summary.status = 'stock_checked'
    
    if has_remaining_stock:
        summary.notes = (summary.notes or '') + f'\nStock restant pointé avant chargement le {datetime.now(UTC).strftime("%Y-%m-%d %H:%M")}'
    
    db.session.commit()
    
    flash('Vérification du stock avant chargement effectuée avec succès', 'success')
    return redirect(url_for('stocks.loading_summary_detail', id=id))

@stocks_bp.route('/warehouse/loading/<int:id>/load', methods=['POST'])
@login_required
def loading_execute(id):
    """Exécuter le chargement de stock"""
    print(f"DEBUG loading_execute: Début - ID: {id}, User: {current_user.username}")
    
    # Le magasinier peut exécuter le chargement même sans permission movements.create
    if not has_permission(current_user, 'movements.create') and not (current_user.role and current_user.role.code == 'warehouse'):
        flash('Vous n\'avez pas la permission de créer des mouvements', 'error')
        return redirect(url_for('stocks.loading_summary_detail', id=id))
    
    summary = StockLoadingSummary.query.options(
        joinedload(StockLoadingSummary.items).joinedload(StockLoadingSummaryItem.stock_item),
        joinedload(StockLoadingSummary.order),
        joinedload(StockLoadingSummary.commercial)
    ).get_or_404(id)
    
    print(f"DEBUG loading_execute: Summary trouvé - Status: {summary.status}, Order: {summary.order.reference if summary.order else 'None'}")
    
    if summary.status not in ('stock_checked', 'loading_in_progress'):
        print(f"DEBUG loading_execute: ERREUR - Statut invalide: {summary.status}")
        flash('Le chargement ne peut pas être effectué dans cet état', 'error')
        return redirect(url_for('stocks.loading_summary_detail', id=id))
    
    summary.status = 'loading_in_progress'
    db.session.flush()
    print(f"DEBUG loading_execute: Statut mis à jour à 'loading_in_progress'")
    
    # Récupérer les quantités chargées depuis le formulaire
    quantities_loaded = {}
    for item in summary.items:
        qty_key = f'item_{item.id}_loaded'
        qty_value = request.form.get(qty_key, type=str)
        if qty_value:
            try:
                qty_decimal = Decimal(qty_value)
                if qty_decimal > 0:
                    quantities_loaded[item.id] = qty_decimal
            except (ValueError, TypeError):
                pass
    
    # Debug: Afficher les quantités récupérées
    print(f"DEBUG loading_execute: quantities_loaded = {quantities_loaded}")
    print(f"DEBUG loading_execute: form data = {dict(request.form)}")
    
    if not quantities_loaded:
        flash('Veuillez spécifier les quantités à charger', 'error')
        db.session.rollback()
        return redirect(url_for('stocks.loading_summary_detail', id=id))
    
    # Vérifier le stock disponible dans le dépôt source
    errors = []
    for item in summary.items:
        if item.id not in quantities_loaded:
            continue
        
        qty_to_load = quantities_loaded[item.id]
        source_stock = DepotStock.query.filter_by(
            depot_id=summary.source_depot_id,
            stock_item_id=item.stock_item_id
        ).first()
        
        available_qty = source_stock.quantity if source_stock else Decimal('0')
        print(f"DEBUG loading_execute: Item {item.stock_item.name} - Stock disponible: {available_qty}, Quantité à charger: {qty_to_load}")
        if available_qty < qty_to_load:
            error_msg = f'Stock insuffisant pour {item.stock_item.name} (disponible: {available_qty}, requis: {qty_to_load})'
            errors.append(error_msg)
            print(f"DEBUG loading_execute: ERREUR - {error_msg}")
    
    if errors:
        print(f"DEBUG loading_execute: Erreurs détectées: {errors}")
        flash('Erreurs de stock: ' + '; '.join(errors), 'error')
        db.session.rollback()
        return redirect(url_for('stocks.loading_summary_detail', id=id))
    
    print("DEBUG loading_execute: Vérification du stock OK, création des transferts...")
    
    # Créer les transferts de stock
    loading_date = datetime.now(UTC)
    generated_references = []  # Pour éviter les doublons dans la même transaction
    
    for item in summary.items:
        if item.id not in quantities_loaded:
            continue
        
        qty_to_load = quantities_loaded[item.id]
        
        # Décrémenter le stock source
        source_stock = DepotStock.query.filter_by(
            depot_id=summary.source_depot_id,
            stock_item_id=item.stock_item_id
        ).first()
        if not source_stock:
            source_stock = DepotStock(depot_id=summary.source_depot_id, stock_item_id=item.stock_item_id, quantity=Decimal('0'))
            db.session.add(source_stock)
        source_stock.quantity -= qty_to_load
        
        # Incrémenter le stock destination
        if summary.commercial_depot_id:
            dest_stock = DepotStock.query.filter_by(
                depot_id=summary.commercial_depot_id,
                stock_item_id=item.stock_item_id
            ).first()
            if not dest_stock:
                dest_stock = DepotStock(depot_id=summary.commercial_depot_id, stock_item_id=item.stock_item_id, quantity=Decimal('0'))
                db.session.add(dest_stock)
            dest_stock.quantity += qty_to_load
        elif summary.commercial_vehicle_id:
            dest_stock = VehicleStock.query.filter_by(
                vehicle_id=summary.commercial_vehicle_id,
                stock_item_id=item.stock_item_id
            ).first()
            if not dest_stock:
                dest_stock = VehicleStock(vehicle_id=summary.commercial_vehicle_id, stock_item_id=item.stock_item_id, quantity=Decimal('0'))
                db.session.add(dest_stock)
            dest_stock.quantity += qty_to_load
        
        # LOGIQUE MÉTIER : TRANSFERT = Déplacement entre dépôts/véhicules
        # Créer DEUX mouvements : SORTIE (négatif) depuis la source + ENTRÉE (positif) vers la destination
        base_reference = generate_movement_reference('transfer', generated_references)
        generated_references.append(base_reference)
        
        # Générer des références uniques pour chaque mouvement
        reference_out = f"{base_reference}-OUT"
        reference_in = f"{base_reference}-IN"
        
        # Vérifier et ajuster si nécessaire pour éviter les doublons
        counter = 1
        while StockMovement.query.filter_by(reference=reference_out).first():
            reference_out = f"{base_reference}-OUT-{counter}"
            counter += 1
        
        counter = 1
        while StockMovement.query.filter_by(reference=reference_in).first():
            reference_in = f"{base_reference}-IN-{counter}"
            counter += 1
        
        reason_text = f'Chargement commande {summary.order.reference} - Commercial: {summary.commercial.full_name or summary.commercial.username}'
        
        # Mouvement SORTIE (source)
        movement_out = StockMovement(
            reference=reference_out,
            movement_type='transfer',
            movement_date=loading_date,
            stock_item_id=item.stock_item_id,
            quantity=-qty_to_load,  # NÉGATIF pour sortie
            user_id=current_user.id,
            from_depot_id=summary.source_depot_id,
            from_vehicle_id=None,
            to_depot_id=None,
            to_vehicle_id=None,
            reason=f'{reason_text} - Sortie'
        )
        db.session.add(movement_out)
        
        # Mouvement ENTRÉE (destination)
        movement_in = StockMovement(
            reference=reference_in,
            movement_type='transfer',
            movement_date=loading_date,
            stock_item_id=item.stock_item_id,
            quantity=qty_to_load,  # POSITIF pour entrée
            user_id=current_user.id,
            from_depot_id=None,
            from_vehicle_id=None,
            to_depot_id=summary.commercial_depot_id,
            to_vehicle_id=summary.commercial_vehicle_id,
            reason=f'{reason_text} - Entrée'
        )
        db.session.add(movement_in)
        
        # Mettre à jour l'item du récapitulatif
        item.quantity_loaded = qty_to_load
        print(f"DEBUG loading_execute: Mouvements créés pour item {item.stock_item.name} - Sortie: {reference_out}, Entrée: {reference_in}")
    
    print("DEBUG loading_execute: Tous les mouvements créés, flush de la session...")
    db.session.flush()
    print("DEBUG loading_execute: Flush réussi")
    
    # Vérification du stock après chargement
    for item in summary.items:
        if item.id not in quantities_loaded:
            continue
        
        if summary.commercial_depot_id:
            stock = DepotStock.query.filter_by(depot_id=summary.commercial_depot_id, stock_item_id=item.stock_item_id).first()
            current_qty = stock.quantity if stock else Decimal('0')
        else:
            stock = VehicleStock.query.filter_by(vehicle_id=summary.commercial_vehicle_id, stock_item_id=item.stock_item_id).first()
            current_qty = stock.quantity if stock else Decimal('0')
        
        # Stock restant après chargement (si > quantité chargée)
        if current_qty > item.quantity_loaded:
            remaining_key = f'item_{item.id}_post_remaining'
            remaining_value = request.form.get(remaining_key, type=str)
            if remaining_value:
                try:
                    item.post_loading_stock_remaining = Decimal(remaining_value)
                except (ValueError, TypeError):
                    item.post_loading_stock_remaining = current_qty - item.quantity_loaded
            else:
                item.post_loading_stock_remaining = current_qty - item.quantity_loaded
    
    # Finaliser le récapitulatif
    try:
        print("DEBUG loading_execute: Finalisation du récapitulatif...")
        summary.status = 'completed'
        summary.loading_completed_at = loading_date
        summary.loading_completed_by_id = current_user.id
        summary.post_loading_stock_verified = True
        summary.post_loading_stock_verified_at = loading_date
        summary.post_loading_stock_verified_by_id = current_user.id
        
        print("DEBUG loading_execute: Commit de la transaction...")
        db.session.commit()
        print("DEBUG loading_execute: Commit réussi !")
        
        flash(f'Chargement effectué avec succès pour la commande {summary.order.reference}', 'success')
        return redirect(url_for('stocks.loading_summary_detail', id=id))
    except Exception as e:
        db.session.rollback()
        print(f"ERROR loading_execute: {str(e)}")
        import traceback
        traceback.print_exc()
        flash(f'Erreur lors du chargement: {str(e)}', 'error')
        return redirect(url_for('stocks.loading_summary_detail', id=id))

