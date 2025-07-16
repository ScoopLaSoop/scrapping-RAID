#!/usr/bin/env python3
"""
Scrapper pour une seule entreprise - Version ligne de commande
Usage: python single_company_scraper.py "Nom de l'entreprise"
"""

import asyncio
import logging
import sys
import json
from config import Config
from modules.company_scraper import CompanyScraper
from modules.api_legal_scraper import APILegalScraper

def setup_logging():
    """Configure le système de logging"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('single_company_scraping.log', encoding='utf-8')
        ]
    )

async def scrape_single_company(company_name: str, save_to_file: bool = True):
    """Scrappe une seule entreprise et retourne les résultats"""
    logger = logging.getLogger(__name__)
    logger.info(f"🚀 Démarrage du scrapping pour: {company_name}")
    
    try:
        # Configuration
        print("🔧 Chargement de la configuration...")
        config = Config()
        print("✅ Configuration chargée")
        
        # Initialisation des scrappeurs
        print("⚙️ Initialisation des scrappeurs...")
        company_scraper = CompanyScraper()
        api_legal_scraper = APILegalScraper()
        print("✅ Scrappeurs initialisés")
        
        print(f"\n📋 === Traitement de: {company_name} ===")
        
        # ÉTAPE 1: Scrapping web pour trouver la raison sociale
        print("🌐 ÉTAPE 1: Scrapping web...")
        website_data = await company_scraper.scrape_company_website(company_name)
        
        # Déterminer le nom à utiliser pour l'API légale
        if website_data and not website_data.get('error'):
            print(f"✅ Données web récupérées: {website_data}")
            
            # Extraire la raison sociale officielle
            official_name = website_data.get('raison_sociale', company_name)
            if official_name != company_name:
                print(f"🎯 Raison sociale officielle trouvée: {official_name}")
            else:
                print(f"⚠️ Raison sociale identique au nom commercial")
        else:
            print(f"⚠️ Scrapping web échoué: {website_data.get('error', 'Erreur inconnue') if website_data else 'Erreur inconnue'}")
            print("🔄 FALLBACK: Utilisation du nom commercial pour l'API légale")
            website_data = {}  # Pas de données web
            official_name = company_name  # Utiliser le nom commercial
            
        # ÉTAPE 2: Scrapping API légale avec le nom déterminé
        print(f"🏛️ ÉTAPE 2: Scrapping API légale avec: {official_name}")
        legal_data = await api_legal_scraper.scrape_legal_info(official_name)
        
        # Préparer les résultats finaux
        results = {
            'company_name': company_name,
            'official_name': official_name,
            'website_data': website_data,
            'legal_data': legal_data,
            'success': True
        }
        
        if legal_data and not legal_data.get('error'):
            print(f"✅ Données légales récupérées: {legal_data}")
            logger.info(f"✅ Entreprise {company_name} traitée avec succès")
        else:
            print(f"❌ Erreur API légale: {legal_data}")
            logger.error(f"❌ Erreur API légale pour {company_name}: {legal_data}")
            results['success'] = False
        
        # Fermer les sessions
        print("\n🔧 Fermeture des sessions...")
        await company_scraper.close_session()
        await api_legal_scraper.close_session()
        print("✅ Sessions fermées")
        
        # Sauvegarder dans un fichier JSON si demandé
        if save_to_file:
            filename = f"results_{company_name.replace(' ', '_').replace('/', '_')}.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            print(f"💾 Résultats sauvegardés dans: {filename}")
        
        # Afficher un résumé
        print("\n" + "="*50)
        print("📊 RÉSUMÉ DES DONNÉES RÉCUPÉRÉES")
        print("="*50)
        
        if website_data and not website_data.get('error'):
            print("🌐 DONNÉES WEB:")
            for key, value in website_data.items():
                if value:
                    print(f"  • {key}: {value}")
        
        if legal_data and not legal_data.get('error'):
            print("\n🏛️ DONNÉES LÉGALES:")
            for key, value in legal_data.items():
                if value:
                    print(f"  • {key}: {value}")
        
        print("\n🎉 Scrapping terminé avec succès!")
        return results
        
    except Exception as e:
        logger.error(f"❌ Erreur critique: {str(e)}")
        print(f"❌ Erreur critique: {str(e)}")
        import traceback
        traceback.print_exc()
        return {'error': str(e), 'success': False}

def main():
    """Fonction principale avec gestion des arguments"""
    if len(sys.argv) < 2:
        print("❌ Usage: python single_company_scraper.py \"Nom de l'entreprise\"")
        print("\n📋 Exemples:")
        print("  python single_company_scraper.py \"ACOGEMAS\"")
        print("  python single_company_scraper.py \"Google France\"")
        print("  python single_company_scraper.py \"Maison d'Accueil Spécialisée\"")
        sys.exit(1)
    
    company_name = sys.argv[1]
    
    print("=== SCRAPPEUR ENTREPRISE UNIQUE ===")
    print(f"🎯 Entreprise cible: {company_name}")
    
    setup_logging()
    
    # Exécuter le scrapping
    results = asyncio.run(scrape_single_company(company_name))
    
    if results.get('success'):
        print(f"✅ Scrapping réussi pour: {company_name}")
    else:
        print(f"❌ Échec du scrapping pour: {company_name}")
        sys.exit(1)

if __name__ == "__main__":
    main() 