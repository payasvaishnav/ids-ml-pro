# Network Intrusion Detection Using Machine Learning

A semester project that compares eight configurations on sampled CICIDS2017 network flows: a majority baseline, Decision Tree, tuned tree, Random Forest, Extra Trees, Histogram Gradient Boosting, a 20-feature tree and stacking. It includes training cross-validation, error analysis, a Streamlit dashboard, report, presentation and an executed notebook.

For viva preparation, start with [the technical walkthrough](docs/VIVA_MASTERCLASS.md). The submission materials are in `deliverables/`. Student: Payas Vaishnav, 23BCP430, CSE PDEU, Semester 7. Faculty guide: Dr Nandini Modi.

## Start here

The local setup includes Python in `.venv`. Open PowerShell in this folder and run:

```powershell
.venv\Scripts\python.exe -m streamlit run app.py
```

Open the localhost URL printed in the terminal. In **Detect attacks**, leave **Use demo flows** selected and click **Analyze flows**. You can download predictions and an example CSV. Stop the server with Ctrl+C.

To set up on another Windows computer, install Python 3.11 or newer and Git, open PowerShell in this folder, and run:

```powershell
powershell -ExecutionPolicy Bypass -File .\setup.ps1
powershell -ExecutionPolicy Bypass -File .\launch.ps1
```

The command-level execution policy applies only to that process. Setup downloads dependencies and the original research repository, then trains the models. Internet access is needed for setup; the trained dashboard works locally.

## Project files

| File | Purpose |
|---|---|
| `ids.py` | Clean data, validate prediction inputs, run inference |
| `train.py` | Reproducible training, model comparison, test evaluation |
| `app.py` | Dashboard, charts, CSV prediction and download |
| `artifacts/` | Trained model, measured results, charts, example inputs |
| `docs/PROJECT_GUIDE.md` | Concepts, report draft, demo script, viva answers |
| `reference/` | Upstream notebooks, datasets, license, research papers |

To retrain: `.venv\Scripts\python.exe train.py`. Restart the dashboard after retraining so the cached model is refreshed. To use another matching labeled numeric dataset: `train.py --data path\to\data.csv`. The normal traffic label must be `BENIGN` for the dashboard's normal/attack status mapping.

## Method and scope

We remove duplicate feature rows before splitting. A fixed seed (42) creates stratified 60% training, 20% validation and 20% test partitions. Missing and infinite values become missing values, with median imputation fitted inside each model pipeline. Three-fold training CV supports comparison; a 12-candidate tree search uses training data only. The configuration with the highest validation macro F1 is refitted on the 80% development partition, then evaluated on test data. This fixed test partition was also evaluated in the earlier prototype, so scores are an internal benchmark rather than independent external validation. The tuned tree CV diagnostic reuses search folds and is not nested CV. The feature importance chart belongs to a separate diagnostic tree when boosting wins; it does not explain the selected boosting model.

The expanded run selects Histogram Gradient Boosting: 99.6141% test accuracy and 0.9923 macro F1. There are 22 benign false alarms and 9 attacks predicted benign. See [measured results](docs/RESULTS.md) for per-class metrics, CV scores and bootstrap intervals. Rerun `.venv\Scripts\python.exe prepare_materials.py` after training to refresh the results guide and executed notebook. Runtime timings can change across machines.

This is offline multiclass classification of flow measurements. It does not capture live packets, block traffic, implement the complete MTH-IDS/LCCDE research systems, or establish detection of previously unseen attack types. Uploaded files must already contain features from a compatible flow extractor with matching units. A random split of a sampled historical dataset can overestimate performance on new days, devices and networks. A stronger extension is evaluation by time or capture session using the original full dataset.

## Attribution

Inspired by [Western OC2 Lab's IDS-ML project](https://github.com/Western-OC2-Lab/Intrusion-Detection-System-Using-Machine-Learning). The dataset used is their `data/CICIDS2017_sample.csv`, described upstream as a randomly sampled subset. Reference revision used during development: `502ba86173a8aae5a9b2973fa4e0a42de69fa6ba`. The upstream repository is MIT licensed; its license is retained in `reference/LICENSE`. The new training pipeline and dashboard are a simplified educational implementation. Do not claim the upstream research as original work.

Dataset source: [Canadian Institute for Cybersecurity, CICIDS2017](https://www.unb.ca/cic/datasets/ids-2017.html).

Research reference: L. Yang, A. Moubayed, I. Hamieh and A. Shami, “Tree-Based Intelligent Intrusion Detection System in Internet of Vehicles,” IEEE GLOBECOM, 2019, DOI: 10.1109/GLOBECOM38437.2019.9013892.

## Troubleshooting

- Missing packages: run `.venv\Scripts\python.exe -m pip install -r requirements.txt`.
- Missing artifacts: run training first.
- Missing CSV features: download the dashboard example and compare your column names. Raw packet captures are not accepted.
- Incomplete reference download: allow an ongoing clone to finish. If it failed, rename that folder and rerun setup; setup avoids overwriting it.
- Port occupied: add `--server.port 8502` to the Streamlit command.
- Model files are Python serialization: use only the model generated by this project, not model files from strangers.

Exact dependency versions used for the verified run are in `requirements-lock.txt`.
