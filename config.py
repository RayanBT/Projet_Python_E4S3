"""Configuration centralisée du projet.

Ce fichier contient tous les chemins et paramètres de configuration
utilisés dans l'application. Les chemins sont relatifs à la racine du projet
pour permettre le clonage et l'utilisation sur différentes machines.
"""

from pathlib import Path
from typing import Final

# =============================================================================
# CHEMINS DE BASE
# =============================================================================

# Racine du projet (où se trouve ce fichier config.py)
ROOT_DIR: Final[Path] = Path(__file__).resolve().parent

# Répertoires principaux
DATA_DIR: Final[Path] = ROOT_DIR / "data"
SRC_DIR: Final[Path] = ROOT_DIR / "src"
DB_DIR: Final[Path] = ROOT_DIR / "db"

# =============================================================================
# DONNÉES BRUTES ET NETTOYÉES
# =============================================================================

# Répertoires de données
DATA_RAW_DIR: Final[Path] = DATA_DIR / "raw"
DATA_CLEAN_DIR: Final[Path] = DATA_DIR / "clean"
DATA_GEO_DIR: Final[Path] = DATA_DIR / "geolocalisation"

# Fichiers CSV
CSV_RAW_PATH: Final[Path] = DATA_RAW_DIR / "effectifs.csv"
CSV_CLEAN_PATH: Final[Path] = DATA_CLEAN_DIR / "csv_clean.csv"

# =============================================================================
# BASE DE DONNÉES
# =============================================================================

# Base de données SQLite
DB_PATH: Final[Path] = DATA_DIR / "effectifs.sqlite3"
DB_TABLE_NAME: Final[str] = "effectifs"

# Paramètres d'import
DB_CHUNK_SIZE: Final[int] = 20_000

# =============================================================================
# FICHIERS DE GÉOLOCALISATION
# =============================================================================

# Fichiers JSON de référence
DEPT_REGION_JSON_PATH: Final[Path] = DATA_GEO_DIR / "departements-regions.json"

# Fichiers GeoJSON pour les cartes
GEOJSON_REGIONS_PATH: Final[Path] = DATA_GEO_DIR / "regions-avec-outre-mer.geojson"
GEOJSON_DEPARTEMENTS_PATH: Final[Path] = DATA_GEO_DIR / "departements-avec-outre-mer.geojson"

# =============================================================================
# RESSOURCES DE L'APPLICATION
# =============================================================================

# Dossier des assets CSS
ASSETS_DIR: Final[Path] = SRC_DIR / "assets"

# =============================================================================
# URLs EXTERNES
# =============================================================================

# URL du CSV des effectifs (data.ameli.fr)
CSV_URL: Final[str] = (
    "https://data.ameli.fr/api/explore/v2.1/catalog/datasets/effectifs/"
    "exports/csv?use_labels=true"
)

# URL du JSON départements-régions (data.gouv.fr)
DEPT_REGION_URL: Final[str] = (
    "https://static.data.gouv.fr/resources/"
    "departements-et-leurs-regions/"
    "20190815-175403/departements-region.json"
)

# =============================================================================
# PARAMÈTRES DE L'APPLICATION
# =============================================================================

# Coordonnées géographiques de la France (pour la carte)
FRANCE_CENTER: Final[tuple[float, float]] = (46.603354, 1.888334)
FRANCE_ZOOM: Final[int] = 6

# Port de l'application Dash
APP_PORT: Final[int] = 8050
APP_HOST: Final[str] = "127.0.0.1"
APP_DEBUG: Final[bool] = True
