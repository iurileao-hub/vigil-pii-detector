# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **Python ML hackathon project** for the "1º Hackathon em Controle Social: Desafio Participa DF" (Category: Acesso à Informação). The goal is to build a PII detector that identifies personal data in Brazilian Portuguese information access requests that were incorrectly marked as public.

**PII Types to Detect:** CPF, RG, Email, Phone, Full Names

**Strategic Priority:** Minimize false negatives (recall-first). The tiebreaker criteria favor fewer FN over fewer FP.

## Build and Run Commands

```bash
# Environment setup
python -m venv venv
source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
python -m spacy download pt_core_news_lg

# Main execution
python main.py --input data/pedidos.csv --output data/resultado.csv

# Evaluation (with ground truth)
python scripts/evaluate.py --predictions resultado.csv --ground-truth gabarito.csv

# Run tests
python -m pytest tests/

# Generate synthetic test data
python scripts/generate_synthetic.py
```

## Architecture

The detector uses a **layered hybrid approach**:

```
Text Input
    ↓
├─ Layer 1: Strong Rules (regex + validators)
│   └─ CPF (with check digit validation), Email, Phone, RG patterns
│   └─ High confidence → immediate positive classification
│
├─ Layer 2: Weak Rules (contextual signals)
│   └─ First-person markers ("meu nome", "meu CPF")
│   └─ Contact keywords ("endereço", "CEP", "e-mail")
│
├─ Layer 3: ML Model (TF-IDF + Logistic Regression/SVM)
│   └─ Word + character n-grams
│   └─ Class weighting to reduce FN
│
├─ Layer 4: Fusion & Calibration
│   └─ Combine rule-based + ML scores
│   └─ Threshold tuned for minimal FN
│
└─ Output: {contem_pii, tipos_detectados, confianca}
```

**Anti-False-Positive Filters:**
- Exclude process number patterns (SEI, NUP, protocol numbers)
- Word boundary checking to avoid "rg" matching "órgão"
- Context requirements for ambiguous patterns

## Key Implementation Files

```
src/
├── config.py        # Configuration and thresholds
├── ingest.py        # CSV/XLSX loading and validation
├── preprocess.py    # Text normalization (preserve digits/separators)
├── rules.py         # Regex patterns + validators (strong/weak rules)
├── features.py      # TF-IDF and feature extraction
├── model.py         # ML model wrapper
├── train.py         # Training pipeline
├── predict.py       # Inference and batch prediction
├── tune.py          # Threshold optimization (FN-first)
├── evaluate.py      # Metrics calculation (F1, Precision, Recall)
└── audit.py         # FN/FP analysis and reporting
```

## Scoring Criteria

**P1 (Technical):** F1-Score = 2 × (Precision × Recall) / (Precision + Recall)

**P2 (Documentation - 10 points, indivisible):**
- Python version + prerequisites listed
- Functional requirements.txt
- Sequential installation commands
- Execution commands with examples
- Input/output format documented
- README with objective + file descriptions
- Comments in complex code sections
- Logical file structure

**Final Score = P1 + P2** (max P2 = 10 points)

## Sample Data

`AMOSTRA_e-SIC.xlsx` contains 99 sample records:
- Columns: `ID`, `Texto Mascarado`
- Text length: min ~10, median ~319, max ~3229 characters
- Contains process numbers (SEI, NUP) that can trigger false positives

## Language and Documentation

- All code comments and documentation must be in **Brazilian Portuguese**
- AI usage must be documented in README.md (per edital item 13.9)
- No real personal data in the repository (all PII is synthetic)

## Regex Patterns Reference

```python
# CPF (with/without punctuation)
r'\d{3}\.?\d{3}\.?\d{3}-?\d{2}'

# Email
r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'

# Brazilian phone
r'(?:\+55\s?)?(?:\(?\d{2}\)?[\s.-]?)?\d{4,5}[\s.-]?\d{4}'

# RG (common patterns)
r'\d{1,2}\.?\d{3}\.?\d{3}-?[0-9Xx]'
```

Use `validate-docbr` library for CPF check digit validation.

## Submission Requirements

- Public GitHub/GitLab repository
- Executable after fresh clone (`git clone` → `pip install` → `python main.py`)
- No modifications allowed after submission deadline (January 30, 2026)
- Tag release as `submission_v1` before submitting
