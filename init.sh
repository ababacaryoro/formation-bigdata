cd ..
uv init formation-bigdata && cd formation-bigdata
uv python pin 3.12

# Socle notebooks + manipulation de données
uv add "pandas>=2.2" "numpy>=2.0" "pyarrow>=17" ipykernel ipywidgets tqdm

# Génération des données simulées
uv add faker

# Mesures (module 01 : limites du poste)
uv add psutil

# Module 02 : Dask
uv add "dask[complete]>=2025.1"

# Module 03 : formats (comparaison Parquet)
uv add fastparquet

# Module 05 : MongoDB
uv add pymongo

# Modules 06-07-10 : Spark, appariement, MLlib
uv add "pyspark>=4.0" rapidfuzz

# Module 08 : Kafka
uv add confluent-kafka

# Visualisation
uv add matplotlib seaborn plotly

# Outils de développement
uv add --dev ruff