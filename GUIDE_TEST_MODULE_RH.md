# 🧪 GUIDE DE TEST - MODULE RESSOURCES HUMAINES

**Date :** 2025-01-XX  
**Version :** 1.0

---

## 📋 PRÉREQUIS

### 1. Exécuter la Migration SQL

**Option A : Script Python (Recommandé)**
```bash
python3 execute_migration_rh.py
```

**Option B : Commande MySQL directe**
```bash
mysql -h 127.0.0.1 -P 3306 -u root -p madargn < migration_rh_complete.sql
```

**Option C : Depuis MySQL**
```sql
source /Users/dantawi/Documents/mini_flask_import_profitability/migration_rh_complete.sql;
```

### 2. Vérifier les Tables Créées

```sql
SHOW TABLES LIKE '%employee%';
SHOW TABLES LIKE '%activity%';
```

Vous devriez voir :
- `user_activity_logs`
- `employees`
- `employee_contracts`
- `employee_trainings`
- `employee_evaluations`
- `employee_absences`

---

## 👤 CRÉER UN UTILISATEUR RH

### 1. Se connecter en tant qu'admin

1. Aller sur `/auth/login`
2. Se connecter avec un compte admin

### 2. Créer un utilisateur RH

**Option A : Via l'interface**
1. Aller dans **Ressources Humaines > Personnel Plateforme**
2. Cliquer sur **Nouveau Personnel**
3. Remplir le formulaire :
   - Username : `rh_manager`
   - Email : `rh@example.com`
   - Rôle : **RH Manager**
   - Mot de passe : (choisir un mot de passe)
4. Enregistrer

**Option B : Via SQL (pour test rapide)**
```sql
-- Créer le rôle si nécessaire
INSERT INTO roles (code, name, description) 
VALUES ('rh_manager', 'RH Manager', 'Gestionnaire RH avec accès complet')
ON DUPLICATE KEY UPDATE name=VALUES(name);

-- Créer l'utilisateur
INSERT INTO users (username, email, password_hash, role_id, is_active, created_at)
SELECT 
    'rh_manager',
    'rh@example.com',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYqJqZqZqZq', -- password: test123
    r.id,
    1,
    NOW()
FROM roles r WHERE r.code = 'rh_manager';
```

---

## ✅ CHECKLIST DE TEST

### 🧑‍💼 Gestion du Personnel Plateforme

- [ ] **Liste du personnel**
  - Accéder à `/rh/personnel`
  - Vérifier l'affichage de la liste
  - Tester les filtres (rôle, région, statut)
  - Tester la recherche

- [ ] **Créer un nouveau membre**
  - Cliquer sur "Nouveau Personnel"
  - Remplir le formulaire
  - Vérifier la création
  - Vérifier le message de succès

- [ ] **Voir les détails**
  - Cliquer sur un membre
  - Vérifier les informations affichées
  - Vérifier les statistiques d'activité

- [ ] **Modifier un membre**
  - Cliquer sur "Modifier"
  - Modifier les informations
  - Vérifier la sauvegarde

### 👥 Gestion des Employés Externes

- [ ] **Liste des employés**
  - Accéder à `/rh/employees`
  - Vérifier l'affichage
  - Tester les filtres

- [ ] **Créer un employé**
  - Cliquer sur "Nouvel Employé"
  - Remplir le formulaire complet
  - Vérifier la création

- [ ] **Voir les détails d'un employé**
  - Cliquer sur un employé
  - Vérifier les informations
  - Vérifier les actions rapides (Contrats, Formations, etc.)

### 📄 Gestion des Contrats

- [ ] **Créer un contrat**
  - Depuis la page d'un employé, cliquer sur "Contrats"
  - Cliquer sur "Nouveau Contrat"
  - Remplir le formulaire (CDI, CDD, etc.)
  - Vérifier la création

- [ ] **Voir les détails d'un contrat**
  - Cliquer sur un contrat
  - Vérifier les informations

- [ ] **Modifier un contrat**
  - Modifier les dates, salaire, statut
  - Vérifier la sauvegarde

### 🎓 Gestion des Formations

- [ ] **Créer une formation**
  - Depuis la page d'un employé, cliquer sur "Formations"
  - Cliquer sur "Nouvelle Formation"
  - Remplir le formulaire
  - Vérifier la création

- [ ] **Modifier une formation**
  - Changer le statut (planifiée → en cours → terminée)
  - Cocher "Certificat obtenu"
  - Vérifier la sauvegarde

### ⭐ Gestion des Évaluations

- [ ] **Créer une évaluation**
  - Depuis la page d'un employé, cliquer sur "Évaluations"
  - Cliquer sur "Nouvelle Évaluation"
  - Remplir le formulaire (type, date, note, score)
  - Ajouter des commentaires
  - Vérifier la création

- [ ] **Modifier une évaluation**
  - Modifier la note et le score
  - Ajouter des objectifs
  - Vérifier la sauvegarde

### 📅 Gestion des Absences

- [ ] **Créer une absence**
  - Depuis la page d'un employé, cliquer sur "Absences"
  - Cliquer sur "Nouvelle Absence"
  - Remplir le formulaire (type, dates, raison)
  - Vérifier la création et le calcul automatique des jours

- [ ] **Approuver une absence**
  - Cliquer sur le bouton "Approuver" (✓)
  - Vérifier le changement de statut
  - Vérifier l'enregistrement de l'approbateur

- [ ] **Rejeter une absence**
  - Cliquer sur le bouton "Rejeter" (✗)
  - Vérifier le changement de statut

### 📊 Suivi et Statistiques

- [ ] **Voir les activités**
  - Accéder à `/rh/activites`
  - Vérifier la liste des activités
  - Tester les filtres (utilisateur, action, date)

- [ ] **Voir les statistiques**
  - Accéder à `/rh/statistiques`
  - Vérifier les graphiques
  - Vérifier les statistiques affichées

---

## 🔐 TEST DES PERMISSIONS

### Tester avec différents rôles RH

1. **RH Manager** (accès complet)
   - Doit pouvoir tout faire

2. **RH Assistant** (saisie et modification)
   - Peut créer et modifier
   - Ne peut pas supprimer

3. **RH Recruiter** (recrutement)
   - Peut créer des employés et contrats
   - Accès limité aux autres modules

4. **RH Analyst** (consultation seule)
   - Peut seulement voir
   - Ne peut pas créer/modifier

5. **Utilisateur non-RH**
   - Ne doit pas accéder aux pages RH
   - Doit voir un message "Accès refusé"

---

## 🐛 TESTS DE VALIDATION

### Formulaires

- [ ] **Champs obligatoires**
  - Essayer de soumettre un formulaire vide
  - Vérifier les messages d'erreur

- [ ] **Validation des données**
  - Dates invalides (fin < début)
  - Emails invalides
  - Numéros de contrat dupliqués
  - Numéros d'employé dupliqués

- [ ] **Messages flash**
  - Vérifier l'affichage des messages de succès
  - Vérifier l'affichage des messages d'erreur

---

## 📝 SCÉNARIOS DE TEST COMPLETS

### Scénario 1 : Recrutement complet

1. Créer un nouvel employé externe
2. Créer un contrat CDI pour cet employé
3. Ajouter une formation d'intégration
4. Créer une évaluation de période d'essai
5. Vérifier que tout est lié à l'employé

### Scénario 2 : Gestion des absences

1. Créer plusieurs absences pour un employé
2. Approuver certaines absences
3. Rejeter une absence
4. Vérifier les statistiques d'absences

### Scénario 3 : Suivi d'activité

1. Se connecter avec différents utilisateurs
2. Effectuer diverses actions
3. Vérifier que toutes les actions sont enregistrées
4. Consulter le journal des activités

---

## ✅ VALIDATION FINALE

Une fois tous les tests passés :

- [ ] Toutes les fonctionnalités de base fonctionnent
- [ ] Les permissions sont correctement appliquées
- [ ] Les messages flash s'affichent correctement
- [ ] Les validations de formulaire fonctionnent
- [ ] Les liens de navigation fonctionnent
- [ ] Les données sont correctement sauvegardées
- [ ] Les relations entre modèles fonctionnent

---

## 🆘 EN CAS DE PROBLÈME

### Erreur "Table doesn't exist"
- Vérifier que la migration SQL a été exécutée
- Vérifier les noms de tables dans la base de données

### Erreur "Access denied"
- Vérifier que l'utilisateur a un rôle RH
- Vérifier les permissions dans `app.py`

### Erreur "Module not found"
- Vérifier que `rh.py` est bien enregistré dans `app.py`
- Redémarrer l'application Flask

### Les templates ne s'affichent pas
- Vérifier que les templates sont dans `templates/rh/`
- Vérifier les noms de fichiers

---

## 📞 SUPPORT

Pour toute question ou problème :
1. Vérifier les logs de l'application
2. Vérifier les logs MySQL
3. Consulter `RESUME_MODULE_RH_COMPLET.md` pour la documentation complète

---

**Bon test ! 🚀**

