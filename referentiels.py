#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module Référentiels - Import Profit Pro
Gestion des régions, dépôts, véhicules, familles et stock-items
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from datetime import datetime, UTC
from models import db, Region, Depot, Vehicle, Family, StockItem, User
from auth import has_permission, require_permission
from sqlalchemy.orm import joinedload
from sqlalchemy import or_
from utils_region_filter import (
    filter_depots_by_region, 
    filter_vehicles_by_region,
    filter_users_by_region,
    get_user_accessible_regions,
    can_access_region
)

# Créer le blueprint
referentiels_bp = Blueprint('referentiels', __name__, url_prefix='/referentiels')

# =========================================================
# RÉGIONS
# =========================================================

@referentiels_bp.route('/regions')
@login_required
def regions_list():
    """Liste des régions avec statistiques"""
    if not has_permission(current_user, 'regions.read'):
        flash('Vous n\'avez pas la permission d\'accéder à cette page', 'error')
        return redirect(url_for('index'))
    
    regions = Region.query.order_by(Region.name).all()
    
    # Calculer les statistiques pour chaque région
    from models import DepotStock
    region_stats = []
    for region in regions:
        stats = {
            'region': region,
            'users_count': User.query.filter_by(region_id=region.id, is_active=True).count(),
            'depots_count': Depot.query.filter_by(region_id=region.id, is_active=True).count(),
            'vehicles_count': Vehicle.query.join(User, Vehicle.current_user_id == User.id)
                                          .filter(User.region_id == region.id, Vehicle.status == 'active').count(),
            'total_stock_items': db.session.query(DepotStock.stock_item_id)
                                          .join(Depot, DepotStock.depot_id == Depot.id)
                                          .filter(Depot.region_id == region.id)
                                          .distinct().count()
        }
        region_stats.append(stats)
    
    return render_template('referentiels/regions_list.html', 
                         regions=regions,
                         region_stats=region_stats)

@referentiels_bp.route('/regions/new', methods=['GET', 'POST'])
@login_required
def region_new():
    """Créer une nouvelle région"""
    if not has_permission(current_user, 'regions.create'):
        flash('Vous n\'avez pas la permission de créer une région', 'error')
        return redirect(url_for('referentiels.regions_list'))
    
    if request.method == 'POST':
        try:
            name = request.form.get('name', '').strip()
            code = request.form.get('code', '').strip()
            
            if not name:
                flash('Le nom est obligatoire', 'error')
                return render_template('referentiels/region_form.html')
            
            # Vérifier si la région existe déjà
            if Region.query.filter_by(name=name).first():
                flash('Cette région existe déjà', 'error')
                return render_template('referentiels/region_form.html')
            
            region = Region(name=name, code=code if code else None)
            db.session.add(region)
            db.session.commit()
            
            flash(f'Région "{name}" créée avec succès', 'success')
            return redirect(url_for('referentiels.regions_list'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur lors de la création de la région: {str(e)}', 'error')
            return render_template('referentiels/region_form.html')
    
    return render_template('referentiels/region_form.html')

@referentiels_bp.route('/regions/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def region_edit(id):
    """Modifier une région"""
    if not has_permission(current_user, 'regions.update'):
        flash('Vous n\'avez pas la permission de modifier une région', 'error')
        return redirect(url_for('referentiels.regions_list'))
    
    region = Region.query.get_or_404(id)
    
    if request.method == 'POST':
        region.name = request.form.get('name')
        region.code = request.form.get('code')
        region.updated_at = datetime.now(UTC)
        
        db.session.commit()
        flash(f'Région "{region.name}" modifiée avec succès', 'success')
        return redirect(url_for('referentiels.regions_list'))
    
    return render_template('referentiels/region_form.html', region=region)

@referentiels_bp.route('/regions/<int:id>/delete', methods=['POST'])
@login_required
def region_delete(id):
    """Supprimer une région"""
    if not has_permission(current_user, 'regions.delete'):
        flash('Vous n\'avez pas la permission de supprimer une région', 'error')
        return redirect(url_for('referentiels.regions_list'))
    
    region = Region.query.get_or_404(id)
    
    # Vérifier si la région a des dépôts
    if region.depots:
        flash('Impossible de supprimer cette région car elle contient des dépôts', 'error')
        return redirect(url_for('referentiels.regions_list'))
    
    db.session.delete(region)
    db.session.commit()
    
    flash(f'Région "{region.name}" supprimée avec succès', 'success')
    return redirect(url_for('referentiels.regions_list'))

# =========================================================
# DÉPÔTS
# =========================================================

@referentiels_bp.route('/depots')
@login_required
def depots_list():
    """Liste des dépôts avec filtrage automatique par région de l'utilisateur"""
    if not has_permission(current_user, 'depots.read'):
        flash('Vous n\'avez pas la permission d\'accéder à cette page', 'error')
        return redirect(url_for('index'))
    
    # Filtre manuel par région (pour les admins)
    region_id = request.args.get('region_id', type=int)
    query = Depot.query.options(
        joinedload(Depot.region)
    )
    
    # Filtrage automatique par région de l'utilisateur (sauf admin)
    query = filter_depots_by_region(query)
    
    # Filtre manuel supplémentaire si spécifié
    if region_id:
        query = query.filter_by(region_id=region_id)
    
    depots = query.order_by(Depot.name).all()
    regions = Region.query.order_by(Region.name).all()
    
    # Statistiques par région
    stats = {}
    for region in regions:
        stats[region.id] = {
            'total': Depot.query.filter_by(region_id=region.id).count(),
            'active': Depot.query.filter_by(region_id=region.id, is_active=True).count(),
            'inactive': Depot.query.filter_by(region_id=region.id, is_active=False).count()
        }
    
    return render_template('referentiels/depots_list.html', 
                         depots=depots, 
                         regions=regions,
                         selected_region_id=region_id,
                         stats=stats)

@referentiels_bp.route('/depots/new', methods=['GET', 'POST'])
@login_required
def depot_new():
    """Créer un nouveau dépôt"""
    if not has_permission(current_user, 'depots.create'):
        flash('Vous n\'avez pas la permission de créer un dépôt', 'error')
        return redirect(url_for('referentiels.depots_list'))
    
    regions = Region.query.order_by(Region.name).all()
    
    if request.method == 'POST':
        name = request.form.get('name')
        region_id = request.form.get('region_id')
        address = request.form.get('address')
        city = request.form.get('city')
        phone = request.form.get('phone')
        email = request.form.get('email')
        
        if not name or not region_id:
            flash('Le nom et la région sont obligatoires', 'error')
            return render_template('referentiels/depot_form.html', regions=regions)
        
        # Vérifier si le dépôt existe déjà
        if Depot.query.filter_by(name=name).first():
            flash('Ce dépôt existe déjà', 'error')
            return render_template('referentiels/depot_form.html', regions=regions)
        
        depot = Depot(
            name=name,
            region_id=int(region_id),
            address=address,
            city=city,
            phone=phone,
            email=email,
            is_active=True
        )
        db.session.add(depot)
        db.session.commit()
        
        flash(f'Dépôt "{name}" créé avec succès', 'success')
        return redirect(url_for('referentiels.depots_list'))
    
    return render_template('referentiels/depot_form.html', regions=regions)

@referentiels_bp.route('/depots/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def depot_edit(id):
    """Modifier un dépôt"""
    if not has_permission(current_user, 'depots.update'):
        flash('Vous n\'avez pas la permission de modifier un dépôt', 'error')
        return redirect(url_for('referentiels.depots_list'))
    
    depot = Depot.query.get_or_404(id)
    regions = Region.query.order_by(Region.name).all()
    
    if request.method == 'POST':
        depot.name = request.form.get('name')
        depot.region_id = int(request.form.get('region_id'))
        depot.address = request.form.get('address')
        depot.city = request.form.get('city')
        depot.phone = request.form.get('phone')
        depot.email = request.form.get('email')
        depot.is_active = bool(request.form.get('is_active'))
        depot.updated_at = datetime.now(UTC)
        
        db.session.commit()
        flash(f'Dépôt "{depot.name}" modifié avec succès', 'success')
        return redirect(url_for('referentiels.depots_list'))
    
    return render_template('referentiels/depot_form.html', depot=depot, regions=regions)

# =========================================================
# VÉHICULES
# =========================================================

@referentiels_bp.route('/vehicles')
@login_required
def vehicles_list():
    """Liste des véhicules avec pagination, recherche et optimisation"""
    if not has_permission(current_user, 'vehicles.read'):
        flash('Vous n\'avez pas la permission d\'accéder à cette page', 'error')
        return redirect(url_for('index'))
    
    # Paramètres de pagination
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    
    # Recherche et filtres
    search = request.args.get('search', '').strip()
    region_id = request.args.get('region_id', type=int)
    
    # Requête de base avec optimisation N+1
    query = Vehicle.query.options(
        joinedload(Vehicle.current_user).joinedload(User.region)
    )
    
    # Filtre par région (via le conducteur)
    if region_id:
        query = query.join(User, Vehicle.current_user_id == User.id).filter(User.region_id == region_id)
    
    # Recherche par immatriculation, marque, modèle, VIN
    if search:
        query = query.filter(
            or_(
                Vehicle.plate_number.ilike(f'%{search}%'),
                Vehicle.brand.ilike(f'%{search}%'),
                Vehicle.model.ilike(f'%{search}%'),
                Vehicle.vin.ilike(f'%{search}%')
            )
        )
    
    # Pagination
    pagination = query.order_by(Vehicle.plate_number).paginate(
        page=page, per_page=per_page, error_out=False
    )
    vehicles = pagination.items
    
    # Statistiques globales (sur TOUS les véhicules, pas seulement la page)
    stats = {
        'total': Vehicle.query.count(),
        'active': Vehicle.query.filter_by(status='active').count(),
        'inactive': Vehicle.query.filter_by(status='inactive').count(),
        'maintenance': Vehicle.query.filter_by(status='maintenance').count(),
        'without_driver': Vehicle.query.filter(
            (Vehicle.current_user_id == None) & (Vehicle.status == 'active')
        ).count()
    }
    
    # Charger les utilisateurs et régions pour les filtres
    users = User.query.filter_by(is_active=True).order_by(User.full_name).all()
    regions = Region.query.order_by(Region.name).all()
    
    return render_template('referentiels/vehicles_list.html',
                         vehicles=vehicles,
                         users=users,
                         regions=regions,
                         pagination=pagination,
                         search=search,
                         region_id=region_id,
                         stats=stats)

@referentiels_bp.route('/vehicles/new', methods=['GET', 'POST'])
@login_required
def vehicle_new():
    """Créer un nouveau véhicule"""
    if not has_permission(current_user, 'vehicles.create'):
        flash('Vous n\'avez pas la permission de créer un véhicule', 'error')
        return redirect(url_for('referentiels.vehicles_list'))
    
    users = User.query.filter_by(is_active=True).all()
    
    if request.method == 'POST':
        plate_number = request.form.get('plate_number')
        brand = request.form.get('brand')
        model = request.form.get('model')
        year = request.form.get('year')
        color = request.form.get('color')
        vin = request.form.get('vin')
        whatsapp = request.form.get('whatsapp')
        current_user_id = request.form.get('current_user_id') or None
        acquisition_date = request.form.get('acquisition_date') or None
        
        if not plate_number:
            flash('Le numéro d\'immatriculation est obligatoire', 'error')
            return render_template('referentiels/vehicle_form.html', users=users)
        
        # Vérifier si le véhicule existe déjà
        if Vehicle.query.filter_by(plate_number=plate_number).first():
            flash('Ce véhicule existe déjà', 'error')
            return render_template('referentiels/vehicle_form.html', users=users)
        
        vehicle = Vehicle(
            plate_number=plate_number,
            brand=brand,
            model=model,
            year=int(year) if year else None,
            color=color,
            vin=vin,
            whatsapp=whatsapp,
            current_user_id=int(current_user_id) if current_user_id else None,
            acquisition_date=datetime.strptime(acquisition_date, '%Y-%m-%d').date() if acquisition_date else None,
            status='active'
        )
        db.session.add(vehicle)
        db.session.commit()
        
        flash(f'Véhicule "{plate_number}" créé avec succès', 'success')
        return redirect(url_for('referentiels.vehicles_list'))
    
    return render_template('referentiels/vehicle_form.html', users=users)

@referentiels_bp.route('/vehicles/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def vehicle_edit(id):
    """Modifier un véhicule"""
    if not has_permission(current_user, 'vehicles.update'):
        flash('Vous n\'avez pas la permission de modifier un véhicule', 'error')
        return redirect(url_for('referentiels.vehicles_list'))
    
    vehicle = Vehicle.query.get_or_404(id)
    users = User.query.filter_by(is_active=True).all()
    
    if request.method == 'POST':
        vehicle.plate_number = request.form.get('plate_number')
        vehicle.brand = request.form.get('brand')
        vehicle.model = request.form.get('model')
        vehicle.year = int(request.form.get('year')) if request.form.get('year') else None
        vehicle.color = request.form.get('color')
        vehicle.vin = request.form.get('vin')
        vehicle.whatsapp = request.form.get('whatsapp')
        vehicle.current_user_id = int(request.form.get('current_user_id')) if request.form.get('current_user_id') else None
        vehicle.status = request.form.get('status')
        acquisition_date = request.form.get('acquisition_date')
        if acquisition_date:
            vehicle.acquisition_date = datetime.strptime(acquisition_date, '%Y-%m-%d').date()
        vehicle.updated_at = datetime.now(UTC)
        
        db.session.commit()
        flash(f'Véhicule "{vehicle.plate_number}" modifié avec succès', 'success')
        return redirect(url_for('referentiels.vehicles_list'))
    
    return render_template('referentiels/vehicle_form.html', vehicle=vehicle, users=users)

# =========================================================
# FAMILLES
# =========================================================

@referentiels_bp.route('/families')
@login_required
def families_list():
    """Liste des familles"""
    if not has_permission(current_user, 'families.read'):
        flash('Vous n\'avez pas la permission d\'accéder à cette page', 'error')
        return redirect(url_for('index'))
    
    families = Family.query.order_by(Family.name).all()
    return render_template('referentiels/families_list.html', families=families)

@referentiels_bp.route('/families/new', methods=['GET', 'POST'])
@login_required
def family_new():
    """Créer une nouvelle famille"""
    if not has_permission(current_user, 'families.create'):
        flash('Vous n\'avez pas la permission de créer une famille', 'error')
        return redirect(url_for('referentiels.families_list'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        code = request.form.get('code')
        description = request.form.get('description')
        
        if not name:
            flash('Le nom est obligatoire', 'error')
            return render_template('referentiels/family_form.html')
        
        # Vérifier si la famille existe déjà
        if Family.query.filter_by(name=name).first():
            flash('Cette famille existe déjà', 'error')
            return render_template('referentiels/family_form.html')
        
        family = Family(name=name, code=code, description=description)
        db.session.add(family)
        db.session.commit()
        
        flash(f'Famille "{name}" créée avec succès', 'success')
        return redirect(url_for('referentiels.families_list'))
    
    return render_template('referentiels/family_form.html')

@referentiels_bp.route('/families/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def family_edit(id):
    """Modifier une famille"""
    if not has_permission(current_user, 'families.update'):
        flash('Vous n\'avez pas la permission de modifier une famille', 'error')
        return redirect(url_for('referentiels.families_list'))
    
    family = Family.query.get_or_404(id)
    
    if request.method == 'POST':
        family.name = request.form.get('name')
        family.code = request.form.get('code')
        family.description = request.form.get('description')
        family.updated_at = datetime.now(UTC)
        
        db.session.commit()
        flash(f'Famille "{family.name}" modifiée avec succès', 'success')
        return redirect(url_for('referentiels.families_list'))
    
    return render_template('referentiels/family_form.html', family=family)

# =========================================================
# STOCK ITEMS
# =========================================================

@referentiels_bp.route('/stock-items')
@login_required
def stock_items_list():
    """Liste des articles de stock avec pagination, recherche et optimisation"""
    if not has_permission(current_user, 'stock_items.read'):
        flash('Vous n\'avez pas la permission d\'accéder à cette page', 'error')
        return redirect(url_for('index'))
    
    try:
        # Paramètres de pagination
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        
        # Paramètres de recherche et filtres
        search = request.args.get('search', '').strip()
        family_filter = request.args.get('family', '').strip()
        status_filter = request.args.get('status', '').strip()
        
        # Requête de base avec optimisation N+1
        query = StockItem.query.options(
            joinedload(StockItem.family)
        )
        
        # Recherche par SKU, nom, description
        if search:
            query = query.filter(
                or_(
                    StockItem.sku.ilike(f'%{search}%'),
                    StockItem.name.ilike(f'%{search}%'),
                    StockItem.description.ilike(f'%{search}%')
                )
            )
        
        # Filtre par famille
        if family_filter:
            query = query.join(Family).filter(Family.name == family_filter)
        
        # Filtre par statut
        if status_filter == 'active':
            query = query.filter_by(is_active=True)
        elif status_filter == 'inactive':
            query = query.filter_by(is_active=False)
        
        # Pagination
        pagination = query.order_by(StockItem.name).paginate(
            page=page, per_page=per_page, error_out=False
        )
        stock_items = pagination.items
        
        # Statistiques globales (sur TOUS les articles)
        stats = {
            'total': StockItem.query.count(),
            'active': StockItem.query.filter_by(is_active=True).count(),
            'inactive': StockItem.query.filter_by(is_active=False).count(),
            'with_family': StockItem.query.filter(StockItem.family_id != None).count(),
            'without_family': StockItem.query.filter(StockItem.family_id == None).count()
        }
        
        # Charger toutes les familles pour le filtre
        families = Family.query.order_by(Family.name).all()
        
        return render_template('referentiels/stock_items_list.html', 
                             stock_items=stock_items,
                             families=families,
                             pagination=pagination,
                             search=search,
                             family_filter=family_filter,
                             status_filter=status_filter,
                             stats=stats)
    except Exception as e:
        print(f"⚠️ Erreur lors du chargement des articles de stock: {e}")
        import traceback
        traceback.print_exc()
        flash(f'Erreur lors du chargement des articles: {str(e)}', 'error')
        return render_template('referentiels/stock_items_list.html', 
                             stock_items=[],
                             families=[],
                             pagination=None,
                             search='',
                             family_filter='',
                             status_filter='',
                             stats={'total': 0, 'active': 0, 'inactive': 0, 'with_family': 0, 'without_family': 0})

@referentiels_bp.route('/stock-items/new', methods=['GET', 'POST'])
@login_required
def stock_item_new():
    """Créer un nouvel article de stock"""
    if not has_permission(current_user, 'stock_items.create'):
        flash('Vous n\'avez pas la permission de créer un article', 'error')
        return redirect(url_for('referentiels.stock_items_list'))
    
    families = Family.query.order_by(Family.name).all()
    
    if request.method == 'POST':
        sku = request.form.get('sku')
        name = request.form.get('name')
        family_id = request.form.get('family_id')
        purchase_price_gnf = request.form.get('purchase_price_gnf') or '0'
        unit_weight_kg = request.form.get('unit_weight_kg') or '0'
        description = request.form.get('description')
        min_stock_depot = request.form.get('min_stock_depot') or '0'
        min_stock_vehicle = request.form.get('min_stock_vehicle') or '0'
        
        if not sku or not name or not family_id:
            flash('Le SKU, le nom et la famille sont obligatoires', 'error')
            return render_template('referentiels/stock_item_form.html', families=families)
        
        # Vérifier si le SKU existe déjà
        if StockItem.query.filter_by(sku=sku).first():
            flash('Ce SKU existe déjà', 'error')
            return render_template('referentiels/stock_item_form.html', families=families)
        
        from decimal import Decimal
        stock_item = StockItem(
            sku=sku,
            name=name,
            family_id=int(family_id),
            purchase_price_gnf=Decimal(purchase_price_gnf),
            unit_weight_kg=Decimal(unit_weight_kg),
            description=description,
            min_stock_depot=Decimal(min_stock_depot),
            min_stock_vehicle=Decimal(min_stock_vehicle),
            is_active=True
        )
        db.session.add(stock_item)
        db.session.commit()
        
        flash(f'Article "{name}" créé avec succès', 'success')
        return redirect(url_for('referentiels.stock_items_list'))
    
    return render_template('referentiels/stock_item_form.html', families=families)

@referentiels_bp.route('/stock-items/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def stock_item_edit(id):
    """Modifier un article de stock"""
    if not has_permission(current_user, 'stock_items.update'):
        flash('Vous n\'avez pas la permission de modifier un article', 'error')
        return redirect(url_for('referentiels.stock_items_list'))
    
    stock_item = StockItem.query.get_or_404(id)
    families = Family.query.order_by(Family.name).all()
    
    if request.method == 'POST':
        from decimal import Decimal
        stock_item.sku = request.form.get('sku')
        stock_item.name = request.form.get('name')
        stock_item.family_id = int(request.form.get('family_id'))
        stock_item.purchase_price_gnf = Decimal(request.form.get('purchase_price_gnf') or '0')
        stock_item.unit_weight_kg = Decimal(request.form.get('unit_weight_kg') or '0')
        stock_item.description = request.form.get('description')
        stock_item.min_stock_depot = Decimal(request.form.get('min_stock_depot') or '0')
        stock_item.min_stock_vehicle = Decimal(request.form.get('min_stock_vehicle') or '0')
        stock_item.is_active = bool(request.form.get('is_active'))
        stock_item.updated_at = datetime.now(UTC)
        
        db.session.commit()
        flash(f'Article "{stock_item.name}" modifié avec succès', 'success')
        return redirect(url_for('referentiels.stock_items_list'))
    
    return render_template('referentiels/stock_item_form.html', stock_item=stock_item, families=families)

