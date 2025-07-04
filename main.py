#!/usr/bin/env python3
"""
Bot de scrapping complet - Version avec scrapping web ET API légale
1. Scrapping web → Récupère la raison sociale officielle  
2. API légale → Récupère les données SIRET/TVA avec la vraie raison sociale
"""

import asyncio
import logging
from config import Config
from modules.airtable_client import AirtableClient
from modules.company_scraper import CompanyScraper
from modules.api_legal_scraper import APILegalScraper

def setup_logging():
    """Configure le système de logging"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('scrapping_complete.log', encoding='utf-8')
        ]
    )

async def main():
    """Fonction principale du scrappeur"""
    logger = logging.getLogger(__name__)
    logger.info("🚀 Démarrage du scrappeur complet...")
    
    try:
        # Configuration
        print("🔧 Chargement de la configuration...")
        config = Config()
        print("✅ Configuration chargée")
        
        # Initialisation d'Airtable
        print("📊 Connexion à Airtable...")
        airtable_client = AirtableClient()
        print("✅ Connexion Airtable OK")
        
        # Récupération des entreprises
        print("📥 Récupération des entreprises depuis Airtable...")
        companies = await airtable_client.get_companies()
        print(f"✅ {len(companies)} entreprises récupérées")
        
        # Limiter aux 3 premières pour test
        companies = companies[:3]
        logger.info(f"🎯 Test avec {len(companies)} entreprises")
        
        # Initialisation des scrappeurs
        print("⚙️ Initialisation des scrappeurs...")
        company_scraper = CompanyScraper()
        api_legal_scraper = APILegalScraper()
        print("✅ Scrappeurs initialisés")
        
        # Traitement des entreprises
        for i, company in enumerate(companies, 1):
            print(f"\n📋 === Entreprise {i}/{len(companies)} ===")
            
            company_name = company.get('name', 'Nom non défini')
            record_id = company.get('id')
            
            logger.info(f"🏢 Traitement de: {company_name}")
            print(f"🏢 Entreprise: {company_name}")
            print(f"🆔 ID: {record_id}")
            
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
                print(f"⚠️ Scrapping web échoué: {website_data.get('error', 'Erreur inconnue')}")
                print("🔄 FALLBACK: Utilisation du nom commercial pour l'API légale")
                website_data = {}  # Pas de données web
                official_name = company_name  # Utiliser le nom commercial
                
            # ÉTAPE 2: Scrapping API légale avec le nom déterminé
            print(f"🏛️ ÉTAPE 2: Scrapping API légale avec: {official_name}")
            legal_data = await api_legal_scraper.scrape_legal_info(official_name)
            
            if legal_data and not legal_data.get('error'):
                print(f"✅ Données légales récupérées: {legal_data}")
                
                # ÉTAPE 3: Mise à jour Airtable avec les données disponibles
                print("💾 ÉTAPE 3: Mise à jour Airtable...")
                await airtable_client.update_company_data(record_id, {
                    'legal_data': legal_data,
                    'website_data': website_data  # Peut être vide si échec web
                })
                print(f"✅ Mise à jour Airtable réussie")
                
                logger.info(f"✅ Entreprise {company_name} traitée avec succès")
            else:
                print(f"❌ Erreur API légale: {legal_data}")
                logger.error(f"❌ Erreur API légale pour {company_name}: {legal_data}")
                
                # Même si l'API légale échoue, sauver les données web si disponibles
                if website_data and not website_data.get('error'):
                    print("🔄 Sauvegarde des données web uniquement...")
                    await airtable_client.update_company_data(record_id, {
                        'legal_data': {},
                        'website_data': website_data
                    })
                    print("✅ Données web sauvegardées")
                else:
                    print("❌ Aucune donnée à sauvegarder")
            
            # Petite pause entre les entreprises
            await asyncio.sleep(2)
        
        # Fermer les sessions
        print("\n🔧 Fermeture des sessions...")
        await company_scraper.close_session()
        await api_legal_scraper.close_session()
        print("✅ Sessions fermées")
        
        logger.info(f"🎉 Scrapping terminé avec succès!")
        print("\n🎉 Scrapping terminé avec succès!")
        
    except Exception as e:
        logger.error(f"❌ Erreur critique: {str(e)}")
        print(f"❌ Erreur critique: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("=== SCRAPPEUR COMPLET - VERSION DEBUG ===")
    setup_logging()
    asyncio.run(main()) 