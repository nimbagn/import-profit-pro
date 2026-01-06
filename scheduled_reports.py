#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module de planification et d'envoi automatique de rapports
Gère l'envoi automatique de rapports PDF via WhatsApp via Message Pro
"""

from flask import Flask
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime, UTC
from messagepro_api import MessageProAPI
from pdf_generator import PDFGenerator
from io import BytesIO
import os
import logging

logger = logging.getLogger(__name__)

class ScheduledReportsManager:
    """Gestionnaire de rapports automatiques"""
    
    def __init__(self, app: Flask = None):
        self.app = app
        self.scheduler = BackgroundScheduler()
        self.scheduler.start()
        self.pdf_generator = PDFGenerator()
        
    def init_app(self, app: Flask):
        """Initialise l'application Flask"""
        self.app = app
        
    def generate_stock_inventory_pdf(self, depot_id=None, period='all', currency='GNF'):
        """Génère un PDF d'inventaire de stock"""
        from stocks import generate_stock_summary_pdf_data
        from pdf_generator import PDFGenerator
        
        with self.app.app_context():
            try:
                # Générer les données du rapport
                stock_data = generate_stock_summary_pdf_data(
                    depot_id=depot_id,
                    period=period,
                    currency=currency
                )
                
                if not stock_data:
                    return None
                
                # Générer le PDF
                pdf_gen = PDFGenerator()
                
                # Déterminer le taux de change
                exchange_rate = None
                if currency == 'USD':
                    exchange_rate = 8500.0
                elif currency == 'EUR':
                    exchange_rate = 9200.0
                elif currency == 'XOF':
                    exchange_rate = 14.0
                
                pdf_buffer = pdf_gen.generate_stock_summary_pdf(
                    stock_data, 
                    currency=currency, 
                    exchange_rate=exchange_rate
                )
                
                return pdf_buffer
            except Exception as e:
                logger.error(f"Erreur lors de la génération du PDF d'inventaire: {e}")
                import traceback
                traceback.print_exc()
                return None
    
    def send_report_via_whatsapp(self, pdf_buffer, recipients, account_id, message="Rapport automatique"):
        """Envoie un PDF via WhatsApp via Message Pro"""
        try:
            api = MessageProAPI()
            
            # Convertir le buffer PDF en bytes
            if hasattr(pdf_buffer, 'getvalue'):
                pdf_bytes = pdf_buffer.getvalue()
            elif hasattr(pdf_buffer, 'read'):
                pdf_bytes = pdf_buffer.read()
            else:
                pdf_bytes = pdf_buffer
            
            # Nettoyer la liste des destinataires
            recipients = [r.strip() for r in recipients if r.strip()]
            
            # Pour chaque destinataire
            for recipient in recipients:
                try:
                    # Créer un nouveau BytesIO pour chaque envoi (car il est consommé)
                    pdf_file = BytesIO(pdf_bytes)
                    
                    # Envoyer le document via WhatsApp
                    result = api.send_whatsapp(
                        account=account_id,
                        recipient=recipient.strip(),
                        message=message,
                        message_type='document',
                        document_file=pdf_file,
                        document_name=f"rapport_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}.pdf",
                        document_type='pdf',
                        priority=2
                    )
                    
                    if result.get('status') == 200:
                        logger.info(f"Rapport envoyé avec succès à {recipient}")
                    else:
                        logger.error(f"Erreur lors de l'envoi à {recipient}: {result.get('message')}")
                        
                except Exception as e:
                    logger.error(f"Erreur lors de l'envoi à {recipient}: {e}")
                    import traceback
                    traceback.print_exc()
                    
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi du rapport: {e}")
            import traceback
            traceback.print_exc()
    
    def execute_scheduled_report(self, report_config):
        """Exécute un rapport planifié"""
        from models import ScheduledReport
        
        with self.app.app_context():
            try:
                # Générer le PDF selon le type de rapport
                pdf_buffer = None
                
                if report_config.report_type == 'stock_inventory':
                    pdf_buffer = self.generate_stock_inventory_pdf(
                        depot_id=report_config.depot_id,
                        period=report_config.period or 'all',
                        currency=report_config.currency or 'GNF'
                    )
                elif report_config.report_type == 'stock_summary':
                    pdf_buffer = self.generate_stock_inventory_pdf(
                        depot_id=report_config.depot_id,
                        period=report_config.period or 'all',
                        currency=report_config.currency or 'GNF'
                    )
                elif report_config.report_type == 'orders_summary':
                    pdf_buffer = self.generate_orders_summary_pdf(
                        period=report_config.period or 'all',
                        currency=report_config.currency or 'GNF'
                    )
                elif report_config.report_type == 'sales_statistics':
                    pdf_buffer = self.generate_sales_statistics_pdf(
                        period=report_config.period or 'all',
                        currency=report_config.currency or 'GNF'
                    )
                elif report_config.report_type == 'stock_alerts':
                    pdf_buffer = self.generate_stock_alerts_pdf(
                        depot_id=report_config.depot_id
                    )
                elif report_config.report_type == 'daily_summary':
                    pdf_buffer = self.generate_daily_summary_pdf(
                        depot_id=report_config.depot_id,
                        currency=report_config.currency or 'GNF'
                    )
                
                if pdf_buffer:
                    # Récupérer les destinataires
                    recipients = []
                    if report_config.recipients:
                        recipients = [r.strip() for r in report_config.recipients.split(',') if r.strip()]
                    
                    # Récupérer les membres des groupes
                    if report_config.group_ids and report_config.group_ids.strip():
                        api = MessageProAPI()
                        groups = [g.strip() for g in report_config.group_ids.split(',') if g.strip()]
                        for group_id in groups:
                            try:
                                # Récupérer les contacts du groupe
                                contacts_result = api.get_contacts_by_group(int(group_id), limit=1000, page=1)
                                if contacts_result and contacts_result.get('status') == 200:
                                    contacts_data = contacts_result.get('data', [])
                                    if isinstance(contacts_data, list):
                                        for contact in contacts_data:
                                            if contact.get('phone'):
                                                phone = contact.get('phone').strip()
                                                if phone and phone not in recipients:
                                                    recipients.append(phone)
                            except Exception as e:
                                logger.error(f"Erreur lors de la récupération du groupe {group_id}: {e}")
                                import traceback
                                traceback.print_exc()
                    
                    if not recipients:
                        error_msg = f"Aucun destinataire trouvé pour le rapport {report_config.id}"
                        logger.error(error_msg)
                        report_config.last_error = error_msg
                        from models import db
                        db.session.commit()
                        return
                    
                    # Envoyer le rapport
                    self.send_report_via_whatsapp(
                        pdf_buffer=pdf_buffer,
                        recipients=recipients,
                        account_id=report_config.whatsapp_account_id,
                        message=report_config.message or "Rapport automatique"
                    )
                    
                    # Mettre à jour la dernière exécution
                    report_config.last_run = datetime.now(UTC)
                    report_config.next_run = self.calculate_next_run(report_config.schedule_type, report_config.schedule)
                    report_config.run_count = (report_config.run_count or 0) + 1
                    report_config.last_error = None
                    from models import db
                    db.session.commit()
                    
                    logger.info(f"Rapport {report_config.id} exécuté avec succès")
                else:
                    error_msg = f"Impossible de générer le PDF pour le rapport {report_config.id}"
                    logger.error(error_msg)
                    report_config.last_error = error_msg
                    from models import db
                    db.session.commit()
                    
            except Exception as e:
                error_msg = f"Erreur lors de l'exécution du rapport {report_config.id}: {e}"
                logger.error(error_msg)
                import traceback
                traceback.print_exc()
                report_config.last_error = error_msg
                from models import db
                db.session.commit()
    
    def calculate_next_run(self, schedule_type, schedule):
        """Calcule la prochaine exécution selon le planning"""
        now = datetime.now(UTC)
        
        if schedule_type == 'daily':
            # Format: "HH:MM"
            hour, minute = map(int, schedule.split(':'))
            next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if next_run <= now:
                from datetime import timedelta
                next_run += timedelta(days=1)
            return next_run
        
        elif schedule_type == 'weekly':
            # Format: "DAY HH:MM" (ex: "MON 18:00")
            day_str, time_str = schedule.split(' ', 1)
            hour, minute = map(int, time_str.split(':'))
            day_map = {'MON': 0, 'TUE': 1, 'WED': 2, 'THU': 3, 'FRI': 4, 'SAT': 5, 'SUN': 6}
            target_day = day_map.get(day_str.upper(), 0)
            
            current_day = now.weekday()
            days_ahead = target_day - current_day
            
            if days_ahead <= 0:
                days_ahead += 7
            
            from datetime import timedelta
            next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0) + timedelta(days=days_ahead)
            return next_run
        
        elif schedule_type == 'monthly':
            # Format: "DD HH:MM" (ex: "01 18:00" pour le 1er de chaque mois)
            day_str, time_str = schedule.split(' ', 1)
            day = int(day_str)
            hour, minute = map(int, time_str.split(':'))
            
            next_run = now.replace(day=day, hour=hour, minute=minute, second=0, microsecond=0)
            if next_run <= now:
                # Passer au mois suivant
                from datetime import timedelta
                if now.month == 12:
                    next_run = next_run.replace(year=now.year + 1, month=1)
                else:
                    next_run = next_run.replace(month=now.month + 1)
            
            return next_run
        
        return now
    
    def schedule_report(self, report_config):
        """Planifie un rapport"""
        try:
            # Vérifier que le rapport est actif
            if not report_config.is_active:
                logger.info(f"Rapport {report_config.id} est inactif, non planifié")
                return False
            
            # Créer un trigger selon le planning
            if report_config.schedule_type == 'daily':
                hour, minute = map(int, report_config.schedule.split(':'))
                trigger = CronTrigger(hour=hour, minute=minute)
            elif report_config.schedule_type == 'weekly':
                # Format: "DAY HH:MM" (ex: "MON 18:00")
                day, time = report_config.schedule.split(' ', 1)
                hour, minute = map(int, time.split(':'))
                day_map = {'MON': 0, 'TUE': 1, 'WED': 2, 'THU': 3, 'FRI': 4, 'SAT': 5, 'SUN': 6}
                trigger = CronTrigger(day_of_week=day_map.get(day.upper(), 0), hour=hour, minute=minute)
            elif report_config.schedule_type == 'monthly':
                # Format: "DD HH:MM" (ex: "01 18:00" pour le 1er de chaque mois)
                day_str, time_str = report_config.schedule.split(' ', 1)
                day = int(day_str)
                hour, minute = map(int, time_str.split(':'))
                trigger = CronTrigger(day=day, hour=hour, minute=minute)
            else:
                logger.error(f"Type de planning non supporté: {report_config.schedule_type}")
                return False
            
            # Ajouter la tâche au scheduler
            self.scheduler.add_job(
                func=self.execute_scheduled_report,
                trigger=trigger,
                args=[report_config],
                id=f"report_{report_config.id}",
                replace_existing=True
            )
            
            logger.info(f"Rapport {report_config.id} planifié avec succès")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de la planification du rapport {report_config.id}: {e}")
            return False
    
    def unschedule_report(self, report_id):
        """Annule la planification d'un rapport"""
        try:
            self.scheduler.remove_job(f"report_{report_id}")
            logger.info(f"Rapport {report_id} désactivé")
            return True
        except Exception as e:
            logger.error(f"Erreur lors de la désactivation du rapport {report_id}: {e}")
            return False
    
    def load_all_scheduled_reports(self):
        """Charge tous les rapports planifiés actifs"""
        from models import ScheduledReport
        
        with self.app.app_context():
            active_reports = ScheduledReport.query.filter_by(is_active=True).all()
            for report in active_reports:
                self.schedule_report(report)
            logger.info(f"{len(active_reports)} rapports planifiés chargés")

# Instance globale
scheduled_reports_manager = ScheduledReportsManager()

