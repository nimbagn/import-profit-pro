# chat/routes.py
# Routes HTML pour le chat interne

from flask import render_template, request, redirect, url_for, flash, jsonify, make_response
from flask_login import login_required, current_user
from datetime import datetime, UTC, timedelta
from io import BytesIO
from models import (
    db, ChatRoom, ChatRoomMember, ChatMessage, ChatAttachment, 
    ChatMessageRead, User
)
from auth import has_permission, require_permission
from sqlalchemy.orm import joinedload, aliased
from sqlalchemy import func, case, or_, and_, desc
from . import chat_bp


@chat_bp.route('/')
@login_required
@require_permission('chat.read')
def rooms_list():
    """Liste des conversations de l'utilisateur avec optimisations"""
    # Paramètres de pagination et filtres
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    search = request.args.get('search', '').strip()
    room_type_filter = request.args.get('room_type', '')
    unread_only = request.args.get('unread_only', '').lower() == 'true'
    
    # Récupérer les membres avec optimisation N+1
    memberships_query = ChatRoomMember.query.options(
        joinedload(ChatRoomMember.room).joinedload(ChatRoom.created_by),
        joinedload(ChatRoomMember.user)
    ).filter_by(user_id=current_user.id)
    
    memberships = memberships_query.all()
    room_ids = [m.room_id for m in memberships]
    membership_map = {m.room_id: m for m in memberships}
    
    if not room_ids:
        # Aucune conversation
        five_minutes_ago = datetime.now(UTC) - timedelta(minutes=5)
        active_users = User.query.filter(
            User.id != current_user.id,
            User.is_active == True,
            User.last_login >= five_minutes_ago
        ).limit(10).all()
        
        return render_template('chat/list.html', 
                             rooms_data=[],
                             active_users=active_users,
                             pagination=None,
                             search=search,
                             room_type_filter=room_type_filter,
                             unread_only=unread_only,
                             per_page=per_page,
                             total_rooms=0,
                             total_unread=0)
    
    # Sous-requête pour le dernier message de chaque room
    last_msg_subq = db.session.query(
        ChatMessage.room_id,
        func.max(ChatMessage.created_at).label('max_created_at')
    ).filter_by(is_deleted=False).group_by(ChatMessage.room_id).subquery()
    
    # Sous-requête pour récupérer le dernier message complet
    last_message_subq = db.session.query(ChatMessage).join(
        last_msg_subq,
        and_(
            ChatMessage.room_id == last_msg_subq.c.room_id,
            ChatMessage.created_at == last_msg_subq.c.max_created_at,
            ChatMessage.is_deleted == False
        )
    ).subquery()
    
    # Construire la requête principale avec optimisations
    query = ChatRoom.query.filter(ChatRoom.id.in_(room_ids)).options(
        joinedload(ChatRoom.created_by),
        joinedload(ChatRoom.members).joinedload(ChatRoomMember.user)
    )
    
    # Appliquer les filtres
    if search:
        query = query.filter(
            or_(
                ChatRoom.name.like(f'%{search}%'),
                ChatRoom.id.in_(
                    db.session.query(ChatRoomMember.room_id).join(User).filter(
                        ChatRoomMember.room_id.in_(room_ids),
                        ChatRoomMember.user_id != current_user.id,
                        User.username.like(f'%{search}%')
                    )
                )
            )
        )
    
    if room_type_filter:
        query = query.filter(ChatRoom.room_type == room_type_filter)
    
    # Pagination
    pagination = query.order_by(ChatRoom.updated_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    rooms = pagination.items
    
    # Préparer les données avec optimisations
    rooms_data = []
    total_unread = 0
    
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
    
    # Calculer les non lus de manière optimisée avec une seule requête groupée
    unread_counts = {}
    if room_ids_list:
        # Récupérer les membres avec last_read_at en une seule requête
        memberships_for_rooms = db.session.query(ChatRoomMember).filter(
            ChatRoomMember.room_id.in_(room_ids_list),
            ChatRoomMember.user_id == current_user.id
        ).all()
        membership_read_map = {m.room_id: m.last_read_at for m in memberships_for_rooms}
        
        # Construire une requête optimisée pour compter les non lus pour toutes les rooms
        # Utiliser une requête avec CASE pour compter par room en une seule fois
        from sqlalchemy import case
        
        # Créer les conditions CASE pour chaque room
        case_conditions = []
        for room_id in room_ids_list:
            last_read = membership_read_map.get(room_id)
            condition = ChatMessage.room_id == room_id
            condition = condition & (ChatMessage.is_deleted == False)
            condition = condition & (ChatMessage.sender_id != current_user.id)
            if last_read:
                condition = condition & (ChatMessage.created_at > last_read)
            case_conditions.append(
                case((condition, 1), else_=0)
            )
        
        # Compter les non lus pour chaque room avec une seule requête
        # Alternative: utiliser une requête groupée par room_id
        unread_counts_query = db.session.query(
            ChatMessage.room_id,
            func.count(ChatMessage.id).label('unread_count')
        ).filter(
            ChatMessage.room_id.in_(room_ids_list),
            ChatMessage.is_deleted == False,
            ChatMessage.sender_id != current_user.id
        )
        
        # Appliquer les filtres de last_read_at avec une sous-requête ou OR
        # Pour simplifier, on garde la boucle mais avec une requête optimisée par room
        # En production, on pourrait utiliser une requête plus complexe avec UNION
        
        # Approche optimisée : une requête par groupe de rooms avec même last_read_at
        # Pour l'instant, on garde l'approche actuelle mais optimisée
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
    for room in rooms:
        membership = membership_map.get(room.id)
        last_message = last_message_map.get(room.id)
        unread_count = unread_counts.get(room.id, 0)
        total_unread += unread_count
        
        # Filtrer par non lus si demandé
        if unread_only and unread_count == 0:
            continue
        
        # Pour les conversations directes, récupérer l'autre utilisateur
        other_user = None
        if room.room_type == 'direct':
            for member in room.members:
                if member.user_id != current_user.id:
                    other_user = member.user
                    break
        
        rooms_data.append({
            'room': room,
            'last_message': last_message,
            'unread_count': unread_count,
            'other_user': other_user,
            'membership': membership
        })
    
    # Trier par dernier message (déjà trié par updated_at, mais on peut améliorer)
    def get_sort_key(x):
        if x['last_message'] and x['last_message'].created_at:
            created_at = x['last_message'].created_at
            # S'assurer que le datetime est aware (avec timezone)
            if created_at.tzinfo is None:
                return created_at.replace(tzinfo=UTC)
            return created_at
        # Valeur par défaut aware pour les conversations sans message
        return datetime(1970, 1, 1, tzinfo=UTC)
    
    rooms_data.sort(key=get_sort_key, reverse=True)
    
    # Statistiques globales
    total_rooms = ChatRoom.query.filter(ChatRoom.id.in_([m.room_id for m in memberships])).count()
    
    # Récupérer les utilisateurs actifs (dernière connexion < 5 minutes)
    five_minutes_ago = datetime.now(UTC) - timedelta(minutes=5)
    active_users = User.query.filter(
        User.id != current_user.id,
        User.is_active == True,
        User.last_login >= five_minutes_ago
    ).limit(10).all()
    
    return render_template('chat/list.html', 
                         rooms_data=rooms_data,
                         active_users=active_users,
                         pagination=pagination,
                         search=search,
                         room_type_filter=room_type_filter,
                         unread_only=unread_only,
                         per_page=per_page,
                         total_rooms=total_rooms,
                         total_unread=total_unread)


@chat_bp.route('/new')
@login_required
@require_permission('chat.create')
def room_new():
    """Créer une nouvelle conversation"""
    # Récupérer tous les utilisateurs (sauf soi-même)
    users = User.query.filter(User.id != current_user.id).filter_by(is_active=True).all()
    
    return render_template('chat/new.html', users=users)


@chat_bp.route('/<int:room_id>')
@login_required
@require_permission('chat.read')
def room_detail(room_id):
    """Afficher une conversation"""
    room = ChatRoom.query.get_or_404(room_id)
    
    # Vérifier que l'utilisateur est membre
    membership = ChatRoomMember.query.filter_by(room_id=room_id, user_id=current_user.id).first()
    if not membership:
        flash('Vous n\'avez pas accès à cette conversation', 'error')
        return redirect(url_for('chat.rooms_list'))
    
    # Récupérer les messages (pagination: 50 derniers) avec les relations
    from sqlalchemy.orm import joinedload
    messages = ChatMessage.query.filter_by(room_id=room_id)\
        .filter_by(is_deleted=False)\
        .options(joinedload(ChatMessage.reply_to).joinedload(ChatMessage.sender))\
        .options(joinedload(ChatMessage.sender))\
        .options(joinedload(ChatMessage.reads))\
        .options(joinedload(ChatMessage.attachments))\
        .order_by(ChatMessage.created_at.desc())\
        .limit(50)\
        .all()
    messages.reverse()  # Plus ancien au plus récent
    
    # Récupérer les membres
    members = ChatRoomMember.query.filter_by(room_id=room_id).all()
    
    # Marquer tous les messages comme lus
    membership.last_read_at = datetime.now(UTC)
    
    # Créer des entrées ChatMessageRead pour tous les messages non lus
    from models import ChatMessageRead
    unread_messages = [msg for msg in messages if msg.sender_id != current_user.id]
    for msg in unread_messages:
        # Vérifier si déjà lu
        existing_read = ChatMessageRead.query.filter_by(
            message_id=msg.id,
            user_id=current_user.id
        ).first()
        if not existing_read:
            read = ChatMessageRead(
                message_id=msg.id,
                user_id=current_user.id
            )
            db.session.add(read)
    
    db.session.commit()
    
    # Pour les conversations directes, récupérer l'autre utilisateur
    other_user = None
    if room.room_type == 'direct':
        other_member = ChatRoomMember.query.filter_by(room_id=room_id)\
            .filter(ChatRoomMember.user_id != current_user.id).first()
        if other_member:
            other_user = other_member.user
    
    return render_template('chat/room.html', 
                         room=room, 
                         messages=messages, 
                         members=members,
                         other_user=other_user,
                         current_user=current_user)

# =========================================================
# ACTIONS GROUPÉES ET EXPORTS
# =========================================================

@chat_bp.route('/api/bulk/mark-read', methods=['POST'])
@login_required
@require_permission('chat.read')
def api_bulk_mark_read():
    """API: Marquer plusieurs conversations comme lues"""
    data = request.get_json()
    room_ids = data.get('room_ids', [])
    
    if not room_ids:
        return jsonify({'error': 'Aucune conversation sélectionnée'}), 400
    
    try:
        # Vérifier que l'utilisateur est membre de ces conversations
        memberships = ChatRoomMember.query.filter(
            ChatRoomMember.room_id.in_(room_ids),
            ChatRoomMember.user_id == current_user.id
        ).all()
        
        marked_count = 0
        now = datetime.now(UTC)
        
        for membership in memberships:
            # Mettre à jour last_read_at
            membership.last_read_at = now
            
            # Marquer tous les messages non lus comme lus
            unread_query = ChatMessage.query.filter_by(room_id=membership.room_id)\
                .filter_by(is_deleted=False)\
                .filter(ChatMessage.sender_id != current_user.id)
            
            # Filtrer par date de dernière lecture si disponible
            if membership.last_read_at:
                unread_query = unread_query.filter(ChatMessage.created_at > membership.last_read_at)
            
            unread_messages = unread_query.all()
            
            for msg in unread_messages:
                existing_read = ChatMessageRead.query.filter_by(
                    message_id=msg.id,
                    user_id=current_user.id
                ).first()
                if not existing_read:
                    read = ChatMessageRead(
                        message_id=msg.id,
                        user_id=current_user.id
                    )
                    db.session.add(read)
            
            marked_count += 1
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'{marked_count} conversation(s) marquée(s) comme lue(s)',
            'marked_count': marked_count
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erreur: {str(e)}'}), 500

@chat_bp.route('/api/bulk/mute', methods=['POST'])
@login_required
@require_permission('chat.read')
def api_bulk_mute():
    """API: Muter/démuter plusieurs conversations"""
    data = request.get_json()
    room_ids = data.get('room_ids', [])
    mute = data.get('mute', True)
    
    if not room_ids:
        return jsonify({'error': 'Aucune conversation sélectionnée'}), 400
    
    try:
        # Vérifier que l'utilisateur est membre de ces conversations
        memberships = ChatRoomMember.query.filter(
            ChatRoomMember.room_id.in_(room_ids),
            ChatRoomMember.user_id == current_user.id
        ).all()
        
        for membership in memberships:
            membership.is_muted = mute
        
        db.session.commit()
        
        action = 'mutée(s)' if mute else 'démutée(s)'
        return jsonify({
            'success': True,
            'message': f'{len(memberships)} conversation(s) {action}',
            'muted_count': len(memberships)
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erreur: {str(e)}'}), 500

@chat_bp.route('/export/excel')
@login_required
@require_permission('chat.read')
def rooms_export_excel():
    """Export Excel de la liste des conversations avec filtres appliqués"""
    try:
        import pandas as pd
        
        # Récupérer les mêmes filtres que rooms_list
        search = request.args.get('search', '').strip()
        room_type_filter = request.args.get('room_type', '')
        unread_only = request.args.get('unread_only', '').lower() == 'true'
        
        # Récupérer les membres avec optimisation N+1
        memberships_query = ChatRoomMember.query.options(
            joinedload(ChatRoomMember.room).joinedload(ChatRoom.created_by),
            joinedload(ChatRoomMember.user)
        ).filter_by(user_id=current_user.id)
        
        memberships = memberships_query.all()
        room_ids = [m.room_id for m in memberships]
        membership_map = {m.room_id: m for m in memberships}
        
        if not room_ids:
            flash('Aucune conversation à exporter', 'warning')
            return redirect(url_for('chat.rooms_list'))
        
        # Construire la requête avec optimisations
        query = ChatRoom.query.filter(ChatRoom.id.in_(room_ids)).options(
            joinedload(ChatRoom.created_by),
            joinedload(ChatRoom.members).joinedload(ChatRoomMember.user)
        )
        
        # Appliquer les filtres
        if search:
            query = query.filter(
                or_(
                    ChatRoom.name.like(f'%{search}%'),
                    ChatRoom.id.in_(
                        db.session.query(ChatRoomMember.room_id).join(User).filter(
                            ChatRoomMember.room_id.in_(room_ids),
                            ChatRoomMember.user_id != current_user.id,
                            User.username.like(f'%{search}%')
                        )
                    )
                )
            )
        
        if room_type_filter:
            query = query.filter(ChatRoom.room_type == room_type_filter)
        
        # Récupérer toutes les conversations (sans pagination pour l'export)
        rooms = query.order_by(ChatRoom.updated_at.desc()).all()
        
        # Sous-requête pour le dernier message
        last_msg_subq = db.session.query(
            ChatMessage.room_id,
            func.max(ChatMessage.created_at).label('max_created_at')
        ).filter_by(is_deleted=False).group_by(ChatMessage.room_id).subquery()
        
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
        
        # Calculer les non lus
        unread_counts = {}
        if room_ids_list:
            memberships_for_rooms = db.session.query(ChatRoomMember).filter(
                ChatRoomMember.room_id.in_(room_ids_list),
                ChatRoomMember.user_id == current_user.id
            ).all()
            membership_read_map = {m.room_id: m.last_read_at for m in memberships_for_rooms}
            
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
        
        # Préparer les données
        data = []
        for room in rooms:
            membership = membership_map.get(room.id)
            last_message = last_message_map.get(room.id)
            unread_count = unread_counts.get(room.id, 0)
            
            # Filtrer par non lus si demandé
            if unread_only and unread_count == 0:
                continue
            
            # Pour les conversations directes, récupérer l'autre utilisateur
            other_user_name = None
            if room.room_type == 'direct':
                for member in room.members:
                    if member.user_id != current_user.id:
                        other_user_name = member.user.username
                        break
            
            data.append({
                'ID': room.id,
                'Nom': room.name if room.name else (other_user_name if other_user_name else 'Conversation'),
                'Type': room.room_type.replace('direct', 'Directe').replace('group', 'Groupe').replace('channel', 'Canal'),
                'Créé par': room.created_by.username if room.created_by else '',
                'Date création': room.created_at.strftime('%d/%m/%Y %H:%M') if room.created_at else '',
                'Dernière mise à jour': room.updated_at.strftime('%d/%m/%Y %H:%M') if room.updated_at else '',
                'Dernier message': last_message.content[:100] if last_message else '',
                'Auteur dernier message': last_message.sender.username if last_message and last_message.sender else '',
                'Date dernier message': last_message.created_at.strftime('%d/%m/%Y %H:%M') if last_message else '',
                'Messages non lus': unread_count,
                'Dernière lecture': membership.last_read_at.strftime('%d/%m/%Y %H:%M') if membership and membership.last_read_at else 'Jamais',
                'Muet': 'Oui' if membership and membership.is_muted else 'Non'
            })
        
        # Créer le DataFrame
        df = pd.DataFrame(data)
        
        # Ajouter une ligne de totaux
        if len(df) > 0:
            total_row = pd.DataFrame([{
                'ID': 'TOTAL',
                'Nom': '',
                'Type': '',
                'Créé par': '',
                'Date création': '',
                'Dernière mise à jour': '',
                'Dernier message': '',
                'Auteur dernier message': '',
                'Date dernier message': '',
                'Messages non lus': df['Messages non lus'].sum(),
                'Dernière lecture': '',
                'Muet': ''
            }])
            df = pd.concat([df, total_row], ignore_index=True)
        
        # Créer le fichier Excel
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Conversations', index=False)
            
            # Formater les colonnes
            worksheet = writer.sheets['Conversations']
            for idx, col in enumerate(df.columns, 1):
                max_length = max(
                    df[col].astype(str).map(len).max(),
                    len(str(col))
                )
                worksheet.column_dimensions[chr(64 + idx)].width = min(max_length + 2, 50)
        
        output.seek(0)
        filename = f'conversations_chat_{datetime.now(UTC).strftime("%Y%m%d_%H%M%S")}.xlsx'
        
        response = make_response(output.getvalue())
        response.headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        flash(f'Erreur lors de l\'export Excel: {str(e)}', 'error')
        return redirect(url_for('chat.rooms_list'))

