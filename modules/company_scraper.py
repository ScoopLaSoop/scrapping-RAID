"""
Scrapper de sites web d'entreprises
Utilise OpenAI pour trouver le site web puis scrappe les informations
"""

import aiohttp
import asyncio
import logging
import json
from typing import Dict, Any, Optional
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin, urlparse
from config import Config

logger = logging.getLogger(__name__)

class CompanyScraper:
    def __init__(self):
        self.config = Config()
        self.session = None
    
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
    
    async def find_company_website(self, company_name: str) -> Optional[str]:
        """Utilise OpenAI pour trouver le site web de l'entreprise"""
        try:
            headers = {
                'Authorization': f'Bearer {self.config.OPENAI_API_KEY}',
                'Content-Type': 'application/json'
            }
            
            # Ajouter l'Organization ID si disponible
            if self.config.OPENAI_ORG_ID:
                headers['OpenAI-Organization'] = self.config.OPENAI_ORG_ID
            
            prompt = f"""
            Je cherche le site web officiel de l'entreprise : "{company_name}"
            
            Peux-tu me donner uniquement l'URL du site web officiel de cette entreprise ?
            Réponds uniquement avec l'URL, sans explication supplémentaire.
            Si tu ne connais pas l'entreprise, réponds "UNKNOWN".
            
            Format de réponse attendu: https://example.com
            """
            
            payload = {
                'model': self.config.OPENAI_MODEL,
                'messages': [
                    {'role': 'user', 'content': prompt}
                ],
                'max_tokens': 100,
                'temperature': 0.1
            }
            
            session = await self.get_session()
            async with session.post('https://api.openai.com/v1/chat/completions', 
                                  headers=headers, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    website_url = data['choices'][0]['message']['content'].strip()
                    
                    if website_url and website_url != "UNKNOWN" and website_url.startswith('http'):
                        logger.info(f"🔍 Site trouvé pour {company_name}: {website_url}")
                        return website_url
                    else:
                        logger.warning(f"⚠️ Site non trouvé pour {company_name}")
                        return None
                else:
                    logger.error(f"❌ Erreur OpenAI API: {response.status}")
                    return None
                    
        except Exception as e:
            logger.error(f"❌ Erreur lors de la recherche du site pour {company_name}: {str(e)}")
            return None
    
    async def scrape_company_website(self, company_name: str) -> Dict[str, Any]:
        """Scrappe les informations d'une entreprise depuis son site web"""
        try:
            # Trouver le site web
            website_url = await self.find_company_website(company_name)
            if not website_url:
                return {'error': 'Site web non trouvé'}
            
            # Scrapper le site
            company_data = await self.scrape_website_data(website_url)
            company_data['website'] = website_url
            
            return company_data
            
        except Exception as e:
            logger.error(f"❌ Erreur lors du scrapping de {company_name}: {str(e)}")
            return {'error': str(e)}
        finally:
            # Fermer la session
            await self.close_session()
    
    async def scrape_website_data(self, url: str) -> Dict[str, Any]:
        """Scrappe les données d'un site web"""
        try:
            session = await self.get_session()
            async with session.get(url) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Extraire les informations
                    data = {
                        'adresse': self.extract_address(soup),
                        'code_postal': self.extract_postal_code(soup),
                        'ville': self.extract_city(soup),
                        'email': self.extract_email(soup),
                        'telephone': self.extract_phone(soup),
                        'mobile': self.extract_mobile(soup)
                    }
                    
                    logger.info(f"✅ Données extraites du site: {url}")
                    return data
                else:
                    logger.error(f"❌ Erreur HTTP {response.status} pour {url}")
                    return {'error': f'HTTP {response.status}'}
                    
        except Exception as e:
            logger.error(f"❌ Erreur lors du scrapping de {url}: {str(e)}")
            return {'error': str(e)}
    
    def extract_address(self, soup: BeautifulSoup) -> Optional[str]:
        """Extrait l'adresse du site"""
        patterns = [
            r'\d+[\s,]+(?:rue|avenue|boulevard|place|allée|chemin|impasse)[^0-9]*',
            r'(?:rue|avenue|boulevard|place|allée|chemin|impasse)[^0-9]*\d+',
        ]
        
        text = soup.get_text()
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                return matches[0].strip()
        return None
    
    def extract_postal_code(self, soup: BeautifulSoup) -> Optional[str]:
        """Extrait le code postal"""
        text = soup.get_text()
        # Chercher un code postal français (5 chiffres)
        matches = re.findall(r'\b\d{5}\b', text)
        if matches:
            return matches[0]
        return None
    
    def extract_city(self, soup: BeautifulSoup) -> Optional[str]:
        """Extrait la ville"""
        text = soup.get_text()
        # Chercher après un code postal
        matches = re.findall(r'\b\d{5}\s+([A-Za-zÀ-ÿ\s-]+)', text)
        if matches:
            return matches[0].strip()
        return None
    
    def extract_email(self, soup: BeautifulSoup) -> Optional[str]:
        """Extrait l'email"""
        text = soup.get_text()
        matches = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text)
        if matches:
            return matches[0]
        return None
    
    def extract_phone(self, soup: BeautifulSoup) -> Optional[str]:
        """Extrait le numéro de téléphone fixe"""
        text = soup.get_text()
        # Patterns pour téléphones français
        patterns = [
            r'\b0[1-5](?:[-.\s]?\d{2}){4}\b',
            r'\b\+33[1-5](?:[-.\s]?\d{2}){4}\b'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text)
            if matches:
                return matches[0]
        return None
    
    def extract_mobile(self, soup: BeautifulSoup) -> Optional[str]:
        """Extrait le numéro de téléphone mobile"""
        text = soup.get_text()
        # Patterns pour mobiles français
        patterns = [
            r'\b0[67](?:[-.\s]?\d{2}){4}\b',
            r'\b\+33[67](?:[-.\s]?\d{2}){4}\b'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text)
            if matches:
                return matches[0]
        return None 