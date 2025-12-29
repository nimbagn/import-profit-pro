# chat/__init__.py
# Module Chat Interne - Import Profit Pro

from flask import Blueprint

chat_bp = Blueprint('chat', __name__, url_prefix='/chat')

from . import routes, api, sse

