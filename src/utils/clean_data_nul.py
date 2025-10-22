import pandas as pd

# Nom du fichier d'entrée
input_file = "data/raw/effectifs.csv"
output_file = "data/clean/csv_clean.csv"

# Colonnes qui peuvent être vides
cols_optional = ["patho_niv2", "patho_niv3"]

# Lecture du CSV
try:
    df = pd.read_csv(input_file, sep=";", dtype=str)  # dtype=str pour garder les NaN comme chaînes
except Exception as e:
    print(f"Erreur lors de la lecture du fichier : {e}")
    exit(1)

# Supprime les lignes où les colonnes obligatoires ont des valeurs manquantes
cols_required = [col for col in df.columns if col not in cols_optional]
df_clean = df.dropna(subset=cols_required, how='any')
df = df[~df[cols_required].apply(lambda x: x.eq("").any(), axis=1)]

# Suppression de la colonne "libelle_classe_age"
if "libelle_classe_age" in df.columns:
    df = df.drop(columns=["libelle_classe_age"])

# Sauvegarde du CSV nettoyé
try:
    df_clean.to_csv(output_file, index=False, encoding="utf-8")

    print(f"Nettoyage terminé : {len(df_clean)} lignes conservées sur {len(df)}.")
    print(f"Fichier nettoyé enregistré sous : {output_file}")

except Exception as e:
    print(f"Erreur lors de l'écriture du fichier : {e}")

