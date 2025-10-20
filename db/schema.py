from pydantic import BaseModel, Field
from pydantic.config import ConfigDict

class EffectifBase(BaseModel):
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
    # alias vers le nom SQL avec espace
    niveau_prioritaire: str | None = Field(None, alias="Niveau prioritaire")
    libelle_classe_age: str | None = None
    libelle_sexe: str | None = None
    tri: float | None = None

    # Pydantic v2
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

class EffectifCreate(EffectifBase):
    """Schéma d'entrée (sans id)."""
    pass

class EffectifOut(EffectifBase):
    """Schéma de sortie (avec id)."""
    id: int

def as_pydantic_models():
    """
    Helper de compatibilité pour le main existant.
    Retourne (EffectifCreate, EffectifOut).
    """
    return EffectifCreate, EffectifOut

__all__ = ["EffectifCreate", "EffectifOut", "as_pydantic_models"]
