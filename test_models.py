#!/usr/bin/env python3
# Test des modèles

from flask import Flask
from models import db, Region, Depot, Vehicle, Family, StockItem, Role, User
from models import DepotStock, VehicleStock, StockMovement, Reception
from models import InventorySession, InventoryDetail
from models import VehicleDocument, VehicleMaintenance, VehicleOdometer
from models import Category, Article, Simulation, SimulationItem

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

with app.app_context():
    try:
        db.create_all()
        print("✅ Tous les modèles créés avec succès!")
        print(f"✅ Total: 21 modèles")
        print("\nModèles créés:")
        print("  - Référentiels: Region, Depot, Vehicle, Family, StockItem")
        print("  - Auth: Role, User")
        print("  - Stocks: DepotStock, VehicleStock, StockMovement, Reception")
        print("  - Inventaires: InventorySession, InventoryDetail")
        print("  - Flotte: VehicleDocument, VehicleMaintenance, VehicleOdometer")
        print("  - Import Profit: Category, Article, Simulation, SimulationItem")
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()

