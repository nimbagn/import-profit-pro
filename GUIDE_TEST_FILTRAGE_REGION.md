# 🧪 Guide de Test - Filtrage par Région

## 📋 Prérequis

1. ✅ Application démarrée sur http://localhost:5002
2. ✅ Au moins 2 régions créées dans la base de données
3. ✅ Au moins 2 utilisateurs avec des régions différentes
4. ✅ Au moins 1 utilisateur admin
5. ✅ Des dépôts, véhicules, équipes assignés à différentes régions

---

## 🎯 Tests à Effectuer

### Test 1 : Vérification des Dépôts par Région

**Objectif** : Vérifier qu'un utilisateur ne voit que les dépôts de sa région

**Étapes** :
1. Se connecter avec un utilisateur ayant une région assignée (ex: Région A)
2. Aller sur `/referentiels/depots`
3. **Vérifier** : Seuls les dépôts de la Région A sont affichés
4. Se connecter avec un utilisateur d'une autre région (ex: Région B)
5. Aller sur `/referentiels/depots`
6. **Vérifier** : Seuls les dépôts de la Région B sont affichés
7. Se connecter avec un admin
8. **Vérifier** : Tous les dépôts sont affichés (toutes régions)

**URLs à tester** :
- http://localhost:5002/referentiels/depots

---

### Test 2 : Vérification des Véhicules par Région

**Objectif** : Vérifier qu'un utilisateur ne voit que les véhicules de sa région (via conducteur)

**Étapes** :
1. Se connecter avec un utilisateur ayant une région assignée (ex: Région A)
2. Aller sur `/referentiels/vehicles`
3. **Vérifier** : Seuls les véhicules dont le conducteur appartient à la Région A sont affichés
4. Se connecter avec un utilisateur d'une autre région (ex: Région B)
5. Aller sur `/referentiels/vehicles`
6. **Vérifier** : Seuls les véhicules dont le conducteur appartient à la Région B sont affichés
7. Se connecter avec un admin
8. **Vérifier** : Tous les véhicules sont affichés

**URLs à tester** :
- http://localhost:5002/referentiels/vehicles

---

### Test 3 : Accès aux Stocks de Dépôt

**Objectif** : Vérifier qu'un utilisateur ne peut accéder qu'aux stocks de sa région

**Étapes** :
1. Se connecter avec un utilisateur ayant une région assignée (ex: Région A)
2. Aller sur `/stocks/depot/<id>` où `<id>` est un dépôt de la Région A
3. **Vérifier** : Le stock s'affiche correctement
4. Essayer d'accéder à `/stocks/depot/<id>` où `<id>` est un dépôt d'une autre région
5. **Vérifier** : Message d'erreur "Vous n'avez pas accès à ce dépôt" et redirection
6. Se connecter avec un admin
7. **Vérifier** : Accès à tous les dépôts sans restriction

**URLs à tester** :
- http://localhost:5002/stocks/depot/1 (remplacer 1 par un ID valide)

---

### Test 4 : Accès aux Stocks de Véhicule

**Objectif** : Vérifier qu'un utilisateur ne peut accéder qu'aux stocks des véhicules de sa région

**Étapes** :
1. Se connecter avec un utilisateur ayant une région assignée (ex: Région A)
2. Aller sur `/stocks/vehicle/<id>` où `<id>` est un véhicule de la Région A
3. **Vérifier** : Le stock s'affiche correctement
4. Essayer d'accéder à `/stocks/vehicle/<id>` où `<id>` est un véhicule d'une autre région
5. **Vérifier** : Message d'erreur "Vous n'avez pas accès à ce véhicule" et redirection
6. Se connecter avec un admin
7. **Vérifier** : Accès à tous les véhicules sans restriction

**URLs à tester** :
- http://localhost:5002/stocks/vehicle/1 (remplacer 1 par un ID valide)

---

### Test 5 : Filtrage dans les Formulaires de Mouvement

**Objectif** : Vérifier que les listes déroulantes dans les formulaires sont filtrées par région

**Étapes** :
1. Se connecter avec un utilisateur ayant une région assignée (ex: Région A)
2. Aller sur une page de création de mouvement (ex: `/stocks/transfer/new`)
3. **Vérifier** : Dans le champ "Dépôt source", seuls les dépôts de la Région A apparaissent
4. **Vérifier** : Dans le champ "Véhicule", seuls les véhicules de la Région A apparaissent
5. Se connecter avec un admin
6. **Vérifier** : Tous les dépôts et véhicules apparaissent

**URLs à tester** :
- http://localhost:5002/stocks/transfer/new
- http://localhost:5002/stocks/receptions/new
- http://localhost:5002/stocks/outgoing/new

---

### Test 6 : Filtrage des Équipes de Promotion

**Objectif** : Vérifier qu'un utilisateur ne voit que les équipes de sa région

**Étapes** :
1. Se connecter avec un utilisateur ayant une région assignée (ex: Région A)
2. Aller sur `/promotion/workflow`
3. **Vérifier** : Seules les équipes dont le responsable appartient à la Région A sont affichées
4. Aller sur `/promotion/members`
5. **Vérifier** : Seuls les membres des équipes de la Région A sont affichés
6. Se connecter avec un admin
7. **Vérifier** : Toutes les équipes et tous les membres sont affichés

**URLs à tester** :
- http://localhost:5002/promotion/workflow
- http://localhost:5002/promotion/members

---

### Test 7 : Filtrage dans les Statistiques

**Objectif** : Vérifier que les statistiques sont filtrées par région

**Étapes** :
1. Se connecter avec un utilisateur ayant une région assignée (ex: Région A)
2. Aller sur `/stocks/summary`
3. **Vérifier** : Dans les filtres, seuls les dépôts et véhicules de la Région A apparaissent
4. Aller sur `/stocks/history`
5. **Vérifier** : Dans les filtres, seuls les dépôts et véhicules de la Région A apparaissent
6. Se connecter avec un admin
7. **Vérifier** : Tous les dépôts et véhicules apparaissent dans les filtres

**URLs à tester** :
- http://localhost:5002/stocks/summary
- http://localhost:5002/stocks/history

---

## ✅ Checklist de Validation

- [ ] Les dépôts sont filtrés par région
- [ ] Les véhicules sont filtrés par région (via conducteur)
- [ ] Les équipes sont filtrées par région (via responsable)
- [ ] Les membres sont filtrés par région (via équipe)
- [ ] L'accès aux stocks de dépôt est restreint par région
- [ ] L'accès aux stocks de véhicule est restreint par région
- [ ] Les formulaires affichent uniquement les données de la région
- [ ] Les admins voient toutes les données sans restriction
- [ ] Les messages d'erreur sont clairs pour les accès refusés
- [ ] Les redirections fonctionnent correctement

---

## 🔍 Tests Manuels Rapides

### Test Rapide 1 : Vérification Console

1. Ouvrir la console du navigateur (F12)
2. Se connecter avec un utilisateur non-admin
3. Naviguer sur différentes pages
4. **Vérifier** : Aucune erreur JavaScript dans la console

### Test Rapide 2 : Vérification Logs Serveur

1. Vérifier les logs de l'application (`app.log`)
2. **Vérifier** : Aucune erreur SQL ou Python
3. **Vérifier** : Les requêtes sont bien filtrées (peut nécessiter l'activation du logging SQL)

### Test Rapide 3 : Test de Performance

1. Se connecter avec un utilisateur ayant une région avec beaucoup de données
2. Naviguer sur les pages principales
3. **Vérifier** : Les pages se chargent rapidement (< 2 secondes)

---

## 🐛 Problèmes Potentiels et Solutions

### Problème 1 : Un utilisateur voit toutes les données

**Cause** : L'utilisateur n'a pas de région assignée ou est admin

**Solution** : 
- Vérifier que `user.region_id` n'est pas NULL
- Vérifier que le rôle n'est pas 'admin' ou 'superadmin'

### Problème 2 : Erreur "Vous n'avez pas accès à ce dépôt"

**Cause** : Le dépôt appartient à une autre région

**Solution** : 
- Vérifier que le dépôt a bien une région assignée
- Vérifier que l'utilisateur appartient à la même région

### Problème 3 : Les véhicules ne sont pas filtrés

**Cause** : Les véhicules n'ont pas de conducteur assigné

**Solution** : 
- Assigner un conducteur avec une région à chaque véhicule
- Vérifier que `vehicle.current_user_id` n'est pas NULL

### Problème 4 : Les équipes ne sont pas filtrées

**Cause** : Les équipes n'ont pas de responsable avec région

**Solution** : 
- Assigner un responsable avec une région à chaque équipe
- Vérifier que `team.team_leader_id` pointe vers un utilisateur avec région

---

## 📊 Résultats Attendus

### Pour un Utilisateur Normal (Région A)

- ✅ Voit uniquement les dépôts de la Région A
- ✅ Voit uniquement les véhicules de la Région A
- ✅ Voit uniquement les équipes de la Région A
- ✅ Voit uniquement les membres de la Région A
- ✅ Ne peut pas accéder aux données d'autres régions
- ✅ Messages d'erreur clairs pour les accès refusés

### Pour un Administrateur

- ✅ Voit tous les dépôts (toutes régions)
- ✅ Voit tous les véhicules (toutes régions)
- ✅ Voit toutes les équipes (toutes régions)
- ✅ Voit tous les membres (toutes régions)
- ✅ Accès complet à toutes les données

---

## 🎯 Commandes SQL pour Vérifier les Données

```sql
-- Vérifier les utilisateurs et leurs régions
SELECT u.id, u.username, u.full_name, r.name as region_name
FROM users u
LEFT JOIN regions r ON u.region_id = r.id
ORDER BY r.name, u.username;

-- Vérifier les dépôts et leurs régions
SELECT d.id, d.name, r.name as region_name
FROM depots d
LEFT JOIN regions r ON d.region_id = r.id
ORDER BY r.name, d.name;

-- Vérifier les véhicules et leurs régions (via conducteur)
SELECT v.id, v.plate_number, u.username as driver, r.name as region_name
FROM vehicles v
LEFT JOIN users u ON v.current_user_id = u.id
LEFT JOIN regions r ON u.region_id = r.id
ORDER BY r.name, v.plate_number;

-- Vérifier les équipes et leurs régions (via responsable)
SELECT pt.id, pt.name, u.username as leader, r.name as region_name
FROM promotion_teams pt
LEFT JOIN users u ON pt.team_leader_id = u.id
LEFT JOIN regions r ON u.region_id = r.id
ORDER BY r.name, pt.name;
```

---

## ✅ Statut

**Date de création** : {{ date }}
**Version** : 1.0
**Statut** : Prêt pour tests

