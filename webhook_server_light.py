#!/usr/bin/env python3
"""
Serveur webhook léger pour Make.com (sans Chrome)
Déclenche le scrapping en temps réel avec APIs uniquement
"""

import asyncio
import logging
import json
import os
from datetime import datetime
from aiohttp import web
from config import Config
from modules.airtable_client import AirtableClient
from modules.api_legal_scraper import APILegalScraper
from modules.solvability_checker import SolvabilityChecker

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('webhook_light.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class WebhookServerLight:
    def __init__(self):
        self.config = Config()
        # Mise à jour temporaire de la clé API pour le test
        self.config.AIRTABLE_API_KEY = "patafQahY2YJYz2ZJ.0106dddf44d1c536bcefbd6566ecdd9861cb1f4461ecb31cf27fabb2a6132604"
        self.airtable_client = AirtableClient()
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
            
            company_name = company.get('name', '')
            logger.info(f"📋 Nom de l'entreprise récupéré: '{company_name}'")
            logger.info(f"📋 Tous les champs: {company.get('fields', {})}")
            logger.info(f"🏢 Scrapping API de l'entreprise: {company_name}")
            
            # Lancer le scrapping API uniquement
            scraped_data = await self.scrape_single_company_api(company_name)
            
            # Mettre à jour Airtable
            update_success = await self.airtable_client.update_company_data(record_id, scraped_data)
            
            logger.info(f"✅ Scrapping API terminé pour: {company_name}")
            
            # Envoyer les notifications vers Make.com si la mise à jour Airtable a réussi
            if update_success:
                await self.send_notifications_to_make(record_id, company_name)
            
            return web.json_response({
                'status': 'success',
                'company_name': company_name,
                'record_id': record_id,
                'scraped_data': scraped_data,
                'mode': 'api_only'
            })
            
        except Exception as e:
            logger.error(f"❌ Erreur webhook: {str(e)}")
            return web.json_response({
                'error': str(e),
                'status': 'error'
            }, status=500)
    
    async def scrape_single_company_api(self, company_name: str) -> dict:
        """Scrapping API uniquement d'une entreprise"""
        scraped_data = {}
        
        try:
            # 1. API légale (SIRET, SIREN, TVA, etc.)
            logger.info(f"🏛️ API légale pour: {company_name}")
            legal_data = await self.api_legal_scraper.scrape_legal_info(company_name)
            if legal_data:
                scraped_data['legal_data'] = legal_data
                logger.info(f"✅ Données légales récupérées pour: {company_name}")
            
            # 2. Vérification solvabilité
            logger.info(f"🏦 Vérification solvabilité pour: {company_name}")
            # Créer un dictionnaire avec les données de l'entreprise
            company_data = {
                'name': company_name,
                'raison_sociale': company_name
            }
            solvability_data = await self.solvability_checker.check_company_solvability(company_data)
            if solvability_data:
                scraped_data['solvability_data'] = solvability_data
                logger.info(f"✅ Données solvabilité récupérées pour: {company_name}")
                
        except Exception as e:
            logger.error(f"❌ Erreur scrapping API {company_name}: {str(e)}")
            scraped_data['error'] = str(e)
        
        return scraped_data
    
    async def send_notifications_to_make(self, record_id: str, company_name: str):
        """Envoie les notifications vers les webhooks Make.com"""
        try:
            # URLs des webhooks Make.com
            webhook_urls = [
                "https://hook.eu2.make.com/xntfo1d88k770bq8uykemtr7gvunh2y8",
                "https://hook.eu2.make.com/e86l71aeljrvlqvor4seahpv57gxl89b"
            ]
            
            # Données à envoyer
            notification_data = {
                "record_id": record_id,
                "company_name": company_name,
                "scrapping_completed": True,
                "timestamp": datetime.now().isoformat(),
                "source": "scrapping-RAID-webhook"
            }
            
            logger.info(f"📤 Envoi des notifications vers {len(webhook_urls)} webhooks Make.com")
            
            # Envoyer vers chaque webhook
            for i, url in enumerate(webhook_urls, 1):
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.post(url, json=notification_data, timeout=aiohttp.ClientTimeout(total=10)) as response:
                            if response.status == 200:
                                logger.info(f"✅ Notification {i} envoyée avec succès vers Make.com")
                            else:
                                logger.warning(f"⚠️ Erreur notification {i}: {response.status}")
                except Exception as e:
                    logger.error(f"❌ Erreur envoi notification {i}: {str(e)}")
                    
        except Exception as e:
            logger.error(f"❌ Erreur lors de l'envoi des notifications: {str(e)}")
    
    async def health_check(self, request):
        """Endpoint de santé pour Railway"""
        return web.json_response({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'service': 'scrapping-RAID-webhook-light',
            'mode': 'api_only'
        })

async def main():
    """Démarrage du serveur webhook léger"""
    server = WebhookServerLight()
    
    # Créer l'application web
    app = web.Application()
    
    # Routes
    app.router.add_post('/webhook', server.handle_webhook)
    app.router.add_get('/health', server.health_check)
    
    # Port (Railway utilise la variable PORT)
    port = int(os.environ.get('PORT', 8080))
    
    logger.info(f"🚀 Serveur webhook léger démarré sur le port {port}")
    logger.info(f"📡 Webhook URL: http://localhost:{port}/webhook")
    logger.info(f"💚 Health check: http://localhost:{port}/health")
    logger.info(f"🔧 Mode: API uniquement (sans Chrome)")
    
    # Démarrer le serveur
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    
    # Garder le serveur actif
    try:
        await asyncio.Future()  # Attendre indéfiniment
    except KeyboardInterrupt:
        logger.info("🛑 Arrêt du serveur webhook léger")
    finally:
        await runner.cleanup()

if __name__ == '__main__':
    asyncio.run(main())
