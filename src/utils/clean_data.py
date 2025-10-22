import pandas as pd

input_file = "data/raw/effectifs.csv"
output_file = "data/clean/csv_clean.csv"

# Colonnes à conserver
cols_required = [
    "annee", "patho_niv1", "top", "cla_age_5", "sexe", "region", "dept",
    "Ntop", "Npop", "prev", "Niveau prioritaire", "libelle_sexe", "tri"
]

# Optionnel : déclarer les types si connus
dtypes = {
    "annee": "Int32",  # Nullable integer
    "top": "category",
    "sexe": "category",
    "region": "category",
    "dept": "category",
    "Ntop": "float32",
    "Npop": "float32",
    "prev": "float32",
    "Niveau prioritaire": "category",
    "libelle_sexe": "category",
    "tri": "float32"
}

# Charger uniquement les colonnes utiles (plus rapide)
df = pd.read_csv(
    input_file,
    sep=";",
    usecols=lambda col: col in cols_required, #ignore les colonnes inutiles
    dtype=dtypes,
    na_values=[""]  # les chaînes vides seront considérées comme NaN
)

# Afficher le nombre de lignes initial
print(f"Nombre de lignes initiales : {len(df)}")

# Supprimer les lignes avec NaN 
df_clean = df.dropna(subset=cols_required)

# Afficher le nombre de lignes après nettoyage
print(f"Nombre de lignes après nettoyage : {len(df_clean)}")

# Export
df_clean.to_csv(output_file, index=False, encoding="utf-8")
