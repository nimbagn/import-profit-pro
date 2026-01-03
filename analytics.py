# analytics.py
# Module de tableaux de bord analytiques avec KPIs, graphiques et alertes

from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required, current_user
from datetime import datetime, date, UTC, timedelta
from decimal import Decimal
from sqlalchemy import func, and_, or_, extract, text
from models import (
    db, Simulation, SimulationItem, Forecast, ForecastItem,
    StockItem, StockMovement, DepotStock, VehicleStock, Depot,
    Vehicle, Reception, InventorySession, VehicleDocument,
    VehicleMaintenance, StockOutgoing, StockOutgoingDetail,
    PriceList, Article, Category, PromotionSale, PromotionTeam,
    PromotionMember, Region, User
)
from auth import has_permission, can_view_stock_values

# Créer le blueprint
analytics_bp = Blueprint('analytics', __name__, url_prefix='/analytics')

def get_period_dates(period='month'):
    """Retourne les dates de début et fin pour une période donnée"""
    today = date.today()
    
    # Gérer les périodes précédentes
    is_previous = period.startswith('previous_')
    if is_previous:
        period = period.replace('previous_', '')
    
    if period == 'today':
        if is_previous:
            start = today - timedelta(days=1)
            end = start
        else:
            start = today
            end = today
    elif period == 'week':
        if is_previous:
            start = today - timedelta(days=today.weekday() + 7)
            end = start + timedelta(days=6)
        else:
            start = today - timedelta(days=today.weekday())
            end = start + timedelta(days=6)
    elif period == 'month':
        if is_previous:
            if today.month == 1:
                start = today.replace(year=today.year - 1, month=12, day=1)
                end = today.replace(year=today.year - 1, month=12, day=31)
            else:
                start = today.replace(month=today.month - 1, day=1)
                if today.month - 1 == 12:
                    end = today.replace(month=12, day=31)
                else:
                    end = (today.replace(month=today.month, day=1) - timedelta(days=1))
        else:
            start = today.replace(day=1)
            if today.month == 12:
                end = today.replace(day=31)
            else:
                end = (today.replace(month=today.month + 1, day=1) - timedelta(days=1))
    elif period == 'quarter':
        quarter = (today.month - 1) // 3
        if is_previous:
            if quarter == 0:
                start = today.replace(year=today.year - 1, month=10, day=1)
                end = today.replace(year=today.year - 1, month=12, day=31)
            else:
                start = today.replace(month=(quarter - 1) * 3 + 1, day=1)
                end = (today.replace(month=quarter * 3 + 1, day=1) - timedelta(days=1))
        else:
            start = today.replace(month=quarter * 3 + 1, day=1)
            if quarter == 3:
                end = today.replace(month=12, day=31)
            else:
                end = (today.replace(month=(quarter + 1) * 3 + 1, day=1) - timedelta(days=1))
    elif period == 'year':
        if is_previous:
            start = today.replace(year=today.year - 1, month=1, day=1)
            end = today.replace(year=today.year - 1, month=12, day=31)
        else:
            start = today.replace(month=1, day=1)
            end = today.replace(month=12, day=31)
    else:
        # Par défaut, mois en cours
        if is_previous:
            if today.month == 1:
                start = today.replace(year=today.year - 1, month=12, day=1)
                end = today.replace(year=today.year - 1, month=12, day=31)
            else:
                start = today.replace(month=today.month - 1, day=1)
                end = (today.replace(month=today.month, day=1) - timedelta(days=1))
        else:
            start = today.replace(day=1)
            if today.month == 12:
                end = today.replace(day=31)
            else:
                end = (today.replace(month=today.month + 1, day=1) - timedelta(days=1))
    
    return start, end

def calculate_simulation_kpis(start_date=None, end_date=None):
    """Calcule les KPIs pour les simulations"""
    from sqlalchemy import text, inspect
    
    try:
        # Essayer d'abord avec ORM
        query = Simulation.query
        
        if start_date:
            query = query.filter(Simulation.created_at >= datetime.combine(start_date, datetime.min.time()).replace(tzinfo=UTC))
        if end_date:
            query = query.filter(Simulation.created_at <= datetime.combine(end_date, datetime.max.time()).replace(tzinfo=UTC))
        
        simulations = query.all()
    except Exception as e:
        # Si l'erreur est due à target_mode ou target_margin_pct, utiliser une requête SQL directe
        if 'target_mode' in str(e) or 'target_margin_pct' in str(e):
            try:
                # Vérifier quelles colonnes existent dans la table
                inspector = inspect(db.engine)
                columns = [col['name'] for col in inspector.get_columns('simulations')]
                
                # Construire la liste des colonnes à sélectionner (sans target_mode et target_margin_pct)
                select_cols = []
                for col in ['id', 'rate_usd', 'rate_eur', 'rate_xof', 'customs_gnf', 'handling_gnf', 
                           'others_gnf', 'transport_fixed_gnf', 'transport_per_kg_gnf', 'basis',
                           'truck_capacity_tons', 'is_completed', 'created_at', 'updated_at']:
                    if col in columns:
                        select_cols.append(col)
                
                if select_cols:
                    # Construire la requête SQL avec filtres de date
                    where_clause = "1=1"
                    params = {}
                    
                    if start_date:
                        where_clause += " AND created_at >= :start_date"
                        params['start_date'] = datetime.combine(start_date, datetime.min.time()).replace(tzinfo=UTC)
                    if end_date:
                        where_clause += " AND created_at <= :end_date"
                        params['end_date'] = datetime.combine(end_date, datetime.max.time()).replace(tzinfo=UTC)
                    
                    cols_str = ', '.join(select_cols)
                    sql_query = f"SELECT {cols_str} FROM simulations WHERE {where_clause} ORDER BY created_at DESC"
                    
                    result = db.session.execute(text(sql_query), params)
                    
                    # Créer des objets Simulation à partir des résultats
                    simulations = []
                    for row in result:
                        try:
                            row_dict = {}
                            for idx, col in enumerate(select_cols):
                                try:
                                    row_dict[col] = row[idx]
                                except (IndexError, AttributeError):
                                    # Si row est un objet Row, utiliser l'accès par nom
                                    row_dict[col] = getattr(row, col, None)
                            
                            sim = Simulation()
                            for col in select_cols:
                                if col in row_dict and hasattr(sim, col):
                                    value = row_dict[col]
                                    # Gérer les types spécifiques
                                    if col in ['rate_xof', 'customs_gnf', 'handling_gnf', 'others_gnf', 
                                              'transport_fixed_gnf', 'transport_per_kg_gnf', 'truck_capacity_tons',
                                              'rate_usd', 'rate_eur']:
                                        value = Decimal(str(value)) if value is not None else Decimal('0')
                                    elif col == 'is_completed':
                                        value = bool(value) if value is not None else False
                                    elif col == 'basis' and value is None:
                                        value = 'value'
                                    setattr(sim, col, value)
                            
                            simulations.append(sim)
                        except Exception as row_error:
                            print(f"⚠️ Erreur lors du traitement d'une ligne: {row_error}")
                            continue
            except Exception as sql_error:
                print(f"⚠️ Erreur lors de la récupération SQL directe: {sql_error}")
                simulations = []
        else:
            # Autre erreur, retourner des valeurs par défaut
            print(f"⚠️ Erreur lors de la récupération des simulations: {e}")
            simulations = []
    
    total_simulations = len(simulations)
    completed_simulations = sum(1 for s in simulations if hasattr(s, 'is_completed') and s.is_completed)
    
    # Calculer les totaux de marge
    total_margin = Decimal('0')
    total_purchase = Decimal('0')
    total_selling = Decimal('0')
    
    for sim in simulations:
        if hasattr(sim, 'is_completed') and sim.is_completed and hasattr(sim, 'id'):
            try:
                items = SimulationItem.query.filter_by(simulation_id=sim.id).all()
                for item in items:
                    # Calculer la marge pour chaque article
                    purchase_price = Decimal(str(item.purchase_price_gnf or 0))
                    selling_price = Decimal(str(item.selling_price_gnf or 0))
                    quantity = Decimal(str(item.quantity or 0))
                    
                    total_purchase += purchase_price * quantity
                    total_selling += selling_price * quantity
            except Exception as item_error:
                print(f"⚠️ Erreur lors du calcul des items pour simulation {sim.id}: {item_error}")
                continue
    
    total_margin = total_selling - total_purchase
    margin_percentage = (total_margin / total_purchase * 100) if total_purchase > 0 else Decimal('0')
    
    return {
        'total_simulations': total_simulations,
        'completed_simulations': completed_simulations,
        'completion_rate': (completed_simulations / total_simulations * 100) if total_simulations > 0 else 0,
        'total_margin': float(total_margin),
        'total_purchase': float(total_purchase),
        'total_selling': float(total_selling),
        'margin_percentage': float(margin_percentage)
    }

def calculate_forecast_kpis(start_date=None, end_date=None):
    """Calcule les KPIs pour les prévisions"""
    query = Forecast.query
    
    if start_date:
        query = query.filter(Forecast.created_at >= datetime.combine(start_date, datetime.min.time()).replace(tzinfo=UTC))
    if end_date:
        query = query.filter(Forecast.created_at <= datetime.combine(end_date, datetime.max.time()).replace(tzinfo=UTC))
    
    forecasts = query.all()
    
    total_forecasts = len(forecasts)
    active_forecasts = sum(1 for f in forecasts if f.status == 'active')
    
    # Calculer les totaux
    total_forecast_value = Decimal('0')
    total_realized_value = Decimal('0')
    
    for forecast in forecasts:
        total_forecast_value += Decimal(str(forecast.total_forecast_value or 0))
        total_realized_value += Decimal(str(forecast.total_realized_value or 0))
    
    accuracy = (total_realized_value / total_forecast_value * 100) if total_forecast_value > 0 else Decimal('0')
    variance = total_realized_value - total_forecast_value
    
    return {
        'total_forecasts': total_forecasts,
        'active_forecasts': active_forecasts,
        'total_forecast_value': float(total_forecast_value),
        'total_realized_value': float(total_realized_value),
        'accuracy': float(accuracy),
        'variance': float(variance),
        'variance_percentage': float((variance / total_forecast_value * 100) if total_forecast_value > 0 else 0)
    }

def calculate_stock_kpis(start_date=None, end_date=None):
    """Calcule les KPIs pour les stocks avec filtrage par région"""
    from utils_region_filter import (
        filter_depot_stocks_by_region, filter_vehicle_stocks_by_region,
        filter_stock_movements_by_region, filter_depots_by_region
    )
    
    # Stock total actuel (filtré par région)
    depot_stocks_query = DepotStock.query
    depot_stocks_query = filter_depot_stocks_by_region(depot_stocks_query)
    depot_stocks = depot_stocks_query.all()
    
    vehicle_stocks_query = VehicleStock.query
    vehicle_stocks_query = filter_vehicle_stocks_by_region(vehicle_stocks_query)
    vehicle_stocks = vehicle_stocks_query.all()
    
    total_quantity = Decimal('0')
    total_value = Decimal('0')
    
    for ds in depot_stocks:
        quantity = Decimal(str(ds.quantity or 0))
        item = StockItem.query.get(ds.stock_item_id)
        if item:
            price = Decimal(str(item.purchase_price_gnf or 0))
            total_quantity += quantity
            total_value += quantity * price
    
    for vs in vehicle_stocks:
        quantity = Decimal(str(vs.quantity or 0))
        item = StockItem.query.get(vs.stock_item_id)
        if item:
            price = Decimal(str(item.purchase_price_gnf or 0))
            total_quantity += quantity
            total_value += quantity * price
    
    # Mouvements dans la période (filtrés par région)
    movements_query = StockMovement.query
    movements_query = filter_stock_movements_by_region(movements_query)
    if start_date:
        movements_query = movements_query.filter(StockMovement.movement_date >= start_date)
    if end_date:
        movements_query = movements_query.filter(StockMovement.movement_date <= end_date)
    
    movements = movements_query.all()
    
    entries = sum(float(m.quantity) for m in movements if float(m.quantity) > 0)
    exits = sum(abs(float(m.quantity)) for m in movements if float(m.quantity) < 0)
    
    # Réceptions dans la période (filtrées par dépôt/région)
    receptions_query = Reception.query
    if start_date:
        receptions_query = receptions_query.filter(Reception.reception_date >= start_date)
    if end_date:
        receptions_query = receptions_query.filter(Reception.reception_date <= end_date)
    
    # Filtrer les réceptions par dépôt/région
    from utils_region_filter import get_user_region_id
    region_id = get_user_region_id()
    if region_id is not None:
        depot_ids = [d.id for d in filter_depots_by_region(Depot.query).all()]
        if depot_ids:
            receptions_query = receptions_query.filter(Reception.depot_id.in_(depot_ids))
        else:
            receptions_query = receptions_query.filter(False)
    
    receptions_count = receptions_query.count()
    
    # Articles en stock faible (moins de 10 unités) - filtrés par région
    low_stock_items = []
    for item in StockItem.query.filter_by(is_active=True).all():
        # Calculer le stock total pour cet article (filtré par région)
        total_item_stock = sum(
            float(ds.quantity or 0) for ds in depot_stocks if ds.stock_item_id == item.id
        ) + sum(
            float(vs.quantity or 0) for vs in vehicle_stocks if vs.stock_item_id == item.id
        )
        if total_item_stock < 10:
            low_stock_items.append({
                'item': item,
                'quantity': total_item_stock
            })
    
    return {
        'total_quantity': float(total_quantity),
        'total_value': float(total_value),
        'entries': float(entries),
        'exits': float(exits),
        'receptions_count': receptions_count,
        'low_stock_items_count': len(low_stock_items),
        'low_stock_items': low_stock_items[:10]  # Top 10
    }

def calculate_vehicle_kpis(start_date=None, end_date=None):
    """Calcule les KPIs pour la flotte avec filtrage par région"""
    from utils_region_filter import filter_vehicles_by_region, get_user_region_id
    
    # Véhicules filtrés par région
    vehicles_query = Vehicle.query
    vehicles_query = filter_vehicles_by_region(vehicles_query)
    total_vehicles = vehicles_query.count()
    
    active_vehicles_query = Vehicle.query.filter_by(status='active')
    active_vehicles_query = filter_vehicles_by_region(active_vehicles_query)
    active_vehicles = active_vehicles_query.count()
    
    # Récupérer les IDs des véhicules de la région
    vehicle_ids = [v.id for v in active_vehicles_query.all()]
    
    # Documents expirés ou expirant bientôt (filtrés par véhicule/région)
    today = date.today()
    if vehicle_ids:
        expired_docs = VehicleDocument.query.filter(
            VehicleDocument.vehicle_id.in_(vehicle_ids),
            VehicleDocument.expiry_date < today
        ).count()
        expiring_soon = VehicleDocument.query.filter(
            VehicleDocument.vehicle_id.in_(vehicle_ids),
            VehicleDocument.expiry_date >= today,
            VehicleDocument.expiry_date <= today + timedelta(days=15)
        ).count()
        
        # Maintenances dues (filtrées par véhicule/région)
        due_maintenances = VehicleMaintenance.query.filter(
            VehicleMaintenance.vehicle_id.in_(vehicle_ids),
            VehicleMaintenance.status == 'planned',
            VehicleMaintenance.planned_date <= today
        ).count()
    else:
        expired_docs = 0
        expiring_soon = 0
        due_maintenances = 0
    
    return {
        'total_vehicles': total_vehicles,
        'active_vehicles': active_vehicles,
        'expired_documents': expired_docs,
        'expiring_soon_documents': expiring_soon,
        'due_maintenances': due_maintenances
    }

def calculate_promotion_kpis(start_date=None, end_date=None):
    """Calcule les KPIs pour la promotion avec filtrage par région"""
    from utils_region_filter import filter_teams_by_region, filter_members_by_region, filter_sales_by_region, get_user_region_id
    from sqlalchemy import case
    
    # Équipes filtrées par région
    teams_query = PromotionTeam.query.filter_by(is_active=True)
    teams_query = filter_teams_by_region(teams_query)
    total_teams = teams_query.count()
    
    # Membres filtrés par région (utiliser count_members_safe pour éviter les colonnes manquantes)
    try:
        from promotion import count_members_safe
        total_members = count_members_safe(is_active=True)
    except Exception as e:
        print(f"⚠️ Erreur count_members dans calculate_promotion_kpis: {e}")
        # Fallback: requête SQL directe
        try:
            from utils_region_filter import get_user_region_id
            from sqlalchemy import text
            region_id = get_user_region_id()
            if region_id is not None:
                sql = """
                    SELECT COUNT(*) 
                    FROM promotion_members pm
                    WHERE pm.is_active = true
                    AND EXISTS (
                        SELECT 1 FROM promotion_teams pt
                        JOIN users u ON pt.team_leader_id = u.id
                        WHERE pt.id = pm.team_id AND u.region_id = :region_id
                    )
                """
                result = db.session.execute(text(sql), {'region_id': region_id})
                total_members = result.scalar() or 0
            else:
                total_members = PromotionMember.query.filter_by(is_active=True).count()
        except:
            total_members = 0
    
    # Ventes filtrées par région dans la période
    sales_query = PromotionSale.query
    sales_query = filter_sales_by_region(sales_query)
    if start_date:
        sales_query = sales_query.filter(PromotionSale.sale_date >= start_date)
    if end_date:
        sales_query = sales_query.filter(PromotionSale.sale_date <= end_date)
    
    # Vérifier si transaction_type existe
    try:
        check_type_sql = """SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS 
                           WHERE TABLE_SCHEMA = DATABASE() 
                           AND TABLE_NAME = 'promotion_sales' 
                           AND COLUMN_NAME = 'transaction_type'"""
        has_transaction_type = db.session.execute(text(check_type_sql)).scalar() > 0
    except:
        has_transaction_type = False
    
    # Calculer les statistiques de ventes
    if has_transaction_type:
        # Enlèvements
        enlevements_query = sales_query.filter(PromotionSale.transaction_type == 'enlevement')
        total_enlevements = enlevements_query.count()
        revenue_enlevements = db.session.query(func.sum(PromotionSale.total_amount_gnf))\
            .join(PromotionMember, PromotionSale.member_id == PromotionMember.id)\
            .join(PromotionTeam, PromotionMember.team_id == PromotionTeam.id)\
            .join(User, PromotionTeam.team_leader_id == User.id)\
            .filter(
                PromotionSale.sale_date >= start_date if start_date else True,
                PromotionSale.sale_date <= end_date if end_date else True,
                PromotionSale.transaction_type == 'enlevement'
            )
        if get_user_region_id() is not None:
            revenue_enlevements = revenue_enlevements.filter(User.region_id == get_user_region_id())
        revenue_enlevements = revenue_enlevements.scalar() or Decimal("0.00")
        
        # Retours
        retours_query = sales_query.filter(PromotionSale.transaction_type == 'retour')
        total_retours = retours_query.count()
        revenue_retours = db.session.query(func.sum(PromotionSale.total_amount_gnf))\
            .join(PromotionMember, PromotionSale.member_id == PromotionMember.id)\
            .join(PromotionTeam, PromotionMember.team_id == PromotionTeam.id)\
            .join(User, PromotionTeam.team_leader_id == User.id)\
            .filter(
                PromotionSale.sale_date >= start_date if start_date else True,
                PromotionSale.sale_date <= end_date if end_date else True,
                PromotionSale.transaction_type == 'retour'
            )
        if get_user_region_id() is not None:
            revenue_retours = revenue_retours.filter(User.region_id == get_user_region_id())
        revenue_retours = revenue_retours.scalar() or Decimal("0.00")
        
        # CA Net
        ca_net = revenue_enlevements - revenue_retours
        
        # Commissions
        commission_enlevements = db.session.query(func.sum(PromotionSale.commission_gnf))\
            .join(PromotionMember, PromotionSale.member_id == PromotionMember.id)\
            .join(PromotionTeam, PromotionMember.team_id == PromotionTeam.id)\
            .join(User, PromotionTeam.team_leader_id == User.id)\
            .filter(
                PromotionSale.sale_date >= start_date if start_date else True,
                PromotionSale.sale_date <= end_date if end_date else True,
                PromotionSale.transaction_type == 'enlevement'
            )
        if get_user_region_id() is not None:
            commission_enlevements = commission_enlevements.filter(User.region_id == get_user_region_id())
        commission_enlevements = commission_enlevements.scalar() or Decimal("0.00")
        
        commission_retours = db.session.query(func.sum(PromotionSale.commission_gnf))\
            .join(PromotionMember, PromotionSale.member_id == PromotionMember.id)\
            .join(PromotionTeam, PromotionMember.team_id == PromotionTeam.id)\
            .join(User, PromotionTeam.team_leader_id == User.id)\
            .filter(
                PromotionSale.sale_date >= start_date if start_date else True,
                PromotionSale.sale_date <= end_date if end_date else True,
                PromotionSale.transaction_type == 'retour'
            )
        if get_user_region_id() is not None:
            commission_retours = commission_retours.filter(User.region_id == get_user_region_id())
        commission_retours = commission_retours.scalar() or Decimal("0.00")
        
        commission_nette = commission_enlevements - commission_retours
    else:
        total_enlevements = sales_query.count()
        total_retours = 0
        revenue_enlevements = db.session.query(func.sum(PromotionSale.total_amount_gnf))\
            .join(PromotionMember, PromotionSale.member_id == PromotionMember.id)\
            .join(PromotionTeam, PromotionMember.team_id == PromotionTeam.id)\
            .join(User, PromotionTeam.team_leader_id == User.id)\
            .filter(
                PromotionSale.sale_date >= start_date if start_date else True,
                PromotionSale.sale_date <= end_date if end_date else True
            )
        if get_user_region_id() is not None:
            revenue_enlevements = revenue_enlevements.filter(User.region_id == get_user_region_id())
        revenue_enlevements = revenue_enlevements.scalar() or Decimal("0.00")
        revenue_retours = Decimal("0.00")
        ca_net = revenue_enlevements
        
        commission_enlevements = db.session.query(func.sum(PromotionSale.commission_gnf))\
            .join(PromotionMember, PromotionSale.member_id == PromotionMember.id)\
            .join(PromotionTeam, PromotionMember.team_id == PromotionTeam.id)\
            .join(User, PromotionTeam.team_leader_id == User.id)\
            .filter(
                PromotionSale.sale_date >= start_date if start_date else True,
                PromotionSale.sale_date <= end_date if end_date else True
            )
        if get_user_region_id() is not None:
            commission_enlevements = commission_enlevements.filter(User.region_id == get_user_region_id())
        commission_enlevements = commission_enlevements.scalar() or Decimal("0.00")
        commission_retours = Decimal("0.00")
        commission_nette = commission_enlevements
    
    # Résultat net
    resultat_net = ca_net - commission_nette
    
    return {
        'total_teams': total_teams,
        'total_members': total_members,
        'total_enlevements': total_enlevements,
        'total_retours': total_retours,
        'total_sales': total_enlevements + total_retours,
        'revenue_enlevements': float(revenue_enlevements),
        'revenue_retours': float(revenue_retours),
        'ca_net': float(ca_net),
        'commission_enlevements': float(commission_enlevements),
        'commission_retours': float(commission_retours),
        'commission_nette': float(commission_nette),
        'resultat_net': float(resultat_net)
    }

def get_alerts():
    """Récupère toutes les alertes automatiques avec filtrage par région"""
    from utils_region_filter import (
        filter_depot_stocks_by_region, filter_vehicle_stocks_by_region,
        filter_vehicles_by_region, get_user_region_id
    )
    
    alerts = []
    today = date.today()
    
    # Alertes stocks faibles (filtrées par région)
    low_stock_items = []
    depot_stocks_query = DepotStock.query
    depot_stocks_query = filter_depot_stocks_by_region(depot_stocks_query)
    depot_stocks_list = depot_stocks_query.all()
    
    vehicle_stocks_query = VehicleStock.query
    vehicle_stocks_query = filter_vehicle_stocks_by_region(vehicle_stocks_query)
    vehicle_stocks_list = vehicle_stocks_query.all()
    
    for item in StockItem.query.filter_by(is_active=True).all():
        total_stock = sum(
            float(ds.quantity or 0) for ds in depot_stocks_list if ds.stock_item_id == item.id
        ) + sum(
            float(vs.quantity or 0) for vs in vehicle_stocks_list if vs.stock_item_id == item.id
        )
        if total_stock < 10:
            low_stock_items.append({
                'type': 'low_stock',
                'severity': 'warning',
                'title': f'Stock faible : {item.name}',
                'message': f'Il ne reste que {total_stock:.2f} unités en stock',
                'item_id': item.id,
                'timestamp': datetime.now(UTC)
            })
    
    alerts.extend(low_stock_items[:5])  # Top 5
    
    # Alertes documents expirés (filtrées par véhicule/région)
    vehicles_query = Vehicle.query
    vehicles_query = filter_vehicles_by_region(vehicles_query)
    vehicle_ids = [v.id for v in vehicles_query.all()]
    
    if vehicle_ids:
        expired_docs = VehicleDocument.query.filter(
            VehicleDocument.vehicle_id.in_(vehicle_ids),
            VehicleDocument.expiry_date < today
        ).all()
        for doc in expired_docs[:5]:  # Top 5
            vehicle = Vehicle.query.get(doc.vehicle_id)
            alerts.append({
                'type': 'expired_document',
                'severity': 'error',
                'title': f'Document expiré : {doc.document_type}',
                'message': f'Le document {doc.document_type} du véhicule {vehicle.plate_number if vehicle else "N/A"} a expiré le {doc.expiry_date.strftime("%d/%m/%Y")}',
                'vehicle_id': doc.vehicle_id,
                'document_id': doc.id,
                'timestamp': datetime.now(UTC)
            })
        
        # Alertes documents expirant bientôt
        expiring_soon = VehicleDocument.query.filter(
            VehicleDocument.vehicle_id.in_(vehicle_ids),
            VehicleDocument.expiry_date >= today,
            VehicleDocument.expiry_date <= today + timedelta(days=15)
        ).all()
        for doc in expiring_soon[:5]:  # Top 5
            vehicle = Vehicle.query.get(doc.vehicle_id)
            days_left = (doc.expiry_date - today).days
            alerts.append({
                'type': 'expiring_document',
                'severity': 'warning',
                'title': f'Document expirant bientôt : {doc.document_type}',
                'message': f'Le document {doc.document_type} du véhicule {vehicle.plate_number if vehicle else "N/A"} expire dans {days_left} jour(s)',
                'vehicle_id': doc.vehicle_id,
                'document_id': doc.id,
                'timestamp': datetime.now(UTC)
            })
        
        # Alertes maintenances dues
        due_maintenances = VehicleMaintenance.query.filter(
            VehicleMaintenance.vehicle_id.in_(vehicle_ids),
            VehicleMaintenance.status == 'planned',
            VehicleMaintenance.planned_date <= today
        ).all()
        for maint in due_maintenances[:5]:  # Top 5
            vehicle = Vehicle.query.get(maint.vehicle_id)
            alerts.append({
                'type': 'due_maintenance',
                'severity': 'warning',
                'title': f'Maintenance due : {maint.maintenance_type}',
                'message': f'La maintenance {maint.maintenance_type} du véhicule {vehicle.plate_number if vehicle else "N/A"} est due',
                'vehicle_id': maint.vehicle_id,
                'maintenance_id': maint.id,
                'timestamp': datetime.now(UTC)
            })
    
    # Trier par timestamp (plus récent en premier)
    alerts.sort(key=lambda x: x['timestamp'], reverse=True)
    
    return alerts[:20]  # Retourner les 20 plus récentes

@analytics_bp.route('/dashboard')
@login_required
def dashboard():
    """Tableau de bord analytique principal"""
    if not has_permission(current_user, 'analytics.read'):
        from flask import flash, redirect, url_for
        flash('Vous n\'avez pas la permission d\'accéder à cette page', 'error')
        return redirect(url_for('index'))
    
    # Récupérer la période sélectionnée
    period = request.args.get('period', 'month')
    start_date, end_date = get_period_dates(period)
    
    # Calculer tous les KPIs
    simulation_kpis = calculate_simulation_kpis(start_date, end_date)
    forecast_kpis = calculate_forecast_kpis(start_date, end_date)
    stock_kpis = calculate_stock_kpis(start_date, end_date)
    vehicle_kpis = calculate_vehicle_kpis(start_date, end_date)
    promotion_kpis = calculate_promotion_kpis(start_date, end_date)
    
    # Récupérer les alertes
    alerts = get_alerts()
    
    # Calculer les KPIs de la période précédente pour comparaison
    try:
        prev_start, prev_end = get_period_dates('previous_' + period)
        prev_simulation_kpis = calculate_simulation_kpis(prev_start, prev_end)
        prev_forecast_kpis = calculate_forecast_kpis(prev_start, prev_end)
        prev_stock_kpis = calculate_stock_kpis(prev_start, prev_end)
    except Exception as e:
        # En cas d'erreur, utiliser des valeurs par défaut
        print(f"⚠️ Erreur lors du calcul des KPIs précédents: {e}")
        prev_simulation_kpis = {'total_simulations': 0, 'total_margin': 0, 'margin_percentage': 0}
        prev_forecast_kpis = {'total_forecasts': 0, 'accuracy': 0}
        prev_stock_kpis = {'total_value': 0}
    
    # Calculer les KPIs de promotion de la période précédente pour comparaison
    try:
        prev_promotion_kpis = calculate_promotion_kpis(prev_start, prev_end)
    except Exception as e:
        print(f"⚠️ Erreur lors du calcul des KPIs promotion précédents: {e}")
        prev_promotion_kpis = {
            'total_teams': 0, 'total_members': 0, 'ca_net': 0,
            'commission_nette': 0, 'resultat_net': 0
        }
    
    # Récupérer la région de l'utilisateur pour l'affichage
    from utils_region_filter import get_user_region_id
    user_region_id = get_user_region_id()
    user_region_name = None
    if user_region_id:
        user_region = Region.query.get(user_region_id)
        user_region_name = user_region.name if user_region else None
    
    # Vérifier si l'utilisateur peut voir les valeurs de stock
    can_view_values = can_view_stock_values(current_user)
    
    return render_template('analytics/dashboard.html',
                         simulation_kpis=simulation_kpis,
                         forecast_kpis=forecast_kpis,
                         stock_kpis=stock_kpis,
                         vehicle_kpis=vehicle_kpis,
                         promotion_kpis=promotion_kpis,
                         alerts=alerts,
                         prev_simulation_kpis=prev_simulation_kpis,
                         prev_forecast_kpis=prev_forecast_kpis,
                         prev_stock_kpis=prev_stock_kpis,
                         prev_promotion_kpis=prev_promotion_kpis,
                         period=period,
                         start_date=start_date,
                         end_date=end_date,
                         user_region_name=user_region_name,
                         can_view_stock_values=can_view_values)

@analytics_bp.route('/api/kpis')
@login_required
def api_kpis():
    """API pour récupérer les KPIs en JSON"""
    if not has_permission(current_user, 'analytics.read'):
        return jsonify({'error': 'Permission denied'}), 403
    
    period = request.args.get('period', 'month')
    start_date, end_date = get_period_dates(period)
    
    return jsonify({
        'simulation': calculate_simulation_kpis(start_date, end_date),
        'forecast': calculate_forecast_kpis(start_date, end_date),
        'stock': calculate_stock_kpis(start_date, end_date),
        'vehicle': calculate_vehicle_kpis(start_date, end_date),
        'period': period,
        'start_date': start_date.isoformat(),
        'end_date': end_date.isoformat()
    })

@analytics_bp.route('/api/charts/revenue')
@login_required
def api_charts_revenue():
    """API pour les données de graphique de revenus"""
    if not has_permission(current_user, 'analytics.read'):
        return jsonify({'error': 'Permission denied'}), 403
    
    period = request.args.get('period', 'month')
    start_date, end_date = get_period_dates(period)
    
    # Générer les données par jour/semaine/mois selon la période
    data = []
    labels = []
    
    if period in ['today', 'week']:
        # Par jour
        current = start_date
        while current <= end_date:
            day_start = datetime.combine(current, datetime.min.time()).replace(tzinfo=UTC)
            day_end = datetime.combine(current, datetime.max.time()).replace(tzinfo=UTC)
            
            kpis = calculate_simulation_kpis(current, current)
            data.append(kpis['total_selling'])
            labels.append(current.strftime('%d/%m'))
            
            current += timedelta(days=1)
    elif period == 'month':
        # Par semaine
        current = start_date
        week_num = 1
        while current <= end_date:
            week_end = min(current + timedelta(days=6), end_date)
            kpis = calculate_simulation_kpis(current, week_end)
            data.append(kpis['total_selling'])
            labels.append(f'Semaine {week_num}')
            current = week_end + timedelta(days=1)
            week_num += 1
    else:
        # Par mois
        current = start_date
        month_num = 1
        while current <= end_date:
            if current.month == 12:
                month_end = current.replace(day=31)
            else:
                month_end = (current.replace(month=current.month + 1, day=1) - timedelta(days=1))
            month_end = min(month_end, end_date)
            
            kpis = calculate_simulation_kpis(current, month_end)
            data.append(kpis['total_selling'])
            labels.append(current.strftime('%m/%Y'))
            
            if current.month == 12:
                current = current.replace(year=current.year + 1, month=1, day=1)
            else:
                current = current.replace(month=current.month + 1, day=1)
    
    return jsonify({
        'labels': labels,
        'data': data
    })

@analytics_bp.route('/api/charts/margin')
@login_required
def api_charts_margin():
    """API pour les données de graphique de marge"""
    if not has_permission(current_user, 'analytics.read'):
        return jsonify({'error': 'Permission denied'}), 403
    
    period = request.args.get('period', 'month')
    start_date, end_date = get_period_dates(period)
    
    # Similaire à revenue mais pour les marges
    data = []
    labels = []
    
    if period in ['today', 'week']:
        current = start_date
        while current <= end_date:
            kpis = calculate_simulation_kpis(current, current)
            data.append(kpis['total_margin'])
            labels.append(current.strftime('%d/%m'))
            current += timedelta(days=1)
    elif period == 'month':
        current = start_date
        week_num = 1
        while current <= end_date:
            week_end = min(current + timedelta(days=6), end_date)
            kpis = calculate_simulation_kpis(current, week_end)
            data.append(kpis['total_margin'])
            labels.append(f'Semaine {week_num}')
            current = week_end + timedelta(days=1)
            week_num += 1
    else:
        current = start_date
        while current <= end_date:
            if current.month == 12:
                month_end = current.replace(day=31)
            else:
                month_end = (current.replace(month=current.month + 1, day=1) - timedelta(days=1))
            month_end = min(month_end, end_date)
            
            kpis = calculate_simulation_kpis(current, month_end)
            data.append(kpis['total_margin'])
            labels.append(current.strftime('%m/%Y'))
            
            if current.month == 12:
                current = current.replace(year=current.year + 1, month=1, day=1)
            else:
                current = current.replace(month=current.month + 1, day=1)
    
    return jsonify({
        'labels': labels,
        'data': data
    })

@analytics_bp.route('/api/alerts')
@login_required
def api_alerts():
    """API pour récupérer les alertes"""
    if not has_permission(current_user, 'analytics.read'):
        return jsonify({'error': 'Permission denied'}), 403
    
    alerts = get_alerts()
    
    # Convertir les datetime en ISO format pour JSON
    for alert in alerts:
        if 'timestamp' in alert:
            alert['timestamp'] = alert['timestamp'].isoformat()
    
    return jsonify({'alerts': alerts})

