#!/usr/bin/env python3
"""
Système de scrapping d'entreprises
Auteur: Assistant IA
Description: Scrapping d'informations d'entreprises pour remplir une base de données
"""

import asyncio
import logging
from typing import List, Dict, Any
from datetime import datetime

from modules.airtable_client import AirtableClient
from modules.company_scraper import CompanyScraper  
from modules.tva_scraper import TVAScraper
from modules.alternative_tva_scraper import AlternativeTVAScraper
from modules.api_legal_scraper import APILegalScraper
from modules.webhook_sender import WebhookSender
from config import Config

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scrapping.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ScrapingOrchestrator:
    def __init__(self, legal_scraper_type='api'):
        self.airtable_client = AirtableClient()
        self.company_scraper = CompanyScraper()
        self.webhook_sender = WebhookSender()
        
        # Choisir le type de scraper légal
        if legal_scraper_type == 'api':
            self.legal_scraper = APILegalScraper()
            logger.info("🔧 Utilisation de l'API publique pour les données légales")
        elif legal_scraper_type == 'alternative':
            self.legal_scraper = AlternativeTVAScraper()
            logger.info("🔧 Utilisation du scraper alternatif pour les données légales")
        else:
            self.legal_scraper = TVAScraper()
            logger.info("🔧 Utilisation du scraper TVA original pour les données légales")
        
    async def run_scraping_process(self):
        """Exécute le processus complet de scrapping"""
        try:
            logger.info("🚀 Démarrage du processus de scrapping...")
            
            # Étape 2: Récupération des noms d'entreprise depuis Airtable
            logger.info("📋 Récupération des entreprises depuis Airtable...")
            companies = await self.airtable_client.get_companies()
            logger.info(f"✅ {len(companies)} entreprises récupérées")
            
            # Traitement de chaque entreprise
            for company in companies:
                await self.process_company(company)
                
            logger.info("✅ Processus de scrapping terminé avec succès!")
            
        except Exception as e:
            logger.error(f"❌ Erreur dans le processus de scrapping: {str(e)}")
            raise

    async def process_company(self, company: Dict[str, Any]):
        """Traite une entreprise individuellement"""
        company_name = company.get('name', 'Nom inconnu')
        record_id = company.get('airtable_record_id', '')
        logger.info(f"🏢 Traitement de l'entreprise: {company_name}")
        
        try:
            # Étape 3.1: Scrapping du site web de l'entreprise
            logger.info(f"🌐 Scrapping du site web pour: {company_name}")
            web_data = await self.company_scraper.scrape_company_website(company_name)
            
            # Étape 3.2: Scrapping des informations légales (SIRET, SIREN, TVA)
            logger.info(f"📊 Scrapping des informations légales pour: {company_name}")
            legal_data = await self.legal_scraper.scrape_legal_info(company_name)
            
            # Préparation des données pour Airtable
            scraped_data = {
                'company_name': company_name,
                'timestamp': datetime.now().isoformat(),
                'website_data': web_data,
                'legal_data': legal_data
            }
            
            # Écriture directe dans Airtable
            logger.info(f"💾 Mise à jour des données dans Airtable pour: {company_name}")
            success = await self.airtable_client.update_company_data(record_id, scraped_data)
            
            if success:
                logger.info(f"✅ Entreprise {company_name} traitée avec succès")
            else:
                logger.warning(f"⚠️ Données collectées pour {company_name} mais erreur lors de la mise à jour Airtable")
            
        except Exception as e:
            logger.error(f"❌ Erreur lors du traitement de {company_name}: {str(e)}")
            # Continuer avec les autres entreprises

async def main():
    """Point d'entrée principal"""
    orchestrator = ScrapingOrchestrator()
    await orchestrator.run_scraping_process()

if __name__ == "__main__":
    asyncio.run(main()) 