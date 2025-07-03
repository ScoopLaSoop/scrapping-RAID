#!/usr/bin/env python3
"""
Script pour lancer le scrapping avec différentes options
"""

import asyncio
import argparse
import logging
import sys
from main import ScrapingOrchestrator

def setup_logging(debug=False):
    """Configure le logging"""
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('scrapping.log'),
            logging.StreamHandler()
        ]
    )

async def run_single_company(company_name: str, legal_scraper_type='api'):
    """Traite une seule entreprise"""
    print(f"🏢 Traitement de l'entreprise: {company_name}")
    
    orchestrator = ScrapingOrchestrator(legal_scraper_type=legal_scraper_type)
    
    # Créer un objet entreprise factice
    company = {
        'id': 'test',
        'name': company_name,
        'airtable_record_id': 'test123'
    }
    
    await orchestrator.process_company(company)
    print(f"✅ Traitement terminé pour: {company_name}")

async def run_full_process(legal_scraper_type='api'):
    """Lance le processus complet"""
    print("🚀 Lancement du processus complet...")
    orchestrator = ScrapingOrchestrator(legal_scraper_type=legal_scraper_type)
    await orchestrator.run_scraping_process()

def main():
    """Point d'entrée principal"""
    parser = argparse.ArgumentParser(description='Système de scrapping d\'entreprises')
    parser.add_argument('--debug', action='store_true', help='Mode debug')
    parser.add_argument('--company', type=str, help='Traiter une seule entreprise')
    parser.add_argument('--test-webhook', action='store_true', help='Tester le webhook')
    parser.add_argument('--legal-scraper', choices=['api', 'alternative', 'original'], 
                       default='api', help='Type de scraper pour les données légales (défaut: api)')
    
    args = parser.parse_args()
    
    # Configuration du logging
    setup_logging(args.debug)
    
    try:
        if args.test_webhook:
            from modules.webhook_sender import WebhookSender
            sender = WebhookSender()
            success = asyncio.run(sender.send_test_data())
            sys.exit(0 if success else 1)
        
        elif args.company:
            asyncio.run(run_single_company(args.company, args.legal_scraper))
        
        else:
            asyncio.run(run_full_process(args.legal_scraper))
            
    except KeyboardInterrupt:
        print("\n⚠️ Arrêt demandé par l'utilisateur")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Erreur: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 