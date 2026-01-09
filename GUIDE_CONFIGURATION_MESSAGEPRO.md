# 📱 Guide Complet - Configuration Message Pro

## 🎯 Vue d'ensemble

Message Pro permet d'envoyer des notifications automatiques (SMS, WhatsApp) pour :
- ✅ Création et validation de commandes
- ✅ Rappels véhicules (documents expirant)
- ✅ Envoi de PDFs d'inventaire et situation de stock

## 🔑 Étape 1 : Obtenir la Clé API

### 1.1 Créer un compte Message Pro

1. Allez sur [https://messagepro-gn.com](https://messagepro-gn.com)
2. Créez un compte ou connectez-vous
3. Allez dans **Tools → API Keys**
4. Créez une nouvelle clé API ou copiez votre clé existante

### 1.2 Obtenir un compte WhatsApp (optionnel mais recommandé)

Pour envoyer des notifications WhatsApp :
1. Dans Message Pro, allez dans **WhatsApp → Accounts**
2. Connectez un compte WhatsApp Business
3. Notez l'ID du compte (nécessaire pour les envois)

## ⚙️ Étape 2 : Configurer la Clé API

Vous avez **2 options** pour configurer la clé API :

### Option A : Via l'Interface Web (Recommandé)

1. **Connectez-vous à l'application** avec un compte ayant les permissions `messaging.update`
2. **Allez dans** : `/messaging/config` ou via le menu "Messagerie → Configuration API"
3. **Entrez votre clé API** dans le formulaire
4. **Cliquez sur "Tester et Enregistrer"**
   - La clé sera testée automatiquement
   - Si valide, elle sera enregistrée dans la base de données

### Option B : Via Variable d'Environnement (Production)

**Sur Render/Heroku :**

1. **Allez dans les paramètres de votre service**
2. **Ajoutez une variable d'environnement** :
   ```
   Nom : MESSAGEPRO_API_SECRET
   Valeur : votre_cle_api_secrete_ici
   ```
3. **Redémarrez l'application**

**Localement :**

1. **Créez/modifiez le fichier `.env`** :
   ```bash
   MESSAGEPRO_API_SECRET=votre_cle_api_secrete_ici
   ```

### Option C : Via Base de Données (SQL)

**PostgreSQL :**
```sql
-- Vérifier si la table existe
SELECT * FROM api_configs WHERE api_name = 'messagepro';

-- Insérer ou mettre à jour la clé
INSERT INTO api_configs (api_name, api_secret, is_active, created_at)
VALUES ('messagepro', 'votre_cle_api_secrete_ici', true, NOW())
ON CONFLICT (api_name) 
DO UPDATE SET 
    api_secret = EXCLUDED.api_secret,
    updated_at = NOW();
```

**MySQL :**
```sql
-- Vérifier si la table existe
SELECT * FROM api_configs WHERE api_name = 'messagepro';

-- Insérer ou mettre à jour la clé
INSERT INTO api_configs (api_name, api_secret, is_active, created_at)
VALUES ('messagepro', 'votre_cle_api_secrete_ici', true, NOW())
ON DUPLICATE KEY UPDATE 
    api_secret = VALUES(api_secret),
    updated_at = NOW();
```

## ✅ Étape 3 : Vérifier la Configuration

### 3.1 Test via l'Interface Web

1. Allez dans `/messaging/config`
2. La page affiche :
   - ✅ **"Clé API configurée"** si tout est OK
   - ✅ **"Crédits disponibles"** si la clé est valide
   - ❌ **"Clé API non configurée"** si la clé est absente

### 3.2 Test via Python

```python
from messagepro_api import MessageProAPI

try:
    api = MessageProAPI()
    credits = api.get_credits()
    
    if credits.get('status') == 200:
        print("✅ Message Pro configuré correctement!")
        print(f"Crédits disponibles: {credits.get('data', {}).get('credits', 'N/A')}")
    else:
        print(f"❌ Erreur: {credits.get('message')}")
except ValueError as e:
    print(f"❌ Configuration manquante: {e}")
```

### 3.3 Test via Terminal

```bash
cd /Users/dantawi/Documents/mini_flask_import_profitability
python3 -c "
from messagepro_api import MessageProAPI
api = MessageProAPI()
result = api.get_credits()
print('Status:', result.get('status'))
print('Message:', result.get('message'))
if result.get('data'):
    print('Crédits:', result.get('data', {}).get('credits', 'N/A'))
"
```

## 🚀 Étape 4 : Utiliser les Notifications Automatiques

Une fois configuré, les notifications fonctionnent automatiquement :

### 4.1 Notifications de Commandes

**Création de commande :**
- Se déclenche automatiquement quand un commercial crée une commande
- Envoie une notification WhatsApp au superviseur

**Validation de commande :**
- Se déclenche automatiquement quand un superviseur valide une commande
- Envoie une notification WhatsApp au commercial

### 4.2 Rappels Véhicules

**Automatique :**
- Envoi quotidien à 8h00 pour les documents expirant dans les 15 prochains jours
- Notification au conducteur + magasinier/superviseur

**Manuel :**
- Bouton "Envoyer rappels" dans le dashboard flotte (`/flotte/dashboard`)

### 4.3 Rapports Stock

**Situation de stock :**
- Bouton "Envoyer par WhatsApp" dans la page de récapitulatif stock
- Envoie le PDF de situation de stock aux superviseurs

**Inventaire de stock :**
- Route `/notifications/inventaire-stock` (POST)
- Génère et envoie le PDF d'inventaire complet

## 🔍 Dépannage

### Problème : "MESSAGEPRO_API_SECRET doit être défini"

**Solution :**
1. Vérifiez que la clé est configurée (Option A, B ou C ci-dessus)
2. Vérifiez que la variable d'environnement est bien définie :
   ```bash
   echo $MESSAGEPRO_API_SECRET
   ```
3. Redémarrez l'application après avoir ajouté la variable

### Problème : "Clé API invalide"

**Solution :**
1. Vérifiez que la clé est correcte (copie sans espaces)
2. Vérifiez que votre compte Message Pro est actif
3. Testez la clé directement sur le site Message Pro

### Problème : "Aucun compte WhatsApp disponible"

**Solution :**
1. Connectez un compte WhatsApp dans Message Pro
2. Vérifiez que le compte est actif
3. L'application utilisera automatiquement le premier compte disponible

### Problème : Les notifications ne partent pas

**Vérifications :**
1. ✅ La clé API est configurée et valide
2. ✅ Un compte WhatsApp est connecté (pour WhatsApp)
3. ✅ Les utilisateurs ont un numéro de téléphone dans leur profil
4. ✅ Les numéros sont au format correct (224XXXXXXXX)
5. ✅ Vérifiez les logs de l'application pour les erreurs

## 📊 Vérifier les Logs

Les notifications sont loggées dans les logs de l'application :

```bash
# Sur Render, allez dans les logs
# Cherchez les lignes avec "Notification" ou "MessagePro"
```

Exemples de logs :
- ✅ `Notification envoyée avec succès à 224XXXXXXXX`
- ❌ `Erreur lors de l'envoi à 224XXXXXXXX: [message d'erreur]`

## 🔐 Sécurité

### Bonnes Pratiques

1. **Ne jamais commiter la clé API** dans Git
2. **Utiliser les variables d'environnement** en production
3. **Limiter les permissions** : Seuls les admins/superviseurs peuvent modifier la config
4. **Vérifier régulièrement** les crédits disponibles

### Rotation des Clés

Si vous devez changer la clé API :
1. Obtenez une nouvelle clé depuis Message Pro
2. Mettez à jour via `/messaging/config` ou la variable d'environnement
3. Testez que tout fonctionne
4. Désactivez l'ancienne clé dans Message Pro

## 📞 Support

### Documentation Message Pro
- Site : [https://messagepro-gn.com](https://messagepro-gn.com)
- Documentation API : Disponible dans votre compte Message Pro

### Support Application
- Vérifiez les logs de l'application
- Consultez `DOCUMENTATION_MESSAGEPRO.md` pour plus de détails
- Route de test : `/messaging/config`

## ✅ Checklist de Configuration

- [ ] Compte Message Pro créé
- [ ] Clé API obtenue
- [ ] Clé API configurée (via interface, variable d'environnement ou SQL)
- [ ] Configuration testée et validée
- [ ] Compte WhatsApp connecté (pour notifications WhatsApp)
- [ ] Numéros de téléphone des utilisateurs renseignés
- [ ] Notifications testées (création commande, rappels véhicules)
- [ ] Logs vérifiés pour s'assurer que tout fonctionne

## 🎉 Résultat Attendu

Une fois configuré, vous devriez voir :
- ✅ Notifications automatiques lors de la création/validation de commandes
- ✅ Rappels automatiques quotidiens pour les documents véhicules
- ✅ Possibilité d'envoyer des PDFs de stock par WhatsApp
- ✅ Tous les logs montrent "Notification envoyée avec succès"

