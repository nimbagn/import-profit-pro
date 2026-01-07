# -*- coding: utf-8 -*-
"""
Blueprint pour la gestion des clients commerciaux avec géolocalisation
Chaque commercial peut gérer son propre listing de clients
"""

from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from models import db, CommercialClient
from auth import has_permission
from datetime import datetime, UTC
from decimal import Decimal, InvalidOperation
from sqlalchemy import or_

commercial_clients_bp = Blueprint('commercial_clients', __name__, url_prefix='/commercial-clients')

@commercial_clients_bp.route('/')
@login_required
def clients_list():
    """Liste des clients du commercial connecté"""
    # Seuls les commerciaux peuvent voir leurs clients
    if not (current_user.role and current_user.role.code == 'commercial'):
        if not has_permission(current_user, 'orders.read'):
            flash('Vous n\'avez pas la permission d\'accéder à cette page', 'error')
            return redirect(url_for('index'))
    
    # Recherche
    search = request.args.get('search', '').strip()
    
    # Filtrer par commercial
    if current_user.role and current_user.role.code == 'commercial':
        query = CommercialClient.query.filter_by(commercial_id=current_user.id, is_active=True)
    elif has_permission(current_user, 'orders.read'):
        # Admin/supervisor peut voir tous les clients
        query = CommercialClient.query.filter_by(is_active=True)
        if search:
            query = query.filter(
                or_(
                    CommercialClient.first_name.ilike(f'%{search}%'),
                    CommercialClient.last_name.ilike(f'%{search}%'),
                    CommercialClient.phone.ilike(f'%{search}%'),
                    CommercialClient.address.ilike(f'%{search}%')
                )
            )
    else:
        flash('Vous n\'avez pas la permission d\'accéder à cette page', 'error')
        return redirect(url_for('index'))
    
    # Recherche pour commercial
    if current_user.role and current_user.role.code == 'commercial' and search:
        query = query.filter(
            or_(
                CommercialClient.first_name.ilike(f'%{search}%'),
                CommercialClient.last_name.ilike(f'%{search}%'),
                CommercialClient.phone.ilike(f'%{search}%'),
                CommercialClient.address.ilike(f'%{search}%')
            )
        )
    
    clients = query.order_by(CommercialClient.last_name, CommercialClient.first_name).all()
    
    return render_template('commercial_clients/list.html', clients=clients, search=search)

@commercial_clients_bp.route('/new', methods=['GET', 'POST'])
@login_required
def client_new():
    """Créer un nouveau client"""
    # Seuls les commerciaux peuvent créer des clients
    if not (current_user.role and current_user.role.code == 'commercial'):
        flash('Seuls les commerciaux peuvent créer des clients', 'error')
        return redirect(url_for('commercial_clients.clients_list'))
    
    if request.method == 'POST':
        try:
            first_name = request.form.get('first_name', '').strip()
            last_name = request.form.get('last_name', '').strip()
            phone = request.form.get('phone', '').strip()
            address = request.form.get('address', '').strip()
            latitude_str = request.form.get('latitude', '').strip()
            longitude_str = request.form.get('longitude', '').strip()
            notes = request.form.get('notes', '').strip()
            
            # Validation
            if not first_name or not last_name:
                flash('Le prénom et le nom sont obligatoires', 'error')
                return render_template('commercial_clients/form.html', is_edit=False)
            
            if not phone:
                flash('Le numéro de téléphone est obligatoire', 'error')
                return render_template('commercial_clients/form.html', is_edit=False)
            
            # Vérifier si le numéro existe déjà pour ce commercial
            existing = CommercialClient.query.filter_by(
                commercial_id=current_user.id,
                phone=phone,
                is_active=True
            ).first()
            
            if existing:
                flash(f'Un client avec le numéro {phone} existe déjà', 'error')
                return render_template('commercial_clients/form.html', is_edit=False)
            
            # Convertir les coordonnées GPS
            latitude = None
            longitude = None
            if latitude_str:
                try:
                    latitude = Decimal(latitude_str)
                    if latitude < -90 or latitude > 90:
                        flash('La latitude doit être entre -90 et 90', 'error')
                        return render_template('commercial_clients/form.html', is_edit=False)
                except (InvalidOperation, ValueError):
                    flash('Format de latitude invalide', 'error')
                    return render_template('commercial_clients/form.html', is_edit=False)
            
            if longitude_str:
                try:
                    longitude = Decimal(longitude_str)
                    if longitude < -180 or longitude > 180:
                        flash('La longitude doit être entre -180 et 180', 'error')
                        return render_template('commercial_clients/form.html', is_edit=False)
                except (InvalidOperation, ValueError):
                    flash('Format de longitude invalide', 'error')
                    return render_template('commercial_clients/form.html', is_edit=False)
            
            # Créer le client
            client = CommercialClient(
                commercial_id=current_user.id,
                first_name=first_name,
                last_name=last_name,
                phone=phone,
                address=address,
                latitude=latitude,
                longitude=longitude,
                notes=notes,
                is_active=True
            )
            
            db.session.add(client)
            db.session.commit()
            
            flash(f'Client {client.full_name} créé avec succès', 'success')
            return redirect(url_for('commercial_clients.clients_list'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur lors de la création du client: {str(e)}', 'error')
            return render_template('commercial_clients/form.html', is_edit=False)
    
    return render_template('commercial_clients/form.html', is_edit=False)

@commercial_clients_bp.route('/<int:client_id>/edit', methods=['GET', 'POST'])
@login_required
def client_edit(client_id):
    """Modifier un client"""
    client = CommercialClient.query.get_or_404(client_id)
    
    # Vérifier que le commercial est propriétaire
    if current_user.role and current_user.role.code == 'commercial':
        if client.commercial_id != current_user.id:
            flash('Vous n\'avez pas la permission de modifier ce client', 'error')
            return redirect(url_for('commercial_clients.clients_list'))
    
    if request.method == 'POST':
        try:
            first_name = request.form.get('first_name', '').strip()
            last_name = request.form.get('last_name', '').strip()
            phone = request.form.get('phone', '').strip()
            address = request.form.get('address', '').strip()
            latitude_str = request.form.get('latitude', '').strip()
            longitude_str = request.form.get('longitude', '').strip()
            notes = request.form.get('notes', '').strip()
            
            # Validation
            if not first_name or not last_name:
                flash('Le prénom et le nom sont obligatoires', 'error')
                return render_template('commercial_clients/form.html', client=client, is_edit=True)
            
            if not phone:
                flash('Le numéro de téléphone est obligatoire', 'error')
                return render_template('commercial_clients/form.html', client=client, is_edit=True)
            
            # Vérifier si le numéro existe déjà pour un autre client du même commercial
            if phone != client.phone:
                existing = CommercialClient.query.filter_by(
                    commercial_id=client.commercial_id,
                    phone=phone,
                    is_active=True
                ).first()
                
                if existing and existing.id != client.id:
                    flash(f'Un client avec le numéro {phone} existe déjà', 'error')
                    return render_template('commercial_clients/form.html', client=client, is_edit=True)
            
            # Convertir les coordonnées GPS
            latitude = None
            longitude = None
            if latitude_str:
                try:
                    latitude = Decimal(latitude_str)
                    if latitude < -90 or latitude > 90:
                        flash('La latitude doit être entre -90 et 90', 'error')
                        return render_template('commercial_clients/form.html', client=client, is_edit=True)
                except (InvalidOperation, ValueError):
                    flash('Format de latitude invalide', 'error')
                    return render_template('commercial_clients/form.html', client=client, is_edit=True)
            
            if longitude_str:
                try:
                    longitude = Decimal(longitude_str)
                    if longitude < -180 or longitude > 180:
                        flash('La longitude doit être entre -180 et 180', 'error')
                        return render_template('commercial_clients/form.html', client=client, is_edit=True)
                except (InvalidOperation, ValueError):
                    flash('Format de longitude invalide', 'error')
                    return render_template('commercial_clients/form.html', client=client, is_edit=True)
            
            # Mettre à jour
            client.first_name = first_name
            client.last_name = last_name
            client.phone = phone
            client.address = address
            client.latitude = latitude
            client.longitude = longitude
            client.notes = notes
            client.updated_at = datetime.now(UTC)
            
            db.session.commit()
            
            flash(f'Client {client.full_name} modifié avec succès', 'success')
            return redirect(url_for('commercial_clients.clients_list'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur lors de la modification du client: {str(e)}', 'error')
            return render_template('commercial_clients/form.html', client=client, is_edit=True)
    
    return render_template('commercial_clients/form.html', client=client, is_edit=True)

@commercial_clients_bp.route('/<int:client_id>/delete', methods=['POST'])
@login_required
def client_delete(client_id):
    """Supprimer (désactiver) un client"""
    client = CommercialClient.query.get_or_404(client_id)
    
    # Vérifier que le commercial est propriétaire
    if current_user.role and current_user.role.code == 'commercial':
        if client.commercial_id != current_user.id:
            flash('Vous n\'avez pas la permission de supprimer ce client', 'error')
            return redirect(url_for('commercial_clients.clients_list'))
    
    try:
        # Soft delete
        client.is_active = False
        client.updated_at = datetime.now(UTC)
        db.session.commit()
        
        flash(f'Client {client.full_name} supprimé avec succès', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erreur lors de la suppression: {str(e)}', 'error')
    
    return redirect(url_for('commercial_clients.clients_list'))

@commercial_clients_bp.route('/search-by-phone', methods=['GET'])
@login_required
def search_by_phone():
    """Rechercher un client par numéro de téléphone (API pour formulaire commande)"""
    phone = request.args.get('phone', '').strip()
    
    if not phone:
        return jsonify({'success': False, 'message': 'Numéro de téléphone requis'})
    
    # Rechercher uniquement les clients du commercial connecté
    if current_user.role and current_user.role.code == 'commercial':
        client = CommercialClient.query.filter_by(
            commercial_id=current_user.id,
            phone=phone,
            is_active=True
        ).first()
    else:
        return jsonify({'success': False, 'message': 'Accès non autorisé'})
    
    if client:
        return jsonify({
            'success': True,
            'client': {
                'id': client.id,
                'first_name': client.first_name,
                'last_name': client.last_name,
                'full_name': client.full_name,
                'phone': client.phone,
                'address': client.address or '',
                'latitude': float(client.latitude) if client.latitude else None,
                'longitude': float(client.longitude) if client.longitude else None,
                'notes': client.notes or ''
            }
        })
    else:
        return jsonify({'success': False, 'message': 'Client non trouvé'})

