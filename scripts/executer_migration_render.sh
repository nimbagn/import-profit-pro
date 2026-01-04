#!/bin/bash
# Script pour exécuter la migration PostgreSQL sur Render
# Usage: ./scripts/executer_migration_render.sh

set -e

echo "=========================================="
echo "Migration PostgreSQL pour Render"
echo "=========================================="

# Vérifier si DATABASE_URL est définie
if [ -z "$DATABASE_URL" ]; then
    echo "❌ Erreur: DATABASE_URL n'est pas définie"
    echo ""
    echo "Pour définir DATABASE_URL:"
    echo "  export DATABASE_URL='postgresql://user:password@host:port/database'"
    echo ""
    echo "OU utilisez l'éditeur SQL de Render (recommandé):"
    echo "  1. Allez dans votre base PostgreSQL → Connect → SQL Editor"
    echo "  2. Copiez-collez le contenu de scripts/migration_postgresql_render_complete.sql"
    echo "  3. Exécutez le script"
    exit 1
fi

# Vérifier si le fichier SQL existe
SQL_FILE="scripts/migration_postgresql_render_complete.sql"
if [ ! -f "$SQL_FILE" ]; then
    echo "❌ Erreur: Fichier $SQL_FILE introuvable"
    exit 1
fi

echo "✅ DATABASE_URL trouvée"
echo "✅ Fichier SQL trouvé: $SQL_FILE"
echo ""
echo "Exécution de la migration..."
echo ""

# Exécuter la migration
psql "$DATABASE_URL" -f "$SQL_FILE"

if [ $? -eq 0 ]; then
    echo ""
    echo "=========================================="
    echo "✅ Migration terminée avec succès!"
    echo "=========================================="
else
    echo ""
    echo "=========================================="
    echo "❌ Erreur lors de la migration"
    echo "=========================================="
    exit 1
fi

