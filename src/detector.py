# -*- coding: utf-8 -*-
"""
Detector principal de PII (Personally Identifiable Information).

Combina múltiplas camadas de detecção:
1. Padrões regex estruturados (CPF, email, telefone, RG)
2. NER (Named Entity Recognition) para nomes de pessoas
3. Sinais contextuais (marcadores de 1ª pessoa, endereço, contato)

Estratégia: Recall-first (minimizar falsos negativos)
- Qualquer sinal positivo resulta em contem_pii=True
- Threshold baixo para maximizar sensibilidade

Modelos NER suportados:
- BERTimbau (padrão): ~99% precisão em PESSOA, requer transformers
- Fallback simples: heurística baseada em padrões de nomes
"""

import re
import logging
from typing import Dict, List, Tuple, Optional, Any

from .patterns import PIIPatterns
from .preprocessor import TextPreprocessor
from .exclusions import is_institutional_name

# Configurar logging
logger = logging.getLogger(__name__)


class PIIDetector:
    """
    Detector de dados pessoais em textos de pedidos de acesso à informação.

    Prioriza recall (sensibilidade) para minimizar falsos negativos,
    conforme critério de desempate do hackathon.

    Attributes:
        patterns: Instância de PIIPatterns para detecção por regex
        preprocessor: Instância de TextPreprocessor para normalização
        use_ner: Se True, usa modelo NER para detecção de nomes
        ner_pipeline: Pipeline do transformers para NER (se disponível)
    """

    def __init__(self, use_ner: bool = True, model_name: str = None):
        """
        Inicializa o detector de PII.

        Args:
            use_ner: Se True, tenta carregar modelo NER para detecção de nomes.
                    Se o modelo não estiver disponível, usa fallback.
            model_name: Nome do modelo NER a usar. Se None, usa BERTimbau padrão.
        """
        self.patterns = PIIPatterns()
        self.preprocessor = TextPreprocessor()
        self.use_ner = use_ner
        self.ner_pipeline = None
        self._ner_available = False

        if use_ner:
            self._init_ner(model_name)

    def _init_ner(self, model_name: Optional[str] = None):
        """
        Inicializa o pipeline de NER.

        Tenta carregar BERTimbau. Se falhar, usa fallback baseado em heurísticas.
        """
        if model_name is None:
            # Modelo BERTimbau treinado para NER em português
            model_name = "pierreguillou/ner-bert-base-cased-pt-lenerbr"

        try:
            from transformers import pipeline
            logger.info(f"Carregando modelo NER: {model_name}")
            self.ner_pipeline = pipeline(
                "ner",
                model=model_name,
                aggregation_strategy="simple"
            )
            self._ner_available = True
            logger.info("Modelo NER carregado com sucesso")
        except ImportError:
            logger.warning(
                "Biblioteca transformers não disponível. "
                "Usando fallback para detecção de nomes."
            )
            self._ner_available = False
        except Exception as e:
            logger.warning(
                f"Erro ao carregar modelo NER: {e}. "
                "Usando fallback para detecção de nomes."
            )
            self._ner_available = False

    def detect(self, text: str) -> Dict[str, Any]:
        """
        Detecta PII em um texto único.

        Executa as 3 camadas de detecção:
        1. Padrões regex (CPF, email, telefone, RG)
        2. NER para nomes de pessoas
        3. Sinais contextuais

        Args:
            text: Texto a ser analisado

        Returns:
            Dicionário com campos:
                - contem_pii (bool): True se algum PII foi detectado
                - tipos_detectados (list): Lista de tipos de PII encontrados
                - detalhes (list): Lista de tuplas (tipo, valor, confiança)
                - confianca (float): Maior confiança entre as detecções
        """
        # Pré-processar texto
        text_clean = self.preprocessor.preprocess(text)

        if not text_clean:
            return self._empty_result()

        pii_found: List[Tuple[str, str, float]] = []

        # Camada 1: Padrões estruturados (regex)
        pii_found.extend(self.patterns.find_all(text_clean))

        # Camada 2: NER para nomes de pessoas
        pii_found.extend(self._detect_names(text_clean))

        # Camada 3: Sinais contextuais
        pii_found.extend(self.patterns.find_contextual(text_clean))

        # Calcular resultado final
        return self._build_result(pii_found)

    def _detect_names(self, text: str) -> List[Tuple[str, str, float]]:
        """
        Detecta nomes de pessoas no texto.

        Usa NER se disponível, senão usa fallback baseado em heurísticas.

        Args:
            text: Texto pré-processado

        Returns:
            Lista de tuplas (tipo, nome, confiança)
        """
        if self._ner_available and self.ner_pipeline:
            return self._detect_names_ner(text)
        else:
            return self._detect_names_fallback(text)

    def _detect_names_ner(self, text: str) -> List[Tuple[str, str, float]]:
        """
        Detecta nomes usando modelo NER (BERTimbau).

        Filtra:
        - Nomes institucionais (Distrito Federal, etc.)
        - Nomes com menos de 2 palavras
        """
        results = []

        try:
            # Limitar tamanho do texto para evitar problemas de memória
            # BERTimbau tem limite de 512 tokens
            max_length = 1500
            text_truncated = text[:max_length] if len(text) > max_length else text

            entities = self.ner_pipeline(text_truncated)

            for ent in entities:
                # Verificar se é entidade de pessoa
                # Modelos diferentes podem usar labels diferentes
                entity_group = ent.get('entity_group', ent.get('entity', ''))

                if entity_group in ('PER', 'PESSOA', 'B-PER', 'I-PER', 'PERSON'):
                    name = ent.get('word', '').strip()
                    score = ent.get('score', 0.8)

                    # Validar nome
                    if self._is_valid_person_name(name):
                        results.append(('nome', name, score))

        except Exception as e:
            logger.warning(f"Erro no NER: {e}. Usando fallback.")
            return self._detect_names_fallback(text)

        return results

    def _detect_names_fallback(self, text: str) -> List[Tuple[str, str, float]]:
        """
        Fallback para detecção de nomes sem NER.

        Usa heurísticas baseadas em:
        - Padrões de nomes próprios (2+ palavras capitalizadas)
        - Contexto explícito ("nome:", "cidadão", "solicitante")
        """
        results = []

        # Padrão para nomes próprios: 2 ou mais palavras começando com maiúscula
        # seguidas por palavras que podem ser minúsculas (de, da, dos, etc.)
        name_pattern = re.compile(
            r'\b([A-Z][a-záàâãéêíóôõúç]+(?:\s+(?:de|da|do|das|dos|e)?\s*[A-Z][a-záàâãéêíóôõúç]+)+)\b'
        )

        # Contextos que indicam nome de pessoa
        name_contexts = [
            r'(?:nome|cidadão|cidadã|solicitante|requerente)[:\s]+([A-Z][a-záàâãéêíóôõúç\s]+)',
            r'(?:eu,?\s+)([A-Z][a-záàâãéêíóôõúç]+(?:\s+[A-Z][a-záàâãéêíóôõúç]+)+)',
        ]

        # Buscar nomes com contexto
        for pattern in name_contexts:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                name = match.group(1).strip()
                if self._is_valid_person_name(name):
                    results.append(('nome', name, 0.75))

        # Buscar nomes pelo padrão geral (menor confiança)
        for match in name_pattern.finditer(text):
            name = match.group(1).strip()
            if self._is_valid_person_name(name):
                # Verificar se já não foi detectado
                if not any(r[1] == name for r in results):
                    results.append(('nome', name, 0.60))

        return results

    def _is_valid_person_name(self, name: str) -> bool:
        """
        Verifica se é um nome de pessoa válido.

        Filtra:
        - Nomes muito curtos (< 2 palavras)
        - Nomes institucionais
        - Nomes muito longos (provavelmente não é nome)

        Args:
            name: Nome a verificar

        Returns:
            True se for um nome válido de pessoa
        """
        if not name:
            return False

        # Limpar nome
        name = name.strip()

        # Deve ter pelo menos 2 palavras
        words = name.split()
        if len(words) < 2:
            return False

        # Não deve ter mais de 6 palavras (provavelmente não é nome)
        if len(words) > 6:
            return False

        # Verificar se é nome institucional
        if is_institutional_name(name):
            return False

        return True

    def _build_result(self, pii_found: List[Tuple[str, str, float]]) -> Dict[str, Any]:
        """
        Constrói o resultado final da detecção.

        Args:
            pii_found: Lista de PIIs encontrados

        Returns:
            Dicionário com resultado estruturado
        """
        if not pii_found:
            return self._empty_result()

        # Extrair tipos únicos
        tipos = list(set(item[0] for item in pii_found))

        # Maior confiança
        confianca = max(item[2] for item in pii_found)

        return {
            'contem_pii': True,
            'tipos_detectados': tipos,
            'detalhes': pii_found,
            'confianca': round(confianca, 2)
        }

    def _empty_result(self) -> Dict[str, Any]:
        """Retorna resultado vazio (sem PII)."""
        return {
            'contem_pii': False,
            'tipos_detectados': [],
            'detalhes': [],
            'confianca': 0.0
        }

    def detect_batch(self, texts: List[str]) -> List[Dict[str, Any]]:
        """
        Processa uma lista de textos.

        Args:
            texts: Lista de textos a analisar

        Returns:
            Lista de resultados de detecção
        """
        return [self.detect(text) for text in texts]

    @property
    def ner_available(self) -> bool:
        """Indica se o modelo NER está disponível."""
        return self._ner_available
