#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module Gestion de Flotte - Import Profit Pro
Gestion des documents, maintenances et odomètre des véhicules
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_required, current_user
from datetime import datetime, date, timedelta, UTC
from decimal import Decimal
from models import (
    db, Vehicle, VehicleDocument, VehicleMaintenance, VehicleOdometer, 
    VehicleAssignment, User
)
from auth import has_permission, can_view_stock_values
from utils import calculate_document_status, check_km_consistency, get_days_until_expiry
from sqlalchemy.orm import joinedload
from sqlalchemy import or_
from functools import wraps

# Créer le blueprint
flotte_bp = Blueprint('flotte', __name__, url_prefix='/vehicles')

# =========================================================
# DASHBOARD FLOTTE
# =========================================================

@flotte_bp.route('/operations-guide')
@login_required
def operations_guide():
    """Guide des opérations véhicules"""
    if not has_permission(current_user, 'vehicles.read'):
        flash('Vous n\'avez pas la permission d\'accéder à cette page', 'error')
        return redirect(url_for('index'))
    
    return render_template('flotte/operations_guide.html')

@flotte_bp.route('/dashboard')
@login_required
def dashboard():
    """Dashboard de la flotte avec statistiques et alertes"""
    if not has_permission(current_user, 'vehicles.read'):
        flash('Vous n\'avez pas la permission d\'accéder à cette page', 'error')
        return redirect(url_for('index'))
    
    try:
        cache = current_app.cache if hasattr(current_app, 'cache') and current_app.cache else None
        today = date.today()
        
        # Essayer de récupérer depuis le cache (cache de 5 minutes)
        if cache:
            cache_key = f"flotte_dashboard_{today.isoformat()}"
            cached_data = cache.get(cache_key)
            if cached_data:
                return render_template('flotte/dashboard.html', **cached_data)
        
        # Calculer les données si pas en cache
        # Filtrage par région
        from utils_region_filter import filter_vehicles_by_region
        
        # Statistiques globales avec filtrage par région
        vehicles_query = Vehicle.query
        vehicles_query = filter_vehicles_by_region(vehicles_query)
        total_vehicles = vehicles_query.count()
        
        # Récupérer les IDs des véhicules accessibles pour les filtres suivants
        accessible_vehicle_ids = [v.id for v in vehicles_query.all()]
        
        active_vehicles_query = Vehicle.query.filter_by(status='active')
        active_vehicles_query = filter_vehicles_by_region(active_vehicles_query)
        active_vehicles = active_vehicles_query.count()
        
        inactive_vehicles_query = Vehicle.query.filter_by(status='inactive')
        inactive_vehicles_query = filter_vehicles_by_region(inactive_vehicles_query)
        inactive_vehicles = inactive_vehicles_query.count()
        
        maintenance_vehicles_query = Vehicle.query.filter_by(status='maintenance')
        maintenance_vehicles_query = filter_vehicles_by_region(maintenance_vehicles_query)
        maintenance_vehicles = maintenance_vehicles_query.count()
        
        # Véhicules sans conducteur avec filtrage par région
        vehicles_without_driver_query = Vehicle.query.filter(
            (Vehicle.current_user_id == None) & (Vehicle.status == 'active')
        )
        vehicles_without_driver_query = filter_vehicles_by_region(vehicles_without_driver_query)
        vehicles_without_driver = vehicles_without_driver_query.count()
        
        # Calculer le kilométrage total (somme du dernier km de chaque véhicule)
        # Optimisation N+1 : charger les odomètres en une seule requête
        from sqlalchemy import func
        active_vehicles_list = active_vehicles_query.all()
        vehicle_ids = [v.id for v in active_vehicles_list]
        
        # Récupérer le dernier odomètre pour chaque véhicule en une seule requête
        if vehicle_ids:
            # Sous-requête pour obtenir le dernier odomètre par véhicule
            subquery = db.session.query(
                VehicleOdometer.vehicle_id,
                func.max(VehicleOdometer.reading_date).label('max_date')
            ).filter(VehicleOdometer.vehicle_id.in_(vehicle_ids)).group_by(VehicleOdometer.vehicle_id).subquery()
            
            last_odometers = db.session.query(VehicleOdometer).join(
                subquery,
                (VehicleOdometer.vehicle_id == subquery.c.vehicle_id) &
                (VehicleOdometer.reading_date == subquery.c.max_date)
            ).all()
            
            # Créer un dictionnaire pour accès rapide
            odo_dict = {odo.vehicle_id: odo for odo in last_odometers}
        else:
            odo_dict = {}
        
        total_km = 0
        vehicles_km = []
        for vehicle in active_vehicles_list:
            last_odo = odo_dict.get(vehicle.id)
            if last_odo:
                vehicles_km.append({
                    'vehicle': vehicle,
                    'km': last_odo.odometer_km
                })
                total_km += last_odo.odometer_km
        
        # Alertes - Documents expirés ou expirant bientôt
        # Optimisation N+1 : charger vehicle en une seule requête avec filtrage par région
        # Utiliser les IDs des véhicules accessibles déjà récupérés (ligne 68)
        if accessible_vehicle_ids:
            all_documents = VehicleDocument.query.filter(
                VehicleDocument.vehicle_id.in_(accessible_vehicle_ids)
            ).options(
                joinedload(VehicleDocument.vehicle)
            ).all()
        else:
            all_documents = []
        expired_documents = []
        expiring_soon_documents = []
        
        for doc in all_documents:
            # Vérifier que le document a un véhicule associé
            if not doc.vehicle:
                continue
            if doc.expiry_date:
                days = get_days_until_expiry(doc.expiry_date)
                if days < 0:
                    expired_documents.append(doc)
                elif 0 <= days <= 15:
                    expiring_soon_documents.append(doc)
        
        # Alertes - Maintenances dues avec filtrage par région
        # Optimisation N+1 : charger vehicle et odomètres en une seule requête
        if accessible_vehicle_ids:
            all_maintenances = VehicleMaintenance.query.filter_by(status='planned').filter(
                VehicleMaintenance.vehicle_id.in_(accessible_vehicle_ids)
            ).options(
                joinedload(VehicleMaintenance.vehicle)
            ).all()
        else:
            all_maintenances = []
        
        # Récupérer tous les odomètres nécessaires en une seule requête
        maintenance_vehicle_ids = [m.vehicle_id for m in all_maintenances if m.vehicle_id]
        if maintenance_vehicle_ids:
            maintenance_odometers = db.session.query(
                VehicleOdometer.vehicle_id,
                func.max(VehicleOdometer.reading_date).label('max_date')
            ).filter(VehicleOdometer.vehicle_id.in_(maintenance_vehicle_ids)).group_by(VehicleOdometer.vehicle_id).all()
            
            odo_max_dates = {odo.vehicle_id: odo.max_date for odo in maintenance_odometers}
            
            # Charger les odomètres correspondants
            odo_conditions = []
            for vid, max_date in odo_max_dates.items():
                odo_conditions.append(
                    (VehicleOdometer.vehicle_id == vid) & (VehicleOdometer.reading_date == max_date)
                )
            
            if odo_conditions:
                last_maintenance_odos = VehicleOdometer.query.filter(or_(*odo_conditions)).all()
                maintenance_odo_dict = {odo.vehicle_id: odo for odo in last_maintenance_odos}
            else:
                maintenance_odo_dict = {}
        else:
            maintenance_odo_dict = {}
        
        due_maintenances = []
        
        for maint in all_maintenances:
            # Vérifier que la maintenance a un véhicule associé
            if not maint.vehicle:
                continue
                
            is_due = False
            reason = ""
            
            # Vérifier par date
            if maint.planned_date and maint.planned_date <= today:
                is_due = True
                reason = f"Date prévue: {maint.planned_date.strftime('%d/%m/%Y')}"
            
            # Vérifier par kilométrage
            if maint.due_at_km:
                vehicle = maint.vehicle
                last_odo = maintenance_odo_dict.get(vehicle.id) if vehicle else None
                if last_odo and last_odo.odometer_km >= maint.due_at_km:
                    is_due = True
                    if reason:
                        reason += f" | "
                    reason += f"Kilométrage atteint: {last_odo.odometer_km} km (limite: {maint.due_at_km} km)"
            
            if is_due:
                due_maintenances.append({
                    'maintenance': maint,
                    'reason': reason
                })
        
        # Véhicules récents (créés dans les 30 derniers jours) avec filtrage par région
        thirty_days_ago = today - timedelta(days=30)
        recent_vehicles_query = Vehicle.query.filter(
            Vehicle.created_at >= datetime.combine(thirty_days_ago, datetime.min.time())
        )
        recent_vehicles_query = filter_vehicles_by_region(recent_vehicles_query)
        recent_vehicles = recent_vehicles_query.options(
            joinedload(Vehicle.current_user)
        ).order_by(Vehicle.created_at.desc()).limit(5).all()
        
        # Maintenances récentes (réalisées dans les 30 derniers jours) avec filtrage par région
        if accessible_vehicle_ids:
            recent_maintenances = VehicleMaintenance.query.filter(
                VehicleMaintenance.status == 'completed'
            ).filter(
                VehicleMaintenance.completed_date >= thirty_days_ago
            ).filter(
                VehicleMaintenance.vehicle_id.in_(accessible_vehicle_ids)
            ).options(
                joinedload(VehicleMaintenance.vehicle)
            ).order_by(VehicleMaintenance.completed_date.desc()).limit(5).all()
        else:
            recent_maintenances = []
        
        # Répartition par statut pour graphique
        status_distribution = {
            'active': active_vehicles,
            'inactive': inactive_vehicles,
            'maintenance': maintenance_vehicles
        }
        
        # Taux de disponibilité
        availability_rate = 0
        if total_vehicles > 0:
            availability_rate = round((active_vehicles / total_vehicles) * 100, 1)
        
        dashboard_data = {
            'total_vehicles': total_vehicles,
            'active_vehicles': active_vehicles,
            'inactive_vehicles': inactive_vehicles,
            'maintenance_vehicles': maintenance_vehicles,
            'vehicles_without_driver': vehicles_without_driver,
            'total_km': total_km,
            'vehicles_km': vehicles_km,
            'expired_documents': expired_documents,
            'expiring_soon_documents': expiring_soon_documents,
            'due_maintenances': due_maintenances,
            'recent_vehicles': recent_vehicles,
            'recent_maintenances': recent_maintenances,
            'status_distribution': status_distribution,
            'availability_rate': availability_rate,
            'today': today
        }
        
        # Mettre en cache si disponible (cache de 5 minutes)
        if cache:
            cache_key = f"flotte_dashboard_{today.isoformat()}"
            cache.set(cache_key, dashboard_data, timeout=300)
        
        return render_template('flotte/dashboard.html', **dashboard_data)
    
    except Exception as e:
        # Gestion d'erreur avec logging
        import traceback
        from sqlalchemy.exc import SQLAlchemyError
        
        # Annuler toute transaction en échec pour PostgreSQL
        try:
            db.session.rollback()
        except:
            pass
        
        current_app.logger.error(f"Erreur lors du chargement du dashboard flotte: {e}", exc_info=True)
        print(f"⚠️ Erreur dashboard flotte: {e}")
        traceback.print_exc()
        flash('Une erreur est survenue lors du chargement du dashboard. Veuillez réessayer.', 'error')
        
        # Retourner un dashboard minimal en cas d'erreur
        return render_template('flotte/dashboard.html',
            total_vehicles=0,
            active_vehicles=0,
            inactive_vehicles=0,
            maintenance_vehicles=0,
            vehicles_without_driver=0,
            total_km=0,
            vehicles_km=[],
            expired_documents=[],
            expiring_soon_documents=[],
            due_maintenances=[],
            recent_vehicles=[],
            recent_maintenances=[],
            status_distribution={'active': 0, 'inactive': 0, 'maintenance': 0},
            availability_rate=0,
            today=date.today()
        )

@flotte_bp.route('/<int:vehicle_id>/documents')
@login_required
def vehicle_documents(vehicle_id):
    """Liste des documents d'un véhicule"""
    if not has_permission(current_user, 'vehicles.read'):
        flash('Vous n\'avez pas la permission d\'accéder à cette page', 'error')
        return redirect(url_for('index'))
    
    # Vérifier l'accès au véhicule par région
    from utils_region_filter import can_access_vehicle
    if not can_access_vehicle(vehicle_id):
        flash('Vous n\'avez pas accès à ce véhicule', 'error')
        return redirect(url_for('index'))
    
    # Paramètres de pagination
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    vehicle = Vehicle.query.get_or_404(vehicle_id)
    
    # Requête de base avec pagination
    query = VehicleDocument.query.filter_by(vehicle_id=vehicle_id)\
        .options(joinedload(VehicleDocument.vehicle))\
        .order_by(VehicleDocument.expiry_date.asc())
    
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    documents = pagination.items
    
    # Calculer les alertes et jours restants
    today = date.today()
    expiring_soon = []
    expired = []
    documents_with_days = []
    
    for doc in documents:
        days = get_days_until_expiry(doc.expiry_date) if doc.expiry_date else None
        if days is not None:
            if days < 0:
                expired.append(doc)
            elif 0 <= days <= 15:
                expiring_soon.append(doc)
        documents_with_days.append((doc, days))
    
    # Calculer les alertes sur TOUS les documents (pas seulement la page actuelle)
    all_documents = VehicleDocument.query.filter_by(vehicle_id=vehicle_id).all()
    total_expired = len([d for d in all_documents if d.expiry_date and get_days_until_expiry(d.expiry_date) < 0])
    total_expiring = len([d for d in all_documents if d.expiry_date and 0 <= get_days_until_expiry(d.expiry_date) <= 15])
    
    return render_template('flotte/vehicle_documents.html', 
                         vehicle=vehicle,
                         documents=documents_with_days,
                         expiring_soon=expiring_soon,
                         expired=expired,
                         pagination=pagination,
                         total_expired=total_expired,
                         total_expiring=total_expiring,
                         today=today)

@flotte_bp.route('/<int:vehicle_id>/documents/new', methods=['GET', 'POST'])
@login_required
def document_new(vehicle_id):
    """Ajouter un document à un véhicule"""
    if not has_permission(current_user, 'vehicles.update'):
        flash('Vous n\'avez pas la permission d\'ajouter un document', 'error')
        return redirect(url_for('flotte.vehicle_documents', vehicle_id=vehicle_id))
    
    # Vérifier l'accès au véhicule par région
    from utils_region_filter import can_access_vehicle
    if not can_access_vehicle(vehicle_id):
        flash('Vous n\'avez pas accès à ce véhicule', 'error')
        return redirect(url_for('index'))
    
    vehicle = Vehicle.query.get_or_404(vehicle_id)
    
    if request.method == 'POST':
        document_type = request.form.get('document_type')
        document_number = request.form.get('document_number')
        issue_date = request.form.get('issue_date') or None
        expiry_date = request.form.get('expiry_date')
        notes = request.form.get('notes')
        
        if not document_type or not expiry_date:
            flash('Le type de document et la date d\'expiration sont obligatoires', 'error')
            return render_template('flotte/document_form.html', vehicle=vehicle)
        
        document = VehicleDocument(
            vehicle_id=vehicle_id,
            document_type=document_type,
            document_number=document_number,
            issue_date=datetime.strptime(issue_date, '%Y-%m-%d').date() if issue_date else None,
            expiry_date=datetime.strptime(expiry_date, '%Y-%m-%d').date(),
            notes=notes
        )
        db.session.add(document)
        db.session.commit()
        
        flash(f'Document "{document_type}" ajouté avec succès', 'success')
        return redirect(url_for('flotte.vehicle_documents', vehicle_id=vehicle_id))
    
    return render_template('flotte/document_form.html', vehicle=vehicle)

@flotte_bp.route('/<int:vehicle_id>/documents/<int:doc_id>/edit', methods=['GET', 'POST'])
@login_required
def document_edit(vehicle_id, doc_id):
    """Modifier un document"""
    if not has_permission(current_user, 'vehicles.update'):
        flash('Vous n\'avez pas la permission de modifier ce document', 'error')
        return redirect(url_for('flotte.vehicle_documents', vehicle_id=vehicle_id))
    
    # Vérifier l'accès au véhicule par région
    from utils_region_filter import can_access_vehicle
    if not can_access_vehicle(vehicle_id):
        flash('Vous n\'avez pas accès à ce véhicule', 'error')
        return redirect(url_for('index'))
    
    vehicle = Vehicle.query.get_or_404(vehicle_id)
    document = VehicleDocument.query.filter_by(id=doc_id, vehicle_id=vehicle_id).first_or_404()
    
    if request.method == 'POST':
        document.document_type = request.form.get('document_type')
        document.document_number = request.form.get('document_number')
        issue_date = request.form.get('issue_date')
        expiry_date = request.form.get('expiry_date')
        document.notes = request.form.get('notes')
        
        if issue_date:
            document.issue_date = datetime.strptime(issue_date, '%Y-%m-%d').date()
        if expiry_date:
            document.expiry_date = datetime.strptime(expiry_date, '%Y-%m-%d').date()
        
        document.updated_at = datetime.now(UTC)
        db.session.commit()
        
        flash('Document modifié avec succès', 'success')
        return redirect(url_for('flotte.vehicle_documents', vehicle_id=vehicle_id))
    
    return render_template('flotte/document_form.html', vehicle=vehicle, document=document)

# =========================================================
# MAINTENANCES VÉHICULE
# =========================================================

@flotte_bp.route('/<int:vehicle_id>/maintenances')
@login_required
def vehicle_maintenances(vehicle_id):
    """Liste des maintenances d'un véhicule"""
    if not has_permission(current_user, 'vehicles.read'):
        flash('Vous n\'avez pas la permission d\'accéder à cette page', 'error')
        return redirect(url_for('index'))
    
    # Vérifier l'accès au véhicule par région
    from utils_region_filter import can_access_vehicle
    if not can_access_vehicle(vehicle_id):
        flash('Vous n\'avez pas accès à ce véhicule', 'error')
        return redirect(url_for('index'))
    
    # Paramètres de pagination
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    status_filter = request.args.get('status', '')
    
    vehicle = Vehicle.query.get_or_404(vehicle_id)
    
    # Requête de base avec filtres
    query = VehicleMaintenance.query.filter_by(vehicle_id=vehicle_id)\
        .options(joinedload(VehicleMaintenance.vehicle))
    
    # Filtre par statut
    if status_filter:
        query = query.filter_by(status=status_filter)
    
    # Pagination
    pagination = query.order_by(VehicleMaintenance.planned_date.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    maintenances = pagination.items
    
    # Récupérer le dernier relevé odomètre
    last_odometer = VehicleOdometer.query.filter_by(vehicle_id=vehicle_id)\
        .options(joinedload(VehicleOdometer.vehicle))\
        .order_by(VehicleOdometer.reading_date.desc()).first()
    current_km = last_odometer.odometer_km if last_odometer else None
    
    # Maintenances dues (sur TOUTES les maintenances, pas seulement la page)
    all_maintenances = VehicleMaintenance.query.filter_by(vehicle_id=vehicle_id, status='planned').all()
    due_maintenances = [m for m in all_maintenances 
                       if m.due_at_km and current_km and current_km >= m.due_at_km]
    
    # Statistiques globales
    stats = {
        'total': VehicleMaintenance.query.filter_by(vehicle_id=vehicle_id).count(),
        'planned': VehicleMaintenance.query.filter_by(vehicle_id=vehicle_id, status='planned').count(),
        'completed': VehicleMaintenance.query.filter_by(vehicle_id=vehicle_id, status='completed').count(),
        'cancelled': VehicleMaintenance.query.filter_by(vehicle_id=vehicle_id, status='cancelled').count(),
        'due': len(due_maintenances)
    }
    
    return render_template('flotte/vehicle_maintenances.html',
                         vehicle=vehicle,
                         maintenances=maintenances,
                         current_km=current_km,
                         due_maintenances=due_maintenances,
                         pagination=pagination,
                         status_filter=status_filter,
                         stats=stats)

@flotte_bp.route('/<int:vehicle_id>/maintenances/new', methods=['GET', 'POST'])
@login_required
def maintenance_new(vehicle_id):
    """Planifier une nouvelle maintenance"""
    if not has_permission(current_user, 'vehicles.update'):
        flash('Vous n\'avez pas la permission d\'ajouter une maintenance', 'error')
        return redirect(url_for('flotte.vehicle_maintenances', vehicle_id=vehicle_id))
    
    # Vérifier l'accès au véhicule par région
    from utils_region_filter import can_access_vehicle
    if not can_access_vehicle(vehicle_id):
        flash('Vous n\'avez pas accès à ce véhicule', 'error')
        return redirect(url_for('index'))
    
    vehicle = Vehicle.query.get_or_404(vehicle_id)
    
    if request.method == 'POST':
        maintenance_type = request.form.get('maintenance_type')
        planned_date = request.form.get('planned_date') or None
        due_at_km = request.form.get('due_at_km') or None
        cost_gnf = request.form.get('cost_gnf') or None
        notes = request.form.get('notes')
        
        if not maintenance_type:
            flash('Le type de maintenance est obligatoire', 'error')
            return render_template('flotte/maintenance_form.html', vehicle=vehicle)
        
        maintenance = VehicleMaintenance(
            vehicle_id=vehicle_id,
            maintenance_type=maintenance_type,
            status='planned',
            planned_date=datetime.strptime(planned_date, '%Y-%m-%d').date() if planned_date else None,
            due_at_km=int(due_at_km) if due_at_km else None,
            cost_gnf=Decimal(cost_gnf) if cost_gnf else None,
            notes=notes
        )
        db.session.add(maintenance)
        db.session.commit()
        
        flash(f'Maintenance "{maintenance_type}" planifiée avec succès', 'success')
        return redirect(url_for('flotte.vehicle_maintenances', vehicle_id=vehicle_id))
    
    return render_template('flotte/maintenance_form.html', vehicle=vehicle)

@flotte_bp.route('/<int:vehicle_id>/maintenances/<int:maint_id>/complete', methods=['POST'])
@login_required
def maintenance_complete(vehicle_id, maint_id):
    """Marquer une maintenance comme réalisée"""
    if not has_permission(current_user, 'vehicles.update'):
        flash('Vous n\'avez pas la permission de modifier cette maintenance', 'error')
        return redirect(url_for('flotte.vehicle_maintenances', vehicle_id=vehicle_id))
    
    # Vérifier l'accès au véhicule par région
    from utils_region_filter import can_access_vehicle
    if not can_access_vehicle(vehicle_id):
        flash('Vous n\'avez pas accès à ce véhicule', 'error')
        return redirect(url_for('index'))
    
    vehicle = Vehicle.query.get_or_404(vehicle_id)
    maintenance = VehicleMaintenance.query.filter_by(id=maint_id, vehicle_id=vehicle_id).first_or_404()
    
    completed_date = request.form.get('completed_date') or date.today()
    cost_gnf = request.form.get('cost_gnf') or maintenance.cost_gnf
    
    maintenance.status = 'completed'
    maintenance.completed_date = datetime.strptime(completed_date, '%Y-%m-%d').date() if isinstance(completed_date, str) else completed_date
    if cost_gnf:
        maintenance.cost_gnf = Decimal(cost_gnf)
    maintenance.updated_at = datetime.now(UTC)
    
    db.session.commit()
    
    flash('Maintenance marquée comme réalisée', 'success')
    return redirect(url_for('flotte.vehicle_maintenances', vehicle_id=vehicle_id))

# =========================================================
# ODOMÈTRE VÉHICULE
# =========================================================

@flotte_bp.route('/<int:vehicle_id>/odometer')
@login_required
def vehicle_odometer(vehicle_id):
    """Historique des relevés odomètre d'un véhicule"""
    # Le magasinier peut voir l'historique de l'odomètre pour le suivi des véhicules
    if not has_permission(current_user, 'vehicles.read') and not (current_user.role and current_user.role.code == 'warehouse'):
        flash('Vous n\'avez pas la permission d\'accéder à cette page', 'error')
        return redirect(url_for('index'))
    
    # Vérifier l'accès au véhicule par région
    from utils_region_filter import can_access_vehicle
    if not can_access_vehicle(vehicle_id):
        flash('Vous n\'avez pas accès à ce véhicule', 'error')
        return redirect(url_for('index'))
    
    # Paramètres de pagination
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 30, type=int)
    
    vehicle = Vehicle.query.get_or_404(vehicle_id)
    
    # Requête de base avec pagination
    query = VehicleOdometer.query.filter_by(vehicle_id=vehicle_id)\
        .options(joinedload(VehicleOdometer.vehicle))\
        .order_by(VehicleOdometer.reading_date.desc())
    
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    odometers = pagination.items
    
    # Récupérer le premier et dernier relevé pour calculer le total (tous les relevés)
    first_reading = VehicleOdometer.query.filter_by(vehicle_id=vehicle_id)\
        .order_by(VehicleOdometer.reading_date.asc()).first()
    last_reading = VehicleOdometer.query.filter_by(vehicle_id=vehicle_id)\
        .order_by(VehicleOdometer.reading_date.desc()).first()
    
    # Calculer les statistiques
    total_km = 0
    current_km = last_reading.odometer_km if last_reading else 0
    if first_reading and last_reading and first_reading.id != last_reading.id:
        total_km = last_reading.odometer_km - first_reading.odometer_km
    
    # Statistiques globales
    total_readings = VehicleOdometer.query.filter_by(vehicle_id=vehicle_id).count()
    
    return render_template('flotte/vehicle_odometer.html',
                         vehicle=vehicle,
                         odometers=odometers,
                         pagination=pagination,
                         total_km=total_km,
                         current_km=current_km,
                         total_readings=total_readings)

# =========================================================
# FICHE VÉHICULE COMPLÈTE
# =========================================================

@flotte_bp.route('/<int:vehicle_id>')
@login_required
def vehicle_detail(vehicle_id):
    """Fiche complète d'un véhicule avec tous les onglets"""
    if not has_permission(current_user, 'vehicles.read'):
        flash('Vous n\'avez pas la permission d\'accéder à cette page', 'error')
        return redirect(url_for('index'))
    
    # Vérifier l'accès au véhicule par région
    from utils_region_filter import can_access_vehicle
    if not can_access_vehicle(vehicle_id):
        flash('Vous n\'avez pas accès à ce véhicule', 'error')
        return redirect(url_for('index'))
    
    vehicle = Vehicle.query.get_or_404(vehicle_id)
    
    # Documents - Optimisation avec préchargement si nécessaire
    documents = VehicleDocument.query.filter_by(vehicle_id=vehicle_id)\
        .options(joinedload(VehicleDocument.vehicle))\
        .order_by(VehicleDocument.expiry_date.asc()).all()
    expired_docs = [d for d in documents if d.expiry_date and get_days_until_expiry(d.expiry_date) < 0]
    expiring_docs = [d for d in documents if d.expiry_date and 0 <= get_days_until_expiry(d.expiry_date) <= 15]
    
    # Maintenances - Optimisation avec préchargement
    maintenances = VehicleMaintenance.query.filter_by(vehicle_id=vehicle_id)\
        .options(joinedload(VehicleMaintenance.vehicle))\
        .order_by(VehicleMaintenance.planned_date.desc()).all()
    last_odometer = VehicleOdometer.query.filter_by(vehicle_id=vehicle_id)\
        .order_by(VehicleOdometer.reading_date.desc()).first()
    current_km = last_odometer.odometer_km if last_odometer else None
    due_maintenances = [m for m in maintenances 
                       if m.status == 'planned' and m.due_at_km 
                       and current_km and current_km >= m.due_at_km]
    
    # Odomètre - Optimisation avec préchargement
    odometers = VehicleOdometer.query.filter_by(vehicle_id=vehicle_id)\
        .options(joinedload(VehicleOdometer.vehicle))\
        .order_by(VehicleOdometer.reading_date.desc()).limit(10).all()
    total_km = 0
    if len(odometers) > 1:
        total_km = odometers[0].odometer_km - odometers[-1].odometer_km
    
    # Stock - Optimisation avec préchargement
    from models import VehicleStock
    vehicle_stocks = VehicleStock.query.filter_by(vehicle_id=vehicle_id)\
        .options(joinedload(VehicleStock.stock_item))\
        .all()
    # Vérifier si l'utilisateur peut voir les valeurs de stock
    can_view_values = can_view_stock_values(current_user)
    stock_value = sum(float(vs.quantity) * float(vs.stock_item.unit_price or 0) 
                     for vs in vehicle_stocks if vs.stock_item and vs.stock_item.unit_price) if can_view_values else 0
    
    # Mouvements de stock - Optimisation avec préchargement
    from models import StockMovement
    recent_movements = StockMovement.query.filter(
        (StockMovement.from_vehicle_id == vehicle_id) | (StockMovement.to_vehicle_id == vehicle_id)
    ).options(
        joinedload(StockMovement.from_vehicle),
        joinedload(StockMovement.to_vehicle),
        joinedload(StockMovement.stock_item)
    ).order_by(StockMovement.movement_date.desc()).limit(10).all()
    
    # Coûts (si table existe)
    costs = []
    total_costs = 0
    try:
        from models import VehicleCost
        costs = VehicleCost.query.filter_by(vehicle_id=vehicle_id)\
            .order_by(VehicleCost.cost_date.desc()).limit(10).all()
        total_costs = sum(float(c.amount) for c in costs) if costs else 0
    except (ImportError, AttributeError):
        # Table VehicleCost n'existe pas ou modèle non disponible
        costs = []
        total_costs = 0
    except Exception as e:
        # Autre erreur - logger mais continuer
        print(f"⚠️ Erreur lors de la récupération des coûts: {e}")
        costs = []
        total_costs = 0
    
    # Assignations
    assignments = VehicleAssignment.query.filter_by(vehicle_id=vehicle_id)\
        .order_by(VehicleAssignment.start_date.desc()).limit(5).all()
    current_assignment = next((a for a in assignments if a.is_active), None)
    
    # Statistiques
    stats = {
        'total_documents': len(documents),
        'expired_documents': len(expired_docs),
        'expiring_documents': len(expiring_docs),
        'total_maintenances': len(maintenances),
        'due_maintenances': len(due_maintenances),
        'completed_maintenances': len([m for m in maintenances if m.status == 'completed']),
        'total_odometer_readings': VehicleOdometer.query.filter_by(vehicle_id=vehicle_id).count(),
        'current_km': current_km,
        'stock_items_count': len(vehicle_stocks),
        'stock_value': stock_value,
        'recent_movements_count': len(recent_movements),
        'total_costs': total_costs
    }
    
    return render_template('flotte/vehicle_detail.html',
                         vehicle=vehicle,
                         documents=documents,
                         expired_docs=expired_docs,
                         expiring_docs=expiring_docs,
                         maintenances=maintenances,
                         due_maintenances=due_maintenances,
                         odometers=odometers,
                         total_km=total_km,
                         current_km=current_km,
                         vehicle_stocks=vehicle_stocks,
                         stock_value=stock_value,
                         recent_movements=recent_movements,
                         costs=costs,
                         assignments=assignments,
                         current_assignment=current_assignment,
                         stats=stats,
                         can_view_stock_values=can_view_values)

@flotte_bp.route('/<int:vehicle_id>/odometer/new', methods=['GET', 'POST'])
@login_required
def odometer_new(vehicle_id):
    """Ajouter un nouveau relevé odomètre"""
    # Le magasinier peut aussi ajouter des relevés odomètre pour le suivi des véhicules
    if not has_permission(current_user, 'vehicles.update') and not (current_user.role and current_user.role.code == 'warehouse'):
        flash('Vous n\'avez pas la permission d\'ajouter un relevé', 'error')
        return redirect(url_for('flotte.vehicle_odometer', vehicle_id=vehicle_id))
    
    # Vérifier l'accès au véhicule par région
    from utils_region_filter import can_access_vehicle
    if not can_access_vehicle(vehicle_id):
        flash('Vous n\'avez pas accès à ce véhicule', 'error')
        return redirect(url_for('index'))
    
    vehicle = Vehicle.query.get_or_404(vehicle_id)
    
    if request.method == 'POST':
        reading_date = request.form.get('reading_date') or date.today()
        odometer_km = int(request.form.get('odometer_km'))
        source = request.form.get('source', 'manual')
        notes = request.form.get('notes')
        
        if not odometer_km or odometer_km < 0:
            flash('Veuillez saisir un kilométrage valide', 'error')
            return render_template('flotte/odometer_form.html', vehicle=vehicle)
        
        # Vérifier la cohérence
        is_valid, last_km, error_msg = check_km_consistency(vehicle_id, odometer_km)
        if not is_valid:
            flash(error_msg, 'error')
            return render_template('flotte/odometer_form.html', vehicle=vehicle, last_km=last_km)
        
        odometer = VehicleOdometer(
            vehicle_id=vehicle_id,
            reading_date=datetime.strptime(reading_date, '%Y-%m-%d').date() if isinstance(reading_date, str) else reading_date,
            odometer_km=odometer_km,
            source=source,
            notes=notes
        )
        db.session.add(odometer)
        db.session.commit()
        
        flash(f'Relevé odomètre enregistré: {odometer_km} km', 'success')
        return redirect(url_for('flotte.vehicle_odometer', vehicle_id=vehicle_id))
    
    # Récupérer le dernier km pour affichage
    last_reading = VehicleOdometer.query.filter_by(vehicle_id=vehicle_id)\
        .order_by(VehicleOdometer.reading_date.desc()).first()
    last_km = last_reading.odometer_km if last_reading else 0
    
    return render_template('flotte/odometer_form.html', vehicle=vehicle, last_km=last_km)

# =========================================================
# HISTORIQUE DES CONDUCTEURS (ASSIGNATIONS)
# =========================================================

@flotte_bp.route('/<int:vehicle_id>/assignments')
@login_required
def vehicle_assignments(vehicle_id):
    """Historique des assignations d'un véhicule"""
    if not has_permission(current_user, 'vehicles.read'):
        flash('Vous n\'avez pas la permission d\'accéder à cette page', 'error')
        return redirect(url_for('index'))
    
    # Vérifier l'accès au véhicule par région
    from utils_region_filter import can_access_vehicle
    if not can_access_vehicle(vehicle_id):
        flash('Vous n\'avez pas accès à ce véhicule', 'error')
        return redirect(url_for('index'))
    
    vehicle = Vehicle.query.get_or_404(vehicle_id)
    assignments = VehicleAssignment.query.filter_by(vehicle_id=vehicle_id)\
        .order_by(VehicleAssignment.start_date.desc()).all()
    
    # Assignation actuelle
    current_assignment = next((a for a in assignments if a.is_active), None)
    
    # Statistiques
    total_assignments = len(assignments)
    active_assignments = len([a for a in assignments if a.is_active])
    
    return render_template('flotte/vehicle_assignments.html',
                         vehicle=vehicle,
                         assignments=assignments,
                         current_assignment=current_assignment,
                         total_assignments=total_assignments,
                         active_assignments=active_assignments,
                         today=date.today())

@flotte_bp.route('/<int:vehicle_id>/assignments/new', methods=['GET', 'POST'])
@login_required
def assignment_new(vehicle_id):
    """Créer une nouvelle assignation"""
    if not has_permission(current_user, 'vehicles.update'):
        flash('Vous n\'avez pas la permission de créer une assignation', 'error')
        return redirect(url_for('flotte.vehicle_assignments', vehicle_id=vehicle_id))
    
    # Vérifier l'accès au véhicule par région
    from utils_region_filter import can_access_vehicle
    if not can_access_vehicle(vehicle_id):
        flash('Vous n\'avez pas accès à ce véhicule', 'error')
        return redirect(url_for('index'))
    
    vehicle = Vehicle.query.get_or_404(vehicle_id)
    users = User.query.filter_by(is_active=True).all()
    
    if request.method == 'POST':
        user_id = request.form.get('user_id')
        start_date = request.form.get('start_date')
        reason = request.form.get('reason')
        notes = request.form.get('notes')
        
        if not user_id or not start_date:
            flash('Le conducteur et la date de début sont obligatoires', 'error')
            return render_template('flotte/assignment_form.html', vehicle=vehicle, users=users)
        
        start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
        
        # Vérifier s'il y a une assignation active
        active_assignment = VehicleAssignment.query.filter_by(
            vehicle_id=vehicle_id,
            end_date=None
        ).first()
        
        # Vérifier les chevauchements avec d'autres assignations
        overlapping_assignments = VehicleAssignment.query.filter(
            VehicleAssignment.vehicle_id == vehicle_id,
            VehicleAssignment.user_id == int(user_id),
            VehicleAssignment.start_date <= start_date_obj,
            db.or_(
                VehicleAssignment.end_date == None,
                VehicleAssignment.end_date >= start_date_obj
            )
        ).all()
        
        if overlapping_assignments:
            flash(f'Ce conducteur a déjà une assignation active pour cette période', 'error')
            return render_template('flotte/assignment_form.html', vehicle=vehicle, users=users, today=date.today())
        
        # Si nouvelle assignation, terminer l'ancienne
        if active_assignment and int(user_id) != active_assignment.user_id:
            active_assignment.end_date = start_date_obj - timedelta(days=1)
            active_assignment.reason = reason or "Changement de conducteur"
        
        # Créer la nouvelle assignation
        assignment = VehicleAssignment(
            vehicle_id=vehicle_id,
            user_id=int(user_id),
            start_date=start_date_obj,
            reason=reason,
            notes=notes,
            created_by_id=current_user.id
        )
        db.session.add(assignment)
        
        # Mettre à jour le conducteur actuel du véhicule
        vehicle.current_user_id = int(user_id)
        
        db.session.commit()
        
        flash(f'Assignation créée avec succès', 'success')
        return redirect(url_for('flotte.vehicle_assignments', vehicle_id=vehicle_id))
    
    return render_template('flotte/assignment_form.html', vehicle=vehicle, users=users, today=date.today())

@flotte_bp.route('/<int:vehicle_id>/assignments/<int:assignment_id>/end', methods=['POST'])
@login_required
def assignment_end(vehicle_id, assignment_id):
    """Terminer une assignation"""
    if not has_permission(current_user, 'vehicles.update'):
        flash('Vous n\'avez pas la permission de modifier cette assignation', 'error')
        return redirect(url_for('flotte.vehicle_assignments', vehicle_id=vehicle_id))
    
    # Vérifier l'accès au véhicule par région
    from utils_region_filter import can_access_vehicle
    if not can_access_vehicle(vehicle_id):
        flash('Vous n\'avez pas accès à ce véhicule', 'error')
        return redirect(url_for('index'))
    
    vehicle = Vehicle.query.get_or_404(vehicle_id)
    assignment = VehicleAssignment.query.filter_by(
        id=assignment_id,
        vehicle_id=vehicle_id
    ).first_or_404()
    
    end_date = request.form.get('end_date') or date.today()
    reason = request.form.get('reason', 'Fin d\'assignation')
    
    assignment.end_date = datetime.strptime(end_date, '%Y-%m-%d').date() if isinstance(end_date, str) else end_date
    assignment.reason = reason
    
    # Si c'était l'assignation active, retirer le conducteur du véhicule
    if vehicle.current_user_id == assignment.user_id:
        vehicle.current_user_id = None
    
    db.session.commit()
    
    flash('Assignation terminée avec succès', 'success')
    return redirect(url_for('flotte.vehicle_assignments', vehicle_id=vehicle_id))

@flotte_bp.route('/users/<int:user_id>/vehicles')
@login_required
def user_vehicles(user_id):
    """Véhicules assignés à un utilisateur"""
    if not has_permission(current_user, 'vehicles.read'):
        flash('Vous n\'avez pas la permission d\'accéder à cette page', 'error')
        return redirect(url_for('index'))
    
    user = User.query.get_or_404(user_id)
    
    # Vérifier l'accès : admin peut voir tous les utilisateurs, sinon même région
    from utils_region_filter import get_user_region_id
    user_region_id = get_user_region_id()
    if user_region_id is not None:  # Utilisateur non-admin
        if not hasattr(user, 'region_id') or user.region_id != user_region_id:
            flash('Vous n\'avez pas accès aux véhicules de cet utilisateur', 'error')
            return redirect(url_for('index'))
    
    # Assignations actives
    active_assignments = VehicleAssignment.query.filter_by(
        user_id=user_id,
        end_date=None
    ).order_by(VehicleAssignment.start_date.desc()).all()
    
    # Historique complet
    all_assignments = VehicleAssignment.query.filter_by(user_id=user_id)\
        .order_by(VehicleAssignment.start_date.desc()).all()
    
    # Statistiques
    total_vehicles = len(set(a.vehicle_id for a in all_assignments))
    current_vehicles = len(active_assignments)
    
    return render_template('flotte/user_vehicles.html',
                         user=user,
                         active_assignments=active_assignments,
                         all_assignments=all_assignments,
                         total_vehicles=total_vehicles,
                         current_vehicles=current_vehicles)

