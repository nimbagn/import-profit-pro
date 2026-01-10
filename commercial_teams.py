#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module Gestion des Équipes Commerciales - Import Profit Pro
Gestion des équipes lockistes, vendeurs et promotion
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from datetime import datetime, UTC
from models import (
    db, LockisteTeam, LockisteMember, VendeurTeam, VendeurMember,
    PromotionTeam, PromotionMember, User, Region, Role
)
from auth import has_permission
from sqlalchemy.orm import joinedload
from utils_region_filter import (
    get_user_region_id, get_user_accessible_regions, filter_teams_by_region,
    filter_lockiste_teams_by_region, filter_vendeur_teams_by_region
)

def get_commercial_users():
    """Retourne la liste des utilisateurs commerciaux actifs de la plateforme"""
    commercial_role = Role.query.filter_by(code='commercial').first()
    if commercial_role:
        return User.query.filter_by(role_id=commercial_role.id, is_active=True).all()
    return []

# Créer le blueprint
commercial_teams_bp = Blueprint('commercial_teams', __name__, url_prefix='/commercial-teams')

# =========================================================
# ROUTES GÉNÉRALES
# =========================================================

@commercial_teams_bp.route('/')
@login_required
def index():
    """Page d'accueil des équipes commerciales"""
    if not has_permission(current_user, 'commercial_teams.read'):
        flash("Vous n'avez pas la permission d'accéder à cette page.", "error")
        return redirect(url_for('index'))
    
    return render_template('commercial_teams/index.html')

# =========================================================
# GESTION DES ÉQUIPES PROMOTION
# =========================================================

@commercial_teams_bp.route('/promotion')
@login_required
def promotion_teams_list():
    """Liste des équipes promotion"""
    if not has_permission(current_user, 'commercial_teams.read'):
        flash("Vous n'avez pas la permission d'accéder à cette page.", "error")
        return redirect(url_for('index'))
    
    # Filtrer par région si nécessaire
    teams_query = PromotionTeam.query.filter_by(is_active=True)
    teams_query = filter_teams_by_region(teams_query)
    teams = teams_query.options(
        joinedload(PromotionTeam.team_leader),
        joinedload(PromotionTeam.supervisor)
    ).all()
    
    return render_template('commercial_teams/teams_list.html', 
                         teams=teams, team_type='promotion')

# =========================================================
# GESTION DES ÉQUIPES LOCKISTES
# =========================================================

@commercial_teams_bp.route('/lockistes')
@login_required
def lockiste_teams_list():
    """Liste des équipes lockistes"""
    if not has_permission(current_user, 'commercial_teams.read'):
        flash("Vous n'avez pas la permission d'accéder à cette page.", "error")
        return redirect(url_for('index'))
    
    # Filtrer par région (sauf admin/supervisor)
    teams_query = LockisteTeam.query.filter_by(is_active=True)
    teams_query = filter_lockiste_teams_by_region(teams_query)
    
    teams = teams_query.options(
        joinedload(LockisteTeam.team_leader),
        joinedload(LockisteTeam.supervisor),
        joinedload(LockisteTeam.region)
    ).all()
    
    return render_template('commercial_teams/teams_list.html', 
                         teams=teams, team_type='lockiste')

@commercial_teams_bp.route('/lockistes/new', methods=['GET', 'POST'])
@login_required
def lockiste_team_new():
    """Créer une nouvelle équipe lockiste"""
    if not has_permission(current_user, 'commercial_teams.write'):
        flash("Vous n'avez pas la permission de créer une équipe.", "error")
        return redirect(url_for('commercial_teams.lockiste_teams_list'))
    
    if request.method == 'POST':
        try:
            team = LockisteTeam(
                name=request.form.get('name'),
                description=request.form.get('description'),
                region_id=int(request.form.get('region_id')) if request.form.get('region_id') else None,
                team_leader_id=int(request.form.get('team_leader_id')),
                supervisor_id=int(request.form.get('supervisor_id')) if request.form.get('supervisor_id') else None,
                is_active=True
            )
            db.session.add(team)
            db.session.commit()
            flash("Équipe lockiste créée avec succès!", "success")
            return redirect(url_for('commercial_teams.lockiste_team_detail', id=team.id))
        except Exception as e:
            db.session.rollback()
            flash(f"Erreur lors de la création: {str(e)}", "error")
    
    # Récupérer les utilisateurs et régions
    users = User.query.filter_by(is_active=True).all()
    regions = Region.query.all()
    return render_template('commercial_teams/team_form.html', 
                         team=None, team_type='lockiste', users=users, regions=regions)

@commercial_teams_bp.route('/lockistes/<int:id>')
@login_required
def lockiste_team_detail(id):
    """Détails d'une équipe lockiste"""
    if not has_permission(current_user, 'commercial_teams.read'):
        flash("Vous n'avez pas la permission d'accéder à cette page.", "error")
        return redirect(url_for('index'))
    
    team = LockisteTeam.query.options(
        joinedload(LockisteTeam.team_leader),
        joinedload(LockisteTeam.supervisor),
        joinedload(LockisteTeam.region),
        joinedload(LockisteTeam.members)
    ).get_or_404(id)
    
    return render_template('commercial_teams/team_detail.html', 
                         team=team, team_type='lockiste')

@commercial_teams_bp.route('/lockistes/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def lockiste_team_edit(id):
    """Modifier une équipe lockiste"""
    if not has_permission(current_user, 'commercial_teams.write'):
        flash("Vous n'avez pas la permission de modifier une équipe.", "error")
        return redirect(url_for('commercial_teams.lockiste_team_detail', id=id))
    
    team = LockisteTeam.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            team.name = request.form.get('name')
            team.description = request.form.get('description')
            team.region_id = int(request.form.get('region_id')) if request.form.get('region_id') else None
            team.team_leader_id = int(request.form.get('team_leader_id'))
            team.supervisor_id = int(request.form.get('supervisor_id')) if request.form.get('supervisor_id') else None
            team.is_active = request.form.get('is_active') == 'on'
            db.session.commit()
            flash("Équipe modifiée avec succès!", "success")
            return redirect(url_for('commercial_teams.lockiste_team_detail', id=team.id))
        except Exception as e:
            db.session.rollback()
            flash(f"Erreur lors de la modification: {str(e)}", "error")
    
    users = User.query.filter_by(is_active=True).all()
    regions = Region.query.all()
    return render_template('commercial_teams/team_form.html', 
                         team=team, team_type='lockiste', users=users, regions=regions)

@commercial_teams_bp.route('/lockistes/<int:team_id>/members')
@login_required
def lockiste_members_list(team_id):
    """Liste des membres d'une équipe lockiste"""
    if not has_permission(current_user, 'commercial_teams.read'):
        flash("Vous n'avez pas la permission d'accéder à cette page.", "error")
        return redirect(url_for('index'))
    
    team = LockisteTeam.query.get_or_404(team_id)
    members = LockisteMember.query.filter_by(team_id=team_id).all()
    
    return render_template('commercial_teams/members_list.html', 
                         team=team, members=members, team_type='lockiste')

@commercial_teams_bp.route('/lockistes/<int:team_id>/members/new', methods=['GET', 'POST'])
@login_required
def lockiste_member_new(team_id):
    """Ajouter un membre à une équipe lockiste"""
    if not has_permission(current_user, 'commercial_teams.write'):
        flash("Vous n'avez pas la permission d'ajouter un membre.", "error")
        return redirect(url_for('commercial_teams.lockiste_members_list', team_id=team_id))
    
    team = LockisteTeam.query.get_or_404(team_id)
    
    if request.method == 'POST':
        try:
            user_id = request.form.get('user_id')
            if not user_id:
                flash("Veuillez sélectionner un utilisateur commercial.", "error")
                return redirect(url_for('commercial_teams.lockiste_member_new', team_id=team_id))
            
            user_id = int(user_id)
            user = User.query.get_or_404(user_id)
            
            # Vérifier si l'utilisateur est déjà membre de cette équipe
            existing_member = LockisteMember.query.filter_by(team_id=team_id, user_id=user_id).first()
            if existing_member:
                flash(f"L'utilisateur {user.full_name or user.username} est déjà membre de cette équipe.", "error")
                return redirect(url_for('commercial_teams.lockiste_member_new', team_id=team_id))
            
            member = LockisteMember(
                team_id=team_id,
                user_id=user_id,
                full_name=user.full_name or user.username,
                phone=user.phone or '',
                email=user.email or '',
                is_active=True
            )
            db.session.add(member)
            db.session.commit()
            flash("Membre ajouté avec succès!", "success")
            return redirect(url_for('commercial_teams.lockiste_members_list', team_id=team_id))
        except Exception as e:
            db.session.rollback()
            flash(f"Erreur lors de l'ajout: {str(e)}", "error")
    
    # Récupérer uniquement les utilisateurs commerciaux non encore membres de cette équipe
    commercial_users = get_commercial_users()
    existing_member_ids = [m.user_id for m in LockisteMember.query.filter_by(team_id=team_id).all() if m.user_id]
    available_users = [u for u in commercial_users if u.id not in existing_member_ids]
    
    return render_template('commercial_teams/member_form.html', 
                         team=team, member=None, team_type='lockiste', users=available_users)

@commercial_teams_bp.route('/lockistes/members/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def lockiste_member_edit(id):
    """Modifier un membre lockiste"""
    if not has_permission(current_user, 'commercial_teams.write'):
        flash("Vous n'avez pas la permission de modifier un membre.", "error")
        return redirect(url_for('index'))
    
    member = LockisteMember.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            user_id = request.form.get('user_id')
            if not user_id:
                flash("Veuillez sélectionner un utilisateur commercial.", "error")
                return redirect(url_for('commercial_teams.lockiste_member_edit', id=id))
            
            user_id = int(user_id)
            user = User.query.get_or_404(user_id)
            
            # Si l'utilisateur change, vérifier qu'il n'est pas déjà membre
            if member.user_id != user_id:
                existing_member = LockisteMember.query.filter_by(team_id=member.team_id, user_id=user_id).first()
                if existing_member and existing_member.id != member.id:
                    flash(f"L'utilisateur {user.full_name or user.username} est déjà membre de cette équipe.", "error")
                    return redirect(url_for('commercial_teams.lockiste_member_edit', id=id))
            
            # Mettre à jour depuis l'utilisateur sélectionné
            member.user_id = user_id
            member.full_name = user.full_name or user.username
            member.phone = user.phone or ''
            member.email = user.email or ''
            member.is_active = request.form.get('is_active') == 'on'
            if not member.is_active and not member.left_at:
                member.left_at = datetime.now(UTC)
            elif member.is_active:
                member.left_at = None
            db.session.commit()
            flash("Membre modifié avec succès!", "success")
            return redirect(url_for('commercial_teams.lockiste_members_list', team_id=member.team_id))
        except Exception as e:
            db.session.rollback()
            flash(f"Erreur lors de la modification: {str(e)}", "error")
    
    # Récupérer uniquement les utilisateurs commerciaux (inclure celui déjà sélectionné)
    commercial_users = get_commercial_users()
    existing_member_ids = [m.user_id for m in LockisteMember.query.filter_by(team_id=member.team_id).all() if m.user_id and m.id != member.id]
    available_users = [u for u in commercial_users if u.id not in existing_member_ids or u.id == member.user_id]
    
    return render_template('commercial_teams/member_form.html', 
                         team=member.team, member=member, team_type='lockiste', users=available_users)

# =========================================================
# GESTION DES ÉQUIPES VANDEURS
# =========================================================

@commercial_teams_bp.route('/vendeurs')
@login_required
def vendeur_teams_list():
    """Liste des équipes vendeurs"""
    if not has_permission(current_user, 'commercial_teams.read'):
        flash("Vous n'avez pas la permission d'accéder à cette page.", "error")
        return redirect(url_for('index'))
    
    # Filtrer par région
    region_id = get_user_region_id()
    teams_query = VendeurTeam.query.filter_by(is_active=True)
    # Filtrer par région (sauf admin/supervisor)
    teams_query = filter_vendeur_teams_by_region(teams_query)
    
    teams = teams_query.options(
        joinedload(VendeurTeam.team_leader),
        joinedload(VendeurTeam.supervisor),
        joinedload(VendeurTeam.region)
    ).all()
    
    return render_template('commercial_teams/teams_list.html', 
                         teams=teams, team_type='vendeur')

@commercial_teams_bp.route('/vendeurs/new', methods=['GET', 'POST'])
@login_required
def vendeur_team_new():
    """Créer une nouvelle équipe vendeur"""
    if not has_permission(current_user, 'commercial_teams.write'):
        flash("Vous n'avez pas la permission de créer une équipe.", "error")
        return redirect(url_for('commercial_teams.vendeur_teams_list'))
    
    if request.method == 'POST':
        try:
            team = VendeurTeam(
                name=request.form.get('name'),
                description=request.form.get('description'),
                region_id=int(request.form.get('region_id')) if request.form.get('region_id') else None,
                team_leader_id=int(request.form.get('team_leader_id')),
                supervisor_id=int(request.form.get('supervisor_id')) if request.form.get('supervisor_id') else None,
                is_active=True
            )
            db.session.add(team)
            db.session.commit()
            flash("Équipe vendeur créée avec succès!", "success")
            return redirect(url_for('commercial_teams.vendeur_team_detail', id=team.id))
        except Exception as e:
            db.session.rollback()
            flash(f"Erreur lors de la création: {str(e)}", "error")
    
    users = User.query.filter_by(is_active=True).all()
    regions = Region.query.all()
    return render_template('commercial_teams/team_form.html', 
                         team=None, team_type='vendeur', users=users, regions=regions)

@commercial_teams_bp.route('/vendeurs/<int:id>')
@login_required
def vendeur_team_detail(id):
    """Détails d'une équipe vendeur"""
    if not has_permission(current_user, 'commercial_teams.read'):
        flash("Vous n'avez pas la permission d'accéder à cette page.", "error")
        return redirect(url_for('index'))
    
    team = VendeurTeam.query.options(
        joinedload(VendeurTeam.team_leader),
        joinedload(VendeurTeam.supervisor),
        joinedload(VendeurTeam.region),
        joinedload(VendeurTeam.members)
    ).get_or_404(id)
    
    return render_template('commercial_teams/team_detail.html', 
                         team=team, team_type='vendeur')

@commercial_teams_bp.route('/vendeurs/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def vendeur_team_edit(id):
    """Modifier une équipe vendeur"""
    if not has_permission(current_user, 'commercial_teams.write'):
        flash("Vous n'avez pas la permission de modifier une équipe.", "error")
        return redirect(url_for('commercial_teams.vendeur_team_detail', id=id))
    
    team = VendeurTeam.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            team.name = request.form.get('name')
            team.description = request.form.get('description')
            team.region_id = int(request.form.get('region_id')) if request.form.get('region_id') else None
            team.team_leader_id = int(request.form.get('team_leader_id'))
            team.supervisor_id = int(request.form.get('supervisor_id')) if request.form.get('supervisor_id') else None
            team.is_active = request.form.get('is_active') == 'on'
            db.session.commit()
            flash("Équipe modifiée avec succès!", "success")
            return redirect(url_for('commercial_teams.vendeur_team_detail', id=team.id))
        except Exception as e:
            db.session.rollback()
            flash(f"Erreur lors de la modification: {str(e)}", "error")
    
    users = User.query.filter_by(is_active=True).all()
    regions = Region.query.all()
    return render_template('commercial_teams/team_form.html', 
                         team=team, team_type='vendeur', users=users, regions=regions)

@commercial_teams_bp.route('/vendeurs/<int:team_id>/members')
@login_required
def vendeur_members_list(team_id):
    """Liste des membres d'une équipe vendeur"""
    if not has_permission(current_user, 'commercial_teams.read'):
        flash("Vous n'avez pas la permission d'accéder à cette page.", "error")
        return redirect(url_for('index'))
    
    team = VendeurTeam.query.get_or_404(team_id)
    members = VendeurMember.query.filter_by(team_id=team_id).all()
    
    return render_template('commercial_teams/members_list.html', 
                         team=team, members=members, team_type='vendeur')

@commercial_teams_bp.route('/vendeurs/<int:team_id>/members/new', methods=['GET', 'POST'])
@login_required
def vendeur_member_new(team_id):
    """Ajouter un membre à une équipe vendeur"""
    if not has_permission(current_user, 'commercial_teams.write'):
        flash("Vous n'avez pas la permission d'ajouter un membre.", "error")
        return redirect(url_for('commercial_teams.vendeur_members_list', team_id=team_id))
    
    team = VendeurTeam.query.get_or_404(team_id)
    
    if request.method == 'POST':
        try:
            user_id = request.form.get('user_id')
            if not user_id:
                flash("Veuillez sélectionner un utilisateur commercial.", "error")
                return redirect(url_for('commercial_teams.vendeur_member_new', team_id=team_id))
            
            user_id = int(user_id)
            user = User.query.get_or_404(user_id)
            
            # Vérifier si l'utilisateur est déjà membre de cette équipe
            existing_member = VendeurMember.query.filter_by(team_id=team_id, user_id=user_id).first()
            if existing_member:
                flash(f"L'utilisateur {user.full_name or user.username} est déjà membre de cette équipe.", "error")
                return redirect(url_for('commercial_teams.vendeur_member_new', team_id=team_id))
            
            member = VendeurMember(
                team_id=team_id,
                user_id=user_id,
                full_name=user.full_name or user.username,
                phone=user.phone or '',
                email=user.email or '',
                is_active=True
            )
            db.session.add(member)
            db.session.commit()
            flash("Membre ajouté avec succès!", "success")
            return redirect(url_for('commercial_teams.vendeur_members_list', team_id=team_id))
        except Exception as e:
            db.session.rollback()
            flash(f"Erreur lors de l'ajout: {str(e)}", "error")
    
    # Récupérer uniquement les utilisateurs commerciaux non encore membres de cette équipe
    commercial_users = get_commercial_users()
    existing_member_ids = [m.user_id for m in VendeurMember.query.filter_by(team_id=team_id).all() if m.user_id]
    available_users = [u for u in commercial_users if u.id not in existing_member_ids]
    
    return render_template('commercial_teams/member_form.html', 
                         team=team, member=None, team_type='vendeur', users=available_users)

@commercial_teams_bp.route('/vendeurs/members/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def vendeur_member_edit(id):
    """Modifier un membre vendeur"""
    if not has_permission(current_user, 'commercial_teams.write'):
        flash("Vous n'avez pas la permission de modifier un membre.", "error")
        return redirect(url_for('index'))
    
    member = VendeurMember.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            user_id = request.form.get('user_id')
            if not user_id:
                flash("Veuillez sélectionner un utilisateur commercial.", "error")
                return redirect(url_for('commercial_teams.vendeur_member_edit', id=id))
            
            user_id = int(user_id)
            user = User.query.get_or_404(user_id)
            
            # Si l'utilisateur change, vérifier qu'il n'est pas déjà membre
            if member.user_id != user_id:
                existing_member = VendeurMember.query.filter_by(team_id=member.team_id, user_id=user_id).first()
                if existing_member and existing_member.id != member.id:
                    flash(f"L'utilisateur {user.full_name or user.username} est déjà membre de cette équipe.", "error")
                    return redirect(url_for('commercial_teams.vendeur_member_edit', id=id))
            
            # Mettre à jour depuis l'utilisateur sélectionné
            member.user_id = user_id
            member.full_name = user.full_name or user.username
            member.phone = user.phone or ''
            member.email = user.email or ''
            member.is_active = request.form.get('is_active') == 'on'
            if not member.is_active and not member.left_at:
                member.left_at = datetime.now(UTC)
            elif member.is_active:
                member.left_at = None
            db.session.commit()
            flash("Membre modifié avec succès!", "success")
            return redirect(url_for('commercial_teams.vendeur_members_list', team_id=member.team_id))
        except Exception as e:
            db.session.rollback()
            flash(f"Erreur lors de la modification: {str(e)}", "error")
    
    # Récupérer uniquement les utilisateurs commerciaux (inclure celui déjà sélectionné)
    commercial_users = get_commercial_users()
    existing_member_ids = [m.user_id for m in VendeurMember.query.filter_by(team_id=member.team_id).all() if m.user_id and m.id != member.id]
    available_users = [u for u in commercial_users if u.id not in existing_member_ids or u.id == member.user_id]
    
    return render_template('commercial_teams/member_form.html', 
                         team=member.team, member=member, team_type='vendeur', users=available_users)

