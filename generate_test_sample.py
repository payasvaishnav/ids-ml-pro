"""Create a reproducible dashboard test CSV from unused held-out examples."""
import hashlib
import json
import joblib
import pandas as pd
from sklearn.model_selection import train_test_split
from ids import ROOT, ARTIFACTS, load_dataset, predict, read_csv


def main():
    x, y, _ = load_dataset()
    _, heldout, _, heldout_labels = train_test_split(x, y, test_size=.2, stratify=y, random_state=42)
    # These are exactly the rows used by train.py for its original 25-flow demo.
    available = heldout.index[25:]
    chosen = []
    for label in sorted(y.unique()):
        eligible = y.loc[available][y.loc[available].eq(label)]
        if len(eligible) < 5:
            raise ValueError(f'Not enough unused held-out examples for {label}.')
        chosen.extend(eligible.sample(n=5, random_state=20261023).index.tolist())
    chosen = pd.Series(chosen).sample(frac=1, random_state=20261023).tolist()
    partitions = pd.read_csv(ARTIFACTS / 'partitions.csv').set_index('row_id')
    assert partitions.loc[chosen, 'partition'].eq('test').all()
    assert not set(chosen).intersection(heldout.index[:25])
    output = ROOT / 'samples'
    output.mkdir(exist_ok=True)
    flows = x.loc[chosen].reset_index(drop=True)
    flows.to_csv(output / 'new_test_traffic.csv', index=False)
    actual = y.loc[chosen].reset_index(drop=True)
    pd.DataFrame({'Row number': range(1, len(flows)+1), 'Actual label': actual}).to_csv(output / 'answer_key.csv', index=False)
    bundle = joblib.load(ARTIFACTS / 'model.joblib')
    # Read the exported file back, exactly as the dashboard does.
    result = predict(bundle, read_csv(output / 'new_test_traffic.csv'))
    assert len(result) == 35
    assert flows.shape[1] == len(bundle['features'])
    manifest = {
        'source': 'Unused examples from the existing CICIDS2017 sample test partition',
        'synthetic': False, 'rows': len(flows), 'features': flows.shape[1],
        'class_counts': actual.value_counts().to_dict(), 'sampling_seed': 20261023,
        'deduplicated_dataset_row_ids': chosen, 'excludes_original_demo': True,
        'csv_sha256': hashlib.sha256((output / 'new_test_traffic.csv').read_bytes()).hexdigest(),
        'purpose': 'Class-balanced functional demonstration; not an independent evaluation dataset.'}
    (output / 'provenance.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    (output / 'README.md').write_text('''# New traffic sample

Upload **new_test_traffic.csv** in the dashboard's Detect attacks tab, turn off
Use demo flows if necessary, and click Analyze flows.

The file contains 35 real held-out flows, five from each of the seven categories,
with all 77 required feature columns. It excludes the original 25 demo rows.
It contains no target labels or answer columns.

Use **answer_key.csv** to compare actual labels with downloaded predictions.
Row number 1 means the first data row after the CSV header. Row order is preserved.
There are five actual BENIGN flows and 30 actual attack flows; predictions may differ.

These records come from the existing sample's test partition, not a new network
capture. They are selected for a balanced functional demo, not for an independent
accuracy claim or representative traffic prevalence. They were not synthesized.
The source row identifiers and checksum are recorded in provenance.json.

Regenerate from the project folder:
`.venv/Scripts/python generate_test_sample.py`
''', encoding='utf-8')
    print(f'Created {len(flows)} flows with {flows.shape[1]} features; dashboard inference passed.')
    print(actual.value_counts().to_string())


if __name__ == '__main__':
    main()
