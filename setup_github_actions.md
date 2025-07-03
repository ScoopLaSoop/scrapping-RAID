# 🚀 Guide GitHub Actions - Hébergement 100% GRATUIT

## 🎯 Pourquoi GitHub Actions ?

- ✅ **Totalement gratuit** (2000 minutes/mois même pour les repos privés)
- ✅ **Cron jobs intégrés** (planification automatique)
- ✅ **Aucun serveur à maintenir**
- ✅ **Logs détaillés** et historique
- ✅ **Docker support** natif
- ✅ **Variables d'environnement** sécurisées

## 📋 Étapes de configuration

### 1. Créer un repository GitHub

```bash
# Initialiser Git (si pas déjà fait)
git init

# Ajouter tous les fichiers
git add .

# Premier commit
git commit -m "Initial commit - Bot de scrapping"

# Créer le repo sur GitHub (remplacez par votre nom d'utilisateur)
# Puis ajouter l'origine
git remote add origin https://github.com/VOTRE-USERNAME/scrapping-RAID.git
git push -u origin main
```

### 2. Configurer les secrets GitHub

1. Aller sur votre repository GitHub
2. Cliquer sur **Settings** > **Secrets and variables** > **Actions**
3. Cliquer sur **New repository secret**
4. Ajouter chaque secret :

| Nom du secret | Valeur |
|--------------|--------|
| `AIRTABLE_API_KEY` | Votre clé API Airtable |
| `AIRTABLE_BASE_ID` | ID de votre base Airtable |
| `AIRTABLE_TABLE_NAME` | Nom de votre table |
| `AIRTABLE_VIEW_NAME` | Nom de votre vue (ex: "Scrapping") |
| `OPENAI_API_KEY` | Votre clé OpenAI |
| `OPENAI_ORG_ID` | Votre Organization ID OpenAI |
| `MAKE_WEBHOOK_URL` | URL de votre webhook Make (optionnel) |

### 3. Pousser la configuration GitHub Actions

```bash
# Ajouter les nouveaux fichiers Docker
git add Dockerfile .github/ docker-compose.yml .dockerignore

# Commit
git commit -m "Ajout configuration Docker et GitHub Actions"

# Push
git push origin main
```

### 4. Tester l'exécution

1. Aller sur votre repository GitHub
2. Cliquer sur **Actions**
3. Sélectionner **Bot de Scrapping Quotidien**
4. Cliquer sur **Run workflow** > **Run workflow**
5. Attendre l'exécution (2-3 minutes)

## 🔧 Configuration avancée

### Modifier l'heure d'exécution

Dans `.github/workflows/scraper.yml`, modifiez la ligne :
```yaml
- cron: '0 9 * * *'  # 9h UTC = 10h Paris (hiver) / 11h Paris (été)
```

Exemples d'heures :
- `0 8 * * *` : 8h UTC (9h/10h Paris)
- `0 10 * * *` : 10h UTC (11h/12h Paris)
- `0 6 * * 1-5` : 6h UTC du lundi au vendredi seulement

### Notifications d'erreur

Ajoutez cette étape dans le workflow pour recevoir des notifications :

```yaml
- name: 📧 Notification d'erreur
  if: failure()
  run: |
    echo "❌ Erreur détectée lors de l'exécution"
    echo "Consultez les logs dans l'onglet Actions"
```

### Limitation des ressources

Pour économiser les minutes gratuites, ajoutez :

```yaml
- name: 🔄 Limitation des entreprises
  run: |
    docker run --rm \
      -e MAX_COMPANIES=10 \
      # ... autres variables
```

## 🔍 Tests locaux avec Docker

### Construction et test

```bash
# Construction de l'image
docker build -t scraper-bot .

# Test local
docker run --rm \
  --env-file .env \
  scraper-bot

# Ou avec Docker Compose
docker-compose up
```

### Debug

```bash
# Exécution interactive
docker run -it --rm \
  --env-file .env \
  scraper-bot bash

# Vérification de Chrome
docker run --rm scraper-bot google-chrome --version
```

## 📊 Monitoring

### Consulter les logs

1. GitHub > Repository > Actions
2. Cliquer sur l'exécution
3. Développer "🚀 Exécution du bot de scrapping"
4. Voir les logs détaillés

### Historique des exécutions

GitHub garde l'historique complet :
- ✅ Exécutions réussies
- ❌ Erreurs avec détails
- ⏱️ Durée d'exécution
- 📊 Nombre d'entreprises traitées

## 🎯 Avantages vs Inconvénients

### ✅ Avantages

- **Gratuit** : 2000 minutes/mois
- **Fiable** : Infrastructure GitHub
- **Sécurisé** : Secrets chiffrés
- **Logs** : Historique complet
- **Flexibilité** : Modification facile

### ⚠️ Limitations

- **Durée max** : 6 heures par job
- **Stockage** : Pas de persistance entre runs
- **Réseau** : Pas d'IP fixe
- **Ressources** : 2 CPU cores, 7GB RAM

## 🚀 Optimisations

### Réduire le temps d'exécution

1. **Limiter les entreprises** par run
2. **Cache Docker** pour les builds
3. **Parallélisation** des tâches
4. **API uniquement** (pas de scraping web)

### Exemple d'optimisation

```yaml
- name: 🔧 Construction optimisée
  run: |
    docker build --cache-from scraper-bot -t scraper-bot .
```

## 📱 Alternative : Self-hosted runners

Si vous avez un serveur/PC qui tourne 24/7 :

```bash
# Installer un runner GitHub sur votre machine
# Settings > Actions > Runners > New self-hosted runner
```

**Avantages** :
- Temps d'exécution illimité
- Pas de limite de minutes
- Performances locales

## 🎉 Résumé

**Votre bot tournera automatiquement :**
- 🕘 **Tous les jours à 9h** (modifiable)
- 🆓 **Totalement gratuit**
- 📊 **Logs détaillés** disponibles
- 🔒 **Sécurisé** avec secrets GitHub
- 🚀 **Mise à jour facile** via Git

**Prochaines étapes :**
1. Pusher le code sur GitHub
2. Configurer les secrets
3. Tester une première exécution
4. Laisser tourner automatiquement !

Le bot est maintenant autonome et ne nécessite plus votre ordinateur ! 🎯 