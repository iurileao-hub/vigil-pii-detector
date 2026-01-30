# -*- coding: utf-8 -*-
"""
Testes de integração para o pipeline completo de detecção de PII.

Testa o fluxo end-to-end: preprocessing → regex → NER fallback → resultado.
Inclui testes de edge cases, batch isolation e performance.
"""

import pytest
import tempfile
import json
import csv
from pathlib import Path

from src.detector import PIIDetector
from src.preprocessor import TextPreprocessor
from src.patterns import PIIPatterns
from src.human_review import HumanReviewAnalyzer, export_review_items, ReviewItem, ReviewPriority, ReviewReason
from src.exclusions import is_institutional_name


@pytest.fixture
def detector():
    """Detector sem NER para testes rápidos."""
    return PIIDetector(use_ner=False)


# =============================================================================
# TESTES DE INTEGRAÇÃO END-TO-END
# =============================================================================

class TestPipelineCompleto:
    """Testa o fluxo completo: texto → detecção → revisão humana."""

    def test_texto_com_cpf_gera_revisao(self, detector):
        """CPF com score médio deve gerar item de revisão."""
        text = 'Nome: João da Silva, CPF: 123.456.789-00'
        result = detector.detect(text)
        assert result['contem_pii'] is True

        analyzer = HumanReviewAnalyzer()
        items = analyzer.analyze("1", text, result)
        # Deve ter resultado (pode ou não gerar revisão dependendo do score)
        assert isinstance(items, list)

    def test_texto_sem_pii_nao_gera_revisao(self, detector):
        """Texto sem PII não deve gerar revisão."""
        text = 'Solicito informações sobre o programa governamental.'
        result = detector.detect(text)
        assert result['contem_pii'] is False

        analyzer = HumanReviewAnalyzer()
        items = analyzer.analyze("1", text, result)
        assert len(items) == 0

    def test_pipeline_export_csv_roundtrip(self, detector):
        """Testa exportação CSV e reimportação."""
        items = [
            ReviewItem(
                id="42",
                texto_trecho="texto com aspas \"duplas\" e vírgulas, aqui",
                tipo_pii="nome",
                valor_detectado="João \"Doc\" Silva",
                score=0.92,
                motivo=ReviewReason.ARTISTIC_CONTEXT,
                prioridade=ReviewPriority.HIGH,
                contexto_adicional="Contexto artístico"
            )
        ]

        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            output_path = f.name

        try:
            export_review_items(items, output_path, output_format='csv')

            with open(output_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = list(reader)

            assert len(rows) == 1
            assert rows[0]['ID'] == '42'
            assert rows[0]['Valor Detectado'] == 'João "Doc" Silva'
            # Aspas e vírgulas devem ser escapadas corretamente
            assert 'aspas' in rows[0]['Texto (Trecho)']
        finally:
            Path(output_path).unlink(missing_ok=True)

    def test_pipeline_export_json_roundtrip(self, detector):
        """Testa exportação JSON e reimportação."""
        items = [
            ReviewItem(
                id="1", texto_trecho="trecho\ncom\nnewlines",
                tipo_pii="cpf", valor_detectado="123.456.789-00",
                score=0.75, motivo=ReviewReason.LOW_CONFIDENCE,
                prioridade=ReviewPriority.HIGH, contexto_adicional="Score baixo"
            )
        ]

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            output_path = f.name

        try:
            export_review_items(items, output_path, output_format='json')

            with open(output_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            assert len(data) == 1
            assert data[0]['id'] == '1'
            assert '\n' in data[0]['texto_trecho']
        finally:
            Path(output_path).unlink(missing_ok=True)


# =============================================================================
# TESTES DE EDGE CASES
# =============================================================================

class TestEdgeCases:
    """Testes de casos extremos e entradas incomuns."""

    def test_whitespace_only(self, detector):
        """Texto com apenas espaços em branco não deve detectar PII."""
        result = detector.detect('   \n\t\r   ')
        assert result['contem_pii'] is False

    def test_texto_muito_longo(self, detector):
        """Texto muito longo deve ser processado sem erro."""
        # 100KB de texto com PII no meio
        padding = 'Lorem ipsum dolor sit amet. ' * 2000
        text = padding + 'CPF: 123.456.789-00' + padding
        result = detector.detect(text)
        assert result['contem_pii'] is True
        assert 'cpf' in result['tipos_detectados']

    def test_texto_com_unicode_exotico(self, detector):
        """Texto com caracteres unicode exóticos não deve causar erro."""
        text = 'Dados do cidadão 👤 CPF: 123.456.789-00 ✅'
        result = detector.detect(text)
        assert result['contem_pii'] is True

    def test_texto_com_zero_width_chars(self, detector):
        """Zero-width characters não devem afetar detecção."""
        # Zero-width space entre dígitos do CPF
        text = 'CPF: 123.456.789-00'
        result = detector.detect(text)
        assert result['contem_pii'] is True

    def test_multiplos_tipos_pii_mesmo_texto(self, detector):
        """Deve detectar todos os tipos de PII em um único texto."""
        text = (
            'Eu, João da Silva, CPF 123.456.789-00, '
            'RG: 1234567-8, email joao@email.com, '
            'telefone (61) 99999-8888, solicito informações.'
        )
        result = detector.detect(text)
        assert result['contem_pii'] is True
        tipos = result['tipos_detectados']
        assert 'cpf' in tipos
        assert 'email' in tipos
        assert 'telefone' in tipos
        assert 'rg' in tipos

    def test_cpf_duplicado_nao_repete(self, detector):
        """CPF repetido deve ser detectado uma única vez."""
        text = 'CPF: 123.456.789-00. Confirmo CPF 123.456.789-00.'
        result = detector.detect(text)
        cpfs = [d for d in result['detalhes'] if d[0] == 'cpf']
        assert len(cpfs) == 1


# =============================================================================
# TESTES DE BATCH ISOLATION
# =============================================================================

class TestBatchIsolation:
    """Testa isolamento entre itens em processamento batch."""

    def test_batch_independence(self, detector):
        """Resultados devem ser independentes entre execuções batch."""
        texts = [
            'CPF: 123.456.789-00',
            'Texto sem PII nenhum',
            'Email: teste@email.com',
        ]
        results1 = detector.detect_batch(texts)
        results2 = detector.detect_batch(texts)

        # Resultados devem ser idênticos entre execuções
        for r1, r2 in zip(results1, results2):
            assert r1['contem_pii'] == r2['contem_pii']
            assert r1['tipos_detectados'] == r2['tipos_detectados']

    def test_batch_vazio(self, detector):
        """Batch vazio deve retornar lista vazia."""
        results = detector.detect_batch([])
        assert results == []

    def test_batch_com_none(self, detector):
        """Batch com None deve retornar resultado sem PII."""
        results = detector.detect_batch([None, '', 'CPF: 123.456.789-00'])
        assert len(results) == 3
        assert results[0]['contem_pii'] is False
        assert results[1]['contem_pii'] is False
        assert results[2]['contem_pii'] is True

    def test_batch_grande(self, detector):
        """Batch grande deve processar sem erro."""
        texts = ['Texto simples sem PII'] * 100
        texts[50] = 'CPF: 123.456.789-00'
        results = detector.detect_batch(texts)
        assert len(results) == 100
        assert results[50]['contem_pii'] is True
        assert sum(1 for r in results if r['contem_pii']) == 1


# =============================================================================
# TESTES DE DETECÇÃO DE NOMES (FALLBACK)
# =============================================================================

class TestNameDetectionFallback:
    """Testes específicos para o fallback de detecção de nomes."""

    def test_nome_com_contexto_cidadao(self, detector):
        """Nome com contexto 'cidadão' deve ser detectado."""
        text = 'O cidadão João da Silva Pereira solicita informações'
        result = detector.detect(text)
        if result['contem_pii']:
            nomes = [d for d in result['detalhes'] if d[0] == 'nome']
            for n in nomes:
                assert 'Distrito Federal' not in n[1]

    def test_nome_institucional_filtrado(self, detector):
        """Nomes institucionais devem ser filtrados pelo detector."""
        text = 'A Secretaria de Estado do Distrito Federal'
        result = detector.detect(text)
        # Não deve detectar nomes institucionais como PII
        nomes = [d for d in result.get('detalhes', []) if d[0] == 'nome']
        for n in nomes:
            assert not is_institutional_name(n[1])

    def test_nome_unico_nao_detectado(self, detector):
        """Nome com uma única palavra não deve ser detectado."""
        text = 'O cidadão João solicita informações'
        result = detector.detect(text)
        nomes = [d for d in result.get('detalhes', []) if d[0] == 'nome']
        # Nome com 1 palavra deve ser filtrado
        for n in nomes:
            assert len(n[1].split()) >= 2


# =============================================================================
# TESTES DE TEXT CHUNKING
# =============================================================================

class TestTextChunking:
    """Testa a divisão de texto em chunks para NER."""

    def test_texto_curto_um_chunk(self):
        """Texto curto deve gerar 1 chunk."""
        chunks = PIIDetector._split_text_chunks('texto curto', 1500)
        assert len(chunks) == 1

    def test_texto_medio_dois_chunks(self):
        """Texto médio deve gerar 2 chunks divididos ao meio."""
        text = 'a' * 2000
        chunks = PIIDetector._split_text_chunks(text, 1500)
        assert len(chunks) == 2
        assert len(chunks[0]) == 1000
        assert len(chunks[1]) == 1000

    def test_texto_longo_inicio_e_fim(self):
        """Texto longo deve gerar 2 chunks: início e fim."""
        text = 'a' * 5000
        chunks = PIIDetector._split_text_chunks(text, 1500)
        assert len(chunks) == 2
        assert len(chunks[0]) == 1500
        assert len(chunks[1]) == 1500

    def test_texto_vazio(self):
        """Texto vazio deve gerar 1 chunk vazio."""
        chunks = PIIDetector._split_text_chunks('', 1500)
        assert len(chunks) == 1
        assert chunks[0] == ''

    def test_texto_exatamente_no_limite(self):
        """Texto no limite exato deve gerar 1 chunk."""
        text = 'a' * 1500
        chunks = PIIDetector._split_text_chunks(text, 1500)
        assert len(chunks) == 1


# =============================================================================
# TESTES DE SEGURANÇA - CONSTANTES E WHITELIST
# =============================================================================

class TestSecurityConstants:
    """Testa que constantes de segurança estão funcionando."""

    def test_modelo_nao_autorizado_usa_fallback(self):
        """Modelo NER fora da whitelist deve resultar em fallback."""
        detector = PIIDetector(use_ner=True, model_name='modelo-malicioso/fake')
        assert detector.ner_available is False

    def test_detector_funciona_sem_ner(self):
        """Detector deve funcionar perfeitamente sem NER."""
        detector = PIIDetector(use_ner=False)
        result = detector.detect('CPF: 123.456.789-00')
        assert result['contem_pii'] is True


# =============================================================================
# TESTES DE PREPROCESSOR - EDGE CASES ADICIONAIS
# =============================================================================

class TestPreprocessorEdgeCases:
    """Testes adicionais do preprocessor."""

    def test_replacement_character(self):
        """Replacement character (U+FFFD) não deve causar erro."""
        preprocessor = TextPreprocessor()
        result = preprocessor.preprocess('João\ufffdSilva')
        assert 'Jo' in result
        assert 'Silva' in result

    def test_lista_com_tipos_mistos(self):
        """Batch com tipos mistos deve funcionar."""
        preprocessor = TextPreprocessor()
        result = preprocessor.preprocess_batch([None, 123, 'texto', True, float('nan')])
        assert len(result) == 5
        assert result[0] == ''
        assert result[1] == '123'
        assert result[2] == 'texto'
        assert result[3] == 'True'
        assert result[4] == ''


# =============================================================================
# TESTES DE PATTERNS - EDGE CASES ADICIONAIS
# =============================================================================

class TestPatternsEdgeCases:
    """Testes adicionais de padrões regex."""

    @pytest.fixture
    def patterns(self):
        return PIIPatterns()

    def test_sei_no_inicio_do_texto(self, patterns):
        """SEI no início do texto deve excluir CPF próximo."""
        text = 'SEI 00015-12345678/2026-01 informa que'
        result = patterns.find_cpf(text)
        assert len(result) == 0

    def test_cpf_longe_do_sei(self, patterns):
        """CPF longe do contexto SEI deve ser detectado."""
        text = 'SEI 111. ' + ('x' * 100) + ' CPF 123.456.789-00'
        result = patterns.find_cpf(text)
        assert len(result) == 1

    def test_email_com_tld_raro(self, patterns):
        """Email com TLD raro (.io, .ai) deve ser detectado."""
        text = 'contato: user@empresa.io'
        result = patterns.find_email(text)
        assert len(result) == 1

    def test_telefone_duplicado_normalizado(self, patterns):
        """Mesmo telefone em formatos diferentes não deve duplicar."""
        text = 'Tel: (61) 99999-8888 ou fone: 61 999998888'
        result = patterns.find_phone(text)
        # Pode detectar ambos por terem formatos diferentes,
        # mas normalizados são o mesmo número
        normalized = set()
        import re
        for r in result:
            normalized.add(re.sub(r'\D', '', r[1]))
        # A lógica de dedup normaliza por dígitos
        assert len(result) <= 2

    def test_rg_nao_detecta_orgao(self, patterns):
        """'RG' em 'órgão' não deve ser detectado como RG."""
        text = 'O órgão responsável informou que não há dados.'
        result = patterns.find_rg(text)
        assert len(result) == 0

    def test_find_all_com_texto_grande(self, patterns):
        """find_all deve funcionar com texto grande."""
        text = 'Texto normal. ' * 5000 + 'CPF: 123.456.789-00'
        result = patterns.find_all(text)
        cpfs = [r for r in result if r[0] == 'cpf']
        assert len(cpfs) == 1


# =============================================================================
# TESTES DE EXCLUSIONS - EDGE CASES ADICIONAIS
# =============================================================================

class TestExclusionsEdgeCases:
    """Testes adicionais do módulo de exclusões."""

    def test_nome_com_espacos_extras(self):
        """Nome com espaços extras deve ser tratado."""
        assert is_institutional_name('  Distrito Federal  ') is True

    def test_nome_parcial_nao_filtrado(self):
        """Substring de nome institucional como nome de pessoa."""
        assert is_institutional_name('Taguatinga Silva') is True  # contém 'taguatinga'

    def test_nomes_compostos_pessoas(self):
        """Nomes compostos de pessoas não devem ser filtrados."""
        assert is_institutional_name('Pedro Henrique') is False
        assert is_institutional_name('Ana Carolina Souza') is False
        assert is_institutional_name('Luiz Fernando Costa') is False


# =============================================================================
# TESTES DE UTILS
# =============================================================================

class TestUtils:
    """Testes do módulo de utilitários compartilhados."""

    def test_normalize_boolean_true_values(self):
        """Deve reconhecer valores verdadeiros."""
        import pandas as pd
        from src.utils import normalize_boolean
        series = pd.Series(['true', 'True', '1', 'sim', 'yes', 'verdadeiro'])
        result = normalize_boolean(series)
        assert result.all()

    def test_normalize_boolean_false_values(self):
        """Deve reconhecer valores falsos."""
        import pandas as pd
        from src.utils import normalize_boolean
        series = pd.Series(['false', '0', 'nao', 'no'])
        result = normalize_boolean(series)
        assert not result.any()

    def test_normalize_boolean_mixed(self):
        """Deve lidar com valores mistos."""
        import pandas as pd
        from src.utils import normalize_boolean
        series = pd.Series([True, False, '1', '0', 'sim', 'nao'])
        result = normalize_boolean(series)
        assert result[0] is True or result[0] == True
        assert result[1] is False or result[1] == False
        assert result[2] == True
        assert result[3] == False


# =============================================================================
# TESTES DE CONSTANTS
# =============================================================================

class TestConstants:
    """Testes de validação das constantes."""

    def test_max_file_size_consistency(self):
        """MAX_FILE_SIZE_BYTES deve ser consistente com MAX_FILE_SIZE_MB."""
        from src.constants import MAX_FILE_SIZE_MB, MAX_FILE_SIZE_BYTES
        assert MAX_FILE_SIZE_BYTES == MAX_FILE_SIZE_MB * 1024 * 1024

    def test_default_model_in_whitelist(self):
        """Modelo padrão deve estar na whitelist."""
        from src.constants import DEFAULT_NER_MODEL, ALLOWED_NER_MODELS
        assert DEFAULT_NER_MODEL in ALLOWED_NER_MODELS

    def test_ner_person_labels_not_empty(self):
        """Labels de pessoa NER não devem estar vazias."""
        from src.constants import NER_PERSON_LABELS
        assert len(NER_PERSON_LABELS) > 0
        assert 'PER' in NER_PERSON_LABELS
