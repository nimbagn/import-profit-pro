#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module Inventaires - Import Profit Pro
Gestion des sessions d'inventaire avec parsing piles et génération d'ajustements
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, make_response
from flask_login import login_required, current_user
from datetime import datetime, UTC, timedelta
from decimal import Decimal
from io import BytesIO
from models import (
    db, InventorySession, InventoryDetail, Depot, StockItem, 
    DepotStock, StockMovement, User
)
from sqlalchemy import or_, func, extract
from auth import has_permission
from utils import parse_pile_dimensions
from sqlalchemy.orm import joinedload

# Créer le blueprint
inventaires_bp = Blueprint('inventaires', __name__, url_prefix='/inventory')

# =========================================================
# SESSIONS D'INVENTAIRE
# =========================================================

@inventaires_bp.route('/sessions')
@login_required
def sessions_list():
    """Liste des sessions d'inventaire avec pagination et optimisations"""
    if not has_permission(current_user, 'inventory.read'):
        flash('Vous n\'avez pas la permission d\'accéder à cette page', 'error')
        return redirect(url_for('index'))
    
    # Paramètres de pagination
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    
    # Filtres
    search = request.args.get('search', '').strip()
    status_filter = request.args.get('status', '')
    depot_id = request.args.get('depot_id', type=int)
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    year_filter = request.args.get('year', type=int)
    
    # Construire la requête avec optimisation N+1
    query = InventorySession.query.options(
        joinedload(InventorySession.depot),
        joinedload(InventorySession.operator),
        joinedload(InventorySession.validator)
    )
    
    # Appliquer les filtres
    if search:
        query = query.join(Depot).outerjoin(User, InventorySession.operator_id == User.id).filter(
            or_(
                Depot.name.like(f'%{search}%'),
                User.username.like(f'%{search}%')
            )
        )
    
    if status_filter:
        query = query.filter(InventorySession.status == status_filter)
    
    if depot_id:
        query = query.filter(InventorySession.depot_id == depot_id)
    
    # Filtre par année (prioritaire sur date_from/date_to si spécifié)
    if year_filter:
        query = query.filter(
            extract('year', InventorySession.session_date) == year_filter
        )
    else:
        # Appliquer les filtres de date seulement si pas de filtre année
        if date_from:
            try:
                date_from_obj = datetime.strptime(date_from, '%Y-%m-%d')
                query = query.filter(InventorySession.session_date >= date_from_obj)
            except ValueError:
                pass
        
        if date_to:
            try:
                date_to_obj = datetime.strptime(date_to, '%Y-%m-%d') + timedelta(days=1)
                query = query.filter(InventorySession.session_date < date_to_obj)
            except ValueError:
                pass
    
    # Pagination
    pagination = query.order_by(InventorySession.session_date.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    sessions = pagination.items
    
    # Statistiques globales - Optimisation avec une seule requête
    stats_query = db.session.query(
        InventorySession.status,
        func.count(InventorySession.id).label('count')
    ).group_by(InventorySession.status).all()
    
    sessions_by_status = {status: count for status, count in stats_query}
    total_sessions = sum(sessions_by_status.values())
    
    # S'assurer que tous les statuts sont présents (même avec 0)
    for status in ['draft', 'in_progress', 'completed', 'validated']:
        if status not in sessions_by_status:
            sessions_by_status[status] = 0
    
    # Données pour filtres
    depots = Depot.query.filter_by(is_active=True).order_by(Depot.name).all()
    
    # Récupérer les années disponibles pour le sélecteur
    available_years = db.session.query(
        extract('year', InventorySession.session_date).label('year')
    ).distinct().order_by('year').all()
    available_years = [int(y.year) for y in available_years if y.year]
    
    # Année par défaut : année en cours si disponible, sinon dernière année disponible
    if not year_filter and available_years:
        current_year = datetime.now(UTC).year
        year_filter = current_year if current_year in available_years else available_years[-1]
    
    return render_template('inventaires/sessions_list.html', 
                         sessions=sessions,
                         pagination=pagination,
                         search=search,
                         status_filter=status_filter,
                         depot_id=depot_id,
                         date_from=date_from,
                         date_to=date_to,
                         year_filter=year_filter,
                         available_years=available_years,
                         per_page=per_page,
                         total_sessions=total_sessions,
                         sessions_by_status=sessions_by_status,
                         depots=depots)

@inventaires_bp.route('/sessions/by-year')
@login_required
def sessions_by_year():
    """Vue consolidée des sessions d'inventaire par année"""
    if not has_permission(current_user, 'inventory.read'):
        flash('Vous n\'avez pas la permission d\'accéder à cette page', 'error')
        return redirect(url_for('index'))
    
    # Récupérer toutes les années disponibles
    years_result = db.session.query(
        extract('year', InventorySession.session_date).label('year')
    ).distinct().order_by('year').all()
    
    available_years = [int(y.year) for y in years_result if y.year]
    
    if not available_years:
        flash('Aucune session d\'inventaire trouvée', 'info')
        return redirect(url_for('inventaires.sessions_list'))
    
    # Statistiques par année
    stats_by_year = []
    for year in available_years:
        sessions = InventorySession.query.options(
            joinedload(InventorySession.depot),
            joinedload(InventorySession.operator),
            joinedload(InventorySession.validator),
            joinedload(InventorySession.details).joinedload(InventoryDetail.stock_item)
        ).filter(
            extract('year', InventorySession.session_date) == year
        ).order_by(InventorySession.session_date.desc()).all()
        
        if not sessions:
            continue
        
        # Calculer les statistiques pour cette année
        total_sessions = len(sessions)
        total_items = sum(len(s.details) for s in sessions)
        
        # Calculer les totaux des écarts
        total_variances = Decimal('0')
        total_value_variances = Decimal('0')
        positive_count = 0
        negative_count = 0
        zero_count = 0
        
        for session in sessions:
            for detail in session.details:
                variance = detail.variance
                total_variances += variance
                
                if detail.stock_item:
                    price = getattr(detail.stock_item, 'purchase_price_gnf', Decimal('0'))
                    total_value_variances += variance * price
                
                if variance > 0:
                    positive_count += 1
                elif variance < 0:
                    negative_count += 1
                else:
                    zero_count += 1
        
        # Compter les sessions par statut
        sessions_by_status = {
            'draft': sum(1 for s in sessions if s.status == 'draft'),
            'in_progress': sum(1 for s in sessions if s.status == 'in_progress'),
            'completed': sum(1 for s in sessions if s.status == 'completed'),
            'validated': sum(1 for s in sessions if s.status == 'validated')
        }
        
        # Calculer le taux de précision
        precision_pct = (zero_count / total_items * 100) if total_items > 0 else 0
        
        stats_by_year.append({
            'year': year,
            'sessions': sessions,
            'total_sessions': total_sessions,
            'total_items': total_items,
            'total_variances': float(total_variances),
            'total_value_variances': float(total_value_variances),
            'positive_count': positive_count,
            'negative_count': negative_count,
            'zero_count': zero_count,
            'precision_pct': precision_pct,
            'sessions_by_status': sessions_by_status
        })
    
    # Trier par année décroissante
    stats_by_year.sort(key=lambda x: x['year'], reverse=True)
    
    return render_template('inventaires/sessions_by_year.html',
                         stats_by_year=stats_by_year)

@inventaires_bp.route('/sessions/new', methods=['GET', 'POST'])
@login_required
def session_new():
    """Créer une nouvelle session d'inventaire"""
    if not has_permission(current_user, 'inventory.create'):
        flash('Vous n\'avez pas la permission de créer une session', 'error')
        return redirect(url_for('inventaires.sessions_list'))
    
    # Charger les dépôts une seule fois (utilisé dans GET et POST en cas d'erreur)
    depots = Depot.query.filter_by(is_active=True).all()
    
    # Date par défaut pour le formulaire
    default_date = datetime.now(UTC).strftime('%Y-%m-%d')
    
    if request.method == 'POST':
        depot_id = request.form.get('depot_id')
        session_date = request.form.get('session_date') or datetime.now(UTC)
        notes = request.form.get('notes')
        
        if not depot_id:
            flash('Veuillez sélectionner un dépôt', 'error')
            return render_template('inventaires/session_form.html', depots=depots, default_date=default_date)
        
        try:
            depot_id = int(depot_id)
        except (ValueError, TypeError):
            flash('Dépôt invalide', 'error')
            return render_template('inventaires/session_form.html', depots=depots, default_date=default_date)
        
        # Parser la date
        if isinstance(session_date, str):
            try:
                session_date = datetime.strptime(session_date, '%Y-%m-%d')
            except ValueError:
                flash('Format de date invalide', 'error')
                return render_template('inventaires/session_form.html', depots=depots, default_date=default_date)
        
        session = InventorySession(
            depot_id=depot_id,
            session_date=session_date,
            operator_id=current_user.id,
            status='draft',
            notes=notes
        )
        db.session.add(session)
        db.session.commit()
        
        flash(f'Session d\'inventaire créée avec succès', 'success')
        return redirect(url_for('inventaires.session_detail', id=session.id))
    
    return render_template('inventaires/session_form.html', depots=depots, default_date=default_date)

@inventaires_bp.route('/sessions/<int:id>')
@login_required
def session_detail(id):
    """Détails d'une session d'inventaire avec optimisations"""
    if not has_permission(current_user, 'inventory.read'):
        flash('Vous n\'avez pas la permission d\'accéder à cette page', 'error')
        return redirect(url_for('inventaires.sessions_list'))
    
    # Optimisation N+1 : charger toutes les relations en une seule requête
    session = InventorySession.query.options(
        joinedload(InventorySession.depot),
        joinedload(InventorySession.operator),
        joinedload(InventorySession.validator),
        joinedload(InventorySession.details).joinedload(InventoryDetail.stock_item)
    ).get_or_404(id)
    
    # Paramètres de pagination et filtres
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    search = request.args.get('search', '').strip()
    variance_filter = request.args.get('variance_filter', '')  # 'positive', 'negative', 'zero', ''
    
    # Construire la requête des détails avec filtres
    details_query = InventoryDetail.query.filter_by(session_id=id).options(
        joinedload(InventoryDetail.stock_item)
    )
    
    # Appliquer les filtres
    if search:
        details_query = details_query.join(StockItem).filter(
            or_(
                StockItem.sku.like(f'%{search}%'),
                StockItem.name.like(f'%{search}%')
            )
        )
    
    if variance_filter == 'positive':
        details_query = details_query.filter(InventoryDetail.variance > 0)
    elif variance_filter == 'negative':
        details_query = details_query.filter(InventoryDetail.variance < 0)
    elif variance_filter == 'zero':
        details_query = details_query.filter(InventoryDetail.variance == 0)
    
    # Pagination
    pagination = details_query.order_by(InventoryDetail.stock_item_id).paginate(
        page=page, per_page=per_page, error_out=False
    )
    details = pagination.items
    
    # Calculer les statistiques globales (tous les détails, pas seulement ceux affichés)
    all_details = session.details
    total_items = len(all_details)
    
    # Calculer les totaux
    total_variances = sum(float(d.variance) for d in all_details)
    total_value_variances = sum(
        float(d.variance * getattr(d.stock_item, 'purchase_price_gnf', 0)) 
        for d in all_details if d.stock_item
    )
    
    # Préparer les détails avec valeur d'écart calculée pour le template
    details_with_value = []
    for detail in details:
        stock_item = detail.stock_item
        value_variance = 0
        has_price = False
        if stock_item:
            price = getattr(stock_item, 'purchase_price_gnf', None)
            if price is not None:
                value_variance = float(detail.variance * price)
                has_price = True
        details_with_value.append({
            'detail': detail,
            'value_variance': value_variance,
            'has_price': has_price
        })
    
    # Statistiques détaillées
    positive_variances = [d for d in all_details if d.variance > 0]
    negative_variances = [d for d in all_details if d.variance < 0]
    zero_variances = [d for d in all_details if d.variance == 0]
    
    positive_count = len(positive_variances)
    negative_count = len(negative_variances)
    zero_count = len(zero_variances)
    
    positive_total = sum(float(d.variance) for d in positive_variances)
    negative_total = sum(float(d.variance) for d in negative_variances)
    
    # Calculer le pourcentage de précision
    precision_pct = (zero_count / total_items * 100) if total_items > 0 else 0
    
    return render_template('inventaires/session_detail.html', 
                         session=session,
                         details=details,
                         details_with_value=details_with_value,
                         pagination=pagination,
                         total_items=total_items,
                         total_variances=total_variances,
                         total_value_variances=total_value_variances,
                         positive_count=positive_count,
                         negative_count=negative_count,
                         zero_count=zero_count,
                         positive_total=positive_total,
                         negative_total=negative_total,
                         precision_pct=precision_pct,
                         search=search,
                         variance_filter=variance_filter,
                         per_page=per_page)

@inventaires_bp.route('/sessions/<int:id>/details', methods=['GET', 'POST'])
@login_required
def session_detail_add(id):
    """Ajouter ou modifier un détail d'inventaire"""
    if not has_permission(current_user, 'inventory.update'):
        flash('Vous n\'avez pas la permission de modifier cette session', 'error')
        return redirect(url_for('inventaires.session_detail', id=id))
    
    session = InventorySession.query.get_or_404(id)
    
    if session.status == 'validated':
        flash('Cette session est déjà validée et ne peut plus être modifiée', 'error')
        return redirect(url_for('inventaires.session_detail', id=id))
    
    if request.method == 'POST':
        stock_item_id = request.form.get('stock_item_id')
        counting_method = request.form.get('counting_method', 'quantity')  # Par défaut: quantity
        counted_quantity_str = request.form.get('counted_quantity', '').strip()
        pile_dimensions = request.form.get('pile_dimensions', '').strip()
        reason = request.form.get('reason', '').strip()
        
        # Validation de stock_item_id
        if not stock_item_id:
            flash('Veuillez sélectionner un article', 'error')
            stock_items = StockItem.query.filter_by(is_active=True).order_by(StockItem.name).all()
            return render_template('inventaires/detail_form.html', session=session, stock_items=stock_items)
        
        try:
            stock_item_id = int(stock_item_id)
        except (ValueError, TypeError):
            flash('Article invalide', 'error')
            stock_items = StockItem.query.filter_by(is_active=True).order_by(StockItem.name).all()
            return render_template('inventaires/detail_form.html', session=session, stock_items=stock_items)
        
        # Vérifier que l'article existe
        stock_item = StockItem.query.get(stock_item_id)
        if not stock_item:
            flash('Article introuvable', 'error')
            stock_items = StockItem.query.filter_by(is_active=True).order_by(StockItem.name).all()
            return render_template('inventaires/detail_form.html', session=session, stock_items=stock_items)
        
        # Validation selon la méthode sélectionnée
        counted_quantity = Decimal('0')
        
        if counting_method == 'piles':
            # Méthode "Dimensions Piles" sélectionnée
            if not pile_dimensions:
                flash('Veuillez saisir les dimensions des piles', 'error')
                stock_items = StockItem.query.filter_by(is_active=True).order_by(StockItem.name).all()
                return render_template('inventaires/detail_form.html', session=session, stock_items=stock_items)
            
            try:
                calculated_qty = parse_pile_dimensions(pile_dimensions)
                if calculated_qty > 0:
                    counted_quantity = Decimal(str(calculated_qty))
                else:
                    flash('Les dimensions de pile sont invalides ou donnent une quantité nulle', 'error')
                    stock_items = StockItem.query.filter_by(is_active=True).order_by(StockItem.name).all()
                    return render_template('inventaires/detail_form.html', session=session, stock_items=stock_items)
            except Exception as e:
                flash(f'Erreur lors du calcul des dimensions de pile: {str(e)}', 'error')
                stock_items = StockItem.query.filter_by(is_active=True).order_by(StockItem.name).all()
                return render_template('inventaires/detail_form.html', session=session, stock_items=stock_items)
        
        else:
            # Méthode "Quantité Comptée" sélectionnée (par défaut)
            if not counted_quantity_str:
                flash('Veuillez saisir une quantité comptée', 'error')
                stock_items = StockItem.query.filter_by(is_active=True).order_by(StockItem.name).all()
                return render_template('inventaires/detail_form.html', session=session, stock_items=stock_items)
            
            try:
                counted_quantity = Decimal(counted_quantity_str)
            except (ValueError, TypeError):
                flash('Quantité invalide. Veuillez saisir un nombre valide', 'error')
                stock_items = StockItem.query.filter_by(is_active=True).order_by(StockItem.name).all()
                return render_template('inventaires/detail_form.html', session=session, stock_items=stock_items)
        
        # Validation finale : la quantité doit être >= 0
        if counted_quantity < 0:
            flash('La quantité ne peut pas être négative', 'error')
            stock_items = StockItem.query.filter_by(is_active=True).order_by(StockItem.name).all()
            return render_template('inventaires/detail_form.html', session=session, stock_items=stock_items)
        
        # Si la méthode "piles" est utilisée, s'assurer que pile_dimensions est conservé
        # Sinon, le vider pour éviter les incohérences
        if counting_method != 'piles':
            pile_dimensions = ''
        
        # Récupérer le stock système
        depot_stock = DepotStock.query.filter_by(
            depot_id=session.depot_id,
            stock_item_id=stock_item_id
        ).first()
        
        if not depot_stock:
            # Si le stock n'existe pas dans le dépôt, créer un enregistrement avec quantité 0
            system_quantity = Decimal('0')
        else:
            system_quantity = depot_stock.quantity if depot_stock.quantity else Decimal('0')
        
        # Calculer l'écart : ÉCART = stock actuel - (QUANTITÉ COMPTÉE + PILE)
        # La quantité comptée inclut déjà la pile si elle a été calculée
        variance = system_quantity - counted_quantity
        
        # Vérifier si le détail existe déjà
        detail = InventoryDetail.query.filter_by(
            session_id=id,
            stock_item_id=stock_item_id
        ).first()
        
        if detail:
            # Mettre à jour
            detail.counted_quantity = counted_quantity
            detail.pile_dimensions = pile_dimensions
            detail.variance = variance
            detail.reason = reason
        else:
            # Créer nouveau
            detail = InventoryDetail(
                session_id=id,
                stock_item_id=stock_item_id,
                system_quantity=system_quantity,
                counted_quantity=counted_quantity,
                pile_dimensions=pile_dimensions,
                variance=variance,
                reason=reason
            )
            db.session.add(detail)
        
        # Mettre à jour le statut de la session
        if session.status == 'draft':
            session.status = 'in_progress'
        
        db.session.commit()
        
        flash(f'Détail d\'inventaire enregistré avec succès', 'success')
        return redirect(url_for('inventaires.session_detail', id=id))
    
    stock_items = StockItem.query.filter_by(is_active=True).order_by(StockItem.name).all()
    return render_template('inventaires/detail_form.html', session=session, stock_items=stock_items)

@inventaires_bp.route('/sessions/<int:id>/validate', methods=['POST'])
@login_required
def session_validate(id):
    """Valider une session d'inventaire et générer les ajustements"""
    if not has_permission(current_user, 'inventory.validate'):
        flash('Vous n\'avez pas la permission de valider cette session', 'error')
        return redirect(url_for('inventaires.session_detail', id=id))
    
    session = InventorySession.query.options(
        joinedload(InventorySession.details).joinedload(InventoryDetail.stock_item)
    ).get_or_404(id)
    
    if session.status == 'validated':
        flash('Cette session est déjà validée', 'error')
        return redirect(url_for('inventaires.session_detail', id=id))
    
    if not session.details:
        flash('Aucun détail d\'inventaire à valider', 'error')
        return redirect(url_for('inventaires.session_detail', id=id))
    
    try:
        # Générer les ajustements pour chaque écart
        movements_created = 0
        for detail in session.details:
            if detail.variance != 0:
                # Récupérer ou créer le stock du dépôt
                depot_stock = DepotStock.query.filter_by(
                    depot_id=session.depot_id,
                    stock_item_id=detail.stock_item_id
                ).first()
                
                if not depot_stock:
                    depot_stock = DepotStock(
                        depot_id=session.depot_id,
                        stock_item_id=detail.stock_item_id,
                        quantity=Decimal('0')
                    )
                    db.session.add(depot_stock)
                
                # Calculer la quantité d'ajustement nécessaire
                # La variance = système - compté
                # Pour ajuster : nouveau_stock = compté
                # Donc ajustement = compté - système = -variance
                adjustment_quantity = detail.counted_quantity - depot_stock.quantity
                
                # Créer un mouvement d'ajustement avec la quantité d'ajustement
                movement = StockMovement(
                    movement_type='adjustment',  # Utiliser 'adjustment' au lieu de 'inventory'
                    stock_item_id=detail.stock_item_id,
                    quantity=adjustment_quantity,  # Quantité d'ajustement (peut être positive ou négative)
                    user_id=current_user.id,
                    to_depot_id=session.depot_id,
                    reason=f"Inventaire session {session.id}: {detail.reason or 'Ajustement suite inventaire'}",
                    inventory_session_id=session.id
                )
                db.session.add(movement)
                movements_created += 1
                
                # Mettre à jour le stock avec la quantité comptée
                depot_stock.quantity = detail.counted_quantity
        
        # Marquer la session comme validée
        session.status = 'validated'
        session.validated_at = datetime.now(UTC)
        session.validated_by_id = current_user.id
        
        db.session.commit()
        
        flash(f'Session d\'inventaire validée avec succès. {movements_created} ajustement(s) généré(s).', 'success')
        return redirect(url_for('inventaires.session_detail', id=id))
        
    except Exception as e:
        db.session.rollback()
        import traceback
        traceback.print_exc()
        flash(f'Erreur lors de la validation: {str(e)}', 'error')
        return redirect(url_for('inventaires.session_detail', id=id))

@inventaires_bp.route('/sessions/<int:id>/complete', methods=['POST'])
@login_required
def session_complete(id):
    """Marquer une session comme complétée"""
    if not has_permission(current_user, 'inventory.update'):
        flash('Vous n\'avez pas la permission de modifier cette session', 'error')
        return redirect(url_for('inventaires.session_detail', id=id))
    
    session = InventorySession.query.get_or_404(id)
    
    if session.status == 'validated':
        flash('Cette session est déjà validée', 'error')
        return redirect(url_for('inventaires.session_detail', id=id))
    
    session.status = 'completed'
    db.session.commit()
    
    flash('Session marquée comme complétée', 'success')
    return redirect(url_for('inventaires.session_detail', id=id))

# =========================================================
# EXPORTS
# =========================================================

@inventaires_bp.route('/sessions/<int:id>/export/excel')
@login_required
def session_export_excel(id):
    """Export Excel des détails d'une session d'inventaire"""
    if not has_permission(current_user, 'inventory.read'):
        flash('Vous n\'avez pas la permission d\'exporter les données', 'error')
        return redirect(url_for('inventaires.session_detail', id=id))
    
    session = InventorySession.query.options(
        joinedload(InventorySession.depot),
        joinedload(InventorySession.operator),
        joinedload(InventorySession.validator),
        joinedload(InventorySession.details).joinedload(InventoryDetail.stock_item)
    ).get_or_404(id)
    
    try:
        import pandas as pd
        
        # Préparer les données
        data = []
        for detail in session.details:
            stock_item = detail.stock_item
            value_variance = float(detail.variance * getattr(stock_item, 'purchase_price_gnf', 0)) if stock_item else 0
            
            data.append({
                'SKU': stock_item.sku if stock_item else '',
                'Article': stock_item.name if stock_item else '',
                'Quantité Système': float(detail.system_quantity),
                'Quantité Comptée': float(detail.counted_quantity),
                'Écart': float(detail.variance),
                'Type Écart': 'Surplus' if detail.variance > 0 else 'Manquant' if detail.variance < 0 else 'Conforme',
                'Valeur Écart (GNF)': value_variance,
                'Prix Unitaire (GNF)': float(getattr(stock_item, 'purchase_price_gnf', 0)) if stock_item else 0,
                'Pile': detail.pile_dimensions or '',
                'Raison': detail.reason or ''
            })
        
        # Créer le DataFrame
        df = pd.DataFrame(data)
        
        # Calculer les totaux
        total_items = len(df)
        total_system = df['Quantité Système'].sum()
        total_counted = df['Quantité Comptée'].sum()
        total_variance = df['Écart'].sum()
        total_value_variance = df['Valeur Écart (GNF)'].sum()
        
        # Ajouter une ligne de totaux
        if len(df) > 0:
            total_row = pd.DataFrame([{
                'SKU': 'TOTAL',
                'Article': '',
                'Quantité Système': total_system,
                'Quantité Comptée': total_counted,
                'Écart': total_variance,
                'Type Écart': '',
                'Valeur Écart (GNF)': total_value_variance,
                'Prix Unitaire (GNF)': '',
                'Pile': '',
                'Raison': ''
            }])
            df = pd.concat([df, total_row], ignore_index=True)
        
        # Créer le fichier Excel
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # Feuille 1 : Détails
            df.to_excel(writer, sheet_name='Détails Inventaire', index=False)
            
            # Feuille 2 : Résumé
            summary_data = {
                'Information': [
                    'ID Session',
                    'Date',
                    'Dépôt',
                    'Opérateur',
                    'Statut',
                    'Validé par',
                    'Date validation',
                    'Total Articles',
                    'Quantité Système Totale',
                    'Quantité Comptée Totale',
                    'Écart Total',
                    'Valeur Écart Totale (GNF)',
                    'Précision (%)'
                ],
                'Valeur': [
                    session.id,
                    session.session_date.strftime('%d/%m/%Y %H:%M') if session.session_date else '',
                    session.depot.name if session.depot else '',
                    session.operator.username if session.operator else '',
                    session.status.replace('_', ' ').title(),
                    session.validator.username if session.validator else '',
                    session.validated_at.strftime('%d/%m/%Y %H:%M') if session.validated_at else '',
                    total_items,
                    total_system,
                    total_counted,
                    total_variance,
                    total_value_variance,
                    f"{(len([d for d in session.details if d.variance == 0]) / total_items * 100) if total_items > 0 else 0:.2f}%"
                ]
            }
            summary_df = pd.DataFrame(summary_data)
            summary_df.to_excel(writer, sheet_name='Résumé', index=False)
            
            # Formater les colonnes
            for sheet_name in writer.sheets:
                worksheet = writer.sheets[sheet_name]
                for idx, col in enumerate(df.columns if sheet_name == 'Détails Inventaire' else summary_df.columns, 1):
                    max_length = max(
                        (df[col].astype(str).map(len).max() if sheet_name == 'Détails Inventaire' else summary_df[col].astype(str).map(len).max()),
                        len(str(col))
                    )
                    worksheet.column_dimensions[chr(64 + idx)].width = min(max_length + 2, 50)
        
        output.seek(0)
        filename = f'inventaire_session_{session.id}_{datetime.now(UTC).strftime("%Y%m%d_%H%M%S")}.xlsx'
        
        response = make_response(output.getvalue())
        response.headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        flash(f'Erreur lors de l\'export Excel: {str(e)}', 'error')
        return redirect(url_for('inventaires.session_detail', id=id))

@inventaires_bp.route('/sessions/export/excel')
@login_required
def sessions_export_excel():
    """Export Excel de la liste des sessions d'inventaire avec filtres appliqués"""
    if not has_permission(current_user, 'inventory.read'):
        flash('Vous n\'avez pas la permission d\'exporter les données', 'error')
        return redirect(url_for('inventaires.sessions_list'))
    
    try:
        import pandas as pd
        
        # Récupérer les mêmes filtres que sessions_list
        search = request.args.get('search', '').strip()
        status_filter = request.args.get('status', '')
        depot_id = request.args.get('depot_id', type=int)
        date_from = request.args.get('date_from', '')
        date_to = request.args.get('date_to', '')
        year_filter = request.args.get('year', type=int)
        
        # Construire la requête avec optimisation N+1
        query = InventorySession.query.options(
            joinedload(InventorySession.depot),
            joinedload(InventorySession.operator),
            joinedload(InventorySession.validator)
        )
        
        # Appliquer les filtres (même logique que sessions_list)
        if search:
            query = query.join(Depot).outerjoin(User, InventorySession.operator_id == User.id).filter(
                or_(
                    Depot.name.like(f'%{search}%'),
                    User.username.like(f'%{search}%')
                )
            )
        
        if status_filter:
            query = query.filter(InventorySession.status == status_filter)
        
        if depot_id:
            query = query.filter(InventorySession.depot_id == depot_id)
        
        # Filtre par année (prioritaire sur date_from/date_to si spécifié)
        if year_filter:
            query = query.filter(
                extract('year', InventorySession.session_date) == year_filter
            )
        else:
            # Appliquer les filtres de date seulement si pas de filtre année
            if date_from:
                try:
                    date_from_obj = datetime.strptime(date_from, '%Y-%m-%d')
                    query = query.filter(InventorySession.session_date >= date_from_obj)
                except ValueError:
                    pass
            
            if date_to:
                try:
                    date_to_obj = datetime.strptime(date_to, '%Y-%m-%d') + timedelta(days=1)
                    query = query.filter(InventorySession.session_date < date_to_obj)
                except ValueError:
                    pass
        
        # Récupérer toutes les sessions (sans pagination pour l'export)
        sessions = query.order_by(InventorySession.session_date.desc()).all()
        
        # Préparer les données
        data = []
        for session in sessions:
            # Compter les détails
            details_count = len(session.details) if session.details else 0
            
            # Calculer les totaux des écarts
            total_variances = sum(float(d.variance) for d in session.details) if session.details else 0
            total_value_variances = sum(
                float(d.variance * getattr(d.stock_item, 'purchase_price_gnf', 0)) 
                for d in session.details 
                if d.stock_item
            ) if session.details else 0
            
            data.append({
                'ID': session.id,
                'Date': session.session_date.strftime('%d/%m/%Y %H:%M') if session.session_date else '',
                'Dépôt': session.depot.name if session.depot else '',
                'Opérateur': session.operator.username if session.operator else '',
                'Statut': session.status.replace('_', ' ').title(),
                'Articles': details_count,
                'Écart Total': total_variances,
                'Valeur Écart (GNF)': total_value_variances,
                'Validé par': session.validator.username if session.validator else '',
                'Date Validation': session.validated_at.strftime('%d/%m/%Y %H:%M') if session.validated_at else '',
                'Notes': session.notes or ''
            })
        
        # Créer le DataFrame
        df = pd.DataFrame(data)
        
        # Ajouter une ligne de totaux
        if len(df) > 0:
            total_row = pd.DataFrame([{
                'ID': 'TOTAL',
                'Date': '',
                'Dépôt': '',
                'Opérateur': '',
                'Statut': '',
                'Articles': df['Articles'].sum(),
                'Écart Total': df['Écart Total'].sum(),
                'Valeur Écart (GNF)': df['Valeur Écart (GNF)'].sum(),
                'Validé par': '',
                'Date Validation': '',
                'Notes': ''
            }])
            df = pd.concat([df, total_row], ignore_index=True)
        
        # Créer le fichier Excel
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Sessions Inventaire', index=False)
            
            # Formater les colonnes
            worksheet = writer.sheets['Sessions Inventaire']
            for idx, col in enumerate(df.columns, 1):
                max_length = max(
                    df[col].astype(str).map(len).max(),
                    len(str(col))
                )
                worksheet.column_dimensions[chr(64 + idx)].width = min(max_length + 2, 40)
        
        output.seek(0)
        filename = f'sessions_inventaire_{datetime.now(UTC).strftime("%Y%m%d_%H%M%S")}.xlsx'
        
        response = make_response(output.getvalue())
        response.headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        flash(f'Erreur lors de l\'export Excel: {str(e)}', 'error')
        return redirect(url_for('inventaires.sessions_list'))

# =========================================================
# API ENDPOINTS
# =========================================================

@inventaires_bp.route('/api/depot-stock')
@login_required
def api_depot_stock():
    """API pour obtenir la quantité système d'un article dans un dépôt"""
    if not has_permission(current_user, 'inventory.read'):
        return jsonify({'error': 'Permission refusée'}), 403
    
    depot_id = request.args.get('depot_id', type=int)
    stock_item_id = request.args.get('stock_item_id', type=int)
    
    if not depot_id or not stock_item_id:
        return jsonify({'error': 'depot_id et stock_item_id sont requis'}), 400
    
    depot_stock = DepotStock.query.filter_by(
        depot_id=depot_id,
        stock_item_id=stock_item_id
    ).first()
    
    quantity = float(depot_stock.quantity) if depot_stock and depot_stock.quantity else 0.0
    
    return jsonify({
        'depot_id': depot_id,
        'stock_item_id': stock_item_id,
        'quantity': quantity
    })

@inventaires_bp.route('/sessions/<int:id>/details/<int:detail_id>/edit', methods=['GET', 'POST'])
@login_required
def session_detail_edit(id, detail_id):
    """Modifier un détail d'inventaire existant"""
    if not has_permission(current_user, 'inventory.update'):
        flash('Vous n\'avez pas la permission de modifier cette session', 'error')
        return redirect(url_for('inventaires.session_detail', id=id))
    
    session = InventorySession.query.get_or_404(id)
    detail = InventoryDetail.query.get_or_404(detail_id)
    
    if detail.session_id != id:
        flash('Ce détail n\'appartient pas à cette session', 'error')
        return redirect(url_for('inventaires.session_detail', id=id))
    
    if session.status == 'validated':
        flash('Cette session est déjà validée et ne peut plus être modifiée', 'error')
        return redirect(url_for('inventaires.session_detail', id=id))
    
    if request.method == 'POST':
        counting_method = request.form.get('counting_method', 'quantity')  # Par défaut: quantity
        counted_quantity_str = request.form.get('counted_quantity', '').strip()
        pile_dimensions = request.form.get('pile_dimensions', '').strip()
        reason = request.form.get('reason', '').strip()
        
        # Validation selon la méthode sélectionnée
        counted_quantity = Decimal('0')
        
        if counting_method == 'piles':
            # Méthode "Dimensions Piles" sélectionnée
            if not pile_dimensions:
                flash('Veuillez saisir les dimensions des piles', 'error')
                stock_items = StockItem.query.filter_by(is_active=True).order_by(StockItem.name).all()
                return render_template('inventaires/detail_form.html', session=session, stock_items=stock_items, detail=detail)
            
            try:
                calculated_qty = parse_pile_dimensions(pile_dimensions)
                if calculated_qty > 0:
                    counted_quantity = Decimal(str(calculated_qty))
                else:
                    flash('Les dimensions de pile sont invalides ou donnent une quantité nulle', 'error')
                    stock_items = StockItem.query.filter_by(is_active=True).order_by(StockItem.name).all()
                    return render_template('inventaires/detail_form.html', session=session, stock_items=stock_items, detail=detail)
            except Exception as e:
                flash(f'Erreur lors du calcul des dimensions de pile: {str(e)}', 'error')
                stock_items = StockItem.query.filter_by(is_active=True).order_by(StockItem.name).all()
                return render_template('inventaires/detail_form.html', session=session, stock_items=stock_items, detail=detail)
        
        else:
            # Méthode "Quantité Comptée" sélectionnée (par défaut)
            if not counted_quantity_str:
                flash('Veuillez saisir une quantité comptée', 'error')
                stock_items = StockItem.query.filter_by(is_active=True).order_by(StockItem.name).all()
                return render_template('inventaires/detail_form.html', session=session, stock_items=stock_items, detail=detail)
            
            try:
                counted_quantity = Decimal(counted_quantity_str)
            except (ValueError, TypeError):
                flash('Quantité invalide. Veuillez saisir un nombre valide', 'error')
                stock_items = StockItem.query.filter_by(is_active=True).order_by(StockItem.name).all()
                return render_template('inventaires/detail_form.html', session=session, stock_items=stock_items, detail=detail)
        
        # Validation finale : la quantité doit être >= 0
        if counted_quantity < 0:
            flash('La quantité ne peut pas être négative', 'error')
            stock_items = StockItem.query.filter_by(is_active=True).order_by(StockItem.name).all()
            return render_template('inventaires/detail_form.html', session=session, stock_items=stock_items, detail=detail)
        
        # Si la méthode "piles" est utilisée, s'assurer que pile_dimensions est conservé
        # Sinon, le vider pour éviter les incohérences
        if counting_method != 'piles':
            pile_dimensions = ''
        
        # Recalculer l'écart avec la quantité système actuelle
        depot_stock = DepotStock.query.filter_by(
            depot_id=session.depot_id,
            stock_item_id=detail.stock_item_id
        ).first()
        
        system_quantity = depot_stock.quantity if depot_stock and depot_stock.quantity else Decimal('0')
        variance = system_quantity - counted_quantity
        
        # Mettre à jour le détail
        detail.counted_quantity = counted_quantity
        detail.pile_dimensions = pile_dimensions
        detail.variance = variance
        detail.reason = reason
        
        db.session.commit()
        
        flash('Détail d\'inventaire modifié avec succès', 'success')
        return redirect(url_for('inventaires.session_detail', id=id))
    
    stock_items = StockItem.query.filter_by(is_active=True).order_by(StockItem.name).all()
    return render_template('inventaires/detail_form.html', session=session, stock_items=stock_items, detail=detail)

@inventaires_bp.route('/sessions/<int:id>/details/<int:detail_id>/delete', methods=['POST'])
@login_required
def session_detail_delete(id, detail_id):
    """Supprimer un détail d'inventaire"""
    if not has_permission(current_user, 'inventory.update'):
        flash('Vous n\'avez pas la permission de modifier cette session', 'error')
        return redirect(url_for('inventaires.session_detail', id=id))
    
    session = InventorySession.query.get_or_404(id)
    detail = InventoryDetail.query.get_or_404(detail_id)
    
    if detail.session_id != id:
        flash('Ce détail n\'appartient pas à cette session', 'error')
        return redirect(url_for('inventaires.session_detail', id=id))
    
    if session.status == 'validated':
        flash('Cette session est déjà validée et ne peut plus être modifiée', 'error')
        return redirect(url_for('inventaires.session_detail', id=id))
    
    stock_item_name = detail.stock_item.name if detail.stock_item else 'Article'
    db.session.delete(detail)
    db.session.commit()
    
    flash(f'Détail "{stock_item_name}" supprimé avec succès', 'success')
    return redirect(url_for('inventaires.session_detail', id=id))

