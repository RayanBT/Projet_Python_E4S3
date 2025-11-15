"""
Configuration pytest et fixtures partagées.

Ce fichier définit les configurations globales pour pytest et les fixtures
qui peuvent être réutilisées dans plusieurs modules de tests.

╔══════════════════════════════════════════════════════════════════════════════╗
║                    CONFIGURATION PYTEST CENTRALISÉE                           ║
╚══════════════════════════════════════════════════════════════════════════════╝

RÔLE DE CE FICHIER (conftest.py):
   
   conftest.py est un fichier spécial reconnu par pytest qui permet de:
   - Définir des fixtures partagées par TOUS les modules de test
   - Configurer le PYTHONPATH pour les imports
   - Définir des hooks pytest (configuration avancée)
   - Éviter la duplication de fixtures entre fichiers
   
   Avantage: Les fixtures ici sont automatiquement disponibles partout
   (pas besoin de les importer explicitement dans les tests)

FIXTURES DÉFINIES:

   1. project_root (scope="session"):
      - Retourne le chemin racine du projet
      - Créée UNE FOIS pour toute la session pytest
      - Utilisée pour construire des chemins absolus
      
   2. data_dir (scope="session"):
      - Retourne le chemin vers le dossier data/
      - Accès facile aux fichiers CSV, SQLite, GeoJSON
      
   3. sample_years (scope="session"):
      - Liste des années de test: [2020, 2021, 2022, 2023]
      - Évite de hard-coder les années dans chaque test
      
   4. sample_regions (scope="session"):
      - Liste des codes région de test: ['11', '24', '27']
      - Régions valides pour les tests (hors 99)

CONFIGURATION PYTHONPATH:

   sys.path.insert(0, str(root_dir))
   
   Permet d'importer les modules depuis le répertoire racine
   Exemple: from src.utils.clean_data import clean_csv_data
   Sans cela: ImportError (module src non trouvé)

SCOPES DES FIXTURES:

   - scope="session": Créée une fois, partagée par tous les tests
     Optimisation: évite recréation
     Usage: données statiques, chemins, constantes
   
   - scope="module": Créée une fois par fichier de test
     Usage: bases de données temporaires
   
   - scope="function" (défaut): Créée à chaque test
     Usage: données modifiées par les tests

UTILISATION DANS LES TESTS:

   Les fixtures sont injectées automatiquement via les paramètres:
   
   def test_example(project_root, sample_years):
       # project_root et sample_years sont disponibles sans import
       csv_path = project_root / "data" / "raw" / "effectifs.csv"
       assert 2023 in sample_years
   
   Pas besoin de:
   - Importer conftest
   - Instancier les fixtures
   - Gérer le nettoyage (pytest s'en charge)
"""

import sys
from pathlib import Path

import pytest

# Ajout du répertoire racine au PYTHONPATH pour permettre les imports
# Cela permet d'importer les modules src.* depuis les tests
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))


@pytest.fixture(scope="session")
def project_root():
    """
    Retourne le chemin racine du projet.
    
    Utile pour construire des chemins absolus vers les fichiers de données
    ou de configuration dans les tests.
    
    Scope: session (créé une seule fois pour toute la session de tests)
    """
    return Path(__file__).parent.parent


@pytest.fixture(scope="session")
def data_dir(project_root):
    """
    Retourne le chemin vers le répertoire data/.
    
    Permet d'accéder facilement aux fichiers de données de test.
    """
    return project_root / "data"


@pytest.fixture
def sample_regions():
    """
    Retourne une liste de codes régions valides pour les tests.
    
    Utile pour tester les fonctions qui manipulent des régions.
    """
    return ['11', '24', '27', '28', '32', '44', '52', '53', '75', '76', '84', '93', '94']


@pytest.fixture
def sample_pathologies():
    """
    Retourne une liste de pathologies de test.
    
    Représente les principales pathologies du jeu de données.
    """
    return [
        'Diabète',
        'Cancers',
        'Maladies cardiovasculaires',
        'Maladies neurologiques',
        'Insuffisance rénale',
        'Traitements risque vasculaire',
        'Traitements psychotropes'
    ]


@pytest.fixture
def sample_years():
    """
    Retourne la plage d'années disponibles dans le jeu de données.
    
    Période standard: 2015-2023
    """
    return list(range(2015, 2024))


# ============================================================================
# Hooks pytest pour personnaliser l'affichage des résultats
# ============================================================================

def pytest_configure(config):
    """
    Hook appelé après la lecture de la configuration pytest.
    
    Permet d'ajouter des markers personnalisés pour organiser les tests.
    """
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )


def pytest_collection_modifyitems(config, items):
    """
    Hook appelé après la collection des tests.
    
    Permet de modifier automatiquement les tests collectés,
    par exemple pour ajouter des markers basés sur le nom du fichier.
    """
    for item in items:
        # Ajouter le marker "unit" à tous les tests dans test_*.py
        if "test_" in item.nodeid:
            item.add_marker(pytest.mark.unit)
        
        # Ajouter le marker "slow" aux tests d'intégration
        if "integration" in item.nodeid:
            item.add_marker(pytest.mark.slow)
            item.add_marker(pytest.mark.integration)
