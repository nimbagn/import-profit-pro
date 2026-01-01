#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Application Import Profit Pro - Version Nettoyée et Moderne
Application complète pour la gestion de la rentabilité des importations
"""

import os
import sys
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_from_directory
from flask_login import login_required, current_user
from datetime import datetime, date, UTC
from decimal import Decimal
import json
from dotenv import load_dotenv

# Charger les variables d'environnement depuis .env (si disponible)
try:
    load_dotenv()
except PermissionError:
    print("⚠️  Impossible de lire le fichier .env (permission refusée)")
    print("   Le serveur utilisera les valeurs par défaut de config.py")
except Exception as e:
    print(f"⚠️  Erreur lors du chargement de .env: {e}")
    print("   Le serveur utilisera les valeurs par défaut de config.py")

# Configuration de l'application
app = Flask(__name__)

# Utiliser la configuration depuis config.py (qui lit les variables d'environnement)
from config import Config
app.config.from_object(Config)

# Vérifier que SECRET_KEY est bien défini
if not app.config.get('SECRET_KEY') or app.config['SECRET_KEY'] in ['import_profit_pro_2024', 'import_profit_pro_2024_modern']:
    import secrets
    generated_key = secrets.token_urlsafe(32)
    app.config['SECRET_KEY'] = generated_key
    print(f"⚠️  ATTENTION: Secret key générée automatiquement.")
    print(f"⚠️  Créez un fichier .env avec SECRET_KEY pour la production!")
    print(f"⚠️  Exécutez: python3 create_env.py")

# Configuration de la base de données
# Utiliser la configuration depuis config.py qui respecte DATABASE_URL
from config import SQLALCHEMY_DATABASE_URI, SQLALCHEMY_ENGINE_OPTIONS

app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = SQLALCHEMY_ENGINE_OPTIONS

# Afficher le type de base de données utilisée
if SQLALCHEMY_DATABASE_URI.startswith('postgresql'):
    print(f"✅ Configuration PostgreSQL: {SQLALCHEMY_DATABASE_URI.split('@')[1] if '@' in SQLALCHEMY_DATABASE_URI else 'configurée'}")
elif SQLALCHEMY_DATABASE_URI.startswith('mysql'):
    print(f"✅ Configuration MySQL: {SQLALCHEMY_DATABASE_URI.split('@')[1] if '@' in SQLALCHEMY_DATABASE_URI else 'configurée'}")
elif SQLALCHEMY_DATABASE_URI.startswith('sqlite'):
    print(f"✅ Configuration SQLite: {SQLALCHEMY_DATABASE_URI}")
else:
    print(f"✅ Configuration base de données: {SQLALCHEMY_DATABASE_URI[:50]}...")

# Initialisation de SQLAlchemy
from models import db
db.init_app(app)

# Configuration du middleware d'adaptation MySQL → PostgreSQL
try:
    from db_utils.db_adapter import setup_sqlalchemy_middleware
    setup_sqlalchemy_middleware(db.engine)
    print("✅ Middleware d'adaptation MySQL/PostgreSQL activé")
except Exception as e:
    print(f"⚠️  Erreur lors de l'initialisation du middleware d'adaptation: {e}")

# Initialisation de Flask-Login
from auth import login_manager, init_rate_limiter
login_manager.init_app(app)

# Initialiser le rate limiting pour la protection contre les attaques brute force
limiter = init_rate_limiter(app)

# Initialisation du cache (Flask-Caching)
try:
    from flask_caching import Cache
    cache_config = {
        'CACHE_TYPE': os.getenv('CACHE_TYPE', 'simple'),  # 'simple', 'redis', 'memcached'
        'CACHE_DEFAULT_TIMEOUT': int(os.getenv('CACHE_TIMEOUT', '3600')),  # 1 heure par défaut
    }
    
    # Si Redis est configuré
    redis_url = os.getenv('REDIS_URL', '')
    if redis_url and redis_url != 'memory://' and redis_url.startswith('redis://'):
        cache_config['CACHE_TYPE'] = 'redis'
        cache_config['CACHE_REDIS_URL'] = redis_url
        print(f"✅ Cache Redis configuré: {redis_url}")
    else:
        cache_config['CACHE_TYPE'] = 'simple'
        print("✅ Cache simple (mémoire) configuré")
    
    cache = Cache(app, config=cache_config)
    app.cache = cache  # Rendre le cache accessible partout
except ImportError:
    print("⚠️  Flask-Caching non installé. Cache désactivé.")
    print("   Installez avec: pip install Flask-Caching")
    app.cache = None
except Exception as e:
    print(f"⚠️  Erreur lors de l'initialisation du cache: {e}")
    app.cache = None

# Compression Gzip pour les réponses HTTP
try:
    from flask_compress import Compress
    Compress(app)
    print("✅ Compression Gzip activée")
except ImportError:
    print("⚠️  Flask-Compress non installé. Compression désactivée.")
    print("   Installez avec: pip install Flask-Compress")
except Exception as e:
    print(f"⚠️  Erreur lors de l'initialisation de la compression: {e}")

# Initialisation de la protection CSRF (Flask-WTF)
try:
    from flask_wtf.csrf import CSRFProtect, CSRFError
    csrf = CSRFProtect(app)
    print("✅ Protection CSRF activée")
    
    # Gestionnaire d'erreur CSRF pour afficher un message clair
    @app.errorhandler(CSRFError)
    def handle_csrf_error(e):
        from flask import flash, redirect, url_for, request
        flash('Erreur de sécurité : Le token CSRF est manquant ou invalide. Veuillez rafraîchir la page et réessayer.', 'error')
        # Rediriger vers la page précédente ou la page d'accueil
        if request.referrer:
            return redirect(request.referrer)
        return redirect(url_for('index'))
except ImportError:
    print("⚠️  Flask-WTF non installé. Protection CSRF désactivée.")
    print("   Installez avec: pip install Flask-WTF")
    csrf = None
    CSRFError = None
except Exception as e:
    print(f"⚠️  Erreur lors de l'initialisation de CSRF: {e}")
    csrf = None
    CSRFError = None

# Initialisation de Flask-Mail
try:
    from email_utils import mail
    mail.init_app(app)
    if app.config.get('MAIL_USERNAME'):
        print("✅ Flask-Mail configuré et prêt")
    else:
        print("⚠️  Flask-Mail configuré mais MAIL_USERNAME non défini")
        print("   Configurez MAIL_USERNAME et MAIL_PASSWORD dans .env pour activer l'envoi d'emails")
except ImportError:
    print("⚠️  Flask-Mail non installé. Envoi d'emails désactivé.")
    print("   Installez avec: pip install Flask-Mail")
except Exception as e:
    print(f"⚠️  Erreur lors de l'initialisation de Flask-Mail: {e}")

# Import et enregistrement des blueprints
from auth import auth_bp, apply_login_rate_limit
from rh import rh_bp
app.register_blueprint(auth_bp)
app.register_blueprint(rh_bp)

# Appliquer le rate limiting APRÈS l'enregistrement du blueprint
if limiter:
    apply_login_rate_limit()

from referentiels import referentiels_bp
app.register_blueprint(referentiels_bp)

from stocks import stocks_bp
app.register_blueprint(stocks_bp)

from inventaires import inventaires_bp
app.register_blueprint(inventaires_bp)

from flotte import flotte_bp
app.register_blueprint(flotte_bp)

from price_lists import price_lists_bp
app.register_blueprint(price_lists_bp)

from chat import chat_bp
app.register_blueprint(chat_bp)
# Exempter toutes les routes API du blueprint chat du CSRF après enregistrement
# Les routes API JSON n'ont pas besoin de token CSRF car elles utilisent l'authentification par session
if csrf:
    # Exempter le blueprint entier - cela exempte toutes les routes du blueprint
    try:
        csrf.exempt(chat_bp)
        print("✅ Blueprint chat exempté du CSRF (toutes les routes)")
    except Exception as e:
        print(f"⚠️  Erreur lors de l'exemption CSRF pour le blueprint chat: {e}")
        import traceback
        traceback.print_exc()

from analytics import analytics_bp
app.register_blueprint(analytics_bp)

from themes import themes_bp
app.register_blueprint(themes_bp)

from search import search_bp
app.register_blueprint(search_bp)

from promotion import promotion_bp
app.register_blueprint(promotion_bp)

from orders import orders_bp
app.register_blueprint(orders_bp)

# Création des tables et initialisation des données
with app.app_context():
    try:
        # Tester la connexion à la base de données
        db.engine.connect()
        print("✅ Connexion à la base de données réussie")
        
        # Créer toutes les tables
        db.create_all()
        print("✅ Tables créées avec succès")
        
        # Initialiser les données de base si nécessaire
        from models import Category, Article, Simulation, SimulationItem, Role, User
        from werkzeug.security import generate_password_hash
        
        # Initialiser les rôles
        if Role.query.count() == 0:
            print("🔄 Initialisation des rôles...")
            roles_data = [
                {
                    'name': 'Administrateur',
                    'code': 'admin',
                    'description': 'Accès complet à toutes les fonctionnalités',
                    'permissions': {'all': ['*'], 'promotion': ['read', 'write']}  # Tous les droits
                },
                {
                    'name': 'Magasinier',
                    'code': 'warehouse',
                    'description': 'Gestion des réceptions, transferts et inventaires',
                    'permissions': {
                        'stocks': ['read', 'create', 'update'],
                        'movements': ['read', 'create'],
                        'inventory': ['read', 'create', 'update'],
                        'vehicles': ['read'],
                        'regions': ['read'],
                        'depots': ['read'],
                        'families': ['read'],
                        'stock_items': ['read'],
                        'orders': ['read'],
                        'outgoings': ['read', 'create', 'update'],
                        'stock_loading': ['read', 'verify', 'load']
                    }
                },
                {
                    'name': 'Commercial',
                    'code': 'commercial',
                    'description': 'Consultation stock véhicule, demandes de réassort',
                    'permissions': {
                        'stocks': ['read'],
                        'vehicles': ['read'],
                        'simulations': ['read', 'create'],
                        'regions': ['read'],
                        'depots': ['read'],
                        'families': ['read'],
                        'stock_items': ['read'],
                        'orders': ['read', 'create', 'update']
                    }
                },
                {
                    'name': 'Superviseur',
                    'code': 'supervisor',
                    'description': 'Suivi régional, KPI, validation inventaires',
                    'permissions': {
                        'stocks': ['read'],
                        'inventory': ['read', 'validate'],
                        'vehicles': ['read', 'update'],
                        'reports': ['read'],
                        'regions': ['read'],
                        'depots': ['read'],
                        'families': ['read'],
                        'stock_items': ['read'],
                        'promotion': ['read', 'write'],
                        'orders': ['read', 'validate', 'update']
                    }
                },
                {
                    'name': 'Ressources Humaines',
                    'code': 'rh',
                    'description': 'Gestion du personnel et suivi des interactions utilisateurs',
                    'permissions': {
                        'users': ['read', 'create', 'update'],
                        'employees': ['read'],
                        'contracts': ['read'],
                        'trainings': ['read'],
                        'evaluations': ['read'],
                        'absences': ['read'],
                        'roles': ['read'],
                        'reports': ['read'],
                        'analytics': ['read']
                    }
                },
                {
                    'name': 'RH Manager',
                    'code': 'rh_manager',
                    'description': 'Gestion complète du personnel, contrats, formations, évaluations',
                    'permissions': {
                        'users': ['read', 'create', 'update', 'delete'],
                        'employees': ['read', 'create', 'update', 'delete'],
                        'contracts': ['read', 'create', 'update', 'delete'],
                        'trainings': ['read', 'create', 'update', 'delete'],
                        'evaluations': ['read', 'create', 'update', 'delete'],
                        'absences': ['read', 'create', 'update', 'delete'],
                        'roles': ['read'],
                        'reports': ['read', 'export'],
                        'analytics': ['read', 'export']
                    }
                },
                {
                    'name': 'RH Assistant',
                    'code': 'rh_assistant',
                    'description': 'Assistance RH : saisie données, suivi formations, gestion absences',
                    'permissions': {
                        'users': ['read', 'create', 'update'],
                        'employees': ['read', 'create', 'update'],
                        'contracts': ['read', 'create', 'update'],
                        'trainings': ['read', 'create', 'update'],
                        'evaluations': ['read', 'create'],
                        'absences': ['read', 'create', 'update'],
                        'reports': ['read']
                    }
                },
                {
                    'name': 'RH Recruiter',
                    'code': 'rh_recruiter',
                    'description': 'Recrutement et intégration du personnel',
                    'permissions': {
                        'users': ['read', 'create'],
                        'employees': ['read', 'create', 'update'],
                        'contracts': ['read', 'create'],
                        'trainings': ['read', 'create'],
                        'reports': ['read']
                    }
                },
                {
                    'name': 'RH Analyst',
                    'code': 'rh_analyst',
                    'description': 'Analyse et reporting RH, statistiques, tableaux de bord',
                    'permissions': {
                        'users': ['read'],
                        'employees': ['read'],
                        'contracts': ['read'],
                        'trainings': ['read'],
                        'evaluations': ['read'],
                        'absences': ['read'],
                        'reports': ['read', 'export'],
                        'analytics': ['read', 'export']
                    }
                }
            ]
            
            for role_data in roles_data:
                role = Role(
                    name=role_data['name'],
                    code=role_data['code'],
                    description=role_data['description'],
                    permissions=role_data['permissions']
                )
                db.session.add(role)
            
            db.session.commit()
            print("✅ Rôles initialisés")
        
        # Créer l'utilisateur admin par défaut
        if User.query.filter_by(username='admin').first() is None:
            print("🔄 Création de l'utilisateur admin...")
            admin_role = Role.query.filter_by(code='admin').first()
            if admin_role:
                admin_user = User(
                    username='admin',
                    email='admin@importprofit.pro',
                    password_hash=generate_password_hash('admin123'),  # À changer en production
                    full_name='Administrateur',
                    role_id=admin_role.id,
                    is_active=True
                )
                db.session.add(admin_user)
                db.session.commit()
                print("✅ Utilisateur admin créé (username: admin, password: admin123)")
        
        # Initialiser les catégories
        if Category.query.count() == 0:
            print("🔄 Initialisation des catégories...")
            categories_data = [
                {'name': 'Électronique'},
                {'name': 'Informatique'},
                {'name': 'Textile'},
                {'name': 'Chaussures'},
                {'name': 'Maroquinerie'},
                {'name': 'Électroménager'},
                {'name': 'Mobilier'},
                {'name': 'Autre'}
            ]
            
            for cat_data in categories_data:
                category = Category(name=cat_data['name'])
                db.session.add(category)
            
            db.session.commit()
            print("✅ Catégories initialisées")
        
        # Ajouter quelques articles de démonstration
        if Article.query.count() == 0:
            print("🔄 Ajout d'articles de démonstration...")
            demo_articles = [
                {
                    'name': 'Smartphone Samsung Galaxy S24',
                    'category_name': 'Électronique',
                    'purchase_price': 150.00,
                    'purchase_currency': 'USD',
                    'unit_weight_kg': 0.2
                },
                {
                    'name': 'Ordinateur Portable Dell XPS',
                    'category_name': 'Informatique',
                    'purchase_price': 800.00,
                    'purchase_currency': 'USD',
                    'unit_weight_kg': 2.5
                },
                {
                    'name': 'Vêtements Importés Premium',
                    'category_name': 'Textile',
                    'purchase_price': 25.00,
                    'purchase_currency': 'EUR',
                    'unit_weight_kg': 0.5
                },
                {
                    'name': 'Chaussures Nike Air Max',
                    'category_name': 'Chaussures',
                    'purchase_price': 80.00,
                    'purchase_currency': 'USD',
                    'unit_weight_kg': 0.8
                }
            ]
            
            for art_data in demo_articles:
                category = Category.query.filter_by(name=art_data['category_name']).first()
                if category:
                    article = Article(
                        name=art_data['name'],
                        category_id=category.id,
                        purchase_price=Decimal(str(art_data['purchase_price'])),
                        purchase_currency=art_data['purchase_currency'],
                        unit_weight_kg=Decimal(str(art_data['unit_weight_kg'])),
                        is_active=True
                    )
                    db.session.add(article)
            
            db.session.commit()
            print("✅ Articles de démonstration ajoutés")
        
        # Créer quelques simulations de démonstration
        try:
            sim_count = Simulation.query.count()
        except Exception:
            sim_count = 0
        if sim_count == 0:
            print("🔄 Création de simulations de démonstration...")
            demo_simulations = [
                {
                    'name': 'Import Électronique Q1 2024',
                    'rate_usd': 8500.0,
                    'rate_eur': 9200.0,
                    'truck_capacity_tons': 25.0,
                    'status': 'completed'
                },
                {
                    'name': 'Simulation Textile Premium',
                    'rate_usd': 8700.0,
                    'rate_eur': 9400.0,
                    'truck_capacity_tons': 20.0,
                    'status': 'active'
                },
                {
                    'name': 'Import Informatique',
                    'rate_usd': 8600.0,
                    'rate_eur': 9300.0,
                    'truck_capacity_tons': 15.0,
                    'status': 'pending'
                }
            ]
            
            # Vérifier quelles colonnes existent dans la table
            from sqlalchemy import inspect, text
            inspector = inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('simulations')]
            
            for sim_data in demo_simulations:
                # Construire les données de base avec seulement les colonnes qui existent
                sim_dict = {
                    'rate_usd': Decimal(str(sim_data['rate_usd'])),
                    'rate_eur': Decimal(str(sim_data['rate_eur'])),
                    'truck_capacity_tons': Decimal(str(sim_data['truck_capacity_tons'])),
                    'is_completed': (sim_data['status'] == 'completed')
                }
                
                # Ajouter les colonnes optionnelles seulement si elles existent
                if 'rate_xof' in columns:
                    sim_dict['rate_xof'] = Decimal('0')
                if 'customs_gnf' in columns:
                    sim_dict['customs_gnf'] = Decimal('0.00')
                if 'handling_gnf' in columns:
                    sim_dict['handling_gnf'] = Decimal('0.00')
                if 'others_gnf' in columns:
                    sim_dict['others_gnf'] = Decimal('0.00')
                if 'transport_fixed_gnf' in columns:
                    sim_dict['transport_fixed_gnf'] = Decimal('0.00')
                if 'transport_per_kg_gnf' in columns:
                    sim_dict['transport_per_kg_gnf'] = Decimal('0.0000')
                if 'basis' in columns:
                    sim_dict['basis'] = 'value'
                if 'target_mode' in columns:
                    sim_dict['target_mode'] = 'none'
                if 'target_margin_pct' in columns:
                    sim_dict['target_margin_pct'] = Decimal('0.0000')
                
                # Utiliser SQL brut pour éviter les problèmes avec les colonnes manquantes
                cols = [k for k in sim_dict.keys() if k in columns]
                cols.append('created_at')
                values_placeholders = ', '.join([f':{col}' for col in cols])
                cols_str = ', '.join(cols)
                
                # Ajouter created_at
                sim_dict['created_at'] = datetime.now(UTC)
                
                # Construire et exécuter la requête SQL
                # Utiliser RETURNING pour PostgreSQL, LAST_INSERT_ID() pour MySQL
                from config import SQLALCHEMY_DATABASE_URI
                is_postgresql = SQLALCHEMY_DATABASE_URI.startswith('postgresql')
                
                if is_postgresql:
                    sql = f"""
                        INSERT INTO simulations ({cols_str})
                        VALUES ({values_placeholders})
                        RETURNING id
                    """
                else:
                    sql = f"""
                        INSERT INTO simulations ({cols_str})
                        VALUES ({values_placeholders})
                    """
                
                try:
                    result = db.session.execute(text(sql), sim_dict)
                    db.session.flush()
                    
                    # Récupérer l'ID de la simulation créée
                    if is_postgresql:
                        simulation_id = result.scalar()
                    else:
                        # MySQL
                        id_result = db.session.execute(text("SELECT LAST_INSERT_ID() as id"))
                        simulation_id = id_result.scalar()
                    
                    if simulation_id:
                        # Ajouter des articles à la simulation
                        articles = Article.query.limit(2).all()
                        for i, article in enumerate(articles):
                            simulation_item = SimulationItem(
                                simulation_id=simulation_id,
                                article_id=article.id,
                                quantity=Decimal(str(10 + i * 5)),
                                selling_price_gnf=Decimal(str(150000 + i * 50000)),
                                purchase_price=article.purchase_price,
                                purchase_currency=article.purchase_currency,
                                unit_weight_kg=article.unit_weight_kg
                            )
                            db.session.add(simulation_item)
                except Exception as e:
                    print(f"⚠️ Erreur lors de la création de la simulation de démonstration: {e}")
                    db.session.rollback()
                    continue
            
            db.session.commit()
            print("✅ Simulations de démonstration créées")
            
    except Exception as e:
        print(f"⚠️ Erreur lors de l'initialisation: {e}")
        print("🔄 Utilisation des données de démonstration")

# Import et enregistrement des blueprints
from api_profitability import profitability_api
app.register_blueprint(profitability_api)

# Fonction url_for_safe pour les templates
def url_for_safe(endpoint, **values):
    """Version sécurisée de url_for"""
    try:
        return url_for(endpoint, **values)
    except:
        return f"/{endpoint}"

# Ajouter les fonctions au contexte des templates
app.jinja_env.globals['url_for_safe'] = url_for_safe
from auth import has_permission
app.jinja_env.globals['has_permission'] = has_permission
from utils import get_days_until_expiry
app.jinja_env.globals['get_days_until_expiry'] = get_days_until_expiry

# Ajouter csrf_token() aux templates si CSRF est activé
if csrf:
    from flask_wtf.csrf import generate_csrf
    app.jinja_env.globals['csrf_token'] = generate_csrf
else:
    app.jinja_env.globals['csrf_token'] = lambda: ''

# Filtre personnalisé pour formater les nombres avec espaces comme séparateurs de milliers
@app.template_filter('to_float')
def to_float(value):
    """Convertit une valeur (Decimal, int, str) en float pour les calculs Jinja2"""
    if value is None:
        return 0.0
    try:
        from decimal import Decimal
        if isinstance(value, Decimal):
            return float(value)
        return float(value)
    except (ValueError, TypeError):
        return 0.0

@app.template_filter('format_number')
def format_number(value, decimals=0):
    """Formate un nombre avec des espaces comme séparateurs de milliers"""
    if value is None:
        return '0'
    try:
        # Gérer les Decimal explicitement
        from decimal import Decimal
        if isinstance(value, Decimal):
            num = float(value)
        else:
            num = float(value)
        if decimals == 0:
            num = int(num)
        # Formater avec virgules puis remplacer par des espaces
        formatted = f"{num:,.{decimals}f}".replace(',', ' ')
        return formatted
    except (ValueError, TypeError):
        return str(value) if value else '-'

@app.template_filter('calculate_items_total')
def calculate_items_total(items):
    """Calcule le total d'une liste d'items (quantité * prix unitaire)"""
    total = 0.0
    if not items:
        return total
    try:
        from decimal import Decimal
        for item in items:
            if hasattr(item, 'quantity') and hasattr(item, 'unit_price_gnf'):
                qty = float(item.quantity) if item.quantity is not None else 0.0
                price = float(item.unit_price_gnf) if item.unit_price_gnf is not None else 0.0
                total += qty * price
    except (ValueError, TypeError, AttributeError):
        pass
    return total

# Routes principales
@app.route('/')
@login_required
def index():
    """Page d'accueil moderne"""
    try:
        from models import (
            Category, Article, Simulation, Region, Depot, Vehicle, 
            Family, StockItem, InventorySession, StockMovement, Reception,
            VehicleDocument, VehicleMaintenance, DepotStock, VehicleStock,
            PriceList
        )
        from datetime import datetime, timedelta
        
        # Récupérer les statistiques depuis la base de données
        # Gérer les erreurs de colonnes manquantes
        try:
            simulations_count = Simulation.query.count()
            completed_simulations = Simulation.query.filter_by(is_completed=True).count()
        except Exception as e:
            print(f"⚠️ Erreur lors du comptage des simulations (colonnes manquantes?): {e}")
            simulations_count = 0
            completed_simulations = 0
        
        # Utiliser le cache pour les statistiques si disponible (avec clé incluant la région)
        from utils_region_filter import (
            get_user_region_id, filter_depots_by_region, filter_vehicles_by_region,
            filter_stock_movements_by_region, filter_depot_stocks_by_region, filter_vehicle_stocks_by_region
        )
        user_region_id = get_user_region_id()
        cache_key = f'dashboard_stats_{user_region_id if user_region_id else "all"}'
        stats = None
        
        if app.cache:
            stats = app.cache.get(cache_key)
        
        if not stats:
            # Import Profit (pas de filtre par région)
            stats = {
                'categories_count': Category.query.count(),
                'articles_count': Article.query.count(),
                'simulations_count': simulations_count,
                'completed_simulations': completed_simulations,
            }
            
            # Référentiels avec filtrage par région
            stats['regions_count'] = Region.query.count()
            
            # Dépôts filtrés par région
            depots_query = Depot.query.filter_by(is_active=True)
            depots_query = filter_depots_by_region(depots_query)
            stats['depots_count'] = depots_query.count()
            
            # Véhicules filtrés par région
            vehicles_query = Vehicle.query.filter_by(status='active')
            vehicles_query = filter_vehicles_by_region(vehicles_query)
            stats['vehicles_count'] = vehicles_query.count()
            
            stats['families_count'] = Family.query.count()
            stats['stock_items_count'] = StockItem.query.filter_by(is_active=True).count()
            
            # Stocks avec filtrage par région
            movements_query = StockMovement.query
            movements_query = filter_stock_movements_by_region(movements_query)
            stats['movements_count'] = movements_query.count()
            
            stats['receptions_count'] = Reception.query.count()  # Les réceptions peuvent être filtrées si nécessaire
            
            depot_stocks_query = DepotStock.query
            depot_stocks_query = filter_depot_stocks_by_region(depot_stocks_query)
            stats['depot_stocks_count'] = depot_stocks_query.count()
            
            vehicle_stocks_query = VehicleStock.query
            vehicle_stocks_query = filter_vehicle_stocks_by_region(vehicle_stocks_query)
            stats['vehicle_stocks_count'] = vehicle_stocks_query.count()
            
            # Inventaires
            stats['inventory_sessions_count'] = InventorySession.query.count()
            stats['inventory_pending'] = InventorySession.query.filter_by(status='draft').count()
            
            # Flotte avec filtrage par région
            vehicles_for_docs_query = Vehicle.query
            vehicles_for_docs_query = filter_vehicles_by_region(vehicles_for_docs_query)
            vehicle_ids_for_docs = [v.id for v in vehicles_for_docs_query.all()]
            if vehicle_ids_for_docs:
                stats['documents_count'] = VehicleDocument.query.filter(VehicleDocument.vehicle_id.in_(vehicle_ids_for_docs)).count()
                stats['maintenances_planned'] = VehicleMaintenance.query.filter(
                    VehicleMaintenance.vehicle_id.in_(vehicle_ids_for_docs),
                    VehicleMaintenance.status == 'planned'
                ).count()
            else:
                stats['documents_count'] = 0
                stats['maintenances_planned'] = 0
            
            # Fiches de Prix
            stats['price_lists_count'] = PriceList.query.count()
            stats['price_lists_active'] = PriceList.query.filter_by(is_active=True).count()
            
            # Statistiques RH (toujours calculées pour l'admin)
            try:
                from models import User, Employee, EmployeeContract, EmployeeTraining, EmployeeAbsence
                from sqlalchemy.exc import SQLAlchemyError
                from sqlalchemy import or_, and_
                
                # Annuler toute transaction en cours en cas d'erreur précédente
                db.session.rollback()
                
                stats['total_users'] = User.query.count()
                stats['active_users'] = User.query.filter_by(is_active=True).count()
                stats['total_employees'] = Employee.query.count()
                stats['active_employees'] = Employee.query.filter_by(employment_status='active').count()
                stats['active_contracts'] = EmployeeContract.query.filter(
                    or_(
                        EmployeeContract.status == 'active',
                        and_(
                            EmployeeContract.end_date.is_(None),
                            EmployeeContract.status != 'terminated'
                        )
                    )
                ).count()
                stats['pending_absences'] = EmployeeAbsence.query.filter_by(status='pending').count()
                stats['ongoing_trainings'] = EmployeeTraining.query.filter_by(status='in_progress').count()
            except (Exception, SQLAlchemyError) as e:
                print(f"⚠️ Erreur lors du calcul des statistiques RH: {e}")
                db.session.rollback()  # Annuler la transaction en cas d'erreur
                stats['total_users'] = 0
                stats['active_users'] = 0
                stats['total_employees'] = 0
                stats['active_employees'] = 0
                stats['active_contracts'] = 0
                stats['pending_absences'] = 0
                stats['ongoing_trainings'] = 0
            
            # Statistiques Commandes Commerciales (toujours calculées pour l'admin)
            try:
                from models import CommercialOrder
                from utils_region_filter import filter_commercial_orders_by_region
                from sqlalchemy.exc import SQLAlchemyError
                
                # Annuler toute transaction en cours en cas d'erreur précédente
                db.session.rollback()
                
                orders_query = CommercialOrder.query
                orders_query = filter_commercial_orders_by_region(orders_query)
                stats['orders_count'] = orders_query.count()
                stats['orders_pending'] = orders_query.filter_by(status='draft').count()
                stats['orders_validated'] = orders_query.filter_by(status='validated').count()
                # Note: l'enum order_status n'a pas "cancelled", mais "rejected" à la place
                stats['orders_rejected'] = orders_query.filter_by(status='rejected').count()
                stats['orders_completed'] = orders_query.filter_by(status='completed').count()
            except (Exception, SQLAlchemyError) as e:
                print(f"⚠️ Erreur lors du calcul des statistiques commandes: {e}")
                db.session.rollback()  # Annuler la transaction en cas d'erreur
                stats['orders_count'] = 0
                stats['orders_pending'] = 0
                stats['orders_validated'] = 0
                stats['orders_rejected'] = 0
                stats['orders_completed'] = 0
            
            # Statistiques Promotion (toujours calculées pour l'admin)
            try:
                from models import PromotionTeam, PromotionMember, PromotionSale, PromotionGamme, PromotionReturn
                from utils_region_filter import filter_teams_by_region, filter_members_by_region, filter_sales_by_region
                from sqlalchemy.exc import SQLAlchemyError
                
                # Annuler toute transaction en cours en cas d'erreur précédente
                db.session.rollback()
                
                # Équipes
                teams_query = PromotionTeam.query.filter_by(is_active=True)
                teams_query = filter_teams_by_region(teams_query)
                stats['promotion_teams'] = teams_query.count()
                
                # Membres
                members_query = PromotionMember.query.filter_by(is_active=True)
                members_query = filter_members_by_region(members_query)
                stats['promotion_members'] = members_query.count()
                
                # Gammes
                stats['promotion_gammes'] = PromotionGamme.query.filter_by(is_active=True).count()
                
                # Ventes (aujourd'hui)
                today = date.today()
                sales_query = PromotionSale.query.filter(PromotionSale.sale_date == today)
                sales_query = filter_sales_by_region(sales_query)
                stats['promotion_sales_today'] = sales_query.count()
                
                # Retours en attente
                stats['promotion_returns_pending'] = PromotionReturn.query.filter_by(status='pending').count()
            except (Exception, SQLAlchemyError) as e:
                print(f"⚠️ Erreur lors du calcul des statistiques promotion: {e}")
                db.session.rollback()  # Annuler la transaction en cas d'erreur
                stats['promotion_teams'] = 0
                stats['promotion_members'] = 0
                stats['promotion_gammes'] = 0
                stats['promotion_sales_today'] = 0
                stats['promotion_returns_pending'] = 0
            
            # Statistiques récentes (7 derniers jours) avec filtrage par région
            seven_days_ago = datetime.now(UTC) - timedelta(days=7)
            recent_movements_query = StockMovement.query.filter(StockMovement.movement_date >= seven_days_ago)
            recent_movements_query = filter_stock_movements_by_region(recent_movements_query)
            stats['recent_movements'] = recent_movements_query.count()
            
            stats['recent_receptions'] = Reception.query.filter(Reception.reception_date >= seven_days_ago).count()
            stats['recent_sessions'] = InventorySession.query.filter(InventorySession.session_date >= seven_days_ago).count()
            
            # Ajouter la région de l'utilisateur pour l'affichage
            stats['user_region_id'] = user_region_id
            if user_region_id:
                user_region = Region.query.get(user_region_id)
                stats['user_region_name'] = user_region.name if user_region else None
            else:
                stats['user_region_name'] = None
            
            # Mettre en cache les statistiques (cache 5 minutes)
            if app.cache:
                app.cache.set(cache_key, stats, timeout=600)  # 10 minutes pour meilleure performance
        
        # Récupérer les simulations récentes (seulement si l'utilisateur a la permission)
        recent_simulations = []
        if has_permission(current_user, 'simulations.read'):
            try:
                recent_simulations = Simulation.query.order_by(Simulation.created_at.desc()).limit(10).all()
            except Exception as e:
                print(f"⚠️ Erreur lors de la récupération des simulations récentes: {e}")
                # Si l'erreur est due à target_mode, utiliser une requête SQL directe
                if 'target_mode' in str(e) or 'target_margin_pct' in str(e):
                    try:
                        from sqlalchemy import text
                        # Vérifier quelles colonnes existent dans la table
                        from sqlalchemy import inspect
                        inspector = inspect(db.engine)
                        columns = [col['name'] for col in inspector.get_columns('simulations')]
                        
                        # Construire la liste des colonnes à sélectionner (sans target_mode et target_margin_pct)
                        select_cols = []
                        for col in ['id', 'rate_usd', 'rate_eur', 'rate_xof', 'customs_gnf', 'handling_gnf', 
                                   'others_gnf', 'transport_fixed_gnf', 'transport_per_kg_gnf', 'basis',
                                   'truck_capacity_tons', 'is_completed', 'created_at', 'updated_at']:
                            if col in columns:
                                select_cols.append(col)
                        
                        if select_cols:
                            # Requête SQL sans les colonnes manquantes
                            cols_str = ', '.join(select_cols)
                            result = db.session.execute(text(f"""
                                SELECT {cols_str}
                                FROM simulations 
                                ORDER BY created_at DESC
                                LIMIT 10
                            """))
                            # Créer des objets Simulation à partir des résultats
                            recent_simulations = []
                            for row in result:
                                try:
                                    # Convertir la row en dictionnaire pour faciliter l'accès
                                    # SQLAlchemy retourne des Row objects qui peuvent être accédés par index ou par nom
                                    row_dict = {}
                                    for idx, col in enumerate(select_cols):
                                        try:
                                            # Essayer d'accéder par nom de colonne d'abord
                                            if hasattr(row, '_mapping'):
                                                row_dict[col] = row._mapping.get(col, row[idx])
                                            else:
                                                row_dict[col] = row[idx]
                                        except (IndexError, KeyError):
                                            print(f"⚠️ Impossible d'accéder à la colonne {col} à l'index {idx}")
                                            continue
                                    
                                    # Créer un objet Simulation avec les données disponibles
                                    sim = Simulation()
                                    for col in select_cols:
                                        if col in row_dict and hasattr(sim, col):
                                            value = row_dict[col]
                                            # Gérer les types spécifiques
                                            if col in ['rate_usd', 'rate_eur', 'rate_xof', 'customs_gnf', 'handling_gnf', 
                                                      'others_gnf', 'transport_fixed_gnf', 'transport_per_kg_gnf', 
                                                      'truck_capacity_tons', 'target_margin_pct']:
                                                from decimal import Decimal
                                                value = Decimal(str(value)) if value is not None else Decimal('0')
                                            elif col == 'is_completed':
                                                value = bool(value) if value is not None else False
                                            elif col == 'basis' and value is None:
                                                value = 'value'
                                            setattr(sim, col, value)
                                    
                                    # S'assurer que l'ID est défini pour charger les items
                                    if hasattr(sim, 'id') and sim.id:
                                        # Charger les items pour calculer la marge
                                        try:
                                            from models import SimulationItem
                                            sim.items = SimulationItem.query.filter_by(simulation_id=sim.id).all()
                                        except:
                                            sim.items = []
                                    else:
                                        sim.items = []
                                    
                                    recent_simulations.append(sim)
                                except Exception as row_error:
                                    print(f"⚠️ Erreur lors du traitement d'une ligne: {row_error}")
                                    import traceback
                                    traceback.print_exc()
                                    continue
                            print(f"✅ {len(recent_simulations)} simulations récentes récupérées via SQL direct")
                            if len(recent_simulations) > 0:
                                print(f"📋 Première simulation: ID={recent_simulations[0].id}, Date={recent_simulations[0].created_at}")
                        else:
                            print("⚠️ Aucune colonne valide trouvée dans la table simulations")
                            recent_simulations = []
                    except Exception as e2:
                        print(f"⚠️ Erreur lors de la récupération SQL directe des simulations récentes: {e2}")
                        import traceback
                        traceback.print_exc()
                        recent_simulations = []
                else:
                    recent_simulations = []
        
        # Calculer la marge totale pour chaque simulation récente
        from decimal import Decimal
        recent_simulations_with_margin = []
        for sim in recent_simulations:
            total_margin_gnf = Decimal('0')
            if sim.items and len(sim.items) > 0:
                # Calculer le prix de revient total et la valeur de vente totale
                total_purchase_value = Decimal('0')
                total_weight = Decimal('0')
                total_selling_value = Decimal('0')
                
                for item in sim.items:
                    # Prix d'achat en GNF
                    purchase_price_gnf = Decimal('0')
                    if item.purchase_currency == 'USD' and sim.rate_usd:
                        purchase_price_gnf = Decimal(str(item.purchase_price)) * sim.rate_usd
                    elif item.purchase_currency == 'EUR' and sim.rate_eur:
                        purchase_price_gnf = Decimal(str(item.purchase_price)) * sim.rate_eur
                    elif item.purchase_currency == 'XOF' and sim.rate_xof:
                        purchase_price_gnf = Decimal(str(item.purchase_price)) * sim.rate_xof
                    
                    # Valeur totale d'achat
                    item_value = purchase_price_gnf * Decimal(str(item.quantity))
                    total_purchase_value += item_value
                    
                    # Poids total
                    item_weight = Decimal(str(item.unit_weight_kg or 0)) * Decimal(str(item.quantity))
                    total_weight += item_weight
                    
                    # Valeur totale de vente
                    total_selling_value += Decimal(str(item.selling_price_gnf or 0)) * Decimal(str(item.quantity))
                
                # Calculer les coûts logistiques totaux
                total_logistics = Decimal('0')
                if sim.customs_gnf:
                    total_logistics += sim.customs_gnf
                if sim.handling_gnf:
                    total_logistics += sim.handling_gnf
                if sim.others_gnf:
                    total_logistics += sim.others_gnf
                if sim.transport_fixed_gnf:
                    total_logistics += sim.transport_fixed_gnf
                if sim.transport_per_kg_gnf and total_weight > 0:
                    total_logistics += sim.transport_per_kg_gnf * total_weight
                
                # Prix de revient total = prix d'achat + coûts logistiques
                total_cost = total_purchase_value + total_logistics
                
                # Marge totale = valeur de vente - prix de revient
                total_margin_gnf = total_selling_value - total_cost
            
            # Ajouter la marge comme attribut à la simulation
            sim.total_margin_gnf = total_margin_gnf
            recent_simulations_with_margin.append(sim)
        
        # Récupérer les mouvements récents (seulement si l'utilisateur a la permission) avec filtrage par région
        recent_movements = []
        if has_permission(current_user, 'movements.read'):
            recent_movements_query = StockMovement.query.order_by(StockMovement.movement_date.desc())
            recent_movements_query = filter_stock_movements_by_region(recent_movements_query)
            recent_movements = recent_movements_query.limit(5).all()
        
        # Récupérer les sessions d'inventaire récentes (seulement si l'utilisateur a la permission)
        recent_inventories = []
        if has_permission(current_user, 'inventory.read'):
            recent_inventories = InventorySession.query.order_by(InventorySession.session_date.desc()).limit(3).all()
        
        # Récupérer les fiches de prix récentes (seulement si l'utilisateur a la permission)
        recent_price_lists = []
        if has_permission(current_user, 'stock_items.read'):
            recent_price_lists = PriceList.query.order_by(PriceList.created_at.desc()).limit(3).all()
        
        # Récupérer les commandes récentes (seulement si l'utilisateur a la permission)
        recent_orders = []
        if has_permission(current_user, 'orders.read'):
            try:
                from models import CommercialOrder
                from utils_region_filter import filter_commercial_orders_by_region
                recent_orders_query = CommercialOrder.query.order_by(CommercialOrder.created_at.desc())
                recent_orders_query = filter_commercial_orders_by_region(recent_orders_query)
                recent_orders = recent_orders_query.limit(5).all()
            except Exception as e:
                print(f"⚠️ Erreur lors de la récupération des commandes récentes: {e}")
                recent_orders = []
        
        # Récupérer les ventes promotion récentes (seulement si l'utilisateur a la permission)
        recent_promotion_sales = []
        if has_permission(current_user, 'promotion.read'):
            try:
                from models import PromotionSale
                from utils_region_filter import filter_sales_by_region
                recent_sales_query = PromotionSale.query.order_by(PromotionSale.sale_date.desc(), PromotionSale.created_at.desc())
                recent_sales_query = filter_sales_by_region(recent_sales_query)
                recent_promotion_sales = recent_sales_query.limit(5).all()
            except Exception as e:
                print(f"⚠️ Erreur lors de la récupération des ventes promotion récentes: {e}")
                recent_promotion_sales = []
        
        # Mettre en cache les statistiques si elles ont été recalculées (cache 5 minutes)
        if app.cache and not app.cache.get(cache_key):
            app.cache.set(cache_key, stats, timeout=300)  # 5 minutes
        
        return render_template('index_hapag_lloyd.html',
                             counts=stats,
                             recent_simulations=recent_simulations_with_margin,
                             recent_movements=recent_movements,
                             recent_inventories=recent_inventories,
                             recent_price_lists=recent_price_lists,
                             recent_orders=recent_orders,
                             recent_promotion_sales=recent_promotion_sales)
    except Exception as e:
        print(f"Erreur lors du chargement de l'index: {e}")
        import traceback
        traceback.print_exc()
        # Fallback avec données vides (pas de données de démonstration)
        # En cas d'erreur, on affiche des zéros pour éviter d'afficher de fausses données
        return render_template('index_hapag_lloyd.html',
                             counts={
                                 'categories_count': 0, 'articles_count': 0, 
                                 'simulations_count': 0, 'completed_simulations': 0,
                                 'regions_count': 0, 'depots_count': 0, 'vehicles_count': 0,
                                 'families_count': 0, 'stock_items_count': 0,
                                 'movements_count': 0, 'receptions_count': 0,
                                 'inventory_sessions_count': 0, 'inventory_pending': 0,
                                 'documents_count': 0, 'maintenances_planned': 0,
                                 'recent_movements': 0, 'recent_receptions': 0, 'recent_sessions': 0,
                                 'total_users': 0, 'active_users': 0, 'total_employees': 0,
                                 'active_employees': 0, 'active_contracts': 0, 'pending_absences': 0,
                                 'orders_count': 0, 'orders_pending': 0, 'orders_validated': 0, 'orders_rejected': 0, 'orders_completed': 0,
                                 'promotion_teams': 0, 'promotion_members': 0, 'promotion_sales_today': 0
                             },
                             recent_simulations=[],
                             recent_movements=[],
                             recent_inventories=[],
                             recent_price_lists=[],
                             recent_orders=[],
                             recent_promotion_sales=[])

@app.route('/simulations')
@login_required
def simulations_list():
    """Liste des simulations ultra-modernes avec pagination et recherche"""
    try:
        from models import Simulation, SimulationItem
        from decimal import Decimal
        from sqlalchemy import or_, and_
        from sqlalchemy.orm import joinedload
        
        # Paramètres de pagination et filtres
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        search = request.args.get('search', '').strip()
        status_filter = request.args.get('status', '')
        date_from = request.args.get('date_from', '')
        date_to = request.args.get('date_to', '')
        
        # Construire la requête de base
        try:
            query = Simulation.query
            
            # Appliquer les filtres
            if status_filter == 'completed':
                query = query.filter(Simulation.is_completed == True)
            elif status_filter == 'active':
                query = query.filter(Simulation.is_completed == False)
            
            if date_from:
                try:
                    date_from_obj = datetime.strptime(date_from, '%Y-%m-%d').date()
                    query = query.filter(Simulation.created_at >= datetime.combine(date_from_obj, datetime.min.time()).replace(tzinfo=UTC))
                except:
                    pass
            
            if date_to:
                try:
                    date_to_obj = datetime.strptime(date_to, '%Y-%m-%d').date()
                    query = query.filter(Simulation.created_at <= datetime.combine(date_to_obj, datetime.max.time()).replace(tzinfo=UTC))
                except:
                    pass
            
            # Recherche (par ID ou date)
            if search:
                try:
                    # Essayer de convertir en ID
                    search_id = int(search)
                    query = query.filter(Simulation.id == search_id)
                except ValueError:
                    # Sinon, chercher dans les dates
                    query = query.filter(Simulation.created_at.like(f'%{search}%'))
            
            # Pagination
            pagination = query.order_by(Simulation.created_at.desc()).paginate(
                page=page, per_page=per_page, error_out=False
            )
            simulations = pagination.items
            print(f"✅ {len(simulations)} simulations récupérées (page {page}/{pagination.pages})")
            
        except Exception as e:
            print(f"⚠️ Erreur lors de la récupération des simulations: {e}")
            # Si l'erreur est due à target_mode ou target_margin_pct, utiliser une requête SQL directe
            if 'target_mode' in str(e) or 'target_margin_pct' in str(e):
                try:
                    from sqlalchemy import text, inspect
                    # Vérifier quelles colonnes existent dans la table
                    inspector = inspect(db.engine)
                    columns = [col['name'] for col in inspector.get_columns('simulations')]
                    
                    # Construire la liste des colonnes à sélectionner (sans target_mode et target_margin_pct)
                    select_cols = []
                    for col in ['id', 'rate_usd', 'rate_eur', 'rate_xof', 'customs_gnf', 'handling_gnf', 
                               'others_gnf', 'transport_fixed_gnf', 'transport_per_kg_gnf', 'basis',
                               'truck_capacity_tons', 'is_completed', 'created_at', 'updated_at']:
                        if col in columns:
                            select_cols.append(col)
                    
                    if select_cols:
                        # Construire la requête SQL avec filtres
                        where_clauses = []
                        params = {}
                        
                        if status_filter == 'completed':
                            where_clauses.append("is_completed = 1")
                        elif status_filter == 'active':
                            where_clauses.append("is_completed = 0")
                        
                        if date_from:
                            try:
                                date_from_obj = datetime.strptime(date_from, '%Y-%m-%d').date()
                                where_clauses.append("created_at >= :date_from")
                                params['date_from'] = datetime.combine(date_from_obj, datetime.min.time()).replace(tzinfo=UTC)
                            except:
                                pass
                        
                        if date_to:
                            try:
                                date_to_obj = datetime.strptime(date_to, '%Y-%m-%d').date()
                                where_clauses.append("created_at <= :date_to")
                                params['date_to'] = datetime.combine(date_to_obj, datetime.max.time()).replace(tzinfo=UTC)
                            except:
                                pass
                        
                        if search:
                            try:
                                search_id = int(search)
                                where_clauses.append("id = :search_id")
                                params['search_id'] = search_id
                            except ValueError:
                                where_clauses.append("created_at LIKE :search")
                                params['search'] = f'%{search}%'
                        
                        where_clause = " AND ".join(where_clauses) if where_clauses else "1=1"
                        
                        # Compter le total pour la pagination
                        count_sql = f"SELECT COUNT(*) FROM simulations WHERE {where_clause}"
                        total_count = db.session.execute(text(count_sql), params).scalar()
                        
                        # Calculer l'offset
                        offset = (page - 1) * per_page
                        
                        # Requête SQL sans les colonnes manquantes avec pagination
                        cols_str = ', '.join(select_cols)
                        result = db.session.execute(text(f"""
                            SELECT {cols_str}
                            FROM simulations 
                            WHERE {where_clause}
                            ORDER BY created_at DESC
                            LIMIT :limit OFFSET :offset
                        """), {**params, 'limit': per_page, 'offset': offset})
                        # Créer des objets Simulation à partir des résultats
                        simulations = []
                        for row in result:
                            try:
                                # Convertir la row en dictionnaire pour faciliter l'accès
                                row_dict = {}
                                for idx, col in enumerate(select_cols):
                                    try:
                                        # Essayer d'accéder par nom de colonne d'abord
                                        if hasattr(row, '_mapping'):
                                            row_dict[col] = row._mapping.get(col, row[idx])
                                        else:
                                            row_dict[col] = row[idx]
                                    except (IndexError, KeyError):
                                        print(f"⚠️ Impossible d'accéder à la colonne {col} à l'index {idx}")
                                        continue
                                
                                # Créer un objet Simulation avec les données disponibles
                                sim = Simulation()
                                for col in select_cols:
                                    if col in row_dict and hasattr(sim, col):
                                        value = row_dict[col]
                                        # Gérer les types spécifiques
                                        if col in ['rate_xof', 'customs_gnf', 'handling_gnf', 'others_gnf', 
                                                  'transport_fixed_gnf', 'transport_per_kg_gnf', 'truck_capacity_tons',
                                                  'rate_usd', 'rate_eur', 'target_margin_pct']:
                                            value = Decimal(str(value)) if value is not None else Decimal('0')
                                        elif col == 'is_completed':
                                            value = bool(value) if value is not None else False
                                        elif col == 'basis' and value is None:
                                            value = 'value'
                                        setattr(sim, col, value)
                                
                                simulations.append(sim)
                            except Exception as row_error:
                                print(f"⚠️ Erreur lors du traitement d'une ligne: {row_error}")
                                import traceback
                                traceback.print_exc()
                                continue
                        print(f"✅ {len(simulations)} simulations récupérées via SQL direct (page {page})")
                        
                        # Créer un objet pagination simulé
                        from math import ceil
                        pagination = type('Pagination', (), {
                            'items': simulations,
                            'page': page,
                            'per_page': per_page,
                            'total': total_count,
                            'pages': ceil(total_count / per_page) if per_page > 0 else 1,
                            'has_prev': page > 1,
                            'has_next': page < ceil(total_count / per_page) if per_page > 0 else False,
                            'prev_num': page - 1 if page > 1 else None,
                            'next_num': page + 1 if page < ceil(total_count / per_page) else None
                        })()
                        
                        if len(simulations) > 0:
                            print(f"📋 Première simulation: ID={simulations[0].id}, Date={simulations[0].created_at}, Items={len(simulations[0].items)}")
                    else:
                        simulations = []
                        pagination = None
                except Exception as e2:
                    print(f"⚠️ Erreur lors de la récupération SQL directe: {e2}")
                    import traceback
                    traceback.print_exc()
                    simulations = []
            else:
                simulations = []
                pagination = None
        
        # Optimisation N+1 : Charger tous les items en une seule requête
        simulation_ids = [s.id for s in simulations if hasattr(s, 'id') and s.id]
        items_map = {}
        if simulation_ids:
            try:
                all_items = SimulationItem.query.filter(SimulationItem.simulation_id.in_(simulation_ids)).all()
                for item in all_items:
                    if item.simulation_id not in items_map:
                        items_map[item.simulation_id] = []
                    items_map[item.simulation_id].append(item)
            except Exception as e:
                print(f"⚠️ Erreur lors du chargement des items: {e}")
        
        # Assigner les items aux simulations
        for sim in simulations:
            if hasattr(sim, 'id') and sim.id:
                sim.items = items_map.get(sim.id, [])
            else:
                sim.items = []
        
        # Calculer la marge totale pour chaque simulation
        simulations_with_margin = []
        for sim in simulations:
            total_margin_gnf = Decimal('0')
            if sim.items and len(sim.items) > 0:
                # Calculer le prix de revient total et la valeur de vente totale
                total_purchase_value = Decimal('0')
                total_weight = Decimal('0')
                total_selling_value = Decimal('0')
                
                for item in sim.items:
                    # Prix d'achat en GNF
                    purchase_price_gnf = Decimal('0')
                    if item.purchase_currency == 'USD' and sim.rate_usd:
                        purchase_price_gnf = Decimal(str(item.purchase_price)) * sim.rate_usd
                    elif item.purchase_currency == 'EUR' and sim.rate_eur:
                        purchase_price_gnf = Decimal(str(item.purchase_price)) * sim.rate_eur
                    elif item.purchase_currency == 'XOF' and sim.rate_xof:
                        purchase_price_gnf = Decimal(str(item.purchase_price)) * sim.rate_xof
                    
                    # Valeur totale d'achat
                    item_value = purchase_price_gnf * Decimal(str(item.quantity))
                    total_purchase_value += item_value
                    
                    # Poids total
                    item_weight = Decimal(str(item.unit_weight_kg or 0)) * Decimal(str(item.quantity))
                    total_weight += item_weight
                    
                    # Valeur totale de vente
                    total_selling_value += Decimal(str(item.selling_price_gnf or 0)) * Decimal(str(item.quantity))
                
                # Calculer les coûts logistiques totaux
                total_logistics = Decimal('0')
                if sim.customs_gnf:
                    total_logistics += sim.customs_gnf
                if sim.handling_gnf:
                    total_logistics += sim.handling_gnf
                if sim.others_gnf:
                    total_logistics += sim.others_gnf
                if sim.transport_fixed_gnf:
                    total_logistics += sim.transport_fixed_gnf
                if sim.transport_per_kg_gnf and total_weight > 0:
                    total_logistics += sim.transport_per_kg_gnf * total_weight
                
                # Prix de revient total = prix d'achat + coûts logistiques
                total_cost = total_purchase_value + total_logistics
                
                # Marge totale = valeur de vente - prix de revient
                total_margin_gnf = total_selling_value - total_cost
            
            # Ajouter la marge comme attribut à la simulation
            sim.total_margin_gnf = total_margin_gnf
            simulations_with_margin.append(sim)
        
        # Calculer la marge moyenne
        total_margin = 0
        for sim in simulations_with_margin:
            if sim.items:
                total_margin += sum(item.margin_pct or 0 for item in sim.items) / len(sim.items)
        avg_margin = total_margin / len(simulations_with_margin) if simulations_with_margin else 0
        
        return render_template('simulations_ultra_modern_v3.html', 
                             simulations=simulations_with_margin,
                             avg_margin=avg_margin,
                             success_rate=85.0,
                             pagination=pagination,
                             search=search,
                             status_filter=status_filter,
                             date_from=date_from,
                             date_to=date_to,
                             per_page=per_page)
    except Exception as e:
        print(f"Erreur lors du chargement des simulations: {e}")
        return render_template('simulations_ultra_modern_v3.html', 
                             simulations=[],
                             avg_margin=0,
                             success_rate=0)

@app.route('/simulations/<int:id>/preview')
@login_required
def simulation_preview(id):
    """Prévisualisation avant export PDF/Excel"""
    from models import Simulation, SimulationItem
    from sqlalchemy import text, inspect
    from decimal import Decimal
    
    try:
        simulation = Simulation.query.get_or_404(id)
    except Exception as e:
        if 'target_mode' in str(e) or 'target_margin_pct' in str(e):
            try:
                inspector = inspect(db.engine)
                columns = [col['name'] for col in inspector.get_columns('simulations')]
                select_cols = []
                for col in ['id', 'rate_usd', 'rate_eur', 'rate_xof', 'customs_gnf', 'handling_gnf', 
                           'others_gnf', 'transport_fixed_gnf', 'transport_per_kg_gnf', 'basis',
                           'truck_capacity_tons', 'is_completed', 'created_at', 'updated_at']:
                    if col in columns:
                        select_cols.append(col)
                if select_cols:
                    cols_str = ', '.join(select_cols)
                    result = db.session.execute(text(f"""
                        SELECT {cols_str}
                        FROM simulations 
                        WHERE id = :sim_id
                    """), {'sim_id': id})
                    row = result.fetchone()
                    if not row:
                        from flask import abort
                        abort(404)
                    row_dict = {}
                    for idx, col in enumerate(select_cols):
                        row_dict[col] = row[idx]
                    simulation = Simulation()
                    for col in select_cols:
                        if hasattr(simulation, col):
                            value = row_dict[col]
                            if col in ['rate_usd', 'rate_eur', 'rate_xof', 'customs_gnf', 'handling_gnf', 
                                      'others_gnf', 'transport_fixed_gnf', 'transport_per_kg_gnf', 
                                      'truck_capacity_tons']:
                                value = Decimal(str(value)) if value is not None else Decimal('0')
                            elif col == 'is_completed':
                                value = bool(value) if value is not None else False
                            elif col == 'basis' and value is None:
                                value = 'value'
                            setattr(simulation, col, value)
                else:
                    from flask import abort
                    abort(404)
            except Exception as e2:
                from flask import abort
                abort(404)
        else:
            raise
    
    items = SimulationItem.query.filter_by(simulation_id=id).all()
    
    # Calculer les totaux (identique à simulation_detail)
    total_purchase_value = Decimal('0')
    total_weight = Decimal('0')
    total_selling_value = Decimal('0')
    
    # Calculer le prix de revient pour chaque article (avec coûts logistiques)
    items_with_cost = []
    for item in items:
        # Convertir le prix d'achat en GNF selon la devise
        rate = simulation.rate_usd
        if item.purchase_currency == 'EUR':
            rate = simulation.rate_eur
        elif item.purchase_currency == 'XOF':
            rate = simulation.rate_xof if simulation.rate_xof else simulation.rate_usd
        
        purchase_price_gnf = Decimal(str(item.purchase_price)) * Decimal(str(rate))
        item_value = purchase_price_gnf * Decimal(str(item.quantity))
        item_weight = Decimal(str(item.quantity)) * Decimal(str(item.unit_weight_kg))
        
        total_purchase_value += item_value
        total_weight += item_weight
        total_selling_value += Decimal(str(item.selling_price_gnf)) * Decimal(str(item.quantity))
    
    # Calculer les coûts logistiques totaux
    total_fixed_costs = (
        Decimal(str(simulation.customs_gnf)) +
        Decimal(str(simulation.handling_gnf)) +
        Decimal(str(simulation.others_gnf)) +
        Decimal(str(simulation.transport_fixed_gnf))
    )
    
    total_variable_costs = Decimal(str(simulation.transport_per_kg_gnf)) * total_weight
    
    total_logistics = total_fixed_costs + total_variable_costs
    
    # Prix de revient total = prix d'achat + coûts logistiques
    total_cost = total_purchase_value + total_logistics
    
    # Marge totale = valeur de vente - prix de revient
    total_margin = total_selling_value - total_cost
    
    # Calculer le prix de revient pour chaque article
    for item in items:
        # Convertir le prix d'achat en GNF
        rate = simulation.rate_usd
        if item.purchase_currency == 'EUR':
            rate = simulation.rate_eur
        elif item.purchase_currency == 'XOF':
            rate = simulation.rate_xof if simulation.rate_xof else simulation.rate_usd
        
        purchase_price_gnf = Decimal(str(item.purchase_price)) * Decimal(str(rate))
        item_value = purchase_price_gnf * Decimal(str(item.quantity))
        item_weight = Decimal(str(item.quantity)) * Decimal(str(item.unit_weight_kg))
        
        # Répartir les coûts logistiques selon la base
        if simulation.basis == 'weight' and total_weight > 0:
            logistics_cost = (total_logistics * item_weight) / total_weight
        else:  # 'value' ou autre
            logistics_cost = (total_logistics * item_value) / total_purchase_value if total_purchase_value > 0 else Decimal('0')
        
        # Prix de revient par unité
        logistics_per_unit = logistics_cost / Decimal(str(item.quantity)) if item.quantity > 0 else Decimal('0')
        cost_price_per_unit = purchase_price_gnf + logistics_per_unit
        
        # Marge
        selling_price = Decimal(str(item.selling_price_gnf))
        margin = selling_price - cost_price_per_unit
        margin_pct = (margin / cost_price_per_unit * 100) if cost_price_per_unit > 0 else Decimal('0')
        
        items_with_cost.append({
            'item': item,
            'purchase_price_gnf': purchase_price_gnf,
            'logistics_per_unit': logistics_per_unit,
            'cost_price_per_unit': cost_price_per_unit,
            'total_cost': cost_price_per_unit * Decimal(str(item.quantity)),
            'selling_price': selling_price,
            'margin': margin,
            'margin_pct': margin_pct
        })
    
    return render_template('simulation_preview.html', 
                         simulation=simulation, 
                         items=items_with_cost,
                         total_purchase_value=total_purchase_value,
                         total_selling_value=total_selling_value,
                         total_logistics=total_logistics,
                         total_cost=total_cost,
                         total_margin=total_margin)

@app.route('/simulations/<int:id>/pdf')
@login_required
def simulation_pdf(id):
    """Générer un PDF pour une simulation"""
    from models import Simulation, SimulationItem
    from pdf_generator import PDFGenerator
    from flask import send_file, make_response, request
    from sqlalchemy import text, inspect
    
    # Récupérer la devise sélectionnée (par défaut GNF)
    currency = request.args.get('currency', 'GNF').upper()
    if currency not in ['GNF', 'USD', 'EUR', 'XOF']:
        currency = 'GNF'
    
    try:
        # Récupérer la simulation (avec gestion des colonnes manquantes)
        try:
            simulation = Simulation.query.get_or_404(id)
        except Exception as e:
            if 'target_mode' in str(e) or 'target_margin_pct' in str(e):
                inspector = inspect(db.engine)
                columns = [col['name'] for col in inspector.get_columns('simulations')]
                select_cols = []
                for col in ['id', 'rate_usd', 'rate_eur', 'rate_xof', 'customs_gnf', 'handling_gnf', 
                           'others_gnf', 'transport_fixed_gnf', 'transport_per_kg_gnf', 'basis',
                           'truck_capacity_tons', 'is_completed', 'created_at', 'updated_at']:
                    if col in columns:
                        select_cols.append(col)
                if select_cols:
                    cols_str = ', '.join(select_cols)
                    result = db.session.execute(text(f"""
                        SELECT {cols_str}
                        FROM simulations 
                        WHERE id = :sim_id
                    """), {'sim_id': id})
                    row = result.fetchone()
                    if not row:
                        from flask import abort
                        abort(404)
                    row_dict = {}
                    for idx, col in enumerate(select_cols):
                        row_dict[col] = row[idx]
                    simulation = Simulation()
                    for col in select_cols:
                        if hasattr(simulation, col):
                            value = row_dict[col]
                            if col in ['rate_usd', 'rate_eur', 'rate_xof', 'customs_gnf', 'handling_gnf', 
                                      'others_gnf', 'transport_fixed_gnf', 'transport_per_kg_gnf', 
                                      'truck_capacity_tons']:
                                value = Decimal(str(value)) if value is not None else Decimal('0')
                            elif col == 'is_completed':
                                value = bool(value) if value is not None else False
                            elif col == 'basis' and value is None:
                                value = 'value'
                            setattr(simulation, col, value)
                else:
                    from flask import abort
                    abort(404)
            else:
                raise
        
        # Récupérer les articles de la simulation
        simulation_items = SimulationItem.query.filter_by(simulation_id=id).all()
        
        if not simulation_items:
            flash('Aucun article dans cette simulation', 'warning')
            return redirect(url_for('simulation_preview', id=id))
        
        # Générer le PDF avec la devise sélectionnée
        pdf_gen = PDFGenerator()
        pdf_buffer = pdf_gen.generate_simulation_pdf(simulation, simulation_items, currency=currency)
        
        # Retourner le PDF
        filename = f'simulation_{id}_{datetime.now(UTC).strftime("%Y%m%d_%H%M%S")}.pdf'
        
        response = make_response(pdf_buffer.getvalue())
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"❌ Erreur lors de la génération du PDF: {e}")
        flash(f'Erreur lors de la génération du PDF: {str(e)}', 'error')
        return redirect(url_for('simulation_preview', id=id))

@app.route('/simulations/<int:id>/excel')
@login_required
def simulation_excel(id):
    """Générer un Excel pour une simulation"""
    from models import Simulation, SimulationItem
    from flask import send_file, make_response, request
    import pandas as pd
    from io import BytesIO
    from sqlalchemy import text, inspect
    
    # Récupérer la devise sélectionnée (par défaut GNF)
    currency = request.args.get('currency', 'GNF').upper()
    if currency not in ['GNF', 'USD', 'EUR', 'XOF']:
        currency = 'GNF'
    
    try:
        # Récupérer la simulation (avec gestion des colonnes manquantes)
        try:
            simulation = Simulation.query.get_or_404(id)
        except Exception as e:
            if 'target_mode' in str(e) or 'target_margin_pct' in str(e):
                inspector = inspect(db.engine)
                columns = [col['name'] for col in inspector.get_columns('simulations')]
                select_cols = []
                for col in ['id', 'rate_usd', 'rate_eur', 'rate_xof', 'customs_gnf', 'handling_gnf', 
                           'others_gnf', 'transport_fixed_gnf', 'transport_per_kg_gnf', 'basis',
                           'truck_capacity_tons', 'is_completed', 'created_at', 'updated_at']:
                    if col in columns:
                        select_cols.append(col)
                if select_cols:
                    cols_str = ', '.join(select_cols)
                    result = db.session.execute(text(f"""
                        SELECT {cols_str}
                        FROM simulations 
                        WHERE id = :sim_id
                    """), {'sim_id': id})
                    row = result.fetchone()
                    if not row:
                        from flask import abort
                        abort(404)
                    row_dict = {}
                    for idx, col in enumerate(select_cols):
                        row_dict[col] = row[idx]
                    simulation = Simulation()
                    for col in select_cols:
                        if hasattr(simulation, col):
                            value = row_dict[col]
                            if col in ['rate_usd', 'rate_eur', 'rate_xof', 'customs_gnf', 'handling_gnf', 
                                      'others_gnf', 'transport_fixed_gnf', 'transport_per_kg_gnf', 
                                      'truck_capacity_tons']:
                                value = Decimal(str(value)) if value is not None else Decimal('0')
                            elif col == 'is_completed':
                                value = bool(value) if value is not None else False
                            elif col == 'basis' and value is None:
                                value = 'value'
                            setattr(simulation, col, value)
                else:
                    from flask import abort
                    abort(404)
            else:
                raise
        
        items = SimulationItem.query.filter_by(simulation_id=id).all()
        
        if not items:
            flash('Aucun article dans cette simulation', 'warning')
            return redirect(url_for('simulation_preview', id=id))
        
        # Calculer les totaux et prix de revient (comme dans preview)
        total_purchase_value = Decimal('0')
        total_weight = Decimal('0')
        total_selling_value = Decimal('0')
        
        for item in items:
            rate = simulation.rate_usd
            if item.purchase_currency == 'EUR':
                rate = simulation.rate_eur
            elif item.purchase_currency == 'XOF':
                rate = simulation.rate_xof if simulation.rate_xof else simulation.rate_usd
            
            purchase_price_gnf = Decimal(str(item.purchase_price)) * Decimal(str(rate))
            item_value = purchase_price_gnf * Decimal(str(item.quantity))
            item_weight = Decimal(str(item.quantity)) * Decimal(str(item.unit_weight_kg))
            
            total_purchase_value += item_value
            total_weight += item_weight
            total_selling_value += Decimal(str(item.selling_price_gnf)) * Decimal(str(item.quantity))
        
        # Calculer les coûts logistiques
        total_fixed_costs = (
            Decimal(str(simulation.customs_gnf)) +
            Decimal(str(simulation.handling_gnf)) +
            Decimal(str(simulation.others_gnf)) +
            Decimal(str(simulation.transport_fixed_gnf))
        )
        total_variable_costs = Decimal(str(simulation.transport_per_kg_gnf)) * total_weight
        total_logistics = total_fixed_costs + total_variable_costs
        total_cost = total_purchase_value + total_logistics
        
        # Déterminer le taux de change pour la conversion
        exchange_rate = None
        if currency == 'USD':
            exchange_rate = float(simulation.rate_usd) if simulation.rate_usd else None
        elif currency == 'EUR':
            exchange_rate = float(simulation.rate_eur) if simulation.rate_eur else None
        elif currency == 'XOF':
            exchange_rate = float(simulation.rate_xof) if simulation.rate_xof else None
        
        def convert_amount(amount_gnf, rate):
            """Convertit un montant GNF vers la devise cible"""
            if currency == 'GNF' or not rate or rate == 0:
                return amount_gnf
            return amount_gnf / rate
        
        # Préparer les données pour Excel
        data = []
        for item in items:
            article_name = getattr(item, 'article_name', 'N/A')
            if hasattr(item, 'article') and item.article:
                article_name = item.article.name or article_name
            
            rate = simulation.rate_usd
            if item.purchase_currency == 'EUR':
                rate = simulation.rate_eur
            elif item.purchase_currency == 'XOF':
                rate = simulation.rate_xof if simulation.rate_xof else simulation.rate_usd
            
            purchase_price_gnf = float(item.purchase_price) * float(rate)
            item_value = purchase_price_gnf * float(item.quantity)
            item_weight = float(item.quantity) * float(item.unit_weight_kg)
            
            # Répartir les coûts logistiques
            if simulation.basis == 'weight' and total_weight > 0:
                logistics_cost = (float(total_logistics) * item_weight) / float(total_weight)
            else:
                logistics_cost = (float(total_logistics) * item_value) / float(total_purchase_value) if total_purchase_value > 0 else 0
            
            logistics_per_unit = logistics_cost / float(item.quantity) if item.quantity > 0 else 0
            cost_price_per_unit = purchase_price_gnf + logistics_per_unit
            
            selling_price_gnf = float(item.selling_price_gnf)
            quantity = float(item.quantity)
            total_purchase = purchase_price_gnf * quantity
            total_cost_item = cost_price_per_unit * quantity
            total_selling = selling_price_gnf * quantity
            margin = total_selling - total_cost_item
            
            data.append({
                'Article': article_name,
                'Quantité': quantity,
                'Prix Achat (GNF)': purchase_price_gnf,
                'Coûts Log. (GNF)': logistics_per_unit,
                'Prix de Revient (GNF)': cost_price_per_unit,
                'Prix Vente (GNF)': selling_price_gnf,
                'Total Achat (GNF)': total_purchase,
                'Total Coûts Log. (GNF)': logistics_cost,
                'Total Prix Revient (GNF)': total_cost_item,
                'Total Vente (GNF)': total_selling,
                'Marge (GNF)': margin,
                'Marge (%)': (margin / total_cost_item * 100) if total_cost_item > 0 else 0
            })
        
        # Créer le DataFrame
        df = pd.DataFrame(data)
        
        # Ajouter une ligne de total
        if len(df) > 0:
            total_row = pd.DataFrame([{
                'Article': 'TOTAL',
                'Quantité': '',
                f'Prix Achat ({currency})': '',
                f'Coûts Log. ({currency})': '',
                f'Prix de Revient ({currency})': '',
                f'Prix Vente ({currency})': '',
                f'Total Achat ({currency})': df[f'Total Achat ({currency})'].sum(),
                f'Total Coûts Log. ({currency})': df[f'Total Coûts Log. ({currency})'].sum(),
                f'Total Prix Revient ({currency})': df[f'Total Prix Revient ({currency})'].sum(),
                f'Total Vente ({currency})': df[f'Total Vente ({currency})'].sum(),
                f'Marge ({currency})': df[f'Marge ({currency})'].sum(),
                'Marge (%)': (df[f'Marge ({currency})'].sum() / df[f'Total Prix Revient ({currency})'].sum() * 100) if df[f'Total Prix Revient ({currency})'].sum() > 0 else 0
            }])
            df = pd.concat([df, total_row], ignore_index=True)
        
        # Créer le fichier Excel en mémoire
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Simulation', index=False)
        
        output.seek(0)
        filename = f'simulation_{id}_{datetime.now(UTC).strftime("%Y%m%d_%H%M%S")}.xlsx'
        
        response = make_response(output.getvalue())
        response.headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"❌ Erreur lors de la génération Excel: {e}")
        flash(f'Erreur lors de la génération Excel: {str(e)}', 'error')
        return redirect(url_for('simulation_preview', id=id))

@app.route('/simulations/<int:id>')
@login_required
def simulation_detail(id):
    """Détails d'une simulation"""
    from models import Simulation, SimulationItem
    from sqlalchemy import text, inspect
    from decimal import Decimal
    
    try:
        # Essayer d'abord avec ORM
        simulation = Simulation.query.get_or_404(id)
    except Exception as e:
        # Si erreur due à target_mode, utiliser SQL direct
        if 'target_mode' in str(e) or 'target_margin_pct' in str(e):
            try:
                inspector = inspect(db.engine)
                columns = [col['name'] for col in inspector.get_columns('simulations')]
                
                # Construire la liste des colonnes à sélectionner
                select_cols = []
                for col in ['id', 'rate_usd', 'rate_eur', 'rate_xof', 'customs_gnf', 'handling_gnf', 
                           'others_gnf', 'transport_fixed_gnf', 'transport_per_kg_gnf', 'basis',
                           'truck_capacity_tons', 'is_completed', 'created_at', 'updated_at']:
                    if col in columns:
                        select_cols.append(col)
                
                if select_cols:
                    cols_str = ', '.join(select_cols)
                    result = db.session.execute(text(f"""
                        SELECT {cols_str}
                        FROM simulations 
                        WHERE id = :sim_id
                    """), {'sim_id': id})
                    
                    row = result.fetchone()
                    if not row:
                        from flask import abort
                        abort(404)
                    
                    # Créer un objet Simulation à partir des résultats
                    row_dict = {}
                    for idx, col in enumerate(select_cols):
                        row_dict[col] = row[idx]
                    
                    simulation = Simulation()
                    for col in select_cols:
                        if hasattr(simulation, col):
                            value = row_dict[col]
                            if col in ['rate_usd', 'rate_eur', 'rate_xof', 'customs_gnf', 'handling_gnf', 
                                      'others_gnf', 'transport_fixed_gnf', 'transport_per_kg_gnf', 
                                      'truck_capacity_tons']:
                                value = Decimal(str(value)) if value is not None else Decimal('0')
                            elif col == 'is_completed':
                                value = bool(value) if value is not None else False
                            elif col == 'basis' and value is None:
                                value = 'value'
                            setattr(simulation, col, value)
                else:
                    from flask import abort
                    abort(404)
            except Exception as e2:
                print(f"⚠️ Erreur lors de la récupération SQL directe: {e2}")
                from flask import abort
                abort(404)
        else:
            raise
    
    items = SimulationItem.query.filter_by(simulation_id=id).all()
    
    # Calculer le prix de revient pour chaque article
    from decimal import Decimal
    
    # Calculer les totaux
    total_purchase_value = Decimal('0')
    total_weight = Decimal('0')
    
    for item in items:
        # Convertir le prix d'achat en GNF selon la devise
        rate = simulation.rate_usd
        if item.purchase_currency == 'EUR':
            rate = simulation.rate_eur
        elif item.purchase_currency == 'XOF':
            rate = simulation.rate_xof if simulation.rate_xof else simulation.rate_usd
        
        purchase_price_gnf = Decimal(str(item.purchase_price)) * Decimal(str(rate))
        item_value = purchase_price_gnf * Decimal(str(item.quantity))
        item_weight = Decimal(str(item.quantity)) * Decimal(str(item.unit_weight_kg))
        
        total_purchase_value += item_value
        total_weight += item_weight
    
    # Calculer les coûts logistiques totaux
    total_fixed_costs = (
        Decimal(str(simulation.customs_gnf)) +
        Decimal(str(simulation.handling_gnf)) +
        Decimal(str(simulation.others_gnf)) +
        Decimal(str(simulation.transport_fixed_gnf))
    )
    total_variable_costs = total_weight * Decimal(str(simulation.transport_per_kg_gnf))
    total_logistics_costs = total_fixed_costs + total_variable_costs
    
    # Calculer le prix de revient pour chaque article
    items_with_cost = []
    for item in items:
        # Convertir le prix d'achat en GNF
        rate = simulation.rate_usd
        if item.purchase_currency == 'EUR':
            rate = simulation.rate_eur
        elif item.purchase_currency == 'XOF':
            rate = simulation.rate_xof if simulation.rate_xof else simulation.rate_usd
        
        purchase_price_gnf = Decimal(str(item.purchase_price)) * Decimal(str(rate))
        item_value = purchase_price_gnf * Decimal(str(item.quantity))
        item_weight = Decimal(str(item.quantity)) * Decimal(str(item.unit_weight_kg))
        
        # Répartir les coûts logistiques selon la base
        logistics_cost = Decimal('0')
        if simulation.basis == 'value' and total_purchase_value > 0:
            logistics_cost = (item_value / total_purchase_value) * total_logistics_costs
        elif simulation.basis == 'weight' and total_weight > 0:
            logistics_cost = (item_weight / total_weight) * total_logistics_costs
        
        # Prix de revient par unité
        logistics_per_unit = logistics_cost / Decimal(str(item.quantity)) if item.quantity > 0 else Decimal('0')
        cost_price_per_unit = purchase_price_gnf + logistics_per_unit
        
        # Marge
        selling_price = Decimal(str(item.selling_price_gnf))
        margin = selling_price - cost_price_per_unit
        margin_pct = (margin / cost_price_per_unit * 100) if cost_price_per_unit > 0 else Decimal('0')
        
        items_with_cost.append({
            'item': item,
            'purchase_price_gnf': purchase_price_gnf,
            'logistics_per_unit': logistics_per_unit,
            'cost_price_per_unit': cost_price_per_unit,
            'total_cost': cost_price_per_unit * Decimal(str(item.quantity)),
            'selling_price': selling_price,
            'margin': margin,
            'margin_pct': margin_pct
        })
    
    return render_template('simulation_detail.html', 
                         simulation=simulation, 
                         items=items,
                         items_with_cost=items_with_cost,
                         total_logistics_costs=total_logistics_costs,
                         total_purchase_value=total_purchase_value)

@app.route('/simulations/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def simulation_edit(id):
    """Modifier une simulation"""
    from models import Simulation, SimulationItem, Article, Category
    from sqlalchemy import text, inspect
    from decimal import Decimal
    
    try:
        # Essayer d'abord avec ORM
        simulation = Simulation.query.get_or_404(id)
    except Exception as e:
        # Si erreur due à target_mode, utiliser SQL direct
        if 'target_mode' in str(e) or 'target_margin_pct' in str(e):
            try:
                inspector = inspect(db.engine)
                columns = [col['name'] for col in inspector.get_columns('simulations')]
                
                # Construire la liste des colonnes à sélectionner
                select_cols = []
                for col in ['id', 'rate_usd', 'rate_eur', 'rate_xof', 'customs_gnf', 'handling_gnf', 
                           'others_gnf', 'transport_fixed_gnf', 'transport_per_kg_gnf', 'basis',
                           'truck_capacity_tons', 'is_completed', 'created_at', 'updated_at']:
                    if col in columns:
                        select_cols.append(col)
                
                if select_cols:
                    cols_str = ', '.join(select_cols)
                    result = db.session.execute(text(f"""
                        SELECT {cols_str}
                        FROM simulations 
                        WHERE id = :sim_id
                    """), {'sim_id': id})
                    
                    row = result.fetchone()
                    if not row:
                        from flask import abort
                        abort(404)
                    
                    # Créer un objet Simulation à partir des résultats
                    row_dict = {}
                    for idx, col in enumerate(select_cols):
                        row_dict[col] = row[idx]
                    
                    simulation = Simulation()
                    for col in select_cols:
                        if hasattr(simulation, col):
                            value = row_dict[col]
                            if col in ['rate_usd', 'rate_eur', 'rate_xof', 'customs_gnf', 'handling_gnf', 
                                      'others_gnf', 'transport_fixed_gnf', 'transport_per_kg_gnf', 
                                      'truck_capacity_tons']:
                                value = Decimal(str(value)) if value is not None else Decimal('0')
                            elif col == 'is_completed':
                                value = bool(value) if value is not None else False
                            elif col == 'basis' and value is None:
                                value = 'value'
                            setattr(simulation, col, value)
                else:
                    from flask import abort
                    abort(404)
            except Exception as e2:
                print(f"⚠️ Erreur lors de la récupération SQL directe: {e2}")
                from flask import abort
                abort(404)
        else:
            raise
    
    if request.method == 'POST':
        try:
            # Mettre à jour tous les champs de la simulation
            simulation.rate_usd = Decimal(request.form.get('rate_usd', 0) or '0')
            simulation.rate_eur = Decimal(request.form.get('rate_eur', 0) or '0')
            simulation.rate_xof = Decimal(request.form.get('rate_xof', 0) or '0')
            simulation.truck_capacity_tons = Decimal(request.form.get('truck_capacity_tons', 0) or '0')
            simulation.basis = request.form.get('basis', 'value')
            
            # Coûts d'importation
            simulation.customs_gnf = Decimal(request.form.get('customs_gnf', 0) or '0')
            simulation.handling_gnf = Decimal(request.form.get('handling_gnf', 0) or '0')
            simulation.others_gnf = Decimal(request.form.get('others_gnf', 0) or '0')
            simulation.transport_fixed_gnf = Decimal(request.form.get('transport_fixed_gnf', 0) or '0')
            simulation.transport_per_kg_gnf = Decimal(request.form.get('transport_per_kg_gnf', 0) or '0')
            
            # Utiliser une mise à jour SQL directe pour éviter les problèmes de colonnes manquantes
            try:
                from sqlalchemy import text, inspect
                inspector = inspect(db.engine)
                columns = [col['name'] for col in inspector.get_columns('simulations')]
                
                # Construire la requête UPDATE avec seulement les colonnes qui existent
                update_fields = []
                update_params = {'sim_id': id}
                
                field_mapping = {
                    'rate_usd': simulation.rate_usd,
                    'rate_eur': simulation.rate_eur,
                    'rate_xof': simulation.rate_xof,
                    'truck_capacity_tons': simulation.truck_capacity_tons,
                    'basis': simulation.basis,
                    'customs_gnf': simulation.customs_gnf,
                    'handling_gnf': simulation.handling_gnf,
                    'others_gnf': simulation.others_gnf,
                    'transport_fixed_gnf': simulation.transport_fixed_gnf,
                    'transport_per_kg_gnf': simulation.transport_per_kg_gnf
                }
                
                for field, value in field_mapping.items():
                    if field in columns:
                        update_fields.append(f"{field} = :{field}")
                        if isinstance(value, Decimal):
                            update_params[field] = float(value)
                        else:
                            update_params[field] = value
                
                if update_fields:
                    update_sql = f"""
                        UPDATE simulations 
                        SET {', '.join(update_fields)}
                        WHERE id = :sim_id
                    """
                    db.session.execute(text(update_sql), update_params)
                    db.session.commit()
                    print(f"✅ Simulation {id} mise à jour avec succès")
                else:
                    # Fallback: utiliser ORM si aucune colonne valide
                    db.session.commit()
                    
            except Exception as e:
                print(f"⚠️ Erreur lors de la mise à jour SQL directe: {e}")
                # Essayer avec ORM
                try:
                    db.session.commit()
                except Exception as e2:
                    db.session.rollback()
                    print(f"❌ Erreur également avec ORM: {e2}")
                    flash(f'Erreur lors de la mise à jour: {str(e2)}', 'error')
                    return redirect(url_for('simulation_edit', id=id))
            
            flash('Simulation mise à jour avec succès', 'success')
            return redirect(url_for('simulation_detail', id=id))
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Erreur lors de la mise à jour de la simulation: {e}")
            import traceback
            traceback.print_exc()
            flash(f'Erreur lors de la mise à jour: {str(e)}', 'error')
            return redirect(url_for('simulation_edit', id=id))
    
    items = SimulationItem.query.filter_by(simulation_id=id).all()
    articles = Article.query.filter_by(is_active=True).all()
    categories = Category.query.all()
    return render_template('simulation_edit.html', simulation=simulation, items=items, articles=articles, categories=categories)

@app.route('/simulations/new', methods=['GET', 'POST'])
@login_required
def simulation_new():
    """Nouvelle simulation"""
    if request.method == 'POST':
        # Traitement de la soumission du formulaire
        try:
            from models import Simulation, SimulationItem, Article
            from decimal import Decimal
            
            # Récupérer les données du formulaire
            name = request.form.get('name', '').strip()
            description = request.form.get('description', '').strip()
            rate_usd = Decimal(request.form.get('rate_usd', '0') or '0')
            rate_eur = Decimal(request.form.get('rate_eur', '0') or '0')
            rate_xof = Decimal(request.form.get('rate_xof', '0') or '0')
            
            # Coûts d'importation
            customs_gnf = Decimal(request.form.get('customs_gnf', '0') or '0')
            handling_gnf = Decimal(request.form.get('handling_gnf', '0') or '0')
            others_gnf = Decimal(request.form.get('others_gnf', '0') or '0')
            transport_fixed_gnf = Decimal(request.form.get('transport_fixed_gnf', '0') or '0')
            transport_per_kg_gnf = Decimal(request.form.get('transport_per_kg_gnf', '0') or '0')
            truck_capacity_tons = Decimal(request.form.get('truck_capacity_tons', '0') or '0')
            target_margin_pct = Decimal(request.form.get('target_margin_pct', '0') or '0')
            basis = request.form.get('basis', 'value')
            
            # Créer la simulation
            # Construire les données de base
            sim_data = {
                'rate_usd': rate_usd,
                'rate_eur': rate_eur,
                'rate_xof': rate_xof,
                'customs_gnf': customs_gnf,
                'handling_gnf': handling_gnf,
                'others_gnf': others_gnf,
                'transport_fixed_gnf': transport_fixed_gnf,
                'transport_per_kg_gnf': transport_per_kg_gnf,
                'truck_capacity_tons': truck_capacity_tons,
                'target_margin_pct': target_margin_pct,
                'basis': basis,
                'is_completed': False
            }
            
            # Vérifier quelles colonnes existent dans la table
            try:
                from sqlalchemy import inspect
                inspector = inspect(db.engine)
                columns = [col['name'] for col in inspector.get_columns('simulations')]
                print(f"📋 Colonnes disponibles dans simulations: {columns}")
                
                # Ne garder que les colonnes qui existent dans la table
                sim_data_filtered = {}
                for key, value in sim_data.items():
                    if key in columns:
                        sim_data_filtered[key] = value
                    else:
                        print(f"⚠️ Colonne '{key}' non trouvée dans la table, ignorée")
                
                # Ajouter target_mode seulement s'il existe
                if 'target_mode' in columns:
                    sim_data_filtered['target_mode'] = 'none'
                # target_margin_pct est déjà dans sim_data, on le garde seulement s'il existe dans la table
                if 'target_margin_pct' not in columns and 'target_margin_pct' in sim_data_filtered:
                    sim_data_filtered.pop('target_margin_pct', None)
                
                sim_data = sim_data_filtered
                print(f"✅ Données de simulation filtrées: {list(sim_data.keys())}")
            except Exception as e:
                print(f"⚠️ Impossible de vérifier les colonnes: {e}")
                # Retirer target_mode et target_margin_pct par sécurité
                sim_data.pop('target_mode', None)
                # Ne pas retirer target_margin_pct ici car on ne peut pas vérifier
            
            # Créer la simulation en utilisant une insertion SQL directe pour éviter les problèmes de colonnes manquantes
            try:
                from sqlalchemy import text
                from datetime import datetime
                
                # Construire la requête SQL INSERT avec seulement les colonnes qui existent
                cols = list(sim_data.keys())
                
                # Construire la liste des placeholders et des paramètres
                placeholders_list = []
                params = []
                
                for key in cols:
                    placeholders_list.append(':col_' + key)  # Utiliser des noms uniques
                    value = sim_data[key]
                    # Convertir Decimal en float pour MySQL
                    if isinstance(value, Decimal):
                        params.append(('col_' + key, float(value)))
                    else:
                        params.append(('col_' + key, value))
                
                # Ajouter created_at si nécessaire
                if 'created_at' not in cols:
                    cols.append('created_at')
                    placeholders_list.append(':created_at')
                    params.append(('created_at', datetime.now(UTC)))
                
                cols_str = ', '.join(cols)
                placeholders_str = ', '.join(placeholders_list)
                
                sql = f"""
                    INSERT INTO simulations ({cols_str})
                    VALUES ({placeholders_str})
                """
                
                # Créer un dictionnaire de paramètres pour SQLAlchemy
                params_dict = dict(params)
                
                print(f"📝 Insertion SQL: {sql[:200]}...")
                print(f"📝 Colonnes: {cols_str}")
                print(f"📝 Paramètres: {list(params_dict.keys())}")
                
                # Exécuter l'insertion avec des paramètres nommés
                # Utiliser RETURNING pour PostgreSQL, LAST_INSERT_ID() pour MySQL
                from config import SQLALCHEMY_DATABASE_URI
                is_postgresql = SQLALCHEMY_DATABASE_URI.startswith('postgresql')
                
                if is_postgresql:
                    # Ajouter RETURNING id à la requête SQL
                    sql = sql.rstrip(';') + " RETURNING id"
                    result = db.session.execute(text(sql), params_dict)
                    db.session.flush()
                    simulation_id = result.scalar()
                else:
                    # MySQL
                    result = db.session.execute(text(sql), params_dict)
                    db.session.flush()
                    try:
                        simulation_id = result.lastrowid
                    except:
                        # Si lastrowid n'est pas disponible, utiliser une requête SELECT
                        id_result = db.session.execute(text("SELECT LAST_INSERT_ID() as id"))
                        simulation_id = id_result.fetchone()[0]
                
                print(f"📝 Simulation ID récupéré: {simulation_id}")
                
                # Récupérer la simulation créée (peut échouer si les colonnes ne correspondent pas)
                try:
                    simulation = Simulation.query.get(simulation_id)
                except:
                    simulation = None
                if not simulation:
                    # Si la récupération échoue, créer un objet Simulation minimal
                    simulation = Simulation()
                    simulation.id = simulation_id
                    for key, value in sim_data.items():
                        if hasattr(simulation, key):
                            setattr(simulation, key, value)
                    simulation.created_at = params_dict.get('created_at', datetime.now(UTC))
                
                print(f"✅ Simulation créée avec succès (ID: {simulation_id})")
                
            except Exception as e:
                print(f"❌ Erreur lors de l'insertion SQL directe: {e}")
                import traceback
                traceback.print_exc()
                # Essayer avec le modèle SQLAlchemy en dernier recours
                try:
                    db.session.rollback()
                    simulation = Simulation(**sim_data)
                    db.session.add(simulation)
                    db.session.flush()
                    print(f"✅ Simulation créée via ORM (ID: {simulation.id})")
                except Exception as e2:
                    print(f"❌ Erreur également avec ORM: {e2}")
                    raise
            
            # Traiter les articles (si présents dans le formulaire)
            article_ids = request.form.getlist('article_ids[]')
            quantities = request.form.getlist('quantities[]')
            selling_prices = request.form.getlist('selling_prices[]')
            
            for i, article_id in enumerate(article_ids):
                if article_id and i < len(quantities) and i < len(selling_prices):
                    try:
                        article = Article.query.get(int(article_id))
                        if article:
                            item = SimulationItem(
                                simulation_id=simulation.id,
                                article_id=article.id,
                                quantity=Decimal(quantities[i] or '0'),
                                selling_price_gnf=Decimal(selling_prices[i] or '0'),
                                purchase_price=article.purchase_price,
                                purchase_currency=article.purchase_currency,
                                unit_weight_kg=article.unit_weight_kg
                            )
                            db.session.add(item)
                    except (ValueError, IndexError):
                        continue
            
            db.session.commit()
            print(f"✅ Simulation créée avec succès (ID: {simulation.id}, Date: {simulation.created_at})")
            print(f"📦 {len(article_ids)} articles ajoutés à la simulation")
            flash('Simulation créée avec succès', 'success')
            return redirect('/simulations')
        except Exception as e:
            db.session.rollback()
            print(f"❌ Erreur lors de la création de la simulation: {e}")
            import traceback
            traceback.print_exc()
            flash(f'Erreur lors de la création de la simulation: {str(e)}', 'error')
            # Recharger le formulaire avec les données
            try:
                from models import Category, Article
                articles = Article.query.filter_by(is_active=True).order_by(Article.name).all()
                categories = Category.query.all()
                return render_template('simulation_new_ultra.html', 
                                     articles=articles,
                                     categories=categories)
            except Exception as e2:
                print(f"❌ Erreur lors du rechargement du formulaire: {e2}")
                return redirect('/simulations/new')
    
    # GET - Afficher le formulaire
    try:
        from models import Category, Article
        from sqlalchemy import or_
        
        # Compter tous les articles (actifs et inactifs) pour debug
        total_articles = Article.query.count()
        active_articles_count = Article.query.filter_by(is_active=True).count()
        print(f"📊 Total articles dans la base: {total_articles}")
        print(f"📊 Articles actifs: {active_articles_count}")
        
        categories = Category.query.all()
        print(f"📊 Catégories: {len(categories)}")
        
        # Charger les articles actifs, avec ou sans catégorie
        # MySQL gère les NULL différemment, utiliser un ordre simple
        articles = Article.query.filter_by(is_active=True).order_by(Article.name).all()
        
        print(f"✅ {len(articles)} articles chargés pour la simulation")
        
        # Debug: afficher les détails des articles
        if len(articles) > 0:
            print("📋 Détails des articles chargés:")
            for article in articles[:5]:  # Afficher les 5 premiers
                print(f"   - ID: {article.id}, Nom: {article.name}, Catégorie: {article.category.name if article.category else 'Aucune'}, Actif: {article.is_active}")
        else:
            print("⚠️ Aucun article actif trouvé dans la base de données")
            print("💡 Astuce: Créez des articles dans la section 'Articles' ou 'Référentiels > Articles de stock'")
        
        return render_template('simulation_new_ultra.html', 
                                 articles=articles,
                                 categories=categories)
    except Exception as e:
        print(f"⚠️ Erreur lors du chargement du formulaire: {e}")
        import traceback
        traceback.print_exc()
        # Essayer de charger au moins les articles sans catégorie
        try:
            articles = Article.query.filter_by(is_active=True).all()
            categories = Category.query.all()
            print(f"✅ {len(articles)} articles chargés (mode secours)")
            return render_template('simulation_new_ultra.html', 
                                 articles=articles,
                                 categories=categories)
        except Exception as e2:
            print(f"⚠️ Erreur lors du chargement de secours: {e2}")
            import traceback
            traceback.print_exc()
            return render_template('simulation_new_ultra.html', 
                                 articles=[],
                                 categories=[])

@app.route('/articles')
@login_required
def articles_list():
    """Liste des articles avec pagination, recherche et optimisation"""
    try:
        from models import Article, Category
        from sqlalchemy.orm import joinedload
        from sqlalchemy import or_
        
        # Paramètres de pagination
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        
        # Paramètres de recherche et filtres
        search = request.args.get('search', '').strip()
        category_filter = request.args.get('category', '').strip()
        price_min = request.args.get('price_min', type=float)
        price_max = request.args.get('price_max', type=float)
        base_currency = request.args.get('base_currency', 'GNF').strip().upper()  # Devise de base pour l'affichage
        
        # Requête de base avec optimisation N+1 et filtrage SQL
        query = Article.query.options(
            joinedload(Article.category)
        ).filter_by(is_active=True)
        
        # Recherche par nom, SKU (ID), description
        if search:
            query = query.filter(
                or_(
                    Article.name.ilike(f'%{search}%'),
                    Article.id.cast(db.String).ilike(f'%{search}%')
                )
            )
        
        # Filtre par catégorie
        if category_filter:
            query = query.join(Category).filter(Category.name == category_filter)
        
        # Filtre par prix min
        if price_min is not None:
            query = query.filter(Article.purchase_price >= price_min)
        
        # Filtre par prix max
        if price_max is not None:
            query = query.filter(Article.purchase_price <= price_max)
        
        # Pagination
        pagination = query.order_by(Article.name).paginate(
            page=page, per_page=per_page, error_out=False
        )
        articles = pagination.items
        
        # Statistiques globales (sur TOUS les articles actifs)
        stats_query = Article.query.filter_by(is_active=True)
        total_articles = stats_query.count()
        
        # Calculer le prix moyen et la valeur totale sur tous les articles actifs
        # Convertir en devise de base si nécessaire
        all_active_articles = Article.query.filter_by(is_active=True).all()
        if all_active_articles:
            # Récupérer les taux de change depuis la dernière simulation
            from models import Simulation
            rate_usd = Decimal('8500')
            rate_eur = Decimal('9200')
            rate_xof = Decimal('1')  # XOF = GNF généralement
            
            try:
                last_simulation = Simulation.query.order_by(Simulation.created_at.desc()).first()
                if last_simulation:
                    rate_usd = Decimal(str(last_simulation.rate_usd)) if last_simulation.rate_usd else Decimal('8500')
                    rate_eur = Decimal(str(last_simulation.rate_eur)) if last_simulation.rate_eur else Decimal('9200')
                    rate_xof = Decimal(str(last_simulation.rate_xof)) if last_simulation.rate_xof else Decimal('1')
            except:
                pass
            
            # Convertir tous les prix en devise de base
            prices_in_base = []
            total_value_in_base = Decimal('0')
            
            for art in all_active_articles:
                price = Decimal(str(art.purchase_price))
                currency = art.purchase_currency or 'USD'
                
                # Convertir en GNF d'abord
                if currency == 'USD':
                    price_gnf = price * rate_usd
                elif currency == 'EUR':
                    price_gnf = price * rate_eur
                elif currency == 'XOF' or currency == 'FCFA':
                    price_gnf = price * rate_xof
                else:  # GNF ou autre
                    price_gnf = price
                
                # Convertir de GNF vers la devise de base
                if base_currency == 'USD':
                    price_base = price_gnf / rate_usd if rate_usd > 0 else price_gnf
                elif base_currency == 'EUR':
                    price_base = price_gnf / rate_eur if rate_eur > 0 else price_gnf
                elif base_currency == 'XOF':
                    price_base = price_gnf / rate_xof if rate_xof > 0 else price_gnf
                else:  # GNF (par défaut)
                    price_base = price_gnf
                
                prices_in_base.append(float(price_base))
                total_value_in_base += price_base
            
            avg_price = sum(prices_in_base) / len(prices_in_base) if prices_in_base else 0
            total_value = float(total_value_in_base)
        else:
            avg_price = 0
            total_value = 0
        
        # Charger toutes les catégories pour le filtre
        categories = Category.query.order_by(Category.name).all()
        
        return render_template('articles_unified.html', 
                             articles=articles,
                             categories=categories,
                             pagination=pagination,
                             search=search,
                             category_filter=category_filter,
                             price_min=price_min,
                             price_max=price_max,
                             base_currency=base_currency,
                             avg_price=avg_price,
                             total_value=total_value,
                             total_articles=total_articles)
    except Exception as e:
        print(f"Erreur lors du chargement des articles: {e}")
        import traceback
        traceback.print_exc()
        return render_template('articles_unified.html', 
                             articles=[],
                             categories=[],
                             pagination=None,
                             search='',
                             category_filter='',
                             price_min=None,
                             price_max=None,
                             base_currency='GNF',
                             avg_price=0,
                             total_value=0,
                             total_articles=0)

@app.route('/articles/new', methods=['GET', 'POST'])
@login_required
def article_new():
    """Nouvel article"""
    if request.method == 'POST':
        try:
            from models import Article, Category
            from decimal import Decimal
            from utils_articles import save_article_image
            
            # Récupérer les données du formulaire
            name = request.form.get('name', '').strip()
            # Le formulaire envoie le nom de la catégorie, pas l'ID
            category_name = request.form.get('category', '').strip()
            purchase_price = request.form.get('purchase_price', '0') or '0'
            purchase_currency = request.form.get('purchase_currency', 'USD') or 'USD'
            # Le formulaire utilise "weight" au lieu de "unit_weight_kg"
            unit_weight_kg = request.form.get('weight', '0') or request.form.get('unit_weight_kg', '0') or '0'
            # Par défaut, les articles sont actifs (True) sauf si explicitement désactivés
            is_active = request.form.get('is_active') not in ('off', 'false', '0', False)
            
            # Convertir le nom de catégorie en ID
            category_id = None
            if category_name:
                category = Category.query.filter_by(name=category_name).first()
                if category:
                    category_id = category.id
                else:
                    flash(f'Catégorie "{category_name}" non trouvée', 'warning')
            
            # Validation
            if not name:
                flash('Le nom de l\'article est obligatoire', 'error')
                categories = Category.query.all()
                return render_template('article_new_unified.html', 
                                     categories=categories,
                                     depots=[],
                                     vehicles=[])
            
            # Vérifier si l'article existe déjà
            existing = Article.query.filter_by(name=name).first()
            if existing:
                flash(f'Un article avec le nom "{name}" existe déjà', 'error')
                categories = Category.query.all()
                return render_template('article_new_unified.html', 
                                     categories=categories,
                                     depots=[],
                                     vehicles=[])
            
            # Créer l'article
            article = Article(
                name=name,
                category_id=int(category_id) if category_id else None,
                purchase_price=Decimal(purchase_price),
                purchase_currency=purchase_currency,
                unit_weight_kg=Decimal(unit_weight_kg),
                is_active=is_active
            )
            
            db.session.add(article)
            db.session.flush()  # Pour obtenir l'ID de l'article
            
            # Gérer l'upload de l'image
            if 'image' in request.files:
                image_file = request.files['image']
                if image_file and image_file.filename:
                    try:
                        image_data = save_article_image(image_file, article.id)
                        if image_data:
                            article.image_path = image_data['file_path']
                    except Exception as e:
                        flash(f'Erreur lors de l\'upload de l\'image: {str(e)}', 'warning')
            
            db.session.commit()
            
            flash(f'Article "{name}" créé avec succès', 'success')
            return redirect(url_for('articles_list'))
            
        except Exception as e:
            db.session.rollback()
            print(f"⚠️ Erreur lors de la création de l'article: {e}")
            import traceback
            traceback.print_exc()
            flash(f'Erreur lors de la création de l\'article: {str(e)}', 'error')
            categories = Category.query.all()
            return render_template('article_new_unified.html', 
                                 categories=categories,
                                 depots=[],
                                 vehicles=[])
    
    # GET - Afficher le formulaire
    try:
        from models import Category
        
        categories = Category.query.all()
        return render_template('article_new_unified.html', 
                             categories=categories,
                             depots=[],
                             vehicles=[])
    except Exception as e:
        print(f"Erreur lors du chargement du formulaire: {e}")
        return render_template('article_new_unified.html', 
                             categories=[],
                             depots=[],
                             vehicles=[])

@app.route('/articles/<int:id>')
@login_required
def article_detail(id):
    """Détail d'un article"""
    try:
        from models import Article, Category
        from sqlalchemy.orm import joinedload
        
        # Charger l'article avec sa catégorie (optimisation N+1)
        article = Article.query.options(
            joinedload(Article.category)
        ).get_or_404(id)
        
        return render_template('article_detail.html', article=article)
    except Exception as e:
        print(f"Erreur lors du chargement de l'article: {e}")
        import traceback
        traceback.print_exc()
        flash('Article non trouvé', 'error')
        return redirect(url_for('articles_list'))

@app.route('/articles/export/excel')
@login_required
def articles_export_excel():
    """Export Excel de la liste des articles avec filtres appliqués"""
    from auth import has_permission
    if not has_permission(current_user, 'articles.read'):
        flash("Vous n'avez pas la permission d'exporter les données.", "error")
        return redirect(url_for('articles_list'))
    
    import pandas as pd
    from io import BytesIO
    from flask import send_file
    from sqlalchemy import or_
    
    # Récupérer les mêmes filtres que articles_list
    search = request.args.get('search', '').strip()
    category_filter = request.args.get('category', '').strip()
    price_min = request.args.get('price_min', type=float)
    price_max = request.args.get('price_max', type=float)
    
    try:
        from models import Article, Category
        from sqlalchemy.orm import joinedload
        
        # Construire la requête (même logique que articles_list)
        query = Article.query.options(
            joinedload(Article.category)
        ).filter_by(is_active=True)
        
        # Appliquer les filtres
        if search:
            query = query.filter(
                or_(
                    Article.name.ilike(f'%{search}%'),
                    Article.id.cast(db.String).ilike(f'%{search}%')
                )
            )
        
        if category_filter:
            query = query.join(Category).filter(Category.name == category_filter)
        
        if price_min is not None:
            query = query.filter(Article.purchase_price >= price_min)
        
        if price_max is not None:
            query = query.filter(Article.purchase_price <= price_max)
        
        # Récupérer tous les articles (sans pagination pour l'export)
        articles = query.order_by(Article.name).all()
        
        # Préparer les données pour Excel
        data = []
        for article in articles:
            data.append({
                'ID': article.id,
                'Nom': article.name,
                'Catégorie': article.category.name if article.category else '',
                'Prix d\'achat': float(article.purchase_price) if article.purchase_price else 0,
                'Devise': article.purchase_currency or 'USD',
                'Poids (kg)': float(article.unit_weight_kg) if article.unit_weight_kg else 0,
                'Actif': 'Oui' if article.is_active else 'Non',
                'Date de création': article.created_at.strftime('%Y-%m-%d %H:%M:%S') if article.created_at else '',
                'Date de modification': article.updated_at.strftime('%Y-%m-%d %H:%M:%S') if article.updated_at else ''
            })
        
        # Créer le DataFrame
        df = pd.DataFrame(data)
        
        # Créer le fichier Excel en mémoire
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Articles', index=False)
            
            # Ajuster la largeur des colonnes
            worksheet = writer.sheets['Articles']
            for idx, col in enumerate(df.columns):
                max_length = max(
                    df[col].astype(str).map(len).max(),
                    len(col)
                )
                worksheet.column_dimensions[chr(65 + idx)].width = min(max_length + 2, 50)
        
        output.seek(0)
        
        # Générer le nom du fichier avec la date
        filename = f'articles_export_{datetime.now(UTC).strftime("%Y%m%d_%H%M%S")}.xlsx'
        
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=filename
        )
    
    except Exception as e:
        print(f"❌ Erreur lors de l'export Excel: {e}")
        import traceback
        traceback.print_exc()
        flash(f'Erreur lors de l\'export Excel: {str(e)}', 'error')
        return redirect(url_for('articles_list'))

@app.route('/articles/import', methods=['GET', 'POST'])
@login_required
def articles_import():
    """Import de articles depuis Excel/CSV"""
    from auth import has_permission, is_admin
    if not has_permission(current_user, 'articles.create') and not is_admin(current_user):
        flash('Vous n\'avez pas la permission d\'importer des articles. Seuls les administrateurs et utilisateurs avec la permission articles.create peuvent importer.', 'error')
        return redirect(url_for('articles_list'))
    
    from models import Article, Category
    import pandas as pd
    import os
    from werkzeug.utils import secure_filename
    from decimal import Decimal
    
    if request.method == 'GET':
        return render_template('articles_import.html')
    
    if request.method == 'POST':
        try:
            file = request.files.get('file')
            if not file or file.filename == '':
                flash('Veuillez sélectionner un fichier', 'error')
                return redirect(url_for('articles_import'))
            
            # Sauvegarder le fichier temporairement
            upload_dir = os.path.join(app.instance_path, 'uploads')
            os.makedirs(upload_dir, exist_ok=True)
            filename = secure_filename(file.filename)
            filepath = os.path.join(upload_dir, filename)
            file.save(filepath)
            
            # Lire le fichier
            try:
                if filename.endswith('.csv'):
                    df = pd.read_csv(filepath, encoding='utf-8')
                elif filename.endswith(('.xlsx', '.xls')):
                    df = pd.read_excel(filepath)
                else:
                    flash('Format de fichier non supporté. Utilisez .xlsx, .xls ou .csv', 'error')
                    os.remove(filepath)
                    return redirect(url_for('articles_import'))
            except Exception as e:
                flash(f'Erreur lors de la lecture du fichier: {str(e)}', 'error')
                os.remove(filepath)
                return redirect(url_for('articles_import'))
            
            # Normaliser les noms de colonnes (minuscules, espaces remplacés par underscores)
            df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_').str.replace('é', 'e').str.replace('è', 'e')
            
            # Colonnes requises (flexibles)
            required_cols = ['nom', 'name']
            has_name = any(col in df.columns for col in required_cols)
            if not has_name:
                flash('Colonne "Nom" ou "Name" manquante. Le fichier doit contenir au moins le nom de l\'article.', 'error')
                os.remove(filepath)
                return redirect(url_for('articles_import'))
            
            # Mapper les colonnes possibles
            name_col = next((col for col in ['nom', 'name', 'article', 'article_name'] if col in df.columns), None)
            category_col = next((col for col in ['categorie', 'category', 'categorie_name', 'category_name'] if col in df.columns), None)
            price_col = next((col for col in ['prix', 'price', 'purchase_price', 'prix_achat', 'prix_d_achat'] if col in df.columns), None)
            currency_col = next((col for col in ['devise', 'currency', 'purchase_currency', 'monnaie'] if col in df.columns), None)
            weight_col = next((col for col in ['poids', 'weight', 'unit_weight_kg', 'poids_kg', 'poids_en_kg'] if col in df.columns), None)
            active_col = next((col for col in ['actif', 'active', 'is_active'] if col in df.columns), None)
            
            # Mode de traitement
            update_mode = request.form.get('update_mode', 'skip')  # 'skip', 'update', 'create_new'
            
            success_count = 0
            error_count = 0
            errors = []
            
            # Traiter chaque ligne
            for idx, row in df.iterrows():
                try:
                    # Récupérer les valeurs
                    name = str(row[name_col]).strip() if name_col and pd.notna(row.get(name_col)) else None
                    if not name or name == 'nan':
                        error_count += 1
                        errors.append(f"Ligne {idx + 2}: Nom d'article manquant")
                        continue
                    
                    # Catégorie
                    category_name = None
                    if category_col and pd.notna(row.get(category_col)):
                        category_name = str(row[category_col]).strip()
                    
                    category_id = None
                    if category_name:
                        category = Category.query.filter_by(name=category_name).first()
                        if not category:
                            # Créer la catégorie si elle n'existe pas
                            category = Category(name=category_name)
                            db.session.add(category)
                            db.session.flush()
                        category_id = category.id
                    
                    # Prix
                    purchase_price = Decimal('0')
                    if price_col and pd.notna(row.get(price_col)):
                        try:
                            purchase_price = Decimal(str(row[price_col]))
                        except:
                            purchase_price = Decimal('0')
                    
                    # Devise
                    purchase_currency = 'USD'
                    if currency_col and pd.notna(row.get(currency_col)):
                        currency_val = str(row[currency_col]).strip().upper()
                        if currency_val in ['USD', 'EUR', 'GNF', 'XOF', 'FCFA']:
                            purchase_currency = currency_val
                    
                    # Poids
                    unit_weight_kg = Decimal('0')
                    if weight_col and pd.notna(row.get(weight_col)):
                        try:
                            unit_weight_kg = Decimal(str(row[weight_col]))
                        except:
                            unit_weight_kg = Decimal('0')
                    
                    # Actif
                    is_active = True
                    if active_col and pd.notna(row.get(active_col)):
                        active_val = str(row[active_col]).strip().lower()
                        is_active = active_val in ['oui', 'yes', 'true', '1', 'actif', 'active']
                    
                    # Vérifier si l'article existe déjà
                    existing = Article.query.filter_by(name=name).first()
                    
                    if existing:
                        if update_mode == 'skip':
                            continue  # Ignorer les articles existants
                        elif update_mode == 'update':
                            # Mettre à jour l'article existant
                            existing.category_id = category_id
                            existing.purchase_price = purchase_price
                            existing.purchase_currency = purchase_currency
                            existing.unit_weight_kg = unit_weight_kg
                            existing.is_active = is_active
                            existing.updated_at = datetime.now(UTC)
                            success_count += 1
                        elif update_mode == 'create_new':
                            # Créer un nouvel article avec un nom modifié
                            name = f"{name} (Import {datetime.now(UTC).strftime('%Y%m%d')})"
                            article = Article(
                                name=name,
                                category_id=category_id,
                                purchase_price=purchase_price,
                                purchase_currency=purchase_currency,
                                unit_weight_kg=unit_weight_kg,
                                is_active=is_active
                            )
                            db.session.add(article)
                            success_count += 1
                    else:
                        # Créer un nouvel article
                        article = Article(
                            name=name,
                            category_id=category_id,
                            purchase_price=purchase_price,
                            purchase_currency=purchase_currency,
                            unit_weight_kg=unit_weight_kg,
                            is_active=is_active
                        )
                        db.session.add(article)
                        success_count += 1
                
                except Exception as e:
                    error_count += 1
                    errors.append(f"Ligne {idx + 2}: {str(e)}")
                    continue
            
            # Commit toutes les modifications
            db.session.commit()
            
            # Nettoyer le fichier temporaire
            try:
                os.remove(filepath)
            except:
                pass
            
            # Message de succès
            if success_count > 0:
                flash(f'Import réussi : {success_count} article(s) traité(s) avec succès.', 'success')
            if error_count > 0:
                flash(f'Import terminé avec {error_count} erreur(s). Voir les détails ci-dessous.', 'warning')
                if errors:
                    flash(f'Erreurs: {"; ".join(errors[:10])}', 'warning')  # Afficher les 10 premières erreurs
            
            return redirect(url_for('articles_list'))
        
        except Exception as e:
            db.session.rollback()
            print(f"❌ Erreur lors de l'import: {e}")
            import traceback
            traceback.print_exc()
            flash(f'Erreur lors de l\'import: {str(e)}', 'error')
            return redirect(url_for('articles_import'))

@app.route('/articles/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def article_edit(id):
    """Éditer un article"""
    try:
        from models import Article, Category
        from decimal import Decimal
        
        article = Article.query.get_or_404(id)
        
        if request.method == 'POST':
            try:
                # Récupérer les données du formulaire
                name = request.form.get('name', '').strip()
                category_name = request.form.get('category', '').strip()
                purchase_price = request.form.get('purchase_price', '0') or '0'
                purchase_currency = request.form.get('purchase_currency', 'USD') or 'USD'
                unit_weight_kg = request.form.get('weight', '0') or request.form.get('unit_weight_kg', '0') or '0'
                is_active = request.form.get('is_active') == 'on' or request.form.get('is_active') == 'true'
                
                # Convertir le nom de catégorie en ID
                category_id = None
                if category_name:
                    category = Category.query.filter_by(name=category_name).first()
                    if category:
                        category_id = category.id
                
                # Validation
                if not name:
                    flash('Le nom de l\'article est obligatoire', 'error')
                    categories = Category.query.all()
                    return render_template('article_new_unified.html', 
                                         article=article,
                                         categories=categories,
                                         depots=[],
                                         vehicles=[])
                
                # Vérifier si un autre article avec le même nom existe
                existing = Article.query.filter_by(name=name).first()
                if existing and existing.id != article.id:
                    flash(f'Un article avec le nom "{name}" existe déjà', 'error')
                    categories = Category.query.all()
                    return render_template('article_new_unified.html', 
                                         article=article,
                                         categories=categories,
                                         depots=[],
                                         vehicles=[])
                
                # Mettre à jour l'article
                article.name = name
                article.category_id = category_id
                article.purchase_price = Decimal(purchase_price)
                article.purchase_currency = purchase_currency
                article.unit_weight_kg = Decimal(unit_weight_kg)
                article.is_active = is_active
                
                # Gérer l'upload de l'image
                if 'image' in request.files:
                    image_file = request.files['image']
                    if image_file and image_file.filename:
                        try:
                            from utils_articles import save_article_image, delete_article_image
                            # Supprimer l'ancienne image si elle existe
                            if article.image_path:
                                delete_article_image(article.image_path)
                            # Sauvegarder la nouvelle image
                            image_data = save_article_image(image_file, article.id)
                            if image_data:
                                article.image_path = image_data['file_path']
                        except Exception as e:
                            flash(f'Erreur lors de l\'upload de l\'image: {str(e)}', 'warning')
                
                db.session.commit()
                
                flash(f'Article "{name}" modifié avec succès', 'success')
                return redirect(url_for('articles_list'))
                
            except Exception as e:
                db.session.rollback()
                print(f"⚠️ Erreur lors de la modification de l'article: {e}")
                import traceback
                traceback.print_exc()
                flash(f'Erreur lors de la modification de l\'article: {str(e)}', 'error')
                categories = Category.query.all()
                return render_template('article_new_unified.html', 
                                     article=article,
                                     categories=categories,
                                     depots=[],
                                     vehicles=[])
        
        # GET - Afficher le formulaire
        categories = Category.query.all()
        return render_template('article_new_unified.html', 
                             article=article,
                             categories=categories,
                             depots=[],
                             vehicles=[])
    except Exception as e:
        print(f"Erreur lors du chargement du formulaire d'édition: {e}")
        flash('Article non trouvé', 'error')
        return redirect(url_for('articles_list'))

# Route de vérification des simulations
@app.route('/api/check-simulations')
@login_required
def check_simulations():
    """Vérifier les simulations dans la base de données"""
    try:
        from sqlalchemy import text, inspect
        
        # Vérifier les colonnes de la table
        inspector = inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns('simulations')]
        
        # Compter les simulations
        result = db.session.execute(text("SELECT COUNT(*) as count FROM simulations"))
        count = result.fetchone()[0]
        
        # Récupérer les simulations si elles existent
        simulations_data = []
        if count > 0:
            select_cols = ', '.join(columns)
            result = db.session.execute(text(f"""
                SELECT {select_cols}
                FROM simulations 
                ORDER BY created_at DESC
                LIMIT 10
            """))
            
            for row in result:
                row_dict = {}
                for i, col in enumerate(columns):
                    row_dict[col] = row[i]
                
                # Compter les items
                sim_id = row_dict.get('id')
                items_count = 0
                if sim_id:
                    items_result = db.session.execute(text(f"""
                        SELECT COUNT(*) as count 
                        FROM simulation_items 
                        WHERE simulation_id = {sim_id}
                    """))
                    items_count = items_result.fetchone()[0]
                
                simulations_data.append({
                    'id': row_dict.get('id'),
                    'created_at': str(row_dict.get('created_at', '')),
                    'rate_usd': float(row_dict.get('rate_usd', 0)),
                    'rate_eur': float(row_dict.get('rate_eur', 0)),
                    'is_completed': bool(row_dict.get('is_completed', False)),
                    'items_count': items_count
                })
        
        from flask import jsonify
        return jsonify({
            'success': True,
            'columns': columns,
            'total_count': count,
            'simulations': simulations_data
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        from flask import jsonify
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# API Routes
@app.route('/api/simulations')
@login_required
def api_simulations():
    """API des simulations"""
    try:
        from models import Simulation, SimulationItem
        
        try:
            simulations = Simulation.query.order_by(Simulation.created_at.desc()).all()
        except Exception as e:
            print(f"⚠️ Erreur lors de la récupération des simulations: {e}")
            simulations = []
        simulations_data = []
        
        for simulation in simulations:
            items = SimulationItem.query.filter_by(simulation_id=simulation.id).all()
            
            simulations_data.append({
                'id': simulation.id,
                'name': getattr(simulation, 'name', f'Simulation {simulation.id}'),
                'created_at': simulation.created_at,
                'rate_usd': float(simulation.rate_usd) if simulation.rate_usd else 8500.0,
                'rate_eur': float(simulation.rate_eur) if simulation.rate_eur else 9200.0,
                'truck_capacity_tons': float(simulation.truck_capacity_tons) if simulation.truck_capacity_tons else 25.0,
                'status': 'completed' if simulation.is_completed else 'active',
                'items': [
                    {
                        'name': item.article.name if item.article else 'Article inconnu',
                        'quantity': float(item.quantity),
                        'price': float(item.selling_price_gnf)
                    } for item in items
                ],
                'items_count': len(items),
                'margin_pct': 20.0,  # Calculer la vraie marge
                'total_weight': sum(float(item.unit_weight_kg * item.quantity) for item in items),
                'total_value': sum(float(item.selling_price_gnf * item.quantity) for item in items),
                'total_revenue': sum(float(item.selling_price_gnf * item.quantity) for item in items),
                'total_cost': sum(float(item.purchase_price * item.quantity) for item in items)
            })
        
        return jsonify(simulations_data)
        
    except Exception as e:
        print(f"Erreur API simulations: {e}")
        return jsonify([])

@app.route('/api/articles')
@login_required
def api_articles():
    """API des articles"""
    try:
        from models import Article, Category
        
        articles = Article.query.filter_by(is_active=True).all()
        articles_data = []
        
        for article in articles:
            articles_data.append({
                'id': article.id,
                'name': article.name,
                'category': article.category.name if article.category else 'Sans catégorie',
                'purchase_price': float(article.purchase_price),
                'purchase_currency': article.purchase_currency,
                'unit_weight': float(article.unit_weight_kg),
                'selling_price': 0,
                'is_active': article.is_active
            })
        
        return jsonify(articles_data)
        
    except Exception as e:
        print(f"Erreur API articles: {e}")
        return jsonify([])

# Routes Forecast & Ventes
from models import Forecast, ForecastItem, StockItem, StockOutgoing, StockOutgoingDetail
from datetime import datetime, date, UTC, timedelta
from sqlalchemy import func, and_, or_

def calculate_realized_sales(stock_item_id, start_date, end_date):
    """Calculer les ventes réalisées pour un article sur une période"""
    # Récupérer toutes les sorties de stock (ventes) dans la période
    outgoings = StockOutgoing.query.filter(
        and_(
            StockOutgoing.outgoing_date >= start_date,
            StockOutgoing.outgoing_date <= end_date,
            StockOutgoing.status == 'completed'
        )
    ).all()
    
    total_quantity = Decimal('0')
    total_value = Decimal('0')
    count = 0
    
    for outgoing in outgoings:
        # Récupérer les détails pour cet article
        details = StockOutgoingDetail.query.filter_by(
            outgoing_id=outgoing.id,
            stock_item_id=stock_item_id
        ).all()
        
        for detail in details:
            total_quantity += Decimal(str(detail.quantity))
            if detail.unit_price_gnf:
                total_value += Decimal(str(detail.quantity)) * Decimal(str(detail.unit_price_gnf))
            count += 1
    
    # Calculer la moyenne réalisée
    avg_quantity = total_quantity / count if count > 0 else Decimal('0')
    
    return {
        'total_quantity': float(total_quantity),
        'avg_quantity': float(avg_quantity),
        'total_value': float(total_value),
        'count': count
    }

@app.route('/forecast')
@login_required
def forecast_dashboard():
    """Dashboard des prévisions"""
    from models import Forecast
    from sqlalchemy import inspect, text
    from auth import is_admin_or_supervisor
    
    try:
        # Filtrer les prévisions selon le rôle
        forecast_query = Forecast.query
        if not is_admin_or_supervisor(current_user) and current_user.role and current_user.role.code == 'commercial':
            # Les commerciaux ne voient que leurs propres prévisions
            commercial_name = current_user.full_name or current_user.username
            forecast_query = forecast_query.filter(
                or_(
                    Forecast.commercial_name == commercial_name,
                    Forecast.created_by_id == current_user.id
                )
            )
        
        # Statistiques
        total_forecasts = forecast_query.count()
        active_forecasts = forecast_query.filter_by(status='active').count()
        completed_forecasts = forecast_query.filter_by(status='completed').count()
        
        # Calculer le taux de précision moyen
        forecasts_with_data = forecast_query.filter(
            Forecast.total_forecast_value > 0
        ).all()
        
        avg_accuracy = 0
        if forecasts_with_data:
            total_accuracy = sum(f.realization_percentage for f in forecasts_with_data)
            avg_accuracy = total_accuracy / len(forecasts_with_data)
        
        # Ventes prévisionnelles totales
        total_forecast_value = db.session.query(func.sum(Forecast.total_forecast_value)).filter(
            forecast_query.whereclause if hasattr(forecast_query, 'whereclause') else True
        ).scalar() or Decimal('0')
        
    except Exception as e:
        # Si erreur due à des colonnes manquantes, utiliser SQL direct
        if 'currency' in str(e) or 'rate_usd' in str(e) or 'rate_eur' in str(e) or 'rate_xof' in str(e):
            try:
                inspector = inspect(db.engine)
                columns = [col['name'] for col in inspector.get_columns('forecasts')]
                
                # Construire la requête avec seulement les colonnes existantes
                select_cols = ['id', 'name', 'status', 'total_forecast_value', 'total_realized_value']
                for col in ['currency', 'rate_usd', 'rate_eur', 'rate_xof']:
                    if col in columns:
                        select_cols.append(col)
                
                cols_str = ', '.join(select_cols)
                # Filtrer pour les commerciaux
                where_clause = ""
                if not is_admin_or_supervisor(current_user) and current_user.role and current_user.role.code == 'commercial':
                    commercial_name = current_user.full_name or current_user.username
                    where_clause = f"WHERE commercial_name = '{commercial_name}' OR created_by_id = {current_user.id}"
                
                result = db.session.execute(text(f"""
                    SELECT COUNT(*) as total,
                           SUM(CASE WHEN status = 'active' THEN 1 ELSE 0 END) as active,
                           SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed,
                           SUM(total_forecast_value) as total_value
                    FROM forecasts
                    {where_clause}
                """))
                
                row = result.fetchone()
                total_forecasts = row[0] if row else 0
                active_forecasts = row[1] if row else 0
                completed_forecasts = row[2] if row else 0
                total_forecast_value = Decimal(str(row[3])) if row and row[3] else Decimal('0')
                avg_accuracy = 0  # Ne peut pas calculer sans les données complètes
                
            except Exception as e2:
                print(f"⚠️ Erreur lors de la récupération SQL directe: {e2}")
                total_forecasts = 0
                active_forecasts = 0
                completed_forecasts = 0
                avg_accuracy = 0
                total_forecast_value = Decimal('0')
        else:
            raise
    
    return render_template('forecast_dashboard_ultra_modern.html',
                         total_forecasts=total_forecasts,
                         active_forecasts=active_forecasts,
                         completed_forecasts=completed_forecasts,
                         avg_accuracy=round(avg_accuracy, 1),
                         total_forecast_value=total_forecast_value)

@app.route('/forecast/new', methods=['GET', 'POST'])
@login_required
def forecast_new():
    """Nouvelle prévision (admin et superviseur uniquement)"""
    # #region agent log
    import json, time
    try:
        with open('/Users/dantawi/Documents/mini_flask_import_profitability/.cursor/debug.log', 'a') as f:
            f.write(json.dumps({"id":"log_entry","timestamp":int(time.time()*1000),"location":"app.py:2744","message":"forecast_new entry","data":{"user_id":current_user.id if current_user else None,"user_role":current_user.role.code if (current_user and current_user.role) else None,"method":request.method},"sessionId":"debug-session","runId":"test-permissions","hypothesisId":"A"}) + "\n")
    except: pass
    # #endregion
    from auth import is_admin_or_supervisor
    is_allowed = is_admin_or_supervisor(current_user)
    # #region agent log
    try:
        with open('/Users/dantawi/Documents/mini_flask_import_profitability/.cursor/debug.log', 'a') as f:
            f.write(json.dumps({"id":"log_entry","timestamp":int(time.time()*1000),"location":"app.py:2750","message":"forecast_new permission check","data":{"is_allowed":is_allowed,"user_role":current_user.role.code if (current_user and current_user.role) else None},"sessionId":"debug-session","runId":"test-permissions","hypothesisId":"A"}) + "\n")
    except: pass
    # #endregion
    if not is_allowed:
        flash('Vous n\'avez pas la permission de créer des prévisions. Seuls les administrateurs et superviseurs peuvent créer des prévisions.', 'error')
        return redirect(url_for('forecast_dashboard'))
    
    from models import StockItem, Simulation
    from sqlalchemy import inspect, text
    
    if request.method == 'POST':
        try:
            # Récupérer la devise choisie
            currency = request.form.get('currency', 'GNF')
            
            # Récupérer les taux de change (depuis la dernière simulation ou valeurs par défaut)
            rate_usd = Decimal('8500')
            rate_eur = Decimal('9200')
            rate_xof = Decimal('0')
            
            try:
                last_simulation = Simulation.query.order_by(Simulation.created_at.desc()).first()
                if last_simulation:
                    rate_usd = Decimal(str(last_simulation.rate_usd)) if last_simulation.rate_usd else Decimal('8500')
                    rate_eur = Decimal(str(last_simulation.rate_eur)) if last_simulation.rate_eur else Decimal('9200')
                    rate_xof = Decimal(str(last_simulation.rate_xof)) if last_simulation.rate_xof else Decimal('0')
            except Exception as e:
                # Si erreur due à des colonnes manquantes, utiliser SQL direct
                if 'target_mode' in str(e) or 'target_margin_pct' in str(e):
                    try:
                        inspector = inspect(db.engine)
                        columns = [col['name'] for col in inspector.get_columns('simulations')]
                        
                        select_cols = ['id', 'rate_usd', 'rate_eur', 'rate_xof', 'created_at']
                        cols_str = ', '.join(select_cols)
                        
                        result = db.session.execute(text(f"""
                            SELECT {cols_str}
                            FROM simulations 
                            ORDER BY created_at DESC 
                            LIMIT 1
                        """))
                        
                        row = result.fetchone()
                        if row:
                            rate_usd = Decimal(str(row[1])) if row[1] else Decimal('8500')
                            rate_eur = Decimal(str(row[2])) if row[2] else Decimal('9200')
                            rate_xof = Decimal(str(row[3])) if row[3] else Decimal('0')
                    except Exception as e2:
                        print(f"⚠️ Erreur lors de la récupération SQL directe des taux: {e2}")
                        # Utiliser les valeurs par défaut
                else:
                    print(f"⚠️ Erreur lors de la récupération des taux: {e}")
                    # Utiliser les valeurs par défaut
            
            # Créer la prévision - utiliser SQL direct si les colonnes n'existent pas
            commercial_name = request.form.get('commercial_name', '').strip()
            try:
                forecast = Forecast(
                    name=request.form.get('name'),
                    description=request.form.get('description'),
                    start_date=datetime.strptime(request.form.get('start_date'), '%Y-%m-%d').date(),
                    end_date=datetime.strptime(request.form.get('end_date'), '%Y-%m-%d').date(),
                    status='draft',
                    commercial_name=commercial_name if commercial_name else None,
                    currency=currency,
                    rate_usd=rate_usd,
                    rate_eur=rate_eur,
                    rate_xof=rate_xof,
                    created_by_id=current_user.id
                )
                db.session.add(forecast)
                db.session.flush()
            except Exception as e:
                # Si erreur due à des colonnes manquantes, utiliser SQL direct
                if 'currency' in str(e) or 'rate_usd' in str(e) or 'commercial_name' in str(e):
                    try:
                        inspector = inspect(db.engine)
                        columns = [col['name'] for col in inspector.get_columns('forecasts')]
                        
                        # Construire l'INSERT avec seulement les colonnes existantes
                        insert_cols = ['name', 'description', 'start_date', 'end_date', 'status', 
                                       'total_forecast_value', 'total_realized_value', 'created_by_id', 'created_at']
                        insert_values = []
                        params = {
                            'name': request.form.get('name'),
                            'description': request.form.get('description'),
                            'start_date': datetime.strptime(request.form.get('start_date'), '%Y-%m-%d').date(),
                            'end_date': datetime.strptime(request.form.get('end_date'), '%Y-%m-%d').date(),
                            'status': 'draft',
                            'total_forecast_value': 0,
                            'total_realized_value': 0,
                            'created_by_id': current_user.id,
                            'created_at': datetime.now(UTC)
                        }
                        
                        # Ajouter les colonnes optionnelles si elles existent
                        if 'currency' in columns:
                            insert_cols.append('currency')
                            params['currency'] = currency
                        if 'commercial_name' in columns:
                            insert_cols.append('commercial_name')
                            params['commercial_name'] = commercial_name if commercial_name else None
                        if 'rate_usd' in columns:
                            insert_cols.append('rate_usd')
                            params['rate_usd'] = float(rate_usd)
                        if 'rate_eur' in columns:
                            insert_cols.append('rate_eur')
                            params['rate_eur'] = float(rate_eur)
                        if 'rate_xof' in columns:
                            insert_cols.append('rate_xof')
                            params['rate_xof'] = float(rate_xof)
                        
                        cols_str = ', '.join(insert_cols)
                        placeholders = ', '.join([f':{col}' for col in insert_cols])
                        
                        # Utiliser RETURNING pour PostgreSQL, lastrowid pour MySQL
                        from config import SQLALCHEMY_DATABASE_URI
                        is_postgresql = SQLALCHEMY_DATABASE_URI.startswith('postgresql')
                        
                        if is_postgresql:
                            sql = f"""
                                INSERT INTO forecasts ({cols_str})
                                VALUES ({placeholders})
                                RETURNING id
                            """
                            result = db.session.execute(text(sql), params)
                            db.session.flush()
                            forecast_id = result.scalar()
                        else:
                            result = db.session.execute(text(f"""
                                INSERT INTO forecasts ({cols_str})
                                VALUES ({placeholders})
                            """), params)
                            db.session.flush()
                            forecast_id = result.lastrowid
                        
                        # Créer un objet minimal pour continuer
                        forecast = Forecast()
                        forecast.id = forecast_id
                        forecast.name = params['name']
                        forecast.description = params.get('description')
                        forecast.start_date = params['start_date']
                        forecast.end_date = params['end_date']
                        forecast.status = params['status']
                        forecast.total_forecast_value = Decimal('0')
                        forecast.total_realized_value = Decimal('0')
                        if 'currency' in columns:
                            forecast.currency = currency
                        if 'rate_usd' in columns:
                            forecast.rate_usd = rate_usd
                        if 'rate_eur' in columns:
                            forecast.rate_eur = rate_eur
                        if 'rate_xof' in columns:
                            forecast.rate_xof = rate_xof
                    except Exception as e2:
                        db.session.rollback()
                        print(f"❌ Erreur lors de la création SQL directe: {e2}")
                        raise
                else:
                    raise
            
            # Traiter les articles
            article_ids = request.form.getlist('article_ids[]')
            quantities = request.form.getlist('quantities[]')
            prices = request.form.getlist('prices[]')
            
            total_forecast_value = Decimal('0')
            
            for i, article_id in enumerate(article_ids):
                if article_id and quantities[i] and prices[i]:
                    # Le prix est dans la devise choisie, on le stocke en GNF pour la cohérence
                    price_in_currency = Decimal(prices[i])
                    
                    # Convertir en GNF selon la devise
                    if currency == 'USD':
                        price_gnf = price_in_currency * rate_usd
                    elif currency == 'EUR':
                        price_gnf = price_in_currency * rate_eur
                    elif currency == 'XOF':
                        price_gnf = price_in_currency * rate_xof if rate_xof > 0 else price_in_currency * Decimal('0.0667')  # Taux approximatif
                    else:  # GNF
                        price_gnf = price_in_currency
                    
                    item = ForecastItem(
                        forecast_id=forecast.id,
                        stock_item_id=int(article_id),
                        forecast_quantity=Decimal(quantities[i]),
                        selling_price_gnf=price_gnf  # Toujours stocké en GNF
                    )
                    db.session.add(item)
                    # Calculer la valeur dans la devise choisie
                    forecast_value_in_currency = price_in_currency * Decimal(quantities[i])
                    total_forecast_value += forecast_value_in_currency
            
            # Convertir la valeur totale en GNF pour le stockage
            total_forecast_value_gnf = total_forecast_value
            if currency == 'USD':
                total_forecast_value_gnf = total_forecast_value * rate_usd
            elif currency == 'EUR':
                total_forecast_value_gnf = total_forecast_value * rate_eur
            elif currency == 'XOF':
                total_forecast_value_gnf = total_forecast_value * rate_xof if rate_xof > 0 else total_forecast_value * Decimal('0.0667')
            
            # Mettre à jour la valeur totale
            try:
                forecast.total_forecast_value = total_forecast_value_gnf
                db.session.commit()
            except Exception as e:
                # Si erreur, utiliser SQL direct pour mettre à jour
                if 'currency' in str(e) or 'rate_usd' in str(e):
                    try:
                        inspector = inspect(db.engine)
                        columns = [col['name'] for col in inspector.get_columns('forecasts')]
                        
                        update_fields = ['total_forecast_value = :total_forecast_value']
                        update_params = {
                            'forecast_id': forecast.id,
                            'total_forecast_value': float(total_forecast_value_gnf)
                        }
                        
                        # Mettre à jour les colonnes optionnelles si elles existent
                        if 'currency' in columns:
                            update_fields.append('currency = :currency')
                            update_params['currency'] = currency
                        if 'rate_usd' in columns:
                            update_fields.append('rate_usd = :rate_usd')
                            update_params['rate_usd'] = float(rate_usd)
                        if 'rate_eur' in columns:
                            update_fields.append('rate_eur = :rate_eur')
                            update_params['rate_eur'] = float(rate_eur)
                        if 'rate_xof' in columns:
                            update_fields.append('rate_xof = :rate_xof')
                            update_params['rate_xof'] = float(rate_xof)
                        
                        db.session.execute(text(f"""
                            UPDATE forecasts 
                            SET {', '.join(update_fields)}
                            WHERE id = :forecast_id
                        """), update_params)
                        db.session.commit()
                    except Exception as e2:
                        db.session.rollback()
                        print(f"⚠️ Erreur lors de la mise à jour SQL directe: {e2}")
                        # Commit quand même les items
                        db.session.commit()
                else:
                    db.session.rollback()
                    raise
            
            flash('Prévision créée avec succès', 'success')
            return redirect(url_for('forecast_detail', id=forecast.id))
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Erreur lors de la création de la prévision: {e}")
            import traceback
            traceback.print_exc()
            flash(f'Erreur lors de la création: {str(e)}', 'error')
    
    from models import User
    stock_items = StockItem.query.filter_by(is_active=True).order_by(StockItem.name).all()
    users = User.query.order_by(User.username).all()
    return render_template('forecast_new_ultra_modern.html', stock_items=stock_items, users=users)

@app.route('/forecast/<int:id>/preview')
@login_required
def forecast_preview(id):
    """Prévisualisation avant export PDF/Excel"""
    from models import Forecast, ForecastItem
    from decimal import Decimal
    
    forecast = Forecast.query.get_or_404(id)
    items = ForecastItem.query.filter_by(forecast_id=id).all()
    
    # Calculer les totaux
    total_forecast = Decimal('0')
    total_realization = Decimal('0')
    
    for item in items:
        total_forecast += Decimal(str(item.forecast_quantity or 0))
        total_realization += Decimal(str(item.realized_quantity or 0))
    
    total_variance = total_realization - total_forecast
    total_rate = (float(total_realization) / float(total_forecast) * 100) if total_forecast > 0 else 0
    
    return render_template('forecast_preview.html', 
                         forecast=forecast, 
                         items=items,
                         total_forecast=total_forecast,
                         total_realization=total_realization,
                         total_variance=total_variance,
                         total_rate=total_rate)

@app.route('/forecast/<int:id>/pdf')
@login_required
def forecast_pdf(id):
    """Générer un PDF pour une prévision"""
    from models import Forecast, ForecastItem
    from pdf_generator import PDFGenerator
    from flask import make_response, request
    
    # Récupérer la devise sélectionnée (par défaut GNF)
    currency = request.args.get('currency', 'GNF').upper()
    if currency not in ['GNF', 'USD', 'EUR', 'XOF']:
        currency = 'GNF'
    
    try:
        # Récupérer la prévision
        forecast = Forecast.query.get_or_404(id)
        
        # Récupérer les articles de la prévision
        forecast_items = ForecastItem.query.filter_by(forecast_id=id).all()
        
        if not forecast_items:
            flash('Aucun article dans cette prévision', 'warning')
            return redirect(url_for('forecast_preview', id=id))
        
        # Générer le PDF avec la devise sélectionnée
        pdf_gen = PDFGenerator()
        pdf_buffer = pdf_gen.generate_forecast_pdf(forecast, forecast_items, currency=currency)
        
        # Retourner le PDF
        filename = f'prevision_{id}_{datetime.now(UTC).strftime("%Y%m%d_%H%M%S")}.pdf'
        
        response = make_response(pdf_buffer.getvalue())
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"❌ Erreur lors de la génération du PDF: {e}")
        flash(f'Erreur lors de la génération du PDF: {str(e)}', 'error')
        return redirect(url_for('forecast_preview', id=id))

@app.route('/forecast/<int:id>/excel')
@login_required
def forecast_excel(id):
    """Générer un Excel pour une prévision"""
    from models import Forecast, ForecastItem
    from flask import make_response, request
    import pandas as pd
    from io import BytesIO
    from decimal import Decimal
    
    # Récupérer la devise sélectionnée (par défaut GNF)
    currency = request.args.get('currency', 'GNF').upper()
    if currency not in ['GNF', 'USD', 'EUR', 'XOF']:
        currency = 'GNF'
    
    try:
        forecast = Forecast.query.get_or_404(id)
        items = ForecastItem.query.filter_by(forecast_id=id).all()
        
        if not items:
            flash('Aucun article dans cette prévision', 'warning')
            return redirect(url_for('forecast_preview', id=id))
        
        # Déterminer le taux de change pour la conversion
        exchange_rate = None
        if hasattr(forecast, 'rate_usd') and forecast.rate_usd:
            if currency == 'USD':
                exchange_rate = float(forecast.rate_usd)
            elif currency == 'EUR' and hasattr(forecast, 'rate_eur') and forecast.rate_eur:
                exchange_rate = float(forecast.rate_eur)
            elif currency == 'XOF' and hasattr(forecast, 'rate_xof') and forecast.rate_xof:
                exchange_rate = float(forecast.rate_xof)
        
        def convert_amount(amount_gnf, rate):
            """Convertit un montant GNF vers la devise cible"""
            if currency == 'GNF' or not rate or rate == 0:
                return amount_gnf
            return amount_gnf / rate
        
        # Préparer les données
        data = []
        for item in items:
            article_name = getattr(item, 'article_name', 'N/A')
            if hasattr(item, 'article') and item.article:
                article_name = item.article.name or article_name
            elif hasattr(item, 'stock_item') and item.stock_item:
                article_name = item.stock_item.name or article_name
            
            forecast_qty = float(item.forecast_quantity or 0)
            realization_qty = float(item.realized_quantity or 0)
            variance = realization_qty - forecast_qty
            rate = (realization_qty / forecast_qty * 100) if forecast_qty > 0 else 0
            
            # Pour les prévisions, on peut convertir les valeurs si nécessaire
            # Ici on garde les quantités en unités, mais on peut ajouter des colonnes de valeur si besoin
            data.append({
                'Article': article_name,
                'Prévision': forecast_qty,
                'Réalisation': realization_qty,
                'Écart': variance,
                'Taux (%)': rate
            })
        
        df = pd.DataFrame(data)
        
        # Ajouter une ligne de total
        if len(df) > 0:
            total_row = pd.DataFrame([{
                'Article': 'TOTAL',
                'Prévision': df['Prévision'].sum(),
                'Réalisation': df['Réalisation'].sum(),
                'Écart': df['Écart'].sum(),
                'Taux (%)': (df['Réalisation'].sum() / df['Prévision'].sum() * 100) if df['Prévision'].sum() > 0 else 0
            }])
            df = pd.concat([df, total_row], ignore_index=True)
        
        # Créer le fichier Excel
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Prévision', index=False)
        
        output.seek(0)
        filename = f'prevision_{id}_{datetime.now(UTC).strftime("%Y%m%d_%H%M%S")}.xlsx'
        
        response = make_response(output.getvalue())
        response.headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"❌ Erreur lors de la génération Excel: {e}")
        flash(f'Erreur lors de la génération Excel: {str(e)}', 'error')
        return redirect(url_for('forecast_preview', id=id))

@app.route('/forecast/<int:id>')
@login_required
def forecast_detail(id):
    """Détails d'une prévision avec tableau récapitulatif"""
    # #region agent log
    import json, time
    try:
        with open('/Users/dantawi/Documents/mini_flask_import_profitability/.cursor/debug.log', 'a') as f:
            f.write(json.dumps({"id":"log_entry","timestamp":int(time.time()*1000),"location":"app.py:3165","message":"forecast_detail entry","data":{"forecast_id":id,"user_id":current_user.id if current_user else None,"user_role":current_user.role.code if (current_user and current_user.role) else None},"sessionId":"debug-session","runId":"test-permissions","hypothesisId":"C"}) + "\n")
    except: pass
    # #endregion
    from sqlalchemy import inspect, text
    from auth import is_admin_or_supervisor
    
    try:
        forecast = Forecast.query.get_or_404(id)
        
        # Vérifier que le commercial peut voir cette prévision
        if not is_admin_or_supervisor(current_user) and current_user.role and current_user.role.code == 'commercial':
            commercial_name = current_user.full_name or current_user.username
            has_access = forecast.commercial_name == commercial_name or forecast.created_by_id == current_user.id
            # #region agent log
            try:
                with open('/Users/dantawi/Documents/mini_flask_import_profitability/.cursor/debug.log', 'a') as f:
                    f.write(json.dumps({"id":"log_entry","timestamp":int(time.time()*1000),"location":"app.py:3178","message":"forecast_detail access check","data":{"has_access":has_access,"commercial_name":commercial_name,"forecast_commercial_name":forecast.commercial_name,"forecast_created_by_id":forecast.created_by_id,"user_id":current_user.id},"sessionId":"debug-session","runId":"test-permissions","hypothesisId":"C"}) + "\n")
            except: pass
            # #endregion
            if not has_access:
                flash('Vous n\'avez pas accès à cette prévision', 'error')
                return redirect(url_for('forecast_list'))
        
        # Récupérer les taux de change
        rate_usd = forecast.rate_usd if hasattr(forecast, 'rate_usd') and forecast.rate_usd else Decimal('8500')
        rate_eur = forecast.rate_eur if hasattr(forecast, 'rate_eur') and forecast.rate_eur else Decimal('9200')
        rate_xof = forecast.rate_xof if hasattr(forecast, 'rate_xof') and forecast.rate_xof else Decimal('0')
        currency = forecast.currency if hasattr(forecast, 'currency') and forecast.currency else 'GNF'
        
    except Exception as e:
        # Si erreur due à des colonnes manquantes, utiliser SQL direct
        if 'currency' in str(e) or 'rate_usd' in str(e):
            try:
                inspector = inspect(db.engine)
                columns = [col['name'] for col in inspector.get_columns('forecasts')]
                
                select_cols = ['id', 'name', 'description', 'start_date', 'end_date', 'status', 
                              'total_forecast_value', 'total_realized_value', 'created_by_id']
                for col in ['currency', 'rate_usd', 'rate_eur', 'rate_xof']:
                    if col in columns:
                        select_cols.append(col)
                
                cols_str = ', '.join(select_cols)
                result = db.session.execute(text(f"""
                    SELECT {cols_str}
                    FROM forecasts 
                    WHERE id = :forecast_id
                """), {'forecast_id': id})
                
                row = result.fetchone()
                if not row:
                    from flask import abort
                    abort(404)
                
                # Créer un objet Forecast minimal
                row_dict = {}
                for idx, col in enumerate(select_cols):
                    row_dict[col] = row[idx]
                
                forecast = Forecast()
                forecast.id = row_dict['id']
                forecast.name = row_dict['name']
                forecast.description = row_dict.get('description')
                forecast.start_date = row_dict['start_date']
                forecast.end_date = row_dict['end_date']
                forecast.status = row_dict['status']
                forecast.total_forecast_value = Decimal(str(row_dict['total_forecast_value']))
                forecast.total_realized_value = Decimal(str(row_dict.get('total_realized_value', 0)))
                
                # Récupérer les taux et devise
                rate_usd = Decimal(str(row_dict.get('rate_usd', 8500))) if 'rate_usd' in row_dict and row_dict.get('rate_usd') else Decimal('8500')
                rate_eur = Decimal(str(row_dict.get('rate_eur', 9200))) if 'rate_eur' in row_dict and row_dict.get('rate_eur') else Decimal('9200')
                rate_xof = Decimal(str(row_dict.get('rate_xof', 0))) if 'rate_xof' in row_dict and row_dict.get('rate_xof') else Decimal('0')
                currency = row_dict.get('currency', 'GNF') if 'currency' in row_dict else 'GNF'
                
            except Exception as e2:
                print(f"⚠️ Erreur lors de la récupération SQL directe: {e2}")
                from flask import abort
                abort(404)
        else:
            raise
    
    # Fonction de conversion GNF vers devise choisie
    def convert_to_currency(value_gnf, target_currency):
        if target_currency == 'USD' and rate_usd > 0:
            return value_gnf / rate_usd
        elif target_currency == 'EUR' and rate_eur > 0:
            return value_gnf / rate_eur
        elif target_currency == 'XOF':
            if rate_xof > 0:
                return value_gnf / rate_xof
            else:
                return value_gnf / Decimal('0.0667')  # Taux approximatif
        else:  # GNF
            return value_gnf
    
    # Calculer les réalisations pour chaque article
    items_with_realizations = []
    total_realized_value_gnf = Decimal('0')
    
    for item in forecast.items:
        # Calculer les ventes réalisées
        realized = calculate_realized_sales(
            item.stock_item_id,
            forecast.start_date,
            forecast.end_date
        )
        
        # Mettre à jour les réalisations (toujours en GNF dans la DB)
        item.realized_quantity = Decimal(str(realized['avg_quantity']))
        item.realized_value_gnf = Decimal(str(realized['total_value']))
        
        # Convertir les valeurs pour l'affichage dans la devise choisie
        item.forecast_value_currency = convert_to_currency(Decimal(str(item.forecast_value)), currency)
        item.realized_value_currency = convert_to_currency(item.realized_value_gnf, currency)
        
        # Calculer le prix unitaire dans la devise choisie
        item.selling_price_currency = convert_to_currency(item.selling_price_gnf, currency)
        
        # Calculer le pourcentage de réalisation
        forecast_value_gnf = Decimal(str(item.forecast_value))  # S'assurer que c'est un Decimal
        if forecast_value_gnf > 0:
            item.realization_percentage = (float(item.realized_value_gnf) / float(forecast_value_gnf)) * 100
        else:
            item.realization_percentage = Decimal('0')
        
        # Calculer les autres métriques
        # EQ (Equivalent Quantity) - pour l'instant = realized_quantity
        item.equivalent_quantity = item.realized_quantity
        
        # EVal (Evaluated Value) - dans la devise choisie
        item.evaluated_value_currency = convert_to_currency(item.realized_value_gnf, currency)
        
        # EVALCFA (en CFA, taux approximatif 1 GNF = 0.0667 CFA)
        item.evaluated_value_cfa = item.realized_value_gnf * Decimal('0.0667')
        
        # ECART A 50% (écart par rapport à 50% de réalisation) - dans la devise choisie
        target_50_gnf = forecast_value_gnf * Decimal('0.5')
        item.deviation_50pct_currency = convert_to_currency(item.realized_value_gnf - target_50_gnf, currency)
        
        # QAF (Quantité disponible) - récupérer depuis le stock
        from models import DepotStock, VehicleStock
        depot_stock = sum(float(ds.quantity) for ds in DepotStock.query.filter_by(stock_item_id=item.stock_item_id).all())
        vehicle_stock = sum(float(vs.quantity) for vs in VehicleStock.query.filter_by(stock_item_id=item.stock_item_id).all())
        item.quantity_available = Decimal(str(depot_stock + vehicle_stock))
        
        # Nb Jr (nombre de jours dans la période)
        days = (forecast.end_date - forecast.start_date).days + 1
        item.number_of_days = days
        
        total_realized_value_gnf += item.realized_value_gnf
        items_with_realizations.append(item)
    
    # Mettre à jour les totaux de la prévision (en GNF)
    forecast.total_realized_value = total_realized_value_gnf
    db.session.commit()
    
    # Calculer les totaux dans la devise choisie
    total_forecast_currency = convert_to_currency(forecast.total_forecast_value, currency)
    total_realized_currency = convert_to_currency(forecast.total_realized_value, currency)
    
    return render_template('forecast_detail_ultra_modern.html',
                         forecast=forecast,
                         items=items_with_realizations,
                         currency=currency,
                         total_forecast_currency=total_forecast_currency,
                         total_realized_currency=total_realized_currency,
                         rate_usd=rate_usd,
                         rate_eur=rate_eur,
                         rate_xof=rate_xof)

@app.route('/forecast/<int:id>/enter-realizations', methods=['GET', 'POST'])
@login_required
def forecast_enter_realizations(id):
    """Saisie manuelle des réalisations pour une prévision"""
    from auth import is_admin_or_supervisor
    forecast = Forecast.query.get_or_404(id)
    
    # Vérifier que le commercial peut saisir les réalisations pour cette prévision
    if not is_admin_or_supervisor(current_user) and current_user.role and current_user.role.code == 'commercial':
        commercial_name = current_user.full_name or current_user.username
        if forecast.commercial_name != commercial_name and forecast.created_by_id != current_user.id:
            flash('Vous n\'avez pas accès à cette prévision', 'error')
            return redirect(url_for('forecast_list'))
    
    from models import ForecastItem
    from sqlalchemy import inspect, text
    
    if request.method == 'POST':
        try:
            # Récupérer les quantités réalisées depuis le formulaire
            item_ids = request.form.getlist('item_ids[]')
            realized_quantities = request.form.getlist('realized_quantities[]')
            
            # Récupérer la devise et les taux
            currency = forecast.currency if hasattr(forecast, 'currency') and forecast.currency else 'GNF'
            rate_usd = Decimal('8500')
            rate_eur = Decimal('9200')
            rate_xof = Decimal('0')
            
            try:
                inspector = inspect(db.engine)
                columns = [col['name'] for col in inspector.get_columns('forecasts')]
                if 'rate_usd' in columns and forecast.rate_usd:
                    rate_usd = Decimal(str(forecast.rate_usd))
                if 'rate_eur' in columns and forecast.rate_eur:
                    rate_eur = Decimal(str(forecast.rate_eur))
                if 'rate_xof' in columns and forecast.rate_xof:
                    rate_xof = Decimal(str(forecast.rate_xof))
            except:
                pass
            
            total_realized_value_gnf = Decimal('0')
            
            # Mettre à jour chaque item
            for i, item_id in enumerate(item_ids):
                if item_id and realized_quantities[i]:
                    item = ForecastItem.query.get(int(item_id))
                    if item:
                        realized_qty = Decimal(realized_quantities[i])
                        item.realized_quantity = realized_qty
                        # Calculer la valeur réalisée en GNF
                        item.realized_value_gnf = item.selling_price_gnf * realized_qty
                        total_realized_value_gnf += item.realized_value_gnf
            
            # Mettre à jour le total de la prévision
            forecast.total_realized_value = total_realized_value_gnf
            db.session.commit()
            
            flash('Réalisations enregistrées avec succès', 'success')
            return redirect(url_for('forecast_detail', id=forecast.id))
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Erreur lors de l'enregistrement des réalisations: {e}")
            import traceback
            traceback.print_exc()
            flash(f'Erreur lors de l\'enregistrement: {str(e)}', 'error')
    
    # Récupérer les items de la prévision
    items = forecast.items
    
    # Récupérer la devise
    currency = forecast.currency if hasattr(forecast, 'currency') and forecast.currency else 'GNF'
    rate_usd = Decimal('8500')
    rate_eur = Decimal('9200')
    rate_xof = Decimal('0')
    
    try:
        inspector = inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns('forecasts')]
        if 'rate_usd' in columns and forecast.rate_usd:
            rate_usd = Decimal(str(forecast.rate_usd))
        if 'rate_eur' in columns and forecast.rate_eur:
            rate_eur = Decimal(str(forecast.rate_eur))
        if 'rate_xof' in columns and forecast.rate_xof:
            rate_xof = Decimal(str(forecast.rate_xof))
    except:
        pass
    
    def convert_to_currency(value_gnf, curr):
        """Convertir une valeur GNF vers la devise choisie"""
        if curr == 'USD' and rate_usd > 0:
            return value_gnf / rate_usd
        elif curr == 'EUR' and rate_eur > 0:
            return value_gnf / rate_eur
        elif curr == 'XOF' and rate_xof > 0:
            return value_gnf / rate_xof
        else:
            return value_gnf
    
    return render_template('forecast_enter_realizations.html',
                         forecast=forecast,
                         items=items,
                         currency=currency,
                         convert_to_currency=convert_to_currency)

@app.route('/forecast/list')
@login_required
def forecast_list():
    """Liste des prévisions"""
    # #region agent log
    import json, time
    try:
        with open('/Users/dantawi/Documents/mini_flask_import_profitability/.cursor/debug.log', 'a') as f:
            f.write(json.dumps({"id":"log_entry","timestamp":int(time.time()*1000),"location":"app.py:3420","message":"forecast_list entry","data":{"user_id":current_user.id if current_user else None,"user_role":current_user.role.code if (current_user and current_user.role) else None},"sessionId":"debug-session","runId":"test-permissions","hypothesisId":"B"}) + "\n")
    except: pass
    # #endregion
    from models import Forecast
    from auth import is_admin_or_supervisor
    from sqlalchemy import or_
    
    # Filtres
    status = request.args.get('status')
    search = request.args.get('search', '')
    
    query = Forecast.query
    
    # Les commerciaux ne voient que leurs propres prévisions
    is_filtered = False
    if not is_admin_or_supervisor(current_user) and current_user.role and current_user.role.code == 'commercial':
        # Filtrer par nom du commercial ou par créateur
        commercial_name = current_user.full_name or current_user.username
        query = query.filter(
            or_(
                Forecast.commercial_name == commercial_name,
                Forecast.created_by_id == current_user.id
            )
        )
        is_filtered = True
        # #region agent log
        try:
            with open('/Users/dantawi/Documents/mini_flask_import_profitability/.cursor/debug.log', 'a') as f:
                f.write(json.dumps({"id":"log_entry","timestamp":int(time.time()*1000),"location":"app.py:3438","message":"forecast_list filtered for commercial","data":{"commercial_name":commercial_name,"user_id":current_user.id},"sessionId":"debug-session","runId":"test-permissions","hypothesisId":"B"}) + "\n")
        except: pass
        # #endregion
    
    if status:
        query = query.filter_by(status=status)
    
    if search:
        query = query.filter(
            or_(
                Forecast.name.like(f'%{search}%'),
                Forecast.description.like(f'%{search}%')
            )
        )
    
    forecasts = query.order_by(Forecast.created_at.desc()).all()
    # #region agent log
    try:
        with open('/Users/dantawi/Documents/mini_flask_import_profitability/.cursor/debug.log', 'a') as f:
            f.write(json.dumps({"id":"log_entry","timestamp":int(time.time()*1000),"location":"app.py:3445","message":"forecast_list result","data":{"forecasts_count":len(forecasts),"is_filtered":is_filtered,"user_role":current_user.role.code if (current_user and current_user.role) else None},"sessionId":"debug-session","runId":"test-permissions","hypothesisId":"B"}) + "\n")
    except: pass
    # #endregion
    
    return render_template('forecast_list_ultra_modern.html', forecasts=forecasts)

@app.route('/forecast/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def forecast_edit(id):
    """Modifier une prévision (admin et superviseur uniquement)"""
    from auth import is_admin_or_supervisor
    if not is_admin_or_supervisor(current_user):
        flash('Vous n\'avez pas la permission de modifier des prévisions. Seuls les administrateurs et superviseurs peuvent modifier des prévisions.', 'error')
        return redirect(url_for('forecast_detail', id=id))
    
    forecast = Forecast.query.get_or_404(id)
    from models import StockItem
    
    if request.method == 'POST':
        try:
            from models import ForecastItem
            from sqlalchemy import inspect, text
            
            forecast.name = request.form.get('name')
            forecast.description = request.form.get('description')
            forecast.start_date = datetime.strptime(request.form.get('start_date'), '%Y-%m-%d').date()
            forecast.end_date = datetime.strptime(request.form.get('end_date'), '%Y-%m-%d').date()
            forecast.status = request.form.get('status', 'draft')
            
            # Mettre à jour la devise si elle existe
            currency = request.form.get('currency', 'GNF')
            try:
                inspector = inspect(db.engine)
                columns = [col['name'] for col in inspector.get_columns('forecasts')]
                if 'currency' in columns:
                    forecast.currency = currency
            except:
                pass
            
            # Supprimer tous les articles existants
            ForecastItem.query.filter_by(forecast_id=forecast.id).delete()
            
            # Traiter les nouveaux articles
            article_ids = request.form.getlist('article_ids[]')
            quantities = request.form.getlist('quantities[]')
            prices = request.form.getlist('prices[]')
            
            total_forecast_value = Decimal('0')
            
            # Récupérer les taux de change
            rate_usd = Decimal('8500')
            rate_eur = Decimal('9200')
            rate_xof = Decimal('0')
            
            try:
                inspector = inspect(db.engine)
                columns = [col['name'] for col in inspector.get_columns('forecasts')]
                if 'rate_usd' in columns and forecast.rate_usd:
                    rate_usd = Decimal(str(forecast.rate_usd))
                if 'rate_eur' in columns and forecast.rate_eur:
                    rate_eur = Decimal(str(forecast.rate_eur))
                if 'rate_xof' in columns and forecast.rate_xof:
                    rate_xof = Decimal(str(forecast.rate_xof))
            except:
                pass
            
            for i, article_id in enumerate(article_ids):
                if article_id and quantities[i] and prices[i]:
                    # Le prix est dans la devise choisie, on le stocke en GNF pour la cohérence
                    price_in_currency = Decimal(prices[i])
                    
                    # Convertir en GNF selon la devise
                    if currency == 'USD':
                        price_gnf = price_in_currency * rate_usd
                    elif currency == 'EUR':
                        price_gnf = price_in_currency * rate_eur
                    elif currency == 'XOF':
                        price_gnf = price_in_currency * rate_xof if rate_xof > 0 else price_in_currency * Decimal('0.0667')
                    else:  # GNF
                        price_gnf = price_in_currency
                    
                    item = ForecastItem(
                        forecast_id=forecast.id,
                        stock_item_id=int(article_id),
                        forecast_quantity=Decimal(quantities[i]),
                        selling_price_gnf=price_gnf
                    )
                    db.session.add(item)
                    # Calculer la valeur dans la devise choisie
                    forecast_value_in_currency = price_in_currency * Decimal(quantities[i])
                    total_forecast_value += forecast_value_in_currency
            
            # Convertir la valeur totale en GNF pour le stockage
            total_forecast_value_gnf = total_forecast_value
            if currency == 'USD':
                total_forecast_value_gnf = total_forecast_value * rate_usd
            elif currency == 'EUR':
                total_forecast_value_gnf = total_forecast_value * rate_eur
            elif currency == 'XOF':
                total_forecast_value_gnf = total_forecast_value * rate_xof if rate_xof > 0 else total_forecast_value * Decimal('0.0667')
            
            # Mettre à jour la valeur totale
            forecast.total_forecast_value = total_forecast_value_gnf
            
            db.session.commit()
            flash('Prévision mise à jour avec succès', 'success')
            return redirect(url_for('forecast_detail', id=forecast.id))
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Erreur lors de la mise à jour de la prévision: {e}")
            import traceback
            traceback.print_exc()
            flash(f'Erreur lors de la mise à jour: {str(e)}', 'error')
    
    from models import User
    stock_items = StockItem.query.filter_by(is_active=True).order_by(StockItem.name).all()
    users = User.query.order_by(User.username).all()
    return render_template('forecast_edit_ultra_modern.html',
                         forecast=forecast,
                         stock_items=stock_items,
                         users=users)

@app.route('/forecast/<int:id>/delete', methods=['POST'])
@login_required
def forecast_delete(id):
    """Supprimer une prévision (admin et superviseur uniquement)"""
    from auth import is_admin_or_supervisor
    if not is_admin_or_supervisor(current_user):
        flash('Vous n\'avez pas la permission de supprimer des prévisions. Seuls les administrateurs et superviseurs peuvent supprimer des prévisions.', 'error')
        return redirect(url_for('forecast_detail', id=id))
    
    forecast = Forecast.query.get_or_404(id)
    
    try:
        db.session.delete(forecast)
        db.session.commit()
        flash('Prévision supprimée avec succès', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erreur lors de la suppression: {str(e)}', 'error')
    
    return redirect(url_for('forecast_list'))

@app.route('/forecast/performance')
@login_required
def forecast_performance():
    """Performance des prévisions avec données pour graphiques"""
    from models import Forecast
    from sqlalchemy import inspect, text
    from collections import defaultdict
    
    # Récupérer toutes les prévisions actives ou terminées
    try:
        forecasts = Forecast.query.filter(
            Forecast.status.in_(['active', 'completed'])
        ).order_by(Forecast.start_date.desc()).all()
    except:
        # Fallback SQL si colonnes manquantes
        try:
            inspector = inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('forecasts')]
            select_cols = ['id', 'name', 'start_date', 'end_date', 'status', 
                          'total_forecast_value', 'total_realized_value', 'created_at']
            if 'commercial_name' in columns:
                select_cols.append('commercial_name')
            if 'currency' in columns:
                select_cols.append('currency')
            
            cols_str = ', '.join(select_cols)
            result = db.session.execute(text(f"""
                SELECT {cols_str}
                FROM forecasts
                WHERE status IN ('active', 'completed')
                ORDER BY start_date DESC
            """))
            
            forecasts = []
            for row in result:
                f = Forecast()
                f.id = row[0]
                f.name = row[1]
                f.start_date = row[2]
                f.end_date = row[3]
                f.status = row[4]
                f.total_forecast_value = Decimal(str(row[5]))
                f.total_realized_value = Decimal(str(row[6]))
                f.created_at = row[7]
                if 'commercial_name' in columns and len(row) > 8:
                    f.commercial_name = row[8] if len(row) > 8 else None
                if 'currency' in columns and len(row) > 9:
                    f.currency = row[9] if len(row) > 9 else 'GNF'
                forecasts.append(f)
        except Exception as e:
            print(f"⚠️ Erreur lors de la récupération des prévisions: {e}")
            forecasts = []
    
    # Calculer les métriques globales
    total_forecast_value = sum(float(f.total_forecast_value) for f in forecasts)
    total_realized_value = sum(float(f.total_realized_value) for f in forecasts)
    overall_accuracy = (total_realized_value / total_forecast_value * 100) if total_forecast_value > 0 else 0
    
    # Préparer les données pour les graphiques
    # 1. Données temporelles (évolution dans le temps)
    timeline_data = []
    for f in sorted(forecasts, key=lambda x: x.start_date):
        accuracy = (float(f.total_realized_value) / float(f.total_forecast_value) * 100) if f.total_forecast_value > 0 else 0
        timeline_data.append({
            'date': f.start_date.strftime('%Y-%m-%d'),
            'name': f.name,
            'forecast': float(f.total_forecast_value),
            'realized': float(f.total_realized_value),
            'accuracy': round(accuracy, 1)
        })
    
    # 2. Données par commercial
    commercial_data = defaultdict(lambda: {'forecast': 0, 'realized': 0, 'count': 0})
    for f in forecasts:
        commercial = f.commercial_name if hasattr(f, 'commercial_name') and f.commercial_name else 'Non assigné'
        commercial_data[commercial]['forecast'] += float(f.total_forecast_value)
        commercial_data[commercial]['realized'] += float(f.total_realized_value)
        commercial_data[commercial]['count'] += 1
    
    commercial_chart_data = []
    for commercial, data in commercial_data.items():
        accuracy = (data['realized'] / data['forecast'] * 100) if data['forecast'] > 0 else 0
        commercial_chart_data.append({
            'name': commercial,
            'forecast': data['forecast'],
            'realized': data['realized'],
            'accuracy': round(accuracy, 1),
            'count': data['count']
        })
    
    # 3. Top 10 prévisions par valeur
    top_forecasts = sorted(forecasts, key=lambda x: float(x.total_forecast_value), reverse=True)[:10]
    
    # 4. Répartition par statut
    status_data = defaultdict(lambda: {'count': 0, 'value': 0})
    for f in forecasts:
        status_data[f.status]['count'] += 1
        status_data[f.status]['value'] += float(f.total_forecast_value)
    
    return render_template('forecast_performance_ultra_modern.html',
                         forecasts=forecasts,
                         total_forecast_value=total_forecast_value,
                         total_realized_value=total_realized_value,
                         overall_accuracy=round(overall_accuracy, 1),
                         timeline_data=timeline_data,
                         commercial_data=commercial_chart_data,
                         top_forecasts=top_forecasts,
                         status_data=dict(status_data))

@app.route('/forecast/quick-entry', methods=['GET', 'POST'])
@login_required
def forecast_quick_entry():
    """Saisie rapide avec tableau éditable (admin et superviseur uniquement)"""
    from auth import is_admin_or_supervisor
    if not is_admin_or_supervisor(current_user):
        flash('Vous n\'avez pas la permission d\'accéder à cette page. Seuls les administrateurs et superviseurs peuvent créer des prévisions.', 'error')
        return redirect(url_for('forecast_dashboard'))
    
    from models import StockItem, ForecastItem
    from sqlalchemy import inspect, text
    
    if request.method == 'POST':
        try:
            # Récupérer les données du formulaire
            name = request.form.get('name')
            commercial_name = request.form.get('commercial_name', '').strip()
            start_date = datetime.strptime(request.form.get('start_date'), '%Y-%m-%d').date()
            end_date = datetime.strptime(request.form.get('end_date'), '%Y-%m-%d').date()
            currency = request.form.get('currency', 'GNF')
            description = request.form.get('description', '')
            
            # Récupérer les taux de change
            rate_usd = Decimal('8500')
            rate_eur = Decimal('9200')
            rate_xof = Decimal('0')
            
            try:
                last_simulation = Simulation.query.order_by(Simulation.created_at.desc()).first()
                if last_simulation:
                    rate_usd = Decimal(str(last_simulation.rate_usd)) if last_simulation.rate_usd else Decimal('8500')
                    rate_eur = Decimal(str(last_simulation.rate_eur)) if last_simulation.rate_eur else Decimal('9200')
                    rate_xof = Decimal(str(last_simulation.rate_xof)) if last_simulation.rate_xof else Decimal('0')
            except:
                pass
            
            # Créer la prévision
            forecast = Forecast(
                name=name,
                description=description,
                start_date=start_date,
                end_date=end_date,
                status='draft',
                commercial_name=commercial_name if commercial_name else None,
                currency=currency,
                rate_usd=rate_usd,
                rate_eur=rate_eur,
                rate_xof=rate_xof,
                created_by_id=current_user.id
            )
            
            try:
                db.session.add(forecast)
                db.session.flush()
            except Exception as e:
                if 'commercial_name' in str(e):
                    # Utiliser SQL direct si la colonne n'existe pas
                    inspector = inspect(db.engine)
                    columns = [col['name'] for col in inspector.get_columns('forecasts')]
                    
                    insert_cols = ['name', 'description', 'start_date', 'end_date', 'status', 
                                 'total_forecast_value', 'total_realized_value', 'created_by_id', 'created_at']
                    params = {
                        'name': name,
                        'description': description,
                        'start_date': start_date,
                        'end_date': end_date,
                        'status': 'draft',
                        'total_forecast_value': 0,
                        'total_realized_value': 0,
                        'created_by_id': current_user.id,
                        'created_at': datetime.now(UTC)
                    }
                    
                    if 'currency' in columns:
                        insert_cols.append('currency')
                        params['currency'] = currency
                    if 'commercial_name' in columns:
                        insert_cols.append('commercial_name')
                        params['commercial_name'] = commercial_name if commercial_name else None
                    if 'rate_usd' in columns:
                        insert_cols.append('rate_usd')
                        params['rate_usd'] = float(rate_usd)
                    if 'rate_eur' in columns:
                        insert_cols.append('rate_eur')
                        params['rate_eur'] = float(rate_eur)
                    if 'rate_xof' in columns:
                        insert_cols.append('rate_xof')
                        params['rate_xof'] = float(rate_xof)
                    
                    cols_str = ', '.join(insert_cols)
                    placeholders = ', '.join([f':{col}' for col in insert_cols])
                    
                    # Utiliser RETURNING pour PostgreSQL, lastrowid pour MySQL
                    from config import SQLALCHEMY_DATABASE_URI
                    is_postgresql = SQLALCHEMY_DATABASE_URI.startswith('postgresql')
                    
                    if is_postgresql:
                        sql = f"""
                            INSERT INTO forecasts ({cols_str})
                            VALUES ({placeholders})
                            RETURNING id
                        """
                        result = db.session.execute(text(sql), params)
                        db.session.flush()
                        forecast_id = result.scalar()
                    else:
                        result = db.session.execute(text(f"""
                            INSERT INTO forecasts ({cols_str})
                            VALUES ({placeholders})
                        """), params)
                        db.session.flush()
                        forecast_id = result.lastrowid
                    forecast = Forecast()
                    forecast.id = forecast_id
                    forecast.name = name
                    forecast.description = description
                    forecast.start_date = start_date
                    forecast.end_date = end_date
                    forecast.status = 'draft'
                    forecast.total_forecast_value = Decimal('0')
                    forecast.total_realized_value = Decimal('0')
                else:
                    raise
            
            # Traiter les données du tableau
            article_ids = request.form.getlist('article_ids[]')
            forecast_quantities = request.form.getlist('forecast_quantities[]')
            realized_quantities = request.form.getlist('realized_quantities[]')
            prices = request.form.getlist('prices[]')
            
            total_forecast_value = Decimal('0')
            total_realized_value = Decimal('0')
            
            for i, article_id in enumerate(article_ids):
                if article_id and forecast_quantities[i]:
                    price_in_currency = Decimal(prices[i]) if prices[i] else Decimal('0')
                    forecast_qty = Decimal(forecast_quantities[i])
                    realized_qty = Decimal(realized_quantities[i]) if realized_quantities[i] else Decimal('0')
                    
                    # Convertir en GNF
                    if currency == 'USD':
                        price_gnf = price_in_currency * rate_usd
                    elif currency == 'EUR':
                        price_gnf = price_in_currency * rate_eur
                    elif currency == 'XOF':
                        price_gnf = price_in_currency * rate_xof if rate_xof > 0 else price_in_currency * Decimal('0.0667')
                    else:
                        price_gnf = price_in_currency
                    
                    item = ForecastItem(
                        forecast_id=forecast.id,
                        stock_item_id=int(article_id),
                        forecast_quantity=forecast_qty,
                        selling_price_gnf=price_gnf,
                        realized_quantity=realized_qty,
                        realized_value_gnf=price_gnf * realized_qty
                    )
                    db.session.add(item)
                    
                    total_forecast_value += price_in_currency * forecast_qty
                    total_realized_value += price_in_currency * realized_qty
            
            # Convertir les totaux en GNF
            if currency == 'USD':
                forecast.total_forecast_value = total_forecast_value * rate_usd
                forecast.total_realized_value = total_realized_value * rate_usd
            elif currency == 'EUR':
                forecast.total_forecast_value = total_forecast_value * rate_eur
                forecast.total_realized_value = total_realized_value * rate_eur
            elif currency == 'XOF':
                rate = rate_xof if rate_xof > 0 else Decimal('0.0667')
                forecast.total_forecast_value = total_forecast_value * rate
                forecast.total_realized_value = total_realized_value * rate
            else:
                forecast.total_forecast_value = total_forecast_value
                forecast.total_realized_value = total_realized_value
            
            db.session.commit()
            flash('Prévision créée avec succès', 'success')
            return redirect(url_for('forecast_detail', id=forecast.id))
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Erreur lors de la création: {e}")
            import traceback
            traceback.print_exc()
            flash(f'Erreur: {str(e)}', 'error')
    
    from models import User
    stock_items = StockItem.query.filter_by(is_active=True).order_by(StockItem.name).all()
    users = User.query.order_by(User.username).all()
    return render_template('forecast_quick_entry.html',
                         stock_items=stock_items,
                         users=users)

@app.route('/forecast/import', methods=['GET', 'POST'])
@login_required
def forecast_import():
    """Import de données pour prévisions depuis Excel/CSV (admin et superviseur uniquement)"""
    from auth import is_admin_or_supervisor
    if not is_admin_or_supervisor(current_user):
        flash('Vous n\'avez pas la permission d\'importer des prévisions. Seuls les administrateurs et superviseurs peuvent importer des prévisions.', 'error')
        return redirect(url_for('forecast_dashboard'))
    
    from models import StockItem, ForecastItem
    import pandas as pd
    import os
    from werkzeug.utils import secure_filename
    
    if request.method == 'POST':
        try:
            file = request.files.get('file')
            if not file or file.filename == '':
                flash('Veuillez sélectionner un fichier', 'error')
                return redirect(url_for('forecast_import'))
            
            # Sauvegarder le fichier temporairement
            upload_dir = os.path.join(app.instance_path, 'uploads')
            os.makedirs(upload_dir, exist_ok=True)
            filename = secure_filename(file.filename)
            filepath = os.path.join(upload_dir, filename)
            file.save(filepath)
            
            # Lire le fichier
            try:
                if filename.endswith('.csv'):
                    df = pd.read_csv(filepath, encoding='utf-8')
                elif filename.endswith(('.xlsx', '.xls')):
                    df = pd.read_excel(filepath)
                else:
                    flash('Format de fichier non supporté', 'error')
                    os.remove(filepath)
                    return redirect(url_for('forecast_import'))
            except Exception as e:
                flash(f'Erreur lors de la lecture du fichier: {str(e)}', 'error')
                os.remove(filepath)
                return redirect(url_for('forecast_import'))
            
            # Vérifier les colonnes requises
            required_cols = ['article', 'forecast_quantity', 'price']
            missing_cols = [col for col in required_cols if col not in df.columns]
            if missing_cols:
                flash(f'Colonnes manquantes: {", ".join(missing_cols)}', 'error')
                os.remove(filepath)
                return redirect(url_for('forecast_import'))
            
            # Récupérer les paramètres du formulaire
            name = request.form.get('name', f'Import {datetime.now().strftime("%Y-%m-%d")}')
            commercial_name = request.form.get('commercial_name', '').strip()
            start_date = datetime.strptime(request.form.get('start_date'), '%Y-%m-%d').date()
            end_date = datetime.strptime(request.form.get('end_date'), '%Y-%m-%d').date()
            currency = request.form.get('currency', 'GNF')
            
            # Récupérer les taux de change
            rate_usd = Decimal('8500')
            rate_eur = Decimal('9200')
            rate_xof = Decimal('0')
            
            try:
                last_simulation = Simulation.query.order_by(Simulation.created_at.desc()).first()
                if last_simulation:
                    rate_usd = Decimal(str(last_simulation.rate_usd)) if last_simulation.rate_usd else Decimal('8500')
                    rate_eur = Decimal(str(last_simulation.rate_eur)) if last_simulation.rate_eur else Decimal('9200')
                    rate_xof = Decimal(str(last_simulation.rate_xof)) if last_simulation.rate_xof else Decimal('0')
            except:
                pass
            
            # Créer la prévision
            forecast = Forecast(
                name=name,
                description=f'Import depuis {filename}',
                start_date=start_date,
                end_date=end_date,
                status='draft',
                commercial_name=commercial_name if commercial_name else None,
                currency=currency,
                rate_usd=rate_usd,
                rate_eur=rate_eur,
                rate_xof=rate_xof,
                created_by_id=current_user.id
            )
            
            try:
                db.session.add(forecast)
                db.session.flush()
            except Exception as e:
                if 'commercial_name' in str(e):
                    # Utiliser SQL direct
                    inspector = inspect(db.engine)
                    columns = [col['name'] for col in inspector.get_columns('forecasts')]
                    
                    insert_cols = ['name', 'description', 'start_date', 'end_date', 'status', 
                                 'total_forecast_value', 'total_realized_value', 'created_by_id', 'created_at']
                    params = {
                        'name': name,
                        'description': f'Import depuis {filename}',
                        'start_date': start_date,
                        'end_date': end_date,
                        'status': 'draft',
                        'total_forecast_value': 0,
                        'total_realized_value': 0,
                        'created_by_id': current_user.id,
                        'created_at': datetime.now(UTC)
                    }
                    
                    if 'currency' in columns:
                        insert_cols.append('currency')
                        params['currency'] = currency
                    if 'commercial_name' in columns:
                        insert_cols.append('commercial_name')
                        params['commercial_name'] = commercial_name if commercial_name else None
                    if 'rate_usd' in columns:
                        insert_cols.append('rate_usd')
                        params['rate_usd'] = float(rate_usd)
                    if 'rate_eur' in columns:
                        insert_cols.append('rate_eur')
                        params['rate_eur'] = float(rate_eur)
                    if 'rate_xof' in columns:
                        insert_cols.append('rate_xof')
                        params['rate_xof'] = float(rate_xof)
                    
                    cols_str = ', '.join(insert_cols)
                    placeholders = ', '.join([f':{col}' for col in insert_cols])
                    
                    # Utiliser RETURNING pour PostgreSQL, lastrowid pour MySQL
                    from config import SQLALCHEMY_DATABASE_URI
                    is_postgresql = SQLALCHEMY_DATABASE_URI.startswith('postgresql')
                    
                    if is_postgresql:
                        sql = f"""
                            INSERT INTO forecasts ({cols_str})
                            VALUES ({placeholders})
                            RETURNING id
                        """
                        result = db.session.execute(text(sql), params)
                        db.session.flush()
                        forecast_id = result.scalar()
                    else:
                        result = db.session.execute(text(f"""
                            INSERT INTO forecasts ({cols_str})
                            VALUES ({placeholders})
                        """), params)
                        db.session.flush()
                        forecast_id = result.lastrowid
                    forecast = Forecast()
                    forecast.id = forecast_id
                    forecast.name = name
                    forecast.description = f'Import depuis {filename}'
                    forecast.start_date = start_date
                    forecast.end_date = end_date
                    forecast.status = 'draft'
                    forecast.total_forecast_value = Decimal('0')
                    forecast.total_realized_value = Decimal('0')
                else:
                    raise
            
            # Traiter les lignes du fichier
            total_forecast_value = Decimal('0')
            total_realized_value = Decimal('0')
            imported_count = 0
            
            for _, row in df.iterrows():
                article_name = str(row['article']).strip()
                forecast_qty = Decimal(str(row['forecast_quantity']))
                price = Decimal(str(row['price']))
                realized_qty = Decimal(str(row.get('realized_quantity', 0)))
                
                # Trouver l'article par nom
                stock_item = StockItem.query.filter_by(name=article_name, is_active=True).first()
                if not stock_item:
                    continue  # Ignorer les articles non trouvés
                
                # Convertir le prix en GNF
                if currency == 'USD':
                    price_gnf = price * rate_usd
                elif currency == 'EUR':
                    price_gnf = price * rate_eur
                elif currency == 'XOF':
                    price_gnf = price * rate_xof if rate_xof > 0 else price * Decimal('0.0667')
                else:
                    price_gnf = price
                
                item = ForecastItem(
                    forecast_id=forecast.id,
                    stock_item_id=stock_item.id,
                    forecast_quantity=forecast_qty,
                    selling_price_gnf=price_gnf,
                    realized_quantity=realized_qty,
                    realized_value_gnf=price_gnf * realized_qty
                )
                db.session.add(item)
                
                total_forecast_value += price * forecast_qty
                total_realized_value += price * realized_qty
                imported_count += 1
            
            # Mettre à jour les totaux
            if currency == 'USD':
                forecast.total_forecast_value = total_forecast_value * rate_usd
                forecast.total_realized_value = total_realized_value * rate_usd
            elif currency == 'EUR':
                forecast.total_forecast_value = total_forecast_value * rate_eur
                forecast.total_realized_value = total_realized_value * rate_eur
            elif currency == 'XOF':
                rate = rate_xof if rate_xof > 0 else Decimal('0.0667')
                forecast.total_forecast_value = total_forecast_value * rate
                forecast.total_realized_value = total_realized_value * rate
            else:
                forecast.total_forecast_value = total_forecast_value
                forecast.total_realized_value = total_realized_value
            
            db.session.commit()
            os.remove(filepath)  # Supprimer le fichier temporaire
            
            flash(f'Import réussi: {imported_count} articles importés', 'success')
            return redirect(url_for('forecast_detail', id=forecast.id))
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Erreur lors de l'import: {e}")
            import traceback
            traceback.print_exc()
            flash(f'Erreur lors de l\'import: {str(e)}', 'error')
            if 'filepath' in locals():
                try:
                    os.remove(filepath)
                except:
                    pass
    
    from models import User
    users = User.query.order_by(User.username).all()
    return render_template('forecast_import_ultra_modern.html', users=users)

@app.route('/forecast/summary')
@login_required
def forecast_summary():
    """Vue récapitulative centralisée par commercial"""
    from sqlalchemy import func
    from sqlalchemy import inspect, text
    
    # Récupérer toutes les prévisions groupées par commercial
    try:
        forecasts = Forecast.query.order_by(Forecast.commercial_name, Forecast.start_date.desc()).all()
    except:
        # Si la colonne commercial_name n'existe pas, utiliser SQL direct
        try:
            inspector = inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('forecasts')]
            
            select_cols = ['id', 'name', 'start_date', 'end_date', 'status', 
                          'total_forecast_value', 'total_realized_value', 'created_at']
            if 'commercial_name' in columns:
                select_cols.append('commercial_name')
            if 'currency' in columns:
                select_cols.append('currency')
            
            cols_str = ', '.join(select_cols)
            result = db.session.execute(text(f"""
                SELECT {cols_str}
                FROM forecasts
                ORDER BY commercial_name, start_date DESC
            """))
            
            forecasts = []
            for row in result:
                f = Forecast()
                f.id = row[0]
                f.name = row[1]
                f.start_date = row[2]
                f.end_date = row[3]
                f.status = row[4]
                f.total_forecast_value = Decimal(str(row[5]))
                f.total_realized_value = Decimal(str(row[6]))
                f.created_at = row[7]
                if 'commercial_name' in columns and len(row) > 8:
                    f.commercial_name = row[8] if len(row) > 8 else None
                if 'currency' in columns and len(row) > 9:
                    f.currency = row[9] if len(row) > 9 else 'GNF'
                forecasts.append(f)
        except Exception as e:
            print(f"⚠️ Erreur lors de la récupération: {e}")
            forecasts = []
    
    # Grouper par commercial
    by_commercial = {}
    for forecast in forecasts:
        commercial = forecast.commercial_name if hasattr(forecast, 'commercial_name') and forecast.commercial_name else 'Sans commercial'
        if commercial not in by_commercial:
            by_commercial[commercial] = {
                'forecasts': [],
                'total_forecast': Decimal('0'),
                'total_realized': Decimal('0')
            }
        by_commercial[commercial]['forecasts'].append(forecast)
        by_commercial[commercial]['total_forecast'] += forecast.total_forecast_value
        by_commercial[commercial]['total_realized'] += forecast.total_realized_value
    
    return render_template('forecast_summary.html',
                         by_commercial=by_commercial)

@app.route('/api/test')
@login_required
def api_test():
    """Route de test"""
    return jsonify({"message": "API fonctionne", "status": "ok"})

# Gestion des erreurs
@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500

@app.errorhandler(400)
def bad_request(error):
    """Gestionnaire d'erreur 400 - retourne JSON pour les routes API"""
    # #region agent log
    try:
        import json, time
        with open('/Users/dantawi/Documents/mini_flask_import_profitability/.cursor/debug.log', 'a') as f:
            f.write(json.dumps({"id":"log_entry","timestamp":int(time.time()*1000),"location":"app.py:4282","message":"bad_request error handler","data":{"path":request.path,"method":request.method,"is_json":request.is_json,"content_type":request.content_type,"error":str(error),"error_description":error.description if hasattr(error, 'description') else None},"sessionId":"debug-session","runId":"run1","hypothesisId":"C"}) + "\n")
    except: pass
    # #endregion
    if request.path.startswith('/api/') or '/api/' in request.path:
        error_msg = str(error)
        if hasattr(error, 'description'):
            error_msg = error.description
        return jsonify({'error': 'Requête invalide', 'message': error_msg, 'path': request.path}), 400
    # Pour les autres routes, utiliser le comportement par défaut
    return error

@app.errorhandler(429)
def too_many_requests(error):
    """Gestionnaire d'erreur 429 - retourne JSON pour les routes API"""
    if request.path.startswith('/api/') or '/api/' in request.path:
        return jsonify({'error': 'Trop de requêtes', 'message': 'Veuillez réessayer dans quelques instants'}), 429
    # Pour les autres routes, utiliser le comportement par défaut
    return error

@app.route('/uploads/<path:filename>')
@login_required
def uploaded_file(filename):
    """Route pour servir les fichiers uploadés"""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/init', methods=['GET'])
def init_database():
    """Initialise la base de données avec les tables et l'utilisateur admin (pour Render)"""
    from models import User, Role
    from werkzeug.security import generate_password_hash
    
    try:
        # Créer toutes les tables
        db.create_all()
        
        # Créer le rôle admin
        admin_role = Role.query.filter_by(code='admin').first()
        if not admin_role:
            admin_role = Role(
                name='Administrateur',
                code='admin',
                permissions={"all": ["*"]},
                description='Accès complet à toutes les fonctionnalités'
            )
            db.session.add(admin_role)
            db.session.commit()
        
        # Créer l'utilisateur admin
        admin_user = User.query.filter_by(username='admin').first()
        if not admin_user:
            admin_user = User(
                username='admin',
                email='admin@importprofit.pro',
                password_hash=generate_password_hash('admin123'),
                full_name='Administrateur',
                role_id=admin_role.id,
                is_active=True
            )
            db.session.add(admin_user)
            db.session.commit()
            return """
            <h1>✅ Base de données initialisée!</h1>
            <p><strong>Identifiants de connexion:</strong></p>
            <ul>
                <li>Username: <code>admin</code></li>
                <li>Password: <code>admin123</code></li>
            </ul>
            <p>⚠️ <strong>IMPORTANT:</strong> Changez le mot de passe après la première connexion!</p>
            <p><a href="/auth/login">Se connecter</a></p>
            """
        else:
            return """
            <h1>ℹ️ Base de données déjà initialisée</h1>
            <p>L'utilisateur admin existe déjà.</p>
            <p><a href="/auth/login">Se connecter</a></p>
            """
    except Exception as e:
        return f"<h1>❌ Erreur lors de l'initialisation</h1><p>{str(e)}</p>", 500

if __name__ == '__main__':
    print("🚀 IMPORT PROFIT PRO - VERSION NETTOYÉE ET MODERNE")
    print("=" * 60)
    print("✅ Projet nettoyé et optimisé")
    print("✅ Base de données connectée")
    print("✅ Interface ultra-moderne")
    print("✅ API REST intégrée")
    print("=" * 60)
    print("🌐 Serveur démarré sur http://localhost:5002")
    print("📱 Testez toutes les fonctionnalités !")
    print("🎯 Application complète et moderne")
    print("=" * 60)
    
    app.run(host='0.0.0.0', port=5002, debug=True, load_dotenv=False)
