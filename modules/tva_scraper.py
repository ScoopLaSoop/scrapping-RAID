"""
Scrapper pour récupérer les informations SIRET, SIREN et TVA
depuis le site numtvagratuit.com
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from config import Config

logger = logging.getLogger(__name__)

class TVAScraper:
    def __init__(self):
        self.config = Config()
        self.driver = None
    
    def setup_driver(self):
        """Configure le driver Selenium"""
        chrome_options = Options()
        chrome_options.add_argument('--headless')  # Mode sans interface
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument(f'--user-agent={self.config.USER_AGENT}')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        self.driver.implicitly_wait(10)
        
        return self.driver
    
    def close_driver(self):
        """Ferme le driver"""
        if self.driver:
            self.driver.quit()
            self.driver = None
    
    async def scrape_legal_info(self, company_name: str) -> Dict[str, Any]:
        """Récupère les informations légales (SIRET, SIREN, TVA) d'une entreprise"""
        try:
            logger.info(f"🔍 Recherche des informations légales pour: {company_name}")
            
            # Configurer le driver
            driver = self.setup_driver()
            
            # Aller sur le site
            driver.get(self.config.TVA_SITE_URL)
            
            # Attendre que la page se charge
            await asyncio.sleep(2)
            
            # Accepter les cookies
            try:
                logger.info("🍪 Acceptation des cookies...")
                cookie_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "body > div.fc-consent-root > div.fc-dialog-container > div.fc-dialog.fc-choice-dialog > div.fc-footer-buttons-container > div.fc-footer-buttons > button.fc-button.fc-cta-consent.fc-primary-button"))
                )
                cookie_button.click()
                logger.info("✅ Cookies acceptés")
                await asyncio.sleep(2)
            except Exception as e:
                logger.warning(f"⚠️ Cookies pas trouvés ou déjà acceptés: {e}")
            
            # Saisir le nom de l'entreprise
            # Sélecteur: //input
            input_element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//input"))
            )
            input_element.clear()
            input_element.send_keys(company_name)
            
            # Cliquer sur le bouton de recherche
            # Sélecteur: //td[(((count(preceding-sibling::*) + 1) = 3) and parent::*)]//input
            search_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//td[(((count(preceding-sibling::*) + 1) = 3) and parent::*)]//input"))
            )
            search_button.click()
            
            # Attendre les résultats
            await asyncio.sleep(3)
            
            # Cliquer sur le premier résultat
            # Sélecteur: //a
            try:
                result_link = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//a"))
                )
                result_link.click()
                
                # Attendre que la page des détails se charge
                await asyncio.sleep(3)
                
                # Extraire les informations
                # Sélecteur: //td
                info_elements = driver.find_elements(By.XPATH, "//td")
                
                legal_data = self.extract_legal_data(info_elements)
                
                logger.info(f"✅ Informations légales trouvées pour: {company_name}")
                return legal_data
                
            except TimeoutException:
                logger.warning(f"⚠️ Aucun résultat trouvé pour: {company_name}")
                return {'error': 'Aucun résultat trouvé'}
                
        except Exception as e:
            logger.error(f"❌ Erreur lors de la recherche des informations légales pour {company_name}: {str(e)}")
            return {'error': str(e)}
        finally:
            self.close_driver()
    
    def extract_legal_data(self, info_elements) -> Dict[str, Any]:
        """Extrait les données légales depuis les éléments HTML"""
        legal_data = {
            'siret': None,
            'siren': None,
            'tva': None,
            'raison_sociale': None,
            'adresse_legale': None,
            'code_postal_legal': None,
            'ville_legale': None
        }
        
        try:
            # Convertir les éléments en texte
            text_elements = [elem.text.strip() for elem in info_elements if elem.text.strip()]
            full_text = ' '.join(text_elements)
            
            # Rechercher les informations spécifiques
            for i, text in enumerate(text_elements):
                text_lower = text.lower()
                
                # SIRET
                if 'siret' in text_lower and i + 1 < len(text_elements):
                    legal_data['siret'] = text_elements[i + 1]
                
                # SIREN
                elif 'siren' in text_lower and i + 1 < len(text_elements):
                    legal_data['siren'] = text_elements[i + 1]
                
                # TVA
                elif 'tva' in text_lower and i + 1 < len(text_elements):
                    legal_data['tva'] = text_elements[i + 1]
                
                # Raison sociale
                elif 'raison sociale' in text_lower and i + 1 < len(text_elements):
                    legal_data['raison_sociale'] = text_elements[i + 1]
                
                # Adresse
                elif 'adresse' in text_lower and i + 1 < len(text_elements):
                    legal_data['adresse_legale'] = text_elements[i + 1]
                
                # Code postal
                elif 'code postal' in text_lower and i + 1 < len(text_elements):
                    legal_data['code_postal_legal'] = text_elements[i + 1]
                
                # Ville
                elif 'ville' in text_lower and i + 1 < len(text_elements):
                    legal_data['ville_legale'] = text_elements[i + 1]
            
            # Nettoyer les données
            legal_data = {k: v.strip() if v and isinstance(v, str) else v for k, v in legal_data.items()}
            
            return legal_data
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de l'extraction des données légales: {str(e)}")
            return {'error': str(e)} 