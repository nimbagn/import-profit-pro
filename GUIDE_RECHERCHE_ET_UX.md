# 🔍 Guide d'utilisation - Moteur de Recherche & Améliorations UX

## 📋 Vue d'ensemble

Ce guide explique comment utiliser le nouveau moteur de recherche global et les améliorations UX/UI (drag & drop, animations).

---

## 🚀 Installation

### 1. Créer la table de recherche

**Option A : Automatique (recommandé)**
La table `search_index` sera créée automatiquement au démarrage de l'application Flask via `db.create_all()`. Il suffit de lancer l'application :

```bash
python3 app.py
```

**Option B : Manuel (si nécessaire)**
Si vous préférez créer la table manuellement, utilisez MySQL :

```bash
# Remplacer par vos vraies valeurs de configuration
mysql -u DB_USER -p DB_NAME < scripts/create_search_index_table.sql
```

Ou via MySQL directement :

```sql
USE votre_database;
SOURCE scripts/create_search_index_table.sql;
```

**Option C : Via Python (utilise la configuration du projet)**
```bash
python3 scripts/create_search_index_simple.py
```

### 2. Indexer les données existantes

Exécutez le script d'indexation initiale :

```bash
python3 scripts/index_all_data.py
```

Ce script va indexer :
- ✅ Tous les articles
- ✅ Toutes les simulations
- ✅ Toutes les prévisions
- ✅ Tous les articles de stock
- ✅ Tous les mouvements de stock
- ✅ Tous les véhicules
- ✅ Tous les messages de chat

---

## 🔍 Utilisation du Moteur de Recherche

### Accès à la recherche

1. Cliquez sur **"Recherche Globale"** dans le menu latéral
2. Ou accédez directement à `/search/`

### Fonctionnalités

#### Recherche de base
- Tapez votre recherche dans la barre de recherche
- La recherche se lance automatiquement après 300ms (debounce)
- Appuyez sur **Entrée** pour rechercher immédiatement

#### Filtres par module
Cochez/décochez les modules à inclure :
- 📦 **Articles** : Recherche dans les articles
- 🧮 **Simulations** : Recherche dans les simulations
- 📊 **Prévisions** : Recherche dans les prévisions
- 📦 **Stocks** : Recherche dans les stocks
- 🚗 **Flotte** : Recherche dans les véhicules
- 💬 **Chat** : Recherche dans les messages

#### Filtres par type
Cochez/décochez les types d'entités :
- Article
- Simulation
- Prévision
- Article Stock
- Mouvement
- Véhicule
- Message

#### Résultats
- Les termes recherchés sont **surlignés** dans les résultats
- Chaque résultat affiche :
  - 📌 Titre avec icône
  - 📝 Extrait du contenu
  - 🏷️ Badge du module
  - 📅 Date de création
  - 🔗 Lien direct vers l'entité

#### Pagination
- Utilisez les boutons **Précédent** / **Suivant**
- Ou cliquez directement sur un numéro de page

---

## 🎨 Améliorations UX/UI

### Drag & Drop pour fichiers

#### Dans le Chat
1. Ouvrez une conversation
2. **Glissez** un ou plusieurs fichiers sur la zone d'upload (icône trombone)
3. Les fichiers sont automatiquement sélectionnés
4. Une notification confirme la sélection
5. Envoyez votre message avec les fichiers

#### Zones de drop personnalisées
Pour ajouter le drag & drop à d'autres formulaires :

```html
<div class="drag-drop-zone" id="myDropZone">
    <input type="file" id="myFileInput" multiple>
    <i class="fas fa-cloud-upload-alt"></i>
    <p>Glissez vos fichiers ici ou cliquez pour sélectionner</p>
</div>

<script>
initFileDropZone(
    document.getElementById('myDropZone'),
    document.getElementById('myFileInput'),
    (files) => {
        console.log(`${files.length} fichier(s) sélectionné(s)`);
    }
);
</script>
```

### Animations

#### Classes CSS disponibles

**Animations d'entrée :**
- `.animate-fade-in` : Fade in
- `.animate-slide-up` : Slide depuis le bas
- `.animate-slide-down` : Slide depuis le haut
- `.animate-slide-left` : Slide depuis la droite
- `.animate-slide-right` : Slide depuis la gauche
- `.animate-bounce` : Effet bounce
- `.animate-pulse` : Pulsation continue

**Effets hover :**
- `.hover-lift` : Soulève l'élément au survol
- `.hover-scale` : Agrandit l'élément au survol
- `.hover-glow` : Ajoute un halo lumineux

**Transitions :**
- `.smooth-transition` : Transition fluide (0.3s)
- `.smooth-transition-fast` : Transition rapide (0.15s)
- `.smooth-transition-slow` : Transition lente (0.5s)

#### Utilisation JavaScript

```javascript
// Fade in
fadeIn(element, 300); // durée en ms

// Fade out
fadeOut(element, 300, () => {
    console.log('Animation terminée');
});

// Slide in
slideIn(element, 'up', 400); // direction: 'up', 'down', 'left', 'right'

// Animation en cascade
staggerAnimation(elements, 'animate-fade-in', 100); // délai entre chaque élément

// Effet ripple sur bouton
button.addEventListener('click', createRipple);
```

### Notifications toast

Afficher une notification :

```javascript
showNotification('Message de succès', 'success', 3000);
showNotification('Message d\'erreur', 'error', 5000);
showNotification('Message d\'avertissement', 'warning', 4000);
showNotification('Message d\'information', 'info', 3000);
```

Types disponibles : `success`, `error`, `warning`, `info`

---

## 🔧 Maintenance

### Réindexer les données

#### Via l'interface (Admin uniquement)
1. Accédez à `/search/api/reindex` (POST)
2. Toutes les données seront réindexées

#### Via le script
```bash
python3 scripts/index_all_data.py
```

### Statistiques de l'index

Accédez à `/search/api/stats` pour voir :
- Nombre total d'entrées indexées
- Répartition par module
- Répartition par type d'entité

---

## 🐛 Dépannage

### La recherche ne retourne aucun résultat

1. **Vérifiez que la table existe :**
   ```sql
   SHOW TABLES LIKE 'search_index';
   ```

2. **Vérifiez que des données sont indexées :**
   ```sql
   SELECT COUNT(*) FROM search_index;
   ```

3. **Réindexez les données :**
   ```bash
   python3 scripts/index_all_data.py
   ```

### Les animations ne fonctionnent pas

1. Vérifiez que `static/css/ux/animations.css` est chargé
2. Vérifiez que `static/js/ux/animations.js` est chargé
3. Ouvrez la console du navigateur pour voir les erreurs

### Le drag & drop ne fonctionne pas

1. Vérifiez que `initFileDropZone` est appelé après le chargement du DOM
2. Vérifiez que les éléments existent dans le DOM
3. Ouvrez la console du navigateur pour voir les erreurs

---

## 📚 API de Recherche

### Recherche complète

**Endpoint :** `POST /search/api/search`

**Body :**
```json
{
    "query": "terme de recherche",
    "modules": ["articles", "simulations"],
    "entity_types": ["article", "simulation"],
    "limit": 50,
    "offset": 0
}
```

**Response :**
```json
{
    "results": [
        {
            "id": 1,
            "entity_type": "article",
            "entity_id": 123,
            "title": "Nom de l'article",
            "content": "Extrait du contenu...",
            "module": "articles",
            "url": "/articles/123",
            "metadata": {...},
            "created_at": "2024-01-01T00:00:00"
        }
    ],
    "total": 1,
    "query": "terme de recherche",
    "modules": ["articles"],
    "entity_types": ["article"]
}
```

### Recherche rapide (autocomplete)

**Endpoint :** `GET /search/api/quick?q=terme&limit=10`

**Response :**
```json
{
    "suggestions": [
        {
            "title": "Nom de l'entité",
            "module": "articles",
            "url": "/articles/123",
            "entity_type": "article"
        }
    ]
}
```

---

## ✅ Checklist de vérification

- [ ] Table `search_index` créée
- [ ] Données indexées (script exécuté)
- [ ] Lien "Recherche Globale" visible dans le menu
- [ ] Recherche fonctionne avec différents termes
- [ ] Filtres par module fonctionnent
- [ ] Filtres par type fonctionnent
- [ ] Pagination fonctionne
- [ ] Drag & drop fonctionne dans le chat
- [ ] Animations s'affichent correctement
- [ ] Notifications toast fonctionnent

---

## 🎯 Prochaines améliorations possibles

- 🔍 Recherche avancée avec opérateurs (AND, OR, NOT)
- 📊 Historique de recherche
- ⭐ Favoris de recherche
- 🔔 Alertes de recherche sauvegardées
- 📱 Mode mobile optimisé
- 🌐 Recherche multilingue

---

**Bonnes recherches ! 🔍✨**

