# -*- coding: utf-8 -*-
"""
Testes unitários para o script de avaliação (scripts/evaluate.py).

Testa cálculo de métricas e normalização de booleanos.
"""

import pytest
import pandas as pd

# Adicionar scripts ao path
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.evaluate import calculate_metrics, normalize_boolean


class TestNormalizeBoolean:
    """Testes de normalização de booleanos."""

    def test_true_values(self):
        """Deve reconhecer valores verdadeiros."""
        df = pd.DataFrame({'col': ['true', 'True', 'TRUE', '1', 'sim', 'yes', 'verdadeiro']})
        result = normalize_boolean(df, 'col')
        assert result.all()

    def test_false_values(self):
        """Deve reconhecer valores falsos."""
        df = pd.DataFrame({'col': ['false', 'False', '0', 'nao', 'no', 'falso']})
        result = normalize_boolean(df, 'col')
        assert not result.any()

    def test_boolean_native(self):
        """Deve normalizar booleanos nativos."""
        df = pd.DataFrame({'col': [True, False, True]})
        result = normalize_boolean(df, 'col')
        assert result[0] is True or result[0] == True
        assert result[1] is False or result[1] == False

    def test_numeric(self):
        """Deve normalizar valores numéricos."""
        df = pd.DataFrame({'col': [1, 0, 1]})
        result = normalize_boolean(df, 'col')
        assert result[0] == True
        assert result[1] == False


class TestCalculateMetrics:
    """Testes de cálculo de métricas."""

    def test_perfeito(self):
        """Classificação perfeita."""
        y_true = pd.Series([True, True, False, False])
        y_pred = pd.Series([True, True, False, False])
        m = calculate_metrics(y_true, y_pred)

        assert m['tp'] == 2
        assert m['tn'] == 2
        assert m['fp'] == 0
        assert m['fn'] == 0
        assert m['accuracy'] == 1.0
        assert m['precision'] == 1.0
        assert m['recall'] == 1.0
        assert m['f1'] == 1.0

    def test_com_erros(self):
        """Classificação com erros."""
        y_true = pd.Series([True, True, False, False])
        y_pred = pd.Series([True, False, True, False])
        m = calculate_metrics(y_true, y_pred)

        assert m['tp'] == 1
        assert m['tn'] == 1
        assert m['fp'] == 1
        assert m['fn'] == 1
        assert m['accuracy'] == 0.5

    def test_todos_positivos(self):
        """Quando tudo é predito como positivo."""
        y_true = pd.Series([True, False, False])
        y_pred = pd.Series([True, True, True])
        m = calculate_metrics(y_true, y_pred)

        assert m['tp'] == 1
        assert m['fp'] == 2
        assert m['fn'] == 0
        assert m['recall'] == 1.0

    def test_vazio(self):
        """Lista vazia deve retornar zeros."""
        y_true = pd.Series([], dtype=bool)
        y_pred = pd.Series([], dtype=bool)
        m = calculate_metrics(y_true, y_pred)

        assert m['total'] == 0
        assert m['accuracy'] == 0

    def test_sem_positivos_verdadeiros(self):
        """Nenhum positivo verdadeiro — recall não deve dividir por zero."""
        y_true = pd.Series([False, False, False])
        y_pred = pd.Series([True, False, False])
        m = calculate_metrics(y_true, y_pred)

        assert m['recall'] == 0
        assert m['fn'] == 0
