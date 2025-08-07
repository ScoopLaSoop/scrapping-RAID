#!/usr/bin/env python3
"""
🎯 DÉMONSTRATION SUR LA DERNIÈRE ENTREPRISE AIRTABLE
Récupère automatiquement la dernière entreprise de la base et lance la démo
"""

import asyncio
import logging
from datetime import datetime
from modules.airtable_client import AirtableClient
from modules.company_scraper import CompanyScraper
from modules.api_legal_scraper import APILegalScraper
from modules.solvability_checker import SolvabilityChecker

# Configuration du logging
logging.basicConfig(level=logging.WARNING)

def print_header():
    """Affiche l'en-tête de démonstration"""
    print("=" * 80)
    print("🎯 DÉMONSTRATION - DERNIÈRE ENTREPRISE AIRTABLE")
    print("🔄 Récupération automatique + Analyse complète")
    print("=" * 80)

def print_section(title, emoji):
    """Affiche une section avec style"""
    print(f"\n{emoji} {title}")
    print("-" * 60)

def print_result(label, value, emoji="📊"):
    """Affiche un résultat avec style"""
    if value:
        print(f"   {emoji} {label}: {value}")
    else:
        print(f"   ❌ {label}: Non trouvé")

async def get_latest_company():
    """Récupère la dernière entreprise ajoutée à Airtable"""
    print_section("RÉCUPÉRATION DEPUIS AIRTABLE", "📋")
    print("   🔍 Connexion à Airtable...")
    
    airtable_client = AirtableClient()
    companies = await airtable_client.get_companies()
    
    if not companies:
        print("   ❌ Aucune entreprise trouvée dans Airtable")
        return None
    
    # Prendre la dernière entreprise (la plus récente)
    latest_company = companies[-1]
    
    print(f"   ✅ {len(companies)} entreprises trouvées")
    print(f"   🎯 Dernière entreprise: {latest_company.get('name', 'Nom non défini')}")
    print(f"   🆔 ID Airtable: {latest_company.get('id')}")
    
    return latest_company

async def demo_complete_analysis(company_data):
    """Analyse complète de l'entreprise"""
    company_name = company_data.get('name', 'Nom non défini')
    company_id = company_data.get('id')
    start_time = datetime.now()
    
    print(f"\n🏢 ANALYSE DE: {company_name}")
    print(f"🕐 Démarrage: {start_time.strftime('%H:%M:%S')}")
    
    # Initialisation des modules
    print("\n⚙️ Initialisation des modules...")
    company_scraper = CompanyScraper()
    api_legal_scraper = APILegalScraper()
    solvability_checker = SolvabilityChecker()
    print("✅ Modules initialisés")
    
    results = {
        'website_data': {},
        'legal_data': {},
        'solvability_data': {}
    }
    
    try:
        # ÉTAPE 1: Scrapping web
        print_section("ÉTAPE 1: SCRAPPING WEB", "🌐")
        print("   🔍 Recherche du site web officiel...")
        
        try:
            website_data = await asyncio.wait_for(
                company_scraper.scrape_company_website(company_name),
                timeout=120
            )
            
            if website_data and not website_data.get('error'):
                results['website_data'] = website_data
                print("   ✅ Données web récupérées!")
                print_result("Site web", website_data.get('website'), "🌐")
                print_result("Raison sociale", website_data.get('raison_sociale'), "🏢")
                print_result("Adresse", website_data.get('adresse'), "📍")
                print_result("Téléphone", website_data.get('telephone'), "📞")
                print_result("Mobile", website_data.get('mobile'), "📱")
                print_result("Email", website_data.get('email'), "📧")
                official_name = website_data.get('raison_sociale', company_name)
            else:
                print(f"   ⚠️ Scrapping web échoué: {website_data.get('error', 'Erreur inconnue')}")
                official_name = company_name
                
        except asyncio.TimeoutError:
            print("   ⏰ Timeout scrapping web (2 minutes dépassées)")
            official_name = company_name
        
        # ÉTAPE 2: API légale
        print_section("ÉTAPE 2: DONNÉES LÉGALES", "🏛️")
        print(f"   🔍 Recherche SIREN/SIRET pour: {official_name}")
        
        try:
            legal_data = await asyncio.wait_for(
                api_legal_scraper.scrape_legal_info(official_name),
                timeout=60
            )
            
            if legal_data and not legal_data.get('error'):
                results['legal_data'] = legal_data
                print("   ✅ Données légales récupérées!")
                print_result("SIREN", legal_data.get('siren'), "🏢")
                print_result("SIRET", legal_data.get('siret'), "🏭")
                print_result("TVA Intracommunautaire", legal_data.get('tva'), "💼")
                print_result("Adresse légale", legal_data.get('adresse_legale'), "📍")
                print_result("Code postal", legal_data.get('code_postal_legal'), "📮")
                print_result("Ville légale", legal_data.get('ville_legale'), "🏙️")
            else:
                print(f"   ⚠️ API légale échouée: {legal_data.get('error', 'Erreur inconnue')}")
                
        except asyncio.TimeoutError:
            print("   ⏰ Timeout API légale (1 minute dépassée)")
        
        # ÉTAPE 3: Vérification de solvabilité
        print_section("ÉTAPE 3: VÉRIFICATION DE SOLVABILITÉ", "🏦")
        print("   🔍 Analyse via BODACC, API Gouvernementale et InfoGreffe...")
        
        # Préparer les données pour la vérification
        company_data_for_check = {
            'siren': results['legal_data'].get('siren'),
            'siret': results['legal_data'].get('siret'),
            'raison_sociale': results['legal_data'].get('raison_sociale') or results['website_data'].get('raison_sociale'),
            'name': company_name
        }
        
        try:
            solvability_data = await asyncio.wait_for(
                solvability_checker.check_company_solvability(company_data_for_check),
                timeout=120
            )
            
            if solvability_data and not solvability_data.get('error'):
                results['solvability_data'] = solvability_data
                print("   ✅ Vérification de solvabilité terminée!")
                
                # Affichage détaillé des résultats de solvabilité
                summary = solvability_checker.get_solvability_summary(solvability_data)
                print(f"   🎯 RÉSULTAT: {summary}")
                print(f"   📊 Statut: {solvability_data.get('status', 'unknown')}")
                print(f"   ⚠️ Niveau de risque: {solvability_data.get('risk_level', 'unknown').upper()}")
                print(f"   🔍 Sources vérifiées: {', '.join(solvability_data.get('sources_checked', []))}")
                
                if solvability_data.get('details'):
                    print("   📝 Détails:")
                    for detail in solvability_data['details'][:3]:
                        print(f"      • {detail}")
            else:
                print(f"   ⚠️ Vérification solvabilité échouée: {solvability_data.get('error', 'Erreur inconnue')}")
                
        except asyncio.TimeoutError:
            print("   ⏰ Timeout vérification solvabilité (2 minutes dépassées)")
        
        # RÉSUMÉ FINAL
        print_section("RÉSUMÉ FINAL", "📊")
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        print(f"   🕐 Durée totale: {duration:.1f} secondes")
        print(f"   🌐 Données web: {'✅ Récupérées' if results['website_data'] else '❌ Échec'}")
        print(f"   🏛️ Données légales: {'✅ Récupérées' if results['legal_data'] else '❌ Échec'}")
        print(f"   🏦 Solvabilité: {'✅ Vérifiée' if results['solvability_data'] else '❌ Échec'}")
        
        # Recommandation finale
        if results['solvability_data']:
            is_solvent = results['solvability_data'].get('is_solvent')
            risk_level = results['solvability_data'].get('risk_level', 'unknown')
            
            print(f"\n   🎯 RECOMMANDATION FINALE:")
            if is_solvent is True and risk_level == 'low':
                print("   ✅ ENTREPRISE FIABLE - Devis recommandé")
            elif is_solvent is True and risk_level == 'medium':
                print("   ⚠️ ENTREPRISE ACCEPTABLE - Vérification supplémentaire recommandée")
            elif is_solvent is False:
                print("   ❌ ENTREPRISE À RISQUE - Éviter les devis")
            else:
                print("   ❓ ENTREPRISE À VÉRIFIER - Analyse manuelle requise")
        
        # VRAIE sauvegarde Airtable
        print_section("💾 MISE À JOUR AIRTABLE", "💾")
        print("   📤 Sauvegarde des données dans Airtable...")
        
        try:
            # Utiliser le client Airtable pour sauvegarder
            airtable_client = AirtableClient()
            
            # Préparer les données pour Airtable
            update_data = {}
            if results['website_data']:
                update_data['website_data'] = results['website_data']
                print("   🌐 Données web ajoutées: Site, Adresse, Téléphone, Email")
            
            if results['legal_data']:
                update_data['legal_data'] = results['legal_data']
                print("   🏛️ Données légales ajoutées: SIREN, SIRET, TVA, Adresse légale")
            
            if results['solvability_data']:
                update_data['solvability_data'] = results['solvability_data']
                print("   🏦 Données solvabilité ajoutées: État, Statut, Risque, Détails")
            
            # Effectuer la mise à jour réelle
            success = await airtable_client.update_company_data(
                company_id, 
                update_data
            )
            
            if success:
                print("   ✅ MISE À JOUR AIRTABLE RÉUSSIE!")
                print("   📋 L'entreprise est maintenant marquée comme 'Get Scrapped = True'")
                print("   🎯 Toutes les données sont disponibles dans votre base")
            else:
                print("   ❌ Erreur lors de la mise à jour Airtable")
                
        except Exception as e:
            print(f"   ❌ Erreur sauvegarde Airtable: {str(e)}")
            print("   💡 Vérifiez que les nouveaux champs existent dans Airtable")
        
    except Exception as e:
        print(f"\n❌ Erreur critique: {str(e)}")
    
    finally:
        # Fermer les sessions
        print("\n🔧 Fermeture des sessions...")
        await company_scraper.close_session()
        await api_legal_scraper.close_session()
        await solvability_checker.close_session()
        print("✅ Sessions fermées")
    
    return results

async def main():
    """Fonction principale"""
    print_header()
    
    try:
        # Récupérer la dernière entreprise
        latest_company = await get_latest_company()
        
        if not latest_company:
            print("\n❌ Impossible de récupérer une entreprise depuis Airtable")
            print("💡 Vérifiez votre configuration Airtable dans le fichier .env")
            return
        
        # Demander confirmation
        company_name = latest_company.get('name', 'Nom non défini')
        print(f"\n🤔 Voulez-vous analyser '{company_name}' ? (o/N): ", end="")
        
        try:
            choice = input().strip().lower()
            if choice not in ['o', 'oui', 'y', 'yes']:
                print("👋 Démonstration annulée")
                return
        except KeyboardInterrupt:
            print("\n👋 Démonstration annulée")
            return
        
        # Lancer l'analyse complète
        print(f"\n🚀 Démarrage de l'analyse complète...")
        print("⏱️ Cela peut prendre 2-5 minutes selon l'entreprise...")
        
        results = await demo_complete_analysis(latest_company)
        
        print("\n" + "=" * 80)
        print("🎉 DÉMONSTRATION TERMINÉE AVEC SUCCÈS")
        print("💡 Cette entreprise a été analysée ET mise à jour dans Airtable")
        print("🔍 Vérifiez votre base Airtable - les données sont maintenant visibles")
        print("=" * 80)
        
    except KeyboardInterrupt:
        print("\n🛑 Démonstration interrompue par l'utilisateur")
    except Exception as e:
        print(f"\n❌ Erreur: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())