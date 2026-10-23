# GardnAIze — ML algorithm research

Six executable Jupyter notebooks for **comparing and selecting algorithms** before production integration.

## Structure

- `ai-service/notebooks/`: research notebooks and Python dependencies.
- `datasets/ml-research/`: synthetic generator and CSV templates for real botanical data.

## Run from WSL / VS Code

```bash
python3 -m venv .venv-ml
source .venv-ml/bin/activate
pip install -r ai-service/notebooks/requirements-ml-research.txt
python datasets/ml-research/generate_synthetic_demo.py
code .
```

Select the `.venv-ml` Python kernel. Run notebooks 01–06 in order. Notebook 06 reads score CSVs produced by 02 and 05.

## Notebooks

1. Data audit and missing values
2. K-Means / agglomerative / DBSCAN clustering comparison
3. PCA visualization
4. Euclidean / Manhattan / cosine nearest-neighbor ranking exploration
5. Dummy / logistic regression / decision tree / random forest / histogram gradient boosting supervised comparison
6. Selection report and evidence limitations

## Scientific cautions

The generated 600 records are **synthetic**, not botanical facts or evidence of real-world accuracy. Replace them with documented, appropriately licensed plant data. A supervised model requires sufficiently reliable labels. Avoid target leakage and group close species/cultivars in evaluation. Cluster silhouette alone cannot validate horticultural usefulness. Recommendation ranking requires independent garden–plant relevance labels before a metric-based winner can be declared. Never silently replace verified plant needs with predicted values.

These experiments are deliberately separate from the FastAPI production runtime. Future experiments (CNN / transfer learning) may be added independently.
