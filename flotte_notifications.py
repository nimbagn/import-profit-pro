#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module de notifications automatiques pour la flotte
Gère les rappels de visage et documents véhicules
"""

from flask import current_app
from datetime import datetime, UTC, timedelta, date
import logging
from typing import List, Optional

logger = logging.getLogger(__name__)

def envoyer_rappels_vehicules():
    """Envoie les rappels pour les documents véhicules expirant bientôt"""
    try:
        from models import Vehicle, VehicleDocument, User
        from notifications_automatiques import notifications_automatiques
        
        # Récupérer tous les véhicules actifs
        vehicles = Vehicle.query.filter_by(status='active').all()
        
        vehicles_a_notifier = []
        
        for vehicle in vehicles:
            # Récupérer les documents expirant dans les 15 prochains jours
            today = date.today()
            documents_expiring = VehicleDocument.query.filter_by(vehicle_id=vehicle.id).all()
            
            # Filtrer ceux qui expirent dans les 15 prochains jours
            docs_to_notify = []
            for doc in documents_expiring:
                if doc.expiry_date:
                    expiry_date = doc.expiry_date
                    if isinstance(expiry_date, datetime):
                        expiry_date = expiry_date.date()
                    days_until = (expiry_date - today).days
                    if 0 <= days_until <= 15:
                        docs_to_notify.append(doc)
            
            documents_expiring = docs_to_notify
            
            if documents_expiring:
                vehicles_a_notifier.append({
                    'vehicle': vehicle,
                    'documents': documents_expiring
                })
        
        # Envoyer les notifications
        for item in vehicles_a_notifier:
            try:
                notifications_automatiques.notifier_rappel_visage_vehicule(
                    item['vehicle'],
                    days_until_expiry=15
                )
            except Exception as e:
                logger.error(f"Erreur lors de la notification pour véhicule {item['vehicle'].id}: {e}")
        
        return len(vehicles_a_notifier)
        
    except Exception as e:
        logger.error(f"Erreur lors de l'envoi des rappels véhicules: {e}")
        import traceback
        traceback.print_exc()
        return 0

