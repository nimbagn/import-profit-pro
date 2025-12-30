#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script pour exécuter la migration RH
Exécute le script SQL de migration pour créer les tables RH
"""

import os
import sys
import subprocess

def execute_migration():
    """Exécuter la migration SQL"""
    script_path = os.path.join(os.path.dirname(__file__), 'migration_rh_complete.sql')
    
    if not os.path.exists(script_path):
        print(f"❌ Erreur: Le fichier {script_path} n'existe pas")
        return False
    
    # Configuration MySQL (à adapter selon votre environnement)
    mysql_host = os.getenv('MYSQL_HOST', '127.0.0.1')
    mysql_port = os.getenv('MYSQL_PORT', '3306')
    mysql_user = os.getenv('MYSQL_USER', 'root')
    mysql_password = os.getenv('MYSQL_PASSWORD', '')
    mysql_database = os.getenv('MYSQL_DATABASE', 'madargn')
    
    print("🔄 Exécution de la migration RH...")
    print(f"   Base de données: {mysql_database}")
    print(f"   Hôte: {mysql_host}:{mysql_port}")
    print()
    
    try:
        # Construire la commande MySQL
        if mysql_password:
            cmd = [
                'mysql',
                f'-h{mysql_host}',
                f'-P{mysql_port}',
                f'-u{mysql_user}',
                f'-p{mysql_password}',
                mysql_database
            ]
        else:
            cmd = [
                'mysql',
                f'-h{mysql_host}',
                f'-P{mysql_port}',
                f'-u{mysql_user}',
                mysql_database
            ]
        
        # Exécuter la commande avec le script SQL
        with open(script_path, 'r', encoding='utf-8') as f:
            result = subprocess.run(
                cmd,
                stdin=f,
                capture_output=True,
                text=True
            )
        
        if result.returncode == 0:
            print("✅ Migration exécutée avec succès!")
            print()
            print("📊 Tables créées:")
            print("   - user_activity_logs")
            print("   - employees")
            print("   - employee_contracts")
            print("   - employee_trainings")
            print("   - employee_evaluations")
            print("   - employee_absences")
            print()
            print("🎯 Prochaines étapes:")
            print("   1. Redémarrer l'application Flask")
            print("   2. Créer un utilisateur avec un rôle RH")
            print("   3. Tester les fonctionnalités RH")
            return True
        else:
            print("❌ Erreur lors de l'exécution de la migration:")
            print(result.stderr)
            return False
            
    except FileNotFoundError:
        print("❌ Erreur: MySQL n'est pas installé ou n'est pas dans le PATH")
        print("   Installez MySQL ou utilisez la commande manuelle:")
        print(f"   mysql -h {mysql_host} -P {mysql_port} -u {mysql_user} -p {mysql_database} < {script_path}")
        return False
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

if __name__ == '__main__':
    success = execute_migration()
    sys.exit(0 if success else 1)

