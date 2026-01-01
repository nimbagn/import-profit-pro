# 🚀 Guide Rapide : Exécuter le Script sur Render

## ⚡ Méthode la Plus Simple (2 minutes)

### Étape 1 : Accéder à Render
1. Allez sur https://dashboard.render.com
2. Connectez-vous à votre compte
3. Cliquez sur votre projet **Import Profit Pro**

### Étape 2 : Ouvrir la Base de Données
1. Dans la liste des services, **cliquez sur votre base de données PostgreSQL**
   - Elle s'appelle généralement `import-profit-pro-db` ou similaire

### Étape 3 : Ouvrir le SQL Editor
1. Dans la page de la base de données, cherchez l'onglet **"SQL Editor"** ou **"Query"**
2. **Cliquez dessus**

### Étape 4 : Copier le Script
1. **Ouvrez** le fichier `scripts/ajouter_permissions_magasinier_postgresql.sql`
2. **Sélectionnez tout** (Ctrl+A ou Cmd+A)
3. **Copiez** (Ctrl+C ou Cmd+C)

### Étape 5 : Coller et Exécuter
1. **Collez** le script** dans l'éditeur SQL de Render (Ctrl+V ou Cmd+V)
2. **Cliquez sur "Run"** ou **"Execute"** (ou Ctrl+Enter)
3. **Attendez** quelques secondes

### Étape 6 : Vérifier
Vous devriez voir :
```
NOTICE: Permissions du rôle magasinier mises à jour avec succès
```

## ✅ C'est Terminé !

Les permissions sont maintenant mises à jour. Vous pouvez tester dans l'application.

---

## 🔍 Vérification Rapide

Pour vérifier que ça a fonctionné, exécutez cette requête dans le SQL Editor :

```sql
SELECT permissions FROM roles WHERE code = 'warehouse';
```

Vous devriez voir les permissions incluant :
- `receptions`
- `outgoings`
- `returns`
- `orders`
- `stock_loading`

---

## 📸 Capture d'Écran (À quoi ça ressemble)

```
Render Dashboard
  └─ Services
      └─ import-profit-pro-db (PostgreSQL)
          └─ [Onglet] SQL Editor
              └─ [Zone de texte] ← Collez le script ici
              └─ [Bouton] Run ← Cliquez ici
```

---

## 🐛 Si ça ne fonctionne pas

1. **Vérifiez** que vous êtes bien dans la base de données PostgreSQL (pas MySQL)
2. **Vérifiez** que le script est complet (123 lignes)
3. **Vérifiez** qu'il n'y a pas d'erreur de syntaxe
4. **Essayez** de copier-coller à nouveau

---

## 📞 Besoin d'Aide ?

Consultez le guide détaillé : `GUIDE_EXECUTER_SCRIPT_RENDER.md`

