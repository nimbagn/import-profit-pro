# 🏗️ DIAGRAMME D'ARCHITECTURE - CHAT INTERNE

## 📊 Schéma de Base de Données

```
┌─────────────┐
│   users     │
│  (existant) │
└──────┬──────┘
       │
       │ 1:N
       │
┌──────▼──────────────────────────────────────────┐
│           chat_rooms                            │
│  ────────────────────────────────────────────  │
│  id (PK)                                        │
│  name (VARCHAR)                                  │
│  room_type (ENUM: direct/group/channel)         │
│  created_by_id (FK → users.id)                 │
│  created_at, updated_at                         │
└──────┬──────────────────────────────────────────┘
       │
       │ 1:N
       │
┌──────▼──────────────────────────────────────────┐
│        chat_room_members                         │
│  ────────────────────────────────────────────  │
│  id (PK)                                        │
│  room_id (FK → chat_rooms.id)                   │
│  user_id (FK → users.id)                        │
│  role (ENUM: member/admin/moderator)            │
│  last_read_at                                    │
│  is_muted                                        │
│  UNIQUE(room_id, user_id)                       │
└──────┬──────────────────────────────────────────┘
       │
       │ 1:N
       │
┌──────▼──────────────────────────────────────────┐
│           chat_messages                          │
│  ────────────────────────────────────────────  │
│  id (PK)                                        │
│  room_id (FK → chat_rooms.id)                   │
│  sender_id (FK → users.id)                      │
│  content (TEXT)                                 │
│  message_type (ENUM: text/file/system)          │
│  reply_to_id (FK → chat_messages.id)           │
│  is_edited, is_deleted                          │
│  created_at                                     │
└──────┬──────────────────────────────────────────┘
       │
       │ 1:N
       │
┌──────▼──────────────────────────────────────────┐
│        chat_attachments                          │
│  ────────────────────────────────────────────  │
│  id (PK)                                        │
│  message_id (FK → chat_messages.id)            │
│  file_name, file_path                            │
│  file_size, file_type, file_extension           │
│  thumbnail_path                                  │
└──────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────┐
│        chat_message_reads                        │
│  ────────────────────────────────────────────  │
│  id (PK)                                        │
│  message_id (FK → chat_messages.id)            │
│  user_id (FK → users.id)                        │
│  read_at                                        │
│  UNIQUE(message_id, user_id)                    │
└──────────────────────────────────────────────────┘
```

## 🔄 Flux de Données

### Envoi d'un Message

```
┌─────────┐
│ Client  │
│ (JS)    │
└────┬────┘
     │ POST /chat/api/messages
     │ {room_id, content, files[]}
     ▼
┌─────────────────┐
│  Flask Route    │
│  chat.api       │
└────┬────────────┘
     │ 1. Validation
     │ 2. Vérification permissions
     │ 3. Upload fichiers
     ▼
┌─────────────────┐
│  Database       │
│  - chat_messages│
│  - attachments  │
└────┬────────────┘
     │
     │ SSE Event
     │ "new_message"
     ▼
┌─────────────────┐
│  Tous les       │
│  Clients SSE    │
│  (membres room) │
└─────────────────┘
```

### Temps Réel (SSE)

```
┌─────────────┐
│   Client    │
│  (Browser)  │
└──────┬──────┘
       │ GET /chat/api/stream?room_id=X
       │ Connection: keep-alive
       ▼
┌──────────────────────────┐
│  Flask SSE Endpoint      │
│  @chat_bp.route('/stream')│
│  stream_with_context()    │
└──────┬───────────────────┘
       │
       │ Boucle infinie
       │ Vérifie nouveaux messages
       │ toutes les 1-2 secondes
       │
       ▼
┌──────────────────────────┐
│  Database Query          │
│  SELECT * FROM messages  │
│  WHERE room_id = X       │
│  AND created_at > last   │
└──────┬───────────────────┘
       │
       │ data: {json}
       │
       ▼
┌──────────────────────────┐
│  Client reçoit           │
│  et met à jour UI        │
└───────────────────────────┘
```

## 🗂️ Structure des Fichiers

```
instance/
  uploads/
    chat/
      {room_id}/
        {message_id}/
          document.pdf
          image.jpg
          thumbnails/
            image_thumb.jpg

chat/
  __init__.py
  models.py          # ChatRoom, ChatMessage, etc.
  routes.py          # Routes HTML (liste, room)
  api.py             # API REST (/api/chat/*)
  sse.py             # Server-Sent Events
  utils.py           # upload_file(), validate_file(), etc.

templates/
  chat/
    list.html        # Liste des conversations
    room.html        # Interface de chat
    message.html     # Partial: un message
    attachment.html  # Partial: pièce jointe

static/
  js/
    chat.js          # Logique principale
    chat_sse.js      # Client SSE
  css/
    chat.css         # Styles chat
```

## 🔐 Matrice de Permissions

| Action | Permission Requise | Vérification |
|--------|-------------------|--------------|
| Voir conversations | `chat.read` | ✅ |
| Créer conversation | `chat.create` | ✅ |
| Envoyer message | `chat.create` + membre room | ✅ |
| Modifier message | `chat.update` + propriétaire | ✅ |
| Supprimer message | `chat.delete` + propriétaire | ✅ |
| Créer groupe | `chat.manage_rooms` | ✅ |
| Gérer membres | `chat.manage_rooms` + admin room | ✅ |
| Upload fichier | `chat.create` + membre room | ✅ |
| Télécharger fichier | `chat.read` + membre room | ✅ |

## 📱 Responsive Design

```
Desktop (> 1024px)
┌─────────────────────────────────────┐
│  Sidebar |  Chat Area |  Info Panel │
│  250px   |    flex    |    300px     │
└─────────────────────────────────────┘

Tablet (768px - 1024px)
┌─────────────────────────────┐
│  Sidebar |  Chat Area       │
│  200px   |    flex          │
└─────────────────────────────┘

Mobile (< 768px)
┌─────────────────────────────┐
│  [Menu]  Chat Area          │
│  (overlay)  (full width)    │
└─────────────────────────────┘
```

## ⚡ Optimisations

1. **Index SQL :**
   - `idx_chatmsg_room_created` sur `(room_id, created_at)`
   - `idx_chatmember_user` sur `user_id`
   - `idx_chatread_user_message` sur `(user_id, message_id)`

2. **Cache :**
   - Cache Redis pour liste des rooms (optionnel)
   - Cache des miniatures d'images

3. **Pagination :**
   - Chargement par batch de 50 messages
   - Lazy loading au scroll

4. **Compression :**
   - Gzip pour les réponses JSON
   - Optimisation des images uploadées

