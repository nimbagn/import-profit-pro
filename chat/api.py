# chat/api.py
# API REST pour le chat interne

from flask import request, jsonify, send_from_directory, current_app
from flask_login import login_required, current_user
from datetime import datetime, UTC
from pathlib import Path
import os
from sqlalchemy.orm import joinedload
from sqlalchemy import func, and_
from models import (
    db, ChatRoom, ChatRoomMember, ChatMessage, ChatAttachment,
    ChatMessageRead, User
)
from auth import has_permission
from . import chat_bp
from .utils import save_chat_file, get_file_url, format_file_size

# Exempter les routes API du CSRF si CSRF est activé
# Le décorateur sera appliqué dans app.py après l'enregistrement du blueprint
def exempt_from_csrf(func):
    """Décorateur placeholder - l'exemption sera appliquée dans app.py"""
    return func


def get_limiter():
    """Récupère le limiter depuis l'application Flask"""
    try:
        from auth import limiter
        return limiter
    except (ImportError, AttributeError):
        return None


# Décorateur de rate limiting pour l'API rooms (plus permissif)
def apply_chat_rate_limit(func):
    """Applique un rate limiting permissif pour les routes chat API"""
    limiter = get_limiter()
    if limiter:
        # Permettre 120 requêtes par heure (au lieu de 50 par défaut)
        # Cela permet un appel toutes les 30 secondes avec une marge de sécurité
        return limiter.limit("120 per hour", error_message="Trop de requêtes. Réessayez dans quelques instants.")(func)
    return func


@chat_bp.route('/api/rooms', methods=['GET'])
@login_required
@apply_chat_rate_limit
def api_rooms_list():
    """API: Liste des conversations avec optimisations N+1"""
    if not has_permission(current_user, 'chat.read'):
        return jsonify({'error': 'Permission refusée'}), 403
    
    # Récupérer les membres avec optimisation
    memberships = ChatRoomMember.query.filter_by(user_id=current_user.id).options(
        joinedload(ChatRoomMember.room)
    ).all()
    room_ids = [m.room_id for m in memberships]
    membership_map = {m.room_id: m for m in memberships}
    
    if not room_ids:
        return jsonify({'rooms': []})
    
    # Récupérer les rooms avec optimisation
    rooms = ChatRoom.query.filter(ChatRoom.id.in_(room_ids)).options(
        joinedload(ChatRoom.created_by)
    ).all()
    
    # Sous-requête pour le dernier message de chaque room
    last_msg_subq = db.session.query(
        ChatMessage.room_id,
        func.max(ChatMessage.created_at).label('max_created_at')
    ).filter_by(is_deleted=False).group_by(ChatMessage.room_id).subquery()
    
    # Récupérer tous les derniers messages en une seule requête
    room_ids_list = [r.id for r in rooms]
    if room_ids_list:
        last_messages = db.session.query(ChatMessage).join(
            last_msg_subq,
            and_(
                ChatMessage.room_id == last_msg_subq.c.room_id,
                ChatMessage.created_at == last_msg_subq.c.max_created_at,
                ChatMessage.is_deleted == False
            )
        ).filter(ChatMessage.room_id.in_(room_ids_list)).options(
            joinedload(ChatMessage.sender)
        ).all()
        last_message_map = {msg.room_id: msg for msg in last_messages}
    else:
        last_message_map = {}
    
    # Calculer les non lus de manière optimisée
    unread_counts = {}
    if room_ids_list:
        # Récupérer les membres avec last_read_at en une seule requête
        memberships_for_rooms = db.session.query(ChatRoomMember).filter(
            ChatRoomMember.room_id.in_(room_ids_list),
            ChatRoomMember.user_id == current_user.id
        ).all()
        membership_read_map = {m.room_id: m.last_read_at for m in memberships_for_rooms}
        
        # Pour chaque room, compter les non lus avec une requête optimisée
        for room_id in room_ids_list:
            last_read = membership_read_map.get(room_id)
            unread_query = ChatMessage.query.filter_by(room_id=room_id)\
                .filter_by(is_deleted=False)\
                .filter(ChatMessage.sender_id != current_user.id)
            
            if last_read:
                unread_query = unread_query.filter(ChatMessage.created_at > last_read)
            
            unread_count = unread_query.count()
            if unread_count > 0:
                unread_counts[room_id] = unread_count
    
    # Construire rooms_data
    rooms_data = []
    for room in rooms:
        membership = membership_map.get(room.id)
        last_message = last_message_map.get(room.id)
        unread_count = unread_counts.get(room.id, 0)
        
        rooms_data.append({
            'id': room.id,
            'name': room.name,
            'type': room.room_type,
            'last_message': {
                'content': last_message.content[:100] if last_message else None,
                'created_at': last_message.created_at.isoformat() if last_message else None
            } if last_message else None,
            'unread_count': unread_count
        })
    
    return jsonify({'rooms': rooms_data})


@chat_bp.route('/api/rooms', methods=['POST'])
@exempt_from_csrf
@login_required
def api_room_create():
    """API: Créer une nouvelle conversation"""
    try:
        if not has_permission(current_user, 'chat.create'):
            return jsonify({'error': 'Permission refusée'}), 403
        
        # Essayer de parser le JSON même si Content-Type n'est pas exact
        data = None
        try:
            if request.is_json:
                data = request.get_json()
            else:
                # Essayer de parser quand même
                data = request.get_json(force=True, silent=True)
                if data is None:
                    # Essayer de lire le body brut
                    try:
                        import json
                        body = request.get_data(as_text=True)
                        if body:
                            data = json.loads(body)
                    except:
                        pass
        except Exception as e:
            return jsonify({'error': 'Données JSON invalides', 'details': str(e)}), 400
        
        if not data:
            return jsonify({'error': 'Données JSON invalides ou vides', 'details': 'Aucune donnée reçue'}), 400
        
        # Accepter à la fois 'type' et 'room_type' pour compatibilité
        room_type = data.get('type') or data.get('room_type', 'direct')
        user_ids = data.get('user_ids', [])
        
        if room_type == 'direct' and len(user_ids) != 1:
            return jsonify({'error': 'Une conversation directe nécessite exactement un autre utilisateur'}), 400
        
        # Vérifier si une conversation directe existe déjà
        # Une conversation directe entre deux utilisateurs est unique, peu importe qui l'a créée
        if room_type == 'direct':
            target_user_id = user_ids[0]
            # Trouver toutes les rooms où l'utilisateur actuel est membre
            current_user_rooms = ChatRoomMember.query.filter_by(user_id=current_user.id).with_entities(ChatRoomMember.room_id).all()
            current_user_room_ids = [r.room_id for r in current_user_rooms]
            
            # Trouver les rooms directes qui contiennent aussi l'utilisateur cible
            existing_room = db.session.query(ChatRoom).join(ChatRoomMember, ChatRoom.id == ChatRoomMember.room_id).filter(
                ChatRoom.id.in_(current_user_room_ids),
                ChatRoom.room_type == 'direct',
                ChatRoomMember.user_id == target_user_id
            ).group_by(ChatRoom.id).having(func.count(ChatRoomMember.id) == 2).first()
            
            if existing_room:
                return jsonify({'room_id': existing_room.id}), 200
        
        # Créer la room
        room = ChatRoom(
            name=data.get('name'),
            room_type=room_type,
            created_by_id=current_user.id
        )
        db.session.add(room)
        db.session.flush()
        
        # Ajouter les membres
        # Créateur
        creator_member = ChatRoomMember(
            room_id=room.id,
            user_id=current_user.id,
            role='admin' if room_type != 'direct' else 'member'
        )
        db.session.add(creator_member)
        
        # Autres utilisateurs
        for user_id in user_ids:
            if user_id != current_user.id:
                member = ChatRoomMember(
                    room_id=room.id,
                    user_id=user_id,
                    role='member'
                )
                db.session.add(member)
        
        db.session.commit()
        
        return jsonify({'room_id': room.id, 'message': 'Conversation créée avec succès'}), 201
        
    except Exception as e:
        db.session.rollback()
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Erreur lors de la création de la conversation', 'details': str(e)}), 500
        
    except Exception as e:
        db.session.rollback()
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Erreur lors de la création de la conversation', 'details': str(e)}), 500


@chat_bp.route('/api/rooms/<int:room_id>/messages', methods=['GET'])
@login_required
def api_messages_list(room_id):
    """API: Liste des messages d'une conversation"""
    if not has_permission(current_user, 'chat.read'):
        return jsonify({'error': 'Permission refusée'}), 403
    
    # Vérifier que l'utilisateur est membre
    membership = ChatRoomMember.query.filter_by(room_id=room_id, user_id=current_user.id).first()
    if not membership:
        return jsonify({'error': 'Accès refusé'}), 403
    
    # Paramètres de pagination
    since = request.args.get('since')
    limit = request.args.get('limit', 50, type=int)
    
    # Valider et limiter la limite
    if limit < 1:
        limit = 50
    elif limit > 200:
        limit = 200
    
    query = ChatMessage.query.filter_by(room_id=room_id, is_deleted=False)
    
    if since:
        try:
            since_dt = datetime.fromisoformat(since.replace('Z', '+00:00'))
            query = query.filter(ChatMessage.created_at > since_dt)
        except (ValueError, AttributeError) as e:
            # Logger l'erreur au lieu de l'ignorer silencieusement
            import logging
            logging.warning(f"Erreur lors du parsing de la date 'since': {e}")
            # Continuer sans filtre de date
    
    messages = query.order_by(ChatMessage.created_at.desc()).limit(limit).all()
    messages.reverse()
    
    messages_data = []
    for msg in messages:
        messages_data.append({
            'id': msg.id,
            'sender_id': msg.sender_id,
            'sender_name': msg.sender.username,
            'content': msg.content,
            'message_type': msg.message_type,
            'is_edited': msg.is_edited,
            'reply_to_id': msg.reply_to_id,
            'created_at': msg.created_at.isoformat(),
            'attachments': [{
                'id': att.id,
                'file_name': att.file_name,
                'file_url': get_file_url(att.file_path),
                'file_size': att.file_size,
                'file_size_formatted': format_file_size(att.file_size),
                'file_type': att.file_type,
                'is_image': att.is_image,
                'thumbnail_url': get_file_url(att.thumbnail_path) if att.thumbnail_path else None
            } for att in msg.attachments]
        })
    
    return jsonify({'messages': messages_data})


@chat_bp.route('/api/rooms/<int:room_id>/messages', methods=['POST'])
@exempt_from_csrf
@login_required
def api_message_create(room_id):
    """API: Envoyer un message"""
    if not has_permission(current_user, 'chat.create'):
        return jsonify({'error': 'Permission refusée'}), 403
    
    # Vérifier que l'utilisateur est membre
    membership = ChatRoomMember.query.filter_by(room_id=room_id, user_id=current_user.id).first()
    if not membership:
        return jsonify({'error': 'Accès refusé'}), 403
    
    content = request.form.get('content', '').strip()
    reply_to_id = request.form.get('reply_to_id')
    
    # Vérifier les fichiers avant de créer le message
    files_to_upload = []
    if 'files' in request.files:
        files_to_upload = [f for f in request.files.getlist('files') if f.filename]
        
        # Valider la taille des fichiers avant de créer le message
        from .utils import MAX_FILE_SIZE
        for file in files_to_upload:
            file.seek(0, os.SEEK_END)
            file_size = file.tell()
            file.seek(0)
            if file_size > MAX_FILE_SIZE:
                return jsonify({'error': f'Fichier "{file.filename}" trop volumineux: {file_size} bytes (max: {MAX_FILE_SIZE})'}), 400
    
    if not content and not files_to_upload:
        return jsonify({'error': 'Le message ne peut pas être vide'}), 400
    
    # Vérifier que reply_to_id existe et appartient à la même room
    reply_to = None
    if reply_to_id:
        try:
            reply_to = ChatMessage.query.filter_by(id=int(reply_to_id), room_id=room_id, is_deleted=False).first()
            if not reply_to:
                return jsonify({'error': 'Message de réponse introuvable'}), 400
        except (ValueError, TypeError):
            reply_to_id = None
    
    # Créer le message
    message = ChatMessage(
        room_id=room_id,
        sender_id=current_user.id,
        content=content or '[Fichier]',
        message_type='file' if files_to_upload else 'text',
        reply_to_id=int(reply_to_id) if reply_to_id and reply_to else None
    )
    db.session.add(message)
    db.session.flush()
    
    # Gérer les fichiers uploadés
    attachments_data = []
    if files_to_upload:
        for file in files_to_upload:
            try:
                file_data = save_chat_file(file, room_id, message.id)
                attachment = ChatAttachment(
                    message_id=message.id,
                    **file_data
                )
                db.session.add(attachment)
                attachments_data.append(file_data)
            except Exception as e:
                db.session.rollback()
                return jsonify({'error': str(e)}), 400
    
    db.session.commit()
    
    # Marquer comme lu par l'expéditeur (l'expéditeur a déjà lu son propre message)
    existing_read = ChatMessageRead.query.filter_by(
        message_id=message.id,
        user_id=current_user.id
    ).first()
    if not existing_read:
        read = ChatMessageRead(message_id=message.id, user_id=current_user.id)
        db.session.add(read)
    
    # Mettre à jour last_read_at pour tous les membres de la room
    membership = ChatRoomMember.query.filter_by(room_id=room_id, user_id=current_user.id).first()
    if membership:
        membership.last_read_at = datetime.now(UTC)
    
    db.session.commit()
    
    # Formater les attachments comme dans format_message_for_sse
    formatted_attachments = []
    for att_data in attachments_data:
        formatted_attachments.append({
            'id': att_data.get('id'),
            'file_name': att_data.get('file_name', ''),
            'file_path': att_data.get('file_path', ''),
            'file_size': att_data.get('file_size', 0),
            'file_type': att_data.get('file_type', ''),
            'is_image': att_data.get('is_image', False),
            'thumbnail_path': att_data.get('thumbnail_path')
        })
    
    return jsonify({
        'message_id': message.id,
        'id': message.id,  # Pour compatibilité
        'sender_id': message.sender_id,
        'sender_name': message.sender.username,
        'content': message.content,
        'created_at': message.created_at.isoformat(),
        'attachments': formatted_attachments
    }), 201


@chat_bp.route('/files/<path:file_path>')
@login_required
def file_download(file_path):
    """Télécharger un fichier de chat"""
    if not has_permission(current_user, 'chat.read'):
        return jsonify({'error': 'Permission refusée'}), 403
    
    # Extraire room_id du chemin et sécuriser contre path traversal
    parts = file_path.split('/')
    if len(parts) < 3 or parts[0] != 'chat':
        return jsonify({'error': 'Chemin invalide'}), 400
    
    # Vérifier qu'il n'y a pas de path traversal (..)
    if '..' in file_path or file_path.startswith('/'):
        return jsonify({'error': 'Chemin invalide'}), 400
    
    try:
        room_id = int(parts[1])
    except ValueError:
        return jsonify({'error': 'Chemin invalide'}), 400
    
    # Vérifier que l'utilisateur est membre
    membership = ChatRoomMember.query.filter_by(room_id=room_id, user_id=current_user.id).first()
    if not membership:
        return jsonify({'error': 'Accès refusé'}), 403
    
    # Chemin complet du fichier
    from config import Config
    upload_folder = Path(Config.UPLOAD_FOLDER)
    file_full_path = upload_folder / file_path
    
    if not file_full_path.exists():
        return jsonify({'error': 'Fichier non trouvé'}), 404
    
    # Envoyer le fichier
    directory = str(file_full_path.parent)
    filename = file_full_path.name
    
    return send_from_directory(directory, filename, as_attachment=True)


@chat_bp.route('/api/messages/<int:message_id>', methods=['PATCH'])
@login_required
def api_message_update(message_id):
    """API: Modifier un message"""
    if not has_permission(current_user, 'chat.update'):
        return jsonify({'error': 'Permission refusée'}), 403
    
    message = ChatMessage.query.get_or_404(message_id)
    
    # Vérifier que c'est le propriétaire du message
    if message.sender_id != current_user.id:
        return jsonify({'error': 'Vous ne pouvez modifier que vos propres messages'}), 403
    
    # Vérifier que le message n'est pas supprimé
    if message.is_deleted:
        return jsonify({'error': 'Message supprimé'}), 400
    
    data = request.get_json()
    new_content = data.get('content', '').strip()
    
    if not new_content:
        return jsonify({'error': 'Le message ne peut pas être vide'}), 400
    
    # Mettre à jour le message
    message.content = new_content
    message.is_edited = True
    message.edited_at = datetime.now(UTC)
    db.session.commit()
    
    return jsonify({
        'id': message.id,
        'content': message.content,
        'is_edited': message.is_edited,
        'edited_at': message.edited_at.isoformat() if message.edited_at else None
    }), 200


@chat_bp.route('/api/messages/<int:message_id>', methods=['DELETE'])
@login_required
def api_message_delete(message_id):
    """API: Supprimer un message"""
    if not has_permission(current_user, 'chat.delete'):
        return jsonify({'error': 'Permission refusée'}), 403
    
    message = ChatMessage.query.get_or_404(message_id)
    
    # Vérifier que c'est le propriétaire du message
    if message.sender_id != current_user.id:
        return jsonify({'error': 'Vous ne pouvez supprimer que vos propres messages'}), 403
    
    # Marquer comme supprimé (soft delete)
    message.is_deleted = True
    message.deleted_at = datetime.now(UTC)
    message.content = '[Message supprimé]'
    db.session.commit()
    
    return jsonify({'message': 'Message supprimé'}), 200


@chat_bp.route('/api/rooms/<int:room_id>/read-status', methods=['POST'])
@exempt_from_csrf
@login_required
def api_read_status(room_id):
    """API: Récupérer les statuts de lecture pour plusieurs messages"""
    if not has_permission(current_user, 'chat.read'):
        return jsonify({'error': 'Permission refusée'}), 403
    
    # Vérifier que l'utilisateur est membre
    membership = ChatRoomMember.query.filter_by(room_id=room_id, user_id=current_user.id).first()
    if not membership:
        return jsonify({'error': 'Accès refusé'}), 403
    
    data = request.get_json()
    message_ids = data.get('message_ids', [])
    
    if not message_ids:
        return jsonify({'read_statuses': {}}), 200
    
    # Récupérer le nombre total de membres (sans l'expéditeur)
    total_members = ChatRoomMember.query.filter_by(room_id=room_id).count()
    
    # Pour chaque message, compter les lecteurs
    read_statuses = {}
    for msg_id in message_ids:
        # Vérifier que le message appartient à cette room
        message = ChatMessage.query.filter_by(id=msg_id, room_id=room_id).first()
        if not message:
            continue
        
        # Compter les lecteurs (sauf l'expéditeur)
        read_count = ChatMessageRead.query.filter_by(message_id=msg_id)\
            .filter(ChatMessageRead.user_id != message.sender_id)\
            .count()
        
        read_statuses[str(msg_id)] = {
            'read_count': read_count,
            'total_members': total_members - 1  # Exclure l'expéditeur
        }
    
    return jsonify({'read_statuses': read_statuses}), 200


@chat_bp.route('/api/rooms/<int:room_id>/search', methods=['GET'])
@login_required
def api_search_messages(room_id):
    """API: Rechercher dans les messages d'une conversation"""
    if not has_permission(current_user, 'chat.read'):
        return jsonify({'error': 'Permission refusée'}), 403
    
    # Vérifier que l'utilisateur est membre
    membership = ChatRoomMember.query.filter_by(room_id=room_id, user_id=current_user.id).first()
    if not membership:
        return jsonify({'error': 'Accès refusé'}), 403
    
    query = request.args.get('q', '').strip()
    if not query or len(query) < 2:
        return jsonify({'results': []}), 200
    
    # Rechercher dans les messages (non supprimés)
    from sqlalchemy import or_
    messages = ChatMessage.query.filter_by(room_id=room_id, is_deleted=False)\
        .filter(ChatMessage.content.like(f'%{query}%'))\
        .options(joinedload(ChatMessage.sender))\
        .order_by(ChatMessage.created_at.desc())\
        .limit(20)\
        .all()
    
    results = []
    for msg in messages:
        results.append({
            'id': msg.id,
            'sender_name': msg.sender.username,
            'content': msg.content,
            'created_at': msg.created_at.isoformat()
        })
    
    return jsonify({'results': results}), 200


@chat_bp.route('/api/search', methods=['GET'])
@login_required
def api_global_search():
    """API: Recherche globale dans toutes les conversations"""
    if not has_permission(current_user, 'chat.read'):
        return jsonify({'error': 'Permission refusée'}), 403
    
    query = request.args.get('q', '').strip()
    if not query or len(query) < 2:
        return jsonify({'results': []}), 200
    
    # Récupérer toutes les conversations de l'utilisateur
    memberships = ChatRoomMember.query.filter_by(user_id=current_user.id).all()
    room_ids = [m.room_id for m in memberships]
    
    if not room_ids:
        return jsonify({'results': []}), 200
    
    # Rechercher dans tous les messages de ces conversations
    messages = ChatMessage.query.filter(
        ChatMessage.room_id.in_(room_ids),
        ChatMessage.is_deleted == False,
        ChatMessage.content.like(f'%{query}%')
    ).options(joinedload(ChatMessage.sender))\
     .options(joinedload(ChatMessage.room))\
     .order_by(ChatMessage.created_at.desc())\
     .limit(50)\
     .all()
    
    results = []
    for msg in messages:
        # Récupérer le nom de la conversation
        room_name = 'Conversation'
        if msg.room.room_type == 'direct':
            other_member = ChatRoomMember.query.filter_by(room_id=msg.room.id)\
                .filter(ChatRoomMember.user_id != current_user.id).first()
            if other_member:
                room_name = other_member.user.username
        else:
            room_name = msg.room.name or 'Groupe'
        
        results.append({
            'room_id': msg.room_id,
            'room_name': room_name,
            'message_id': msg.id,
            'sender_name': msg.sender.username,
            'content': msg.content,
            'created_at': msg.created_at.isoformat()
        })
    
    return jsonify({'results': results}), 200


@chat_bp.route('/api/stats', methods=['GET'])
@login_required
def api_chat_stats():
    """API: Statistiques du chat"""
    if not has_permission(current_user, 'chat.read'):
        return jsonify({'error': 'Permission refusée'}), 403
    
    from datetime import timedelta
    today_start = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Compter les messages d'aujourd'hui dans toutes les conversations de l'utilisateur
    memberships = ChatRoomMember.query.filter_by(user_id=current_user.id).all()
    room_ids = [m.room_id for m in memberships]
    
    today_messages = 0
    if room_ids:
        today_messages = ChatMessage.query.filter(
            ChatMessage.room_id.in_(room_ids),
            ChatMessage.is_deleted == False,
            ChatMessage.created_at >= today_start
        ).count()
    
    return jsonify({
        'today_messages': today_messages
    }), 200


# Route supprimée - doublon avec api_room_create() ci-dessus
# Cette route causait des conflits car Flask utilisait la première route définie

