#!/bin/bash
# Script de déploiement pour PythonAnywhere

echo "🚀 Déploiement du bot de scrapping..."

# Installation des dépendances
pip3.9 install --user -r requirements.txt

# Création du dossier de logs
mkdir -p logs

# Configuration des permissions
chmod +x run_scraper.py

# Test de la configuration
echo "🔍 Test de la configuration..."
python3.9 -c "
import os
print('✅ Python OK')
try:
    from modules.airtable_client import AirtableClient
    print('✅ Airtable OK')
except Exception as e:
    print(f'❌ Airtable: {e}')
try:
    import openai
    print('✅ OpenAI OK')
except Exception as e:
    print(f'❌ OpenAI: {e}')
try:
    from selenium import webdriver
    print('✅ Selenium OK')
except Exception as e:
    print(f'❌ Selenium: {e}')
"

echo "✅ Déploiement terminé !"
echo "📝 N'oubliez pas de configurer le cron job :"
echo "   0 9 * * * cd /home/votrenom/scrapping-RAID && python3.9 main.py" 