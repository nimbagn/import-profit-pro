# Configuration Gunicorn pour Render
# Optimisée pour les connexions SSE (Server-Sent Events)

# Nombre de workers
workers = 2

# Timeout augmenté pour les connexions SSE (5 minutes)
# Les connexions SSE peuvent rester ouvertes longtemps
timeout = 300

# Keep-alive pour les connexions longues
keepalive = 65

# Worker class - utiliser sync pour compatibilité maximale
worker_class = 'sync'

# Max requests - recycler les workers après N requêtes pour éviter les fuites mémoire
max_requests = 1000
max_requests_jitter = 50

# Logging
accesslog = '-'
errorlog = '-'
loglevel = 'info'

# Graceful timeout pour l'arrêt propre
graceful_timeout = 30

# Preload app pour meilleure performance
preload_app = True
