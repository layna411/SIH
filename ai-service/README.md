# EduResolve AI — AI Service Architecture & ML Pipeline

The EduResolve AI AI Service delivers natural language processing (NLP), multi-class grievance categorization, multi-tenant duplicate detection, explainable priority triage, and intelligent officer routing.

---

## 1. Architecture Overview

```text
ai-service/
├── artifacts/
│   ├── category_classifier.joblib  # Serialized scikit-learn TF-IDF + LogisticRegression pipeline
│   ├── model_metadata.json         # Artifact version, hyperparameters, class labels, and metadata
│   └── README.md                   # Model artifact registry
├── classifiers/
│   ├── category_classifier.py      # Category inference engine with calibrated confidence and fallback
│   └── train_classifier.py         # Reproducible model training pipeline with stratified train/test split
├── data/
│   ├── dataset_builder.py          # Labeled synthetic development dataset generator (150 examples, 10 classes)
│   └── training_dataset.json       # Versioned development dataset
├── evaluation/
│   ├── evaluate_classifier.py      # Reproducible model evaluation and report generator
│   ├── evaluation_metrics.py       # Metrics calculator (accuracy, macro/weighted P/R/F1, confusion matrix)
│   ├── evaluation_report.md        # Formatted markdown evaluation report
│   └── evaluation_results.json     # Machine-readable evaluation metrics
├── prioritization/
│   └── priority_recommender.py     # Transparent, rule-based urgency triage (safety threats, deadlines)
├── routing/
│   └── assignment_recommender.py   # Multi-tenant officer assignment recommendations
├── similarity/
│   └── duplicate_detector.py       # Multi-tenant institution-isolated duplicate grievance detector
└── README.md                       # This architecture documentation
```

---

## 2. Model Specifications

- **Model Type**: Scikit-learn Pipeline
  - Preprocessor: `TfidfVectorizer(ngram_range=(1, 2), max_features=2500, sublinear_tf=True, stop_words='english')`
  - Classifier: `LogisticRegression(C=1.0, class_weight='balanced', max_iter=1000, random_state=42)`
- **Version**: `v1.0.0-dev`
- **Supported Categories (10)**:
  `ACADEMIC`, `EXAM`, `FINANCE`, `SCHOLARSHIP`, `HOSTEL`, `INFRA`, `ADMIN`, `CONDUCT`, `SUPPORT`, `OTHER`
- **Confidence Calibration**: Employs softmax probability distributions. Inputs with maximum probability below `0.35` are explicitly marked as uncertain (`is_uncertain=True`) with human intake verification requested.
- **Inference Latency**: < 15ms on CPU (single-core x86_64).

---

## 3. Evaluation Metrics & Scientific Integrity

Evaluated on held-out test split (25% stratified test partition, 38 examples across 10 classes):
- **Overall Accuracy**: **63.16%**
- **Macro Precision**: **0.6983**
- **Macro Recall**: **0.6417**
- **Macro F1 Score**: **0.6299**
- **Weighted F1 Score**: **0.6245**

> **Integrity Statement & Dataset Provenance:**
> The current model is trained and benchmarked on a synthetic development dataset (`training_dataset.json`, 150 samples). Real-world generalization on diverse student populations and regional dialects remains unvalidated until operational data is collected under human ombudsperson supervision. High synthetic scores are NOT represented as production-ready accuracy.

---

## 4. Semantic Duplicate Detection & Privacy Preservation

- **Algorithm**: TF-IDF unigram vectorization with cosine similarity scoring.
- **Configurable Threshold**: `0.65` (scores ≥ 0.65 flagged as potential duplicates).
- **Multi-Tenant Boundary**: Strictly queries grievances belonging to the **same institution ID**.
- **Confidentiality Shielding**: Does NOT expose other students' names, roll numbers, full complaint text, or internal notes. Only non-sensitive reference number, match score, and truncated summary are returned.

---

## 5. Priority Triage & Safety Scoring

- **Deterministic Rule Engine**: Transparent keyword and phrase pattern matching.
- **Critical / Urgent Triggers**:
  - Ragging, sexual harassment, suicide/self-harm, physical violence, weapons.
  - Urgent deadlines: Exam clash tomorrow, scholarship cancellation deadline, hall ticket withheld.
- **Advisory Principle**: High priority suggestion is an operational triage aid, NEVER a determination of guilt or legal finding. Human officers retain sole authority to set final priority.

---

## 6. CLI Commands

### Generate Dataset
```powershell
python ai-service/data/dataset_builder.py
```

### Train Classifier Pipeline
```powershell
python ai-service/classifiers/train_classifier.py
```

### Run Model Evaluation
```powershell
python ai-service/evaluation/evaluate_classifier.py
```

### Run Automated Backend & AI Test Suite
```powershell
cd backend
..\venv\Scripts\pytest app/tests/test_ai.py -v
..\venv\Scripts\pytest app/tests/ -v
```
