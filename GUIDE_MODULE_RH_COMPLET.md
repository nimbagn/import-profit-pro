# 📋 GUIDE COMPLET DU MODULE RESSOURCES HUMAINES

**Date :** 2025-01-XX  
**Statut :** ✅ **IMPLÉMENTÉ**

---

## 🎯 VUE D'ENSEMBLE

Le module RH permet de gérer deux types de personnel :
1. **Utilisateurs de la plateforme** : Personnel ayant un compte et accès à l'application
2. **Employés externes** : Personnel sans accès à la plateforme mais suivi par le service RH

---

## 👥 RÔLES RH HIÉRARCHIQUES

### 1. **RH Manager** (`rh_manager`)
**Description :** Gestion complète du personnel, contrats, formations, évaluations

**Permissions :**
- ✅ Gestion complète des utilisateurs (CRUD)
- ✅ Gestion complète des employés externes (CRUD)
- ✅ Gestion complète des contrats (CRUD)
- ✅ Gestion complète des formations (CRUD)
- ✅ Gestion complète des évaluations (CRUD)
- ✅ Gestion complète des absences (CRUD)
- ✅ Consultation des rôles
- ✅ Rapports et exports
- ✅ Analytics et exports

**Utilisation :** Directeur RH, Responsable RH

---

### 2. **RH Assistant** (`rh_assistant`)
**Description :** Assistance RH : saisie données, suivi formations, gestion absences

**Permissions :**
- ✅ Consultation et création/modification des utilisateurs
- ✅ Consultation et création/modification des employés externes
- ✅ Consultation et création/modification des contrats
- ✅ Consultation et création/modification des formations
- ✅ Consultation et création des évaluations
- ✅ Gestion complète des absences (CRUD)
- ✅ Consultation des rapports

**Utilisation :** Assistant RH, Secrétaire RH

---

### 3. **RH Recruiter** (`rh_recruiter`)
**Description :** Recrutement et intégration du personnel

**Permissions :**
- ✅ Consultation et création des utilisateurs
- ✅ Gestion complète des employés externes (CRUD)
- ✅ Consultation et création des contrats
- ✅ Consultation et création des formations
- ✅ Consultation des rapports

**Utilisation :** Chargé de recrutement, Responsable recrutement

---

### 4. **RH Analyst** (`rh_analyst`)
**Description :** Analyse et reporting RH, statistiques, tableaux de bord

**Permissions :**
- ✅ Consultation seule (lecture) de tous les modules RH
- ✅ Rapports et exports
- ✅ Analytics et exports

**Utilisation :** Analyste RH, Data Analyst RH

---

### 5. **Ressources Humaines** (`rh`) - Rôle de base
**Description :** Gestion du personnel et suivi des interactions utilisateurs

**Permissions :**
- ✅ Gestion des utilisateurs (read, create, update)
- ✅ Consultation des rôles
- ✅ Consultation des rapports
- ✅ Consultation des analytics

**Utilisation :** Personnel RH généraliste

---

## 👤 GESTION DES EMPLOYÉS EXTERNES

### Modèle Employee

Les employés externes sont des personnes qui n'ont **pas accès à la plateforme** mais qui sont suivies par le service RH.

#### Informations personnelles
- Numéro d'employé (unique)
- Prénom, Nom
- Email, Téléphone
- Date de naissance
- Genre
- Numéro CNI/Passeport
- Adresse complète
- Contact d'urgence

#### Informations professionnelles
- Département/Service
- Poste/Fonction
- Responsable hiérarchique (lien vers un autre employé)
- Région
- Dépôt
- Date d'embauche
- Statut d'emploi (actif, inactif, suspendu, terminé, en congé)

#### Lien avec utilisateur
- Possibilité de lier un employé à un compte utilisateur (si l'employé obtient un accès plus tard)

---

## 📄 MODULES DE GESTION RH

### 1. **Contrats** (EmployeeContract)
- Types : CDI, CDD, Stage, Consultant, Freelance
- Dates de début/fin
- Salaire et devise
- Poste et département
- Statut : brouillon, actif, expiré, terminé
- Document du contrat signé

### 2. **Formations** (EmployeeTraining)
- Nom de la formation
- Type : interne, externe, en ligne, certification
- Organisme de formation
- Dates de début/fin
- Durée en heures
- Coût
- Statut : planifiée, en cours, terminée, annulée
- Certificat obtenu

### 3. **Évaluations** (EmployeeEvaluation)
- Type : annuelle, période d'essai, mi-année, projet, personnalisée
- Date d'évaluation
- Évaluateur
- Note globale (excellent, très bien, bien, satisfaisant, à améliorer, insatisfaisant)
- Score sur 100
- Points forts
- Axes d'amélioration
- Objectifs
- Statut : brouillon, soumis, révisé, approuvé

### 4. **Absences** (EmployeeAbsence)
- Type : congés, arrêt maladie, personnel, maternité, paternité, non payé, autre
- Dates de début/fin
- Nombre de jours
- Statut : en attente, approuvé, rejeté, annulé
- Raison
- Approbateur
- Certificat médical (pour arrêts maladie)

---

## 🔐 PERMISSIONS PAR RÔLE

| Fonctionnalité | RH Manager | RH Assistant | RH Recruiter | RH Analyst | RH (base) |
|----------------|------------|--------------|--------------|------------|-----------|
| **Utilisateurs** |
| Lire | ✅ | ✅ | ✅ | ✅ | ✅ |
| Créer | ✅ | ✅ | ✅ | ❌ | ✅ |
| Modifier | ✅ | ✅ | ❌ | ❌ | ✅ |
| Supprimer | ✅ | ❌ | ❌ | ❌ | ❌ |
| **Employés Externes** |
| Lire | ✅ | ✅ | ✅ | ✅ | ❌ |
| Créer | ✅ | ✅ | ✅ | ❌ | ❌ |
| Modifier | ✅ | ✅ | ✅ | ❌ | ❌ |
| Supprimer | ✅ | ❌ | ❌ | ❌ | ❌ |
| **Contrats** |
| Lire | ✅ | ✅ | ✅ | ✅ | ❌ |
| Créer | ✅ | ✅ | ✅ | ❌ | ❌ |
| Modifier | ✅ | ✅ | ❌ | ❌ | ❌ |
| Supprimer | ✅ | ❌ | ❌ | ❌ | ❌ |
| **Formations** |
| Lire | ✅ | ✅ | ✅ | ✅ | ❌ |
| Créer | ✅ | ✅ | ✅ | ❌ | ❌ |
| Modifier | ✅ | ✅ | ❌ | ❌ | ❌ |
| Supprimer | ✅ | ❌ | ❌ | ❌ | ❌ |
| **Évaluations** |
| Lire | ✅ | ✅ | ❌ | ✅ | ❌ |
| Créer | ✅ | ✅ | ❌ | ❌ | ❌ |
| Modifier | ✅ | ❌ | ❌ | ❌ | ❌ |
| Supprimer | ✅ | ❌ | ❌ | ❌ | ❌ |
| **Absences** |
| Lire | ✅ | ✅ | ❌ | ✅ | ❌ |
| Créer | ✅ | ✅ | ❌ | ❌ | ❌ |
| Modifier | ✅ | ✅ | ❌ | ❌ | ❌ |
| Supprimer | ✅ | ❌ | ❌ | ❌ | ❌ |
| **Rapports** |
| Lire | ✅ | ✅ | ✅ | ✅ | ✅ |
| Exporter | ✅ | ❌ | ❌ | ✅ | ❌ |
| **Analytics** |
| Lire | ✅ | ❌ | ❌ | ✅ | ✅ |
| Exporter | ✅ | ❌ | ❌ | ✅ | ❌ |

---

## 🚀 UTILISATION

### Pour les RH Managers
1. Accéder à `/rh/employees` pour gérer les employés externes
2. Créer des contrats pour chaque employé
3. Suivre les formations et évaluations
4. Gérer les absences et congés
5. Générer des rapports et analyses

### Pour les RH Assistants
1. Saisir les données des nouveaux employés
2. Créer et modifier les contrats
3. Enregistrer les formations suivies
4. Gérer les demandes d'absences

### Pour les RH Recruiters
1. Créer les profils des nouveaux recrutés
2. Créer les contrats d'embauche
3. Planifier les formations d'intégration

### Pour les RH Analysts
1. Consulter toutes les données RH
2. Générer des rapports et analyses
3. Exporter les données pour analyses externes

---

## 📊 FONCTIONNALITÉS PRINCIPALES

### 1. Gestion du Personnel
- Liste complète avec filtres (département, poste, statut, région)
- Recherche par nom, numéro, email, téléphone
- Statistiques globales (total, actifs, par département)

### 2. Suivi des Contrats
- Historique complet des contrats
- Contrat actuel automatiquement identifié
- Alertes pour contrats expirant

### 3. Suivi des Formations
- Historique des formations
- Formations en cours
- Certificats obtenus

### 4. Évaluations de Performance
- Historique des évaluations
- Scores et notes
- Objectifs et axes d'amélioration

### 5. Gestion des Absences
- Demandes d'absences
- Approbation/rejet
- Calendrier des absences

---

## 🔄 MIGRATION

Pour activer le module complet, exécuter :

```sql
-- Voir migration_add_rh_employees.sql
```

---

## 📝 NOTES IMPORTANTES

1. **Séparation Utilisateurs/Employés** : Les utilisateurs ont accès à la plateforme, les employés externes non
2. **Lien possible** : Un employé peut être lié à un utilisateur si besoin
3. **Hiérarchie** : Les employés peuvent avoir un responsable hiérarchique (autre employé)
4. **Traçabilité** : Toutes les actions sont enregistrées dans les logs d'activité

---

## 🎯 PROCHAINES ÉTAPES

- [ ] Créer les templates pour la gestion des contrats
- [ ] Créer les templates pour la gestion des formations
- [ ] Créer les templates pour la gestion des évaluations
- [ ] Créer les templates pour la gestion des absences
- [ ] Ajouter des rapports RH automatisés
- [ ] Ajouter des alertes (contrats expirant, formations à renouveler, etc.)

