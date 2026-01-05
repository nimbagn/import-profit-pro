#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module Gestion des Commandes Commerciales - Import Profit Pro
Système de commandes avec validation hiérarchique
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from datetime import datetime, UTC, timedelta
from decimal import Decimal, InvalidOperation
from models import (
    db, CommercialOrder, CommercialOrderClient, CommercialOrderItem,
    StockItem, User, Region, Depot, Vehicle, StockOutgoing, StockOutgoingDetail,
    DepotStock, VehicleStock, StockMovement, PriceList, PriceListItem, Article
)
from auth import has_permission
from sqlalchemy.orm import joinedload
from sqlalchemy import or_, and_
from utils_region_filter import filter_commercial_orders_by_region, get_user_region_id, get_user_accessible_regions

# Créer le blueprint
orders_bp = Blueprint('orders', __name__, url_prefix='/orders')

def generate_order_reference():
    """Génère une référence unique pour une commande"""
    import time
    date_str = datetime.now().strftime('%Y%m%d')
    prefix = 'CMD'
    
    # Chercher la dernière commande du jour
    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    last_order = CommercialOrder.query.filter(
        CommercialOrder.reference.like(f'{prefix}-{date_str}-%'),
        CommercialOrder.created_at >= today_start
    ).order_by(CommercialOrder.id.desc()).first()
    
    if last_order and last_order.reference:
        try:
            last_num = int(last_order.reference.split('-')[-1])
            next_num = last_num + 1
        except (ValueError, IndexError):
            next_num = 1
    else:
        next_num = 1
    
    reference = f"{prefix}-{date_str}-{next_num:04d}"
    
    # Vérifier l'unicité
    while CommercialOrder.query.filter_by(reference=reference).first():
        time.sleep(1)
        next_num += 1
        reference = f"{prefix}-{date_str}-{next_num:04d}"
    
    return reference

def generate_movement_reference(movement_type='transfer'):
    """Génère une référence unique pour un mouvement de stock"""
    import time
    prefix_map = {
        'transfer': 'TRANS',
        'reception': 'REC',
        'adjustment': 'AJUST',
        'inventory': 'INV'
    }
    prefix = prefix_map.get(movement_type, 'MV')
    date_str = datetime.now().strftime('%Y%m%d')
    
    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    last_movement = StockMovement.query.filter(
        StockMovement.reference.like(f'{prefix}-{date_str}-%'),
        StockMovement.created_at >= today_start
    ).order_by(StockMovement.id.desc()).first()
    
    if last_movement and last_movement.reference:
        try:
            last_num = int(last_movement.reference.split('-')[-1])
            next_num = last_num + 1
        except (ValueError, IndexError):
            next_num = 1
    else:
        next_num = 1
    
    reference = f"{prefix}-{date_str}-{next_num:04d}"
    
    while StockMovement.query.filter_by(reference=reference).first():
        time.sleep(1)
        next_num += 1
        reference = f"{prefix}-{date_str}-{next_num:04d}"
    
    return reference

@orders_bp.route('/')
@login_required
def orders_list():
    """Liste des commandes commerciales"""
    # #region agent log
    import json, time
    try:
        with open('/Users/dantawi/Documents/mini_flask_import_profitability/.cursor/debug.log', 'a') as f:
            f.write(json.dumps({"id":"log_entry","timestamp":int(time.time()*1000),"location":"orders.py:94","message":"orders_list entry","data":{"user_id":current_user.id if current_user else None,"user_role":current_user.role.code if (current_user and current_user.role) else None},"sessionId":"debug-session","runId":"run1","hypothesisId":"A"}) + "\n")
    except: pass
    # #endregion
    
    # Permissions : commerciaux voient leurs commandes, hiérarchie voit toutes
    # Le magasinier peut voir les commandes validées même sans permission orders.read
    if not has_permission(current_user, 'orders.read'):
        # Exception pour le magasinier qui doit voir les commandes validées pour générer les bons de sortie
        if not (current_user.role and current_user.role.code == 'warehouse'):
            # #region agent log
            try:
                with open('/Users/dantawi/Documents/mini_flask_import_profitability/.cursor/debug.log', 'a') as f:
                    f.write(json.dumps({"id":"log_entry","timestamp":int(time.time()*1000),"location":"orders.py:99","message":"permission denied","data":{"user_id":current_user.id if current_user else None},"sessionId":"debug-session","runId":"run1","hypothesisId":"D"}) + "\n")
            except: pass
            # #endregion
            flash('Vous n\'avez pas la permission de voir les commandes', 'error')
            return redirect(url_for('index'))
    
    # Filtres
    status_filter = request.args.get('status', 'all')
    commercial_filter = request.args.get('commercial_id', type=int)
    region_filter = request.args.get('region_id', type=int)
    search_query = request.args.get('search', '')
    sort_order = request.args.get('sort', 'arrival')  # 'arrival' pour ordre d'arrivée, 'date' pour date décroissante
    
    # Filtres de période
    period = request.args.get('period', '')
    start_date_str = request.args.get('start_date', '')
    end_date_str = request.args.get('end_date', '')
    
    # Calculer les dates de début et fin selon la période sélectionnée
    start_date = None
    end_date = None
    
    if period:
        now = datetime.now(UTC)
        if period == 'today':
            start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = now.replace(hour=23, minute=59, second=59, microsecond=999999)
        elif period == 'week':
            # Lundi de cette semaine
            days_since_monday = now.weekday()
            start_date = (now - timedelta(days=days_since_monday)).replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = now.replace(hour=23, minute=59, second=59, microsecond=999999)
        elif period == 'month':
            start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            end_date = now.replace(hour=23, minute=59, second=59, microsecond=999999)
        elif period == 'quarter':
            # Premier jour du trimestre
            quarter = (now.month - 1) // 3
            start_date = now.replace(month=quarter * 3 + 1, day=1, hour=0, minute=0, second=0, microsecond=0)
            end_date = now.replace(hour=23, minute=59, second=59, microsecond=999999)
        elif period == 'year':
            start_date = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
            end_date = now.replace(hour=23, minute=59, second=59, microsecond=999999)
    elif start_date_str and end_date_str:
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').replace(hour=0, minute=0, second=0, microsecond=0)
            start_date = start_date.replace(tzinfo=UTC)
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').replace(hour=23, minute=59, second=59, microsecond=999999)
            end_date = end_date.replace(tzinfo=UTC)
        except ValueError:
            start_date = None
            end_date = None
    
    # #region agent log
    try:
        with open('/Users/dantawi/Documents/mini_flask_import_profitability/.cursor/debug.log', 'a') as f:
            f.write(json.dumps({"id":"log_entry","timestamp":int(time.time()*1000),"location":"orders.py:107","message":"filters extracted","data":{"status_filter":status_filter,"commercial_filter":commercial_filter,"search_query":search_query},"sessionId":"debug-session","runId":"run1","hypothesisId":"A"}) + "\n")
    except: pass
    # #endregion
    
    # Base query
    try:
        query = CommercialOrder.query.options(
            joinedload(CommercialOrder.commercial),
            joinedload(CommercialOrder.validator),
            joinedload(CommercialOrder.region),
            joinedload(CommercialOrder.clients).joinedload(CommercialOrderClient.items).joinedload(CommercialOrderItem.stock_item)
        )
        # #region agent log
        try:
            with open('/Users/dantawi/Documents/mini_flask_import_profitability/.cursor/debug.log', 'a') as f:
                f.write(json.dumps({"id":"log_entry","timestamp":int(time.time()*1000),"location":"orders.py:115","message":"base query created","data":{"query_type":str(type(query))},"sessionId":"debug-session","runId":"run1","hypothesisId":"A"}) + "\n")
        except: pass
        # #endregion
    except Exception as e:
        # #region agent log
        try:
            with open('/Users/dantawi/Documents/mini_flask_import_profitability/.cursor/debug.log', 'a') as f:
                f.write(json.dumps({"id":"log_entry","timestamp":int(time.time()*1000),"location":"orders.py:120","message":"query creation failed","data":{"error":str(e)},"sessionId":"debug-session","runId":"run1","hypothesisId":"A"}) + "\n")
        except: pass
        # #endregion
        raise
    
    # IMPORTANT: Filtrer selon le rôle de l'utilisateur
    # - Commercial : voit uniquement SES commandes (sa session de travail)
    # - Magasinier (warehouse) : voit uniquement les commandes VALIDÉES (pour générer les bons de sortie)
    # - Admin : voit toutes les commandes
    # - Autres rôles : filtrer par région
    if current_user.role and current_user.role.code == 'commercial':
        query = query.filter(CommercialOrder.commercial_id == current_user.id)
        # #region agent log
        try:
            with open('/Users/dantawi/Documents/mini_flask_import_profitability/.cursor/debug.log', 'a') as f:
                f.write(json.dumps({"id":"log_entry","timestamp":int(time.time()*1000),"location":"orders.py:125","message":"filtered by commercial","data":{"commercial_id":current_user.id},"sessionId":"debug-session","runId":"run1","hypothesisId":"A"}) + "\n")
        except: pass
        # #endregion
    elif current_user.role and current_user.role.code == 'warehouse':
        # Le magasinier voit uniquement les commandes validées (pour générer les bons de sortie)
        query = query.filter(CommercialOrder.status == 'validated')
        # Compter le nombre de commandes validées pour debug
        validated_count = query.count()
        # #region agent log
        try:
            with open('/Users/dantawi/Documents/mini_flask_import_profitability/.cursor/debug.log', 'a') as f:
                f.write(json.dumps({"id":"log_entry","timestamp":int(time.time()*1000),"location":"orders.py:130","message":"filtered by warehouse - validated only","data":{"user_id":current_user.id,"validated_orders_count":validated_count},"sessionId":"debug-session","runId":"run1","hypothesisId":"A"}) + "\n")
        except: pass
        # #endregion
    elif current_user.role and current_user.role.code == 'admin':
        # Admin voit toutes les commandes sans filtre
        pass
    else:
        # Pour les superviseurs et autres rôles, filtrer par région
        query = filter_commercial_orders_by_region(query)
    
    # Appliquer les filtres de statut (sauf pour le magasinier qui voit déjà uniquement les validées)
    if current_user.role and current_user.role.code != 'warehouse' and status_filter != 'all':
        query = query.filter(CommercialOrder.status == status_filter)
    
    # Le magasinier voit toutes les commandes validées, peu importe le commercial ou la région
    if current_user.role and current_user.role.code != 'warehouse':
        if commercial_filter:
            query = query.filter(CommercialOrder.commercial_id == commercial_filter)
        
        if region_filter:
            query = query.filter(CommercialOrder.region_id == region_filter)
    
    if search_query:
        query = query.filter(
            or_(
                CommercialOrder.reference.like(f'%{search_query}%'),
                CommercialOrder.notes.like(f'%{search_query}%')
            )
        )
    
    # Appliquer le filtre de période
    if start_date and end_date:
        query = query.filter(
            and_(
                CommercialOrder.order_date >= start_date,
                CommercialOrder.order_date <= end_date
            )
        )
    
    # Pagination
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    # Tri : par défaut, ordre d'arrivée (created_at ASC) pour gérer les commandes dans l'ordre chronologique
    # Le magasinier voit toujours par ordre d'arrivée pour traiter dans l'ordre
    if current_user.role and current_user.role.code == 'warehouse':
        # Magasinier : toujours par ordre d'arrivée (plus anciennes en premier)
        order_by = CommercialOrder.created_at.asc()
    elif sort_order == 'arrival':
        # Ordre d'arrivée : plus anciennes en premier
        order_by = CommercialOrder.created_at.asc()
    else:
        # Date décroissante : plus récentes en premier
        order_by = CommercialOrder.created_at.desc()
    
    # #region agent log
    try:
        with open('/Users/dantawi/Documents/mini_flask_import_profitability/.cursor/debug.log', 'a') as f:
            f.write(json.dumps({"id":"log_entry","timestamp":int(time.time()*1000),"location":"orders.py:150","message":"before pagination","data":{"page":page,"per_page":per_page,"sort_order":sort_order},"sessionId":"debug-session","runId":"run1","hypothesisId":"B"}) + "\n")
    except: pass
    # #endregion
    
    try:
        orders = query.order_by(order_by).paginate(
            page=page, per_page=per_page, error_out=False
        )
        # Protection : s'assurer que orders n'est jamais None
        if orders is None:
            # #region agent log
            try:
                with open('/Users/dantawi/Documents/mini_flask_import_profitability/.cursor/debug.log', 'a') as f:
                    f.write(json.dumps({"id":"log_entry","timestamp":int(time.time()*1000),"location":"orders.py:157","message":"orders is None after pagination","data":{},"sessionId":"debug-session","runId":"run1","hypothesisId":"B"}) + "\n")
            except: pass
            # #endregion
            # Créer un objet pagination vide en cas d'erreur
            from flask_sqlalchemy import Pagination
            orders = Pagination(query=None, page=1, per_page=20, total=0, items=[])
        # #region agent log
        try:
            with open('/Users/dantawi/Documents/mini_flask_import_profitability/.cursor/debug.log', 'a') as f:
                f.write(json.dumps({"id":"log_entry","timestamp":int(time.time()*1000),"location":"orders.py:165","message":"pagination result","data":{"orders_type":str(type(orders)),"orders_items_count":len(orders.items) if orders and hasattr(orders,'items') else None,"orders_is_none":orders is None,"orders_has_items":hasattr(orders,'items') if orders else False,"orders_items_is_none":orders.items is None if (orders and hasattr(orders,'items')) else None},"sessionId":"debug-session","runId":"run1","hypothesisId":"B"}) + "\n")
        except: pass
        # #endregion
    except Exception as e:
        # #region agent log
        try:
            with open('/Users/dantawi/Documents/mini_flask_import_profitability/.cursor/debug.log', 'a') as f:
                f.write(json.dumps({"id":"log_entry","timestamp":int(time.time()*1000),"location":"orders.py:172","message":"pagination failed","data":{"error":str(e),"error_type":type(e).__name__},"sessionId":"debug-session","runId":"run1","hypothesisId":"B"}) + "\n")
        except: pass
        # #endregion
        # En cas d'erreur, créer un objet pagination vide pour éviter None
        from flask_sqlalchemy import Pagination
        orders = Pagination(query=None, page=1, per_page=20, total=0, items=[])
    
    # Récupérer les commerciaux pour le filtre
    try:
        commercials_query = User.query.join(User.role).filter(
            User.role.has(code='commercial')
        )
        # Filtrer les commerciaux par région si nécessaire
        from utils_region_filter import filter_users_by_region
        commercials_query = filter_users_by_region(commercials_query)
        commercials = commercials_query.all() if has_permission(current_user, 'orders.validate') else []
        # #region agent log
        try:
            with open('/Users/dantawi/Documents/mini_flask_import_profitability/.cursor/debug.log', 'a') as f:
                f.write(json.dumps({"id":"log_entry","timestamp":int(time.time()*1000),"location":"orders.py:168","message":"commercials fetched","data":{"commercials_count":len(commercials) if commercials else 0},"sessionId":"debug-session","runId":"run1","hypothesisId":"A"}) + "\n")
        except: pass
        # #endregion
    except Exception as e:
        # #region agent log
        try:
            with open('/Users/dantawi/Documents/mini_flask_import_profitability/.cursor/debug.log', 'a') as f:
                f.write(json.dumps({"id":"log_entry","timestamp":int(time.time()*1000),"location":"orders.py:173","message":"commercials fetch failed","data":{"error":str(e)},"sessionId":"debug-session","runId":"run1","hypothesisId":"A"}) + "\n")
        except: pass
        # #endregion
        commercials = []
    
    # Récupérer les régions pour le filtre (pour les admins/superviseurs)
    try:
        regions = get_user_accessible_regions()
    except Exception as e:
        regions = []
    
    # Calculer les valeurs totales et préparer le récapitulatif
    orders_summary = []
    total_general = Decimal('0')
    
    # Récupérer toutes les commandes (sans pagination) pour le récapitulatif
    summary_query = query.order_by(order_by)
    all_orders_for_summary = summary_query.all()
    
    # Calculer les valeurs pour chaque commande et préparer le format tableau
    for order in all_orders_for_summary:
        order_total = Decimal('0')
        clients_data = []
        all_clients = []  # Liste de tous les clients uniques
        all_articles = {}  # Dict: article_name -> {client_name: quantity, ...}
        
        for client in order.clients:
            if client.status != 'rejected':  # Exclure les clients rejetés
                client_name = client.client_name
                if client_name not in all_clients:
                    all_clients.append(client_name)
                
                client_total = Decimal('0')
                for item in client.items:
                    if item.quantity and item.unit_price_gnf:
                        item_name = item.stock_item.name if item.stock_item else 'Article inconnu'
                        item_quantity = float(item.quantity)
                        item_value = Decimal(str(item.quantity)) * Decimal(str(item.unit_price_gnf))
                        order_total += item_value
                        client_total += item_value
                        
                        # Ajouter l'article au dictionnaire
                        if item_name not in all_articles:
                            all_articles[item_name] = {}
                        if client_name not in all_articles[item_name]:
                            all_articles[item_name][client_name] = 0
                        all_articles[item_name][client_name] += item_quantity
                
                if client_total > 0:  # Ne garder que les clients avec des articles
                    clients_data.append({
                        'name': client_name,
                        'total_value': client_total
                    })
        
        if clients_data and all_articles:  # Ne garder que les commandes avec des clients valides
            # Convertir all_articles en liste triée
            articles_list = []
            for article_name, clients_quantities in sorted(all_articles.items()):
                article_total = sum(clients_quantities.values())
                articles_list.append({
                    'name': article_name,
                    'clients_quantities': clients_quantities,
                    'total': article_total
                })
            
            orders_summary.append({
                'order': order,
                'reference': order.reference,
                'date': order.order_date,
                'commercial': order.commercial.full_name if order.commercial and order.commercial.full_name else (order.commercial.username if order.commercial else '-'),
                'region': order.region.name if order.region else '-',
                'clients': clients_data,
                'clients_list': all_clients,
                'articles': articles_list,
                'total_value': order_total
            })
            total_general += order_total
    
    # #region agent log
    try:
        with open('/Users/dantawi/Documents/mini_flask_import_profitability/.cursor/debug.log', 'a') as f:
            f.write(json.dumps({"id":"log_entry","timestamp":int(time.time()*1000),"location":"orders.py:178","message":"before render_template","data":{"orders_is_none":orders is None,"orders_items_exists":hasattr(orders,'items') if orders else False,"orders_items_count":len(orders.items) if (orders and hasattr(orders,'items')) else None},"sessionId":"debug-session","runId":"run1","hypothesisId":"E"}) + "\n")
    except: pass
    # #endregion
    
    try:
        result = render_template('orders/orders_list.html',
                             orders=orders,
                             status_filter=status_filter,
                             commercial_filter=commercial_filter,
                             region_filter=region_filter,
                             search_query=search_query,
                             sort_order=sort_order,
                             commercials=commercials,
                             regions=regions,
                             period=period,
                             start_date=start_date_str,
                             end_date=end_date_str,
                             orders_summary=orders_summary,
                             total_general=total_general)
        # #region agent log
        try:
            with open('/Users/dantawi/Documents/mini_flask_import_profitability/.cursor/debug.log', 'a') as f:
                f.write(json.dumps({"id":"log_entry","timestamp":int(time.time()*1000),"location":"orders.py:187","message":"render_template success","data":{"result_length":len(result) if result else 0},"sessionId":"debug-session","runId":"run1","hypothesisId":"C"}) + "\n")
        except: pass
        # #endregion
        return result
    except Exception as e:
        # #region agent log
        try:
            with open('/Users/dantawi/Documents/mini_flask_import_profitability/.cursor/debug.log', 'a') as f:
                f.write(json.dumps({"id":"log_entry","timestamp":int(time.time()*1000),"location":"orders.py:192","message":"render_template failed","data":{"error":str(e),"error_type":type(e).__name__},"sessionId":"debug-session","runId":"run1","hypothesisId":"C"}) + "\n")
        except: pass
        # #endregion
        raise

@orders_bp.route('/new', methods=['GET', 'POST'])
@login_required
def order_new():
    """Créer une nouvelle commande commerciale"""
    # #region agent log
    import json, time
    try:
        with open('/Users/dantawi/Documents/mini_flask_import_profitability/.cursor/debug.log', 'a') as f:
            f.write(json.dumps({"id":"log_entry","timestamp":int(time.time()*1000),"location":"orders.py:270","message":"order_new entry","data":{"method":request.method,"user_id":current_user.id if current_user else None,"user_role":current_user.role.code if (current_user and current_user.role) else None},"sessionId":"debug-session","runId":"run1","hypothesisId":"A"}) + "\n")
    except: pass
    # #endregion
    
    if not has_permission(current_user, 'orders.create'):
        # #region agent log
        try:
            with open('/Users/dantawi/Documents/mini_flask_import_profitability/.cursor/debug.log', 'a') as f:
                f.write(json.dumps({"id":"log_entry","timestamp":int(time.time()*1000),"location":"orders.py:276","message":"permission denied for create","data":{"user_id":current_user.id if current_user else None},"sessionId":"debug-session","runId":"run1","hypothesisId":"A"}) + "\n")
        except: pass
        # #endregion
        flash('Vous n\'avez pas la permission de créer une commande', 'error')
        return redirect(url_for('orders.orders_list'))
    
    # Vérifier que l'utilisateur est commercial
    if current_user.role and current_user.role.code != 'commercial':
        # #region agent log
        try:
            with open('/Users/dantawi/Documents/mini_flask_import_profitability/.cursor/debug.log', 'a') as f:
                f.write(json.dumps({"id":"log_entry","timestamp":int(time.time()*1000),"location":"orders.py:282","message":"user is not commercial","data":{"user_role":current_user.role.code if current_user.role else None},"sessionId":"debug-session","runId":"run1","hypothesisId":"A"}) + "\n")
        except: pass
        # #endregion
        flash('Seuls les commerciaux peuvent créer des commandes', 'error')
        return redirect(url_for('orders.orders_list'))
    
    if request.method == 'POST':
        # #region agent log
        try:
            form_keys = list(request.form.keys())
            clients_count = len([k for k in form_keys if k.startswith('client_') and '_name' in k])
            items_count = len([k for k in form_keys if '_item_' in k and '_id' in k])
            with open('/Users/dantawi/Documents/mini_flask_import_profitability/.cursor/debug.log', 'a') as f:
                f.write(json.dumps({"id":"log_entry","timestamp":int(time.time()*1000),"location":"orders.py:289","message":"POST request received","data":{"form_keys_count":len(form_keys),"clients_count":clients_count,"items_count":items_count,"order_date":request.form.get('order_date')},"sessionId":"debug-session","runId":"run1","hypothesisId":"B"}) + "\n")
        except: pass
        # #endregion
        # Récupérer les données du formulaire
        order_date_str = request.form.get('order_date', '').strip()
        notes = request.form.get('notes', '').strip() or None
        
        # Convertir order_date
        order_date = datetime.now(UTC)
        if order_date_str:
            try:
                order_date = datetime.strptime(order_date_str, '%Y-%m-%d')
            except (ValueError, TypeError):
                order_date = datetime.now(UTC)
        
        # Générer la référence
        reference = generate_order_reference()
        # #region agent log
        try:
            with open('/Users/dantawi/Documents/mini_flask_import_profitability/.cursor/debug.log', 'a') as f:
                f.write(json.dumps({"id":"log_entry","timestamp":int(time.time()*1000),"location":"orders.py:295","message":"reference generated","data":{"reference":reference},"sessionId":"debug-session","runId":"run1","hypothesisId":"B"}) + "\n")
        except: pass
        # #endregion
        
        # Créer la commande
        try:
            order = CommercialOrder(
                reference=reference,
                order_date=order_date,
                commercial_id=current_user.id,
                region_id=current_user.region_id,
                notes=notes,
                status='draft',
                user_id=current_user.id
            )
            db.session.add(order)
            db.session.flush()
            # #region agent log
            try:
                with open('/Users/dantawi/Documents/mini_flask_import_profitability/.cursor/debug.log', 'a') as f:
                    f.write(json.dumps({"id":"log_entry","timestamp":int(time.time()*1000),"location":"orders.py:308","message":"order created","data":{"order_id":order.id,"reference":order.reference},"sessionId":"debug-session","runId":"run1","hypothesisId":"B"}) + "\n")
            except: pass
            # #endregion
        except Exception as e:
            # #region agent log
            try:
                with open('/Users/dantawi/Documents/mini_flask_import_profitability/.cursor/debug.log', 'a') as f:
                    f.write(json.dumps({"id":"log_entry","timestamp":int(time.time()*1000),"location":"orders.py:312","message":"order creation failed","data":{"error":str(e),"error_type":type(e).__name__},"sessionId":"debug-session","runId":"run1","hypothesisId":"B"}) + "\n")
            except: pass
            # #endregion
            raise
        
        # Traiter les clients (format: client_0_name, client_0_phone, client_0_items)
        clients_data = []
        i = 0
        clients_processed = 0
        total_items_count = 0
        while True:
            client_name = request.form.get(f'client_{i}_name', '').strip()
            if not client_name:
                break
            # #region agent log
            try:
                with open('/Users/dantawi/Documents/mini_flask_import_profitability/.cursor/debug.log', 'a') as f:
                    f.write(json.dumps({"id":"log_entry","timestamp":int(time.time()*1000),"location":"orders.py:320","message":"processing client","data":{"client_index":i,"client_name":client_name},"sessionId":"debug-session","runId":"run1","hypothesisId":"B"}) + "\n")
            except: pass
            # #endregion
            
            client_phone = request.form.get(f'client_{i}_phone', '').strip()
            client_address = request.form.get(f'client_{i}_address', '').strip()
            payment_type = request.form.get(f'client_{i}_payment_type', 'cash').strip()
            payment_due_date_str = request.form.get(f'client_{i}_payment_due_date', '').strip()
            client_notes = request.form.get(f'client_{i}_notes', '').strip()
            client_comments = request.form.get(f'client_{i}_comments', '').strip()
            
            # Convertir la date d'échéance si fournie
            payment_due_date = None
            if payment_due_date_str:
                try:
                    from datetime import datetime as dt
                    payment_due_date = dt.strptime(payment_due_date_str, '%Y-%m-%d').date()
                except:
                    pass
            
            # Créer le client
            order_client = CommercialOrderClient(
                order_id=order.id,
                client_name=client_name,
                client_phone=client_phone,
                client_address=client_address,
                payment_type=payment_type,
                payment_due_date=payment_due_date,
                notes=client_notes,
                comments=client_comments
            )
            db.session.add(order_client)
            db.session.flush()
            clients_processed += 1
            # #region agent log
            try:
                with open('/Users/dantawi/Documents/mini_flask_import_profitability/.cursor/debug.log', 'a') as f:
                    f.write(json.dumps({"id":"log_entry","timestamp":int(time.time()*1000),"location":"orders.py:345","message":"client added","data":{"client_index":i,"order_client_id":order_client.id},"sessionId":"debug-session","runId":"run1","hypothesisId":"B"}) + "\n")
            except: pass
            # #endregion
            
            # Traiter les articles du client (format: client_{i}_item_{j}_id, client_{i}_item_{j}_qty)
            j = 0
            items_for_client = 0
            while True:
                item_id_str = request.form.get(f'client_{i}_item_{j}_id', '').strip()
                if not item_id_str:
                    break
                
                try:
                    item_id = int(item_id_str)
                except (ValueError, TypeError):
                    j += 1
                    continue
                
                # Convertir quantity et unit_price en Decimal de manière sécurisée
                quantity_str = request.form.get(f'client_{i}_item_{j}_qty', '').strip()
                unit_price_str = request.form.get(f'client_{i}_item_{j}_price', '').strip()
                item_notes = request.form.get(f'client_{i}_item_{j}_notes', '').strip() or None
                
                quantity = None
                unit_price = None
                
                try:
                    if quantity_str:
                        quantity = Decimal(str(quantity_str))
                except (ValueError, TypeError, InvalidOperation):
                    quantity = None
                
                try:
                    if unit_price_str:
                        unit_price = Decimal(str(unit_price_str))
                except (ValueError, TypeError, InvalidOperation):
                    unit_price = None
                
                if quantity and quantity > 0 and unit_price and unit_price >= 0:
                    order_item = CommercialOrderItem(
                        order_client_id=order_client.id,
                        stock_item_id=item_id,
                        quantity=quantity,
                        unit_price_gnf=unit_price,
                        notes=item_notes
                    )
                    db.session.add(order_item)
                    items_for_client += 1
                    total_items_count += 1
                    # #region agent log
                    try:
                        with open('/Users/dantawi/Documents/mini_flask_import_profitability/.cursor/debug.log', 'a') as f:
                            f.write(json.dumps({"id":"log_entry","timestamp":int(time.time()*1000),"location":"orders.py:365","message":"item added to client","data":{"client_index":i,"item_index":j,"item_id":item_id,"quantity":str(quantity),"unit_price":str(unit_price) if unit_price else None},"sessionId":"debug-session","runId":"run1","hypothesisId":"B"}) + "\n")
                    except: pass
                    # #endregion
                
                j += 1
            
            # #region agent log
            try:
                with open('/Users/dantawi/Documents/mini_flask_import_profitability/.cursor/debug.log', 'a') as f:
                    f.write(json.dumps({"id":"log_entry","timestamp":int(time.time()*1000),"location":"orders.py:373","message":"client processing complete","data":{"client_index":i,"items_count":items_for_client},"sessionId":"debug-session","runId":"run1","hypothesisId":"B"}) + "\n")
            except: pass
            # #endregion
            
            i += 1
        
        # #region agent log
        try:
            with open('/Users/dantawi/Documents/mini_flask_import_profitability/.cursor/debug.log', 'a') as f:
                f.write(json.dumps({"id":"log_entry","timestamp":int(time.time()*1000),"location":"orders.py:380","message":"all clients processed","data":{"total_clients":clients_processed},"sessionId":"debug-session","runId":"run1","hypothesisId":"B"}) + "\n")
        except: pass
        # #endregion
        
        if clients_processed == 0:
            flash('Veuillez ajouter au moins un client', 'error')
            db.session.rollback()
            return redirect(url_for('orders.order_new'))
        
        # Vérifier qu'au moins un client a des articles
        if total_items_count == 0:
            flash('Veuillez ajouter au moins un article à un client', 'error')
            db.session.rollback()
            return redirect(url_for('orders.order_new'))
        
        # Passer en attente de validation
        order.status = 'pending_validation'
        try:
            db.session.commit()
            # #region agent log
            try:
                with open('/Users/dantawi/Documents/mini_flask_import_profitability/.cursor/debug.log', 'a') as f:
                    f.write(json.dumps({"id":"log_entry","timestamp":int(time.time()*1000),"location":"orders.py:390","message":"order committed successfully","data":{"order_id":order.id,"reference":order.reference,"status":order.status},"sessionId":"debug-session","runId":"run1","hypothesisId":"B"}) + "\n")
            except: pass
            # #endregion
        except Exception as e:
            # #region agent log
            try:
                with open('/Users/dantawi/Documents/mini_flask_import_profitability/.cursor/debug.log', 'a') as f:
                    f.write(json.dumps({"id":"log_entry","timestamp":int(time.time()*1000),"location":"orders.py:395","message":"commit failed","data":{"error":str(e),"error_type":type(e).__name__},"sessionId":"debug-session","runId":"run1","hypothesisId":"B"}) + "\n")
            except: pass
            # #endregion
            db.session.rollback()
            flash(f'Erreur lors de la création de la commande: {str(e)}', 'error')
            return redirect(url_for('orders.order_new'))
        
        flash(f'Commande "{reference}" créée avec succès et soumise à validation', 'success')
        return redirect(url_for('orders.order_detail', id=order.id))
    
    # GET : Afficher le formulaire
    # #region agent log
    try:
        with open('/Users/dantawi/Documents/mini_flask_import_profitability/.cursor/debug.log', 'a') as f:
            f.write(json.dumps({"id":"log_entry","timestamp":int(time.time()*1000),"location":"orders.py:405","message":"GET request - loading form","data":{},"sessionId":"debug-session","runId":"run1","hypothesisId":"A"}) + "\n")
    except: pass
    # #endregion
    
    stock_items = StockItem.query.filter_by(is_active=True).order_by(StockItem.name).all()
    # #region agent log
    try:
        with open('/Users/dantawi/Documents/mini_flask_import_profitability/.cursor/debug.log', 'a') as f:
            f.write(json.dumps({"id":"log_entry","timestamp":int(time.time()*1000),"location":"orders.py:410","message":"stock items loaded","data":{"stock_items_count":len(stock_items) if stock_items else 0},"sessionId":"debug-session","runId":"run1","hypothesisId":"A"}) + "\n")
    except: pass
    # #endregion
    
    # Récupérer la fiche de prix active pour les prix de vente
    from datetime import date
    today = date.today()
    
    active_price_list = PriceList.query.filter(
        PriceList.is_active == True,
        PriceList.start_date <= today,
        db.or_(
            PriceList.end_date.is_(None),
            PriceList.end_date >= today
        )
    ).order_by(PriceList.start_date.desc()).first()
    
    # Créer un dictionnaire de prix par nom d'article (PriceListItem est lié à Article)
    # On fait le lien entre Article et StockItem par le nom (car Article n'a pas de SKU)
    prices_by_name = {}
    if active_price_list:
        for price_item in active_price_list.items:
            if price_item.article:
                # Utiliser le prix grossiste (wholesale_price) par défaut, sinon détaillant
                price = price_item.wholesale_price or price_item.retail_price
                if price:
                    prices_by_name[price_item.article.name.lower()] = float(price)
    
    # Convertir les stock_items en format JSON pour le JavaScript avec prix
    stock_items_json = []
    for item in stock_items:
        try:
            item_data = {
                'id': int(item.id),
                'name': str(item.name) if item.name else '',
                'sku': str(item.sku) if item.sku else '',
                'default_price': None
            }
            
            # Chercher le prix dans la fiche de prix active par nom d'article
            item_name_lower = item.name.lower() if item.name else ''
            if item_name_lower in prices_by_name:
                item_data['default_price'] = float(prices_by_name[item_name_lower])
            # Sinon utiliser le prix d'achat comme référence (peut être modifié)
            elif item.purchase_price_gnf:
                try:
                    item_data['default_price'] = float(item.purchase_price_gnf)
                except (ValueError, TypeError):
                    item_data['default_price'] = None
            
            stock_items_json.append(item_data)
        except Exception as e:
            print(f"⚠️ Erreur lors de la conversion de l'article {item.id}: {e}")
            continue
    
    return render_template('orders/order_form.html',
                         stock_items=stock_items_json,
                         today=datetime.now(UTC).strftime('%Y-%m-%d'))

@orders_bp.route('/<int:id>')
@login_required
def order_detail(id):
    """Détails d'une commande"""
    order = CommercialOrder.query.options(
        joinedload(CommercialOrder.commercial),
        joinedload(CommercialOrder.validator),
        joinedload(CommercialOrder.region),
        joinedload(CommercialOrder.clients).joinedload(CommercialOrderClient.items).joinedload(CommercialOrderItem.stock_item),
        joinedload(CommercialOrder.clients).joinedload(CommercialOrderClient.rejected_by)
    ).get_or_404(id)
    
    # IMPORTANT: Vérifier les permissions d'accès selon le rôle
    # - Commercial : accède uniquement à SES commandes (sa session)
    # - Magasinier : accède uniquement aux commandes VALIDÉES
    # - Admin/Supervisor : accès à toutes les commandes (selon région pour supervisor)
    if current_user.role and current_user.role.code == 'commercial':
        if order.commercial_id != current_user.id:
            flash('Vous n\'avez pas accès à cette commande. Vous ne pouvez voir que vos propres commandes dans votre session.', 'error')
            return redirect(url_for('orders.orders_list'))
    elif current_user.role and current_user.role.code == 'warehouse':
        if order.status != 'validated':
            flash('Vous ne pouvez accéder qu\'aux commandes validées pour générer les bons de sortie.', 'error')
            return redirect(url_for('orders.orders_list'))
    
    # Vérifier si la commande peut être modifiée
    can_edit = False
    if has_permission(current_user, 'orders.update'):
        # Peut modifier si draft, rejected ou pending_validation, et si c'est le commercial qui l'a créée ou si c'est admin/supervisor
        if order.status in ('draft', 'rejected', 'pending_validation'):
            if order.commercial_id == current_user.id or (current_user.role and current_user.role.code in ('admin', 'supervisor')):
                can_edit = True
    
    # Récupérer les dépôts et véhicules pour le formulaire de génération de sortie
    depots = Depot.query.filter_by(is_active=True).order_by(Depot.name).all()
    vehicles = Vehicle.query.filter_by(status='active').order_by(Vehicle.plate_number).all()
    
    return render_template('orders/order_detail.html', order=order, depots=depots, vehicles=vehicles, can_edit=can_edit)

@orders_bp.route('/<int:id>/validate', methods=['POST'])
@login_required
def order_validate(id):
    """Valider une commande (hiérarchie uniquement)"""
    if not has_permission(current_user, 'orders.validate'):
        flash('Vous n\'avez pas la permission de valider des commandes', 'error')
        return redirect(url_for('orders.orders_list'))
    
    order = CommercialOrder.query.options(
        joinedload(CommercialOrder.commercial),
        joinedload(CommercialOrder.clients).joinedload(CommercialOrderClient.items)
    ).get_or_404(id)
    
    if order.status != 'pending_validation':
        flash('Cette commande ne peut pas être validée', 'error')
        return redirect(url_for('orders.order_detail', id=id))
    
    order.status = 'validated'
    order.validated_by_id = current_user.id
    order.validated_at = datetime.now(UTC)
    db.session.flush()
    
    # Générer automatiquement le récapitulatif de chargement
    try:
        from models import StockLoadingSummary, StockLoadingSummaryItem, Depot
        from collections import defaultdict
        
        # Déterminer le dépôt source (dépôt principal de la région ou premier dépôt disponible)
        commercial_region_id = order.commercial.region_id if order.commercial else order.region_id
        source_depot = None
        
        if commercial_region_id:
            source_depot = Depot.query.filter_by(region_id=commercial_region_id, is_active=True).order_by(Depot.name).first()
        
        # Si pas de dépôt dans la région, prendre le premier dépôt actif disponible
        if not source_depot:
            source_depot = Depot.query.filter_by(is_active=True).order_by(Depot.name).first()
        
        if not source_depot:
            flash('Aucun dépôt source disponible. Récapitulatif de chargement non créé.', 'warning')
            db.session.commit()
            return redirect(url_for('orders.order_detail', id=id))
        
        # Vérifier si un récapitulatif existe déjà pour cette commande
        existing_summary = StockLoadingSummary.query.filter_by(order_id=order.id).first()
        if existing_summary:
            flash(f'Commande "{order.reference}" validée avec succès. Récapitulatif de chargement déjà existant.', 'success')
            db.session.commit()
            return redirect(url_for('orders.order_detail', id=id))
        
        # Créer le récapitulatif
        summary = StockLoadingSummary(
            order_id=order.id,
            commercial_id=order.commercial_id,
            commercial_depot_id=None,  # Sera défini lors du chargement
            commercial_vehicle_id=None,  # Sera défini lors du chargement
            source_depot_id=source_depot.id,
            status='pending',
            notes=f'Récapitulatif généré automatiquement pour commande {order.reference}'
        )
        db.session.add(summary)
        db.session.flush()
        
        # Agréger les quantités par article depuis tous les clients
        items_required = defaultdict(Decimal)
        
        for client in order.clients:
            for item in client.items:
                items_required[item.stock_item_id] += item.quantity
        
        # Créer les items du récapitulatif
        for stock_item_id, quantity in items_required.items():
            summary_item = StockLoadingSummaryItem(
                summary_id=summary.id,
                stock_item_id=stock_item_id,
                quantity_required=quantity,
                quantity_loaded=Decimal('0')
            )
            db.session.add(summary_item)
        
        db.session.commit()
        
        flash(f'Commande "{order.reference}" validée avec succès. Récapitulatif de chargement généré.', 'success')
    except Exception as e:
        print(f"⚠️ Erreur lors de la génération du récapitulatif de chargement: {e}")
        import traceback
        traceback.print_exc()
        # Continuer même en cas d'erreur pour ne pas bloquer la validation
        db.session.commit()
        flash(f'Commande "{order.reference}" validée avec succès. Erreur lors de la génération du récapitulatif: {str(e)}', 'warning')
    
    return redirect(url_for('orders.order_detail', id=id))

@orders_bp.route('/<int:id>/reject', methods=['POST'])
@login_required
def order_reject(id):
    """Rejeter une commande (hiérarchie uniquement)"""
    if not has_permission(current_user, 'orders.validate'):
        flash('Vous n\'avez pas la permission de rejeter des commandes', 'error')
        return redirect(url_for('orders.orders_list'))
    
    order = CommercialOrder.query.get_or_404(id)
    rejection_reason = request.form.get('rejection_reason', '').strip()
    
    if order.status != 'pending_validation':
        flash('Cette commande ne peut pas être rejetée', 'error')
        return redirect(url_for('orders.order_detail', id=id))
    
    if not rejection_reason:
        flash('Veuillez indiquer la raison du rejet', 'error')
        return redirect(url_for('orders.order_detail', id=id))
    
    order.status = 'rejected'
    order.validated_by_id = current_user.id
    order.validated_at = datetime.now(UTC)
    order.rejection_reason = rejection_reason
    db.session.commit()
    
    flash(f'Commande "{order.reference}" rejetée', 'warning')
    return redirect(url_for('orders.order_detail', id=id))

@orders_bp.route('/<int:order_id>/client/<int:client_id>/reject', methods=['POST'])
@login_required
def client_reject(order_id, client_id):
    """Rejeter un client individuel dans une commande"""
    if not has_permission(current_user, 'orders.validate'):
        flash('Vous n\'avez pas la permission de rejeter des clients', 'error')
        return redirect(url_for('orders.order_detail', id=order_id))
    
    order = CommercialOrder.query.get_or_404(order_id)
    client = CommercialOrderClient.query.filter_by(id=client_id, order_id=order_id).first_or_404()
    rejection_reason = request.form.get('rejection_reason', '').strip()
    
    # Ne peut rejeter que si la commande est en attente de validation ou validée
    if order.status not in ('pending_validation', 'validated'):
        flash('Cette commande ne permet pas le rejet de clients', 'error')
        return redirect(url_for('orders.order_detail', id=order_id))
    
    if not rejection_reason:
        flash('Veuillez indiquer la raison du rejet', 'error')
        return redirect(url_for('orders.order_detail', id=order_id))
    
    client.status = 'rejected'
    client.rejection_reason = rejection_reason
    client.rejected_by_id = current_user.id
    client.rejected_at = datetime.now(UTC)
    db.session.commit()
    
    flash(f'Client "{client.client_name}" rejeté dans la commande "{order.reference}"', 'warning')
    return redirect(url_for('orders.order_detail', id=order_id))

@orders_bp.route('/<int:order_id>/client/<int:client_id>/approve', methods=['POST'])
@login_required
def client_approve(order_id, client_id):
    """Approuver un client rejeté dans une commande"""
    if not has_permission(current_user, 'orders.validate'):
        flash('Vous n\'avez pas la permission d\'approuver des clients', 'error')
        return redirect(url_for('orders.order_detail', id=order_id))
    
    order = CommercialOrder.query.get_or_404(order_id)
    client = CommercialOrderClient.query.filter_by(id=client_id, order_id=order_id).first_or_404()
    
    # Ne peut approuver que si la commande est en attente de validation ou validée
    if order.status not in ('pending_validation', 'validated'):
        flash('Cette commande ne permet pas l\'approbation de clients', 'error')
        return redirect(url_for('orders.order_detail', id=order_id))
    
    client.status = 'approved'
    client.rejection_reason = None
    client.rejected_by_id = None
    client.rejected_at = None
    db.session.commit()
    
    flash(f'Client "{client.client_name}" approuvé dans la commande "{order.reference}"', 'success')
    return redirect(url_for('orders.order_detail', id=order_id))

@orders_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def order_edit(id):
    """Modifier une commande (seulement draft ou rejected)"""
    order = CommercialOrder.query.options(
        joinedload(CommercialOrder.clients).joinedload(CommercialOrderClient.items).joinedload(CommercialOrderItem.stock_item)
    ).get_or_404(id)
    
    # Vérifier les permissions
    if not has_permission(current_user, 'orders.update'):
        flash('Vous n\'avez pas la permission de modifier une commande', 'error')
        return redirect(url_for('orders.order_detail', id=id))
    
    # Vérifier que la commande peut être modifiée
    if order.status not in ('draft', 'rejected', 'pending_validation'):
        flash('Cette commande ne peut pas être modifiée (statut: {})'.format(order.status), 'error')
        return redirect(url_for('orders.order_detail', id=id))
    
    # Vérifier que c'est le commercial qui l'a créée ou un admin/supervisor
    if current_user.role and current_user.role.code == 'commercial':
        if order.commercial_id != current_user.id:
            flash('Vous ne pouvez modifier que vos propres commandes', 'error')
            return redirect(url_for('orders.order_detail', id=id))
    
    if request.method == 'POST':
        try:
            # Récupérer les données du formulaire
            order_date = request.form.get('order_date') or datetime.now(UTC)
            notes = request.form.get('notes')
            
            # Mettre à jour la commande
            order.order_date = datetime.strptime(order_date, '%Y-%m-%d') if isinstance(order_date, str) else order_date
            order.notes = notes
            # Gérer le statut après modification
            if order.status == 'rejected':
                order.status = 'draft'  # Remettre en draft après modification si rejetée
            # Si pending_validation ou draft, on garde le statut actuel après modification
            order.updated_at = datetime.now(UTC)
            
            # Supprimer les anciens clients et articles
            for client in order.clients:
                for item in client.items:
                    db.session.delete(item)
                db.session.delete(client)
            db.session.flush()
            
            # Traiter les nouveaux clients (même logique que création)
            i = 0
            while True:
                client_name = request.form.get(f'client_{i}_name', '').strip()
                if not client_name:
                    break
                
                client_phone = request.form.get(f'client_{i}_phone', '').strip()
                client_address = request.form.get(f'client_{i}_address', '').strip()
                payment_type = request.form.get(f'client_{i}_payment_type', 'cash').strip()
                payment_due_date_str = request.form.get(f'client_{i}_payment_due_date', '').strip()
                client_notes = request.form.get(f'client_{i}_notes', '').strip()
                client_comments = request.form.get(f'client_{i}_comments', '').strip()
                
                # Convertir la date d'échéance si fournie
                payment_due_date = None
                if payment_due_date_str:
                    try:
                        from datetime import datetime as dt
                        payment_due_date = dt.strptime(payment_due_date_str, '%Y-%m-%d').date()
                    except:
                        pass
                
                # Créer le client
                order_client = CommercialOrderClient(
                    order_id=order.id,
                    client_name=client_name,
                    client_phone=client_phone,
                    client_address=client_address,
                    payment_type=payment_type,
                    payment_due_date=payment_due_date,
                    notes=client_notes,
                    comments=client_comments
                )
                db.session.add(order_client)
                db.session.flush()
                
                # Traiter les articles du client
                j = 0
                while True:
                    item_id = request.form.get(f'client_{i}_item_{j}_id', type=int)
                    if not item_id:
                        break
                    
                    quantity = request.form.get(f'client_{i}_item_{j}_qty', type=Decimal)
                    unit_price = request.form.get(f'client_{i}_item_{j}_price', type=Decimal)
                    item_notes = request.form.get(f'client_{i}_item_{j}_notes', '').strip()
                    
                    if quantity and quantity > 0:
                        order_item = CommercialOrderItem(
                            order_client_id=order_client.id,
                            stock_item_id=item_id,
                            quantity=quantity,
                            unit_price_gnf=unit_price,
                            notes=item_notes
                        )
                        db.session.add(order_item)
                    
                    j += 1
                
                i += 1
            
            if i == 0:
                flash('Veuillez ajouter au moins un client avec des articles', 'error')
                db.session.rollback()
                return redirect(url_for('orders.order_edit', id=id))
            
            db.session.commit()
            flash(f'Commande "{order.reference}" modifiée avec succès', 'success')
            return redirect(url_for('orders.order_detail', id=id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur lors de la modification: {str(e)}', 'error')
            return redirect(url_for('orders.order_edit', id=id))
    
    # GET : Afficher le formulaire pré-rempli
    stock_items = StockItem.query.filter_by(is_active=True).order_by(StockItem.name).all()
    
    # Récupérer la fiche de prix active pour les prix de vente
    from datetime import date
    today = date.today()
    
    active_price_list = PriceList.query.filter(
        PriceList.is_active == True,
        PriceList.start_date <= today,
        db.or_(
            PriceList.end_date.is_(None),
            PriceList.end_date >= today
        )
    ).order_by(PriceList.start_date.desc()).first()
    
    # Créer un dictionnaire de prix par nom d'article
    prices_by_name = {}
    if active_price_list:
        for price_item in active_price_list.items:
            if price_item.article:
                price = price_item.wholesale_price or price_item.retail_price
                if price:
                    prices_by_name[price_item.article.name.lower()] = float(price)
    
    # Convertir les stock_items en format JSON pour le JavaScript avec prix
    stock_items_json = []
    for item in stock_items:
        try:
            item_data = {
                'id': int(item.id),
                'name': str(item.name) if item.name else '',
                'sku': str(item.sku) if item.sku else '',
                'default_price': None
            }
            
            item_name_lower = item.name.lower() if item.name else ''
            if item_name_lower in prices_by_name:
                item_data['default_price'] = float(prices_by_name[item_name_lower])
            elif item.purchase_price_gnf:
                try:
                    item_data['default_price'] = float(item.purchase_price_gnf)
                except (ValueError, TypeError):
                    item_data['default_price'] = None
            
            stock_items_json.append(item_data)
        except Exception as e:
            print(f"⚠️ Erreur lors de la conversion de l'article {item.id}: {e}")
            continue
    
    return render_template('orders/order_form.html',
                         stock_items=stock_items_json,
                         today=datetime.now(UTC).strftime('%Y-%m-%d'),
                         order=order,
                         is_edit=True)

@orders_bp.route('/<int:id>/generate-outgoing', methods=['POST'])
@login_required
def order_generate_outgoing(id):
    """Générer un bon de sortie depuis une commande validée (magasinier)"""
    if not has_permission(current_user, 'outgoings.create'):
        flash('Vous n\'avez pas la permission de créer des sorties', 'error')
        return redirect(url_for('orders.orders_list'))
    
    order = CommercialOrder.query.options(
        joinedload(CommercialOrder.clients).joinedload(CommercialOrderClient.items).joinedload(CommercialOrderItem.stock_item)
    ).get_or_404(id)
    
    if order.status != 'validated':
        flash('Seules les commandes validées peuvent générer des bons de sortie', 'error')
        return redirect(url_for('orders.order_detail', id=id))
    
    depot_id = request.form.get('depot_id', type=int)
    vehicle_id = request.form.get('vehicle_id', type=int)
    
    if not depot_id and not vehicle_id:
        flash('Veuillez sélectionner un dépôt ou un véhicule source', 'error')
        return redirect(url_for('orders.order_detail', id=id))
    
    # Générer une référence pour la sortie
    import time
    date_str = datetime.now().strftime('%Y%m%d')
    reference = f"OUT-{date_str}-{int(time.time())}"
    while StockOutgoing.query.filter_by(reference=reference).first():
        time.sleep(1)
        reference = f"OUT-{date_str}-{int(time.time())}"
    
    outgoing_date = datetime.now(UTC)
    
    # Créer une sortie pour chaque client de la commande
    created_outgoings = []
    
    for order_client in order.clients:
        # Créer la sortie pour ce client
        outgoing = StockOutgoing(
            reference=f"{reference}-{order_client.id}",
            outgoing_date=outgoing_date,
            client_name=order_client.client_name,
            client_phone=order_client.client_phone,
            commercial_id=order.commercial_id,
            vehicle_id=vehicle_id,
            depot_id=depot_id,
            user_id=current_user.id,
            notes=f"Généré depuis commande {order.reference}",
            status='draft'
        )
        db.session.add(outgoing)
        db.session.flush()
        
        # Ajouter les articles
        for order_item in order_client.items:
            # Vérifier le stock disponible
            if depot_id:
                stock = DepotStock.query.filter_by(depot_id=depot_id, stock_item_id=order_item.stock_item_id).first()
            elif vehicle_id:
                stock = VehicleStock.query.filter_by(vehicle_id=vehicle_id, stock_item_id=order_item.stock_item_id).first()
            else:
                stock = None
            
            if not stock or stock.quantity < order_item.quantity:
                flash(f'Stock insuffisant pour {order_item.stock_item.name} (client: {order_client.client_name})', 'error')
                db.session.rollback()
                return redirect(url_for('orders.order_detail', id=id))
            
            # Créer le détail de sortie
            detail = StockOutgoingDetail(
                outgoing_id=outgoing.id,
                stock_item_id=order_item.stock_item_id,
                quantity=order_item.quantity,
                unit_price_gnf=order_item.unit_price_gnf
            )
            db.session.add(detail)
            
            # Décrémenter le stock
            stock.quantity -= order_item.quantity
            
            # Créer le mouvement de stock
            movement_ref = generate_movement_reference('transfer')
            movement = StockMovement(
                reference=movement_ref,
                movement_type='transfer',
                movement_date=outgoing_date,
                stock_item_id=order_item.stock_item_id,
                quantity=-order_item.quantity,  # Négatif pour sortie
                user_id=current_user.id,
                from_depot_id=depot_id,
                from_vehicle_id=vehicle_id,
                to_depot_id=None,
                to_vehicle_id=None,
                reason=f'Sortie client: {order_client.client_name} (Commande: {order.reference})'
            )
            db.session.add(movement)
        
        outgoing.status = 'completed'
        created_outgoings.append(outgoing)
    
    # Marquer la commande comme complétée
    order.status = 'completed'
    db.session.commit()
    
    flash(f'{len(created_outgoings)} bon(s) de sortie créé(s) avec succès depuis la commande "{order.reference}"', 'success')
    
    if len(created_outgoings) == 1:
        return redirect(url_for('stocks.outgoing_detail', id=created_outgoings[0].id))
    else:
        return redirect(url_for('orders.order_detail', id=id))

