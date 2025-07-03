#!/bin/bash

# 🚀 Script de configuration GitHub Actions
# Automatise la mise en place du bot sur GitHub

echo "🚀 Configuration GitHub Actions - Bot de Scrapping"
echo "================================================"

# Vérifier si Git est initialisé
if [ ! -d ".git" ]; then
    echo "📁 Initialisation de Git..."
    git init
fi

# Vérifier si Docker est installé
if ! command -v docker &> /dev/null; then
    echo "❌ Docker n'est pas installé. Veuillez l'installer d'abord."
    echo "💡 Téléchargez Docker Desktop : https://www.docker.com/products/docker-desktop"
    exit 1
fi

# Vérifier si le fichier .env existe
if [ ! -f ".env" ]; then
    echo "❌ Fichier .env manquant !"
    echo "💡 Copiez env_example.txt vers .env et configurez vos variables"
    exit 1
fi

echo "✅ Prérequis vérifiés"

# Test de construction Docker
echo "🔧 Test de construction Docker..."
docker build -t scraper-bot-test . --quiet

if [ $? -eq 0 ]; then
    echo "✅ Construction Docker réussie"
else
    echo "❌ Erreur lors de la construction Docker"
    exit 1
fi

# Test rapide du conteneur
echo "🔍 Test rapide du conteneur..."
docker run --rm scraper-bot-test python -c "
import sys
print(f'✅ Python {sys.version}')
try:
    from selenium import webdriver
    print('✅ Selenium installé')
except ImportError as e:
    print(f'❌ Selenium: {e}')
try:
    import openai
    print('✅ OpenAI installé')
except ImportError as e:
    print(f'❌ OpenAI: {e}')
"

# Ajouter tous les fichiers
echo "📦 Ajout des fichiers au Git..."
git add .

# Vérifier le statut
echo "📋 Statut Git :"
git status --short

# Préparer les instructions
echo ""
echo "🎯 PROCHAINES ÉTAPES MANUELLES :"
echo "================================="
echo ""
echo "1. 📝 Créer le repository sur GitHub :"
echo "   - Aller sur https://github.com/new"
echo "   - Nom : scrapping-RAID"
echo "   - Visibilité : Privé (recommandé)"
echo "   - Créer le repository"
echo ""
echo "2. 🔗 Lier le repository local :"
echo "   git remote add origin https://github.com/VOTRE-USERNAME/scrapping-RAID.git"
echo "   git branch -M main"
echo "   git commit -m 'Initial commit - Bot de scrapping'"
echo "   git push -u origin main"
echo ""
echo "3. 🔐 Configurer les secrets GitHub :"
echo "   - Aller sur Settings > Secrets and variables > Actions"
echo "   - Ajouter ces secrets :"
echo "     * AIRTABLE_API_KEY"
echo "     * AIRTABLE_BASE_ID"
echo "     * AIRTABLE_TABLE_NAME"
echo "     * AIRTABLE_VIEW_NAME"
echo "     * OPENAI_API_KEY"
echo "     * OPENAI_ORG_ID"
echo ""
echo "4. 🚀 Tester l'exécution :"
echo "   - Aller sur Actions > Bot de Scrapping Quotidien"
echo "   - Run workflow > Run workflow"
echo ""
echo "5. 📊 Consulter les logs :"
echo "   - Développer '🚀 Exécution du bot de scrapping'"
echo ""
echo "📖 Guide complet : setup_github_actions.md"
echo ""
echo "🎉 Votre bot tournera automatiquement chaque jour à 9h !"

# Nettoyer l'image de test
docker rmi scraper-bot-test --force > /dev/null 2>&1 