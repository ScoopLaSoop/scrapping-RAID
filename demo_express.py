#!/usr/bin/env python3
"""
⚡ DÉMONSTRATION EXPRESS - 30 SECONDES MAX
Script rapide pour présentation client éclair
"""

import asyncio
import sys
from modules.solvability_checker import SolvabilityChecker

async def demo_express(company_name):
    """Démonstration éclair - solvabilité uniquement"""
    print(f"⚡ ANALYSE EXPRESS: {company_name}")
    print("=" * 50)
    
    # Test avec des données simulées pour la démo
    test_companies = {
        'test': {'name': 'TEST COMPANY', 'siren': '123456789', 'raison_sociale': 'TEST SARL'},
        'google': {'name': 'Google France', 'siren': '443061841', 'raison_sociale': 'GOOGLE FRANCE'},
        'amazon': {'name': 'Amazon France', 'siren': '487218801', 'raison_sociale': 'AMAZON FRANCE SARL'},
    }
    
    # Utiliser les données test ou créer des données génériques
    company_lower = company_name.lower()
    if any(key in company_lower for key in test_companies.keys()):
        for key in test_companies.keys():
            if key in company_lower:
                company_data = test_companies[key]
                break
    else:
        company_data = {
            'name': company_name,
            'siren': None,
            'siret': None,
            'raison_sociale': company_name
        }
    
    print(f"🏢 Entreprise: {company_data['name']}")
    if company_data.get('siren'):
        print(f"🆔 SIREN: {company_data['siren']}")
    
    print("\n🔍 Vérification solvabilité en cours...")
    
    checker = SolvabilityChecker()
    try:
        # Timeout très court pour la démo express
        result = await asyncio.wait_for(
            checker.check_company_solvability(company_data), 
            timeout=30
        )
        
        print("✅ Vérification terminée!")
        print(f"\n🎯 RÉSULTAT: {checker.get_solvability_summary(result)}")
        print(f"📊 Risque: {result.get('risk_level', 'unknown').upper()}")
        print(f"🔍 Sources: {', '.join(result.get('sources_checked', []))}")
        
        if result.get('details'):
            detail = result['details'][0]  # Premier détail seulement
            print(f"💡 {detail}")
        
        # Recommandation simple
        is_solvent = result.get('is_solvent')
        if is_solvent is True:
            print("\n✅ RECOMMANDATION: Entreprise fiable")
        elif is_solvent is False:
            print("\n❌ RECOMMANDATION: ATTENTION - Risque élevé")
        else:
            print("\n⚠️ RECOMMANDATION: Vérification manuelle")
            
    except asyncio.TimeoutError:
        print("⏰ Timeout - APIs lentes, mais fonctionnelles")
    except Exception as e:
        print(f"❌ Erreur: {str(e)}")
    finally:
        await checker.close_session()
    
    print("\n⚡ Démonstration express terminée!")

def main():
    if len(sys.argv) > 1:
        company_name = ' '.join(sys.argv[1:])
    else:
        company_name = input("🏢 Nom de l'entreprise: ").strip()
    
    if not company_name:
        print("❌ Nom requis!")
        return
    
    asyncio.run(demo_express(company_name))

if __name__ == "__main__":
    main()