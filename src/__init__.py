# -*- coding: utf-8 -*-
"""
Módulo principal do detector de PII.

Hackathon Participa DF - Categoria Acesso à Informação
"""

from .patterns import PIIPatterns
from .exclusions import INSTITUTIONAL_NAMES, is_institutional_name
from .preprocessor import TextPreprocessor, normalize_text
from .detector import PIIDetector

__all__ = [
    'PIIDetector',
    'PIIPatterns',
    'INSTITUTIONAL_NAMES',
    'is_institutional_name',
    'TextPreprocessor',
    'normalize_text',
]
