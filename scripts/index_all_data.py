#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script d'indexation initiale pour le moteur de recherche
Indexe toutes les données existantes dans la base de données
"""

import sys
import os

# Ajouter le répertoire parent au path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask
from models import db
from search import (
    index_article, index_simulation, index_forecast,
    index_stock_item, index_stock_movement, index_vehicle, index_chat_message
)
from models import (
    Article, Simulation, Forecast, StockItem, StockMovement,
    Vehicle, ChatMessage
)

def create_app():
    """Créer l'application Flask"""
    app = Flask(__name__)
    
    # Configuration de la base de données
    try:
        import pymysql
        from config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD_RAW
        
        db_uri = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD_RAW}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"
        app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        mysql_available = True
    except Exception as e:
        db_path = os.path.join(os.path.dirname(__file__), '..', 'instance', 'app.db')
        app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        mysql_available = False
    
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
        'connect_args': {'charset': 'utf8mb4'} if mysql_available else {}
    }
    
    db.init_app(app)
    return app

def index_all_data():
    """Indexer toutes les données"""
    app = create_app()
    
    with app.app_context():
        try:
            print("🔄 Début de l'indexation...")
            print("=" * 60)
            
            # Indexer les articles
            print("\n📦 Indexation des articles...")
            articles = Article.query.all()
            count_articles = 0
            for article in articles:
                try:
                    index_article(article)
                    count_articles += 1
                except Exception as e:
                    print(f"  ⚠️  Erreur pour l'article {article.id}: {e}")
            db.session.commit()
            print(f"  ✅ {count_articles} article(s) indexé(s)")
            
            # Indexer les simulations
            print("\n🧮 Indexation des simulations...")
            simulations = Simulation.query.all()
            count_simulations = 0
            for simulation in simulations:
                try:
                    index_simulation(simulation)
                    count_simulations += 1
                except Exception as e:
                    print(f"  ⚠️  Erreur pour la simulation {simulation.id}: {e}")
            db.session.commit()
            print(f"  ✅ {count_simulations} simulation(s) indexée(s)")
            
            # Indexer les prévisions
            print("\n📊 Indexation des prévisions...")
            forecasts = Forecast.query.all()
            count_forecasts = 0
            for forecast in forecasts:
                try:
                    index_forecast(forecast)
                    count_forecasts += 1
                except Exception as e:
                    print(f"  ⚠️  Erreur pour la prévision {forecast.id}: {e}")
            db.session.commit()
            print(f"  ✅ {count_forecasts} prévision(s) indexée(s)")
            
            # Indexer les articles de stock
            print("\n📦 Indexation des articles de stock...")
            stock_items = StockItem.query.all()
            count_stock_items = 0
            for item in stock_items:
                try:
                    index_stock_item(item)
                    count_stock_items += 1
                except Exception as e:
                    print(f"  ⚠️  Erreur pour l'article de stock {item.id}: {e}")
            db.session.commit()
            print(f"  ✅ {count_stock_items} article(s) de stock indexé(s)")
            
            # Indexer les mouvements de stock
            print("\n🔄 Indexation des mouvements de stock...")
            movements = StockMovement.query.all()
            count_movements = 0
            for movement in movements:
                try:
                    index_stock_movement(movement)
                    count_movements += 1
                except Exception as e:
                    print(f"  ⚠️  Erreur pour le mouvement {movement.id}: {e}")
            db.session.commit()
            print(f"  ✅ {count_movements} mouvement(s) indexé(s)")
            
            # Indexer les véhicules
            print("\n🚗 Indexation des véhicules...")
            vehicles = Vehicle.query.all()
            count_vehicles = 0
            for vehicle in vehicles:
                try:
                    index_vehicle(vehicle)
                    count_vehicles += 1
                except Exception as e:
                    print(f"  ⚠️  Erreur pour le véhicule {vehicle.id}: {e}")
            db.session.commit()
            print(f"  ✅ {count_vehicles} véhicule(s) indexé(s)")
            
            # Indexer les messages de chat
            print("\n💬 Indexation des messages de chat...")
            messages = ChatMessage.query.all()
            count_messages = 0
            for message in messages:
                try:
                    index_chat_message(message)
                    count_messages += 1
                except Exception as e:
                    print(f"  ⚠️  Erreur pour le message {message.id}: {e}")
            db.session.commit()
            print(f"  ✅ {count_messages} message(s) indexé(s)")
            
            print("\n" + "=" * 60)
            print("✅ INDEXATION TERMINÉE AVEC SUCCÈS")
            print("=" * 60)
            print(f"\n📊 Récapitulatif:")
            print(f"   • Articles: {count_articles}")
            print(f"   • Simulations: {count_simulations}")
            print(f"   • Prévisions: {count_forecasts}")
            print(f"   • Articles de stock: {count_stock_items}")
            print(f"   • Mouvements: {count_movements}")
            print(f"   • Véhicules: {count_vehicles}")
            print(f"   • Messages: {count_messages}")
            print(f"\n   Total: {count_articles + count_simulations + count_forecasts + count_stock_items + count_movements + count_vehicles + count_messages} entités indexées")
            
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ ERREUR LORS DE L'INDEXATION: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    return True

if __name__ == '__main__':
    success = index_all_data()
    sys.exit(0 if success else 1)

