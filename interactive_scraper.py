#!/usr/bin/env python3
"""
Scrapper interactif pour une seule entreprise
Script interactif qui demande le nom de l'entreprise à l'utilisateur
"""

import asyncio
import logging
import json
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
            logging.FileHandler('interactive_scraping.log', encoding='utf-8')
        ]
    )

async def scrape_company_interactive():
    """Scrapper interactif pour une entreprise"""
    logger = logging.getLogger(__name__)
    
    print("="*60)
    print("🚀 SCRAPPEUR INTERACTIF D'ENTREPRISE")
    print("="*60)
    
    # Demander le nom de l'entreprise
    while True:
        company_name = input("\n📋 Entrez le nom de l'entreprise à scrapper: ").strip()
        if company_name:
            break
        print("❌ Veuillez entrer un nom d'entreprise valide.")
    
    # Demander si on veut sauvegarder dans Airtable
    save_to_airtable = input("\n💾 Voulez-vous sauvegarder dans Airtable ? (o/N): ").strip().lower()
    save_to_airtable = save_to_airtable in ['o', 'oui', 'y', 'yes']
    
    # Demander l'ID Airtable si nécessaire
    airtable_record_id = None
    if save_to_airtable:
        airtable_record_id = input("🆔 ID du record Airtable (optionnel, laisser vide si nouveau): ").strip()
        if not airtable_record_id:
            airtable_record_id = None
    
    print(f"\n🎯 Démarrage du scrapping pour: {company_name}")
    logger.info(f"🚀 Scrapping interactif pour: {company_name}")
    
    try:
        # Configuration
        config = Config()
        
        # Initialisation des modules
        company_scraper = CompanyScraper()
        api_legal_scraper = APILegalScraper()
        airtable_client = AirtableClient() if save_to_airtable else None
        
        print("\n" + "="*50)
        print(f"📋 TRAITEMENT DE: {company_name}")
        print("="*50)
        
        # ÉTAPE 1: Scrapping web
        print("\n🌐 ÉTAPE 1: Recherche du site web et extraction des données...")
        website_data = await company_scraper.scrape_company_website(company_name)
        
        if website_data and not website_data.get('error'):
            print("✅ Données web récupérées avec succès!")
            print("🌐 Données du site web:")
            for key, value in website_data.items():
                if value and key != 'error':
                    print(f"  • {key}: {value}")
            
            official_name = website_data.get('raison_sociale', company_name)
            if official_name != company_name:
                print(f"\n🎯 Raison sociale officielle trouvée: {official_name}")
            else:
                print(f"\n⚠️ Raison sociale identique au nom commercial")
        else:
            print("⚠️ Scrapping web échoué ou aucune donnée trouvée")
            if website_data and website_data.get('error'):
                print(f"   Erreur: {website_data['error']}")
            website_data = {}
            official_name = company_name
        
        # ÉTAPE 2: API légale
        print(f"\n🏛️ ÉTAPE 2: Recherche des données légales pour: {official_name}")
        legal_data = await api_legal_scraper.scrape_legal_info(official_name)
        
        if legal_data and not legal_data.get('error'):
            print("✅ Données légales récupérées avec succès!")
            print("🏛️ Données légales:")
            for key, value in legal_data.items():
                if value and key != 'error':
                    print(f"  • {key}: {value}")
        else:
            print("⚠️ Récupération des données légales échouée")
            if legal_data and legal_data.get('error'):
                print(f"   Erreur: {legal_data['error']}")
            legal_data = {}
        
        # ÉTAPE 3: Sauvegarde
        results = {
            'company_name': company_name,
            'official_name': official_name,
            'website_data': website_data,
            'legal_data': legal_data,
            'timestamp': str(asyncio.get_event_loop().time())
        }
        
        # Sauvegarder dans un fichier JSON
        filename = f"scraping_result_{company_name.replace(' ', '_').replace('/', '_')}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"\n💾 Résultats sauvegardés dans: {filename}")
        
        # Sauvegarder dans Airtable si demandé
        if save_to_airtable and airtable_client:
            print("\n📊 Sauvegarde dans Airtable...")
            if airtable_record_id:
                success = await airtable_client.update_company_data(airtable_record_id, {
                    'legal_data': legal_data,
                    'website_data': website_data
                })
                if success:
                    print(f"✅ Données mises à jour dans Airtable (ID: {airtable_record_id})")
                else:
                    print("❌ Erreur lors de la mise à jour Airtable")
            else:
                print("⚠️ Pas d'ID record fourni - impossible de mettre à jour Airtable")
                print("   Pour créer un nouveau record, utilisez l'interface Airtable")
        
        # Fermer les sessions
        await company_scraper.close_session()
        await api_legal_scraper.close_session()
        
        # Résumé final
        print("\n" + "="*60)
        print("📊 RÉSUMÉ FINAL")
        print("="*60)
        
        has_website_data = website_data and not website_data.get('error')
        has_legal_data = legal_data and not legal_data.get('error')
        
        if has_website_data or has_legal_data:
            print("✅ SCRAPPING RÉUSSI!")
            if has_website_data:
                print("  🌐 Données web: ✅")
            else:
                print("  🌐 Données web: ❌")
            
            if has_legal_data:
                print("  🏛️ Données légales: ✅")
            else:
                print("  🏛️ Données légales: ❌")
                
            if save_to_airtable and airtable_record_id:
                print("  📊 Sauvegarde Airtable: ✅")
            
            print(f"  📄 Fichier JSON: {filename}")
        else:
            print("❌ AUCUNE DONNÉE RÉCUPÉRÉE")
            print("   Vérifiez le nom de l'entreprise et réessayez")
        
        print(f"\n🎉 Traitement terminé pour: {company_name}")
        
        return results
        
    except Exception as e:
        logger.error(f"❌ Erreur critique: {str(e)}")
        print(f"\n❌ Erreur critique: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def main():
    """Fonction principale"""
    setup_logging()
    
    try:
        results = asyncio.run(scrape_company_interactive())
        
        if results:
            print("\n🎊 Session terminée avec succès!")
        else:
            print("\n💥 Session terminée avec des erreurs")
            
    except KeyboardInterrupt:
        print("\n\n⏹️ Scrapping interrompu par l'utilisateur")
    except Exception as e:
        print(f"\n💥 Erreur fatale: {str(e)}")

if __name__ == "__main__":
    main() 