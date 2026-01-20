# -*- coding: utf-8 -*-
"""
Padrões regex para detecção de PII e filtros anti-falso positivo.

Este módulo contém todos os padrões regex otimizados para detectar
dados pessoais em textos de pedidos de acesso à informação brasileiros.

IMPORTANTE: Não usamos validação de dígitos verificadores de CPF porque
100% dos CPFs na amostra são sintéticos com dígitos inválidos.
"""

import re
from typing import List, Tuple, Optional


class PIIPatterns:
    """
    Gerenciador de padrões regex para detecção de PII.

    Implementa detecção de:
    - CPF (formatado e numérico com contexto)
    - Email
    - Telefone brasileiro
    - RG com contexto
    - Sinais contextuais de PII

    Também implementa filtros anti-falso positivo para:
    - Processos SEI/NUP
    - CDA, CNH, NIS, matrícula
    """

    # ==========================================================================
    # PADRÕES DE PII (DADOS PESSOAIS)
    # ==========================================================================

    # CPF formatado (XXX.XXX.XXX-XX) - alta confiança
    CPF_FORMATTED = r'\d{3}\.\d{3}\.\d{3}-\d{2}'

    # CPF numérico precedido por contexto explícito (11 dígitos)
    # Precisa de contexto "CPF" para evitar falsos positivos
    CPF_NUMERIC_CONTEXT = r'(?:CPF\s*[:\s]*)\b(\d{11})\b'

    # Email - padrão robusto
    EMAIL = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'

    # Telefone brasileiro - formato (XX) XXXXX-XXXX ou (XX) XXXX-XXXX
    PHONE = r'\(\d{2}\)\s*\d{4,5}-?\d{4}'

    # Telefone com prefixo +55
    PHONE_INTL = r'\+55\s*\(?\d{2}\)?\s*\d{4,5}[-\s]?\d{4}'

    # RG com contexto explícito
    RG = r'\bRG[:\s]*[\d.-]+'

    # ==========================================================================
    # PADRÕES DE EXCLUSÃO (FALSOS POSITIVOS)
    # ==========================================================================

    # Processo SEI - padrões comuns encontrados na amostra
    SEI_PATTERNS = [
        r'(?:SEI|NUP)\s*(?:nº|n°|n\.?)?\s*[\d./-]+',
        r'(?:Processo|processo)\s*(?:nº|n°|n\.?)?\s*[\d./-]+',
        r'protocolo\s*(?:nº|n°|n\.?)?\s*[\d./-]+',
    ]

    # Números de 11 dígitos que NÃO são CPF
    NOT_CPF_PATTERNS = [
        r'(?:CDA|CNH|NIS|matrícula|RNE|PIS|PASEP)\s*(?:nº|n°|n\.?)?\s*[:\s]*\d{11}',
    ]

    # ==========================================================================
    # SINAIS CONTEXTUAIS
    # ==========================================================================

    # Marcadores de primeira pessoa com dados pessoais
    FIRST_PERSON_DATA = [
        r'(?:meu|minha)\s+(?:CPF|nome|RG|telefone|email|e-mail|celular|endereço)',
        r'(?:sou|chamo-me|nome\s+é)\s+[A-Z][a-záàâãéêíóôõúç]+\s+[A-Z]',
    ]

    # Indicadores de endereço
    ADDRESS_MARKERS = [
        r'(?:moro|resido|residente)\s+(?:na?|em)',
        r'(?:rua|avenida|quadra|conjunto|bloco|lote|apartamento|apt\.?)\s+',
        r'CEP[:\s]*\d{5}-?\d{3}',
    ]

    # Indicadores de contato
    CONTACT_MARKERS = [
        r'(?:contato|WhatsApp|whatsapp|Whats|zap)\s*[:\s]*\(?\d',
        r'(?:fone|telefone|cel|celular)\s*[:\s]*\(?\d',
    ]

    def __init__(self):
        """Inicializa compilando os padrões regex para melhor performance."""
        # Compilar padrões principais
        self._cpf_formatted = re.compile(self.CPF_FORMATTED)
        self._cpf_numeric = re.compile(self.CPF_NUMERIC_CONTEXT, re.IGNORECASE)
        self._email = re.compile(self.EMAIL, re.IGNORECASE)
        self._phone = re.compile(self.PHONE)
        self._phone_intl = re.compile(self.PHONE_INTL)
        self._rg = re.compile(self.RG, re.IGNORECASE)

        # Compilar padrões de exclusão
        self._sei_patterns = [re.compile(p, re.IGNORECASE) for p in self.SEI_PATTERNS]
        self._not_cpf = [re.compile(p, re.IGNORECASE) for p in self.NOT_CPF_PATTERNS]

        # Compilar sinais contextuais
        self._first_person = [re.compile(p, re.IGNORECASE) for p in self.FIRST_PERSON_DATA]
        self._address = [re.compile(p, re.IGNORECASE) for p in self.ADDRESS_MARKERS]
        self._contact = [re.compile(p, re.IGNORECASE) for p in self.CONTACT_MARKERS]

    def find_all(self, text: str) -> List[Tuple[str, str, float]]:
        """
        Encontra todos os padrões de PII no texto.

        Args:
            text: Texto a ser analisado

        Returns:
            Lista de tuplas (tipo, valor, confiança)
            Ex: [('cpf', '123.456.789-00', 0.95), ('email', 'x@y.com', 0.95)]
        """
        if not text:
            return []

        results = []

        # CPF formatado (alta confiança)
        results.extend(self._find_cpf_formatted(text))

        # CPF numérico com contexto
        results.extend(self._find_cpf_numeric(text))

        # Email
        results.extend(self._find_email(text))

        # Telefone
        results.extend(self._find_phone(text))

        # RG
        results.extend(self._find_rg(text))

        return results

    def _find_cpf_formatted(self, text: str) -> List[Tuple[str, str, float]]:
        """
        Encontra CPFs formatados (XXX.XXX.XXX-XX).

        Aplica filtro anti-FP: ignora se estiver em contexto de processo SEI.
        """
        results = []
        for match in self._cpf_formatted.finditer(text):
            # Verificar se não está em contexto de processo SEI
            if not self._is_sei_context(text, match.start()):
                results.append(('cpf', match.group(), 0.95))
        return results

    def _find_cpf_numeric(self, text: str) -> List[Tuple[str, str, float]]:
        """
        Encontra CPFs numéricos (11 dígitos) precedidos por contexto "CPF".

        Só considera válido se tiver contexto explícito para evitar FP.
        """
        results = []
        for match in self._cpf_numeric.finditer(text):
            cpf_value = match.group(1)  # Grupo capturado (só os dígitos)
            # Verificar se não é outro tipo de documento
            if not self._is_not_cpf_context(text, match.start()):
                results.append(('cpf', cpf_value, 0.90))
        return results

    def _find_email(self, text: str) -> List[Tuple[str, str, float]]:
        """Encontra endereços de email."""
        results = []
        for match in self._email.finditer(text):
            results.append(('email', match.group(), 0.95))
        return results

    def _find_phone(self, text: str) -> List[Tuple[str, str, float]]:
        """Encontra telefones brasileiros."""
        results = []
        seen = set()

        # Telefone nacional
        for match in self._phone.finditer(text):
            phone = match.group()
            if phone not in seen:
                results.append(('telefone', phone, 0.90))
                seen.add(phone)

        # Telefone internacional (+55)
        for match in self._phone_intl.finditer(text):
            phone = match.group()
            if phone not in seen:
                results.append(('telefone', phone, 0.90))
                seen.add(phone)

        return results

    def _find_rg(self, text: str) -> List[Tuple[str, str, float]]:
        """Encontra números de RG com contexto explícito."""
        results = []
        for match in self._rg.finditer(text):
            results.append(('rg', match.group(), 0.85))
        return results

    def _is_sei_context(self, text: str, position: int) -> bool:
        """
        Verifica se a posição está em contexto de processo SEI/NUP.

        Olha até 50 caracteres antes para identificar marcadores de processo.
        """
        start = max(0, position - 50)
        context = text[start:position + 30]  # Incluir um pouco depois também

        for pattern in self._sei_patterns:
            if pattern.search(context):
                return True
        return False

    def _is_not_cpf_context(self, text: str, position: int) -> bool:
        """
        Verifica se um número de 11 dígitos NÃO é CPF.

        Retorna True se for CDA, CNH, NIS, matrícula, etc.
        """
        start = max(0, position - 30)
        context = text[start:position + 15]

        for pattern in self._not_cpf:
            if pattern.search(context):
                return True
        return False

    def find_contextual(self, text: str) -> List[Tuple[str, str, float]]:
        """
        Encontra sinais contextuais de PII.

        Detecta marcadores de primeira pessoa, endereços e contatos
        que indicam presença de dados pessoais mesmo sem padrão estruturado.

        Returns:
            Lista de tuplas (tipo, descrição, confiança)
        """
        if not text:
            return []

        results = []

        # Marcadores de primeira pessoa com dados
        for pattern in self._first_person:
            if pattern.search(text):
                results.append(('contexto_1pessoa', 'marcador_primeira_pessoa', 0.70))
                break  # Um sinal é suficiente

        # Marcadores de endereço
        for pattern in self._address:
            if pattern.search(text):
                results.append(('endereco', 'marcador_endereco', 0.60))
                break

        # Marcadores de contato
        for pattern in self._contact:
            if pattern.search(text):
                results.append(('contato', 'marcador_contato', 0.65))
                break

        return results

    def find_cpf(self, text: str) -> List[Tuple[str, str, float]]:
        """Wrapper para encontrar apenas CPFs."""
        return self._find_cpf_formatted(text) + self._find_cpf_numeric(text)

    def find_email(self, text: str) -> List[Tuple[str, str, float]]:
        """Wrapper para encontrar apenas emails."""
        return self._find_email(text)

    def find_phone(self, text: str) -> List[Tuple[str, str, float]]:
        """Wrapper para encontrar apenas telefones."""
        return self._find_phone(text)

    def find_rg(self, text: str) -> List[Tuple[str, str, float]]:
        """Wrapper para encontrar apenas RGs."""
        return self._find_rg(text)
