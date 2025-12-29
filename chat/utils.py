# chat/utils.py
# Utilitaires pour le chat (upload, validation, etc.)

import os
import uuid
from pathlib import Path
from werkzeug.utils import secure_filename
from flask import current_app
try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False
import mimetypes

ALLOWED_EXTENSIONS = {
    'images': {'jpg', 'jpeg', 'png', 'gif', 'webp'},
    'documents': {'pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx'},
    'archives': {'zip', 'rar', '7z'}
}

ALLOWED_MIME_TYPES = {
    'image/jpeg', 'image/png', 'image/gif', 'image/webp',
    'application/pdf',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'application/vnd.ms-excel',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'application/vnd.ms-powerpoint',
    'application/vnd.openxmlformats-officedocument.presentationml.presentation',
    'application/zip', 'application/x-rar-compressed', 'application/x-7z-compressed'
}

MAX_FILE_SIZE = 25 * 1024 * 1024  # 25 MB


def allowed_file(filename):
    """Vérifie si le fichier est autorisé"""
    if '.' not in filename:
        return False
    ext = filename.rsplit('.', 1)[1].lower()
    return ext in {ext for category in ALLOWED_EXTENSIONS.values() for ext in category}


def get_file_category(filename):
    """Détermine la catégorie du fichier"""
    if '.' not in filename:
        return None
    ext = filename.rsplit('.', 1)[1].lower()
    for category, extensions in ALLOWED_EXTENSIONS.items():
        if ext in extensions:
            return category
    return None


def save_chat_file(file, room_id, message_id):
    """Sauvegarde un fichier uploadé pour un message de chat"""
    if not allowed_file(file.filename):
        raise ValueError(f"Type de fichier non autorisé: {file.filename}")
    
    # Vérifier la taille
    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)
    
    if file_size > MAX_FILE_SIZE:
        raise ValueError(f"Fichier trop volumineux: {file_size} bytes (max: {MAX_FILE_SIZE})")
    
    # Créer le dossier de destination
    upload_dir = Path(current_app.config['UPLOAD_FOLDER']) / 'chat' / str(room_id) / str(message_id)
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    # Générer un nom de fichier sécurisé
    original_filename = secure_filename(file.filename)
    file_ext = original_filename.rsplit('.', 1)[1].lower() if '.' in original_filename else ''
    unique_filename = f"{uuid.uuid4().hex}.{file_ext}" if file_ext else uuid.uuid4().hex
    
    # Sauvegarder le fichier
    file_path = upload_dir / unique_filename
    file.save(str(file_path))
    
    # Obtenir le type MIME
    mime_type, _ = mimetypes.guess_type(original_filename)
    if not mime_type:
        mime_type = 'application/octet-stream'
    
    # Générer une miniature pour les images
    thumbnail_path = None
    if get_file_category(original_filename) == 'images' and HAS_PIL:
        try:
            thumbnail_dir = upload_dir / 'thumbnails'
            thumbnail_dir.mkdir(exist_ok=True)
            thumbnail_filename = f"{unique_filename.rsplit('.', 1)[0]}_thumb.jpg"
            thumbnail_path_full = thumbnail_dir / thumbnail_filename
            
            img = Image.open(file_path)
            img.thumbnail((200, 200), Image.Resampling.LANCZOS)
            img.convert('RGB').save(thumbnail_path_full, 'JPEG', quality=85)
            
            # Chemin relatif pour la base de données
            thumbnail_path = f"chat/{room_id}/{message_id}/thumbnails/{thumbnail_filename}"
        except Exception as e:
            print(f"⚠️ Erreur lors de la génération de la miniature: {e}")
    
    # Chemin relatif pour la base de données
    relative_path = f"chat/{room_id}/{message_id}/{unique_filename}"
    
    return {
        'file_name': original_filename,
        'file_path': relative_path,
        'file_size': file_size,
        'file_type': mime_type,
        'file_extension': file_ext,
        'thumbnail_path': thumbnail_path
    }


def get_file_url(file_path):
    """Génère l'URL pour télécharger un fichier"""
    return f"/chat/files/{file_path}"


def format_file_size(size_bytes):
    """Formate la taille d'un fichier en format lisible"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"

