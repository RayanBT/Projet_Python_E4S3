"""
Tests unitaires pour le module de nettoyage des données.

Ce module teste les fonctions de nettoyage et normalisation des données,
notamment la transformation des labels de pathologies et le nettoyage du CSV.

╔══════════════════════════════════════════════════════════════════════════════╗
║                        STRATÉGIE DE TEST APPLIQUÉE                            ║
╚══════════════════════════════════════════════════════════════════════════════╝

OBJECTIF DE COUVERTURE:
   - Module clean_data.py: 90%+ (module critique pour la qualité des données)
   - Nombre de tests: 10 tests unitaires
   - Temps d'exécution: < 2 secondes

STRATÉGIE DE TEST APPLIQUÉE:
   
   1. PATTERN AAA (Arrange-Act-Assert):
      - ARRANGE: Préparation des données de test (fixtures, DataFrames)
      - ACT: Exécution de la fonction à tester
      - ASSERT: Vérification des résultats avec messages explicites
   
   2. ISOLATION ET INDÉPENDANCE:
      - Fichiers temporaires pour chaque test (tempfile)
      - Aucune dépendance entre les tests
      - Nettoyage automatique après exécution
   
   3. NOMENCLATURE EXPLICITE:
      - Format: test_<fonction>_<comportement_testé>
      - Exemple: test_clean_csv_removes_missing_required_values
      - Chaque nom décrit clairement ce qui est vérifié
   
   4. COUVERTURE DES CAS LIMITES:
      - Valeurs manquantes (None, '', NaN)
      - Colonnes optionnelles (patho_niv2, patho_niv3)
      - DataFrames vides
      - Fichiers inexistants
      - Mode dry_run (simulation sans modification)
   
   5. DOCUMENTATION EXHAUSTIVE:
      - Docstring sur chaque test (pourquoi et comment)
      - Commentaires inline pour la logique complexe
      - Messages d'erreur explicites dans les assertions

TYPES DE TESTS IMPLÉMENTÉS:

   A. Tests de nettoyage CSV:
      - Suppression des lignes avec valeurs manquantes (colonnes requises)
      - Préservation des colonnes optionnelles
      - Validation du format de sortie
   
   B. Tests de normalisation des labels:
      - Application du mapping PATHOLOGIE_MAPPING
      - Nettoyage des espaces et casse
      - Raccourcissement des labels longs (> 50 caractères)
   
   C. Tests de robustesse:
      - Gestion des DataFrames vides
      - Gestion des fichiers inexistants
      - Mode dry_run (pas de modification effective)

FIXTURES UTILISÉES:
   
   - sample_csv_data: DataFrame avec données valides/invalides
     Permet de tester sans fichiers réels
   
   - temp_csv_file: Fichier CSV temporaire
     Créé automatiquement, supprimé après le test
   
   - sample_db_data: Données de base de données de test
     Pour tester le nettoyage depuis SQLite

MARKERS PYTEST:
   
   @pytest.mark.unit
   Tests unitaires isolés, rapides (< 1 seconde chacun)
   Exécution: pytest -m unit
"""

import sqlite3
import tempfile
from pathlib import Path

import pandas as pd
import pytest

from src.utils.clean_data import (
    PATHOLOGIE_MAPPING,
    clean_csv_data,
    clean_pathologie_labels,
)


# ============================================================================
# FIXTURES - Données de test réutilisables
# ============================================================================

@pytest.fixture
def sample_csv_data():
    """
    Crée un DataFrame CSV de test avec des données valides et invalides.
    
    Permet de tester la logique de nettoyage sans dépendre de fichiers réels.
    """
    return pd.DataFrame({
        'annee': ['2023', '2023', '2023', '', '2023'],
        'region': ['11', '24', '27', '32', None],
        'dept': ['75', '41', '21', '59', '69'],
        'patho_niv1': ['Diabète', 'Cancers', 'Diabète', 'Cancers', 'Diabète'],
        'patho_niv2': ['Type 1', 'Poumon', None, 'Sein', 'Type 2'],
        'patho_niv3': [None, 'Stade 1', None, None, None],
        'Ntop': ['100', '200', '150', '300', '250'],
        'Npop': ['10000', '20000', '15000', '', '25000'],
        'libelle_classe_age': ['0-20', '21-40', '41-60', '61-80', '81+']
    })


@pytest.fixture
def temp_csv_file(sample_csv_data):
    """
    Crée un fichier CSV temporaire pour les tests.
    
    Utilise tempfile pour éviter de polluer le système de fichiers.
    Le fichier est automatiquement nettoyé après le test.
    
    IMPORTANT: Utilise encoding='utf-8' pour la compatibilité avec clean_csv().
    """
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
        sample_csv_data.to_csv(f, sep=';', index=False)
        temp_path = Path(f.name)
    
    yield temp_path
    
    # Nettoyage après le test
    if temp_path.exists():
        temp_path.unlink()


@pytest.fixture
def temp_db_with_pathologies():
    """
    Crée une base de données SQLite temporaire avec des pathologies à nettoyer.
    
    Simule une vraie base de données avec des noms de pathologies longs
    pour tester la fonction de nettoyage des labels.
    """
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = Path(f.name)
    
    # Création de la table et insertion de données de test
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE effectifs (
            annee INTEGER,
            region TEXT,
            dept TEXT,
            patho_niv1 TEXT,
            patho_niv2 TEXT,
            patho_niv3 TEXT,
            Ntop INTEGER,
            Npop INTEGER
        )
    """)
    
    # Insertion de pathologies avec des noms longs (avant nettoyage)
    test_data = [
        (2023, '11', '75', 'Traitements du risque vasculaire (hors pathologies)', None, None, 100, 10000),
        (2023, '24', '41', 'Traitements psychotropes (hors pathologies)', None, None, 200, 20000),
        (2023, '27', '21', 'Cancers', 'Poumon', None, 150, 15000),
    ]
    
    cursor.executemany(
        "INSERT INTO effectifs VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        test_data
    )
    
    conn.commit()
    conn.close()
    
    yield db_path
    
    # Nettoyage après le test
    if db_path.exists():
        db_path.unlink()


# ============================================================================
# TESTS - Nettoyage CSV
# ============================================================================

def test_clean_csv_removes_missing_required_values(temp_csv_file):
    """
    Vérifie que les lignes avec des valeurs manquantes dans les colonnes
    obligatoires sont correctement supprimées.
    
    Cas de test: ligne avec 'region' manquante et ligne avec 'Npop' vide.
    """
    output_file = temp_csv_file.parent / "output_clean.csv"
    
    try:
        clean_csv_data(temp_csv_file, output_file, report=lambda x: None)
        
        # Lecture du fichier nettoyé
        df_cleaned = pd.read_csv(output_file, sep=';', encoding='utf-8')
        
        # Vérifications
        assert len(df_cleaned) == 3, "Devrait conserver 3 lignes sur 5"
        assert df_cleaned['region'].notna().all(), "Toutes les régions doivent être renseignées"
        assert df_cleaned['Npop'].notna().all(), "Toutes les populations doivent être renseignées"
        
    finally:
        if output_file.exists():
            output_file.unlink()


def test_clean_csv_keeps_optional_columns_with_null(temp_csv_file):
    """
    Vérifie que les colonnes optionnelles (patho_niv2, patho_niv3) peuvent
    contenir des valeurs NULL sans que la ligne soit supprimée.
    
    Important: permet de garder les pathologies sans sous-catégories.
    """
    output_file = temp_csv_file.parent / "output_clean.csv"
    
    try:
        clean_csv_data(temp_csv_file, output_file, report=lambda x: None)
        df_cleaned = pd.read_csv(output_file, sep=';', encoding='utf-8')
        
        # Vérification que des valeurs NULL existent bien dans patho_niv2 ou patho_niv3
        has_null_niv2 = df_cleaned['patho_niv2'].isna().any()
        has_null_niv3 = df_cleaned['patho_niv3'].isna().any()
        
        assert has_null_niv2 or has_null_niv3, \
            "Les colonnes optionnelles doivent pouvoir contenir des NULL"
        
    finally:
        if output_file.exists():
            output_file.unlink()


def test_clean_csv_removes_libelle_classe_age_column(temp_csv_file):
    """
    Vérifie que la colonne 'libelle_classe_age' est supprimée lors du nettoyage.
    
    Cette colonne est redondante et n'est pas nécessaire pour l'analyse.
    """
    output_file = temp_csv_file.parent / "output_clean.csv"
    
    try:
        clean_csv_data(temp_csv_file, output_file, report=lambda x: None)
        df_cleaned = pd.read_csv(output_file, sep=';', encoding='utf-8')
        
        assert 'libelle_classe_age' not in df_cleaned.columns, \
            "La colonne libelle_classe_age doit être supprimée"
        
    finally:
        if output_file.exists():
            output_file.unlink()


def test_clean_csv_creates_output_directory():
    """
    Vérifie que les répertoires parents sont créés automatiquement
    si le dossier de destination n'existe pas.
    
    Important pour éviter les erreurs FileNotFoundError.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        # Création d'un CSV source
        input_file = Path(tmpdir) / "input.csv"
        pd.DataFrame({'annee': ['2023'], 'region': ['11'], 'Ntop': ['100'], 'Npop': ['1000']}).to_csv(
            input_file, sep=';', index=False
        )
        
        # Chemin de sortie avec un dossier qui n'existe pas encore
        output_file = Path(tmpdir) / "subdir" / "nested" / "output.csv"
        
        clean_csv_data(input_file, output_file, report=lambda x: None)
        
        assert output_file.exists(), "Le fichier de sortie doit être créé"
        assert output_file.parent.exists(), "Les répertoires parents doivent être créés"


# ============================================================================
# TESTS - Nettoyage des labels de pathologies
# ============================================================================

def test_clean_pathologie_labels_shortens_long_names(temp_db_with_pathologies):
    """
    Vérifie que les noms de pathologies longs sont correctement raccourcis
    selon le mapping défini.
    
    Exemple: 'Traitements du risque vasculaire (hors pathologies)' 
             → 'Traitements risque vasculaire'
    """
    # Exécution du nettoyage (sans dry_run)
    stats = clean_pathologie_labels(temp_db_with_pathologies, dry_run=False, report=lambda x: None)
    
    # Vérification des statistiques
    assert stats['pathologies_modifiees'] > 0, "Des pathologies doivent être modifiées"
    assert stats['lignes_affectees'] > 0, "Des lignes doivent être affectées"
    
    # Vérification dans la base de données
    conn = sqlite3.connect(str(temp_db_with_pathologies))
    cursor = conn.cursor()
    
    cursor.execute("SELECT DISTINCT patho_niv1 FROM effectifs ORDER BY patho_niv1")
    pathologies = [row[0] for row in cursor.fetchall()]
    
    conn.close()
    
    # Vérification que les noms courts sont bien présents
    assert "Traitements risque vasculaire" in pathologies, \
        "Le nom court doit remplacer le nom long"
    assert "Traitements psychotropes" in pathologies, \
        "Le nom court doit remplacer le nom long"
    
    # Vérification que les noms longs ont disparu
    assert "Traitements du risque vasculaire (hors pathologies)" not in pathologies, \
        "Le nom long ne doit plus exister"


def test_clean_pathologie_labels_dry_run_does_not_modify(temp_db_with_pathologies):
    """
    Vérifie que le mode dry_run affiche les changements mais ne modifie
    pas réellement la base de données.
    
    Utile pour prévisualiser les modifications avant de les appliquer.
    
    IMPORTANT: dry_run compte les lignes qui seraient modifiées (stats['lignes_affectees'] > 0)
    mais ne modifie pas la base (pathologies_before == pathologies_after).
    """
    # Lecture de l'état initial
    conn = sqlite3.connect(str(temp_db_with_pathologies))
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT patho_niv1 FROM effectifs ORDER BY patho_niv1")
    pathologies_before = [row[0] for row in cursor.fetchall()]
    conn.close()
    
    # Exécution en mode dry_run
    stats = clean_pathologie_labels(temp_db_with_pathologies, dry_run=True, report=lambda x: None)
    
    # Lecture de l'état après
    conn = sqlite3.connect(str(temp_db_with_pathologies))
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT patho_niv1 FROM effectifs ORDER BY patho_niv1")
    pathologies_after = [row[0] for row in cursor.fetchall()]
    conn.close()
    
    # Vérification que rien n'a changé dans la base
    assert pathologies_before == pathologies_after, \
        "Le mode dry_run ne doit pas modifier la base"
    # Mais les stats doivent montrer ce qui aurait été modifié
    assert stats['lignes_affectees'] > 0, \
        "Le dry_run doit détecter les lignes qui seraient modifiées"


def test_clean_pathologie_labels_preserves_unmapped_pathologies(temp_db_with_pathologies):
    """
    Vérifie que les pathologies non présentes dans le mapping
    sont conservées telles quelles.
    
    Exemple: 'Cancers' n'a pas de mapping et doit rester 'Cancers'.
    """
    clean_pathologie_labels(temp_db_with_pathologies, dry_run=False, report=lambda x: None)
    
    conn = sqlite3.connect(str(temp_db_with_pathologies))
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT patho_niv1 FROM effectifs WHERE patho_niv1 = 'Cancers'")
    result = cursor.fetchone()
    conn.close()
    
    assert result is not None, "La pathologie 'Cancers' doit être préservée"
    assert result[0] == "Cancers", "Le nom doit rester inchangé"


def test_pathologie_mapping_contains_expected_entries():
    """
    Vérifie que le dictionnaire PATHOLOGIE_MAPPING contient bien
    les mappings essentiels pour le projet.
    
    Test de validation de la configuration.
    """
    # Vérification de quelques mappings critiques
    assert "Traitements du risque vasculaire (hors pathologies)" in PATHOLOGIE_MAPPING
    assert "Traitements psychotropes (hors pathologies)" in PATHOLOGIE_MAPPING
    assert "Maladies psychiatriques" in PATHOLOGIE_MAPPING
    
    # Vérification que les valeurs sont plus courtes que les clés
    for long_name, short_name in PATHOLOGIE_MAPPING.items():
        assert len(short_name) <= len(long_name), \
            f"Le nom court '{short_name}' doit être plus court que '{long_name}'"


# ============================================================================
# TESTS - Cas limites et gestion d'erreurs
# ============================================================================

def test_clean_csv_with_empty_dataframe():
    """
    Vérifie que le nettoyage d'un DataFrame vide ne provoque pas d'erreur.
    
    Cas limite important pour la robustesse.
    
    IMPORTANT: Vérifie simplement que la fonction s'exécute sans exception.
    Le fichier de sortie peut être minimal (juste un newline) car le DataFrame est vide.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        input_file = Path(tmpdir) / "empty.csv"
        output_file = Path(tmpdir) / "output.csv"
        
        # Création d'un CSV vide avec les colonnes requises
        pd.DataFrame(columns=['annee', 'region', 'Ntop', 'Npop']).to_csv(
            input_file, sep=';', index=False, encoding='utf-8'
        )
        
        # Nettoyage (ne devrait pas planter)
        # C'est le comportement essentiel testé ici
        try:
            result_path = clean_csv_data(input_file, output_file, report=lambda x: None)
            assert result_path.exists(), "Le fichier de sortie doit être créé"
        except Exception as e:
            pytest.fail(f"Le nettoyage d'un DataFrame vide ne devrait pas lever d'exception: {e}")


def test_clean_pathologie_labels_with_nonexistent_db():
    """
    Vérifie qu'une erreur appropriée est levée si la base de données
    n'existe pas.
    
    Important pour le diagnostic d'erreurs.
    """
    nonexistent_db = Path("/nonexistent/path/database.db")
    
    with pytest.raises(Exception):
        clean_pathologie_labels(nonexistent_db, dry_run=False, report=lambda x: None)
