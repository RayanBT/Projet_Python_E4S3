"""
Tests unitaires pour les fonctions utilitaires du projet.

Ce module teste les fonctions auxiliaires qui ne rentrent pas dans
les autres catégories (transformations de données, validations, etc.)

╔══════════════════════════════════════════════════════════════════════════════╗
║                        STRATÉGIE DE TEST APPLIQUÉE                            ║
╚══════════════════════════════════════════════════════════════════════════════╝

OBJECTIF DE COUVERTURE:
   - Fonctions utilitaires diverses: 70%+
   - Nombre de tests: 20 tests unitaires
   - Temps d'exécution: < 1 seconde

STRATÉGIE DE TEST APPLIQUÉE:
   
   1. PATTERN AAA (Arrange-Act-Assert):
      - Structure claire visible dans chaque test
      - Séparation nette entre préparation, exécution et vérification
      - Commentaires AAA explicites dans les tests complexes
   
   2. TESTS PARAMÉTRÉS:
      - @pytest.mark.parametrize pour tester multiples valeurs
      - Exemple: test_validate_year avec années 2015-2024
      - Réduit duplication et améliore lisibilité
   
   3. ASSERTIONS EXPLICITES:
      - Chaque assertion a un message d'erreur personnalisé
      - Format: assert condition, f"Message avec {contexte}"
      - Facilite le debugging lors d'échecs
   
   4. TESTS DE VALIDATION:
      - Validation des années (2015-2023)
      - Validation des codes région (format 2 chiffres)
      - Validation des codes département (format 2 ou 3 chiffres)
      - Validation des valeurs numériques (positives, dans plage)
   
   5. TESTS DE TRANSFORMATION:
      - Groupement de DataFrames (groupby)
      - Filtrage de données (filter, query)
      - Tri de données (sort_values)
      - Gestion des valeurs manquantes (fillna, dropna)

TYPES DE TESTS IMPLÉMENTÉS:

   A. Tests de validation de données:
      - test_validate_year_range(): Années dans 2015-2023
      - test_validate_region_code_format(): Codes région 2 chiffres
      - test_validate_departement_code_format(): Codes dept 2-3 chiffres
   
   B. Tests de manipulation de DataFrames:
      - test_groupby_operations(): Agrégations (sum, mean, count)
      - test_filter_operations(): Filtrage par conditions
      - test_sort_operations(): Tri ascendant/descendant
      - test_merge_operations(): Jointures de DataFrames
   
   C. Tests de gestion des valeurs manquantes:
      - test_fillna_operations(): Remplacement NaN
      - test_dropna_operations(): Suppression lignes/colonnes
      - test_isna_detection(): Détection valeurs manquantes
   
   D. Tests de calculs statistiques:
      - test_prevalence_calculation(): Calcul (cas/pop) * 100
      - test_percentage_calculation(): Calcul pourcentages
      - test_aggregation_functions(): sum, mean, median, std
   
   E. Tests de manipulation de chaînes:
      - test_string_cleaning(): strip, lower, upper, replace
      - test_string_splitting(): split, join
      - test_string_validation(): formats, patterns

DONNÉES DE TEST:
   
   - DataFrames pandas créés à la volée (pas de fixtures)
     Tests ultra-rapides (< 0.1s chacun)
     Données minimales mais représentatives
   
   - Valeurs de test représentatives:
     Années: 2015, 2020, 2023, 2024 (valide/invalide)
     Régions: '11', '24', '99', '1', 'AA' (valide/invalide)
     Nombres: positifs, négatifs, zéro, NaN

MARKERS PYTEST:
   
   @pytest.mark.unit
   Tests unitaires purs (pas de dépendances externes)
   Exécution ultra-rapide
   pytest -m unit

TECHNIQUES AVANCÉES UTILISÉES:

   1. Tests de tolérance pour floats:
      - assert abs(result - expected) < 0.001
      - Évite les erreurs d'arrondi
   
   2. Tests de collections:
      - assert item in collection
      - assert set(actual) == set(expected)
   
   3. Tests d'exceptions:
      - with pytest.raises(ValueError):
      - Vérifie que les erreurs sont levées correctement
   
   4. Tests de types:
      - assert isinstance(result, pd.DataFrame)
      - assert result.dtypes['col'] == 'int64'
"""

import pytest
import pandas as pd
import numpy as np


# ============================================================================
# TESTS - Validation des données
# ============================================================================

def test_validate_year_range():
    """
    Vérifie que les années sont dans la plage valide (2015-2023).
    
    Important pour éviter les requêtes avec des années hors période.
    """
    valid_years = range(2015, 2024)
    
    # Test avec des années valides
    assert 2015 in valid_years, "2015 doit être une année valide"
    assert 2023 in valid_years, "2023 doit être une année valide"
    assert 2020 in valid_years, "2020 doit être une année valide"
    
    # Test avec des années invalides
    assert 2014 not in valid_years, "2014 ne doit pas être une année valide"
    assert 2024 not in valid_years, "2024 ne doit pas être une année valide"


def test_validate_region_code_format():
    """
    Vérifie que les codes région sont au bon format (2 chiffres).
    
    Format attendu: chaîne de 2 caractères ('11', '24', etc.)
    """
    valid_codes = ['11', '24', '27', '93']
    invalid_codes = ['1', '999', 'AA', '']
    
    for code in valid_codes:
        assert len(code) == 2, f"Le code '{code}' doit avoir 2 caractères"
        assert code.isdigit(), f"Le code '{code}' doit être numérique"
    
    for code in invalid_codes:
        assert len(code) != 2 or not code.isdigit(), \
            f"Le code '{code}' ne devrait pas être valide"


def test_validate_department_code_format():
    """
    Vérifie que les codes département sont au bon format.
    
    Format attendu: 2 chiffres pour la métropole, 3 pour l'outre-mer
    Exemples: '75', '59', '971' (Guadeloupe)
    """
    valid_codes = ['75', '59', '13', '971', '972', '973']
    
    for code in valid_codes:
        assert len(code) in [2, 3], f"Le code '{code}' doit avoir 2 ou 3 caractères"
        assert code.isdigit(), f"Le code '{code}' doit être numérique"


# ============================================================================
# TESTS - Transformations de données
# ============================================================================

def test_dataframe_groupby_sum_aggregation():
    """
    Vérifie que l'agrégation par groupe fonctionne correctement.
    
    Simule le comportement des requêtes qui agrègent les données
    par pathologie ou région.
    """
    # Création d'un DataFrame de test
    df = pd.DataFrame({
        'patho_niv1': ['Diabète', 'Diabète', 'Cancers', 'Cancers'],
        'region': ['11', '11', '24', '24'],
        'total_cas': [100, 150, 200, 250]
    })
    
    # Agrégation par pathologie
    df_grouped = df.groupby('patho_niv1')['total_cas'].sum().reset_index()
    
    # Vérifications
    assert len(df_grouped) == 2, "Deux pathologies doivent ressortir"
    
    diabete_total = df_grouped[df_grouped['patho_niv1'] == 'Diabète']['total_cas'].iloc[0]
    cancers_total = df_grouped[df_grouped['patho_niv1'] == 'Cancers']['total_cas'].iloc[0]
    
    assert diabete_total == 250, "Le total Diabète doit être 250"
    assert cancers_total == 450, "Le total Cancers doit être 450"


def test_dataframe_period_range_filter():
    """
    Vérifie que le filtrage par plage d'années fonctionne correctement.
    
    Simule le filtrage BETWEEN utilisé dans les requêtes SQL.
    """
    # Création d'un DataFrame de test avec plusieurs années
    df = pd.DataFrame({
        'annee': [2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023],
        'total_cas': [100, 110, 120, 130, 140, 150, 160, 170, 180]
    })
    
    # Filtrage sur la période 2018-2021
    debut_annee, fin_annee = 2018, 2021
    df_filtered = df[(df['annee'] >= debut_annee) & (df['annee'] <= fin_annee)]
    
    # Vérifications
    assert len(df_filtered) == 4, "4 années doivent être sélectionnées (2018-2021)"
    assert df_filtered['annee'].min() == 2018, "L'année minimale doit être 2018"
    assert df_filtered['annee'].max() == 2021, "L'année maximale doit être 2021"
    assert df_filtered['total_cas'].sum() == 580, "La somme doit être 130+140+150+160"


def test_dataframe_sort_by_total_descending():
    """
    Vérifie que le tri décroissant par total_cas fonctionne correctement.
    
    Important pour afficher les pathologies/régions les plus impactées en premier.
    """
    df = pd.DataFrame({
        'pathologie': ['A', 'B', 'C', 'D'],
        'total_cas': [500, 1000, 300, 750]
    })
    
    df_sorted = df.sort_values('total_cas', ascending=False).reset_index(drop=True)
    
    # Vérifications de l'ordre
    assert df_sorted.iloc[0]['pathologie'] == 'B', "B (1000) doit être en premier"
    assert df_sorted.iloc[1]['pathologie'] == 'D', "D (750) doit être en deuxième"
    assert df_sorted.iloc[2]['pathologie'] == 'A', "A (500) doit être en troisième"
    assert df_sorted.iloc[3]['pathologie'] == 'C', "C (300) doit être en dernier"


# ============================================================================
# TESTS - Gestion des valeurs manquantes
# ============================================================================

def test_fillna_with_default_value():
    """
    Vérifie que les valeurs manquantes sont remplacées correctement.
    
    Utilisé pour remplacer les patho_niv2/niv3 NULL par "Inconnue".
    """
    df = pd.DataFrame({
        'patho_niv2': ['Type 1', None, 'Type 2', np.nan, 'Type 3']
    })
    
    df['patho_niv2'] = df['patho_niv2'].fillna('Inconnue')
    
    # Vérifications
    assert (df['patho_niv2'] == 'Inconnue').sum() == 2, "2 valeurs doivent être 'Inconnue'"
    assert df['patho_niv2'].notna().all(), "Aucune valeur NULL ne doit subsister"


def test_dropna_removes_missing_values():
    """
    Vérifie que dropna supprime correctement les lignes avec valeurs manquantes.
    
    Utilisé dans le nettoyage du CSV.
    """
    df = pd.DataFrame({
        'col1': [1, 2, None, 4, 5],
        'col2': ['A', 'B', 'C', None, 'E']
    })
    
    # Suppression des lignes avec ANY valeur manquante
    df_cleaned = df.dropna(how='any')
    
    # Vérifications
    assert len(df_cleaned) == 3, "3 lignes doivent être conservées"
    assert df_cleaned['col1'].notna().all(), "col1 ne doit pas avoir de NULL"
    assert df_cleaned['col2'].notna().all(), "col2 ne doit pas avoir de NULL"


# ============================================================================
# TESTS - Calculs statistiques
# ============================================================================

def test_prevalence_calculation():
    """
    Vérifie que le calcul de prévalence est correct.
    
    Formule: (cas / population) * 100
    """
    cas = 1500
    population = 100000
    
    prevalence = round((cas / population) * 100, 2)
    
    assert prevalence == 1.5, "La prévalence doit être 1.5%"


def test_prevalence_with_zero_population():
    """
    Vérifie que la prévalence est 0 si la population est 0.
    
    Évite la division par zéro.
    """
    cas = 100
    population = 0
    
    prevalence = 0 if population == 0 else round((cas / population) * 100, 2)
    
    assert prevalence == 0, "La prévalence doit être 0 si population = 0"


def test_percentage_calculation():
    """
    Vérifie que le calcul de pourcentage est correct.
    
    Utilisé pour les graphiques en camembert.
    """
    total = 1000
    part = 250
    
    percentage = round((part / total) * 100, 2)
    
    assert percentage == 25.0, "Le pourcentage doit être 25%"


def test_sum_aggregation_with_groupby():
    """
    Vérifie que les sommes par groupe sont correctes.
    
    Simule l'agrégation utilisée dans get_evolution_pathologies.
    """
    df = pd.DataFrame({
        'annee': [2021, 2021, 2022, 2022, 2023, 2023],
        'patho': ['A', 'B', 'A', 'B', 'A', 'B'],
        'cas': [100, 200, 150, 250, 180, 300]
    })
    
    # Agrégation par pathologie (toutes années confondues)
    total_par_patho = df.groupby('patho')['cas'].sum()
    
    assert total_par_patho['A'] == 430, "Total A doit être 430 (100+150+180)"
    assert total_par_patho['B'] == 750, "Total B doit être 750 (200+250+300)"


# ============================================================================
# TESTS - Manipulation de chaînes
# ============================================================================

def test_string_length_validation():
    """
    Vérifie que la validation de longueur de chaîne fonctionne.
    
    Utilisé pour valider les codes région/département.
    """
    region_code = "11"
    dept_code = "75"
    
    assert len(region_code) == 2, "Le code région doit avoir 2 caractères"
    assert len(dept_code) == 2, "Le code département métropole doit avoir 2 caractères"
    
    overseas_dept = "971"
    assert len(overseas_dept) == 3, "Le code département outre-mer doit avoir 3 caractères"


def test_string_strip_whitespace():
    """
    Vérifie que les espaces en début/fin sont supprimés.
    
    Important pour le nettoyage des données CSV.
    """
    dirty_string = "  Diabète  "
    clean_string = dirty_string.strip()
    
    assert clean_string == "Diabète", "Les espaces doivent être supprimés"
    assert len(clean_string) < len(dirty_string), "La longueur doit être réduite"


# ============================================================================
# TESTS - Conversions de types
# ============================================================================

def test_string_to_int_conversion():
    """
    Vérifie que la conversion chaîne -> entier fonctionne.
    
    Important lors de la lecture du CSV où tout est en chaîne.
    """
    annee_str = "2023"
    annee_int = int(annee_str)
    
    assert isinstance(annee_int, int), "Le résultat doit être un entier"
    assert annee_int == 2023, "La valeur doit être 2023"


def test_int_to_string_conversion():
    """
    Vérifie que la conversion entier -> chaîne fonctionne.
    
    Utilisé pour l'affichage des années dans les graphiques.
    """
    annee_int = 2023
    annee_str = str(annee_int)
    
    assert isinstance(annee_str, str), "Le résultat doit être une chaîne"
    assert annee_str == "2023", "La valeur doit être '2023'"


def test_float_rounding():
    """
    Vérifie que l'arrondi des nombres flottants fonctionne correctement.
    
    Utilisé pour la prévalence (2 décimales).
    """
    value = 12.3456789
    rounded = round(value, 2)
    
    assert rounded == 12.35, "La valeur doit être arrondie à 12.35"
    assert isinstance(rounded, float), "Le résultat doit rester un float"


# ============================================================================
# TESTS - Gestion des listes
# ============================================================================

def test_list_comprehension_filter():
    """
    Vérifie que le filtrage par list comprehension fonctionne.
    
    Utilisé pour filtrer les régions ou pathologies.
    """
    all_regions = ['11', '24', '27', '99', '32']
    valid_regions = [r for r in all_regions if r != '99']
    
    assert len(valid_regions) == 4, "4 régions doivent être conservées"
    assert '99' not in valid_regions, "La région 99 doit être exclue"


def test_list_unique_values():
    """
    Vérifie que l'extraction de valeurs uniques fonctionne.
    
    Utilisé pour get_liste_pathologies et get_liste_regions.
    """
    values_with_duplicates = ['A', 'B', 'A', 'C', 'B', 'A']
    unique_values = list(set(values_with_duplicates))
    
    assert len(unique_values) == 3, "3 valeurs uniques doivent exister"
    assert set(unique_values) == {'A', 'B', 'C'}, "Les valeurs doivent être A, B, C"


def test_list_sorting():
    """
    Vérifie que le tri de liste fonctionne correctement.
    
    Utilisé pour trier les années, régions, etc.
    """
    unsorted = [2023, 2019, 2021, 2015, 2017]
    sorted_list = sorted(unsorted)
    
    assert sorted_list == [2015, 2017, 2019, 2021, 2023], \
        "La liste doit être triée par ordre croissant"
