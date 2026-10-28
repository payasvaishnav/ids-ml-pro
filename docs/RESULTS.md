# Measured results

Expanded benchmark run on 22 October 2026. All values below come from saved experiment artifacts.

Selected model: **Histogram Gradient Boosting**. Test accuracy **99.6141%**; macro F1 **0.9923**.

44,051 distinct flows, 77 features, 12,610 duplicate feature rows removed. Partitions: {'train': 26430, 'validation': 8810, 'test': 8811}.

| Configuration | Validation accuracy | Validation macro F1 | Training CV macro F1 |
|---|---:|---:|---:|
| Majority baseline | 49.24% | 0.0943 | 0.0943 ± 0.0000 |
| Decision Tree | 99.35% | 0.9641 | 0.9076 ± 0.0512 |
| Tuned Decision Tree | 99.27% | 0.9546 | 0.9081 ± 0.0511 |
| Random Forest | 98.94% | 0.9277 | 0.9166 ± 0.0460 |
| Extra Trees | 98.35% | 0.9481 | 0.8958 ± 0.0365 |
| Histogram Gradient Boosting | 99.33% | 0.9653 | 0.9296 ± 0.0404 |
| Top 20 features Tree | 98.42% | 0.9143 | 0.8948 ± 0.0550 |
| Stacking ensemble | 98.41% | 0.8503 | 0.8478 ± 0.0035 |

Three-fold CV uses training data. The tuned tree CV score reuses search folds and is a diagnostic, not an unbiased nested-CV estimate. Timing includes three CV fits plus one full training fit and excludes hyperparameter-search cost.

| Label | Precision | Recall | F1 | Test support |
|---|---:|---:|---:|---:|
| BENIGN | 0.9979 | 0.9949 | 0.9964 | 4338 |
| Bot | 0.9662 | 0.9931 | 0.9795 | 288 |
| BruteForce | 0.9975 | 0.9950 | 0.9962 | 398 |
| DoS | 0.9967 | 0.9994 | 0.9980 | 3286 |
| Infiltration | 1.0000 | 1.0000 | 1.0000 | 7 |
| PortScan | 1.0000 | 0.9692 | 0.9844 | 65 |
| WebAttack | 0.9930 | 0.9907 | 0.9918 | 429 |

Normal-versus-attack counts: 4316 true normal, 22 false alarms, 9 missed attacks, 4464 detected attacks.
Attack recall: 99.7988%. Benign false alarm rate: 0.5071%.

95% stratified bootstrap intervals, 300 resamples: accuracy 99.4779%–99.7390%; macro F1 0.9882–0.9955.

Intervals describe resampling uncertainty on these examples. They do not account for collection-level correlation, dataset shift or model selection. Rare-class support remains small.

Fixed sample test split reused from initial prototype. Internal benchmark, not independent external validation.
Random splitting can place related traffic in different partitions. Scores do not establish reliability on live networks or unknown attacks.

Reproduce: `.venv/Scripts/python train.py`, then `.venv/Scripts/python verify.py`. Seed: 42. Dataset SHA-256: `03ba3626a0f9bb73b90c56772893e68b0577285130891cd7d811542c17b032dd`.
The tuned tree, feature subset and stacking were retained even though validation scores were lower. No improvement is assumed merely from additional complexity.