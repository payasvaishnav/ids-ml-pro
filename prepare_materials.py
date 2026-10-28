"""Refresh the results guide and build a small executed learning notebook."""
import contextlib
import io
import json
from pathlib import Path
import pandas as pd

root = Path(__file__).resolve().parent
m = json.loads((root / 'artifacts/metrics.json').read_text())
c = pd.read_csv(root / 'artifacts/comparison.csv')
report = m['classification_report']
lines = ['# Measured results', '', 'Expanded benchmark run on 22 October 2026. All values below come from saved experiment artifacts.', '',
         f"Selected model: **{m['best_model']}**. Test accuracy **{m['test_accuracy']:.4%}**; macro F1 **{m['test_macro_f1']:.4f}**.", '',
         f"{m['rows']:,} distinct flows, {m['features']} features, {m['duplicates_removed']:,} duplicate feature rows removed. Partitions: {m['split']}.", '',
         '| Configuration | Validation accuracy | Validation macro F1 | Training CV macro F1 |', '|---|---:|---:|---:|']
for _,r in c.iterrows():
    lines.append(f"| {r.model} | {r.validation_accuracy:.2%} | {r.validation_macro_f1:.4f} | {r.cv_macro_f1_mean:.4f} ± {r.cv_macro_f1_std:.4f} |")
lines += ['', 'Three-fold CV uses training data. The tuned tree CV score reuses search folds and is a diagnostic, not an unbiased nested-CV estimate. Timing includes three CV fits plus one full training fit and excludes hyperparameter-search cost.', '',
          '| Label | Precision | Recall | F1 | Test support |', '|---|---:|---:|---:|---:|']
for label in m['labels']:
    r = report[label]
    lines.append(f"| {label} | {r['precision']:.4f} | {r['recall']:.4f} | {r['f1-score']:.4f} | {r['support']:.0f} |")
b = m['binary_confusion_matrix']
lines += ['', f"Normal-versus-attack counts: {b[0][0]} true normal, {b[0][1]} false alarms, {b[1][0]} missed attacks, {b[1][1]} detected attacks.",
          f"Attack recall: {m['binary_attack_recall']:.4%}. Benign false alarm rate: {m['binary_false_positive_rate']:.4%}.", '',
          f"95% stratified bootstrap intervals, 300 resamples: accuracy {m['accuracy_ci95'][0]:.4%}–{m['accuracy_ci95'][1]:.4%}; macro F1 {m['macro_f1_ci95'][0]:.4f}–{m['macro_f1_ci95'][1]:.4f}.", '',
          'Intervals describe resampling uncertainty on these examples. They do not account for collection-level correlation, dataset shift or model selection. Rare-class support remains small.', '',
          m['test_note'], 'Random splitting can place related traffic in different partitions. Scores do not establish reliability on live networks or unknown attacks.', '',
          'Reproduce: `.venv/Scripts/python train.py`, then `.venv/Scripts/python verify.py`. Seed: 42. Dataset SHA-256: `' + m['dataset_sha256'] + '`.',
          'The tuned tree, feature subset and stacking were retained even though validation scores were lower. No improvement is assumed merely from additional complexity.']
(root / 'docs/RESULTS.md').write_text('\n'.join(lines), encoding='utf-8')
cells = []
def md(s): cells.append({'cell_type':'markdown', 'metadata':{}, 'source':s.splitlines(True)})
def code(s): cells.append({'cell_type':'code','metadata':{},'execution_count':None,'outputs':[],'source':s.splitlines(True)})
md('# Network Intrusion Detection\nPayas Vaishnav · 23BCP430 · CSE PDEU · Semester 7\n\nThis executed companion notebook reads the real experiment outputs and demonstrates saved-model inference. Run `train.py` first to regenerate the benchmark. No training metrics are hard-coded here.')
code("from pathlib import Path\nimport json\nimport pandas as pd\nimport joblib\nfrom ids import ARTIFACTS, load_dataset, read_csv, predict\nmetrics = json.loads((ARTIFACTS / 'metrics.json').read_text())\nprint('Selected model:', metrics['best_model'])")
md('## 1 Understand the inputs\nA row describes a network flow. Feature columns contain traffic measurements; `Label` is the known class. Duplicating flows across partitions would make evaluation too easy.')
code("x, y, removed = load_dataset()\nprint('Distinct rows:', len(x), 'Features:', len(x.columns), 'Duplicates removed:', removed)\nprint(y.value_counts().to_string())\nprint(x.iloc[:3, :5].to_string(index=False))")
md('## 2 Inspect partition separation\nThe split uses seed 42 and stratification. Imputation and feature selection fit inside model pipelines. Three-fold training CV supports comparison; validation macro F1 chooses the final model.')
code("partitions = pd.read_csv(ARTIFACTS / 'partitions.csv')\nassert partitions.row_id.is_unique\nprint(partitions.partition.value_counts().to_string())")
md('## 3 Compare algorithms\nThe majority baseline demonstrates why overall accuracy alone is insufficient. Hyperparameter search uses only the training partition. The tuned tree CV result is a reused-search-fold diagnostic.')
code("comparison = pd.read_csv(ARTIFACTS / 'comparison.csv')\nprint(comparison[['model','validation_accuracy','validation_macro_f1','cv_macro_f1_mean']].to_string(index=False))\nprint('Chosen tree settings:', metrics['tuning_best_params'])")
md('## 4 Read final evaluation\nMacro F1 weights every label equally. Per-class recall exposes missed attacks that accuracy may hide. The fixed test split has also been evaluated in the earlier prototype, so this remains an internal benchmark.')
code("print('Test accuracy:', round(metrics['test_accuracy'],6))\nprint('Test macro F1:', round(metrics['test_macro_f1'],6))\nprint(pd.DataFrame({k:metrics['classification_report'][k] for k in metrics['labels']}).T.to_string())\nprint('Binary matrix [normal, attack]:', metrics['binary_confusion_matrix'])\nprint('95% macro F1 bootstrap interval:', metrics['macro_f1_ci95'])")
md('## 5 Predict new flow records\nUse the supplied held-out demo flows. An uploaded file needs the same columns and measurement units. Confidence scores are uncalibrated model scores.')
code("bundle = joblib.load(ARTIFACTS / 'model.joblib')\nflows = read_csv(ARTIFACTS / 'demo_flows.csv')\nresult = predict(bundle, flows)\nprint(result[['Predicted label','Traffic status','Model confidence']].to_string(index=False))")
md('## 6 Examine mistakes\nRetain errors for discussion. A missed attack and a false alarm have different practical costs. A perfect score from only a few rare examples is weak evidence.')
code("errors = pd.read_csv(ARTIFACTS / 'error_examples.csv')\nprint(errors[['actual','predicted']].value_counts().to_string())\nprint('Total multiclass mistakes:', len(errors))")
md('## 7 Reproduce and extend\nRun `python train.py` using the project virtual environment, then `python verify.py`. The report and presentation sources are in `tools/`. A stronger extension requires the full dataset with day or session metadata for an independent chronological evaluation. The current sample does not provide those grouping fields.\n\nReferences: Western OC2 Lab IDS-ML repository, CICIDS2017 dataset documentation and scikit-learn documentation, linked in the README.')
scope = {'__name__':'__notebook__'}
count = 0
for cell in cells:
    if cell['cell_type'] == 'code':
        count += 1
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf): exec(compile(''.join(cell['source']), '<notebook>', 'exec'), scope)
        cell['execution_count'] = count
        cell['outputs'] = [{'output_type':'stream','name':'stdout','text':buf.getvalue().splitlines(True)}]
notebook = {'cells':cells,'metadata':{'kernelspec':{'display_name':'Python 3','language':'python','name':'python3'},'language_info':{'name':'python','version':m['python']}},'nbformat':4,'nbformat_minor':5}
for i,cell in enumerate(cells): cell['id'] = f'ids-{i:02}'
(root / 'IDS_Experiment.ipynb').write_text(json.dumps(notebook,indent=2), encoding='utf-8')
print('Updated results and executed notebook.')
