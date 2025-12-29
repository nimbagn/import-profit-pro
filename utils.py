#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Utilitaires - Import Profit Pro
Fonctions utilitaires pour parsing, calculs, validations
"""

from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from models import VehicleOdometer, VehicleDocument

def parse_pile_dimensions(pile_str):
    """
    Parse une chaîne de dimensions de pile (ex: "2x5+3x4" ou "2*10+100*2") et retourne la quantité totale.
    
    Format attendu : "NxM+NxM+..." ou "N*M+N*M+..." où N est le nombre de piles et M est la quantité par pile.
    Accepte les séparateurs 'x' et '*' (astérisque).
    
    Exemples:
    - "2x5+3x4" → (2*5) + (3*4) = 10 + 12 = 22
    - "2*10+100*2" → (2*10) + (100*2) = 20 + 200 = 220
    - "5x10" → 50
    - "1x5+2x3+1x2" → 5 + 6 + 2 = 13
    
    Args:
        pile_str (str): Chaîne à parser (ex: "2x5+3x4" ou "2*10+100*2")
    
    Returns:
        Decimal: Quantité totale calculée, ou 0 si erreur de parsing
    """
    if not pile_str or not pile_str.strip():
        return Decimal('0')
    
    try:
        total = Decimal('0')
        # Séparer par les '+'
        parts = pile_str.strip().split('+')
        
        for part in parts:
            part = part.strip()
            if not part:  # Ignorer les parties vides
                continue
            
            # Accepter 'x' ou '*' comme séparateur
            separator = None
            if 'x' in part or 'X' in part:
                separator = 'x' if 'x' in part else 'X'
            elif '*' in part:
                separator = '*'
            
            if separator:
                # Séparer par le séparateur trouvé
                factors = part.split(separator)
                if len(factors) == 2:
                    # Vérifier que les deux parties sont numériques
                    nb_piles_str = factors[0].strip()
                    qty_per_pile_str = factors[1].strip()
                    
                    if nb_piles_str and qty_per_pile_str:
                        try:
                            nb_piles = Decimal(nb_piles_str)
                            qty_per_pile = Decimal(qty_per_pile_str)
                            total += nb_piles * qty_per_pile
                        except (ValueError, TypeError, InvalidOperation):
                            # Ignorer cette partie si elle n'est pas valide
                            continue
            else:
                # Si pas de séparateur, considérer comme quantité directe
                # Vérifier que c'est un nombre valide
                if part:
                    try:
                        total += Decimal(part)
                    except (ValueError, TypeError, InvalidOperation):
                        # Ignorer cette partie si elle n'est pas valide
                        continue
        
        return total
    except (ValueError, TypeError, InvalidOperation):
        return Decimal('0')

def calculate_document_status(expiry_date):
    """
    Calcule le statut d'un document basé sur sa date d'expiration.
    
    Args:
        expiry_date (date): Date d'expiration du document
    
    Returns:
        str: 'valid', 'expiring', 'expired', ou 'unknown'
    """
    if not expiry_date:
        return 'unknown'
    
    today = date.today()
    days_until_expiry = (expiry_date - today).days
    
    if days_until_expiry < 0:
        return 'expired'
    elif days_until_expiry <= 7:
        return 'expiring'
    else:
        return 'valid'

def check_km_consistency(vehicle_id, new_km):
    """
    Vérifie que le nouveau kilométrage est cohérent (croissant).
    
    Args:
        vehicle_id (int): ID du véhicule
        new_km (int): Nouveau kilométrage à vérifier
    
    Returns:
        tuple: (is_valid, last_km, error_message)
        - is_valid (bool): True si le km est valide
        - last_km (int): Dernier km enregistré (ou None)
        - error_message (str): Message d'erreur si invalide
    """
    from models import db, VehicleOdometer
    
    # Récupérer le dernier relevé
    last_reading = VehicleOdometer.query.filter_by(vehicle_id=vehicle_id)\
        .order_by(VehicleOdometer.reading_date.desc(), VehicleOdometer.odometer_km.desc())\
        .first()
    
    if last_reading:
        if new_km < last_reading.odometer_km:
            return (False, last_reading.odometer_km, 
                   f"Le kilométrage ({new_km} km) est inférieur au dernier relevé ({last_reading.odometer_km} km)")
    
    return (True, last_reading.odometer_km if last_reading else None, None)

def format_currency(amount, currency="GNF"):
    """
    Formate un montant en devise avec espaces comme séparateurs de milliers.
    
    Args:
        amount (Decimal): Montant à formater
        currency (str): Code devise (par défaut GNF)
    
    Returns:
        str: Montant formaté avec espaces comme séparateurs
    """
    if amount is None:
        return "-"
    
    try:
        amount_float = float(amount)
        if currency == "GNF":
            # Formater avec virgules puis remplacer par des espaces
            formatted = f"{amount_float:,.0f}".replace(',', ' ')
            return f"{formatted} {currency}"
        else:
            # Pour les autres devises, utiliser 2 décimales
            formatted = f"{amount_float:,.2f}".replace(',', ' ')
            return f"{formatted} {currency}"
    except (ValueError, TypeError):
        return "-"

def get_days_until_expiry(expiry_date):
    """
    Calcule le nombre de jours jusqu'à l'expiration.
    
    Args:
        expiry_date (date): Date d'expiration
    
    Returns:
        int: Nombre de jours (négatif si expiré)
    """
    if not expiry_date:
        return None
    
    today = date.today()
    return (expiry_date - today).days

