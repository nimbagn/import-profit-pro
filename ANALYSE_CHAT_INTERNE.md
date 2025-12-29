# 📋 ANALYSE : INTÉGRATION D'UN CHAT INTERNE AVEC PIÈCES JOINTES

**Date :** 20 Novembre 2025  
**Version :** 1.0  
**Projet :** Import Profit Pro

---

## 🎯 OBJECTIF

Intégrer un système de messagerie interne permettant aux utilisateurs de communiquer en temps réel avec la possibilité d'attacher des documents (PDF, images, Excel, etc.).

---

## 📊 ANALYSE DE L'EXISTANT

### Architecture Actuelle

1. **Framework :** Flask avec SQLAlchemy ORM
2. **Base de données :** MySQL (avec fallback SQLite)
3. **Authentification :** Flask-Login avec système de rôles et permissions
4. **Upload de fichiers :** 
   - Dossier `instance/uploads/` déjà configuré
   - `MAX_CONTENT_LENGTH = 25 MB` dans `config.py`
   - Exemple d'utilisation : `VehicleDocument.attachment_url` (chaîne de caractères)

### Points Forts à Exploiter

✅ Système de permissions déjà en place (`has_permission`)  
✅ Structure d'upload déjà configurée  
✅ Modèle `User` avec relations SQLAlchemy  
✅ Interface moderne avec style Hapag-Lloyd  
✅ Blueprints Flask pour modularité  

### Limitations Actuelles

⚠️ Pas de système de notifications en temps réel  
⚠️ Pas de WebSocket pour le chat en temps réel  
⚠️ Upload de fichiers non standardisé (juste `attachment_url` comme string)  

---

## 🏗️ ARCHITECTURE PROPOSÉE

### 1. Modèles de Données

#### 1.1 Table `chat_rooms` (Conversations)
```sql
CREATE TABLE `chat_rooms` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `name` VARCHAR(200),  -- NULL pour conversations 1-1, nom pour groupes
    `room_type` ENUM('direct', 'group', 'channel') NOT NULL DEFAULT 'direct',
    `created_by_id` BIGINT UNSIGNED NOT NULL,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME NULL ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    INDEX `idx_chatroom_creator` (`created_by_id`),
    INDEX `idx_chatroom_type` (`room_type`),
    CONSTRAINT `fk_chatrooms_creator` FOREIGN KEY (`created_by_id`) REFERENCES `users` (`id`) ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

#### 1.2 Table `chat_room_members` (Participants)
```sql
CREATE TABLE `chat_room_members` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `room_id` BIGINT UNSIGNED NOT NULL,
    `user_id` BIGINT UNSIGNED NOT NULL,
    `role` ENUM('member', 'admin', 'moderator') NOT NULL DEFAULT 'member',
    `joined_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `last_read_at` DATETIME NULL,  -- Pour marquer les messages comme lus
    `is_muted` BOOLEAN NOT NULL DEFAULT FALSE,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uq_room_member` (`room_id`, `user_id`),
    INDEX `idx_chatmember_room` (`room_id`),
    INDEX `idx_chatmember_user` (`user_id`),
    INDEX `idx_chatmember_lastread` (`last_read_at`),
    CONSTRAINT `fk_chatmembers_room` FOREIGN KEY (`room_id`) REFERENCES `chat_rooms` (`id`) ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT `fk_chatmembers_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON UPDATE CASCADE ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

#### 1.3 Table `chat_messages` (Messages)
```sql
CREATE TABLE `chat_messages` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `room_id` BIGINT UNSIGNED NOT NULL,
    `sender_id` BIGINT UNSIGNED NOT NULL,
    `content` TEXT NOT NULL,
    `message_type` ENUM('text', 'file', 'system') NOT NULL DEFAULT 'text',
    `is_edited` BOOLEAN NOT NULL DEFAULT FALSE,
    `edited_at` DATETIME NULL,
    `is_deleted` BOOLEAN NOT NULL DEFAULT FALSE,
    `deleted_at` DATETIME NULL,
    `reply_to_id` BIGINT UNSIGNED NULL,  -- Pour répondre à un message
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    INDEX `idx_chatmsg_room` (`room_id`),
    INDEX `idx_chatmsg_sender` (`sender_id`),
    INDEX `idx_chatmsg_created` (`created_at`),
    INDEX `idx_chatmsg_reply` (`reply_to_id`),
    CONSTRAINT `fk_chatmessages_room` FOREIGN KEY (`room_id`) REFERENCES `chat_rooms` (`id`) ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT `fk_chatmessages_sender` FOREIGN KEY (`sender_id`) REFERENCES `users` (`id`) ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT `fk_chatmessages_reply` FOREIGN KEY (`reply_to_id`) REFERENCES `chat_messages` (`id`) ON UPDATE CASCADE ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

#### 1.4 Table `chat_attachments` (Pièces Jointes)
```sql
CREATE TABLE `chat_attachments` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `message_id` BIGINT UNSIGNED NOT NULL,
    `file_name` VARCHAR(255) NOT NULL,
    `file_path` VARCHAR(500) NOT NULL,  -- Chemin relatif dans instance/uploads/chat/
    `file_size` BIGINT UNSIGNED NOT NULL,  -- Taille en octets
    `file_type` VARCHAR(100) NOT NULL,  -- MIME type
    `file_extension` VARCHAR(10) NOT NULL,
    `thumbnail_path` VARCHAR(500) NULL,  -- Pour les images (miniature)
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    INDEX `idx_chatattach_message` (`message_id`),
    INDEX `idx_chatattach_type` (`file_type`),
    CONSTRAINT `fk_chatattachments_message` FOREIGN KEY (`message_id`) REFERENCES `chat_messages` (`id`) ON UPDATE CASCADE ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

#### 1.5 Table `chat_message_reads` (Marqueurs de Lecture)
```sql
CREATE TABLE `chat_message_reads` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `message_id` BIGINT UNSIGNED NOT NULL,
    `user_id` BIGINT UNSIGNED NOT NULL,
    `read_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uq_msg_read` (`message_id`, `user_id`),
    INDEX `idx_chatread_message` (`message_id`),
    INDEX `idx_chatread_user` (`user_id`),
    CONSTRAINT `fk_chatreads_message` FOREIGN KEY (`message_id`) REFERENCES `chat_messages` (`id`) ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT `fk_chatreads_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON UPDATE CASCADE ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

---

## 🔧 COMPOSANTS TECHNIQUES

### 2.1 Technologies à Intégrer

#### Option A : Polling (Simple, Pas de dépendances)
- ✅ **Avantages :** Simple, pas de serveur WebSocket
- ❌ **Inconvénients :** Latence, charge serveur
- **Implémentation :** Endpoint REST `/api/chat/messages?room_id=X&since=timestamp`

#### Option B : Server-Sent Events (SSE) - RECOMMANDÉ
- ✅ **Avantages :** Temps réel, simple, pas de WebSocket
- ❌ **Inconvénients :** Unidirectionnel (serveur → client)
- **Implémentation :** Flask-SSE ou natif avec `Response(stream_with_context())`

#### Option C : WebSocket (Socket.IO)
- ✅ **Avantages :** Bidirectionnel, temps réel optimal
- ❌ **Inconvénients :** Complexité, dépendance Flask-SocketIO
- **Implémentation :** `flask-socketio` avec Redis pour scaling

**RECOMMANDATION :** Commencer avec **Option B (SSE)** pour la simplicité, puis migrer vers WebSocket si nécessaire.

### 2.2 Gestion des Fichiers

#### Structure de Dossiers
```
instance/
  uploads/
    chat/
      {room_id}/
        {message_id}/
          {filename}
          thumbnails/
            {filename}_thumb.jpg
```

#### Types de Fichiers Supportés
- **Documents :** PDF, DOC, DOCX, XLS, XLSX, PPT, PPTX
- **Images :** JPG, PNG, GIF, WEBP (avec génération de miniatures)
- **Archives :** ZIP, RAR, 7Z
- **Taille max :** 25 MB par fichier (configuré dans `config.py`)

#### Sécurité
- Validation du type MIME
- Scan antivirus (optionnel, avec ClamAV)
- Renommage des fichiers (UUID pour éviter les collisions)
- Vérification des permissions (seuls les membres de la room peuvent télécharger)

---

## 📁 STRUCTURE DES FICHIERS

### 3.1 Nouveaux Fichiers à Créer

```
chat/
  __init__.py
  models.py          # Modèles SQLAlchemy pour le chat
  routes.py           # Routes Flask (blueprint)
  api.py              # API REST pour le chat
  sse.py              # Server-Sent Events pour temps réel
  utils.py             # Utilitaires (upload, validation, etc.)
  templates/
    chat_list.html
    chat_room.html
    chat_message.html (partial)
    chat_attachment.html (partial)
  static/
    js/
      chat.js          # JavaScript pour interface chat
      chat_sse.js      # Client SSE
    css/
      chat.css         # Styles spécifiques au chat
```

### 3.2 Modifications aux Fichiers Existants

#### `models.py`
- Ajouter les 5 nouveaux modèles (ChatRoom, ChatRoomMember, ChatMessage, ChatAttachment, ChatMessageRead)

#### `app.py`
- Enregistrer le blueprint `chat_bp`
- Ajouter route SSE pour temps réel

#### `templates/base_modern_complete.html`
- Ajouter lien "Messages" dans le menu latéral
- Ajouter badge de notifications non lues
- Intégrer le widget de chat (optionnel, en bas à droite)

#### `auth.py`
- Ajouter permissions : `chat.read`, `chat.create`, `chat.delete`, `chat.manage_rooms`

---

## 🎨 INTERFACE UTILISATEUR

### 4.1 Page Liste des Conversations (`/chat`)

**Layout :**
```
┌─────────────────────────────────────────────────┐
│  [Nouvelle Conversation] [Nouveau Groupe]       │
├──────────────┬──────────────────────────────────┤
│ Conversations│  Aperçu / Sélection              │
│              │                                   │
│ • User 1     │  [Icône chat vide ou preview]    │
│ • User 2     │                                   │
│ • Groupe A   │  Sélectionnez une conversation   │
│ • Groupe B   │  pour commencer                  │
│              │                                   │
│              │                                   │
└──────────────┴──────────────────────────────────┘
```

**Fonctionnalités :**
- Liste des conversations avec dernier message
- Badge de messages non lus
- Recherche de conversations
- Filtres (Tous, Non lus, Groupes, Directs)

### 4.2 Page Conversation (`/chat/<room_id>`)

**Layout :**
```
┌─────────────────────────────────────────────────┐
│  [← Retour]  Nom Conversation  [⚙️ Paramètres]  │
├─────────────────────────────────────────────────┤
│                                                 │
│  [Zone de messages avec scroll]                 │
│                                                 │
│  ┌─────────────────────────────────────────┐   │
│  │ [📎] [Message...]              [Envoyer]│   │
│  └─────────────────────────────────────────┘   │
└─────────────────────────────────────────────────┘
```

**Fonctionnalités :**
- Affichage des messages avec horodatage
- Indicateurs de lecture (✓ lu, ✓✓ lu par tous)
- Réponse à un message (quote)
- Édition/suppression de ses propres messages
- Upload de fichiers (drag & drop)
- Prévisualisation des images
- Téléchargement des fichiers
- Emojis (optionnel, avec picker)

### 4.3 Widget Chat Flottant (Optionnel)

**Position :** Coin inférieur droit  
**Comportement :** Minimisé par défaut, s'ouvre au clic  
**Fonctionnalités :** Notifications en temps réel, accès rapide aux conversations

---

## 🔐 SÉCURITÉ ET PERMISSIONS

### 5.1 Permissions Requises

```python
ALL_PERMISSIONS = {
    'chat': ['read', 'create', 'update', 'delete', 'manage_rooms'],
    # ...
}
```

- **`chat.read`** : Voir les conversations et messages
- **`chat.create`** : Envoyer des messages et créer des conversations
- **`chat.update`** : Modifier ses propres messages
- **`chat.delete`** : Supprimer ses propres messages
- **`chat.manage_rooms`** : Créer/supprimer des groupes, gérer les membres

### 5.2 Vérifications de Sécurité

1. **Accès aux conversations :** Vérifier que l'utilisateur est membre de la room
2. **Upload de fichiers :** Validation du type, taille, nom
3. **Modification/Suppression :** Seulement ses propres messages
4. **Gestion des rooms :** Seulement les admins/moderators
5. **Rate limiting :** Limiter le nombre de messages par minute (anti-spam)

---

## 🚀 PLAN D'IMPLÉMENTATION

### Phase 1 : Fondations (2-3 jours)
- [ ] Créer les modèles SQLAlchemy
- [ ] Créer les migrations SQL
- [ ] Créer le blueprint `chat_bp`
- [ ] Routes de base (liste, création, affichage)

### Phase 2 : Messages et Upload (2-3 jours)
- [ ] Système d'upload de fichiers
- [ ] Validation et stockage sécurisé
- [ ] Affichage des messages avec pièces jointes
- [ ] Génération de miniatures pour images

### Phase 3 : Temps Réel (2-3 jours)
- [ ] Implémentation SSE
- [ ] Client JavaScript pour SSE
- [ ] Mise à jour automatique de l'interface
- [ ] Indicateurs de "typing" (optionnel)

### Phase 4 : Fonctionnalités Avancées (2-3 jours)
- [ ] Réponse à un message
- [ ] Édition/Suppression de messages
- [ ] Marqueurs de lecture
- [ ] Recherche dans les messages
- [ ] Notifications (badge, son)

### Phase 5 : Interface et UX (2-3 jours)
- [ ] Design responsive
- [ ] Intégration au style Hapag-Lloyd
- [ ] Animations et transitions
- [ ] Tests utilisateurs

**TOTAL ESTIMÉ :** 10-15 jours de développement

---

## 📦 DÉPENDANCES SUPPLÉMENTAIRES

### Optionnel (pour fonctionnalités avancées)

```txt
# requirements.txt additions
Pillow>=10.0.0          # Pour génération de miniatures d'images
python-magic>=0.4.27    # Détection du type MIME
flask-socketio>=5.3.0   # Si WebSocket (Option C)
redis>=5.0.0            # Si WebSocket avec scaling
```

---

## 🧪 TESTS À PRÉVOIR

1. **Tests Unitaires :**
   - Création de conversations
   - Envoi de messages
   - Upload de fichiers
   - Validation des permissions

2. **Tests d'Intégration :**
   - Flux complet de conversation
   - Temps réel (SSE)
   - Gestion des erreurs

3. **Tests de Performance :**
   - Charge avec 100+ utilisateurs simultanés
   - Upload de gros fichiers
   - Requêtes SQL optimisées

---

## 📊 MÉTRIQUES DE SUCCÈS

- ✅ Messages envoyés avec succès > 99%
- ✅ Temps de réponse < 500ms
- ✅ Upload de fichiers < 5s pour 10MB
- ✅ Interface responsive sur mobile
- ✅ Aucune faille de sécurité détectée

---

## 🔄 ÉVOLUTIONS FUTURES

1. **Notifications Push** (navigateur, mobile)
2. **Intégration Email** (notifications par email)
3. **Chatbots** (réponses automatiques)
4. **Intégration avec modules existants** (notifications sur simulations, stocks, etc.)
5. **Export de conversations** (PDF, Excel)
6. **Chiffrement end-to-end** (pour conversations sensibles)

---

## ✅ CONCLUSION

L'intégration d'un chat interne est **faisable** et **cohérente** avec l'architecture existante. Le système de permissions déjà en place facilitera la gestion des accès. L'utilisation de SSE pour le temps réel est un bon compromis entre simplicité et performance.

**Recommandation :** Commencer par une version simple (Phase 1-2), puis itérer avec les fonctionnalités avancées selon les besoins utilisateurs.

---

**Prochaine étape :** Valider cette analyse et commencer l'implémentation de la Phase 1.

