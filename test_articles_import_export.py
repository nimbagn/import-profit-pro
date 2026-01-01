#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de test pour l'import/export Excel des articles
"""

import pandas as pd
import os
from datetime import datetime

def create_example_excel():
    """Créer un fichier Excel exemple pour tester l'import"""
    
    # Données d'exemple
    data = {
        'Nom': [
            'Riz 25 kg',
            'Huile végétale 5L',
            'Javel 1L',
            'Sucre en poudre 1kg',
            'Tomate concentrée 400g'
        ],
        'Catégorie': [
            'Alimentaire',
            'Alimentaire',
            'Entretien',
            'Alimentaire',
            'Alimentaire'
        ],
        'Prix': [
            200000,
            15000,
            5000,
            8000,
            3000
        ],
        'Devise': [
            'GNF',
            'GNF',
            'GNF',
            'GNF',
            'GNF'
        ],
        'Poids (kg)': [
            25,
            5,
            1,
            1,
            0.4
        ],
        'Actif': [
            'Oui',
            'Oui',
            'Oui',
            'Oui',
            'Oui'
        ]
    }
    
    # Créer le DataFrame
    df = pd.DataFrame(data)
    
    # Créer le fichier Excel
    filename = 'exemple_articles_import.xlsx'
    output_dir = 'instance/uploads'
    os.makedirs(output_dir, exist_ok=True)
    filepath = os.path.join(output_dir, filename)
    
    # Écrire dans Excel
    with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Articles', index=False)
        
        # Ajuster la largeur des colonnes
        worksheet = writer.sheets['Articles']
        for idx, col in enumerate(df.columns):
            max_length = max(
                df[col].astype(str).map(len).max(),
                len(col)
            )
            worksheet.column_dimensions[chr(65 + idx)].width = min(max_length + 2, 50)
    
    print(f"✅ Fichier Excel exemple créé : {filepath}")
    print(f"   Nombre d'articles : {len(df)}")
    print(f"   Colonnes : {', '.join(df.columns.tolist())}")
    return filepath

def test_excel_read():
    """Tester la lecture du fichier Excel"""
    filepath = 'instance/uploads/exemple_articles_import.xlsx'
    
    if not os.path.exists(filepath):
        print(f"❌ Fichier non trouvé : {filepath}")
        return False
    
    try:
        df = pd.read_excel(filepath)
        print(f"✅ Fichier Excel lu avec succès")
        print(f"   Nombre de lignes : {len(df)}")
        print(f"   Colonnes : {', '.join(df.columns.tolist())}")
        print("\n   Première ligne :")
        print(f"   {df.iloc[0].to_dict()}")
        return True
    except Exception as e:
        print(f"❌ Erreur lors de la lecture : {e}")
        return False

if __name__ == '__main__':
    print("=" * 60)
    print("TEST IMPORT/EXPORT ARTICLES")
    print("=" * 60)
    
    print("\n1. Création du fichier Excel exemple...")
    filepath = create_example_excel()
    
    print("\n2. Test de lecture du fichier Excel...")
    test_excel_read()
    
    print("\n" + "=" * 60)
    print("✅ Tests terminés")
    print("=" * 60)
    print(f"\n📁 Fichier créé : {filepath}")
    print("   Vous pouvez utiliser ce fichier pour tester l'import sur http://localhost:5002/articles/import")

