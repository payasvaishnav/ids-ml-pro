# Beginner's guide and submission material

The expanded submission now compares eight configurations and selects Histogram Gradient Boosting. For the current technical explanation, use `docs/VIVA_MASTERCLASS.md`; for measured results, use `docs/RESULTS.md`. The original three-model introduction below is retained as beginner background. Final submission files are in `deliverables/`.

## Your project in one sentence

“My project learns patterns from labeled network traffic records and predicts whether a new recorded flow is benign or belongs to a known attack category.”

A network is how computers communicate. A packet is a small unit of transmitted data. A flow summarizes a related exchange of packets. An intrusion is malicious activity; an intrusion detection system identifies suspicious activity. Machine learning learns a mapping from examples rather than requiring us to manually write every detection rule.

## The minimum concepts to learn

- **Dataset:** a table of examples. One row is a flow; feature columns describe it; `Label` gives its known category.
- **Feature:** an input measurement, such as flow duration, packet count or average packet size.
- **Supervised learning:** learning using inputs with known labels.
- **Training:** fitting the model's rules from examples.
- **Validation:** comparing candidate models on examples excluded from fitting.
- **Testing:** estimating the final model's performance on separate examples.
- **Prediction:** applying the fitted model to new measurements.
- **Overfitting:** memorizing training patterns that fail to generalize.
- **Data leakage:** allowing information from evaluation data to affect model fitting or selection.
- **Class imbalance:** one label occurs much more often than another; accuracy can hide poor rare-class detection.

Decision Tree makes a sequence of questions such as “is packet count above a threshold?” Random Forest combines trees trained with randomness in examples and features. Extra Trees introduces additional randomness into split thresholds. Ensembles reduce dependence on one tree, but require more computation. We use balanced class weights to give scarce classes greater influence during fitting. We do not use SMOTE or pretend we implemented advanced research ensembles.

## Report draft

**Title:** Network Intrusion Detection Using Tree-Based Machine Learning

**Abstract:** This project implements an educational intrusion detection prototype using recorded network flow measurements from a sampled CICIDS2017 dataset. Decision Tree, Random Forest and Extra Trees classifiers are compared using a validation partition. The selected model is evaluated on a held-out test partition using accuracy, macro F1, per-class precision and recall, and a confusion matrix. A local web dashboard displays experimental results and predicts traffic categories from uploaded CSV files. The prototype demonstrates a reproducible workflow from preprocessing to inference. Results apply to the sampled dataset and do not establish deployment performance or unknown-attack detection.

**Problem statement:** Manually inspecting many network records is difficult. We investigate whether tree classifiers can learn useful distinctions between benign traffic and labeled attack categories.

**Objectives:** Prepare and validate flow data; compare three classifiers; evaluate with metrics sensitive to class imbalance; save the selected model; provide a usable prediction interface.

**Related work:** The project is inspired by Western OC2 Lab's IDS-ML repository and its tree-based IDS paper (Yang et al., GLOBECOM 2019). The original repository also contains more advanced research systems. This submission implements a narrower educational workflow and credits the original dataset sample and research.

**System architecture:** Labeled flow CSV → cleaning and deduplication → stratified train/validation/test partitions → training-only imputation and classifier fitting → validation comparison → refit selected model → test evaluation → save pipeline → dashboard CSV inference.

**Implementation:** Python, pandas, scikit-learn, matplotlib, joblib and Streamlit. The seed is fixed at 42. Model settings are visible in `train.py`. The input has numeric flow features and a `Label` column; output is a predicted category and the model's confidence score.

**Results:** Use `docs/RESULTS.md`, generated from the actual run, and the charts in `artifacts/`. Report both accuracy and macro F1, the number of flows, duplicate removal, split sizes and weaker classes. Do not substitute scores from the research papers or describe the random holdout as an external validation dataset.

**Limitations:** Historical sampled data, correlated flows across a random split, no chronological external evaluation, no live packet extraction, no traffic blocking, no demonstrated detection of unknown attacks, uncalibrated confidence, and sensitivity to compatible input features. Identical features with conflicting labels are collapsed by keeping their first occurrence during deduplication; this can remove ambiguous examples.

**Future work:** Evaluate by day or capture session; assess a second dataset with compatible measurements; tune hyperparameters using training/validation data; examine false negatives; calibrate probabilities on a separate validation set; integrate a compatible flow extractor and measure throughput.

**Conclusion:** The project demonstrates a complete offline intrusion classification workflow and an interactive demo. Its evaluation provides evidence for the sampled benchmark setting, with the limitations above.

Add your name, roll number, faculty details and college-required formatting when preparing the final submission. The references are in the README.

## Five-minute demo

1. Explain the problem: classify recorded normal and malicious network traffic.
2. Open Model results. Show the dataset size and model comparison; explain validation selects the winner.
3. Show macro F1 and the confusion matrix. Rows are actual labels; columns are predicted labels; off-diagonal entries are errors.
4. Open Detect attacks, use demo flows and click Analyze flows. Explain that these examples came from the held-out test partition.
5. Download predictions. Show the code paths for data preparation, model fitting and inference.
6. Close by explaining the scope and one improvement: testing on a different capture day.

## Viva practice

**Why this project?** It combines supervised learning with a concrete network security application and supports comparison of multiple classifiers.

**Why these algorithms?** They work well with numeric tabular features, capture nonlinear relationships and provide feature importance. Their performance must still be checked empirically.

**Why no scaling?** These tree classifiers split individual features by thresholds, so standard normalization is not necessary for this implementation.

**Why split before preprocessing?** Learned imputation values should be estimated from fitting data, not from held-out examples.

**Why macro F1?** It averages F1 equally over classes, making rare-class performance visible even when a common class dominates accuracy.

**What is a false negative?** A missed attack, such as an attack predicted as benign. A false positive is benign traffic flagged as malicious. Both matter, with different operational costs.

**What does confidence mean?** The largest class score produced by the fitted classifier. It is not proof that the event is malicious and is not calibrated in this project.

**Can it detect a new attack?** We have not demonstrated that. This supervised classifier predicts the categories it learned.

**Is it real time?** This version analyzes CSV flow records offline. Live operation needs a compatible flow extraction stage plus latency and throughput testing.

**What is your contribution?** A simplified reproducible pipeline, validation-based selection, deduplication, saved inference pipeline, dashboard and measured evaluation. The research ideas and sample data are credited upstream.

## Suggested presentation outline

1. Title and problem
2. What an IDS does and project scope
3. Dataset and features
4. Pipeline and split strategy
5. Three algorithms
6. Measured comparison and test results
7. Dashboard demonstration
8. Limitations, future work and references

## Learning sequence

First run the demo. Next read the minimum concepts above. Then read `ids.py`, followed by `train.py`, then `app.py`. Practice explaining one row of input, how a model is selected, and why test data is separate. Finally rehearse the demo and viva answers in your own words.
