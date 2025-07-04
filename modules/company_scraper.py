"""
Scrapper de sites web d'entreprises
Utilise une recherche web réelle (Google/DuckDuckGo) puis OpenAI pour trouver les sites
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
from .web_search import WebSearcher

logger = logging.getLogger(__name__)

class CompanyScraper:
    def __init__(self):
        self.config = Config()
        self.session = None
        self.web_searcher = WebSearcher()
    
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
        
        # Fermer aussi la session du web searcher
        await self.web_searcher.close_session()
    
    async def find_company_website(self, company_name: str) -> Optional[str]:
        """
        Trouve le site web d'une entreprise via recherche web réelle
        puis OpenAI en fallback
        """
        # Méthode 1: Recherche web réelle (Google/DuckDuckGo)
        website_url = await self.web_searcher.search_company_website(company_name)
        if website_url:
            return website_url
        
        # Méthode 2: Fallback OpenAI (comme avant mais amélioré)
        logger.info(f"🔄 Fallback OpenAI pour {company_name}")
        return await self._find_website_via_openai(company_name)
    
    async def _find_website_via_openai(self, company_name: str) -> Optional[str]:
        """Utilise OpenAI pour trouver le site web de l'entreprise (méthode fallback)"""
        try:
            headers = {
                'Authorization': f'Bearer {self.config.OPENAI_API_KEY}',
                'Content-Type': 'application/json'
            }
            
            # Ajouter l'Organization ID si disponible
            if self.config.OPENAI_ORG_ID:
                headers['OpenAI-Organization'] = self.config.OPENAI_ORG_ID
            
            prompt = f"""
            Je cherche le site web officiel de l'entreprise française : "{company_name}"
            
            Cette entreprise est située en France. Peux-tu me donner l'URL exacte de son site web officiel ?
            
            Essaie plusieurs variantes possibles :
            - Avec et sans espaces/tirets
            - Avec .fr ou .com
            - Avec www ou sans www
            
            Instructions :
            1. Réponds uniquement avec l'URL complète (avec https://)
            2. Si tu connais l'entreprise, donne son site officiel
            3. Si tu ne la connais pas, essaie de deviner l'URL la plus probable
            4. Si vraiment impossible, réponds "UNKNOWN"
            
            Format de réponse attendu: https://example.com
            """
            
            payload = {
                'model': self.config.OPENAI_MODEL,
                'messages': [
                    {'role': 'user', 'content': prompt}
                ],
                'max_tokens': 150,
                'temperature': 0.3  # Un peu plus créatif pour deviner
            }
            
            session = await self.get_session()
            async with session.post('https://api.openai.com/v1/chat/completions', 
                                  headers=headers, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    website_url = data['choices'][0]['message']['content'].strip()
                    
                    # Nettoyer la réponse au cas où il y aurait du texte en plus
                    lines = website_url.split('\n')
                    for line in lines:
                        line = line.strip()
                        if line.startswith('http'):
                            website_url = line
                            break
                    
                    if website_url and website_url != "UNKNOWN" and website_url.startswith('http'):
                        logger.info(f"🔍 Site trouvé pour {company_name}: {website_url}")
                        
                        # Vérifier que le site existe vraiment
                        try:
                            async with session.get(website_url, timeout=aiohttp.ClientTimeout(total=10)) as test_response:
                                if test_response.status == 200:
                                    return website_url
                                else:
                                    logger.warning(f"⚠️ Site non accessible ({test_response.status}): {website_url}")
                                    return None
                        except:
                            logger.warning(f"⚠️ Site non accessible: {website_url}")
                            return None
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
            
            # Extraire la raison sociale avec OpenAI
            official_name = await self.extract_official_company_name(website_url, company_name)
            if official_name:
                company_data['raison_sociale'] = official_name
                logger.info(f"🏢 Raison sociale trouvée: {official_name}")
            
            return company_data
            
        except Exception as e:
            logger.error(f"❌ Erreur lors du scrapping de {company_name}: {str(e)}")
            return {'error': str(e)}
    
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
        """Extrait l'adresse du site avec méthodes améliorées"""
        text = soup.get_text()
        
        # Patterns plus précis pour les adresses françaises
        patterns = [
            # Numéro + type de voie + nom
            r'\b\d{1,4}[\s,]*(?:bis|ter|quater)?\s*(?:rue|avenue|boulevard|place|allée|chemin|impasse|cours|quai|square|passage|villa|cité)\s+[A-Za-zÀ-ÿ\s\-\'\.]{2,50}',
            # Type de voie + numéro + nom
            r'\b(?:rue|avenue|boulevard|place|allée|chemin|impasse|cours|quai|square|passage|villa|cité)\s+[A-Za-zÀ-ÿ\s\-\'\.]*\s*\d{1,4}[\s,]*(?:bis|ter|quater)?',
            # Recherche dans les balises spécifiques
            r'(?i)(?:adresse|address)[\s:]*([^\n\r]{10,100})'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                # Nettoyer et valider l'adresse
                address = matches[0].strip()
                if len(address) > 8 and len(address) < 100:  # Longueur raisonnable
                    return address
        
        # Chercher aussi dans les balises HTML spécifiques
        address_selectors = [
            '[itemprop="streetAddress"]',
            '[class*="address"]',
            '[class*="adresse"]',
            '[id*="address"]',
            '[id*="adresse"]'
        ]
        
        for selector in address_selectors:
            elements = soup.select(selector)
            for element in elements:
                text = element.get_text().strip()
                if len(text) > 8 and len(text) < 100:
                    return text
        
        return None
    
    def extract_postal_code(self, soup: BeautifulSoup) -> Optional[str]:
        """Extrait le code postal avec méthodes améliorées"""
        text = soup.get_text()
        
        # Patterns pour codes postaux français
        patterns = [
            r'\b\d{5}\b',  # 5 chiffres
            r'(?i)(?:code postal|cp)[\s:]*(\d{5})',  # Avec label
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                # Vérifier que c'est un vrai code postal français
                code = match if isinstance(match, str) else match
                if code.isdigit() and len(code) == 5:
                    # Codes postaux français commencent par 01-95 ou 2A/2B pour Corse
                    first_two = int(code[:2])
                    if 1 <= first_two <= 95:
                        return code
        
        # Chercher dans les balises spécifiques
        postal_selectors = [
            '[itemprop="postalCode"]',
            '[class*="postal"]',
            '[class*="cp"]',
            '[id*="postal"]'
        ]
        
        for selector in postal_selectors:
            elements = soup.select(selector)
            for element in elements:
                text = element.get_text().strip()
                if re.match(r'^\d{5}$', text):
                    return text
        
        return None
    
    def extract_city(self, soup: BeautifulSoup) -> Optional[str]:
        """Extrait la ville avec méthodes améliorées"""
        text = soup.get_text()
        
        # Patterns pour villes françaises
        patterns = [
            r'\b\d{5}\s+([A-Za-zÀ-ÿ\s\-\']{2,30})',  # Après code postal
            r'(?i)(?:ville|city)[\s:]*([A-Za-zÀ-ÿ\s\-\']{2,30})',  # Avec label
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                city = match.strip()
                # Vérifier que c'est une ville valide (pas de chiffres, longueur raisonnable)
                if len(city) > 2 and len(city) < 30 and not re.search(r'\d', city):
                    return city
        
        # Chercher dans les balises spécifiques
        city_selectors = [
            '[itemprop="addressLocality"]',
            '[class*="city"]',
            '[class*="ville"]',
            '[id*="city"]',
            '[id*="ville"]'
        ]
        
        for selector in city_selectors:
            elements = soup.select(selector)
            for element in elements:
                city = element.get_text().strip()
                if len(city) > 2 and len(city) < 30 and not re.search(r'\d', city):
                    return city
        
        return None
    
    def extract_email(self, soup: BeautifulSoup) -> Optional[str]:
        """Extrait l'email avec méthodes améliorées"""
        text = soup.get_text()
        
        # Pattern pour emails
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        matches = re.findall(email_pattern, text)
        
        # Filtrer les emails non pertinents
        excluded_domains = [
            'example.com', 'test.com', 'noreply', 'no-reply',
            'facebook.com', 'twitter.com', 'linkedin.com', 'instagram.com',
            'youtube.com', 'google.com', 'microsoft.com'
        ]
        
        for email in matches:
            email_lower = email.lower()
            is_excluded = any(domain in email_lower for domain in excluded_domains)
            
            if not is_excluded and '.' in email and len(email) < 50:
                return email
        
        # Chercher dans les balises spécifiques
        email_selectors = [
            'a[href^="mailto:"]',
            '[itemprop="email"]',
            '[class*="email"]',
            '[id*="email"]'
        ]
        
        for selector in email_selectors:
            elements = soup.select(selector)
            for element in elements:
                if selector == 'a[href^="mailto:"]':
                    href = element.get('href', '')
                    if href.startswith('mailto:'):
                        email = href.replace('mailto:', '').strip()
                        if re.match(email_pattern, email):
                            return email
                else:
                    email = element.get_text().strip()
                    if re.match(email_pattern, email):
                        return email
        
        return None
    
    def extract_phone(self, soup: BeautifulSoup) -> Optional[str]:
        """Extrait le numéro de téléphone fixe avec méthodes améliorées"""
        text = soup.get_text()
        
        # Patterns pour téléphones français (fixes)
        patterns = [
            # Formats standards français
            r'\b0[1-5](?:[-.\s]?\d{2}){4}\b',  # 01 23 45 67 89
            r'\b\+33[1-5](?:[-.\s]?\d{2}){4}\b',  # +33 1 23 45 67 89
            r'\b(?:33|0033)[1-5](?:[-.\s]?\d{2}){4}\b',  # 0033 1 23 45 67 89
            # Avec labels
            r'(?i)(?:tél|tel|téléphone|telephone|fixe)[\s:]*([0-9\s\.\-\+]{10,20})',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                phone = re.sub(r'[^\d\+]', '', match)  # Garder seulement chiffres et +
                
                # Normaliser le numéro
                if phone.startswith('0033'):
                    phone = '+33' + phone[4:]
                elif phone.startswith('33') and len(phone) == 11:
                    phone = '+33' + phone[2:]
                
                # Vérifier que c'est un numéro français valide
                if phone.startswith('+33') and len(phone) == 12:
                    return '+33 ' + phone[3:4] + ' ' + phone[4:6] + ' ' + phone[6:8] + ' ' + phone[8:10] + ' ' + phone[10:12]
                elif phone.startswith('0') and len(phone) == 10:
                    return phone[:2] + ' ' + phone[2:4] + ' ' + phone[4:6] + ' ' + phone[6:8] + ' ' + phone[8:10]
        
        # Chercher dans les balises spécifiques
        phone_selectors = [
            'a[href^="tel:"]',
            '[itemprop="telephone"]',
            '[class*="phone"]',
            '[class*="tel"]',
            '[id*="phone"]',
            '[id*="tel"]'
        ]
        
        for selector in phone_selectors:
            elements = soup.select(selector)
            for element in elements:
                if selector == 'a[href^="tel:"]':
                    href = element.get('href', '')
                    if href.startswith('tel:'):
                        phone = re.sub(r'[^\d\+]', '', href.replace('tel:', ''))
                        if len(phone) >= 10:
                            return self._format_phone_number(phone)
                else:
                    phone_text = element.get_text().strip()
                    phone = re.sub(r'[^\d\+]', '', phone_text)
                    if len(phone) >= 10:
                        return self._format_phone_number(phone)
        
        return None
    
    def extract_mobile(self, soup: BeautifulSoup) -> Optional[str]:
        """Extrait le numéro de téléphone mobile avec méthodes améliorées"""
        text = soup.get_text()
        
        # Patterns pour mobiles français
        patterns = [
            r'\b0[67](?:[-.\s]?\d{2}){4}\b',  # 06/07 XX XX XX XX
            r'\b\+33[67](?:[-.\s]?\d{2}){4}\b',  # +33 6/7 XX XX XX XX
            r'(?i)(?:mobile|portable|cell)[\s:]*([0-9\s\.\-\+]{10,20})',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                phone = re.sub(r'[^\d\+]', '', match)
                
                # Vérifier que c'est un mobile français valide
                if phone.startswith('0') and len(phone) == 10 and phone[1] in ['6', '7']:
                    return phone[:2] + ' ' + phone[2:4] + ' ' + phone[4:6] + ' ' + phone[6:8] + ' ' + phone[8:10]
                elif phone.startswith('+336') or phone.startswith('+337'):
                    return self._format_phone_number(phone)
        
        return None
    
    def _format_phone_number(self, phone: str) -> str:
        """Formate un numéro de téléphone français"""
        # Supprimer tous les caractères non numériques sauf +
        clean_phone = re.sub(r'[^\d\+]', '', phone)
        
        # Format français standard
        if clean_phone.startswith('+33') and len(clean_phone) == 12:
            return '+33 ' + clean_phone[3:4] + ' ' + clean_phone[4:6] + ' ' + clean_phone[6:8] + ' ' + clean_phone[8:10] + ' ' + clean_phone[10:12]
        elif clean_phone.startswith('0') and len(clean_phone) == 10:
            return clean_phone[:2] + ' ' + clean_phone[2:4] + ' ' + clean_phone[4:6] + ' ' + clean_phone[6:8] + ' ' + clean_phone[8:10]
        else:
            return phone  # Retourner tel quel si format non reconnu

    async def extract_official_company_name(self, website_url: str, commercial_name: str) -> Optional[str]:
        """Utilise OpenAI pour extraire la raison sociale officielle depuis le site web"""
        try:
            # D'abord récupérer le contenu du site
            session = await self.get_session()
            async with session.get(website_url) as response:
                if response.status != 200:
                    return None
                    
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                # Extraire le texte principal (limiter pour éviter le token limit)
                text_content = soup.get_text()[:3000]  # Limiter à 3000 caractères
                
            # Utiliser OpenAI pour extraire la raison sociale
            headers = {
                'Authorization': f'Bearer {self.config.OPENAI_API_KEY}',
                'Content-Type': 'application/json'
            }
            
            if self.config.OPENAI_ORG_ID:
                headers['OpenAI-Organization'] = self.config.OPENAI_ORG_ID
            
            prompt = f"""
            Je cherche la raison sociale officielle de l'entreprise "{commercial_name}".
            
            Voici le contenu de leur site web :
            {text_content}
            
            Peux-tu identifier la raison sociale officielle (nom légal) de cette entreprise ?
            Cherche les mentions légales, le bas de page, ou toute référence à SARL, SAS, SA, EURL, etc.
            
            Réponds uniquement avec la raison sociale exacte, sans explication.
            Si tu ne trouves pas, réponds "NOT_FOUND".
            
            Exemples de format:
            - BIMBENET SARL
            - SOCIÉTÉ DURALEX
            - LEROY MERLIN FRANCE SAS
            """
            
            payload = {
                'model': self.config.OPENAI_MODEL,
                'messages': [
                    {'role': 'user', 'content': prompt}
                ],
                'max_tokens': 50,
                'temperature': 0.1
            }
            
            async with session.post('https://api.openai.com/v1/chat/completions', 
                                  headers=headers, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    official_name = data['choices'][0]['message']['content'].strip()
                    
                    if official_name and official_name != "NOT_FOUND":
                        return official_name
                    else:
                        return None
                else:
                    logger.error(f"❌ Erreur OpenAI API pour raison sociale: {response.status}")
                    return None
                    
        except Exception as e:
            logger.error(f"❌ Erreur extraction raison sociale: {str(e)}")
            return None 