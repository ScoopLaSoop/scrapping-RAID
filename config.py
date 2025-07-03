"""
Configuration du système de scrapping
"""

import os
from dataclasses import dataclass
from dotenv import load_dotenv

# Charger les variables d'environnement depuis le fichier .env
load_dotenv()

@dataclass
class Config:
    # Configuration Airtable
    AIRTABLE_API_KEY: str = os.getenv('AIRTABLE_API_KEY', '')
    AIRTABLE_BASE_ID: str = os.getenv('AIRTABLE_BASE_ID', '')
    AIRTABLE_TABLE_NAME: str = os.getenv('AIRTABLE_TABLE_NAME', 'Entreprises')
    AIRTABLE_VIEW_NAME: str = os.getenv('AIRTABLE_VIEW_NAME', 'Scrapping')
    
    # Configuration OpenAI
    OPENAI_API_KEY: str = os.getenv('OPENAI_API_KEY', '')
    OPENAI_MODEL: str = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')
    OPENAI_ORG_ID: str = os.getenv('OPENAI_ORG_ID', '')
    
    # Configuration Make Webhook
    MAKE_WEBHOOK_URL: str = os.getenv('MAKE_WEBHOOK_URL', 'https://hook.eu2.make.com/mt23gnuf54r6vqzeby66n2gnv7ivkt56')
    
    # Configuration TVA site
    TVA_SITE_URL: str = 'https://www.numtvagratuit.com/'
    
    # Configuration scrapping
    SCRAPING_DELAY: float = 1.0  # Délai entre les requêtes (secondes)
    MAX_RETRIES: int = 3
    TIMEOUT: int = 30
    
    # User Agent pour les requêtes
    USER_AGENT: str = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36' 