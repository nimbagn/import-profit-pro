#!/bin/bash

# =====================================================
# Script d'exécution automatique de l'initialisation
# =====================================================

echo "=========================================="
echo "🚀 INITIALISATION COMPLÈTE DE LA BASE DE DONNÉES"
echo "=========================================="
echo ""

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Vérifier que MySQL est accessible
echo "📋 Vérification de l'accès MySQL..."
if ! command -v mysql &> /dev/null; then
    echo -e "${RED}❌ MySQL n'est pas installé ou n'est pas dans le PATH${NC}"
    exit 1
fi
echo -e "${GREEN}✅ MySQL trouvé${NC}"
echo ""

# Demander les identifiants MySQL
read -p "🔐 Nom d'utilisateur MySQL (root): " MYSQL_USER
MYSQL_USER=${MYSQL_USER:-root}

read -sp "🔐 Mot de passe MySQL: " MYSQL_PASS
echo ""

# Nom de la base de données (détection automatique depuis config.py ou demande)
if [ -f "config.py" ]; then
    # Essayer de détecter depuis config.py
    DETECTED_DB=$(grep -E "DB_NAME\s*=" config.py | head -1 | sed -E "s/.*DB_NAME\s*=\s*env\([^,]*,\s*[\"']([^\"']+)[\"'].*/\1/" | tr -d '"' | tr -d "'")
    if [ -n "$DETECTED_DB" ] && [ "$DETECTED_DB" != "None" ]; then
        DB_NAME="$DETECTED_DB"
        echo -e "${GREEN}✅ Base de données détectée depuis config.py: ${DB_NAME}${NC}"
    else
        DB_NAME="madargn"
        echo -e "${YELLOW}⚠️  Utilisation de la base par défaut: ${DB_NAME}${NC}"
    fi
else
    DB_NAME="madargn"
    echo -e "${YELLOW}⚠️  Utilisation de la base par défaut: ${DB_NAME}${NC}"
fi

# Demander confirmation ou modification
read -p "📦 Nom de la base de données [$DB_NAME]: " USER_DB_NAME
DB_NAME=${USER_DB_NAME:-$DB_NAME}

echo ""
echo "📦 Base de données: ${DB_NAME}"
echo "👤 Utilisateur: ${MYSQL_USER}"
echo ""

# Vérifier que la base existe
echo "🔍 Vérification de l'existence de la base de données..."
if mysql -u "$MYSQL_USER" -p"$MYSQL_PASS" -e "USE $DB_NAME" 2>/dev/null; then
    echo -e "${GREEN}✅ Base de données '$DB_NAME' trouvée${NC}"
else
    echo -e "${YELLOW}⚠️  La base de données '$DB_NAME' n'existe pas${NC}"
    read -p "Voulez-vous la créer ? (o/n): " CREATE_DB
    if [[ "$CREATE_DB" == "o" || "$CREATE_DB" == "O" ]]; then
        mysql -u "$MYSQL_USER" -p"$MYSQL_PASS" -e "CREATE DATABASE IF NOT EXISTS $DB_NAME CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
        echo -e "${GREEN}✅ Base de données créée${NC}"
    else
        echo -e "${RED}❌ Impossible de continuer sans la base de données${NC}"
        exit 1
    fi
fi

echo ""
echo "=========================================="
echo "⚠️  ATTENTION: Ce script va SUPPRIMER toutes les données existantes"
echo "=========================================="
read -p "Voulez-vous continuer ? (o/n): " CONFIRM

if [[ "$CONFIRM" != "o" && "$CONFIRM" != "O" ]]; then
    echo -e "${YELLOW}❌ Opération annulée${NC}"
    exit 0
fi

echo ""
echo "🔄 Exécution du script d'initialisation..."
echo ""

# Exécuter le script SQL
if mysql -u "$MYSQL_USER" -p"$MYSQL_PASS" "$DB_NAME" < INITIALISATION_COMPLETE.sql 2>&1; then
    echo ""
    echo -e "${GREEN}=========================================="
    echo "✅ INITIALISATION TERMINÉE AVEC SUCCÈS"
    echo "==========================================${NC}"
    echo ""
    echo "📊 Vérification des données créées..."
    echo ""
    
    # Afficher un résumé
    mysql -u "$MYSQL_USER" -p"$MYSQL_PASS" "$DB_NAME" -e "
        SELECT 'Rôles' as Type, COUNT(*) as Nombre FROM roles
        UNION ALL
        SELECT 'Utilisateurs', COUNT(*) FROM users
        UNION ALL
        SELECT 'Catégories', COUNT(*) FROM categories
        UNION ALL
        SELECT 'Articles', COUNT(*) FROM articles;
    " 2>/dev/null
    
    echo ""
    echo -e "${GREEN}✅ Utilisateur admin créé${NC}"
    echo "   Username: admin"
    echo "   Password: admin123"
    echo ""
    echo "🌐 URL de connexion: http://localhost:5002/auth/login"
    echo ""
    echo "🔄 N'oubliez pas de redémarrer Flask après l'initialisation !"
    echo ""
else
    echo ""
    echo -e "${RED}=========================================="
    echo "❌ ERREUR LORS DE L'INITIALISATION"
    echo "==========================================${NC}"
    echo ""
    echo "Vérifiez les erreurs ci-dessus et réessayez."
    exit 1
fi

