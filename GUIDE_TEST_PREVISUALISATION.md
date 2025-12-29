# 🧪 GUIDE DE TEST - PRÉVISUALISATION ET EXPORT PDF/EXCEL

## ✅ Vérifications Effectuées

### Routes Disponibles
- ✅ `/simulations/<id>/preview` - Prévisualisation simulation
- ✅ `/simulations/<id>/pdf` - Export PDF simulation
- ✅ `/simulations/<id>/excel` - Export Excel simulation
- ✅ `/forecast/<id>/preview` - Prévisualisation prévision
- ✅ `/forecast/<id>/pdf` - Export PDF prévision
- ✅ `/forecast/<id>/excel` - Export Excel prévision
- ✅ `/stocks/summary/preview` - Prévisualisation stock
- ✅ `/stocks/summary/pdf` - Export PDF stock
- ✅ `/stocks/summary/excel` - Export Excel stock

### Templates Créés
- ✅ `templates/simulation_preview.html`
- ✅ `templates/forecast_preview.html`
- ✅ `templates/stocks/stock_preview.html`

---

## 🧪 Tests à Effectuer

### 1. Test Simulation

#### Étape 1 : Accéder à une simulation
1. Se connecter à l'application (http://localhost:5002)
2. Aller sur `/simulations`
3. Cliquer sur une simulation existante (ex: Simulation #1)

#### Étape 2 : Prévisualiser
1. Sur la page de détail, cliquer sur **"Prévisualiser"**
2. Vérifier que la page de prévisualisation s'affiche avec :
   - ✅ En-tête avec titre et boutons d'export
   - ✅ Informations générales (ID, date, taux de change)
   - ✅ Tableau des articles avec calculs
   - ✅ Résumé financier avec cartes colorées

#### Étape 3 : Exporter PDF
1. Cliquer sur **"Exporter PDF"** (bouton rouge)
2. Vérifier que le PDF se télécharge
3. Ouvrir le PDF et vérifier :
   - ✅ En-tête avec logo "IMPORT PROFIT PRO"
   - ✅ Informations de la simulation
   - ✅ Tableau des articles
   - ✅ Résumé financier
   - ✅ Pied de page avec date et numéro de page

#### Étape 4 : Exporter Excel
1. Retourner à la prévisualisation
2. Cliquer sur **"Exporter Excel"** (bouton vert)
3. Vérifier que le fichier .xlsx se télécharge
4. Ouvrir le fichier Excel et vérifier :
   - ✅ Feuille "Simulation" avec les données
   - ✅ Tableau avec en-têtes
   - ✅ Ligne de total

---

### 2. Test Prévision

#### Étape 1 : Accéder à une prévision
1. Aller sur `/forecast`
2. Cliquer sur une prévision existante

#### Étape 2 : Prévisualiser
1. Cliquer sur **"Prévisualiser"**
2. Vérifier que la page s'affiche avec :
   - ✅ Informations de la prévision (nom, période, commercial)
   - ✅ Tableau prévision vs réalisation
   - ✅ Calculs d'écarts et taux de réalisation
   - ✅ Résumé avec cartes

#### Étape 3 : Exporter PDF
1. Cliquer sur **"Exporter PDF"**
2. Vérifier le téléchargement et le contenu du PDF

#### Étape 4 : Exporter Excel
1. Cliquer sur **"Exporter Excel"**
2. Vérifier le téléchargement et le contenu du fichier Excel

---

### 3. Test Stock

#### Étape 1 : Accéder au récapitulatif de stock
1. Aller sur `/stocks/summary`
2. Appliquer des filtres si nécessaire (période, dépôt, article)

#### Étape 2 : Prévisualiser
1. Cliquer sur **"Prévisualiser"**
2. Vérifier que la page s'affiche avec :
   - ✅ Informations du rapport (date, période, dépôt)
   - ✅ Tableau des stocks par article
   - ✅ Valeurs calculées
   - ✅ Résumé avec statistiques

#### Étape 3 : Exporter PDF
1. Cliquer sur **"Exporter PDF"**
2. Vérifier le téléchargement et le contenu

#### Étape 4 : Exporter Excel
1. Cliquer sur **"Exporter Excel"**
2. Vérifier le téléchargement et le contenu

---

## ✅ Checklist de Vérification

### Interface
- [ ] Les boutons "Prévisualiser" sont visibles sur les pages de détail
- [ ] Les prévisualisations s'affichent correctement
- [ ] Les tableaux sont lisibles et bien formatés
- [ ] Les cartes de résumé affichent les bonnes valeurs
- [ ] Les couleurs sont cohérentes (vert = positif, rouge = négatif)

### Export PDF
- [ ] Les PDFs se téléchargent correctement
- [ ] Les PDFs contiennent toutes les informations
- [ ] Le formatage est correct (montants avec espaces)
- [ ] L'en-tête et le pied de page sont présents

### Export Excel
- [ ] Les fichiers Excel se téléchargent correctement
- [ ] Les fichiers s'ouvrent dans Excel/LibreOffice
- [ ] Les tableaux sont bien formatés
- [ ] Les lignes de total sont présentes

### Responsive
- [ ] Les prévisualisations sont lisibles sur mobile
- [ ] Les tableaux sont scrollables horizontalement si nécessaire
- [ ] Les boutons sont accessibles sur tous les écrans

---

## 🐛 Problèmes Potentiels et Solutions

### Problème : Erreur 404 sur la prévisualisation
**Solution** : Vérifier que la simulation/prévision/stock existe dans la base de données

### Problème : PDF vide ou mal formaté
**Solution** : Vérifier que les données sont bien chargées (items non vides)

### Problème : Excel ne s'ouvre pas
**Solution** : Vérifier que pandas et openpyxl sont installés (`pip install pandas openpyxl`)

### Problème : Boutons non visibles
**Solution** : Vérifier que l'utilisateur est connecté et a les permissions nécessaires

---

## 📝 Notes

- Les prévisualisations utilisent le même style que le reste de l'application
- Les exports conservent les filtres appliqués (pour le stock)
- Les calculs sont effectués côté serveur pour garantir la précision
- Les fichiers sont nommés avec la date/heure pour éviter les conflits

---

**Status** : ✅ **PRÊT POUR LES TESTS**

**URL de test** : http://localhost:5002

