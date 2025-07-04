"""
Module de recherche web pour trouver les sites d'entreprises
Utilise l'API Google Custom Search
"""

import aiohttp
import asyncio
import logging
from typing import Optional, List, Dict, Any
from config import Config

logger = logging.getLogger(__name__)

class WebSearcher:
    def __init__(self):
        self.config = Config()
        self.session = None
        
        # Configuration Google Custom Search (à ajouter dans config.py)
        self.google_api_key = getattr(self.config, 'GOOGLE_API_KEY', None)
        self.google_cx = getattr(self.config, 'GOOGLE_CX', None)
        
    async def get_session(self):
        """Crée ou retourne la session HTTP"""
        if not self.session:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30)
            )
        return self.session
    
    async def close_session(self):
        """Ferme la session HTTP"""
        if self.session and not self.session.closed:
            await self.session.close()
            self.session = None
    
    async def search_company_website(self, company_name: str) -> Optional[str]:
        """
        Recherche le site web d'une entreprise via Google Search
        Fallback vers DuckDuckGo si Google n'est pas configuré
        """
        # Méthode 1: Google Custom Search API (si configuré)
        if self.google_api_key and self.google_cx:
            result = await self._search_via_google(company_name)
            if result:
                return result
        
        # Méthode 2: DuckDuckGo (gratuit, pas d'API key nécessaire)
        result = await self._search_via_duckduckgo(company_name)
        if result:
            return result
        
        # Méthode 3: Fallback OpenAI (comme avant)
        logger.warning(f"⚠️ Recherche web échouée pour {company_name}, fallback OpenAI")
        return None
    
    async def _search_via_google(self, company_name: str) -> Optional[str]:
        """Recherche via Google Custom Search API"""
        try:
            session = await self.get_session()
            
            # Construire la requête de recherche
            query = f'"{company_name}" site officiel'
            url = f"https://www.googleapis.com/customsearch/v1"
            
            params = {
                'key': self.google_api_key,
                'cx': self.google_cx,
                'q': query,
                'num': 5,
                'lr': 'lang_fr'  # Privilégier les sites français
            }
            
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Analyser les résultats
                    items = data.get('items', [])
                    for item in items:
                        url = item.get('link', '')
                        title = item.get('title', '')
                        
                        # Vérifier si c'est un site pertinent
                        if self._is_relevant_website(url, title, company_name):
                            # Vérifier que le site est accessible
                            if await self._test_website_access(url):
                                logger.info(f"🔍 Site trouvé via Google: {url}")
                                return url
                    
                    logger.warning(f"⚠️ Aucun site pertinent trouvé via Google pour {company_name}")
                    return None
                else:
                    logger.error(f"❌ Erreur Google Search API: {response.status}")
                    return None
                    
        except Exception as e:
            logger.error(f"❌ Erreur recherche Google pour {company_name}: {str(e)}")
            return None
    
    async def _search_via_duckduckgo(self, company_name: str) -> Optional[str]:
        """Recherche via DuckDuckGo (parsing HTML)"""
        try:
            session = await self.get_session()
            
            # Construire la requête
            query = f'"{company_name}" site officiel'
            url = f"https://duckduckgo.com/html/"
            
            params = {
                'q': query,
                'kl': 'fr-fr'  # Région française
            }
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            async with session.get(url, params=params, headers=headers) as response:
                if response.status == 200:
                    html = await response.text()
                    
                    # Parser les résultats (basique)
                    urls = self._extract_urls_from_duckduckgo_html(html)
                    
                    for url in urls[:5]:  # Tester les 5 premiers
                        if self._is_relevant_website(url, "", company_name):
                            if await self._test_website_access(url):
                                logger.info(f"🔍 Site trouvé via DuckDuckGo: {url}")
                                return url
                    
                    logger.warning(f"⚠️ Aucun site pertinent trouvé via DuckDuckGo pour {company_name}")
                    return None
                else:
                    logger.error(f"❌ Erreur DuckDuckGo: {response.status}")
                    return None
                    
        except Exception as e:
            logger.error(f"❌ Erreur recherche DuckDuckGo pour {company_name}: {str(e)}")
            return None
    
    def _extract_urls_from_duckduckgo_html(self, html: str) -> List[str]:
        """Extrait les URLs des résultats DuckDuckGo"""
        from bs4 import BeautifulSoup
        import re
        
        soup = BeautifulSoup(html, 'html.parser')
        urls = []
        
        # Chercher les liens dans les résultats
        for link in soup.find_all('a', href=True):
            href = link.get('href')
            if href and href.startswith('http') and 'duckduckgo.com' not in href:
                urls.append(href)
        
        return urls
    
    def _is_relevant_website(self, url: str, title: str, company_name: str) -> bool:
        """Vérifie si un site web est pertinent pour l'entreprise"""
        # Filtrer les sites non pertinents
        blacklist = [
            'facebook.com', 'linkedin.com', 'twitter.com', 'instagram.com',
            'youtube.com', 'google.com', 'wikipedia.org', 'pages-jaunes.fr',
            'societe.com', 'verif.com', 'infogreffe.fr'
        ]
        
        for blocked in blacklist:
            if blocked in url.lower():
                return False
        
        # Vérifier si le nom de l'entreprise est dans l'URL ou le titre
        company_clean = company_name.lower().replace(' ', '').replace('-', '').replace('.', '')
        url_clean = url.lower().replace(' ', '').replace('-', '').replace('.', '')
        title_clean = title.lower().replace(' ', '').replace('-', '').replace('.', '')
        
        # Recherche flexible
        if company_clean in url_clean or company_clean in title_clean:
            return True
        
        # Recherche par mots-clés
        company_words = company_name.lower().split()
        url_words = url.lower().split('/')
        title_words = title.lower().split()
        
        matches = 0
        for word in company_words:
            if len(word) > 3:  # Ignorer les mots trop courts
                if any(word in url_word for url_word in url_words) or any(word in title_word for title_word in title_words):
                    matches += 1
        
        return matches >= len(company_words) * 0.6  # Au moins 60% des mots doivent matcher
    
    async def _test_website_access(self, url: str) -> bool:
        """Teste si un site web est accessible"""
        try:
            session = await self.get_session()
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                return response.status == 200
        except:
            return False 