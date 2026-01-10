# utils_region_filter.py
# Utilitaires pour filtrer les données par région selon l'utilisateur connecté

from flask_login import current_user
from models import (
    Depot, Vehicle, User, Region, DepotStock, VehicleStock, StockMovement, 
    PromotionTeam, PromotionMember, PromotionSale, CommercialOrder, CommercialSale, 
    SalesObjective, LockisteTeam, VendeurTeam
)
from sqlalchemy import or_


def get_user_region_id():
    """
    Retourne l'ID de la région de l'utilisateur connecté
    Retourne None si l'utilisateur n'a pas de région ou est admin/superviseur
    
    IMPORTANT: 
    - Les admins et superviseurs voient TOUT (pas de filtre par région)
    - TOUS les autres utilisateurs (magasiniers, commerciaux, etc.) voient uniquement leur région
    - Cette fonction retourne None pour les admins/superviseurs, ce qui désactive tous les filtres
    """
    if not current_user or not current_user.is_authenticated:
        return None
    
    # ⚠️ RÈGLE FONDAMENTALE : Seuls les admins et superviseurs voient TOUT (pas de filtre par région)
    # Retourner None désactive tous les filtres de région pour l'admin et le superviseur
    # Vérifier le rôle avec gestion d'erreur
    try:
        if hasattr(current_user, 'role') and current_user.role:
            role_code = getattr(current_user.role, 'code', None)
            # Seuls admin et supervisor voient toutes les régions
            if role_code in ['admin', 'superadmin', 'supervisor']:
                return None  # Admin et superviseur voient toutes les régions - aucun filtre appliqué
    except Exception as e:
        # En cas d'erreur, continuer avec le filtrage par région
        print(f"⚠️ Erreur lors de la vérification du rôle: {e}")
    
    # Retourner la région de l'utilisateur
    # TOUS les autres utilisateurs (magasiniers, commerciaux, etc.) sont filtrés par leur région
    region_id = getattr(current_user, 'region_id', None)
    if region_id is None:
        # Debug : afficher un avertissement si l'utilisateur n'a pas de région (sauf admin/supervisor)
        try:
            if hasattr(current_user, 'role') and current_user.role:
                role_code = getattr(current_user.role, 'code', None)
                if role_code not in ['admin', 'superadmin', 'supervisor']:
                    print(f"⚠️ Utilisateur {current_user.id} ({current_user.username}) n'a pas de région assignée - filtrage désactivé")
        except:
            pass
    
    return region_id


def filter_depots_by_region(query):
    """
    Filtre les dépôts selon la région de l'utilisateur connecté
    Les admins voient tous les dépôts
    """
    region_id = get_user_region_id()
    if region_id is not None:
        query = query.filter_by(region_id=region_id)
    return query


def filter_vehicles_by_region(query):
    """
    Filtre les véhicules selon la région de l'utilisateur connecté
    Un véhicule appartient à une région si son conducteur appartient à cette région
    Les admins voient tous les véhicules
    """
    region_id = get_user_region_id()
    if region_id is not None:
        # Filtrer les véhicules dont le conducteur appartient à la région
        # Utiliser join explicite avec condition pour éviter les ambiguïtés
        query = query.join(User, Vehicle.current_user_id == User.id).filter(
            User.region_id == region_id
        )
    return query


def filter_users_by_region(query):
    """
    Filtre les utilisateurs selon la région de l'utilisateur connecté
    Les admins voient tous les utilisateurs
    """
    region_id = get_user_region_id()
    if region_id is not None:
        query = query.filter_by(region_id=region_id)
    return query


def filter_teams_by_region(query):
    """
    Filtre les équipes de promotion selon la région de l'utilisateur connecté
    Une équipe appartient à une région si son responsable (team_leader) appartient à cette région
    Les admins voient toutes les équipes
    """
    region_id = get_user_region_id()
    if region_id is not None:
        # Filtrer les équipes dont le responsable appartient à la région
        query = query.join(User, PromotionTeam.team_leader_id == User.id).filter(
            User.region_id == region_id
        )
    return query


def filter_members_by_region(query):
    """
    Filtre les membres de promotion selon la région de l'utilisateur connecté
    Un membre appartient à une région si son équipe appartient à cette région
    Les admins voient tous les membres
    Utilise load_only pour éviter de charger les colonnes manquantes
    """
    from sqlalchemy.orm import load_only
    region_id = get_user_region_id()
    if region_id is not None:
        # Filtrer les membres dont l'équipe appartient à la région
        # Utiliser load_only pour ne charger que les colonnes essentielles
        query = query.options(
            load_only(PromotionMember.id, PromotionMember.team_id, PromotionMember.full_name,
                     PromotionMember.phone, PromotionMember.is_active)
        ).join(PromotionTeam, PromotionMember.team_id == PromotionTeam.id)\
         .join(User, PromotionTeam.team_leader_id == User.id)\
         .filter(User.region_id == region_id)
    else:
        # Même pour les admins, utiliser load_only pour éviter les colonnes manquantes
        query = query.options(
            load_only(PromotionMember.id, PromotionMember.team_id, PromotionMember.full_name,
                     PromotionMember.phone, PromotionMember.is_active)
        )
    return query


def filter_sales_by_region(query):
    """
    Filtre les ventes de promotion selon la région de l'utilisateur connecté
    Une vente appartient à une région si le membre appartient à une équipe de cette région
    Les admins voient toutes les ventes
    """
    region_id = get_user_region_id()
    if region_id is not None:
        # Filtrer les ventes dont le membre appartient à une équipe de la région
        query = query.join(PromotionMember, PromotionSale.member_id == PromotionMember.id)\
                     .join(PromotionTeam, PromotionMember.team_id == PromotionTeam.id)\
                     .join(User, PromotionTeam.team_leader_id == User.id)\
                     .filter(User.region_id == region_id)
    return query


def filter_stock_movements_by_region(query):
    """
    Filtre les mouvements de stock selon la région de l'utilisateur connecté
    Un mouvement appartient à une région si :
    - Le dépôt source ou destination appartient à cette région, OU
    - Le véhicule source ou destination appartient à cette région (via son conducteur)
    Les admins voient tous les mouvements
    """
    region_id = get_user_region_id()
    if region_id is not None:
        # Récupérer les IDs des dépôts de la région
        depot_ids = [d.id for d in Depot.query.filter_by(region_id=region_id).all()]
        
        # Récupérer les IDs des véhicules de la région (via leur conducteur)
        vehicle_ids = []
        vehicles = Vehicle.query.join(User, Vehicle.current_user_id == User.id).filter(
            User.region_id == region_id
        ).all()
        vehicle_ids = [v.id for v in vehicles]
        
        # Filtrer les mouvements liés aux dépôts OU véhicules de la région
        conditions = []
        if depot_ids:
            conditions.append(
                or_(
                    StockMovement.from_depot_id.in_(depot_ids),
                    StockMovement.to_depot_id.in_(depot_ids)
                )
            )
        if vehicle_ids:
            conditions.append(
                or_(
                    StockMovement.from_vehicle_id.in_(vehicle_ids),
                    StockMovement.to_vehicle_id.in_(vehicle_ids)
                )
            )
        
        if conditions:
            # Utiliser or_() pour combiner les conditions dépôts et véhicules
            query = query.filter(or_(*conditions))
        else:
            # Aucun dépôt/véhicule dans la région, retourner une requête vide
            query = query.filter(False)
    
    return query


def filter_depot_stocks_by_region(query):
    """
    Filtre les stocks de dépôt selon la région de l'utilisateur connecté
    Les admins voient tous les stocks
    """
    region_id = get_user_region_id()
    if region_id is not None:
        # Récupérer les IDs des dépôts de la région
        depot_ids = [d.id for d in Depot.query.filter_by(region_id=region_id).all()]
        
        if depot_ids:
            query = query.filter(DepotStock.depot_id.in_(depot_ids))
        else:
            query = query.filter(False)
    
    return query


def filter_vehicle_stocks_by_region(query):
    """
    Filtre les stocks de véhicule selon la région de l'utilisateur connecté
    Un véhicule appartient à une région si son conducteur appartient à cette région
    Les admins voient tous les stocks
    """
    region_id = get_user_region_id()
    if region_id is not None:
        # Récupérer les IDs des véhicules de la région
        vehicle_ids = [
            v.id for v in Vehicle.query.join(User, Vehicle.current_user_id == User.id)
            .filter(User.region_id == region_id).all()
        ]
        
        if vehicle_ids:
            query = query.filter(VehicleStock.vehicle_id.in_(vehicle_ids))
        else:
            query = query.filter(False)
    
    return query


def can_access_region(region_id):
    """
    Vérifie si l'utilisateur connecté peut accéder à une région spécifique
    Les admins et superviseurs peuvent accéder à toutes les régions
    """
    if not current_user or not current_user.is_authenticated:
        return False
    
    # Les admins et superviseurs peuvent accéder à toutes les régions
    if hasattr(current_user, 'role') and current_user.role:
        if current_user.role.code in ['admin', 'superadmin', 'supervisor']:
            return True
    
    # Vérifier si l'utilisateur appartient à cette région
    return current_user.region_id == region_id if hasattr(current_user, 'region_id') else False


def can_access_depot(depot_id):
    """
    Vérifie si l'utilisateur connecté peut accéder à un dépôt spécifique
    Les admins et superviseurs peuvent accéder à tous les dépôts
    """
    if not current_user or not current_user.is_authenticated:
        return False
    
    # Les admins et superviseurs peuvent accéder à tous les dépôts
    if hasattr(current_user, 'role') and current_user.role:
        if current_user.role.code in ['admin', 'superadmin', 'supervisor']:
            return True
    
    # Vérifier si le dépôt appartient à la région de l'utilisateur
    depot = Depot.query.get(depot_id)
    if not depot:
        return False
    
    return depot.region_id == current_user.region_id if hasattr(current_user, 'region_id') and depot.region_id else False


def can_access_vehicle(vehicle_id):
    """
    Vérifie si l'utilisateur connecté peut accéder à un véhicule spécifique
    Les admins et superviseurs peuvent accéder à tous les véhicules
    Les magasiniers peuvent accéder à tous les véhicules (pour gestion de flotte)
    """
    if not current_user or not current_user.is_authenticated:
        return False
    
    # Les admins, superviseurs et magasiniers peuvent accéder à tous les véhicules
    if hasattr(current_user, 'role') and current_user.role:
        role_code = getattr(current_user.role, 'code', None)
        if role_code in ['admin', 'superadmin', 'supervisor', 'warehouse']:
            return True
    
    # Vérifier si le véhicule appartient à la région de l'utilisateur (via le conducteur)
    vehicle = Vehicle.query.get(vehicle_id)
    if not vehicle or not vehicle.current_user_id:
        return False
    
    driver = User.query.get(vehicle.current_user_id)
    if not driver:
        return False
    
    return driver.region_id == current_user.region_id if hasattr(current_user, 'region_id') and driver.region_id else False


def get_user_accessible_regions():
    """
    Retourne la liste des régions accessibles par l'utilisateur connecté
    Les admins et superviseurs voient toutes les régions
    """
    if not current_user or not current_user.is_authenticated:
        return []
    
    # Les admins et superviseurs voient toutes les régions
    if hasattr(current_user, 'role') and current_user.role:
        if current_user.role.code in ['admin', 'superadmin', 'supervisor']:
            return Region.query.order_by(Region.name).all()
    
    # Sinon, retourner uniquement la région de l'utilisateur
    if hasattr(current_user, 'region_id') and current_user.region_id:
        region = Region.query.get(current_user.region_id)
        return [region] if region else []
    
    return []


def get_user_accessible_depots():
    """
    Retourne la liste des dépôts accessibles par l'utilisateur connecté
    Les admins et superviseurs voient tous les dépôts
    """
    if not current_user or not current_user.is_authenticated:
        return []
    
    # Les admins et superviseurs voient tous les dépôts
    if hasattr(current_user, 'role') and current_user.role:
        if current_user.role.code in ['admin', 'superadmin', 'supervisor']:
            return Depot.query.order_by(Depot.name).all()
    
    # Sinon, retourner uniquement les dépôts de la région de l'utilisateur
    if hasattr(current_user, 'region_id') and current_user.region_id:
        return Depot.query.filter_by(region_id=current_user.region_id).order_by(Depot.name).all()
    
    return []


def filter_commercial_orders_by_region(query):
    """
    Filtre les commandes commerciales selon la région de l'utilisateur connecté
    Les admins voient toutes les commandes
    Les commerciaux voient uniquement leurs propres commandes (géré ailleurs)
    Les superviseurs voient les commandes de leur région
    """
    region_id = get_user_region_id()
    if region_id is not None:
        # Filtrer les commandes par région
        query = query.filter(CommercialOrder.region_id == region_id)
    return query


def filter_employees_by_region(query):
    """
    Filtre les employés externes selon la région de l'utilisateur connecté
    Les admins voient tous les employés
    """
    from models import Employee
    region_id = get_user_region_id()
    if region_id is not None:
        query = query.filter(Employee.region_id == region_id)
    return query


def filter_receptions_by_region(query):
    """
    Filtre les réceptions selon la région de l'utilisateur connecté
    Une réception appartient à une région si le dépôt appartient à cette région
    Les admins voient toutes les réceptions
    """
    from models import Reception
    region_id = get_user_region_id()
    if region_id is not None:
        # Récupérer les IDs des dépôts de la région
        depot_ids = [d.id for d in Depot.query.filter_by(region_id=region_id).all()]
        
        if depot_ids:
            query = query.filter(Reception.depot_id.in_(depot_ids))
        else:
            # Aucun dépôt dans la région, retourner une requête vide
            query = query.filter(False)
    
    return query


def filter_inventory_sessions_by_region(query):
    """
    Filtre les sessions d'inventaire selon la région de l'utilisateur connecté
    Une session appartient à une région si le dépôt appartient à cette région
    Les admins et superviseurs voient toutes les sessions
    """
    from models import InventorySession
    region_id = get_user_region_id()
    if region_id is not None:
        # Récupérer les IDs des dépôts de la région
        depot_ids = [d.id for d in Depot.query.filter_by(region_id=region_id).all()]
        
        if depot_ids:
            query = query.filter(InventorySession.depot_id.in_(depot_ids))
        else:
            # Aucun dépôt dans la région, retourner une requête vide
            query = query.filter(False)
    
    return query


def filter_commercial_sales_by_region(query):
    """
    Filtre les ventes commerciales selon la région de l'utilisateur connecté
    Une vente appartient à une région si la commande appartient à cette région
    Les admins et superviseurs voient toutes les ventes
    """
    region_id = get_user_region_id()
    if region_id is not None:
        # Filtrer les ventes par région via la commande
        query = query.join(CommercialOrder, CommercialSale.order_id == CommercialOrder.id).filter(
            CommercialOrder.region_id == region_id
        )
    return query


def filter_sales_objectives_by_region(query):
    """
    Filtre les objectifs de vente selon la région de l'utilisateur connecté
    Un objectif appartient à une région si le commercial appartient à cette région
    Les admins et superviseurs voient tous les objectifs
    """
    region_id = get_user_region_id()
    if region_id is not None:
        # Filtrer les objectifs par région via le commercial
        query = query.join(User, SalesObjective.commercial_id == User.id).filter(
            User.region_id == region_id
        )
    return query


def filter_lockiste_teams_by_region(query):
    """
    Filtre les équipes lockistes selon la région de l'utilisateur connecté
    Les admins et superviseurs voient toutes les équipes
    """
    region_id = get_user_region_id()
    if region_id is not None:
        query = query.filter(LockisteTeam.region_id == region_id)
    return query


def filter_vendeur_teams_by_region(query):
    """
    Filtre les équipes vendeurs selon la région de l'utilisateur connecté
    Les admins et superviseurs voient toutes les équipes
    """
    region_id = get_user_region_id()
    if region_id is not None:
        query = query.filter(VendeurTeam.region_id == region_id)
    return query


def filter_outgoings_by_region(query):
    """
    Filtre les sorties de stock selon la région de l'utilisateur connecté
    Une sortie appartient à une région si le dépôt ou le véhicule appartient à cette région
    Les admins et superviseurs voient toutes les sorties
    """
    from models import StockOutgoing
    region_id = get_user_region_id()
    if region_id is not None:
        # Récupérer les IDs des dépôts de la région
        depot_ids = [d.id for d in Depot.query.filter_by(region_id=region_id).all()]
        
        # Récupérer les IDs des véhicules de la région
        vehicle_ids = [
            v.id for v in Vehicle.query.join(User, Vehicle.current_user_id == User.id)
            .filter(User.region_id == region_id).all()
        ]
        
        conditions = []
        if depot_ids:
            conditions.append(StockOutgoing.depot_id.in_(depot_ids))
        if vehicle_ids:
            conditions.append(StockOutgoing.vehicle_id.in_(vehicle_ids))
        
        if conditions:
            query = query.filter(or_(*conditions))
        else:
            query = query.filter(False)
    
    return query


def filter_returns_by_region(query):
    """
    Filtre les retours de stock selon la région de l'utilisateur connecté
    Un retour appartient à une région si le dépôt ou le véhicule appartient à cette région
    Les admins et superviseurs voient tous les retours
    """
    from models import StockReturn
    region_id = get_user_region_id()
    if region_id is not None:
        # Récupérer les IDs des dépôts de la région
        depot_ids = [d.id for d in Depot.query.filter_by(region_id=region_id).all()]
        
        # Récupérer les IDs des véhicules de la région
        vehicle_ids = [
            v.id for v in Vehicle.query.join(User, Vehicle.current_user_id == User.id)
            .filter(User.region_id == region_id).all()
        ]
        
        conditions = []
        if depot_ids:
            conditions.append(StockReturn.depot_id.in_(depot_ids))
        if vehicle_ids:
            conditions.append(StockReturn.vehicle_id.in_(vehicle_ids))
        
        if conditions:
            query = query.filter(or_(*conditions))
        else:
            query = query.filter(False)
    
    return query

