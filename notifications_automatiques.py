#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module de Notifications Automatiques via Message Pro
Gère l'envoi automatique de notifications et PDFs pour les événements importants
"""

from flask import current_app
from datetime import datetime, UTC, timedelta, date
from decimal import Decimal
from io import BytesIO
import logging
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)

class NotificationsAutomatiques:
    """Gestionnaire de notifications automatiques via Message Pro"""
    
    def __init__(self):
        self.messagepro_api = None
        self.pdf_generator = None
        self._init_apis()
    
    def _init_apis(self):
        """Initialise les APIs nécessaires"""
        try:
            from messagepro_api import MessageProAPI
            self.messagepro_api = MessageProAPI()
        except Exception as e:
            logger.warning(f"Impossible d'initialiser MessageProAPI: {e}")
            self.messagepro_api = None
        
        try:
            from pdf_generator import PDFGenerator
            self.pdf_generator = PDFGenerator()
        except Exception as e:
            logger.warning(f"Impossible d'initialiser PDFGenerator: {e}")
            self.pdf_generator = None
    
    def _get_whatsapp_account(self) -> Optional[str]:
        """Récupère le compte WhatsApp par défaut"""
        if not self.messagepro_api:
            return None
        
        try:
            accounts = self.messagepro_api.get_whatsapp_accounts(limit=1)
            if accounts.get('status') == 200 and accounts.get('data'):
                return accounts['data'][0].get('id')
        except Exception as e:
            logger.error(f"Erreur lors de la récupération du compte WhatsApp: {e}")
        
        return None
    
    def _send_whatsapp_notification(self, recipient: str, message: str, pdf_file: Optional[BytesIO] = None, pdf_name: Optional[str] = None) -> bool:
        """Envoie une notification WhatsApp avec optionnellement un PDF"""
        if not self.messagepro_api:
            logger.warning("MessageProAPI non disponible")
            return False
        
        account_id = self._get_whatsapp_account()
        if not account_id:
            logger.warning("Aucun compte WhatsApp disponible")
            return False
        
        try:
            if pdf_file:
                result = self.messagepro_api.send_whatsapp(
                    account=account_id,
                    recipient=recipient,
                    message=message,
                    message_type='document',
                    document_file=pdf_file,
                    document_name=pdf_name or f"document_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}.pdf",
                    document_type='pdf',
                    priority=2
                )
            else:
                result = self.messagepro_api.send_whatsapp(
                    account=account_id,
                    recipient=recipient,
                    message=message,
                    message_type='text',
                    priority=2
                )
            
            if result.get('status') == 200:
                logger.info(f"Notification envoyée avec succès à {recipient}")
                return True
            else:
                logger.error(f"Erreur lors de l'envoi à {recipient}: {result.get('message')}")
                return False
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi de notification: {e}")
            return False
    
    def _send_sms_notification(self, recipient: str, message: str) -> bool:
        """Envoie une notification SMS"""
        if not self.messagepro_api:
            logger.warning("MessageProAPI non disponible")
            return False
        
        try:
            result = self.messagepro_api.send_sms(
                recipient=recipient,
                message=message,
                sender='IMPORTPRO',
                priority=2
            )
            
            if result.get('status') == 200:
                logger.info(f"SMS envoyé avec succès à {recipient}")
                return True
            else:
                logger.error(f"Erreur lors de l'envoi SMS à {recipient}: {result.get('message')}")
                return False
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi SMS: {e}")
            return False
    
    def _get_user_phone(self, user) -> Optional[str]:
        """Récupère le numéro de téléphone d'un utilisateur"""
        if not user:
            return None
        
        # Essayer différents champs possibles
        phone = getattr(user, 'phone', None) or getattr(user, 'mobile', None) or getattr(user, 'telephone', None)
        
        if phone:
            # Nettoyer le numéro (enlever espaces, +, etc.)
            phone = str(phone).strip().replace(' ', '').replace('+', '').replace('-', '')
            # Ajouter l'indicatif guinéen si nécessaire
            if not phone.startswith('224'):
                if phone.startswith('0'):
                    phone = '224' + phone[1:]
                else:
                    phone = '224' + phone
        
        return phone
    
    # =========================================================
    # NOTIFICATIONS COMMANDES
    # =========================================================
    
    def notifier_creation_commande(self, order) -> bool:
        """Notifie la création d'une nouvelle commande"""
        try:
            from models import User
            
            # Récupérer le commercial
            commercial = order.commercial if hasattr(order, 'commercial') else User.query.get(order.commercial_id)
            if not commercial:
                return False
            
            # Récupérer le superviseur (via région ou hiérarchie)
            supervisor = None
            if hasattr(order, 'region_id') and order.region_id:
                from models import Region
                region = Region.query.get(order.region_id)
                if region and hasattr(region, 'supervisor_id') and region.supervisor_id:
                    supervisor = User.query.get(region.supervisor_id)
            
            # Si pas de superviseur régional, chercher un superviseur général
            if not supervisor:
                supervisor = User.query.join(User.role).filter(
                    User.role.has(code='supervisor'),
                    User.is_active == True
                ).first()
            
            if not supervisor:
                logger.warning("Aucun superviseur trouvé pour notifier")
                return False
            
            supervisor_phone = self._get_user_phone(supervisor)
            if not supervisor_phone:
                logger.warning(f"Superviseur {supervisor.username} n'a pas de numéro de téléphone")
                return False
            
            # Calculer le montant total de la commande
            total_amount = Decimal('0')
            if hasattr(order, 'clients'):
                for client in order.clients:
                    if hasattr(client, 'items'):
                        for item in client.items:
                            if hasattr(item, 'quantity') and hasattr(item, 'unit_price_gnf'):
                                qty = Decimal(str(item.quantity)) if item.quantity else Decimal('0')
                                price = Decimal(str(item.unit_price_gnf)) if item.unit_price_gnf else Decimal('0')
                                total_amount += qty * price
            
            # Message de notification
            message = f"""🔔 NOUVELLE COMMANDE CRÉÉE

Référence: {order.reference}
Commercial: {commercial.full_name or commercial.username}
Date: {order.order_date.strftime('%d/%m/%Y %H:%M') if hasattr(order.order_date, 'strftime') else str(order.order_date)}
Montant: {self._format_amount(total_amount)} GNF

Veuillez valider la commande dans l'application.
"""
            
            return self._send_whatsapp_notification(supervisor_phone, message)
            
        except Exception as e:
            logger.error(f"Erreur lors de la notification de création de commande: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def notifier_validation_commande(self, order) -> bool:
        """Notifie la validation d'une commande"""
        try:
            from models import User
            
            # Récupérer le commercial
            commercial = order.commercial if hasattr(order, 'commercial') else User.query.get(order.commercial_id)
            if not commercial:
                return False
            
            commercial_phone = self._get_user_phone(commercial)
            if not commercial_phone:
                logger.warning(f"Commercial {commercial.username} n'a pas de numéro de téléphone")
                return False
            
            # Message de notification
            validator_name = "Superviseur"
            if hasattr(order, 'validator') and order.validator:
                validator_name = order.validator.full_name or order.validator.username
            elif hasattr(order, 'validated_by_id') and order.validated_by_id:
                validator = User.query.get(order.validated_by_id)
                if validator:
                    validator_name = validator.full_name or validator.username
            
            message = f"""✅ COMMANDE VALIDÉE

Référence: {order.reference}
Validée par: {validator_name}
Date: {order.validated_at.strftime('%d/%m/%Y %H:%M') if hasattr(order, 'validated_at') and order.validated_at else datetime.now(UTC).strftime('%d/%m/%Y %H:%M')}

Votre commande a été validée et peut être traitée.
"""
            
            return self._send_whatsapp_notification(commercial_phone, message)
            
        except Exception as e:
            logger.error(f"Erreur lors de la notification de validation de commande: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    # =========================================================
    # NOTIFICATIONS VÉHICULES
    # =========================================================
    
    def notifier_rappel_visage_vehicule(self, vehicle, days_until_expiry: int) -> bool:
        """Notifie le rappel de visage/renouvellement de document véhicule"""
        try:
            from models import User, VehicleDocument
            
            # Récupérer le conducteur actuel
            driver = None
            if hasattr(vehicle, 'current_user_id') and vehicle.current_user_id:
                driver = User.query.get(vehicle.current_user_id)
            
            # Récupérer les documents expirant bientôt
            today = date.today()
            documents_expiring = VehicleDocument.query.filter_by(vehicle_id=vehicle.id).all()
            expiring_docs = []
            for doc in documents_expiring:
                if doc.expiry_date:
                    expiry_date = doc.expiry_date
                    if isinstance(expiry_date, datetime):
                        expiry_date = expiry_date.date()
                    days = (expiry_date - today).days
                    if 0 <= days <= days_until_expiry:
                        expiring_docs.append(doc)
            
            if not expiring_docs:
                return False
            
            # Notifier le conducteur si disponible
            recipients = []
            if driver:
                driver_phone = self._get_user_phone(driver)
                if driver_phone:
                    recipients.append(driver_phone)
            
            # Notifier aussi le magasinier/superviseur
            from models import User, Role
            supervisors = User.query.join(Role).filter(
                Role.code.in_(['supervisor', 'warehouse', 'admin']),
                User.is_active == True
            ).all()
            
            for supervisor in supervisors:
                supervisor_phone = self._get_user_phone(supervisor)
                if supervisor_phone and supervisor_phone not in recipients:
                    recipients.append(supervisor_phone)
            
            if not recipients:
                logger.warning("Aucun destinataire trouvé pour le rappel véhicule")
                return False
            
            # Message de notification
            docs_list = []
            for doc in expiring_docs:
                expiry_date = doc.expiry_date
                if isinstance(expiry_date, datetime):
                    expiry_date = expiry_date.date()
                expiry_str = expiry_date.strftime('%d/%m/%Y') if hasattr(expiry_date, 'strftime') else str(expiry_date)
                docs_list.append(f"- {doc.document_type}: Expire le {expiry_str}")
            docs_list_str = "\n".join(docs_list)
            
            message = f"""🚗 RAPPEL - DOCUMENTS VÉHICULE

Véhicule: {vehicle.plate_number or vehicle.name or f'ID {vehicle.id}'}
Documents expirant bientôt:
{docs_list_str}

Veuillez renouveler ces documents avant expiration.
"""
            
            success = True
            for recipient in recipients:
                if not self._send_whatsapp_notification(recipient, message):
                    success = False
            
            return success
            
        except Exception as e:
            logger.error(f"Erreur lors de la notification de rappel véhicule: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    # =========================================================
    # NOTIFICATIONS STOCK
    # =========================================================
    
    def notifier_inventaire_stock(self, depot_id: Optional[int] = None, recipients: Optional[List[str]] = None) -> bool:
        """Génère et envoie le PDF d'inventaire de stock"""
        try:
            if not self.pdf_generator:
                logger.warning("PDFGenerator non disponible")
                return False
            
            # Utiliser la fonction utilitaire pour générer les données
            from stocks import generate_stock_summary_pdf_data
            stock_data = generate_stock_summary_pdf_data(
                depot_id=depot_id,
                period='all',
                currency='GNF'
            )
            
            if not stock_data:
                logger.error("Erreur lors de la génération des données d'inventaire")
                return False
            
            # Générer le PDF d'inventaire
            pdf_buffer = self.pdf_generator.generate_stock_summary_pdf(
                stock_data,
                currency='GNF',
                exchange_rate=None
            )
            
            if not pdf_buffer:
                logger.error("Erreur lors de la génération du PDF d'inventaire")
                return False
            
            # Déterminer les destinataires
            if not recipients:
                recipients = []
                from models import User, Role
                supervisors = User.query.join(Role).filter(
                    Role.code.in_(['supervisor', 'warehouse', 'admin']),
                    User.is_active == True
                ).all()
                
                for supervisor in supervisors:
                    supervisor_phone = self._get_user_phone(supervisor)
                    if supervisor_phone:
                        recipients.append(supervisor_phone)
            
            if not recipients:
                logger.warning("Aucun destinataire trouvé pour l'inventaire")
                return False
            
            # Message
            depot_name = "Tous les dépôts"
            if depot_id:
                from models import Depot
                depot = Depot.query.get(depot_id)
                if depot:
                    depot_name = depot.name
            
            message = f"""📊 INVENTAIRE DE STOCK

Dépôt: {depot_name}
Date: {datetime.now(UTC).strftime('%d/%m/%Y %H:%M')}

Veuillez trouver ci-joint le rapport d'inventaire de stock.
"""
            
            pdf_name = f"inventaire_stock_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}.pdf"
            
            success = True
            for recipient in recipients:
                # Créer une nouvelle copie du buffer pour chaque envoi
                pdf_copy = BytesIO(pdf_buffer.getvalue())
                if not self._send_whatsapp_notification(recipient, message, pdf_copy, pdf_name):
                    success = False
            
            return success
            
        except Exception as e:
            logger.error(f"Erreur lors de la notification d'inventaire: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def notifier_situation_stock_periode(self, depot_id: Optional[int] = None, period: str = 'month', recipients: Optional[List[str]] = None) -> bool:
        """Génère et envoie le PDF de situation de stock par période"""
        try:
            if not self.pdf_generator:
                logger.warning("PDFGenerator non disponible")
                return False
            
            # Calculer les dates selon la période
            end_date = datetime.now(UTC).date()
            if period == 'week':
                start_date = end_date - timedelta(days=7)
            elif period == 'month':
                start_date = end_date - timedelta(days=30)
            elif period == 'quarter':
                start_date = end_date - timedelta(days=90)
            elif period == 'year':
                start_date = end_date - timedelta(days=365)
            else:
                start_date = None
            
            # Utiliser la fonction utilitaire pour générer les données
            from stocks import generate_stock_summary_pdf_data
            stock_data = generate_stock_summary_pdf_data(
                depot_id=depot_id,
                period=period,
                currency='GNF',
                start_date=start_date.strftime('%Y-%m-%d') if start_date else None,
                end_date=end_date.strftime('%Y-%m-%d') if end_date else None
            )
            
            if not stock_data:
                logger.error("Erreur lors de la génération des données de situation")
                return False
            
            # Générer le PDF de situation de stock
            pdf_buffer = self.pdf_generator.generate_stock_summary_pdf(
                stock_data,
                currency='GNF',
                exchange_rate=None
            )
            
            if not pdf_buffer:
                logger.error("Erreur lors de la génération du PDF de situation")
                return False
            
            # Déterminer les destinataires
            if not recipients:
                recipients = []
                from models import User, Role
                supervisors = User.query.join(Role).filter(
                    Role.code.in_(['supervisor', 'warehouse', 'admin']),
                    User.is_active == True
                ).all()
                
                for supervisor in supervisors:
                    supervisor_phone = self._get_user_phone(supervisor)
                    if supervisor_phone:
                        recipients.append(supervisor_phone)
            
            if not recipients:
                logger.warning("Aucun destinataire trouvé pour la situation de stock")
                return False
            
            # Message
            depot_name = "Tous les dépôts"
            if depot_id:
                from models import Depot
                depot = Depot.query.get(depot_id)
                if depot:
                    depot_name = depot.name
            
            period_names = {
                'week': 'Semaine',
                'month': 'Mois',
                'quarter': 'Trimestre',
                'year': 'Année'
            }
            period_name = period_names.get(period, period)
            
            message = f"""📈 SITUATION DE STOCK - {period_name.upper()}

Dépôt: {depot_name}
Période: {start_date.strftime('%d/%m/%Y') if start_date else 'Tout'} au {end_date.strftime('%d/%m/%Y')}
Date: {datetime.now(UTC).strftime('%d/%m/%Y %H:%M')}

Veuillez trouver ci-joint le rapport de situation de stock.
"""
            
            pdf_name = f"situation_stock_{period}_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}.pdf"
            
            success = True
            for recipient in recipients:
                # Créer une nouvelle copie du buffer pour chaque envoi
                pdf_copy = BytesIO(pdf_buffer.getvalue())
                if not self._send_whatsapp_notification(recipient, message, pdf_copy, pdf_name):
                    success = False
            
            return success
            
        except Exception as e:
            logger.error(f"Erreur lors de la notification de situation de stock: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _format_amount(self, amount) -> str:
        """Formate un montant avec séparateurs de milliers"""
        try:
            if isinstance(amount, Decimal):
                amount = float(amount)
            elif not isinstance(amount, (int, float)):
                return str(amount)
            
            return f"{amount:,.0f}".replace(',', ' ')
        except:
            return str(amount)


# Instance globale
notifications_automatiques = NotificationsAutomatiques()

