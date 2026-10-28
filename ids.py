"""Shared data validation and inference for the semester IDS project."""
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
DATA = ROOT / 'reference' / 'data' / 'CICIDS2017_sample.csv'
ARTIFACTS = ROOT / 'artifacts'


def read_csv(source):
    df = pd.read_csv(source)
    df.columns = df.columns.str.strip()
    if df.columns.duplicated().any():
        raise ValueError('CSV contains duplicate column names.')
    return df


def numeric_features(df):
    return df.apply(pd.to_numeric, errors='coerce').replace([np.inf, -np.inf], np.nan)


def load_dataset(path=DATA):
    df = read_csv(path)
    if 'Label' not in df:
        raise ValueError('Training CSV must contain a Label column.')
    df = df.dropna(subset=['Label']).copy()
    df['Label'] = df['Label'].astype(str).str.strip()
    df = df[df.Label.ne('')]
    # Exported dataframe indices are not network measurements.
    df = df.loc[:, ~df.columns.str.match(r'^Unnamed:')]
    features = [c for c in df if c != 'Label']
    x = numeric_features(df[features])
    # Deduplicate on features, before splitting, to prevent identical flows
    # appearing in both training and held-out partitions.
    unique = ~x.duplicated()
    removed = int((~unique).sum())
    x, y = x.loc[unique].reset_index(drop=True), df.loc[unique, 'Label'].reset_index(drop=True)
    features = x.columns[x.notna().any()].tolist()
    if not features or y.nunique() < 2:
        raise ValueError('Need numeric features and at least two classes.')
    if y.value_counts().min() < 5:
        raise ValueError('Each class needs at least five distinct flows for stratified splits.')
    return x[features], y, removed


def predict(bundle, df):
    missing = sorted(set(bundle['features']) - set(df.columns))
    if missing:
        raise ValueError('Missing required features: ' + ', '.join(missing))
    x = numeric_features(df[bundle['features']])
    if x.isna().all(axis=1).any():
        raise ValueError('Some rows contain no usable numeric measurements.')
    model = bundle['model']
    probabilities = model.predict_proba(x)
    out = df.copy()
    out['Predicted label'] = model.predict(x)
    out['Model confidence'] = probabilities.max(axis=1)
    out['Traffic status'] = np.where(out['Predicted label'].str.upper().eq('BENIGN'), 'Normal', 'Attack')
    return out
