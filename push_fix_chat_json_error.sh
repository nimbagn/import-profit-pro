#!/bin/bash

# Script pour pousser les corrections du module chat (parsing JSON et timeout SSE)

echo "🔄 Préparation du commit pour les corrections du module chat..."

# Ajouter les fichiers modifiés
git add chat/api.py
git add chat/sse.py
git add gunicorn.conf.py
git add templates/chat/new.html

# Ajouter les fichiers de migration PostgreSQL
git add scripts/create_chat_tables_postgresql.sql
git add GUIDE_MIGRATION_CHAT_POSTGRESQL.md
git add EXECUTER_MIGRATION_CHAT_RENDER.txt

# Vérifier s'il y a des changements
if git diff --staged --quiet; then
    echo "⚠️  Aucun changement à committer"
    exit 0
fi

# Créer le commit
git commit -m "fix(chat): Correction parsing JSON, timeout SSE et migration PostgreSQL

- Amélioration du parsing JSON dans chat/api.py pour gérer les données supplémentaires
- Extraction automatique du premier objet JSON valide
- Ajout de logs de débogage détaillés
- Correction du timeout Gunicorn pour les connexions SSE (300s)
- Amélioration de la gestion des erreurs côté client dans templates/chat/new.html
- Heartbeats SSE plus fréquents (10s au lieu de 30s)
- Ajout du script SQL PostgreSQL pour créer les tables chat (idempotent)
- Documentation complète pour la migration PostgreSQL sur Render"

echo "✅ Commit créé avec succès"

# Pousser vers le dépôt distant
echo "📤 Envoi vers le dépôt distant..."
git push origin main

if [ $? -eq 0 ]; then
    echo "✅ Changements poussés avec succès vers Git"
else
    echo "❌ Erreur lors du push. Vérifiez votre connexion et vos permissions."
    exit 1
fi

echo "🎉 Migration Git terminée avec succès !"
