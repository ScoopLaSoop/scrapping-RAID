"""
Scrapper alternatif pour récupérer les informations SIRET, SIREN et TVA
Version plus robuste avec gestion des protections anti-bot
"""

import asyncio
import logging
import time
from typing import Dict, Any, Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from config import Config

logger = logging.getLogger(__name__)

class AlternativeTVAScraper:
    def __init__(self):
        self.config = Config()
        self.driver = None
        self.max_retries = 3
    
    def setup_driver(self):
        """Configure le driver Selenium avec options avancées"""
        chrome_options = Options()
        
        # Options pour éviter la détection
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Options de performance
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--disable-plugins')
        chrome_options.add_argument('--disable-images')
        chrome_options.add_argument('--disable-javascript')  # Désactiver JS pour éviter les protections
        
        # User agent réaliste
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        # Taille de fenêtre normale
        chrome_options.add_argument('--window-size=1366,768')
        
        # Mode headless pour la production
        chrome_options.add_argument('--headless')
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            
            # Scripts pour masquer l'automatisation
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            self.driver.execute_script("Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]})")
            self.driver.execute_script("Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en', 'fr']})")
            
            self.driver.implicitly_wait(10)
            return self.driver
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de la configuration du driver: {e}")
            return None
    
    def close_driver(self):
        """Ferme le driver proprement"""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
            self.driver = None
    
    async def scrape_legal_info(self, company_name: str) -> Dict[str, Any]:
        """Récupère les informations légales avec retry"""
        
        for attempt in range(self.max_retries):
            try:
                logger.info(f"🔍 Tentative {attempt + 1}/{self.max_retries} pour {company_name}")
                result = await self._scrape_attempt(company_name)
                
                if result.get('error'):
                    logger.warning(f"⚠️ Tentative {attempt + 1} échouée: {result['error']}")
                    if attempt < self.max_retries - 1:
                        await asyncio.sleep(5 * (attempt + 1))  # Attente croissante
                        continue
                else:
                    return result
                    
            except Exception as e:
                logger.error(f"❌ Erreur tentative {attempt + 1}: {e}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(5 * (attempt + 1))
                    continue
            finally:
                self.close_driver()
        
        return {'error': f'Toutes les tentatives ont échoué pour {company_name}'}
    
    async def _scrape_attempt(self, company_name: str) -> Dict[str, Any]:
        """Une tentative de scraping"""
        try:
            # Configurer le driver
            driver = self.setup_driver()
            if not driver:
                return {'error': 'Impossible de configurer le driver'}
            
            # Accéder au site
            logger.info(f"🌐 Accès au site TVA pour {company_name}")
            driver.get(self.config.TVA_SITE_URL)
            
            # Attendre le chargement
            await asyncio.sleep(3)
            
            # Vérifier si la page est chargée
            if "numtvagratuit" not in driver.current_url:
                return {'error': 'Page non chargée correctement'}
            
            # Essayer d'accepter les cookies (optionnel)
            await self._try_accept_cookies(driver)
            
            # Rechercher et remplir le champ de saisie
            success = await self._search_company(driver, company_name)
            if not success:
                return {'error': 'Impossible de faire la recherche'}
            
            # Extraire les résultats
            legal_data = await self._extract_results(driver)
            
            if legal_data:
                logger.info(f"✅ Données extraites pour {company_name}")
                return legal_data
            else:
                return {'error': 'Aucune donnée extraite'}
                
        except Exception as e:
            logger.error(f"❌ Erreur dans _scrape_attempt: {e}")
            return {'error': str(e)}
    
    async def _try_accept_cookies(self, driver):
        """Essaie d'accepter les cookies"""
        try:
            # Plusieurs sélecteurs possibles pour les cookies
            cookie_selectors = [
                "button.fc-cta-consent",
                "button.fc-button.fc-cta-consent",
                ".fc-primary-button",
                "[data-role='acceptAll']",
                "button[id*='accept']",
                "button[class*='accept']"
            ]
            
            for selector in cookie_selectors:
                try:
                    cookie_button = WebDriverWait(driver, 5).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    cookie_button.click()
                    logger.info(f"✅ Cookies acceptés avec sélecteur: {selector}")
                    await asyncio.sleep(2)
                    return True
                except:
                    continue
                    
        except Exception as e:
            logger.debug(f"Cookies non trouvés ou déjà acceptés: {e}")
        
        return False
    
    async def _search_company(self, driver, company_name: str) -> bool:
        """Recherche une entreprise"""
        try:
            # Chercher le champ de saisie
            input_selectors = [
                "input[type='text']",
                "input[name*='search']",
                "input[placeholder*='entreprise']",
                "input[id*='search']",
                "#search",
                ".search-input"
            ]
            
            input_field = None
            for selector in input_selectors:
                try:
                    input_field = WebDriverWait(driver, 5).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    break
                except:
                    continue
            
            if not input_field:
                return False
            
            # Saisir le nom de l'entreprise
            input_field.clear()
            await asyncio.sleep(1)
            input_field.send_keys(company_name)
            await asyncio.sleep(1)
            
            # Chercher le bouton de recherche
            submit_selectors = [
                "input[type='submit']",
                "button[type='submit']",
                "input[value*='recherch']",
                "button[class*='search']",
                ".search-button"
            ]
            
            for selector in submit_selectors:
                try:
                    submit_button = driver.find_element(By.CSS_SELECTOR, selector)
                    submit_button.click()
                    logger.info(f"✅ Recherche lancée pour {company_name}")
                    await asyncio.sleep(5)
                    return True
                except:
                    continue
            
            # Si pas de bouton, essayer Enter
            input_field.send_keys(Keys.RETURN)
            await asyncio.sleep(5)
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de la recherche: {e}")
            return False
    
    async def _extract_results(self, driver) -> Dict[str, Any]:
        """Extrait les résultats de la page"""
        try:
            # Attendre les résultats
            await asyncio.sleep(3)
            
            # Chercher les liens de résultats
            result_links = driver.find_elements(By.TAG_NAME, "a")
            
            # Cliquer sur le premier lien qui semble être un résultat
            for link in result_links:
                link_text = link.text.strip()
                if link_text and len(link_text) > 10 and any(word in link_text.lower() for word in ['sarl', 'sas', 'sa', 'eurl', 'auto-entrepreneur']):
                    try:
                        link.click()
                        await asyncio.sleep(5)
                        break
                    except:
                        continue
            
            # Extraire les données de la page de détails
            legal_data = {
                'siret': None,
                'siren': None,
                'tva': None,
                'raison_sociale': None,
                'adresse_legale': None,
                'code_postal_legal': None,
                'ville_legale': None
            }
            
            # Récupérer tout le texte de la page
            page_text = driver.page_source.lower()
            
            # Rechercher les informations par regex dans le texte
            import re
            
            # SIRET (14 chiffres)
            siret_match = re.search(r'siret[^\d]*(\d{14})', page_text)
            if siret_match:
                legal_data['siret'] = siret_match.group(1)
            
            # SIREN (9 chiffres)
            siren_match = re.search(r'siren[^\d]*(\d{9})', page_text)
            if siren_match:
                legal_data['siren'] = siren_match.group(1)
            
            # TVA (FR + 11 chiffres)
            tva_match = re.search(r'tva[^\w]*fr[^\d]*(\d{11})', page_text)
            if tva_match:
                legal_data['tva'] = f"FR{tva_match.group(1)}"
            
            return legal_data
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de l'extraction: {e}")
            return {'error': str(e)} 