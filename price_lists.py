#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module Fiches de Prix - Import Profit Pro
Gestion des fiches de prix avec périodes, prix grossiste/détaillant et gratuités
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from datetime import datetime, date
from decimal import Decimal
from models import db, PriceList, PriceListItem, Article, Category
from auth import has_permission

# Créer le blueprint
price_lists_bp = Blueprint('price_lists', __name__, url_prefix='/price-lists')

# =========================================================
# ROUTES - LISTES
# =========================================================

@price_lists_bp.route('/')
@login_required
def lists():
    """Liste des fiches de prix"""
    if not has_permission(current_user, 'price_lists.view'):
        flash('Vous n\'avez pas la permission d\'accéder aux fiches de prix', 'error')
        return redirect(url_for('index'))
    
    # Récupérer toutes les fiches de prix
    price_lists = PriceList.query.order_by(PriceList.start_date.desc(), PriceList.created_at.desc()).all()
    
    return render_template('price_lists/lists.html', price_lists=price_lists)

@price_lists_bp.route('/<int:price_list_id>')
@login_required
def detail(price_list_id):
    """Détail d'une fiche de prix"""
    if not has_permission(current_user, 'price_lists.view'):
        flash('Vous n\'avez pas la permission d\'accéder aux fiches de prix', 'error')
        return redirect(url_for('price_lists.lists'))
    
    price_list = PriceList.query.get_or_404(price_list_id)
    
    # Charger les items avec les articles, groupés par catégorie
    items = PriceListItem.query.filter_by(price_list_id=price_list_id)\
        .join(Article).outerjoin(Category).order_by(Category.name, Article.name).all()
    
    # Grouper les items par catégorie
    items_by_category = {}
    for item in items:
        category_name = item.article.category.name if item.article.category else 'Sans catégorie'
        if category_name not in items_by_category:
            items_by_category[category_name] = []
        items_by_category[category_name].append(item)
    
    # Récupérer toutes les catégories pour les filtres
    categories = Category.query.order_by(Category.name).all()
    
    return render_template('price_lists/detail.html', 
                         price_list=price_list, 
                         items=items,
                         items_by_category=items_by_category,
                         categories=categories)

# =========================================================
# ROUTES - CRÉATION / ÉDITION
# =========================================================

@price_lists_bp.route('/new', methods=['GET', 'POST'])
@login_required
def new():
    """Créer une nouvelle fiche de prix"""
    if not has_permission(current_user, 'price_lists.create'):
        flash('Vous n\'avez pas la permission de créer une fiche de prix', 'error')
        return redirect(url_for('price_lists.lists'))
    
    if request.method == 'POST':
        try:
            name = request.form.get('name', '').strip()
            description = request.form.get('description', '').strip()
            start_date_str = request.form.get('start_date', '')
            end_date_str = request.form.get('end_date', '') or None
            
            if not name:
                flash('Le nom est obligatoire', 'error')
                return render_template('price_lists/form.html')
            
            if not start_date_str:
                flash('La date de début est obligatoire', 'error')
                return render_template('price_lists/form.html')
            
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = None
            if end_date_str:
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
                if end_date < start_date:
                    flash('La date de fin doit être postérieure à la date de début', 'error')
                    return render_template('price_lists/form.html')
            
            price_list = PriceList(
                name=name,
                description=description if description else None,
                start_date=start_date,
                end_date=end_date,
                is_active=True,
                created_by_id=current_user.id if current_user.is_authenticated else None
            )
            db.session.add(price_list)
            db.session.flush()  # Pour obtenir l'ID
            
            # Traiter les articles
            article_ids = request.form.getlist('article_ids[]')
            wholesale_prices = request.form.getlist('wholesale_prices[]')
            retail_prices = request.form.getlist('retail_prices[]')
            freebies_list = request.form.getlist('freebies[]')
            notes_list = request.form.getlist('notes[]')
            
            for i, article_id in enumerate(article_ids):
                if not article_id:
                    continue
                
                try:
                    article_id = int(article_id)
                    wholesale_price = Decimal(wholesale_prices[i]) if wholesale_prices[i] else None
                    retail_price = Decimal(retail_prices[i]) if retail_prices[i] else None
                    freebies = freebies_list[i].strip() if i < len(freebies_list) and freebies_list[i] else None
                    notes = notes_list[i].strip() if i < len(notes_list) and notes_list[i] else None
                    
                    # Ne créer l'item que si au moins un prix est renseigné
                    if wholesale_price or retail_price:
                        item = PriceListItem(
                            price_list_id=price_list.id,
                            article_id=article_id,
                            wholesale_price=wholesale_price,
                            retail_price=retail_price,
                            freebies=freebies,
                            notes=notes
                        )
                        db.session.add(item)
                except (ValueError, IndexError):
                    continue
            
            db.session.commit()
            flash(f'Fiche de prix "{name}" créée avec succès', 'success')
            return redirect(url_for('price_lists.detail', price_list_id=price_list.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur lors de la création de la fiche de prix: {str(e)}', 'error')
            return render_template('price_lists/form.html')
    
    # GET - Afficher le formulaire
    articles = Article.query.filter_by(is_active=True).outerjoin(Category).order_by(Category.name, Article.name).all()
    
    # Grouper les articles par catégorie
    articles_by_category = {}
    for article in articles:
        category_name = article.category.name if article.category else 'Sans catégorie'
        if category_name not in articles_by_category:
            articles_by_category[category_name] = []
        articles_by_category[category_name].append(article)
    
    return render_template('price_lists/form.html', 
                         price_list=None, 
                         articles=articles,
                         articles_by_category=articles_by_category)

@price_lists_bp.route('/<int:price_list_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(price_list_id):
    """Éditer une fiche de prix"""
    if not has_permission(current_user, 'price_lists.edit'):
        flash('Vous n\'avez pas la permission de modifier une fiche de prix', 'error')
        return redirect(url_for('price_lists.lists'))
    
    price_list = PriceList.query.get_or_404(price_list_id)
    
    if request.method == 'POST':
        try:
            name = request.form.get('name', '').strip()
            description = request.form.get('description', '').strip()
            start_date_str = request.form.get('start_date', '')
            end_date_str = request.form.get('end_date', '') or None
            is_active = request.form.get('is_active') == 'on'
            
            if not name:
                flash('Le nom est obligatoire', 'error')
                return render_template('price_lists/form.html', price_list=price_list)
            
            if not start_date_str:
                flash('La date de début est obligatoire', 'error')
                return render_template('price_lists/form.html', price_list=price_list)
            
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = None
            if end_date_str:
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
                if end_date < start_date:
                    flash('La date de fin doit être postérieure à la date de début', 'error')
                    return render_template('price_lists/form.html', price_list=price_list)
            
            price_list.name = name
            price_list.description = description if description else None
            price_list.start_date = start_date
            price_list.end_date = end_date
            price_list.is_active = is_active
            
            # Supprimer les anciens items
            PriceListItem.query.filter_by(price_list_id=price_list.id).delete()
            
            # Traiter les nouveaux articles
            article_ids = request.form.getlist('article_ids[]')
            wholesale_prices = request.form.getlist('wholesale_prices[]')
            retail_prices = request.form.getlist('retail_prices[]')
            freebies_list = request.form.getlist('freebies[]')
            notes_list = request.form.getlist('notes[]')
            
            for i, article_id in enumerate(article_ids):
                if not article_id:
                    continue
                
                try:
                    article_id = int(article_id)
                    wholesale_price = Decimal(wholesale_prices[i]) if wholesale_prices[i] else None
                    retail_price = Decimal(retail_prices[i]) if retail_prices[i] else None
                    freebies = freebies_list[i].strip() if i < len(freebies_list) and freebies_list[i] else None
                    notes = notes_list[i].strip() if i < len(notes_list) and notes_list[i] else None
                    
                    # Ne créer l'item que si au moins un prix est renseigné
                    if wholesale_price or retail_price:
                        item = PriceListItem(
                            price_list_id=price_list.id,
                            article_id=article_id,
                            wholesale_price=wholesale_price,
                            retail_price=retail_price,
                            freebies=freebies,
                            notes=notes
                        )
                        db.session.add(item)
                except (ValueError, IndexError):
                    continue
            
            db.session.commit()
            flash(f'Fiche de prix "{name}" modifiée avec succès', 'success')
            return redirect(url_for('price_lists.detail', price_list_id=price_list.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur lors de la modification de la fiche de prix: {str(e)}', 'error')
            return render_template('price_lists/form.html', price_list=price_list)
    
    # GET - Afficher le formulaire
    articles = Article.query.filter_by(is_active=True).outerjoin(Category).order_by(Category.name, Article.name).all()
    
    # Grouper les articles par catégorie
    articles_by_category = {}
    for article in articles:
        category_name = article.category.name if article.category else 'Sans catégorie'
        if category_name not in articles_by_category:
            articles_by_category[category_name] = []
        articles_by_category[category_name].append(article)
    
    existing_items = {item.article_id: item for item in price_list.items}
    return render_template('price_lists/form.html', 
                         price_list=price_list, 
                         articles=articles,
                         articles_by_category=articles_by_category,
                         existing_items=existing_items)

@price_lists_bp.route('/<int:price_list_id>/delete', methods=['POST'])
@login_required
def delete(price_list_id):
    """Supprimer une fiche de prix"""
    if not has_permission(current_user, 'price_lists.delete'):
        flash('Vous n\'avez pas la permission de supprimer une fiche de prix', 'error')
        return redirect(url_for('price_lists.lists'))
    
    price_list = PriceList.query.get_or_404(price_list_id)
    
    try:
        name = price_list.name
        db.session.delete(price_list)
        db.session.commit()
        flash(f'Fiche de prix "{name}" supprimée avec succès', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erreur lors de la suppression: {str(e)}', 'error')
    
    return redirect(url_for('price_lists.lists'))

