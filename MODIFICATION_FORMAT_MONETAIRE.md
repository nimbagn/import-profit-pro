# Modification : Format Monétaire avec Espaces

## ✅ Modifications Réalisées

### 1. Fonction `format_currency()` dans `utils.py`
- ✅ Modifiée pour utiliser des **espaces** comme séparateurs de milliers
- ✅ Remplace les virgules par des espaces après formatage
- ✅ Format : `1 500 000 GNF` au lieu de `1,500,000 GNF`

### 2. Templates Inventaires

#### A. `sessions_by_year.html`
- ✅ `total_variances` : Utilise `format_number(2)` au lieu de `"%.2f"|format`
- ✅ `total_value_variances` : Utilise `format_number(0)` au lieu de `"{:,.0f}"|format`

#### B. `session_detail.html`
- ✅ `total_variances` : Utilise `format_number(2)` au lieu de `"{:,.2f}"|format`
- ✅ `total_value_variances` : Utilise `format_number(0)` au lieu de `"{:,.0f}"|format`
- ✅ `item.value_variance` : Utilise `format_number(0)` au lieu de `"{:,.0f}"|format`

## 📝 Formatage Utilisé

### Filtre Jinja2 `format_number`
Le filtre `format_number` existe déjà dans `app.py` et formate les nombres avec des espaces :
```python
@app.template_filter('format_number')
def format_number(value, decimals=0):
    """Formate un nombre avec des espaces comme séparateurs de milliers"""
    formatted = f"{num:,.{decimals}f}".replace(',', ' ')
    return formatted
```

### Exemples de Formatage
- `150000` → `150 000`
- `1500000` → `1 500 000`
- `150000.50` → `150 000` (avec `decimals=0`)
- `150000.50` → `150 000.50` (avec `decimals=2`)

## 🎯 Utilisation dans les Templates

### Avant
```jinja2
{{ "{:,.0f}".format(total_value_variances) }} GNF
```

### Après
```jinja2
{{ total_value_variances|format_number(0) }} GNF
```

## 📋 Autres Templates à Vérifier

D'autres templates utilisent déjà `|replace(',', ' ')` après le formatage :
- `templates/simulation_preview.html`
- `templates/promotion/sales_list.html`
- `templates/forecast_list_ultra_modern.html`
- etc.

Ces templates sont déjà corrects et utilisent des espaces.

## ✅ Résultat

Tous les montants monétaires dans les modules Inventaires utilisent maintenant des **espaces** comme séparateurs de milliers, conformément aux standards français/guinéens.

**Exemple d'affichage** :
- `1 500 000 GNF` au lieu de `1,500,000 GNF`
- `25 000 GNF` au lieu de `25,000 GNF`

