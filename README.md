# 🚀 Système de Scrapping d'Entreprises

Ce système automatise le processus de collecte d'informations sur les entreprises en combinant plusieurs sources de données.

## 📋 Fonctionnalités

### Étape 1 : Déclenchement
- Peut être déclenché manuellement ou programmé
- Support pour traitement par lots ou entreprise individuelle

### Étape 2 : Récupération des données Airtable
- Connexion automatique à votre base Airtable
- Récupération des noms d'entreprises à traiter

### Étape 3 : Double scrapping
1. **Scrapping web** : Utilise OpenAI pour trouver le site officiel puis extrait :
   - Adresse
   - Code postal
   - Ville
   - Adresse email
   - Téléphone fixe
   - Téléphone mobile
   - Site web

2. **Scrapping légal** : Utilise [numtvagratuit.com](https://www.numtvagratuit.com/) pour récupérer :
   - Numéro SIRET
   - Numéro SIREN
   - Numéro TVA intracommunautaire
   - Raison sociale
   - Adresse légale

### Étape 4 : Envoi vers Make
- Envoi automatique des données collectées via webhook
- Format JSON structuré

## 🛠️ Installation

### 1. Cloner le projet
```bash
git clone <votre-repo>
cd scrapping-RAID
```

### 2. Installer les dépendances
```bash
pip install -r requirements.txt
```

### 3. Installer ChromeDriver
Pour le scrapping du site TVA, vous devez installer ChromeDriver :

**macOS** :
```bash
brew install chromedriver
```

**Linux** :
```bash
# Ubuntu/Debian
sudo apt-get install chromium-chromedriver

# CentOS/RHEL
sudo yum install chromium-chromedriver
```

**Windows** :
- Télécharger depuis [chromedriver.chromium.org](https://chromedriver.chromium.org/)
- Ajouter au PATH

### 4. Configuration des variables d'environnement

Créez un fichier `.env` basé sur `env_example.txt` :

```bash
cp env_example.txt .env
```

Puis éditez le fichier `.env` avec vos vraies clés API :

```bash
# Configuration Airtable
AIRTABLE_API_KEY=your_airtable_api_key_here
AIRTABLE_BASE_ID=your_airtable_base_id_here
AIRTABLE_TABLE_NAME=Entreprises

# Configuration OpenAI
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-3.5-turbo

# Configuration Make Webhook (déjà configuré)
MAKE_WEBHOOK_URL=https://hook.eu2.make.com/mt23gnuf54r6vqzeby66n2gnv7ivkt56
```

## 🚀 Utilisation

### Lancement complet
```bash
python main.py
```

### Lancement avec options
```bash
# Test du webhook
python run_scraper.py --test-webhook

# Traitement d'une seule entreprise
python run_scraper.py --company "Nom de l'entreprise"

# Mode debug
python run_scraper.py --debug

# Aide
python run_scraper.py --help
```

### Test du webhook uniquement
```bash
python test_webhook.py
```

## 📊 Structure des données envoyées

```json
{
  "timestamp": "2023-12-01T10:00:00",
  "entreprise": {
    "nom": "Nom de l'entreprise",
    "airtable_id": "rec123456789"
  },
  "informations_web": {
    "site_web": "https://example.com",
    "adresse": "123 Rue de la Paix",
    "code_postal": "75001",
    "ville": "Paris",
    "email": "contact@example.com",
    "telephone": "0123456789",
    "mobile": "0612345678"
  },
  "informations_legales": {
    "siret": "12345678901234",
    "siren": "123456789",
    "tva": "FR12345678901",
    "raison_sociale": "EXAMPLE SARL",
    "adresse_legale": "123 Rue Légale",
    "code_postal_legal": "75001",
    "ville_legale": "Paris"
  },
  "erreurs": {
    "erreur_web": null,
    "erreur_legale": null
  }
}
```

## 🔧 Configuration Airtable

### Structure de la table
Votre table Airtable doit contenir au minimum :
- **Nom** : Nom de l'entreprise (type : Single line text)
- **Status** : Statut du traitement (type : Single select)

### Obtenir les clés API
1. **API Key** : [airtable.com/create/tokens](https://airtable.com/create/tokens)
2. **Base ID** : Dans l'URL de votre base `https://airtable.com/[BASE_ID]/...`

## 🔑 Configuration OpenAI

1. Créez un compte sur [OpenAI](https://platform.openai.com/)
2. Générez une clé API dans les paramètres
3. Ajoutez la clé dans votre fichier `.env`

## 📝 Logs

Les logs sont enregistrés dans :
- **Console** : Informations en temps réel
- **Fichier** : `scrapping.log` pour l'historique

## 🚨 Gestion des erreurs

Le système gère automatiquement :
- **Erreurs réseau** : Retry automatique
- **Sites inaccessibles** : Marquage des erreurs
- **Données manquantes** : Champs null dans le JSON
- **Interruptions** : Sauvegarde de l'état

## 🛡️ Bonnes pratiques

1. **Délais** : Respectez les délais entre requêtes (configuré à 1 seconde)
2. **Quotas API** : Surveillez vos quotas OpenAI
3. **Logs** : Consultez régulièrement les logs
4. **Tests** : Testez avec quelques entreprises avant le lancement complet

## 📞 Support

Pour toute question ou problème :
1. Consultez les logs pour identifier l'erreur
2. Vérifiez la configuration des variables d'environnement
3. Testez les connexions API individuellement

## 🔄 Webhook Make

Le webhook est configuré pour recevoir les données au format JSON structuré. 

**URL** : `https://hook.eu2.make.com/mt23gnuf54r6vqzeby66n2gnv7ivkt56`

Testez la connexion avec :
```bash
python test_webhook.py
``` 