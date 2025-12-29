# Guide de Test - Module Stocks

## 📋 Vue d'ensemble

Ce guide permet de tester toutes les améliorations apportées au module stocks (Phases 1, 2 et 3).

---

## 🔍 Phase 1 - Performance et Filtres

### 1.1 Pagination

#### Test sur `/stocks/movements`
1. Accéder à http://localhost:5002/stocks/movements
2. **Vérifier** :
   - ✅ Affichage de la pagination en bas de page (si plus de 50 mouvements)
   - ✅ Boutons "Précédent" et "Suivant" fonctionnels
   - ✅ Numéros de page cliquables
   - ✅ Sélecteur "Par page" (25/50/100/200) fonctionne
   - ✅ Le nombre total de mouvements est affiché

#### Test sur `/stocks/receptions`
1. Accéder à http://localhost:5002/stocks/receptions
2. **Vérifier** :
   - ✅ Pagination présente si plus de 50 réceptions
   - ✅ Navigation entre pages fonctionne

#### Test sur `/stocks/outgoings`
1. Accéder à http://localhost:5002/stocks/outgoings
2. **Vérifier** :
   - ✅ Pagination présente si plus de 50 sorties
   - ✅ Navigation entre pages fonctionne

#### Test sur `/stocks/returns`
1. Accéder à http://localhost:5002/stocks/returns
2. **Vérifier** :
   - ✅ Pagination présente si plus de 50 retours
   - ✅ Navigation entre pages fonctionne

### 1.2 Filtres avancés

#### Test sur `/stocks/movements`
1. Accéder à http://localhost:5002/stocks/movements
2. **Tester chaque filtre** :
   - ✅ **Recherche textuelle** : Entrer une référence, BL ou nom de fournisseur → Résultats filtrés
   - ✅ **Type** : Sélectionner "Transfert" → Seuls les transferts s'affichent
   - ✅ **Date début** : Sélectionner une date → Mouvements à partir de cette date
   - ✅ **Date fin** : Sélectionner une date → Mouvements jusqu'à cette date
   - ✅ **Article** : Sélectionner un article → Seuls les mouvements de cet article
   - ✅ **Dépôt** : Sélectionner un dépôt → Mouvements liés à ce dépôt
   - ✅ **Véhicule** : Sélectionner un véhicule → Mouvements liés à ce véhicule
   - ✅ **Utilisateur** : Sélectionner un utilisateur → Mouvements créés par cet utilisateur
3. **Tester combinaison de filtres** :
   - ✅ Appliquer plusieurs filtres simultanément → Résultats correctement filtrés
   - ✅ Cliquer sur "Réinitialiser" → Tous les filtres sont effacés
4. **Vérifier conservation des filtres** :
   - ✅ Appliquer des filtres puis changer de page → Les filtres sont conservés
   - ✅ Les filtres sont présents dans l'URL

#### Test sur `/stocks/receptions`
1. Accéder à http://localhost:5002/stocks/receptions
2. **Tester les filtres** :
   - ✅ Recherche (référence, BL, fournisseur)
   - ✅ Date début/fin
   - ✅ Dépôt
   - ✅ Fournisseur
   - ✅ Bouton "Réinitialiser" fonctionne

#### Test sur `/stocks/outgoings`
1. Accéder à http://localhost:5002/stocks/outgoings
2. **Tester les filtres** :
   - ✅ Recherche (référence, client)
   - ✅ Date début/fin
   - ✅ Dépôt
   - ✅ Véhicule
   - ✅ Client
   - ✅ Bouton "Réinitialiser" fonctionne

#### Test sur `/stocks/returns`
1. Accéder à http://localhost:5002/stocks/returns
2. **Tester les filtres** :
   - ✅ Recherche (référence, client)
   - ✅ Date début/fin
   - ✅ Dépôt
   - ✅ Véhicule
   - ✅ Client
   - ✅ Bouton "Réinitialiser" fonctionne

### 1.3 Statistiques globales

#### Test sur `/stocks/movements`
1. Accéder à http://localhost:5002/stocks/movements
2. **Vérifier** :
   - ✅ Carte "Total Mouvements" affiche le bon nombre
   - ✅ Cartes par type (Transfert, Réception, Ajustement, Inventaire) affichent les bons compteurs
   - ✅ Les statistiques sont visibles en haut de la page

---

## 📊 Phase 2 - Export Excel

### 2.1 Export Mouvements

1. Accéder à http://localhost:5002/stocks/movements
2. **Tester l'export** :
   - ✅ Cliquer sur "Exporter Excel"
   - ✅ Le fichier se télécharge (nom : `mouvements_stock_YYYYMMDD_HHMMSS.xlsx`)
   - ✅ Ouvrir le fichier Excel
   - ✅ **Vérifier** :
     - Toutes les colonnes sont présentes (Date, Référence, Type, Article, Quantité, etc.)
     - Les données correspondent aux mouvements affichés
     - La ligne de totaux est présente en bas
     - Les colonnes sont correctement formatées

3. **Tester l'export avec filtres** :
   - ✅ Appliquer des filtres (ex: type "Transfert", date spécifique)
   - ✅ Cliquer sur "Exporter Excel"
   - ✅ Le fichier contient uniquement les mouvements filtrés
   - ✅ Les totaux correspondent aux données filtrées

### 2.2 Export Réceptions

1. Accéder à http://localhost:5002/stocks/receptions
2. **Tester l'export** :
   - ✅ Cliquer sur "Exporter Excel"
   - ✅ Le fichier se télécharge (`receptions_stock_YYYYMMDD_HHMMSS.xlsx`)
   - ✅ Ouvrir le fichier Excel
   - ✅ **Vérifier** :
     - Une ligne par détail de réception
     - Colonnes : Date, Référence, Dépôt, Fournisseur, BL, Article, Quantité, Prix, Montant, etc.
     - Ligne de totaux présente
     - Formatage correct

### 2.3 Export Sorties

1. Accéder à http://localhost:5002/stocks/outgoings
2. **Tester l'export** :
   - ✅ Cliquer sur "Exporter Excel"
   - ✅ Le fichier se télécharge (`sorties_stock_YYYYMMDD_HHMMSS.xlsx`)
   - ✅ Ouvrir le fichier Excel
   - ✅ **Vérifier** :
     - Une ligne par détail de sortie
     - Colonnes : Date, Référence, Client, Téléphone, Dépôt, Véhicule, Article, Quantité, Prix, Montant, etc.
     - Ligne de totaux présente

### 2.4 Export Retours

1. Accéder à http://localhost:5002/stocks/returns
2. **Tester l'export** :
   - ✅ Cliquer sur "Exporter Excel"
   - ✅ Le fichier se télécharge (`retours_stock_YYYYMMDD_HHMMSS.xlsx`)
   - ✅ Ouvrir le fichier Excel
   - ✅ **Vérifier** :
     - Une ligne par détail de retour
     - Colonnes : Date, Référence, Client, Dépôt, Véhicule, Article, Quantité, Raison, etc.
     - Ligne de totaux présente

---

## 🎨 Phase 3 - Améliorations Visuelles

### 3.1 Graphiques Chart.js

#### Test sur `/stocks/movements`
1. Accéder à http://localhost:5002/stocks/movements
2. **Vérifier le graphique de tendance** :
   - ✅ Le graphique "Tendances des 30 derniers jours" est visible
   - ✅ Le graphique affiche plusieurs lignes (Transferts, Réceptions, Ajustements, Inventaires, Total)
   - ✅ Les couleurs sont distinctes pour chaque type
   - ✅ Le graphique est responsive (s'adapte à la taille de l'écran)
   - ✅ Passer la souris sur les points → Tooltips affichent les valeurs
   - ✅ La légende est cliquable (masquer/afficher des séries)

3. **Tester l'interactivité** :
   - ✅ Cliquer sur une série dans la légende → La série se masque/affiche
   - ✅ Zoomer/dézoomer si possible
   - ✅ Le graphique se met à jour si des filtres sont appliqués (si applicable)

### 3.2 Badges améliorés

#### Test sur `/stocks/movements`
1. Accéder à http://localhost:5002/stocks/movements
2. **Vérifier les badges de type** :
   - ✅ Badge "Transfert" : bleu avec icône `fa-exchange-alt`
   - ✅ Badge "Réception" : vert avec icône `fa-arrow-down`
   - ✅ Badge "Ajustement" : orange avec icône `fa-adjust`
   - ✅ Badge "Inventaire" : violet avec icône `fa-clipboard-check`
   - ✅ Les badges ont des dégradés et des ombres

3. **Vérifier les badges de quantité** :
   - ✅ Quantités positives (entrées) : dégradé vert avec icône `fa-arrow-up`
   - ✅ Quantités négatives (sorties) : dégradé rouge avec icône `fa-arrow-down`
   - ✅ Les badges sont lisibles et bien visibles

4. **Vérifier les indicateurs source/destination** :
   - ✅ Source : fond rouge clair avec bordure rouge à gauche
   - ✅ Destination : fond vert clair avec bordure verte à gauche
   - ✅ Icônes appropriées (warehouse, car, truck)

#### Test sur `/stocks/receptions`
1. Accéder à http://localhost:5002/stocks/receptions
2. **Vérifier les badges de statut** :
   - ✅ "Completed" : dégradé vert avec icône `fa-check-circle`
   - ✅ "Draft" : dégradé orange avec icône `fa-edit`
   - ✅ Autres statuts : dégradé rouge avec icône `fa-exclamation-circle`

#### Test sur `/stocks/outgoings`
1. Accéder à http://localhost:5002/stocks/outgoings
2. **Vérifier les badges de statut** :
   - ✅ Mêmes badges que pour les réceptions
   - ✅ Design cohérent

#### Test sur `/stocks/returns`
1. Accéder à http://localhost:5002/stocks/returns
2. **Vérifier les badges de statut** :
   - ✅ Mêmes badges que pour les réceptions
   - ✅ Design cohérent

### 3.3 Cartes statistiques améliorées

#### Test sur `/stocks/movements`
1. Accéder à http://localhost:5002/stocks/movements
2. **Vérifier les cartes statistiques** :
   - ✅ Carte "Total Mouvements" : dégradé violet avec icône
   - ✅ Cartes par type : dégradés colorés distincts
   - ✅ Icônes Font Awesome visibles
   - ✅ Ombres portées pour profondeur
   - ✅ Design responsive (s'adapte sur mobile)

---

## 🧪 Tests de Performance

### Performance générale
1. **Tester avec beaucoup de données** :
   - ✅ Charger une page avec 1000+ mouvements → La pagination fonctionne
   - ✅ Les filtres s'appliquent rapidement
   - ✅ Pas de ralentissement visible

2. **Tester l'optimisation N+1** :
   - ✅ Ouvrir les outils de développement (F12)
   - ✅ Aller dans l'onglet "Network"
   - ✅ Charger `/stocks/movements`
   - ✅ Vérifier qu'il n'y a pas de nombreuses requêtes répétitives

---

## 📱 Tests Responsive

### Test sur mobile
1. Ouvrir les outils de développement (F12)
2. Activer le mode responsive (Ctrl+Shift+M)
3. **Tester chaque page** :
   - ✅ `/stocks/movements` : Graphique et tableaux s'adaptent
   - ✅ `/stocks/receptions` : Filtres et tableaux s'adaptent
   - ✅ `/stocks/outgoings` : Interface responsive
   - ✅ `/stocks/returns` : Interface responsive

---

## ✅ Checklist finale

### Phase 1 - Performance
- [ ] Pagination fonctionne sur toutes les listes
- [ ] Filtres avancés fonctionnent correctement
- [ ] Statistiques globales s'affichent
- [ ] Performance acceptable avec beaucoup de données

### Phase 2 - Export Excel
- [ ] Export mouvements fonctionne
- [ ] Export réceptions fonctionne
- [ ] Export sorties fonctionne
- [ ] Export retours fonctionne
- [ ] Les filtres sont respectés dans les exports
- [ ] Les fichiers Excel sont correctement formatés

### Phase 3 - Améliorations Visuelles
- [ ] Graphique Chart.js s'affiche et fonctionne
- [ ] Badges améliorés sont visibles et colorés
- [ ] Cartes statistiques ont des dégradés
- [ ] Design responsive fonctionne
- [ ] Interface générale est moderne et cohérente

---

## 🐛 Problèmes connus / Notes

- Si le graphique ne s'affiche pas, vérifier que Chart.js est chargé (CDN)
- Si les exports Excel échouent, vérifier que `pandas` et `openpyxl` sont installés
- Les filtres conservent leurs valeurs dans l'URL pour faciliter le partage

---

## 📞 Support

En cas de problème lors des tests :
1. Vérifier les logs de l'application (`app.log`)
2. Vérifier la console du navigateur (F12)
3. Vérifier que toutes les dépendances sont installées (`pip install -r requirements.txt`)

