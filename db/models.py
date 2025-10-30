"""Helpers SQLAlchemy pour interagir avec la base effectifs."""

from contextlib import contextmanager
from pathlib import Path
from typing import Generator

from sqlalchemy import Column, Integer, MetaData, Table, create_engine, inspect
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, registry, sessionmaker


def get_engine(db_path: Path) -> Engine:
    """Cree un moteur SQLAlchemy pour une base SQLite donnee.

    Args:
        db_path (Path): Chemin du fichier SQLite cible.

    Returns:
        Engine: Moteur SQLAlchemy configure pour SQLite.
    """
    return create_engine(f"sqlite:///{db_path}", future=True)


@contextmanager
def get_session(engine: Engine) -> Generator[Session, None, None]:
    """Ouvre une session SQLAlchemy et la referme automatiquement.

    Args:
        engine (Engine): Moteur SQLAlchemy sur lequel ouvrir la session.

    Yields:
        Session: Objet Session pret a l'emploi dans un bloc with.
    """
    SessionLocal = sessionmaker(bind=engine, future=True)
    session: Session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def reflect_effectifs(engine: Engine, table_name: str):
    """Mappe dynamiquement une table SQLite vers une classe ORM.

    Args:
        engine (Engine): Moteur SQLAlchemy connecte a la base.
        table_name (str): Nom de la table a refleter.

    Returns:
        type: Classe ORM generique associee a la table.

    Raises:
        LookupError: Si la table demandee n'existe pas dans la base.
    """
    insp = inspect(engine)
    tables = insp.get_table_names()
    if table_name not in tables:
        raise LookupError(f"Table introuvable dans la base : '{table_name}'. Tables vues: {tables}")

    pk_info = insp.get_pk_constraint(table_name) or {}
    pk_cols = pk_info.get("constrained_columns") or []

    mapper_registry = registry()
    metadata: MetaData = mapper_registry.metadata

    if not pk_cols:
        # Fallback : on force 'id' comme cle primaire si disponible
        table = Table(
            table_name,
            metadata,
            Column("id", Integer, primary_key=True),
            autoload_with=engine,
        )
    else:
        table = Table(table_name, metadata, autoload_with=engine)

    class Effectif:
        """Enregistrement ORM de la table effectifs."""

    mapper_registry.map_imperatively(Effectif, table)
    return Effectif


def count_rows_orm(session: Session, Effectif) -> int:
    """Compte le nombre de lignes via l'ORM SQLAlchemy.

    Args:
        session (Session): Session SQLAlchemy active.
        Effectif (type): Classe ORM retournee par reflect_effectifs.

    Returns:
        int: Nombre de lignes presentes dans la table.
    """
    return session.query(Effectif).count()
