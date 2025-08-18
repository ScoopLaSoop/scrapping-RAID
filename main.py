#!/usr/bin/env python3
"""
Bot de scrapping complet - Version avec planification automatique et vérification de solvabilité
1. Scrapping web → Récupère la raison sociale officielle  
2. API légale → Récupère les données SIRET/TVA avec la vraie raison sociale
3. Vérification solvabilité → Vérifie l'état de l'entreprise (active/fermée/procédures)
4. Planification automatique → Tous les jours à 10h heure de Paris
"""

import asyncio
import logging
import schedule
import time
import threading
from datetime import datetime
from pytz import timezone
from config import Config
from modules.airtable_client import AirtableClient
from modules.company_scraper import CompanyScraper
from modules.api_legal_scraper import APILegalScraper
from modules.solvability_checker import SolvabilityChecker

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

def get_paris_time():
    """Retourne l'heure actuelle à Paris"""
    paris_tz = timezone('Europe/Paris')
    return datetime.now(paris_tz)

async def run_scrapping():
    """Fonction principale du scrappeur"""
    logger = logging.getLogger(__name__)
    paris_time = get_paris_time()
    logger.info(f"🚀 Démarrage du scrappeur complet à {paris_time.strftime('%Y-%m-%d %H:%M:%S')} (Paris)...")
    
    try:
        # Configuration
        print("🔧 Chargement de la configuration...")
        config = Config()
        print("✅ Configuration chargée - Traitement complet avec vérification de solvabilité")
        
        # Initialisation d'Airtable
        print("📊 Connexion à Airtable...")
        airtable_client = AirtableClient()
        print("✅ Connexion Airtable OK")
        
        # Récupération des entreprises
        print("📥 Récupération des entreprises depuis Airtable...")
        companies = await airtable_client.get_companies()
        print(f"✅ {len(companies)} entreprises récupérées")
        
        # Traiter toutes les entreprises sans limite
        logger.info(f"🎯 Traitement de {len(companies)} entreprises (toutes les entreprises disponibles)")
        
        # Initialisation des scrappeurs
        print("⚙️ Initialisation des scrappeurs...")
        company_scraper = CompanyScraper()
        api_legal_scraper = APILegalScraper()
        solvability_checker = SolvabilityChecker()
        print("✅ Scrappeurs initialisés")
        
        # Traitement des entreprises
        for i, company in enumerate(companies, 1):
            print(f"\n📋 === Entreprise {i}/{len(companies)} ===")
            
            company_name = company.get('name', 'Nom non défini')
            record_id = company.get('id')
            
            logger.info(f"🏢 Traitement de: {company_name}")
            print(f"🏢 Entreprise: {company_name}")
            print(f"🆔 ID: {record_id}")
            
            try:
                # Timeout global par entreprise (3 minutes max)
                start_time = asyncio.get_event_loop().time()
                max_time_per_company = 180  # 3 minutes
                
                # ÉTAPE 1: Scrapping web pour trouver la raison sociale
                print("🌐 ÉTAPE 1: Scrapping web...")
                
                try:
                    # Timeout optimisé pour le scrapping web (1 minute max)
                    website_data = await asyncio.wait_for(
                        company_scraper.scrape_company_website(company_name),
                        timeout=60  # 1 minute
                    )
                except asyncio.TimeoutError:
                    print("⏰ Timeout scrapping web - Passage à l'étape suivante...")
                    website_data = {'error': 'Timeout scrapping web'}
                except Exception as e:
                    print(f"❌ Erreur scrapping web: {str(e)}")
                    website_data = {'error': str(e)}
                
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
                
                try:
                    # Timeout pour l'API légale (1 minute max)
                    legal_data = await asyncio.wait_for(
                        api_legal_scraper.scrape_legal_info(official_name),
                        timeout=60  # 1 minute
                    )
                except asyncio.TimeoutError:
                    print("⏰ Timeout API légale - Passage à l'étape suivante...")
                    legal_data = {'error': 'Timeout API légale'}
                except Exception as e:
                    print(f"❌ Erreur API légale: {str(e)}")
                    legal_data = {'error': str(e)}
                
                if legal_data and not legal_data.get('error'):
                    print(f"✅ Données légales récupérées: {legal_data}")
                    
                    # ÉTAPE 3: Vérification de solvabilité
                    print("🏦 ÉTAPE 3: Vérification de solvabilité...")
                    # Préparer les données pour la vérification
                    company_data_for_check = {
                        'siren': legal_data.get('siren'),
                        'siret': legal_data.get('siret'),
                        'raison_sociale': legal_data.get('raison_sociale'),
                        'name': company_name
                    }
                    
                    try:
                        # Timeout pour la solvabilité (2 minutes max)
                        solvability_data = await asyncio.wait_for(
                            solvability_checker.check_company_solvability(company_data_for_check),
                            timeout=120  # 2 minutes
                        )
                    except asyncio.TimeoutError:
                        print("⏰ Timeout vérification solvabilité - Données partielles sauvegardées...")
                        solvability_data = {
                            'error': 'Timeout vérification solvabilité',
                            'is_solvent': None,
                            'status': 'unknown',
                            'risk_level': 'unknown'
                        }
                    except Exception as e:
                        print(f"❌ Erreur solvabilité: {str(e)}")
                        solvability_data = {'error': str(e)}
                    
                    if solvability_data and not solvability_data.get('error'):
                        print(f"✅ Solvabilité vérifiée: {solvability_checker.get_solvability_summary(solvability_data)}")
                        print(f"📊 Détails: {solvability_data.get('details', [])}")
                    else:
                        print(f"⚠️ Vérification solvabilité échouée: {solvability_data.get('error', 'Erreur inconnue')}")
                        if not solvability_data:
                            solvability_data = {}  # Pas de données de solvabilité
                    
                    # ÉTAPE 4: Mise à jour Airtable avec toutes les données
                    print("💾 ÉTAPE 4: Mise à jour Airtable...")
                    await airtable_client.update_company_data(record_id, {
                        'legal_data': legal_data,
                        'website_data': website_data,  # Peut être vide si échec web
                        'solvability_data': solvability_data
                    })
                    print(f"✅ Mise à jour Airtable réussie")
                    
                    logger.info(f"✅ Entreprise {company_name} traitée avec succès")
                else:
                    print(f"❌ Erreur API légale: {legal_data}")
                    logger.error(f"❌ Erreur API légale pour {company_name}: {legal_data}")
                    
                    # Même si l'API légale échoue, sauver les données web si disponibles
                    # et essayer quand même la vérification de solvabilité avec le nom
                    if website_data and not website_data.get('error'):
                        print("🔄 Sauvegarde des données web et tentative de vérification solvabilité...")
                        
                        # Essayer la vérification de solvabilité avec les données disponibles
                        company_data_for_check = {
                            'siren': None,  # Pas de SIREN disponible
                            'siret': None,  # Pas de SIRET disponible
                            'raison_sociale': website_data.get('raison_sociale'),
                            'name': company_name
                        }
                        
                        try:
                            solvability_data = await asyncio.wait_for(
                                solvability_checker.check_company_solvability(company_data_for_check),
                                timeout=120  # 2 minutes
                            )
                        except asyncio.TimeoutError:
                            print("⏰ Timeout vérification solvabilité (mode dégradé)...")
                            solvability_data = {}
                        except Exception as e:
                            print(f"❌ Erreur solvabilité: {str(e)}")
                            solvability_data = {}
                        
                        if solvability_data and not solvability_data.get('error'):
                            print(f"✅ Solvabilité vérifiée (mode dégradé): {solvability_checker.get_solvability_summary(solvability_data)}")
                        else:
                            print(f"⚠️ Vérification solvabilité échouée: {solvability_data.get('error', 'Erreur inconnue')}")
                            solvability_data = {}
                        
                        await airtable_client.update_company_data(record_id, {
                            'legal_data': {},
                            'website_data': website_data,
                            'solvability_data': solvability_data
                        })
                        print("✅ Données web et solvabilité sauvegardées")
                    else:
                        print("❌ Aucune donnée à sauvegarder")
                
                # Vérifier le temps total écoulé
                elapsed_time = asyncio.get_event_loop().time() - start_time
                if elapsed_time > max_time_per_company:
                    print(f"⏰ Temps maximum dépassé pour {company_name} ({elapsed_time:.1f}s)")
                
            except Exception as e:
                logger.error(f"❌ Erreur critique pour {company_name}: {str(e)}")
                print(f"❌ Erreur critique pour {company_name}: {str(e)}")
                # Continuer avec l'entreprise suivante
                continue
            
            # Pause minimale entre les entreprises
            await asyncio.sleep(1)
        
        # Fermer les sessions
        print("\n🔧 Fermeture des sessions...")
        await company_scraper.close_session()
        await api_legal_scraper.close_session()
        await solvability_checker.close_session()
        print("✅ Sessions fermées")
        
        end_time = get_paris_time()
        logger.info(f"🎉 Scrapping terminé avec succès à {end_time.strftime('%Y-%m-%d %H:%M:%S')} (Paris)!")
        print(f"\n🎉 Scrapping terminé avec succès à {end_time.strftime('%Y-%m-%d %H:%M:%S')} (Paris)!")
        
    except Exception as e:
        logger.error(f"❌ Erreur critique: {str(e)}")
        print(f"❌ Erreur critique: {str(e)}")
        import traceback
        traceback.print_exc()

def job_wrapper():
    """Wrapper pour exécuter la fonction async dans le scheduler"""
    print(f"\n🕙 Début de l'exécution planifiée - {get_paris_time().strftime('%Y-%m-%d %H:%M:%S')} (Paris)")
    asyncio.run(run_scrapping())

def run_scheduler():
    """Exécute le scheduler dans un thread séparé"""
    while True:
        schedule.run_pending()
        time.sleep(1)

def main():
    """Fonction principale avec planification"""
    print("=== SCRAPPEUR COMPLET - VERSION PLANIFIÉE AVEC SOLVABILITÉ ===")
    print("🕙 Planification: Tous les jours à 10h00 (heure de Paris)")
    print("📊 Traitement: Toutes les entreprises disponibles")
    print("🏦 Nouveauté: Vérification automatique de la solvabilité")
    print("=" * 60)
    
    setup_logging()
    logger = logging.getLogger(__name__)
    
    # Planifier la tâche pour 10h00 heure de Paris
    schedule.every().day.at("10:00").do(job_wrapper)
    
    # Afficher l'heure actuelle et la prochaine exécution
    paris_time = get_paris_time()
    logger.info(f"🕐 Heure actuelle (Paris): {paris_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🕐 Heure actuelle (Paris): {paris_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Calculer la prochaine exécution
    next_run = schedule.next_run()
    if next_run:
        logger.info(f"⏰ Prochaine exécution: {next_run.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"⏰ Prochaine exécution: {next_run.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Exécution automatique immédiate puis planification
    print("\n" + "=" * 60)
    print("🚀 Mode automatique : Exécution immédiate puis planification")
    print("=" * 60)
    
    try:
        # Exécution immédiate
        print("\n🚀 Exécution immédiate en cours...")
        job_wrapper()
        
        # Démarrer le scheduler dans un thread séparé
        print("\n📅 Démarrage du scheduler pour les prochaines exécutions...")
        logger.info("📅 Scheduler démarré - En attente de la prochaine exécution...")
        
        scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
        scheduler_thread.start()
        
        print("✅ Bot en cours d'exécution...")
        print("📋 Logs disponibles dans 'scrapping_complete.log'")
        print("🛑 Appuyez sur Ctrl+C pour arrêter")
        
        # Boucle principale
        try:
            while True:
                time.sleep(60)  # Vérifier toutes les minutes
                # Afficher le statut périodiquement
                next_run = schedule.next_run()
                if next_run:
                    current_time = get_paris_time()
                    time_until_next = next_run - current_time.replace(tzinfo=None)
                    hours, remainder = divmod(time_until_next.total_seconds(), 3600)
                    minutes, _ = divmod(remainder, 60)
                    
                    # Afficher le statut seulement toutes les 10 minutes pour éviter le spam
                    if int(minutes) % 10 == 0:
                        print(f"⏳ Prochaine exécution dans {int(hours)}h {int(minutes)}m - {next_run.strftime('%Y-%m-%d %H:%M:%S')}")
                    
        except KeyboardInterrupt:
            print("\n🛑 Arrêt du bot demandé...")
            logger.info("🛑 Arrêt du bot par l'utilisateur")
            
    except KeyboardInterrupt:
        print("\n🛑 Arrêt du bot demandé...")
        logger.info("🛑 Arrêt du bot par l'utilisateur")
    except Exception as e:
        logger.error(f"❌ Erreur dans le scheduler: {str(e)}")
        print(f"❌ Erreur dans le scheduler: {str(e)}")

if __name__ == "__main__":
    main() 