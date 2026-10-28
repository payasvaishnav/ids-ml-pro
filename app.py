import json
import joblib
import pandas as pd
import streamlit as st
from ids import ARTIFACTS, ROOT, predict, read_csv

st.set_page_config(page_title='Network Intrusion Detection', page_icon='🛡️', layout='wide')
st.markdown('''<style>
.stApp {background: #f7f9fc;}
h1, h2, h3 {color: #10253f;}
div[data-testid="stMetric"] {background: white; padding: 18px; border-bottom: 3px solid #087e8b;}
.block-container {padding-top: 2.5rem;}
</style>''', unsafe_allow_html=True)
st.title('🛡️ Network Intrusion Detection')
st.write('Classify recorded network flows using machine learning.')
st.caption('Semester project • CICIDS2017 sampled data • Offline traffic analysis')
if not (ARTIFACTS / 'metrics.json').exists():
    st.info('Train the models first: .venv/Scripts/python train.py')
    st.stop()

@st.cache_resource
def load_model():
    return joblib.load(ARTIFACTS / 'model.joblib')

bundle = load_model()
metrics = json.loads((ARTIFACTS / 'metrics.json').read_text())
overview, detection, experiments, learn = st.tabs(['Model results', 'Detect attacks', 'Experiments', 'Understand the project'])
with overview:
    a, b, c = st.columns(3)
    a.metric('Selected model', metrics['best_model'])
    b.metric('Test accuracy', f"{metrics['test_accuracy']:.2%}")
    c.metric('Test macro F1', f"{metrics['test_macro_f1']:.4f}")
    st.write(f"{metrics['rows']:,} distinct flows • {metrics['features']} features • 60/20/20 train/validation/test split")
    st.subheader('Validation comparison')
    st.dataframe(pd.read_csv(ARTIFACTS / 'comparison.csv'), hide_index=True)
    st.caption('The winner is selected by validation macro F1, then refitted on train + validation. Test data is held out.')
    left, right = st.columns(2)
    with left:
        st.subheader('Test confusion matrix')
        st.image(str(ARTIFACTS / 'confusion_matrix.png'))
    with right:
        st.subheader('Most influential features')
        if (ARTIFACTS / 'importance_source.txt').exists():
            st.caption('Importance source: ' + (ARTIFACTS / 'importance_source.txt').read_text())
        importance = pd.read_csv(ARTIFACTS / 'feature_importance.csv', index_col=0).head(15)
        st.bar_chart(importance)
    st.subheader('Per-class test results')
    st.dataframe(pd.DataFrame({k:v for k,v in metrics['classification_report'].items() if k in metrics['labels']}).T)
    if 'binary_attack_recall' in metrics:
        a, b = st.columns(2)
        a.metric('Attack detection recall', f"{metrics['binary_attack_recall']:.2%}")
        b.metric('Benign false alarm rate', f"{metrics['binary_false_positive_rate']:.2%}")
        st.caption(metrics['test_note'])
with experiments:
    st.subheader('Reproducible benchmark')
    st.write('Eight configurations include a majority baseline, tuned tree, boosting, feature selection and stacking. Three-fold cross-validation runs inside the training partition. Validation macro F1 selects the final configuration.')
    st.image(str(ARTIFACTS / 'model_comparison.png')) if (ARTIFACTS / 'model_comparison.png').exists() else None
    if 'tuning_best_params' in metrics:
        st.subheader('Tree hyperparameter search')
        st.json(metrics['tuning_best_params'])
        st.caption('12 random configurations, three training folds each. Cross-validation for the selected tree settings is a search diagnostic, not an unbiased nested-CV estimate.')
        st.subheader('Sample uncertainty')
        st.write(f"Test accuracy 95% stratified bootstrap interval: {metrics['accuracy_ci95'][0]:.2%} to {metrics['accuracy_ci95'][1]:.2%}.")
        st.write(f"Macro F1 interval: {metrics['macro_f1_ci95'][0]:.4f} to {metrics['macro_f1_ci95'][1]:.4f}.")
        st.caption('300 bootstrap resamples. These intervals do not account for dataset shift or model selection uncertainty.')
        st.subheader('Inspect prediction errors')
        errors = pd.read_csv(ARTIFACTS / 'error_examples.csv')
        st.dataframe(errors[['actual', 'predicted']].value_counts().rename('flows').reset_index(), hide_index=True)
        st.download_button('Download error examples', errors.to_csv(index=False), 'error_examples.csv', 'text/csv')
        st.subheader('Dataset balance')
        st.bar_chart(pd.Series(metrics['class_counts'], name='Flows'))
with detection:
    st.write('Upload a CSV of flow measurements or try the supplied held-out examples.')
    st.caption('The CSV must use the same feature names and units as the training data. This app does not capture packets.')
    upload = st.file_uploader('Flow CSV', type=['csv'])
    demo = st.checkbox('Use demo flows', value=upload is None)
    try:
        frame = read_csv(upload) if upload is not None else (read_csv(ARTIFACTS / 'demo_flows.csv') if demo else None)
        if frame is not None:
            if len(frame) > 50000:
                st.error('Upload at most 50,000 rows at a time.')
            elif len(frame) == 0:
                st.error('CSV contains no rows.')
            elif st.button('Analyze flows', type='primary'):
                result = predict(bundle, frame)
                st.success(f"Analyzed {len(result)} flows; {(result['Traffic status'] == 'Attack').sum()} predicted attacks.")
                st.dataframe(result[['Predicted label', 'Traffic status', 'Model confidence']], hide_index=True)
                st.caption('Confidence is the model’s score, not a guarantee or a calibrated probability of a real attack.')
                st.download_button('Download predictions', result.to_csv(index=False), 'predictions.csv', 'text/csv')
    except (ValueError, pd.errors.ParserError, UnicodeDecodeError) as exc:
        st.error(str(exc))
    st.download_button('Download example CSV', (ARTIFACTS / 'demo_flows.csv').read_bytes(), 'demo_flows.csv', 'text/csv')
with learn:
    guide = ROOT / 'docs' / 'VIVA_MASTERCLASS.md'
    if guide.exists():
        st.download_button('Download technical viva guide', guide.read_bytes(), 'VIVA_MASTERCLASS.md', 'text/markdown')
    report = ROOT / 'deliverables' / 'IDS_Project_Report.pdf'
    if report.exists():
        st.download_button('Download project report', report.read_bytes(), 'IDS_Project_Report.pdf', 'application/pdf')
    st.markdown('''### How it works
1. Each row describes one network flow. Columns measure traffic properties; `Label` is the known traffic category.
2. We remove duplicate flows and split the data before fitting preprocessing or models.
3. We compare a baseline, trees, boosting and stacking, including tuning and a feature-selection experiment.
4. We compare models on validation data and evaluate the selected model on untouched test data.
5. The saved model predicts labels for new CSV rows with matching measurements.

**Accuracy** measures the fraction of correct predictions. **Precision** asks how many predicted attacks of a class were correct. **Recall** asks how many actual examples of a class were found. **F1** balances precision and recall. **Macro F1** gives every class equal weight.

This is an educational prototype using a sampled historical dataset. A random holdout can contain related flows, so high scores do not prove performance on new networks or unknown attacks. See the project guide for limitations and viva preparation.
''')
