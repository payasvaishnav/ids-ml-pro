# Your project explained for the viva

Payas Vaishnav · 23BCP430 · CSE PDEU · Semester 7 · Dr Nandini Modi

Read this in order once, then practice the opening, the demo and the questions aloud. Understand the reasoning rather than memorizing every number.

## 1 Your opening explanation

“My project is an offline network intrusion classification system. It takes recorded network flow measurements and predicts whether the traffic is benign or belongs to a known attack category. I used a sampled CICIDS2017 dataset, cleaned duplicate flows, and compared eight configurations including a baseline, tree models, boosting and stacking. I selected the model using validation macro F1. Histogram Gradient Boosting achieved 99.61% accuracy and 0.9923 macro F1 on our internal test split. The project also includes a dashboard for CSV prediction and inspection of errors.”

If asked about the source: “The problem and sample data come from Western OC2 Lab’s IDS-ML repository. My submission is an educational adaptation with its own benchmark pipeline and dashboard. I credit their work and do not claim to reproduce all their research systems.”

## 2 What is happening on a network

Computers communicate by exchanging packets. A packet is a small unit of network data with addressing and protocol information. A **flow** groups related packets, often by source and destination addresses and ports and transport protocol, with timeouts determining when a flow ends. Bidirectional flow summaries describe both directions of an exchange.

For example, your laptop requesting a web page produces packets to a server and packets returning from it. A flow extractor can summarize the exchange as its duration, number of packets in each direction, packet length statistics and timing statistics. Your CSV already contains these summaries. The model does not need the text of the web page.

An **intrusion detection system** identifies suspicious activity. An intrusion prevention system can take action such as blocking it. Your application classifies records and displays predictions. It does not block traffic.

This is **network-based** analysis because the inputs describe network communication. Host-based intrusion detection instead examines evidence such as operating-system events and process behavior.

## 3 What attacks mean

| Dataset category | Plain explanation |
|---|---|
| BENIGN | Traffic labeled as normal in the dataset |
| Bot | Traffic associated with an automated malicious agent |
| BruteForce | Repeated guesses at credentials |
| DoS | Activity intended to exhaust resources or disrupt service |
| Infiltration | Activity associated with gaining or expanding unauthorized access |
| PortScan | Probing services or ports to discover what is available |
| WebAttack | Attacks targeting web applications |

These are the sample's labels. A predicted category is a learned classification, not proof of intent. A traffic pattern can overlap with legitimate activity.

## 4 What the table contains

One row is one flow. There are **77 numeric input columns** and a **Label** target column. The source sample contains **56,661 rows**. Removing **12,610 duplicate feature rows** leaves **44,051 distinct feature vectors**.

Examples of actual features:

- `Flow Duration`: elapsed duration of the flow.
- `Total Fwd Packets`: packet count in the forward direction.
- `Total Backward Packets`: packet count in the reverse direction.
- `Fwd Packet Length Mean`: average length of forward packets.
- `Flow Bytes/s`: byte transfer rate.
- `Flow IAT Mean`: mean time between packets. IAT means inter-arrival time.
- `SYN Flag Count`: a count related to TCP connection signaling.

Why can these help? An attack may change timing, volume, direction balance or connection behavior. A classifier learns combinations of measurements associated with labels. No single feature universally proves an attack.

We use the repository's **sample of CICIDS2017**, not the complete original capture. The sample contains seven grouped labels, and the script preserves them. It does not merge the original fine-grained labels itself.

## 5 The machine learning task

This is **supervised learning** because the training examples have known labels. It is **classification** because outputs are categories. The main task is **multiclass classification**, because there are seven possible categories.

In mathematical language, each flow is a vector x in R^77. The model learns a function f(x) that returns one of seven labels. Training chooses parameters that reduce a classification loss on labeled examples. Inference applies the fitted function to a new vector.

The dashboard also creates a **binary summary**: BENIGN becomes Normal and every other predicted label becomes Attack. It does not train a second binary model.

## 6 Cleaning and its technical reasoning

The code in `ids.py` trims column names and labels, removes missing or empty labels and removes exported dataframe index columns named `Unnamed:...`. Those indices are administrative data rather than traffic measurements.

Feature values are converted to numbers. Unparseable values and infinities become missing values. Infinite rates can arise in flow datasets when a rate denominator is zero or very small. A missing value should not be interpreted as an extremely large observed rate.

**Median imputation** replaces a missing measurement with the training median for that column. The median is less sensitive to extreme values than the mean. This is a practical baseline policy, not a claim that it is always optimal.

Crucially, the imputer fits inside each model pipeline. If we computed medians using the test data, the training process would acquire information about evaluation data. That is data leakage.

We remove exact duplicate feature vectors **before splitting**. Otherwise an identical flow could appear in both training and testing, making apparent generalization partly memorization. The current policy keeps the first row when identical feature vectors have conflicting labels. That policy discards ambiguity and is a limitation to mention if asked. Exact deduplication cannot eliminate related but non-identical flows.

There are constant measurements in the sample. The ANOVA selection experiment records warnings for them because their within-class variance is zero. They carry no discrimination in that fitting partition. They are not evidence that the benchmark failed.

## 7 Why three partitions

| Partition | Rows | Purpose |
|---|---:|---|
| Training | 26,430 | Fit candidate models, run cross-validation and tune tree settings |
| Validation | 8,810 | Choose a configuration using macro F1 |
| Test | 8,811 | Report the selected model's performance |

Training is like studying worked examples. Validation is a practice examination used to choose your study approach. Testing is an examination after that choice. Repeatedly changing the approach because of test results would make the reported test result optimistic.

The split is **stratified**, so label proportions are approximately preserved. That matters because Infiltration has only 36 distinct examples. A careless split could omit a rare class from a partition. Random seed 42 makes the random partition repeatable; it has no special statistical significance.

After selection, we refit the chosen configuration on training plus validation, totaling **35,240 flows**. Validation can now be used for fitting because its model-selection purpose is finished. The test data is still excluded from fitting.

Be honest about history: the same fixed test partition was evaluated in the earlier three-model prototype. The expanded results are therefore an internal benchmark, not independent external validation. The expanded script chooses the winner using validation scores.

## 8 Three-fold cross-validation

Within the training partition, divide examples into three stratified folds. Fit on two and score on the remaining one. Repeat so each fold is evaluated once. The mean macro F1 summarizes the three scores; standard deviation describes fold-to-fold dispersion.

This reduces dependence on a single training subdivision. It does not make the dataset independent or eliminate scarce-class uncertainty. The separate validation set still chooses the final configuration.

The tuned tree uses these same training folds during search and in its later CV diagnostic. That reused score is not an unbiased nested-CV estimate of the entire search procedure. Say this if asked about tuning optimism.

## 9 Decision Tree

A tree repeatedly divides examples by asking a question such as “is flow duration below a learned threshold?” A path from the root to a leaf gives a sequence of feature tests. The leaf assigns class scores based on the fitting examples that reach it, including any class weights.

A common split criterion is **Gini impurity**:

`Gini = 1 − sum(p_k²)`

Here p_k is the class proportion in a node. A pure node has Gini zero. The tree chooses splits that reduce weighted child impurity relative to the parent.

Our original comparator limits maximum depth to 20 and uses balanced class weights. Deep trees can fit complex boundaries but can memorize noise. Depth and minimum leaf size control that complexity.

## 10 Random Forest and Extra Trees

**Random Forest** combines many decision trees. Each tree typically learns from a bootstrap sample, and split construction considers a random subset of features. Averaging class scores reduces dependence on the peculiarities of one tree. This often reduces variance, but more trees cost memory and computation. Our configuration uses 120 trees.

**Extra Trees** also combines randomized trees but introduces additional randomness in split thresholds. In our scikit-learn configuration, bootstrap is false by default, so trees use the fitting dataset rather than bootstrap resamples. It also uses 120 trees. Extra randomness can reduce variance while increasing bias; the net effect must be measured.

Neither method is guaranteed to beat a single tree on every dataset, metric or split.

## 11 Histogram Gradient Boosting

This is the selected configuration. Boosting builds a model sequentially. New trees learn corrections that reduce the current model's loss. For classification, this means following information from gradients of a classification loss, rather than simply training an independent tree and voting.

A simplified update is:

`F_next(x) = F_current(x) + learning_rate × correction_tree(x)`

For multiclass classification, the model maintains class scores and converts them to probabilities using a softmax. The loss penalizes assigning low probability to the correct label. Saying “it only trains on misclassified rows” is inaccurate: gradient-based corrections can use all fitting examples with different correction targets.

The **histogram** implementation bins continuous feature values into a bounded number of bins. Candidate split calculations operate on these bins, reducing the cost of searching many possible numeric thresholds.

Our explicit settings are `max_iter=120`, `max_leaf_nodes=15`, balanced class weights and random seed 42. A maximum is a cap; automatic early stopping can stop before it. Do not say it necessarily trains exactly 120 iterations. The default learning rate is 0.1 in the verified environment. With multiple classes, a boosting iteration can contain a tree per class.

The saved final model actually stopped after **46 boosting iterations**, with **seven trees per iteration**, so it contains 322 small trees. Its early-stopping mechanism internally holds out 10% of the development data to monitor loss; that is separate from the external validation partition used to choose the algorithm, and it does not use the test set. These values were inspected from the saved model rather than inferred from the 120-iteration cap.

This implementation uses scikit-learn's HistGradientBoostingClassifier. It is **not XGBoost**, even though both belong to the broader gradient boosting family.

## 12 Hyperparameter tuning

Parameters are values learned from data, such as split thresholds. Hyperparameters are choices controlling training, such as maximum depth.

The tree search considers five depth options, four minimum-leaf options and two criteria. That is 5 × 4 × 2 = **40 combinations**. RandomizedSearchCV samples **12** of them and evaluates each using **three training folds**, for 36 candidate-fold fits, plus its refit. The scoring objective is macro F1.

The chosen tree settings are unlimited maximum depth, minimum leaf size 1 and Gini criterion. Its validation macro F1 is lower than the original depth-20 tree. This is a useful outcome: the setting that looks best on training CV does not necessarily look best on another sample. Tuning is an experiment, not a guaranteed improvement.

## 13 Feature selection experiment

SelectKBest uses ANOVA F scores to select 20 out of 77 inputs within each fitting pipeline. ANOVA compares between-class mean differences with within-class variation for an individual feature.

This is a **filter method** because selection uses a feature-level statistical score rather than repeatedly fitting the final classifier to candidate subsets. It is **univariate**, so it can miss interactions where two features matter together even though each looks weak alone.

The 20-feature tree has validation macro F1 around 0.9143, below the original tree's 0.9641. Removing inputs loses useful information in this configuration. We keep the negative result to explain the tradeoff. The input validator still requires the full CSV schema because selection occurs internally in the pipeline.

## 14 Stacking

Stacking trains base models and then trains another model using their predictions as inputs. Our base models are a depth-20 Decision Tree and a 60-tree Extra Trees classifier. The final model is logistic regression.

To train the meta-model, scikit-learn uses cross-validated base predictions. Training the meta-model on base predictions from the same rows used to fit those base models could create unrealistic confidence. Out-of-fold predictions reduce that problem.

The tested stacking configuration achieves validation macro F1 around 0.8503. It does not help here. Potential explanations include highly related base learners, scarce classes and the chosen meta-model, but these are hypotheses, not established causes. Additional experiments would be needed to identify why.

## 15 Class imbalance and weighting

BENIGN has 21,688 distinct flows and Infiltration only 36. A model that always predicts BENIGN gets approximately 49.24% validation accuracy while learning no useful attack discrimination.

Balanced class weights increase the fitting influence of rare labels. A common balanced weight for class k is `N / (K × N_k)`, where N is the fitting sample count, K the number of labels and N_k the count for class k. Weighting changes the loss or split calculations; it does not generate additional examples.

We do **not** use SMOTE, oversampling or synthetic attack data. Rare examples remain rare even when weighted, so uncertainty still matters.

## 16 Evaluation metrics

For binary attack detection, call Attack the positive class:

- True positive: attack predicted Attack.
- True negative: benign predicted Normal.
- False positive: benign predicted Attack, a false alarm.
- False negative: attack predicted Normal, a missed attack.

`Accuracy = correct predictions / all predictions`

`Precision = TP / (TP + FP)`

`Recall = TP / (TP + FN)`

`F1 = 2PR / (P + R)`

Precision answers “when we predict this class, how often are we correct?” Recall answers “of the real examples of this class, how many do we find?” F1 is the harmonic mean, so a low precision or recall lowers it.

For seven classes, each class can be treated as positive against all the others. **Macro F1** averages the seven class F1 values equally. **Weighted F1** averages using class support, so common labels dominate more. **Support** is the number of actual evaluation examples for that label.

Do not confuse multiclass accuracy with binary detection accuracy. Predicting one attack type as a different attack is a multiclass mistake but still a correct attack-versus-normal decision.

## 17 Your measured results

| Configuration | Validation macro F1 |
|---|---:|
| Majority baseline | 0.0943 |
| Decision Tree | 0.9641 |
| Tuned Decision Tree | 0.9546 |
| Random Forest | 0.9277 |
| Extra Trees | 0.9481 |
| Histogram Gradient Boosting | 0.9653 |
| Top 20 features Tree | 0.9143 |
| Stacking ensemble | 0.8503 |

We select boosting using the **validation** column. Its lead over the original tree is small. Do not claim a statistically established victory or universal superiority.

Final internal test results after refitting:

- Test flows: **8,811**.
- Correct multiclass predictions: **8,777**.
- Multiclass mistakes: **34**.
- Multiclass accuracy: **99.6141%**.
- Macro F1: **0.9923**.
- Benign flows flagged as attacks: **22 of 4,338**.
- Attack flows predicted as benign: **9 of 4,473**.
- Attack detection recall: **99.7988%**.
- Benign false alarm rate: **0.5071%**.

Of the 34 multiclass errors, 31 cross the normal/attack boundary and three confuse one attack category with another.

Bot has the lowest class F1, about **0.9795**. Infiltration has a perfect test score but only **seven test examples**, which is insufficient evidence for reliable generalization.

## 18 Confidence intervals and confidence scores

These are different ideas.

A **bootstrap interval** describes variation in an evaluation metric when resampling observed test examples. We create 300 resamples while preserving each class count and calculate percentile intervals. The measured 95% intervals are approximately 99.48%–99.74% for accuracy and 0.9882–0.9955 for macro F1.

These intervals do not account for changing networks, capture-day correlation or model-selection uncertainty. A narrow interval on a biased sample does not establish real-world reliability.

A **prediction confidence** is the largest class probability score returned by the classifier for one flow. It is not guaranteed to equal the real probability that a prediction is correct. Our probabilities are not calibrated on a separate calibration set. Do not describe 99% confidence as a 99% real-world guarantee.

## 19 What feature importance means here

The saved boosting model does not expose impurity importance through the API used. The displayed feature-importance chart comes from a separately fitted **diagnostic Decision Tree**.

In a tree, impurity importance aggregates how much splits on a feature reduce impurity, weighted by the fitting samples involved. It indicates usefulness to that fitted tree, not causality, and correlated features can divide or distort importance. It also does not explain the winning boosting model. Say the chart's source explicitly.

## 20 The software architecture

`ids.py` reads and validates CSVs and runs prediction. `train.py` performs tuning, CV, validation selection, final fitting and evaluation. `app.py` creates the Streamlit interface. `verify.py` checks inference, invalid schema rejection and a real Streamlit demo interaction. `IDS_Experiment.ipynb` is an executed walkthrough of the recorded experiment and predictions.

The saved `model.joblib` bundle contains the fitted pipeline, feature names and selected model name. A pipeline keeps preprocessing and classification together so prediction uses the same transformations as fitting.

`predict()` checks required columns, orders them consistently, converts numeric values and applies the saved pipeline. It creates predicted labels, maximum class scores and the normal/attack summary. A row with no usable numeric measurements is rejected. Some invalid values become missing and are imputed, so strict upstream data-quality checking would be useful for deployment.

The dashboard accepts up to 50,000 rows per upload. This is an application limit, not a measured throughput guarantee. Uploaded rows are not automatically used to retrain the model.

## 21 Why no normalization or deep learning

Trees compare values with thresholds. Changing units by a positive linear transformation preserves the feature ordering and corresponding possible partitions, so standard scaling is generally unnecessary for these tree models. The stacking logistic regression operates on bounded base-model probability features rather than raw flow measurements.

Deep learning is not required simply because a problem is about attacks. Tabular features and a modest sample make tree methods a sensible starting point. Choosing neural networks would require an appropriate comparison, tuning and computational justification.

## 22 Honest limitations

The application is offline, uses historical sampled data and predicts learned categories. It does not capture live packets, block traffic or demonstrate zero-day detection. A new type of attack can be misclassified as one of the known labels or benign.

Random partitioning may share related traffic patterns across partitions even after exact deduplication. The same internal test split appeared in the earlier prototype. The sample lacks suitable timestamps and session identifiers for an honest chronological split. We should use the full dataset's metadata for the next evaluation rather than pretend a random split is time-based.

Real deployment would require compatible flow extraction, unit and schema validation, an independent evaluation, drift monitoring, probability or threshold calibration, and latency and throughput measurements. These are future work, not implemented features.

## 23 The five minute demo

1. Launch with `.venv\Scripts\python.exe -m streamlit run app.py`. Keep the terminal running. Internet is not required once dependencies, data and model are local.
2. Deliver the opening explanation from Section 1.
3. In Model results, explain the validation comparison and then the final test metrics. The two sets serve different purposes.
4. Show the confusion matrix. Rows are actual labels, columns are predicted labels. Point to a non-diagonal count.
5. Open Detect attacks. Use demo flows and click Analyze flows. These are 25 held-out test rows with labels excluded from the input.
6. Explain the predicted label, traffic status and uncalibrated confidence. Download predictions.
7. Open Experiments. Show tuning settings, error groups and class imbalance. Explain one negative finding and one limitation.
8. If asked for code, open `train.py` for the candidate dictionary and validation selection, then `ids.py` for inference.

Never generate an actual network attack during the presentation. The supplied historical records demonstrate the classifier without requiring network access.

## 24 Short answers to likely questions

**What is your novelty?** The contribution is an integrated educational implementation with a reproducible comparison, tuning, feature ablation, saved inference and dashboard. I do not claim a new intrusion detection algorithm.

**Why macro F1?** The data is imbalanced. It gives rare classes equal weight instead of allowing BENIGN and DoS to dominate the comparison.

**Why did boosting win?** It achieved the highest validation macro F1 in this configured experiment. Its sequential correction mechanism can model nonlinear relationships, but our experiment does not prove the exact cause of the ranking.

**Why did stacking fail?** This configured stack scored lower. Related base models, the meta-model or scarce classes may contribute, but identifying the cause needs controlled follow-up experiments.

**Why is the test score higher than the validation score?** The final model fits on more data after selection, and the partitions differ. Sampling variation is substantial for rare labels. A higher test score alone is not evidence of leakage or proof of a better model.

**What is overfitting?** Learning fitting-specific patterns that do not generalize. We use held-out evaluation and compare folds, with complexity controls such as leaf limits. We do not claim these eliminate overfitting.

**How do you prevent leakage?** Remove exact duplicates before splitting, fit imputation and feature selection within fitting pipelines, and use validation rather than test scores for configuration selection. Related-flow dependence and historical test reuse remain limitations.

**Why does the baseline matter?** It shows what happens without useful feature learning and exposes how imbalanced data can give misleading accuracy.

**Is the feature chart explaining boosting?** No. It is explicitly a separate diagnostic Decision Tree because the chosen boosting interface does not provide that impurity importance.

**How is the result reproducible?** The project saves a dataset checksum, fixed seed, package versions, partition IDs, training settings and actual predictions. The benchmark can be rerun and its scores recalculated.

**What would you improve first?** Evaluate on separate capture days or networks using full collection metadata. That addresses generalization more directly than adding another classifier.

## 25 Tonight's study order

Spend 20 minutes on Sections 1–7, 30 minutes on the algorithms and metrics, 20 minutes running the demo twice, and 20 minutes answering the viva questions aloud without reading. Then review the code's candidate dictionary, split calls and inference function. Keep the report, PPT, notebook and a local copy of results available offline.

If a question goes beyond your evidence, say: “I have not measured that in this version. Here is how I would evaluate it.” That is a technically sound answer.
