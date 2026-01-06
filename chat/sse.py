# chat/sse.py
# Server-Sent Events pour le chat en temps réel

from flask import Response, stream_with_context
from flask_login import login_required, current_user
from datetime import datetime, UTC
import json
import time
from models import (
    db, ChatRoom, ChatRoomMember, ChatMessage, ChatAttachment,
    ChatMessageRead, User
)
from auth import has_permission
from . import chat_bp


def format_message_for_sse(message):
    """Formate un message pour l'envoi via SSE"""
    reply_to_data = None
    if message.reply_to_id and message.reply_to:
        reply_to_data = {
            'id': message.reply_to.id,
            'sender_name': message.reply_to.sender.username,
            'content': message.reply_to.content[:100] if message.reply_to.content else ''
        }
    
    return {
        'id': message.id,
        'room_id': message.room_id,
        'sender_id': message.sender_id,
        'sender_name': message.sender.username,
        'content': message.content,
        'message_type': message.message_type,
        'is_edited': message.is_edited,
        'edited_at': message.edited_at.isoformat() if message.edited_at else None,
        'reply_to_id': message.reply_to_id,
        'reply_to': reply_to_data,
        'created_at': message.created_at.isoformat(),
        'attachments': [{
            'id': att.id,
            'file_name': att.file_name,
            'file_path': att.file_path,
            'file_size': att.file_size,
            'file_type': att.file_type,
            'is_image': att.is_image,
            'thumbnail_path': att.thumbnail_path
        } for att in message.attachments]
    }


@chat_bp.route('/api/stream/<int:room_id>')
@login_required
def stream_messages(room_id):
    """Stream Server-Sent Events pour les nouveaux messages"""
    if not has_permission(current_user, 'chat.read'):
        return Response('Permission refusée', status=403, mimetype='text/plain')
    
    # Vérifier que l'utilisateur est membre
    membership = ChatRoomMember.query.filter_by(room_id=room_id, user_id=current_user.id).first()
    if not membership:
        return Response('Accès refusé', status=403, mimetype='text/plain')
    
    def event_stream():
        """Générateur pour les événements SSE"""
        last_message_id = None
        last_check = datetime.now(UTC)
        
        # Envoyer un message de connexion
        yield f"data: {json.dumps({'type': 'connected', 'timestamp': datetime.now(UTC).isoformat()})}\n\n"
        
        try:
            iteration = 0
            while True:
                iteration += 1
                
                # Envoyer un heartbeat toutes les 10 secondes pour éviter le timeout Gunicorn
                # (Gunicorn timeout par défaut est 30s, on envoie un heartbeat toutes les 10s)
                if iteration % 10 == 0:  # Toutes les 10 itérations (10 * 1s = 10s)
                    yield f"data: {json.dumps({'type': 'heartbeat', 'timestamp': datetime.now(UTC).isoformat()})}\n\n"
                    last_check = datetime.now(UTC)
                
                # Récupérer les nouveaux messages depuis le dernier check avec les relations
                from sqlalchemy.orm import joinedload
                query = ChatMessage.query.filter_by(room_id=room_id, is_deleted=False)\
                    .options(joinedload(ChatMessage.reply_to).joinedload(ChatMessage.sender))\
                    .options(joinedload(ChatMessage.sender))\
                    .options(joinedload(ChatMessage.attachments))
                
                if last_message_id:
                    query = query.filter(ChatMessage.id > last_message_id)
                else:
                    # Pour la première connexion, récupérer les messages depuis le dernier check
                    query = query.filter(ChatMessage.created_at > last_check)
                
                new_messages = query.order_by(ChatMessage.created_at.asc()).all()
                
                for message in new_messages:
                    # Envoyer TOUS les messages (le client décidera s'il doit les afficher)
                    message_data = format_message_for_sse(message)
                    message_data['type'] = 'new_message'
                    yield f"data: {json.dumps(message_data)}\n\n"
                    
                    # Mettre à jour le dernier message ID
                    if not last_message_id or message.id > last_message_id:
                        last_message_id = message.id
                
                # Sleep après avoir envoyé les données pour éviter de bloquer trop longtemps
                # Utiliser un sleep plus court et gérer les interruptions
                try:
                    time.sleep(1)  # Vérifier toutes les 1 seconde
                except (KeyboardInterrupt, SystemExit):
                    # Interruption par Gunicorn (timeout ou shutdown)
                    break
                
        except GeneratorExit:
            # Connexion fermée par le client
            pass
        except (KeyboardInterrupt, SystemExit):
            # Interruption par Gunicorn
            break
        except Exception as e:
            print(f"⚠️ Erreur dans le stream SSE: {e}")
            try:
                yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
            except:
                pass  # Ignorer si le générateur est déjà fermé
    
    return Response(
        stream_with_context(event_stream()),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no',  # Désactiver le buffering pour nginx
            'Connection': 'keep-alive'
        }
    )


@chat_bp.route('/api/stream/rooms')
@login_required
def stream_rooms():
    """Stream Server-Sent Events pour les mises à jour des conversations (nouveaux messages, etc.)"""
    if not has_permission(current_user, 'chat.read'):
        return Response('Permission refusée', status=403, mimetype='text/plain')
    
    def event_stream():
        """Générateur pour les événements SSE des conversations"""
        last_check = datetime.now(UTC)
        last_room_updates = {}  # {room_id: last_message_id}
        
        # Envoyer un message de connexion
        yield f"data: {json.dumps({'type': 'connected', 'timestamp': datetime.now(UTC).isoformat()})}\n\n"
        
        try:
            iteration = 0
            while True:
                iteration += 1
                
                # Envoyer un heartbeat toutes les 10 secondes pour éviter le timeout Gunicorn
                # (Gunicorn timeout par défaut est 30s, on envoie un heartbeat toutes les 10s)
                if iteration % 5 == 0:  # Toutes les 5 itérations (5 * 2s = 10s)
                    yield f"data: {json.dumps({'type': 'heartbeat', 'timestamp': datetime.now(UTC).isoformat()})}\n\n"
                    last_check = datetime.now(UTC)
                
                # Récupérer toutes les conversations de l'utilisateur (optimisé)
                from sqlalchemy.orm import joinedload
                memberships = ChatRoomMember.query.filter_by(user_id=current_user.id).all()
                room_ids = [m.room_id for m in memberships]
                
                if not room_ids:
                    # Envoyer un heartbeat même si pas de rooms pour maintenir la connexion
                    time.sleep(2)
                    continue
                
                # OPTIMISATION: Récupérer tous les derniers messages en une seule requête
                from sqlalchemy import func, and_
                last_msg_subq = db.session.query(
                    ChatMessage.room_id,
                    func.max(ChatMessage.id).label('max_id')
                ).filter_by(is_deleted=False)\
                 .filter(ChatMessage.sender_id != current_user.id)\
                 .filter(ChatMessage.room_id.in_(room_ids))\
                 .group_by(ChatMessage.room_id).subquery()
                
                # Récupérer les derniers messages avec sender en une seule requête
                latest_messages = db.session.query(ChatMessage).join(
                    last_msg_subq,
                    and_(
                        ChatMessage.room_id == last_msg_subq.c.room_id,
                        ChatMessage.id == last_msg_subq.c.max_id
                    )
                ).options(joinedload(ChatMessage.sender)).all()
                
                latest_message_map = {msg.room_id: msg for msg in latest_messages}
                
                # OPTIMISATION: Récupérer tous les membres avec last_read_at en une seule requête
                memberships_map = {m.room_id: m for m in memberships}
                
                # OPTIMISATION: Compter les non lus pour toutes les rooms en une seule requête
                # Utiliser une sous-requête pour compter les non lus par room
                for room_id in room_ids:
                    last_message_id = last_room_updates.get(room_id, 0)
                    latest_message = latest_message_map.get(room_id)
                    
                    # Vérifier s'il y a de nouveaux messages
                    if latest_message and latest_message.id > last_message_id:
                        last_room_updates[room_id] = latest_message.id
                        
                        # Compter les non lus (optimisé)
                        membership = memberships_map.get(room_id)
                        last_read = membership.last_read_at if membership else None
                        
                        if last_read:
                            unread_count = ChatMessage.query.filter_by(room_id=room_id)\
                                .filter(ChatMessage.created_at > last_read)\
                                .filter_by(is_deleted=False)\
                                .filter(ChatMessage.sender_id != current_user.id)\
                                .count()
                        else:
                            unread_count = ChatMessage.query.filter_by(room_id=room_id)\
                                .filter_by(is_deleted=False)\
                                .filter(ChatMessage.sender_id != current_user.id)\
                                .count()
                        
                        # Envoyer la mise à jour
                        yield f"data: {json.dumps({
                            'type': 'room_update',
                            'room_id': room_id,
                            'last_message': {
                                'id': latest_message.id,
                                'content': latest_message.content[:100],
                                'sender_name': latest_message.sender.username,
                                'created_at': latest_message.created_at.isoformat()
                            },
                            'unread_count': unread_count
                        })}\n\n"
                
                # Sleep après avoir envoyé les données pour éviter de bloquer trop longtemps
                # Utiliser un sleep plus court et gérer les interruptions
                try:
                    time.sleep(2)  # Vérifier toutes les 2 secondes
                except (KeyboardInterrupt, SystemExit):
                    # Interruption par Gunicorn (timeout ou shutdown)
                    break
                
        except GeneratorExit:
            pass
        except (KeyboardInterrupt, SystemExit):
            # Interruption par Gunicorn
            break
        except Exception as e:
            print(f"⚠️ Erreur dans le stream SSE rooms: {e}")
            try:
                yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
            except:
                pass  # Ignorer si le générateur est déjà fermé
    
    return Response(
        stream_with_context(event_stream()),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no',
            'Connection': 'keep-alive'
        }
    )

