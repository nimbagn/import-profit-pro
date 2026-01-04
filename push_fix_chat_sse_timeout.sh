#!/bin/bash
# Script pour pousser la correction du timeout SSE chat sur Git
# Date : 3 Janvier 2026

echo "🚀 PUSH : CORRECTION TIMEOUT SSE CHAT"
echo "======================================"
echo ""

# Ajouter les fichiers modifiés
echo "📦 Ajout des fichiers modifiés..."
git add chat/sse.py
git add gunicorn.conf.py

echo ""
echo "📋 Fichiers à commiter :"
git status --short

echo ""
echo "💾 Création du commit..."
git commit -m "fix: Correction timeout worker Gunicorn pour SSE chat

🐛 Bug corrigé :
- WORKER TIMEOUT dans chat/sse.py
- SystemExit: 1 lors des connexions SSE longues
- time.sleep() bloquait le worker Gunicorn

✅ Solution :
- Heartbeats plus fréquents (toutes les 10s au lieu de 30s)
- Déplacement de time.sleep() après l'envoi des données
- Timeout Gunicorn augmenté à 300s (5 minutes)
- Heartbeats envoyés même sans nouvelles données

📝 Fichiers modifiés :
- chat/sse.py : Heartbeats fréquents et meilleure gestion du sleep
- gunicorn.conf.py : Timeout augmenté à 300s

🎯 Objectif :
Éviter que Gunicorn tue les workers lors des connexions SSE longues"

echo ""
echo "📤 Push vers le dépôt distant..."
git push origin main

echo ""
echo "✅ Push terminé avec succès !"
echo ""

