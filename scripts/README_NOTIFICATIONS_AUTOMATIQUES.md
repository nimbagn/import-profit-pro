# 📱 Système de Notifications Automatiques via Message Pro

## 📋 Vue d'ensemble

Le système de notifications automatiques permet d'envoyer des notifications WhatsApp et SMS via Message Pro pour les événements importants de l'application.

## 🎯 Fonctionnalités

### 1. Notifications de Commandes

#### Création de Commande
- **Déclencheur** : Lorsqu'un commercial crée une nouvelle commande
- **Destinataire** : Superviseur de la région ou superviseur général
- **Contenu** : Référence, commercial, date, montant total
- **Intégration** : `orders.py` → `order_new()`

#### Validation de Commande
- **Déclencheur** : Lorsqu'un superviseur valide une commande
- **Destinataire** : Commercial qui a créé la commande
- **Contenu** : Référence, validateur, date de validation
- **Intégration** : `orders.py` → `order_validate()`

### 2. Rappels Véhicules

#### Rappels de Documents Expirant
- **Déclencheur** : Automatique quotidien à 8h00 + manuel depuis le dashboard
- **Destinataires** : Conducteur du véhicule + Magasinier/Superviseur/Admin
- **Contenu** : Véhicule, liste des documents expirant dans les 15 prochains jours
- **Planification** : `scheduled_reports.py` → `schedule_vehicle_reminders()`
- **Intégration** : `flotte.py` → `dashboard()` (envoi automatique)

### 3. Rapports Stock

#### Inventaire de Stock
- **Déclencheur** : Manuel via route `/notifications/inventaire-stock`
- **Destinataires** : Superviseurs, Magasiniers, Admins
- **Contenu** : PDF d'inventaire complet avec tous les articles
- **Route** : `routes_notifications.py` → `envoyer_inventaire_stock()`

#### Situation de Stock par Période
- **Déclencheur** : Manuel depuis la page de récapitulatif stock
- **Destinataires** : Superviseurs, Magasiniers, Admins
- **Contenu** : PDF de situation de stock pour la période sélectionnée
- **Route** : `routes_notifications.py` → `envoyer_situation_stock()`
- **Intégration** : Template `stock_summary.html` avec bouton WhatsApp

## 📁 Fichiers Créés/Modifiés

### Nouveaux Fichiers
- `notifications_automatiques.py` : Module principal de notifications
- `flotte_notifications.py` : Module spécifique pour les rappels véhicules
- `routes_notifications.py` : Routes Flask pour déclencher manuellement les notifications

### Fichiers Modifiés
- `orders.py` : Ajout des notifications lors de la création et validation
- `flotte.py` : Envoi automatique des rappels lors de l'accès au dashboard
- `stocks.py` : Option d'envoi de notification lors de la génération PDF
- `scheduled_reports.py` : Planification des rappels véhicules quotidiens
- `app.py` : Enregistrement du blueprint `notifications_bp`
- `templates/stocks/stock_summary.html` : Bouton d'envoi WhatsApp
- `templates/flotte/dashboard.html` : Bouton d'envoi des rappels

## 🔧 Configuration

### Prérequis
1. **Message Pro API** : Clé API configurée dans `ApiConfig` ou variable d'environnement `MESSAGEPRO_API_SECRET`
2. **Compte WhatsApp** : Au moins un compte WhatsApp configuré dans Message Pro
3. **Numéros de téléphone** : Les utilisateurs doivent avoir un numéro de téléphone dans leur profil

### Format des Numéros
Les numéros sont automatiquement formatés avec l'indicatif guinéen (224) :
- `0XXXXXXXX` → `224XXXXXXXX`
- `XXXXXXXX` → `224XXXXXXXX`
- `224XXXXXXXX` → Conservé tel quel

## 📊 Planification Automatique

### Rappels Véhicules
- **Fréquence** : Quotidien
- **Heure** : 8h00
- **Délai** : Documents expirant dans les 15 prochains jours
- **Configuration** : `scheduled_reports.py` → `schedule_vehicle_reminders()`

## 🚀 Utilisation

### Notifications Automatiques
Les notifications sont envoyées automatiquement lors des événements suivants :
- Création de commande → Notification au superviseur
- Validation de commande → Notification au commercial
- Accès au dashboard flotte → Rappels véhicules si documents expirant

### Notifications Manuelles

#### Envoyer Inventaire de Stock
```bash
POST /notifications/inventaire-stock
Form data:
  - depot_id (optionnel)
```

#### Envoyer Situation de Stock
```bash
POST /notifications/situation-stock
Form data:
  - depot_id (optionnel)
  - period (week/month/quarter/year)
```

#### Envoyer Rappels Véhicules
```bash
POST /notifications/rappels-vehicules
```

## 📝 Messages Exemples

### Création de Commande
```
🔔 NOUVELLE COMMANDE CRÉÉE

Référence: CMD-20260103-0001
Commercial: Amadou Diallo
Date: 03/01/2026 14:30
Montant: 1 275 000 GNF

Veuillez valider la commande dans l'application.
```

### Validation de Commande
```
✅ COMMANDE VALIDÉE

Référence: CMD-20260103-0001
Validée par: Superviseur Régional
Date: 03/01/2026 15:00

Votre commande a été validée et peut être traitée.
```

### Rappel Véhicule
```
🚗 RAPPEL - DOCUMENTS VÉHICULE

Véhicule: ABC-123
Documents expirant bientôt:
- Assurance: Expire le 15/01/2026
- Carte grise: Expire le 18/01/2026

Veuillez renouveler ces documents avant expiration.
```

## ⚠️ Gestion des Erreurs

Le système gère gracieusement les erreurs :
- Si Message Pro API n'est pas disponible → Log d'avertissement, pas d'erreur
- Si aucun destinataire trouvé → Log d'avertissement
- Si PDF ne peut pas être généré → Log d'erreur, notification échoue
- Les erreurs n'interrompent pas le flux principal de l'application

## 🔍 Logs

Tous les événements sont loggés :
- Succès : `logger.info()`
- Avertissements : `logger.warning()`
- Erreurs : `logger.error()` avec traceback

## 📈 Améliorations Futures

- [ ] Notifications SMS en complément de WhatsApp
- [ ] Templates de messages personnalisables
- [ ] Historique des notifications envoyées
- [ ] Statistiques d'envoi
- [ ] Notifications groupées pour réduire les coûts
- [ ] Support des notifications push pour l'application mobile

