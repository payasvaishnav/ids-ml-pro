"""Expanded reproducible IDS benchmark. See README for evaluation scope."""
import argparse
import hashlib
import json
import os
import platform
import time
from datetime import datetime, timezone
from pathlib import Path
os.environ.setdefault('MPLCONFIGDIR', str(Path(__file__).resolve().parent / '.matplotlib'))
import joblib
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import sklearn
from sklearn.base import clone
from sklearn.dummy import DummyClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier, ExtraTreesClassifier, HistGradientBoostingClassifier, StackingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.feature_selection import SelectKBest, f_classif
from sklearn.impute import SimpleImputer
from sklearn.pipeline import make_pipeline
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_validate, RandomizedSearchCV
from sklearn.metrics import accuracy_score, f1_score, classification_report, confusion_matrix, ConfusionMatrixDisplay
from ids import DATA, ARTIFACTS, load_dataset

SEED = 42


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--data', default=str(DATA))
    args = parser.parse_args()
    x, y, duplicates = load_dataset(args.data)
    x_dev, x_test, y_dev, y_test = train_test_split(x, y, test_size=.2, stratify=y, random_state=SEED)
    x_train, x_val, y_train, y_val = train_test_split(x_dev, y_dev, test_size=.25, stratify=y_dev, random_state=SEED)
    cv = StratifiedKFold(n_splits=3, shuffle=True, random_state=SEED)
    def pipe(estimator):
        return make_pipeline(SimpleImputer(strategy='median', keep_empty_features=True), estimator)
    tree = DecisionTreeClassifier(class_weight='balanced', random_state=SEED)
    tune = RandomizedSearchCV(pipe(tree), {
        'decisiontreeclassifier__max_depth': [8, 12, 20, 30, None],
        'decisiontreeclassifier__min_samples_leaf': [1, 2, 4, 8],
        'decisiontreeclassifier__criterion': ['gini', 'entropy']},
        n_iter=12, scoring='f1_macro', cv=cv, n_jobs=2, random_state=SEED)
    print('Tuning tree on training partition only...', flush=True)
    tune.fit(x_train, y_train)
    candidates = {
        'Majority baseline': pipe(DummyClassifier(strategy='most_frequent')),
        'Decision Tree': pipe(clone(tree).set_params(max_depth=20)),
        'Tuned Decision Tree': clone(tune.best_estimator_),
        'Random Forest': pipe(RandomForestClassifier(n_estimators=120, class_weight='balanced', n_jobs=2, random_state=SEED)),
        'Extra Trees': pipe(ExtraTreesClassifier(n_estimators=120, class_weight='balanced', n_jobs=2, random_state=SEED)),
        'Histogram Gradient Boosting': pipe(HistGradientBoostingClassifier(max_iter=120, max_leaf_nodes=15, class_weight='balanced', random_state=SEED)),
        'Top 20 features Tree': make_pipeline(SimpleImputer(strategy='median', keep_empty_features=True), SelectKBest(f_classif, k=min(20, x.shape[1])), clone(tree).set_params(max_depth=20)),
        'Stacking ensemble': pipe(StackingClassifier(estimators=[
            ('dt', clone(tree).set_params(max_depth=20)),
            ('et', ExtraTreesClassifier(n_estimators=60, class_weight='balanced', n_jobs=2, random_state=SEED))],
            final_estimator=LogisticRegression(max_iter=1000, class_weight='balanced'), cv=3, n_jobs=1)),
    }
    rows = []
    for name, model in candidates.items():
        start = time.perf_counter()
        scores = cross_validate(model, x_train, y_train, cv=cv, scoring='f1_macro', n_jobs=1)
        model.fit(x_train, y_train)
        elapsed = time.perf_counter() - start
        pred = model.predict(x_val)
        rows.append({'model': name, 'validation_accuracy': accuracy_score(y_val, pred),
            'validation_macro_f1': f1_score(y_val, pred, average='macro'),
            'cv_macro_f1_mean': float(scores['test_score'].mean()),
            'cv_macro_f1_std': float(scores['test_score'].std()), 'benchmark_seconds': elapsed})
        print(rows[-1], flush=True)
    best = max((r for r in rows if r['model'] != 'Majority baseline'), key=lambda r: r['validation_macro_f1'])['model']
    final = clone(candidates[best]).fit(x_dev, y_dev)
    start = time.perf_counter()
    pred = final.predict(x_test)
    inference_seconds = time.perf_counter() - start
    labels = final.classes_.tolist()
    truth = y_test.to_numpy()
    cm = confusion_matrix(truth, pred, labels=labels)
    binary = confusion_matrix(truth != 'BENIGN', pred != 'BENIGN', labels=[False, True])
    rng = np.random.default_rng(SEED)
    groups = [np.flatnonzero(truth == label) for label in labels]
    boot = []
    for _ in range(300):
        ix = np.concatenate([rng.choice(g, len(g), replace=True) for g in groups])
        boot.append([accuracy_score(truth[ix], pred[ix]), f1_score(truth[ix], pred[ix], average='macro', labels=labels)])
    intervals = np.quantile(boot, [.025,.975], axis=0)
    metrics = {'best_model': best, 'test_accuracy': accuracy_score(truth, pred),
        'test_macro_f1': f1_score(truth, pred, average='macro'),
        'classification_report': classification_report(truth, pred, output_dict=True, zero_division=0),
        'labels': labels, 'confusion_matrix': cm.tolist(), 'binary_confusion_matrix': binary.tolist(),
        'binary_false_positive_rate': float(binary[0,1] / binary[0].sum()),
        'binary_attack_recall': float(binary[1,1] / binary[1].sum()),
        'accuracy_ci95': intervals[:,0].tolist(), 'macro_f1_ci95': intervals[:,1].tolist(),
        'inference_seconds': inference_seconds, 'rows': len(x), 'duplicates_removed': duplicates, 'features': len(x.columns),
        'split': {'train': len(x_train), 'validation': len(x_val), 'test': len(x_test)},
        'class_counts': y.value_counts().to_dict(), 'seed': SEED, 'tuning_best_params': tune.best_params_,
        'cv_folds': 3, 'bootstrap_repeats': 300, 'dataset_sha256': hashlib.sha256(Path(args.data).read_bytes()).hexdigest(),
        'python': platform.python_version(), 'sklearn': sklearn.__version__, 'created_utc': datetime.now(timezone.utc).isoformat(),
        'test_note': 'Fixed sample test split reused from initial prototype. Internal benchmark, not independent external validation.'}
    ARTIFACTS.mkdir(exist_ok=True)
    joblib.dump({'model': final, 'features': x.columns.tolist(), 'name': best}, ARTIFACTS / 'model.joblib')
    (ARTIFACTS / 'metrics.json').write_text(json.dumps(metrics, indent=2), encoding='utf-8')
    comparison = pd.DataFrame(rows)
    comparison.to_csv(ARTIFACTS / 'comparison.csv', index=False)
    pd.DataFrame(tune.cv_results_).to_csv(ARTIFACTS / 'tuning.csv', index=False)
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 11, 'axes.spines.top': False, 'axes.spines.right': False})
    fig, ax = plt.subplots(figsize=(10,8))
    ConfusionMatrixDisplay(cm, display_labels=labels).plot(ax=ax, xticks_rotation=35, colorbar=False, cmap='Blues', values_format='d')
    fig.tight_layout(); fig.savefig(ARTIFACTS / 'confusion_matrix.png', dpi=160); plt.close(fig)
    fig, ax = plt.subplots(figsize=(10,5))
    ordered = comparison.sort_values('validation_macro_f1')
    ax.barh(ordered.model, ordered.validation_macro_f1, color=['#cbd5e1' if n == 'Majority baseline' else '#087e8b' for n in ordered.model])
    ax.set(xlim=(0,1.08), xlabel='Validation macro F1')
    for i,v in enumerate(ordered.validation_macro_f1): ax.text(v+.008,i,f'{v:.4f}', va='center')
    fig.tight_layout(); fig.savefig(ARTIFACTS / 'model_comparison.png', dpi=180); plt.close(fig)
    fig, ax = plt.subplots(figsize=(9,4))
    counts = y.value_counts().sort_values()
    ax.barh(counts.index, counts.values, color='#087e8b'); ax.set_xscale('log'); ax.set_xlabel('Distinct flows (log scale)')
    for i,v in enumerate(counts): ax.text(v*1.08,i,f'{v:,}', va='center')
    ax.set_xlim(10,60000); fig.tight_layout(); fig.savefig(ARTIFACTS / 'class_distribution.png', dpi=180); plt.close(fig)
    estimator = final[-1]
    if hasattr(estimator, 'feature_importances_'):
        cols = x.columns[final[-2].get_support()] if hasattr(final[-2], 'get_support') else x.columns
        importance = pd.Series(estimator.feature_importances_, index=cols)
        source = best
    else:
        diagnostic = clone(tree).set_params(max_depth=20).fit(SimpleImputer(strategy='median', keep_empty_features=True).fit_transform(x_dev), y_dev)
        importance = pd.Series(diagnostic.feature_importances_, index=x.columns)
        source = 'Diagnostic Decision Tree (not selected model)'
    importance = importance.sort_values(ascending=False)
    importance.rename('importance').to_csv(ARTIFACTS / 'feature_importance.csv')
    (ARTIFACTS / 'importance_source.txt').write_text(source, encoding='utf-8')
    fig, ax = plt.subplots(figsize=(9,5))
    importance.head(12).sort_values().plot.barh(ax=ax, color='#087e8b'); ax.set_xlabel('Impurity based importance'); fig.tight_layout()
    fig.savefig(ARTIFACTS / 'feature_importance.png', dpi=180); plt.close(fig)
    x_test.iloc[:25].to_csv(ARTIFACTS / 'demo_flows.csv', index=False)
    pd.DataFrame({'actual': truth, 'predicted': pred}).to_csv(ARTIFACTS / 'test_predictions.csv', index=False)
    errors = x_test.loc[truth != pred].copy()
    errors['actual'] = truth[truth != pred]; errors['predicted'] = pred[truth != pred]
    errors.to_csv(ARTIFACTS / 'error_examples.csv', index=False)
    train_ids, val_ids = set(x_train.index), set(x_val.index)
    pd.DataFrame({'row_id': x.index, 'partition': ['train' if i in train_ids else 'validation' if i in val_ids else 'test' for i in x.index]}).to_csv(ARTIFACTS / 'partitions.csv', index=False)
    print(f'Saved {best}; accuracy={metrics["test_accuracy"]:.4f}, macro F1={metrics["test_macro_f1"]:.4f}', flush=True)


if __name__ == '__main__':
    main()
