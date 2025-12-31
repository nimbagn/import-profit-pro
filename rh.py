#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module Ressources Humaines - Import Profit Pro
Gestion du personnel et suivi des interactions utilisateurs
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
from datetime import datetime, UTC, timedelta, date
from decimal import Decimal, InvalidOperation
from sqlalchemy import func, desc, and_, or_
from models import (db, User, Role, Region, UserActivityLog, Employee, EmployeeContract, 
                   EmployeeTraining, EmployeeEvaluation, EmployeeAbsence, Depot)
from auth import has_permission, require_permission
import json

# Créer le blueprint
rh_bp = Blueprint('rh', __name__, url_prefix='/rh')

# =========================================================
# PAGE D'ACCUEIL / TABLEAU DE BORD RH
# =========================================================

@rh_bp.route('/')
@login_required
def index():
    """Tableau de bord RH - Page d'accueil du module"""
    if not has_rh_permission(current_user, 'users.read') and not is_rh_user(current_user):
        flash('Accès refusé. Vous devez avoir un rôle RH pour accéder à cette page.', 'error')
        return redirect(url_for('index'))
    
    # Statistiques générales
    total_users = User.query.count()
    active_users = User.query.filter_by(is_active=True).count()
    inactive_users = User.query.filter_by(is_active=False).count()
    
    # Statistiques employés externes
    total_employees = Employee.query.count()
    active_employees = Employee.query.filter_by(employment_status='active').count()
    
    # Statistiques récentes (30 derniers jours)
    last_30_days = datetime.now(UTC) - timedelta(days=30)
    
    # Activités récentes
    recent_activities_count = UserActivityLog.query.filter(
        UserActivityLog.created_at >= last_30_days
    ).count()
    
    # Connexions récentes
    recent_logins = UserActivityLog.query.filter(
        and_(
            UserActivityLog.action == 'login',
            UserActivityLog.created_at >= last_30_days
        )
    ).count()
    
    # Utilisateurs par rôle
    users_by_role = db.session.query(
        Role.name,
        Role.code,
        func.count(User.id).label('count')
    ).join(User).group_by(Role.id, Role.name, Role.code).all()
    
    # Activités par type (30 derniers jours)
    activities_by_type = db.session.query(
        UserActivityLog.action,
        func.count(UserActivityLog.id).label('count')
    ).filter(
        UserActivityLog.created_at >= last_30_days
    ).group_by(UserActivityLog.action).order_by(desc('count')).limit(10).all()
    
    # Top 5 utilisateurs les plus actifs (30 derniers jours)
    top_active_users = db.session.query(
        User.id,
        User.username,
        User.full_name,
        func.count(UserActivityLog.id).label('activity_count')
    ).join(UserActivityLog).filter(
        UserActivityLog.created_at >= last_30_days
    ).group_by(User.id, User.username, User.full_name).order_by(desc('activity_count')).limit(5).all()
    
    # Contrats actifs
    active_contracts = EmployeeContract.query.filter(
        or_(
            EmployeeContract.status == 'active',
            and_(
                EmployeeContract.end_date.is_(None),
                EmployeeContract.status != 'terminated'
            )
        )
    ).count()
    
    # Formations en cours
    ongoing_trainings = EmployeeTraining.query.filter(
        and_(
            EmployeeTraining.status == 'in_progress',
            EmployeeTraining.start_date <= date.today(),
            or_(
                EmployeeTraining.end_date.is_(None),
                EmployeeTraining.end_date >= date.today()
            )
        )
    ).count()
    
    # Absences en attente
    pending_absences = EmployeeAbsence.query.filter_by(status='pending').count()
    
    return render_template('rh/index.html',
                         total_users=total_users,
                         active_users=active_users,
                         inactive_users=inactive_users,
                         total_employees=total_employees,
                         active_employees=active_employees,
                         recent_activities_count=recent_activities_count,
                         recent_logins=recent_logins,
                         users_by_role=users_by_role,
                         activities_by_type=activities_by_type,
                         top_active_users=top_active_users,
                         active_contracts=active_contracts,
                         ongoing_trainings=ongoing_trainings,
                         pending_absences=pending_absences)

# =========================================================
# GESTION DU PERSONNEL
# =========================================================

@rh_bp.route('/personnel')
@login_required
def personnel_list():
    """Liste du personnel avec filtres et recherche"""
    if not has_rh_permission(current_user, 'users.read') and not is_rh_user(current_user):
        flash('Accès refusé. Vous devez avoir un rôle RH pour accéder à cette page.', 'error')
        return redirect(url_for('index'))
    
    # Filtres
    region_id = request.args.get('region_id', type=int)
    role_id = request.args.get('role_id', type=int)
    is_active = request.args.get('is_active', type=str)
    search = request.args.get('search', '').strip()
    
    # Construire la requête
    query = User.query
    
    # Filtre par région
    if region_id:
        query = query.filter_by(region_id=region_id)
    
    # Filtre par rôle
    if role_id:
        query = query.filter_by(role_id=role_id)
    
    # Filtre actif/inactif
    # Par défaut, on affiche TOUS les utilisateurs (actifs et inactifs)
    # L'utilisateur peut filtrer pour voir uniquement les actifs ou inactifs
    if is_active == 'active':
        query = query.filter_by(is_active=True)
    elif is_active == 'inactive':
        query = query.filter_by(is_active=False)
    # Si is_active n'est pas défini, on affiche tous les utilisateurs (actifs ET inactifs)
    
    # Recherche
    if search:
        search_pattern = f'%{search}%'
        query = query.filter(
            or_(
                User.username.like(search_pattern),
                User.email.like(search_pattern),
                User.full_name.like(search_pattern),
                User.phone.like(search_pattern)
            )
        )
    
    # Trier par date de création (plus récent en premier)
    users = query.order_by(desc(User.created_at)).all()
    
    # Statistiques
    total_users = User.query.count()
    active_users = User.query.filter_by(is_active=True).count()
    inactive_users = User.query.filter_by(is_active=False).count()
    
    # Par rôle
    roles_stats = db.session.query(
        Role.name,
        func.count(User.id).label('count')
    ).join(User).group_by(Role.id, Role.name).all()
    
    # Par région
    regions_stats = db.session.query(
        Region.name,
        func.count(User.id).label('count')
    ).join(User).group_by(Region.id, Region.name).all()
    
    roles = Role.query.order_by(Role.name).all()
    regions = Region.query.order_by(Region.name).all()
    
    return render_template('rh/personnel_list.html',
                         users=users,
                         roles=roles,
                         regions=regions,
                         selected_region_id=region_id,
                         selected_role_id=role_id,
                         selected_is_active=is_active,
                         search=search,
                         total_users=total_users,
                         active_users=active_users,
                         inactive_users=inactive_users,
                         roles_stats=roles_stats,
                         regions_stats=regions_stats)

@rh_bp.route('/personnel/<int:user_id>')
@login_required
def personnel_detail(user_id):
    """Détails d'un membre du personnel"""
    if not has_rh_permission(current_user, 'users.read') and not is_rh_user(current_user):
        flash('Accès refusé. Vous devez avoir un rôle RH pour accéder à cette page.', 'error')
        return redirect(url_for('rh.personnel_list'))
    
    user = User.query.get_or_404(user_id)
    
    # Statistiques d'activité
    last_30_days = datetime.now(UTC) - timedelta(days=30)
    
    # Nombre de connexions dans les 30 derniers jours
    recent_logins = UserActivityLog.query.filter(
        and_(
            UserActivityLog.user_id == user_id,
            UserActivityLog.action == 'login',
            UserActivityLog.created_at >= last_30_days
        )
    ).count()
    
    # Dernière activité
    last_activity = UserActivityLog.query.filter_by(user_id=user_id).order_by(desc(UserActivityLog.created_at)).first()
    
    # Activités récentes (10 dernières)
    recent_activities = UserActivityLog.query.filter_by(user_id=user_id).order_by(desc(UserActivityLog.created_at)).limit(10).all()
    
    # Statistiques par type d'action
    activity_stats = db.session.query(
        UserActivityLog.action,
        func.count(UserActivityLog.id).label('count')
    ).filter(
        and_(
            UserActivityLog.user_id == user_id,
            UserActivityLog.created_at >= last_30_days
        )
    ).group_by(UserActivityLog.action).all()
    
    return render_template('rh/personnel_detail.html',
                         user=user,
                         recent_logins=recent_logins,
                         last_activity=last_activity,
                         recent_activities=recent_activities,
                         activity_stats=activity_stats)

@rh_bp.route('/personnel/new', methods=['GET', 'POST'])
@login_required
def personnel_new():
    """Créer un nouveau membre du personnel"""
    if not has_rh_permission(current_user, 'users.create'):
        flash('Accès refusé. Vous n\'avez pas la permission de créer des utilisateurs.', 'error')
        return redirect(url_for('rh.personnel_list'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        full_name = request.form.get('full_name')
        phone = request.form.get('phone')
        role_id = request.form.get('role_id')
        region_id = request.form.get('region_id') or None
        is_active = bool(request.form.get('is_active'))
        
        # Validation
        if not username or not email or not password or not role_id:
            flash('Veuillez remplir tous les champs obligatoires', 'error')
            roles = Role.query.all()
            regions = Region.query.order_by(Region.name).all()
            return render_template('rh/personnel_form.html', user=None, roles=roles, regions=regions)
        
        # Vérifier si l'utilisateur existe déjà
        if User.query.filter_by(username=username).first():
            flash('Ce nom d\'utilisateur existe déjà', 'error')
            roles = Role.query.all()
            regions = Region.query.order_by(Region.name).all()
            return render_template('rh/personnel_form.html', user=None, roles=roles, regions=regions)
        
        if User.query.filter_by(email=email).first():
            flash('Cet email est déjà utilisé', 'error')
            roles = Role.query.all()
            regions = Region.query.order_by(Region.name).all()
            return render_template('rh/personnel_form.html', user=None, roles=roles, regions=regions)
        
        # Créer l'utilisateur
        user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password),
            full_name=full_name,
            phone=phone,
            role_id=int(role_id),
            region_id=int(region_id) if region_id else None,
            is_active=is_active
        )
        
        db.session.add(user)
        db.session.flush()  # S'assurer que l'utilisateur est créé dans la session
        
        # Logger la création
        log_activity(user.id, 'user_created', {
            'created_by': current_user.id,
            'username': username,
            'role_id': role_id
        })
        
        db.session.commit()
        
        flash(f'Personnel {username} créé avec succès', 'success')
        # Rediriger vers la liste avec le filtre de région si l'utilisateur créé a une région
        # Cela garantit que l'utilisateur créé sera visible dans la liste
        redirect_url = url_for('rh.personnel_list')
        if user.region_id:
            redirect_url = url_for('rh.personnel_list', region_id=user.region_id)
        return redirect(redirect_url)
    
    roles = Role.query.all()
    regions = Region.query.order_by(Region.name).all()
    return render_template('rh/personnel_form.html', user=None, roles=roles, regions=regions)

@rh_bp.route('/personnel/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
def personnel_edit(user_id):
    """Modifier un membre du personnel"""
    if not has_rh_permission(current_user, 'users.update'):
        flash('Accès refusé. Vous n\'avez pas la permission de modifier des utilisateurs.', 'error')
        return redirect(url_for('rh.personnel_list'))
    
    user = User.query.get_or_404(user_id)
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        full_name = request.form.get('full_name')
        phone = request.form.get('phone')
        role_id = request.form.get('role_id')
        region_id = request.form.get('region_id') or None
        is_active = bool(request.form.get('is_active'))
        
        # Validation
        if not username or not email or not role_id:
            flash('Veuillez remplir tous les champs obligatoires', 'error')
            roles = Role.query.all()
            regions = Region.query.order_by(Region.name).all()
            return render_template('rh/personnel_form.html', user=user, roles=roles, regions=regions)
        
        # Vérifier si le username existe déjà (pour un autre utilisateur)
        existing_user = User.query.filter_by(username=username).first()
        if existing_user and existing_user.id != user.id:
            flash('Ce nom d\'utilisateur existe déjà', 'error')
            roles = Role.query.all()
            regions = Region.query.order_by(Region.name).all()
            return render_template('rh/personnel_form.html', user=user, roles=roles, regions=regions)
        
        # Vérifier si l'email existe déjà (pour un autre utilisateur)
        existing_email = User.query.filter_by(email=email).first()
        if existing_email and existing_email.id != user.id:
            flash('Cet email est déjà utilisé', 'error')
            roles = Role.query.all()
            regions = Region.query.order_by(Region.name).all()
            return render_template('rh/personnel_form.html', user=user, roles=roles, regions=regions)
        
        # Sauvegarder les changements pour le log
        changes = {}
        if user.username != username:
            changes['username'] = {'old': user.username, 'new': username}
        if user.email != email:
            changes['email'] = {'old': user.email, 'new': email}
        if user.role_id != int(role_id):
            old_role = Role.query.get(user.role_id)
            new_role = Role.query.get(int(role_id))
            changes['role'] = {'old': old_role.name if old_role else None, 'new': new_role.name if new_role else None}
        if user.is_active != is_active:
            changes['is_active'] = {'old': user.is_active, 'new': is_active}
        
        # Mettre à jour l'utilisateur
        user.username = username
        user.email = email
        user.full_name = full_name
        user.phone = phone
        user.role_id = int(role_id)
        user.region_id = int(region_id) if region_id else None
        user.is_active = is_active
        user.updated_at = datetime.now(UTC)
        
        db.session.commit()
        
        # Logger les modifications
        if changes:
            log_activity(user.id, 'user_updated', {
                'updated_by': current_user.id,
                'changes': changes
            })
        
        flash(f'Personnel {username} modifié avec succès', 'success')
        return redirect(url_for('rh.personnel_detail', user_id=user.id))
    
    roles = Role.query.all()
    regions = Region.query.order_by(Region.name).all()
    return render_template('rh/personnel_form.html', user=user, roles=roles, regions=regions)

# =========================================================
# SUIVI DES INTERACTIONS UTILISATEURS
# =========================================================

@rh_bp.route('/activites')
@login_required
def activites_list():
    """Liste des activités/interactions des utilisateurs"""
    if not has_rh_permission(current_user, 'users.read') and not is_rh_user(current_user):
        flash('Accès refusé. Vous devez avoir un rôle RH pour accéder à cette page.', 'error')
        return redirect(url_for('index'))
    
    # Filtres
    user_id = request.args.get('user_id', type=int)
    action = request.args.get('action', '')
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    limit = request.args.get('limit', 100, type=int)
    
    # Construire la requête
    query = UserActivityLog.query
    
    # Filtre par utilisateur
    if user_id:
        query = query.filter_by(user_id=user_id)
    
    # Filtre par action
    if action:
        query = query.filter_by(action=action)
    
    # Filtre par date
    if date_from:
        try:
            date_from_obj = datetime.strptime(date_from, '%Y-%m-%d')
            query = query.filter(UserActivityLog.created_at >= date_from_obj)
        except ValueError:
            pass
    
    if date_to:
        try:
            date_to_obj = datetime.strptime(date_to, '%Y-%m-%d') + timedelta(days=1)
            query = query.filter(UserActivityLog.created_at < date_to_obj)
        except ValueError:
            pass
    
    # Trier par date (plus récent en premier)
    activities = query.order_by(desc(UserActivityLog.created_at)).limit(limit).all()
    
    # Statistiques globales
    total_activities = UserActivityLog.query.count()
    
    # Activités par type
    activities_by_type = db.session.query(
        UserActivityLog.action,
        func.count(UserActivityLog.id).label('count')
    ).group_by(UserActivityLog.action).all()
    
    # Activités par utilisateur (top 10)
    top_users = db.session.query(
        User.username,
        func.count(UserActivityLog.id).label('count')
    ).join(UserActivityLog).group_by(User.id, User.username).order_by(desc('count')).limit(10).all()
    
    # Liste des utilisateurs pour le filtre
    users = User.query.order_by(User.username).all()
    
    # Liste des actions uniques
    actions = db.session.query(UserActivityLog.action).distinct().all()
    actions = [a[0] for a in actions]
    
    return render_template('rh/activites_list.html',
                         activities=activities,
                         users=users,
                         actions=actions,
                         selected_user_id=user_id,
                         selected_action=action,
                         date_from=date_from,
                         date_to=date_to,
                         total_activities=total_activities,
                         activities_by_type=activities_by_type,
                         top_users=top_users)

@rh_bp.route('/statistiques')
@login_required
def statistiques():
    """Statistiques d'utilisation de l'application"""
    if not has_rh_permission(current_user, 'analytics.read') and not is_rh_user(current_user):
        flash('Accès refusé. Vous devez avoir un rôle RH pour accéder à cette page.', 'error')
        return redirect(url_for('index'))
    
    # Période par défaut: 30 derniers jours
    days = request.args.get('days', 30, type=int)
    date_from = datetime.now(UTC) - timedelta(days=days)
    
    # Statistiques générales
    total_users = User.query.count()
    active_users = User.query.filter_by(is_active=True).count()
    
    # Connexions dans la période
    logins_count = UserActivityLog.query.filter(
        and_(
            UserActivityLog.action == 'login',
            UserActivityLog.created_at >= date_from
        )
    ).count()
    
    # Utilisateurs actifs (qui se sont connectés dans la période)
    active_users_period = db.session.query(func.count(func.distinct(UserActivityLog.user_id))).filter(
        and_(
            UserActivityLog.action == 'login',
            UserActivityLog.created_at >= date_from
        )
    ).scalar()
    
    # Activités par jour (pour graphique)
    activities_by_day = db.session.query(
        func.date(UserActivityLog.created_at).label('date'),
        func.count(UserActivityLog.id).label('count')
    ).filter(
        UserActivityLog.created_at >= date_from
    ).group_by(func.date(UserActivityLog.created_at)).order_by('date').all()
    
    # Activités par type
    activities_by_type = db.session.query(
        UserActivityLog.action,
        func.count(UserActivityLog.id).label('count')
    ).filter(
        UserActivityLog.created_at >= date_from
    ).group_by(UserActivityLog.action).order_by(desc('count')).all()
    
    # Top 10 utilisateurs les plus actifs
    top_active_users = db.session.query(
        User.id,
        User.username,
        User.full_name,
        func.count(UserActivityLog.id).label('activity_count')
    ).join(UserActivityLog).filter(
        UserActivityLog.created_at >= date_from
    ).group_by(User.id, User.username, User.full_name).order_by(desc('activity_count')).limit(10).all()
    
    # Activités par heure de la journée
    activities_by_hour = db.session.query(
        func.extract('hour', UserActivityLog.created_at).label('hour'),
        func.count(UserActivityLog.id).label('count')
    ).filter(
        UserActivityLog.created_at >= date_from
    ).group_by(func.extract('hour', UserActivityLog.created_at)).order_by('hour').all()
    
    return render_template('rh/statistiques.html',
                         days=days,
                         total_users=total_users,
                         active_users=active_users,
                         logins_count=logins_count,
                         active_users_period=active_users_period,
                         activities_by_day=activities_by_day,
                         activities_by_type=activities_by_type,
                         top_active_users=top_active_users,
                         activities_by_hour=activities_by_hour)

# =========================================================
# FONCTIONS UTILITAIRES
# =========================================================

# =========================================================
# GESTION DES EMPLOYÉS EXTERNES (SANS ACCÈS PLATEFORME)
# =========================================================

def has_rh_permission(user, permission):
    """
    Vérifier si l'utilisateur a une permission RH
    
    IMPORTANT: Le rôle 'admin' a TOUS les droits RH et passe toutes les vérifications.
    L'admin peut accéder à toutes les fonctionnalités RH sans exception.
    
    Args:
        user: L'utilisateur à vérifier
        permission: Permission au format 'module.action' (ex: 'employees.read', 'contracts.create')
    
    Returns:
        bool: True si l'utilisateur a la permission, False sinon
    """
    if not user or not hasattr(user, 'is_authenticated') or not user.is_authenticated:
        return False
    if not hasattr(user, 'role') or not user.role:
        return False
    
    # ⚠️ RÈGLE FONDAMENTALE : L'admin a TOUS les droits RH
    # L'admin passe toutes les vérifications de permissions RH, peu importe la permission demandée
    if user.role.code == 'admin':
        return True  # Admin a tous les droits RH - accès à toutes les fonctionnalités RH
    
    # Vérifier les rôles RH
    rh_roles = ['rh', 'rh_manager', 'rh_assistant', 'rh_recruiter', 'rh_analyst']
    if user.role.code not in rh_roles:
        return False
    
    # RH Manager a tous les droits RH
    if user.role.code == 'rh_manager':
        return True
    
    # Vérifier les permissions spécifiques selon le rôle
    if not user.role.permissions:
        return False
    
    permissions = user.role.permissions
    if isinstance(permissions, dict):
        parts = permission.split('.')
        if len(parts) == 2:
            module, action = parts
            # Vérifier si le module existe dans les permissions
            if module in permissions:
                # Vérifier si l'action est autorisée (peut être une liste ou '*')
                module_perms = permissions[module]
                if isinstance(module_perms, list):
                    return action in module_perms or '*' in module_perms
                elif module_perms == '*':
                    return True
        # Vérifier aussi les permissions globales
        if 'all' in permissions:
            all_perms = permissions['all']
            if isinstance(all_perms, list):
                return '*' in all_perms or permission in all_perms
            elif all_perms == '*':
                return True
    
    return False

def is_rh_user(user):
    """Vérifier si l'utilisateur a un rôle RH"""
    if not user or not hasattr(user, 'is_authenticated') or not user.is_authenticated:
        return False
    if not hasattr(user, 'role') or not user.role:
        return False
    
    rh_roles = ['rh', 'rh_manager', 'rh_assistant', 'rh_recruiter', 'rh_analyst']
    return user.role.code in rh_roles or user.role.code == 'admin'

@rh_bp.route('/employees')
@login_required
def employees_list():
    """Liste des employés externes (sans accès plateforme)"""
    if not has_rh_permission(current_user, 'employees.read'):
        flash('Accès refusé', 'error')
        return redirect(url_for('index'))
    
    # Filtres
    department = request.args.get('department', '')
    position = request.args.get('position', '')
    status = request.args.get('status', '')
    region_id = request.args.get('region_id', type=int)
    search = request.args.get('search', '').strip()
    
    # Construire la requête
    query = Employee.query
    
    if department:
        query = query.filter(Employee.department.like(f'%{department}%'))
    if position:
        query = query.filter(Employee.position.like(f'%{position}%'))
    if status:
        query = query.filter_by(employment_status=status)
    if region_id:
        query = query.filter_by(region_id=region_id)
    if search:
        search_pattern = f'%{search}%'
        query = query.filter(
            or_(
                Employee.first_name.like(search_pattern),
                Employee.last_name.like(search_pattern),
                Employee.employee_number.like(search_pattern),
                Employee.email.like(search_pattern),
                Employee.phone.like(search_pattern)
            )
        )
    
    employees = query.order_by(desc(Employee.created_at)).all()
    
    # Statistiques
    total_employees = Employee.query.count()
    active_employees = Employee.query.filter_by(employment_status='active').count()
    
    # Par département
    departments = db.session.query(Employee.department, func.count(Employee.id).label('count')).filter(
        Employee.department.isnot(None)
    ).group_by(Employee.department).all()
    
    regions = Region.query.order_by(Region.name).all()
    
    return render_template('rh/employees_list.html',
                         employees=employees,
                         regions=regions,
                         selected_region_id=region_id,
                         selected_status=status,
                         search=search,
                         total_employees=total_employees,
                         active_employees=active_employees,
                         departments=departments)

@rh_bp.route('/employees/<int:employee_id>')
@login_required
def employee_detail(employee_id):
    """Détails d'un employé externe"""
    if not has_rh_permission(current_user, 'employees.read'):
        flash('Accès refusé', 'error')
        return redirect(url_for('rh.employees_list'))
    
    employee = Employee.query.get_or_404(employee_id)
    
    # Récupérer les informations associées
    current_contract = employee.current_contract
    recent_trainings = employee.trainings.order_by(desc(EmployeeTraining.start_date)).limit(5).all()
    recent_evaluations = employee.evaluations.order_by(desc(EmployeeEvaluation.evaluation_date)).limit(5).all()
    recent_absences = employee.absences.order_by(desc(EmployeeAbsence.start_date)).limit(5).all()
    
    return render_template('rh/employee_detail.html',
                         employee=employee,
                         current_contract=current_contract,
                         recent_trainings=recent_trainings,
                         recent_evaluations=recent_evaluations,
                         recent_absences=recent_absences)

@rh_bp.route('/employees/new', methods=['GET', 'POST'])
@login_required
def employee_new():
    """Créer un nouvel employé externe"""
    if not has_rh_permission(current_user, 'employees.create'):
        flash('Accès refusé', 'error')
        return redirect(url_for('rh.employees_list'))
    
    if request.method == 'POST':
        # Récupérer les données du formulaire
        employee_number = request.form.get('employee_number')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        department = request.form.get('department')
        position = request.form.get('position')
        hire_date_str = request.form.get('hire_date')
        region_id = request.form.get('region_id') or None
        
        # Validation
        if not employee_number or not first_name or not last_name:
            flash('Veuillez remplir tous les champs obligatoires', 'error')
            regions = Region.query.all()
            depots = Depot.query.all()
            employees = Employee.query.filter_by(employment_status='active').all()
            return render_template('rh/employee_form.html', employee=None, regions=regions, depots=depots, employees=employees)
        
        # Vérifier si le numéro d'employé existe déjà
        if Employee.query.filter_by(employee_number=employee_number).first():
            flash('Ce numéro d\'employé existe déjà', 'error')
            regions = Region.query.all()
            depots = Depot.query.all()
            employees = Employee.query.filter_by(employment_status='active').all()
            return render_template('rh/employee_form.html', employee=None, regions=regions, depots=depots, employees=employees)
        
        # Créer l'employé
        employee = Employee(
            employee_number=employee_number,
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone=phone,
            department=department,
            position=position,
            hire_date=datetime.strptime(hire_date_str, '%Y-%m-%d').date() if hire_date_str else None,
            region_id=int(region_id) if region_id else None,
            employment_status='active',
            created_by_id=current_user.id
        )
        
        db.session.add(employee)
        db.session.commit()
        
        # Logger la création
        log_activity(current_user.id, 'employee_created', {
            'employee_id': employee.id,
            'employee_number': employee_number
        })
        
        flash(f'Employé {employee.full_name} créé avec succès', 'success')
        return redirect(url_for('rh.employee_detail', employee_id=employee.id))
    
    regions = Region.query.all()
    depots = Depot.query.all()
    employees = Employee.query.filter_by(employment_status='active').all()  # Pour sélectionner un manager
    return render_template('rh/employee_form.html', employee=None, regions=regions, depots=depots, employees=employees)

@rh_bp.route('/employees/<int:employee_id>/edit', methods=['GET', 'POST'])
@login_required
def employee_edit(employee_id):
    """Modifier un employé externe"""
    if not has_rh_permission(current_user, 'employees.update'):
        flash('Accès refusé', 'error')
        return redirect(url_for('rh.employees_list'))
    
    employee = Employee.query.get_or_404(employee_id)
    
    if request.method == 'POST':
        # Mettre à jour les champs
        employee.first_name = request.form.get('first_name')
        employee.last_name = request.form.get('last_name')
        employee.email = request.form.get('email')
        employee.phone = request.form.get('phone')
        employee.department = request.form.get('department')
        employee.position = request.form.get('position')
        employee.employment_status = request.form.get('employment_status')
        employee.region_id = int(request.form.get('region_id')) if request.form.get('region_id') else None
        employee.updated_at = datetime.now(UTC)
        
        db.session.commit()
        
        log_activity(current_user.id, 'employee_updated', {
            'employee_id': employee.id
        })
        
        flash(f'Employé {employee.full_name} modifié avec succès', 'success')
        return redirect(url_for('rh.employee_detail', employee_id=employee.id))
    
    regions = Region.query.all()
    depots = Depot.query.all()
    employees = Employee.query.filter_by(employment_status='active').all()
    return render_template('rh/employee_form.html', employee=employee, regions=regions, depots=depots, employees=employees)

# =========================================================
# GESTION DES CONTRATS
# =========================================================

@rh_bp.route('/employees/<int:employee_id>/contracts')
@login_required
def employee_contracts_list(employee_id):
    """Liste des contrats d'un employé"""
    if not has_rh_permission(current_user, 'contracts.read'):
        flash('Accès refusé', 'error')
        return redirect(url_for('rh.employees_list'))
    
    employee = Employee.query.get_or_404(employee_id)
    contracts = employee.contracts.order_by(desc(EmployeeContract.start_date)).all()
    
    return render_template('rh/contracts_list.html', employee=employee, contracts=contracts)

@rh_bp.route('/employees/<int:employee_id>/contracts/new', methods=['GET', 'POST'])
@login_required
def contract_new(employee_id):
    """Créer un nouveau contrat"""
    if not has_rh_permission(current_user, 'contracts.create'):
        flash('Accès refusé', 'error')
        return redirect(url_for('rh.employee_detail', employee_id=employee_id))
    
    employee = Employee.query.get_or_404(employee_id)
    
    if request.method == 'POST':
        contract_number = request.form.get('contract_number')
        contract_type = request.form.get('contract_type')
        start_date_str = request.form.get('start_date')
        end_date_str = request.form.get('end_date')
        salary = request.form.get('salary')
        currency = request.form.get('currency', 'GNF')
        position = request.form.get('position')
        department = request.form.get('department')
        status = request.form.get('status', 'draft')
        
        if not contract_number or not contract_type or not start_date_str:
            flash('Veuillez remplir tous les champs obligatoires', 'error')
            return render_template('rh/contract_form.html', employee=employee, contract=None)
        
        # Vérifier si le numéro de contrat existe déjà
        existing_contract = EmployeeContract.query.filter_by(contract_number=contract_number).first()
        if existing_contract:
            flash('Ce numéro de contrat existe déjà', 'error')
            return render_template('rh/contract_form.html', employee=employee, contract=None)
        
        # Validation des dates
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        if end_date_str:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            if end_date < start_date:
                flash('La date de fin doit être postérieure à la date de début', 'error')
                return render_template('rh/contract_form.html', employee=employee, contract=None)
        
        # Validation du salaire
        if salary:
            try:
                salary_decimal = Decimal(salary)
                if salary_decimal < 0:
                    flash('Le salaire ne peut pas être négatif', 'error')
                    return render_template('rh/contract_form.html', employee=employee, contract=None)
            except (ValueError, InvalidOperation):
                flash('Le salaire doit être un nombre valide', 'error')
                return render_template('rh/contract_form.html', employee=employee, contract=None)
        
        contract = EmployeeContract(
            employee_id=employee_id,
            contract_number=contract_number,
            contract_type=contract_type,
            start_date=start_date,
            end_date=datetime.strptime(end_date_str, '%Y-%m-%d').date() if end_date_str else None,
            salary=salary_decimal if salary else None,
            currency=currency,
            position=position or employee.position,
            department=department or employee.department,
            status=status,
            created_by_id=current_user.id
        )
        
        db.session.add(contract)
        db.session.commit()
        
        log_activity(current_user.id, 'contract_created', {
            'contract_id': contract.id,
            'employee_id': employee_id
        })
        
        flash(f'Contrat {contract_number} créé avec succès', 'success')
        return redirect(url_for('rh.employee_contracts_list', employee_id=employee_id))
    
    return render_template('rh/contract_form.html', employee=employee, contract=None)

@rh_bp.route('/contracts/<int:contract_id>')
@login_required
def contract_detail(contract_id):
    """Détails d'un contrat"""
    if not has_rh_permission(current_user, 'contracts.read'):
        flash('Accès refusé', 'error')
        return redirect(url_for('rh.employees_list'))
    
    contract = EmployeeContract.query.get_or_404(contract_id)
    return render_template('rh/contract_detail.html', contract=contract)

@rh_bp.route('/contracts/<int:contract_id>/edit', methods=['GET', 'POST'])
@login_required
def contract_edit(contract_id):
    """Modifier un contrat"""
    if not has_rh_permission(current_user, 'contracts.update'):
        flash('Accès refusé', 'error')
        return redirect(url_for('rh.employees_list'))
    
    contract = EmployeeContract.query.get_or_404(contract_id)
    
    if request.method == 'POST':
        contract.contract_type = request.form.get('contract_type')
        contract.start_date = datetime.strptime(request.form.get('start_date'), '%Y-%m-%d').date()
        end_date_str = request.form.get('end_date')
        contract.end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date() if end_date_str else None
        salary = request.form.get('salary')
        contract.salary = Decimal(salary) if salary else None
        contract.currency = request.form.get('currency', 'GNF')
        contract.position = request.form.get('position')
        contract.department = request.form.get('department')
        contract.status = request.form.get('status')
        contract.updated_at = datetime.now(UTC)
        
        db.session.commit()
        
        log_activity(current_user.id, 'contract_updated', {
            'contract_id': contract.id
        })
        
        flash('Contrat modifié avec succès', 'success')
        return redirect(url_for('rh.contract_detail', contract_id=contract.id))
    
    return render_template('rh/contract_form.html', employee=contract.employee, contract=contract)

# =========================================================
# GESTION DES FORMATIONS
# =========================================================

@rh_bp.route('/employees/<int:employee_id>/trainings')
@login_required
def employee_trainings_list(employee_id):
    """Liste des formations d'un employé"""
    if not has_rh_permission(current_user, 'trainings.read'):
        flash('Accès refusé', 'error')
        return redirect(url_for('rh.employees_list'))
    
    employee = Employee.query.get_or_404(employee_id)
    trainings = employee.trainings.order_by(desc(EmployeeTraining.start_date)).all()
    
    return render_template('rh/trainings_list.html', employee=employee, trainings=trainings)

@rh_bp.route('/employees/<int:employee_id>/trainings/new', methods=['GET', 'POST'])
@login_required
def training_new(employee_id):
    """Créer une nouvelle formation"""
    if not has_rh_permission(current_user, 'trainings.create'):
        flash('Accès refusé', 'error')
        return redirect(url_for('rh.employee_detail', employee_id=employee_id))
    
    employee = Employee.query.get_or_404(employee_id)
    
    if request.method == 'POST':
        training_name = request.form.get('training_name')
        training_type = request.form.get('training_type')
        provider = request.form.get('provider')
        start_date_str = request.form.get('start_date')
        end_date_str = request.form.get('end_date')
        duration_hours = request.form.get('duration_hours')
        cost = request.form.get('cost')
        currency = request.form.get('currency', 'GNF')
        status = request.form.get('status', 'planned')
        certificate_obtained = bool(request.form.get('certificate_obtained'))
        
        if not training_name or not training_type or not start_date_str:
            flash('Veuillez remplir tous les champs obligatoires', 'error')
            return render_template('rh/training_form.html', employee=employee, training=None)
        
        # Validation des dates
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        if end_date_str:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            if end_date < start_date:
                flash('La date de fin doit être postérieure à la date de début', 'error')
                return render_template('rh/training_form.html', employee=employee, training=None)
        
        # Validation de la durée
        if duration_hours:
            try:
                duration = int(duration_hours)
                if duration < 0:
                    flash('La durée ne peut pas être négative', 'error')
                    return render_template('rh/training_form.html', employee=employee, training=None)
            except ValueError:
                flash('La durée doit être un nombre entier valide', 'error')
                return render_template('rh/training_form.html', employee=employee, training=None)
        
        # Validation du coût
        if cost:
            try:
                cost_decimal = Decimal(cost)
                if cost_decimal < 0:
                    flash('Le coût ne peut pas être négatif', 'error')
                    return render_template('rh/training_form.html', employee=employee, training=None)
            except (ValueError, InvalidOperation):
                flash('Le coût doit être un nombre valide', 'error')
                return render_template('rh/training_form.html', employee=employee, training=None)
        
        training = EmployeeTraining(
            employee_id=employee_id,
            training_name=training_name,
            training_type=training_type,
            provider=provider,
            start_date=start_date,
            end_date=datetime.strptime(end_date_str, '%Y-%m-%d').date() if end_date_str else None,
            duration_hours=duration if duration_hours else None,
            cost=cost_decimal if cost else None,
            currency=currency,
            status=status,
            certificate_obtained=certificate_obtained,
            created_by_id=current_user.id
        )
        
        db.session.add(training)
        db.session.commit()
        
        log_activity(current_user.id, 'training_created', {
            'training_id': training.id,
            'employee_id': employee_id
        })
        
        flash(f'Formation {training_name} créée avec succès', 'success')
        return redirect(url_for('rh.employee_trainings_list', employee_id=employee_id))
    
    return render_template('rh/training_form.html', employee=employee, training=None)

@rh_bp.route('/trainings/<int:training_id>/edit', methods=['GET', 'POST'])
@login_required
def training_edit(training_id):
    """Modifier une formation"""
    if not has_rh_permission(current_user, 'trainings.update'):
        flash('Accès refusé', 'error')
        return redirect(url_for('rh.employees_list'))
    
    training = EmployeeTraining.query.get_or_404(training_id)
    
    if request.method == 'POST':
        training.training_name = request.form.get('training_name')
        training.training_type = request.form.get('training_type')
        training.provider = request.form.get('provider')
        training.start_date = datetime.strptime(request.form.get('start_date'), '%Y-%m-%d').date()
        end_date_str = request.form.get('end_date')
        training.end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date() if end_date_str else None
        duration_hours = request.form.get('duration_hours')
        training.duration_hours = int(duration_hours) if duration_hours else None
        cost = request.form.get('cost')
        training.cost = Decimal(cost) if cost else None
        training.currency = request.form.get('currency', 'GNF')
        training.status = request.form.get('status')
        training.certificate_obtained = bool(request.form.get('certificate_obtained'))
        training.updated_at = datetime.now(UTC)
        
        db.session.commit()
        
        log_activity(current_user.id, 'training_updated', {
            'training_id': training.id
        })
        
        flash('Formation modifiée avec succès', 'success')
        return redirect(url_for('rh.employee_trainings_list', employee_id=training.employee_id))
    
    return render_template('rh/training_form.html', employee=training.employee, training=training)

# =========================================================
# GESTION DES ÉVALUATIONS
# =========================================================

@rh_bp.route('/employees/<int:employee_id>/evaluations')
@login_required
def employee_evaluations_list(employee_id):
    """Liste des évaluations d'un employé"""
    if not has_rh_permission(current_user, 'evaluations.read'):
        flash('Accès refusé', 'error')
        return redirect(url_for('rh.employees_list'))
    
    employee = Employee.query.get_or_404(employee_id)
    evaluations = employee.evaluations.order_by(desc(EmployeeEvaluation.evaluation_date)).all()
    
    return render_template('rh/evaluations_list.html', employee=employee, evaluations=evaluations)

@rh_bp.route('/employees/<int:employee_id>/evaluations/new', methods=['GET', 'POST'])
@login_required
def evaluation_new(employee_id):
    """Créer une nouvelle évaluation"""
    if not has_rh_permission(current_user, 'evaluations.create'):
        flash('Accès refusé', 'error')
        return redirect(url_for('rh.employee_detail', employee_id=employee_id))
    
    employee = Employee.query.get_or_404(employee_id)
    
    if request.method == 'POST':
        evaluation_type = request.form.get('evaluation_type')
        evaluation_date_str = request.form.get('evaluation_date')
        evaluator_id = request.form.get('evaluator_id')
        overall_rating = request.form.get('overall_rating')
        overall_score = request.form.get('overall_score')
        strengths = request.form.get('strengths')
        areas_for_improvement = request.form.get('areas_for_improvement')
        goals = request.form.get('goals')
        comments = request.form.get('comments')
        status = request.form.get('status', 'draft')
        
        if not evaluation_type or not evaluation_date_str:
            flash('Veuillez remplir tous les champs obligatoires', 'error')
            users = User.query.filter_by(is_active=True).all()
            return render_template('rh/evaluation_form.html', employee=employee, evaluation=None, users=users)
        
        # Validation de la date
        evaluation_date = datetime.strptime(evaluation_date_str, '%Y-%m-%d').date()
        if evaluation_date > date.today():
            flash('La date d\'évaluation ne peut pas être dans le futur', 'error')
            users = User.query.filter_by(is_active=True).all()
            return render_template('rh/evaluation_form.html', employee=employee, evaluation=None, users=users)
        
        # Validation du score
        if overall_score:
            try:
                score_decimal = Decimal(overall_score)
                if score_decimal < 0 or score_decimal > 100:
                    flash('Le score doit être entre 0 et 100', 'error')
                    users = User.query.filter_by(is_active=True).all()
                    return render_template('rh/evaluation_form.html', employee=employee, evaluation=None, users=users)
            except (ValueError, InvalidOperation):
                flash('Le score doit être un nombre valide', 'error')
                users = User.query.filter_by(is_active=True).all()
                return render_template('rh/evaluation_form.html', employee=employee, evaluation=None, users=users)
        
        evaluation = EmployeeEvaluation(
            employee_id=employee_id,
            evaluation_type=evaluation_type,
            evaluation_date=evaluation_date,
            evaluator_id=int(evaluator_id) if evaluator_id else None,
            overall_rating=overall_rating if overall_rating else None,
            overall_score=score_decimal if overall_score else None,
            strengths=strengths,
            areas_for_improvement=areas_for_improvement,
            goals=goals,
            comments=comments,
            status=status,
            created_by_id=current_user.id
        )
        
        db.session.add(evaluation)
        db.session.commit()
        
        log_activity(current_user.id, 'evaluation_created', {
            'evaluation_id': evaluation.id,
            'employee_id': employee_id
        })
        
        flash('Évaluation créée avec succès', 'success')
        return redirect(url_for('rh.employee_evaluations_list', employee_id=employee_id))
    
    users = User.query.filter_by(is_active=True).all()
    return render_template('rh/evaluation_form.html', employee=employee, evaluation=None, users=users)

@rh_bp.route('/evaluations/<int:evaluation_id>/edit', methods=['GET', 'POST'])
@login_required
def evaluation_edit(evaluation_id):
    """Modifier une évaluation"""
    if not has_rh_permission(current_user, 'evaluations.update'):
        flash('Accès refusé', 'error')
        return redirect(url_for('rh.employees_list'))
    
    evaluation = EmployeeEvaluation.query.get_or_404(evaluation_id)
    
    if request.method == 'POST':
        evaluation.evaluation_type = request.form.get('evaluation_type')
        evaluation.evaluation_date = datetime.strptime(request.form.get('evaluation_date'), '%Y-%m-%d').date()
        evaluator_id = request.form.get('evaluator_id')
        evaluation.evaluator_id = int(evaluator_id) if evaluator_id else None
        evaluation.overall_rating = request.form.get('overall_rating') if request.form.get('overall_rating') else None
        overall_score = request.form.get('overall_score')
        evaluation.overall_score = Decimal(overall_score) if overall_score else None
        evaluation.strengths = request.form.get('strengths')
        evaluation.areas_for_improvement = request.form.get('areas_for_improvement')
        evaluation.goals = request.form.get('goals')
        evaluation.comments = request.form.get('comments')
        evaluation.status = request.form.get('status')
        evaluation.updated_at = datetime.now(UTC)
        
        db.session.commit()
        
        log_activity(current_user.id, 'evaluation_updated', {
            'evaluation_id': evaluation.id
        })
        
        flash('Évaluation modifiée avec succès', 'success')
        return redirect(url_for('rh.employee_evaluations_list', employee_id=evaluation.employee_id))
    
    users = User.query.filter_by(is_active=True).all()
    return render_template('rh/evaluation_form.html', employee=evaluation.employee, evaluation=evaluation, users=users)

# =========================================================
# GESTION DES ABSENCES
# =========================================================

@rh_bp.route('/employees/<int:employee_id>/absences')
@login_required
def employee_absences_list(employee_id):
    """Liste des absences d'un employé"""
    if not has_rh_permission(current_user, 'absences.read'):
        flash('Accès refusé', 'error')
        return redirect(url_for('rh.employees_list'))
    
    employee = Employee.query.get_or_404(employee_id)
    absences = employee.absences.order_by(desc(EmployeeAbsence.start_date)).all()
    
    return render_template('rh/absences_list.html', employee=employee, absences=absences)

@rh_bp.route('/employees/<int:employee_id>/absences/new', methods=['GET', 'POST'])
@login_required
def absence_new(employee_id):
    """Créer une nouvelle absence"""
    if not has_rh_permission(current_user, 'absences.create'):
        flash('Accès refusé', 'error')
        return redirect(url_for('rh.employee_detail', employee_id=employee_id))
    
    employee = Employee.query.get_or_404(employee_id)
    
    if request.method == 'POST':
        absence_type = request.form.get('absence_type')
        start_date_str = request.form.get('start_date')
        end_date_str = request.form.get('end_date')
        reason = request.form.get('reason')
        status = request.form.get('status', 'pending')
        
        if not absence_type or not start_date_str or not end_date_str:
            flash('Veuillez remplir tous les champs obligatoires', 'error')
            return render_template('rh/absence_form.html', employee=employee, absence=None)
        
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        
        # Validation des dates
        if end_date < start_date:
            flash('La date de fin doit être postérieure à la date de début', 'error')
            return render_template('rh/absence_form.html', employee=employee, absence=None)
        
        # Calculer le nombre de jours
        days_count = (end_date - start_date).days + 1
        if days_count < 1:
            flash('La durée de l\'absence doit être d\'au moins 1 jour', 'error')
            return render_template('rh/absence_form.html', employee=employee, absence=None)
        
        absence = EmployeeAbsence(
            employee_id=employee_id,
            absence_type=absence_type,
            start_date=start_date,
            end_date=end_date,
            days_count=days_count,
            reason=reason,
            status=status,
            created_by_id=current_user.id
        )
        
        db.session.add(absence)
        db.session.commit()
        
        log_activity(current_user.id, 'absence_created', {
            'absence_id': absence.id,
            'employee_id': employee_id
        })
        
        flash('Absence créée avec succès', 'success')
        return redirect(url_for('rh.employee_absences_list', employee_id=employee_id))
    
    return render_template('rh/absence_form.html', employee=employee, absence=None)

@rh_bp.route('/absences/<int:absence_id>/edit', methods=['GET', 'POST'])
@login_required
def absence_edit(absence_id):
    """Modifier une absence"""
    if not has_rh_permission(current_user, 'absences.update'):
        flash('Accès refusé', 'error')
        return redirect(url_for('rh.employees_list'))
    
    absence = EmployeeAbsence.query.get_or_404(absence_id)
    
    if request.method == 'POST':
        absence.absence_type = request.form.get('absence_type')
        absence.start_date = datetime.strptime(request.form.get('start_date'), '%Y-%m-%d').date()
        absence.end_date = datetime.strptime(request.form.get('end_date'), '%Y-%m-%d').date()
        absence.days_count = (absence.end_date - absence.start_date).days + 1
        absence.reason = request.form.get('reason')
        absence.status = request.form.get('status')
        absence.updated_at = datetime.now(UTC)
        
        db.session.commit()
        
        log_activity(current_user.id, 'absence_updated', {
            'absence_id': absence.id
        })
        
        flash('Absence modifiée avec succès', 'success')
        return redirect(url_for('rh.employee_absences_list', employee_id=absence.employee_id))
    
    return render_template('rh/absence_form.html', employee=absence.employee, absence=absence)

@rh_bp.route('/absences/<int:absence_id>/approve', methods=['POST'])
@login_required
def absence_approve(absence_id):
    """Approuver une absence"""
    if not has_rh_permission(current_user, 'absences.update'):
        flash('Accès refusé', 'error')
        return redirect(url_for('rh.employees_list'))
    
    absence = EmployeeAbsence.query.get_or_404(absence_id)
    absence.status = 'approved'
    absence.approved_by_id = current_user.id
    absence.approved_at = datetime.now(UTC)
    absence.updated_at = datetime.now(UTC)
    
    db.session.commit()
    
    log_activity(current_user.id, 'absence_approved', {
        'absence_id': absence.id
    })
    
    flash('Absence approuvée avec succès', 'success')
    return redirect(url_for('rh.employee_absences_list', employee_id=absence.employee_id))

@rh_bp.route('/absences/<int:absence_id>/reject', methods=['POST'])
@login_required
def absence_reject(absence_id):
    """Rejeter une absence"""
    if not has_rh_permission(current_user, 'absences.update'):
        flash('Accès refusé', 'error')
        return redirect(url_for('rh.employees_list'))
    
    absence = EmployeeAbsence.query.get_or_404(absence_id)
    absence.status = 'rejected'
    absence.rejection_reason = request.form.get('rejection_reason', '')
    absence.approved_by_id = current_user.id
    absence.approved_at = datetime.now(UTC)
    absence.updated_at = datetime.now(UTC)
    
    db.session.commit()
    
    log_activity(current_user.id, 'absence_rejected', {
        'absence_id': absence.id
    })
    
    flash('Absence rejetée', 'success')
    return redirect(url_for('rh.employee_absences_list', employee_id=absence.employee_id))

# =========================================================
# FONCTIONS UTILITAIRES
# =========================================================

def log_activity(user_id, action, metadata=None):
    """Enregistrer une activité utilisateur"""
    try:
        activity = UserActivityLog(
            user_id=user_id,
            action=action,
            activity_metadata=metadata if metadata else {},
            created_at=datetime.now(UTC)
        )
        db.session.add(activity)
        db.session.commit()
    except Exception as e:
        # Ne pas bloquer l'application si le logging échoue
        print(f"Erreur lors de l'enregistrement de l'activité: {e}")
        db.session.rollback()

