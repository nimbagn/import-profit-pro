# utils_articles.py
# Utilitaires pour la gestion des images d'articles

import os
import uuid
from pathlib import Path
from werkzeug.utils import secure_filename
from flask import current_app

ALLOWED_IMAGE_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif', 'webp'}
MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5 MB


def allowed_image_file(filename):
    """Vérifie si le fichier est une image autorisée"""
    if '.' not in filename:
        return False
    ext = filename.rsplit('.', 1)[1].lower()
    return ext in ALLOWED_IMAGE_EXTENSIONS


def save_article_image(file, article_id=None):
    """
    Sauvegarde une image d'article
    
    Args:
        file: Fichier Flask uploadé
        article_id: ID de l'article (None pour nouveau)
    
    Returns:
        dict: {'file_path': str, 'file_name': str, 'file_size': int}
    """
    if not file or not file.filename:
        return None
    
    if not allowed_image_file(file.filename):
        raise ValueError(f"Type de fichier non autorisé. Formats acceptés: {', '.join(ALLOWED_IMAGE_EXTENSIONS)}")
    
    # Vérifier la taille
    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)
    
    if file_size > MAX_IMAGE_SIZE:
        raise ValueError(f"Image trop volumineuse: {file_size / 1024 / 1024:.2f} MB (max: {MAX_IMAGE_SIZE / 1024 / 1024} MB)")
    
    # Créer le dossier de destination
    upload_dir = Path(current_app.config['UPLOAD_FOLDER']) / 'articles'
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    # Générer un nom de fichier sécurisé et unique
    original_filename = secure_filename(file.filename)
    file_ext = original_filename.rsplit('.', 1)[1].lower() if '.' in original_filename else 'jpg'
    
    # Utiliser l'ID de l'article si disponible, sinon UUID
    if article_id:
        unique_filename = f"article_{article_id}_{uuid.uuid4().hex[:8]}.{file_ext}"
    else:
        unique_filename = f"article_{uuid.uuid4().hex}.{file_ext}"
    
    # Sauvegarder le fichier
    file_path = upload_dir / unique_filename
    file.save(str(file_path))
    
    # Retourner le chemin relatif (depuis instance/uploads/)
    relative_path = f"articles/{unique_filename}"
    
    return {
        'file_path': relative_path,
        'file_name': original_filename,
        'file_size': file_size
    }


def delete_article_image(image_path):
    """Supprime une image d'article"""
    if not image_path:
        return
    
    try:
        full_path = Path(current_app.config['UPLOAD_FOLDER']) / image_path
        if full_path.exists():
            full_path.unlink()
    except Exception as e:
        print(f"Erreur lors de la suppression de l'image {image_path}: {e}")

