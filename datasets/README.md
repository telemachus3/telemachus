![Verify](https://github.com/telemachus3/telemachus-datasets/actions/workflows/verify.yml/badge.svg)

# Telemachus Datasets

📊 Jeu de données **Telemachus 0.1** généré avec [RoadSimulator3](https://github.com/SebE585/RoadSimulator3).  
Format conforme à la spécification [Telemachus Spec 0.1](https://github.com/telemachus3/telemachus-spec).

---

## 📂 Contenu

- `2025-10-01-v1.0/`
  - `dataset.json` → métadonnées (schéma, version, infos simulation)
  - `samples.csv` → données tabulaires brutes (lisibles avec Pandas / Excel)
  - `samples.parquet` → version optimisée pour analyse big data

---

## ⚙️ Utilisation rapide

```python
import pandas as pd

# Charger le CSV
df = pd.read_csv("2025-10-01-v1.0/samples.csv")

# Charger le Parquet
df_parquet = pd.read_parquet("2025-10-01-v1.0/samples.parquet")
```

[![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://github.com/telemachus3/telemachus-datasets/blob/main/notebooks/quickstart.ipynb)

Ce notebook permet d’explorer le dataset directement dans votre navigateur, sans installation préalable. Il offre une introduction interactive à l’analyse des données Telemachus. 

---

## 📜 Licence

Ce dataset est publié sous licence **[CC0 1.0 Universal](LICENSE)**.  
Vous pouvez l’utiliser librement (recherche, industriel, enseignement) sans restriction.