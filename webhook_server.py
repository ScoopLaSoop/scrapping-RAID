#!/usr/bin/env python3
"""
Serveur webhook simple pour Make.com
Déclenche le scrapping en temps réel quand une nouvelle entreprise est ajoutée
"""

import asyncio
import logging
import json
import os
from datetime import datetime
from aiohttp import web
from config import Config
from modules.airtable_client import AirtableClient
from modules.company_scraper import CompanyScraper
from modules.api_legal_scraper import APILegalScraper
from modules.solvability_checker import SolvabilityChecker

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('webhook.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class WebhookServer:
    def __init__(self):
        self.config = Config()
        self.airtable_client = AirtableClient()
        self.company_scraper = CompanyScraper()
        self.api_legal_scraper = APILegalScraper()
        self.solvability_checker = SolvabilityChecker()
        
    async def handle_webhook(self, request):
        """Gère les requêtes webhook de Make.com"""
        try:
            # Récupérer les données JSON
            data = await request.json()
            logger.info(f"📥 Webhook reçu: {data}")
            
            # Extraire le record ID
            record_id = data.get('record_id')
            if not record_id:
                return web.json_response({
                    'error': 'record_id manquant',
                    'status': 'error'
                }, status=400)
            
            # Récupérer l'entreprise depuis Airtable
            company = await self.airtable_client.get_company_by_id(record_id)
            if not company:
                return web.json_response({
                    'error': f'Entreprise non trouvée: {record_id}',
                    'status': 'error'
                }, status=404)
            
            company_name = company.get('fields', {}).get('Nom de l\'entreprise', '')
            logger.info(f"🏢 Scrapping de l'entreprise: {company_name}")
            
            # Lancer le scrapping complet
            scraped_data = await self.scrape_single_company(company_name)
            
            # Mettre à jour Airtable
            await self.airtable_client.update_company_data(record_id, scraped_data)
            
            logger.info(f"✅ Scrapping terminé pour: {company_name}")
            
            return web.json_response({
                'status': 'success',
                'company_name': company_name,
                'record_id': record_id,
                'scraped_data': scraped_data
            })
            
        except Exception as e:
            logger.error(f"❌ Erreur webhook: {str(e)}")
            return web.json_response({
                'error': str(e),
                'status': 'error'
            }, status=500)
    
    async def scrape_single_company(self, company_name: str) -> dict:
        """Scrapping complet d'une entreprise"""
        scraped_data = {}
        
        try:
            # 1. Scrapping web
            logger.info(f"🌐 Scrapping web pour: {company_name}")
            website_data = await self.company_scraper.scrape_company_website(company_name)
            if website_data:
                scraped_data['website_data'] = website_data
            
            # 2. API légale
            logger.info(f"🏛️ API légale pour: {company_name}")
            legal_data = await self.api_legal_scraper.get_company_info(company_name)
            if legal_data:
                scraped_data['legal_data'] = legal_data
            
            # 3. Vérification solvabilité
            logger.info(f"🏦 Vérification solvabilité pour: {company_name}")
            solvability_data = await self.solvability_checker.check_company_solvability(company_name)
            if solvability_data:
                scraped_data['solvability_data'] = solvability_data
                
        except Exception as e:
            logger.error(f"❌ Erreur scrapping {company_name}: {str(e)}")
            scraped_data['error'] = str(e)
        
        return scraped_data
    
    async def health_check(self, request):
        """Endpoint de santé pour Railway"""
        return web.json_response({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'service': 'scrapping-RAID-webhook'
        })

async def main():
    """Démarrage du serveur webhook"""
    server = WebhookServer()
    
    # Créer l'application web
    app = web.Application()
    
    # Routes
    app.router.add_post('/webhook', server.handle_webhook)
    app.router.add_get('/health', server.health_check)
    
    # Port (Railway utilise la variable PORT)
    port = int(os.environ.get('PORT', 8080))
    
    logger.info(f"🚀 Serveur webhook démarré sur le port {port}")
    logger.info(f"📡 Webhook URL: http://localhost:{port}/webhook")
    logger.info(f"💚 Health check: http://localhost:{port}/health")
    
    # Démarrer le serveur
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    
    # Garder le serveur actif
    try:
        await asyncio.Future()  # Attendre indéfiniment
    except KeyboardInterrupt:
        logger.info("🛑 Arrêt du serveur webhook")
    finally:
        await runner.cleanup()

if __name__ == '__main__':
    asyncio.run(main())
