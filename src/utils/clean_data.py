"""
Module de nettoyage et normalisation des données.
Contient toutes les fonctions pour nettoyer le CSV et la base de données.
"""

import pandas as pd
import sqlite3
from pathlib import Path
from typing import Optional, Callable


# ============================================================================
# DICTIONNAIRE DES LABELS COURTS POUR LES PATHOLOGIES
# ============================================================================

PATHOLOGIE_MAPPING = {
    "Affections de longue durée (dont 31 et 32) pour d'autres causes": "Affections longue durée (autres)",
    "Cancers": "Cancers",
    "Diabète": "Diabète",
    "Hospitalisation pour Covid-19": "Covid-19",
    "Hospitalisations hors pathologies repérées (avec ou sans pathologies, traitements ou maternité)": "Hospitalisations diverses",
    "Insuffisance rénale chronique terminale": "Insuffisance rénale",
    "Maladies cardioneurovasculaires": "Maladies cardiovasculaires",
    "Maladies du foie ou du pancréas (hors mucoviscidose)": "Maladies hépatiques/pancréatiques",
    "Maladies inflammatoires ou rares ou infection VIH": "Maladies inflammatoires/VIH",
    "Maladies neurologiques": "Maladies neurologiques",
    "Maladies psychiatriques": "Maladies psychiatriques",
    "Maladies respiratoires chroniques (hors mucoviscidose)": "Maladies respiratoires",
    "Maternité (avec ou sans pathologies)": "Maternité",
    "Pas de pathologie repérée, traitement, maternité, hospitalisation ou traitement antalgique ou anti-inflammatoire": "Aucune pathologie repérée",
    "Traitements antalgiques ou anti-inflammatoires (hors pathologies, traitements, maternité ou hospitalisations)": "Traitements antalgiques/anti-inflammatoires",
    "Traitements du risque vasculaire (hors pathologies)": "Traitements risque vasculaire",
    "Traitements psychotropes (hors pathologies)": "Traitements psychotropes",
}


# ============================================================================
# NETTOYAGE CSV
# ============================================================================

def clean_csv_data(
    input_file: Path, 
    output_file: Path, 
    report: Optional[Callable[[str], None]] = None
) -> Path:
    """
    Nettoie les données du CSV en supprimant les lignes avec des valeurs manquantes.
    
    Args:
        input_file: Chemin vers le fichier CSV d'entrée
        output_file: Chemin où sauvegarder le fichier CSV nettoyé
        report: Fonction optionnelle pour le reporting
        
    Returns:
        Chemin vers le fichier CSV nettoyé
    """
    reporter = report or print
    
    try:
        # Colonnes qui peuvent être vides
        cols_optional = ["patho_niv2", "patho_niv3"]

        # Lecture du CSV
        df = pd.read_csv(input_file, sep=";", dtype=str)
        initial_rows = len(df)
        
        # Supprime les lignes où les colonnes obligatoires ont des valeurs manquantes
        cols_required = [col for col in df.columns if col not in cols_optional]
        df = df.dropna(subset=cols_required, how='any')
        df = df[~df[cols_required].apply(lambda x: x.eq("").any(), axis=1)]

        # Suppression de la colonne "libelle_classe_age" si elle existe
        if "libelle_classe_age" in df.columns:
            df = df.drop(columns=["libelle_classe_age"])

        # Sauvegarde du CSV nettoyé
        output_file.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_file, index=False, encoding="utf-8")

        reporter(f"[INFO] Nettoyage CSV terminé : {len(df)} lignes conservées sur {initial_rows}.")
        reporter(f"[INFO] Fichier nettoyé enregistré sous : {output_file}")
        
        return output_file

    except Exception as e:
        reporter(f"[ERREUR] Erreur lors du nettoyage du fichier CSV : {e}")
        raise


# ============================================================================
# NETTOYAGE BASE DE DONNÉES
# ============================================================================

def clean_pathologie_labels(
    db_path: str | Path,
    dry_run: bool = False,
    report: Optional[Callable[[str], None]] = None
) -> dict:
    """
    Raccourcit les noms de pathologies trop longs dans la base de données.
    
    Args:
        db_path: Chemin vers le fichier SQLite
        dry_run: Si True, affiche les changements sans les appliquer
        report: Fonction optionnelle pour le reporting
        
    Returns:
        Dictionnaire avec les statistiques de nettoyage
    """
    reporter = report or print
    stats = {
        "pathologies_analysees": 0,
        "pathologies_modifiees": 0,
        "lignes_affectees": 0,
        "mapping": {}
    }
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Vérifier quelles pathologies existent dans la DB
        cursor.execute("SELECT DISTINCT patho_niv1 FROM effectifs ORDER BY patho_niv1")
        pathologies_actuelles = [row[0] for row in cursor.fetchall()]
        stats["pathologies_analysees"] = len(pathologies_actuelles)
        
        reporter(f"\n[INFO] Analyse de {len(pathologies_actuelles)} pathologies...")
        
        # Pour chaque pathologie à modifier
        for patho_long, patho_court in PATHOLOGIE_MAPPING.items():
            if patho_long in pathologies_actuelles and patho_long != patho_court:
                # Compter combien de lignes seront affectées
                cursor.execute(
                    "SELECT COUNT(*) FROM effectifs WHERE patho_niv1 = ?",
                    (patho_long,)
                )
                count = cursor.fetchone()[0]
                
                if count > 0:
                    reporter(f"\n[MODIF] '{patho_long}' ({len(patho_long)} car.)")
                    reporter(f"     → '{patho_court}' ({len(patho_court)} car.)")
                    reporter(f"     → {count:,} lignes affectées")
                    
                    stats["pathologies_modifiees"] += 1
                    stats["lignes_affectees"] += count
                    stats["mapping"][patho_long] = {
                        "nouveau_label": patho_court,
                        "lignes_affectees": count,
                        "reduction": len(patho_long) - len(patho_court)
                    }
                    
                    # Appliquer la modification si pas en mode dry_run
                    if not dry_run:
                        cursor.execute(
                            "UPDATE effectifs SET patho_niv1 = ? WHERE patho_niv1 = ?",
                            (patho_court, patho_long)
                        )
        
        if not dry_run:
            conn.commit()
            reporter(f"\n✅ [SUCCÈS] Modifications appliquées dans la base de données.")
        else:
            reporter(f"\n[DRY RUN] Aucune modification appliquée (mode simulation).")
        
        reporter(f"\n[RÉSUMÉ]")
        reporter(f"  • Pathologies analysées : {stats['pathologies_analysees']}")
        reporter(f"  • Pathologies modifiées : {stats['pathologies_modifiees']}")
        reporter(f"  • Lignes totales affectées : {stats['lignes_affectees']:,}")
        
        conn.close()
        return stats
        
    except Exception as e:
        reporter(f"\n[ERREUR] Erreur lors du nettoyage des pathologies : {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        raise


def verify_pathologie_labels(
    db_path: str | Path,
    report: Optional[Callable[[str], None]] = None
) -> list[dict]:
    """
    Vérifie les labels de pathologies actuels dans la base de données.
    
    Args:
        db_path: Chemin vers le fichier SQLite
        report: Fonction optionnelle pour le reporting
        
    Returns:
        Liste de dictionnaires avec les infos sur chaque pathologie
    """
    reporter = report or print
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT patho_niv1, COUNT(*) as nb_lignes
            FROM effectifs
            GROUP BY patho_niv1
            ORDER BY patho_niv1
        """)
        
        pathologies = []
        reporter(f"\n[INFO] Pathologies actuelles dans la base de données :\n")
        
        for patho, count in cursor.fetchall():
            info = {
                "label": patho,
                "longueur": len(patho),
                "nb_lignes": count,
                "est_long": len(patho) > 50
            }
            pathologies.append(info)
            
            indicateur = "⚠️" if info["est_long"] else "✓"
            reporter(f"{indicateur} {patho} ({len(patho)} car.) - {count:,} lignes")
        
        conn.close()
        return pathologies
        
    except Exception as e:
        reporter(f"[ERREUR] Erreur lors de la vérification : {e}")
        raise


# ============================================================================
# FONCTION PRINCIPALE DE NETTOYAGE
# ============================================================================

def clean_all_data(
    db_path: str | Path,
    dry_run: bool = False,
    report: Optional[Callable[[str], None]] = None
) -> dict:
    """
    Effectue un nettoyage complet des données (pathologies, etc.).
    
    Args:
        db_path: Chemin vers le fichier SQLite
        dry_run: Si True, simule les changements sans les appliquer
        report: Fonction optionnelle pour le reporting
        
    Returns:
        Dictionnaire avec toutes les statistiques de nettoyage
    """
    reporter = report or print
    
    reporter("=" * 70)
    reporter("NETTOYAGE COMPLET DES DONNÉES")
    reporter("=" * 70)
    
    all_stats = {}
    
    # 1. Vérification avant nettoyage
    reporter("\n[ÉTAPE 1] Vérification de l'état actuel...")
    verify_pathologie_labels(db_path, report)
    
    # 2. Nettoyage des pathologies
    reporter("\n[ÉTAPE 2] Nettoyage des labels de pathologies...")
    patho_stats = clean_pathologie_labels(db_path, dry_run, report)
    all_stats["pathologies"] = patho_stats
    
    # 3. Vérification après nettoyage
    if not dry_run:
        reporter("\n[ÉTAPE 3] Vérification après nettoyage...")
        verify_pathologie_labels(db_path, report)
    
    reporter("\n" + "=" * 70)
    reporter("NETTOYAGE TERMINÉ")
    reporter("=" * 70)
    
    return all_stats


# ============================================================================
# SCRIPT EXÉCUTABLE
# ============================================================================

if __name__ == "__main__":
    import sys
    
    # Chemin par défaut vers la base de données
    default_db = Path(__file__).parent.parent.parent / "data" / "effectifs.sqlite3"
    
    # Arguments
    dry_run = "--dry-run" in sys.argv or "-d" in sys.argv
    db_path = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("-") else default_db
    
    print(f"\nBase de données : {db_path}")
    print(f"Mode : {'SIMULATION (dry-run)' if dry_run else 'MODIFICATION RÉELLE'}\n")
    
    if not dry_run:
        confirmation = input("⚠️  Voulez-vous vraiment modifier la base de données ? (oui/non) : ")
        if confirmation.lower() not in ["oui", "yes", "o", "y"]:
            print("Opération annulée.")
            sys.exit(0)
    
    # Exécution
    stats = clean_all_data(db_path, dry_run=dry_run)
    
    print("\n✅ Script terminé avec succès.")
