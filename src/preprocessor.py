# -*- coding: utf-8 -*-
"""
Módulo de pré-processamento de texto para detecção de PII.

Normaliza textos preservando informações críticas como:
- Dígitos (para CPF, telefone, RG)
- Separadores (pontos, hífens, barras)
- Caracteres especiais de email (@, .)
- Acentuação (para nomes próprios)

NÃO remove ou normaliza:
- Números e dígitos
- Pontuação em padrões de documentos
- Maiúsculas (importantes para NER)
"""

import re
import unicodedata
from typing import Optional


class TextPreprocessor:
    """
    Pré-processador de texto otimizado para detecção de PII.

    Faz normalização leve que preserva padrões importantes
    enquanto remove ruído irrelevante.
    """

    def __init__(self):
        """Inicializa o pré-processador."""
        # Padrão para múltiplos espaços
        self._multi_space = re.compile(r'\s+')

        # Padrão para caracteres de controle (exceto newline e tab)
        self._control_chars = re.compile(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]')

    def preprocess(self, text: Optional[str]) -> str:
        """
        Pré-processa o texto para detecção de PII.

        Operações realizadas:
        1. Tratamento de None/NaN
        2. Remoção de caracteres de controle
        3. Normalização de espaços
        4. Normalização Unicode (NFC)

        Args:
            text: Texto a ser processado (pode ser None)

        Returns:
            Texto normalizado, ou string vazia se input inválido
        """
        # Tratar None, NaN, e tipos não-string
        if text is None:
            return ''

        if not isinstance(text, str):
            text = str(text)

        # Verificar NaN do pandas
        if text.lower() == 'nan':
            return ''

        # Normalização Unicode (NFC - Canonical Decomposition, then Canonical Composition)
        # Isso garante que caracteres acentuados sejam representados consistentemente
        text = unicodedata.normalize('NFC', text)

        # Remover caracteres de controle (mantém \n e \t)
        text = self._control_chars.sub('', text)

        # Normalizar múltiplos espaços para um único espaço
        text = self._multi_space.sub(' ', text)

        # Remover espaços no início e fim
        text = text.strip()

        return text

    def preprocess_batch(self, texts: list) -> list:
        """
        Pré-processa uma lista de textos.

        Args:
            texts: Lista de textos

        Returns:
            Lista de textos pré-processados
        """
        return [self.preprocess(text) for text in texts]


def normalize_text(text: Optional[str]) -> str:
    """
    Função de conveniência para normalizar um único texto.

    Cria uma instância temporária de TextPreprocessor.
    Para processamento em batch, use TextPreprocessor diretamente.

    Args:
        text: Texto a ser normalizado

    Returns:
        Texto normalizado
    """
    preprocessor = TextPreprocessor()
    return preprocessor.preprocess(text)
