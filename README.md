# 📊 Dashboard Effectifs & Prévalence Pathologies

> Tableau de bord interactif pour l'analyse des données de santé publique de l'Assurance Maladie (data.ameli.fr)

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue.svg)](https://www.python.org/)
[![Dash](https://img.shields.io/badge/Dash-2.14%2B-orange.svg)](https://dash.plotly.com/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)]()

## 📖 Description

Application web interactive permettant d'explorer et visualiser les données d'effectifs et de prévalence des pathologies en France. Le projet propose plusieurs visualisations :

- 🗺️ **Carte choroplèthe** : Répartition géographique des pathologies par région/département
- 📈 **Évolution temporelle** : Suivi de l'évolution des pathologies dans le temps
- 📊 **Histogrammes** : Distributions statistiques (âge, prévalence, nombre de cas, population)
- 🏠 **Dashboard** : Vue d'ensemble combinant carte et graphiques

## 📦 Source des Données

- **Source** : [Open Data Assurance Maladie](https://data.ameli.fr)
- **Dataset** : Effectifs et prévalences des pathologies
- **URL** : `https://data.ameli.fr/api/explore/v2.1/catalog/datasets/effectifs/exports/csv?use_labels=true`
- **Format** : CSV (~850 Mo, 3.7M+ enregistrements)
- **Période** : 2015-2023
- **Dimensions** : Année, pathologie, âge, sexe, territoire (région/département)
- **Métriques** : Ntop (effectifs), Npop (population), prev (prévalence)

## 🚀 Installation

### Prérequis

- **Python 3.9+** ([Télécharger Python](https://www.python.org/downloads/))
- **Git** ([Télécharger Git](https://git-scm.com/downloads))

### Étapes d'installation

#### 1. Cloner le dépôt

```bash
git clone https://github.com/RayanBT/Projet_Python_E4S3.git
cd Projet_Python_E4S3
```

#### 2. Créer un environnement virtuel

##### 🪟 Windows (PowerShell)

```powershell
# Créer l'environnement virtuel
python -m venv venv

# Activer l'environnement
.\venv\Scripts\Activate.ps1

# Si erreur "Execution Policy", exécuter d'abord :
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

##### 🐧 Linux / 🍎 macOS

```bash
# Créer l'environnement virtuel
python3 -m venv venv

# Activer l'environnement
source venv/bin/activate
```

#### 3. Installer les dépendances

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

#### 4. Lancer l'application

```bash
python main.py
```

**Premier lancement** : L'application va automatiquement :
1. ✅ Télécharger le CSV (~850 Mo) - prend 1-3 minutes
2. ✅ Nettoyer les données
3. ✅ Créer la base SQLite locale (~600 Mo)
4. ✅ Importer les données (~3-5 minutes)
5. ✅ Nettoyer les labels de pathologies

L'application sera accessible sur : **http://127.0.0.1:8050/**

## 📁 Structure du Projet

```
Projet_Python_E4S3/
├── main.py                    # Point d'entrée de l'application
├── requirements.txt           # Dépendances Python
├── README.md                  # Documentation
│
├── data/                      # Données (créé automatiquement)
│   ├── raw/                   # CSV brut téléchargé
│   ├── clean/                 # CSV nettoyé
│   ├── geolocalisation/       # GeoJSON pour la carte
│   └── effectifs.sqlite3      # Base de données SQLite
│
├── db/                        # Gestion base de données
│   ├── models.py              # Modèles SQLAlchemy
│   ├── schema.py              # Schémas Pydantic
│   └── utils.py               # Utilitaires DB (import CSV, etc.)
│
└── src/                       # Code source
    ├── assets/                # CSS pour le style
    │   ├── 0_base.css
    │   ├── 1_accueil.css
    │   ├── 2_carte.css
    │   ├── 3_evolution.css
    │   └── 4_histogramme.css
    │
    ├── components/            # Composants réutilisables
    │   ├── header.py
    │   ├── footer.py
    │   ├── navbar.py
    │   └── icons.py
    │
    ├── pages/                 # Pages de l'application
    │   ├── home.py            # Routage principal
    │   ├── setup.py           # Page d'initialisation
    │   ├── accueil.py         # Page d'accueil
    │   ├── carte.py           # Carte choroplèthe
    │   ├── evolution.py       # Graphiques temporels
    │   ├── histogramme.py     # Distributions statistiques
    │   └── dashboard.py       # Vue d'ensemble
    │
    ├── state/                 # Gestion d'état
    │   └── init_progress.py   # Suivi progression initialisation
    │
    └── utils/                 # Utilitaires
        ├── clean_data.py      # Nettoyage des données
        ├── db_queries.py      # Requêtes SQL
        └── geo_reference.py   # Référentiel géographique
```

## 🎯 Fonctionnalités

### 🏠 Page d'Accueil
- Présentation du projet et démonstration vidéo
- Accès rapide aux différentes visualisations

### 🗺️ Carte Choroplèthe
- Visualisation géographique par région ou département
- Filtres : pathologie, année, sexe
- Légende interactive avec dégradé de couleurs
- Tooltips avec statistiques détaillées

### 📈 Évolution Temporelle
- Graphiques d'évolution des pathologies (2015-2023)
- Comparaison multi-pathologies
- Filtres : pathologie, sexe, classe d'âge
- Mode région spécifique ou France entière

### 📊 Histogrammes
Quatre types de distributions :
1. **Distribution par âge** : Répartition par tranches d'âge (0-10, 10-20...)
2. **Distribution de prévalence** : Répartition par taux de prévalence (0-5%, 5-10%...)
3. **Distribution nombre de cas** : Classes de nombre d'effectifs
4. **Distribution population** : Classes de taille de population

### 📋 Dashboard
- Vue combinée carte + graphiques d'évolution
- Filtres synchronisés
- Export possible des visualisations

## 🛠️ Technologies Utilisées

| Technologie | Usage | Version |
|-------------|-------|---------|
| **Python** | Langage principal | 3.9+ |
| **Dash** | Framework web interactif | 2.14+ |
| **Plotly** | Graphiques interactifs | Inclus avec Dash |
| **Pandas** | Manipulation de données | 2.0+ |
| **SQLAlchemy** | ORM base de données | 2.0+ |
| **Pydantic** | Validation de données | 2.0+ |
| **Folium** | Cartes interactives | 0.15+ |
| **Branca** | Légendes cartes | 0.7+ |
| **SQLite** | Base de données locale | (intégré Python) |

## ⚙️ Configuration

### Variables d'environnement (optionnel)

Aucune configuration n'est nécessaire par défaut. Les chemins sont gérés automatiquement.

### Données personnalisées

Pour utiliser un fichier CSV différent, modifiez la variable `CSV_URL` dans `main.py` :

```python
CSV_URL: Final[str] = "votre-url-csv-ici"
```

## 🐛 Dépannage

### Problème : Erreur "Execution Policy" (Windows)

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Problème : Téléchargement du CSV échoue

- Vérifiez votre connexion internet
- Le fichier fait ~850 Mo, assurez-vous d'avoir assez d'espace disque (2 Go recommandé)
- Si le téléchargement échoue, relancez simplement `python main.py`

### Problème : Port 8050 déjà utilisé

Modifiez le port dans `main.py` :
```python
app.run(debug=True, port=8051)
```

### Problème : "Module not found"

Assurez-vous que l'environnement virtuel est activé :
```bash
# Windows
.\venv\Scripts\Activate.ps1

# Linux/Mac
source venv/bin/activate
```



## 🎓 Contexte Académique

Ce projet a été développé dans le cadre d'un projet académique à l'ESIEE Paris. Il vise à démontrer la maîtrise de :

- Développement d'applications web interactives avec Python
- Manipulation et analyse de grandes quantités de données
- Visualisation de données (graphiques, cartes)
- Architecture logicielle et bonnes pratiques de développement
- Gestion de base de données relationnelles

## 📄 Licence

Ce projet est sous licence MIT. Voir le fichier `LICENSE` pour plus de détails.

La licence MIT permet à l'établissement académique d'utiliser, consulter et évaluer ce projet librement.



## 📧 Contact

- **Projet** : [Projet_Python_E4S3](https://github.com/RayanBT/Projet_Python_E4S3)
- **Auteur** : RayanBT / LuccaMT / e-chab
- **École** : ESIEE Paris
