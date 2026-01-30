# -*- coding: utf-8 -*-
"""
Testes unitários para o módulo de pré-processamento (src/preprocessor.py).

Testa normalização Unicode, tratamento de None/NaN, remoção de caracteres
de controle e normalização de espaços.
"""

import math
import pytest
from src.preprocessor import TextPreprocessor, normalize_text


@pytest.fixture
def preprocessor():
    """Fixture que retorna uma instância de TextPreprocessor."""
    return TextPreprocessor()


class TestPreprocessorBasico:
    """Testes básicos do pré-processador."""

    def test_texto_simples(self, preprocessor):
        """Texto simples deve ser retornado sem alteração."""
        assert preprocessor.preprocess('Olá mundo') == 'Olá mundo'

    def test_none_retorna_vazio(self, preprocessor):
        """None deve retornar string vazia."""
        assert preprocessor.preprocess(None) == ''

    def test_float_nan_retorna_vazio(self, preprocessor):
        """Float NaN deve retornar string vazia."""
        assert preprocessor.preprocess(float('nan')) == ''

    def test_math_nan_retorna_vazio(self, preprocessor):
        """math.nan deve retornar string vazia."""
        assert preprocessor.preprocess(math.nan) == ''

    def test_numero_convertido_para_string(self, preprocessor):
        """Números devem ser convertidos para string."""
        assert preprocessor.preprocess(12345) == '12345'

    def test_booleano_convertido(self, preprocessor):
        """Booleanos devem ser convertidos para string."""
        assert preprocessor.preprocess(True) == 'True'

    def test_texto_vazio(self, preprocessor):
        """String vazia deve retornar string vazia."""
        assert preprocessor.preprocess('') == ''


class TestNormalizacaoUnicode:
    """Testes de normalização Unicode NFKC."""

    def test_nfkc_circled_numbers(self, preprocessor):
        """Números circulados devem ser normalizados (① → 1)."""
        assert '1' in preprocessor.preprocess('①')

    def test_nfkc_ligatures(self, preprocessor):
        """Ligaduras devem ser normalizadas (ﬁ → fi)."""
        result = preprocessor.preprocess('ﬁnal')
        assert 'fi' in result

    def test_preserva_acentos(self, preprocessor):
        """Acentuação brasileira deve ser preservada."""
        texto = 'João José Conceição Fátima'
        assert preprocessor.preprocess(texto) == texto


class TestCaracteresControle:
    """Testes de remoção de caracteres de controle."""

    def test_remove_null_byte(self, preprocessor):
        """Deve remover byte nulo \\x00 (sem deixar espaço)."""
        assert preprocessor.preprocess('texto\x00limpo') == 'textolimpo'

    def test_preserva_newline_e_tab(self, preprocessor):
        """Deve normalizar newline e tab para espaço (via multi_space)."""
        result = preprocessor.preprocess('linha1\nlinha2\ttab')
        assert 'linha1' in result
        assert 'linha2' in result

    def test_remove_controle_obscuro(self, preprocessor):
        """Deve remover caracteres de controle obscuros."""
        assert preprocessor.preprocess('a\x0fb') == 'ab'


class TestNormalizacaoEspacos:
    """Testes de normalização de espaços."""

    def test_multiplos_espacos(self, preprocessor):
        """Múltiplos espaços devem virar um só."""
        assert preprocessor.preprocess('a   b    c') == 'a b c'

    def test_espacos_inicio_fim(self, preprocessor):
        """Espaços no início e fim devem ser removidos."""
        assert preprocessor.preprocess('  texto  ') == 'texto'

    def test_tabs_e_newlines(self, preprocessor):
        """Tabs e newlines devem ser normalizados para espaço."""
        assert preprocessor.preprocess('a\t\nb') == 'a b'


class TestPreprocessBatch:
    """Testes de processamento em batch."""

    def test_batch_lista_simples(self, preprocessor):
        """Deve processar lista de textos."""
        result = preprocessor.preprocess_batch(['a', 'b', 'c'])
        assert result == ['a', 'b', 'c']

    def test_batch_com_none(self, preprocessor):
        """Deve tratar None no batch."""
        result = preprocessor.preprocess_batch([None, 'texto', None])
        assert result == ['', 'texto', '']

    def test_batch_vazio(self, preprocessor):
        """Lista vazia deve retornar lista vazia."""
        assert preprocessor.preprocess_batch([]) == []


class TestNormalizeTextConveniencia:
    """Testes da função de conveniência normalize_text."""

    def test_funciona(self):
        """Deve normalizar texto corretamente."""
        assert normalize_text('  hello  ') == 'hello'

    def test_none(self):
        """Deve tratar None."""
        assert normalize_text(None) == ''
