# 🏦 Guide de la Vérification de Solvabilité

## 🎯 Objectif

Cette amélioration ajoute une vérification automatique de la solvabilité des entreprises pour éviter les problèmes de paiement futurs. Avant de traiter une demande de devis, vous saurez si l'entreprise est encore active et solvable.

## 🔄 Nouveau flux de traitement

Le scraper suit maintenant ces étapes :

1. **🌐 Scrapping web** - Récupère la raison sociale officielle
2. **🏛️ API légale** - Récupère SIREN/SIRET/TVA 
3. **🏦 Vérification solvabilité** - ✨ **NOUVEAU** ✨
4. **💾 Sauvegarde Airtable** - Avec toutes les données

## 🔍 Sources de vérification

### BODACC (Bulletin Officiel)
- ✅ Détecte les procédures collectives
- ✅ Liquidations judiciaires  
- ✅ Redressements judiciaires
- ✅ Procédures de sauvegarde

### API Gouvernementale
- ✅ État administratif (active/fermée)
- ✅ Date de cessation d'activité
- ✅ Validation des données SIREN/SIRET

### InfoGreffe  
- ✅ Radiations du RCS
- ✅ Informations complémentaires
- ✅ Alertes spécifiques

## 📊 Interprétation des résultats

### ✅ Entreprise FIABLE
```
État: OK
Statut: active  
Risque: low
```
**→ Vous pouvez traiter le devis en toute sécurité**

### ⚠️ Entreprise ATTENTION
```
État: OK
Statut: active
Risque: medium/high
```  
**→ Vérification manuelle recommandée avant devis**

### ❌ Entreprise ÉVITER
```
État: Fermé/Insolvable
Statut: closed/liquidation/redressement
Risque: high
```
**→ NE PAS traiter de devis - Risque de non-paiement**

## 🛠️ Installation et mise à jour

### 1. Mettre à jour Airtable

Ajoutez ces nouveaux champs à votre table `Base Client Contact` :

| Champ | Type | Options |
|-------|------|---------|
| `État de la société` | Single select | "OK", "Fermé/Insolvable" |
| `Statut Entreprise` | Single select | "active", "closed", "liquidation", "redressement", "unknown" |
| `Niveau de Risque` | Single select | "low", "medium", "high", "unknown" |
| `Détails Solvabilité` | Long text | - |
| `Dernière Vérif Solvabilité` | Date & time | - |

### 2. Aucune configuration requise

Les APIs utilisées sont publiques et gratuites :
- ✅ Pas de clé API supplémentaire
- ✅ Pas de configuration env
- ✅ Fonctionne immédiatement

### 3. Tester l'installation

```bash
python test_solvability.py
```

## 📈 Exemple d'utilisation

### Avant (ancien système)
```
Entreprise: ABC COMPANY
SIREN: 123456789
→ Pas d'info sur la solvabilité
→ Risque de devis non payé
```

### Après (nouveau système)  
```
Entreprise: ABC COMPANY
SIREN: 123456789
État: Fermé/Insolvable ❌
Statut: liquidation
Détails: Liquidation judiciaire depuis 2023-05-15
→ ALERTE: Ne pas faire de devis !
```

## 🚀 Démarrage

1. **Mode immédiat** - Pour tester tout de suite :
   ```bash
   python main.py
   # Choisir option 2: "Exécuter immédiatement"
   ```

2. **Mode automatique** - Pour la planification :
   ```bash
   python main.py  
   # Choisir option 1: "Attendre l'exécution planifiée"
   ```

## 📱 Notifications dans les logs

Le nouveau système affiche des informations claires :

```
🏦 ÉTAPE 3: Vérification de solvabilité...
🔍 Vérification solvabilité pour: ABC COMPANY
✅ Solvabilité vérifiée: ✅ Entreprise solvable et active
📊 Détails: ['Aucune procédure collective trouvée - Entreprise présumée active']
```

## ⚡ Performance

- **Temps ajouté** : ~2-3 secondes par entreprise
- **APIs gratuites** : Pas de coût supplémentaire  
- **Fiabilité** : Sources officielles françaises
- **Cache** : Évite les requêtes redondantes

## 🆘 Dépannage

### Problème : Vérification échoue
```
⚠️ Vérification solvabilité échouée: Timeout
```
**Solution** : Les APIs publiques peuvent être lentes, c'est normal. Les données web et légales sont quand même sauvegardées.

### Problème : Champs manquants dans Airtable  
```
❌ Erreur mise à jour Airtable: Unknown field
```
**Solution** : Vérifiez que vous avez bien créé tous les nouveaux champs listés dans `CHAMPS_AIRTABLE.md`

## 💡 Conseils d'utilisation

1. **Filtrage dans Airtable** : Créez des vues filtrées par `État de la société` 
2. **Alertes** : Mettez en couleur rouge les entreprises "Fermé/Insolvable"
3. **Workflow** : Intégrez cette info dans votre processus de validation des devis
4. **Mise à jour** : La vérification se fait à chaque passage du scraper

## 📞 Support

Pour toute question sur cette nouvelle fonctionnalité, vérifiez :
1. Les logs détaillés dans `scrapping_complete.log`
2. Le fichier `CHAMPS_AIRTABLE.md` pour la configuration
3. Le script de test `test_solvability.py` 