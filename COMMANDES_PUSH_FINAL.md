# 🚀 Commandes pour Pousser le Code

## 📋 Commandes à Exécuter

Copiez-collez ces commandes **une par une** dans votre terminal :

```bash
cd /Users/dantawi/Documents/mini_flask_import_profitability

# Mettre à jour le remote avec le nouveau token
# REMPLACEZ VOTRE_TOKEN par votre token GitHub
git remote set-url origin https://VOTRE_TOKEN@github.com/nimbagn/import-profit-pro.git

# Vérifier que c'est correct
git remote -v

# Pousser le code
git push origin main
```

## ✅ Après le Push Réussi

1. **Render détectera automatiquement** le nouveau commit
2. **Render redéploiera** avec :
   - Python 3.11.9
   - Route `/init` pour créer les utilisateurs
   - Toutes les améliorations

3. **Une fois déployé**, allez sur :
   `https://votre-app.onrender.com/init`
   
   Pour créer les utilisateurs (admin/admin123)

## 🔐 Sécurité

⚠️ **Important** : Après le push réussi, vous pouvez révoquer ce token et en créer un nouveau si vous voulez, car il est maintenant visible dans l'historique de cette conversation.

---

**Exécutez ces commandes maintenant pour pousser votre code !**

