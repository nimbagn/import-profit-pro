# 📋 Guide de Test - Import/Export Excel Stock Items

## ✅ Vérifications Effectuées

### 1. Code Python
- ✅ Aucune erreur de syntaxe détectée
- ✅ Imports corrects (pandas, openpyxl, BytesIO, send_file)
- ✅ Routes bien définies (`/referentiels/stock-items/export/excel` et `/referentiels/stock-items/import`)
- ✅ Gestion des erreurs avec try/except
- ✅ Vérification des permissions

### 2. Templates HTML
- ✅ `stock_items_list.html` : Boutons ajoutés
- ✅ `stock_items_import.html` : Template créé avec interface complète
- ✅ JavaScript pour glisser-déposer fonctionnel

### 3. Fonctionnalités
- ✅ Export Excel avec filtres
- ✅ Import Excel/CSV avec validation
- ✅ Création automatique de familles
- ✅ 3 modes de traitement des articles existants (par SKU)

---

## 🧪 Tests à Effectuer

### Test 1 : Export Excel

**Étapes :**
1. Aller sur `http://localhost:5002/referentiels/stock-items`
2. Vérifier que les boutons "Importer Excel" et "Exporter Excel" sont visibles
3. Cliquer sur "Exporter Excel"
4. Vérifier que le fichier se télécharge
5. Ouvrir le fichier Excel
6. Vérifier que toutes les colonnes sont présentes :
   - SKU
   - Nom
   - Famille
   - Prix Achat (GNF)
   - Poids (kg)
   - Description
   - Stock Min Dépôt
   - Stock Min Véhicule
   - Actif
   - Date de création
   - Date de modification

**Résultat attendu :** ✅ Fichier Excel téléchargé avec tous les articles de stock

---

### Test 2 : Export avec Filtres

**Étapes :**
1. Aller sur `http://localhost:5002/referentiels/stock-items`
2. Appliquer un filtre (ex: recherche "RIZ")
3. Cliquer sur "Exporter Excel"
4. Vérifier que seuls les articles filtrés sont dans le fichier

**Résultat attendu :** ✅ Fichier Excel contient uniquement les articles filtrés

---

### Test 3 : Import Excel - Nouveaux Articles

**Étapes :**
1. Créer un fichier Excel avec les colonnes :
   - SKU
   - Nom
   - Famille
   - Prix Achat (GNF)
   - Poids (kg)
   - Stock Min Dépôt
   - Stock Min Véhicule
   - Actif
2. Aller sur `http://localhost:5002/referentiels/stock-items/import`
3. Sélectionner le fichier Excel
4. Choisir "Ignorer les articles existants"
5. Cliquer sur "Importer"
6. Vérifier que les nouveaux articles apparaissent dans la liste

**Résultat attendu :** ✅ Nouveaux articles créés avec succès

---

### Test 4 : Import Excel - Mise à Jour

**Étapes :**
1. Créer un fichier Excel avec un article existant (même SKU)
2. Modifier le prix dans le fichier Excel
3. Aller sur `http://localhost:5002/referentiels/stock-items/import`
4. Sélectionner le fichier Excel
5. Choisir "Mettre à jour les articles existants"
6. Cliquer sur "Importer"
7. Vérifier que l'article a été mis à jour

**Résultat attendu :** ✅ Article existant mis à jour avec les nouvelles valeurs

---

### Test 5 : Import Excel - Créer Nouveau

**Étapes :**
1. Créer un fichier Excel avec un article existant (même SKU)
2. Aller sur `http://localhost:5002/referentiels/stock-items/import`
3. Sélectionner le fichier Excel
4. Choisir "Créer de nouveaux articles (avec SKU modifié)"
5. Cliquer sur "Importer"
6. Vérifier qu'un nouvel article avec SKU modifié a été créé

**Résultat attendu :** ✅ Nouvel article créé avec SKU modifié (ex: "RIZ-25KG-20250101")

---

### Test 6 : Import CSV

**Étapes :**
1. Créer un fichier CSV avec les mêmes colonnes que l'Excel
2. Aller sur `http://localhost:5002/referentiels/stock-items/import`
3. Sélectionner le fichier CSV
4. Cliquer sur "Importer"
5. Vérifier que les articles sont importés

**Résultat attendu :** ✅ Articles importés depuis CSV avec succès

---

### Test 7 : Création Automatique de Familles

**Étapes :**
1. Créer un fichier Excel avec une famille qui n'existe pas
2. Aller sur `http://localhost:5002/referentiels/stock-items/import`
3. Sélectionner le fichier Excel
4. Cliquer sur "Importer"
5. Vérifier que la famille a été créée automatiquement
6. Vérifier que l'article est associé à cette famille

**Résultat attendu :** ✅ Famille créée automatiquement et article associé

---

### Test 8 : Gestion des Erreurs

**Étapes :**
1. Créer un fichier Excel sans la colonne "SKU"
2. Aller sur `http://localhost:5002/referentiels/stock-items/import`
3. Sélectionner le fichier Excel
4. Cliquer sur "Importer"
5. Vérifier qu'un message d'erreur s'affiche

**Résultat attendu :** ✅ Message d'erreur clair : "Colonne 'SKU' manquante"

---

### Test 9 : Glisser-Déposer

**Étapes :**
1. Aller sur `http://localhost:5002/referentiels/stock-items/import`
2. Glisser un fichier Excel dans la zone de dépôt
3. Vérifier que le fichier est sélectionné
4. Cliquer sur "Importer"

**Résultat attendu :** ✅ Fichier accepté par glisser-déposer

---

### Test 10 : Permissions

**Étapes :**
1. Se connecter avec un utilisateur sans permission `stock_items.create`
2. Aller sur `http://localhost:5002/referentiels/stock-items/import`
3. Vérifier qu'un message d'erreur s'affiche

**Résultat attendu :** ✅ Message d'erreur : "Vous n'avez pas la permission d'importer des articles de stock"

---

## 📝 Format Excel Exemple

Créer un fichier Excel avec cette structure :

| SKU | Nom | Famille | Prix Achat (GNF) | Poids (kg) | Stock Min Dépôt | Stock Min Véhicule | Actif |
|-----|-----|---------|------------------|------------|-----------------|-------------------|-------|
| RIZ-25KG | Riz 25 kg | Alimentaire | 200000 | 25 | 10 | 5 | Oui |
| HUILE-5L | Huile végétale 5L | Alimentaire | 15000 | 5 | 20 | 10 | Oui |
| JAVEL-1L | Javel 1L | Entretien | 5000 | 1 | 30 | 15 | Oui |

**Note :** Les colonnes peuvent être dans n'importe quel ordre et avec des noms variés :
- SKU / Sku / sku
- Nom / Name / Article / Article Name
- Famille / Family / Famille Name
- Prix Achat (GNF) / Price / Purchase Price GNF
- Poids / Weight / Unit Weight Kg / Poids (kg)
- Stock Min Dépôt / Min Stock Depot / Seuil Dépôt
- Stock Min Véhicule / Min Stock Vehicle / Seuil Véhicule
- Actif / Active / Is Active

---

## ✅ Checklist de Test

- [ ] Export Excel fonctionne
- [ ] Export avec filtres fonctionne
- [ ] Import Excel nouveaux articles fonctionne
- [ ] Import Excel mise à jour fonctionne
- [ ] Import Excel créer nouveau fonctionne
- [ ] Import CSV fonctionne
- [ ] Création automatique de familles fonctionne
- [ ] Gestion des erreurs fonctionne
- [ ] Glisser-déposer fonctionne
- [ ] Permissions fonctionnent

---

## 🐛 Problèmes Potentiels

### Problème 1 : Erreur "Module pandas not found"
**Solution :** Installer pandas : `pip install pandas openpyxl`

### Problème 2 : Erreur lors de l'import
**Solution :** Vérifier que le fichier Excel est bien formaté et contient les colonnes "SKU" et "Nom"

### Problème 3 : Articles dupliqués
**Solution :** Utiliser le mode "Mettre à jour" au lieu de "Créer nouveau"

### Problème 4 : SKU déjà existant
**Solution :** Le système identifie les articles par SKU. Si un SKU existe déjà, choisir "Mettre à jour" ou "Créer nouveau"

---

## 📊 Résultats Attendus

Après tous les tests, vous devriez avoir :
- ✅ Export Excel fonctionnel avec tous les articles de stock
- ✅ Import Excel fonctionnel avec création/mise à jour
- ✅ Interface utilisateur intuitive
- ✅ Gestion des erreurs robuste
- ✅ Permissions respectées
- ✅ Création automatique de familles

---

## 🔍 Différences avec Articles

| Aspect | Articles | Stock Items |
|--------|----------|-------------|
| Identifiant unique | Nom | SKU |
| Prix | Multi-devises (USD, EUR, GNF, XOF) | GNF uniquement |
| Catégorie/Famille | Catégorie | Famille |
| Seuils | Non | Oui (Dépôt et Véhicule) |
| Description | Non | Oui |

