#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Point d'entrée WSGI pour le déploiement en production avec Gunicorn
"""

import os

# Import de l'application Flask
from app import app

# Gunicorn cherchera l'objet 'app' dans ce fichier
# C'est ce qui sera utilisé en production
# Note: render.yaml utilise 'wsgi:app', donc on expose 'app'
# (application est aussi disponible pour compatibilité)

# Pour les tests locaux uniquement
if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

