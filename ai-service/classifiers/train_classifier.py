"""
EduResolve AI - Category Classifier Training Pipeline.
Trains a scikit-learn TF-IDF + LogisticRegression model on the labeled development dataset.
Produces serialized model artifacts and metadata.
"""
import os
import sys
import json
import joblib
from datetime import datetime, timezone
from typing import Dict, Any, Tuple

from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.metrics import classification_report, accuracy_score, f1_score

MODEL_VERSION = "EduResolve-TFIDF-LogReg-v1.0"
DATASET_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "training_dataset.json")
ARTIFACTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "artifacts")

LABEL_MAPPING = {
    "ACADEMIC": {"code": "ACADEMIC", "name": "Academics & Teaching"},
    "EXAM": {"code": "EXAM", "name": "Examinations & Results"},
    "FINANCE": {"code": "FINANCE", "name": "Fees & Finance"},
    "SCHOLARSHIP": {"code": "SCHOLARSHIP", "name": "Scholarships & Financial Aid"},
    "HOSTEL": {"code": "HOSTEL", "name": "Hostel & Accommodation"},
    "INFRA": {"code": "INFRA", "name": "Infrastructure & Facilities"},
    "ADMIN": {"code": "ADMIN", "name": "Administration & Records"},
    "CONDUCT": {"code": "CONDUCT", "name": "Student Conduct & Anti-Ragging"},
    "SUPPORT": {"code": "SUPPORT", "name": "Accessibility & Special Support"},
    "OTHER": {"code": "OTHER", "name": "Other Grievances"}
}

def clean_text(title: str, description: str) -> str:
    combined = f"{title.strip()} {description.strip()}".lower()
    return combined

def load_data(filepath: str) -> Tuple[list, list]:
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Dataset not found at {filepath}")
    with open(filepath, "r", encoding="utf-8") as f:
        items = json.load(f)
    
    texts = [clean_text(item["title"], item["description"]) for item in items]
    labels = [item["category"] for item in items]
    return texts, labels

def train_and_save_pipeline(output_dir: str = ARTIFACTS_DIR) -> Dict[str, Any]:
    print("=" * 65)
    print("EduResolve AI - Grievance Category Classifier Training")
    print("=" * 65)

    texts, labels = load_data(DATASET_PATH)
    print(f"Loaded {len(texts)} samples across {len(set(labels))} classes from {DATASET_PATH}")

    # Stratified split with fixed seed for strict reproducibility without leakage
    X_train, X_test, y_train, y_test = train_test_split(
        texts, labels, test_size=0.25, random_state=42, stratify=labels
    )
    print(f"Training split: {len(X_train)} samples | Evaluation split: {len(X_test)} samples")

    pipeline = Pipeline([
        ("tfidf", TfidfVectorizer(
            ngram_range=(1, 2),
            max_features=3000,
            sublinear_tf=True,
            stop_words="english",
            min_df=1
        )),
        ("clf", LogisticRegression(
            C=2.5,
            max_iter=1000,
            random_state=42,
            class_weight="balanced"
        ))
    ])

    print("Fitting TF-IDF Vectorizer and Logistic Regression classifier...")
    pipeline.fit(X_train, y_train)

    # Evaluate on held-out test split
    y_pred = pipeline.predict(X_test)
    test_acc = accuracy_score(y_test, y_pred)
    test_f1_macro = f1_score(y_test, y_pred, average="macro")
    test_f1_weighted = f1_score(y_test, y_pred, average="weighted")

    print(f"\n[+] Model Evaluation on Held-Out Split:")
    print(f"    - Accuracy:        {test_acc:.4f} ({test_acc * 100:.2f}%)")
    print(f"    - Macro F1:        {test_f1_macro:.4f}")
    print(f"    - Weighted F1:     {test_f1_weighted:.4f}")

    # Detailed classification report
    report_dict = classification_report(y_test, y_pred, output_dict=True, zero_division=0)
    print("\n" + classification_report(y_test, y_pred, zero_division=0))

    # Save artifact
    os.makedirs(output_dir, exist_ok=True)
    model_filename = "category_classifier.joblib"
    model_path = os.path.join(output_dir, model_filename)
    joblib.dump(pipeline, model_path)
    print(f"[+] Serialized model artifact saved to: {model_path}")

    # Save metadata
    metadata = {
        "model_type": "TF-IDF + LogisticRegression (scikit-learn Pipeline)",
        "model_version": MODEL_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "random_state": 42,
        "classes": sorted(list(set(labels))),
        "label_mapping": LABEL_MAPPING,
        "evaluation_summary": {
            "dataset_provenance": "Curated developmental dataset (150 balanced academic grievance samples)",
            "validation_method": "Stratified 75/25 train/test split without leakage",
            "eval_samples_count": len(X_test),
            "test_accuracy": round(test_acc, 4),
            "test_macro_f1": round(test_f1_macro, 4),
            "test_weighted_f1": round(test_f1_weighted, 4),
            "per_class_metrics": {
                cls: {
                    "precision": round(metrics.get("precision", 0), 3),
                    "recall": round(metrics.get("recall", 0), 3),
                    "f1_score": round(metrics.get("f1-score", 0), 3),
                    "support": metrics.get("support", 0)
                }
                for cls, metrics in report_dict.items() if cls not in ["accuracy", "macro avg", "weighted avg"]
            }
        },
        "known_limitations": "Model trained on synthetic development data covering higher education scenarios. Accuracy on out-of-distribution real-world regional dialects requires continuous human intake verification."
    }

    metadata_path = os.path.join(output_dir, "model_metadata.json")
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
    print(f"[+] Model metadata and evaluation audit saved to: {metadata_path}")

    # Also mirror artifact to backend service model directory for seamless packaging
    backend_model_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "backend", "app", "services", "models")
    os.makedirs(backend_model_dir, exist_ok=True)
    joblib.dump(pipeline, os.path.join(backend_model_dir, model_filename))
    with open(os.path.join(backend_model_dir, "model_metadata.json"), "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
    print(f"[+] Model artifact mirrored to backend at: {backend_model_dir}")

    return metadata

if __name__ == "__main__":
    train_and_save_pipeline()
