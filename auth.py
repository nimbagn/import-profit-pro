#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module d'authentification - Import Profit Pro
Gestion des utilisateurs, rôles et permissions
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, UTC
from models import db, User, Role, Region, UserActivityLog
import re
import os

# Créer le blueprint
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

# Initialiser Flask-Login (sera fait dans app.py)
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Veuillez vous connecter pour accéder à cette page.'
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    """Charger l'utilisateur depuis la base de données"""
    return User.query.get(int(user_id))

# Rate limiting pour la protection contre les attaques brute force
limiter = None

def init_rate_limiter(app):
    """Initialise le rate limiter"""
    global limiter
    try:
        from flask_limiter import Limiter
        from flask_limiter.util import get_remote_address
        
        limiter = Limiter(
            app=app,
            key_func=get_remote_address,
            default_limits=["200 per day", "50 per hour"],
            storage_uri=os.getenv('RATELIMIT_STORAGE_URL', 'memory://')
        )
        print("✅ Rate limiting activé")
        return limiter
    except ImportError:
        print("⚠️  Flask-Limiter non installé. Rate limiting désactivé.")
        print("   Installez avec: pip install Flask-Limiter")
        limiter = None
        return None

# Routes d'authentification
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Page de connexion"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = bool(request.form.get('remember'))
        
        if not username or not password:
            flash('Veuillez remplir tous les champs', 'error')
            return render_template('auth/login.html')
        
        # Chercher l'utilisateur
        user = User.query.filter_by(username=username).first()
        
        # Debug logging (amélioré pour être plus visible)
        import sys
        print("=" * 70, file=sys.stderr)
        print(f"🔐 TENTATIVE DE CONNEXION - Username: '{username}'", file=sys.stderr)
        print("=" * 70, file=sys.stderr)
        
        if not user:
            print(f"❌ ERREUR: Utilisateur '{username}' NON TROUVÉ dans la base de données", file=sys.stderr)
            print(f"   → Action: Créer l'utilisateur avec: mysql -u root -p madargn < CREER_ADMIN.sql", file=sys.stderr)
        elif not user.password_hash:
            print(f"❌ ERREUR: Utilisateur '{username}' trouvé mais PAS DE PASSWORD_HASH", file=sys.stderr)
            print(f"   → Action: Réinitialiser le hash avec: mysql -u root -p madargn < CREER_ADMIN.sql", file=sys.stderr)
        elif not check_password_hash(user.password_hash, password):
            print(f"❌ ERREUR: Hash du mot de passe INVALIDE pour '{username}'", file=sys.stderr)
            print(f"   Hash stocké: {user.password_hash[:50]}...", file=sys.stderr)
            print(f"   → Action: Réinitialiser le hash avec: mysql -u root -p madargn < CREER_ADMIN.sql", file=sys.stderr)
        else:
            print(f"✅ SUCCÈS: Utilisateur '{username}' trouvé et mot de passe VALIDE", file=sys.stderr)
            print(f"   User ID: {user.id}, Email: {user.email}, Role: {user.role.code if user.role else 'N/A'}", file=sys.stderr)
        
        print("=" * 70, file=sys.stderr)
        
        if user and check_password_hash(user.password_hash, password):
            if not user.is_active:
                flash('Votre compte est désactivé. Contactez un administrateur.', 'error')
                return render_template('auth/login.html')
            
            # Mettre à jour la dernière connexion
            user.last_login = datetime.now(UTC)
            db.session.commit()
            
            # Logger la connexion
            try:
                # request est déjà importé en haut du fichier
                activity = UserActivityLog(
                    user_id=user.id,
                    action='login',
                    module='auth',
                    ip_address=request.remote_addr,
                    user_agent=request.headers.get('User-Agent', ''),
                    created_at=datetime.now(UTC)
                )
                db.session.add(activity)
                db.session.commit()
            except Exception as e:
                # Ne pas bloquer la connexion si le logging échoue
                print(f"Erreur lors de l'enregistrement de la connexion: {e}")
                db.session.rollback()
            
            # Connecter l'utilisateur
            login_user(user, remember=remember)
            
            # Rediriger selon le rôle
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            
            # Redirection par défaut selon le rôle
            if user.role and user.role.code == 'admin':
                return redirect(url_for('index'))
            elif user.role and user.role.code == 'supervisor':
                return redirect(url_for('index'))
            elif user.role and user.role.code == 'warehouse':
                return redirect(url_for('index'))
            elif user.role and user.role.code == 'commercial':
                return redirect(url_for('index'))
            else:
                return redirect(url_for('index'))
        else:
            flash('Nom d\'utilisateur ou mot de passe incorrect', 'error')
    
    return render_template('auth/login.html')

# Fonction pour appliquer le rate limiting après initialisation
def apply_login_rate_limit():
    """Applique le rate limiting sur la route login après initialisation"""
    global limiter
    if limiter:
        try:
            # Utiliser une approche différente : wrapper la fonction existante
            original_login = login
            
            # Créer une fonction wrapper avec rate limiting
            @limiter.limit("5 per minute", error_message="Trop de tentatives de connexion. Réessayez dans une minute.")
            def rate_limited_login(*args, **kwargs):
                return original_login(*args, **kwargs)
            
            # Remplacer la fonction dans le blueprint
            auth_bp.view_functions['login'] = rate_limited_login
            print("✅ Rate limiting appliqué sur /auth/login (5 tentatives/minute)")
        except Exception as e:
            print(f"⚠️  Erreur lors de l'application du rate limiting: {e}")
            # Le rate limiting n'est pas critique, on continue sans
            import traceback
            traceback.print_exc()

@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Page de réinitialisation de mot de passe"""
    return _forgot_password_handler()

def _forgot_password_handler():
    """Gestionnaire principal de la réinitialisation de mot de passe"""
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        
        if not email:
            flash('Veuillez entrer votre adresse email', 'error')
            return render_template('auth/forgot_password.html')
        
        # Valider le format de l'email
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            flash('Adresse email invalide', 'error')
            return render_template('auth/forgot_password.html')
        
        # Chercher l'utilisateur par email
        user = User.query.filter_by(email=email).first()
        
        # Pour des raisons de sécurité, on ne révèle pas si l'email existe ou non
        # On affiche toujours le même message de succès
        if user and user.is_active:
            try:
                # Importer les fonctions d'email
                from email_utils import create_password_reset_token, send_password_reset_email
                
                # Créer le token de réinitialisation
                token = create_password_reset_token(user.id)
                
                # Envoyer l'email
                email_sent = send_password_reset_email(user, token)
                
                if email_sent:
                    flash('Si un compte existe avec cette adresse email, vous recevrez un lien de réinitialisation dans quelques instants.', 'success')
                else:
                    # Si l'envoi d'email échoue, on affiche quand même le message de succès
                    # pour ne pas révéler si l'email existe
                    flash('Si un compte existe avec cette adresse email, vous recevrez un lien de réinitialisation dans quelques instants.', 'success')
                    # Logger l'erreur pour le débogage
                    import sys
                    print(f"⚠️  Erreur lors de l'envoi de l'email de réinitialisation pour {email}", file=sys.stderr)
            except Exception as e:
                # En cas d'erreur, on affiche quand même le message de succès
                flash('Si un compte existe avec cette adresse email, vous recevrez un lien de réinitialisation dans quelques instants.', 'success')
                import sys
                print(f"⚠️  Erreur lors de la création du token de réinitialisation: {e}", file=sys.stderr)
        else:
            # Même si l'utilisateur n'existe pas, on affiche le message de succès
            flash('Si un compte existe avec cette adresse email, vous recevrez un lien de réinitialisation dans quelques instants.', 'success')
        
        return render_template('auth/forgot_password.html', success=True)
    
    return render_template('auth/forgot_password.html')

@auth_bp.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    """Page de réinitialisation de mot de passe avec token"""
    token = request.args.get('token') or request.form.get('token')
    
    if not token:
        flash('Token de réinitialisation manquant ou invalide', 'error')
        return redirect(url_for('auth.forgot_password'))
    
    # Vérifier le token
    from email_utils import verify_reset_token
    reset_token = verify_reset_token(token)
    
    if not reset_token:
        flash('Token de réinitialisation invalide ou expiré. Veuillez demander un nouveau lien.', 'error')
        return redirect(url_for('auth.forgot_password'))
    
    user = reset_token.user
    if not user or not user.is_active:
        flash('Compte utilisateur invalide ou désactivé', 'error')
        return redirect(url_for('auth.forgot_password'))
    
    if request.method == 'POST':
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        if not new_password or not confirm_password:
            flash('Veuillez remplir tous les champs', 'error')
            return render_template('auth/reset_password.html', token=token, user=user)
        
        if new_password != confirm_password:
            flash('Les mots de passe ne correspondent pas', 'error')
            return render_template('auth/reset_password.html', token=token, user=user)
        
        # Validation du mot de passe fort (même règles que lors de l'inscription)
        password_errors = []
        if len(new_password) < 8:
            password_errors.append("au moins 8 caractères")
        if not re.search(r'[A-Z]', new_password):
            password_errors.append("au moins une majuscule")
        if not re.search(r'[a-z]', new_password):
            password_errors.append("au moins une minuscule")
        if not re.search(r'\d', new_password):
            password_errors.append("au moins un chiffre")
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', new_password):
            password_errors.append("au moins un caractère spécial (!@#$%^&*...)")
        
        if password_errors:
            flash(f'Le mot de passe doit contenir : {", ".join(password_errors)}', 'error')
            return render_template('auth/reset_password.html', token=token, user=user)
        
        # Vérifier à nouveau que le token est toujours valide (protection contre les attaques)
        reset_token = verify_reset_token(token)
        if not reset_token or reset_token.user_id != user.id:
            flash('Token de réinitialisation invalide ou expiré. Veuillez demander un nouveau lien.', 'error')
            return redirect(url_for('auth.forgot_password'))
        
        # Mettre à jour le mot de passe
        user.password_hash = generate_password_hash(new_password)
        user.updated_at = datetime.now(UTC)
        
        # Marquer le token comme utilisé
        reset_token.used = True
        reset_token.updated_at = datetime.now(UTC)
        
        db.session.commit()
        
        flash('Votre mot de passe a été réinitialisé avec succès. Vous pouvez maintenant vous connecter.', 'success')
        return redirect(url_for('auth.login'))
    
    # GET: Afficher le formulaire
    return render_template('auth/reset_password.html', token=token, user=user)

@auth_bp.route('/logout')
@login_required
def logout():
    """Déconnexion"""
    # Logger la déconnexion avant de déconnecter
    try:
        # request est déjà importé en haut du fichier
        activity = UserActivityLog(
            user_id=current_user.id,
            action='logout',
            module='auth',
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent', ''),
            created_at=datetime.now(UTC)
        )
        db.session.add(activity)
        db.session.commit()
    except Exception as e:
        # Ne pas bloquer la déconnexion si le logging échoue
        print(f"Erreur lors de l'enregistrement de la déconnexion: {e}")
        db.session.rollback()
    
    logout_user()
    flash('Vous avez été déconnecté avec succès', 'success')
    return redirect(url_for('auth.login'))

@auth_bp.route('/register', methods=['GET', 'POST'])
@login_required
def register():
    """Page d'inscription (réservée aux admins)"""
    # Vérifier que l'utilisateur est admin
    if not current_user.is_authenticated or not has_permission(current_user, 'users.create'):
        flash('Accès refusé. Seuls les administrateurs peuvent créer des utilisateurs.', 'error')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        full_name = request.form.get('full_name')
        phone = request.form.get('phone')
        role_id = request.form.get('role_id')
        region_id = request.form.get('region_id') or None
        
        # Validation
        if not username or not email or not password or not role_id:
            flash('Veuillez remplir tous les champs obligatoires', 'error')
            roles = Role.query.all()
            regions = Region.query.order_by(Region.name).all()
            return render_template('auth/register.html', roles=roles, regions=regions)
        
        # Validation du mot de passe fort
        password_errors = []
        if len(password) < 8:
            password_errors.append("au moins 8 caractères")
        if not re.search(r'[A-Z]', password):
            password_errors.append("au moins une majuscule")
        if not re.search(r'[a-z]', password):
            password_errors.append("au moins une minuscule")
        if not re.search(r'\d', password):
            password_errors.append("au moins un chiffre")
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            password_errors.append("au moins un caractère spécial (!@#$%^&*...)")
        
        if password_errors:
            flash(f'Le mot de passe doit contenir : {", ".join(password_errors)}', 'error')
            roles = Role.query.all()
            regions = Region.query.order_by(Region.name).all()
            return render_template('auth/register.html', roles=roles, regions=regions)
        
        # Validation de l'email
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            flash('Format d\'email invalide', 'error')
            roles = Role.query.all()
            regions = Region.query.order_by(Region.name).all()
            return render_template('auth/register.html', roles=roles, regions=regions)
        
        # Vérifier si l'utilisateur existe déjà
        if User.query.filter_by(username=username).first():
            flash('Ce nom d\'utilisateur existe déjà', 'error')
            roles = Role.query.all()
            regions = Region.query.order_by(Region.name).all()
            return render_template('auth/register.html', roles=roles, regions=regions)
        
        if User.query.filter_by(email=email).first():
            flash('Cet email est déjà utilisé', 'error')
            roles = Role.query.all()
            regions = Region.query.order_by(Region.name).all()
            return render_template('auth/register.html', roles=roles, regions=regions)
        
        # Créer l'utilisateur
        user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password),
            full_name=full_name,
            phone=phone,
            role_id=int(role_id),
            region_id=int(region_id) if region_id else None,
            is_active=True
        )
        
        db.session.add(user)
        db.session.flush()  # S'assurer que l'utilisateur est créé dans la session
        db.session.commit()
        
        # Rediriger vers la liste avec le filtre de région si l'utilisateur créé a une région
        # Cela garantit que l'utilisateur créé sera visible dans la liste
        redirect_url = url_for('auth.users_list')
        if user.region_id:
            redirect_url = url_for('auth.users_list', region_id=user.region_id)
        
        flash(f'Utilisateur {username} créé avec succès', 'success')
        return redirect(redirect_url)
    
    roles = Role.query.all()
    regions = Region.query.order_by(Region.name).all()
    return render_template('auth/register.html', roles=roles, regions=regions)

@auth_bp.route('/users')
@login_required
def users_list():
    """Liste des utilisateurs (admin seulement)"""
    if not has_permission(current_user, 'users.read'):
        flash('Accès refusé', 'error')
        return redirect(url_for('index'))
    
    # Filtrer par région si fourni
    region_id = request.args.get('region_id', type=int)
    query = User.query
    
    if region_id:
        query = query.filter_by(region_id=region_id)
    
    # Trier par date de création (plus récent en premier), puis par ID si created_at est NULL
    from sqlalchemy import desc, nullslast
    users = query.order_by(nullslast(desc(User.created_at)), desc(User.id)).all()
    roles = Role.query.all()
    regions = Region.query.order_by(Region.name).all()
    return render_template('auth/users_list.html', users=users, roles=roles, regions=regions, selected_region_id=region_id)

@auth_bp.route('/users/<int:user_id>')
@login_required
def user_detail(user_id):
    """Détails d'un utilisateur"""
    if not has_permission(current_user, 'users.read'):
        flash('Accès refusé', 'error')
        return redirect(url_for('index'))
    
    user = User.query.get_or_404(user_id)
    return render_template('auth/user_detail.html', user=user)

@auth_bp.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
def user_edit(user_id):
    """Modifier un utilisateur"""
    if not has_permission(current_user, 'users.update'):
        flash('Accès refusé', 'error')
        return redirect(url_for('index'))
    
    user = User.query.get_or_404(user_id)
    
    # Empêcher un utilisateur non-admin de modifier un admin
    if user.role and user.role.code == 'admin' and current_user.role and current_user.role.code != 'admin':
        flash('Vous ne pouvez pas modifier un administrateur', 'error')
        return redirect(url_for('auth.users_list'))
    
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
            return render_template('auth/user_edit.html', user=user, roles=roles, regions=regions)
        
        # Vérifier si le username existe déjà (pour un autre utilisateur)
        existing_user = User.query.filter_by(username=username).first()
        if existing_user and existing_user.id != user.id:
            flash('Ce nom d\'utilisateur existe déjà', 'error')
            roles = Role.query.all()
            regions = Region.query.order_by(Region.name).all()
            return render_template('auth/user_edit.html', user=user, roles=roles, regions=regions)
        
        # Vérifier si l'email existe déjà (pour un autre utilisateur)
        existing_email = User.query.filter_by(email=email).first()
        if existing_email and existing_email.id != user.id:
            flash('Cet email est déjà utilisé', 'error')
            roles = Role.query.all()
            regions = Region.query.order_by(Region.name).all()
            return render_template('auth/user_edit.html', user=user, roles=roles, regions=regions)
        
        # Empêcher de désactiver le dernier admin
        if user.role and user.role.code == 'admin' and not is_active:
            admin_count = User.query.join(Role).filter(Role.code == 'admin', User.is_active == True).count()
            if admin_count <= 1:
                flash('Impossible de désactiver le dernier administrateur', 'error')
                roles = Role.query.all()
                regions = Region.query.order_by(Region.name).all()
                return render_template('auth/user_edit.html', user=user, roles=roles, regions=regions)
        
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
        
        flash(f'Utilisateur {username} modifié avec succès', 'success')
        return redirect(url_for('auth.user_detail', user_id=user.id))
    
    roles = Role.query.all()
    regions = Region.query.order_by(Region.name).all()
    return render_template('auth/user_edit.html', user=user, roles=roles, regions=regions)

@auth_bp.route('/users/<int:user_id>/delete', methods=['POST'])
@login_required
def user_delete(user_id):
    """Supprimer un utilisateur"""
    if not has_permission(current_user, 'users.delete'):
        flash('Accès refusé', 'error')
        return redirect(url_for('index'))
    
    user = User.query.get_or_404(user_id)
    
    # Empêcher de supprimer son propre compte
    if user.id == current_user.id:
        flash('Vous ne pouvez pas supprimer votre propre compte', 'error')
        return redirect(url_for('auth.users_list'))
    
    # Empêcher de supprimer un admin
    if user.role and user.role.code == 'admin':
        flash('Impossible de supprimer un administrateur. Désactivez-le plutôt.', 'error')
        return redirect(url_for('auth.users_list'))
    
    # Empêcher de supprimer le dernier admin
    admin_count = User.query.join(Role).filter(Role.code == 'admin', User.is_active == True).count()
    if user.role and user.role.code == 'admin' and admin_count <= 1:
        flash('Impossible de supprimer le dernier administrateur', 'error')
        return redirect(url_for('auth.users_list'))
    
    username = user.username
    db.session.delete(user)
    db.session.commit()
    
    flash(f'Utilisateur {username} supprimé avec succès', 'success')
    return redirect(url_for('auth.users_list'))

@auth_bp.route('/users/<int:user_id>/toggle-active', methods=['POST'])
@login_required
def user_toggle_active(user_id):
    """Activer/Désactiver un utilisateur"""
    if not has_permission(current_user, 'users.update'):
        flash('Accès refusé', 'error')
        return redirect(url_for('index'))
    
    user = User.query.get_or_404(user_id)
    
    # Empêcher de désactiver son propre compte
    if user.id == current_user.id:
        flash('Vous ne pouvez pas désactiver votre propre compte', 'error')
        return redirect(url_for('auth.users_list'))
    
    # Empêcher de désactiver le dernier admin
    if user.role and user.role.code == 'admin' and user.is_active:
        admin_count = User.query.join(Role).filter(Role.code == 'admin', User.is_active == True).count()
        if admin_count <= 1:
            flash('Impossible de désactiver le dernier administrateur', 'error')
            return redirect(url_for('auth.users_list'))
    
    user.is_active = not user.is_active
    user.updated_at = datetime.now(UTC)
    db.session.commit()
    
    status = 'activé' if user.is_active else 'désactivé'
    flash(f'Utilisateur {user.username} {status} avec succès', 'success')
    return redirect(url_for('auth.users_list'))

@auth_bp.route('/users/<int:user_id>/reset-password', methods=['GET', 'POST'])
@login_required
def user_reset_password(user_id):
    """Réinitialiser le mot de passe d'un utilisateur"""
    if not has_permission(current_user, 'users.update'):
        flash('Accès refusé', 'error')
        return redirect(url_for('index'))
    
    user = User.query.get_or_404(user_id)
    
    if request.method == 'POST':
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        if not new_password or not confirm_password:
            flash('Veuillez remplir tous les champs', 'error')
            return render_template('auth/user_reset_password.html', user=user)
        
        if new_password != confirm_password:
            flash('Les mots de passe ne correspondent pas', 'error')
            return render_template('auth/user_reset_password.html', user=user)
        
        if len(new_password) < 6:
            flash('Le mot de passe doit contenir au moins 6 caractères', 'error')
            return render_template('auth/user_reset_password.html', user=user)
        
        user.password_hash = generate_password_hash(new_password)
        user.updated_at = datetime.now(UTC)
        db.session.commit()
        
        flash(f'Mot de passe de {user.username} réinitialisé avec succès', 'success')
        return redirect(url_for('auth.user_detail', user_id=user.id))
    
    return render_template('auth/user_reset_password.html', user=user)

@auth_bp.route('/profile')
@login_required
def profile():
    """Profil de l'utilisateur connecté"""
    return render_template('auth/profile.html', user=current_user)

@auth_bp.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def profile_edit():
    """Modifier son propre profil"""
    if request.method == 'POST':
        email = request.form.get('email')
        full_name = request.form.get('full_name')
        phone = request.form.get('phone')
        
        # Validation
        if not email:
            flash('L\'email est obligatoire', 'error')
            return render_template('auth/profile_edit.html', user=current_user)
        
        # Vérifier si l'email existe déjà (pour un autre utilisateur)
        existing_email = User.query.filter_by(email=email).first()
        if existing_email and existing_email.id != current_user.id:
            flash('Cet email est déjà utilisé', 'error')
            return render_template('auth/profile_edit.html', user=current_user)
        
        # Mettre à jour le profil
        current_user.email = email
        current_user.full_name = full_name
        current_user.phone = phone
        current_user.updated_at = datetime.now(UTC)
        
        db.session.commit()
        
        flash('Profil modifié avec succès', 'success')
        return redirect(url_for('auth.profile'))
    
    return render_template('auth/profile_edit.html', user=current_user)

@auth_bp.route('/profile/change-password', methods=['GET', 'POST'])
@login_required
def profile_change_password():
    """Changer son propre mot de passe"""
    if request.method == 'POST':
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        if not current_password or not new_password or not confirm_password:
            flash('Veuillez remplir tous les champs', 'error')
            return render_template('auth/profile_change_password.html')
        
        # Vérifier le mot de passe actuel
        if not check_password_hash(current_user.password_hash, current_password):
            flash('Mot de passe actuel incorrect', 'error')
            return render_template('auth/profile_change_password.html')
        
        if new_password != confirm_password:
            flash('Les nouveaux mots de passe ne correspondent pas', 'error')
            return render_template('auth/profile_change_password.html')
        
        if len(new_password) < 6:
            flash('Le mot de passe doit contenir au moins 6 caractères', 'error')
            return render_template('auth/profile_change_password.html')
        
        current_user.password_hash = generate_password_hash(new_password)
        current_user.updated_at = datetime.now(UTC)
        db.session.commit()
        
        flash('Mot de passe modifié avec succès', 'success')
        return redirect(url_for('auth.profile'))
    
    return render_template('auth/profile_change_password.html')

# Fonctions utilitaires pour les permissions
def has_permission(user, permission):
    """Vérifier si l'utilisateur a une permission"""
    # Vérifier si l'utilisateur est authentifié
    if not user or not hasattr(user, 'is_authenticated') or not user.is_authenticated:
        return False
    
    # Vérifier si l'utilisateur a un rôle
    if not hasattr(user, 'role') or not user.role:
        return False
    
    if user.role.code == 'admin':
        return True  # Admin a tous les droits
    
    if not user.role.permissions:
        return False
    
    permissions = user.role.permissions
    if isinstance(permissions, dict):
        # Permissions structurées : {'module': ['action1', 'action2']}
        parts = permission.split('.')
        if len(parts) == 2:
            module, action = parts
            return module in permissions and action in permissions[module]
        else:
            # Permission simple
            return permission in permissions.get('all', [])
    elif isinstance(permissions, list):
        # Liste simple de permissions
        return permission in permissions
    
    return False

def is_admin(user):
    """Vérifier si l'utilisateur est administrateur"""
    if not user or not hasattr(user, 'is_authenticated') or not user.is_authenticated:
        return False
    if not hasattr(user, 'role') or not user.role:
        return False
    return user.role.code == 'admin'

def is_admin_or_supervisor(user):
    """Vérifier si l'utilisateur est administrateur ou superviseur"""
    if not user or not hasattr(user, 'is_authenticated') or not user.is_authenticated:
        return False
    if not hasattr(user, 'role') or not user.role:
        return False
    return user.role.code in ['admin', 'supervisor']

def require_permission(permission):
    """Décorateur pour vérifier une permission"""
    def decorator(f):
        @login_required
        def decorated_function(*args, **kwargs):
            if not has_permission(current_user, permission):
                flash('Vous n\'avez pas la permission d\'accéder à cette page', 'error')
                return redirect(url_for('index'))
            return f(*args, **kwargs)
        decorated_function.__name__ = f.__name__
        return decorated_function
    return decorator

# =========================================================
# GESTION DES RÔLES ET PERMISSIONS
# =========================================================

def get_available_permissions():
    """Retourne la liste de toutes les fonctionnalités disponibles avec leurs actions"""
    return {
        'simulations': {
            'name': 'Simulations',
            'description': 'Création et gestion des simulations de rentabilité',
            'actions': {
                'read': 'Consulter',
                'create': 'Créer',
                'update': 'Modifier',
                'delete': 'Supprimer'
            }
        },
        'forecast': {
            'name': 'Prévisions & Ventes',
            'description': 'Gestion des prévisions et réalisations de ventes',
            'actions': {
                'read': 'Consulter',
                'create': 'Créer',
                'update': 'Modifier',
                'delete': 'Supprimer',
                'import': 'Importer'
            }
        },
        'stocks': {
            'name': 'Stocks',
            'description': 'Gestion des stocks et mouvements',
            'actions': {
                'read': 'Consulter',
                'create': 'Créer',
                'update': 'Modifier',
                'delete': 'Supprimer'
            }
        },
        'movements': {
            'name': 'Mouvements de Stock',
            'description': 'Transferts, réceptions, sorties et retours',
            'actions': {
                'read': 'Consulter',
                'create': 'Créer',
                'update': 'Modifier',
                'delete': 'Supprimer'
            }
        },
        'inventory': {
            'name': 'Inventaires',
            'description': 'Réalisation et validation des inventaires',
            'actions': {
                'read': 'Consulter',
                'create': 'Créer',
                'update': 'Modifier',
                'validate': 'Valider'
            }
        },
        'vehicles': {
            'name': 'Flotte',
            'description': 'Gestion de la flotte de véhicules',
            'actions': {
                'read': 'Consulter',
                'create': 'Créer',
                'update': 'Modifier',
                'delete': 'Supprimer'
            }
        },
        'regions': {
            'name': 'Régions',
            'description': 'Gestion des régions',
            'actions': {
                'read': 'Consulter',
                'create': 'Créer',
                'update': 'Modifier',
                'delete': 'Supprimer'
            }
        },
        'depots': {
            'name': 'Dépôts',
            'description': 'Gestion des dépôts',
            'actions': {
                'read': 'Consulter',
                'create': 'Créer',
                'update': 'Modifier',
                'delete': 'Supprimer'
            }
        },
        'families': {
            'name': 'Familles',
            'description': 'Gestion des familles d\'articles',
            'actions': {
                'read': 'Consulter',
                'create': 'Créer',
                'update': 'Modifier',
                'delete': 'Supprimer'
            }
        },
        'stock_items': {
            'name': 'Articles de Stock',
            'description': 'Gestion des articles en stock',
            'actions': {
                'read': 'Consulter',
                'create': 'Créer',
                'update': 'Modifier',
                'delete': 'Supprimer'
            }
        },
        'users': {
            'name': 'Utilisateurs',
            'description': 'Gestion des utilisateurs et accès',
            'actions': {
                'read': 'Consulter',
                'create': 'Créer',
                'update': 'Modifier',
                'delete': 'Supprimer'
            }
        },
        'roles': {
            'name': 'Rôles',
            'description': 'Gestion des rôles et permissions',
            'actions': {
                'read': 'Consulter',
                'create': 'Créer',
                'update': 'Modifier',
                'delete': 'Supprimer'
            }
        },
        'chat': {
            'name': 'Chat Interne',
            'description': 'Messagerie interne avec pièces jointes',
            'actions': {
                'read': 'Consulter',
                'create': 'Créer',
                'update': 'Modifier',
                'delete': 'Supprimer',
                'manage_rooms': 'Gérer les conversations'
            }
        },
        'reports': {
            'name': 'Rapports',
            'description': 'Consultation des rapports et statistiques',
            'actions': {
                'read': 'Consulter',
                'export': 'Exporter'
            }
        },
        'analytics': {
            'name': 'Tableaux de Bord Analytiques',
            'description': 'KPIs, graphiques et analyses en temps réel',
            'actions': {
                'read': 'Consulter',
                'export': 'Exporter'
            }
        }
    }

@auth_bp.route('/roles')
@login_required
def roles_list():
    """Liste des rôles"""
    if not has_permission(current_user, 'roles.read'):
        flash('Accès refusé', 'error')
        return redirect(url_for('index'))
    
    roles = Role.query.order_by(Role.name).all()
    
    # Calculer les statistiques globales
    total_users = sum(len(role.users) for role in roles)
    roles_with_permissions = sum(1 for role in roles if role.permissions)
    admin_count = sum(1 for role in roles if role.code == 'admin')
    
    # Calculer les statistiques d'utilisateurs actifs/inactifs par rôle
    roles_stats = []
    total_active = 0
    total_inactive = 0
    
    for role in roles:
        active_users = [u for u in role.users if u.is_active]
        inactive_users = [u for u in role.users if not u.is_active]
        
        roles_stats.append({
            'role': role,
            'active_count': len(active_users),
            'inactive_count': len(inactive_users),
            'active_users': active_users,
            'inactive_users': inactive_users
        })
        
        total_active += len(active_users)
        total_inactive += len(inactive_users)
    
    return render_template('auth/roles_list.html', 
                         roles=roles,
                         roles_stats=roles_stats,
                         total_users=total_users,
                         total_active=total_active,
                         total_inactive=total_inactive,
                         roles_with_permissions=roles_with_permissions,
                         admin_count=admin_count)

@auth_bp.route('/roles/new', methods=['GET', 'POST'])
@login_required
def role_new():
    """Créer un nouveau rôle"""
    if not has_permission(current_user, 'roles.create'):
        flash('Accès refusé', 'error')
        return redirect(url_for('auth.roles_list'))
    
    permissions_map = get_available_permissions()
    
    if request.method == 'POST':
        name = request.form.get('name')
        code = request.form.get('code')
        description = request.form.get('description')
        
        if not name or not code:
            flash('Le nom et le code sont obligatoires', 'error')
            return render_template('auth/role_form.html', 
                                 role=None, 
                                 permissions_map=permissions_map)
        
        # Vérifier si le code existe déjà
        if Role.query.filter_by(code=code).first():
            flash('Ce code de rôle existe déjà', 'error')
            return render_template('auth/role_form.html', 
                                 role=None, 
                                 permissions_map=permissions_map)
        
        # Construire les permissions depuis le formulaire
        permissions = {}
        for module_key in permissions_map.keys():
            module_perms = request.form.getlist(f'permissions[{module_key}]')
            if module_perms:
                permissions[module_key] = module_perms
        
        # Créer le rôle
        role = Role(
            name=name,
            code=code.lower().replace(' ', '_'),
            description=description,
            permissions=permissions if permissions else None
        )
        
        db.session.add(role)
        db.session.commit()
        
        flash(f'Rôle {name} créé avec succès', 'success')
        return redirect(url_for('auth.roles_list'))
    
    return render_template('auth/role_form.html', 
                         role=None, 
                         permissions_map=permissions_map)

@auth_bp.route('/roles/<int:role_id>')
@login_required
def role_detail(role_id):
    """Détails d'un rôle"""
    if not has_permission(current_user, 'roles.read'):
        flash('Accès refusé', 'error')
        return redirect(url_for('index'))
    
    role = Role.query.get_or_404(role_id)
    permissions_map = get_available_permissions()
    
    return render_template('auth/role_detail.html', 
                         role=role, 
                         permissions_map=permissions_map)

@auth_bp.route('/roles/<int:role_id>/edit', methods=['GET', 'POST'])
@login_required
def role_edit(role_id):
    """Modifier un rôle"""
    if not has_permission(current_user, 'roles.update'):
        flash('Accès refusé', 'error')
        return redirect(url_for('auth.roles_list'))
    
    role = Role.query.get_or_404(role_id)
    
    # Empêcher de modifier le rôle admin
    if role.code == 'admin' and current_user.role and current_user.role.code != 'admin':
        flash('Vous ne pouvez pas modifier le rôle administrateur', 'error')
        return redirect(url_for('auth.roles_list'))
    
    permissions_map = get_available_permissions()
    
    if request.method == 'POST':
        name = request.form.get('name')
        code = request.form.get('code')
        description = request.form.get('description')
        
        if not name or not code:
            flash('Le nom et le code sont obligatoires', 'error')
            return render_template('auth/role_form.html', 
                                 role=role, 
                                 permissions_map=permissions_map)
        
        # Vérifier si le code existe déjà (pour un autre rôle)
        existing_role = Role.query.filter_by(code=code).first()
        if existing_role and existing_role.id != role.id:
            flash('Ce code de rôle existe déjà', 'error')
            return render_template('auth/role_form.html', 
                                 role=role, 
                                 permissions_map=permissions_map)
        
        # Construire les permissions depuis le formulaire
        permissions = {}
        for module_key in permissions_map.keys():
            module_perms = request.form.getlist(f'permissions[{module_key}]')
            if module_perms:
                permissions[module_key] = module_perms
        
        # Mettre à jour le rôle
        role.name = name
        role.code = code.lower().replace(' ', '_')
        role.description = description
        role.permissions = permissions if permissions else None
        role.updated_at = datetime.now(UTC)
        
        db.session.commit()
        
        flash(f'Rôle {name} modifié avec succès', 'success')
        return redirect(url_for('auth.role_detail', role_id=role.id))
    
    return render_template('auth/role_form.html', 
                         role=role, 
                         permissions_map=permissions_map)

@auth_bp.route('/roles/<int:role_id>/delete', methods=['POST'])
@login_required
def role_delete(role_id):
    """Supprimer un rôle"""
    if not has_permission(current_user, 'roles.delete'):
        flash('Accès refusé', 'error')
        return redirect(url_for('index'))
    
    role = Role.query.get_or_404(role_id)
    
    # Empêcher de supprimer le rôle admin
    if role.code == 'admin':
        flash('Impossible de supprimer le rôle administrateur', 'error')
        return redirect(url_for('auth.roles_list'))
    
    # Vérifier si des utilisateurs utilisent ce rôle
    user_count = User.query.filter_by(role_id=role_id).count()
    if user_count > 0:
        flash(f'Impossible de supprimer ce rôle : {user_count} utilisateur(s) l\'utilisent', 'error')
        return redirect(url_for('auth.roles_list'))
    
    role_name = role.name
    db.session.delete(role)
    db.session.commit()
    
    flash(f'Rôle {role_name} supprimé avec succès', 'success')
    return redirect(url_for('auth.roles_list'))

