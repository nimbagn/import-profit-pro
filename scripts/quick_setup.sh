#!/bin/bash

# =====================================================
# SCRIPT RAPIDE DE CONFIGURATION DE LA BASE DE DONNÉES
# IMPORT PROFIT PRO - MySQL
# =====================================================

echo "🚀 CONFIGURATION RAPIDE DE LA BASE DE DONNÉES"
echo "=============================================="

# Aller dans le répertoire du projet
cd "$(dirname "$0")/.."

# Vérifier que MySQL est installé
if ! command -v mysql &> /dev/null; then
    echo "❌ MySQL n'est pas installé"
    exit 1
fi

# Lire les paramètres de configuration
if [ -f "config.py" ]; then
    echo "📄 Fichier config.py trouvé"
    
    # Extraire les paramètres de configuration (méthode simple)
    DB_HOST=$(grep "DB_HOST" config.py | cut -d"'" -f2)
    DB_PORT=$(grep "DB_PORT" config.py | cut -d"=" -f2 | tr -d ' ')
    DB_NAME=$(grep "DB_NAME" config.py | cut -d"'" -f2)
    DB_USER=$(grep "DB_USER" config.py | cut -d"'" -f2)
    
    echo "🗄️ Base de données: $DB_NAME"
    echo "🌐 Serveur: $DB_HOST:$DB_PORT"
else
    echo "❌ Fichier config.py non trouvé"
    exit 1
fi

# Demander le mot de passe MySQL
echo "🔐 Veuillez entrer le mot de passe MySQL pour l'utilisateur $DB_USER:"
read -s DB_PASSWORD

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

# Exécuter le script SQL
echo "🔄 Exécution du script SQL..."
mysql -h "$DB_HOST" -P "$DB_PORT" -u "$DB_USER" -p"$DB_PASSWORD" "$DB_NAME" < scripts/simple_database_setup.sql

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
echo "=============================================="
echo "✅ Base de données configurée"
echo "✅ Tables créées"
echo "✅ Données insérées"
echo "=============================================="
echo "🌐 Votre application Flask peut maintenant fonctionner!"
echo "🚀 Pour démarrer: python3 app_unified.py"
echo "=============================================="
