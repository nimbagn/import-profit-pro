#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de vérification complète du projet
- Vérifie toutes les routes Flask
- Vérifie la compatibilité PostgreSQL
- Vérifie l'état Git
"""

import os
import sys
import re
import subprocess
from pathlib import Path

# Ajouter le répertoire parent au path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Couleurs pour la sortie
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*80}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*80}{Colors.RESET}\n")

def print_success(text):
    print(f"{Colors.GREEN}✅ {text}{Colors.RESET}")

def print_error(text):
    print(f"{Colors.RED}❌ {text}{Colors.RESET}")

def print_warning(text):
    print(f"{Colors.YELLOW}⚠️  {text}{Colors.RESET}")

def print_info(text):
    print(f"{Colors.BLUE}ℹ️  {text}{Colors.RESET}")

# =========================================================
# 1. VÉRIFICATION DES ROUTES FLASK
# =========================================================

def find_all_routes():
    """Trouve toutes les routes Flask dans le projet"""
    routes = []
    python_files = [
        'app.py',
        'orders.py',
        'stocks.py',
        'auth.py',
        'rh.py',
        'promotion.py',
        'referentiels.py',
        'flotte.py',
        'price_lists.py',
        'inventaires.py',
        'analytics.py',
        'search.py',
        'themes.py',
        'chat/routes.py',
        'chat/api.py',
        'chat/sse.py',
    ]
    
    for file_path in python_files:
        full_path = Path(__file__).parent.parent / file_path
        if not full_path.exists():
            continue
        
        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.split('\n')
            
            for i, line in enumerate(lines, 1):
                # Chercher @app.route ou @*_bp.route
                match = re.search(r'@(?:app|[\w_]+_bp)\.route\([\'"]([^\'"]+)[\'"]', line)
                if match:
                    route_path = match.group(1)
                    # Chercher la fonction suivante
                    func_name = None
                    for j in range(i, min(i+5, len(lines))):
                        func_match = re.search(r'def\s+(\w+)', lines[j])
                        if func_match:
                            func_name = func_match.group(1)
                            break
                    
                    routes.append({
                        'file': file_path.name,
                        'route': route_path,
                        'function': func_name or 'unknown',
                        'line': i
                    })
    
    return routes

# =========================================================
# 2. VÉRIFICATION COMPATIBILITÉ POSTGRESQL
# =========================================================

def check_postgresql_compatibility():
    """Vérifie la compatibilité PostgreSQL"""
    issues = []
    python_files = [
        'app.py',
        'orders.py',
        'stocks.py',
        'auth.py',
        'rh.py',
        'promotion.py',
        'referentiels.py',
        'flotte.py',
        'price_lists.py',
        'inventaires.py',
        'analytics.py',
    ]
    
    mysql_patterns = [
        (r'DATABASE\(\)', 'DATABASE() - Utiliser db_adapter.check_column_exists()'),
        (r'INFORMATION_SCHEMA\.COLUMNS.*DATABASE\(\)', 'INFORMATION_SCHEMA avec DATABASE() - Utiliser db_adapter'),
        (r'LAST_INSERT_ID\(\)', 'LAST_INSERT_ID() - Utiliser RETURNING id pour PostgreSQL'),
        (r'IFNULL\(', 'IFNULL() - Utiliser COALESCE() pour PostgreSQL'),
        (r'DATE_FORMAT\(', 'DATE_FORMAT() - Utiliser TO_CHAR() pour PostgreSQL'),
    ]
    
    for file_path in python_files:
        full_path = Path(__file__).parent.parent / file_path
        if not full_path.exists():
            continue
        
        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.split('\n')
            
            for i, line in enumerate(lines, 1):
                for pattern, description in mysql_patterns:
                    if re.search(pattern, line, re.IGNORECASE):
                        # Vérifier si c'est dans un commentaire ou une docstring
                        if not (line.strip().startswith('#') or '"""' in line or "'''" in line):
                            # Vérifier si db_adapter est utilisé
                            if 'db_adapter' not in content and 'db_utils' not in content:
                                issues.append({
                                    'file': file_path.name,
                                    'line': i,
                                    'issue': description,
                                    'code': line.strip()[:80]
                                })
    
    return issues

# =========================================================
# 3. VÉRIFICATION ÉTAT GIT
# =========================================================

def check_git_status():
    """Vérifie l'état Git"""
    try:
        repo_path = Path(__file__).parent.parent
        os.chdir(repo_path)
        
        # Vérifier si c'est un dépôt Git
        result = subprocess.run(['git', 'status', '--porcelain'], 
                              capture_output=True, text=True, timeout=10)
        
        if result.returncode != 0:
            return {'error': 'Not a git repository or git error'}
        
        # Analyser les fichiers modifiés/non trackés
        lines = result.stdout.strip().split('\n') if result.stdout.strip() else []
        modified = []
        untracked = []
        
        for line in lines:
            if line.startswith('??'):
                untracked.append(line[3:])
            elif line.startswith(' M') or line.startswith('M '):
                modified.append(line[3:])
            elif line.startswith('A '):
                modified.append(f"NEW: {line[3:]}")
        
        return {
            'modified': modified,
            'untracked': untracked,
            'total': len(modified) + len(untracked)
        }
    except subprocess.TimeoutExpired:
        return {'error': 'Git command timeout'}
    except Exception as e:
        return {'error': str(e)}

# =========================================================
# 4. VÉRIFICATION DB_ADAPTER
# =========================================================

def check_db_adapter_usage():
    """Vérifie l'utilisation de db_adapter"""
    python_files = [
        'app.py',
        'promotion.py',
    ]
    
    usage = []
    missing = []
    
    for file_path in python_files:
        full_path = Path(__file__).parent.parent / file_path
        if not full_path.exists():
            continue
        
        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
            if 'db_adapter' in content or 'db_utils' in content:
                usage.append(file_path)
            else:
                # Vérifier s'il y a des requêtes SQL directes
                if re.search(r'INFORMATION_SCHEMA|DATABASE\(\)', content, re.IGNORECASE):
                    missing.append(file_path)
    
    return {'using': usage, 'missing': missing}

# =========================================================
# RAPPORT COMPLET
# =========================================================

def generate_report():
    """Génère un rapport complet"""
    print_header("VÉRIFICATION COMPLÈTE DU PROJET")
    
    # 1. Routes Flask
    print_header("1. ROUTES FLASK")
    routes = find_all_routes()
    print_success(f"Total de routes trouvées: {len(routes)}")
    
    # Grouper par fichier
    routes_by_file = {}
    for route in routes:
        file = route['file']
        if file not in routes_by_file:
            routes_by_file[file] = []
        routes_by_file[file].append(route)
    
    for file, file_routes in sorted(routes_by_file.items()):
        print_info(f"\n{file}: {len(file_routes)} routes")
        for route in file_routes[:5]:  # Afficher les 5 premières
            print(f"   - {route['route']} → {route['function']}")
        if len(file_routes) > 5:
            print(f"   ... et {len(file_routes) - 5} autres")
    
    # 2. Compatibilité PostgreSQL
    print_header("2. COMPATIBILITÉ POSTGRESQL")
    issues = check_postgresql_compatibility()
    if issues:
        print_error(f"Problèmes de compatibilité trouvés: {len(issues)}")
        for issue in issues[:10]:  # Afficher les 10 premiers
            print_warning(f"{issue['file']}:{issue['line']} - {issue['issue']}")
            print(f"   Code: {issue['code']}")
        if len(issues) > 10:
            print(f"   ... et {len(issues) - 10} autres problèmes")
    else:
        print_success("Aucun problème de compatibilité PostgreSQL détecté")
    
    # 3. DB Adapter
    print_header("3. UTILISATION DB_ADAPTER")
    db_adapter_check = check_db_adapter_usage()
    if db_adapter_check['using']:
        print_success(f"db_adapter utilisé dans: {', '.join(db_adapter_check['using'])}")
    if db_adapter_check['missing']:
        print_warning(f"db_adapter pourrait être utilisé dans: {', '.join(db_adapter_check['missing'])}")
    
    # Vérifier que db_adapter est configuré dans app.py
    app_path = Path(__file__).parent.parent / 'app.py'
    if app_path.exists():
        with open(app_path, 'r', encoding='utf-8') as f:
            app_content = f.read()
            if 'setup_sqlalchemy_middleware' in app_content:
                print_success("Middleware db_adapter configuré dans app.py")
            else:
                print_error("Middleware db_adapter NON configuré dans app.py")
    
    # 4. État Git
    print_header("4. ÉTAT GIT")
    git_status = check_git_status()
    if 'error' in git_status:
        print_error(f"Erreur Git: {git_status['error']}")
    else:
        if git_status['total'] == 0:
            print_success("Aucun fichier modifié ou non tracké")
        else:
            print_warning(f"Fichiers modifiés/non trackés: {git_status['total']}")
            if git_status['modified']:
                print_info(f"Modifiés: {len(git_status['modified'])}")
                for f in git_status['modified'][:5]:
                    print(f"   - {f}")
            if git_status['untracked']:
                print_info(f"Non trackés: {len(git_status['untracked'])}")
                for f in git_status['untracked'][:5]:
                    print(f"   - {f}")
    
    # 5. Résumé
    print_header("5. RÉSUMÉ")
    print(f"Routes Flask: {Colors.GREEN}{len(routes)}{Colors.RESET}")
    print(f"Problèmes PostgreSQL: {Colors.RED if issues else Colors.GREEN}{len(issues)}{Colors.RESET}")
    print(f"Fichiers Git modifiés: {Colors.YELLOW if git_status.get('total', 0) > 0 else Colors.GREEN}{git_status.get('total', 0)}{Colors.RESET}")
    
    # Recommandations
    print_header("6. RECOMMANDATIONS")
    if issues:
        print_warning("Corriger les problèmes de compatibilité PostgreSQL avant le déploiement")
    if git_status.get('total', 0) > 0:
        print_warning("Commiter et pousser les modifications sur Git")
    if not db_adapter_check['using']:
        print_warning("Considérer l'utilisation de db_adapter pour une meilleure compatibilité")
    
    print("\n" + "="*80 + "\n")

if __name__ == '__main__':
    generate_report()

