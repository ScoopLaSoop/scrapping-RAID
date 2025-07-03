"""
Module utilisant les APIs publiques françaises pour récupérer les informations légales
Plus fiable que le scraping de sites web
"""

import asyncio
import aiohttp
import logging
from typing import Dict, Any, Optional, List
from config import Config
import urllib.parse

logger = logging.getLogger(__name__)

class APILegalScraper:
    def __init__(self):
        self.config = Config()
        self.session = None
        
        # URLs des APIs publiques françaises
        self.apis = {
            'sirene': 'https://api.insee.fr/entreprises/sirene/V3/siret',
            'recherche_entreprise': 'https://recherche-entreprises.api.gouv.fr/search',
            'pappers': 'https://api.pappers.fr/v2/entreprise',  # API gratuite avec limite
        }
    
    async def get_session(self):
        """Crée ou retourne la session HTTP"""
        if not self.session:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.config.TIMEOUT),
                headers={'User-Agent': self.config.USER_AGENT}
            )
        return self.session
    
    async def close_session(self):
        """Ferme la session HTTP"""
        if self.session:
            await self.session.close()
            self.session = None
    
    async def scrape_legal_info(self, company_name: str) -> Dict[str, Any]:
        """Récupère les informations légales via les APIs publiques"""
        try:
            logger.info(f"🔍 Recherche API pour: {company_name}")
            
            # Essayer d'abord avec l'API de recherche d'entreprises
            result = await self._search_via_gouv_api(company_name)
            
            if result and not result.get('error'):
                logger.info(f"✅ Données trouvées via API gouvernementale pour {company_name}")
                return result
            
            # Fallback: essayer avec l'API Pappers (gratuite avec limite)
            result = await self._search_via_pappers_api(company_name)
            
            if result and not result.get('error'):
                logger.info(f"✅ Données trouvées via API Pappers pour {company_name}")
                return result
            
            # Fallback: recherche manuelle dans les données ouvertes
            result = await self._search_manual_fallback(company_name)
            
            if result and not result.get('error'):
                logger.info(f"✅ Données trouvées via recherche manuelle pour {company_name}")
                return result
            
            return {'error': f'Aucune donnée trouvée pour {company_name}'}
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de la recherche API pour {company_name}: {e}")
            return {'error': str(e)}
        finally:
            await self.close_session()
    
    async def _search_via_gouv_api(self, company_name: str) -> Dict[str, Any]:
        """Recherche via l'API gouvernementale recherche-entreprises"""
        try:
            session = await self.get_session()
            
            # Encoder le nom pour l'URL
            encoded_name = urllib.parse.quote(company_name)
            url = f"{self.apis['recherche_entreprise']}?q={encoded_name}&limite=10"
            
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    results = data.get('results', [])
                    if results:
                        # Prendre le premier résultat le plus pertinent
                        best_match = self._find_best_match(results, company_name)
                        
                        if best_match:
                            return self._format_api_result(best_match)
                
                logger.warning(f"⚠️ API gouv: {response.status} pour {company_name}")
                return {'error': f'API gouv error: {response.status}'}
                
        except Exception as e:
            logger.error(f"❌ Erreur API gouv: {e}")
            return {'error': str(e)}
    
    async def _search_via_pappers_api(self, company_name: str) -> Dict[str, Any]:
        """Recherche via l'API Pappers (gratuite avec limite)"""
        try:
            session = await self.get_session()
            
            # API Pappers gratuite (500 requêtes/mois)
            url = f"{self.apis['pappers']}"
            params = {
                'nom_entreprise': company_name,
                'format': 'json'
            }
            
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if data.get('entreprises'):
                        enterprise = data['entreprises'][0]
                        return self._format_pappers_result(enterprise)
                
                logger.warning(f"⚠️ API Pappers: {response.status} pour {company_name}")
                return {'error': f'API Pappers error: {response.status}'}
                
        except Exception as e:
            logger.error(f"❌ Erreur API Pappers: {e}")
            return {'error': str(e)}
    
    async def _search_manual_fallback(self, company_name: str) -> Dict[str, Any]:
        """Recherche manuelle dans les données ouvertes"""
        try:
            # Utiliser l'API Insee directement (plus complexe mais publique)
            session = await self.get_session()
            
            # Rechercher dans l'annuaire des entreprises
            search_url = "https://api.insee.fr/entreprises/sirene/V3/siret"
            headers = {
                'Accept': 'application/json',
                'User-Agent': self.config.USER_AGENT
            }
            
            params = {
                'q': f'denominationUniteLegale:{company_name}*',
                'nombre': 10
            }
            
            async with session.get(search_url, headers=headers, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if data.get('etablissements'):
                        # Prendre le premier établissement
                        etablissement = data['etablissements'][0]
                        return self._format_insee_result(etablissement)
                
                logger.warning(f"⚠️ API Insee: {response.status} pour {company_name}")
                return {'error': f'API Insee error: {response.status}'}
                
        except Exception as e:
            logger.error(f"❌ Erreur recherche manuelle: {e}")
            return {'error': str(e)}
    
    def _find_best_match(self, results: List[Dict], company_name: str) -> Optional[Dict]:
        """Trouve le meilleur match parmi les résultats"""
        company_name_lower = company_name.lower()
        
        for result in results:
            # Vérifier différents champs de nom
            names_to_check = [
                result.get('nom_complet', '') or '',
                result.get('nom_raison_sociale', '') or '',
                result.get('nom', '') or '',
                result.get('sigle', '') or ''
            ]
            
            for name in names_to_check:
                if name:  # S'assurer que name n'est pas None ou vide
                    name_lower = name.lower()
                    if company_name_lower in name_lower or name_lower in company_name_lower:
                        return result
        
        # Si pas de match exact, retourner le premier
        return results[0] if results else None
    
    def _format_api_result(self, result: Dict) -> Dict[str, Any]:
        """Formate le résultat de l'API gouvernementale"""
        return {
            'siret': result.get('siret'),
            'siren': result.get('siren'),
            'tva': self._calculate_tva(result.get('siren')),
            'raison_sociale': result.get('nom_raison_sociale') or result.get('nom_complet'),
            'adresse_legale': result.get('adresse'),
            'code_postal_legal': result.get('code_postal'),
            'ville_legale': result.get('libelle_commune')
        }
    
    def _format_pappers_result(self, enterprise: Dict) -> Dict[str, Any]:
        """Formate le résultat de l'API Pappers"""
        return {
            'siret': enterprise.get('siret'),
            'siren': enterprise.get('siren'),
            'tva': enterprise.get('numero_tva_intracommunautaire'),
            'raison_sociale': enterprise.get('nom_entreprise'),
            'adresse_legale': enterprise.get('adresse_ligne_1'),
            'code_postal_legal': enterprise.get('code_postal'),
            'ville_legale': enterprise.get('ville')
        }
    
    def _format_insee_result(self, etablissement: Dict) -> Dict[str, Any]:
        """Formate le résultat de l'API Insee"""
        unite_legale = etablissement.get('uniteLegale', {})
        adresse = etablissement.get('adresseEtablissement', {})
        
        return {
            'siret': etablissement.get('siret'),
            'siren': etablissement.get('siren'),
            'tva': self._calculate_tva(etablissement.get('siren')),
            'raison_sociale': unite_legale.get('denominationUniteLegale'),
            'adresse_legale': f"{adresse.get('numeroVoieEtablissement', '')} {adresse.get('typeVoieEtablissement', '')} {adresse.get('libelleVoieEtablissement', '')}".strip(),
            'code_postal_legal': adresse.get('codePostalEtablissement'),
            'ville_legale': adresse.get('libelleCommuneEtablissement')
        }
    
    def _calculate_tva(self, siren: str) -> Optional[str]:
        """Calcule le numéro TVA intracommunautaire à partir du SIREN"""
        if not siren or len(siren) != 9:
            return None
        
        try:
            # Algorithme officiel de calcul de la TVA
            # TVA = (12 + 3 * (SIREN % 97)) % 97
            siren_int = int(siren)
            key = (12 + 3 * (siren_int % 97)) % 97
            return f"FR{key:02d}{siren}"
        except:
            return None
    
    async def test_apis(self) -> Dict[str, bool]:
        """Test la disponibilité des APIs"""
        results = {}
        
        try:
            session = await self.get_session()
            
            # Test API gouvernementale
            try:
                async with session.get(f"{self.apis['recherche_entreprise']}?q=test&limite=1") as response:
                    results['gouv_api'] = response.status == 200
            except:
                results['gouv_api'] = False
            
            # Test API Pappers
            try:
                async with session.get(f"{self.apis['pappers']}?nom_entreprise=test") as response:
                    results['pappers_api'] = response.status in [200, 429]  # 429 = rate limit
            except:
                results['pappers_api'] = False
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Erreur test APIs: {e}")
            return {'error': str(e)}
        finally:
            await self.close_session() 