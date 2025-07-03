# Guide de Mise en Production - Bot de Scrapping

## 🎯 PythonAnywhere (Recommandé)

### Étape 1 : Création du compte
1. Aller sur [pythonanywhere.com](https://www.pythonanywhere.com)
2. Créer un compte "Hacker" (5$/mois)
3. Accéder au dashboard

### Étape 2 : Upload du code
```bash
# Option A : Git (recommandé)
git clone https://github.com/votre-repo/scrapping-RAID.git

# Option B : Upload direct via interface web
# Zipper le projet et uploader via Files
```

### Étape 3 : Configuration des variables d'environnement
Dans le bash console PythonAnywhere :
```bash
# Créer le fichier .env
nano .env

# Ajouter vos variables :
AIRTABLE_API_KEY=votre_clé
AIRTABLE_BASE_ID=votre_base_id
AIRTABLE_TABLE_NAME=votre_table
AIRTABLE_VIEW_NAME=Scrapping
OPENAI_API_KEY=votre_clé_openai
OPENAI_ORG_ID=votre_org_id
MAKE_WEBHOOK_URL=votre_webhook_url
```

### Étape 4 : Installation des dépendances
```bash
pip3.9 install --user -r requirements.txt
```

### Étape 5 : Configuration du Cron Job
1. Aller dans l'onglet "Tasks"
2. Créer une nouvelle tâche :
   - **Command:** `python3.9 /home/votrenom/scrapping-RAID/main.py`
   - **Hour:** 9 (9h du matin)
   - **Minute:** 0

### Étape 6 : Test
```bash
cd scrapping-RAID
python3.9 main.py
```

## 🚀 Heroku

### Étape 1 : Préparer le projet
```bash
# Créer un Procfile
echo "worker: python main.py" > Procfile

# Ajouter les buildpacks nécessaires
echo "https://github.com/heroku/heroku-buildpack-chromedriver" > .buildpacks
echo "https://github.com/heroku/heroku-buildpack-google-chrome" >> .buildpacks
echo "heroku/python" >> .buildpacks
```

### Étape 2 : Déployer
```bash
# Installer Heroku CLI
brew install heroku/brew/heroku

# Login et création
heroku login
heroku create votre-app-name
heroku buildpacks:add --index 1 heroku-community/multi-buildpack

# Configuration des variables
heroku config:set AIRTABLE_API_KEY=votre_clé
heroku config:set AIRTABLE_BASE_ID=votre_base_id
heroku config:set OPENAI_API_KEY=votre_clé_openai
# ... toutes les autres variables

# Déploiement
git add .
git commit -m "Deploy to Heroku"
git push heroku main
```

### Étape 3 : Planifier avec Heroku Scheduler
```bash
heroku addons:create scheduler:standard
heroku addons:open scheduler
```
Ajouter une tâche : `python main.py` à 9h00 chaque jour

## 🌊 DigitalOcean

### Étape 1 : Créer un Droplet
1. Choisir Ubuntu 20.04 LTS
2. Taille : 5$/mois (1GB RAM)
3. Région : Europe (Amsterdam/Frankfurt)

### Étape 2 : Configuration serveur
```bash
# Connexion SSH
ssh root@votre_ip

# Mise à jour système
apt update && apt upgrade -y

# Installation Python et dépendances
apt install python3-pip python3-venv git -y

# Installation Chrome et ChromeDriver
wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add -
echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list
apt update
apt install google-chrome-stable -y

# Installation ChromeDriver
wget -N http://chromedriver.storage.googleapis.com/LATEST_RELEASE -O /tmp/chromedriver_version
CHROMEDRIVER_VERSION=$(cat /tmp/chromedriver_version)
wget -N http://chromedriver.storage.googleapis.com/$CHROMEDRIVER_VERSION/chromedriver_linux64.zip -P /tmp/
unzip /tmp/chromedriver_linux64.zip -d /tmp/
chmod +x /tmp/chromedriver
mv /tmp/chromedriver /usr/local/bin/
```

### Étape 3 : Déploiement du code
```bash
# Cloner le projet
git clone https://github.com/votre-repo/scrapping-RAID.git
cd scrapping-RAID

# Environnement virtuel
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configuration des variables
cp env_example.txt .env
nano .env  # Éditer avec vos vraies valeurs
```

### Étape 4 : Automatisation avec Cron
```bash
# Ouvrir crontab
crontab -e

# Ajouter la ligne (9h chaque jour)
0 9 * * * cd /root/scrapping-RAID && /root/scrapping-RAID/venv/bin/python main.py
```

## 💡 Conseils de Production

### Monitoring
- Ajouter des logs dans `/var/log/scrapping.log`
- Configurer des alertes email en cas d'erreur
- Utiliser un service comme UptimeRobot pour surveiller

### Sécurité
- Utiliser des variables d'environnement (jamais de clés en dur)
- Configurer un pare-feu
- Mettre à jour régulièrement le système

### Performance
- Limiter le nombre d'entreprises traitées par run
- Ajouter des délais entre les requêtes
- Utiliser un cache pour éviter les re-scrapping

### Sauvegarde
- Sauvegarder le code sur Git
- Exporter régulièrement la configuration
- Documenter les changements

## 🎉 Résumé

**Ma recommandation : PythonAnywhere**
- ✅ Simple à configurer
- ✅ Selenium pré-installé
- ✅ Cron jobs intégrés
- ✅ Support technique
- ✅ Prix abordable (5$/mois)

Votre bot tournera automatiquement chaque jour à 9h sans intervention ! 