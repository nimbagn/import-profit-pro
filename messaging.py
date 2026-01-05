#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module Messaging - Intégration Message Pro
Gestion de l'envoi de SMS, WhatsApp et OTP via l'API Message Pro
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from datetime import datetime
from messagepro_api import MessageProAPI
from auth import has_permission
import os

# Créer le blueprint
messaging_bp = Blueprint('messaging', __name__, url_prefix='/messaging')

# =========================================================
# ROUTES - DASHBOARD
# =========================================================

@messaging_bp.route('/')
@login_required
def dashboard():
    """Tableau de bord messaging"""
    if not has_permission(current_user, 'messaging.read'):
        flash('Vous n\'avez pas la permission d\'accéder à la messagerie', 'error')
        return redirect(url_for('index'))
    
    try:
        api = MessageProAPI()
        
        # Récupérer les informations du compte
        credits_info = api.get_credits()
        subscription_info = api.get_subscription()
        
        # Récupérer les statistiques récentes
        sent_messages = api.get_sent_messages(limit=5)
        received_messages = api.get_received_messages(limit=5)
        
        return render_template('messaging/dashboard.html',
                             credits_info=credits_info,
                             subscription_info=subscription_info,
                             sent_messages=sent_messages.get('data', []),
                             received_messages=received_messages.get('data', []))
    except ValueError as e:
        flash(f'Configuration manquante: {str(e)}', 'error')
        return render_template('messaging/dashboard.html',
                             credits_info=None,
                             subscription_info=None,
                             sent_messages=[],
                             received_messages=[])
    except Exception as e:
        flash(f'Erreur lors du chargement: {str(e)}', 'error')
        return render_template('messaging/dashboard.html',
                             credits_info=None,
                             subscription_info=None,
                             sent_messages=[],
                             received_messages=[])

# =========================================================
# ROUTES - SMS
# =========================================================

@messaging_bp.route('/sms/send', methods=['GET', 'POST'])
@login_required
def send_sms():
    """Envoyer un SMS"""
    if not has_permission(current_user, 'messaging.send_sms'):
        flash('Vous n\'avez pas la permission d\'envoyer des SMS', 'error')
        return redirect(url_for('messaging.dashboard'))
    
    try:
        api = MessageProAPI()
        
        if request.method == 'POST':
            phone = request.form.get('phone', '').strip()
            message = request.form.get('message', '').strip()
            mode = request.form.get('mode', 'devices')
            device = request.form.get('device', '').strip() or None
            gateway = request.form.get('gateway', '').strip() or None
            sim = request.form.get('sim')
            sim = int(sim) if sim else None
            priority = int(request.form.get('priority', 0))
            
            if not phone or not message:
                flash('Le numéro et le message sont obligatoires', 'error')
            else:
                result = api.send_sms(
                    phone=phone,
                    message=message,
                    mode=mode,
                    device=device,
                    gateway=gateway,
                    sim=sim,
                    priority=priority
                )
                
                if result.get('status') == 200:
                    flash(f"SMS envoyé avec succès! ID: {result.get('data', {}).get('messageId', 'N/A')}", 'success')
                    return redirect(url_for('messaging.send_sms'))
                else:
                    flash(f"Erreur: {result.get('message', 'Erreur inconnue')}", 'error')
        
        # Récupérer les appareils et gateways pour le formulaire
        devices = api.get_devices(limit=100)
        rates = api.get_rates()
        
        return render_template('messaging/send_sms.html',
                             devices=devices.get('data', []),
                             rates=rates.get('data', {}))
    except ValueError as e:
        flash(f'Configuration manquante: {str(e)}', 'error')
        return render_template('messaging/send_sms.html', devices=[], rates={})
    except Exception as e:
        flash(f'Erreur: {str(e)}', 'error')
        return render_template('messaging/send_sms.html', devices=[], rates={})

@messaging_bp.route('/sms/bulk', methods=['GET', 'POST'])
@login_required
def send_bulk_sms():
    """Envoyer des SMS en masse"""
    if not has_permission(current_user, 'messaging.send_sms'):
        flash('Vous n\'avez pas la permission d\'envoyer des SMS', 'error')
        return redirect(url_for('messaging.dashboard'))
    
    try:
        api = MessageProAPI()
        
        if request.method == 'POST':
            campaign = request.form.get('campaign', '').strip()
            message = request.form.get('message', '').strip()
            mode = request.form.get('mode', 'devices')
            numbers = request.form.get('numbers', '').strip() or None
            # Récupérer les groupes depuis les checkboxes
            group_ids = request.form.getlist('group_ids')
            groups = ','.join(group_ids) if group_ids else None
            device = request.form.get('device', '').strip() or None
            gateway = request.form.get('gateway', '').strip() or None
            sim = request.form.get('sim')
            sim = int(sim) if sim else None
            priority = int(request.form.get('priority', 0))
            
            if not campaign or not message:
                flash('Le nom de campagne et le message sont obligatoires', 'error')
            elif not numbers and not groups:
                flash('Vous devez spécifier des numéros ou des groupes', 'error')
            else:
                result = api.send_bulk_sms(
                    campaign=campaign,
                    message=message,
                    mode=mode,
                    numbers=numbers,
                    groups=groups,
                    device=device,
                    gateway=gateway,
                    sim=sim,
                    priority=priority
                )
                
                if result.get('status') == 200:
                    flash(f"Campagne SMS créée avec succès! ID: {result.get('data', {}).get('messageId', 'N/A')}", 'success')
                    return redirect(url_for('messaging.send_bulk_sms'))
                else:
                    flash(f"Erreur: {result.get('message', 'Erreur inconnue')}", 'error')
        
        # Récupérer les données pour le formulaire
        devices = api.get_devices(limit=100)
        rates = api.get_rates()
        groups = api.get_groups(limit=100)
        
        return render_template('messaging/send_bulk_sms.html',
                             devices=devices.get('data', []),
                             rates=rates.get('data', {}),
                             groups=groups.get('data', []))
    except ValueError as e:
        flash(f'Configuration manquante: {str(e)}', 'error')
        return render_template('messaging/send_bulk_sms.html', devices=[], rates={}, groups=[])
    except Exception as e:
        flash(f'Erreur: {str(e)}', 'error')
        return render_template('messaging/send_bulk_sms.html', devices=[], rates={}, groups=[])

@messaging_bp.route('/sms/history')
@login_required
def sms_history():
    """Historique des SMS"""
    if not has_permission(current_user, 'messaging.read'):
        flash('Vous n\'avez pas la permission d\'accéder à l\'historique', 'error')
        return redirect(url_for('messaging.dashboard'))
    
    try:
        api = MessageProAPI()
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 20))
        message_type = request.args.get('type', 'sent')  # sent, received, pending
        
        if message_type == 'sent':
            messages = api.get_sent_messages(limit=limit, page=page)
        elif message_type == 'received':
            messages = api.get_received_messages(limit=limit, page=page)
        else:
            messages = api.get_pending_messages(limit=limit, page=page)
        
        return render_template('messaging/sms_history.html',
                             messages=messages.get('data', []),
                             message_type=message_type,
                             page=page,
                             limit=limit)
    except Exception as e:
        flash(f'Erreur: {str(e)}', 'error')
        return render_template('messaging/sms_history.html', messages=[], message_type='sent', page=1, limit=20)

# =========================================================
# ROUTES - WHATSAPP
# =========================================================

@messaging_bp.route('/whatsapp/send', methods=['GET', 'POST'])
@login_required
def send_whatsapp():
    """Envoyer un message WhatsApp"""
    if not has_permission(current_user, 'messaging.send_whatsapp'):
        flash('Vous n\'avez pas la permission d\'envoyer des messages WhatsApp', 'error')
        return redirect(url_for('messaging.dashboard'))
    
    try:
        api = MessageProAPI()
        
        if request.method == 'POST':
            account = request.form.get('account', '').strip()
            recipient = request.form.get('recipient', '').strip()
            message = request.form.get('message', '').strip()
            message_type = request.form.get('type', 'text')
            priority = int(request.form.get('priority', 2))
            
            if not account or not recipient or not message:
                flash('Le compte, le destinataire et le message sont obligatoires', 'error')
            else:
                # Gérer les fichiers si type media ou document
                files = None
                if message_type == 'media' and 'media_file' in request.files:
                    media_file = request.files['media_file']
                    if media_file.filename:
                        files = {'media_file': (media_file.filename, media_file.stream, media_file.content_type)}
                elif message_type == 'document' and 'document_file' in request.files:
                    doc_file = request.files['document_file']
                    if doc_file.filename:
                        files = {'document_file': (doc_file.filename, doc_file.stream, doc_file.content_type)}
                
                result = api.send_whatsapp(
                    account=account,
                    recipient=recipient,
                    message=message,
                    message_type=message_type,
                    priority=priority,
                    media_file=files.get('media_file') if files else None,
                    document_file=files.get('document_file') if files else None
                )
                
                if result.get('status') == 200:
                    flash(f"Message WhatsApp envoyé avec succès! ID: {result.get('data', {}).get('messageId', 'N/A')}", 'success')
                    return redirect(url_for('messaging.send_whatsapp'))
                else:
                    flash(f"Erreur: {result.get('message', 'Erreur inconnue')}", 'error')
        
        # Récupérer les comptes WhatsApp
        accounts = api.get_whatsapp_accounts(limit=100)
        
        return render_template('messaging/send_whatsapp.html',
                             accounts=accounts.get('data', []))
    except ValueError as e:
        flash(f'Configuration manquante: {str(e)}', 'error')
        return render_template('messaging/send_whatsapp.html', accounts=[])
    except Exception as e:
        flash(f'Erreur: {str(e)}', 'error')
        return render_template('messaging/send_whatsapp.html', accounts=[])

@messaging_bp.route('/whatsapp/history')
@login_required
def whatsapp_history():
    """Historique des messages WhatsApp"""
    if not has_permission(current_user, 'messaging.read'):
        flash('Vous n\'avez pas la permission d\'accéder à l\'historique', 'error')
        return redirect(url_for('messaging.dashboard'))
    
    try:
        api = MessageProAPI()
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 20))
        message_type = request.args.get('type', 'sent')  # sent, received
        
        if message_type == 'sent':
            messages = api.get_sent_chats(limit=limit, page=page)
        else:
            messages = api.get_received_chats(limit=limit, page=page)
        
        return render_template('messaging/whatsapp_history.html',
                             messages=messages.get('data', []),
                             message_type=message_type,
                             page=page,
                             limit=limit)
    except Exception as e:
        flash(f'Erreur: {str(e)}', 'error')
        return render_template('messaging/whatsapp_history.html', messages=[], message_type='sent', page=1, limit=20)

# =========================================================
# ROUTES - OTP
# =========================================================

@messaging_bp.route('/otp/send', methods=['GET', 'POST'])
@login_required
def send_otp():
    """Envoyer un code OTP"""
    if not has_permission(current_user, 'messaging.send_otp'):
        flash('Vous n\'avez pas la permission d\'envoyer des OTP', 'error')
        return redirect(url_for('messaging.dashboard'))
    
    try:
        api = MessageProAPI()
        
        if request.method == 'POST':
            phone = request.form.get('phone', '').strip()
            message = request.form.get('message', '').strip()
            message_type = request.form.get('type', 'sms')
            expire = int(request.form.get('expire', 300))
            priority = int(request.form.get('priority', 2))
            mode = request.form.get('mode', '').strip() or None
            device = request.form.get('device', '').strip() or None
            gateway = request.form.get('gateway', '').strip() or None
            sim = request.form.get('sim')
            sim = int(sim) if sim else None
            account = request.form.get('account', '').strip() or None
            
            if not phone or not message:
                flash('Le numéro et le message sont obligatoires', 'error')
            elif '{{otp}}' not in message:
                flash('Le message doit contenir {{otp}} pour le code OTP', 'error')
            else:
                result = api.send_otp(
                    phone=phone,
                    message=message,
                    message_type=message_type,
                    expire=expire,
                    priority=priority,
                    account=account,
                    mode=mode,
                    device=device,
                    gateway=gateway,
                    sim=sim
                )
                
                if result.get('status') == 200:
                    otp_code = result.get('data', {}).get('otp', 'N/A')
                    flash(f"OTP envoyé avec succès! Code: {otp_code}", 'success')
                    return redirect(url_for('messaging.send_otp'))
                else:
                    flash(f"Erreur: {result.get('message', 'Erreur inconnue')}", 'error')
        
        # Récupérer les données pour le formulaire
        devices = api.get_devices(limit=100)
        rates = api.get_rates()
        accounts = api.get_whatsapp_accounts(limit=100)
        
        return render_template('messaging/send_otp.html',
                             devices=devices.get('data', []),
                             rates=rates.get('data', {}),
                             accounts=accounts.get('data', []))
    except ValueError as e:
        flash(f'Configuration manquante: {str(e)}', 'error')
        return render_template('messaging/send_otp.html', devices=[], rates={}, accounts=[])
    except Exception as e:
        flash(f'Erreur: {str(e)}', 'error')
        return render_template('messaging/send_otp.html', devices=[], rates={}, accounts=[])

# =========================================================
# ROUTES - CONTACTS
# =========================================================

@messaging_bp.route('/contacts')
@login_required
def contacts_list():
    """Liste des contacts"""
    if not has_permission(current_user, 'messaging.read'):
        flash('Vous n\'avez pas la permission d\'accéder aux contacts', 'error')
        return redirect(url_for('messaging.dashboard'))
    
    try:
        api = MessageProAPI()
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 20))
        
        contacts = api.get_contacts(limit=limit, page=page)
        groups = api.get_groups(limit=100)
        
        return render_template('messaging/contacts.html',
                             contacts=contacts.get('data', []),
                             groups=groups.get('data', []),
                             page=page,
                             limit=limit)
    except Exception as e:
        flash(f'Erreur: {str(e)}', 'error')
        return render_template('messaging/contacts.html', contacts=[], groups=[], page=1, limit=20)

@messaging_bp.route('/contacts/create', methods=['GET', 'POST'])
@login_required
def create_contact():
    """Créer un contact"""
    if not has_permission(current_user, 'messaging.manage_contacts'):
        flash('Vous n\'avez pas la permission de gérer les contacts', 'error')
        return redirect(url_for('messaging.contacts_list'))
    
    try:
        api = MessageProAPI()
        
        if request.method == 'POST':
            phone = request.form.get('phone', '').strip()
            name = request.form.get('name', '').strip()
            groups = request.form.get('groups', '').strip()
            
            if not phone or not name:
                flash('Le numéro et le nom sont obligatoires', 'error')
            else:
                result = api.create_contact(phone=phone, name=name, groups=groups)
                
                if result.get('status') == 200:
                    flash('Contact créé avec succès!', 'success')
                    return redirect(url_for('messaging.contacts_list'))
                else:
                    flash(f"Erreur: {result.get('message', 'Erreur inconnue')}", 'error')
        
        groups = api.get_groups(limit=100)
        return render_template('messaging/create_contact.html', groups=groups.get('data', []))
    except Exception as e:
        flash(f'Erreur: {str(e)}', 'error')
        groups = api.get_groups(limit=100) if 'api' in locals() else []
        return render_template('messaging/create_contact.html', groups=groups.get('data', []) if isinstance(groups, dict) else [])

@messaging_bp.route('/contacts/<int:contact_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_contact(contact_id):
    """Modifier un contact"""
    if not has_permission(current_user, 'messaging.manage_contacts'):
        flash('Vous n\'avez pas la permission de gérer les contacts', 'error')
        return redirect(url_for('messaging.contacts_list'))
    
    try:
        api = MessageProAPI()
        
        # Récupérer le contact existant
        contacts = api.get_contacts(limit=1000, page=1)
        contact = None
        for c in contacts.get('data', []):
            if c.get('id') == contact_id:
                contact = c
                break
        
        if not contact:
            flash('Contact introuvable', 'error')
            return redirect(url_for('messaging.contacts_list'))
        
        if request.method == 'POST':
            phone = request.form.get('phone', '').strip()
            name = request.form.get('name', '').strip()
            groups = request.form.get('groups', '').strip()
            
            if not phone or not name:
                flash('Le numéro et le nom sont obligatoires', 'error')
            else:
                # L'API Message Pro utilise create/contact pour créer ou mettre à jour
                result = api.create_contact(phone=phone, name=name, groups=groups)
                
                if result.get('status') == 200:
                    flash('Contact modifié avec succès!', 'success')
                    return redirect(url_for('messaging.contacts_list'))
                else:
                    flash(f"Erreur: {result.get('message', 'Erreur inconnue')}", 'error')
        
        groups = api.get_groups(limit=100)
        return render_template('messaging/edit_contact.html', 
                             contact=contact, 
                             groups=groups.get('data', []))
    except Exception as e:
        flash(f'Erreur: {str(e)}', 'error')
        return redirect(url_for('messaging.contacts_list'))

@messaging_bp.route('/contacts/<int:contact_id>/delete', methods=['POST', 'GET'])
@login_required
def delete_contact(contact_id):
    """Supprimer un contact"""
    if not has_permission(current_user, 'messaging.manage_contacts'):
        flash('Vous n\'avez pas la permission de gérer les contacts', 'error')
        return redirect(url_for('messaging.contacts_list'))
    
    try:
        api = MessageProAPI()
        result = api.delete_contact(contact_id)
        
        if result.get('status') == 200:
            flash('Contact supprimé avec succès!', 'success')
        else:
            flash(f"Erreur: {result.get('message', 'Erreur inconnue')}", 'error')
    except Exception as e:
        flash(f'Erreur: {str(e)}', 'error')
    
    return redirect(url_for('messaging.contacts_list'))

# =========================================================
# ROUTES API JSON
# =========================================================

@messaging_bp.route('/api/credits')
@login_required
def api_credits():
    """API JSON pour récupérer les crédits"""
    if not has_permission(current_user, 'messaging.read'):
        return jsonify({'error': 'Permission refusée'}), 403
    
    try:
        api = MessageProAPI()
        result = api.get_credits()
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@messaging_bp.route('/api/verify-otp')
@login_required
def api_verify_otp():
    """API JSON pour vérifier un OTP"""
    if not has_permission(current_user, 'messaging.send_otp'):
        return jsonify({'error': 'Permission refusée'}), 403
    
    otp = request.args.get('otp')
    if not otp:
        return jsonify({'error': 'OTP requis'}), 400
    
    try:
        api = MessageProAPI()
        result = api.verify_otp(otp)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# =========================================================
# ROUTES - CONFIGURATION API
# =========================================================

@messaging_bp.route('/config', methods=['GET', 'POST'])
@login_required
def api_config():
    """Configuration de l'API Message Pro"""
    if not has_permission(current_user, 'messaging.read'):
        flash('Vous n\'avez pas la permission d\'accéder à cette page', 'error')
        return redirect(url_for('index'))
    
    from models import ApiConfig, db
    
    # Récupérer la configuration actuelle
    config = ApiConfig.query.filter_by(api_name='messagepro').first()
    api_secret = config.api_secret if config else None
    is_configured = bool(api_secret)
    
    # Tester la connexion si configurée
    connection_status = None
    if is_configured:
        try:
            api = MessageProAPI(api_secret=api_secret)
            credits = api.get_credits()
            if credits.get('status') == 200:
                connection_status = {
                    'success': True,
                    'message': 'Connexion réussie',
                    'credits': credits.get('data', {})
                }
            else:
                connection_status = {
                    'success': False,
                    'message': credits.get('message', 'Erreur de connexion')
                }
        except Exception as e:
            connection_status = {
                'success': False,
                'message': f'Erreur: {str(e)}'
            }
    
    if request.method == 'POST':
        if not has_permission(current_user, 'messaging.update'):
            flash('Vous n\'avez pas la permission de modifier la configuration', 'error')
            return redirect(url_for('messaging.api_config'))
        
        new_api_secret = request.form.get('api_secret', '').strip()
        action = request.form.get('action', 'save')
        
        if action == 'save':
            if not new_api_secret:
                flash('La clé API est obligatoire', 'error')
            else:
                try:
                    # Tester la clé avant de l'enregistrer
                    test_api = MessageProAPI(api_secret=new_api_secret)
                    test_result = test_api.get_credits()
                    
                    if test_result.get('status') == 200:
                        # Enregistrer la clé
                        ApiConfig.set_api_secret('messagepro', new_api_secret, current_user.id)
                        db.session.commit()
                        flash('Clé API enregistrée avec succès!', 'success')
                        return redirect(url_for('messaging.api_config'))
                    else:
                        flash(f'Clé API invalide: {test_result.get("message", "Erreur de connexion")}', 'error')
                except Exception as e:
                    flash(f'Erreur lors de la validation: {str(e)}', 'error')
        elif action == 'delete':
            if config:
                config.is_active = False
                config.api_secret = None
                config.updated_by_id = current_user.id
                db.session.commit()
                flash('Configuration supprimée', 'success')
                return redirect(url_for('messaging.api_config'))
    
    # Vérifier aussi la variable d'environnement
    env_secret = os.getenv('MESSAGEPRO_API_SECRET')
    has_env_config = bool(env_secret)
    
    return render_template('messaging/api_config.html',
                         api_secret=api_secret,
                         is_configured=is_configured,
                         connection_status=connection_status,
                         has_env_config=has_env_config)

