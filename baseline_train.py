"""Original three-model prototype, retained for historical reference."""
import argparse
import json
import time
import hashlib
import joblib
import os
from pathlib import Path
os.environ.setdefault('MPLCONFIGDIR', str(Path(__file__).resolve().parent / '.matplotlib'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier, ExtraTreesClassifier
from sklearn.impute import SimpleImputer
from sklearn.pipeline import make_pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, f1_score, classification_report, confusion_matrix, ConfusionMatrixDisplay
from ids import DATA, ARTIFACTS, load_dataset


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--data', type=str, default=str(DATA))
    args = parser.parse_args()
    x, y, duplicates = load_dataset(args.data)
    x_dev, x_test, y_dev, y_test = train_test_split(x, y, test_size=.2, stratify=y, random_state=42)
    x_train, x_val, y_train, y_val = train_test_split(x_dev, y_dev, test_size=.25, stratify=y_dev, random_state=42)
    candidates = {
        'Decision Tree': DecisionTreeClassifier(max_depth=20, class_weight='balanced', random_state=42),
        'Random Forest': RandomForestClassifier(n_estimators=120, class_weight='balanced', n_jobs=-1, random_state=42),
        'Extra Trees': ExtraTreesClassifier(n_estimators=120, class_weight='balanced', n_jobs=-1, random_state=42),
    }
    rows = []
    for name, estimator in candidates.items():
        model = make_pipeline(SimpleImputer(strategy='median', keep_empty_features=True), estimator)
        start = time.perf_counter()
        model.fit(x_train, y_train)
        pred = model.predict(x_val)
        rows.append({'model': name, 'validation_accuracy': accuracy_score(y_val, pred),
                     'validation_macro_f1': f1_score(y_val, pred, average='macro'),
                     'training_seconds': time.perf_counter() - start})
        print(rows[-1], flush=True)
    best = max(rows, key=lambda row: row['validation_macro_f1'])['model']
    final = make_pipeline(SimpleImputer(strategy='median', keep_empty_features=True), candidates[best])
    final.fit(x_dev, y_dev)
    pred = final.predict(x_test)
    labels = final.classes_.tolist()
    ARTIFACTS.mkdir(exist_ok=True)
    joblib.dump({'model': final, 'features': x.columns.tolist()}, ARTIFACTS / 'model.joblib')
    pd.DataFrame(rows).to_csv(ARTIFACTS / 'comparison.csv', index=False)
    report = classification_report(y_test, pred, output_dict=True, zero_division=0)
    cm = confusion_matrix(y_test, pred, labels=labels)
    metrics = {'best_model': best, 'test_accuracy': accuracy_score(y_test, pred),
               'test_macro_f1': f1_score(y_test, pred, average='macro'), 'classification_report': report,
               'labels': labels, 'confusion_matrix': cm.tolist(), 'rows': len(x), 'duplicates_removed': duplicates,
               'features': len(x.columns), 'split': {'train': len(x_train), 'validation': len(x_val), 'test': len(x_test)},
               'class_counts': y.value_counts().to_dict(), 'seed': 42,
               'dataset_sha256': hashlib.sha256(open(args.data, 'rb').read()).hexdigest()}
    (ARTIFACTS / 'metrics.json').write_text(json.dumps(metrics, indent=2), encoding='utf-8')
    fig, ax = plt.subplots(figsize=(12, 10))
    ConfusionMatrixDisplay(cm, display_labels=labels).plot(ax=ax, xticks_rotation=90, colorbar=False)
    fig.tight_layout()
    fig.savefig(ARTIFACTS / 'confusion_matrix.png', dpi=150)
    plt.close(fig)
    importance = pd.Series(final[-1].feature_importances_, index=x.columns).sort_values(ascending=False)
    importance.rename('importance').to_csv(ARTIFACTS / 'feature_importance.csv')
    demo = x_test.iloc[:25].copy()
    demo.to_csv(ARTIFACTS / 'demo_flows.csv', index=False)
    pd.DataFrame({'actual': y_test, 'predicted': pred}).to_csv(ARTIFACTS / 'test_predictions.csv', index=False)
    print(f'Saved {best}; test accuracy={metrics["test_accuracy"]:.4f}, macro F1={metrics["test_macro_f1"]:.4f}')


if __name__ == '__main__':
    main()
