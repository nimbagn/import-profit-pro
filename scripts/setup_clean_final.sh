#!/bin/bash

# =====================================================
# SCRIPT DE NETTOYAGE ET CONFIGURATION FINALE
# IMPORT PROFIT PRO - MySQL
# =====================================================

echo "🚀 NETTOYAGE ET CONFIGURATION FINALE DE LA BASE DE DONNÉES"
echo "============================================================"

# Aller dans le répertoire du projet
cd "$(dirname "$0")/.."

# Paramètres de configuration fixes
DB_HOST="127.0.0.1"
DB_PORT="3306"
DB_NAME="madargn"
DB_USER="madar"
DB_PASSWORD="Satina12345"

echo "🗄️ Base de données: $DB_NAME"
echo "🌐 Serveur: $DB_HOST:$DB_PORT"
echo "👤 Utilisateur: $DB_USER"

# Tester la connexion
echo "🔄 Test de connexion à la base de données..."
mysql -h "$DB_HOST" -P "$DB_PORT" -u "$DB_USER" -p"$DB_PASSWORD" -e "USE $DB_NAME; SHOW TABLES;" 2>/dev/null

if [ $? -eq 0 ]; then
    echo "✅ Connexion à la base de données réussie"
else
    echo "❌ Impossible de se connecter à la base de données"
    echo "Vérifiez vos paramètres de configuration"
    exit 1
fi

# Exécuter le script SQL de nettoyage et configuration
echo "🔄 Nettoyage et configuration de la base de données..."
mysql -h "$DB_HOST" -P "$DB_PORT" -u "$DB_USER" -p"$DB_PASSWORD" "$DB_NAME" < scripts/clean_and_setup.sql

if [ $? -eq 0 ]; then
    echo "✅ Script SQL exécuté avec succès"
else
    echo "❌ Erreur lors de l'exécution du script SQL"
    exit 1
fi

# Vérifier les résultats
echo "🔍 Vérification des résultats..."
mysql -h "$DB_HOST" -P "$DB_PORT" -u "$DB_USER" -p"$DB_PASSWORD" "$DB_NAME" -e "
SELECT 'users' as table_name, COUNT(*) as count FROM users
UNION ALL
SELECT 'roles', COUNT(*) FROM roles
UNION ALL
SELECT 'categories', COUNT(*) FROM categories
UNION ALL
SELECT 'articles', COUNT(*) FROM articles
UNION ALL
SELECT 'depots', COUNT(*) FROM depots
UNION ALL
SELECT 'vehicles', COUNT(*) FROM vehicles
UNION ALL
SELECT 'currencies', COUNT(*) FROM currencies
UNION ALL
SELECT 'exchange_rates', COUNT(*) FROM exchange_rates
UNION ALL
SELECT 'regions', COUNT(*) FROM regions;
"

echo ""
echo "🎉 CONFIGURATION TERMINÉE AVEC SUCCÈS!"
echo "============================================================"
echo "✅ Base de données nettoyée"
echo "✅ Tables créées"
echo "✅ Données insérées"
echo "✅ Contraintes configurées"
echo "============================================================"
echo "🌐 Votre application Flask peut maintenant fonctionner!"
echo "🚀 Pour démarrer: python3 app_unified.py"
echo "============================================================"
