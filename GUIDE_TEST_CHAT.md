# 🧪 GUIDE DE TEST - CHAT INTERNE

## ✅ Vérifications Préalables

### 1. Les modèles sont bien importés
✅ Les 5 modèles de chat sont détectés par SQLAlchemy :
- `ChatRoom`
- `ChatRoomMember`
- `ChatMessage`
- `ChatAttachment`
- `ChatMessageRead`

### 2. Les tables seront créées automatiquement
Les tables seront créées automatiquement au démarrage de l'application grâce à `db.create_all()` dans `app.py`.

**Note :** Si les tables n'existent pas encore, elles seront créées au prochain démarrage.

---

## 🚀 Tests à Effectuer

### Test 1 : Accéder à la page de chat

1. **Connectez-vous** à l'application : http://localhost:5002
2. **Cliquez sur "Messages"** dans le menu latéral (ou accédez directement à http://localhost:5002/chat)
3. **Vérifiez** que la page s'affiche correctement

**Résultat attendu :**
- Page "Messages" s'affiche
- Bouton "Nouvelle Conversation" visible (si vous avez la permission `chat.create`)
- Liste vide ou liste des conversations existantes

---

### Test 2 : Créer une conversation

1. **Cliquez sur "Nouvelle Conversation"**
2. **Sélectionnez un utilisateur** (pour une conversation directe)
3. **Cliquez sur "Créer la conversation"**

**Résultat attendu :**
- Redirection vers la page de conversation
- Interface de chat s'affiche
- Zone de saisie visible

---

### Test 3 : Envoyer un message

1. **Tapez un message** dans la zone de saisie
2. **Cliquez sur "Envoyer"** (ou appuyez sur Entrée)
3. **Vérifiez** que le message apparaît dans la conversation

**Résultat attendu :**
- Message affiché immédiatement
- Avatar et nom de l'expéditeur visibles
- Horodatage affiché

---

### Test 4 : Temps réel (nécessite 2 utilisateurs)

1. **Ouvrez 2 navigateurs** (ou 2 onglets en navigation privée)
2. **Connectez-vous avec 2 utilisateurs différents**
3. **Dans le navigateur 1 :** Créez/ouvrez une conversation avec l'utilisateur 2
4. **Dans le navigateur 2 :** Ouvrez la même conversation
5. **Dans le navigateur 1 :** Envoyez un message
6. **Dans le navigateur 2 :** Vérifiez que le message apparaît automatiquement

**Résultat attendu :**
- Le message apparaît dans le navigateur 2 **sans recharger la page**
- Badge de non lus mis à jour dans la liste des conversations

---

### Test 5 : Upload de fichier

1. **Cliquez sur l'icône trombone** (📎) dans la zone de saisie
2. **Sélectionnez un fichier** (image, PDF, etc.)
3. **Envoyez le message**

**Résultat attendu :**
- Fichier uploadé avec succès
- Lien de téléchargement affiché dans le message
- Pour les images : miniature générée (si Pillow est installé)

---

## 🔍 Vérifications Techniques

### Vérifier que les tables existent

```sql
-- Connectez-vous à MySQL
mysql -u root -p madargn

-- Vérifiez les tables
SHOW TABLES LIKE 'chat_%';

-- Devrait afficher :
-- chat_rooms
-- chat_room_members
-- chat_messages
-- chat_attachments
-- chat_message_reads
```

### Vérifier les permissions

1. **Allez dans** : Gestion des Utilisateurs → Rôles & Permissions
2. **Vérifiez** que le rôle "Administrateur" a les permissions chat :
   - `chat.read`
   - `chat.create`
   - `chat.update`
   - `chat.delete`
   - `chat.manage_rooms`

---

## ⚠️ Problèmes Courants

### Les tables n'existent pas

**Solution :** Les tables seront créées automatiquement au prochain démarrage de l'application.

Ou exécutez manuellement :
```bash
mysql -u root -p madargn < scripts/create_chat_tables_direct.sql
```

### Erreur "Permission refusée"

**Solution :** Vérifiez que votre rôle a les permissions `chat.read` et `chat.create`.

### Les messages n'apparaissent pas en temps réel

**Vérifications :**
1. Ouvrez la console du navigateur (F12)
2. Vérifiez qu'il n'y a pas d'erreurs JavaScript
3. Vérifiez que la connexion SSE est établie (message "✅ Connexion SSE établie")

### Erreur lors de l'upload de fichier

**Vérifications :**
1. Vérifiez que le dossier `instance/uploads/chat/` existe
2. Vérifiez que le fichier ne dépasse pas 25 MB
3. Vérifiez que le type de fichier est autorisé (images, PDF, documents Office)

---

## 📊 Checklist de Test

- [ ] Page `/chat` accessible
- [ ] Création de conversation fonctionne
- [ ] Envoi de message fonctionne
- [ ] Messages affichés correctement
- [ ] Temps réel fonctionne (2 utilisateurs)
- [ ] Upload de fichier fonctionne
- [ ] Badges de non lus mis à jour
- [ ] Liste des conversations mise à jour en temps réel
- [ ] Permissions respectées

---

## 🎯 Prochaines Étapes

Une fois les tests de base validés, vous pouvez :
1. Tester avec plusieurs utilisateurs simultanés
2. Tester l'upload de différents types de fichiers
3. Vérifier les performances avec beaucoup de messages
4. Implémenter la Phase 3 (réponse, édition, suppression)

---

**Bon test ! 🚀**

