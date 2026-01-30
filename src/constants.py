# -*- coding: utf-8 -*-
"""
Constantes centralizadas do projeto VIGIL.

Reúne valores configuráveis que antes estavam hardcoded em múltiplos módulos.
"""

# Limite máximo de tamanho de arquivo de entrada (em MB)
MAX_FILE_SIZE_MB = 500
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024

# Limite de caracteres para processamento NER (~375 tokens, conservador para 512 do modelo)
DEFAULT_NER_MAX_LENGTH = 1500

# Modelo NER padrão (BERTimbau treinado para NER em português)
DEFAULT_NER_MODEL = "pierreguillou/ner-bert-base-cased-pt-lenerbr"

# Modelos NER permitidos (whitelist de segurança)
ALLOWED_NER_MODELS = frozenset({
    "pierreguillou/ner-bert-base-cased-pt-lenerbr",
})

# Chaves conhecidas para arrays em JSON de entrada
JSON_ARRAY_KEYS = ('registros', 'data', 'resultados')

# Limite máximo de registros em JSON de entrada
MAX_JSON_RECORDS = 100_000

# Labels de entidade NER reconhecidas como pessoa
NER_PERSON_LABELS = frozenset({'PER', 'PESSOA', 'B-PER', 'I-PER', 'PERSON'})
