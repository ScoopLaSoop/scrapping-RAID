"""
Module de recherche web amélioré pour trouver les sites d'entreprises
Utilise plusieurs méthodes et moteurs de recherche
"""

import aiohttp
import asyncio
import logging
import random
import time
from typing import Optional, List, Dict, Any
from config import Config
import difflib

logger = logging.getLogger(__name__)

class WebSearcher:
    def __init__(self):
        self.config = Config()
        self.session = None
        
        # Configuration Google Custom Search (à ajouter dans config.py)
        self.google_api_key = getattr(self.config, 'GOOGLE_API_KEY', None)
        self.google_cx = getattr(self.config, 'GOOGLE_CX', None)
        
        # User agents rotatifs pour éviter la détection
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:89.0) Gecko/20100101 Firefox/89.0'
        ]
        
    async def get_session(self):
        """Crée ou retourne la session HTTP avec User-Agent rotatif"""
        if not self.session:
            headers = {
                'User-Agent': random.choice(self.user_agents),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'fr-FR,fr;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            }
            
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30),
                headers=headers
            )
        return self.session
    
    async def close_session(self):
        """Ferme la session HTTP"""
        if self.session and not self.session.closed:
            await self.session.close()
            self.session = None
    
    def _generate_name_variants(self, company_name: str) -> List[str]:
        """Génère des variantes du nom d'entreprise pour la recherche"""
        variants = [company_name]
        
        # Variantes courantes
        name_lower = company_name.lower()
        
        # Supprimer les formes juridiques
        legal_forms = ['sarl', 'sas', 'sa', 'eurl', 'sasu', 'sci', 'association', 'ass']
        for form in legal_forms:
            if form in name_lower:
                variants.append(company_name.replace(form, '').replace(form.upper(), '').strip())
        
        # Acronymes -> mots complets (ex: ACOGEMAS -> ACO GEMAS)
        if len(company_name) > 3 and company_name.isupper():
            # Diviser l'acronyme en parties
            for i in range(2, len(company_name)-1):
                variant = company_name[:i] + ' ' + company_name[i:]
                variants.append(variant)
        
        # Mots similaires phonétiquement
        variants.extend(self._get_phonetic_variants(company_name))
        
        return list(set(variants))
    
    def _get_phonetic_variants(self, name: str) -> List[str]:
        """Génère des variantes phonétiques communes"""
        variants = []
        
        # Remplacements phonétiques courants
        phonetic_replacements = {
            'PH': 'F',
            'C': 'K',
            'QU': 'K',
            'X': 'KS',
            'Z': 'S',
            'J': 'G',
            'EMAS': 'EMAS',
            'EMAT': 'EMAS',
            'EGON': 'EGON',
            'EGOMA': 'EGOMA'
        }
        
        for old, new in phonetic_replacements.items():
            if old in name.upper():
                variants.append(name.upper().replace(old, new))
        
        return variants
    
    def _detect_organization_type(self, company_name: str) -> str:
        """Détecte le type d'organisation (entreprise, association, etc.)"""
        name_lower = company_name.lower()
        
        # Mots clés d'associations
        association_keywords = [
            'association', 'ass', 'amicale', 'club', 'federation', 'syndicat',
            'comite', 'collectif', 'groupement', 'union', 'confederation',
            'maison', 'accueil', 'specialise', 'pupilles', 'enseignement'
        ]
        
        association_score = sum(1 for keyword in association_keywords if keyword in name_lower)
        
        if association_score >= 2:
            return 'association'
        elif any(word in name_lower for word in ['sarl', 'sas', 'sa', 'eurl', 'sasu']):
            return 'company'
        else:
            return 'unknown'
    
    async def search_company_website(self, company_name: str) -> Optional[str]:
        """
        Recherche optimisée du site web d'une entreprise
        Version accélérée : URL directe + Bing uniquement
        """
        logger.info(f"🔍 Recherche du site web pour: {company_name}")
        
        # ÉTAPE 1: Test direct des URLs probables (le plus rapide)
        logger.info(f"🎯 Recherche du nom exact: {company_name}")
        result = await self._try_direct_url_variants(company_name)
        if result:
            return result
        
        # ÉTAPE 2: Bing uniquement (plus rapide que DuckDuckGo)
        result = await self._search_via_bing(company_name)
        if result:
            return result
        
        # ÉTAPE 3: Test des variantes du nom (URL directe + Bing)
        logger.info(f"⚠️ Nom exact non trouvé, test des variantes...")
        name_variants = self._generate_name_variants(company_name)
        name_variants = [v for v in name_variants if v != company_name]
        
        if name_variants:
            logger.info(f"🔄 Variantes à tester: {name_variants[:2]}...")
            
            # Tester seulement les 2 premières variantes
            for i, variant in enumerate(name_variants[:2]):
                logger.info(f"🔍 Test variante {i+1}: {variant}")
                
                # Test direct URL uniquement pour les variantes
                result = await self._try_direct_url_variants(variant)
                if result:
                    return result
                
                # Test Bing pour les variantes
                result = await self._search_via_bing(variant)
                if result:
                    return result
                
                # Pause minimale entre les variantes
                await asyncio.sleep(0.5)
        
        logger.warning(f"⚠️ Aucun site trouvé pour {company_name}")
        return None
    
    async def _try_direct_url_variants(self, company_name: str) -> Optional[str]:
        """Teste directement des variantes d'URL probables"""
        logger.info(f"🎯 Test des variantes d'URL directes pour: {company_name}")
        
        # Nettoyer le nom pour créer des URLs
        clean_name = self._clean_name_for_url(company_name)
        
        # Variantes d'URL à tester
        url_variants = [
            f"https://www.{clean_name}.fr",
            f"https://www.{clean_name}.com",
            f"https://{clean_name}.fr",
            f"https://{clean_name}.com",
            f"https://www.{clean_name}.net",
            f"https://www.{clean_name}.org"
        ]
        
        for url in url_variants:
            try:
                session = await self.get_session()
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=3)) as response:
                    if response.status == 200:
                        # Vérification rapide de pertinence
                        if await self._verify_website_relevance_fast(url, company_name):
                            logger.info(f"✅ URL directe trouvée: {url}")
                            return url
                        else:
                            logger.info(f"❌ URL trouvée mais non pertinente: {url}")
            except:
                continue
            
            # Pause minimale
            await asyncio.sleep(0.2)
        
        logger.info(f"❌ Aucune URL directe trouvée pour: {company_name}")
        return None
    
    def _clean_name_for_url(self, company_name: str) -> str:
        """Nettoie un nom d'entreprise pour créer une URL"""
        # Supprimer les mots courants
        words_to_remove = [
            'sarl', 'sas', 'sa', 'eurl', 'sasu', 'sci',
            'société', 'entreprise', 'ets', 'etablissements',
            'groupe', 'compagnie', 'cie', 'et', 'de', 'la', 'le', 'les',
            'du', 'des', 'au', 'aux', 'pour', 'avec', 'sans'
        ]
        
        name = company_name.lower()
        
        # Supprimer les mots courants
        for word in words_to_remove:
            name = name.replace(f' {word} ', ' ')
            name = name.replace(f' {word}', '')
            name = name.replace(f'{word} ', '')
        
        # Nettoyer les caractères spéciaux
        import re
        name = re.sub(r'[^a-zA-Z0-9\s-]', '', name)
        
        # Remplacer espaces par tirets
        name = re.sub(r'\s+', '-', name.strip())
        
        # Supprimer les tirets multiples
        name = re.sub(r'-+', '-', name)
        
        return name.strip('-')
    
    async def _search_via_bing(self, company_name: str) -> Optional[str]:
        """Recherche via Bing (optimisée pour la vitesse)"""
        try:
            logger.info(f"🔍 Recherche Bing pour: {company_name}")
            session = await self.get_session()
            
            # Construire la requête
            query = f'"{company_name}" site officiel'
            url = f"https://www.bing.com/search"
            
            params = {
                'q': query,
                'setlang': 'fr',
                'cc': 'FR'
            }
            
            # Délai minimal pour éviter la détection
            await asyncio.sleep(random.uniform(0.5, 1.5))
            
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    html = await response.text()
                    
                    # Parser les résultats Bing
                    urls = self._extract_urls_from_bing_html(html)
                    
                    for url in urls[:5]:  # Tester les 5 premiers
                        if self._is_relevant_website(url, "", company_name):
                            if await self._test_website_access(url):
                                logger.info(f"✅ Site trouvé via Bing: {url}")
                                return url
                    
                    logger.info(f"❌ Aucun site pertinent trouvé via Bing pour {company_name}")
                    return None
                else:
                    logger.error(f"❌ Erreur Bing: {response.status}")
                    return None
                    
        except Exception as e:
            logger.error(f"❌ Erreur recherche Bing pour {company_name}: {str(e)}")
            return None
    
    def _extract_urls_from_bing_html(self, html: str) -> List[str]:
        """Extrait les URLs des résultats Bing"""
        from bs4 import BeautifulSoup
        import re
        
        soup = BeautifulSoup(html, 'html.parser')
        urls = []
        
        # Chercher les liens dans les résultats Bing
        for link in soup.find_all('a', href=True):
            href = link.get('href')
            if href and href.startswith('http') and 'bing.com' not in href and 'microsoft.com' not in href:
                urls.append(href)
        
        return urls
    
    async def _search_via_duckduckgo_improved(self, company_name: str) -> Optional[str]:
        """Recherche via DuckDuckGo avec gestion améliorée des erreurs et proxies"""
        max_attempts = 3
        
        for attempt in range(max_attempts):
            try:
                logger.info(f"🔍 Recherche DuckDuckGo pour: {company_name} (tentative {attempt + 1}/{max_attempts})")
                
                # Rotation des User-Agents à chaque tentative
                session = await self.get_session()
                session.headers['User-Agent'] = random.choice(self.user_agents)
                
                # Construire la requête avec des termes français
                query = f'"{company_name}" site:fr OR inurl:fr OR "France" OR "français"'
                url = "https://duckduckgo.com/html/"
                
                params = {
                    'q': query,
                    'kl': 'fr-fr',  # Région française
                    'ia': 'web',
                    'safe': 'moderate'
                }
                
                # Délai aléatoire croissant à chaque tentative
                delay = random.uniform(5, 15) * (attempt + 1)
                logger.info(f"⏳ Attente de {delay:.1f}s avant retry...")
                await asyncio.sleep(delay)
                
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        html = await response.text()
                        
                        # Parser les résultats
                        urls = self._extract_urls_from_duckduckgo_html(html)
                        
                        for url in urls[:5]:  # Tester les 5 premiers
                            if self._is_relevant_website(url, "", company_name):
                                if await self._test_website_access(url):
                                    logger.info(f"✅ Site trouvé via DuckDuckGo: {url}")
                                    return url
                        
                        logger.info(f"❌ Aucun site pertinent trouvé via DuckDuckGo pour {company_name}")
                        return None
                        
                    elif response.status == 202:
                        logger.warning(f"⚠️ Erreur DuckDuckGo: {response.status} (tentative {attempt + 1})")
                        if attempt < max_attempts - 1:
                            # Attendre plus longtemps avant le retry
                            await asyncio.sleep(random.uniform(10, 20))
                            continue
                        else:
                            logger.error(f"❌ DuckDuckGo bloqué après {max_attempts} tentatives")
                            return None
                    else:
                        logger.error(f"❌ Erreur DuckDuckGo: {response.status}")
                        return None
                        
            except Exception as e:
                logger.error(f"❌ Erreur recherche DuckDuckGo (tentative {attempt + 1}): {str(e)}")
                if attempt < max_attempts - 1:
                    await asyncio.sleep(random.uniform(5, 10))
                    continue
                else:
                    return None
        
        return None
    
    async def _search_professional_directories(self, company_name: str) -> Optional[str]:
        """Recherche dans les annuaires professionnels français"""
        logger.info(f"📋 Recherche dans les annuaires pour: {company_name}")
        
        # Annuaires français à consulter
        directories = [
            "https://www.pagesjaunes.fr/pagesblanches/recherche",
            "https://www.societe.com/cgi-bin/search",
            "https://www.verif.com/Search"
        ]
        
        # Cette méthode pourrait être développée pour parser les annuaires
        # Pour l'instant, on retourne None (à implémenter si besoin)
        return None
    
    async def _verify_website_relevance_fast(self, url: str, company_name: str) -> bool:
        """Vérification rapide de pertinence (version optimisée)"""
        try:
            session = await self.get_session()
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as response:
                if response.status == 200:
                    html = await response.text()
                    html_lower = html.lower()
                    
                    # Vérification rapide : nom de l'entreprise + indicateurs français
                    company_words = [word.lower() for word in company_name.split() if len(word) > 2]
                    company_matches = sum(1 for word in company_words if word in html_lower)
                    
                    french_indicators = ['france', 'français', 'fr', 'siret', 'siren', 'tva']
                    french_score = sum(1 for indicator in french_indicators if indicator in html_lower)
                    
                    # Validation rapide
                    is_relevant = (
                        company_matches >= len(company_words) * 0.3 and  # Au moins 30% des mots
                        french_score >= 1 and  # Au moins un indicateur français
                        '.fr' in url  # Domaine français
                    )
                    
                    return is_relevant
                else:
                    return False
        except Exception as e:
            logger.error(f"❌ Erreur validation rapide {url}: {str(e)}")
            return False
    
    async def _verify_website_relevance(self, url: str, company_name: str) -> bool:
        """Vérifie si un site web contient bien des informations sur l'entreprise française"""
        try:
            session = await self.get_session()
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 200:
                    html = await response.text()
                    html_lower = html.lower()
                    
                    # 1. Vérifier que c'est un site français
                    french_indicators = [
                        'france', 'français', 'francais', 'fr', 
                        'mentions légales', 'mentions legales',
                        'siret', 'siren', 'tva', 'intracom',
                        'adresse', 'téléphone', 'telephone'
                    ]
                    
                    french_score = sum(1 for indicator in french_indicators if indicator in html_lower)
                    
                    # 2. Vérifier la présence du nom de l'entreprise
                    company_words = [word.lower() for word in company_name.split() if len(word) > 2]
                    company_matches = sum(1 for word in company_words if word in html_lower)
                    
                    # 3. Vérifier des éléments commerciaux français
                    business_indicators = [
                        'contact', 'services', 'produits', 'société', 'entreprise',
                        'accueil', 'à propos', 'qui sommes-nous', 'notre équipe'
                    ]
                    
                    business_score = sum(1 for indicator in business_indicators if indicator in html_lower)
                    
                    # 4. Exclure les sites étrangers évidents
                    foreign_indicators = [
                        'united states', 'usa', 'america', 'uk', 'england',
                        'germany', 'deutschland', 'spain', 'espana', 'italy'
                    ]
                    
                    has_foreign = any(indicator in html_lower for indicator in foreign_indicators)
                    
                    # 5. Vérifier l'extension du domaine
                    domain_score = 2 if '.fr' in url else (1 if '.com' in url else 0)
                    
                    # Calcul du score de pertinence
                    total_score = french_score + (company_matches * 2) + business_score + domain_score
                    
                    # Conditions pour valider le site
                    is_relevant = (
                        total_score >= 5 and  # Score minimum
                        company_matches >= len(company_words) * 0.5 and  # Au moins 50% des mots de l'entreprise
                        not has_foreign and  # Pas d'indicateurs étrangers
                        french_score >= 1  # Au moins un indicateur français
                    )
                    
                    logger.info(f"🔍 Pertinence {url}: score={total_score}, entreprise={company_matches}/{len(company_words)}, français={french_score}, étranger={has_foreign} → {'✅' if is_relevant else '❌'}")
                    
                    return is_relevant
                else:
                    return False
        except Exception as e:
            logger.error(f"❌ Erreur validation pertinence {url}: {str(e)}")
            return False
    
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
        """Vérifie si un site web est pertinent pour l'entreprise (version rapide)"""
        # Filtrer les sites non pertinents
        blacklist = [
            'facebook.com', 'linkedin.com', 'twitter.com', 'instagram.com',
            'youtube.com', 'google.com', 'wikipedia.org', 'pages-jaunes.fr',
            'societe.com', 'verif.com', 'infogreffe.fr', 'company.com',
            'glassdoor.com', 'indeed.com', 'jobijoba.com', 'monster.fr'
        ]
        
        # Exclure les domaines étrangers évidents
        foreign_domains = [
            '.us', '.uk', '.de', '.es', '.it', '.ca', '.au', '.be', '.nl'
        ]
        
        url_lower = url.lower()
        
        # Vérifier blacklist
        for blocked in blacklist:
            if blocked in url_lower:
                return False
        
        # Vérifier domaines étrangers
        for foreign in foreign_domains:
            if foreign in url_lower:
                return False
        
        # Privilégier les domaines français
        if '.fr' in url_lower:
            preference_bonus = 2
        elif '.com' in url_lower:
            preference_bonus = 1
        else:
            preference_bonus = 0
        
        # Vérifier si le nom de l'entreprise est dans l'URL ou le titre
        company_clean = company_name.lower().replace(' ', '').replace('-', '').replace('.', '')
        url_clean = url_lower.replace(' ', '').replace('-', '').replace('.', '')
        title_clean = title.lower().replace(' ', '').replace('-', '').replace('.', '')
        
        # Recherche flexible
        if company_clean in url_clean or company_clean in title_clean:
            return True
        
        # Recherche par mots-clés avec bonus pour domaines français
        company_words = company_name.lower().split()
        url_words = url_lower.split('/')
        title_words = title.lower().split()
        
        matches = 0
        for word in company_words:
            if len(word) > 3:  # Ignorer les mots trop courts
                if any(word in url_word for url_word in url_words) or any(word in title_word for title_word in title_words):
                    matches += 1
        
        required_match_ratio = max(0.4, 0.8 - (preference_bonus * 0.2))  # Plus flexible pour .fr
        return matches >= len(company_words) * required_match_ratio
    
    async def _test_website_access(self, url: str) -> bool:
        """Teste si un site web est accessible"""
        try:
            session = await self.get_session()
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                return response.status == 200
        except:
            return False
    
    async def _search_via_alternative_engines(self, company_name: str) -> Optional[str]:
        """Recherche via des moteurs alternatifs quand les principaux échouent"""
        alternative_engines = [
            ('Startpage', 'https://startpage.com/sp/search'),
            ('Searx', 'https://searx.be/search'),
            ('Yandex', 'https://yandex.com/search/')
        ]
        
        for engine_name, base_url in alternative_engines:
            try:
                logger.info(f"🔍 Recherche via {engine_name} pour: {company_name}")
                
                session = await self.get_session()
                query = f'"{company_name}" site officiel France'
                
                params = {
                    'q': query,
                    'lang': 'fr',
                    'category_general': '1'
                }
                
                async with session.get(base_url, params=params) as response:
                    if response.status == 200:
                        html = await response.text()
                        
                        # Parser les résultats (méthode générique)
                        urls = self._extract_urls_from_generic_html(html)
                        
                        for url in urls[:3]:  # Tester les 3 premiers
                            if self._is_relevant_website(url, "", company_name):
                                if await self._test_website_access(url):
                                    logger.info(f"✅ Site trouvé via {engine_name}: {url}")
                                    return url
                
                # Pause entre les moteurs
                await asyncio.sleep(random.uniform(3, 7))
                
            except Exception as e:
                logger.warning(f"⚠️ Erreur {engine_name}: {str(e)}")
                continue
        
        return None
    
    def _extract_urls_from_generic_html(self, html: str) -> List[str]:
        """Extrait les URLs de n'importe quel moteur de recherche"""
        import re
        
        # Patterns pour trouver les URLs
        url_patterns = [
            r'href="(https?://[^"]+)"',
            r'href=\'(https?://[^\']+)\'',
            r'url":"(https?://[^"]+)"',
            r'(https?://[^\s<>"]+\.[a-zA-Z]{2,})'
        ]
        
        urls = []
        for pattern in url_patterns:
            matches = re.findall(pattern, html, re.IGNORECASE)
            urls.extend(matches)
        
        # Nettoyer et filtrer les URLs
        clean_urls = []
        for url in urls:
            # Supprimer les URLs internes aux moteurs de recherche
            skip_domains = [
                'google.com', 'bing.com', 'duckduckgo.com', 'yahoo.com',
                'startpage.com', 'searx.be', 'yandex.com', 'wikipedia.org',
                'facebook.com', 'twitter.com', 'linkedin.com', 'youtube.com'
            ]
            
            if not any(domain in url.lower() for domain in skip_domains):
                if url.startswith(('http://', 'https://')):
                    clean_urls.append(url)
        
        return list(set(clean_urls))[:10]  # Retourner max 10 URLs uniques 