"""
EduResolve AI - Reproducible Category Classifier Evaluation Script.
Loads the trained pipeline artifact and benchmarks its performance on an evaluation dataset.
Outputs detailed metrics, class distributions, per-category F1 scores, and confusion matrix.
"""
import os
import sys
import json
import joblib
from datetime import datetime, timezone
from sklearn.model_selection import train_test_split

# Add parent directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from evaluation.evaluation_metrics import compute_classification_metrics, format_confusion_matrix_ascii
from classifiers.train_classifier import clean_text, load_data, DATASET_PATH, ARTIFACTS_DIR

MODEL_PATH = os.path.join(ARTIFACTS_DIR, "category_classifier.joblib")

def run_evaluation(model_path: str = MODEL_PATH, dataset_path: str = DATASET_PATH):
    print("=" * 70)
    print("EduResolve AI - Category Classifier Evaluation & Benchmarking")
    print("=" * 70)

    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model artifact not found at {model_path}. Run train_classifier.py first.")

    pipeline = joblib.load(model_path)
    print(f"Loaded model artifact: {model_path}")

    texts, labels = load_data(dataset_path)
    classes = sorted(list(set(labels)))

    # Use the same stratified split random seed (42) to isolate the held-out evaluation test split
    _, X_eval, _, y_eval = train_test_split(
        texts, labels, test_size=0.25, random_state=42, stratify=labels
    )

    print(f"Evaluation set size: {len(X_eval)} examples across {len(classes)} classes")
    y_pred = pipeline.predict(X_eval)

    metrics = compute_classification_metrics(y_eval, y_pred, classes)

    print("\n--- Summary Performance Metrics ---")
    print(f"Evaluation Examples:    {metrics['num_eval_examples']}")
    print(f"Accuracy:               {metrics['accuracy']:.4f} ({metrics['accuracy'] * 100:.2f}%)")
    print(f"Macro Precision:        {metrics['macro_precision']:.4f}")
    print(f"Macro Recall:           {metrics['macro_recall']:.4f}")
    print(f"Macro F1 Score:         {metrics['macro_f1']:.4f}")
    print(f"Weighted F1 Score:      {metrics['weighted_f1']:.4f}")

    print("\n--- Per-Category Performance ---")
    print(f"{'Category':<15} | {'Precision':<10} | {'Recall':<10} | {'F1-Score':<10} | {'Support':<8}")
    print("-" * 65)
    for cat, p_metrics in sorted(metrics["per_category"].items()):
        print(f"{cat:<15} | {p_metrics['precision']:<10.3f} | {p_metrics['recall']:<10.3f} | {p_metrics['f1_score']:<10.3f} | {p_metrics['support']:<8}")

    print("\n--- Confusion Matrix ---")
    cm_ascii = format_confusion_matrix_ascii(metrics["confusion_matrix"]["matrix"], classes)
    print(cm_ascii)

    # Save detailed evaluation artifact
    eval_report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "model_path": model_path,
        "dataset_provenance": "150-sample curated developmental benchmark dataset",
        "dataset_limitations": (
            "This evaluation is performed on a synthetic developmental dataset. "
            "Real-world generalization on arbitrary regional student grievances remains unvalidated "
            "until operational historical datasets are collected with human ombudsperson reviews."
        ),
        "metrics": metrics
    }

    report_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "evaluation_results.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(eval_report, f, indent=2)
    print(f"\n[+] Saved evaluation metrics to: {report_path}")

    # Generate Markdown summary report
    md_content = f"""# EduResolve AI — Classifier Evaluation Report
**Evaluation Date**: {eval_report['timestamp']}  
**Evaluator Engine**: Scikit-learn Pipeline (TF-IDF + Balanced Logistic Regression)  
**Dataset Provenance**: {eval_report['dataset_provenance']}  

---

## 1. Executive Summary

| Metric | Score |
| :--- | :--- |
| **Evaluation Examples** | {metrics['num_eval_examples']} |
| **Overall Accuracy** | {metrics['accuracy'] * 100:.2f}% |
| **Macro Precision** | {metrics['macro_precision']:.4f} |
| **Macro Recall** | {metrics['macro_recall']:.4f} |
| **Macro F1 Score** | {metrics['macro_f1']:.4f} |
| **Weighted F1 Score** | {metrics['weighted_f1']:.4f} |

---

## 2. Per-Category Breakdown

| Category | Precision | Recall | F1-Score | Evaluation Support |
| :--- | :--- | :--- | :--- | :--- |
"""
    for cat, p_metrics in sorted(metrics["per_category"].items()):
        md_content += f"| `{cat}` | {p_metrics['precision']:.3f} | {p_metrics['recall']:.3f} | {p_metrics['f1_score']:.3f} | {p_metrics['support']} |\n"

    md_content += f"""
---

## 3. Confusion Matrix

```text
{cm_ascii}
```

---

## 4. Known Limitations & Integrity Statement
- **Developmental Baseline**: {eval_report['dataset_limitations']}
- **Human-in-the-Loop Mandate**: The model is an **advisory triage tool**. All recommendations require human officer review and can be edited prior to final determination.
"""
    md_report_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "evaluation_report.md")
    with open(md_report_path, "w", encoding="utf-8") as f:
        f.write(md_content)
    print(f"[+] Generated markdown report at: {md_report_path}")

    return metrics

if __name__ == "__main__":
    run_evaluation()
