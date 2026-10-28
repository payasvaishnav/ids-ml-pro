# New traffic sample

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
