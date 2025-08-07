#!/usr/bin/env python3
"""
🎯 SCRIPT DE DÉMONSTRATION CLIENT
Teste le scraper complet sur une entreprise spécifique
Parfait pour les présentations et démonstrations
"""

import asyncio
import logging
from datetime import datetime
from modules.company_scraper import CompanyScraper
from modules.api_legal_scraper import APILegalScraper
from modules.solvability_checker import SolvabilityChecker

# Configuration du logging pour démo
logging.basicConfig(level=logging.WARNING)  # Réduire les logs pour la démo

def print_header():
    """Affiche l'en-tête de démonstration"""
    print("=" * 80)
    print("🎯 DÉMONSTRATION SCRAPER AVEC VÉRIFICATION DE SOLVABILITÉ")
    print("🚀 Scrapping web + API légale + Vérification solvabilité")
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

def print_summary(solvability_data, checker):
    """Affiche un résumé de solvabilité coloré"""
    if not solvability_data:
        print("   ❓ Solvabilité: Indéterminée")
        return
    
    summary = checker.get_solvability_summary(solvability_data)
    risk_level = solvability_data.get('risk_level', 'unknown')
    sources = solvability_data.get('sources_checked', [])
    
    print(f"   🏦 SOLVABILITÉ: {summary}")
    print(f"   📊 Niveau de risque: {risk_level.upper()}")
    print(f"   🔍 Sources vérifiées: {', '.join(sources)}")
    
    if solvability_data.get('details'):
        print("   📝 Détails:")
        for detail in solvability_data['details'][:3]:  # Limiter à 3 détails pour la démo
            print(f"      • {detail}")

async def demo_entreprise(company_name):
    """Démonstration complète pour une entreprise"""
    start_time = datetime.now()
    
    print_header()
    print(f"🏢 Entreprise analysée: {company_name}")
    print(f"🕐 Démarrage: {start_time.strftime('%H:%M:%S')}")
    
    # Initialisation des modules
    print("\n⚙️ Initialisation des modules...")
    company_scraper = CompanyScraper()
    api_legal_scraper = APILegalScraper()
    solvability_checker = SolvabilityChecker()
    print("✅ Modules initialisés")
    
    try:
        # ÉTAPE 1: Scrapping web
        print_section("ÉTAPE 1: SCRAPPING WEB", "🌐")
        print("   🔍 Recherche du site web et extraction des données...")
        
        try:
            website_data = await asyncio.wait_for(
                company_scraper.scrape_company_website(company_name),
                timeout=120  # 2 minutes max pour la démo
            )
            
            if website_data and not website_data.get('error'):
                print("   ✅ Données web récupérées avec succès!")
                print_result("Site web", website_data.get('website'), "🌐")
                print_result("Raison sociale", website_data.get('raison_sociale'), "🏢")
                print_result("Adresse", website_data.get('adresse'), "📍")
                print_result("Téléphone", website_data.get('telephone'), "📞")
                print_result("Email", website_data.get('email'), "📧")
                official_name = website_data.get('raison_sociale', company_name)
            else:
                print(f"   ⚠️ Scrapping web échoué: {website_data.get('error', 'Erreur inconnue')}")
                website_data = {}
                official_name = company_name
                
        except asyncio.TimeoutError:
            print("   ⏰ Timeout scrapping web - Passage à l'étape suivante")
            website_data = {}
            official_name = company_name
        
        # ÉTAPE 2: API légale
        print_section("ÉTAPE 2: DONNÉES LÉGALES", "🏛️")
        print(f"   🔍 Recherche des données légales pour: {official_name}")
        
        try:
            legal_data = await asyncio.wait_for(
                api_legal_scraper.scrape_legal_info(official_name),
                timeout=60  # 1 minute max pour la démo
            )
            
            if legal_data and not legal_data.get('error'):
                print("   ✅ Données légales récupérées avec succès!")
                print_result("SIREN", legal_data.get('siren'), "🏢")
                print_result("SIRET", legal_data.get('siret'), "🏭")
                print_result("TVA Intracommunautaire", legal_data.get('tva'), "💼")
                print_result("Adresse légale", legal_data.get('adresse_legale'), "📍")
                print_result("Ville", legal_data.get('ville_legale'), "🏙️")
            else:
                print(f"   ⚠️ API légale échouée: {legal_data.get('error', 'Erreur inconnue')}")
                legal_data = {}
                
        except asyncio.TimeoutError:
            print("   ⏰ Timeout API légale - Passage à l'étape suivante")
            legal_data = {}
        
        # ÉTAPE 3: Vérification de solvabilité
        print_section("ÉTAPE 3: VÉRIFICATION DE SOLVABILITÉ", "🏦")
        print("   🔍 Vérification via BODACC, API Gouvernementale et InfoGreffe...")
        
        # Préparer les données pour la vérification
        company_data_for_check = {
            'siren': legal_data.get('siren') if legal_data else None,
            'siret': legal_data.get('siret') if legal_data else None,
            'raison_sociale': legal_data.get('raison_sociale') if legal_data else website_data.get('raison_sociale'),
            'name': company_name
        }
        
        try:
            solvability_data = await asyncio.wait_for(
                solvability_checker.check_company_solvability(company_data_for_check),
                timeout=120  # 2 minutes max pour la démo
            )
            
            if solvability_data and not solvability_data.get('error'):
                print("   ✅ Vérification de solvabilité terminée!")
                print_summary(solvability_data, solvability_checker)
            else:
                print(f"   ⚠️ Vérification solvabilité échouée: {solvability_data.get('error', 'Erreur inconnue')}")
                solvability_data = {}
                
        except asyncio.TimeoutError:
            print("   ⏰ Timeout vérification solvabilité")
            solvability_data = {}
        
        # RÉSUMÉ FINAL
        print_section("RÉSUMÉ FINAL", "📊")
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        print(f"   🕐 Durée totale: {duration:.1f} secondes")
        print(f"   🌐 Données web: {'✅ Récupérées' if website_data else '❌ Échec'}")
        print(f"   🏛️ Données légales: {'✅ Récupérées' if legal_data else '❌ Échec'}")
        print(f"   🏦 Solvabilité: {'✅ Vérifiée' if solvability_data else '❌ Échec'}")
        
        if solvability_data:
            is_solvent = solvability_data.get('is_solvent')
            if is_solvent is True:
                print("   🎯 RECOMMANDATION: ✅ Entreprise fiable pour devis")
            elif is_solvent is False:
                print("   🎯 RECOMMANDATION: ❌ ATTENTION - Vérifier avant devis")
            else:
                print("   🎯 RECOMMANDATION: ⚠️ Vérification manuelle recommandée")
        
        print_section("DONNÉES BRUTES (JSON)", "💾")
        print(f"   🌐 Web: {len(str(website_data))} caractères")
        print(f"   🏛️ Légal: {len(str(legal_data))} caractères") 
        print(f"   🏦 Solvabilité: {len(str(solvability_data))} caractères")
        
    except Exception as e:
        print(f"\n❌ Erreur critique: {str(e)}")
    
    finally:
        # Fermer les sessions
        print("\n🔧 Fermeture des sessions...")
        await company_scraper.close_session()
        await api_legal_scraper.close_session()
        await solvability_checker.close_session()
        print("✅ Sessions fermées")
    
    print("\n" + "=" * 80)
    print("🎉 DÉMONSTRATION TERMINÉE")
    print("=" * 80)

def main():
    """Fonction principale de démonstration"""
    print("🎯 DÉMONSTRATION SCRAPER - VERSION CLIENT")
    print("=" * 50)
    
    # Demander le nom de l'entreprise
    company_name = input("\n🏢 Entrez le nom de l'entreprise à analyser: ").strip()
    
    if not company_name:
        print("❌ Nom d'entreprise requis!")
        return
    
    print(f"\n🚀 Démarrage de l'analyse pour: {company_name}")
    print("⏱️ Cela peut prendre 1-3 minutes...")
    
    # Lancer la démonstration
    try:
        asyncio.run(demo_entreprise(company_name))
    except KeyboardInterrupt:
        print("\n🛑 Démonstration interrompue par l'utilisateur")
    except Exception as e:
        print(f"\n❌ Erreur: {str(e)}")

if __name__ == "__main__":
    main()