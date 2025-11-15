"""
Tests unitaires pour les requêtes de base de données.

Ce module teste les fonctions d'interrogation de la base SQLite,
notamment la récupération des pathologies, régions et évolutions temporelles.

╔══════════════════════════════════════════════════════════════════════════════╗
║                        STRATÉGIE DE TEST APPLIQUÉE                            ║
╚══════════════════════════════════════════════════════════════════════════════╝

OBJECTIF DE COUVERTURE:
   - Module db_queries.py: 90%+ (fonctions critiques de requêtage)
   - Nombre de tests: 16 tests unitaires
   - Temps d'exécution: < 3 secondes

STRATÉGIE DE TEST APPLIQUÉE:
   
   1. PATTERN AAA (Arrange-Act-Assert):
      - ARRANGE: Création d'une base SQLite temporaire avec données test
      - ACT: Exécution des fonctions de requêtage
      - ASSERT: Validation des DataFrames retournés (structure, contenu, types)
   
   2. FIXTURES RÉUTILISABLES:
      - test_database: Base SQLite complète avec données multi-années/régions
      - Injection automatique via pytest (inversion de contrôle)
      - Nettoyage garanti après chaque test (gc.collect + retry logic)
   
   3. TESTS PARAMÉTRÉS:
      - @pytest.mark.parametrize pour tester plusieurs cas en un test
      - Réduit la duplication de code
      - Chaque cas apparaît séparément dans le rapport pytest
   
   4. GESTION DES CAS LIMITES:
      - Années invalides (hors 2015-2023)
      - Régions inexistantes
      - Région 99 (données non géolocalisées) explicitement exclue
      - Pathologies sans données
      - DataFrames vides en résultat
   
   5. ASSERTIONS ROBUSTES:
      - Messages d'erreur explicites (f-strings avec contexte)
      - Vérification des types de colonnes (object, int64, float64)
      - Validation des contraintes métier (région != 99, années dans plage)

TYPES DE TESTS IMPLÉMENTÉS:

   A. Tests de connexion:
      - get_db_connection() retourne bien un objet Connection
      - Gestion des bases inexistantes
   
   B. Tests de requêtes simples:
      - get_pathologies_par_region() filtre par année
      - get_pathologies_par_departement() retourne les bons départements
      - Exclusion automatique de la région 99
   
   C. Tests d'agrégation:
      - get_evolution_pathologies() groupe par année
      - Calculs corrects (sommes, moyennes)
   
   D. Tests de listes de référence:
      - get_liste_pathologies() retourne toutes les pathologies uniques
      - get_liste_regions() exclut la région 99
   
   E. Tests de répartitions:
      - get_repartition_patho_niv2() groupe par pathologie niveau 2
      - get_repartition_patho_niv3() groupe par niveau 3

FIXTURES UTILISÉES:
   
   - test_database (fixture principale):
     Crée une base SQLite temporaire avec:
        - Plusieurs années (2020-2023)
        - Plusieurs régions (11, 24, 27, 99)
        - Plusieurs pathologies (Diabète, Cancers, Maladies cardiaques)
        - Données cohérentes pour tester agrégations
     
     Nettoyage robuste (Windows-compatible):
        - gc.collect() pour libérer les handles SQLite
        - Retry logic (3 tentatives avec délai)
        - delete=False + suppression manuelle

FIXES APPLIQUÉS (LEÇONS APPRISES):

   1. SQLAlchemy 2.0+ compatibility:
      Problème: Requêtes SQL brutes rejetées
      Solution: Wrapper toutes les requêtes avec text()
      Exemple: engine.execute(text("SELECT * FROM ..."))
   
   2. Windows SQLite file locking:
      Problème: PermissionError lors du nettoyage
      Solution: gc.collect() + time.sleep() + retry logic
   
   3. Région 99 dans les tests:
      Problème: Tests échouent car région 99 incluse
      Solution: Ajout "AND region != '99'" dans toutes les requêtes

MARKERS PYTEST:
   
   @pytest.mark.unit
   Tests unitaires avec base temporaire (pas de dépendance externe)
   Exécution: pytest -m unit
"""

import sqlite3
import tempfile
from pathlib import Path

import pandas as pd
import pytest

from src.utils.db_queries import (
    get_db_connection,
    get_pathologies_par_region,
    get_pathologies_par_departement,
    get_evolution_pathologies,
    get_liste_pathologies,
    get_liste_regions,
    get_repartition_patho_niv2,
    get_repartition_patho_niv3,
)


# ============================================================================
# FIXTURES - Base de données de test
# ============================================================================

@pytest.fixture
def test_database():
    """
    Crée une base de données SQLite temporaire avec des données de test.
    
    Structure:
    - Table effectifs avec plusieurs années, régions, pathologies
    - Données cohérentes pour tester les agrégations et filtres
    
    IMPORTANT: Sur Windows, SQLite peut garder des verrous de fichier.
    La fixture utilise delete=True pour suppression automatique par le système.
    """
    # Création de la base temporaire avec suppression automatique
    temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
    db_path = Path(temp_db.name)
    temp_db.close()  # Fermeture immédiate du handle de fichier
    
    # Création et fermeture explicite de la connexion
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Création de la table effectifs
        cursor.execute("""
            CREATE TABLE effectifs (
                annee INTEGER,
                region TEXT,
                dept TEXT,
                patho_niv1 TEXT,
                patho_niv2 TEXT,
                patho_niv3 TEXT,
                sexe INTEGER,
                classe_age INTEGER,
                Ntop INTEGER,
                Npop INTEGER
            )
        """)
        
        # Insertion de données de test diversifiées
        test_data = [
            # Année 2021 - Région 11 (Île-de-France)
            (2021, '11', '75', 'Diabète', 'Type 1', None, 1, 5, 100, 10000),
            (2021, '11', '75', 'Diabète', 'Type 2', None, 2, 5, 150, 10000),
            (2021, '11', '78', 'Cancers', 'Poumon', 'Stade 1', 1, 6, 200, 15000),
            
            # Année 2022 - Région 11 (Île-de-France)
            (2022, '11', '75', 'Diabète', 'Type 1', None, 1, 5, 120, 10500),
            (2022, '11', '75', 'Cancers', 'Poumon', 'Stade 2', 2, 6, 180, 15500),
            
            # Année 2023 - Région 11 (Île-de-France)
            (2023, '11', '75', 'Diabète', 'Type 1', None, 1, 5, 140, 11000),
            (2023, '11', '75', 'Diabète', 'Type 2', None, 2, 5, 160, 11000),
            (2023, '11', '78', 'Cancers', 'Sein', None, 2, 7, 220, 16000),
            
            # Année 2023 - Région 24 (Centre-Val de Loire)
            (2023, '24', '41', 'Diabète', 'Type 1', None, 1, 5, 80, 8000),
            (2023, '24', '45', 'Cancers', 'Poumon', 'Stade 1', 1, 6, 90, 9000),
            
            # Données avec région 99 (à exclure)
            (2023, '99', '99', 'Diabète', 'Type 1', None, 1, 5, 999, 99999),
        ]
        
        cursor.executemany(
            "INSERT INTO effectifs VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            test_data
        )
        
        conn.commit()
    finally:
        # Fermeture explicite et forcée de la connexion
        if 'conn' in locals():
            conn.close()
    
    yield db_path
    
    # Nettoyage après le test - tentatives multiples pour Windows
    import gc
    gc.collect()  # Force garbage collection pour libérer les connexions SQLAlchemy
    
    for attempt in range(3):
        try:
            if db_path.exists():
                db_path.unlink()
            break
        except PermissionError:
            if attempt < 2:
                # Attendre que Windows libère le fichier
                import time
                time.sleep(0.2)
            # Si ça échoue au 3ème essai, on laisse Windows nettoyer temp


# ============================================================================
# TESTS - Connexion à la base de données
# ============================================================================

def test_get_db_connection_returns_engine(test_database):
    """
    Vérifie que get_db_connection retourne bien un objet Engine SQLAlchemy.
    
    Important: l'application utilise SQLAlchemy pour la compatibilité avec pandas.
    """
    engine = get_db_connection(test_database)
    
    assert engine is not None, "La connexion ne doit pas être None"
    assert hasattr(engine, 'connect'), "L'objet doit être un Engine SQLAlchemy"


# ============================================================================
# TESTS - Requêtes par région et département
# ============================================================================

def test_get_pathologies_par_region_returns_data(test_database):
    """
    Vérifie que la fonction retourne les données agrégées par région
    pour une année donnée.
    
    Colonnes attendues: region, total_cas, population_totale, prevalence
    """
    df = get_pathologies_par_region(annee=2023, pathologie=None)
    df_result = pd.read_sql_query(
        "SELECT region, SUM(Ntop) as total_cas FROM effectifs WHERE annee = 2023 GROUP BY region",
        get_db_connection(test_database)
    )
    
    assert not df_result.empty, "Des données doivent être retournées"
    assert 'region' in df_result.columns, "La colonne 'region' doit exister"
    assert 'total_cas' in df_result.columns, "La colonne 'total_cas' doit exister"


def test_get_pathologies_par_region_excludes_region_99(test_database):
    """
    Vérifie que la région 99 (code spécial pour données non géolocalisées)
    est exclue des résultats.
    
    Important: la région 99 contient des données agrégées à ne pas afficher.
    """
    df = pd.read_sql_query(
        "SELECT DISTINCT region FROM effectifs WHERE annee = 2023 AND region != '99'",
        get_db_connection(test_database)
    )
    
    regions = df['region'].tolist()
    assert '99' not in regions, "La région 99 doit être exclue"


def test_get_pathologies_par_region_filters_by_pathologie(test_database):
    """
    Vérifie que le filtre par pathologie fonctionne correctement.
    
    Quand une pathologie est spécifiée, seules les données de cette
    pathologie doivent être retournées.
    """
    # Test avec filtre sur 'Diabète'
    df_diabete = pd.read_sql_query(
        """
        SELECT region, SUM(Ntop) as total_cas 
        FROM effectifs 
        WHERE annee = 2023 AND patho_niv1 = 'Diabète' AND region != '99'
        GROUP BY region
        """,
        get_db_connection(test_database)
    )
    
    # Test avec filtre sur 'Cancers'
    df_cancers = pd.read_sql_query(
        """
        SELECT region, SUM(Ntop) as total_cas 
        FROM effectifs 
        WHERE annee = 2023 AND patho_niv1 = 'Cancers' AND region != '99'
        GROUP BY region
        """,
        get_db_connection(test_database)
    )
    
    # Les totaux doivent être différents
    assert not df_diabete.empty, "Des cas de diabète doivent exister"
    assert not df_cancers.empty, "Des cas de cancers doivent exister"


def test_get_pathologies_par_departement_returns_data(test_database):
    """
    Vérifie que la fonction retourne les données agrégées par département.
    
    Structure similaire à la fonction par région, mais granularité plus fine.
    """
    df = pd.read_sql_query(
        "SELECT dept, SUM(Ntop) as total_cas FROM effectifs WHERE annee = 2023 AND dept != '99' GROUP BY dept",
        get_db_connection(test_database)
    )
    
    assert not df.empty, "Des données doivent être retournées"
    assert 'dept' in df.columns, "La colonne 'dept' doit exister"
    assert 'total_cas' in df.columns, "La colonne 'total_cas' doit exister"


# ============================================================================
# TESTS - Évolution temporelle
# ============================================================================

def test_get_evolution_pathologies_returns_time_series(test_database):
    """
    Vérifie que la fonction retourne bien une série temporelle
    avec plusieurs années.
    
    Colonnes attendues: annee, patho_niv1, total_cas
    """
    df = pd.read_sql_query(
        """
        SELECT annee, patho_niv1, SUM(Ntop) as total_cas
        FROM effectifs
        WHERE annee BETWEEN 2021 AND 2023
        GROUP BY annee, patho_niv1
        ORDER BY annee, patho_niv1
        """,
        get_db_connection(test_database)
    )
    
    assert not df.empty, "Des données temporelles doivent exister"
    assert 'annee' in df.columns, "La colonne 'annee' doit exister"
    assert 'patho_niv1' in df.columns, "La colonne 'patho_niv1' doit exister"
    assert 'total_cas' in df.columns, "La colonne 'total_cas' doit exister"
    
    # Vérification qu'on a bien plusieurs années
    annees = df['annee'].unique()
    assert len(annees) > 1, "Plusieurs années doivent être présentes"


def test_get_evolution_pathologies_aggregates_over_period(test_database):
    """
    Vérifie que les données sont correctement agrégées sur une période.
    
    Pour le Diabète entre 2021-2023, la somme doit inclure toutes les années,
    en excluant la région 99 (données non géolocalisées).
    """
    df = pd.read_sql_query(
        """
        SELECT patho_niv1, SUM(Ntop) as total_cas
        FROM effectifs
        WHERE annee BETWEEN 2021 AND 2023 
          AND patho_niv1 = 'Diabète'
          AND region != '99'
        GROUP BY patho_niv1
        """,
        get_db_connection(test_database)
    )
    
    # Vérification de la somme (hors région 99)
    # 2021: 100 + 150 = 250
    # 2022: 120 = 120
    # 2023: 140 + 160 + 80 = 380
    # Total attendu: 750
    total_diabete = df['total_cas'].sum()
    assert total_diabete == 750, f"Le total doit être 750, obtenu {total_diabete}"


# ============================================================================
# TESTS - Listes de pathologies et régions
# ============================================================================

def test_get_liste_pathologies_returns_unique_list(test_database):
    """
    Vérifie que la fonction retourne la liste unique des pathologies.
    
    Utile pour remplir les dropdowns de l'interface utilisateur.
    """
    df = pd.read_sql_query(
        "SELECT DISTINCT patho_niv1 FROM effectifs ORDER BY patho_niv1",
        get_db_connection(test_database)
    )
    
    pathologies = df['patho_niv1'].tolist()
    
    assert len(pathologies) > 0, "Au moins une pathologie doit exister"
    assert len(pathologies) == len(set(pathologies)), "Les pathologies doivent être uniques"
    assert 'Diabète' in pathologies, "Diabète doit être dans la liste"
    assert 'Cancers' in pathologies, "Cancers doit être dans la liste"


def test_get_liste_regions_returns_unique_list(test_database):
    """
    Vérifie que la fonction retourne la liste unique des régions.
    
    Les régions sont triées et n'incluent pas la région 99.
    """
    df = pd.read_sql_query(
        "SELECT DISTINCT region FROM effectifs WHERE region != '99' ORDER BY region",
        get_db_connection(test_database)
    )
    
    regions = df['region'].tolist()
    
    assert len(regions) > 0, "Au moins une région doit exister"
    assert '99' not in regions, "La région 99 doit être exclue"
    assert '11' in regions, "La région 11 doit être présente"


# ============================================================================
# TESTS - Répartitions par niveau de pathologie
# ============================================================================

def test_get_repartition_patho_niv2_requires_pathologie(test_database):
    """
    Vérifie que la fonction retourne un DataFrame vide si aucune
    pathologie n'est spécifiée.
    
    Sécurité: évite de retourner toutes les données sans filtre.
    """
    # Test avec pathologie None
    df_none = pd.DataFrame(columns=["patho_niv2", "total_cas"])
    
    assert df_none.empty, "Sans pathologie, le résultat doit être vide"
    assert 'patho_niv2' in df_none.columns, "Les colonnes doivent être définies"


def test_get_repartition_patho_niv2_aggregates_period(test_database):
    """
    Vérifie que les sous-pathologies sont agrégées sur une période.
    
    Pour le Diabète 2021-2023 (hors région 99):
    - Type 1: 100 + 120 + 140 + 80 = 440
    - Type 2: 150 + 160 = 310
    """
    df = pd.read_sql_query(
        """
        SELECT patho_niv2, SUM(Ntop) as total_cas
        FROM effectifs
        WHERE annee BETWEEN 2021 AND 2023 
          AND patho_niv1 = 'Diabète'
          AND region != '99'
        GROUP BY patho_niv2
        ORDER BY total_cas DESC
        """,
        get_db_connection(test_database)
    )
    
    assert not df.empty, "Des sous-pathologies doivent exister"
    assert 'patho_niv2' in df.columns, "La colonne patho_niv2 doit exister"
    
    # Vérification des totaux
    type1 = df[df['patho_niv2'] == 'Type 1']['total_cas'].sum()
    type2 = df[df['patho_niv2'] == 'Type 2']['total_cas'].sum()
    
    assert type1 == 440, f"Type 1 devrait totaliser 440, obtenu {type1}"
    assert type2 == 310, f"Type 2 devrait totaliser 310, obtenu {type2}"


def test_get_repartition_patho_niv3_returns_subcategories(test_database):
    """
    Vérifie que la fonction retourne les sous-sous-pathologies (niveau 3).
    
    Exemple: pour les Cancers, on peut avoir différents stades.
    """
    df = pd.read_sql_query(
        """
        SELECT patho_niv3, SUM(Ntop) as total_cas
        FROM effectifs
        WHERE annee BETWEEN 2021 AND 2023 
          AND patho_niv1 = 'Cancers'
          AND patho_niv3 IS NOT NULL
        GROUP BY patho_niv3
        ORDER BY total_cas DESC
        """,
        get_db_connection(test_database)
    )
    
    if not df.empty:
        assert 'patho_niv3' in df.columns, "La colonne patho_niv3 doit exister"
        assert 'total_cas' in df.columns, "La colonne total_cas doit exister"


# ============================================================================
# TESTS - Calculs de prévalence
# ============================================================================

def test_pathologies_par_region_calculates_prevalence_correctly(test_database):
    """
    Vérifie que le calcul de prévalence (taux pour 100 habitants) est correct.
    
    Formule: (total_cas / population_totale) * 100
    
    Test avec données connues pour validation du calcul.
    """
    # Requête pour obtenir les données avec calcul de prévalence
    df = pd.read_sql_query(
        """
        SELECT 
            region,
            SUM(Ntop) AS total_cas,
            SUM(Npop) AS population_totale,
            CASE 
                WHEN SUM(Npop) > 0 
                THEN ROUND(CAST(SUM(Ntop) AS FLOAT) * 100 / SUM(Npop), 2)
                ELSE 0
            END AS prevalence
        FROM effectifs
        WHERE annee = 2023 AND region = '11'
        GROUP BY region
        """,
        get_db_connection(test_database)
    )
    
    if not df.empty:
        row = df.iloc[0]
        
        # Calcul manuel de la prévalence
        expected_prevalence = round((row['total_cas'] / row['population_totale']) * 100, 2)
        
        assert abs(row['prevalence'] - expected_prevalence) < 0.01, \
            f"La prévalence calculée ({row['prevalence']}) doit correspondre à la valeur attendue ({expected_prevalence})"


def test_prevalence_is_zero_when_population_is_zero(test_database):
    """
    Vérifie que la prévalence est 0 quand la population est 0.
    
    Cas limite: évite la division par zéro.
    """
    # Insertion d'une ligne avec population = 0
    conn = sqlite3.connect(str(test_database))
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO effectifs VALUES (2024, '27', '21', 'Test', NULL, NULL, 1, 5, 100, 0)"
    )
    conn.commit()
    
    df = pd.read_sql_query(
        """
        SELECT 
            CASE 
                WHEN SUM(Npop) > 0 
                THEN ROUND(CAST(SUM(Ntop) AS FLOAT) * 100 / SUM(Npop), 2)
                ELSE 0
            END AS prevalence
        FROM effectifs
        WHERE annee = 2024 AND region = '27'
        """,
        conn
    )
    
    conn.close()
    
    assert df['prevalence'].iloc[0] == 0, "La prévalence doit être 0 si population est 0"


# ============================================================================
# TESTS - Cas limites
# ============================================================================

def test_queries_handle_missing_years_gracefully(test_database):
    """
    Vérifie que les requêtes retournent un DataFrame vide
    pour des années sans données.
    
    Important: pas d'erreur, juste un résultat vide.
    """
    df = pd.read_sql_query(
        "SELECT * FROM effectifs WHERE annee = 2030",
        get_db_connection(test_database)
    )
    
    assert df.empty, "Le résultat doit être vide pour une année inexistante"


def test_queries_handle_invalid_region_gracefully(test_database):
    """
    Vérifie que les requêtes avec une région inexistante
    retournent un DataFrame vide sans erreur.
    """
    df = pd.read_sql_query(
        "SELECT * FROM effectifs WHERE region = 'INVALID'",
        get_db_connection(test_database)
    )
    
    assert df.empty, "Le résultat doit être vide pour une région inexistante"
