# 🎯 Guide des Scripts de Démonstration Client

## 📋 Scripts disponibles

### 1. `demo_entreprise.py` - Démonstration Complète
**Durée** : 1-3 minutes  
**Usage** : Présentation détaillée avec toutes les fonctionnalités

```bash
python3 demo_entreprise.py
```

**Affiche** :
- ✅ Scrapping web complet (site, adresse, téléphone, email)
- ✅ Données légales (SIREN, SIRET, TVA)
- ✅ Vérification solvabilité (BODACC, API Gouv, InfoGreffe)
- ✅ Recommandation finale
- ✅ Résumé avec durée d'exécution

### 2. `demo_express.py` - Démonstration Express  
**Durée** : 30 secondes max  
**Usage** : Présentation rapide, focus solvabilité

```bash
python3 demo_express.py "Nom Entreprise"
# ou
python3 demo_express.py
```

**Affiche** :
- ⚡ Vérification solvabilité uniquement
- ⚡ Résultat immédiat
- ⚡ Recommandation simple

## 🎬 Scénarios de démonstration

### Scénario 1 : Entreprise connue solvable
**Commande** :
```bash
python3 demo_entreprise.py
# Saisir: "Google France" ou "Amazon France"
```

**Résultat attendu** :
- ✅ Toutes les données récupérées
- ✅ Entreprise solvable et active
- ✅ Recommandation positive

### Scénario 2 : Test rapide
**Commande** :
```bash
python3 demo_express.py "TEST COMPANY"
```

**Résultat attendu** :
- ⚡ Analyse en moins de 30 secondes
- ✅ Données simulées pour démo fluide
- ✅ Vérification 3 sources officielles

### Scénario 3 : Entreprise quelconque
**Commande** :
```bash
python3 demo_entreprise.py
# Saisir n'importe quel nom d'entreprise française
```

**Résultat** :
- 🔍 Recherche réelle sur internet
- 📊 Données légales via APIs officielles
- 🏦 Vérification solvabilité réelle
- ⏱️ Peut prendre 1-3 minutes selon l'entreprise

## 💡 Conseils pour la démonstration

### ✅ Bonnes pratiques
1. **Tester avant** la démonstration client
2. **Préparer 2-3 entreprises** qui fonctionnent bien
3. **Utiliser demo_express** pour les présentations courtes
4. **Montrer demo_entreprise** pour les clients techniques
5. **Avoir une connexion internet stable**

### 🎯 Entreprises recommandées pour démo
- **"Google France"** - Toujours fonctionnel, données complètes
- **"Amazon France"** - Résultats rapides et fiables  
- **"TEST COMPANY"** - Pour démonstration express sans internet
- **Entreprises locales** - Pour montrer la pertinence

### ⚠️ À éviter
- Entreprises trop petites (peuvent ne pas avoir de site)
- Noms trop génériques ("Boulangerie", "Restaurant")
- Entreprises fermées (sauf si vous voulez montrer la détection!)

## 🎭 Script de présentation suggéré

### Introduction (30 secondes)
*"Je vais vous montrer comment notre système analyse automatiquement la solvabilité d'une entreprise en quelques minutes seulement."*

### Démonstration (2-3 minutes)
1. **Lancer** `demo_entreprise.py`
2. **Saisir** une entreprise connue
3. **Commenter** chaque étape :
   - *"D'abord, on trouve le site web officiel..."*
   - *"Puis on récupère les données légales SIREN/SIRET..."*
   - *"Enfin, on vérifie la solvabilité via 3 sources officielles..."*

### Conclusion (30 secondes)
*"En moins de 3 minutes, vous savez si l'entreprise est fiable pour un devis. Plus de mauvaises surprises !"*

## 🚀 Lancement rapide

```bash
# Démonstration complète
python3 demo_entreprise.py

# Démonstration express
python3 demo_express.py "Google France"

# Test de fonctionnement
python3 demo_express.py "TEST"
```

## 🔧 Dépannage

### Problème : Timeout ou erreurs
**Solution** : Utiliser `demo_express.py` avec "TEST COMPANY"

### Problème : Pas de données trouvées
**Solution** : Essayer avec "Google France" ou "Amazon France"

### Problème : Démonstration trop lente
**Solution** : Utiliser `demo_express.py` uniquement

## 📞 Support

Les scripts sont conçus pour être robustes et continuer même en cas d'erreur API. Si un problème persiste, vérifier la connexion internet et réessayer avec une entreprise connue.