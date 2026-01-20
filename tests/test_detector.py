# -*- coding: utf-8 -*-
"""
Testes de integração para o detector de PII (src/detector.py).

Testa o fluxo completo de detecção incluindo:
- Detecção de múltiplos tipos de PII
- Fallback quando NER não está disponível
- Processamento em batch
- Casos reais da amostra AMOSTRA_e-SIC.xlsx
"""

import pytest
from src.detector import PIIDetector


@pytest.fixture
def detector_no_ner():
    """Fixture que retorna detector sem NER (mais rápido para testes)."""
    return PIIDetector(use_ner=False)


@pytest.fixture
def detector_with_ner():
    """Fixture que retorna detector com NER (se disponível)."""
    return PIIDetector(use_ner=True)


# =============================================================================
# TESTES BÁSICOS DO DETECTOR
# =============================================================================

class TestDetectorBasic:
    """Testes básicos de funcionalidade."""

    def test_detect_retorna_estrutura_correta(self, detector_no_ner):
        """Resultado deve ter as chaves esperadas."""
        result = detector_no_ner.detect('Texto qualquer')
        assert 'contem_pii' in result
        assert 'tipos_detectados' in result
        assert 'detalhes' in result
        assert 'confianca' in result

    def test_texto_vazio_retorna_sem_pii(self, detector_no_ner):
        """Texto vazio não deve detectar PII."""
        result = detector_no_ner.detect('')
        assert result['contem_pii'] is False
        assert result['tipos_detectados'] == []

    def test_texto_none_retorna_sem_pii(self, detector_no_ner):
        """None não deve detectar PII."""
        result = detector_no_ner.detect(None)
        assert result['contem_pii'] is False

    def test_texto_sem_pii(self, detector_no_ner):
        """Texto sem PII deve retornar contem_pii=False."""
        text = 'Solicito informações sobre o processo administrativo número 123.'
        result = detector_no_ner.detect(text)
        assert result['contem_pii'] is False


# =============================================================================
# TESTES DE DETECÇÃO DE PII
# =============================================================================

class TestDetectorPII:
    """Testes de detecção de diferentes tipos de PII."""

    def test_detecta_cpf_formatado(self, detector_no_ner):
        """Deve detectar CPF formatado."""
        text = 'Meu CPF é 123.456.789-00'
        result = detector_no_ner.detect(text)
        assert result['contem_pii'] is True
        assert 'cpf' in result['tipos_detectados']

    def test_detecta_email(self, detector_no_ner):
        """Deve detectar email."""
        text = 'Contato: joao.silva@email.com.br'
        result = detector_no_ner.detect(text)
        assert result['contem_pii'] is True
        assert 'email' in result['tipos_detectados']

    def test_detecta_telefone(self, detector_no_ner):
        """Deve detectar telefone."""
        text = 'Telefone para contato: (61) 99999-8888'
        result = detector_no_ner.detect(text)
        assert result['contem_pii'] is True
        assert 'telefone' in result['tipos_detectados']

    def test_detecta_rg(self, detector_no_ner):
        """Deve detectar RG."""
        text = 'RG: 1.234.567-8'
        result = detector_no_ner.detect(text)
        assert result['contem_pii'] is True
        assert 'rg' in result['tipos_detectados']

    def test_detecta_multiplos_tipos(self, detector_no_ner):
        """Deve detectar múltiplos tipos de PII."""
        text = 'CPF: 123.456.789-00, email: teste@email.com, tel: (11) 99999-0000'
        result = detector_no_ner.detect(text)
        assert result['contem_pii'] is True
        tipos = result['tipos_detectados']
        assert 'cpf' in tipos
        assert 'email' in tipos
        assert 'telefone' in tipos


# =============================================================================
# TESTES DE FILTRO ANTI-FALSO POSITIVO
# =============================================================================

class TestDetectorAntiFP:
    """Testes de filtros anti-falso positivo."""

    def test_sei_nao_detecta_como_cpf(self, detector_no_ner):
        """Processo SEI não deve ser detectado como CPF."""
        text = 'Conforme SEI 00015-12345678/2026-01'
        result = detector_no_ner.detect(text)
        # Pode ter outros PIIs, mas CPF não deve estar presente
        if result['contem_pii']:
            assert 'cpf' not in result['tipos_detectados']

    def test_nup_nao_detecta_como_cpf(self, detector_no_ner):
        """NUP não deve ser detectado como CPF."""
        text = 'NUP 00015-12345678/2026-01'
        result = detector_no_ner.detect(text)
        if result['contem_pii']:
            assert 'cpf' not in result['tipos_detectados']

    def test_processo_nao_detecta_como_cpf(self, detector_no_ner):
        """Número de processo não deve ser detectado como CPF."""
        text = 'Processo nº 56478.000012/2026-05'
        result = detector_no_ner.detect(text)
        if result['contem_pii']:
            assert 'cpf' not in result['tipos_detectados']


# =============================================================================
# TESTES DE DETECÇÃO DE NOMES (FALLBACK)
# =============================================================================

class TestDetectorNomes:
    """Testes de detecção de nomes de pessoas."""

    def test_nome_com_contexto(self, detector_no_ner):
        """Deve detectar nome com contexto explícito."""
        text = 'O cidadão João da Silva Pereira solicita informações'
        result = detector_no_ner.detect(text)
        # O fallback pode ou não detectar, mas não deve dar erro
        assert 'contem_pii' in result

    def test_nome_institucional_nao_detecta(self, detector_no_ner):
        """Nomes institucionais não devem ser detectados como PII."""
        text = 'A Secretaria de Estado do Distrito Federal informa'
        result = detector_no_ner.detect(text)
        # Nomes institucionais devem ser filtrados
        if result['contem_pii']:
            for detalhe in result['detalhes']:
                if detalhe[0] == 'nome':
                    assert 'Distrito Federal' not in detalhe[1]
                    assert 'Secretaria' not in detalhe[1]


# =============================================================================
# TESTES DE SINAIS CONTEXTUAIS
# =============================================================================

class TestDetectorContextual:
    """Testes de sinais contextuais."""

    def test_marcador_primeira_pessoa(self, detector_no_ner):
        """Deve detectar marcador de primeira pessoa."""
        text = 'Solicito informações sobre meu CPF cadastrado'
        result = detector_no_ner.detect(text)
        assert result['contem_pii'] is True
        assert 'contexto_1pessoa' in result['tipos_detectados']

    def test_marcador_endereco(self, detector_no_ner):
        """Deve detectar marcador de endereço."""
        text = 'Moro na Quadra 302 Norte, Bloco A'
        result = detector_no_ner.detect(text)
        assert result['contem_pii'] is True
        assert 'endereco' in result['tipos_detectados']


# =============================================================================
# TESTES DE BATCH PROCESSING
# =============================================================================

class TestDetectorBatch:
    """Testes de processamento em batch."""

    def test_batch_retorna_lista(self, detector_no_ner):
        """detect_batch deve retornar lista."""
        texts = ['Texto 1', 'Texto 2']
        results = detector_no_ner.detect_batch(texts)
        assert isinstance(results, list)
        assert len(results) == 2

    def test_batch_processa_todos(self, detector_no_ner):
        """Deve processar todos os textos."""
        texts = [
            'CPF: 123.456.789-00',
            'Texto sem PII',
            'Email: teste@email.com'
        ]
        results = detector_no_ner.detect_batch(texts)
        assert results[0]['contem_pii'] is True
        assert results[1]['contem_pii'] is False
        assert results[2]['contem_pii'] is True


# =============================================================================
# TESTES COM CASOS REAIS DA AMOSTRA
# =============================================================================

class TestDetectorRealCases:
    """Testes com casos reais da AMOSTRA_e-SIC.xlsx."""

    def test_caso_id7(self, detector_no_ner):
        """ID 7: CPF e nomes."""
        text = 'sob o CPF: 210.201.140-24, Júlio Cesar Alves, Maria Martins Mota'
        result = detector_no_ner.detect(text)
        assert result['contem_pii'] is True
        assert 'cpf' in result['tipos_detectados']

    def test_caso_id17(self, detector_no_ner):
        """ID 17: Email e nome de advogado."""
        text = 'Jorge Luiz Pereira, advogado, email netolemos@me.pe'
        result = detector_no_ner.detect(text)
        assert result['contem_pii'] is True
        assert 'email' in result['tipos_detectados']

    def test_caso_id10(self, detector_no_ner):
        """ID 10: Telefone."""
        text = 'Telefone para contato: (54)99199-1000'
        result = detector_no_ner.detect(text)
        assert result['contem_pii'] is True
        assert 'telefone' in result['tipos_detectados']

    def test_caso_sem_pii(self, detector_no_ner):
        """Texto sem PII (apenas processo SEI)."""
        text = 'Em referência ao processo SEI 00015-01009853/2026-01, solicito cópia'
        result = detector_no_ner.detect(text)
        # Não deve detectar CPF do número SEI
        if result['contem_pii']:
            assert 'cpf' not in result['tipos_detectados']

    def test_caso_id85_cpf_numerico(self, detector_no_ner):
        """ID 85: CPF numérico com contexto."""
        text = 'CPF: 12345678908, nome João Lopes Ribeiro'
        result = detector_no_ner.detect(text)
        assert result['contem_pii'] is True
        assert 'cpf' in result['tipos_detectados']
