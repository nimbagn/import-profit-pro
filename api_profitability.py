# api_profitability.py
# API pour les calculs de rentabilité des simulations

from flask import Blueprint, request, jsonify
from decimal import Decimal
import json

# Création du blueprint
profitability_api = Blueprint('profitability_api', __name__)

@profitability_api.route('/api/profitability/calculate', methods=['POST'])
def calculate_profitability():
    """API pour calculer la rentabilité d'une simulation"""
    try:
        data = request.get_json()
        
        # Simulation de calcul de rentabilité
        result = {
            'success': True,
            'data': {
                'totals': {
                    'total_weight_kg': 450.0,
                    'total_value_gnf': 5200000.0,
                    'total_fixed_costs': 5000000.0,
                    'total_variable_costs': 200000.0,
                    'total_costs': 5200000.0,
                    'total_revenue': 6500000.0,
                    'total_margin': 1300000.0,
                    'margin_pct': 20.0
                },
                'truck': {
                    'utilization_pct': 85.0,
                    'overflow': False
                },
                'costs_breakdown': {
                    'customs_gnf': 2000000.0,
                    'handling_gnf': 500000.0,
                    'others_gnf': 300000.0,
                    'transport_fixed_gnf': 1000000.0,
                    'transport_variable_gnf': 1200000.0
                },
                'averages': {
                    'avg_cost_per_kg': 11555.56,
                    'avg_logistics_per_kg': 13333.33
                },
                'items': []
            }
        }
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

@profitability_api.route('/api/profitability/sensitivity', methods=['POST'])
def calculate_sensitivity():
    """API pour l'analyse de sensibilité"""
    try:
        data = request.get_json()
        
        result = {
            'success': True,
            'data': {
                'base_margin': 20.0,
                'sensitivity': {
                    'rate_usd': {
                        'impact': 2.5,
                        'new_rate': 8700.0,
                        'new_margin': 22.5
                    },
                    'customs': {
                        'impact': 1.8,
                        'new_rate': 5500000.0,
                        'new_margin': 18.2
                    }
                }
            }
        }
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

@profitability_api.route('/api/profitability/optimize', methods=['POST'])
def optimize_prices():
    """API pour l'optimisation des prix"""
    try:
        data = request.get_json()
        
        result = {
            'success': True,
            'data': {
                'original_margin': 15.0,
                'optimized_margin': 22.0,
                'improvement': 7.0,
                'optimized_prices': [165000.0, 850000.0, 28000.0],
                'recommendations': [
                    {
                        'article_id': 1,
                        'original_price': 150000.0,
                        'recommended_price': 165000.0,
                        'price_change': 15000.0,
                        'price_change_pct': 10.0
                    }
                ]
            }
        }
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400
