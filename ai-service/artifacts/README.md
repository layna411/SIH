# EduResolve AI — Model Artifacts Registry

This directory contains the serialized machine learning model artifacts, label mappings, and training metadata.

## Artifact Manifest

| Artifact File | Model Type | Parameters / Architecture | Model Version | Date Trained |
| :--- | :--- | :--- | :--- | :--- |
| `category_classifier.joblib` | Scikit-learn Pipeline | `TfidfVectorizer(max_features=2500, ngram_range=(1,2))` + `LogisticRegression(C=1.0, class_weight='balanced')` | `v1.0.0-dev` | 2026-10-28 |
| `model_metadata.json` | JSON Metadata | Class mapping (10 categories), training metrics, evaluation split metrics, and provenance | `v1.0.0-dev` | 2026-10-28 |

## Model Reproducibility

To retrain the category classifier:
```bash
# In SIH/ai-service directory:
python classifiers/train_classifier.py
```

To evaluate the category classifier against the held-out split:
```bash
# In SIH/ai-service directory:
python evaluation/evaluate_classifier.py
```

## Production & Deployment Considerations
- Artifact is loaded as a singleton in `backend/app/services/ai_service.py` to prevent redundant disk I/O on every request.
- If the artifact is missing or corrupted, the service automatically falls back to domain-rule pattern matching without interrupting grievance submission or the API.
- Local inference is performed entirely on CPU with latency under 15ms per request. No GPU is required.
