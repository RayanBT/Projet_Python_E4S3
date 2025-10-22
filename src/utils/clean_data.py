import pandas as pd

# Nom des fichiers csv
input_file = "data/raw/effectifs.csv"
output_file = "data/clean/csv_clean.csv"

# Définir les colonnes obligatoires
cols_required = [
    "annee", "patho_niv1", "top", "cla_age_5", "sexe", "region", "dept",
    "Ntop", "Npop", "prev", "Niveau prioritaire", "libelle_sexe", "tri"
]

# Charger le fichier CSV
df = pd.read_csv(input_file, sep=";")

# Supprimer les lignes avec des valeurs vides dans les colonnes obligatoires
df_clean = df.dropna(subset=cols_required, how="any")
# Supprimer les lignes où une des colonnes obligatoires contient une chaîne vide
df_clean = df_clean[~df_clean[cols_required].apply(lambda x: x.eq("").any(), axis=1)]

# Supprimer la colonne 'libelle_classe_age'
df_clean = df_clean.drop(columns=["libelle_classe_age"], errors="ignore")

# Enregistrer le fichier nettoyé
df_clean.to_csv(output_file, index=False, encoding="utf-8")
