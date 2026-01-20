# -*- coding: utf-8 -*-
"""
Testes unitários para o módulo de padrões regex (src/patterns.py).

Testa detecção de CPF, email, telefone, RG e filtros anti-falso positivo.
"""

import pytest
from src.patterns import PIIPatterns


@pytest.fixture
def patterns():
    """Fixture que retorna uma instância de PIIPatterns."""
    return PIIPatterns()


# =============================================================================
# TESTES DE DETECÇÃO DE CPF
# =============================================================================

class TestCPFDetection:
    """Testes de detecção de CPF."""

    def test_cpf_formatado_simples(self, patterns):
        """Deve detectar CPF no formato XXX.XXX.XXX-XX."""
        text = 'O CPF do solicitante é 123.456.789-00.'
        result = patterns.find_cpf(text)
        assert len(result) == 1
        assert result[0][0] == 'cpf'
        assert result[0][1] == '123.456.789-00'
        assert result[0][2] >= 0.9

    def test_cpf_formatado_multiplos(self, patterns):
        """Deve detectar múltiplos CPFs formatados."""
        text = 'CPF: 111.222.333-44 e também 555.666.777-88'
        result = patterns.find_cpf(text)
        assert len(result) == 2

    def test_cpf_numerico_com_contexto(self, patterns):
        """Deve detectar CPF numérico quando precedido por 'CPF'."""
        text = 'CPF: 12345678900'
        result = patterns.find_cpf(text)
        assert len(result) == 1
        assert result[0][1] == '12345678900'

    def test_cpf_numerico_sem_contexto_nao_detecta(self, patterns):
        """NÃO deve detectar 11 dígitos sem contexto 'CPF'."""
        text = 'O número 12345678900 é um código qualquer.'
        result = patterns.find_cpf(text)
        assert len(result) == 0

    def test_cpf_em_contexto_sei_nao_detecta(self, patterns):
        """NÃO deve detectar CPF em contexto de processo SEI."""
        text = 'Processo SEI 00015-12345678/2026-01'
        result = patterns.find_cpf(text)
        assert len(result) == 0

    def test_cpf_em_contexto_nup_nao_detecta(self, patterns):
        """NÃO deve detectar CPF em contexto de NUP."""
        text = 'NUP 00015-12345678/2026-01'
        result = patterns.find_cpf(text)
        assert len(result) == 0

    def test_cpf_em_contexto_processo_nao_detecta(self, patterns):
        """NÃO deve detectar CPF em contexto de Processo."""
        text = 'Processo nº 56478.000012/2026-05'
        result = patterns.find_cpf(text)
        assert len(result) == 0

    def test_cda_nao_confunde_com_cpf(self, patterns):
        """NÃO deve detectar CDA como CPF."""
        text = 'CDA n. 08563214753'
        result = patterns.find_cpf(text)
        assert len(result) == 0

    def test_cnh_nao_confunde_com_cpf(self, patterns):
        """NÃO deve detectar CNH como CPF."""
        text = 'CNH: 78945612378'
        result = patterns.find_cpf(text)
        assert len(result) == 0

    def test_nis_nao_confunde_com_cpf(self, patterns):
        """NÃO deve detectar NIS como CPF."""
        text = 'Nis: 98765432165'
        result = patterns.find_cpf(text)
        assert len(result) == 0


# =============================================================================
# TESTES DE DETECÇÃO DE EMAIL
# =============================================================================

class TestEmailDetection:
    """Testes de detecção de email."""

    def test_email_simples(self, patterns):
        """Deve detectar email simples."""
        text = 'Contato: joao@email.com'
        result = patterns.find_email(text)
        assert len(result) == 1
        assert result[0][1] == 'joao@email.com'

    def test_email_com_subdominio(self, patterns):
        """Deve detectar email com subdomínio."""
        text = 'Email: maria.silva@empresa.gov.br'
        result = patterns.find_email(text)
        assert len(result) == 1
        assert 'empresa.gov.br' in result[0][1]

    def test_email_com_numeros(self, patterns):
        """Deve detectar email com números."""
        text = 'usuario123@dominio456.net'
        result = patterns.find_email(text)
        assert len(result) == 1

    def test_email_com_caracteres_especiais(self, patterns):
        """Deve detectar email com caracteres especiais válidos."""
        text = 'jose.silva+teste@email.com.br'
        result = patterns.find_email(text)
        assert len(result) == 1

    def test_email_multiplos(self, patterns):
        """Deve detectar múltiplos emails."""
        text = 'Emails: a@b.com e c@d.org'
        result = patterns.find_email(text)
        assert len(result) == 2


# =============================================================================
# TESTES DE DETECÇÃO DE TELEFONE
# =============================================================================

class TestPhoneDetection:
    """Testes de detecção de telefone."""

    def test_telefone_celular_com_hifen(self, patterns):
        """Deve detectar telefone celular com hífen."""
        text = 'Telefone: (11) 99999-8888'
        result = patterns.find_phone(text)
        assert len(result) == 1
        assert '99999-8888' in result[0][1]

    def test_telefone_celular_sem_hifen(self, patterns):
        """Deve detectar telefone celular sem hífen."""
        text = 'Cel: (21) 987654321'
        result = patterns.find_phone(text)
        assert len(result) == 1

    def test_telefone_fixo(self, patterns):
        """Deve detectar telefone fixo."""
        text = 'Fone: (61) 3333-4444'
        result = patterns.find_phone(text)
        assert len(result) == 1

    def test_telefone_internacional(self, patterns):
        """Deve detectar telefone com prefixo +55."""
        text = 'WhatsApp: +55 11 99999-1234'
        result = patterns.find_phone(text)
        assert len(result) >= 1

    def test_telefone_multiplos(self, patterns):
        """Deve detectar múltiplos telefones."""
        text = 'Contatos: (11) 99999-1111 e (21) 88888-2222'
        result = patterns.find_phone(text)
        assert len(result) == 2


# =============================================================================
# TESTES DE DETECÇÃO DE RG
# =============================================================================

class TestRGDetection:
    """Testes de detecção de RG."""

    def test_rg_com_contexto(self, patterns):
        """Deve detectar RG com contexto explícito."""
        text = 'RG: 12.345.678-9'
        result = patterns.find_rg(text)
        assert len(result) == 1

    def test_rg_simples(self, patterns):
        """Deve detectar RG simples."""
        text = 'RG 1234567'
        result = patterns.find_rg(text)
        assert len(result) == 1

    def test_rg_com_dois_pontos(self, patterns):
        """Deve detectar RG com dois pontos."""
        text = 'Documento RG: 9876543'
        result = patterns.find_rg(text)
        assert len(result) == 1


# =============================================================================
# TESTES DE SINAIS CONTEXTUAIS
# =============================================================================

class TestContextualSignals:
    """Testes de sinais contextuais."""

    def test_primeira_pessoa_cpf(self, patterns):
        """Deve detectar marcador de primeira pessoa com CPF."""
        text = 'Solicito informações sobre meu CPF'
        result = patterns.find_contextual(text)
        assert any(r[0] == 'contexto_1pessoa' for r in result)

    def test_primeira_pessoa_nome(self, patterns):
        """Deve detectar marcador de primeira pessoa com nome."""
        text = 'O meu nome completo é informado abaixo'
        result = patterns.find_contextual(text)
        assert any(r[0] == 'contexto_1pessoa' for r in result)

    def test_marcador_endereco(self, patterns):
        """Deve detectar marcador de endereço."""
        text = 'Moro na Quadra 302 Norte'
        result = patterns.find_contextual(text)
        assert any(r[0] == 'endereco' for r in result)

    def test_marcador_cep(self, patterns):
        """Deve detectar CEP como marcador de endereço."""
        text = 'CEP: 70000-000'
        result = patterns.find_contextual(text)
        assert any(r[0] == 'endereco' for r in result)

    def test_marcador_contato(self, patterns):
        """Deve detectar marcador de contato."""
        text = 'WhatsApp: (61) 99999'
        result = patterns.find_contextual(text)
        assert any(r[0] == 'contato' for r in result)


# =============================================================================
# TESTES DO MÉTODO find_all
# =============================================================================

class TestFindAll:
    """Testes do método find_all que combina todas as detecções."""

    def test_find_all_multiplos_tipos(self, patterns):
        """Deve encontrar múltiplos tipos de PII."""
        text = 'CPF: 123.456.789-00, email: teste@email.com, tel: (11) 99999-0000'
        result = patterns.find_all(text)
        tipos = [r[0] for r in result]
        assert 'cpf' in tipos
        assert 'email' in tipos
        assert 'telefone' in tipos

    def test_find_all_texto_limpo(self, patterns):
        """Deve retornar lista vazia para texto sem PII."""
        text = 'Solicito informações sobre o processo administrativo.'
        result = patterns.find_all(text)
        assert len(result) == 0

    def test_find_all_texto_vazio(self, patterns):
        """Deve retornar lista vazia para texto vazio."""
        result = patterns.find_all('')
        assert len(result) == 0

    def test_find_all_texto_none(self, patterns):
        """Deve retornar lista vazia para None."""
        result = patterns.find_all(None)
        assert len(result) == 0


# =============================================================================
# TESTES COM CASOS REAIS DA AMOSTRA
# =============================================================================

class TestRealSampleCases:
    """Testes com casos reais encontrados na AMOSTRA_e-SIC.xlsx."""

    def test_caso_id7_cpf_com_nome(self, patterns):
        """ID 7: CPF 210.201.140-24 com nome Júlio Cesar."""
        text = 'sob o CPF: 210.201.140-24, Júlio Cesar Alves solicitou'
        result = patterns.find_all(text)
        cpfs = [r for r in result if r[0] == 'cpf']
        assert len(cpfs) == 1
        assert cpfs[0][1] == '210.201.140-24'

    def test_caso_id17_email_advogado(self, patterns):
        """ID 17: Email de advogado."""
        text = 'Jorge Luiz Pereira, email netolemos@me.pe'
        result = patterns.find_all(text)
        emails = [r for r in result if r[0] == 'email']
        assert len(emails) == 1
        assert emails[0][1] == 'netolemos@me.pe'

    def test_caso_id10_telefone(self, patterns):
        """ID 10: Telefone (54)99199-1000."""
        text = 'Telefone para contato: (54)99199-1000'
        result = patterns.find_all(text)
        phones = [r for r in result if r[0] == 'telefone']
        assert len(phones) == 1

    def test_caso_sei_filtro(self, patterns):
        """Filtro SEI: Processo SEI 00015-01009853/2026-01."""
        text = 'Conforme SEI 00015-01009853/2026-01, solicito'
        result = patterns.find_all(text)
        cpfs = [r for r in result if r[0] == 'cpf']
        # Não deve detectar o número do processo como CPF
        assert len(cpfs) == 0

    def test_caso_id85_cpf_numerico(self, patterns):
        """ID 85: CPF numérico 12345678908."""
        text = 'CPF: 12345678908, nome João Lopes Ribeiro'
        result = patterns.find_all(text)
        cpfs = [r for r in result if r[0] == 'cpf']
        assert len(cpfs) == 1
        assert cpfs[0][1] == '12345678908'
