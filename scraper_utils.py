#!/usr/bin/env python3
"""
Utilitaires de scrapping pour une seule entreprise
Module réutilisable pour d'autres scripts
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from config import Config
from modules.company_scraper import CompanyScraper
from modules.api_legal_scraper import APILegalScraper

async def scrape_company(company_name: str, include_website: bool = True, include_legal: bool = True) -> Dict[str, Any]:
    """
    Scrappe les informations d'une seule entreprise
    
    Args:
        company_name: Nom de l'entreprise à scrapper
        include_website: Inclure le scrapping du site web (défaut: True)
        include_legal: Inclure les données légales via API (défaut: True)
    
    Returns:
        Dict contenant les résultats du scrapping
    """
    logger = logging.getLogger(__name__)
    
    results = {
        'company_name': company_name,
        'official_name': company_name,
        'website_data': {},
        'legal_data': {},
        'success': False,
        'errors': []
    }
    
    company_scraper = None
    api_legal_scraper = None
    
    try:
        # Initialisation des scrappeurs
        if include_website:
            company_scraper = CompanyScraper()
        if include_legal:
            api_legal_scraper = APILegalScraper()
        
        # ÉTAPE 1: Scrapping web (si demandé)
        if include_website and company_scraper:
            logger.info(f"🌐 Scrapping web pour: {company_name}")
            website_data = await company_scraper.scrape_company_website(company_name)
            
            if website_data and not website_data.get('error'):
                results['website_data'] = website_data
                # Extraire la raison sociale officielle
                official_name = website_data.get('raison_sociale', company_name)
                if official_name and official_name != company_name:
                    results['official_name'] = official_name
                logger.info(f"✅ Données web récupérées pour: {company_name}")
            else:
                error_msg = website_data.get('error', 'Erreur inconnue') if website_data else 'Aucune donnée web'
                results['errors'].append(f"Web scraping: {error_msg}")
                logger.warning(f"⚠️ Scrapping web échoué pour {company_name}: {error_msg}")
        
        # ÉTAPE 2: API légale (si demandé)
        if include_legal and api_legal_scraper:
            search_name = results['official_name']  # Utiliser la raison sociale si trouvée
            logger.info(f"🏛️ API légale pour: {search_name}")
            legal_data = await api_legal_scraper.scrape_legal_info(search_name)
            
            if legal_data and not legal_data.get('error'):
                results['legal_data'] = legal_data
                logger.info(f"✅ Données légales récupérées pour: {company_name}")
            else:
                error_msg = legal_data.get('error', 'Erreur inconnue') if legal_data else 'Aucune donnée légale'
                results['errors'].append(f"Legal API: {error_msg}")
                logger.warning(f"⚠️ API légale échouée pour {company_name}: {error_msg}")
        
        # Déterminer le succès global
        has_website_data = results['website_data'] and not results['website_data'].get('error')
        has_legal_data = results['legal_data'] and not results['legal_data'].get('error')
        results['success'] = has_website_data or has_legal_data
        
        return results
        
    except Exception as e:
        error_msg = f"Erreur critique: {str(e)}"
        results['errors'].append(error_msg)
        logger.error(f"❌ {error_msg}")
        return results
        
    finally:
        # Fermer les sessions
        if company_scraper:
            await company_scraper.close_session()
        if api_legal_scraper:
            await api_legal_scraper.close_session()

def setup_logging(level: int = logging.INFO) -> None:
    """Configure le système de logging"""
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler()
        ]
    )

# Fonction synchrone pour faciliter l'usage
def scrape_company_sync(company_name: str, include_website: bool = True, include_legal: bool = True) -> Dict[str, Any]:
    """
    Version synchrone de scrape_company()
    
    Args:
        company_name: Nom de l'entreprise à scrapper
        include_website: Inclure le scrapping du site web (défaut: True)
        include_legal: Inclure les données légales via API (défaut: True)
    
    Returns:
        Dict contenant les résultats du scrapping
    """
    return asyncio.run(scrape_company(company_name, include_website, include_legal))

# Exemple d'utilisation
if __name__ == "__main__":
    import sys
    
    setup_logging()
    
    # Test avec une entreprise
    if len(sys.argv) > 1:
        company_name = sys.argv[1]
    else:
        company_name = "Google France"  # Exemple par défaut
    
    print(f"🔍 Test du scrapping pour: {company_name}")
    
    # Scrapper avec toutes les options
    results = scrape_company_sync(company_name)
    
    print("\n📊 RÉSULTATS:")
    print(f"✅ Succès: {results['success']}")
    print(f"🏢 Nom original: {results['company_name']}")
    print(f"🏛️ Nom officiel: {results['official_name']}")
    
    if results['website_data']:
        print("\n🌐 Données web:")
        for key, value in results['website_data'].items():
            if value and key != 'error':
                print(f"  • {key}: {value}")
    
    if results['legal_data']:
        print("\n🏛️ Données légales:")
        for key, value in results['legal_data'].items():
            if value and key != 'error':
                print(f"  • {key}: {value}")
    
    if results['errors']:
        print("\n❌ Erreurs:")
        for error in results['errors']:
            print(f"  • {error}") 