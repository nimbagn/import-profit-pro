# 📱 Documentation Message Pro - Intégration Complète

## 🎯 Qu'est-ce que Message Pro ?

Message Pro est une plateforme de messagerie qui permet d'envoyer des SMS, WhatsApp et codes OTP via une API REST. Elle offre deux modes d'envoi :
- **Mode "devices"** : Utilise des appareils Android liés (SIM cards physiques)
- **Mode "credits"** : Utilise des gateways/partenaires (nécessite des crédits)

---

## 🏗️ Architecture de l'Intégration

### 1. Module API (`messagepro_api.py`)

Le module `MessageProAPI` est un client Python qui encapsule toutes les interactions avec l'API Message Pro.

#### Structure de base :

```python
from messagepro_api import MessageProAPI

# Initialisation (lit automatiquement MESSAGEPRO_API_SECRET depuis .env)
api = MessageProAPI()

# Exemple : Envoyer un SMS
result = api.send_sms(
    phone="+224601123456",
    message="Votre commande est prête!",
    mode="devices",
    device="device_id",
    sim=1
)
```

#### Fonctionnalités principales :

**Account APIs :**
- `get_credits()` - Voir les crédits restants
- `get_subscription()` - Informations d'abonnement
- `get_earnings()` - Gains partenaire

**SMS APIs :**
- `send_sms()` - Envoyer un SMS unique
- `send_bulk_sms()` - Envoyer des SMS en masse (campagne)
- `get_sent_messages()` - Historique SMS envoyés
- `get_received_messages()` - SMS reçus
- `get_pending_messages()` - SMS en attente

**WhatsApp APIs :**
- `send_whatsapp()` - Envoyer un message WhatsApp unique
- `send_bulk_whatsapp()` - Campagne WhatsApp
- `get_whatsapp_accounts()` - Liste des comptes WhatsApp
- `get_sent_chats()` - Historique WhatsApp envoyés
- `get_received_chats()` - WhatsApp reçus

**OTP APIs :**
- `send_otp()` - Envoyer un code OTP (SMS ou WhatsApp)
- `verify_otp()` - Vérifier un code OTP

**Contacts APIs :**
- `create_contact()` - Créer un contact
- `create_group()` - Créer un groupe
- `get_contacts()` - Liste des contacts
- `get_groups()` - Liste des groupes

---

## 🔧 Configuration

### 1. Obtenir la clé API

1. Connectez-vous à [https://messagepro-gn.com](https://messagepro-gn.com)
2. Allez dans **Tools → API Keys**
3. Copiez votre **API Secret**

### 2. Configurer dans l'application

Ajoutez dans votre fichier `.env` :

```bash
MESSAGEPRO_API_SECRET=votre_cle_api_secrete_ici
```

### 3. Vérifier la configuration

Le module vérifie automatiquement la présence de la clé API. Si elle est absente, une erreur `ValueError` sera levée.

---

## 📨 Fonctionnement des Envois

### Mode "devices" (Appareils Android)

**Avantages :**
- Utilise vos propres SIM cards
- Pas de coût par message
- Contrôle total sur les appareils

**Configuration requise :**
- Appareil Android lié à votre compte Message Pro
- SIM card active dans l'appareil
- ID de l'appareil (obtenu via `get_devices()`)

**Exemple :**
```python
api.send_sms(
    phone="+224601123456",
    message="Bonjour!",
    mode="devices",
    device="abc123-device-id",  # ID de votre appareil
    sim=1,  # Slot SIM 1 ou 2
    priority=0  # 0 ou 1 = immédiat, 2 = en file
)
```

### Mode "credits" (Gateways)

**Avantages :**
- Pas besoin d'appareils physiques
- Envoi via des gateways professionnels
- Plus rapide pour les campagnes massives

**Configuration requise :**
- Crédits suffisants sur votre compte
- ID du gateway ou partenaire (obtenu via `get_rates()`)

**Exemple :**
```python
api.send_sms(
    phone="+224601123456",
    message="Bonjour!",
    mode="credits",
    gateway="gateway-id-123"  # ID du gateway
)
```

---

## 🔐 Codes OTP (One-Time Password)

### Fonctionnement

1. **Envoi du code :**
   ```python
   result = api.send_otp(
       phone="+224601123456",
       message="Votre code OTP est {{otp}}",
       message_type="sms",  # ou "whatsapp"
       expire=300  # Expiration en secondes (5 minutes)
   )
   # Le code OTP est généré automatiquement et inséré dans le message
   # Exemple : "Votre code OTP est 123456"
   ```

2. **Vérification du code :**
   ```python
   result = api.verify_otp(otp="123456")
   # Retourne {"status": 200, "message": "OTP has been verified!"}
   ```

### Cas d'usage typiques :
- Authentification à deux facteurs
- Vérification de numéro de téléphone
- Confirmation de commande
- Réinitialisation de mot de passe

---

## 👥 Gestion des Contacts

### Structure hiérarchique

```
Contacts
  └── Groupes
      └── Contacts (peuvent être dans plusieurs groupes)
```

### Workflow typique :

1. **Créer un groupe :**
   ```python
   api.create_group(name="Clients VIP")
   ```

2. **Créer un contact et l'ajouter au groupe :**
   ```python
   api.create_contact(
       phone="+224601123456",
       name="Jean Dupont",
       groups="1,2"  # IDs des groupes séparés par des virgules
   )
   ```

3. **Envoyer à un groupe :**
   ```python
   api.send_bulk_sms(
       campaign="Promotion VIP",
       message="Offre spéciale pour vous!",
       groups="1"  # ID du groupe
   )
   ```

---

## 📊 Campagnes SMS/WhatsApp

### Campagnes SMS

Les campagnes permettent d'envoyer des messages à plusieurs destinataires :

```python
api.send_bulk_sms(
    campaign="Promotion Janvier 2026",
    message="Découvrez nos nouvelles offres!",
    mode="devices",
    numbers="+224601123456,+224601123457,+224601123458",  # OU
    groups="1,2",  # IDs des groupes
    device="device-id",
    sim=1
)
```

**Avantages :**
- Gestion centralisée des campagnes
- Suivi du statut (en attente, en cours, terminée)
- Possibilité de pause/reprise

### Campagnes WhatsApp

Similaire aux SMS mais pour WhatsApp :

```python
api.send_bulk_whatsapp(
    account="whatsapp-account-id",
    campaign="Newsletter Janvier",
    message="Notre newsletter mensuelle",
    recipients="+224601123456,+224601123457",  # OU
    groups="1",
    message_type="text"  # ou "media", "document"
)
```

---

## 🎨 Interface Web (Blueprint Flask)

### Routes disponibles

| Route | Permission | Description |
|-------|------------|-------------|
| `/messaging/` | `messaging.read` | Dashboard principal |
| `/messaging/sms/send` | `messaging.send_sms` | Envoyer un SMS unique |
| `/messaging/sms/bulk` | `messaging.send_sms` | Campagne SMS |
| `/messaging/sms/history` | `messaging.read` | Historique SMS |
| `/messaging/whatsapp/send` | `messaging.send_whatsapp` | Envoyer WhatsApp |
| `/messaging/whatsapp/history` | `messaging.read` | Historique WhatsApp |
| `/messaging/otp/send` | `messaging.send_otp` | Envoyer un OTP |
| `/messaging/contacts` | `messaging.read` | Liste des contacts |
| `/messaging/contacts/create` | `messaging.manage_contacts` | Créer un contact |

### Permissions requises

Le rôle **superviseur** a toutes les permissions :
- `read` - Consulter l'historique et les contacts
- `send_sms` - Envoyer des SMS
- `send_whatsapp` - Envoyer des messages WhatsApp
- `send_otp` - Envoyer des codes OTP
- `manage_contacts` - Gérer les contacts et groupes

---

## 🔄 Flux d'Envoi d'un SMS

```
1. Utilisateur remplit le formulaire (/messaging/sms/send)
   ↓
2. Blueprint Flask (messaging.py) reçoit la requête POST
   ↓
3. Vérification des permissions (has_permission)
   ↓
4. Initialisation de MessageProAPI()
   ↓
5. Appel à api.send_sms() avec les paramètres
   ↓
6. MessageProAPI fait une requête HTTP POST vers l'API Message Pro
   ↓
7. Message Pro traite la requête et envoie le SMS
   ↓
8. Retour de la réponse JSON avec le statut
   ↓
9. Affichage du message de succès/erreur à l'utilisateur
```

---

## 📝 Format des Numéros de Téléphone

### Format E.164 (Recommandé)

```
+224601123456
```
- `+` : Préfixe international
- `224` : Code pays (Guinée)
- `601123456` : Numéro local

### Format Local

```
601123456
```
- Utilise le code pays configuré dans votre profil Message Pro
- Automatiquement converti en E.164

---

## 🛠️ Gestion des Erreurs

### Types d'erreurs courantes

1. **Clé API manquante :**
   ```python
   ValueError: MESSAGEPRO_API_SECRET doit être défini
   ```
   **Solution :** Ajouter `MESSAGEPRO_API_SECRET` dans `.env`

2. **Crédits insuffisants (mode credits) :**
   ```json
   {
     "status": 400,
     "message": "Insufficient credits"
   }
   ```
   **Solution :** Recharger des crédits ou utiliser le mode "devices"

3. **Appareil non disponible (mode devices) :**
   ```json
   {
     "status": 400,
     "message": "Device not found or offline"
   }
   ```
   **Solution :** Vérifier que l'appareil est en ligne et lié

4. **Numéro invalide :**
   ```json
   {
     "status": 400,
     "message": "Invalid phone number"
   }
   ```
   **Solution :** Vérifier le format du numéro (E.164 recommandé)

---

## 🔍 Exemples d'Utilisation

### Exemple 1 : Notification de Commande

```python
from messagepro_api import MessageProAPI

api = MessageProAPI()

# Envoyer une notification SMS quand une commande est validée
def notify_order_ready(order_id, client_phone):
    message = f"Votre commande #{order_id} est prête pour récupération!"
    result = api.send_sms(
        phone=client_phone,
        message=message,
        mode="devices",
        device="main-device-id",
        sim=1
    )
    return result.get('status') == 200
```

### Exemple 2 : Campagne Promotionnelle

```python
# Envoyer une promotion à tous les clients VIP
api.send_bulk_sms(
    campaign="Promotion VIP - Janvier 2026",
    message="🎉 Offre spéciale : 20% de réduction sur tous les produits!",
    groups="1",  # Groupe "Clients VIP"
    mode="credits",
    gateway="gateway-id"
)
```

### Exemple 3 : Vérification OTP

```python
# Envoyer un code OTP pour vérifier un numéro
result = api.send_otp(
    phone="+224601123456",
    message="Votre code de vérification est {{otp}}. Valide 5 minutes.",
    message_type="sms",
    mode="devices",
    device="device-id",
    expire=300
)

otp_code = result.get('data', {}).get('otp')
# Stocker otp_code pour vérification ultérieure

# Plus tard, vérifier le code saisi par l'utilisateur
verification = api.verify_otp(otp="123456")
if verification.get('status') == 200:
    print("Code valide!")
```

---

## 📈 Bonnes Pratiques

### 1. Gestion des Erreurs

Toujours vérifier le statut de la réponse :

```python
result = api.send_sms(...)
if result.get('status') == 200:
    # Succès
    message_id = result.get('data', {}).get('messageId')
else:
    # Erreur
    error_message = result.get('message', 'Erreur inconnue')
    # Logger l'erreur
```

### 2. Rate Limiting

Message Pro peut avoir des limites de débit. Pour les campagnes massives :
- Utilisez les campagnes plutôt que des envois individuels
- Espacez les envois si nécessaire
- Surveillez les messages en attente

### 3. Format des Messages

- **SMS** : Maximum 160 caractères pour un SMS standard (GSM 7-bit)
- **WhatsApp** : Pas de limite stricte, mais gardez les messages concis
- **OTP** : Incluez toujours `{{otp}}` dans le message

### 4. Sécurité

- Ne jamais exposer `MESSAGEPRO_API_SECRET` dans le code
- Utiliser des variables d'environnement
- Vérifier les permissions avant chaque action
- Logger les envois pour audit

---

## 🔗 Intégration avec l'Application

### Lien avec les Commandes

Vous pouvez notifier automatiquement les clients lors de changements de statut de commande :

```python
# Dans orders.py, après validation d'une commande
from messagepro_api import MessageProAPI

if order.status == 'validated':
    api = MessageProAPI()
    api.send_sms(
        phone=order.client.phone,
        message=f"Votre commande #{order.reference} a été validée!",
        mode="devices",
        device="device-id"
    )
```

### Lien avec les Stocks

Notifier les commerciaux quand un article est en rupture :

```python
# Dans stocks.py
if stock.current_stock <= stock.min_stock:
    api = MessageProAPI()
    # Envoyer à tous les commerciaux
    api.send_bulk_sms(
        campaign="Alerte Stock",
        message=f"⚠️ {stock.name} est en rupture de stock!",
        groups="commerciaux-group-id"
    )
```

---

## 📚 Ressources

- **Documentation API** : Fournie dans la demande initiale
- **Dashboard Message Pro** : [https://messagepro-gn.com](https://messagepro-gn.com)
- **Support** : Contactez le support via le dashboard

---

## ✅ Checklist de Déploiement

- [ ] Clé API obtenue depuis Message Pro
- [ ] `MESSAGEPRO_API_SECRET` configuré dans `.env`
- [ ] Permissions messaging ajoutées au rôle superviseur
- [ ] Appareils Android liés (si mode "devices")
- [ ] Crédits suffisants (si mode "credits")
- [ ] Test d'envoi réussi
- [ ] Contacts et groupes créés
- [ ] Intégration avec les commandes (optionnel)

---

**💡 Astuce** : Commencez par tester avec un SMS unique avant de lancer des campagnes massives !

