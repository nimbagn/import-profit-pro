# Analyse : Gestion par Année

## 📋 Résumé Exécutif

Cette analyse étudie la possibilité d'implémenter une gestion par année dans le système, en particulier pour les inventaires et autres modules pertinents.

## 🔍 État Actuel

### Modules avec Filtres par Année Existants :
1. **Analytics** (`analytics.py`)
   - Fonction `get_period_dates()` supporte déjà `period='year'`
   - Filtrage par année pour les KPIs
   - Comparaisons année précédente

2. **Stocks** (`stocks.py`)
   - Filtre par période incluant `'year'` dans `stock_summary()`
   - Calcul automatique : `year_start = today.replace(month=1, day=1)`
   - Interface utilisateur avec sélecteur d'année

3. **Promotion** (`promotion.py`)
   - Utilisation de `date(today.year, ...)` pour les calculs mensuels
   - Pas de filtre dédié par année actuellement

### Modules SANS Gestion par Année :

1. **Inventaires** (`inventaires.py`)
   - ✅ Filtres par `date_from` et `date_to` existants
   - ❌ Pas de sélecteur d'année dédié
   - ❌ Pas de regroupement par année dans les listes
   - ❌ Pas de statistiques annuelles

2. **Commandes Commerciales** (`orders.py`)
   - Filtres par date mais pas de vue annuelle structurée

3. **Réceptions** (`stocks.py` - Reception)
   - Filtres par date mais pas de vue annuelle

4. **Forecasts** (`models.py` - Forecast)
   - Déjà des champs `start_date` et `end_date`
   - Pas de vue consolidée par année

## 💡 Opportunités d'Amélioration

### 1. Module Inventaires

#### Avantages d'une Gestion par Année :
- **Organisation** : Regrouper les sessions d'inventaire par année facilite la consultation historique
- **Rapports Annuels** : Générer des rapports de synthèse annuels
- **Comparaisons** : Comparer les performances d'inventaire année sur année
- **Archivage** : Faciliter l'archivage des données anciennes

#### Implémentation Proposée :

**A. Ajout d'un Filtre Année dans la Liste des Sessions**
```python
# Dans inventaires.py - sessions_list()
year_filter = request.args.get('year', type=int)
if year_filter:
    query = query.filter(
        extract('year', InventorySession.session_date) == year_filter
    )
```

**B. Vue Annuelle Consolidée**
- Nouvelle route `/inventory/sessions/by-year`
- Regroupement des sessions par année
- Statistiques par année (nombre de sessions, écarts moyens, etc.)

**C. Export Annuel**
- Export Excel consolidé pour une année complète
- Rapport de synthèse annuel avec graphiques

### 2. Module Commandes Commerciales

#### Avantages :
- Analyse des ventes par année
- Comparaison des performances annuelles
- Planification budgétaire annuelle

#### Implémentation :
- Ajout d'un filtre année dans la liste des commandes
- Dashboard annuel des commandes
- Statistiques de validation/rejet par année

### 3. Module Réceptions

#### Avantages :
- Suivi des approvisionnements par année
- Analyse des volumes reçus annuellement
- Comparaison avec les années précédentes

### 4. Module Forecasts

#### Avantages :
- Vue consolidée des prévisions par année
- Comparaison prévisions vs réalisations par année
- Planification stratégique annuelle

## 🛠️ Modifications Techniques Nécessaires

### 1. Base de Données

**Aucune modification de schéma nécessaire** ✅
- Les champs de date existent déjà (`session_date`, `order_date`, etc.)
- Utilisation de `extract('year', date_column)` pour le filtrage

### 2. Modifications de Code

#### A. Inventaires (`inventaires.py`)

**a) Ajout du filtre année dans `sessions_list()` :**
```python
year_filter = request.args.get('year', type=int)
if year_filter:
    query = query.filter(
        extract('year', InventorySession.session_date) == year_filter
    )
```

**b) Nouvelle route pour vue annuelle :**
```python
@inventaires_bp.route('/sessions/by-year')
@login_required
def sessions_by_year():
    """Vue consolidée des sessions d'inventaire par année"""
    from sqlalchemy import extract, func
    
    # Récupérer toutes les années disponibles
    years = db.session.query(
        extract('year', InventorySession.session_date).label('year')
    ).distinct().order_by('year').all()
    
    # Statistiques par année
    stats_by_year = []
    for year in years:
        year_value = year.year
        sessions = InventorySession.query.filter(
            extract('year', InventorySession.session_date) == year_value
        ).all()
        
        # Calculer les statistiques
        total_sessions = len(sessions)
        total_items = sum(len(s.details) for s in sessions)
        # ... autres stats
        
        stats_by_year.append({
            'year': year_value,
            'sessions': sessions,
            'stats': {...}
        })
    
    return render_template('inventaires/sessions_by_year.html', 
                         stats_by_year=stats_by_year)
```

**c) Modification du template `sessions_list.html` :**
- Ajout d'un sélecteur d'année dans les filtres
- Liste déroulante avec les années disponibles

#### B. Commandes (`orders.py`)

**Ajout similaire du filtre année :**
```python
year_filter = request.args.get('year', type=int)
if year_filter:
    query = query.filter(
        extract('year', CommercialOrder.order_date) == year_filter
    )
```

#### C. Utilitaires (`utils.py` ou nouveau fichier)

**Fonction helper pour extraire les années disponibles :**
```python
def get_available_years(model_class, date_column):
    """Récupère les années disponibles pour un modèle"""
    from sqlalchemy import extract
    years = db.session.query(
        extract('year', date_column).label('year')
    ).distinct().order_by('year').all()
    return [y.year for y in years]
```

### 3. Modifications des Templates

#### A. Template Inventaires

**Ajout du sélecteur d'année :**
```html
<div>
  <label class="form-hl-label">Année</label>
  <select name="year" class="form-hl-input">
    <option value="">Toutes les années</option>
    {% for year in available_years %}
    <option value="{{ year }}" {% if year_filter == year %}selected{% endif %}>
      {{ year }}
    </option>
    {% endfor %}
  </select>
</div>
```

**Nouveau template `sessions_by_year.html` :**
- Vue en tableau avec une ligne par année
- Statistiques consolidées par année
- Graphiques de tendance

## 📊 Structure de Données Proposée

### Vue Annuelle des Inventaires

```python
{
    'year': 2024,
    'sessions': [
        {
            'id': 1,
            'date': '2024-01-15',
            'depot': 'Dépôt Central',
            'status': 'validated',
            'items_count': 150,
            'total_variance': -25.5,
            'value_variance': -125000.00
        },
        # ... autres sessions
    ],
    'statistics': {
        'total_sessions': 12,
        'total_items_inventoried': 1800,
        'average_variance': -2.1,
        'total_value_variance': -1500000.00,
        'precision_rate': 95.2
    }
}
```

## 🎯 Avantages Globaux

1. **Organisation** : Meilleure structuration des données historiques
2. **Performance** : Requêtes optimisées avec index sur les années
3. **Reporting** : Génération facilitée de rapports annuels
4. **Comparaisons** : Analyse année sur année simplifiée
5. **Archivage** : Identification facile des données à archiver

## ⚠️ Considérations

### Performance
- **Index recommandé** : Créer un index sur l'extraction de l'année si nécessaire
- **Cache** : Mettre en cache les listes d'années disponibles

### Compatibilité
- **Rétrocompatibilité** : Les filtres existants (`date_from`, `date_to`) restent fonctionnels
- **Migration** : Aucune migration de données nécessaire

### UX
- **Sélecteur d'année** : Doit être intuitif et visible
- **Valeur par défaut** : Année en cours sélectionnée par défaut
- **Combinaison de filtres** : Possibilité de combiner année + dépôt + statut

## 📝 Plan d'Implémentation Recommandé

### Phase 1 : Inventaires (Priorité Haute)
1. ✅ Ajout du filtre année dans `sessions_list()`
2. ✅ Modification du template avec sélecteur d'année
3. ✅ Nouvelle route `sessions_by_year()` pour vue consolidée
4. ✅ Template de vue annuelle
5. ✅ Export Excel annuel

### Phase 2 : Commandes Commerciales (Priorité Moyenne)
1. Ajout du filtre année
2. Dashboard annuel des commandes
3. Statistiques de validation par année

### Phase 3 : Autres Modules (Priorité Basse)
1. Réceptions
2. Forecasts
3. Autres modules selon besoins

## 🔧 Exemple de Code Complet

### Modification de `inventaires.py`

```python
@inventaires_bp.route('/sessions')
@login_required
def sessions_list():
    """Liste des sessions d'inventaire avec pagination et optimisations"""
    if not has_permission(current_user, 'inventory.read'):
        flash('Vous n\'avez pas la permission d\'accéder à cette page', 'error')
        return redirect(url_for('index'))
    
    # ... code existant ...
    
    # NOUVEAU : Filtre par année
    year_filter = request.args.get('year', type=int)
    if year_filter:
        from sqlalchemy import extract
        query = query.filter(
            extract('year', InventorySession.session_date) == year_filter
        )
    
    # ... reste du code ...
    
    # Récupérer les années disponibles pour le sélecteur
    from sqlalchemy import extract, func
    available_years = db.session.query(
        extract('year', InventorySession.session_date).label('year')
    ).distinct().order_by('year').all()
    available_years = [y.year for y in available_years]
    
    return render_template('inventaires/sessions_list.html', 
                         sessions=sessions,
                         pagination=pagination,
                         # ... autres paramètres ...
                         year_filter=year_filter,
                         available_years=available_years)
```

## ✅ Conclusion

La gestion par année est **techniquement faisable** et **recommandée** pour améliorer l'organisation et l'analyse des données historiques. 

**Recommandation** : Commencer par le module Inventaires (Phase 1) car :
- C'est un module critique pour la gestion des stocks
- Les données historiques sont importantes pour les audits
- L'implémentation est simple (pas de modification de schéma)

**Effort estimé** : 2-3 jours de développement pour la Phase 1 (Inventaires)

