"""Check saved inference and the actual Streamlit demo interaction."""
import joblib
import json
import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, f1_score, confusion_matrix
from streamlit.testing.v1 import AppTest
from ids import ARTIFACTS, predict, read_csv

bundle = joblib.load(ARTIFACTS / 'model.joblib')
sample = read_csv(ARTIFACTS / 'demo_flows.csv')
out = predict(bundle, sample)
assert len(out) == len(sample)
assert out['Model confidence'].between(0, 1).all()
assert set(out['Predicted label']).issubset(set(bundle['model'].classes_))
metrics = json.loads((ARTIFACTS / 'metrics.json').read_text())
recorded = pd.read_csv(ARTIFACTS / 'test_predictions.csv')
assert np.isclose(accuracy_score(recorded.actual, recorded.predicted), metrics['test_accuracy'])
assert np.isclose(f1_score(recorded.actual, recorded.predicted, average='macro'), metrics['test_macro_f1'])
assert confusion_matrix(recorded.actual.ne('BENIGN'), recorded.predicted.ne('BENIGN'), labels=[False, True]).tolist() == metrics['binary_confusion_matrix']
partitions = pd.read_csv(ARTIFACTS / 'partitions.csv')
assert partitions.row_id.is_unique
assert partitions.partition.value_counts().to_dict() == metrics['split']
try:
    predict(bundle, sample.drop(columns=[bundle['features'][0]]))
except ValueError as exc:
    assert 'Missing required features' in str(exc)
else:
    raise AssertionError('Missing feature was accepted')
app = AppTest.from_file('app.py').run(timeout=30)
assert not app.exception, app.exception
app.button[0].click().run(timeout=30)
assert not app.exception, app.exception
assert any('Analyzed 25 flows' in s.value for s in app.success)
print('PASS: inference, schema rejection, recorded test metrics, partition counts, dashboard render and demo predictions.')
