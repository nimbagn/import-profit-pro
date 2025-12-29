#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module de gestion des emails et tokens de réinitialisation de mot de passe
"""

import secrets
from datetime import datetime, timedelta, UTC
from flask import current_app, url_for
from flask_mail import Mail, Message
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, PasswordResetToken

# Instance globale de Flask-Mail (sera initialisée dans app.py)
mail = Mail()

def generate_reset_token():
    """
    Génère un token sécurisé pour la réinitialisation de mot de passe.
    Retourne le token en clair (à envoyer par email) et le hash (à stocker en DB).
    """
    # Générer un token cryptographiquement sécurisé (32 bytes = 256 bits)
    token = secrets.token_urlsafe(32)
    # Hasher le token avant de le stocker (comme les mots de passe)
    token_hash = generate_password_hash(token)
    return token, token_hash

def create_password_reset_token(user_id):
    """
    Crée un token de réinitialisation pour un utilisateur.
    Retourne le token en clair (à envoyer par email).
    """
    # Invalider tous les tokens précédents non utilisés pour cet utilisateur
    PasswordResetToken.query.filter_by(
        user_id=user_id,
        used=False
    ).update({'used': True})
    db.session.commit()
    
    # Générer un nouveau token
    token, token_hash = generate_reset_token()
    
    # Définir l'expiration (30 minutes)
    expires_at = datetime.now(UTC) + timedelta(minutes=30)
    
    # Créer le token en base de données
    reset_token = PasswordResetToken(
        user_id=user_id,
        token_hash=token_hash,
        expires_at=expires_at,
        used=False
    )
    
    db.session.add(reset_token)
    db.session.commit()
    
    return token

def verify_reset_token(token):
    """
    Vérifie si un token de réinitialisation est valide.
    Retourne l'objet PasswordResetToken si valide, None sinon.
    """
    if not token:
        return None
    
    # Chercher tous les tokens non utilisés et non expirés
    valid_tokens = PasswordResetToken.query.filter_by(used=False).all()
    
    for reset_token in valid_tokens:
        # Vérifier si le token correspond (en comparant les hash)
        if check_password_hash(reset_token.token_hash, token):
            # Vérifier si le token n'est pas expiré
            if reset_token.is_valid():
                return reset_token
    
    return None

def send_password_reset_email(user, token):
    """
    Envoie un email de réinitialisation de mot de passe à l'utilisateur.
    """
    try:
        # Construire l'URL de réinitialisation
        reset_url = url_for(
            'auth.reset_password',
            token=token,
            _external=True
        )
        
        # Créer le message email
        msg = Message(
            subject="Réinitialisation de votre mot de passe - Import Profit Pro",
            recipients=[user.email],
            html=f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <style>
                    body {{
                        font-family: Arial, sans-serif;
                        line-height: 1.6;
                        color: #333;
                        max-width: 600px;
                        margin: 0 auto;
                        padding: 20px;
                    }}
                    .header {{
                        background: linear-gradient(135deg, #003865 0%, #0052a5 100%);
                        color: white;
                        padding: 30px;
                        text-align: center;
                        border-radius: 10px 10px 0 0;
                    }}
                    .content {{
                        background: #f9fafb;
                        padding: 30px;
                        border: 2px solid #e5e7eb;
                        border-top: none;
                    }}
                    .button {{
                        display: inline-block;
                        background: linear-gradient(135deg, #003865 0%, #0052a5 100%);
                        color: white;
                        padding: 15px 30px;
                        text-decoration: none;
                        border-radius: 8px;
                        font-weight: bold;
                        margin: 20px 0;
                    }}
                    .footer {{
                        background: #f3f4f6;
                        padding: 20px;
                        text-align: center;
                        font-size: 12px;
                        color: #6b7280;
                        border-radius: 0 0 10px 10px;
                    }}
                    .warning {{
                        background: #fef3c7;
                        border-left: 4px solid #f59e0b;
                        padding: 15px;
                        margin: 20px 0;
                        border-radius: 4px;
                    }}
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>🔐 Réinitialisation de mot de passe</h1>
                </div>
                <div class="content">
                    <p>Bonjour {user.full_name or user.username},</p>
                    
                    <p>Vous avez demandé à réinitialiser votre mot de passe pour votre compte Import Profit Pro.</p>
                    
                    <p>Cliquez sur le bouton ci-dessous pour créer un nouveau mot de passe :</p>
                    
                    <div style="text-align: center;">
                        <a href="{reset_url}" class="button">Réinitialiser mon mot de passe</a>
                    </div>
                    
                    <p>Ou copiez-collez ce lien dans votre navigateur :</p>
                    <p style="word-break: break-all; color: #003865; font-size: 12px;">{reset_url}</p>
                    
                    <div class="warning">
                        <strong>⚠️ Important :</strong>
                        <ul style="margin: 10px 0; padding-left: 20px;">
                            <li>Ce lien est valide pendant <strong>30 minutes</strong> uniquement</li>
                            <li>Il ne peut être utilisé qu'<strong>une seule fois</strong></li>
                            <li>Si vous n'avez pas demandé cette réinitialisation, ignorez cet email</li>
                        </ul>
                    </div>
                    
                    <p>Si vous n'avez pas demandé cette réinitialisation, vous pouvez ignorer cet email en toute sécurité.</p>
                </div>
                <div class="footer">
                    <p>Cet email a été envoyé automatiquement, merci de ne pas y répondre.</p>
                    <p>© Import Profit Pro - Tous droits réservés</p>
                </div>
            </body>
            </html>
            """,
            body=f"""
Bonjour {user.full_name or user.username},

Vous avez demandé à réinitialiser votre mot de passe pour votre compte Import Profit Pro.

Cliquez sur le lien suivant pour créer un nouveau mot de passe :
{reset_url}

⚠️ Important :
- Ce lien est valide pendant 30 minutes uniquement
- Il ne peut être utilisé qu'une seule fois
- Si vous n'avez pas demandé cette réinitialisation, ignorez cet email

Si vous n'avez pas demandé cette réinitialisation, vous pouvez ignorer cet email en toute sécurité.

Cet email a été envoyé automatiquement, merci de ne pas y répondre.
© Import Profit Pro - Tous droits réservés
            """
        )
        
        # Envoyer l'email
        mail.send(msg)
        return True
    except Exception as e:
        current_app.logger.error(f"Erreur lors de l'envoi de l'email de réinitialisation: {e}")
        return False

def cleanup_expired_tokens():
    """
    Nettoie les tokens expirés de la base de données (à appeler périodiquement).
    """
    try:
        expired_count = PasswordResetToken.query.filter(
            PasswordResetToken.expires_at < datetime.now(UTC)
        ).delete()
        db.session.commit()
        if expired_count > 0:
            current_app.logger.info(f"Nettoyage: {expired_count} tokens expirés supprimés")
        return expired_count
    except Exception as e:
        current_app.logger.error(f"Erreur lors du nettoyage des tokens: {e}")
        db.session.rollback()
        return 0

