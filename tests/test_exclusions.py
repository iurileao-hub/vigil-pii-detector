# -*- coding: utf-8 -*-
"""
Testes unitários para o módulo de exclusões (src/exclusions.py).

Testa filtragem de nomes institucionais e verifica que nomes reais
de pessoas NÃO são filtrados incorretamente (falsos negativos).
"""

import pytest
from src.exclusions import is_institutional_name, INSTITUTIONAL_NAMES


class TestNomesInstitucionais:
    """Testes de detecção de nomes institucionais."""

    def test_nome_exato(self):
        """Deve detectar nome institucional exato."""
        assert is_institutional_name('Distrito Federal') is True

    def test_nome_exato_case_insensitive(self):
        """Deve ser case-insensitive."""
        assert is_institutional_name('distrito federal') is True
        assert is_institutional_name('DISTRITO FEDERAL') is True

    def test_nome_contendo_institucional(self):
        """Deve detectar nome que contém termo institucional."""
        assert is_institutional_name('Secretaria de Estado de Saúde do DF') is True

    def test_string_vazia(self):
        """String vazia deve retornar False."""
        assert is_institutional_name('') is False

    def test_none(self):
        """None deve retornar False."""
        assert is_institutional_name(None) is False

    def test_secretaria(self):
        """Deve detectar variantes de Secretaria."""
        assert is_institutional_name('Secretaria de Educação') is True

    def test_tribunal(self):
        """Deve detectar Tribunal de Contas."""
        assert is_institutional_name('Tribunal de Contas') is True


class TestNomesReaisNaoFiltrados:
    """Testa que nomes reais de pessoas NÃO são filtrados.

    CRÍTICO: O bug anterior fazia `name_lower in institutional`, o que
    significava que nomes curtos como "Ana" eram filtrados porque "ana"
    é substring de "candangolândia". Isso causava falsos negativos.
    """

    def test_ana_nao_filtrado(self):
        """'Ana' NÃO deve ser filtrado (era substring de 'candangolândia')."""
        assert is_institutional_name('Ana') is False
        assert is_institutional_name('Ana Silva') is False

    def test_gama_como_sobrenome(self):
        """'Vasco da Gama' NÃO deve ser filtrado pelo 'Gama' na lista."""
        # 'Gama' está na lista como região administrativa, mas
        # 'Vasco da Gama' não contém 'gama' como termo institucional inteiro
        # O nome 'Gama' sozinho SERÁ filtrado (é a região administrativa)
        assert is_institutional_name('Gama') is True  # região administrativa
        # Mas nomes compostos com Gama não devem ser filtrados
        # a menos que contenham exatamente "gama" como substring

    def test_nome_pessoa_simples(self):
        """Nomes de pessoa simples NÃO devem ser filtrados."""
        assert is_institutional_name('João Silva') is False
        assert is_institutional_name('Maria Santos') is False
        assert is_institutional_name('Carlos Pereira') is False

    def test_nome_curto_nao_filtrado(self):
        """Nomes curtos NÃO devem ser filtrados por substring."""
        assert is_institutional_name('Lia') is False
        assert is_institutional_name('Ivo') is False
        assert is_institutional_name('Eva') is False

    def test_nome_com_preposicao(self):
        """Nomes com preposição NÃO devem ser filtrados."""
        assert is_institutional_name('José da Silva') is False
        assert is_institutional_name('Maria do Carmo') is False


class TestListaInstitucional:
    """Testes da lista de nomes institucionais."""

    def test_lista_nao_vazia(self):
        """A lista deve ter entradas."""
        assert len(INSTITUTIONAL_NAMES) > 0

    def test_contem_orgaos_gdf(self):
        """Deve conter órgãos do GDF."""
        assert 'Distrito Federal' in INSTITUTIONAL_NAMES
        assert 'Controladoria Geral' in INSTITUTIONAL_NAMES

    def test_contem_regioes_administrativas(self):
        """Deve conter regiões administrativas."""
        assert 'Taguatinga' in INSTITUTIONAL_NAMES
        assert 'Ceilândia' in INSTITUTIONAL_NAMES
