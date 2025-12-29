#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de nettoyage des templates HTML
Supprime tous les templates en doublons ou inutiles
"""

import os
import shutil

def cleanup_templates():
    """Nettoyer les templates inutiles"""
    print("🧹 Nettoyage des templates HTML...")
    
    # Templates utilisés dans l'application
    used_templates = {
        'index_unified_final.html',
        'simulations_ultra_modern_v3.html', 
        'simulation_new_ultra.html',
        'articles_unified.html',
        'article_new_unified.html',
        '404.html',
        '500.html',
        'base_modern_complete.html'  # Template de base
    }
    
    templates_dir = 'templates'
    if not os.path.exists(templates_dir):
        print("❌ Dossier templates introuvable")
        return
    
    # Lister tous les fichiers HTML
    all_templates = [f for f in os.listdir(templates_dir) if f.endswith('.html')]
    print(f"📊 Total des templates: {len(all_templates)}")
    
    # Identifier les templates à supprimer
    templates_to_remove = []
    for template in all_templates:
        if template not in used_templates:
            templates_to_remove.append(template)
    
    print(f"🗑️ Templates à supprimer: {len(templates_to_remove)}")
    
    # Supprimer les templates inutiles
    removed_count = 0
    for template in templates_to_remove:
        try:
            template_path = os.path.join(templates_dir, template)
            os.remove(template_path)
            print(f"✅ Supprimé: {template}")
            removed_count += 1
        except Exception as e:
            print(f"❌ Erreur lors de la suppression de {template}: {e}")
    
    print(f"✅ {removed_count} templates supprimés")
    
    # Vérifier le résultat
    remaining_templates = [f for f in os.listdir(templates_dir) if f.endswith('.html')]
    print(f"📁 Templates restants: {len(remaining_templates)}")
    
    print("🎯 Templates conservés:")
    for template in remaining_templates:
        print(f"  - {template}")

def create_minimal_templates():
    """Créer des templates minimaux si nécessaire"""
    print("🔧 Vérification des templates essentiels...")
    
    templates_dir = 'templates'
    essential_templates = {
        'base_modern_complete.html': '''{% extends "base.html" %}
{% block content %}
<div class="container">
    <h1>Template de base moderne</h1>
    <p>Template de base pour l'application Import Profit Pro</p>
</div>
{% endblock %}''',
        
        '404.html': '''<!DOCTYPE html>
<html>
<head>
    <title>404 - Page non trouvée</title>
</head>
<body>
    <h1>404 - Page non trouvée</h1>
    <p>La page que vous recherchez n'existe pas.</p>
</body>
</html>''',
        
        '500.html': '''<!DOCTYPE html>
<html>
<head>
    <title>500 - Erreur serveur</title>
</head>
<body>
    <h1>500 - Erreur serveur</h1>
    <p>Une erreur interne s'est produite.</p>
</body>
</html>'''
    }
    
    for template_name, content in essential_templates.items():
        template_path = os.path.join(templates_dir, template_name)
        if not os.path.exists(template_path):
            with open(template_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ Créé: {template_name}")

def main():
    """Fonction principale"""
    print("🚀 NETTOYAGE DES TEMPLATES HTML")
    print("=" * 50)
    
    # Nettoyer les templates
    cleanup_templates()
    
    # Créer les templates essentiels
    create_minimal_templates()
    
    print("=" * 50)
    print("✅ NETTOYAGE TERMINÉ")
    print("📁 Templates optimisés et nettoyés")
    print("🎯 Projet plus léger et performant")
    print("=" * 50)

if __name__ == "__main__":
    main()
