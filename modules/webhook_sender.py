"""
Module pour envoyer les données à Make via webhook
"""

import aiohttp
import asyncio
import json
import logging
from typing import Dict, Any
from config import Config

logger = logging.getLogger(__name__)

class WebhookSender:
    def __init__(self):
        self.config = Config()
    
    async def send_data(self, data: Dict[str, Any]) -> bool:
        """Envoie les données à Make via webhook"""
        try:
            # Préparer les données JSON
            json_data = self.prepare_json_data(data)
            
            # Headers pour la requête
            headers = {
                'Content-Type': 'application/json',
                'User-Agent': self.config.USER_AGENT
            }
            
            # Envoyer les données
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.config.MAKE_WEBHOOK_URL,
                    json=json_data,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=self.config.TIMEOUT)
                ) as response:
                    
                    if response.status == 200:
                        logger.info(f"✅ Données envoyées avec succès à Make")
                        return True
                    else:
                        logger.error(f"❌ Erreur lors de l'envoi à Make: {response.status}")
                        error_text = await response.text()
                        logger.error(f"Réponse: {error_text}")
                        return False
                        
        except Exception as e:
            logger.error(f"❌ Erreur lors de l'envoi des données: {str(e)}")
            return False
    
    def prepare_json_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Prépare les données au format JSON pour Make"""
        
        # Structure des données à envoyer
        json_data = {
            'timestamp': data.get('processed_at'),
            'entreprise': {
                'nom': data.get('name'),
                'airtable_id': data.get('airtable_record_id')
            },
            'informations_web': {
                'site_web': data.get('website'),
                'adresse': data.get('adresse'),
                'code_postal': data.get('code_postal'),
                'ville': data.get('ville'),
                'email': data.get('email'),
                'telephone': data.get('telephone'),
                'mobile': data.get('mobile')
            },
            'informations_legales': {
                'siret': data.get('siret'),
                'siren': data.get('siren'),
                'tva': data.get('tva'),
                'raison_sociale': data.get('raison_sociale'),
                'adresse_legale': data.get('adresse_legale'),
                'code_postal_legal': data.get('code_postal_legal'),
                'ville_legale': data.get('ville_legale')
            },
            'erreurs': {
                'erreur_web': data.get('error') if 'error' in data else None,
                'erreur_legale': data.get('error_legal') if 'error_legal' in data else None
            }
        }
        
        # Nettoyer les valeurs None
        json_data = self.clean_none_values(json_data)
        
        return json_data
    
    def clean_none_values(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Supprime les valeurs None du dictionnaire"""
        if isinstance(data, dict):
            return {k: self.clean_none_values(v) for k, v in data.items() if v is not None}
        elif isinstance(data, list):
            return [self.clean_none_values(item) for item in data if item is not None]
        else:
            return data
    
    async def send_test_data(self) -> bool:
        """Envoie des données de test pour vérifier le webhook"""
        test_data = {
            'processed_at': '2023-12-01T10:00:00',
            'name': 'Entreprise Test',
            'airtable_record_id': 'test123',
            'website': 'https://test.com',
            'adresse': '123 Rue Test',
            'code_postal': '75001',
            'ville': 'Paris',
            'email': 'test@test.com',
            'telephone': '0123456789',
            'mobile': '0612345678',
            'siret': '12345678901234',
            'siren': '123456789',
            'tva': 'FR12345678901',
            'raison_sociale': 'ENTREPRISE TEST SARL'
        }
        
        return await self.send_data(test_data) 