#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Point d'entrée WSGI pour le déploiement en production avec Gunicorn
"""

from app import app

# Gunicorn cherchera l'objet 'app' dans ce fichier
if __name__ == "__main__":
    # Ce code ne sera exécuté que si le fichier est lancé directement
    # En production, Gunicorn utilisera directement l'objet 'app'
    app.run(host='0.0.0.0', port=5000, debug=False)

