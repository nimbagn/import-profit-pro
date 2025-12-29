# 🎨 Guide d'Application du Style Hapag-Lloyd

## ✅ Templates Déjà Mis à Jour

1. ✅ `templates/index_hapag_lloyd.html` - Page d'accueil
2. ✅ `templates/base_modern_complete.html` - Template de base
3. ✅ `templates/referentiels/regions_list.html` - Liste des régions
4. ✅ `templates/referentiels/region_form.html` - Formulaire région
5. ✅ `templates/stocks/movements_list.html` - Liste des mouvements

## 📋 Remplacements à Effectuer

### Classes CSS à Remplacer

| Ancienne Classe | Nouvelle Classe |
|----------------|-----------------|
| `btn-premium` | `btn-hl btn-hl-primary` |
| `table-premium` | `table-hl` (dans une `card-hl`) |
| `badge-premium` | `badge-hl badge-hl-info` (ou success/warning/danger selon le contexte) |
| `card-premium` | `card-hl` |
| `form-card` | `form-hl` |
| `form-control` | `form-hl-input` |
| `form-label` | `form-hl-label` |

### Structure de Page

**Avant :**
```html
<div class="container-premium">
  <div class="header-premium">
    <h1 class="title-premium">Titre</h1>
    <a href="#" class="btn-premium">Action</a>
  </div>
  <div class="table-premium">...</div>
</div>
```

**Après :**
```html
<div class="page-container">
  <div class="page-header-hl">
    <h1 class="page-title-hl">Titre</h1>
    <a href="#" class="btn-hl btn-hl-primary">Action</a>
  </div>
  <div class="card-hl">
    <div class="table-hl">...</div>
  </div>
</div>
```

### Structure de Formulaire

**Avant :**
```html
<div class="form-container">
  <div class="form-card">
    <div class="form-header">
      <h1 class="form-title">Titre</h1>
    </div>
    <form>
      <div class="form-group">
        <label class="form-label">Label</label>
        <input class="form-control">
      </div>
      <button class="btn-submit">Sauvegarder</button>
    </form>
  </div>
</div>
```

**Après :**
```html
<div class="form-container">
  <div class="form-hl">
    <div class="page-header-hl" style="border-bottom: 2px solid var(--gray-200); padding-bottom: var(--space-lg); margin-bottom: var(--space-xl);">
      <h1 class="page-title-hl">Titre</h1>
    </div>
    <form>
      <div class="form-group" style="margin-bottom: var(--space-lg);">
        <label class="form-hl-label">Label</label>
        <input class="form-hl-input">
      </div>
      <div style="display: flex; gap: var(--space-md); margin-top: var(--space-xl);">
        <a href="#" class="btn-hl btn-hl-outline" style="flex: 1;">Annuler</a>
        <button type="submit" class="btn-hl btn-hl-primary" style="flex: 1;">Sauvegarder</button>
      </div>
    </form>
  </div>
</div>
```

## 🎨 Classes Disponibles

### Boutons
- `btn-hl btn-hl-primary` - Bouton principal (bleu)
- `btn-hl btn-hl-secondary` - Bouton secondaire (outline bleu)
- `btn-hl btn-hl-accent` - Bouton accent (orange)
- `btn-hl btn-hl-outline` - Bouton outline (gris)

### Badges
- `badge-hl badge-hl-primary` - Badge bleu
- `badge-hl badge-hl-success` - Badge vert
- `badge-hl badge-hl-warning` - Badge orange
- `badge-hl badge-hl-danger` - Badge rouge
- `badge-hl badge-hl-info` - Badge bleu clair

### Cartes
- `card-hl` - Carte principale
- `stat-card-hl` - Carte de statistique

### Tableaux
- `table-hl` - Tableau (à mettre dans une `card-hl`)

### Formulaires
- `form-hl` - Conteneur de formulaire
- `form-hl-input` - Input
- `form-hl-label` - Label
- `form-hl-select` - Select

## 📝 Templates Restants à Mettre à Jour

### Référentiels
- [ ] `depots_list.html`
- [ ] `depot_form.html`
- [ ] `vehicles_list.html`
- [ ] `vehicle_form.html`
- [ ] `families_list.html`
- [ ] `family_form.html`
- [ ] `stock_items_list.html`
- [ ] `stock_item_form.html`

### Stocks
- [ ] `receptions_list.html`
- [ ] `reception_form.html`
- [ ] `reception_detail.html`
- [ ] `outgoings_list.html`
- [ ] `outgoing_form.html`
- [ ] `outgoing_detail.html`
- [ ] `returns_list.html`
- [ ] `return_form.html`
- [ ] `return_detail.html`
- [ ] `depot_stock.html`
- [ ] `vehicle_stock.html`
- [ ] `movement_form.html`

### Inventaires
- [ ] `sessions_list.html`
- [ ] `session_form.html`
- [ ] `session_detail.html`
- [ ] `detail_form.html`

### Flotte
- [ ] `vehicle_documents.html`
- [ ] `document_form.html`
- [ ] `vehicle_maintenances.html`
- [ ] `maintenance_form.html`
- [ ] `vehicle_odometer.html`
- [ ] `odometer_form.html`

### Autres
- [ ] `simulations_ultra_modern_v3.html`
- [ ] `articles_unified.html`
- [ ] `article_new_unified.html`
- [ ] `article_edit_unified.html`

## 🚀 Script de Remplacement Automatique

Un script est disponible pour faciliter les remplacements :

```bash
./scripts/update_templates_to_hl_style.sh
```

**Note** : Vérifiez toujours les résultats manuellement après l'exécution du script.

## 💡 Conseils

1. **Cohérence** : Utilisez toujours les mêmes classes pour les mêmes éléments
2. **Espacements** : Utilisez les variables CSS (`var(--space-md)`, etc.)
3. **Couleurs** : Utilisez les variables CSS (`var(--color-primary)`, etc.)
4. **Responsive** : Le style Hapag-Lloyd est déjà responsive
5. **Test** : Testez chaque page après modification

## ✅ Checklist de Vérification

Pour chaque template mis à jour, vérifiez :
- [ ] Les boutons utilisent `btn-hl`
- [ ] Les tableaux sont dans une `card-hl` avec `table-hl`
- [ ] Les formulaires utilisent `form-hl`, `form-hl-input`, `form-hl-label`
- [ ] Les badges utilisent `badge-hl`
- [ ] Les titres utilisent `page-title-hl`
- [ ] Les headers utilisent `page-header-hl`
- [ ] Le design est cohérent avec les autres pages
- [ ] La page fonctionne correctement

---

**Date** : $(date)
**Statut** : En cours de mise à jour

