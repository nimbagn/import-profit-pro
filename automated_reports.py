#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module de gestion des rapports automatiques
Interface Flask pour configurer et gérer les rapports automatiques
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_file
from flask_login import login_required, current_user
from datetime import datetime, UTC, timedelta
from models import db, ScheduledReport, Depot
from auth import has_permission
from messagepro_api import MessageProAPI
from pdf_generator import PDFGenerator
from io import BytesIO
import logging

logger = logging.getLogger(__name__)

automated_reports_bp = Blueprint('automated_reports', __name__, url_prefix='/automated-reports')

# =========================================================
# ROUTES - LISTE ET GESTION
# =========================================================

@automated_reports_bp.route('/')
@login_required
def reports_list():
    """Liste des rapports automatiques"""
    if not has_permission(current_user, 'messaging.read'):
        flash('Vous n\'avez pas la permission d\'accéder aux rapports automatiques', 'error')
        return redirect(url_for('index'))
    
    reports = ScheduledReport.query.order_by(ScheduledReport.created_at.desc()).all()
    return render_template('automated_reports/list.html', reports=reports)

@automated_reports_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_report():
    """Créer un nouveau rapport automatique"""
    if not has_permission(current_user, 'messaging.read'):
        flash('Vous n\'avez pas la permission de créer des rapports automatiques', 'error')
        return redirect(url_for('automated_reports.reports_list'))
    
    if request.method == 'POST':
        try:
            # Récupérer les données du formulaire
            name = request.form.get('name', '').strip()
            description = request.form.get('description', '').strip()
            report_type = request.form.get('report_type', 'stock_inventory')
            schedule_type = request.form.get('schedule_type', 'daily')
            schedule = request.form.get('schedule', '').strip()
            
            depot_id = request.form.get('depot_id', type=int) or None
            period = request.form.get('period', 'all')
            currency = request.form.get('currency', 'GNF')
            
            whatsapp_account_id = request.form.get('whatsapp_account_id', '').strip()
            recipients = request.form.get('recipients', '').strip()
            group_ids = request.form.get('group_ids', '').strip()
            message = request.form.get('message', '').strip()
            
            # Validation
            if not name or not schedule or not whatsapp_account_id:
                flash('Le nom, le planning et le compte WhatsApp sont obligatoires', 'error')
                return redirect(url_for('automated_reports.create_report'))
            
            if not recipients and not group_ids:
                flash('Vous devez spécifier au moins un destinataire ou un groupe', 'error')
                return redirect(url_for('automated_reports.create_report'))
            
            # Calculer next_run
            next_run = calculate_next_run(schedule_type, schedule)
            
            # Créer le rapport
            report = ScheduledReport(
                name=name,
                description=description,
                report_type=report_type,
                schedule_type=schedule_type,
                schedule=schedule,
                depot_id=depot_id,
                period=period,
                currency=currency,
                whatsapp_account_id=whatsapp_account_id,
                recipients=recipients,
                group_ids=group_ids,
                message=message or f"Rapport automatique: {name}",
                next_run=next_run,
                created_by_id=current_user.id,
                is_active=True
            )
            
            db.session.add(report)
            db.session.commit()
            
            # Planifier le rapport
            from scheduled_reports import scheduled_reports_manager
            scheduled_reports_manager.schedule_report(report)
            
            flash('Rapport automatique créé avec succès!', 'success')
            return redirect(url_for('automated_reports.reports_list'))
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Erreur lors de la création du rapport: {e}")
            flash(f'Erreur lors de la création: {str(e)}', 'error')
            return redirect(url_for('automated_reports.create_report'))
    
    # GET - Afficher le formulaire
    depots = Depot.query.filter_by(is_active=True).order_by(Depot.name).all()
    
    # Récupérer les comptes WhatsApp disponibles
    accounts = []
    try:
        api = MessageProAPI()
        accounts_result = api.get_whatsapp_accounts(limit=100)
        if accounts_result and accounts_result.get('status') == 200:
            accounts = accounts_result.get('data', [])
        elif accounts_result and isinstance(accounts_result.get('data'), list):
            accounts = accounts_result.get('data', [])
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des comptes WhatsApp: {e}")
        accounts = []
    
    return render_template('automated_reports/create.html', 
                         depots=depots, 
                         accounts=accounts)

@automated_reports_bp.route('/<int:report_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_report(report_id):
    """Modifier un rapport automatique"""
    if not has_permission(current_user, 'messaging.read'):
        flash('Vous n\'avez pas la permission de modifier des rapports automatiques', 'error')
        return redirect(url_for('automated_reports.reports_list'))
    
    report = ScheduledReport.query.get_or_404(report_id)
    
    if request.method == 'POST':
        try:
            report.name = request.form.get('name', '').strip()
            report.description = request.form.get('description', '').strip()
            report.report_type = request.form.get('report_type', 'stock_inventory')
            report.schedule_type = request.form.get('schedule_type', 'daily')
            report.schedule = request.form.get('schedule', '').strip()
            
            depot_id = request.form.get('depot_id', type=int) or None
            report.depot_id = depot_id
            report.period = request.form.get('period', 'all')
            report.currency = request.form.get('currency', 'GNF')
            
            report.whatsapp_account_id = request.form.get('whatsapp_account_id', '').strip()
            report.recipients = request.form.get('recipients', '').strip()
            report.group_ids = request.form.get('group_ids', '').strip()
            report.message = request.form.get('message', '').strip()
            
            report.next_run = calculate_next_run(report.schedule_type, report.schedule)
            
            db.session.commit()
            
            # Replanifier le rapport
            from scheduled_reports import scheduled_reports_manager
            scheduled_reports_manager.unschedule_report(report.id)
            if report.is_active:
                scheduled_reports_manager.schedule_report(report)
            
            flash('Rapport automatique modifié avec succès!', 'success')
            return redirect(url_for('automated_reports.reports_list'))
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Erreur lors de la modification du rapport: {e}")
            flash(f'Erreur lors de la modification: {str(e)}', 'error')
    
    depots = Depot.query.filter_by(is_active=True).order_by(Depot.name).all()
    
    accounts = []
    try:
        api = MessageProAPI()
        accounts_result = api.get_whatsapp_accounts(limit=100)
        if accounts_result and accounts_result.get('status') == 200:
            accounts = accounts_result.get('data', [])
        elif accounts_result and isinstance(accounts_result.get('data'), list):
            accounts = accounts_result.get('data', [])
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des comptes WhatsApp: {e}")
        accounts = []
    
    return render_template('automated_reports/edit.html', 
                         report=report, 
                         depots=depots, 
                         accounts=accounts)

@automated_reports_bp.route('/<int:report_id>/toggle', methods=['POST'])
@login_required
def toggle_report(report_id):
    """Activer/Désactiver un rapport automatique"""
    if not has_permission(current_user, 'messaging.read'):
        return jsonify({'error': 'Permission refusée'}), 403
    
    report = ScheduledReport.query.get_or_404(report_id)
    report.is_active = not report.is_active
    
    from scheduled_reports import scheduled_reports_manager
    if report.is_active:
        scheduled_reports_manager.schedule_report(report)
    else:
        scheduled_reports_manager.unschedule_report(report.id)
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'is_active': report.is_active,
        'message': 'Rapport activé' if report.is_active else 'Rapport désactivé'
    })

@automated_reports_bp.route('/<int:report_id>/delete', methods=['POST'])
@login_required
def delete_report(report_id):
    """Supprimer un rapport automatique"""
    if not has_permission(current_user, 'messaging.read'):
        flash('Vous n\'avez pas la permission de supprimer des rapports automatiques', 'error')
        return redirect(url_for('automated_reports.reports_list'))
    
    report = ScheduledReport.query.get_or_404(report_id)
    
    from scheduled_reports import scheduled_reports_manager
    scheduled_reports_manager.unschedule_report(report.id)
    
    db.session.delete(report)
    db.session.commit()
    
    flash('Rapport automatique supprimé avec succès!', 'success')
    return redirect(url_for('automated_reports.reports_list'))

@automated_reports_bp.route('/<int:report_id>/test', methods=['POST'])
@login_required
def test_report(report_id):
    """Tester l'envoi d'un rapport (envoi immédiat)"""
    if not has_permission(current_user, 'messaging.read'):
        return jsonify({'error': 'Permission refusée'}), 403
    
    report = ScheduledReport.query.get_or_404(report_id)
    
    try:
        from scheduled_reports import scheduled_reports_manager
        scheduled_reports_manager.execute_scheduled_report(report)
        
        return jsonify({
            'success': True,
            'message': 'Rapport test envoyé avec succès!'
        })
    except Exception as e:
        logger.error(f"Erreur lors du test du rapport: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

def calculate_next_run(schedule_type, schedule):
    """Calcule la prochaine date d'exécution"""
    now = datetime.now(UTC)
    
    if schedule_type == 'daily':
        # Format: "HH:MM"
        hour, minute = map(int, schedule.split(':'))
        next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if next_run <= now:
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
            if now.month == 12:
                next_run = next_run.replace(year=now.year + 1, month=1)
            else:
                next_run = next_run.replace(month=now.month + 1)
        
        return next_run
    
    return now

