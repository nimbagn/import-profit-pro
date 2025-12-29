# 🚀 Instructions Rapides - Initialisation de la Base de Données

## Option 1 : Script Automatique (Recommandé)

```bash
./executer_initialisation.sh
```

Le script va :
- ✅ Vérifier MySQL
- ✅ Demander vos identifiants
- ✅ Créer la base si nécessaire
- ✅ Exécuter l'initialisation
- ✅ Afficher un résumé

## Option 2 : Commande Manuelle

```bash
mysql -u root -p madargn < INITIALISATION_COMPLETE.sql
```

## Option 3 : Dans MySQL Workbench

1. Ouvrez MySQL Workbench
2. Connectez-vous à votre serveur
3. Ouvrez le fichier `INITIALISATION_COMPLETE.sql`
4. Exécutez le script (⌘+Shift+Enter)

## ⚠️ Important

**Ce script supprime toutes les données existantes** et recrée la base de zéro.

## ✅ Après l'exécution

1. **Redémarrez Flask** :
   ```bash
   pkill -f "python.*app.py"
   python3 app.py
   ```

2. **Connectez-vous** :
   - URL : http://localhost:5002/auth/login
   - Username : `admin`
   - Password : `admin123`

## 🔍 Vérification

Le script affiche automatiquement :
- Nombre de rôles créés
- Nombre d'utilisateurs créés
- Nombre de catégories créées
- Nombre d'articles créés

---

**Prêt ?** Exécutez : `./executer_initialisation.sh`

