"""Utilitaires pour la correspondance departement <-> region."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import TypedDict


class DepartementInfo(TypedDict):
    """Information sur un departement."""

    num_dep: str
    dep_name: str
    region_name: str


@lru_cache(maxsize=1)
def load_departements_regions() -> list[DepartementInfo]:
    """Charge le JSON des departements et regions.

    Returns:
        list[DepartementInfo]: Liste des informations departements-regions.

    Raises:
        FileNotFoundError: Si le fichier n'existe pas.
        json.JSONDecodeError: Si le fichier n'est pas un JSON valide.
    """
    json_path = (
        Path(__file__).resolve().parents[2]
        / "data"
        / "geolocalisation"
        / "departements-regions.json"
    )

    if not json_path.exists():
        raise FileNotFoundError(
            f"Le fichier {json_path} n'existe pas. "
            "Lancez l'initialisation avec main.py pour le télécharger."
        )

    with json_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    return data  # type: ignore[no-any-return]


@lru_cache(maxsize=1)
def get_dept_to_region_mapping() -> dict[str, str]:
    """Construit un dictionnaire num_dep -> region_name.

    Returns:
        dict[str, str]: Mapping code departement -> nom region.
    """
    data = load_departements_regions()
    # Normaliser les codes departement en string avec 2 chiffres (01, 02, etc.)
    mapping = {}
    for item in data:
        num_dep = item["num_dep"]
        # Convertir en string et padding si necessaire
        if isinstance(num_dep, int):
            num_dep = str(num_dep).zfill(2)
        else:
            num_dep = str(num_dep)
        mapping[num_dep] = item["region_name"]
    return mapping


@lru_cache(maxsize=1)
def get_region_departments() -> dict[str, list[str]]:
    """Construit un dictionnaire region_name -> [num_dep, ...].

    Returns:
        dict[str, list[str]]: Mapping nom region -> liste codes departements.
    """
    data = load_departements_regions()
    result: dict[str, list[str]] = {}

    for item in data:
        region = item["region_name"]
        num_dep = item["num_dep"]
        # Normaliser le code departement
        if isinstance(num_dep, int):
            num_dep = str(num_dep).zfill(2)
        else:
            num_dep = str(num_dep)

        if region not in result:
            result[region] = []
        result[region].append(num_dep)

    return result


@lru_cache(maxsize=1)
def get_all_regions() -> list[str]:
    """Retourne la liste de toutes les regions.

    Returns:
        list[str]: Liste des noms de regions.
    """
    data = load_departements_regions()
    regions = sorted(set(item["region_name"] for item in data))
    return regions


@lru_cache(maxsize=1)
def get_all_departements() -> list[DepartementInfo]:
    """Retourne la liste de tous les departements avec leurs infos.

    Returns:
        list[DepartementInfo]: Liste des departements avec code, nom et region.
    """
    return load_departements_regions()
