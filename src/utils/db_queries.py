"""Fonctions utilitaires pour interroger la base SQLite."""

from __future__ import annotations

from pathlib import Path
from typing import Optional, List

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

import config


def get_db_connection(db_path: Path = config.DB_PATH) -> Engine:
    """Cree une connexion a la base de donnees SQLite."""
    return create_engine(f"sqlite:///{db_path}")


def get_pathologies_par_region(
    annee: int = 2023,
    pathologie: Optional[str] = None,
) -> pd.DataFrame:
    """Retourne les totaux et la prevalence par region pour une annee donnee."""
    engine = get_db_connection()
    query = text(
        """
        SELECT 
            region,
            SUM(Ntop) AS total_cas,
            SUM(Npop) AS population_totale,
            CASE 
                WHEN SUM(Npop) > 0 THEN ROUND(CAST(SUM(Ntop) AS FLOAT) * 100 / SUM(Npop), 2)
                ELSE 0
            END AS prevalence
        FROM effectifs
        WHERE annee = :annee
          AND region != '99'
          AND (:pathologie IS NULL OR patho_niv1 = :pathologie)
        GROUP BY region
        ORDER BY total_cas DESC
        """
    )
    return pd.read_sql_query(
        query,
        engine,
        params={"annee": annee, "pathologie": pathologie},  # type: ignore[arg-type]
    )


def get_pathologies_par_departement(
    annee: int = 2023,
    pathologie: Optional[str] = None,
) -> pd.DataFrame:
    """Retourne les totaux et la prevalence par departement pour une annee donnee."""
    engine = get_db_connection()
    query = text(
        """
        SELECT 
            dept,
            SUM(Ntop) AS total_cas,
            SUM(Npop) AS population_totale,
            CASE 
                WHEN SUM(Npop) > 0 THEN ROUND(CAST(SUM(Ntop) AS FLOAT) * 100 / SUM(Npop), 2)
                ELSE 0
            END AS prevalence
        FROM effectifs
        WHERE annee = :annee
          AND dept IS NOT NULL
          AND dept != '99'
          AND (:pathologie IS NULL OR patho_niv1 = :pathologie)
        GROUP BY dept
        ORDER BY total_cas DESC
        """
    )
    return pd.read_sql_query(
        query,
        engine,
        params={"annee": annee, "pathologie": pathologie},  # type: ignore[arg-type]
    )


def get_evolution_pathologies(
    debut_annee: int = 2015,
    fin_annee: int = 2023,
    pathologie: Optional[str] = None,
    region: Optional[str] = None,
) -> pd.DataFrame:
    """Retourne l'evolution des pathologies principales sur la periode donnee.
    
    Args:
        debut_annee: Année de début de la période
        fin_annee: Année de fin de la période
        pathologie: Pathologie spécifique à filtrer (optionnel)
        region: Région spécifique à filtrer (optionnel)
        
    Returns:
        DataFrame avec les colonnes: annee, patho_niv1, total_cas
    """
    engine = get_db_connection()
    query = text(
        """
        SELECT 
            annee,
            patho_niv1,
            SUM(Ntop) AS total_cas
        FROM effectifs
        WHERE annee BETWEEN :debut AND :fin
          AND (:pathologie IS NULL OR patho_niv1 = :pathologie)
          AND (:region IS NULL OR region = :region)
        GROUP BY annee, patho_niv1
        ORDER BY annee, total_cas DESC
        """
    )

    return pd.read_sql_query(
        query,
        engine,
        params={
            "debut": debut_annee,
            "fin": fin_annee,
            "pathologie": pathologie,
            "region": region,
        },  # type: ignore[arg-type]
    )


def get_repartition_age_sexe(
    annee: int = 2023,
    pathologie: Optional[str] = None,
) -> pd.DataFrame:
    """Retourne la repartition par age et sexe pour la pathologie eventuelle."""
    engine = get_db_connection()
    query = text(
        """
        SELECT 
            cla_age_5,
            libelle_sexe,
            SUM(Ntop) AS total_cas
        FROM effectifs
        WHERE annee = :annee
          AND (:patho IS NULL OR patho_niv1 = :patho)
        GROUP BY cla_age_5, libelle_sexe
        ORDER BY cla_age_5, libelle_sexe
        """
    )

    return pd.read_sql_query(
        query,
        engine,
        params={
            "annee": annee,
            "patho": pathologie,
        },  # type: ignore[arg-type]
    )


def get_liste_pathologies() -> list[str]:
    """Retourne la liste des pathologies principales disponibles."""
    engine = get_db_connection()
    query = text(
        """
        SELECT DISTINCT patho_niv1
        FROM effectifs
        ORDER BY patho_niv1
        """
    )

    return pd.read_sql_query(query, engine)["patho_niv1"].tolist()


def get_repartition_patho_niv2(debut_annee: int = 2015, fin_annee: int = 2023, pathologie: Optional[str] = None) -> pd.DataFrame:
    """Retourne la répartition des sous-pathologies (patho_niv2) pour une patho_niv1 donnée sur une période.

    Si pathologie est None, retourne une table vide.
    """
    if not pathologie:
        return pd.DataFrame(columns=["patho_niv2", "total_cas"])

    engine = get_db_connection()
    query = text(
        """
        SELECT
            patho_niv2,
            SUM(Ntop) AS total_cas
        FROM effectifs
        WHERE annee BETWEEN :debut_annee AND :fin_annee
          AND (:patho IS NULL OR patho_niv1 = :patho)
        GROUP BY patho_niv2
        ORDER BY total_cas DESC
        """
    )
    return pd.read_sql_query(
        query,
        engine,
        params={"debut_annee": debut_annee, "fin_annee": fin_annee, "patho": pathologie},
    )


def get_pathologies_with_niv2() -> List[str]:
    """Retourne la liste des patho_niv1 qui ont au moins une patho_niv2 renseignée."""
    engine = get_db_connection()
    query = text(
        """
        SELECT DISTINCT patho_niv1
        FROM effectifs
        WHERE patho_niv2 IS NOT NULL
          AND TRIM(patho_niv2) != ''
        ORDER BY patho_niv1
        """
    )
    return pd.read_sql_query(query, engine)["patho_niv1"].tolist()


def get_repartition_patho_niv3(debut_annee: int = 2015, fin_annee: int = 2023, pathologie: Optional[str] = None) -> pd.DataFrame:
    """Retourne la répartition des sous-pathologies (patho_niv3) pour une patho_niv1 donnée sur une période.

    Si pathologie est None, retourne une table vide.
    """
    if not pathologie:
        return pd.DataFrame(columns=["patho_niv3", "total_cas"])

    engine = get_db_connection()
    query = text(
        """
        SELECT
            patho_niv3,
            SUM(Ntop) AS total_cas
        FROM effectifs
        WHERE annee BETWEEN :debut_annee AND :fin_annee
          AND (:patho IS NULL OR patho_niv1 = :patho)
        GROUP BY patho_niv3
        ORDER BY total_cas DESC
        """
    )
    return pd.read_sql_query(
        query,
        engine,
        params={"debut_annee": debut_annee, "fin_annee": fin_annee, "patho": pathologie},
    )


def get_distribution_age(
    annee: int = 2023,
    pathologie: Optional[str] = None,
    region: Optional[str] = None,
    sexe: Optional[int] = None,
) -> pd.DataFrame:
    """Retourne la distribution des cas par tranche d'âge."""
    engine = get_db_connection()
    query = text(
        """
        SELECT 
            cla_age_5,
            SUM(Ntop) AS nombre_cas
        FROM effectifs
        WHERE annee = :annee
          AND cla_age_5 != 'tsage'
          AND (:pathologie IS NULL OR patho_niv1 = :pathologie)
          AND (:region IS NULL OR region = :region)
          AND (:sexe IS NULL OR sexe = :sexe)
        GROUP BY cla_age_5
        ORDER BY cla_age_5
        """
    )
    return pd.read_sql_query(
        query,
        engine,
        params={
            "annee": annee,
            "pathologie": pathologie,
            "region": region,
            "sexe": sexe,
        },  # type: ignore[arg-type]
    )


def get_distribution_prevalence(
    annee: int = 2023,
    pathologie: Optional[str] = None,
    region: Optional[str] = None,
    sexe: Optional[int] = None,
) -> pd.DataFrame:
    """Retourne la distribution de la prévalence (variable continue)."""
    engine = get_db_connection()
    query = text(
        """
        SELECT 
            prev as prevalence
        FROM effectifs
        WHERE annee = :annee
          AND prev IS NOT NULL
          AND prev > 0
          AND (:pathologie IS NULL OR patho_niv1 = :pathologie)
          AND (:region IS NULL OR region = :region)
          AND (:sexe IS NULL OR sexe = :sexe)
        """
    )
    return pd.read_sql_query(
        query,
        engine,
        params={
            "annee": annee,
            "pathologie": pathologie,
            "region": region,
            "sexe": sexe,
        },  # type: ignore[arg-type]
    )


def get_distribution_nombre_cas(
    annee: int = 2023,
    pathologie: Optional[str] = None,
    region: Optional[str] = None,
    sexe: Optional[int] = None,
) -> pd.DataFrame:
    """Retourne la distribution du nombre de cas (variable continue)."""
    engine = get_db_connection()
    query = text(
        """
        SELECT 
            Ntop as nombre_cas
        FROM effectifs
        WHERE annee = :annee
          AND Ntop IS NOT NULL
          AND Ntop > 0
          AND (:pathologie IS NULL OR patho_niv1 = :pathologie)
          AND (:region IS NULL OR region = :region)
          AND (:sexe IS NULL OR sexe = :sexe)
        """
    )
    return pd.read_sql_query(
        query,
        engine,
        params={
            "annee": annee,
            "pathologie": pathologie,
            "region": region,
            "sexe": sexe,
        },  # type: ignore[arg-type]
    )


def get_distribution_population(
    annee: int = 2023,
    pathologie: Optional[str] = None,
    region: Optional[str] = None,
    sexe: Optional[int] = None,
) -> pd.DataFrame:
    """Retourne la distribution de la population (variable continue)."""
    engine = get_db_connection()
    query = text(
        """
        SELECT 
            Npop as population
        FROM effectifs
        WHERE annee = :annee
          AND Npop IS NOT NULL
          AND Npop > 0
          AND (:pathologie IS NULL OR patho_niv1 = :pathologie)
          AND (:region IS NULL OR region = :region)
          AND (:sexe IS NULL OR sexe = :sexe)
        """
    )
    return pd.read_sql_query(
        query,
        engine,
        params={
            "annee": annee,
            "pathologie": pathologie,
            "region": region,
            "sexe": sexe,
        },  # type: ignore[arg-type]
    )


def get_liste_regions() -> list[str]:
    """Retourne la liste des régions disponibles."""
    engine = get_db_connection()
    query = text(
        """
        SELECT DISTINCT region
        FROM effectifs
        WHERE region != '99'
        ORDER BY region
        """
    )
    return pd.read_sql_query(query, engine)["region"].tolist()


def get_annees_disponibles() -> list[int]:
    """Retourne la liste des années disponibles dans la base."""
    engine = get_db_connection()
    query = text(
        """
        SELECT DISTINCT annee
        FROM effectifs
        ORDER BY annee DESC
        """
    )
    return pd.read_sql_query(query, engine)["annee"].tolist()



def get_repartition_gravite(
    debut_annee: int = 2015,
    fin_annee: int = 2023,
    region: Optional[str] = None,
    pathologie: Optional[str] = None
) -> pd.DataFrame:
    """
    Retourne la répartition par niveau de gravité (Niveau prioritaire).
    
    Args:
        debut_annee: Année de début pour le filtre
        fin_annee: Année de fin pour le filtre
        region: Code région optionnel (None = toutes régions)
        pathologie: Pathologie niveau 1 optionnelle (None = toutes pathologies)
    
    Returns:
        DataFrame avec colonnes: Niveau_prioritaire, total_cas
    """
    engine = get_db_connection()
    
    # Construction de la requête
    conditions = [
        "annee BETWEEN :debut_annee AND :fin_annee",
        "cla_age_5 = 'tsage'",
        "\"Niveau prioritaire\" IS NOT NULL"
    ]
    
    params = {"debut_annee": debut_annee, "fin_annee": fin_annee}
    
    if region and region != 'Toutes':
        conditions.append("region = :region")
        params["region"] = region
    
    if pathologie and pathologie != 'Toutes':
        conditions.append("patho_niv1 = :pathologie")
        params["pathologie"] = pathologie
    
    where_clause = " AND ".join(conditions)
    
    query = text(
        f"""
        SELECT 
            "Niveau prioritaire" AS Niveau_prioritaire,
            SUM(Ntop) AS total_cas
        FROM effectifs
        WHERE {where_clause}
        GROUP BY "Niveau prioritaire"
        ORDER BY "Niveau prioritaire"
        """
    )
    
    return pd.read_sql_query(query, engine, params=params)