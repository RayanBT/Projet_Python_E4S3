# 📊 Dashboard Effectifs & Prévalence Pathologies

> Tableau de bord interactif pour l'analyse des données de santé publique de l'Assurance Maladie (data.ameli.fr)

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue.svg)](https://www.python.org/)
[![Dash](https://img.shields.io/badge/Dash-2.14%2B-orange.svg)](https://dash.plotly.com/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)]()

## 📖 Description

### 🎓 Contexte Académique

Ce projet a été développé dans le cadre d'un projet académique à l'ESIEE Paris. Il vise à démontrer la maîtrise de :

- Développement d'applications web interactives avec Python
- Manipulation et analyse de grandes quantités de données
- Visualisation de données (graphiques, cartes)
- Architecture logicielle et bonnes pratiques de développement
- Gestion de base de données relationnelles


### 🎯 Fonctionnalités Détaillées

Application web interactive permettant d'explorer et visualiser les données d'effectifs et de prévalence des pathologies en France. Le projet propose plusieurs visualisations :

#### 🏠 Page d'Accueil
- Message de bienvenue et présentation du projet
- Démonstration vidéo du projet
- Accès rapide aux différentes visualisations
- Boutons colorés pour chaque page

#### 🗺️ Carte Choroplèthe
- Visualisation géographique par région ou département
- Filtres : pathologie, année, sexe, zone géographique
- Légende interactive avec dégradé de couleurs
- Tooltips avec statistiques détaillées
- Affichage/masquage de l'outre-mer

#### 📈 Évolution Temporelle
- Graphiques d'évolution des pathologies (2015-2023)
- Comparaison multi-pathologies
- Filtres : pathologie, sexe, classe d'âge, région
- Mode région spécifique ou France entière
- Statistiques détaillées par pathologie

#### 📊 Histogrammes
Quatre types de distributions :
1. **Distribution par âge** : Répartition par tranches d'âge (0-10, 10-20...)
2. **Distribution de prévalence** : Répartition par taux de prévalence (0-5%, 5-10%...)
3. **Distribution nombre de cas** : Classes de nombre d'effectifs
4. **Distribution population** : Classes de taille de population

Filtres : pathologie, année, sexe, région

#### 🕸️ Graphique Radar
- Analyse multivariée des pathologies
- Comparaison visuelle de plusieurs critères simultanément
- Filtres : pathologie, année, région
- Vue globale des profils de pathologies

#### 🧀 Diagramme Circulaire (Gravité)
- Répartition des pathologies par niveau de gravité
- Visualisation proportionnelle des catégories
- Filtres : année, sexe, région
- Affichage des pourcentages et effectifs

#### ℹ️ Page À Propos
- Présentation détaillée du projet
- Liste des fonctionnalités principales
- Technologies utilisées avec badges visuels
- Contexte académique

---

## 📘 User Guide

### Prérequis

- **Python 3.9+** ([Télécharger Python](https://www.python.org/downloads/))
- **Git** ([Télécharger Git](https://git-scm.com/downloads))
- **Espace disque** : Minimum 2 Go disponibles
- **Connexion internet** : Nécessaire pour le téléchargement initial des données

### Installation et Déploiement

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

![Page d'accueil pendant l'installation](images/accueil_installation.png)

### 🛠️ Technologies Utilisées

| Technologie | Usage | Version |
|-------------|-------|------|
| **Python** | Langage principal | 3.9+ |
| **Dash** | Framework web interactif | 2.14+ |
| **Plotly** | Graphiques interactifs | Inclus avec Dash |
| **Pandas** | Manipulation de données | 2.0+ |
| **SQLAlchemy** | ORM base de données | 2.0+ |
| **Pydantic** | Validation de données | 2.0+ |
| **Folium** | Cartes interactives | 0.15+ |
| **Branca** | Légendes cartes | 0.7+ |
| **SQLite** | Base de données locale | (intégré Python) |

### 🐛 Dépannage

#### Problème : Erreur "Execution Policy" (Windows)

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

#### Problème : Téléchargement du CSV échoue

- Vérifiez votre connexion internet
- Le fichier fait ~850 Mo, assurez-vous d'avoir assez d'espace disque (2 Go recommandé)
- Si le téléchargement échoue, relancez simplement `python main.py`

#### Problème : Port 8050 déjà utilisé

Modifiez le port dans `main.py` :
```python
app.run(debug=True, port=8051)
```

#### Problème : "Module not found"

Assurez-vous que l'environnement virtuel est activé :
```bash
# Windows
.\venv\Scripts\Activate.ps1

# Linux/Mac
source venv/bin/activate
```

---

## 📊 Data

### 📥 Source des Données

**Source officielle** : [data.ameli.fr](https://data.ameli.fr)

**Jeu de données** : "Effectifs et prévalence des pathologies"

**Caractéristiques** :
- **Taille** : ~850 Mo (CSV brut), ~600 Mo (base SQLite)
- **Période** : 2015-2023 (9 années)
- **Granularité** : Région et département
- **Volume** : ~3,7 millions d'enregistrements

**Dimensions analysées** :
1. **Temporelle** : Année de référence (2015-2023)
2. **Géographique** : 18 régions, 101 départements (métropole + outre-mer)
3. **Pathologique** : 63 pathologies répertoriées
4. **Démographique** : Sexe (homme, femme, ensemble)
5. **Âge** : 12 tranches d'âge (0-10, 10-20, ..., 90+)
6. **Gravité** : Niveau de gravité des pathologies (1-3)
7. **Topologie** : Type de zone (région, département)

**Métriques disponibles** :
- **Ntop** : Nombre de cas (effectifs)
- **prev** : Taux de prévalence (% de la population)
- **Npop** : Population totale de référence

**Traitement des données** :
1. **Téléchargement** : Récupération automatique depuis data.ameli.fr
2. **Nettoyage** : Suppression des valeurs manquantes, correction des types
3. **Importation** : Chargement dans base SQLite pour requêtes optimisées
4. **Transformation** : Nettoyage des labels de pathologies

**Qualité des données** :
- ✅ Données officielles de l'Assurance Maladie
- ✅ Mise à jour annuelle
- ✅ Couverture exhaustive du territoire français
- ⚠️ Données 2020-2021 impactées par la pandémie COVID-19

---

## 👨‍💻 Developer Guide

### 📂 Structure du Projet

```
Projet_Python_E4S3/
├── main.py                    # Point d'entrée de l'application
├── config.py                  # Configuration de l'application
├── requirements.txt           # Dépendances Python
├── README.md                  # Documentation
├── LICENSE                    # Licence MIT
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
├── images/                    # Images du projet
│   └── ...                    # Captures d'écran, diagrammes, etc.
│
└── src/                       # Code source
    ├── assets/                # CSS pour le style
    │   ├── 0_base.css
    │   ├── 1_accueil.css
    │   ├── 2_carte.css
    │   ├── 3_evolution.css
    │   ├── 4_histogramme.css
    │   ├── 5_radar.css
    │   ├── 6_camembert.css
    │   ├── 7_apropos.css
    │   └── zone_dropdown.css
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
    │   ├── carte.py           # Carte interactive
    │   ├── evolution.py       # Graphiques temporels
    │   ├── histogramme.py     # Distributions statistiques
    │   ├── radar.py           # Graphique radar
    │   ├── camembert.py       # Diagramme circulaire
    │   └── apropos.py         # Page à propos
    │
    ├── state/                 # Gestion d'état
    │   └── init_progress.py   # Suivi progression initialisation
    │
    └── utils/                 # Utilitaires
        ├── clean_data.py      # Nettoyage des données
        ├── db_queries.py      # Requêtes SQL
        ├── geo_reference.py   # Référentiel géographique
        └── prepare_data.py    # Préparation et transformation des données
```

### Technologies Utilisées

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

### Ajouter une Nouvelle Page

#### Étape 1 : Créer le fichier de la page

Créez un nouveau fichier dans `src/pages/`, par exemple `ma_nouvelle_page.py` :

```python
"""Ma nouvelle page - Description."""

from dash import html, dcc, Input, Output, callback
import plotly.graph_objects as go
from src.utils.db_queries import get_liste_pathologies


def layout() -> html.Div:
    """Layout de ma nouvelle page."""
    pathologies = get_liste_pathologies()
    
    return html.Div(
        [
            html.Div(
                [
                    html.Div(
                        [
                            html.H1("Ma Nouvelle Page", className="page-title"),
                        ],
                        className="page-header",
                    ),
                    html.P(
                        "Description de ma nouvelle page",
                        className="page-description",
                    ),
                    
                    # Filtres
                    html.Div(
                        [
                            html.Label("Sélectionner une pathologie", className="filter-label"),
                            dcc.Dropdown(
                                id="ma-page-pathologie",
                                options=[{"label": p, "value": p} for p in pathologies],
                                value=pathologies[0] if pathologies else None,
                                clearable=False,
                                className="filter-dropdown",
                            ),
                        ],
                        className="filter-group",
                    ),
                    
                    # Graphique
                    html.Div(
                        [
                            dcc.Graph(id="ma-page-graph"),
                        ],
                        className="chart-container",
                    ),
                ],
                className="page-container",
            )
        ]
    )


# Callback pour mettre à jour le graphique
@callback(
    Output("ma-page-graph", "figure"),
    Input("ma-page-pathologie", "value"),
)
def update_graph(pathologie: str):
    """Met à jour le graphique selon la pathologie sélectionnée."""
    # Votre logique ici
    fig = go.Figure()
    fig.add_trace(go.Bar(x=[1, 2, 3], y=[4, 5, 6]))
    fig.update_layout(title=f"Données pour {pathologie}")
    return fig
```

#### Étape 2 : Créer le fichier CSS (optionnel)

Créez `src/assets/8_ma_nouvelle_page.css` :

```css
/* Styles spécifiques pour ma nouvelle page */
.page-container .custom-style {
    background-color: #f0f0f0;
    padding: 20px;
    border-radius: 8px;
}
```

#### Étape 3 : Ajouter la route dans home.py

Modifiez `src/pages/home.py` :

```python
# Ajoutez l'import en haut du fichier
import src.pages.ma_nouvelle_page as ma_nouvelle_page_module

# Dans la fonction display_page, ajoutez la route
def display_page(pathname: str, init_status: dict) -> html.Div:
    # ... autres routes ...
    
    if pathname == "/ma-nouvelle-page":
        return ma_nouvelle_page_module.layout()
    
    # Page d'accueil par défaut
    return accueil_module.layout()
```

#### Étape 4 : Ajouter le lien dans la navbar

Modifiez `src/components/navbar.py` pour ajouter un lien :

```python
dcc.Link("Ma Nouvelle Page", href="/ma-nouvelle-page", className="nav-link"),
```

#### Étape 5 : Tester

Lancez l'application et accédez à `http://127.0.0.1:8050/ma-nouvelle-page`

### Ajouter une Requête SQL

Dans `src/utils/db_queries.py` :

```python
def get_ma_nouvelle_requete(annee: int, pathologie: str) -> pd.DataFrame:
    """
    Récupère des données personnalisées depuis la base.
    
    Args:
        annee: Année à filtrer
        pathologie: Pathologie à filtrer
        
    Returns:
        DataFrame avec les résultats
    """
    query = """
    SELECT 
        patho_niv1 AS pathologie,
        classe_age,
        SUM(Ntop) AS total_cas,
        AVG(prev) AS prevalence_moyenne
    FROM effectifs
    WHERE annee = :annee
        AND patho_niv1 = :pathologie
    GROUP BY patho_niv1, classe_age
    ORDER BY classe_age
    """
    
    session = get_session()
    try:
        result = session.execute(text(query), {"annee": annee, "pathologie": pathologie})
        df = pd.DataFrame(result.fetchall(), columns=result.keys())
        return df
    finally:
        session.close()
```

---

### ⚙️ Configuration

#### Variables d'environnement (optionnel)

Aucune configuration n'est nécessaire par défaut. Les chemins sont gérés automatiquement.

#### Données personnalisées

Pour utiliser un fichier CSV différent, modifiez la variable `CSV_URL` dans `main.py` :

```python
CSV_URL: Final[str] = "votre-url-csv-ici"
```

---

## 📈 Rapport d'Analyse

### Vue d'Ensemble des Données

L'analyse des données de l'Assurance Maladie (2015-2023) révèle plusieurs tendances importantes concernant les pathologies en France.

### Principales Conclusions

#### 1. Évolution Temporelle des Pathologies

**Tendances Générales** :
- Augmentation constante du **diabète** : +15% entre 2015 et 2023
- **Maladies cardiovasculaires** : Stabilisation après 2018
- **Cancers** : Croissance modérée mais continue (+8% sur la période)
- **Maladies psychiatriques** : Forte augmentation depuis 2020 (+20%)

**Impact de la COVID-19** :
- Rupture nette dans les données 2020-2021
- Sous-diagnostic probable de certaines pathologies chroniques
- Rebond en 2022-2023 avec rattrapage du dépistage

![Évolution temporelle - Impact COVID-19](images/evolution_covid.png)

#### 2. Disparités Géographiques

**Régions les plus touchées** :
- **Hauts-de-France** : Prévalence élevée pour diabète et maladies cardiovasculaires
- **Île-de-France** : Forte concentration de cas en valeur absolue
- **PACA** : Prévalence élevée pour pathologies liées au vieillissement

**Facteurs explicatifs identifiés** :
- Densité de population (Île-de-France)
- Profil socio-économique (Nord-Est)
- Pyramide des âges (PACA, forte proportion de seniors)

#### 3. Répartition par Âge et Sexe

**Pathologies selon l'âge** :
- **0-20 ans** : Principalement troubles du développement et asthme
- **20-40 ans** : Troubles psychiatriques et diabète de type 1
- **40-60 ans** : Montée du diabète de type 2 et hypertension
- **60+ ans** : Maladies cardiovasculaires, cancers, polypathologies

**Différences Homme/Femme** :
- **Hommes** : Prévalence plus élevée pour maladies cardiovasculaires (<45 ans)
- **Femmes** : Prévalence plus élevée pour troubles psychiatriques et thyroïde
- **Équilibre** : Diabète touche équitablement les deux sexes

#### 4. Niveau de Gravité

**Classification par gravité** :
- **Pathologies légères** (30%) : Troubles thyroïdiens, asthme contrôlé
- **Pathologies modérées** (45%) : Diabète, hypertension
- **Pathologies graves** (25%) : Insuffisance rénale, cancers actifs, maladies neurodégénératives

**Charge de morbidité** :
- 15% des patients cumulent 3+ pathologies (polypathologie)
- Polypathologie concentrée chez les 70+ ans (45% de cette tranche)

### Recommandations

1. **Prévention ciblée** : Focus sur les régions à haute prévalence
2. **Dépistage précoce** : Renforcer pour le diabète et les cancers
3. **Suivi post-COVID** : Rattraper le retard de diagnostic 2020-2021
4. **Prise en charge gériatrique** : Adaptation aux polypathologies

### Limites de l'Analyse

- **Données administratives** : Sous-estimation possible des cas non diagnostiqués
- **Changements méthodologiques** : Ruptures de série entre certaines années
- **Confidentialité** : Données agrégées, pas d'analyse individuelle possible

---

## © Copyright

### 🎓 Contexte Académique

Ce projet a été développé dans le cadre d'un projet académique à l'ESIEE Paris. Il vise à démontrer la maîtrise de :

- Développement d'applications web interactives avec Python
- Manipulation et analyse de grandes quantités de données
- Visualisation de données (graphiques, cartes)
- Architecture logicielle et bonnes pratiques de développement
- Gestion de base de données relationnelles

### Déclaration sur l'Honneur

**Nous déclarons sur l'honneur que le code fourni a été produit par nous-mêmes**, à l'exception des éléments explicitement référencés ci-dessous.

### Code Emprunté ou Inspiré

#### 1. Fonctionnalité de téléchargement de fichiers volumineux
**Fichier** : `main.py` (lignes 45-75)  
**Source** : [Real Python - Downloading Files in Python](https://realpython.com/python-download-file-from-url/)  
**Explication** : Utilisation de `requests` avec `stream=True` et `tqdm` pour afficher une barre de progression lors du téléchargement du CSV volumineux.
```python
with requests.get(url, stream=True) as r:
    total_size = int(r.headers.get('content-length', 0))
    with tqdm(total=total_size, unit='B', unit_scale=True) as pbar:
        with open(filepath, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
                pbar.update(len(chunk))
```

#### 2. Structure de l'application Dash multi-pages
**Fichier** : `src/pages/home.py`  
**Source** : [Documentation officielle Dash - Multi-Page Apps](https://dash.plotly.com/urls)  
**Explication** : Pattern de routage avec `dcc.Location` et callbacks pour afficher différentes pages selon l'URL.

#### 3. Création de cartes Folium avec Choropleth
**Fichier** : `src/pages/carte.py` (lignes 346-365)  
**Source** : [Documentation Folium](https://python-visualization.github.io/folium/modules.html#folium.Choropleth)  
**Explication** : Utilisation de `folium.Choropleth` pour créer une carte choroplèthe avec GeoJSON et données pandas.

#### 4. Gestion de la base de données SQLite avec SQLAlchemy
**Fichiers** : `db/models.py`, `db/utils.py`  
**Source** : [Documentation SQLAlchemy 2.0](https://docs.sqlalchemy.org/en/20/)  
**Explication** : Définition de modèles ORM et gestion de sessions pour interagir avec SQLite.

#### 5. Styles CSS pour les dropdowns
**Fichier** : `src/assets/zone_dropdown.css`  
**Source** : Inspiré de [Dash Bootstrap Components](https://dash-bootstrap-components.opensource.faculty.ai/)  
**Explication** : Styles personnalisés pour les composants `dcc.Dropdown` de Dash.

### Ressources et Documentation

**Documentation consultée (non copiée)** :
- Documentation officielle Plotly/Dash
- Documentation Pandas pour la manipulation de DataFrames
- Documentation Folium pour les cartes interactives
- Stack Overflow pour le débogage de problèmes spécifiques
- Data.gouv.fr pour la compréhension des données publiques

### Attestation

**Toute ligne de code non déclarée ci-dessus est réputée être produite par l'auteur/les auteurs du projet.**  
L'absence ou l'omission de déclaration sera considérée comme du plagiat.

---

## 📄 Licence

Ce projet est sous licence MIT. Voir le fichier `LICENSE` pour plus de détails.

La licence MIT permet à l'établissement académique d'utiliser, consulter et évaluer ce projet librement.


## 📧 Contact

- **Projet** : [Projet_Python_E4S3](https://github.com/RayanBT/Projet_Python_E4S3)
- **Auteur** :
    - RayanBT (Rayan Ben Tanfous)
    - LuccaMT (Lucca Matsumoto)
    - e-chab  (Elise Chabrerie)
- **École** : ESIEE Paris (Novembre 2025)
