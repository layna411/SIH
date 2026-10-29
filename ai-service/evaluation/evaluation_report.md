# EduResolve AI — Classifier Evaluation Report
**Evaluation Date**: 2026-10-28T05:21:42.772426+00:00  
**Evaluator Engine**: Scikit-learn Pipeline (TF-IDF + Balanced Logistic Regression)  
**Dataset Provenance**: 150-sample curated developmental benchmark dataset  

---

## 1. Executive Summary

| Metric | Score |
| :--- | :--- |
| **Evaluation Examples** | 38 |
| **Overall Accuracy** | 63.16% |
| **Macro Precision** | 0.6983 |
| **Macro Recall** | 0.6417 |
| **Macro F1 Score** | 0.6299 |
| **Weighted F1 Score** | 0.6245 |

---

## 2. Per-Category Breakdown

| Category | Precision | Recall | F1-Score | Evaluation Support |
| :--- | :--- | :--- | :--- | :--- |
| `ACADEMIC` | 1.000 | 0.500 | 0.667 | 4.0 |
| `ADMIN` | 0.500 | 1.000 | 0.667 | 3.0 |
| `CONDUCT` | 0.400 | 0.500 | 0.444 | 4.0 |
| `EXAM` | 0.500 | 0.750 | 0.600 | 4.0 |
| `FINANCE` | 0.667 | 1.000 | 0.800 | 4.0 |
| `HOSTEL` | 0.667 | 0.500 | 0.571 | 4.0 |
| `INFRA` | 1.000 | 0.500 | 0.667 | 4.0 |
| `OTHER` | 0.500 | 0.250 | 0.333 | 4.0 |
| `SCHOLARSHIP` | 1.000 | 0.667 | 0.800 | 3.0 |
| `SUPPORT` | 0.750 | 0.750 | 0.750 | 4.0 |

---

## 3. Confusion Matrix

```text
True \ Pred | ACADEM |  ADMIN | CONDUC |   EXAM | FINANC | HOSTEL |  INFRA |  OTHER | SCHOLA | SUPPOR
-----------------------------------------------------------------------------------------------------
ACADEMIC    |      2 |      1 |      0 |      1 |      0 |      0 |      0 |      0 |      0 |      0
ADMIN       |      0 |      3 |      0 |      0 |      0 |      0 |      0 |      0 |      0 |      0
CONDUCT     |      0 |      1 |      2 |      1 |      0 |      0 |      0 |      0 |      0 |      0
EXAM        |      0 |      1 |      0 |      3 |      0 |      0 |      0 |      0 |      0 |      0
FINANCE     |      0 |      0 |      0 |      0 |      4 |      0 |      0 |      0 |      0 |      0
HOSTEL      |      0 |      0 |      1 |      0 |      1 |      2 |      0 |      0 |      0 |      0
INFRA       |      0 |      0 |      0 |      0 |      0 |      1 |      2 |      1 |      0 |      0
OTHER       |      0 |      0 |      1 |      1 |      0 |      0 |      0 |      1 |      0 |      1
SCHOLARSHIP |      0 |      0 |      0 |      0 |      1 |      0 |      0 |      0 |      2 |      0
SUPPORT     |      0 |      0 |      1 |      0 |      0 |      0 |      0 |      0 |      0 |      3
```

---

## 4. Known Limitations & Integrity Statement
- **Developmental Baseline**: This evaluation is performed on a synthetic developmental dataset. Real-world generalization on arbitrary regional student grievances remains unvalidated until operational historical datasets are collected with human ombudsperson reviews.
- **Human-in-the-Loop Mandate**: The model is an **advisory triage tool**. All recommendations require human officer review and can be edited prior to final determination.
