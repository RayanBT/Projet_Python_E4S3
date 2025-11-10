"""Schemas Pydantic utilises pour valider les donnees d'effectifs."""

from typing import Any

from pydantic import BaseModel, Field, field_validator
from pydantic.config import ConfigDict


class EffectifBase(BaseModel):
    """Modele de base partage par les schemas d'entree et de sortie.

    Attributs:
        annee: Annee de reference des donnees.
        patho_niv1: Pathologie niveau 1 (categorie principale).
        patho_niv2: Pathologie niveau 2 (sous-categorie).
        patho_niv3: Pathologie niveau 3 (detail specifique).
        top: Indicateur top pathologie.
        cla_age_5: Classe d'age par tranche de 5 ans.
        sexe: Code sexe (1=homme, 2=femme).
        region: Code region.
        dept: Code departement.
        ntop: Nombre de cas top pathologie.
        npop: Population de reference.
        prev: Taux de prevalence.
        niveau_prioritaire: Niveau de priorite de la pathologie.
        libelle_classe_age: Libelle de la classe d'age.
        libelle_sexe: Libelle du sexe.
        tri: Valeur de tri.
    """

    annee: int | None = None
    patho_niv1: str | None = None
    patho_niv2: str | None = None
    patho_niv3: str | None = None
    top: str | None = None
    cla_age_5: str | None = None
    sexe: int | None = None
    region: str | None = None
    dept: str | None = None
    Ntop: int | None = None
    Npop: int | None = None
    prev: str | None = None
    niveau_prioritaire: str | None = Field(None, alias="Niveau prioritaire")
    libelle_classe_age: str | None = None
    libelle_sexe: str | None = None
    tri: float | None = None

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    @field_validator("annee", "sexe", "Ntop", "Npop", "tri", mode="before")
    @classmethod
    def empty_string_to_none(cls, value: Any) -> Any:
        """Convertit les chaines vides en None pour faciliter le typage numerique.

        Args:
            value: Valeur issue du CSV.

        Returns:
            Valeur nettoyee (None si chaine vide, valeur originale sinon).
        """
        if isinstance(value, str) and value.strip() == "":
            return None
        return value


class EffectifCreate(EffectifBase):
    """Schema d'entree pour la creation d'une ligne d'effectifs."""


class EffectifOut(EffectifBase):
    """Schema de sortie expose par l'API.

    Attributs:
        id: Identifiant unique de l'enregistrement.
    """

    id: int


def as_pydantic_models() -> tuple[type[EffectifCreate], type[EffectifOut]]:
    """Retourne les schemas utilises par le code historique.

    Returns:
        Tuple contenant les classes EffectifCreate et EffectifOut.
    """
    return EffectifCreate, EffectifOut


__all__ = ["EffectifCreate", "EffectifOut", "as_pydantic_models"]
