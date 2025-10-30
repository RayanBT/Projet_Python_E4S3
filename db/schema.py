"""Schemas Pydantic utilises pour valider les donnees d'effectifs."""

from pydantic import BaseModel, Field, field_validator
from pydantic.config import ConfigDict


class EffectifBase(BaseModel):
    """Modele de base partage par les schemas d'entree et de sortie."""

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
    def empty_string_to_none(cls, value):
        """Convertit les chaines vides en None pour faciliter le typage numerique.

        Args:
            value (str | int | float | None): Valeur issue du CSV.

        Returns:
            int | float | None | str: Valeur nettoyee si besoin.
        """
        if isinstance(value, str) and value.strip() == "":
            return None
        return value


class EffectifCreate(EffectifBase):
    """Schema d'entree pour la creation d'une ligne d'effectifs."""


class EffectifOut(EffectifBase):
    """Schema de sortie expose par l'API."""

    id: int


def as_pydantic_models():
    """Retourne les schemas utilises par le code historique.

    Returns:
        tuple[type[EffectifCreate], type[EffectifOut]]: Tuple des classes Pydantic.
    """
    return EffectifCreate, EffectifOut


__all__ = ["EffectifCreate", "EffectifOut", "as_pydantic_models"]
