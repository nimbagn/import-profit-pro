# 📋 Guide de Test - Import/Export Excel Articles

## ✅ Vérifications Effectuées

### 1. Code Python
- ✅ Aucune erreur de syntaxe détectée
- ✅ Imports corrects (pandas, openpyxl, BytesIO, send_file)
- ✅ Routes bien définies (`/articles/export/excel` et `/articles/import`)
- ✅ Gestion des erreurs avec try/except
- ✅ Vérification des permissions

### 2. Templates HTML
- ✅ `articles_unified.html` : Boutons ajoutés
- ✅ `articles_import.html` : Template créé avec interface complète
- ✅ JavaScript pour glisser-déposer fonctionnel

### 3. Fonctionnalités
- ✅ Export Excel avec filtres
- ✅ Import Excel/CSV avec validation
- ✅ Création automatique de catégories
- ✅ 3 modes de traitement des articles existants

---

## 🧪 Tests à Effectuer

### Test 1 : Export Excel

**Étapes :**
1. Aller sur `http://localhost:5002/articles`
2. Vérifier que les boutons "Importer Excel" et "Exporter Excel" sont visibles
3. Cliquer sur "Exporter Excel"
4. Vérifier que le fichier se télécharge
5. Ouvrir le fichier Excel
6. Vérifier que toutes les colonnes sont présentes :
   - ID
   - Nom
   - Catégorie
   - Prix d'achat
   - Devise
   - Poids (kg)
   - Actif
   - Date de création
   - Date de modification

**Résultat attendu :** ✅ Fichier Excel téléchargé avec tous les articles

---

### Test 2 : Export avec Filtres

**Étapes :**
1. Aller sur `http://localhost:5002/articles`
2. Appliquer un filtre (ex: recherche "Riz")
3. Cliquer sur "Exporter Excel"
4. Vérifier que seuls les articles filtrés sont dans le fichier

**Résultat attendu :** ✅ Fichier Excel contient uniquement les articles filtrés

---

### Test 3 : Import Excel - Nouveaux Articles

**Étapes :**
1. Créer un fichier Excel avec les colonnes :
   - Nom
   - Catégorie
   - Prix
   - Devise
   - Poids (kg)
   - Actif
2. Aller sur `http://localhost:5002/articles/import`
3. Sélectionner le fichier Excel
4. Choisir "Ignorer les articles existants"
5. Cliquer sur "Importer"
6. Vérifier que les nouveaux articles apparaissent dans la liste

**Résultat attendu :** ✅ Nouveaux articles créés avec succès

---

### Test 4 : Import Excel - Mise à Jour

**Étapes :**
1. Créer un fichier Excel avec un article existant (même nom)
2. Modifier le prix dans le fichier Excel
3. Aller sur `http://localhost:5002/articles/import`
4. Sélectionner le fichier Excel
5. Choisir "Mettre à jour les articles existants"
6. Cliquer sur "Importer"
7. Vérifier que l'article a été mis à jour

**Résultat attendu :** ✅ Article existant mis à jour avec les nouvelles valeurs

---

### Test 5 : Import Excel - Créer Nouveau

**Étapes :**
1. Créer un fichier Excel avec un article existant (même nom)
2. Aller sur `http://localhost:5002/articles/import`
3. Sélectionner le fichier Excel
4. Choisir "Créer de nouveaux articles (avec nom modifié)"
5. Cliquer sur "Importer"
6. Vérifier qu'un nouvel article avec nom modifié a été créé

**Résultat attendu :** ✅ Nouvel article créé avec nom modifié (ex: "Riz 25 kg (Import 20250101)")

---

### Test 6 : Import CSV

**Étapes :**
1. Créer un fichier CSV avec les mêmes colonnes que l'Excel
2. Aller sur `http://localhost:5002/articles/import`
3. Sélectionner le fichier CSV
4. Cliquer sur "Importer"
5. Vérifier que les articles sont importés

**Résultat attendu :** ✅ Articles importés depuis CSV avec succès

---

### Test 7 : Création Automatique de Catégories

**Étapes :**
1. Créer un fichier Excel avec une catégorie qui n'existe pas
2. Aller sur `http://localhost:5002/articles/import`
3. Sélectionner le fichier Excel
4. Cliquer sur "Importer"
5. Vérifier que la catégorie a été créée automatiquement
6. Vérifier que l'article est associé à cette catégorie

**Résultat attendu :** ✅ Catégorie créée automatiquement et article associé

---

### Test 8 : Gestion des Erreurs

**Étapes :**
1. Créer un fichier Excel sans la colonne "Nom"
2. Aller sur `http://localhost:5002/articles/import`
3. Sélectionner le fichier Excel
4. Cliquer sur "Importer"
5. Vérifier qu'un message d'erreur s'affiche

**Résultat attendu :** ✅ Message d'erreur clair : "Colonne 'Nom' ou 'Name' manquante"

---

### Test 9 : Glisser-Déposer

**Étapes :**
1. Aller sur `http://localhost:5002/articles/import`
2. Glisser un fichier Excel dans la zone de dépôt
3. Vérifier que le fichier est sélectionné
4. Cliquer sur "Importer"

**Résultat attendu :** ✅ Fichier accepté par glisser-déposer

---

### Test 10 : Permissions

**Étapes :**
1. Se connecter avec un utilisateur sans permission `articles.create`
2. Aller sur `http://localhost:5002/articles/import`
3. Vérifier qu'un message d'erreur s'affiche

**Résultat attendu :** ✅ Message d'erreur : "Vous n'avez pas la permission d'importer des articles"

---

## 📝 Format Excel Exemple

Créer un fichier Excel avec cette structure :

| Nom | Catégorie | Prix | Devise | Poids (kg) | Actif |
|-----|-----------|------|--------|------------|-------|
| Riz 25 kg | Alimentaire | 200000 | GNF | 25 | Oui |
| Huile végétale 5L | Alimentaire | 15000 | GNF | 5 | Oui |
| Javel 1L | Entretien | 5000 | GNF | 1 | Oui |

**Note :** Les colonnes peuvent être dans n'importe quel ordre et avec des noms variés :
- Nom / Name / Article / Article Name
- Catégorie / Category / Categorie Name
- Prix / Price / Purchase Price / Prix d'achat
- Devise / Currency / Purchase Currency / Monnaie
- Poids / Weight / Unit Weight Kg / Poids (kg)
- Actif / Active / Is Active

---

## ✅ Checklist de Test

- [ ] Export Excel fonctionne
- [ ] Export avec filtres fonctionne
- [ ] Import Excel nouveaux articles fonctionne
- [ ] Import Excel mise à jour fonctionne
- [ ] Import Excel créer nouveau fonctionne
- [ ] Import CSV fonctionne
- [ ] Création automatique de catégories fonctionne
- [ ] Gestion des erreurs fonctionne
- [ ] Glisser-déposer fonctionne
- [ ] Permissions fonctionnent

---

## 🐛 Problèmes Potentiels

### Problème 1 : Erreur "Module pandas not found"
**Solution :** Installer pandas : `pip install pandas openpyxl`

### Problème 2 : Erreur lors de l'import
**Solution :** Vérifier que le fichier Excel est bien formaté et contient la colonne "Nom"

### Problème 3 : Articles dupliqués
**Solution :** Utiliser le mode "Mettre à jour" au lieu de "Créer nouveau"

---

## 📊 Résultats Attendus

Après tous les tests, vous devriez avoir :
- ✅ Export Excel fonctionnel avec tous les articles
- ✅ Import Excel fonctionnel avec création/mise à jour
- ✅ Interface utilisateur intuitive
- ✅ Gestion des erreurs robuste
- ✅ Permissions respectées

