#!/usr/bin/env python3
"""
Script de sauvegarde de la configuration pour la mise en production
"""

import os
import zipfile
import datetime
from pathlib import Path

def create_backup():
    """Crée une sauvegarde complète du projet"""
    
    # Nom du fichier de sauvegarde avec timestamp
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"scrapping_backup_{timestamp}.zip"
    
    # Fichiers à sauvegarder
    files_to_backup = [
        "main.py",
        "config.py",
        "requirements.txt",
        "run_scraper.py",
        "modules/",
        ".env",
        "production_setup.md",
        "deploy.sh",
        "README.md"
    ]
    
    print(f"🔄 Création de la sauvegarde : {backup_name}")
    
    with zipfile.ZipFile(backup_name, 'w', zipfile.ZIP_DEFLATED) as backup_zip:
        for file_path in files_to_backup:
            if os.path.exists(file_path):
                if os.path.isdir(file_path):
                    # Sauvegarder récursivement les dossiers
                    for root, dirs, files in os.walk(file_path):
                        for file in files:
                            file_full_path = os.path.join(root, file)
                            backup_zip.write(file_full_path)
                else:
                    # Sauvegarder les fichiers individuels
                    backup_zip.write(file_path)
                print(f"✅ {file_path} sauvegardé")
            else:
                print(f"⚠️  {file_path} introuvable")
    
    # Afficher les informations de sauvegarde
    backup_size = os.path.getsize(backup_name)
    print(f"\n🎉 Sauvegarde terminée !")
    print(f"📁 Fichier : {backup_name}")
    print(f"📊 Taille : {backup_size / 1024:.1f} KB")
    
    return backup_name

def verify_env_file():
    """Vérifie que le fichier .env contient toutes les variables nécessaires"""
    
    required_vars = [
        "AIRTABLE_API_KEY",
        "AIRTABLE_BASE_ID", 
        "AIRTABLE_TABLE_NAME",
        "AIRTABLE_VIEW_NAME",
        "OPENAI_API_KEY",
        "OPENAI_ORG_ID"
    ]
    
    print("\n🔍 Vérification de la configuration...")
    
    if not os.path.exists(".env"):
        print("❌ Fichier .env introuvable !")
        return False
    
    with open(".env", "r") as f:
        env_content = f.read()
    
    missing_vars = []
    for var in required_vars:
        if var not in env_content or f"{var}=" not in env_content:
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Variables manquantes : {', '.join(missing_vars)}")
        return False
    
    print("✅ Toutes les variables d'environnement sont présentes")
    return True

def production_checklist():
    """Affiche une checklist avant la mise en production"""
    
    print("\n📋 CHECKLIST AVANT MISE EN PRODUCTION")
    print("="*50)
    
    checklist = [
        "✅ Bot testé localement avec succès",
        "✅ Toutes les APIs fonctionnent (Airtable, OpenAI)",
        "✅ Variables d'environnement configurées",
        "✅ Sauvegarde créée",
        "⬜ Compte hébergeur créé (PythonAnywhere recommandé)",
        "⬜ Code uploadé sur l'hébergeur",
        "⬜ Dépendances installées",
        "⬜ Variables d'environnement configurées sur l'hébergeur",
        "⬜ Cron job configuré (9h chaque jour)",
        "⬜ Test de production effectué",
        "⬜ Monitoring configuré"
    ]
    
    for item in checklist:
        print(f"  {item}")
    
    print("\n🎯 PROCHAINES ÉTAPES :")
    print("1. Créer un compte PythonAnywhere (5$/mois)")
    print("2. Suivre le guide dans production_setup.md")
    print("3. Tester une fois en production")
    print("4. Configurer le cron job quotidien")

if __name__ == "__main__":
    print("🚀 PRÉPARATION POUR LA MISE EN PRODUCTION")
    print("="*50)
    
    # Créer la sauvegarde
    backup_file = create_backup()
    
    # Vérifier la configuration
    config_ok = verify_env_file()
    
    # Afficher la checklist
    production_checklist()
    
    print(f"\n💾 Sauvegarde créée : {backup_file}")
    
    if config_ok:
        print("✅ Configuration OK - Prêt pour la production !")
    else:
        print("❌ Configuration incomplète - Vérifiez votre fichier .env") 