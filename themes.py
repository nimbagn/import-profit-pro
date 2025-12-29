# themes.py
# Gestion des thèmes personnalisables - Import Profit Pro

from flask import Blueprint, render_template, request, jsonify, session
from flask_login import login_required, current_user
from models import db, UserPreference
from datetime import datetime, UTC

# Créer le blueprint
themes_bp = Blueprint('themes', __name__, url_prefix='/themes')

# Rate limiting pour les routes API
def get_limiter():
    """Récupère le limiter depuis l'application Flask"""
    try:
        from auth import limiter
        return limiter
    except (ImportError, AttributeError):
        return None

def apply_themes_rate_limit(func):
    """Applique un rate limiting permissif pour les routes themes API"""
    limiter = get_limiter()
    if limiter:
        # Permettre 300 requêtes par heure pour les préférences (appelées fréquemment)
        return limiter.limit("300 per hour", error_message="Trop de requêtes. Réessayez dans quelques instants.")(func)
    return func

@themes_bp.route('/settings', methods=['GET'])
@login_required
def settings():
    """Page de paramètres d'apparence"""
    # Récupérer ou créer les préférences de l'utilisateur
    preference = UserPreference.query.filter_by(user_id=current_user.id).first()
    if not preference:
        preference = UserPreference(
            user_id=current_user.id,
            theme_name='hapag-lloyd',
            color_mode='light'
        )
        db.session.add(preference)
        db.session.commit()
    
    return render_template('themes/settings.html', preference=preference)

@themes_bp.route('/api/preferences', methods=['GET'])
@login_required
@apply_themes_rate_limit
def get_preferences():
    """API: Récupérer les préférences de thème de l'utilisateur"""
    preference = UserPreference.query.filter_by(user_id=current_user.id).first()
    if not preference:
        # Créer des préférences par défaut
        preference = UserPreference(
            user_id=current_user.id,
            theme_name='hapag-lloyd',
            color_mode='light'
        )
        db.session.add(preference)
        db.session.commit()
    
    return jsonify({
        'theme_name': preference.theme_name,
        'color_mode': preference.color_mode
    })

@themes_bp.route('/api/preferences', methods=['POST'])
@login_required
def update_preferences():
    """API: Mettre à jour les préférences de thème de l'utilisateur"""
    data = request.get_json()
    theme_name = data.get('theme_name', 'hapag-lloyd')
    color_mode = data.get('color_mode', 'light')
    
    # Valider les valeurs
    valid_themes = ['hapag-lloyd', 'professional', 'energetic', 'nature', 'christmas', 'summer', 'custom', 'minimalist', 'cyberpunk', 'ocean']
    valid_modes = ['light', 'dark', 'auto', 'system']
    
    if theme_name not in valid_themes:
        return jsonify({'error': 'Thème invalide'}), 400
    if color_mode not in valid_modes:
        return jsonify({'error': 'Mode de couleur invalide'}), 400
    
    # Récupérer ou créer les préférences
    preference = UserPreference.query.filter_by(user_id=current_user.id).first()
    if not preference:
        preference = UserPreference(user_id=current_user.id)
        db.session.add(preference)
    
    # Mettre à jour
    preference.theme_name = theme_name
    preference.color_mode = color_mode
    preference.updated_at = datetime.now(UTC)
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'theme_name': preference.theme_name,
        'color_mode': preference.color_mode
    })

@themes_bp.route('/api/apply', methods=['POST'])
@login_required
def apply_theme():
    """API: Appliquer un thème temporairement (sans sauvegarder)"""
    data = request.get_json()
    theme_name = data.get('theme_name', 'hapag-lloyd')
    color_mode = data.get('color_mode', 'light')
    
    # Valider les valeurs
    valid_themes = ['hapag-lloyd', 'professional', 'energetic', 'nature', 'christmas', 'summer', 'custom', 'minimalist', 'cyberpunk', 'ocean']
    valid_modes = ['light', 'dark', 'auto', 'system']
    
    if theme_name not in valid_themes:
        return jsonify({'error': 'Thème invalide'}), 400
    if color_mode not in valid_modes:
        return jsonify({'error': 'Mode de couleur invalide'}), 400
    
    # Stocker temporairement dans la session
    session['theme_name'] = theme_name
    session['color_mode'] = color_mode
    
    return jsonify({
        'success': True,
        'theme_name': theme_name,
        'color_mode': color_mode
    })

