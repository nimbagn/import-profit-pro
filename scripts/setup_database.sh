#!/bin/bash

# =====================================================
# SCRIPT DE CONFIGURATION DE LA BASE DE DONNÉES
# IMPORT PROFIT PRO - MySQL
# =====================================================

echo "🚀 CONFIGURATION DE LA BASE DE DONNÉES IMPORT PROFIT PRO"
echo "============================================================"
echo "📅 Date: $(date)"
echo "============================================================"

# Vérifier si Python est installé
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 n'est pas installé"
    exit 1
fi

# Vérifier si pip est installé
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 n'est pas installé"
    exit 1
fi

# Vérifier si MySQL est installé
if ! command -v mysql &> /dev/null; then
    echo "❌ MySQL n'est pas installé"
    echo "📝 Veuillez installer MySQL et créer la base de données 'madargn'"
    exit 1
fi

# Aller dans le répertoire du projet
cd "$(dirname "$0")/.."

echo "📁 Répertoire de travail: $(pwd)"

# Activer l'environnement virtuel s'il existe
if [ -d ".venv" ]; then
    echo "🔄 Activation de l'environnement virtuel..."
    source .venv/bin/activate
    echo "✅ Environnement virtuel activé"
else
    echo "⚠️ Environnement virtuel non trouvé, utilisation de Python système"
fi

# Installer les dépendances Python
echo "📦 Installation des dépendances Python..."
pip3 install pymysql flask sqlalchemy

# Vérifier que le fichier config.py existe
if [ ! -f "config.py" ]; then
    echo "❌ Fichier config.py non trouvé"
    echo "📝 Veuillez créer le fichier config.py avec vos paramètres de base de données"
    exit 1
fi

# Vérifier que le fichier SQL existe
if [ ! -f "scripts/update_database.sql" ]; then
    echo "❌ Fichier SQL non trouvé: scripts/update_database.sql"
    exit 1
fi

# Exécuter le script Python de mise à jour
echo "🔄 Exécution du script de mise à jour de la base de données..."
python3 scripts/update_database.py

if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 CONFIGURATION TERMINÉE AVEC SUCCÈS!"
    echo "============================================================"
    echo "✅ Base de données MySQL configurée"
    echo "✅ Tables créées"
    echo "✅ Données insérées"
    echo "✅ Contraintes configurées"
    echo "============================================================"
    echo "🌐 Votre application Flask peut maintenant fonctionner!"
    echo "🚀 Pour démarrer l'application: python3 app_unified.py"
    echo "============================================================"
else
    echo ""
    echo "❌ ERREUR LORS DE LA CONFIGURATION"
    echo "============================================================"
    echo "⚠️ Veuillez vérifier:"
    echo "   - Que MySQL est en cours d'exécution"
    echo "   - Que la base de données 'madargn' existe"
    echo "   - Que les paramètres dans config.py sont corrects"
    echo "   - Que l'utilisateur MySQL a les permissions nécessaires"
    echo "============================================================"
    exit 1
fi
