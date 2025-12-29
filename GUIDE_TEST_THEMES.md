# 🎨 Guide de Test - Système de Thèmes Personnalisables

## ✅ Vérifications Préalables

### 1. Fichiers Créés
- ✅ `models.py` - Modèle `UserPreference` ajouté
- ✅ `themes.py` - Blueprint avec routes API
- ✅ `static/css/themes.css` - Styles pour tous les thèmes
- ✅ `static/js/themes.js` - JavaScript pour gestion dynamique
- ✅ `templates/themes/settings.html` - Page de paramètres
- ✅ `scripts/create_user_preferences_table.sql` - Script SQL

### 2. Intégration
- ✅ Blueprint enregistré dans `app.py`
- ✅ Lien "Apparence" ajouté dans le menu utilisateur
- ✅ CSS et JS inclus dans `base_modern_complete.html`

## 🧪 Tests à Effectuer

### Test 1 : Accès à la Page de Paramètres
1. Connectez-vous à l'application
2. Cliquez sur votre nom d'utilisateur dans le menu en haut à droite
3. Cliquez sur "Apparence"
4. **Résultat attendu** : La page `/themes/settings` s'affiche avec :
   - 4 aperçus de thèmes (Hapag-Lloyd, Professionnel, Énergique, Nature)
   - 2 options de mode (Clair, Sombre)
   - Boutons "Enregistrer" et "Réinitialiser"

### Test 2 : Application Temporaire d'un Thème
1. Sur la page de paramètres, cliquez sur un aperçu de thème différent
2. **Résultat attendu** : 
   - Le thème s'applique immédiatement à la page
   - L'aperçu sélectionné est mis en surbrillance
   - Les couleurs changent selon le thème choisi

### Test 3 : Changement de Mode (Clair/Sombre)
1. Cliquez sur l'option "Sombre"
2. **Résultat attendu** :
   - Le fond devient sombre
   - Le texte devient clair
   - Tous les éléments s'adaptent au mode sombre

### Test 4 : Sauvegarde des Préférences
1. Sélectionnez un thème (ex: "Professionnel")
2. Sélectionnez un mode (ex: "Sombre")
3. Cliquez sur "Enregistrer les Préférences"
4. **Résultat attendu** :
   - Notification de succès s'affiche
   - Les préférences sont sauvegardées dans la base de données
5. Rechargez la page
6. **Résultat attendu** : Le thème et le mode sauvegardés sont appliqués automatiquement

### Test 5 : Application Automatique au Chargement
1. Enregistrez un thème et un mode
2. Déconnectez-vous puis reconnectez-vous
3. **Résultat attendu** : Vos préférences sont appliquées automatiquement

### Test 6 : Réinitialisation
1. Cliquez sur "Réinitialiser"
2. **Résultat attendu** :
   - Le thème revient à "Hapag-Lloyd"
   - Le mode revient à "Clair"
   - Les changements sont appliqués temporairement (non sauvegardés)

## 🔍 Vérifications Techniques

### Base de Données
La table `user_preferences` sera créée automatiquement au prochain démarrage grâce à `db.create_all()`.

Pour vérifier manuellement :
```sql
DESCRIBE user_preferences;
SELECT * FROM user_preferences;
```

### API Endpoints
- `GET /themes/settings` - Page de paramètres
- `GET /themes/api/preferences` - Récupérer les préférences (JSON)
- `POST /themes/api/preferences` - Sauvegarder les préférences (JSON)
- `POST /themes/api/apply` - Appliquer temporairement un thème (JSON)

### Variables CSS
Les thèmes utilisent des variables CSS personnalisées :
- `--color-primary` : Couleur principale
- `--color-accent` : Couleur d'accent
- `--bg-primary` : Fond principal
- `--text-primary` : Texte principal
- etc.

## 🐛 Dépannage

### Problème : La page `/themes/settings` ne s'affiche pas
**Solution** : Vérifiez que :
- Le blueprint est enregistré dans `app.py`
- Vous êtes connecté (la route nécessite `@login_required`)

### Problème : Les thèmes ne s'appliquent pas
**Solution** : Vérifiez que :
- Le fichier `static/css/themes.css` est chargé
- Le JavaScript `static/js/themes.js` est chargé
- Les attributs `data-theme` et `data-color-mode` sont définis sur `<html>`

### Problème : Les préférences ne sont pas sauvegardées
**Solution** : Vérifiez que :
- La table `user_preferences` existe dans la base de données
- Les logs du serveur pour voir les erreurs éventuelles

## 📝 Notes

- Les préférences sont stockées par utilisateur
- Chaque utilisateur peut avoir son propre thème
- Les préférences sont appliquées automatiquement au chargement de chaque page
- Le localStorage est utilisé comme fallback si l'API ne répond pas








