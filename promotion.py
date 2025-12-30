#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module Promotion - Import Profit Pro
Gestion des équipes de promotion, gammes, ventes et retours
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from datetime import datetime, date, timedelta, UTC
from decimal import Decimal
from sqlalchemy import func, or_, and_, text, case
from sqlalchemy.orm import joinedload, load_only
from functools import lru_cache
import time
from models import (
    db, PromotionGamme, PromotionTeam, PromotionMember, PromotionSale, 
    PromotionReturn, PromotionMemberLocation, PromotionMemberStock, PromotionTeamStock, 
    PromotionSupervisorStock, PromotionStockMovement, PromotionDailyClosure, User, Role, Article, promotion_gamme_articles
)
from auth import has_permission

# Créer le blueprint
promotion_bp = Blueprint('promotion', __name__, url_prefix='/promotion')

# =========================================================
# FONCTIONS HELPER
# =========================================================

def get_low_stock_alerts(threshold=10):
    """Récupère les alertes de stock faible"""
    alerts = []
    
    try:
        # Stock superviseur faible
        supervisor_stocks = PromotionSupervisorStock.query.filter(
            PromotionSupervisorStock.quantity <= threshold
        ).all()
        
        for stock in supervisor_stocks:
            gamme = PromotionGamme.query.get(stock.gamme_id)
            if gamme:
                alerts.append({
                    'type': 'supervisor',
                    'level': 'critical' if stock.quantity == 0 else 'warning',
                    'message': f"Stock superviseur faible: {stock.quantity} unité(s) de {gamme.name}",
                    'gamme_id': stock.gamme_id,
                    'gamme_name': gamme.name,
                    'quantity': stock.quantity,
                    'threshold': threshold
                })
        
        # Stock équipe faible
        team_stocks = PromotionTeamStock.query.filter(
            PromotionTeamStock.quantity <= threshold
        ).all()
        
        for stock in team_stocks:
            gamme = PromotionGamme.query.get(stock.gamme_id)
            team = PromotionTeam.query.get(stock.team_id)
            if gamme and team:
                alerts.append({
                    'type': 'team',
                    'level': 'critical' if stock.quantity == 0 else 'warning',
                    'message': f"Stock équipe '{team.name}' faible: {stock.quantity} unité(s) de {gamme.name}",
                    'team_id': stock.team_id,
                    'team_name': team.name,
                    'gamme_id': stock.gamme_id,
                    'gamme_name': gamme.name,
                    'quantity': stock.quantity,
                    'threshold': threshold
                })
        
        # Stock membre faible
        member_stocks = PromotionMemberStock.query.filter(
            PromotionMemberStock.quantity <= threshold
        ).all()
        
        for stock in member_stocks:
            gamme = PromotionGamme.query.get(stock.gamme_id)
            member = PromotionMember.query.get(stock.member_id)
            if gamme and member:
                alerts.append({
                    'type': 'member',
                    'level': 'critical' if stock.quantity == 0 else 'warning',
                    'message': f"Stock membre '{member.full_name}' faible: {stock.quantity} unité(s) de {gamme.name}",
                    'member_id': stock.member_id,
                    'member_name': member.full_name,
                    'gamme_id': stock.gamme_id,
                    'gamme_name': gamme.name,
                    'quantity': stock.quantity,
                    'threshold': threshold
                })
        
    except Exception as e:
        print(f"Erreur lors de la récupération des alertes de stock: {e}")
    
    return alerts

# Cache pour les vérifications de colonnes (durée: 1 heure)
_column_cache = {}
_column_cache_time = {}

def has_transaction_type_column_cached():
    """Vérifie si la colonne transaction_type existe (avec cache)"""
    cache_key = 'has_transaction_type'
    current_time = time.time()
    
    # Vérifier le cache (valide pendant 1 heure)
    if cache_key in _column_cache:
        if current_time - _column_cache_time.get(cache_key, 0) < 3600:
            return _column_cache[cache_key]
    
    # Requête à la base de données
    try:
        check_type_sql = """SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS 
                           WHERE TABLE_SCHEMA = DATABASE() 
                           AND TABLE_NAME = 'promotion_sales' 
                           AND COLUMN_NAME = 'transaction_type'"""
        result = db.session.execute(text(check_type_sql)).scalar() > 0
        
        # Mettre en cache
        _column_cache[cache_key] = result
        _column_cache_time[cache_key] = current_time
        
        return result
    except Exception as e:
        print(f"Erreur vérification colonne transaction_type: {e}")
        return False

def load_teams_batch(team_ids):
    """Charge les équipes en batch pour éviter N+1 queries"""
    if not team_ids:
        return {}
    teams = PromotionTeam.query.options(
        load_only(PromotionTeam.id, PromotionTeam.name)
    ).filter(PromotionTeam.id.in_(team_ids)).all()
    return {team.id: team for team in teams}

def load_members_batch(member_ids):
    """Charge les membres en batch pour éviter N+1 queries"""
    if not member_ids:
        return {}
    members = PromotionMember.query.options(
        load_only(PromotionMember.id, PromotionMember.full_name, PromotionMember.team_id)
    ).filter(PromotionMember.id.in_(member_ids)).all()
    return {member.id: member for member in members}

def load_gammes_batch(gamme_ids):
    """Charge les gammes en batch pour éviter N+1 queries"""
    if not gamme_ids:
        return {}
    gammes = PromotionGamme.query.options(
        load_only(PromotionGamme.id, PromotionGamme.name, PromotionGamme.selling_price_gnf)
    ).filter(PromotionGamme.id.in_(gamme_ids)).all()
    return {gamme.id: gamme for gamme in gammes}

def load_member_stats_batch(member_ids):
    """Charge les statistiques de ventes pour plusieurs membres en une seule requête"""
    if not member_ids:
        return {}
    
    # Vérifier si transaction_type existe
    try:
        has_transaction_type = has_transaction_type_column_cached()
    except:
        has_transaction_type = False
    
    stats_dict = {mid: {'sales_count': 0, 'total_commission': Decimal("0.00")} for mid in member_ids}
    
    try:
        if has_transaction_type:
            # Enlèvements
            enlevements = db.session.query(
                PromotionSale.member_id,
                func.sum(PromotionSale.quantity).label('total_qty'),
                func.sum(PromotionSale.commission_gnf).label('total_commission')
            ).filter(
                PromotionSale.member_id.in_(member_ids),
                PromotionSale.transaction_type == 'enlevement'
            ).group_by(PromotionSale.member_id).all()
            
            # Retours
            retours = db.session.query(
                PromotionSale.member_id,
                func.sum(PromotionSale.quantity).label('total_qty'),
                func.sum(PromotionSale.commission_gnf).label('total_commission')
            ).filter(
                PromotionSale.member_id.in_(member_ids),
                PromotionSale.transaction_type == 'retour'
            ).group_by(PromotionSale.member_id).all()
            
            # Calculer les totaux
            for row in enlevements:
                member_id = row.member_id
                stats_dict[member_id]['sales_count'] += (row.total_qty or 0)
                stats_dict[member_id]['total_commission'] += (row.total_commission or Decimal("0.00"))
            
            for row in retours:
                member_id = row.member_id
                stats_dict[member_id]['sales_count'] -= (row.total_qty or 0)
                stats_dict[member_id]['total_commission'] -= (row.total_commission or Decimal("0.00"))
        else:
            # Sans distinction
            sales_stats = db.session.query(
                PromotionSale.member_id,
                func.sum(PromotionSale.quantity).label('total_qty'),
                func.sum(PromotionSale.commission_gnf).label('total_commission')
            ).filter(
                PromotionSale.member_id.in_(member_ids)
            ).group_by(PromotionSale.member_id).all()
            
            for row in sales_stats:
                member_id = row.member_id
                stats_dict[member_id]['sales_count'] = row.total_qty or 0
                stats_dict[member_id]['total_commission'] = row.total_commission or Decimal("0.00")
    except Exception as e:
        print(f"Erreur lors du chargement des stats batch: {e}")
    
    return stats_dict

def record_stock_movement(movement_type, gamme_id, quantity, quantity_change, 
                         from_supervisor_id=None, from_team_id=None, from_member_id=None,
                         to_supervisor_id=None, to_team_id=None, to_member_id=None,
                         sale_id=None, return_id=None, performed_by_id=None, notes=None, movement_date=None):
    """Enregistre un mouvement de stock dans l'historique"""
    try:
        # Vérifier si la table existe
        try:
            # Test simple pour voir si la table existe
            db.session.execute(text("SELECT 1 FROM promotion_stock_movements LIMIT 1"))
        except Exception:
            # La table n'existe pas encore
            print(f"⚠️ La table promotion_stock_movements n'existe pas encore. Exécutez le script SQL pour la créer.")
            return False
        
        # S'assurer que performed_by_id est défini
        if not performed_by_id:
            if current_user and current_user.is_authenticated:
                performed_by_id = current_user.id
            else:
                print(f"⚠️ Impossible d'enregistrer le mouvement : aucun utilisateur authentifié")
                return False
        
        movement = PromotionStockMovement(
            movement_type=movement_type,
            movement_date=movement_date or datetime.now(UTC),
            gamme_id=gamme_id,
            quantity=abs(quantity),  # Toujours positif
            quantity_change=quantity_change,  # Peut être négatif
            from_supervisor_id=from_supervisor_id,
            from_team_id=from_team_id,
            from_member_id=from_member_id,
            to_supervisor_id=to_supervisor_id,
            to_team_id=to_team_id,
            to_member_id=to_member_id,
            sale_id=sale_id,
            return_id=return_id,
            performed_by_id=performed_by_id,
            notes=notes
        )
        db.session.add(movement)
        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        print(f"Erreur lors de l'enregistrement du mouvement de stock: {e}")
        import traceback
        traceback.print_exc()
        return False

def update_member_stock(member_id, gamme_id, quantity_change, operation='enlevement', sale_id=None, return_id=None, movement_date=None):
    """
    Met à jour le stock d'un membre pour une gamme donnée.
    - operation='enlevement' : augmente le stock (quantité positive)
    - operation='retour' : diminue le stock (quantité négative)
    """
    try:
        # Vérifier si la table existe en essayant une requête simple
        try:
            stock = PromotionMemberStock.query.filter_by(
                member_id=member_id,
                gamme_id=gamme_id
            ).first()
            
            if not stock:
                stock = PromotionMemberStock(
                    member_id=member_id,
                    gamme_id=gamme_id,
                    quantity=0
                )
                db.session.add(stock)
            
            if operation == 'enlevement':
                stock.quantity += quantity_change
            elif operation == 'retour':
                stock.quantity -= quantity_change
                if stock.quantity < 0:
                    stock.quantity = 0
            
            stock.last_updated = datetime.now(UTC)
            db.session.commit()
            
            # Enregistrer le mouvement
            try:
                if operation == 'enlevement':
                    record_stock_movement(
                        movement_type='enlevement',
                        gamme_id=gamme_id,
                        quantity=stock.quantity,
                        quantity_change=quantity_change,
                        to_member_id=member_id,
                        sale_id=sale_id,
                        movement_date=movement_date
                    )
                elif operation == 'retour':
                    record_stock_movement(
                        movement_type='retour',
                        gamme_id=gamme_id,
                        quantity=stock.quantity,
                        quantity_change=-quantity_change,  # Négatif car c'est un retour
                        from_member_id=member_id,
                        return_id=return_id,
                        movement_date=movement_date
                    )
            except Exception as e:
                print(f"Erreur lors de l'enregistrement du mouvement pour le membre: {e}")
            
            return True
        except Exception as e:
            # Si la table n'existe pas encore, on ignore silencieusement
            print(f"DEBUG update_member_stock: Table peut-être absente: {e}")
            db.session.rollback()
            return False
    except Exception as e:
        db.session.rollback()
        print(f"Erreur lors de la mise à jour du stock: {e}")
        return False

def get_supervisor_stock(supervisor_id):
    """Récupère le stock actuel du superviseur"""
    try:
        stocks = PromotionSupervisorStock.query.filter_by(supervisor_id=supervisor_id).all()
        return {stock.gamme_id: stock.quantity for stock in stocks}
    except Exception:
        return {}

def update_supervisor_stock(supervisor_id, gamme_id, quantity_change, operation='add', movement_type='approvisionnement', to_team_id=None, movement_date=None, notes=None):
    """
    Met à jour le stock du superviseur pour une gamme donnée.
    - operation='add' : ajoute au stock (quantité positive)
    - operation='subtract' : soustrait du stock (quantité négative)
    """
    try:
        stock = PromotionSupervisorStock.query.filter_by(
            supervisor_id=supervisor_id,
            gamme_id=gamme_id
        ).first()
        
        if not stock:
            if operation == 'add' and quantity_change > 0:
                stock = PromotionSupervisorStock(
                    supervisor_id=supervisor_id,
                    gamme_id=gamme_id,
                    quantity=quantity_change
                )
                db.session.add(stock)
            else:
                return False
        else:
            if operation == 'add':
                stock.quantity += quantity_change
            elif operation == 'subtract':
                stock.quantity -= quantity_change
                if stock.quantity < 0:
                    stock.quantity = 0
        
        stock.last_updated = datetime.now(UTC)
        db.session.commit()
        
        # Enregistrer le mouvement
        try:
            if operation == 'subtract':
                record_stock_movement(
                    movement_type=movement_type or 'approvisionnement',
                    gamme_id=gamme_id,
                    quantity=stock.quantity,
                    quantity_change=-quantity_change,  # Négatif car on soustrait
                    from_supervisor_id=supervisor_id,
                    to_team_id=to_team_id,
                    movement_date=movement_date,
                    notes=notes
                )
            elif operation == 'add':
                record_stock_movement(
                    movement_type='reception',
                    gamme_id=gamme_id,
                    quantity=stock.quantity,
                    quantity_change=quantity_change,
                    to_supervisor_id=supervisor_id,
                    movement_date=movement_date,
                    notes=notes
                )
        except Exception as e:
            print(f"Erreur lors de l'enregistrement du mouvement pour le superviseur: {e}")
        
        return True
    except Exception as e:
        db.session.rollback()
        print(f"Erreur lors de la mise à jour du stock du superviseur: {e}")
        return False

def get_team_stock(team_id):
    """Récupère le stock actuel d'une équipe (format simple: {gamme_id: quantity})"""
    try:
        stocks = PromotionTeamStock.query.filter_by(team_id=team_id).all()
        result = {stock.gamme_id: stock.quantity for stock in stocks}
        print(f"DEBUG get_team_stock({team_id}): {len(stocks)} enregistrement(s) trouvé(s)")
        for stock in stocks:
            print(f"  - Gamme ID {stock.gamme_id}: {stock.quantity} unités")
        return result
    except Exception as e:
        print(f"❌ Erreur lors de la récupération du stock de l'équipe {team_id}: {e}")
        import traceback
        traceback.print_exc()
        return {}

def get_team_stock_details(team_id):
    """Récupère le stock actuel d'une équipe avec détails (quantity et last_updated)"""
    try:
        stocks = PromotionTeamStock.query.filter_by(team_id=team_id).all()
        result = {}
        for stock in stocks:
            result[stock.gamme_id] = {
                'quantity': stock.quantity,
                'last_updated': stock.last_updated if hasattr(stock, 'last_updated') else None
            }
        return result
    except Exception as e:
        print(f"Erreur lors de la récupération des détails du stock de l'équipe {team_id}: {e}")
        import traceback
        traceback.print_exc()
        return {}

def update_team_stock(team_id, gamme_id, quantity_change, operation='add', movement_type='distribution', from_supervisor_id=None, to_member_id=None, movement_date=None):
    """
    Met à jour le stock d'une équipe pour une gamme donnée.
    - operation='add' : ajoute au stock (quantité positive)
    - operation='subtract' : soustrait du stock (quantité négative)
    """
    try:
        stock = PromotionTeamStock.query.filter_by(
            team_id=team_id,
            gamme_id=gamme_id
        ).first()
        
        if not stock:
            if operation == 'add' and quantity_change > 0:
                stock = PromotionTeamStock(
                    team_id=team_id,
                    gamme_id=gamme_id,
                    quantity=quantity_change
                )
                db.session.add(stock)
            else:
                return False
        else:
            if operation == 'add':
                stock.quantity += quantity_change
            elif operation == 'subtract':
                stock.quantity -= quantity_change
                if stock.quantity < 0:
                    stock.quantity = 0
        
        stock.last_updated = datetime.now(UTC)
        db.session.commit()
        
        # Enregistrer le mouvement
        try:
            if operation == 'add':
                record_stock_movement(
                    movement_type='approvisionnement',
                    gamme_id=gamme_id,
                    quantity=stock.quantity,
                    quantity_change=quantity_change,
                    from_supervisor_id=from_supervisor_id,
                    to_team_id=team_id,
                    movement_date=movement_date
                )
            elif operation == 'subtract':
                record_stock_movement(
                    movement_type=movement_type or 'distribution',
                    gamme_id=gamme_id,
                    quantity=stock.quantity,
                    quantity_change=-quantity_change,  # Négatif car on soustrait
                    from_team_id=team_id,
                    to_member_id=to_member_id,
                    movement_date=movement_date
                )
        except Exception as e:
            print(f"Erreur lors de l'enregistrement du mouvement pour l'équipe: {e}")
        
        return True
    except Exception as e:
        db.session.rollback()
        print(f"Erreur lors de la mise à jour du stock de l'équipe: {e}")
        return False

def get_member_stock(member_id):
    """Récupère le stock actuel d'un membre"""
    try:
        stocks = PromotionMemberStock.query.filter_by(member_id=member_id).all()
        return {stock.gamme_id: stock.quantity for stock in stocks}
    except Exception:
        return {}

def count_members_safe(**filters):
    """Compte les membres de manière sécurisée avec filtrage par région"""
    try:
        from utils_region_filter import filter_members_by_region, get_user_region_id
        from sqlalchemy import text
        
        # Utiliser une requête SQL directe pour éviter de charger les colonnes manquantes
        region_id = get_user_region_id()
        
        # Construire la requête SQL
        base_sql = """
            SELECT COUNT(*) 
            FROM promotion_members pm
            WHERE pm.is_active = true
        """
        params = {}
        
        # Ajouter le filtrage par région si nécessaire
        if region_id is not None:
            base_sql += """
                AND EXISTS (
                    SELECT 1 FROM promotion_teams pt
                    JOIN users u ON pt.team_leader_id = u.id
                    WHERE pt.id = pm.team_id AND u.region_id = :region_id
                )
            """
            params['region_id'] = region_id
        
        # Ajouter les autres filtres
        if 'is_active' in filters:
            # Déjà dans la requête de base
            pass
        
        # Exécuter la requête
        result = db.session.execute(text(base_sql), params)
        return result.scalar() or 0
    except Exception as e:
        print(f"⚠️ Erreur count_members_safe: {e}")
        # Fallback: requête simple sans filtrage par région
        try:
            return PromotionMember.query.filter_by(**filters).count()
        except:
            return 0

def count_sales_safe(date_from=None, date_to=None, **filters):
    """Compte les ventes de manière sécurisée avec filtrage par région"""
    try:
        from utils_region_filter import filter_sales_by_region
        query = PromotionSale.query
        query = filter_sales_by_region(query)  # Filtrage par région
        if date_from:
            query = query.filter(PromotionSale.sale_date >= date_from)
        if date_to:
            query = query.filter(PromotionSale.sale_date <= date_to)
        return query.filter_by(**filters).count()
    except Exception:
        return 0

def get_member_safe(member_id):
    """Récupère un membre de manière sécurisée sans charger les colonnes manquantes"""
    try:
        # Essayer avec load_only pour éviter les colonnes manquantes
        member = PromotionMember.query.options(
            load_only(PromotionMember.id, PromotionMember.full_name, PromotionMember.team_id,
                     PromotionMember.phone, PromotionMember.is_active)
        ).get(member_id)
        if member:
            return member
    except Exception:
        pass
    
    # Fallback: requête SQL directe
    try:
        sql = "SELECT id, full_name, team_id, phone, is_active FROM promotion_members WHERE id = :member_id"
        result = db.session.execute(text(sql), {'member_id': member_id})
        row = result.fetchone()
        if row:
            # Créer un objet minimal
            class MinimalMember:
                def __init__(self, id, full_name, team_id, phone, is_active):
                    self.id = id
                    self.full_name = full_name
                    self.team_id = team_id
                    self.phone = phone
                    self.is_active = is_active
            return MinimalMember(row[0], row[1], row[2], row[3], row[4])
    except Exception:
        pass
    
    return None

def generate_supply_reference():
    """
    Génère une référence unique pour un approvisionnement
    Format: APP-YYYYMMDD-NNNN
    """
    try:
        prefix = 'APP'
        date_str = date.today().strftime('%Y%m%d')
        today_start = datetime.combine(date.today(), datetime.min.time()).replace(tzinfo=UTC)
        
        # Chercher la dernière référence du jour
        next_num = 1
        try:
            sql = """SELECT notes FROM promotion_stock_movements 
                     WHERE notes LIKE :pattern 
                     AND movement_date >= :today_start
                     AND movement_type = 'reception'
                     ORDER BY notes DESC LIMIT 1"""
            result = db.session.execute(text(sql), {
                'pattern': f'{prefix}-{date_str}-%',
                'today_start': today_start
            })
            row = result.fetchone()
            if row and row[0]:
                try:
                    last_num = int(row[0].split('-')[-1])
                    next_num = last_num + 1
                except (ValueError, IndexError):
                    next_num = 1
        except Exception:
            # Compter les mouvements de réception du jour
            try:
                count_sql = """SELECT COUNT(*) FROM promotion_stock_movements 
                              WHERE movement_date >= :today_start
                              AND movement_type = 'reception'"""
                count_result = db.session.execute(text(count_sql), {'today_start': today_start})
                count = count_result.scalar() or 0
                next_num = count + 1
            except Exception:
                import time
                next_num = int(time.time()) % 10000
        
        reference = f"{prefix}-{date_str}-{next_num:04d}"
        return reference
    except Exception as e:
        import time
        prefix = 'APP'
        date_str = date.today().strftime('%Y%m%d')
        timestamp_part = int(time.time() * 1000) % 100000
        return f"{prefix}-{date_str}-{timestamp_part:05d}"

def generate_sale_reference(transaction_type='enlevement'):
    """
    Génère une référence unique pour une vente/retour
    Format: ENL-YYYYMMDD-NNNN pour enlèvements, RET-YYYYMMDD-NNNN pour retours
    """
    try:
        prefix = 'ENL' if transaction_type == 'enlevement' else 'RET'
        date_str = date.today().strftime('%Y%m%d')
        today_start = datetime.combine(date.today(), datetime.min.time()).replace(tzinfo=UTC)
        
        # Vérifier si la colonne reference existe
        check_sql = """SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS 
                      WHERE TABLE_SCHEMA = DATABASE() 
                      AND TABLE_NAME = 'promotion_sales' 
                      AND COLUMN_NAME = 'reference'"""
        has_reference = db.session.execute(text(check_sql)).scalar() > 0
        
        if not has_reference:
            # Si la colonne n'existe pas, utiliser un timestamp
            import time
            timestamp_part = int(time.time() * 1000) % 100000
            return f"{prefix}-{date_str}-{timestamp_part:05d}"
        
        # Stratégie 1: Chercher la dernière référence du jour avec le même préfixe
        next_num = 1
        try:
            sql = """SELECT reference FROM promotion_sales 
                     WHERE reference LIKE :pattern 
                     AND created_at >= :today_start
                     ORDER BY reference DESC LIMIT 1"""
            result = db.session.execute(text(sql), {
                'pattern': f'{prefix}-{date_str}-%',
                'today_start': today_start
            })
            row = result.fetchone()
            if row and row[0]:
                try:
                    last_num = int(row[0].split('-')[-1])
                    next_num = last_num + 1
                except (ValueError, IndexError):
                    next_num = 1
        except Exception:
            # Stratégie 2: Compter toutes les ventes du jour (même sans référence)
            try:
                count_sql = """SELECT COUNT(*) FROM promotion_sales 
                              WHERE created_at >= :today_start"""
                count_result = db.session.execute(text(count_sql), {'today_start': today_start})
                count = count_result.scalar() or 0
                next_num = count + 1
            except Exception:
                # Stratégie 3: Utiliser le dernier ID
                try:
                    last_id_sql = "SELECT MAX(id) FROM promotion_sales"
                    last_id_result = db.session.execute(text(last_id_sql))
                    last_id = last_id_result.scalar() or 0
                    next_num = last_id + 1
                except Exception:
                    # Dernier recours: timestamp
                    import time
                    next_num = int(time.time()) % 10000
        
        # Générer la référence
        reference = f"{prefix}-{date_str}-{next_num:04d}"
        
        # Vérifier l'unicité (si la colonne existe)
        max_attempts = 10
        attempt = 0
        while attempt < max_attempts:
            try:
                check_sql = "SELECT COUNT(*) FROM promotion_sales WHERE reference = :ref"
                check_result = db.session.execute(text(check_sql), {'ref': reference})
                exists = check_result.scalar() or 0
                if exists == 0:
                    break  # Référence unique trouvée
                else:
                    # Incrémenter et réessayer
                    next_num += 1
                    reference = f"{prefix}-{date_str}-{next_num:04d}"
                    attempt += 1
            except Exception:
                # Si la colonne n'existe pas, on ne peut pas vérifier, mais on retourne la référence générée
                break
        
        return reference
    except Exception as e:
        # Fallback absolu avec timestamp pour garantir l'unicité
        import time
        prefix = 'ENL' if transaction_type == 'enlevement' else 'RET'
        date_str = date.today().strftime('%Y%m%d')
        timestamp_part = int(time.time() * 1000) % 100000  # Utiliser millisecondes pour plus d'unicité
        return f"{prefix}-{date_str}-{timestamp_part:05d}"

# =========================================================
# WORKFLOW - PROCESSUS DE PROMOTION
# =========================================================

@promotion_bp.route('/workflow')
@login_required
def workflow():
    """Interface de workflow pour le processus de promotion"""
    if not has_permission(current_user, 'promotion.read'):
        flash("Vous n'avez pas la permission d'accéder à cette page.", "error")
        return redirect(url_for('index'))
    
    today = date.today()
    
    # Récupérer les équipes actives avec leurs responsables (filtrées par région)
    from utils_region_filter import filter_teams_by_region
    try:
        teams_query = PromotionTeam.query.filter_by(is_active=True)
        teams_query = filter_teams_by_region(teams_query)
        teams = teams_query.options(
            joinedload(PromotionTeam.team_leader)
        ).all()
        # S'assurer que team_leader est chargé
        for team in teams:
            if team.team_leader_id and not hasattr(team, '_team_leader_loaded'):
                try:
                    team.team_leader = User.query.options(
                        load_only(User.id, User.username, User.full_name)
                    ).get(team.team_leader_id)
                except Exception:
                    team.team_leader = None
    except Exception as e:
        print(f"DEBUG workflow teams error: {e}")
        teams = PromotionTeam.query.filter_by(is_active=True).all()
        for team in teams:
            team.team_leader = None
    
    # Récupérer les membres actifs avec leurs stocks (filtrés par région)
    from utils_region_filter import filter_members_by_region
    members = []
    try:
        members_query = PromotionMember.query.filter_by(is_active=True)
        members_query = filter_members_by_region(members_query)
        members_query = members_query.options(
            load_only(PromotionMember.id, PromotionMember.full_name, PromotionMember.team_id, PromotionMember.is_active)
        )
        members_list = members_query.all()
        
        for member in members_list:
            # Charger l'équipe du membre
            if member.team_id:
                try:
                    member.team = PromotionTeam.query.options(
                        load_only(PromotionTeam.id, PromotionTeam.name)
                    ).get(member.team_id)
                except Exception:
                    member.team = None
            else:
                member.team = None
            
            # Récupérer le stock actuel
            stock = get_member_stock(member.id)
            total_stock = sum(stock.values())
            
            # Récupérer les ventes du jour (enlèvements - retours)
            try:
                check_type_sql = """SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS 
                                   WHERE TABLE_SCHEMA = DATABASE() 
                                   AND TABLE_NAME = 'promotion_sales' 
                                   AND COLUMN_NAME = 'transaction_type'"""
                has_transaction_type = db.session.execute(text(check_type_sql)).scalar() > 0
                
                if has_transaction_type:
                    enlevements = db.session.query(func.sum(PromotionSale.quantity)).filter(
                        PromotionSale.member_id == member.id,
                        PromotionSale.sale_date == today,
                        PromotionSale.transaction_type == 'enlevement'
                    ).scalar() or 0
                    
                    retours = db.session.query(func.sum(PromotionSale.quantity)).filter(
                        PromotionSale.member_id == member.id,
                        PromotionSale.sale_date == today,
                        PromotionSale.transaction_type == 'retour'
                    ).scalar() or 0
                    
                    ventes_net = enlevements - retours
                else:
                    enlevements = db.session.query(func.sum(PromotionSale.quantity)).filter(
                        PromotionSale.member_id == member.id,
                        PromotionSale.sale_date == today
                    ).scalar() or 0
                    retours = 0
                    ventes_net = enlevements
            except Exception:
                enlevements = 0
                retours = 0
                ventes_net = 0
            
            members.append({
                'member': member,
                'stock': stock,
                'total_stock': total_stock,
                'enlevements': enlevements,
                'retours': retours,
                'ventes_net': ventes_net,
                'status': 'en_mission' if total_stock > 0 else 'au_point'
            })
    except Exception as e:
        print(f"DEBUG workflow members error: {e}")
        members = []
    
    # Statistiques du jour
    try:
        check_type_sql = """SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS 
                          WHERE TABLE_SCHEMA = DATABASE() 
                          AND TABLE_NAME = 'promotion_sales' 
                          AND COLUMN_NAME = 'transaction_type'"""
        has_transaction_type = db.session.execute(text(check_type_sql)).scalar() > 0
        
        if has_transaction_type:
            enlevements_today = db.session.query(func.sum(PromotionSale.quantity)).filter(
                PromotionSale.sale_date == today,
                PromotionSale.transaction_type == 'enlevement'
            ).scalar() or 0
            
            retours_today = db.session.query(func.sum(PromotionSale.quantity)).filter(
                PromotionSale.sale_date == today,
                PromotionSale.transaction_type == 'retour'
            ).scalar() or 0
            
            ventes_net_today = enlevements_today - retours_today
        else:
            ventes_net_today = db.session.query(func.sum(PromotionSale.quantity)).filter(
                PromotionSale.sale_date == today
            ).scalar() or 0
            enlevements_today = ventes_net_today
            retours_today = 0
    except Exception:
        ventes_net_today = 0
        enlevements_today = 0
        retours_today = 0
    
    # Récupérer les gammes actives
    gammes = PromotionGamme.query.filter_by(is_active=True).order_by(PromotionGamme.name).all()
    
    # Récupérer le stock de chaque équipe
    teams_stock = {}
    for team in teams:
        teams_stock[team.id] = get_team_stock(team.id)
    
    return render_template('promotion/workflow.html',
                         teams=teams,
                         members=members,
                         gammes=gammes,
                         teams_stock=teams_stock,
                         today=today,
                         ventes_net_today=ventes_net_today,
                         enlevements_today=enlevements_today,
                         retours_today=retours_today)

@promotion_bp.route('/workflow/distribute', methods=['POST'])
@login_required
def workflow_distribute():
    """Distribution des gammes aux membres (étape 2 du workflow)"""
    if not has_permission(current_user, 'promotion.write'):
        flash("Vous n'avez pas la permission de distribuer des gammes.", "error")
        return redirect(url_for('promotion.workflow'))
    
    try:
        member_id = int(request.form.get('member_id', 0))
        gamme_id = int(request.form.get('gamme_id', 0))
        quantity = int(request.form.get('quantity', 0))
        
        if quantity <= 0:
            flash("La quantité doit être positive.", "error")
            return redirect(url_for('promotion.workflow'))
        
        member = get_member_safe(member_id)
        if not member:
            flash("Membre introuvable.", "error")
            return redirect(url_for('promotion.workflow'))
        
        if not member.team_id:
            flash("Le membre doit appartenir à une équipe pour recevoir des gammes.", "error")
            return redirect(url_for('promotion.workflow'))
        
        gamme = PromotionGamme.query.get(gamme_id)
        if not gamme:
            flash("Gamme introuvable.", "error")
            return redirect(url_for('promotion.workflow'))
        
        # Vérifier le stock de l'équipe
        team_stock = get_team_stock(member.team_id)
        current_team_stock = team_stock.get(gamme_id, 0)
        
        if current_team_stock < quantity:
            flash(f"⚠️ Stock insuffisant dans l'équipe! Stock disponible: {current_team_stock} unité(s) de {gamme.name}. Besoin: {quantity} unité(s). Opération annulée. Veuillez d'abord approvisionner l'équipe.", "error")
            return redirect(url_for('promotion.workflow'))
        
        # Déduire du stock de l'équipe
        if not update_team_stock(member.team_id, gamme_id, quantity, 'subtract',
                                 movement_type='distribution',
                                 to_member_id=member.id):
            flash("Erreur lors de la mise à jour du stock de l'équipe.", "error")
            return redirect(url_for('promotion.workflow'))
        
        # Ajouter au stock du membre
        try:
            stock = PromotionMemberStock.query.filter_by(
                member_id=member_id,
                gamme_id=gamme_id
            ).first()
            
            if stock:
                stock.quantity += quantity
                stock.last_updated = datetime.now(UTC)
            else:
                # Créer un nouveau stock si il n'existe pas
                stock = PromotionMemberStock(
                    member_id=member_id,
                    gamme_id=gamme_id,
                    quantity=quantity
                )
                db.session.add(stock)
            
            # Enregistrer le mouvement de distribution
            try:
                record_stock_movement(
                    movement_type='distribution',
                    gamme_id=gamme_id,
                    quantity=stock.quantity,
                    quantity_change=quantity,
                    from_team_id=member.team_id if member else None,
                    to_member_id=member_id,
                    movement_date=datetime.now(UTC)
                )
            except Exception as e:
                print(f"Erreur lors de l'enregistrement du mouvement de distribution: {e}")
            
            db.session.commit()
        except Exception as stock_error:
            # Si la table n'existe pas encore, on continue quand même
            print(f"DEBUG workflow_distribute stock error (table peut-être absente): {stock_error}")
            db.session.rollback()
            # On continue quand même pour permettre la distribution
        
        flash(f"{quantity} unité(s) de {gamme.name} distribuée(s) à {member.full_name if member else 'Membre'} depuis le stock de l'équipe", "success")
        return redirect(url_for('promotion.workflow'))
    except Exception as e:
        db.session.rollback()
        flash(f"Erreur lors de la distribution: {str(e)}", "error")
        return redirect(url_for('promotion.workflow'))

# =========================================================
# DASHBOARD
# =========================================================

@promotion_bp.route('/dashboard')
@login_required
def dashboard():
    """Dashboard de la promotion"""
    if not has_permission(current_user, 'promotion.read'):
        flash("Vous n'avez pas la permission d'accéder à cette page.", "error")
        return redirect(url_for('index'))
    
    today = date.today()
    month_start = date(today.year, today.month, 1)
    
    # Vérifier si la journée est clôturée
    try:
        daily_closure = PromotionDailyClosure.query.filter_by(closure_date=today).first()
        is_day_closed = daily_closure is not None
    except Exception:
        is_day_closed = False
        daily_closure = None
    
    # Vérifier si transaction_type existe
    check_type_sql = """SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS 
                       WHERE TABLE_SCHEMA = DATABASE() 
                       AND TABLE_NAME = 'promotion_sales' 
                       AND COLUMN_NAME = 'transaction_type'"""
    has_transaction_type = db.session.execute(text(check_type_sql)).scalar() > 0
    
    # Statistiques de base avec filtrage par région
    from utils_region_filter import filter_teams_by_region
    teams_query = PromotionTeam.query.filter_by(is_active=True)
    teams_query = filter_teams_by_region(teams_query)
    
    stats = {
        'teams_count': teams_query.count(),
        'members_count': count_members_safe(is_active=True),  # Déjà filtré par région
        'gammes_count': PromotionGamme.query.filter_by(is_active=True).count(),
        'total_sales_today': count_sales_safe(date_from=today, date_to=today),  # Déjà filtré par région
        'total_sales_month': count_sales_safe(date_from=month_start, date_to=today),  # Déjà filtré par région
    }
    
    # Revenus et commissions (avec distinction enlèvements/retours si possible) avec filtrage par région
    from utils_region_filter import filter_sales_by_region, get_user_region_id
    try:
        if has_transaction_type:
            # CA et commissions avec distinction (filtrées par région via join)
            # Enlèvements aujourd'hui
            revenue_query_enl_today = db.session.query(func.sum(PromotionSale.total_amount_gnf))\
                .join(PromotionMember, PromotionSale.member_id == PromotionMember.id)\
                .join(PromotionTeam, PromotionMember.team_id == PromotionTeam.id)\
                .join(User, PromotionTeam.team_leader_id == User.id)\
                .filter(
                    PromotionSale.sale_date == today,
                    PromotionSale.transaction_type == 'enlevement'
                )
            if get_user_region_id() is not None:
                revenue_query_enl_today = revenue_query_enl_today.filter(User.region_id == get_user_region_id())
            revenue_enlevements_today = revenue_query_enl_today.scalar() or Decimal("0.00")
            # Retours aujourd'hui
            revenue_query_ret_today = db.session.query(func.sum(PromotionSale.total_amount_gnf))\
                .join(PromotionMember, PromotionSale.member_id == PromotionMember.id)\
                .join(PromotionTeam, PromotionMember.team_id == PromotionTeam.id)\
                .join(User, PromotionTeam.team_leader_id == User.id)\
                .filter(
                    PromotionSale.sale_date == today,
                    PromotionSale.transaction_type == 'retour'
                )
            if get_user_region_id() is not None:
                revenue_query_ret_today = revenue_query_ret_today.filter(User.region_id == get_user_region_id())
            revenue_retours_today = revenue_query_ret_today.scalar() or Decimal("0.00")
            stats['total_revenue_today'] = revenue_enlevements_today - revenue_retours_today
            
            # Enlèvements du mois
            revenue_query_enl_month = db.session.query(func.sum(PromotionSale.total_amount_gnf))\
                .join(PromotionMember, PromotionSale.member_id == PromotionMember.id)\
                .join(PromotionTeam, PromotionMember.team_id == PromotionTeam.id)\
                .join(User, PromotionTeam.team_leader_id == User.id)\
                .filter(
                    PromotionSale.sale_date >= month_start,
                    PromotionSale.sale_date <= today,
                    PromotionSale.transaction_type == 'enlevement'
                )
            if get_user_region_id() is not None:
                revenue_query_enl_month = revenue_query_enl_month.filter(User.region_id == get_user_region_id())
            revenue_enlevements_month = revenue_query_enl_month.scalar() or Decimal("0.00")
            
            # Retours du mois
            revenue_query_ret_month = db.session.query(func.sum(PromotionSale.total_amount_gnf))\
                .join(PromotionMember, PromotionSale.member_id == PromotionMember.id)\
                .join(PromotionTeam, PromotionMember.team_id == PromotionTeam.id)\
                .join(User, PromotionTeam.team_leader_id == User.id)\
                .filter(
                    PromotionSale.sale_date >= month_start,
                    PromotionSale.sale_date <= today,
                    PromotionSale.transaction_type == 'retour'
                )
            if get_user_region_id() is not None:
                revenue_query_ret_month = revenue_query_ret_month.filter(User.region_id == get_user_region_id())
            revenue_retours_month = revenue_query_ret_month.scalar() or Decimal("0.00")
            stats['total_revenue_month'] = revenue_enlevements_month - revenue_retours_month
            
            # Commissions du jour - Enlèvements
            commission_query_enl_today = db.session.query(func.sum(PromotionSale.commission_gnf))\
                .join(PromotionMember, PromotionSale.member_id == PromotionMember.id)\
                .join(PromotionTeam, PromotionMember.team_id == PromotionTeam.id)\
                .join(User, PromotionTeam.team_leader_id == User.id)\
                .filter(
                    PromotionSale.sale_date == today,
                    PromotionSale.transaction_type == 'enlevement'
                )
            if get_user_region_id() is not None:
                commission_query_enl_today = commission_query_enl_today.filter(User.region_id == get_user_region_id())
            commission_enlevements_today = commission_query_enl_today.scalar() or Decimal("0.00")
            
            # Commissions du jour - Retours
            commission_query_ret_today = db.session.query(func.sum(PromotionSale.commission_gnf))\
                .join(PromotionMember, PromotionSale.member_id == PromotionMember.id)\
                .join(PromotionTeam, PromotionMember.team_id == PromotionTeam.id)\
                .join(User, PromotionTeam.team_leader_id == User.id)\
                .filter(
                    PromotionSale.sale_date == today,
                    PromotionSale.transaction_type == 'retour'
                )
            if get_user_region_id() is not None:
                commission_query_ret_today = commission_query_ret_today.filter(User.region_id == get_user_region_id())
            commission_retours_today = commission_query_ret_today.scalar() or Decimal("0.00")
            stats['total_commissions_today'] = commission_enlevements_today - commission_retours_today
            
            # Commissions du mois - Enlèvements
            commission_query_enl_month = db.session.query(func.sum(PromotionSale.commission_gnf))\
                .join(PromotionMember, PromotionSale.member_id == PromotionMember.id)\
                .join(PromotionTeam, PromotionMember.team_id == PromotionTeam.id)\
                .join(User, PromotionTeam.team_leader_id == User.id)\
                .filter(
                    PromotionSale.sale_date >= month_start,
                    PromotionSale.sale_date <= today,
                    PromotionSale.transaction_type == 'enlevement'
                )
            if get_user_region_id() is not None:
                commission_query_enl_month = commission_query_enl_month.filter(User.region_id == get_user_region_id())
            commission_enlevements_month = commission_query_enl_month.scalar() or Decimal("0.00")
            
            # Commissions du mois - Retours
            commission_query_ret_month = db.session.query(func.sum(PromotionSale.commission_gnf))\
                .join(PromotionMember, PromotionSale.member_id == PromotionMember.id)\
                .join(PromotionTeam, PromotionMember.team_id == PromotionTeam.id)\
                .join(User, PromotionTeam.team_leader_id == User.id)\
                .filter(
                    PromotionSale.sale_date >= month_start,
                    PromotionSale.sale_date <= today,
                    PromotionSale.transaction_type == 'retour'
                )
            if get_user_region_id() is not None:
                commission_query_ret_month = commission_query_ret_month.filter(User.region_id == get_user_region_id())
            commission_retours_month = commission_query_ret_month.scalar() or Decimal("0.00")
            stats['total_commissions_month'] = commission_enlevements_month - commission_retours_month
            stats['resultat_net_month'] = stats['total_revenue_month'] - stats['total_commissions_month']
            stats['resultat_net_today'] = stats['total_revenue_today'] - stats['total_commissions_today']
        else:
            # Sans distinction (avec filtrage par région)
            revenue_query_today = db.session.query(func.sum(PromotionSale.total_amount_gnf))\
                .join(PromotionMember, PromotionSale.member_id == PromotionMember.id)\
                .join(PromotionTeam, PromotionMember.team_id == PromotionTeam.id)\
                .join(User, PromotionTeam.team_leader_id == User.id)\
                .filter(PromotionSale.sale_date == today)
            if get_user_region_id() is not None:
                revenue_query_today = revenue_query_today.filter(User.region_id == get_user_region_id())
            stats['total_revenue_today'] = revenue_query_today.scalar() or Decimal("0.00")
            
            revenue_query_month = db.session.query(func.sum(PromotionSale.total_amount_gnf))\
                .join(PromotionMember, PromotionSale.member_id == PromotionMember.id)\
                .join(PromotionTeam, PromotionMember.team_id == PromotionTeam.id)\
                .join(User, PromotionTeam.team_leader_id == User.id)\
                .filter(
                    PromotionSale.sale_date >= month_start,
                    PromotionSale.sale_date <= today
                )
            if get_user_region_id() is not None:
                revenue_query_month = revenue_query_month.filter(User.region_id == get_user_region_id())
            stats['total_revenue_month'] = revenue_query_month.scalar() or Decimal("0.00")
            
            commission_query_today = db.session.query(func.sum(PromotionSale.commission_gnf))\
                .join(PromotionMember, PromotionSale.member_id == PromotionMember.id)\
                .join(PromotionTeam, PromotionMember.team_id == PromotionTeam.id)\
                .join(User, PromotionTeam.team_leader_id == User.id)\
                .filter(PromotionSale.sale_date == today)
            if get_user_region_id() is not None:
                commission_query_today = commission_query_today.filter(User.region_id == get_user_region_id())
            stats['total_commissions_today'] = commission_query_today.scalar() or Decimal("0.00")
            
            commission_query_month = db.session.query(func.sum(PromotionSale.commission_gnf))\
                .join(PromotionMember, PromotionSale.member_id == PromotionMember.id)\
                .join(PromotionTeam, PromotionMember.team_id == PromotionTeam.id)\
                .join(User, PromotionTeam.team_leader_id == User.id)\
                .filter(
                    PromotionSale.sale_date >= month_start,
                    PromotionSale.sale_date <= today
                )
            if get_user_region_id() is not None:
                commission_query_month = commission_query_month.filter(User.region_id == get_user_region_id())
            stats['total_commissions_month'] = commission_query_month.scalar() or Decimal("0.00")
            stats['resultat_net_month'] = stats['total_revenue_month'] - stats['total_commissions_month']
            stats['resultat_net_today'] = stats['total_revenue_today'] - stats['total_commissions_today']
    except Exception as e:
        print(f"DEBUG dashboard stats error: {e}")
        stats['total_revenue_today'] = Decimal("0.00")
        stats['total_revenue_month'] = Decimal("0.00")
        stats['total_commissions_today'] = Decimal("0.00")
        stats['total_commissions_month'] = Decimal("0.00")
        stats['resultat_net_today'] = Decimal("0.00")
        stats['resultat_net_month'] = Decimal("0.00")
    
    # Top vendeurs du mois (avec distinction enlèvements/retours pour les commissions) avec filtrage par région
    try:
        if has_transaction_type:
            # Calculer les commissions nettes (enlèvements - retours) pour chaque membre avec filtrage par région
            top_sellers_query = db.session.query(
                PromotionMember.id, PromotionMember.full_name, PromotionMember.team_id,
                func.sum(
                    case(
                        (PromotionSale.transaction_type == 'enlevement', PromotionSale.quantity),
                        else_=-PromotionSale.quantity
                    )
                ).label('total_qty'),
                func.sum(
                    case(
                        (PromotionSale.transaction_type == 'enlevement', PromotionSale.commission_gnf),
                        else_=-PromotionSale.commission_gnf
                    )
                ).label('total_comm')
            ).join(PromotionSale, PromotionMember.id == PromotionSale.member_id)\
             .join(PromotionTeam, PromotionMember.team_id == PromotionTeam.id)\
             .join(User, PromotionTeam.team_leader_id == User.id)\
             .filter(
                PromotionSale.sale_date >= month_start,
                PromotionSale.sale_date <= today
            )
            if get_user_region_id() is not None:
                top_sellers_query = top_sellers_query.filter(User.region_id == get_user_region_id())
            top_sellers_query = top_sellers_query.group_by(PromotionMember.id, PromotionMember.full_name, PromotionMember.team_id)\
             .order_by(
                func.sum(
                    case(
                        (PromotionSale.transaction_type == 'enlevement', PromotionSale.commission_gnf),
                        else_=-PromotionSale.commission_gnf
                    )
                ).desc()
            ).limit(10).all()
        else:
            # Sans distinction (avec filtrage par région)
            top_sellers_query = db.session.query(
                PromotionMember.id, PromotionMember.full_name, PromotionMember.team_id,
                func.sum(PromotionSale.quantity).label('total_qty'),
                func.sum(PromotionSale.commission_gnf).label('total_comm')
            ).join(PromotionSale, PromotionMember.id == PromotionSale.member_id)\
             .join(PromotionTeam, PromotionMember.team_id == PromotionTeam.id)\
             .join(User, PromotionTeam.team_leader_id == User.id)\
             .filter(
                PromotionSale.sale_date >= month_start,
                PromotionSale.sale_date <= today
            )
            if get_user_region_id() is not None:
                top_sellers_query = top_sellers_query.filter(User.region_id == get_user_region_id())
            top_sellers_query = top_sellers_query.group_by(PromotionMember.id, PromotionMember.full_name, PromotionMember.team_id)\
             .order_by(func.sum(PromotionSale.commission_gnf).desc())\
             .limit(10).all()
        
        # Formater les résultats pour le template
        top_sellers = []
        for row in top_sellers_query:
            member = PromotionMember.query.options(
                load_only(PromotionMember.id, PromotionMember.full_name, PromotionMember.team_id)
            ).get(row[0])
            if member and member.team_id:
                member.team = PromotionTeam.query.options(
                    load_only(PromotionTeam.id, PromotionTeam.name)
                ).get(member.team_id)
            top_sellers.append({
                'member': member,
                'total_quantity': row[3] or 0,
                'total_commission': row[4] or Decimal("0.00")
            })
    except Exception as e:
        print(f"DEBUG dashboard top_sellers error: {e}")
        top_sellers = []
    
    # Ventes récentes (filtrées par région)
    try:
        from utils_region_filter import filter_sales_by_region
        recent_sales_query = PromotionSale.query
        recent_sales_query = filter_sales_by_region(recent_sales_query)
        recent_sales = recent_sales_query.options(
            load_only(PromotionSale.id, PromotionSale.member_id, PromotionSale.gamme_id, 
                     PromotionSale.quantity, PromotionSale.total_amount_gnf, 
                     PromotionSale.commission_gnf, PromotionSale.sale_date, 
                     PromotionSale.created_at)
        ).order_by(PromotionSale.created_at.desc()).limit(10).all()
        # Charger les relations manuellement
        for sale in recent_sales:
            try:
                sale.member = PromotionMember.query.options(load_only(PromotionMember.id, PromotionMember.full_name)).get(sale.member_id)
                sale.gamme = PromotionGamme.query.options(load_only(PromotionGamme.id, PromotionGamme.name)).get(sale.gamme_id)
                # Définir transaction_type si la colonne n'existe pas
                if '_sa_instance_state' in sale.__dict__:
                    if 'transaction_type' not in sale.__dict__:
                        try:
                            type_sql = "SELECT transaction_type FROM promotion_sales WHERE id = :sale_id"
                            type_result = db.session.execute(text(type_sql), {'sale_id': sale.id})
                            type_row = type_result.fetchone()
                            sale.__dict__['transaction_type'] = type_row[0] if type_row and type_row[0] else 'enlevement'
                        except Exception:
                            sale.__dict__['transaction_type'] = 'enlevement'
            except Exception:
                pass
    except Exception as e:
        print(f"DEBUG dashboard recent_sales error: {e}")
        recent_sales = []
    
    # Données pour les graphiques
    try:
        # Graphique des ventes des 7 derniers jours
        from datetime import timedelta
        import json
        sales_chart_labels = []
        sales_chart_data = []
        for i in range(6, -1, -1):
            day = today - timedelta(days=i)
            sales_chart_labels.append(day.strftime('%d/%m'))
            count = count_sales_safe(date_from=day, date_to=day)
            sales_chart_data.append(count)
        
        # Graphique top vendeurs (commissions)
        top_sellers_chart_labels = []
        top_sellers_chart_data = []
        for seller in top_sellers[:5]:  # Top 5 seulement pour le graphique
            if seller['member']:
                name = seller['member'].full_name[:15] if seller['member'].full_name else 'N/A'
                top_sellers_chart_labels.append(name)
                top_sellers_chart_data.append(float(seller['total_commission']))
        
        # Convertir en JSON pour le template
        sales_chart_labels_json = json.dumps(sales_chart_labels)
        sales_chart_data_json = json.dumps(sales_chart_data)
        top_sellers_chart_labels_json = json.dumps(top_sellers_chart_labels)
        top_sellers_chart_data_json = json.dumps(top_sellers_chart_data)
    except Exception as e:
        print(f"DEBUG dashboard charts error: {e}")
        import json
        sales_chart_labels_json = json.dumps([])
        sales_chart_data_json = json.dumps([])
        top_sellers_chart_labels_json = json.dumps([])
        top_sellers_chart_data_json = json.dumps([])
    
    # Récupérer les alertes de stock faible
    stock_alerts = get_low_stock_alerts(threshold=10)
    
    return render_template('promotion/dashboard.html',
                         is_day_closed=is_day_closed,
                         daily_closure=daily_closure,
                         today=today, 
                         stats=stats, 
                         top_sellers=top_sellers, 
                         recent_sales=recent_sales,
                         sales_chart_labels=sales_chart_labels_json,
                         sales_chart_data=sales_chart_data_json,
                         top_sellers_chart_labels=top_sellers_chart_labels_json,
                         top_sellers_chart_data=top_sellers_chart_data_json,
                         stock_alerts=stock_alerts)

# =========================================================
# GESTION DES ÉQUIPES
# =========================================================

@promotion_bp.route('/teams')
@login_required
def teams_list():
    """Liste des équipes de promotion"""
    if not has_permission(current_user, 'promotion.read'):
        flash("Vous n'avez pas la permission d'accéder à cette page.", "error")
        return redirect(url_for('index'))
    
    # Filtrer les équipes par région
    from utils_region_filter import filter_teams_by_region
    teams_query = PromotionTeam.query.filter_by(is_active=True)
    teams_query = filter_teams_by_region(teams_query)
    teams = teams_query.all()
    total_teams = PromotionTeam.query.count()  # Total global (pour admin)
    active_teams = len(teams)  # Équipes actives filtrées
    total_members = count_members_safe(is_active=True)  # Déjà filtré par région
    
    # Calculer les statistiques pour chaque équipe
    for team in teams:
        try:
            # Compter les membres de l'équipe
            members_count = count_members_safe(team_id=team.id, is_active=True)
            
            # Calculer les ventes totales (enlèvements - retours)
            try:
                # Enlèvements
                enlevements = db.session.query(
                    func.sum(PromotionSale.quantity).label('total_qty'),
                    func.sum(PromotionSale.total_amount).label('total_revenue')
                ).join(PromotionMember).filter(
                    PromotionMember.team_id == team.id,
                    PromotionSale.transaction_type == 'enlevement'
                ).first()
                
                enlevements_qty = enlevements.total_qty or 0
                enlevements_revenue = enlevements.total_revenue or 0
                
                # Retours
                retours = db.session.query(
                    func.sum(PromotionSale.quantity).label('total_qty'),
                    func.sum(PromotionSale.total_amount).label('total_revenue')
                ).join(PromotionMember).filter(
                    PromotionMember.team_id == team.id,
                    PromotionSale.transaction_type == 'retour'
                ).first()
                
                retours_qty = retours.total_qty or 0
                retours_revenue = retours.total_revenue or 0
                
                # Net (enlèvements - retours)
                total_sales = int(enlevements_qty - retours_qty)
                total_revenue = float(enlevements_revenue - retours_revenue)
            except Exception as e:
                print(f"Erreur calcul stats ventes pour équipe {team.id}: {e}")
                total_sales = 0
                total_revenue = 0.0
            
            # Ajouter les statistiques à l'objet team
            team.stats = type('Stats', (), {
                'members_count': members_count,
                'total_sales': total_sales,
                'total_revenue': total_revenue
            })()
        except Exception as e:
            print(f"Erreur calcul stats pour équipe {team.id}: {e}")
            team.stats = type('Stats', (), {
                'members_count': 0,
                'total_sales': 0,
                'total_revenue': 0.0
            })()
    
    stats = {
        'total': total_teams,
        'active': active_teams,
        'total_members': total_members
    }
    
    return render_template('promotion/teams_list.html', teams=teams, stats=stats)

@promotion_bp.route('/teams/new', methods=['GET', 'POST'])
@login_required
def team_new():
    """Créer une nouvelle équipe"""
    if not has_permission(current_user, 'promotion.write'):
        flash("Vous n'avez pas la permission de créer une équipe.", "error")
        return redirect(url_for('promotion.teams_list'))
    
    if request.method == 'POST':
        try:
            team = PromotionTeam(
                name=request.form.get('name'),
                region=request.form.get('region'),
                manager_id=int(request.form.get('manager_id', 0)) or None,
                is_active=True
            )
            db.session.add(team)
            db.session.commit()
            flash("Équipe créée avec succès!", "success")
            return redirect(url_for('promotion.teams_list'))
        except Exception as e:
            db.session.rollback()
            flash(f"Erreur: {str(e)}", "error")
    
    # Récupérer les utilisateurs avec le rôle promotion_manager
    managers = User.query.join(Role).filter(Role.name == 'promotion_manager').all()
    return render_template('promotion/team_form.html', team=None, managers=managers)

@promotion_bp.route('/teams/<int:id>')
@login_required
def team_detail(id):
    """Détails d'une équipe"""
    if not has_permission(current_user, 'promotion.read'):
        flash("Vous n'avez pas la permission d'accéder à cette page.", "error")
        return redirect(url_for('promotion.teams_list'))
    
    team = PromotionTeam.query.get_or_404(id)
    
    # Récupérer les membres de l'équipe avec leurs statistiques
    try:
        members_query = PromotionMember.query.filter_by(team_id=id, is_active=True).options(
            load_only(PromotionMember.id, PromotionMember.full_name, PromotionMember.phone, 
                     PromotionMember.email, PromotionMember.is_active)
        ).all()
        
        members = []
        for member in members_query:
            # Calculer les statistiques pour chaque membre
            try:
                check_type_sql = """SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS 
                                   WHERE TABLE_SCHEMA = DATABASE() 
                                   AND TABLE_NAME = 'promotion_sales' 
                                   AND COLUMN_NAME = 'transaction_type'"""
                has_transaction_type = db.session.execute(text(check_type_sql)).scalar() > 0
                
                if has_transaction_type:
                    sales_count = db.session.query(func.count(PromotionSale.id)).filter(
                        PromotionSale.member_id == member.id,
                        PromotionSale.transaction_type == 'enlevement'
                    ).scalar() or 0
                    
                    returns_count = db.session.query(func.count(PromotionSale.id)).filter(
                        PromotionSale.member_id == member.id,
                        PromotionSale.transaction_type == 'retour'
                    ).scalar() or 0
                    
                    sales_count = sales_count - returns_count
                    
                    total_commission = db.session.query(func.sum(PromotionSale.commission_gnf)).filter(
                        PromotionSale.member_id == member.id,
                        PromotionSale.transaction_type == 'enlevement'
                    ).scalar() or Decimal("0.00")
                    
                    returns_commission = db.session.query(func.sum(PromotionSale.commission_gnf)).filter(
                        PromotionSale.member_id == member.id,
                        PromotionSale.transaction_type == 'retour'
                    ).scalar() or Decimal("0.00")
                    
                    total_commission = total_commission - returns_commission
                else:
                    sales_count = db.session.query(func.count(PromotionSale.id)).filter(
                        PromotionSale.member_id == member.id
                    ).scalar() or 0
                    
                    total_commission = db.session.query(func.sum(PromotionSale.commission_gnf)).filter(
                        PromotionSale.member_id == member.id
                    ).scalar() or Decimal("0.00")
            except Exception:
                sales_count = 0
                total_commission = Decimal("0.00")
            
            member.stats = type('Stats', (), {
                'sales_count': sales_count,
                'total_commission': total_commission
            })()
            members.append(member)
    except Exception:
        members = []
    
    # Calculer les statistiques de l'équipe
    try:
        has_transaction_type = has_transaction_type_column_cached()
        
        if has_transaction_type:
            total_sales = db.session.query(func.count(PromotionSale.id)).join(
                PromotionMember
            ).filter(
                PromotionMember.team_id == id,
                PromotionSale.transaction_type == 'enlevement'
            ).scalar() or 0
            
            total_returns = db.session.query(func.count(PromotionSale.id)).join(
                PromotionMember
            ).filter(
                PromotionMember.team_id == id,
                PromotionSale.transaction_type == 'retour'
            ).scalar() or 0
            
            total_sales = total_sales - total_returns
            
            total_revenue = db.session.query(func.sum(PromotionSale.total_amount_gnf)).join(
                PromotionMember
            ).filter(
                PromotionMember.team_id == id,
                PromotionSale.transaction_type == 'enlevement'
            ).scalar() or Decimal("0.00")
            
            returns_revenue = db.session.query(func.sum(PromotionSale.total_amount_gnf)).join(
                PromotionMember
            ).filter(
                PromotionMember.team_id == id,
                PromotionSale.transaction_type == 'retour'
            ).scalar() or Decimal("0.00")
            
            total_revenue = total_revenue - returns_revenue
            
            total_commissions = db.session.query(func.sum(PromotionSale.commission_gnf)).join(
                PromotionMember
            ).filter(
                PromotionMember.team_id == id,
                PromotionSale.transaction_type == 'enlevement'
            ).scalar() or Decimal("0.00")
            
            returns_commissions = db.session.query(func.sum(PromotionSale.commission_gnf)).join(
                PromotionMember
            ).filter(
                PromotionMember.team_id == id,
                PromotionSale.transaction_type == 'retour'
            ).scalar() or Decimal("0.00")
            
            total_commissions = total_commissions - returns_commissions
        else:
            total_sales = db.session.query(func.count(PromotionSale.id)).join(
                PromotionMember
            ).filter(PromotionMember.team_id == id).scalar() or 0
            
            total_revenue = db.session.query(func.sum(PromotionSale.total_amount_gnf)).join(
                PromotionMember
            ).filter(PromotionMember.team_id == id).scalar() or Decimal("0.00")
            
            total_commissions = db.session.query(func.sum(PromotionSale.commission_gnf)).join(
                PromotionMember
            ).filter(PromotionMember.team_id == id).scalar() or Decimal("0.00")
        
        stats = type('Stats', (), {
            'members_count': len(members),
            'total_sales': total_sales,
            'total_revenue': total_revenue,
            'total_commissions': total_commissions
        })()
    except Exception as e:
        print(f"Erreur calcul stats pour équipe {id}: {e}")
        stats = type('Stats', (), {
            'members_count': len(members),
            'total_sales': 0,
            'total_revenue': Decimal("0.00"),
            'total_commissions': Decimal("0.00")
        })()
    
    # Récupérer le stock de l'équipe avec toutes les informations
    team_stock = get_team_stock(id)
    team_stock_details = get_team_stock_details(id)
    
    # Récupérer toutes les gammes (actives et inactives) pour afficher le stock complet
    gammes = PromotionGamme.query.all()
    
    # Récupérer aussi les gammes qui ont du stock mais qui ne sont peut-être pas dans la liste
    gammes_with_stock = []
    if team_stock:
        for gamme_id in team_stock.keys():
            gamme = PromotionGamme.query.get(gamme_id)
            if gamme and gamme not in gammes:
                gammes_with_stock.append(gamme)
    
    # Combiner les listes
    all_gammes = list(gammes) + gammes_with_stock
    
    # Debug: afficher le stock récupéré
    print(f"\n=== DEBUG TEAM DETAIL ÉQUIPE {id} ===")
    print(f"Stock récupéré: {team_stock}")
    print(f"Nombre de gammes avec stock: {len(team_stock) if team_stock else 0}")
    print(f"Nombre de gammes dans la liste: {len(all_gammes)}")
    if team_stock:
        for gamme_id, qty in team_stock.items():
            gamme = PromotionGamme.query.get(gamme_id)
            gamme_name = gamme.name if gamme else f"Gamme ID {gamme_id} (non trouvée)"
            print(f"  - {gamme_name}: {qty} unités")
    print(f"=== FIN DEBUG ===\n")
    
    return render_template('promotion/team_detail.html', team=team, members=members, stats=stats, 
                         team_stock=team_stock, team_stock_details=team_stock_details, gammes=all_gammes)

@promotion_bp.route('/teams/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def team_edit(id):
    """Modifier une équipe"""
    if not has_permission(current_user, 'promotion.write'):
        flash("Vous n'avez pas la permission de modifier une équipe.", "error")
        return redirect(url_for('promotion.teams_list'))
    
    team = PromotionTeam.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            team.name = request.form.get('name')
            team.region = request.form.get('region')
            manager_id = request.form.get('manager_id', '')
            team.manager_id = int(manager_id) if manager_id else None
            team.is_active = request.form.get('is_active') == 'on'
            db.session.commit()
            flash("Équipe modifiée avec succès!", "success")
            return redirect(url_for('promotion.teams_list'))
        except Exception as e:
            db.session.rollback()
            flash(f"Erreur: {str(e)}", "error")
    
    # Récupérer les utilisateurs avec le rôle promotion_manager
    managers = User.query.join(Role).filter(Role.name == 'promotion_manager').all()
    return render_template('promotion/team_form.html', team=team, managers=managers)

@promotion_bp.route('/teams/<int:team_id>/supply', methods=['GET', 'POST'])
@login_required
def team_supply(team_id):
    """Approvisionner une équipe en gammes et pièces"""
    if not has_permission(current_user, 'promotion.write'):
        flash("Vous n'avez pas la permission d'approvisionner une équipe.", "error")
        return redirect(url_for('promotion.teams_list'))
    
    team = PromotionTeam.query.get_or_404(team_id)
    
    if request.method == 'POST':
        try:
            supply_date_str = request.form.get('supply_date', '')
            
            # Parser la date d'approvisionnement
            if supply_date_str:
                try:
                    supply_date = datetime.strptime(supply_date_str, '%Y-%m-%d').date()
                    supply_datetime = datetime.combine(supply_date, datetime.min.time()).replace(tzinfo=UTC)
                except ValueError:
                    supply_datetime = datetime.now(UTC)
            else:
                supply_datetime = datetime.now(UTC)
            
            # Récupérer toutes les approvisionnements (plusieurs gammes/pièces)
            supplies = []
            i = 0
            while True:
                gamme_id_str = request.form.get(f'gamme_id_{i}')
                quantity_str = request.form.get(f'quantity_{i}')
                
                if not gamme_id_str or not quantity_str:
                    break
                
                try:
                    gamme_id = int(gamme_id_str)
                    quantity = int(quantity_str)
                    
                    if quantity <= 0:
                        i += 1
                        continue
                    
                    supplies.append({
                        'gamme_id': gamme_id,
                        'quantity': quantity
                    })
                except (ValueError, TypeError):
                    pass
                
                i += 1
            
            if not supplies:
                flash("Veuillez ajouter au moins une gamme/pièce avec une quantité valide.", "error")
                return redirect(url_for('promotion.team_supply', team_id=team_id))
            
            # Identifier le superviseur (current_user si promotion_manager, sinon team_leader)
            supervisor_id = current_user.id
            try:
                # Vérifier si l'utilisateur est un promotion_manager
                user_role = db.session.query(Role).join(User.roles).filter(User.id == current_user.id, Role.name == 'promotion_manager').first()
                if not user_role and team.team_leader_id:
                    supervisor_id = team.team_leader_id
            except Exception:
                pass
            
            # Vérifier le stock du superviseur avant d'approvisionner
            supervisor_stock = get_supervisor_stock(supervisor_id)
            for supply in supplies:
                gamme_id = supply['gamme_id']
                quantity = supply['quantity']
                current_supervisor_stock = supervisor_stock.get(gamme_id, 0)
                
                if current_supervisor_stock < quantity:
                    gamme = PromotionGamme.query.get(gamme_id)
                    flash(f"⚠️ Stock insuffisant du superviseur! Stock disponible: {current_supervisor_stock} unité(s) de {gamme.name if gamme else 'N/A'}. Besoin: {quantity} unité(s). Opération annulée.", "error")
                    return redirect(url_for('promotion.team_supply', team_id=team_id))
            
            # Traiter tous les approvisionnements
            success_count = 0
            failed_supplies = []
            
            print(f"\n=== DEBUG APPROVISIONNEMENT ÉQUIPE {team_id} - DÉBUT ===")
            print(f"Nombre d'approvisionnements à traiter: {len(supplies)}")
            for idx, supply in enumerate(supplies):
                gamme_id = supply['gamme_id']
                quantity = supply['quantity']
                print(f"  [{idx+1}/{len(supplies)}] Traitement: Gamme ID {gamme_id}, Quantité: {quantity}")
                
                # Déduire du stock du superviseur
                if not update_supervisor_stock(supervisor_id, gamme_id, quantity, 'subtract', 
                                               movement_type='approvisionnement', 
                                               to_team_id=team_id, 
                                               movement_date=supply_datetime):
                    error_msg = f"Erreur lors de la déduction du stock du superviseur pour la gamme {gamme_id}."
                    print(f"  ❌ {error_msg}")
                    flash(error_msg, "error")
                    failed_supplies.append(supply)
                    continue
                
                # Augmenter le stock de l'équipe
                stock = PromotionTeamStock.query.filter_by(
                    team_id=team_id,
                    gamme_id=gamme_id
                ).first()
                
                old_quantity = stock.quantity if stock else 0
                
                if stock:
                    stock.quantity += quantity
                    stock.last_updated = supply_datetime
                    print(f"  ✅ Stock existant mis à jour: {old_quantity} + {quantity} = {stock.quantity}")
                else:
                    stock = PromotionTeamStock(
                        team_id=team_id,
                        gamme_id=gamme_id,
                        quantity=quantity,
                        last_updated=supply_datetime
                    )
                    db.session.add(stock)
                    print(f"  ✅ Nouveau stock créé: {quantity} unités")
                
                # Enregistrer le mouvement pour l'équipe (approvisionnement depuis le superviseur)
                try:
                    record_stock_movement(
                        movement_type='approvisionnement',
                        gamme_id=gamme_id,
                        quantity=stock.quantity,
                        quantity_change=quantity,
                        from_supervisor_id=supervisor_id,
                        to_team_id=team_id,
                        movement_date=supply_datetime
                    )
                    print(f"  ✅ Mouvement enregistré")
                except Exception as e:
                    print(f"  ⚠️ Erreur lors de l'enregistrement du mouvement: {e}")
                
                success_count += 1
            
            # Commit de toutes les modifications
            try:
                db.session.commit()
                print(f"✅ Commit réussi: {success_count} approvisionnement(s) enregistré(s)")
            except Exception as e:
                db.session.rollback()
                print(f"❌ ERREUR lors du commit: {e}")
                import traceback
                traceback.print_exc()
                flash(f"Erreur lors de l'enregistrement: {str(e)}", "error")
                return redirect(url_for('promotion.team_supply', team_id=team_id))
            
            # Debug: vérifier que le stock est bien enregistré après le commit
            print(f"\n=== DEBUG APPROVISIONNEMENT ÉQUIPE {team_id} - VÉRIFICATION POST-COMMIT ===")
            verification_ok = True
            for supply in supplies:
                # Rafraîchir la session pour s'assurer qu'on lit les données les plus récentes
                db.session.expire_all()
                
                stock_check = PromotionTeamStock.query.filter_by(
                    team_id=team_id,
                    gamme_id=supply['gamme_id']
                ).first()
                
                if stock_check:
                    expected_quantity = supply['quantity']
                    if stock_check.quantity != expected_quantity:
                        # Si c'est un stock existant, on doit additionner
                        old_stock = PromotionTeamStock.query.filter_by(
                            team_id=team_id,
                            gamme_id=supply['gamme_id']
                        ).with_for_update().first()
                        if old_stock and old_stock.quantity < expected_quantity:
                            print(f"  ⚠️ ATTENTION: Le stock enregistré ({stock_check.quantity}) est inférieur à la quantité attendue ({expected_quantity})")
                            verification_ok = False
                        else:
                            print(f"✅ Stock vérifié: Gamme ID {supply['gamme_id']} = {stock_check.quantity} unités (attendu: {expected_quantity}, stock existant additionné)")
                    else:
                        print(f"✅ Stock vérifié: Gamme ID {supply['gamme_id']} = {stock_check.quantity} unités (attendu: {expected_quantity})")
                else:
                    print(f"❌ ERREUR: Stock non trouvé pour gamme ID {supply['gamme_id']}")
                    verification_ok = False
            
            if not verification_ok:
                print(f"⚠️ Certains stocks n'ont pas été correctement enregistrés!")
            
            print(f"=== FIN DEBUG ===\n")
            
            if failed_supplies:
                flash(f"{success_count} approvisionnement(s) enregistré(s), {len(failed_supplies)} échoué(s).", "warning")
            else:
                flash(f"{success_count} approvisionnement(s) enregistré(s) avec succès le {supply_date_str or 'aujourd\'hui'}! Stock du superviseur déduit et stock de l'équipe augmenté.", "success")
            
            return redirect(url_for('promotion.team_detail', id=team_id))
        except Exception as e:
            db.session.rollback()
            flash(f"Erreur lors de l'approvisionnement: {str(e)}", "error")
    
    gammes = PromotionGamme.query.filter_by(is_active=True).order_by(PromotionGamme.name).all()
    current_stocks = get_team_stock(team_id)
    today = date.today()
    return render_template('promotion/team_supply.html',
                         team=team, gammes=gammes, current_stocks=current_stocks, today=today)

# =========================================================
# GESTION DES GAMMES
# =========================================================

@promotion_bp.route('/gammes')
@login_required
def gammes_list():
    """Liste des gammes de produits"""
    if not has_permission(current_user, 'promotion.read'):
        flash("Vous n'avez pas la permission d'accéder à cette page.", "error")
        return redirect(url_for('index'))
    
    gammes = PromotionGamme.query.filter_by(is_active=True).order_by(PromotionGamme.name).all()
    total_gammes = PromotionGamme.query.count()
    active_gammes = len(gammes)
    
    stats = {
        'total': total_gammes,
        'active': active_gammes
    }
    
    return render_template('promotion/gammes_list.html', gammes=gammes, stats=stats)

@promotion_bp.route('/gammes/new', methods=['GET', 'POST'])
@login_required
def gamme_new():
    """Créer une nouvelle gamme"""
    if not has_permission(current_user, 'promotion.write'):
        flash("Vous n'avez pas la permission de créer une gamme.", "error")
        return redirect(url_for('promotion.gammes_list'))
    
    if request.method == 'POST':
        try:
            gamme = PromotionGamme(
                name=request.form.get('name'),
                description=request.form.get('description'),
                is_piece=request.form.get('is_piece') == 'on',
                unit_type=request.form.get('unit_type'),
                unit_description=request.form.get('unit_description'),
                selling_price_gnf=Decimal(request.form.get('selling_price_gnf', '0')),
                commission_per_unit_gnf=Decimal(request.form.get('commission_per_unit_gnf', '0')),
                is_active=True
            )
            db.session.add(gamme)
            
            # Ajouter les articles associés
            article_ids = request.form.getlist('article_ids')
            if article_ids:
                articles = Article.query.filter(Article.id.in_([int(aid) for aid in article_ids])).all()
                gamme.articles = articles
            
            db.session.commit()
            flash("Gamme créée avec succès!", "success")
            return redirect(url_for('promotion.gammes_list'))
        except Exception as e:
            db.session.rollback()
            flash(f"Erreur: {str(e)}", "error")
    
    articles = Article.query.filter_by(is_active=True).order_by(Article.name).all()
    return render_template('promotion/gamme_form.html', gamme=None, articles=articles)

@promotion_bp.route('/gammes/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def gamme_edit(id):
    """Modifier une gamme"""
    if not has_permission(current_user, 'promotion.write'):
        flash("Vous n'avez pas la permission de modifier une gamme.", "error")
        return redirect(url_for('promotion.gammes_list'))
    
    gamme = PromotionGamme.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            gamme.name = request.form.get('name')
            gamme.description = request.form.get('description')
            gamme.is_piece = request.form.get('is_piece') == 'on'
            gamme.unit_type = request.form.get('unit_type')
            gamme.unit_description = request.form.get('unit_description')
            gamme.selling_price_gnf = Decimal(request.form.get('selling_price_gnf', '0'))
            gamme.commission_per_unit_gnf = Decimal(request.form.get('commission_per_unit_gnf', '0'))
            gamme.is_active = request.form.get('is_active') == 'on'
            
            # Mettre à jour les articles associés
            article_ids = request.form.getlist('article_ids')
            if article_ids:
                articles = Article.query.filter(Article.id.in_([int(aid) for aid in article_ids])).all()
                gamme.articles = articles
            else:
                gamme.articles = []
            
            db.session.commit()
            flash("Gamme modifiée avec succès!", "success")
            return redirect(url_for('promotion.gammes_list'))
        except Exception as e:
            db.session.rollback()
            flash(f"Erreur: {str(e)}", "error")
    
    articles = Article.query.filter_by(is_active=True).order_by(Article.name).all()
    return render_template('promotion/gamme_form.html', gamme=gamme, articles=articles)

# =========================================================
# GESTION DES MEMBRES
# =========================================================

@promotion_bp.route('/members')
@login_required
def members_list():
    """Liste des membres de l'équipe de promotion"""
    if not has_permission(current_user, 'promotion.read'):
        flash("Vous n'avez pas la permission d'accéder à cette page.", "error")
        return redirect(url_for('index'))
    
    # Paramètres de pagination
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    search = request.args.get('search', '').strip()
    team_filter = request.args.get('team_id', type=int)
    
    try:
        # Requête de base avec filtrage par région
        from utils_region_filter import filter_members_by_region
        query = PromotionMember.query.filter_by(is_active=True)
        query = filter_members_by_region(query)
        
        # Filtre par équipe
        if team_filter:
            query = query.filter_by(team_id=team_filter)
        
        # Recherche
        if search:
            query = query.filter(
                or_(
                    PromotionMember.full_name.ilike(f'%{search}%'),
                    PromotionMember.phone.ilike(f'%{search}%')
                )
            )
        
        # Pagination
        pagination = query.options(
            load_only(PromotionMember.id, PromotionMember.full_name, PromotionMember.team_id,
                     PromotionMember.phone, PromotionMember.is_active)
        ).paginate(page=page, per_page=per_page, error_out=False)
        
        members = pagination.items
        
        # Optimisation: Charger les équipes en batch
        team_ids = [m.team_id for m in members if m.team_id]
        teams_map = load_teams_batch(team_ids)
        
        # Optimisation: Charger les statistiques en batch
        member_ids = [m.id for m in members]
        stats_map = load_member_stats_batch(member_ids)
        
        # Assigner les relations et statistiques
        for member in members:
            member.team = teams_map.get(member.team_id) if member.team_id else None
            
            # Définir intermediaire à None pour éviter les erreurs
            if '_sa_instance_state' in member.__dict__:
                member.__dict__['intermediaire'] = None
            else:
                member.intermediaire = None
            
            # Ajouter les statistiques
            stats = stats_map.get(member.id, {'sales_count': 0, 'total_commission': Decimal("0.00")})
            member.stats = type('Stats', (), {
                'sales_count': int(stats['sales_count']),
                'total_commission': float(stats['total_commission'])
            })()
    except Exception as e:
        print(f"DEBUG members_list error: {e}")
        members = []
        pagination = None
    
    # Charger toutes les équipes pour le filtre (filtrées par région)
    from utils_region_filter import filter_teams_by_region
    teams_query = PromotionTeam.query.filter_by(is_active=True)
    teams_query = filter_teams_by_region(teams_query)
    teams = teams_query.all()
    
    return render_template('promotion/members_list.html', 
                         members=members, 
                         teams=teams,
                         pagination=pagination,
                         search=search,
                         team_filter=team_filter)

@promotion_bp.route('/members/new', methods=['GET', 'POST'])
@login_required
def member_new():
    """Créer un nouveau membre"""
    if not has_permission(current_user, 'promotion.write'):
        flash("Vous n'avez pas la permission de créer un membre.", "error")
        return redirect(url_for('promotion.members_list'))
    
    if request.method == 'POST':
        try:
            # Utiliser SQL direct pour éviter les colonnes manquantes
            sql = """INSERT INTO promotion_members 
                     (full_name, phone, team_id, is_active, created_at) 
                     VALUES (:full_name, :phone, :team_id, :is_active, :created_at)"""
            
            team_id = request.form.get('team_id', '')
            team_id = int(team_id) if team_id else None
            
            db.session.execute(text(sql), {
                'full_name': request.form.get('full_name'),
                'phone': request.form.get('phone'),
                'team_id': team_id,
                'is_active': True,
                'created_at': datetime.now(UTC)
            })
            db.session.commit()
            flash("Membre créé avec succès!", "success")
            return redirect(url_for('promotion.members_list'))
        except Exception as e:
            db.session.rollback()
            flash(f"Erreur: {str(e)}", "error")
    
    teams = PromotionTeam.query.filter_by(is_active=True).all()
    return render_template('promotion/member_form.html', member=None, teams=teams)

@promotion_bp.route('/members/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def member_edit(id):
    """Modifier un membre"""
    if not has_permission(current_user, 'promotion.write'):
        flash("Vous n'avez pas la permission de modifier un membre.", "error")
        return redirect(url_for('promotion.members_list'))
    
    member = get_member_safe(id)
    if not member:
        flash("Membre introuvable.", "error")
        return redirect(url_for('promotion.members_list'))
    
    if request.method == 'POST':
        try:
            sql = """UPDATE promotion_members 
                     SET full_name = :full_name, phone = :phone, team_id = :team_id, 
                         is_active = :is_active, updated_at = :updated_at
                     WHERE id = :id"""
            
            team_id = request.form.get('team_id', '')
            team_id = int(team_id) if team_id else None
            
            db.session.execute(text(sql), {
                'id': id,
                'full_name': request.form.get('full_name'),
                'phone': request.form.get('phone'),
                'team_id': team_id,
                'is_active': request.form.get('is_active') == 'on',
                'updated_at': datetime.now(UTC)
            })
            db.session.commit()
            flash("Membre modifié avec succès!", "success")
            return redirect(url_for('promotion.members_list'))
        except Exception as e:
            db.session.rollback()
            flash(f"Erreur: {str(e)}", "error")
    
    teams = PromotionTeam.query.filter_by(is_active=True).all()
    return render_template('promotion/member_form.html', member=member, teams=teams)

@promotion_bp.route('/members/<int:member_id>/situation')
@login_required
def member_situation(member_id):
    """Situation individuelle d'un membre (stock et ventes)"""
    if not has_permission(current_user, 'promotion.read'):
        flash("Vous n'avez pas la permission d'accéder à cette page.", "error")
        return redirect(url_for('promotion.members_list'))
    
    member = get_member_safe(member_id)
    if not member:
        flash("Membre introuvable.", "error")
        return redirect(url_for('promotion.members_list'))
    
    # Récupérer le stock sous forme de dictionnaire
    stock_dict = get_member_stock(member_id)
    
    # Formater le stock pour le template (liste d'objets avec gamme et quantity)
    stock_data = []
    gammes = PromotionGamme.query.filter_by(is_active=True).all()
    for gamme in gammes:
        quantity = stock_dict.get(gamme.id, 0)
        if quantity > 0:  # Afficher seulement les gammes avec stock > 0
            stock_data.append({
                'gamme': gamme,
                'quantity': quantity
            })
    
    # Calculer les statistiques
    try:
        total_enlevements = db.session.query(func.sum(PromotionSale.quantity)).filter(
            PromotionSale.member_id == member_id,
            PromotionSale.transaction_type == 'enlevement'
        ).scalar() or 0
        
        total_retours = db.session.query(func.sum(PromotionSale.quantity)).filter(
            PromotionSale.member_id == member_id,
            PromotionSale.transaction_type == 'retour'
        ).scalar() or 0
        
        total_commission = db.session.query(func.sum(
            case(
                (PromotionSale.transaction_type == 'enlevement', PromotionSale.commission_gnf),
                else_=-PromotionSale.commission_gnf
            )
        )).filter(PromotionSale.member_id == member_id).scalar() or Decimal("0.00")
    except Exception:
        total_enlevements = 0
        total_retours = 0
        total_commission = Decimal("0.00")
    
    # Récupérer les ventes récentes
    try:
        sales = PromotionSale.query.options(
            load_only(PromotionSale.id, PromotionSale.gamme_id, PromotionSale.quantity,
                     PromotionSale.total_amount_gnf, PromotionSale.commission_gnf, 
                     PromotionSale.sale_date, PromotionSale.created_at)
        ).filter_by(member_id=member_id).order_by(PromotionSale.created_at.desc()).limit(20).all()
        
        for sale in sales:
            sale.gamme = PromotionGamme.query.options(
                load_only(PromotionGamme.id, PromotionGamme.name, PromotionGamme.selling_price_gnf, PromotionGamme.is_piece, PromotionGamme.unit_type)
            ).get(sale.gamme_id)
    except Exception:
        sales = []
    
    return render_template('promotion/member_situation.html', 
                         member=member, 
                         stock_data=stock_data,
                         total_enlevements=total_enlevements,
                         total_retours=total_retours,
                         total_returns=0,  # Pour compatibilité avec le template
                         total_commission=total_commission,
                         sales=sales, 
                         gammes=gammes)

@promotion_bp.route('/supervisor/stock')
@login_required
def supervisor_stock():
    """Situation du stock du superviseur"""
    if not has_permission(current_user, 'promotion.read'):
        flash("Vous n'avez pas la permission d'accéder à cette page.", "error")
        return redirect(url_for('promotion.dashboard'))
    
    # Récupérer le stock du superviseur (utilisateur actuel)
    supervisor_id = current_user.id
    stock_dict = get_supervisor_stock(supervisor_id)
    
    # Formater le stock pour le template (liste d'objets avec gamme et quantity)
    stock_data = []
    gammes = PromotionGamme.query.filter_by(is_active=True).all()
    total_stock_value = Decimal("0.00")
    
    # Récupérer les objets PromotionSupervisorStock pour avoir last_updated
    try:
        supervisor_stocks = PromotionSupervisorStock.query.filter_by(supervisor_id=supervisor_id).all()
        stock_objects = {stock.gamme_id: stock for stock in supervisor_stocks}
    except Exception:
        stock_objects = {}
    
    for gamme in gammes:
        quantity = stock_dict.get(gamme.id, 0)
        stock_obj = stock_objects.get(gamme.id)
        stock_data.append({
            'gamme': gamme,
            'quantity': quantity,
            'value': gamme.selling_price_gnf * quantity if gamme.selling_price_gnf else Decimal("0.00"),
            'last_updated': stock_obj.last_updated if stock_obj and stock_obj.last_updated else None
        })
        total_stock_value += gamme.selling_price_gnf * quantity if gamme.selling_price_gnf else Decimal("0.00")
    
    # Trier par quantité décroissante
    stock_data.sort(key=lambda x: x['quantity'], reverse=True)
    
    # Calculer le total des quantités
    total_quantity = sum(item['quantity'] for item in stock_data)
    
    return render_template('promotion/supervisor_stock.html',
                         stock_data=stock_data,
                         total_quantity=total_quantity,
                         total_stock_value=total_stock_value,
                         gammes=gammes)

@promotion_bp.route('/supervisor/stock/add', methods=['GET', 'POST'])
@login_required
def supervisor_stock_add():
    """Ajouter du stock au superviseur"""
    if not has_permission(current_user, 'promotion.write'):
        flash("Vous n'avez pas la permission d'effectuer cette opération.", "error")
        return redirect(url_for('promotion.supervisor_stock'))
    
    supervisor_id = current_user.id
    gammes = PromotionGamme.query.filter_by(is_active=True).all()
    
    # Valeur par défaut pour l'heure
    default_time = datetime.now(UTC).strftime('%H:%M')
    default_date = datetime.now(UTC).strftime('%Y-%m-%d')
    
    if request.method == 'POST':
        try:
            # Récupérer la date d'approvisionnement
            supply_date_str = request.form.get('supply_date')
            supply_time_str = request.form.get('supply_time', '00:00')
            
            if supply_date_str:
                try:
                    supply_datetime = datetime.strptime(f"{supply_date_str} {supply_time_str}", "%Y-%m-%d %H:%M")
                    supply_datetime = supply_datetime.replace(tzinfo=UTC)
                except ValueError:
                    supply_datetime = datetime.now(UTC)
            else:
                supply_datetime = datetime.now(UTC)
            
            # Récupérer les approvisionnements (plusieurs gammes possibles)
            supplies = []
            i = 0
            while True:
                gamme_id = request.form.get(f'gamme_id_{i}')
                quantity_str = request.form.get(f'quantity_{i}')
                
                if not gamme_id or not quantity_str:
                    break
                
                try:
                    quantity = int(quantity_str)
                    if quantity > 0:
                        supplies.append({
                            'gamme_id': int(gamme_id),
                            'quantity': quantity
                        })
                except ValueError:
                    pass
                
                i += 1
            
            if not supplies:
                flash("Veuillez ajouter au moins une gamme avec une quantité valide.", "error")
                return redirect(url_for('promotion.supervisor_stock_add'))
            
            # Générer une référence unique pour cet approvisionnement
            reference = request.form.get('reference') or generate_supply_reference()
            
            # Traiter tous les approvisionnements avec la même référence
            success_count = 0
            for supply in supplies:
                gamme_id = supply['gamme_id']
                quantity = supply['quantity']
                
                # Ajouter au stock du superviseur avec la référence dans les notes
                notes = f"Réf: {reference}"
                if update_supervisor_stock(supervisor_id, gamme_id, quantity, 'add', 
                                          movement_type='reception', 
                                          movement_date=supply_datetime,
                                          notes=notes):
                    success_count += 1
                else:
                    flash(f"Erreur lors de l'ajout du stock pour la gamme ID {gamme_id}.", "error")
            
            if success_count > 0:
                flash(f"✅ {success_count} approvisionnement(s) ajouté(s) au stock du superviseur avec succès le {supply_date_str or 'aujourd\'hui'}! Référence: {reference}", "success")
                return redirect(url_for('promotion.supervisor_stock'))
            else:
                flash("Aucun stock n'a pu être ajouté.", "error")
                
        except Exception as e:
            db.session.rollback()
            flash(f"Erreur lors de l'ajout du stock: {str(e)}", "error")
            print(f"Erreur lors de l'ajout du stock au superviseur: {e}")
            import traceback
            traceback.print_exc()
    
    return render_template('promotion/supervisor_stock_add.html', 
                         gammes=gammes,
                         default_date=default_date,
                         default_time=default_time)

@promotion_bp.route('/supervisor/stock/movements')
@login_required
def supervisor_stock_movements():
    """Historique des mouvements de stock du superviseur"""
    if not has_permission(current_user, 'promotion.read'):
        flash("Vous n'avez pas la permission d'accéder à cette page.", "error")
        return redirect(url_for('promotion.dashboard'))
    
    supervisor_id = current_user.id
    
    # Vérifier si la table existe
    table_exists = False
    try:
        db.session.execute(text("SELECT 1 FROM promotion_stock_movements LIMIT 1"))
        table_exists = True
    except Exception:
        table_exists = False
    
    # Récupérer les mouvements
    movements = []
    movements_with_balance = []  # Initialiser avant le bloc if
    if table_exists:
        try:
            movements = PromotionStockMovement.query.filter(
                or_(
                    PromotionStockMovement.from_supervisor_id == supervisor_id,
                    PromotionStockMovement.to_supervisor_id == supervisor_id
                )
            ).order_by(PromotionStockMovement.movement_date.asc()).limit(500).all()
            
            # Debug: vérification directe dans la DB
            try:
                from sqlalchemy import text
                db_movements = db.session.execute(
                    text("""
                        SELECT 
                            id, movement_type, movement_date, gamme_id, 
                            quantity, quantity_change, 
                            from_supervisor_id, to_supervisor_id,
                            notes
                        FROM promotion_stock_movements
                        WHERE from_supervisor_id = :supervisor_id OR to_supervisor_id = :supervisor_id
                        ORDER BY movement_date DESC
                        LIMIT 20
                    """),
                    {'supervisor_id': supervisor_id}
                ).fetchall()
                
                print(f"\n=== DEBUG DB DIRECTE - SUPERVISEUR {supervisor_id} ===")
                print(f"Nombre de mouvements dans la DB: {len(db_movements)}")
                if db_movements:
                    print("Mouvements récents (20 derniers):")
                    for m in db_movements:
                        date_str = m.movement_date.strftime('%d/%m/%Y %H:%M') if m.movement_date else 'N/A'
                        print(f"  - ID {m.id}: {date_str} | Type: {m.movement_type} | Gamme: {m.gamme_id} | Qty: {m.quantity_change} | From: {m.from_supervisor_id} | To: {m.to_supervisor_id} | Notes: {m.notes}")
                else:
                    print("⚠️ Aucun mouvement trouvé dans la DB pour ce superviseur")
                print(f"=== FIN DEBUG DB ===\n")
            except Exception as e:
                print(f"Erreur lors de la vérification DB directe: {e}")
            
            # Récupérer le stock actuel réel du superviseur
            current_stock = get_supervisor_stock(supervisor_id)
            
            # Calculer le solde progressif pour chaque gamme
            # On part du stock actuel et on remonte dans le temps
            stock_balances = {}  # {gamme_id: solde_actuel}
            movements_with_balance = []
            
            # Initialiser avec le stock actuel
            for gamme_id, qty in current_stock.items():
                stock_balances[gamme_id] = qty
            
            # Charger les relations et calculer le solde progressif en remontant dans le temps
            # On parcourt les mouvements du plus récent au plus ancien pour remonter dans le temps
            for movement in reversed(movements):
                if movement.gamme_id:
                    movement.gamme = PromotionGamme.query.options(
                        load_only(PromotionGamme.id, PromotionGamme.name, PromotionGamme.selling_price_gnf)
                    ).get(movement.gamme_id)
                if movement.from_team_id:
                    movement.from_team = PromotionTeam.query.options(
                        load_only(PromotionTeam.id, PromotionTeam.name)
                    ).get(movement.from_team_id)
                if movement.to_team_id:
                    movement.to_team = PromotionTeam.query.options(
                        load_only(PromotionTeam.id, PromotionTeam.name)
                    ).get(movement.to_team_id)
                if movement.from_member_id:
                    movement.from_member = get_member_safe(movement.from_member_id)
                if movement.to_member_id:
                    movement.to_member = get_member_safe(movement.to_member_id)
                if movement.sale_id:
                    movement.sale = PromotionSale.query.options(
                        load_only(PromotionSale.id, PromotionSale.reference, PromotionSale.transaction_type)
                    ).get(movement.sale_id)
                if movement.return_id:
                    movement.return_obj = PromotionReturn.query.options(
                        load_only(PromotionReturn.id, PromotionReturn.return_date)
                    ).get(movement.return_id)
                if movement.performed_by_id:
                    movement.performed_by = User.query.options(
                        load_only(User.id, User.full_name, User.email)
                    ).get(movement.performed_by_id)
                
                # Calculer le solde progressif pour cette gamme
                gamme_id = movement.gamme_id
                if gamme_id not in stock_balances:
                    stock_balances[gamme_id] = 0
                
                # Attacher le solde progressif AVANT le mouvement (on remonte dans le temps)
                movement.progressive_balance = stock_balances[gamme_id]
                
                # Déterminer si le mouvement augmente ou diminue le stock du superviseur
                # Pour un superviseur, on calcule le solde en fonction des mouvements vers/depuis ce superviseur
                # On soustrait le changement pour remonter dans le temps
                if movement.to_supervisor_id == supervisor_id:
                    # Stock entrant pour le superviseur : on soustrait pour remonter dans le temps
                    stock_balances[gamme_id] -= movement.quantity_change
                elif movement.from_supervisor_id == supervisor_id:
                    # Stock sortant du superviseur : on ajoute pour remonter dans le temps
                    stock_balances[gamme_id] += movement.quantity_change
                
                movements_with_balance.append(movement)
            
            # Inverser pour afficher du plus récent au plus ancien
            movements_with_balance.reverse()
            
            # Debug: afficher les mouvements récupérés
            print(f"\n=== DEBUG MOUVEMENTS SUPERVISEUR {supervisor_id} ===")
            print(f"Nombre de mouvements trouvés: {len(movements)}")
            print(f"Nombre de mouvements avec balance: {len(movements_with_balance)}")
            if movements:
                print("Dates des mouvements:")
                for m in movements[:10]:  # Afficher les 10 premiers
                    print(f"  - {m.movement_date.strftime('%d/%m/%Y %H:%M') if m.movement_date else 'N/A'}: {m.movement_type}, Gamme ID: {m.gamme_id}, Qty: {m.quantity_change}, From: {m.from_supervisor_id}, To: {m.to_supervisor_id}")
                if len(movements) > 10:
                    print(f"  ... et {len(movements) - 10} autres mouvements")
            else:
                print("⚠️ Aucun mouvement trouvé pour ce superviseur")
            print(f"=== FIN DEBUG ===\n")
            
        except Exception as e:
            print(f"Erreur lors de la récupération des mouvements: {e}")
            import traceback
            traceback.print_exc()
            movements_with_balance = []
    
    return render_template('promotion/stock_movements.html',
                         movements=movements_with_balance,
                         title="Mouvements de Stock - Superviseur",
                         entity_type="supervisor",
                         entity_id=supervisor_id,
                         table_exists=table_exists)

@promotion_bp.route('/stock/movements/rebuild', methods=['POST'])
@login_required
def rebuild_stock_movements():
    """Reconstruire l'historique des mouvements à partir des données existantes"""
    if not has_permission(current_user, 'promotion.write'):
        flash("Vous n'avez pas la permission d'effectuer cette opération.", "error")
        return redirect(url_for('promotion.dashboard'))
    
    try:
        # Vérifier si la table existe
        try:
            db.session.execute(text("SELECT 1 FROM promotion_stock_movements LIMIT 1"))
        except Exception:
            flash("La table promotion_stock_movements n'existe pas encore. Exécutez d'abord le script SQL.", "error")
            return redirect(url_for('promotion.dashboard'))
        
        created_count = 0
        
        # 1. Reconstruire les mouvements à partir des ventes (enlèvements et retours)
        try:
            sales = PromotionSale.query.options(
                load_only(PromotionSale.id, PromotionSale.member_id, PromotionSale.gamme_id,
                         PromotionSale.quantity, PromotionSale.sale_date, PromotionSale.recorded_by_id,
                         PromotionSale.transaction_type, PromotionSale.reference)
            ).order_by(PromotionSale.sale_date.asc()).all()
            
            for sale in sales:
                # Vérifier si le mouvement existe déjà
                existing = PromotionStockMovement.query.filter_by(sale_id=sale.id).first()
                if existing:
                    continue
                
                # Charger le membre pour obtenir l'équipe
                member = get_member_safe(sale.member_id)
                if not member:
                    continue
                
                transaction_type = getattr(sale, 'transaction_type', 'enlevement')
                
                if transaction_type == 'enlevement':
                    # Enlèvement : équipe → membre
                    sale_date = sale.sale_date if hasattr(sale, 'sale_date') and sale.sale_date else None
                    created_at = sale.created_at if hasattr(sale, 'created_at') and sale.created_at else datetime.now(UTC)
                    movement = PromotionStockMovement(
                        movement_type='enlevement',
                        movement_date=sale_date or created_at,
                        gamme_id=sale.gamme_id,
                        quantity=sale.quantity,
                        quantity_change=sale.quantity,
                        from_team_id=member.team_id if member else None,
                        to_member_id=sale.member_id,
                        sale_id=sale.id,
                        performed_by_id=sale.recorded_by_id or current_user.id
                    )
                else:  # retour
                    # Retour : membre → équipe
                    sale_date = sale.sale_date if hasattr(sale, 'sale_date') and sale.sale_date else None
                    created_at = sale.created_at if hasattr(sale, 'created_at') and sale.created_at else datetime.now(UTC)
                    movement = PromotionStockMovement(
                        movement_type='retour',
                        movement_date=sale_date or created_at,
                        gamme_id=sale.gamme_id,
                        quantity=sale.quantity,
                        quantity_change=-sale.quantity,
                        from_member_id=sale.member_id,
                        to_team_id=member.team_id if member else None,
                        sale_id=sale.id,
                        performed_by_id=sale.recorded_by_id or current_user.id
                    )
                
                db.session.add(movement)
                created_count += 1
        except Exception as e:
            print(f"Erreur lors de la reconstruction des mouvements depuis les ventes: {e}")
            import traceback
            traceback.print_exc()
        
        # 2. Reconstruire les mouvements à partir des retours approuvés
        try:
            returns = PromotionReturn.query.filter_by(status='approved').options(
                load_only(PromotionReturn.id, PromotionReturn.member_id, PromotionReturn.gamme_id,
                         PromotionReturn.quantity, PromotionReturn.return_date, PromotionReturn.approved_by_id)
            ).order_by(PromotionReturn.return_date.asc()).all()
            
            for return_obj in returns:
                # Vérifier si le mouvement existe déjà
                existing = PromotionStockMovement.query.filter_by(return_id=return_obj.id).first()
                if existing:
                    continue
                
                # Charger le membre pour obtenir l'équipe
                member = get_member_safe(return_obj.member_id)
                if not member:
                    continue
                
                # Retour approuvé : membre → équipe
                return_date = return_obj.return_date if hasattr(return_obj, 'return_date') and return_obj.return_date else None
                created_at = return_obj.created_at if hasattr(return_obj, 'created_at') and return_obj.created_at else datetime.now(UTC)
                movement = PromotionStockMovement(
                    movement_type='retour',
                    movement_date=return_date or created_at,
                    gamme_id=return_obj.gamme_id,
                    quantity=return_obj.quantity,
                    quantity_change=-return_obj.quantity,
                    from_member_id=return_obj.member_id,
                    to_team_id=member.team_id if member else None,
                    return_id=return_obj.id,
                    performed_by_id=return_obj.approved_by_id or current_user.id
                )
                
                db.session.add(movement)
                created_count += 1
        except Exception as e:
            print(f"Erreur lors de la reconstruction des mouvements depuis les retours: {e}")
            import traceback
            traceback.print_exc()
        
        # 3. Reconstruire les mouvements d'approvisionnement (superviseur → équipe)
        # On peut déduire cela des stocks d'équipe qui ont été créés
        try:
            team_stocks = PromotionTeamStock.query.options(
                load_only(PromotionTeamStock.team_id, PromotionTeamStock.gamme_id,
                         PromotionTeamStock.quantity, PromotionTeamStock.created_at)
            ).all()
            
            for team_stock in team_stocks:
                # Chercher le superviseur actuel (premier utilisateur avec rôle promotion_manager)
                supervisor = User.query.join(Role).filter(Role.name == 'promotion_manager').first()
                if not supervisor:
                    continue
                
                # Vérifier si un mouvement d'approvisionnement existe déjà pour cette équipe/gamme
                existing = PromotionStockMovement.query.filter_by(
                    from_supervisor_id=supervisor.id,
                    to_team_id=team_stock.team_id,
                    gamme_id=team_stock.gamme_id,
                    movement_type='approvisionnement'
                ).first()
                
                if existing:
                    continue
                
                # Créer un mouvement d'approvisionnement initial
                movement = PromotionStockMovement(
                    movement_type='approvisionnement',
                    movement_date=team_stock.created_at or datetime.now(UTC),
                    gamme_id=team_stock.gamme_id,
                    quantity=team_stock.quantity,
                    quantity_change=team_stock.quantity,
                    from_supervisor_id=supervisor.id,
                    to_team_id=team_stock.team_id,
                    performed_by_id=supervisor.id,
                    notes="Mouvement reconstruit depuis les données existantes"
                )
                
                db.session.add(movement)
                created_count += 1
        except Exception as e:
            print(f"Erreur lors de la reconstruction des mouvements d'approvisionnement: {e}")
            import traceback
            traceback.print_exc()
        
        db.session.commit()
        flash(f"✅ {created_count} mouvement(s) historique(s) reconstruit(s) avec succès!", "success")
        
    except Exception as e:
        db.session.rollback()
        flash(f"Erreur lors de la reconstruction de l'historique: {str(e)}", "error")
        print(f"Erreur lors de la reconstruction: {e}")
        import traceback
        traceback.print_exc()
    
    return redirect(request.referrer or url_for('promotion.dashboard'))

@promotion_bp.route('/stock/movements/create-table', methods=['POST'])
@login_required
def create_stock_movements_table():
    """Créer la table promotion_stock_movements si elle n'existe pas"""
    if not has_permission(current_user, 'promotion.write'):
        flash("Vous n'avez pas la permission d'effectuer cette opération.", "error")
        return redirect(url_for('promotion.dashboard'))
    
    try:
        # Vérifier si la table existe déjà
        try:
            db.session.execute(text("SELECT 1 FROM promotion_stock_movements LIMIT 1"))
            flash("La table promotion_stock_movements existe déjà.", "info")
            return redirect(request.referrer or url_for('promotion.dashboard'))
        except Exception:
            # La table n'existe pas, on la crée
            pass
        
        print(f"\n=== CRÉATION DE LA TABLE promotion_stock_movements ===")
        
        # Méthode 1: Utiliser db.create_all() pour créer uniquement cette table
        try:
            from models import PromotionStockMovement
            PromotionStockMovement.__table__.create(db.engine, checkfirst=True)
            print("✅ Table créée avec db.create_all()")
        except Exception as e1:
            print(f"⚠️ Méthode 1 échouée: {e1}")
            # Méthode 2: Exécuter le script SQL
            try:
                import os
                sql_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'scripts', 'create_promotion_stock_movements.sql')
                
                if not os.path.exists(sql_file):
                    raise FileNotFoundError(f"Fichier SQL introuvable: {sql_file}")
                
                with open(sql_file, 'r', encoding='utf-8') as f:
                    sql_script = f.read()
                
                # Exécuter le script SQL complet
                # MySQL peut exécuter plusieurs instructions en une fois
                try:
                    # Exécuter tout le script en une fois
                    db.session.execute(text(sql_script))
                    db.session.commit()
                    print("✅ Table créée avec le script SQL")
                except Exception as e2:
                    # Si ça échoue, essayer instruction par instruction
                    print(f"⚠️ Exécution complète échouée, tentative instruction par instruction: {e2}")
                    statements = []
                    current_statement = ""
                    for line in sql_script.split('\n'):
                        line = line.strip()
                        if not line or line.startswith('--'):
                            continue
                        current_statement += line + " "
                        if line.endswith(';'):
                            statements.append(current_statement.strip())
                            current_statement = ""
                    
                    for statement in statements:
                        if statement and statement != ';':
                            try:
                                db.session.execute(text(statement))
                            except Exception as e3:
                                # Ignorer les erreurs "table already exists"
                                if "already exists" not in str(e3).lower() and "Duplicate table" not in str(e3).lower():
                                    print(f"⚠️ Erreur lors de l'exécution de l'instruction SQL: {e3}")
                    
                    db.session.commit()
                    print("✅ Table créée instruction par instruction")
            except Exception as e2:
                print(f"❌ Méthode 2 échouée: {e2}")
                raise
        
        # Vérifier que la table existe maintenant
        try:
            db.session.execute(text("SELECT 1 FROM promotion_stock_movements LIMIT 1"))
            print("✅ Vérification: La table existe bien")
            flash("✅ Table promotion_stock_movements créée avec succès! Les nouveaux mouvements seront maintenant enregistrés automatiquement.", "success")
        except Exception as e:
            print(f"❌ Erreur de vérification: {e}")
            flash("⚠️ La table n'a pas pu être créée. Vérifiez les logs pour plus de détails.", "error")
        
        print(f"=== FIN CRÉATION TABLE ===\n")
        
    except Exception as e:
        db.session.rollback()
        flash(f"Erreur lors de la création de la table: {str(e)}", "error")
        print(f"❌ Erreur lors de la création de la table: {e}")
        import traceback
        traceback.print_exc()
    
    return redirect(request.referrer or url_for('promotion.dashboard'))

@promotion_bp.route('/stock/movements/clear', methods=['POST'])
@login_required
def clear_stock_movements():
    """Supprimer tous les mouvements de stock de la promotion"""
    if not has_permission(current_user, 'promotion.write'):
        flash("Vous n'avez pas la permission d'effectuer cette opération.", "error")
        return redirect(url_for('promotion.dashboard'))
    
    try:
        # Vérifier si la table existe
        try:
            db.session.execute(text("SELECT 1 FROM promotion_stock_movements LIMIT 1"))
        except Exception:
            flash("La table promotion_stock_movements n'existe pas encore.", "error")
            return redirect(url_for('promotion.dashboard'))
        
        # Compter les mouvements avant suppression
        count = PromotionStockMovement.query.count()
        
        # Supprimer tous les mouvements
        PromotionStockMovement.query.delete()
        db.session.commit()
        
        flash(f"✅ {count} mouvement(s) de stock supprimé(s) avec succès. Vous pouvez maintenant recommencer.", "success")
        
    except Exception as e:
        db.session.rollback()
        flash(f"Erreur lors de la suppression des mouvements: {str(e)}", "error")
        print(f"Erreur lors de la suppression: {e}")
        import traceback
        traceback.print_exc()
    
    return redirect(request.referrer or url_for('promotion.dashboard'))

@promotion_bp.route('/members/<int:member_id>/stock/movements')
@login_required
def member_stock_movements(member_id):
    """Historique des mouvements de stock d'un membre"""
    if not has_permission(current_user, 'promotion.read'):
        flash("Vous n'avez pas la permission d'accéder à cette page.", "error")
        return redirect(url_for('promotion.members_list'))
    
    member = get_member_safe(member_id)
    if not member:
        flash("Membre introuvable.", "error")
        return redirect(url_for('promotion.members_list'))
    
    # Vérifier si la table existe
    table_exists = False
    try:
        db.session.execute(text("SELECT 1 FROM promotion_stock_movements LIMIT 1"))
        table_exists = True
    except Exception:
        table_exists = False
    
    # Récupérer les mouvements
    movements = []
    movements_with_balance = []  # Initialiser avant le bloc if
    if table_exists:
        try:
            movements = PromotionStockMovement.query.filter(
                or_(
                    PromotionStockMovement.from_member_id == member_id,
                    PromotionStockMovement.to_member_id == member_id
                )
            ).order_by(PromotionStockMovement.movement_date.asc()).limit(500).all()
            
            # Debug: afficher les mouvements récupérés
            print(f"\n=== DEBUG MOUVEMENTS MEMBRE {member_id} ===")
            print(f"Nombre de mouvements trouvés: {len(movements)}")
            if movements:
                print("Dates des mouvements:")
                for m in movements[:10]:  # Afficher les 10 premiers
                    print(f"  - {m.movement_date.strftime('%d/%m/%Y %H:%M') if m.movement_date else 'N/A'}: {m.movement_type}, Gamme ID: {m.gamme_id}, Qty: {m.quantity_change}")
                if len(movements) > 10:
                    print(f"  ... et {len(movements) - 10} autres mouvements")
            else:
                print("⚠️ Aucun mouvement trouvé pour ce membre")
            print(f"=== FIN DEBUG ===\n")
            
            # Calculer le solde progressif pour chaque gamme
            # Logique pour le membre : Stock = Enlèvements - Retours
            # L'enlèvement représente l'approvisionnement, le retour le diminue
            # On part de 0 et on avance dans le temps
            stock_balances = {}  # {gamme_id: solde_actuel}
            movements_with_balance = []
            
            # Charger les relations et calculer le solde progressif en avançant dans le temps
            # On parcourt les mouvements du plus ancien au plus récent
            for movement in movements:
                if movement.gamme_id:
                    movement.gamme = PromotionGamme.query.options(
                        load_only(PromotionGamme.id, PromotionGamme.name, PromotionGamme.selling_price_gnf)
                    ).get(movement.gamme_id)
                if movement.from_team_id:
                    movement.from_team = PromotionTeam.query.options(
                        load_only(PromotionTeam.id, PromotionTeam.name)
                    ).get(movement.from_team_id)
                if movement.from_member_id:
                    movement.from_member = get_member_safe(movement.from_member_id)
                if movement.to_member_id:
                    movement.to_member = get_member_safe(movement.to_member_id)
                if movement.sale_id:
                    movement.sale = PromotionSale.query.options(
                        load_only(PromotionSale.id, PromotionSale.reference, PromotionSale.transaction_type)
                    ).get(movement.sale_id)
                if movement.return_id:
                    movement.return_obj = PromotionReturn.query.options(
                        load_only(PromotionReturn.id, PromotionReturn.return_date)
                    ).get(movement.return_id)
                if movement.performed_by_id:
                    movement.performed_by = User.query.options(
                        load_only(User.id, User.full_name, User.email)
                    ).get(movement.performed_by_id)
                
                # Calculer le solde progressif pour cette gamme
                gamme_id = movement.gamme_id
                if gamme_id not in stock_balances:
                    stock_balances[gamme_id] = 0
                
                # Déterminer si le mouvement augmente ou diminue le stock du membre
                # Logique : Stock = Enlèvements - Retours
                # L'enlèvement représente l'approvisionnement, le retour le diminue
                if movement.to_member_id == member_id:
                    # Stock entrant pour le membre (enlèvement depuis l'équipe = approvisionnement)
                    # Enlèvement : movement_type = 'enlevement' ou 'distribution'
                    # quantity_change est positif dans la DB (quantité reçue)
                    stock_balances[gamme_id] += movement.quantity_change
                elif movement.from_member_id == member_id:
                    # Stock sortant du membre (retour vers l'équipe)
                    # Retour : movement_type = 'retour'
                    # quantity_change est négatif dans la DB
                    # Donc on ajoute quantity_change (qui est négatif) = on soustrait
                    stock_balances[gamme_id] += movement.quantity_change
                    if stock_balances[gamme_id] < 0:
                        stock_balances[gamme_id] = 0
                
                # Attacher le solde progressif APRÈS le mouvement
                movement.progressive_balance = stock_balances[gamme_id]
                movements_with_balance.append(movement)
            
            # Inverser pour afficher du plus récent au plus ancien
            movements_with_balance.reverse()
            
        except Exception as e:
            print(f"Erreur lors de la récupération des mouvements: {e}")
            import traceback
            traceback.print_exc()
            movements_with_balance = []
    
    # Debug supplémentaire : vérifier directement dans la DB
    if table_exists:
        try:
            from sqlalchemy import text
            db_movements = db.session.execute(
                text("""
                    SELECT 
                        id, movement_type, movement_date, gamme_id, 
                        quantity, quantity_change, 
                        from_member_id, to_member_id,
                        sale_id, return_id
                    FROM promotion_stock_movements
                    WHERE from_member_id = :member_id OR to_member_id = :member_id
                    ORDER BY movement_date DESC
                    LIMIT 20
                """),
                {'member_id': member_id}
            ).fetchall()
            
            print(f"\n=== DEBUG DB DIRECTE - MEMBRE {member_id} ===")
            print(f"Nombre de mouvements dans la DB: {len(db_movements)}")
            if db_movements:
                print("Mouvements récents (20 derniers):")
                for m in db_movements:
                    date_str = m.movement_date.strftime('%d/%m/%Y %H:%M') if m.movement_date else 'N/A'
                    print(f"  - ID {m.id}: {date_str} | Type: {m.movement_type} | Gamme: {m.gamme_id} | Qty: {m.quantity_change} | From: {m.from_member_id} | To: {m.to_member_id}")
            else:
                print("⚠️ Aucun mouvement trouvé dans la DB pour ce membre")
            print(f"=== FIN DEBUG DB ===\n")
        except Exception as e:
            print(f"Erreur lors de la vérification DB directe: {e}")
    
    return render_template('promotion/stock_movements.html',
                         movements=movements_with_balance,
                         title=f"Mouvements de Stock - {member.full_name}",
                         entity_type="member",
                         entity_id=member_id,
                         member=member,
                         table_exists=table_exists)

@promotion_bp.route('/teams/<int:team_id>/stock/movements')
@login_required
def team_stock_movements(team_id):
    """Historique des mouvements de stock d'une équipe"""
    if not has_permission(current_user, 'promotion.read'):
        flash("Vous n'avez pas la permission d'accéder à cette page.", "error")
        return redirect(url_for('promotion.teams_list'))
    
    team = PromotionTeam.query.get_or_404(team_id)
    
    # Vérifier si la table existe
    table_exists = False
    try:
        db.session.execute(text("SELECT 1 FROM promotion_stock_movements LIMIT 1"))
        table_exists = True
    except Exception:
        table_exists = False
    
    # Récupérer les mouvements
    movements = []
    movements_with_balance = []  # Initialiser avant le bloc if
    if table_exists:
        try:
            movements = PromotionStockMovement.query.filter(
                or_(
                    PromotionStockMovement.from_team_id == team_id,
                    PromotionStockMovement.to_team_id == team_id
                )
            ).order_by(PromotionStockMovement.movement_date.asc()).limit(100).all()
            
            # Calculer le solde progressif pour chaque gamme
            stock_balances = {}  # {gamme_id: solde_actuel}
            movements_with_balance = []
            
            # Charger les relations et calculer le solde progressif
            for movement in movements:
                if movement.gamme_id:
                    movement.gamme = PromotionGamme.query.options(
                        load_only(PromotionGamme.id, PromotionGamme.name, PromotionGamme.selling_price_gnf)
                    ).get(movement.gamme_id)
                if movement.from_supervisor_id:
                    movement.from_supervisor = User.query.options(
                        load_only(User.id, User.full_name, User.email)
                    ).get(movement.from_supervisor_id)
                if movement.to_supervisor_id:
                    movement.to_supervisor = User.query.options(
                        load_only(User.id, User.full_name, User.email)
                    ).get(movement.to_supervisor_id)
                if movement.from_team_id:
                    movement.from_team = PromotionTeam.query.options(
                        load_only(PromotionTeam.id, PromotionTeam.name)
                    ).get(movement.from_team_id)
                if movement.to_team_id:
                    movement.to_team = PromotionTeam.query.options(
                        load_only(PromotionTeam.id, PromotionTeam.name)
                    ).get(movement.to_team_id)
                if movement.from_member_id:
                    movement.from_member = get_member_safe(movement.from_member_id)
                if movement.to_member_id:
                    movement.to_member = get_member_safe(movement.to_member_id)
                if movement.sale_id:
                    movement.sale = PromotionSale.query.options(
                        load_only(PromotionSale.id, PromotionSale.reference, PromotionSale.transaction_type)
                    ).get(movement.sale_id)
                if movement.return_id:
                    movement.return_obj = PromotionReturn.query.options(
                        load_only(PromotionReturn.id, PromotionReturn.return_date)
                    ).get(movement.return_id)
                if movement.performed_by_id:
                    movement.performed_by = User.query.options(
                        load_only(User.id, User.full_name, User.email)
                    ).get(movement.performed_by_id)
                
                # Calculer le solde progressif pour cette gamme
                gamme_id = movement.gamme_id
                if gamme_id not in stock_balances:
                    stock_balances[gamme_id] = 0
                
                # Déterminer si le mouvement augmente ou diminue le stock de l'équipe
                # Logique : Stock = Approvisionnement - Enlèvements + Retours
                if movement.to_team_id == team_id:
                    # Stock entrant dans l'équipe
                    if movement.movement_type == 'approvisionnement':
                        # Approvisionnement depuis superviseur : quantity_change est positif
                        stock_balances[gamme_id] += movement.quantity_change
                    elif movement.movement_type == 'retour':
                        # Retour depuis membre : quantity_change est négatif dans la DB
                        # Mais pour l'équipe, c'est un ajout, donc on ajoute la valeur absolue
                        stock_balances[gamme_id] += abs(movement.quantity_change)
                elif movement.from_team_id == team_id:
                    # Stock sortant de l'équipe (enlèvement vers membre)
                    # Enlèvement : movement_type = 'enlevement' ou 'distribution'
                    # quantity_change est positif dans la DB (quantité enlevée)
                    # Donc on soustrait
                    stock_balances[gamme_id] -= abs(movement.quantity_change)
                    if stock_balances[gamme_id] < 0:
                        stock_balances[gamme_id] = 0
                
                # Attacher le solde progressif APRÈS le mouvement
                movement.progressive_balance = stock_balances[gamme_id]
                movements_with_balance.append(movement)
            
            # Inverser pour afficher du plus récent au plus ancien
            movements_with_balance.reverse()
            
        except Exception as e:
            print(f"Erreur lors de la récupération des mouvements de l'équipe: {e}")
            import traceback
            traceback.print_exc()
            movements_with_balance = []
    
    # Debug: Afficher les détails des mouvements dans la console
    if movements_with_balance:
        print(f"\n🔍 DEBUG - Mouvements pour l'équipe {team.name} (ID: {team_id}):")
        print("=" * 80)
        for movement in movements_with_balance:
            print(f"  Date: {movement.movement_date.strftime('%d/%m/%Y %H:%M')}")
            print(f"  Type: {movement.movement_type}")
            print(f"  Gamme ID: {movement.gamme_id}")
            print(f"  Quantity Change: {movement.quantity_change}")
            print(f"  From Team: {movement.from_team_id}, To Team: {movement.to_team_id}")
            print(f"  Solde Progressif: {getattr(movement, 'progressive_balance', 'N/A')}")
            print("-" * 80)
    
    return render_template('promotion/stock_movements.html',
                         movements=movements_with_balance,
                         title=f"Mouvements de Stock - {team.name}",
                         entity_type="team",
                         entity_id=team_id,
                         team=team,
                         table_exists=table_exists)

@promotion_bp.route('/members/<int:member_id>/assign-stock', methods=['GET', 'POST'])
@login_required
def assign_member_stock(member_id):
    """Affecter des quantités de gammes à un membre"""
    if not has_permission(current_user, 'promotion.write'):
        flash("Vous n'avez pas la permission d'affecter des quantités.", "error")
        return redirect(url_for('promotion.members_list'))
    
    member = get_member_safe(member_id)
    if not member:
        flash("Membre introuvable.", "error")
        return redirect(url_for('promotion.members_list'))
    
    if request.method == 'POST':
        try:
            assignment_date_str = request.form.get('assignment_date', '')
            
            # Parser la date d'affectation
            if assignment_date_str:
                try:
                    assignment_date = datetime.strptime(assignment_date_str, '%Y-%m-%d').date()
                    assignment_datetime = datetime.combine(assignment_date, datetime.min.time()).replace(tzinfo=UTC)
                except ValueError:
                    assignment_datetime = datetime.now(UTC)
            else:
                assignment_datetime = datetime.now(UTC)
            
            # Récupérer toutes les affectations (plusieurs gammes/pièces)
            assignments = []
            i = 0
            while True:
                gamme_id_str = request.form.get(f'gamme_id_{i}')
                quantity_str = request.form.get(f'quantity_{i}')
                
                if not gamme_id_str or not quantity_str:
                    break
                
                try:
                    gamme_id = int(gamme_id_str)
                    quantity = int(quantity_str)
                    
                    if quantity < 0:
                        i += 1
                        continue
                    
                    assignments.append({
                        'gamme_id': gamme_id,
                        'quantity': quantity
                    })
                except (ValueError, TypeError):
                    pass
                
                i += 1
            
            if not assignments:
                flash("Veuillez ajouter au moins une gamme/pièce avec une quantité valide.", "error")
                return redirect(url_for('promotion.assign_member_stock', member_id=member_id))
            
            # Vérifier le stock de l'équipe si le membre appartient à une équipe
            if member.team_id:
                team_stock = get_team_stock(member.team_id)
                for assignment in assignments:
                    gamme_id = assignment['gamme_id']
                    new_quantity = assignment['quantity']
                    
                    # Récupérer l'ancien stock du membre
                    old_stock = PromotionMemberStock.query.filter_by(
                        member_id=member_id,
                        gamme_id=gamme_id
                    ).first()
                    old_quantity = old_stock.quantity if old_stock else 0
                    
                    # Calculer la différence
                    quantity_diff = new_quantity - old_quantity
                    
                    if quantity_diff > 0:
                        # On augmente le stock, vérifier que l'équipe a assez
                        current_team_stock = team_stock.get(gamme_id, 0)
                        if current_team_stock < quantity_diff:
                            gamme = PromotionGamme.query.get(gamme_id)
                            flash(f"⚠️ Stock insuffisant dans l'équipe! Stock disponible: {current_team_stock} unité(s) de {gamme.name if gamme else 'N/A'}. Besoin: {quantity_diff} unité(s). Opération annulée.", "error")
                            return redirect(url_for('promotion.assign_member_stock', member_id=member_id))
            
            # Traiter toutes les affectations
            success_count = 0
            for assignment in assignments:
                gamme_id = assignment['gamme_id']
                quantity = assignment['quantity']
                
                # Récupérer l'ancien stock pour calculer la différence
                old_stock = PromotionMemberStock.query.filter_by(
                    member_id=member_id,
                    gamme_id=gamme_id
                ).first()
                old_quantity = old_stock.quantity if old_stock else 0
                quantity_diff = quantity - old_quantity
                
                # Mettre à jour ou créer le stock du membre
                if old_stock:
                    old_stock.quantity = quantity
                    old_stock.last_updated = assignment_datetime
                else:
                    stock = PromotionMemberStock(
                        member_id=member_id,
                        gamme_id=gamme_id,
                        quantity=quantity,
                        last_updated=assignment_datetime
                    )
                    db.session.add(stock)
                
                # Si le membre appartient à une équipe et qu'on augmente le stock, déduire du stock de l'équipe
                if member.team_id and quantity_diff > 0:
                    update_team_stock(member.team_id, gamme_id, quantity_diff, 'subtract',
                                     movement_type='affectation', to_member_id=member_id,
                                     movement_date=assignment_datetime)
                
                success_count += 1
            
            db.session.commit()
            flash(f"{success_count} affectation(s) enregistrée(s) avec succès le {assignment_date_str or 'aujourd\'hui'}!", "success")
            return redirect(url_for('promotion.member_situation', member_id=member_id))
        except Exception as e:
            db.session.rollback()
            flash(f"Erreur lors de l'affectation: {str(e)}", "error")
    
    gammes = PromotionGamme.query.filter_by(is_active=True).order_by(PromotionGamme.name).all()
    current_stocks = get_member_stock(member_id)
    today = date.today()
    return render_template('promotion/assign_stock.html',
                         member=member, gammes=gammes, current_stocks=current_stocks, today=today)

# =========================================================
# GESTION DES VENTES
# =========================================================

@promotion_bp.route('/sales')
@login_required
def sales_list():
    """Liste des ventes"""
    if not has_permission(current_user, 'promotion.read'):
        flash("Vous n'avez pas la permission d'accéder à cette page.", "error")
        return redirect(url_for('index'))
    
    # Filtres
    search = request.args.get('search', '')
    team_id = request.args.get('team_id', type=int)
    member_id = request.args.get('member_id', type=int)
    gamme_id = request.args.get('gamme_id', type=int)
    transaction_type = request.args.get('transaction_type', '')
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    
    # Construire la requête avec filtrage par région
    from utils_region_filter import filter_sales_by_region
    query = PromotionSale.query
    query = filter_sales_by_region(query)
    
    # Vérifier si transaction_type existe
    check_type_sql = """SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS 
                       WHERE TABLE_SCHEMA = DATABASE() 
                       AND TABLE_NAME = 'promotion_sales' 
                       AND COLUMN_NAME = 'transaction_type'"""
    has_transaction_type = db.session.execute(text(check_type_sql)).scalar() > 0
    
    # Appliquer les filtres
    if member_id:
        query = query.filter_by(member_id=member_id)
    if gamme_id:
        query = query.filter_by(gamme_id=gamme_id)
    if date_from:
        try:
            date_from_obj = datetime.strptime(date_from, '%Y-%m-%d').date()
            query = query.filter(PromotionSale.sale_date >= date_from_obj)
        except:
            pass
    if date_to:
        try:
            date_to_obj = datetime.strptime(date_to, '%Y-%m-%d').date()
            query = query.filter(PromotionSale.sale_date <= date_to_obj)
        except:
            pass
    
    if has_transaction_type and transaction_type:
        query = query.filter(PromotionSale.transaction_type == transaction_type)
    
    # Recherche par nom de membre ou référence
    if search:
        # Récupérer les IDs des membres correspondants
        try:
            member_ids_search = [row[0] for row in db.session.query(PromotionMember.id).filter(
                PromotionMember.full_name.ilike(f'%{search}%')
            ).all()]
            
            # Filtrer par membre ou référence
            if member_ids_search:
                query = query.filter(
                    or_(
                        PromotionSale.member_id.in_(member_ids_search),
                        PromotionSale.reference.ilike(f'%{search}%')
                    )
                )
            else:
                # Si aucun membre trouvé, chercher seulement par référence
                query = query.filter(PromotionSale.reference.ilike(f'%{search}%'))
        except Exception as e:
            print(f"Erreur recherche: {e}")
            # En cas d'erreur, chercher seulement par référence
            query = query.filter(PromotionSale.reference.ilike(f'%{search}%'))
    
    # Pagination
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    
    # Charger avec load_only pour éviter les colonnes manquantes
    try:
        load_columns = [
            PromotionSale.id, PromotionSale.member_id, PromotionSale.gamme_id,
            PromotionSale.quantity, PromotionSale.total_amount_gnf,
            PromotionSale.commission_gnf, PromotionSale.sale_date,
            PromotionSale.created_at
        ]
        
        if has_transaction_type:
            load_columns.append(PromotionSale.transaction_type)
        
        # Pagination
        pagination = query.options(load_only(*load_columns)).order_by(
            PromotionSale.created_at.desc()
        ).paginate(page=page, per_page=per_page, error_out=False)
        
        sales = pagination.items
        
        # Optimisation: Charger les membres et gammes en batch
        member_ids = list(set([s.member_id for s in sales]))
        gamme_ids = list(set([s.gamme_id for s in sales]))
        
        members_map = load_members_batch(member_ids)
        gammes_map = load_gammes_batch(gamme_ids)
        
        # Charger les équipes pour les membres en batch
        team_ids = list(set([m.team_id for m in members_map.values() if m and m.team_id]))
        teams_map = load_teams_batch(team_ids)
        
        # Assigner les équipes aux membres
        for member in members_map.values():
            if member and member.team_id:
                member.team = teams_map.get(member.team_id)
        
        # Charger les références en batch si nécessaire
        sale_ids = [s.id for s in sales]
        references_map = {}
        if sale_ids:
            try:
                ref_sql = "SELECT id, reference FROM promotion_sales WHERE id IN :sale_ids"
                ref_results = db.session.execute(
                    text(ref_sql.replace(':sale_ids', f"({','.join(map(str, sale_ids))})"))
                ).fetchall()
                references_map = {row[0]: row[1] for row in ref_results}
            except:
                pass
        
        # Assigner les relations
        for sale in sales:
            sale.member = members_map.get(sale.member_id)
            sale.gamme = gammes_map.get(sale.gamme_id)
            
            # Définir reference et transaction_type si manquants
            if '_sa_instance_state' in sale.__dict__:
                if 'reference' not in sale.__dict__:
                    sale.__dict__['reference'] = references_map.get(sale.id)
                
                if not has_transaction_type or 'transaction_type' not in sale.__dict__:
                    sale.__dict__['transaction_type'] = 'enlevement'
            else:
                sale.reference = references_map.get(sale.id)
                sale.transaction_type = 'enlevement'
    except Exception as e:
        print(f"DEBUG sales_list error: {e}")
        sales = []
        pagination = None
    
    # Statistiques
    try:
        if has_transaction_type:
            enlevements_query = PromotionSale.query.filter(PromotionSale.transaction_type == 'enlevement')
            retours_query = PromotionSale.query.filter(PromotionSale.transaction_type == 'retour')
            
            revenue_enlevements = db.session.query(func.sum(PromotionSale.total_amount_gnf)).filter(
                PromotionSale.transaction_type == 'enlevement'
            ).scalar() or Decimal("0.00")
            
            revenue_retours = db.session.query(func.sum(PromotionSale.total_amount_gnf)).filter(
                PromotionSale.transaction_type == 'retour'
            ).scalar() or Decimal("0.00")
            
            ca_net = revenue_enlevements - revenue_retours
            
            commission_enlevements = db.session.query(func.sum(PromotionSale.commission_gnf)).filter(
                PromotionSale.transaction_type == 'enlevement'
            ).scalar() or Decimal("0.00")
            
            commission_retours = db.session.query(func.sum(PromotionSale.commission_gnf)).filter(
                PromotionSale.transaction_type == 'retour'
            ).scalar() or Decimal("0.00")
            
            commission_nette = commission_enlevements - commission_retours
            
            resultat_net = ca_net - commission_nette
            
            stats = {
                'total_sales': count_sales_safe(),
                'total_enlevements': enlevements_query.count(),
                'total_retours': retours_query.count(),
                'total_quantity': db.session.query(func.sum(PromotionSale.quantity)).scalar() or 0,
                'quantity_enlevements': db.session.query(func.sum(PromotionSale.quantity)).filter(PromotionSale.transaction_type == 'enlevement').scalar() or 0,
                'quantity_retours': db.session.query(func.sum(PromotionSale.quantity)).filter(PromotionSale.transaction_type == 'retour').scalar() or 0,
                'total_revenue': db.session.query(func.sum(PromotionSale.total_amount_gnf)).scalar() or Decimal("0.00"),
                'revenue_enlevements': revenue_enlevements,
                'revenue_retours': revenue_retours,
                'ca_net': ca_net,
                'total_commissions': db.session.query(func.sum(PromotionSale.commission_gnf)).scalar() or Decimal("0.00"),
                'commission_enlevements': commission_enlevements,
                'commission_retours': commission_retours,
                'commission_nette': commission_nette,
                'resultat_net': resultat_net,
            }
        else:
            total_revenue = db.session.query(func.sum(PromotionSale.total_amount_gnf)).scalar() or Decimal("0.00")
            total_commissions = db.session.query(func.sum(PromotionSale.commission_gnf)).scalar() or Decimal("0.00")
            stats = {
                'total_sales': count_sales_safe(),
                'total_enlevements': count_sales_safe(),
                'total_retours': 0,
                'total_quantity': db.session.query(func.sum(PromotionSale.quantity)).scalar() or 0,
                'quantity_enlevements': db.session.query(func.sum(PromotionSale.quantity)).scalar() or 0,
                'quantity_retours': 0,
                'total_revenue': total_revenue,
                'revenue_enlevements': total_revenue,
                'revenue_retours': Decimal("0.00"),
                'ca_net': total_revenue,
                'total_commissions': total_commissions,
                'commission_enlevements': total_commissions,
                'commission_retours': Decimal("0.00"),
                'commission_nette': total_commissions,
                'resultat_net': total_revenue - total_commissions,
            }
    except Exception:
        stats = {
            'total_sales': 0, 'total_enlevements': 0, 'total_retours': 0,
            'total_quantity': 0, 'quantity_enlevements': 0, 'quantity_retours': 0,
            'total_revenue': Decimal("0.00"), 'revenue_enlevements': Decimal("0.00"),
            'revenue_retours': Decimal("0.00"), 'ca_net': Decimal("0.00"),
            'total_commissions': Decimal("0.00"), 'commission_enlevements': Decimal("0.00"),
            'commission_retours': Decimal("0.00"), 'commission_nette': Decimal("0.00"),
            'resultat_net': Decimal("0.00")
        }
    
    teams = PromotionTeam.query.filter_by(is_active=True).all()
    members = PromotionMember.query.options(
        load_only(PromotionMember.id, PromotionMember.full_name)
    ).filter_by(is_active=True).all()
    gammes = PromotionGamme.query.filter_by(is_active=True).all()
    
    return render_template('promotion/sales_list.html', 
                         sales=sales, 
                         stats=stats, 
                         teams=teams,
                         members=members, 
                         gammes=gammes, 
                         pagination=pagination,
                         search=search, 
                         team_id=team_id,
                         member_id=member_id, 
                         gamme_id=gamme_id, 
                         transaction_type=transaction_type,
                         date_from=date_from, 
                         date_to=date_to)

@promotion_bp.route('/sales/export/pdf')
@login_required
def sales_export_pdf():
    """Export PDF des ventes avec filtres appliqués"""
    if not has_permission(current_user, 'promotion.read'):
        flash("Vous n'avez pas la permission d'exporter les données.", "error")
        return redirect(url_for('promotion.sales_list'))
    
    from flask import make_response
    from pdf_generator import PDFGenerator
    
    # Récupérer les mêmes filtres que sales_list
    search = request.args.get('search', '').strip()
    team_id = request.args.get('team_id', type=int)
    member_id = request.args.get('member_id', type=int)
    gamme_id = request.args.get('gamme_id', type=int)
    transaction_type = request.args.get('transaction_type', '')
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    
    try:
        # Construire la requête (même logique que sales_list)
        query = PromotionSale.query
        has_transaction_type = has_transaction_type_column_cached()
        
        # Appliquer les filtres
        if member_id:
            query = query.filter_by(member_id=member_id)
        if gamme_id:
            query = query.filter_by(gamme_id=gamme_id)
        if date_from:
            try:
                date_from_obj = datetime.strptime(date_from, '%Y-%m-%d').date()
                query = query.filter(PromotionSale.sale_date >= date_from_obj)
            except:
                pass
        if date_to:
            try:
                date_to_obj = datetime.strptime(date_to, '%Y-%m-%d').date()
                query = query.filter(PromotionSale.sale_date <= date_to_obj)
            except:
                pass
        
        if has_transaction_type and transaction_type:
            query = query.filter(PromotionSale.transaction_type == transaction_type)
        
        # Recherche
        if search:
            try:
                member_ids_search = [row[0] for row in db.session.query(PromotionMember.id).filter(
                    PromotionMember.full_name.ilike(f'%{search}%')
                ).all()]
                
                if member_ids_search:
                    query = query.filter(
                        or_(
                            PromotionSale.member_id.in_(member_ids_search),
                            PromotionSale.reference.ilike(f'%{search}%')
                        )
                    )
                else:
                    query = query.filter(PromotionSale.reference.ilike(f'%{search}%'))
            except:
                query = query.filter(PromotionSale.reference.ilike(f'%{search}%'))
        
        # Récupérer toutes les ventes
        load_columns = [
            PromotionSale.id, PromotionSale.member_id, PromotionSale.gamme_id,
            PromotionSale.quantity, PromotionSale.total_amount_gnf,
            PromotionSale.commission_gnf, PromotionSale.sale_date,
            PromotionSale.created_at, PromotionSale.reference
        ]
        
        if has_transaction_type:
            load_columns.append(PromotionSale.transaction_type)
        
        sales = query.options(load_only(*load_columns)).order_by(
            PromotionSale.created_at.desc()
        ).limit(1000).all()  # Limite pour PDF
        
        # Charger les relations en batch
        member_ids = list(set([s.member_id for s in sales]))
        gamme_ids = list(set([s.gamme_id for s in sales]))
        
        members_map = load_members_batch(member_ids)
        gammes_map = load_gammes_batch(gamme_ids)
        team_ids = list(set([m.team_id for m in members_map.values() if m and m.team_id]))
        teams_map = load_teams_batch(team_ids)
        
        for member in members_map.values():
            if member and member.team_id:
                member.team = teams_map.get(member.team_id)
        
        # Préparer les données pour PDF
        sales_data = []
        filters_info = {}
        
        if date_from:
            filters_info['date_from'] = date_from
        if date_to:
            filters_info['date_to'] = date_to
        if member_id and member_id in members_map:
            filters_info['member'] = members_map[member_id].full_name
        if team_id:
            team = PromotionTeam.query.get(team_id)
            if team:
                filters_info['team'] = team.name
        if transaction_type:
            filters_info['transaction_type'] = transaction_type
        
        for sale in sales:
            member = members_map.get(sale.member_id)
            gamme = gammes_map.get(sale.gamme_id)
            transaction_type_val = getattr(sale, 'transaction_type', 'enlevement') if has_transaction_type else 'enlevement'
            
            sales_data.append({
                'date': sale.sale_date.strftime('%d/%m/%Y') if sale.sale_date else 'N/A',
                'reference': sale.reference or '',
                'type': transaction_type_val,
                'member': member.full_name if member else 'N/A',
                'team': member.team.name if member and member.team else 'N/A',
                'gamme': gamme.name if gamme else 'N/A',
                'quantity': sale.quantity,
                'amount': sale.total_amount_gnf,
                'commission': sale.commission_gnf,
            })
        
        # Générer le PDF
        pdf_gen = PDFGenerator()
        pdf_buffer = pdf_gen.generate_sales_pdf(sales_data, filters_info, currency='GNF')
        
        filename = f'ventes_promotion_{datetime.now(UTC).strftime("%Y%m%d_%H%M%S")}.pdf'
        
        response = make_response(pdf_buffer.getvalue())
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"❌ Erreur lors de l'export PDF: {e}")
        flash(f'Erreur lors de l\'export PDF: {str(e)}', 'error')
        return redirect(url_for('promotion.sales_list'))

@promotion_bp.route('/sales/export/excel')
@login_required
def sales_export_excel():
    """Export Excel des ventes avec filtres appliqués"""
    if not has_permission(current_user, 'promotion.read'):
        flash("Vous n'avez pas la permission d'exporter les données.", "error")
        return redirect(url_for('promotion.sales_list'))
    
    from flask import make_response
    import pandas as pd
    from io import BytesIO
    
    # Récupérer les mêmes filtres que sales_list
    search = request.args.get('search', '').strip()
    team_id = request.args.get('team_id', type=int)
    member_id = request.args.get('member_id', type=int)
    gamme_id = request.args.get('gamme_id', type=int)
    transaction_type = request.args.get('transaction_type', '')
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    
    try:
        # Construire la requête (même logique que sales_list)
        query = PromotionSale.query
        
        # Vérifier si transaction_type existe
        has_transaction_type = has_transaction_type_column_cached()
        
        # Appliquer les filtres
        if member_id:
            query = query.filter_by(member_id=member_id)
        if gamme_id:
            query = query.filter_by(gamme_id=gamme_id)
        if date_from:
            try:
                date_from_obj = datetime.strptime(date_from, '%Y-%m-%d').date()
                query = query.filter(PromotionSale.sale_date >= date_from_obj)
            except:
                pass
        if date_to:
            try:
                date_to_obj = datetime.strptime(date_to, '%Y-%m-%d').date()
                query = query.filter(PromotionSale.sale_date <= date_to_obj)
            except:
                pass
        
        if has_transaction_type and transaction_type:
            query = query.filter(PromotionSale.transaction_type == transaction_type)
        
        # Recherche
        if search:
            try:
                member_ids_search = [row[0] for row in db.session.query(PromotionMember.id).filter(
                    PromotionMember.full_name.ilike(f'%{search}%')
                ).all()]
                
                if member_ids_search:
                    query = query.filter(
                        or_(
                            PromotionSale.member_id.in_(member_ids_search),
                            PromotionSale.reference.ilike(f'%{search}%')
                        )
                    )
                else:
                    query = query.filter(PromotionSale.reference.ilike(f'%{search}%'))
            except:
                query = query.filter(PromotionSale.reference.ilike(f'%{search}%'))
        
        # Récupérer toutes les ventes (sans limite pour l'export)
        load_columns = [
            PromotionSale.id, PromotionSale.member_id, PromotionSale.gamme_id,
            PromotionSale.quantity, PromotionSale.total_amount_gnf,
            PromotionSale.commission_gnf, PromotionSale.sale_date,
            PromotionSale.created_at, PromotionSale.reference
        ]
        
        if has_transaction_type:
            load_columns.append(PromotionSale.transaction_type)
        
        sales = query.options(load_only(*load_columns)).order_by(
            PromotionSale.created_at.desc()
        ).all()
        
        # Charger les relations en batch
        member_ids = list(set([s.member_id for s in sales]))
        gamme_ids = list(set([s.gamme_id for s in sales]))
        
        members_map = load_members_batch(member_ids)
        gammes_map = load_gammes_batch(gamme_ids)
        team_ids = list(set([m.team_id for m in members_map.values() if m and m.team_id]))
        teams_map = load_teams_batch(team_ids)
        
        for member in members_map.values():
            if member and member.team_id:
                member.team = teams_map.get(member.team_id)
        
        # Préparer les données pour Excel
        data = []
        for sale in sales:
            member = members_map.get(sale.member_id)
            gamme = gammes_map.get(sale.gamme_id)
            transaction_type_val = getattr(sale, 'transaction_type', 'enlevement') if has_transaction_type else 'enlevement'
            
            data.append({
                'Date': sale.sale_date.strftime('%d/%m/%Y') if sale.sale_date else '',
                'Référence': sale.reference or '',
                'Type': transaction_type_val.title(),
                'Membre': member.full_name if member else 'N/A',
                'Équipe': member.team.name if member and member.team else 'N/A',
                'Gamme': gamme.name if gamme else 'N/A',
                'Quantité': sale.quantity,
                'Prix Unitaire (GNF)': float(sale.total_amount_gnf / sale.quantity) if sale.quantity > 0 else 0,
                'Montant Total (GNF)': float(sale.total_amount_gnf),
                'Commission Unitaire (GNF)': float(sale.commission_gnf / sale.quantity) if sale.quantity > 0 else 0,
                'Commission Totale (GNF)': float(sale.commission_gnf),
            })
        
        # Créer le DataFrame
        df = pd.DataFrame(data)
        
        # Ajouter une ligne de totaux
        if len(df) > 0:
            total_row = pd.DataFrame([{
                'Date': 'TOTAL',
                'Référence': '',
                'Type': '',
                'Membre': '',
                'Équipe': '',
                'Gamme': '',
                'Quantité': df['Quantité'].sum(),
                'Prix Unitaire (GNF)': '',
                'Montant Total (GNF)': df['Montant Total (GNF)'].sum(),
                'Commission Unitaire (GNF)': '',
                'Commission Totale (GNF)': df['Commission Totale (GNF)'].sum(),
            }])
            df = pd.concat([df, total_row], ignore_index=True)
        
        # Créer le fichier Excel
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Ventes', index=False)
            
            # Formater les colonnes
            worksheet = writer.sheets['Ventes']
            for idx, col in enumerate(df.columns, 1):
                max_length = max(
                    df[col].astype(str).map(len).max(),
                    len(str(col))
                )
                worksheet.column_dimensions[chr(64 + idx)].width = min(max_length + 2, 30)
        
        output.seek(0)
        filename = f'ventes_promotion_{datetime.now(UTC).strftime("%Y%m%d_%H%M%S")}.xlsx'
        
        response = make_response(output.getvalue())
        response.headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"❌ Erreur lors de l'export Excel: {e}")
        flash(f'Erreur lors de l\'export Excel: {str(e)}', 'error')
        return redirect(url_for('promotion.sales_list'))

@promotion_bp.route('/sales/new', methods=['GET', 'POST'])
@login_required
def sale_new():
    """Créer une nouvelle vente"""
    if not has_permission(current_user, 'promotion.write'):
        flash("Vous n'avez pas la permission de créer une vente.", "error")
        return redirect(url_for('promotion.sales_list'))
    
    if request.method == 'POST':
        try:
            member = get_member_safe(int(request.form.get('member_id', 0)))
            if not member:
                flash("Membre introuvable.", "error")
                return redirect(url_for('promotion.sale_new'))
            
            transaction_type = request.form.get('transaction_type', 'enlevement')
            sale_date_str = request.form.get('sale_date', '')
            sale_date = datetime.strptime(sale_date_str, '%Y-%m-%d').date() if sale_date_str else date.today()
            
            # Vérifier si les colonnes existent
            check_ref_sql = """SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS 
                              WHERE TABLE_SCHEMA = DATABASE() 
                              AND TABLE_NAME = 'promotion_sales' 
                              AND COLUMN_NAME = 'reference'"""
            has_reference = db.session.execute(text(check_ref_sql)).scalar() > 0
            
            check_type_sql = """SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS 
                               WHERE TABLE_SCHEMA = DATABASE() 
                               AND TABLE_NAME = 'promotion_sales' 
                               AND COLUMN_NAME = 'transaction_type'"""
            has_transaction_type = db.session.execute(text(check_type_sql)).scalar() > 0
            
            # Récupérer toutes les ventes (plusieurs gammes/pièces)
            sales_data = []
            member_stock = get_member_stock(member.id)
            i = 0
            
            while True:
                gamme_id_str = request.form.get(f'gamme_id_{i}')
                quantity_str = request.form.get(f'quantity_{i}')
                selling_price_str = request.form.get(f'selling_price_gnf_{i}')
                commission_per_unit_str = request.form.get(f'commission_per_unit_gnf_{i}')
                
                if not gamme_id_str or not quantity_str:
                    break
                
                try:
                    gamme_id = int(gamme_id_str)
                    quantity = int(quantity_str)
                    selling_price = Decimal(selling_price_str) if selling_price_str else Decimal("0")
                    commission_per_unit = Decimal(commission_per_unit_str) if commission_per_unit_str else Decimal("0")
                    
                    if quantity <= 0:
                        i += 1
                        continue
                    
                    gamme = PromotionGamme.query.get(gamme_id)
                    if not gamme:
                        i += 1
                        continue
                    
                    # Vérifier le stock avant l'opération
                    if transaction_type == 'enlevement':
                        # Pour un enlèvement, vérifier que l'équipe a assez de stock
                        if member.team_id:
                            team_stock = get_team_stock(member.team_id)
                            current_team_stock = team_stock.get(gamme_id, 0)
                            if current_team_stock < quantity:
                                flash(f"⚠️ Stock insuffisant dans l'équipe! Stock disponible: {current_team_stock} unité(s) de {gamme.name}. Besoin: {quantity} unité(s). Veuillez d'abord approvisionner l'équipe.", "error")
                                return redirect(url_for('promotion.sale_new'))
                    elif transaction_type == 'retour':
                        # Pour un retour, vérifier que le membre a assez de stock
                        current_member_stock = member_stock.get(gamme_id, 0)
                        if current_member_stock < quantity:
                            flash(f"⚠️ Stock insuffisant pour le retour! L'agent {member.full_name} n'a que {current_member_stock} unité(s) de {gamme.name} en stock. Impossible de retourner {quantity} unité(s).", "error")
                            return redirect(url_for('promotion.sale_new'))
                    
                    total_amount = selling_price * quantity
                    commission = commission_per_unit * quantity
                    
                    sales_data.append({
                        'gamme_id': gamme_id,
                        'gamme': gamme,
                        'quantity': quantity,
                        'selling_price': selling_price,
                        'total_amount': total_amount,
                        'commission_per_unit': commission_per_unit,
                        'commission': commission
                    })
                except (ValueError, TypeError) as e:
                    print(f"DEBUG sale_new: Erreur parsing ligne {i}: {e}")
                    pass
                
                i += 1
            
            if not sales_data:
                flash("Veuillez ajouter au moins une gamme/pièce avec une quantité valide.", "error")
                return redirect(url_for('promotion.sale_new'))
            
            # Générer une référence pour chaque vente
            reference = generate_sale_reference(transaction_type)
            
            # Vérifier si les colonnes existent
            check_ref_sql = """SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS 
                              WHERE TABLE_SCHEMA = DATABASE() 
                              AND TABLE_NAME = 'promotion_sales' 
                              AND COLUMN_NAME = 'reference'"""
            has_reference = db.session.execute(text(check_ref_sql)).scalar() > 0
            
            check_type_sql = """SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS 
                               WHERE TABLE_SCHEMA = DATABASE() 
                               AND TABLE_NAME = 'promotion_sales' 
                               AND COLUMN_NAME = 'transaction_type'"""
            has_transaction_type = db.session.execute(text(check_type_sql)).scalar() > 0
            
            # Traiter toutes les ventes
            saved_count = 0
            errors = []
            
            try:
                for sale_item in sales_data:
                    try:
                        # Générer une référence unique pour chaque vente
                        sale_reference = generate_sale_reference(transaction_type)
                        
                        sale = PromotionSale(
                            reference=sale_reference if has_reference else None,
                            member_id=member.id,
                            gamme_id=sale_item['gamme_id'],
                            transaction_type=transaction_type if has_transaction_type else 'enlevement',
                            quantity=sale_item['quantity'],
                            selling_price_gnf=sale_item['selling_price'],
                            total_amount_gnf=sale_item['total_amount'],
                            commission_per_unit_gnf=sale_item['commission_per_unit'],
                            commission_gnf=sale_item['commission'],
                            sale_date=sale_date,
                            recorded_by_id=current_user.id
                        )
                        db.session.add(sale)
                        db.session.flush()
                        
                        # Mettre à jour le stock avec référence à la vente
                        update_member_stock(member.id, sale_item['gamme_id'], sale_item['quantity'], transaction_type,
                                           sale_id=sale.id, movement_date=sale_date)
                        
                        saved_count += 1
                    except Exception as e:
                        print(f"DEBUG sale_new: Erreur ORM pour gamme {sale_item['gamme_id']}: {e}")
                        db.session.rollback()
                        
                        # Fallback: SQL direct
                        try:
                            sale_reference = generate_sale_reference(transaction_type)
                            
                            if has_reference and has_transaction_type:
                                sql = """INSERT INTO promotion_sales 
                                         (reference, member_id, gamme_id, transaction_type, quantity, 
                                          selling_price_gnf, total_amount_gnf, commission_per_unit_gnf, 
                                          commission_gnf, sale_date, recorded_by_id, created_at) 
                                         VALUES (:reference, :member_id, :gamme_id, :transaction_type, :quantity,
                                                 :selling_price, :total_amount, :commission_per_unit,
                                                 :commission, :sale_date, :recorded_by, :created_at)"""
                                params = {
                                    'reference': sale_reference,
                                    'member_id': member.id,
                                    'gamme_id': sale_item['gamme_id'],
                                    'transaction_type': transaction_type,
                                    'quantity': sale_item['quantity'],
                                    'selling_price': sale_item['selling_price'],
                                    'total_amount': sale_item['total_amount'],
                                    'commission_per_unit': sale_item['commission_per_unit'],
                                    'commission': sale_item['commission'],
                                    'sale_date': sale_date,
                                    'recorded_by': current_user.id,
                                    'created_at': datetime.now(UTC)
                                }
                            elif has_reference:
                                sql = """INSERT INTO promotion_sales 
                                         (reference, member_id, gamme_id, quantity, 
                                          selling_price_gnf, total_amount_gnf, commission_per_unit_gnf, 
                                          commission_gnf, sale_date, recorded_by_id, created_at) 
                                         VALUES (:reference, :member_id, :gamme_id, :quantity,
                                                 :selling_price, :total_amount, :commission_per_unit,
                                                 :commission, :sale_date, :recorded_by, :created_at)"""
                                params = {
                                    'reference': sale_reference,
                                    'member_id': member.id,
                                    'gamme_id': sale_item['gamme_id'],
                                    'quantity': sale_item['quantity'],
                                    'selling_price': sale_item['selling_price'],
                                    'total_amount': sale_item['total_amount'],
                                    'commission_per_unit': sale_item['commission_per_unit'],
                                    'commission': sale_item['commission'],
                                    'sale_date': sale_date,
                                    'recorded_by': current_user.id,
                                    'created_at': datetime.now(UTC)
                                }
                            else:
                                sql = """INSERT INTO promotion_sales 
                                         (member_id, gamme_id, quantity, 
                                          selling_price_gnf, total_amount_gnf, commission_per_unit_gnf, 
                                          commission_gnf, sale_date, recorded_by_id, created_at) 
                                         VALUES (:member_id, :gamme_id, :quantity,
                                                 :selling_price, :total_amount, :commission_per_unit,
                                                 :commission, :sale_date, :recorded_by, :created_at)"""
                                params = {
                                    'member_id': member.id,
                                    'gamme_id': sale_item['gamme_id'],
                                    'quantity': sale_item['quantity'],
                                    'selling_price': sale_item['selling_price'],
                                    'total_amount': sale_item['total_amount'],
                                    'commission_per_unit': sale_item['commission_per_unit'],
                                    'commission': sale_item['commission'],
                                    'sale_date': sale_date,
                                    'recorded_by': current_user.id,
                                    'created_at': datetime.now(UTC)
                                }
                            
                            # Utiliser RETURNING pour PostgreSQL, lastrowid pour MySQL
                            from config import SQLALCHEMY_DATABASE_URI
                            is_postgresql = SQLALCHEMY_DATABASE_URI.startswith('postgresql')
                            
                            if is_postgresql:
                                # Ajouter RETURNING id à la requête SQL
                                sql = sql.rstrip(';') + " RETURNING id"
                                result = db.session.execute(text(sql), params)
                                db.session.flush()
                                sale_id = result.scalar()
                            else:
                                result = db.session.execute(text(sql), params)
                                db.session.flush()
                                sale_id = result.lastrowid if hasattr(result, 'lastrowid') else None
                            
                            # Mettre à jour le stock avec référence à la vente
                            update_member_stock(member.id, sale_item['gamme_id'], sale_item['quantity'], transaction_type,
                                               sale_id=sale_id, movement_date=sale_date)
                            
                            saved_count += 1
                        except Exception as sql_error:
                            errors.append(f"Erreur pour {sale_item['gamme'].name}: {str(sql_error)}")
                            print(f"DEBUG sale_new: Erreur SQL pour gamme {sale_item['gamme_id']}: {sql_error}")
                
                if saved_count > 0:
                    db.session.commit()
                    flash(f"{saved_count} vente(s) enregistrée(s) avec succès!", "success")
                    if errors:
                        for error in errors[:3]:
                            flash(error, "warning")
                    return redirect(url_for('promotion.sales_list'))
                else:
                    flash("Aucune vente n'a pu être enregistrée.", "error")
                    if errors:
                        for error in errors[:5]:
                            flash(error, "error")
            except Exception as e:
                db.session.rollback()
                print(f"DEBUG sale_new: Erreur générale: {e}")
                flash(f"Erreur lors de l'enregistrement: {str(e)}", "error")
        except Exception as e:
            db.session.rollback()
            flash(f"Erreur lors de l'enregistrement: {str(e)}", "error")
    
    members_query = PromotionMember.query.options(
        load_only(PromotionMember.id, PromotionMember.full_name, PromotionMember.team_id)
    ).filter_by(is_active=True).all()
    
    # Charger les stocks pour chaque membre et leurs équipes
    members_with_stock = []
    for member in members_query:
        # Charger l'équipe du membre de manière sécurisée
        if member.team_id:
            try:
                member.team = PromotionTeam.query.options(
                    load_only(PromotionTeam.id, PromotionTeam.name)
                ).get(member.team_id)
            except Exception:
                member.team = None
        else:
            member.team = None
        
        stock = get_member_stock(member.id)
        members_with_stock.append({
            'member': member,
            'stock': stock,
            'total_stock': sum(stock.values())
        })
    
    gammes = PromotionGamme.query.filter_by(is_active=True).all()
    today_date = date.today().isoformat()
    return render_template('promotion/sale_form.html', sale=None, members=members_with_stock, gammes=gammes, today_date=today_date)

@promotion_bp.route('/sales/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def sale_edit(id):
    """Modifier une vente"""
    if not has_permission(current_user, 'promotion.write'):
        flash("Vous n'avez pas la permission de modifier une vente.", "error")
        return redirect(url_for('promotion.sales_list'))
    
    try:
        sale = PromotionSale.query.options(
            load_only(PromotionSale.id, PromotionSale.member_id, PromotionSale.gamme_id,
                     PromotionSale.quantity, PromotionSale.selling_price_gnf,
                     PromotionSale.total_amount_gnf, PromotionSale.commission_per_unit_gnf,
                     PromotionSale.commission_gnf, PromotionSale.sale_date, PromotionSale.created_at)
        ).get_or_404(id)
        
        # Charger transaction_type si la colonne existe
        has_transaction_type = has_transaction_type_column_cached()
        
        if has_transaction_type:
            type_sql = "SELECT transaction_type FROM promotion_sales WHERE id = :sale_id"
            type_result = db.session.execute(text(type_sql), {'sale_id': id})
            type_row = type_result.fetchone()
            sale.__dict__['transaction_type'] = type_row[0] if type_row and type_row[0] else 'enlevement'
        else:
            sale.__dict__['transaction_type'] = 'enlevement'
        
        sale.member = get_member_safe(sale.member_id)
        sale.gamme = PromotionGamme.query.get(sale.gamme_id)
    except Exception as e:
        flash(f"Erreur lors du chargement: {str(e)}", "error")
        return redirect(url_for('promotion.sales_list'))
    
    if request.method == 'POST':
        try:
            member = get_member_safe(int(request.form.get('member_id', 0)))
            gamme = PromotionGamme.query.get(int(request.form.get('gamme_id', 0)))
            quantity = int(request.form.get('quantity', 1))
            transaction_type = request.form.get('transaction_type', 'enlevement')
            sale_date_str = request.form.get('sale_date', '')
            sale_date = datetime.strptime(sale_date_str, '%Y-%m-%d').date() if sale_date_str else date.today()
            
            old_quantity = sale.quantity
            old_transaction_type = sale.__dict__.get('transaction_type', 'enlevement')
            
            total_amount = gamme.selling_price_gnf * quantity
            commission = gamme.commission_per_unit_gnf * quantity
            
            sale.member_id = member.id
            sale.gamme_id = gamme.id
            sale.quantity = quantity
            sale.selling_price_gnf = gamme.selling_price_gnf
            sale.total_amount_gnf = total_amount
            sale.commission_per_unit_gnf = gamme.commission_per_unit_gnf
            sale.commission_gnf = commission
            sale.sale_date = sale_date
            
            if has_transaction_type:
                sale.__dict__['transaction_type'] = transaction_type
            
            # Ajuster le stock
            if old_transaction_type == 'enlevement':
                update_member_stock(member.id, gamme.id, -old_quantity, 'retour',
                                   sale_id=sale.id if sale else None)
            elif old_transaction_type == 'retour':
                update_member_stock(member.id, gamme.id, old_quantity, 'enlevement',
                                   sale_id=sale.id if sale else None)
            
            if transaction_type == 'enlevement':
                update_member_stock(member.id, gamme.id, quantity, 'enlevement',
                                   sale_id=sale.id if sale else None, movement_date=sale_date)
            elif transaction_type == 'retour':
                update_member_stock(member.id, gamme.id, quantity, 'retour',
                                   sale_id=sale.id if sale else None, movement_date=sale_date)
            
            db.session.commit()
            flash("Vente modifiée avec succès!", "success")
            return redirect(url_for('promotion.sales_list'))
        except Exception as e:
            db.session.rollback()
            flash(f"Erreur lors de la modification: {str(e)}", "error")
    
    members_query = PromotionMember.query.options(
        load_only(PromotionMember.id, PromotionMember.full_name, PromotionMember.team_id)
    ).filter_by(is_active=True).all()
    
    # Charger les équipes pour chaque membre
    members_with_stock = []
    for member in members_query:
        # Charger l'équipe du membre de manière sécurisée
        if member.team_id:
            try:
                member.team = PromotionTeam.query.options(
                    load_only(PromotionTeam.id, PromotionTeam.name)
                ).get(member.team_id)
            except Exception:
                member.team = None
        else:
            member.team = None
        
        stock = get_member_stock(member.id)
        members_with_stock.append({
            'member': member,
            'stock': stock,
            'total_stock': sum(stock.values())
        })
    
    gammes = PromotionGamme.query.filter_by(is_active=True).all()
    today_date = date.today().isoformat()
    return render_template('promotion/sale_form.html', sale=sale, members=members_with_stock, gammes=gammes, today_date=today_date)

# =========================================================
# SAISIE RAPIDE
# =========================================================

@promotion_bp.route('/sales/quick-entry')
@login_required
def quick_entry():
    """Saisie rapide de ventes pour plusieurs agents"""
    if not has_permission(current_user, 'promotion.write'):
        flash("Vous n'avez pas la permission d'accéder à cette page.", "error")
        return redirect(url_for('promotion.sales_list'))
    
    members_query = PromotionMember.query.options(
        load_only(PromotionMember.id, PromotionMember.full_name, PromotionMember.team_id)
    ).filter_by(is_active=True).all()
    
    # Charger les stocks pour chaque membre et leurs équipes
    members_with_stock = []
    for member in members_query:
        # Charger l'équipe du membre de manière sécurisée
        if member.team_id:
            try:
                member.team = PromotionTeam.query.options(
                    load_only(PromotionTeam.id, PromotionTeam.name)
                ).get(member.team_id)
            except Exception:
                member.team = None
        else:
            member.team = None
        
        stock = get_member_stock(member.id)
        members_with_stock.append({
            'member': member,
            'stock': stock,
            'total_stock': sum(stock.values())
        })
    
    gammes = PromotionGamme.query.filter_by(is_active=True).all()
    teams = PromotionTeam.query.filter_by(is_active=True).all()
    
    return render_template('promotion/quick_entry.html', 
                         members=members_with_stock, gammes=gammes, teams=teams)

@promotion_bp.route('/sales/quick-entry/save', methods=['POST'])
@login_required
def quick_sales_save():
    """Sauvegarder les ventes en saisie rapide"""
    if not has_permission(current_user, 'promotion.write'):
        flash("Vous n'avez pas la permission d'enregistrer des ventes.", "error")
        return redirect(url_for('promotion.quick_entry'))
    
    try:
        saved_count = 0
        errors = []
        
        # Parcourir les entrées du formulaire
        i = 1
        while True:
            member_id = request.form.get(f'member_id_{i}')
            if not member_id:
                break
            
            try:
                gamme_id = int(request.form.get(f'gamme_id_{i}', 0))
                quantity = int(request.form.get(f'quantity_{i}', 0))
                sale_date_str = request.form.get(f'sale_date_{i}', '')
                transaction_type = request.form.get(f'transaction_type_{i}', 'enlevement')
                
                if quantity <= 0:
                    i += 1
                    continue
                
                member = get_member_safe(int(member_id))
                if not member:
                    errors.append(f"Entrée {i}: Membre introuvable")
                    i += 1
                    continue
                
                gamme = PromotionGamme.query.get(gamme_id)
                if not gamme:
                    errors.append(f"Entrée {i}: Gamme introuvable")
                    i += 1
                    continue
                
                if sale_date_str:
                    sale_date = datetime.strptime(sale_date_str, '%Y-%m-%d').date()
                else:
                    sale_date = date.today()
                
                # Vérifier le stock avant l'opération
                if transaction_type == 'enlevement':
                    # Pour un enlèvement, vérifier que l'équipe a assez de stock
                    if member.team_id:
                        team_stock = get_team_stock(member.team_id)
                        current_team_stock = team_stock.get(gamme_id, 0)
                        if current_team_stock < quantity:
                            errors.append(f"⚠️ Entrée {i}: Stock insuffisant dans l'équipe pour {member.full_name}! Stock disponible: {current_team_stock}, demandé: {quantity} de {gamme.name}. Veuillez d'abord approvisionner l'équipe.")
                            i += 1
                            continue
                elif transaction_type == 'retour':
                    # Pour un retour, vérifier que le membre a assez de stock
                    member_stock = get_member_stock(int(member_id))
                    current_member_stock = member_stock.get(gamme_id, 0)
                    if current_member_stock < quantity:
                        errors.append(f"⚠️ Entrée {i}: Stock insuffisant pour le retour de {member.full_name}! Stock disponible: {current_member_stock}, retour demandé: {quantity} de {gamme.name}")
                        i += 1
                        continue
                
                selling_price_per_unit = gamme.selling_price_gnf
                commission_per_unit = gamme.commission_per_unit_gnf
                total_amount = selling_price_per_unit * quantity
                total_commission = commission_per_unit * quantity
                
                reference = generate_sale_reference(transaction_type)
                
                sale = PromotionSale(
                    reference=reference,
                    member_id=int(member_id),
                    gamme_id=gamme_id,
                    transaction_type=transaction_type,
                    quantity=quantity,
                    selling_price_gnf=selling_price_per_unit,
                    total_amount_gnf=total_amount,
                    commission_per_unit_gnf=commission_per_unit,
                    commission_gnf=total_commission,
                    sale_date=sale_date,
                    recorded_by_id=current_user.id
                )
                
                db.session.add(sale)
                db.session.flush()  # Pour obtenir l'ID de la vente
                
                # Récupérer l'ID de la vente créée
                sale_id = sale.id if hasattr(sale, 'id') and sale.id else None
                
                if transaction_type == 'enlevement':
                    update_member_stock(int(member_id), gamme_id, quantity, 'enlevement',
                                       sale_id=sale_id, movement_date=sale_date)
                elif transaction_type == 'retour':
                    update_member_stock(int(member_id), gamme_id, quantity, 'retour',
                                       sale_id=sale_id, movement_date=sale_date)
                
                saved_count += 1
                
            except Exception as e:
                errors.append(f"Entrée {i}: {str(e)}")
            
            i += 1
        
        if saved_count > 0:
            db.session.commit()
            flash(f"{saved_count} vente(s) enregistrée(s) avec succès!", "success")
        else:
            flash("Aucune vente n'a pu être enregistrée.", "error")
            if errors:
                for error in errors[:5]:
                    flash(error, "error")
        
        return redirect(url_for('promotion.sales_list'))
        
    except Exception as e:
        db.session.rollback()
        flash(f"Erreur lors de l'enregistrement: {str(e)}", "error")
        return redirect(url_for('promotion.quick_entry'))

# =========================================================
# GESTION DES RETOURS
# =========================================================

@promotion_bp.route('/returns')
@login_required
def returns_list():
    """Liste des retours"""
    if not has_permission(current_user, 'promotion.read'):
        flash("Vous n'avez pas la permission d'accéder à cette page.", "error")
        return redirect(url_for('index'))
    
    # Récupérer les paramètres de filtrage
    search = request.args.get('search', '').strip()
    status_filter = request.args.get('status', '').strip()
    member_id = request.args.get('member_id', '').strip()
    
    # Construire la requête de manière sécurisée pour éviter les colonnes manquantes
    try:
        query = PromotionReturn.query.options(
            joinedload(PromotionReturn.member).options(
                load_only(PromotionMember.id, PromotionMember.full_name, PromotionMember.phone, 
                         PromotionMember.team_id, PromotionMember.is_active)
            ),
            joinedload(PromotionReturn.gamme).options(
                load_only(PromotionGamme.id, PromotionGamme.name)
            )
        )
    except Exception as e:
        print(f"DEBUG returns_list: Erreur lors de la construction de la requête: {e}")
        # Fallback: requête simple sans joinedload
        query = PromotionReturn.query
    
    # Appliquer les filtres
    if search:
        query = query.join(PromotionMember).filter(
            or_(
                PromotionMember.full_name.ilike(f'%{search}%'),
                PromotionReturn.reason.ilike(f'%{search}%')
            )
        )
    
    if status_filter:
        query = query.filter(PromotionReturn.status == status_filter)
    
    if member_id:
        try:
            query = query.filter(PromotionReturn.member_id == int(member_id))
        except ValueError:
            pass
    
    returns = query.order_by(PromotionReturn.created_at.desc()).limit(100).all()
    
    # Charger les équipes manuellement pour chaque retour pour éviter les colonnes manquantes
    for return_obj in returns:
        if return_obj.member and return_obj.member.team_id:
            try:
                return_obj.member.team = PromotionTeam.query.options(
                    load_only(PromotionTeam.id, PromotionTeam.name)
                ).get(return_obj.member.team_id)
            except Exception:
                return_obj.member.team = None
        else:
            return_obj.member.team = None
    
    # Calculer les statistiques
    try:
        total_returns = PromotionReturn.query.count()
        pending_returns = PromotionReturn.query.filter_by(status='pending').count()
        approved_returns = PromotionReturn.query.filter_by(status='approved').count()
        rejected_returns = PromotionReturn.query.filter_by(status='rejected').count()
    except Exception as e:
        print(f"Erreur calcul stats retours: {e}")
        total_returns = len(returns)
        pending_returns = 0
        approved_returns = 0
        rejected_returns = 0
    
    stats = {
        'total': total_returns,
        'pending': pending_returns,
        'approved': approved_returns,
        'rejected': rejected_returns
    }
    
    # Récupérer la liste des membres actifs pour le filtre
    try:
        members = PromotionMember.query.filter_by(is_active=True).options(
            load_only(PromotionMember.id, PromotionMember.full_name, PromotionMember.phone)
        ).order_by(PromotionMember.full_name).all()
    except Exception:
        members = []
    
    return render_template('promotion/returns_list.html', 
                         returns=returns, 
                         stats=stats,
                         search=search,
                         status_filter=status_filter,
                         member_id=member_id,
                         members=members)

@promotion_bp.route('/returns/new', methods=['GET', 'POST'])
@login_required
def return_new():
    """Créer un nouveau retour"""
    if not has_permission(current_user, 'promotion.write'):
        flash("Vous n'avez pas la permission de créer un retour.", "error")
        return redirect(url_for('promotion.returns_list'))
    
    if request.method == 'POST':
        try:
            member_id = int(request.form.get('member_id', 0))
            member = get_member_safe(member_id)
            if not member:
                flash("Membre introuvable.", "error")
                return redirect(url_for('promotion.return_new'))
            
            return_date_str = request.form.get('return_date', '')
            return_date = datetime.strptime(return_date_str, '%Y-%m-%d').date() if return_date_str else date.today()
            reason = request.form.get('reason', '')
            notes = request.form.get('notes', '')
            
            # Récupérer tous les retours (plusieurs gammes/pièces)
            returns_data = []
            member_stock = get_member_stock(member_id)
            i = 0
            
            while True:
                gamme_id_str = request.form.get(f'gamme_id_{i}')
                quantity_str = request.form.get(f'quantity_{i}')
                
                if not gamme_id_str or not quantity_str:
                    break
                
                try:
                    gamme_id = int(gamme_id_str)
                    quantity = int(quantity_str)
                    
                    if quantity <= 0:
                        i += 1
                        continue
                    
                    gamme = PromotionGamme.query.get(gamme_id)
                    if not gamme:
                        i += 1
                        continue
                    
                    # Vérifier le stock de l'agent avant le retour
                    current_stock = member_stock.get(gamme_id, 0)
                    if current_stock < quantity:
                        flash(f"⚠️ Stock insuffisant pour le retour! L'agent {member.full_name} n'a que {current_stock} unité(s) de {gamme.name} en stock. Impossible de retourner {quantity} unité(s). Opération annulée.", "error")
                        return redirect(url_for('promotion.return_new'))
                    
                    returns_data.append({
                        'gamme_id': gamme_id,
                        'quantity': quantity
                    })
                except (ValueError, TypeError):
                    pass
                
                i += 1
            
            if not returns_data:
                flash("Veuillez ajouter au moins une gamme/pièce avec une quantité valide.", "error")
                return redirect(url_for('promotion.return_new'))
            
            # Créer tous les retours
            saved_count = 0
            for return_item in returns_data:
                return_obj = PromotionReturn(
                    member_id=member_id,
                    gamme_id=return_item['gamme_id'],
                    quantity=return_item['quantity'],
                    return_date=return_date,
                    reason=reason,
                    notes=notes,
                    status='pending',
                    recorded_by_id=current_user.id
                )
                db.session.add(return_obj)
                saved_count += 1
            
            db.session.commit()
            flash(f"{saved_count} retour(s) créé(s) avec succès!", "success")
            return redirect(url_for('promotion.returns_list'))
        except Exception as e:
            db.session.rollback()
            flash(f"Erreur: {str(e)}", "error")
    
    # Récupérer le member_id depuis les paramètres de requête si disponible
    member_id_param = request.args.get('member_id', '').strip()
    member_stocks = {}
    
    if member_id_param:
        try:
            member_stocks = get_member_stock(int(member_id_param))
        except (ValueError, TypeError):
            pass
    
    members_query = PromotionMember.query.options(
        load_only(PromotionMember.id, PromotionMember.full_name, PromotionMember.team_id)
    ).filter_by(is_active=True).all()
    
    # Charger les équipes pour chaque membre
    members = []
    for member in members_query:
        # Charger l'équipe du membre de manière sécurisée
        if member.team_id:
            try:
                member.team = PromotionTeam.query.options(
                    load_only(PromotionTeam.id, PromotionTeam.name)
                ).get(member.team_id)
            except Exception:
                member.team = None
        else:
            member.team = None
        members.append(member)
    
    gammes = PromotionGamme.query.filter_by(is_active=True).all()
    today = date.today()
    return render_template('promotion/return_form.html', return_obj=None, members=members, gammes=gammes, 
                         member_stocks=member_stocks, member_id=member_id_param, today=today)

@promotion_bp.route('/returns/<int:id>/approve', methods=['POST'])
@login_required
def return_approve(id):
    """Approuver un retour"""
    if not has_permission(current_user, 'promotion.write'):
        flash("Vous n'avez pas la permission d'approuver un retour.", "error")
        return redirect(url_for('promotion.returns_list'))
    
    return_obj = PromotionReturn.query.get_or_404(id)
    
    # Vérifier le stock avant d'approuver le retour
    member_stock = get_member_stock(return_obj.member_id)
    current_stock = member_stock.get(return_obj.gamme_id, 0)
    
    if current_stock < return_obj.quantity:
        member = get_member_safe(return_obj.member_id)
        gamme = PromotionGamme.query.get(return_obj.gamme_id)
        flash(f"Stock insuffisant! L'agent {member.full_name if member else 'N/A'} n'a que {current_stock} unité(s) de {gamme.name if gamme else 'N/A'} en stock. Impossible d'approuver un retour de {return_obj.quantity} unité(s).", "error")
        return redirect(url_for('promotion.returns_list'))
    
    # Récupérer le membre pour obtenir son équipe
    member = get_member_safe(return_obj.member_id)
    if not member or not member.team_id:
        flash("Le membre doit appartenir à une équipe pour que le retour soit traité.", "error")
        return redirect(url_for('promotion.returns_list'))
    
    gamme = PromotionGamme.query.get(return_obj.gamme_id)
    if not gamme:
        flash("Gamme introuvable.", "error")
        return redirect(url_for('promotion.returns_list'))
    
    return_obj.status = 'approved'
    return_obj.approved_by_id = current_user.id
    return_obj.approved_at = datetime.now(UTC)
    
    # Diminuer le stock du membre
    update_member_stock(return_obj.member_id, return_obj.gamme_id, return_obj.quantity, 'retour',
                       return_id=return_obj.id, movement_date=return_obj.return_date)
    
    # Augmenter le stock de l'équipe
    update_team_stock(member.team_id, return_obj.gamme_id, return_obj.quantity, 'add',
                     movement_type='retour', movement_date=return_obj.return_date)
    
    # Créer une entrée dans PromotionSale pour comptabiliser le retour
    try:
        has_transaction_type = has_transaction_type_column_cached()
        
        if has_transaction_type:
            selling_price = gamme.selling_price_gnf
            commission_per_unit = gamme.commission_per_unit_gnf
            total_amount = selling_price * return_obj.quantity
            commission = commission_per_unit * return_obj.quantity
            reference = generate_sale_reference('retour')
            
            sale = PromotionSale(
                reference=reference,
                member_id=return_obj.member_id,
                gamme_id=return_obj.gamme_id,
                transaction_type='retour',
                quantity=return_obj.quantity,
                selling_price_gnf=selling_price,
                total_amount_gnf=total_amount,
                commission_per_unit_gnf=commission_per_unit,
                commission_gnf=commission,
                sale_date=return_obj.return_date,
                recorded_by_id=current_user.id
            )
            db.session.add(sale)
    except Exception as e:
        print(f"Erreur lors de la création de la vente pour le retour: {e}")
        # On continue quand même
    
    db.session.commit()
    flash("Retour approuvé avec succès! Le stock du membre a été diminué et le stock de l'équipe a été augmenté.", "success")
    return redirect(url_for('promotion.returns_list'))

@promotion_bp.route('/returns/<int:id>/reject', methods=['POST'])
@login_required
def return_reject(id):
    """Rejeter un retour"""
    if not has_permission(current_user, 'promotion.write'):
        flash("Vous n'avez pas la permission de rejeter un retour.", "error")
        return redirect(url_for('promotion.returns_list'))
    
    return_obj = PromotionReturn.query.get_or_404(id)
    return_obj.status = 'rejected'
    db.session.commit()
    flash("Retour rejeté.", "info")
    return redirect(url_for('promotion.returns_list'))

# =========================================================
# CARTOGRAPHIE - SUIVI DES DÉPLACEMENTS
# =========================================================

@promotion_bp.route('/map')
@login_required
def map_view():
    """Vue cartographique des équipes et déplacements"""
    if not has_permission(current_user, 'promotion.read'):
        flash("Vous n'avez pas la permission d'accéder à cette page.", "error")
        return redirect(url_for('promotion.dashboard'))
    
    try:
        teams = PromotionTeam.query.filter_by(is_active=True).options(
            joinedload(PromotionTeam.members).load_only(
                PromotionMember.id, PromotionMember.full_name, PromotionMember.team_id, 
                PromotionMember.is_active
            )
        ).all()
    except Exception:
        try:
            teams = PromotionTeam.query.filter_by(is_active=True).all()
            for team in teams:
                try:
                    team.members = PromotionMember.query.options(
                        load_only(PromotionMember.id, PromotionMember.full_name, PromotionMember.team_id, PromotionMember.is_active)
                    ).filter_by(team_id=team.id, is_active=True).all()
                except Exception:
                    team.members = []
        except Exception:
            teams = []
    
    # Préparer les données pour le JavaScript (format JSON-serializable)
    teams_data = []
    for team in teams:
        team_dict = {
            'id': team.id,
            'name': team.name or '',
            'region': team.region or '',
            'members': []
        }
        try:
            for member in team.members:
                team_dict['members'].append({
                    'id': member.id,
                    'full_name': member.full_name or '',
                    'team_id': member.team_id
                })
        except Exception:
            pass
        teams_data.append(team_dict)
    
    return render_template('promotion/map.html', teams=teams, teams_data=teams_data)

# =========================================================
# CLÔTURE QUOTIDIENNE
# =========================================================

@promotion_bp.route('/daily-closure', methods=['GET', 'POST'])
@login_required
def daily_closure():
    """Clôture quotidienne des opérations de promotion"""
    if not has_permission(current_user, 'promotion.write'):
        flash("Vous n'avez pas la permission de clôturer une journée.", "error")
        return redirect(url_for('promotion.dashboard'))
    
    today = date.today()
    
    # Vérifier si la journée est déjà clôturée
    existing_closure = PromotionDailyClosure.query.filter_by(closure_date=today).first()
    is_closed = existing_closure is not None
    
    if request.method == 'POST' and not is_closed:
        try:
            notes = request.form.get('notes', '')
            
            closure = PromotionDailyClosure(
                closure_date=today,
                closed_by_id=current_user.id,
                notes=notes
            )
            db.session.add(closure)
            db.session.commit()
            flash(f"Journée du {today.strftime('%d/%m/%Y')} clôturée avec succès!", "success")
            return redirect(url_for('promotion.daily_closure'))
        except Exception as e:
            db.session.rollback()
            flash(f"Erreur lors de la clôture: {str(e)}", "error")
    
    # Récupérer les statistiques de la journée
    try:
        has_transaction_type = has_transaction_type_column_cached()
        
        if has_transaction_type:
            # Enlèvements
            enlevements = db.session.query(
                PromotionSale.member_id,
                PromotionSale.gamme_id,
                func.sum(PromotionSale.quantity).label('total_quantity')
            ).filter(
                PromotionSale.sale_date == today,
                PromotionSale.transaction_type == 'enlevement'
            ).group_by(PromotionSale.member_id, PromotionSale.gamme_id).all()
            
            # Retours
            retours = db.session.query(
                PromotionSale.member_id,
                PromotionSale.gamme_id,
                func.sum(PromotionSale.quantity).label('total_quantity')
            ).filter(
                PromotionSale.sale_date == today,
                PromotionSale.transaction_type == 'retour'
            ).group_by(PromotionSale.member_id, PromotionSale.gamme_id).all()
        else:
            enlevements = db.session.query(
                PromotionSale.member_id,
                PromotionSale.gamme_id,
                func.sum(PromotionSale.quantity).label('total_quantity')
            ).filter(
                PromotionSale.sale_date == today
            ).group_by(PromotionSale.member_id, PromotionSale.gamme_id).all()
            retours = []
        
        # Organiser les données par membre
        members_summary = {}
        
        for sale in enlevements:
            member_id = sale.member_id
            if member_id not in members_summary:
                member = get_member_safe(member_id)
                members_summary[member_id] = {
                    'member': member,
                    'gammes': {}
                }
            members_summary[member_id]['gammes'][sale.gamme_id] = {
                'enlevements': sale.total_quantity,
                'retours': 0
            }
        
        for sale in retours:
            member_id = sale.member_id
            if member_id not in members_summary:
                member = get_member_safe(member_id)
                members_summary[member_id] = {
                    'member': member,
                    'gammes': {}
                }
            if sale.gamme_id not in members_summary[member_id]['gammes']:
                members_summary[member_id]['gammes'][sale.gamme_id] = {
                    'enlevements': 0,
                    'retours': 0
                }
            members_summary[member_id]['gammes'][sale.gamme_id]['retours'] = sale.total_quantity
        
        # Enrichir avec les noms des gammes et charger les équipes
        teams_map = {}  # Cache pour les équipes
        for member_id, summary in members_summary.items():
            member = summary['member']
            # Charger l'équipe du membre si nécessaire
            if member and member.team_id:
                if member.team_id not in teams_map:
                    try:
                        team = PromotionTeam.query.options(
                            load_only(PromotionTeam.id, PromotionTeam.name)
                        ).get(member.team_id)
                        teams_map[member.team_id] = team
                    except Exception:
                        teams_map[member.team_id] = None
                summary['team'] = teams_map[member.team_id]
            else:
                summary['team'] = None
            
            for gamme_id, data in summary['gammes'].items():
                gamme = PromotionGamme.query.get(gamme_id)
                data['gamme'] = gamme
                data['net'] = data['enlevements'] - data['retours']
        
        # Calculer les totaux de la journée (montants)
        if has_transaction_type:
            # Total enlèvements (montant)
            total_ca_enlevements = db.session.query(
                func.sum(PromotionSale.total_amount_gnf)
            ).filter(
                PromotionSale.sale_date == today,
                PromotionSale.transaction_type == 'enlevement'
            ).scalar() or Decimal("0.00")
            
            # Total retours (montant)
            total_ca_retours = db.session.query(
                func.sum(PromotionSale.total_amount_gnf)
            ).filter(
                PromotionSale.sale_date == today,
                PromotionSale.transaction_type == 'retour'
            ).scalar() or Decimal("0.00")
            
            # Vente nette = Total enlèvements - Total retours
            vente_nette = total_ca_enlevements - total_ca_retours
        else:
            # Si pas de transaction_type, on considère tout comme enlèvements
            total_ca_enlevements = db.session.query(
                func.sum(PromotionSale.total_amount_gnf)
            ).filter(
                PromotionSale.sale_date == today
            ).scalar() or Decimal("0.00")
            total_ca_retours = Decimal("0.00")
            vente_nette = total_ca_enlevements
        
    except Exception as e:
        print(f"Erreur lors de la récupération des statistiques: {e}")
        members_summary = {}
        total_ca_enlevements = Decimal("0.00")
        total_ca_retours = Decimal("0.00")
        vente_nette = Decimal("0.00")
    
    return render_template('promotion/daily_closure.html',
                         today=today,
                         is_closed=is_closed,
                         closure=existing_closure,
                         members_summary=members_summary,
                         total_ca_enlevements=total_ca_enlevements,
                         total_ca_retours=total_ca_retours,
                         vente_nette=vente_nette)

@promotion_bp.route('/api/notifications/stock-alerts')
@login_required
def api_stock_alerts():
    """API pour récupérer les alertes de stock faible"""
    if not has_permission(current_user, 'promotion.read'):
        return jsonify({'error': 'Permission denied'}), 403
    
    threshold = request.args.get('threshold', 10, type=int)
    alerts = get_low_stock_alerts(threshold=threshold)
    
    return jsonify({
        'alerts': alerts,
        'count': len(alerts),
        'critical_count': len([a for a in alerts if a['level'] == 'critical']),
        'warning_count': len([a for a in alerts if a['level'] == 'warning'])
    })

@promotion_bp.route('/reports')
@login_required
def reports():
    """Page de rapports avancés avec graphiques et analyses"""
    if not has_permission(current_user, 'promotion.read'):
        flash("Vous n'avez pas la permission d'accéder à cette page.", "error")
        return redirect(url_for('promotion.dashboard'))
    
    from datetime import timedelta
    import json
    
    today = date.today()
    month_start = date(today.year, today.month, 1)
    last_month_start = date(today.year, today.month - 1, 1) if today.month > 1 else date(today.year - 1, 12, 1)
    last_month_end = month_start - timedelta(days=1)
    
    has_transaction_type = has_transaction_type_column_cached()
    
    # Statistiques mensuelles
    try:
        if has_transaction_type:
            # CA du mois
            revenue_enlevements_month = db.session.query(func.sum(PromotionSale.total_amount_gnf)).filter(
                PromotionSale.sale_date >= month_start,
                PromotionSale.sale_date <= today,
                PromotionSale.transaction_type == 'enlevement'
            ).scalar() or Decimal("0.00")
            
            revenue_retours_month = db.session.query(func.sum(PromotionSale.total_amount_gnf)).filter(
                PromotionSale.sale_date >= month_start,
                PromotionSale.sale_date <= today,
                PromotionSale.transaction_type == 'retour'
            ).scalar() or Decimal("0.00")
            
            ca_net_month = revenue_enlevements_month - revenue_retours_month
            
            # CA du mois dernier
            revenue_enlevements_last_month = db.session.query(func.sum(PromotionSale.total_amount_gnf)).filter(
                PromotionSale.sale_date >= last_month_start,
                PromotionSale.sale_date <= last_month_end,
                PromotionSale.transaction_type == 'enlevement'
            ).scalar() or Decimal("0.00")
            
            revenue_retours_last_month = db.session.query(func.sum(PromotionSale.total_amount_gnf)).filter(
                PromotionSale.sale_date >= last_month_start,
                PromotionSale.sale_date <= last_month_end,
                PromotionSale.transaction_type == 'retour'
            ).scalar() or Decimal("0.00")
            
            ca_net_last_month = revenue_enlevements_last_month - revenue_retours_last_month
            
            # Variation
            variation = ((float(ca_net_month) - float(ca_net_last_month)) / float(ca_net_last_month) * 100) if ca_net_last_month > 0 else 0
        else:
            ca_net_month = db.session.query(func.sum(PromotionSale.total_amount_gnf)).filter(
                PromotionSale.sale_date >= month_start,
                PromotionSale.sale_date <= today
            ).scalar() or Decimal("0.00")
            ca_net_last_month = Decimal("0.00")
            variation = 0
    except Exception as e:
        print(f"Erreur calcul stats mensuelles: {e}")
        ca_net_month = Decimal("0.00")
        ca_net_last_month = Decimal("0.00")
        variation = 0
    
    # Données pour graphique des ventes des 30 derniers jours
    sales_by_day = []
    labels_30_days = []
    for i in range(29, -1, -1):
        day = today - timedelta(days=i)
        labels_30_days.append(day.strftime('%d/%m'))
        
        if has_transaction_type:
            enlevements = db.session.query(func.sum(PromotionSale.total_amount_gnf)).filter(
                PromotionSale.sale_date == day,
                PromotionSale.transaction_type == 'enlevement'
            ).scalar() or Decimal("0.00")
            
            retours = db.session.query(func.sum(PromotionSale.total_amount_gnf)).filter(
                PromotionSale.sale_date == day,
                PromotionSale.transaction_type == 'retour'
            ).scalar() or Decimal("0.00")
            
            sales_by_day.append(float(enlevements - retours))
        else:
            total = db.session.query(func.sum(PromotionSale.total_amount_gnf)).filter(
                PromotionSale.sale_date == day
            ).scalar() or Decimal("0.00")
            sales_by_day.append(float(total))
    
    # Top équipes par CA
    top_teams = []
    try:
        if has_transaction_type:
            team_stats = db.session.query(
                PromotionTeam.id,
                PromotionTeam.name,
                func.sum(
                    case(
                        (PromotionSale.transaction_type == 'enlevement', PromotionSale.total_amount_gnf),
                        else_=-PromotionSale.total_amount_gnf
                    )
                ).label('ca_net')
            ).join(PromotionMember, PromotionTeam.id == PromotionMember.team_id).join(
                PromotionSale, PromotionMember.id == PromotionSale.member_id
            ).filter(
                PromotionSale.sale_date >= month_start,
                PromotionSale.sale_date <= today
            ).group_by(PromotionTeam.id, PromotionTeam.name).order_by(
                func.sum(
                    case(
                        (PromotionSale.transaction_type == 'enlevement', PromotionSale.total_amount_gnf),
                        else_=-PromotionSale.total_amount_gnf
                    )
                ).desc()
            ).limit(5).all()
            
            for team_id, team_name, ca_net in team_stats:
                top_teams.append({
                    'name': team_name,
                    'ca_net': float(ca_net or 0)
                })
        else:
            team_stats = db.session.query(
                PromotionTeam.id,
                PromotionTeam.name,
                func.sum(PromotionSale.total_amount_gnf).label('ca_net')
            ).join(PromotionMember, PromotionTeam.id == PromotionMember.team_id).join(
                PromotionSale, PromotionMember.id == PromotionSale.member_id
            ).filter(
                PromotionSale.sale_date >= month_start,
                PromotionSale.sale_date <= today
            ).group_by(PromotionTeam.id, PromotionTeam.name).order_by(
                func.sum(PromotionSale.total_amount_gnf).desc()
            ).limit(5).all()
            
            for team_id, team_name, ca_net in team_stats:
                top_teams.append({
                    'name': team_name,
                    'ca_net': float(ca_net or 0)
                })
    except Exception as e:
        print(f"Erreur calcul top équipes: {e}")
    
    # Top gammes par quantité vendue
    top_gammes = []
    try:
        if has_transaction_type:
            gamme_stats = db.session.query(
                PromotionGamme.id,
                PromotionGamme.name,
                func.sum(
                    case(
                        (PromotionSale.transaction_type == 'enlevement', PromotionSale.quantity),
                        else_=-PromotionSale.quantity
                    )
                ).label('qty_net')
            ).join(PromotionSale, PromotionGamme.id == PromotionSale.gamme_id).filter(
                PromotionSale.sale_date >= month_start,
                PromotionSale.sale_date <= today
            ).group_by(PromotionGamme.id, PromotionGamme.name).order_by(
                func.sum(
                    case(
                        (PromotionSale.transaction_type == 'enlevement', PromotionSale.quantity),
                        else_=-PromotionSale.quantity
                    )
                ).desc()
            ).limit(5).all()
            
            for gamme_id, gamme_name, qty_net in gamme_stats:
                top_gammes.append({
                    'name': gamme_name,
                    'quantity': int(qty_net or 0)
                })
        else:
            gamme_stats = db.session.query(
                PromotionGamme.id,
                PromotionGamme.name,
                func.sum(PromotionSale.quantity).label('qty_net')
            ).join(PromotionSale, PromotionGamme.id == PromotionSale.gamme_id).filter(
                PromotionSale.sale_date >= month_start,
                PromotionSale.sale_date <= today
            ).group_by(PromotionGamme.id, PromotionGamme.name).order_by(
                func.sum(PromotionSale.quantity).desc()
            ).limit(5).all()
            
            for gamme_id, gamme_name, qty_net in gamme_stats:
                top_gammes.append({
                    'name': gamme_name,
                    'quantity': int(qty_net or 0)
                })
    except Exception as e:
        print(f"Erreur calcul top gammes: {e}")
    
    return render_template('promotion/reports.html',
                         today=today,
                         month_start=month_start,
                         ca_net_month=ca_net_month,
                         ca_net_last_month=ca_net_last_month,
                         variation=variation,
                         sales_by_day_labels=json.dumps(labels_30_days),
                         sales_by_day_data=json.dumps(sales_by_day),
                         top_teams=json.dumps(top_teams),
                         top_gammes=json.dumps(top_gammes))

@promotion_bp.route('/api/gammes/<int:gamme_id>/info')
@promotion_bp.route('/api/gamme/<int:gamme_id>/info')
@login_required
def get_gamme_info(gamme_id):
    """API pour récupérer les informations d'une gamme"""
    if not has_permission(current_user, 'promotion.read'):
        return jsonify({'error': 'Permission denied'}), 403
    
    try:
        gamme = PromotionGamme.query.get_or_404(gamme_id)
        return jsonify({
            'id': gamme.id,
            'name': gamme.name,
            'selling_price_gnf': float(gamme.selling_price_gnf),
            'commission_per_unit_gnf': float(gamme.commission_per_unit_gnf),
            'is_piece': gamme.is_piece,
            'unit_type': gamme.unit_type,
            'unit_description': gamme.unit_description
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@promotion_bp.route('/api/team-locations')
@login_required
def get_team_locations():
    """API pour récupérer les localisations des équipes"""
    if not has_permission(current_user, 'promotion.read'):
        return jsonify({'error': 'Permission denied'}), 403
    
    try:
        locations = PromotionMemberLocation.query.options(
            joinedload(PromotionMemberLocation.member).load_only(
                PromotionMember.id, PromotionMember.full_name
            )
        ).order_by(PromotionMemberLocation.timestamp.desc()).limit(100).all()
        
        result = []
        for loc in locations:
            if loc.member:
                result.append({
                    'id': loc.id,
                    'member_id': loc.member_id,
                    'member_name': loc.member.full_name,
                    'latitude': float(loc.latitude),
                    'longitude': float(loc.longitude),
                    'timestamp': loc.timestamp.isoformat() if loc.timestamp else None
                })
        
        return jsonify(result)
    except Exception as e:
        print(f"DEBUG get_team_locations error: {e}")
        return jsonify({'error': str(e)}), 500
