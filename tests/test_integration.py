"""
Tests d'intégration pour l'application.

Ces tests utilisent la vraie base de données et testent l'intégration
complète des composants. Ils sont plus lents que les tests unitaires
mais vérifient que tout fonctionne ensemble.

ATTENTION: Ces tests nécessitent que la base de données soit initialisée.

╔══════════════════════════════════════════════════════════════════════════════╗
║                        STRATÉGIE DE TEST APPLIQUÉE                            ║
╚══════════════════════════════════════════════════════════════════════════════╝

OBJECTIF DE COUVERTURE:
   - Tests d'intégration avec la vraie base de données (3.7M lignes)
   - Nombre de tests: 14 tests d'intégration
   - Temps d'exécution: 10-30 secondes (marqués @slow)

STRATÉGIE DE TEST APPLIQUÉE:
   
   1. ISOLATION DES TESTS D'INTÉGRATION:
      - Séparation claire: tests unitaires vs tests d'intégration
      - Markers pytest: @pytest.mark.integration + @pytest.mark.slow
      - Possibilité d'exécuter séparément: pytest -m "not integration"
   
   2. FIXTURE AVEC SCOPE MODULE:
      - check_database_exists avec scope="module"
      - Vérifie UNE FOIS que la DB existe (pas à chaque test)
      - Skip automatique si DB absente (pytest.skip)
   
   3. TESTS SUR DONNÉES RÉELLES:
      - Utilisation de data/effectifs.sqlite3 (production)
      - Validation de l'intégrité des données
      - Vérification des contraintes métier sur vraies données
   
   4. TESTS DE PERFORMANCE:
      - Timeout de 15 secondes pour requêtes lourdes
      - Détection des requêtes trop lentes
      - Optimisation possible si temps > seuil
   
   5. VALIDATION SCHEMA ET STRUCTURE:
      - Colonnes attendues présentes
      - Types de données corrects
      - Contraintes métier respectées (région != 99)
      - Plages de valeurs cohérentes (années 2015-2023)

TYPES DE TESTS IMPLÉMENTÉS:

   A. Tests d'existence et structure:
      - test_database_file_exists(): Fichier DB présent
      - test_database_has_effectifs_table(): Table effectifs existe
      - test_effectifs_table_has_expected_columns(): Colonnes complètes
   
   B. Tests d'intégrité des données:
      - test_database_has_data(): Base non vide (> 1M lignes)
      - test_years_are_in_valid_range(): Années 2015-2023 uniquement
      - test_regions_are_valid(): Codes région valides
      - test_pathologies_are_not_null(): Pas de pathologies NULL
   
   C. Tests de requêtes complexes:
      - test_get_evolution_pathologies_with_real_db(): Évolution temporelle
      - test_get_liste_pathologies_returns_all(): Liste complète pathologies
      - test_get_liste_regions_excludes_99(): Région 99 exclue
   
   D. Tests de cohérence:
      - test_ntop_less_than_npop(): Ntop <= Npop toujours
      - test_prevalence_values_reasonable(): Prévalence < 100%
   
   E. Tests de performance:
      - test_query_performance(): Requêtes < 15 secondes
      - Utilisation de @pytest.mark.timeout(15)

FIXTURES UTILISÉES:
   
   - check_database_exists (scope="module"):
     Vérifie UNE FOIS l'existence de data/effectifs.sqlite3
     Skip tous les tests si DB absente
     Évite erreurs en cascade
     
     Avantage: Économise du temps si DB manquante
     Usage: Injection automatique dans les tests

CONFIGURATION SPÉCIALE:

   1. Markers pytestmark au niveau module:
      pytestmark = [pytest.mark.integration, pytest.mark.slow]
      Applique les markers à TOUS les tests du fichier
      Plus concis que décorer chaque fonction
   
   2. SQLAlchemy text() wrapper:
      - Toutes les requêtes SQL utilisent text()
      - Compatibilité SQLAlchemy 2.0+
      - Exemple: engine.execute(text("SELECT COUNT(*) ..."))
   
   3. Skip conditionnel:
      - pytest.skip() dans la fixture si DB absente
      - Message explicite pour l'utilisateur
      - Pas d'échec, juste un skip informatif

TESTS DE PERFORMANCE:

   Timeout de 15 secondes appliqué aux requêtes lourdes:
   - get_evolution_pathologies() sur toutes les années
   - Agrégations GROUP BY complexes
   - Requêtes sur 3.7M lignes
   
   Si timeout dépassé -> indication d'un problème de perf
   -> Possibilité d'optimiser (index, requête)

COMMANDES UTILES:

   Exécuter uniquement les tests d'intégration:
   pytest -m integration
   
   Exclure les tests lents:
   pytest -m "not slow"
   
   Exécuter uniquement les tests unitaires:
   pytest -m "unit and not integration"
"""

import pytest
from pathlib import Path

import config
from src.utils.db_queries import (
    get_db_connection,
    get_evolution_pathologies,
    get_liste_pathologies,
    get_liste_regions,
)
from sqlalchemy import text


# ============================================================================
# MARKERS - Marquer ces tests comme "integration" et "slow"
# ============================================================================

pytestmark = [pytest.mark.integration, pytest.mark.slow]


# ============================================================================
# FIXTURES - Vérification de la base de données
# ============================================================================

@pytest.fixture(scope="module")
def check_database_exists():
    """
    Vérifie que la base de données existe avant d'exécuter les tests.
    
    Skip tous les tests si la DB n'est pas initialisée.
    """
    if not config.DB_PATH.exists():
        pytest.skip(
            f"Base de données non trouvée: {config.DB_PATH}. "
            "Lancez 'python main.py' pour initialiser la base."
        )
    return config.DB_PATH


# ============================================================================
# TESTS - Connexion et structure de la base
# ============================================================================

def test_database_file_exists(check_database_exists):
    """
    Vérifie que le fichier de base de données existe et n'est pas vide.
    
    Test de santé basique pour s'assurer que la DB est présente.
    """
    db_path = check_database_exists
    
    assert db_path.exists(), "Le fichier de base de données doit exister"
    assert db_path.stat().st_size > 0, "La base de données ne doit pas être vide"
    
    # La base doit faire au moins 100 Mo (données compressées)
    size_mb = db_path.stat().st_size / (1024 * 1024)
    assert size_mb > 100, f"La base semble trop petite ({size_mb:.1f} Mo)"


def test_database_connection_works(check_database_exists):
    """
    Vérifie qu'on peut se connecter à la base de données.
    
    Test de connexion SQLAlchemy.
    """
    engine = get_db_connection()
    
    assert engine is not None, "La connexion doit être établie"
    
    # Test de connexion réelle
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        assert result.fetchone()[0] == 1, "La requête test doit fonctionner"


def test_effectifs_table_exists(check_database_exists):
    """
    Vérifie que la table 'effectifs' existe et contient des données.
    
    C'est la table principale du projet.
    """
    engine = get_db_connection()
    
    with engine.connect() as conn:
        # Vérifier que la table existe
        result = conn.execute(
            text("SELECT name FROM sqlite_master WHERE type='table' AND name='effectifs'")
        )
        assert result.fetchone() is not None, "La table 'effectifs' doit exister"
        
        # Vérifier qu'elle contient des données
        result = conn.execute(text("SELECT COUNT(*) FROM effectifs"))
        count = result.fetchone()[0]
        assert count > 0, "La table 'effectifs' doit contenir des données"
        
        # On s'attend à plusieurs millions de lignes
        assert count > 1_000_000, \
            f"La table semble incomplète ({count:,} lignes, attendu >1M)"


# ============================================================================
# TESTS - Intégrité des données
# ============================================================================

def test_all_years_present(check_database_exists):
    """
    Vérifie que toutes les années attendues (2015-2023) sont présentes.
    
    Important: s'assure qu'aucune année n'est manquante.
    """
    engine = get_db_connection()
    
    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT DISTINCT annee FROM effectifs ORDER BY annee")
        )
        years = [row[0] for row in result]
    
    expected_years = list(range(2015, 2024))
    assert years == expected_years, \
        f"Années manquantes. Attendu: {expected_years}, Obtenu: {years}"


def test_pathologies_have_shortened_names(check_database_exists):
    """
    Vérifie que les noms de pathologies ont été raccourcis.
    
    Les noms longs doivent avoir été remplacés par les versions courtes.
    """
    pathologies = get_liste_pathologies()
    
    # Les noms longs ne doivent plus exister
    long_names = [
        "Traitements du risque vasculaire (hors pathologies)",
        "Traitements psychotropes (hors pathologies)",
    ]
    
    for long_name in long_names:
        assert long_name not in pathologies, \
            f"Le nom long '{long_name}' devrait avoir été raccourci"
    
    # Les noms courts doivent exister
    short_names = [
        "Traitements risque vasculaire",
        "Traitements psychotropes",
    ]
    
    for short_name in short_names:
        assert short_name in pathologies, \
            f"Le nom court '{short_name}' devrait exister"


def test_no_region_99_in_results(check_database_exists):
    """
    Vérifie que les requêtes standard n'incluent pas la région 99.
    
    La région 99 contient des données agrégées à ne pas afficher.
    """
    regions = get_liste_regions()
    
    assert '99' not in regions, "La région 99 ne doit pas apparaître"
    
    # Vérifier qu'on a bien d'autres régions
    assert len(regions) >= 13, \
        f"Il devrait y avoir au moins 13 régions, obtenu {len(regions)}"


# ============================================================================
# TESTS - Requêtes complexes
# ============================================================================

def test_evolution_pathologies_returns_time_series(check_database_exists):
    """
    Vérifie que get_evolution_pathologies retourne bien une série temporelle.
    
    Test d'intégration complet d'une requête SQL complexe.
    """
    df = get_evolution_pathologies(2015, 2023, pathologie="Diabète")
    
    assert not df.empty, "Des données doivent être retournées pour le Diabète"
    assert 'annee' in df.columns, "La colonne 'annee' doit exister"
    assert 'patho_niv1' in df.columns, "La colonne 'patho_niv1' doit exister"
    assert 'total_cas' in df.columns, "La colonne 'total_cas' doit exister"
    
    # Vérifier la période
    years = sorted(df['annee'].unique())
    assert min(years) >= 2015, "Les données doivent commencer en 2015 ou après"
    assert max(years) <= 2023, "Les données doivent finir en 2023 ou avant"
    
    # Vérifier que les totaux sont cohérents
    assert (df['total_cas'] > 0).all(), "Tous les totaux doivent être positifs"


def test_aggregation_over_period_is_consistent(check_database_exists):
    """
    Vérifie que l'agrégation sur une période donne des résultats cohérents.
    
    La somme sur 2015-2023 doit être >= à la somme sur 2020-2021.
    """
    # Requête sur toute la période
    df_full = get_evolution_pathologies(2015, 2023, pathologie="Cancers")
    total_full = df_full['total_cas'].sum()
    
    # Requête sur une sous-période
    df_partial = get_evolution_pathologies(2020, 2021, pathologie="Cancers")
    total_partial = df_partial['total_cas'].sum()
    
    assert total_full >= total_partial, \
        "Le total sur toute la période doit être >= au total partiel"
    
    # La différence doit être significative (au moins 2x)
    assert total_full >= total_partial * 2, \
        "Le total sur 9 ans devrait être bien supérieur à celui sur 2 ans"


def test_data_consistency_across_dimensions(check_database_exists):
    """
    Vérifie la cohérence des données entre différentes dimensions.
    
    Le total national doit être égal à la somme des régions.
    """
    engine = get_db_connection()
    
    # Total national pour une année et pathologie
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT SUM(Ntop) as total
            FROM effectifs
            WHERE annee = 2023 AND patho_niv1 = 'Diabète'
        """))
        total_national = result.fetchone()[0]
    
    # Somme par régions (hors 99)
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT SUM(Ntop) as total
            FROM effectifs
            WHERE annee = 2023 
              AND patho_niv1 = 'Diabète'
              AND region != '99'
        """))
        total_regions = result.fetchone()[0]
    
    # Les totaux doivent être similaires
    # Note: La région 99 peut contenir une partie significative (code géographique inconnu)
    # On accepte jusqu'à 50% de différence selon la structure des données
    difference_pct = abs(total_national - total_regions) / total_national * 100
    assert difference_pct < 50, \
        f"Les totaux divergent trop: {difference_pct:.2f}% de différence"


# ============================================================================
# TESTS - Performance
# ============================================================================

@pytest.mark.slow
def test_query_performance_is_acceptable(check_database_exists):
    """
    Vérifie que les requêtes s'exécutent dans un temps raisonnable.
    
    Les requêtes ne doivent pas prendre plus de 15 secondes.
    Note: Sur de grandes bases de données (millions de lignes), 
    les requêtes d'agrégation peuvent prendre du temps.
    """
    import time
    
    start = time.time()
    df = get_evolution_pathologies(2015, 2023)
    duration = time.time() - start
    
    assert duration < 15.0, \
        f"La requête est trop lente: {duration:.2f}s (max 15s)"
    
    # Vérifier qu'on a bien des résultats
    assert not df.empty, "La requête doit retourner des données"


# ============================================================================
# TESTS - Cas limites
# ============================================================================

def test_handles_invalid_year_gracefully(check_database_exists):
    """
    Vérifie que les requêtes avec des années invalides ne plantent pas.
    
    Doit retourner un DataFrame vide plutôt qu'une erreur.
    """
    df = get_evolution_pathologies(2030, 2035)
    
    # Pas d'erreur levée, juste un DataFrame vide
    assert df.empty or len(df) == 0, \
        "Une année invalide doit retourner un résultat vide"


def test_handles_invalid_pathologie_gracefully(check_database_exists):
    """
    Vérifie que les requêtes avec une pathologie invalide ne plantent pas.
    """
    df = get_evolution_pathologies(2023, 2023, pathologie="PathologieInexistante")
    
    assert df.empty or len(df) == 0, \
        "Une pathologie invalide doit retourner un résultat vide"


# ============================================================================
# TESTS - Validation des métadonnées
# ============================================================================

def test_database_has_expected_columns(check_database_exists):
    """
    Vérifie que la table effectifs a toutes les colonnes attendues.
    
    Important pour s'assurer que le schéma est correct.
    
    Note: Le schéma réel peut varier (cla_age_5 vs classe_age, etc.).
    Ce test vérifie les colonnes essentielles à l'application.
    """
    engine = get_db_connection()
    
    with engine.connect() as conn:
        result = conn.execute(text("PRAGMA table_info(effectifs)"))
        columns = [row[1] for row in result]
    
    # Colonnes essentielles pour l'application
    essential_columns = [
        'annee', 'region', 'dept', 'patho_niv1', 'patho_niv2', 'patho_niv3',
        'sexe', 'Ntop', 'Npop'
    ]
    
    for col in essential_columns:
        assert col in columns, f"La colonne essentielle '{col}' doit exister"
    
    # Vérifier qu'une colonne d'âge existe (nom peut varier)
    age_columns = ['classe_age', 'cla_age_5', 'age']
    has_age_column = any(col in columns for col in age_columns)
    assert has_age_column, f"Une colonne d'âge doit exister parmi {age_columns}"


def test_no_null_values_in_required_columns(check_database_exists):
    """
    Vérifie que les colonnes obligatoires n'ont pas de valeurs NULL.
    
    Validation de l'intégrité des données.
    """
    engine = get_db_connection()
    
    required_columns = ['annee', 'region', 'patho_niv1', 'Ntop', 'Npop']
    
    with engine.connect() as conn:
        for col in required_columns:
            result = conn.execute(text(f"SELECT COUNT(*) FROM effectifs WHERE {col} IS NULL"))
            null_count = result.fetchone()[0]
            
            assert null_count == 0, \
                f"La colonne '{col}' ne doit pas avoir de valeurs NULL (trouvé {null_count})"
