"""
EduResolve AI - ML Evaluation Metrics Utility.
Provides reproducible computation of classification performance, per-class metrics,
and formatted confusion matrices.
"""
from typing import Dict, Any, List
import numpy as np
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    classification_report,
    confusion_matrix
)

def compute_classification_metrics(
    y_true: List[str],
    y_pred: List[str],
    classes: List[str]
) -> Dict[str, Any]:
    """
    Computes standard evaluation metrics for multi-class classification.
    """
    acc = accuracy_score(y_true, y_pred)
    macro_prec = precision_score(y_true, y_pred, average="macro", zero_division=0)
    macro_rec = recall_score(y_true, y_pred, average="macro", zero_division=0)
    macro_f1 = f1_score(y_true, y_pred, average="macro", zero_division=0)
    weighted_f1 = f1_score(y_true, y_pred, average="weighted", zero_division=0)

    report = classification_report(
        y_true, y_pred, labels=classes, output_dict=True, zero_division=0
    )

    cm = confusion_matrix(y_true, y_pred, labels=classes)

    class_distribution = {}
    for label in y_true:
        class_distribution[label] = class_distribution.get(label, 0) + 1

    per_category = {}
    for cls in classes:
        if cls in report:
            per_category[cls] = {
                "precision": round(report[cls]["precision"], 3),
                "recall": round(report[cls]["recall"], 3),
                "f1_score": round(report[cls]["f1-score"], 3),
                "support": report[cls]["support"]
            }

    return {
        "num_eval_examples": len(y_true),
        "class_distribution": class_distribution,
        "accuracy": round(float(acc), 4),
        "macro_precision": round(float(macro_prec), 4),
        "macro_recall": round(float(macro_rec), 4),
        "macro_f1": round(float(macro_f1), 4),
        "weighted_f1": round(float(weighted_f1), 4),
        "per_category": per_category,
        "confusion_matrix": {
            "labels": classes,
            "matrix": cm.tolist()
        }
    }

def format_confusion_matrix_ascii(cm: List[List[int]], labels: List[str]) -> str:
    """Format confusion matrix as clean ASCII table."""
    header = "True \\ Pred | " + " | ".join(f"{l[:6]:>6}" for l in labels)
    sep = "-" * len(header)
    lines = [header, sep]
    for i, row in enumerate(cm):
        row_str = f"{labels[i][:11]:<11} | " + " | ".join(f"{val:>6}" for val in row)
        lines.append(row_str)
    return "\n".join(lines)
