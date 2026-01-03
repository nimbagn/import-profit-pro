#!/bin/bash
# Script pour pousser la correction de validation des dépôts dans les mouvements

cd "$(dirname "$0")"

echo "🔄 Vérification de l'état Git..."
git status

echo ""
echo "📦 Ajout des fichiers modifiés..."
git add stocks.py templates/stocks/movement_form.html

echo ""
echo "📝 Création du commit..."
git commit -m "Fix: Dépôts obligatoires et véhicules facultatifs dans mouvements

📋 MODIFICATIONS
- Dépôt Source: maintenant obligatoire (required)
- Dépôt Destination: maintenant obligatoire (required)
- Véhicule Source: reste optionnel
- Véhicule Destination: reste optionnel

✅ TEMPLATE (movement_form.html)
- Ajout de l'attribut 'required' sur from_depot_id et to_depot_id
- Ajout d'un astérisque rouge (*) pour indiquer les champs obligatoires
- Ajout de '(optionnel)' pour les champs véhicules
- Changement du texte par défaut: 'Sélectionner un dépôt' au lieu de 'Aucun dépôt'

✅ VALIDATION SERVEUR (stocks.py)
- Vérification que from_depot_id est fourni
- Vérification que to_depot_id est fourni
- Messages d'erreur clairs si les dépôts ne sont pas fournis
- Les véhicules restent facultatifs (pas de validation)

📋 FICHIERS MODIFIÉS
- templates/stocks/movement_form.html
- stocks.py (ligne 927-944)

✅ RÉSULTAT
- Les utilisateurs doivent obligatoirement sélectionner un dépôt source et destination
- Les véhicules peuvent être laissés vides
- Validation côté client (HTML5) et côté serveur"

echo ""
echo "🚀 Push vers le dépôt distant..."
git push origin main

echo ""
echo "✅ Corrections poussées avec succès!"

