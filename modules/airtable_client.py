"""
Client Airtable pour récupérer les noms d'entreprises
"""

import aiohttp
import asyncio
import logging
from typing import List, Dict, Any
from config import Config

logger = logging.getLogger(__name__)

class AirtableClient:
    def __init__(self):
        self.config = Config()
        self.base_url = f"https://api.airtable.com/v0/{self.config.AIRTABLE_BASE_ID}"
        self.headers = {
            'Authorization': f'Bearer {self.config.AIRTABLE_API_KEY}',
            'Content-Type': 'application/json'
        }
    
    async def get_companies(self) -> List[Dict[str, Any]]:
        """Récupère la liste des entreprises depuis Airtable"""
        try:
            companies = []
            url = f"{self.base_url}/{self.config.AIRTABLE_TABLE_NAME}"
            
            async with aiohttp.ClientSession() as session:
                offset = None
                while True:
                    params = {}
                    if self.config.AIRTABLE_VIEW_NAME:
                        params['view'] = self.config.AIRTABLE_VIEW_NAME
                    if offset:
                        params['offset'] = offset
                    
                    async with session.get(url, headers=self.headers, params=params) as response:
                        if response.status == 200:
                            data = await response.json()
                            records = data.get('records', [])
                            
                            for record in records:
                                fields = record.get('fields', {})
                                company_data = {
                                    'id': record.get('id'),
                                    'name': fields.get('Nom', ''),
                                    'airtable_record_id': record.get('id')
                                }
                                companies.append(company_data)
                            
                            # Vérifier s'il y a plus de données à récupérer
                            offset = data.get('offset')
                            if not offset:
                                break
                        else:
                            logger.error(f"Erreur API Airtable: {response.status}")
                            break
            
            logger.info(f"✅ {len(companies)} entreprises récupérées depuis Airtable")
            return companies
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de la récupération des entreprises: {str(e)}")
            return []
    
    async def update_company_status(self, record_id: str, status: str, data: Dict[str, Any] = None):
        """Met à jour le statut d'une entreprise dans Airtable"""
        try:
            url = f"{self.base_url}/{self.config.AIRTABLE_TABLE_NAME}/{record_id}"
            
            fields = {'Status': status}
            if data:
                fields.update(data)
            
            payload = {'fields': fields}
            
            async with aiohttp.ClientSession() as session:
                async with session.patch(url, headers=self.headers, json=payload) as response:
                    if response.status == 200:
                        logger.info(f"✅ Statut mis à jour pour l'entreprise {record_id}")
                    else:
                        logger.error(f"❌ Erreur mise à jour Airtable: {response.status}")
                        
        except Exception as e:
            logger.error(f"❌ Erreur lors de la mise à jour du statut: {str(e)}")

    async def update_company_data(self, record_id: str, scraped_data: Dict[str, Any]):
        """Met à jour les données de scrapping d'une entreprise dans Airtable"""
        try:
            url = f"{self.base_url}/{self.config.AIRTABLE_TABLE_NAME}/{record_id}"
            
            # Préparer les champs pour Airtable (utilisation des champs existants)
            fields = {}
            
            # Données du site web
            if 'website_data' in scraped_data:
                website = scraped_data['website_data']
                if website.get('website'):
                    fields['Site'] = website['website']
                if website.get('adresse'):
                    fields['Adresse de facturation'] = website['adresse']
                if website.get('telephone'):
                    fields['Tel Principal'] = website['telephone']
                if website.get('mobile'):
                    fields['Portable'] = website['mobile']
            
            # Données légales
            if 'legal_data' in scraped_data:
                legal = scraped_data['legal_data']
                if legal.get('siren'):
                    fields['SIREN'] = legal['siren']
                if legal.get('siret'):
                    fields['SIRET'] = legal['siret']
                if legal.get('numero_tva') or legal.get('tva'):
                    fields['TVA Intracom'] = legal.get('numero_tva') or legal.get('tva')
                if legal.get('adresse') or legal.get('adresse_legale'):
                    fields['Adresse'] = legal.get('adresse') or legal.get('adresse_legale')
                if legal.get('code_postal') or legal.get('code_postal_legal'):
                    fields['Code Postal'] = legal.get('code_postal') or legal.get('code_postal_legal')
                if legal.get('ville') or legal.get('ville_legale'):
                    fields['Ville'] = legal.get('ville') or legal.get('ville_legale')
            
            # Données de solvabilité (utiliser seulement les champs existants)
            if 'solvability_data' in scraped_data:
                solvability = scraped_data['solvability_data']
                if solvability.get('is_solvent') is not None:
                    fields['État de la société'] = "Fermé/Insolvable" if solvability.get('is_solvent') is False else "OK"
                # Note: Le champ 'Statut Entreprise' n'existe pas dans Airtable
                # if solvability.get('status'):
                #     fields['Statut Entreprise'] = solvability['status']
                if solvability.get('risk_level'):
                    fields['Niveau de Risque'] = solvability['risk_level']
                if solvability.get('details'):
                    # Joindre les détails en une seule chaîne
                    details_text = "; ".join([str(detail) for detail in solvability['details']])
                    fields['Détails Solvabilité'] = details_text[:1000]  # Limiter la taille

            # Marquer comme scrappé si des données ont été récupérées
            if 'website_data' in scraped_data or 'legal_data' in scraped_data or 'solvability_data' in scraped_data:
                fields['Get Scrapped ?'] = True
            
            payload = {'fields': fields}
            
            async with aiohttp.ClientSession() as session:
                async with session.patch(url, headers=self.headers, json=payload) as response:
                    if response.status == 200:
                        result = await response.json()
                        logger.info(f"✅ Données de scrapping mises à jour dans Airtable pour {scraped_data.get('company_name', record_id)}")
                        return True
                    else:
                        error_text = await response.text()
                        logger.error(f"❌ Erreur mise à jour Airtable {response.status}: {error_text}")
                        return False
                        
        except Exception as e:
            logger.error(f"❌ Erreur lors de la mise à jour des données: {str(e)}")
            return False 

    async def get_company_by_id(self, record_id: str) -> Dict[str, Any]:
        """Récupère une entreprise spécifique par son record ID"""
        try:
            url = f"{self.base_url}/{self.config.AIRTABLE_TABLE_NAME}/{record_id}"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        logger.info(f"📊 Réponse Airtable brute: {data}")
                        
                        # Airtable retourne directement l'enregistrement, pas dans 'records'
                        fields = data.get('fields', {})
                        company_data = {
                            'id': data.get('id'),
                            'name': fields.get('Nom', ''),  # Chercher le champ "Nom"
                            'airtable_record_id': data.get('id'),
                            'fields': fields
                        }
                        logger.info(f"✅ Entreprise récupérée par ID: {record_id}")
                        logger.info(f"📋 Champs trouvés: {list(fields.keys())}")
                        logger.info(f"📋 Nom trouvé: '{company_data['name']}'")
                        return company_data
                    else:
                        error_text = await response.text()
                        logger.error(f"❌ Erreur API Airtable: {response.status} - {error_text}")
                        return {}
        except Exception as e:
            logger.error(f"❌ Erreur lors de la récupération de l'entreprise par ID: {str(e)}")
            return {} 