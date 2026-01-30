# -*- coding: utf-8 -*-
"""
Módulo principal do detector de PII.

Hackathon Participa DF - Categoria Acesso à Informação
"""

from .patterns import PIIPatterns
from .exclusions import INSTITUTIONAL_NAMES, is_institutional_name
from .preprocessor import TextPreprocessor, normalize_text
from .detector import PIIDetector
from .utils import normalize_boolean
from .human_review import (
    HumanReviewAnalyzer,
    HumanReviewConfig,
    ReviewItem,
    ReviewPriority,
    ReviewReason,
    analyze_for_review,
    export_review_items,
)

__all__ = [
    'PIIDetector',
    'PIIPatterns',
    'INSTITUTIONAL_NAMES',
    'is_institutional_name',
    'TextPreprocessor',
    'normalize_text',
    # Revisão humana
    'HumanReviewAnalyzer',
    'HumanReviewConfig',
    'ReviewItem',
    'ReviewPriority',
    'ReviewReason',
    'analyze_for_review',
    'export_review_items',
]
