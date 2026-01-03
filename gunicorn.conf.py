# Configuration Gunicorn pour Render
# Augmente le timeout pour les connexions SSE (Server-Sent Events)

import multiprocessing

# Workers
workers = 2
worker_class = "sync"
worker_connections = 1000

# Timeout pour les connexions longues (SSE, WebSocket, etc.)
# Par défaut Gunicorn a un timeout de 30 secondes
# On l'augmente à 300 secondes (5 minutes) pour les connexions SSE
# Les heartbeats sont envoyés toutes les 10 secondes pour maintenir la connexion active
timeout = 300
graceful_timeout = 30
keepalive = 5

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"

# Performance
max_requests = 1000
max_requests_jitter = 50
preload_app = True

# Bind - sera défini dans Procfile avec $PORT
# bind sera défini via --bind dans Procfile

