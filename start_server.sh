#!/bin/bash
# Script de démarrage du serveur Flask avec gestion des erreurs

echo "🚀 Démarrage du serveur Flask..."
echo "=================================="

# Arrêter les processus existants
echo "1️⃣  Arrêt des processus existants..."
lsof -ti:5002 | xargs kill -9 2>/dev/null
pkill -f "python.*app.py" 2>/dev/null
sleep 2

# Vérifier que le port est libre
if lsof -ti:5002 > /dev/null 2>&1; then
    echo "⚠️  Le port 5002 est encore utilisé"
    echo "   Arrêt forcé..."
    kill -9 $(lsof -ti:5002) 2>/dev/null
    sleep 2
fi

echo "✅ Port 5002 libéré"

# Vérifier la configuration MySQL
echo ""
echo "2️⃣  Vérification de la configuration..."
python3 -c "
from config import DB_NAME, DB_USER, DB_PASSWORD_RAW, DB_HOST, DB_PORT
print(f'   Base de données: {DB_NAME}')
print(f'   Serveur: {DB_HOST}:{DB_PORT}')
print(f'   Utilisateur: {DB_USER}')
print(f'   Mot de passe: {\"*\" * len(DB_PASSWORD_RAW) if DB_PASSWORD_RAW else \"Non défini\"}')
"

# Démarrer le serveur
echo ""
echo "3️⃣  Démarrage du serveur Flask..."
echo "   URL: http://localhost:5002"
echo "   Appuyez sur Ctrl+C pour arrêter"
echo ""

python3 app.py

