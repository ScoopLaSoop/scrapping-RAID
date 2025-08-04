# 📋 Champs Airtable - Scraper avec Vérification de Solvabilité

## Configuration de la table

**Nom de la table :** `Base Client Contact`  
**Nom de la vue :** `Scrapping`

## Champs existants (déjà utilisés)

### Informations de base
- `Nom` - Nom de l'entreprise (utilisé pour récupérer les entreprises)
- `Status` - Statut général de traitement

### Données du site web
- `Site` - URL du site web trouvé
- `Adresse de facturation` - Adresse récupérée depuis le site web
- `Tel Principal` - Numéro de téléphone fixe
- `Portable` - Numéro de téléphone mobile

### Données légales
- `SIREN` - Numéro SIREN de l'entreprise
- `SIRET` - Numéro SIRET de l'établissement
- `TVA Intracom` - Numéro TVA intracommunautaire
- `Adresse` - Adresse légale officielle
- `Code Postal` - Code postal légal
- `Ville` - Ville légale

### Suivi du traitement
- `Get Scrapped ?` - Booléen pour marquer les entreprises traitées

## 🆕 Nouveaux champs ajoutés (Vérification de Solvabilité)

### Statut de solvabilité
- `État de la société` - Statut principal : "OK" ou "Fermé/Insolvable"
- `Statut Entreprise` - Statut détaillé : "active", "closed", "liquidation", "redressement", etc.
- `Niveau de Risque` - Évaluation du risque : "low", "medium", "high", "unknown"

### Détails et suivi
- `Détails Solvabilité` - Texte libre avec les détails des vérifications (max 1000 caractères)
- `Dernière Vérif Solvabilité` - Date/heure de la dernière vérification au format ISO

## Types de champs recommandés dans Airtable

| Champ | Type Airtable | Options |
|-------|---------------|---------|
| `État de la société` | Single select | Options: "OK", "Fermé/Insolvable" |
| `Statut Entreprise` | Single select | Options: "active", "closed", "liquidation", "redressement", "sauvegarde", "unknown" |
| `Niveau de Risque` | Single select | Options: "low", "medium", "high", "unknown" |
| `Détails Solvabilité` | Long text | - |
| `Dernière Vérif Solvabilité` | Date & time | Format ISO |

## Sources de données pour la solvabilité

Le système vérifie automatiquement :

1. **BODACC** - Bulletin officiel des annonces civiles et commerciales
   - Procédures collectives
   - Liquidations judiciaires
   - Redressements judiciaires

2. **API Gouvernementale** - API entreprise du gouvernement français
   - État administratif (active/fermée)
   - Date de cessation d'activité

3. **InfoGreffe** - Registre du commerce et des sociétés
   - Radiations
   - Informations complémentaires

## Exemple de données générées

```json
{
  "État de la société": "OK",
  "Statut Entreprise": "active", 
  "Niveau de Risque": "low",
  "Détails Solvabilité": "Aucune procédure collective trouvée - Entreprise présumée active",
  "Dernière Vérif Solvabilité": "2024-01-15T10:30:45.123Z"
}
```

## Interprétation des résultats

### ✅ Entreprise fiable
- État : "OK"
- Statut : "active"
- Risque : "low"

### ⚠️ Attention requise
- État : "OK" 
- Statut : "active"
- Risque : "medium" ou "high"

### ❌ Entreprise à éviter
- État : "Fermé/Insolvable"
- Statut : "closed", "liquidation", "redressement"
- Risque : "high" 