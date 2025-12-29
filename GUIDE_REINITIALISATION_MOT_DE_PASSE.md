# 🔐 Guide de Réinitialisation de Mot de Passe Sécurisée

## 📋 Vue d'ensemble

Ce guide explique comment configurer et utiliser le système de réinitialisation de mot de passe sécurisé implémenté dans l'application Import Profit Pro.

---

## ✅ Fonctionnalités Implémentées

### 🔒 Sécurité

1. **Tokens cryptographiquement sécurisés**
   - Génération avec `secrets.token_urlsafe(32)` (256 bits)
   - Hashage avec `werkzeug.security` (comme les mots de passe)
   - Stockage uniquement du hash en base de données

2. **Expiration automatique**
   - Tokens valides pendant **30 minutes** uniquement
   - Nettoyage automatique des tokens expirés

3. **Utilisation unique**
   - Chaque token ne peut être utilisé qu'**une seule fois**
   - Invalidation automatique après utilisation
   - Invalidation des tokens précédents lors d'une nouvelle demande

4. **Rate Limiting**
   - Protection contre les attaques par force brute
   - Limite: **3 demandes par heure** par adresse IP

5. **Validation stricte**
   - Format email validé
   - Mot de passe fort requis (8+ caractères, majuscule, minuscule, chiffre, caractère spécial)
   - Vérification de correspondance des mots de passe

6. **Protection de la vie privée**
   - Message générique (ne révèle pas si l'email existe)
   - Protection contre l'énumération d'emails

---

## 🚀 Configuration

### 1. Installation des dépendances

```bash
pip install Flask-Mail>=0.9.1
```

Ou installez toutes les dépendances :

```bash
pip install -r requirements.txt
```

### 2. Configuration Email

Ajoutez les variables d'environnement suivantes dans votre fichier `.env` :

```env
# Configuration Email (Flask-Mail)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=1
MAIL_USE_SSL=0
MAIL_USERNAME=votre_email@gmail.com
MAIL_PASSWORD=votre_mot_de_passe_application
MAIL_DEFAULT_SENDER=votre_email@gmail.com

# Pour les tests (désactive l'envoi réel d'emails)
# MAIL_SUPPRESS_SEND=1
```

#### Configuration pour Gmail

1. Activez l'authentification à deux facteurs sur votre compte Gmail
2. Générez un "Mot de passe d'application" :
   - Allez dans : Paramètres Google → Sécurité → Validation en 2 étapes → Mots de passe des applications
   - Créez un nouveau mot de passe d'application
   - Utilisez ce mot de passe dans `MAIL_PASSWORD`

#### Configuration pour autres serveurs SMTP

**Outlook/Office 365:**
```env
MAIL_SERVER=smtp.office365.com
MAIL_PORT=587
MAIL_USE_TLS=1
```

**SendGrid:**
```env
MAIL_SERVER=smtp.sendgrid.net
MAIL_PORT=587
MAIL_USERNAME=apikey
MAIL_PASSWORD=votre_api_key_sendgrid
```

**Mailgun:**
```env
MAIL_SERVER=smtp.mailgun.org
MAIL_PORT=587
MAIL_USERNAME=votre_domaine_mailgun
MAIL_PASSWORD=votre_api_key_mailgun
```

### 3. Migration de la base de données

Exécutez le script SQL pour créer la table `password_reset_tokens` :

```bash
mysql -u root -p madargn < migrations/create_password_reset_tokens_table.sql
```

Ou via MySQL directement :

```sql
SOURCE migrations/create_password_reset_tokens_table.sql;
```

---

## 📧 Utilisation

### Pour les utilisateurs

1. **Demander une réinitialisation**
   - Aller sur `/auth/forgot-password`
   - Entrer l'adresse email associée au compte
   - Cliquer sur "Envoyer le lien de réinitialisation"

2. **Réinitialiser le mot de passe**
   - Vérifier la boîte email (et les spams)
   - Cliquer sur le lien dans l'email reçu
   - Entrer un nouveau mot de passe conforme aux exigences
   - Confirmer le nouveau mot de passe
   - Cliquer sur "Réinitialiser le mot de passe"

3. **Se connecter**
   - Utiliser le nouveau mot de passe pour se connecter

### Exigences du mot de passe

Le nouveau mot de passe doit contenir :
- ✅ Au moins **8 caractères**
- ✅ Au moins **une majuscule** (A-Z)
- ✅ Au moins **une minuscule** (a-z)
- ✅ Au moins **un chiffre** (0-9)
- ✅ Au moins **un caractère spécial** (!@#$%^&*...)

---

## 🔧 Maintenance

### Nettoyage automatique des tokens expirés

Les tokens expirés peuvent être nettoyés automatiquement en appelant la fonction `cleanup_expired_tokens()` :

```python
from email_utils import cleanup_expired_tokens

# Nettoyer les tokens expirés
expired_count = cleanup_expired_tokens()
print(f"{expired_count} tokens expirés supprimés")
```

**Recommandation :** Ajouter cette fonction à une tâche cron ou un scheduler pour un nettoyage périodique.

### Exemple avec APScheduler

```python
from apscheduler.schedulers.background import BackgroundScheduler
from email_utils import cleanup_expired_tokens

scheduler = BackgroundScheduler()
scheduler.add_job(
    func=cleanup_expired_tokens,
    trigger="interval",
    hours=1,  # Nettoyer toutes les heures
    id='cleanup_expired_tokens',
    name='Nettoyer les tokens expirés'
)
scheduler.start()
```

---

## 🛡️ Sécurité - Bonnes Pratiques

### ✅ Implémenté

- [x] Tokens hashés (pas de stockage en clair)
- [x] Expiration courte (30 minutes)
- [x] Utilisation unique
- [x] Rate limiting
- [x] Validation stricte des mots de passe
- [x] Protection contre l'énumération d'emails
- [x] HTTPS recommandé (via `PREFERRED_URL_SCHEME=https`)

### ⚠️ Recommandations supplémentaires

1. **HTTPS en production**
   - Configurez `PREFERRED_URL_SCHEME=https` dans `.env`
   - Utilisez un certificat SSL valide

2. **Monitoring**
   - Surveillez les tentatives de réinitialisation
   - Alertez en cas de taux anormalement élevé

3. **Logs**
   - Les erreurs d'envoi d'email sont loggées
   - Surveillez les logs pour détecter les problèmes

4. **Tests réguliers**
   - Testez le flux de réinitialisation périodiquement
   - Vérifiez que les emails sont bien reçus

---

## 🧪 Tests

### Test manuel

1. **Test de demande de réinitialisation**
   ```
   POST /auth/forgot-password
   email: test@example.com
   ```

2. **Vérifier l'email reçu**
   - Le lien doit pointer vers `/auth/reset-password?token=...`
   - Le token doit être long et aléatoire

3. **Test de réinitialisation**
   ```
   GET /auth/reset-password?token=<token_reçu>
   POST /auth/reset-password
   token: <token>
   new_password: NouveauMotDePasse123!
   confirm_password: NouveauMotDePasse123!
   ```

4. **Vérifier que le token est invalidé**
   - Essayer de réutiliser le même token doit échouer

### Test avec MAIL_SUPPRESS_SEND

Pour tester sans envoyer d'emails réels :

```env
MAIL_SUPPRESS_SEND=1
```

Les emails seront "envoyés" mais ne partiront pas réellement. Utile pour les tests en développement.

---

## 📝 Structure des fichiers

```
├── auth.py                          # Routes d'authentification
├── email_utils.py                   # Gestion des emails et tokens
├── models.py                        # Modèle PasswordResetToken
├── config.py                        # Configuration email
├── templates/
│   └── auth/
│       ├── forgot_password.html     # Page de demande
│       └── reset_password.html     # Page de réinitialisation
└── migrations/
    └── create_password_reset_tokens_table.sql
```

---

## 🐛 Dépannage

### Les emails ne sont pas envoyés

1. **Vérifier la configuration**
   - `MAIL_USERNAME` et `MAIL_PASSWORD` sont-ils définis ?
   - Les identifiants sont-ils corrects ?

2. **Vérifier les logs**
   - Regarder les logs de l'application pour les erreurs
   - Vérifier les logs du serveur SMTP

3. **Tester la connexion SMTP**
   ```python
   from flask import current_app
   from flask_mail import Message
   from email_utils import mail
   
   msg = Message('Test', recipients=['test@example.com'])
   mail.send(msg)
   ```

### Le token est invalide

1. **Vérifier l'expiration**
   - Les tokens expirent après 30 minutes
   - Demander un nouveau lien si nécessaire

2. **Vérifier l'utilisation**
   - Chaque token ne peut être utilisé qu'une fois
   - Demander un nouveau lien si déjà utilisé

3. **Vérifier la base de données**
   ```sql
   SELECT * FROM password_reset_tokens 
   WHERE token_hash LIKE '%...%' 
   AND used = 0 
   AND expires_at > NOW();
   ```

### Rate limiting trop strict

Si vous trouvez que 3 demandes/heure est trop restrictif, vous pouvez ajuster dans `auth.py` :

```python
# Dans _forgot_password_handler, ajouter :
@limiter.limit("5 per hour")  # Augmenter à 5 par heure
```

---

## 📚 Références

- [Flask-Mail Documentation](https://pythonhosted.org/Flask-Mail/)
- [Werkzeug Security](https://werkzeug.palletsprojects.com/en/2.3.x/utils/#werkzeug.security)
- [Python secrets module](https://docs.python.org/3/library/secrets.html)

---

## ✅ Checklist de déploiement

Avant de déployer en production :

- [ ] Configuration email testée et fonctionnelle
- [ ] Migration SQL exécutée
- [ ] HTTPS configuré (`PREFERRED_URL_SCHEME=https`)
- [ ] Rate limiting testé
- [ ] Nettoyage automatique des tokens configuré (cron/scheduler)
- [ ] Tests de bout en bout effectués
- [ ] Monitoring configuré
- [ ] Documentation à jour

---

**Date de création :** 2024  
**Version :** 1.0  
**Auteur :** Système de réinitialisation de mot de passe sécurisé

