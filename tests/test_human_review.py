# -*- coding: utf-8 -*-
"""
Testes para o módulo de revisão humana.

Verifica:
1. Detecção correta de contextos suspeitos (artístico, acadêmico)
2. Classificação de prioridade baseada em score
3. Funcionamento dos thresholds configuráveis
4. Exportação de arquivos de revisão
"""

import pytest
import tempfile
import csv
import json
from pathlib import Path

from src.human_review import (
    HumanReviewAnalyzer,
    HumanReviewConfig,
    ReviewItem,
    ReviewPriority,
    ReviewReason,
    analyze_for_review,
    export_review_items,
)


class TestHumanReviewConfig:
    """Testes para configuração de thresholds."""

    def test_config_default_values(self):
        """Configuração padrão deve ter valores sensatos."""
        config = HumanReviewConfig()

        assert config.high_confidence_threshold == 0.95
        assert config.medium_confidence_threshold == 0.80
        assert config.low_confidence_threshold == 0.80
        assert config.context_window == 100

    def test_config_custom_values(self):
        """Deve aceitar valores customizados."""
        config = HumanReviewConfig(
            high_confidence_threshold=0.90,
            medium_confidence_threshold=0.70,
            low_confidence_threshold=0.70,
            context_window=50,
        )

        assert config.high_confidence_threshold == 0.90
        assert config.context_window == 50


class TestContextoArtistico:
    """Testes para detecção de contexto artístico."""

    def test_detecta_vitrais(self):
        """Deve detectar contexto com vitrais."""
        analyzer = HumanReviewAnalyzer()
        text = "No referido imóvel há inúmeros vitrais e painéis Athos Bulcão."
        result = {
            'contem_pii': True,
            'detalhes': [('nome', 'Athos Bulcão', 1.0)]
        }

        items = analyzer.analyze("1", text, result)

        assert len(items) > 0
        assert any(item.motivo == ReviewReason.ARTISTIC_CONTEXT for item in items)

    def test_detecta_mosaicos(self):
        """Deve detectar contexto com mosaicos."""
        analyzer = HumanReviewAnalyzer()
        text = "A obra inclui mosaicos de artistas renomados como Roberto Burle Marx."
        result = {
            'contem_pii': True,
            'detalhes': [('nome', 'Roberto Burle Marx', 1.0)]
        }

        items = analyzer.analyze("1", text, result)

        assert any(item.motivo == ReviewReason.ARTISTIC_CONTEXT for item in items)

    def test_nao_detecta_painel_dashboard(self):
        """Não deve detectar 'painel de controle' como contexto artístico."""
        analyzer = HumanReviewAnalyzer()
        text = "Acesse o painel de controle para ver os dados de João Silva."
        result = {
            'contem_pii': True,
            'detalhes': [('nome', 'João Silva', 1.0)]
        }

        items = analyzer.analyze("1", text, result)

        # Não deve ter itens de contexto artístico
        assert not any(item.motivo == ReviewReason.ARTISTIC_CONTEXT for item in items)

    def test_nao_detecta_historico_consumo(self):
        """Não deve detectar 'histórico de consumo' como contexto artístico."""
        analyzer = HumanReviewAnalyzer()
        text = "Solicito histórico de consumo de Maria Santos."
        result = {
            'contem_pii': True,
            'detalhes': [('nome', 'Maria Santos', 1.0)]
        }

        items = analyzer.analyze("1", text, result)

        assert not any(item.motivo == ReviewReason.ARTISTIC_CONTEXT for item in items)

    def test_detecta_artista_conhecido(self):
        """Deve detectar nomes de artistas conhecidos."""
        analyzer = HumanReviewAnalyzer()
        text = "Os painéis foram feitos por Athos Bulcão."
        result = {
            'contem_pii': True,
            'detalhes': [('nome', 'Athos Bulcão', 1.0)]
        }

        items = analyzer.analyze("1", text, result)

        assert any(item.motivo == ReviewReason.ARTISTIC_CONTEXT for item in items)


class TestContextoAcademico:
    """Testes para detecção de contexto acadêmico."""

    def test_detecta_pesquisador(self):
        """Deve detectar contexto com pesquisador."""
        analyzer = HumanReviewAnalyzer()
        text = "Pesquisadora do Instituto: Carolina Guimarães Neves."
        result = {
            'contem_pii': True,
            'detalhes': [('nome', 'Carolina Guimarães Neves', 1.0)]
        }

        items = analyzer.analyze("1", text, result)

        assert any(item.motivo == ReviewReason.ACADEMIC_CONTEXT for item in items)

    def test_detecta_mestrado(self):
        """Deve detectar contexto de mestrado."""
        analyzer = HumanReviewAnalyzer()
        text = "Estou fazendo uma pesquisa de mestrado. Grata, Conceição Sampaio."
        result = {
            'contem_pii': True,
            'detalhes': [('nome', 'Conceição Sampaio', 0.98)]
        }

        items = analyzer.analyze("1", text, result)

        assert any(item.motivo == ReviewReason.ACADEMIC_CONTEXT for item in items)

    def test_detecta_professor(self):
        """Deve detectar contexto com professor."""
        analyzer = HumanReviewAnalyzer()
        text = "Sob orientação do professor Pablo Souza Ramos."
        result = {
            'contem_pii': True,
            'detalhes': [('nome', 'Pablo Souza Ramos', 1.0)]
        }

        items = analyzer.analyze("1", text, result)

        assert any(item.motivo == ReviewReason.ACADEMIC_CONTEXT for item in items)

    def test_detecta_universidade(self):
        """Deve detectar contexto de universidade."""
        analyzer = HumanReviewAnalyzer()
        text = "Sou formando na Universidade de São Paulo. Thiago Silva."
        result = {
            'contem_pii': True,
            'detalhes': [('nome', 'Thiago Silva', 1.0)]
        }

        items = analyzer.analyze("1", text, result)

        assert any(item.motivo == ReviewReason.ACADEMIC_CONTEXT for item in items)

    def test_nao_detecta_instituto_defesa(self):
        """Não deve detectar 'Instituto de Defesa' como contexto acadêmico."""
        analyzer = HumanReviewAnalyzer()
        text = "Protocolo do Instituto de Defesa do Consumidor. João Pereira."
        result = {
            'contem_pii': True,
            'detalhes': [('nome', 'João Pereira', 1.0)]
        }

        items = analyzer.analyze("1", text, result)

        assert not any(item.motivo == ReviewReason.ACADEMIC_CONTEXT for item in items)


class TestScoreConfidence:
    """Testes para classificação por score de confiança."""

    def test_score_baixo_alta_prioridade(self):
        """Score abaixo do threshold deve gerar alta prioridade."""
        config = HumanReviewConfig(low_confidence_threshold=0.80)
        analyzer = HumanReviewAnalyzer(config)

        text = "Nome: João Silva"
        result = {
            'contem_pii': True,
            'detalhes': [('nome', 'João Silva', 0.70)]  # Score baixo
        }

        items = analyzer.analyze("1", text, result)

        assert any(
            item.motivo == ReviewReason.LOW_CONFIDENCE and
            item.prioridade == ReviewPriority.HIGH
            for item in items
        )

    def test_score_medio_baixa_prioridade(self):
        """Score médio deve gerar baixa prioridade."""
        config = HumanReviewConfig(
            high_confidence_threshold=0.95,
            medium_confidence_threshold=0.80,
        )
        analyzer = HumanReviewAnalyzer(config)

        text = "Nome: João Silva"
        result = {
            'contem_pii': True,
            'detalhes': [('nome', 'João Silva', 0.90)]  # Score médio
        }

        items = analyzer.analyze("1", text, result)

        assert any(
            item.motivo == ReviewReason.MEDIUM_CONFIDENCE and
            item.prioridade == ReviewPriority.LOW
            for item in items
        )

    def test_score_alto_sem_revisao_por_score(self):
        """Score alto não deve gerar revisão por score."""
        config = HumanReviewConfig(high_confidence_threshold=0.95)
        analyzer = HumanReviewAnalyzer(config)

        text = "Nome: João Silva"
        result = {
            'contem_pii': True,
            'detalhes': [('nome', 'João Silva', 0.99)]  # Score alto
        }

        items = analyzer.analyze("1", text, result)

        # Não deve ter itens por score
        assert not any(
            item.motivo in (ReviewReason.LOW_CONFIDENCE, ReviewReason.MEDIUM_CONFIDENCE)
            for item in items
        )


class TestPrioridade:
    """Testes para classificação de prioridade."""

    def test_contexto_artistico_alta_prioridade(self):
        """Contexto artístico deve ter alta prioridade."""
        analyzer = HumanReviewAnalyzer()
        text = "Os vitrais de Portinari são lindos."
        result = {
            'contem_pii': True,
            'detalhes': [('nome', 'Portinari', 1.0)]
        }

        items = analyzer.analyze("1", text, result)

        artistic_items = [i for i in items if i.motivo == ReviewReason.ARTISTIC_CONTEXT]
        assert all(item.prioridade == ReviewPriority.HIGH for item in artistic_items)

    def test_contexto_academico_media_prioridade(self):
        """Contexto acadêmico deve ter média prioridade."""
        analyzer = HumanReviewAnalyzer()
        text = "Pesquisadora do Instituto de Ensino: Maria Lima."
        result = {
            'contem_pii': True,
            'detalhes': [('nome', 'Maria Lima', 1.0)]
        }

        items = analyzer.analyze("1", text, result)

        academic_items = [i for i in items if i.motivo == ReviewReason.ACADEMIC_CONTEXT]
        assert all(item.prioridade == ReviewPriority.MEDIUM for item in academic_items)


class TestSemPII:
    """Testes para casos sem PII."""

    def test_sem_pii_retorna_vazio(self):
        """Resultado sem PII não deve gerar itens de revisão."""
        analyzer = HumanReviewAnalyzer()
        text = "Texto sem dados pessoais."
        result = {
            'contem_pii': False,
            'detalhes': []
        }

        items = analyzer.analyze("1", text, result)

        assert len(items) == 0


class TestExtracaoContexto:
    """Testes para extração de contexto do texto."""

    def test_extrai_contexto_ao_redor(self):
        """Deve extrair trecho do texto ao redor do valor."""
        config = HumanReviewConfig(context_window=20)
        analyzer = HumanReviewAnalyzer(config)

        text = "Início do texto. Nome do cidadão: João Silva. Final do texto."
        result = {
            'contem_pii': True,
            'detalhes': [('nome', 'João Silva', 0.70)]
        }

        items = analyzer.analyze("1", text, result)

        assert len(items) > 0
        # O trecho deve conter o nome
        assert 'João Silva' in items[0].texto_trecho


class TestExportacao:
    """Testes para exportação de arquivos."""

    def test_export_csv(self):
        """Deve exportar corretamente para CSV."""
        items = [
            ReviewItem(
                id="1",
                texto_trecho="Texto de exemplo",
                tipo_pii="nome",
                valor_detectado="João Silva",
                score=0.95,
                motivo=ReviewReason.ARTISTIC_CONTEXT,
                prioridade=ReviewPriority.HIGH,
                contexto_adicional="Explicação"
            )
        ]

        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            output_path = f.name

        try:
            export_review_items(items, output_path, output_format='csv')

            # Verificar conteúdo
            with open(output_path, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                rows = list(reader)

            assert len(rows) == 2  # Header + 1 item
            assert rows[0][0] == 'ID'  # Header
            assert rows[1][0] == '1'  # ID do item
            assert rows[1][3] == 'João Silva'  # Valor detectado
        finally:
            Path(output_path).unlink(missing_ok=True)

    def test_export_json(self):
        """Deve exportar corretamente para JSON."""
        items = [
            ReviewItem(
                id="2",
                texto_trecho="Outro texto",
                tipo_pii="cpf",
                valor_detectado="123.456.789-00",
                score=0.85,
                motivo=ReviewReason.LOW_CONFIDENCE,
                prioridade=ReviewPriority.HIGH,
                contexto_adicional="Score baixo"
            )
        ]

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            output_path = f.name

        try:
            export_review_items(items, output_path, output_format='json')

            # Verificar conteúdo
            with open(output_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            assert len(data) == 1
            assert data[0]['id'] == '2'
            assert data[0]['valor_detectado'] == '123.456.789-00'
            assert data[0]['motivo'] == 'score_baixo'
        finally:
            Path(output_path).unlink(missing_ok=True)

    def test_export_lista_vazia(self):
        """Exportar lista vazia não deve criar arquivo."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            output_path = f.name

        # Remover arquivo temporário criado
        Path(output_path).unlink()

        export_review_items([], output_path, output_format='csv')

        # Arquivo não deve ser criado
        assert not Path(output_path).exists()


class TestFuncaoConveniencia:
    """Testes para função de conveniência analyze_for_review."""

    def test_analyze_for_review_funciona(self):
        """Função de conveniência deve funcionar."""
        text = "Os vitrais de Oscar Niemeyer são impressionantes."
        result = {
            'contem_pii': True,
            'detalhes': [('nome', 'Oscar Niemeyer', 1.0)]
        }

        items = analyze_for_review("1", text, result)

        assert isinstance(items, list)
        assert len(items) > 0

    def test_analyze_for_review_com_config(self):
        """Deve aceitar configuração customizada."""
        config = HumanReviewConfig(low_confidence_threshold=0.90)

        text = "Nome: Ana Costa"
        result = {
            'contem_pii': True,
            'detalhes': [('nome', 'Ana Costa', 0.85)]
        }

        items = analyze_for_review("1", text, result, config=config)

        assert any(item.motivo == ReviewReason.LOW_CONFIDENCE for item in items)


class TestCasosReais:
    """Testes baseados em casos reais da amostra."""

    def test_id15_athos_bulcao(self):
        """ID 15 deve ser marcado como contexto artístico."""
        analyzer = HumanReviewAnalyzer()
        text = (
            "No referido imóvel há inúmeros vitrais (imagens anexas), "
            "painéis Athos Bulsão, mosaicos de Gugon e lustres e luminárias antigas."
        )
        result = {
            'contem_pii': True,
            'detalhes': [
                ('nome', 'Athos Bulsão', 1.0),
                ('nome', 'Gugon', 1.0),
            ]
        }

        items = analyzer.analyze("15", text, result)

        # Deve ter itens de contexto artístico
        assert any(item.motivo == ReviewReason.ARTISTIC_CONTEXT for item in items)
        # Deve ter alta prioridade
        assert any(item.prioridade == ReviewPriority.HIGH for item in items)

    def test_id52_contexto_academico(self):
        """ID 52 deve ser marcado como contexto acadêmico."""
        analyzer = HumanReviewAnalyzer()
        text = (
            "Pesquisadora do Instituto Brasileiro de Ensino, Desenvolvimento e Pesquisa. "
            "Orientador: Profª. Doutorª. Fátima Lima. "
            "Carolina Guimarães Neves."
        )
        result = {
            'contem_pii': True,
            'detalhes': [
                ('nome', 'Carolina Guimarães Neves', 1.0),
                ('nome', 'Fátima Lima', 0.998),
            ]
        }

        items = analyzer.analyze("52", text, result)

        # Deve ter itens de contexto acadêmico
        assert any(item.motivo == ReviewReason.ACADEMIC_CONTEXT for item in items)
        # Deve ter média prioridade
        assert any(item.prioridade == ReviewPriority.MEDIUM for item in items)
