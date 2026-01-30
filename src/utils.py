# -*- coding: utf-8 -*-
"""
Utilidades compartilhadas entre módulos do VIGIL.

Funções de uso comum extraídas para evitar duplicação de código
entre scripts de avaliação e análise de erros.
"""

import pandas as pd


# Valores reconhecidos como booleano verdadeiro
TRUE_VALUES = frozenset(['true', '1', '1.0', 'sim', 'yes', 's', 'y', 'verdadeiro'])


def normalize_boolean(series: pd.Series) -> pd.Series:
    """
    Normaliza uma Series pandas para valores booleanos.

    Aceita: True/False, 1/0, 'true'/'false', 'sim'/'não', etc.

    Args:
        series: Series com valores a normalizar

    Returns:
        Series com valores booleanos
    """
    values = series.astype(str).str.lower().str.strip()
    return values.isin(TRUE_VALUES)
