# 📊 GUIDE DES RAPPORTS AUTOMATIQUES

## 🎯 Vue d'ensemble

Le système de rapports automatiques permet d'envoyer automatiquement des rapports PDF (inventaires de stock, récapitulatifs, etc.) via WhatsApp à des heures programmées.

## ✨ Fonctionnalités

### Types de Rapports Disponibles
- **Inventaire de Stock** : Rapport détaillé des stocks par dépôt avec quantités restantes
- **Récapitulatif Stock** : Vue d'ensemble des mouvements de stock

### Fréquences de Planification
- **Quotidien** : Format `HH:MM` (ex: `18:00` pour chaque jour à 18h00)
- **Hebdomadaire** : Format `DAY HH:MM` (ex: `MON 18:00` pour chaque lundi à 18h00)
- **Mensuel** : Format `DD HH:MM` (ex: `01 18:00` pour le 1er de chaque mois à 18h00)

### Destinataires
- **Numéros individuels** : Liste de numéros séparés par des virgules
- **Groupes WhatsApp** : IDs de groupes Message Pro séparés par des virgules

## 🚀 Utilisation

### 1. Accéder aux Rapports Automatiques

1. Connectez-vous à l'application
2. Dans le menu latéral, cliquez sur **Messagerie** → **Rapports Automatiques**
3. Ou accédez directement à `/automated-reports/`

### 2. Créer un Nouveau Rapport

1. Cliquez sur **"Nouveau Rapport"**
2. Remplissez le formulaire :
   - **Nom** : Nom descriptif du rapport
   - **Type** : Choisissez le type de rapport (Inventaire de Stock, etc.)
   - **Dépôt** : Sélectionnez un dépôt spécifique ou laissez "Tous les dépôts"
   - **Période** : Choisissez la période (Aujourd'hui, Cette semaine, Ce mois, etc.)
   - **Fréquence** : Quotidien, Hebdomadaire ou Mensuel
   - **Planning** : Heure d'envoi selon le format approprié
   - **Compte WhatsApp** : Sélectionnez le compte Message Pro à utiliser
   - **Destinataires** : Numéros ou groupes WhatsApp
   - **Message** : Message personnalisé (optionnel)

3. Cliquez sur **"Créer le Rapport"**

### 3. Gérer les Rapports

- **Tester** : Envoyer un test immédiat du rapport
- **Modifier** : Modifier la configuration
- **Activer/Désactiver** : Activer ou désactiver temporairement
- **Supprimer** : Supprimer définitivement

## 📋 Exemples d'Utilisation

### Exemple 1 : Inventaire Quotidien par Dépôt

**Configuration :**
- Nom : "Inventaire Quotidien - Dépôt Principal"
- Type : Inventaire de Stock
- Dépôt : Dépôt Principal
- Période : Aujourd'hui
- Fréquence : Quotidien
- Planning : `18:00`
- Destinataires : `+224601123456, +224601123457`
- Message : "Rapport d'inventaire quotidien du dépôt principal"

**Résultat :** Chaque jour à 18h00, un PDF d'inventaire sera envoyé aux numéros spécifiés.

### Exemple 2 : Récapitulatif Hebdomadaire

**Configuration :**
- Nom : "Récap Stock Hebdomadaire"
- Type : Récapitulatif Stock
- Dépôt : Tous les dépôts
- Période : Cette semaine
- Fréquence : Hebdomadaire
- Planning : `MON 08:00`
- Groupes : `1, 2` (IDs de groupes)
- Message : "Récapitulatif hebdomadaire des stocks"

**Résultat :** Chaque lundi à 8h00, un PDF sera envoyé à tous les membres des groupes 1 et 2.

## 🔧 Configuration Technique

### Installation

1. **Installer APScheduler** :
```bash
pip install APScheduler>=3.10.4
```

2. **Créer la table dans la base de données** :

**Pour MySQL :**
```bash
mysql -u user -p database < scripts/create_scheduled_reports_table.sql
```

**Pour PostgreSQL :**
```bash
psql -U user -d database -f scripts/create_scheduled_reports_table_postgresql.sql
```

3. **Redémarrer l'application** pour charger les rapports actifs

### Variables d'Environnement

Assurez-vous que `MESSAGEPRO_API_SECRET` est configuré dans votre `.env` :
```
MESSAGEPRO_API_SECRET=votre_cle_api_secrete
```

## 📊 Structure de la Base de Données

### Table `scheduled_reports`

| Colonne | Type | Description |
|---------|------|-------------|
| `id` | BIGINT | ID unique |
| `name` | VARCHAR(200) | Nom du rapport |
| `report_type` | ENUM | Type de rapport |
| `schedule_type` | ENUM | Fréquence (daily, weekly, monthly) |
| `schedule` | VARCHAR(50) | Planning (format selon fréquence) |
| `is_active` | BOOLEAN | Actif/Inactif |
| `depot_id` | BIGINT | ID du dépôt (optionnel) |
| `period` | VARCHAR(50) | Période (all, today, week, etc.) |
| `currency` | VARCHAR(10) | Devise (GNF, USD, EUR, XOF) |
| `whatsapp_account_id` | VARCHAR(100) | ID compte WhatsApp |
| `recipients` | TEXT | Numéros séparés par virgules |
| `group_ids` | TEXT | IDs groupes séparés par virgules |
| `message` | TEXT | Message personnalisé |
| `last_run` | DATETIME | Dernière exécution |
| `next_run` | DATETIME | Prochaine exécution |
| `run_count` | INT | Nombre d'exécutions |
| `last_error` | TEXT | Dernière erreur |

## 🔍 Dépannage

### Le rapport ne s'envoie pas

1. Vérifiez que le rapport est **actif** (badge vert)
2. Vérifiez les **logs** de l'application pour les erreurs
3. Testez manuellement avec le bouton **"Tester"**
4. Vérifiez que `MESSAGEPRO_API_SECRET` est correctement configuré
5. Vérifiez que le compte WhatsApp est valide

### Erreur "Impossible de générer le PDF"

1. Vérifiez les permissions de l'utilisateur (`stocks.read`)
2. Vérifiez que les données existent pour la période sélectionnée
3. Consultez les logs pour plus de détails

### Le scheduler ne démarre pas

1. Vérifiez que APScheduler est installé : `pip list | grep APScheduler`
2. Redémarrez l'application
3. Vérifiez les logs au démarrage pour voir si les rapports sont chargés

## 📝 Notes Importantes

- Les rapports sont exécutés en arrière-plan via APScheduler
- Les PDFs sont générés à la volée à chaque exécution
- Les erreurs sont enregistrées dans `last_error` pour chaque rapport
- Le système calcule automatiquement la prochaine exécution après chaque envoi
- Les rapports inactifs ne sont pas exécutés mais restent dans la base de données

## 🎯 Prochaines Améliorations Possibles

- Ajout de rapports pour les commandes
- Support de rapports Excel
- Historique des envois
- Notifications en cas d'erreur
- Templates de messages personnalisables

