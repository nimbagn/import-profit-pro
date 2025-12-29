# Adaptation des Pages Référentiels au Style Hapag-Lloyd

## Pages à Adapter

1. ✅ `regions_list.html` - DÉJÀ ADAPTÉE
2. ⏳ `depots_list.html` - À ADAPTER
3. ⏳ `vehicles_list.html` - À ADAPTER
4. ⏳ `families_list.html` - À ADAPTER
5. ⏳ `stock_items_list.html` - À ADAPTER

## Modifications à Appliquer

### Structure HTML
- Remplacer `<div class="page-container">` par `<section class="page-section">`
- Remplacer `.page-header-hl` par `.page-header-promo`
- Remplacer `.card-hl` par `.card-promo`
- Remplacer `.table-hl` par `.table-responsive` + `.table-promo`

### Classes CSS
- Remplacer `btn-hl` par `btn-promo`
- Remplacer `badge-hl` par `badge-promo`
- Supprimer les styles CSS redondants

### Header
- Utiliser la structure avec `d-flex justify-content-between`
- Utiliser `icon-promo` pour les icônes

