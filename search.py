# search.py
# Moteur de recherche global pour Import Profit Pro

from flask import Blueprint, request, jsonify, render_template
from flask_login import login_required, current_user
from sqlalchemy import or_, and_, func, text, case
from sqlalchemy.orm import joinedload
from datetime import datetime, UTC
from decimal import Decimal
import re

from models import (
    db, SearchIndex, Article, Simulation, SimulationItem, Forecast, ForecastItem,
    StockItem, StockMovement, Depot, Vehicle, User, ChatMessage, ChatRoom,
    Reception, StockOutgoing, PriceList, Family, Region
)
from auth import has_permission

# Créer le blueprint
search_bp = Blueprint('search', __name__, url_prefix='/search')

# =========================================================
# INDEXATION DES DONNÉES
# =========================================================

def index_article(article):
    """Indexe un article"""
    content_parts = [
        article.name or '',
        article.category.name if article.category else '',
        str(article.purchase_price) if article.purchase_price else '',
        article.purchase_currency or '',
    ]
    content = ' '.join(filter(None, content_parts))
    
    keywords = f"{article.name} {article.purchase_currency}"
    
    index = SearchIndex.query.filter_by(
        entity_type='article',
        entity_id=article.id
    ).first()
    
    if not index:
        index = SearchIndex(
            entity_type='article',
            entity_id=article.id,
            title=article.name or 'Article sans nom',
            content=content,
            keywords=keywords,
            module='articles',
            url=f'/articles/{article.id}',
            search_metadata={
                'category': article.category.name if article.category else None,
                'purchase_price': str(article.purchase_price) if article.purchase_price else None,
                'currency': article.purchase_currency
            }
        )
        db.session.add(index)
    else:
        index.title = article.name or 'Article sans nom'
        index.content = content
        index.keywords = keywords
        index.updated_at = datetime.now(UTC)
    
    return index

def index_simulation(simulation):
    """Indexe une simulation avec son nom si disponible"""
    items = simulation.items or []
    article_names = [item.article.name for item in items if item.article]
    
    # Utiliser le nom de la simulation s'il existe, sinon le numéro
    simulation_name = getattr(simulation, 'name', None)
    if simulation_name and simulation_name.strip():
        title = simulation_name.strip()
        title_display = title
    else:
        title_display = f"Simulation #{simulation.id}"
        title = title_display
    
    content_parts = [
        title,
        ' '.join(article_names),
        f"Taux USD: {simulation.rate_usd}",
        f"Taux EUR: {simulation.rate_eur}",
    ]
    # Ajouter la description si elle existe
    description = getattr(simulation, 'description', None)
    if description and description.strip():
        content_parts.append(description.strip())
    
    content = ' '.join(filter(None, content_parts))
    
    keywords = f"simulation {simulation.id} {title} {' '.join(article_names)}"
    
    index = SearchIndex.query.filter_by(
        entity_type='simulation',
        entity_id=simulation.id
    ).first()
    
    if not index:
        index = SearchIndex(
            entity_type='simulation',
            entity_id=simulation.id,
            title=title_display,
            content=content,
            keywords=keywords,
            module='simulations',
            url=f'/simulations/{simulation.id}',
            search_metadata={
                'name': simulation_name,
                'rate_usd': str(simulation.rate_usd),
                'rate_eur': str(simulation.rate_eur),
                'is_completed': simulation.is_completed,
                'created_at': simulation.created_at.isoformat() if simulation.created_at else None
            }
        )
        db.session.add(index)
    else:
        index.title = title_display
        index.content = content
        index.keywords = keywords
        index.updated_at = datetime.now(UTC)
        # Mettre à jour les métadonnées avec le nom
        if index.search_metadata:
            index.search_metadata['name'] = simulation_name
        else:
            index.search_metadata = {'name': simulation_name}
    
    return index

def index_forecast(forecast):
    """Indexe une prévision"""
    items = forecast.items or []
    item_names = [item.stock_item.name if item.stock_item else '' for item in items]
    content_parts = [
        f"Prévision {forecast.id}",
        forecast.commercial_name or '',
        ' '.join(filter(None, item_names)),
    ]
    content = ' '.join(filter(None, content_parts))
    
    keywords = f"prévision forecast {forecast.commercial_name} {' '.join(filter(None, item_names))}"
    
    index = SearchIndex.query.filter_by(
        entity_type='forecast',
        entity_id=forecast.id
    ).first()
    
    if not index:
        index = SearchIndex(
            entity_type='forecast',
            entity_id=forecast.id,
            title=f"Prévision {forecast.commercial_name or f'#{forecast.id}'}",
            content=content,
            keywords=keywords,
            module='forecast',
            url=f'/forecast/{forecast.id}',
            search_metadata={
                'commercial_name': forecast.commercial_name,
                'period': forecast.period,
                'created_at': forecast.created_at.isoformat() if forecast.created_at else None
            }
        )
        db.session.add(index)
    else:
        index.title = f"Prévision {forecast.commercial_name or f'#{forecast.id}'}"
        index.content = content
        index.keywords = keywords
        index.updated_at = datetime.now(UTC)
    
    return index

def index_stock_item(stock_item):
    """Indexe un article de stock"""
    content_parts = [
        stock_item.name or '',
        stock_item.family.name if stock_item.family else '',
        stock_item.reference or '',
        stock_item.description or '',
    ]
    content = ' '.join(filter(None, content_parts))
    
    keywords = f"{stock_item.name} {stock_item.reference} {stock_item.family.name if stock_item.family else ''}"
    
    index = SearchIndex.query.filter_by(
        entity_type='stock_item',
        entity_id=stock_item.id
    ).first()
    
    if not index:
        index = SearchIndex(
            entity_type='stock_item',
            entity_id=stock_item.id,
            title=stock_item.name or 'Article sans nom',
            content=content,
            keywords=keywords,
            module='stocks',
            url=f'/referentiels/stock-items/{stock_item.id}',
            search_metadata={
                'reference': stock_item.reference,
                'family': stock_item.family.name if stock_item.family else None,
                'unit': stock_item.unit
            }
        )
        db.session.add(index)
    else:
        index.title = stock_item.name or 'Article sans nom'
        index.content = content
        index.keywords = keywords
        index.updated_at = datetime.now(UTC)
    
    return index

def index_stock_movement(movement):
    """Indexe un mouvement de stock"""
    content_parts = [
        movement.reference or '',
        movement.movement_type or '',
        movement.depot_source.name if movement.depot_source else '',
        movement.depot_destination.name if movement.depot_destination else '',
        movement.vehicle.plate_number if movement.vehicle else '',
    ]
    content = ' '.join(filter(None, content_parts))
    
    keywords = f"{movement.reference} {movement.movement_type}"
    
    index = SearchIndex.query.filter_by(
        entity_type='stock_movement',
        entity_id=movement.id
    ).first()
    
    if not index:
        index = SearchIndex(
            entity_type='stock_movement',
            entity_id=movement.id,
            title=f"Mouvement {movement.reference or f'#{movement.id}'}",
            content=content,
            keywords=keywords,
            module='stocks',
            url=f'/stocks/movements/{movement.id}',
            search_metadata={
                'reference': movement.reference,
                'movement_type': movement.movement_type,
                'created_at': movement.created_at.isoformat() if movement.created_at else None
            }
        )
        db.session.add(index)
    else:
        index.title = f"Mouvement {movement.reference or f'#{movement.id}'}"
        index.content = content
        index.keywords = keywords
        index.updated_at = datetime.now(UTC)
    
    return index

def index_vehicle(vehicle):
    """Indexe un véhicule"""
    content_parts = [
        vehicle.plate_number or '',
        vehicle.brand or '',
        vehicle.model or '',
        vehicle.chassis_number or '',
    ]
    content = ' '.join(filter(None, content_parts))
    
    keywords = f"{vehicle.plate_number} {vehicle.brand} {vehicle.model}"
    
    index = SearchIndex.query.filter_by(
        entity_type='vehicle',
        entity_id=vehicle.id
    ).first()
    
    if not index:
        index = SearchIndex(
            entity_type='vehicle',
            entity_id=vehicle.id,
            title=f"Véhicule {vehicle.plate_number or f'#{vehicle.id}'}",
            content=content,
            keywords=keywords,
            module='flotte',
            url=f'/flotte/vehicles/{vehicle.id}',
            search_metadata={
                'plate_number': vehicle.plate_number,
                'brand': vehicle.brand,
                'model': vehicle.model,
                'status': vehicle.status
            }
        )
        db.session.add(index)
    else:
        index.title = f"Véhicule {vehicle.plate_number or f'#{vehicle.id}'}"
        index.content = content
        index.keywords = keywords
        index.updated_at = datetime.now(UTC)
    
    return index

def index_chat_message(message):
    """Indexe un message de chat"""
    content = message.content or ''
    keywords = f"chat message {message.room.name if message.room else ''}"
    
    index = SearchIndex.query.filter_by(
        entity_type='chat_message',
        entity_id=message.id
    ).first()
    
    if not index:
        index = SearchIndex(
            entity_type='chat_message',
            entity_id=message.id,
            title=f"Message dans {message.room.name if message.room else 'Chat'}",
            content=content,
            keywords=keywords,
            module='chat',
            url=f'/chat/rooms/{message.room_id}/messages#{message.id}',
            search_metadata={
                'room_id': message.room_id,
                'room_name': message.room.name if message.room else None,
                'sender': message.sender.username if message.sender else None,
                'created_at': message.created_at.isoformat() if message.created_at else None
            }
        )
        db.session.add(index)
    else:
        index.title = f"Message dans {message.room.name if message.room else 'Chat'}"
        index.content = content
        index.keywords = keywords
        index.updated_at = datetime.now(UTC)
    
    return index

# =========================================================
# ROUTES DE RECHERCHE
# =========================================================

@search_bp.route('/')
@login_required
def search_page():
    """Page principale de recherche moderne"""
    try:
        # Récupérer les statistiques pour affichage
        from flask import current_app
        cache = current_app.cache if hasattr(current_app, 'cache') and current_app.cache else None
        
        stats = None
        if cache:
            stats = cache.get('search_stats')
        
        if not stats:
            total = SearchIndex.query.count()
            by_module = db.session.query(
                SearchIndex.module,
                func.count(SearchIndex.id).label('count')
            ).group_by(SearchIndex.module).all()
            
            stats = {
                'total': total,
                'by_module': {module: count for module, count in by_module}
            }
            
            if cache:
                cache.set('search_stats', stats, timeout=300)
        
        return render_template('search/global_search.html', stats=stats)
    except Exception as e:
        current_app.logger.error(f"Erreur lors du chargement de la page de recherche: {e}", exc_info=True)
        return render_template('search/global_search.html', stats={'total': 0, 'by_module': {}})

@search_bp.route('/api/search', methods=['GET', 'POST'])
@login_required
def api_search():
    """API de recherche globale moderne avec cache et optimisation"""
    try:
        if request.method == 'POST':
            data = request.get_json() or {}
            query = data.get('query', '').strip()
            modules = data.get('modules', [])
            entity_types = data.get('entity_types', [])
            limit = min(int(data.get('limit', 50)), 100)
            offset = int(data.get('offset', 0))
        else:
            query = request.args.get('q', '').strip()
            modules = request.args.getlist('modules')
            entity_types = request.args.getlist('entity_types')
            limit = min(int(request.args.get('limit', 50)), 100)
            offset = int(request.args.get('offset', 0))
        
        # Validation de la requête
        if not query or len(query) < 2:
            return jsonify({
                'results': [],
                'total': 0,
                'query': query,
                'modules': modules,
                'entity_types': entity_types,
                'message': 'La recherche doit contenir au moins 2 caractères'
            })
        
        # Vérifier le cache
        from flask import current_app
        cache = current_app.cache if hasattr(current_app, 'cache') and current_app.cache else None
        
        cache_key = None
        if cache:
            import hashlib
            cache_data = f"{query}_{sorted(modules)}_{sorted(entity_types)}_{limit}_{offset}"
            cache_key = f"search_{hashlib.md5(cache_data.encode()).hexdigest()}"
            cached_result = cache.get(cache_key)
            if cached_result:
                return jsonify(cached_result)
        
        # Construire la requête de recherche optimisée
        search_query = SearchIndex.query
        
        # Recherche améliorée avec scoring de pertinence
        # Priorité : title > keywords > content
        query_lower = query.lower()
        search_pattern = f"%{query}%"
        
        # Recherche dans title (priorité haute)
        title_match = SearchIndex.title.ilike(search_pattern)
        # Recherche dans keywords (priorité moyenne)
        keywords_match = SearchIndex.keywords.ilike(search_pattern)
        # Recherche dans content (priorité basse)
        content_match = SearchIndex.content.ilike(search_pattern)
        
        search_query = search_query.filter(
            or_(title_match, keywords_match, content_match)
        )
        
        # Filtres par module
        if modules:
            search_query = search_query.filter(SearchIndex.module.in_(modules))
        
        # Filtres par type d'entité
        if entity_types:
            search_query = search_query.filter(SearchIndex.entity_type.in_(entity_types))
        
        # Compter le total avant pagination
        total = search_query.count()
        
        # Trier par pertinence (title d'abord, puis date)
        # Utiliser une expression CASE pour prioriser les matches dans le title
        search_query = search_query.order_by(
            case(
                (SearchIndex.title.ilike(search_pattern), 1),
                else_=2
            ),
            SearchIndex.created_at.desc()
        )
        
        # Pagination
        results = search_query.offset(offset).limit(limit).all()
        
        # Formater les résultats avec scoring
        formatted_results = []
        for result in results:
            # Calculer un score de pertinence simple
            score = 0
            if query_lower in (result.title or '').lower():
                score += 10
            if query_lower in (result.keywords or '').lower():
                score += 5
            if query_lower in (result.content or '').lower():
                score += 1
            
            # Tronquer le contenu intelligemment
            content = result.content or ''
            if len(content) > 200:
                # Essayer de tronquer à un mot complet
                truncated = content[:200]
                last_space = truncated.rfind(' ')
                if last_space > 150:
                    content = truncated[:last_space] + '...'
                else:
                    content = truncated + '...'
            
            formatted_results.append({
                'id': result.id,
                'entity_type': result.entity_type,
                'entity_id': result.entity_id,
                'title': result.title or 'Sans titre',
                'content': content,
                'module': result.module,
                'url': result.url,
                'metadata': result.search_metadata or {},
                'score': score,
                'created_at': result.created_at.isoformat() if result.created_at else None,
                'updated_at': result.updated_at.isoformat() if result.updated_at else None
            })
        
        # Trier par score décroissant
        formatted_results.sort(key=lambda x: x['score'], reverse=True)
        
        response_data = {
            'results': formatted_results,
            'total': total,
            'query': query,
            'modules': modules,
            'entity_types': entity_types,
            'limit': limit,
            'offset': offset,
            'has_more': (offset + limit) < total
        }
        
        # Mettre en cache (5 minutes)
        if cache and cache_key:
            cache.set(cache_key, response_data, timeout=300)
        
        return jsonify(response_data)
    
    except Exception as e:
        current_app.logger.error(f"Erreur lors de la recherche: {e}", exc_info=True)
        return jsonify({
            'results': [],
            'total': 0,
            'error': 'Une erreur est survenue lors de la recherche',
            'query': query if 'query' in locals() else ''
        }), 500

@search_bp.route('/api/quick', methods=['GET'])
@login_required
def api_quick_search():
    """Recherche rapide (autocomplete) optimisée"""
    try:
        query = request.args.get('q', '').strip()
        limit = min(int(request.args.get('limit', 10)), 20)
        
        if not query or len(query) < 2:
            return jsonify({'suggestions': []})
        
        # Cache pour les suggestions
        from flask import current_app
        cache = current_app.cache if hasattr(current_app, 'cache') and current_app.cache else None
        
        cache_key = None
        if cache:
            import hashlib
            cache_key = f"search_quick_{hashlib.md5(f'{query}_{limit}'.encode()).hexdigest()}"
            cached = cache.get(cache_key)
            if cached:
                return jsonify(cached)
        
        # Recherche optimisée - priorité au title
        search_pattern = f"%{query}%"
        results = SearchIndex.query.filter(
            or_(
                SearchIndex.title.ilike(search_pattern),
                SearchIndex.keywords.ilike(search_pattern)
            )
        ).order_by(
            # Prioriser les matches dans le title
            case(
                (SearchIndex.title.ilike(search_pattern), 1),
                else_=2
            ),
            SearchIndex.created_at.desc()
        ).limit(limit).all()
        
        suggestions = []
        for result in results:
            suggestions.append({
                'title': result.title or 'Sans titre',
                'module': result.module,
                'url': result.url,
                'entity_type': result.entity_type,
                'icon': get_entity_icon(result.entity_type)
            })
        
        response_data = {'suggestions': suggestions}
        
        # Cache de 2 minutes pour les suggestions
        if cache and cache_key:
            cache.set(cache_key, response_data, timeout=120)
        
        return jsonify(response_data)
    
    except Exception as e:
        current_app.logger.error(f"Erreur lors de la recherche rapide: {e}", exc_info=True)
        return jsonify({'suggestions': []})

def get_entity_icon(entity_type):
    """Retourne l'icône appropriée pour un type d'entité"""
    icons = {
        'article': 'fas fa-box',
        'simulation': 'fas fa-calculator',
        'forecast': 'fas fa-chart-line',
        'stock_item': 'fas fa-warehouse',
        'stock_movement': 'fas fa-exchange-alt',
        'vehicle': 'fas fa-truck',
        'chat_message': 'fas fa-comment'
    }
    return icons.get(entity_type, 'fas fa-file')

@search_bp.route('/api/reindex', methods=['POST'])
@login_required
def api_reindex():
    """Réindexer toutes les données (admin uniquement)"""
    from flask_login import current_user
    from auth import is_admin
    if not is_admin(current_user):
        return jsonify({'error': 'Accès refusé'}), 403
    
    try:
        # Indexer les articles
        articles = Article.query.all()
        for article in articles:
            index_article(article)
        
        # Indexer les simulations
        simulations = Simulation.query.all()
        for simulation in simulations:
            index_simulation(simulation)
        
        # Indexer les prévisions
        forecasts = Forecast.query.all()
        for forecast in forecasts:
            index_forecast(forecast)
        
        # Indexer les articles de stock
        stock_items = StockItem.query.all()
        for item in stock_items:
            index_stock_item(item)
        
        # Indexer les mouvements de stock
        movements = StockMovement.query.all()
        for movement in movements:
            index_stock_movement(movement)
        
        # Indexer les véhicules
        vehicles = Vehicle.query.all()
        for vehicle in vehicles:
            index_vehicle(vehicle)
        
        # Indexer les messages de chat
        messages = ChatMessage.query.all()
        for message in messages:
            index_chat_message(message)
        
        db.session.commit()
        
        return jsonify({
            'message': 'Indexation terminée avec succès',
            'articles': len(articles),
            'simulations': len(simulations),
            'forecasts': len(forecasts),
            'stock_items': len(stock_items),
            'movements': len(movements),
            'vehicles': len(vehicles),
            'messages': len(messages)
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@search_bp.route('/api/stats', methods=['GET'])
@login_required
def api_stats():
    """Statistiques de l'index de recherche"""
    total = SearchIndex.query.count()
    
    by_module = db.session.query(
        SearchIndex.module,
        func.count(SearchIndex.id).label('count')
    ).group_by(SearchIndex.module).all()
    
    by_type = db.session.query(
        SearchIndex.entity_type,
        func.count(SearchIndex.id).label('count')
    ).group_by(SearchIndex.entity_type).all()
    
    return jsonify({
        'total': total,
        'by_module': {module: count for module, count in by_module},
        'by_type': {entity_type: count for entity_type, count in by_type}
    })

