#!/bin/bash
# Script pour pousser les corrections PostgreSQL sur Git

cd /Users/dantawi/Documents/mini_flask_import_profitability

echo "📦 Ajout du fichier corrigé..."
git add app.py

echo "💾 Création du commit..."
git commit -m "fix: Correction erreurs PostgreSQL enum order_status et gestion transactions

- Remplacement 'cancelled' par 'rejected' (valeur valide de l'enum order_status)
- Ajout statistique orders_completed pour les commandes complétées
- Ajout db.session.rollback() dans tous les blocs except pour éviter transactions en échec
- Amélioration gestion erreurs avec SQLAlchemyError
- Ajout imports or_ et and_ dans section RH
- Correction erreur: invalid input value for enum order_status: cancelled
- Correction erreur: current transaction is aborted"

echo "🚀 Push vers origin/main..."
git push origin main

echo "✅ Corrections poussées avec succès!"

