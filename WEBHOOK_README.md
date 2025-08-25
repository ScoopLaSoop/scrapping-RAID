# 🚀 Webhook Scrapping-RAID pour Make.com

## 📋 Description

Ce webhook permet de déclencher le scrapping automatique d'une entreprise en temps réel quand elle est ajoutée dans Airtable via Make.com.

## 🔧 Configuration Railway

### 1. Variables d'environnement requises

Dans Railway, configurez ces variables :

```env
# Airtable
AIRTABLE_API_KEY=votre_clé_api_airtable
AIRTABLE_BASE_ID=votre_base_id
AIRTABLE_TABLE_NAME=votre_table_name

# APIs légales (optionnel)
API_LEGAL_KEY=votre_clé_api_legale

# Configuration
LOG_LEVEL=INFO
```

### 2. Déploiement

1. Connectez votre repository GitHub à Railway
2. Railway détectera automatiquement la configuration
3. Le serveur démarrera sur le port configuré par Railway

## 📡 Utilisation avec Make.com

### 1. Configuration du webhook dans Make.com

Dans votre scénario Make.com, après l'ajout d'un record dans Airtable :

1. **Ajouter un module HTTP**
2. **Méthode** : POST
3. **URL** : `https://votre-app-railway.railway.app/webhook`
4. **Headers** : `Content-Type: application/json`
5. **Body** :
```json
{
  "record_id": "{{record_id_from_airtable}}"
}
```

### 2. Exemple de scénario Make.com

```
Airtable (Ajouter un record) 
    ↓
HTTP Request (Webhook)
    ↓
Scrapping automatique
    ↓
Airtable (Mise à jour avec données scrappées)
```

## 🔍 Endpoints disponibles

### POST `/webhook`
- **Description** : Déclenche le scrapping d'une entreprise
- **Body** : `{"record_id": "recXXXXXXXXXXXXXX"}`
- **Réponse** :
```json
{
  "status": "success",
  "company_name": "NOM ENTREPRISE",
  "record_id": "recXXXXXXXXXXXXXX",
  "scraped_data": {
    "website_data": {...},
    "legal_data": {...},
    "solvability_data": {...}
  }
}
```

### GET `/health`
- **Description** : Vérification de santé du service
- **Réponse** :
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T12:00:00",
  "service": "scrapping-RAID-webhook"
}
```

## 📊 Données récupérées

Le webhook effectue automatiquement :

1. **🌐 Scrapping web** : Site officiel, téléphone, adresse
2. **🏛️ API légale** : SIRET, SIREN, TVA, adresse légale
3. **🏦 Solvabilité** : État de l'entreprise, niveau de risque

## 🚨 Gestion d'erreurs

- **400** : `record_id` manquant
- **404** : Entreprise non trouvée
- **500** : Erreur interne du serveur

## 📝 Logs

Les logs sont disponibles dans Railway et dans le fichier `webhook.log`.

## 🔄 Redémarrage

Le service redémarre automatiquement en cas d'échec (max 10 tentatives).
