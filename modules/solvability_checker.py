"""
Module de vérification de la solvabilité des entreprises françaises
Utilise plusieurs sources pour déterminer l'état d'une entreprise
"""

import asyncio
import aiohttp
import logging
from typing import Dict, Any, Optional
from config import Config
import urllib.parse
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class SolvabilityChecker:
    def __init__(self):
        self.config = Config()
        self.session = None
        
        # URLs des APIs pour vérifier la solvabilité
        self.apis = {
            'bodacc': 'https://bodacc-datainfogreffe.opendatasoft.com/api/records/1.0/search/',
            'entreprise_api': 'https://recherche-entreprises.api.gouv.fr/search',
            'infogreffe': 'https://opendata.datainfogreffe.fr/api/records/1.0/search/'
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
        if self.session and not self.session.closed:
            await self.session.close()
            self.session = None
    
    async def check_company_solvability(self, company_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Vérifie la solvabilité d'une entreprise
        Retourne un dictionnaire avec l'état et les détails
        """
        try:
            siren = company_data.get('siren')
            siret = company_data.get('siret')
            company_name = company_data.get('raison_sociale') or company_data.get('name', '')
            
            logger.info(f"🔍 Vérification solvabilité pour: {company_name}")
            
            # Résultat par défaut
            result = {
                'is_solvent': None,  # True/False/None (inconnu)
                'status': 'active',  # active, closed, liquidation, redressement, unknown
                'risk_level': 'low',  # low, medium, high, unknown
                'details': [],
                'sources_checked': []
            }
            
            # 1. Vérifier via BODACC (procédures collectives)
            bodacc_result = await self._check_bodacc(siren, siret, company_name)
            if bodacc_result:
                result['sources_checked'].append('BODACC')
                if bodacc_result.get('has_procedures'):
                    result['is_solvent'] = False
                    result['status'] = bodacc_result.get('procedure_type', 'redressement')
                    result['risk_level'] = 'high'
                    result['details'].extend(bodacc_result.get('procedures', []))
            
            # 2. Vérifier l'état de l'entreprise (active/fermée)
            status_result = await self._check_company_status(siren, siret, company_name)
            if status_result:
                result['sources_checked'].append('API_GOUV')
                if status_result.get('is_active') is False:
                    result['is_solvent'] = False
                    result['status'] = 'closed'
                    result['risk_level'] = 'high'
                    result['details'].append(f"Entreprise fermée depuis {status_result.get('date_cessation', 'date inconnue')}")
                elif status_result.get('is_active') is True and result['is_solvent'] is None:
                    result['is_solvent'] = True
                    result['status'] = 'active'
            
            # 3. Vérifications additionnelles via InfoGreffe
            infogreffe_result = await self._check_infogreffe(siren, company_name)
            if infogreffe_result:
                result['sources_checked'].append('INFOGREFFE')
                if infogreffe_result.get('has_alerts'):
                    if result['risk_level'] == 'low':
                        result['risk_level'] = 'medium'
                    result['details'].extend(infogreffe_result.get('alerts', []))
            
            # Déterminer le statut final
            if result['is_solvent'] is None:
                result['is_solvent'] = True  # Par défaut, considérer comme solvable si pas d'info négative
                result['status'] = 'active'
                result['details'].append("Aucune procédure collective trouvée - Entreprise présumée active")
            
            logger.info(f"✅ Solvabilité {company_name}: {result['status']} (risque: {result['risk_level']})")
            return result
            
        except Exception as e:
            logger.error(f"❌ Erreur vérification solvabilité: {str(e)}")
            return {
                'is_solvent': None,
                'status': 'unknown',
                'risk_level': 'unknown',
                'details': [f"Erreur lors de la vérification: {str(e)}"],
                'sources_checked': [],
                'error': str(e)
            }
    
    async def _check_bodacc(self, siren: str, siret: str, company_name: str) -> Optional[Dict[str, Any]]:
        """Vérifie les procédures collectives dans BODACC"""
        try:
            session = await self.get_session()
            
            # Rechercher par SIREN si disponible
            search_terms = []
            if siren:
                search_terms.append(f'numerosiren:{siren}')
            if siret:
                search_terms.append(f'numerosiret:{siret}')
            if company_name:
                # Échapper les caractères spéciaux
                clean_name = company_name.replace('"', '').replace("'", "")
                search_terms.append(f'raisonsociale:"{clean_name}"')
            
            for search_term in search_terms:
                params = {
                    'dataset': 'annonces-commerciales',
                    'q': search_term,
                    'rows': 10,
                    'sort': 'dateparution',
                    # Chercher les procédures des 5 dernières années
                    'refine.typeavis': ['Procédure collective', 'Liquidation judiciaire', 'Redressement judiciaire']
                }
                
                try:
                    async with session.get(self.apis['bodacc'], params=params) as response:
                        if response.status == 200:
                            data = await response.json()
                            records = data.get('records', [])
                            
                            if records:
                                procedures = []
                                latest_procedure = None
                                
                                for record in records:
                                    fields = record.get('fields', {})
                                    procedure_type = fields.get('typeavis', '')
                                    date_parution = fields.get('dateparution', '')
                                    
                                    procedure_info = {
                                        'type': procedure_type,
                                        'date': date_parution,
                                        'details': fields.get('texte', '')
                                    }
                                    procedures.append(procedure_info)
                                    
                                    # Garder la procédure la plus récente
                                    if not latest_procedure or date_parution > latest_procedure.get('date', ''):
                                        latest_procedure = procedure_info
                                
                                return {
                                    'has_procedures': True,
                                    'procedure_type': self._map_procedure_type(latest_procedure.get('type', '')),
                                    'procedures': procedures,
                                    'latest_procedure': latest_procedure
                                }
                        
                        await asyncio.sleep(0.5)  # Respecter les limites de l'API
                        
                except Exception as e:
                    logger.warning(f"⚠️ Erreur BODACC pour {search_term}: {e}")
                    continue
            
            return {'has_procedures': False}
            
        except Exception as e:
            logger.error(f"❌ Erreur vérification BODACC: {e}")
            return None
    
    async def _check_company_status(self, siren: str, siret: str, company_name: str) -> Optional[Dict[str, Any]]:
        """Vérifie le statut de l'entreprise (active/fermée)"""
        try:
            session = await self.get_session()
            
            # Utiliser l'API gouvernementale
            search_terms = []
            if siren:
                search_terms.append(siren)
            if siret:
                search_terms.append(siret)
            if company_name:
                search_terms.append(company_name)
            
            for term in search_terms:
                params = {
                    'q': term,
                    'limite': 5
                }
                
                try:
                    async with session.get(self.apis['entreprise_api'], params=params) as response:
                        if response.status == 200:
                            data = await response.json()
                            results = data.get('results', [])
                            
                            if results:
                                # Prendre le premier résultat qui correspond
                                for result in results:
                                    result_siren = result.get('siren')
                                    if siren and result_siren == siren:
                                        # Entreprise trouvée, vérifier son état
                                        etat = result.get('etat_administratif_unite_legale', 'A')
                                        date_cessation = result.get('date_cessation_unite_legale')
                                        
                                        return {
                                            'is_active': etat == 'A',  # A = Active, C = Cessée
                                            'date_cessation': date_cessation,
                                            'etat_administratif': etat
                                        }
                        
                        await asyncio.sleep(0.5)
                        
                except Exception as e:
                    logger.warning(f"⚠️ Erreur statut entreprise pour {term}: {e}")
                    continue
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Erreur vérification statut: {e}")
            return None
    
    async def _check_infogreffe(self, siren: str, company_name: str) -> Optional[Dict[str, Any]]:
        """Vérifie les informations complémentaires sur InfoGreffe"""
        try:
            session = await self.get_session()
            
            # Cette API peut avoir des limitations, donc gestion d'erreur plus souple
            search_terms = [siren] if siren else [company_name]
            
            for term in search_terms:
                if not term:
                    continue
                    
                params = {
                    'dataset': 'entreprises-immatriculees-rcs-france',
                    'q': term,
                    'rows': 5
                }
                
                try:
                    async with session.get(self.apis['infogreffe'], params=params) as response:
                        if response.status == 200:
                            data = await response.json()
                            records = data.get('records', [])
                            
                            if records:
                                # Analyser les enregistrements pour des alertes
                                alerts = []
                                for record in records:
                                    fields = record.get('fields', {})
                                    
                                    # Vérifier la date de radiation
                                    date_radiation = fields.get('dateradiation')
                                    if date_radiation:
                                        alerts.append(f"Entreprise radiée le {date_radiation}")
                                    
                                    # Vérifier d'autres indicateurs
                                    forme_juridique = fields.get('formejuridique', '')
                                    if 'liquidation' in forme_juridique.lower():
                                        alerts.append(f"Forme juridique indique une liquidation: {forme_juridique}")
                                
                                return {
                                    'has_alerts': len(alerts) > 0,
                                    'alerts': alerts
                                }
                        
                        await asyncio.sleep(0.5)
                        
                except Exception as e:
                    logger.warning(f"⚠️ InfoGreffe non accessible pour {term}: {e}")
                    # Ne pas considérer comme une erreur bloquante
                    break
            
            return {'has_alerts': False, 'alerts': []}
            
        except Exception as e:
            logger.warning(f"⚠️ Erreur InfoGreffe (non bloquante): {e}")
            return None
    
    def _map_procedure_type(self, procedure_type: str) -> str:
        """Mappe les types de procédures BODACC vers des statuts standard"""
        procedure_lower = procedure_type.lower()
        
        if 'liquidation' in procedure_lower:
            return 'liquidation'
        elif 'redressement' in procedure_lower:
            return 'redressement'
        elif 'sauvegarde' in procedure_lower:
            return 'sauvegarde'
        elif 'cessation' in procedure_lower:
            return 'closed'
        else:
            return 'procedure_collective'
    
    def get_solvability_summary(self, solvability_data: Dict[str, Any]) -> str:
        """Génère un résumé textuel de la solvabilité"""
        if not solvability_data:
            return "❓ État inconnu"
        
        is_solvent = solvability_data.get('is_solvent')
        status = solvability_data.get('status', 'unknown')
        risk_level = solvability_data.get('risk_level', 'unknown')
        
        if is_solvent is True and status == 'active':
            if risk_level == 'low':
                return "✅ Entreprise solvable et active"
            elif risk_level == 'medium':
                return "⚠️ Entreprise active mais avec alertes"
            else:
                return "🔶 Entreprise active mais risque élevé"
        elif is_solvent is False:
            if status == 'liquidation':
                return "❌ Entreprise en liquidation"
            elif status == 'redressement':
                return "🔴 Entreprise en redressement judiciaire"
            elif status == 'closed':
                return "⚫ Entreprise fermée"
            else:
                return "❌ Entreprise non solvable"
        else:
            return "❓ Solvabilité indéterminée" 