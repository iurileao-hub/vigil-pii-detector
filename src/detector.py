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
            logger.info("Carregando modelo NER: %s", model_name)
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
                "Erro ao carregar modelo NER: %s. "
                "Usando fallback para detecção de nomes.", e
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

        Estratégia de processamento:
        - Textos curtos (<= max_length): processa inteiro
        - Textos longos (> max_length): processa início + final
          para não perder nomes em assinaturas no fim do texto

        Filtra:
        - Nomes institucionais (Distrito Federal, etc.)
        - Nomes com menos de 2 palavras
        """
        results = []
        seen_names = set()  # Evitar duplicatas

        try:
            # Limite de caracteres (~375 tokens, conservador para 512 do modelo)
            max_length = 1500

            if len(text) <= max_length:
                # Texto curto: processa inteiro
                chunks = [text]
            elif len(text) <= max_length * 2:
                # Texto médio: evitar sobreposição processando metades
                mid = len(text) // 2
                chunks = [text[:mid], text[mid:]]
                logger.debug(
                    "Texto com %d chars processado em 2 chunks sem sobreposição",
                    len(text)
                )
            else:
                # Texto longo: processa início E final para não perder
                # nomes em assinaturas (comum em pedidos de informação)
                chunk_start = text[:max_length]
                chunk_end = text[-max_length:]
                chunks = [chunk_start, chunk_end]
                logger.debug(
                    "Texto com %d chars processado em 2 chunks "
                    "(início + final de %d chars cada)",
                    len(text), max_length
                )

            for chunk in chunks:
                entities = self.ner_pipeline(chunk)

                for ent in entities:
                    # Verificar se é entidade de pessoa
                    # Modelos diferentes podem usar labels diferentes
                    entity_group = ent.get('entity_group', ent.get('entity', ''))

                    if entity_group in ('PER', 'PESSOA', 'B-PER', 'I-PER', 'PERSON'):
                        name = ent.get('word', '').strip()
                        score = ent.get('score', 0.8)

                        # Validar nome e evitar duplicatas
                        if self._is_valid_person_name(name):
                            name_lower = name.lower()
                            if name_lower not in seen_names:
                                results.append(('nome', name, score))
                                seen_names.add(name_lower)

        except Exception as e:
            logger.warning("Erro no NER: %s. Usando fallback.", e)
            return self._detect_names_fallback(text)

        return results

    def _detect_names_fallback(self, text: str) -> List[Tuple[str, str, float]]:
        """
        Fallback CONSERVADOR para detecção de nomes sem NER.

        IMPORTANTE: Sem modelo NER, usamos apenas contextos EXPLÍCITOS
        para evitar falsos positivos. Preferimos perder alguns nomes
        (aumentar FN) do que detectar incorretamente (aumentar FP).

        Estratégia:
        - Detectar apenas nomes com contexto explícito forte
        - Não usar pattern matching genérico (causa muitos FP)
        """
        results = []
        seen_names = set()

        # Contextos FORTES que indicam nome de pessoa com alta confiança
        # Nota: grupos repetidos limitados a {1,5} para evitar backtracking exponencial (ReDoS)
        _nome_parte = r'[A-Z][a-záàâãéêíóôõúç]+'
        _nome_completo = _nome_parte + r'(?:\s+(?:de|da|do|das|dos|e)?\s*' + _nome_parte + r'){1,5}'

        strong_contexts = [
            # Nome explícito
            r'(?:meu\s+nome\s+(?:é|completo\s+é))[:\s]+(' + _nome_completo + r')',
            r'(?:nome)[:\s]+(' + _nome_completo + r')',
            r'(?:chamo-me|me\s+chamo)[:\s]+(' + _nome_completo + r')',
            # CPF junto com nome (indica pessoa física)
            r'(?:CPF[:\s]*[\d.-]+[,\s]+)(' + _nome_completo + r')',
            r'(' + _nome_completo + r')[,\s]+(?:CPF|portador)',
            # Identificação de cidadão
            r'(?:cidadão|cidadã|requerente|solicitante)[:\s]+(' + _nome_completo + r')',
            # Servidor/servidora
            r'(?:servidor(?:a)?|funcionário(?:a)?)[:\s]+(' + _nome_completo + r')',
        ]

        # Buscar nomes com contexto forte
        for pattern in strong_contexts:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                name = match.group(1).strip()
                # Limpar nome: remover palavras do início que não são nome
                name = self._clean_name(name)
                if name and self._is_valid_person_name(name):
                    if name.lower() not in seen_names:
                        results.append(('nome', name, 0.80))
                        seen_names.add(name.lower())

        return results

    def _clean_name(self, name: str) -> str:
        """
        Limpa um nome removendo prefixos e sufixos inválidos.
        """
        if not name:
            return ''

        # Remover prefixos comuns que não são parte do nome
        prefixos_invalidos = [
            'Dr', 'Dra', 'Sr', 'Sra', 'Prof', 'Profa',
        ]
        for prefixo in prefixos_invalidos:
            if name.startswith(prefixo + ' ') or name.startswith(prefixo + '. '):
                name = name[len(prefixo):].strip('. ')

        return name.strip()

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

    # Tipos de PII definidos no edital (item 2.2.I):
    # "nome, CPF, RG, telefone e endereço de e-mail"
    TIPOS_PII_REAIS = {'cpf', 'email', 'telefone', 'rg', 'nome'}

    # Sinais contextuais que indicam possível PII mas não são PII por si só
    TIPOS_CONTEXTUAIS = {'contexto_1pessoa', 'endereco', 'contato'}

    def _build_result(self, pii_found: List[Tuple[str, str, float]]) -> Dict[str, Any]:
        """
        Constrói o resultado final da detecção.

        IMPORTANTE: Apenas tipos de PII reais (cpf, email, telefone, rg, nome)
        determinam se contem_pii=True. Sinais contextuais são apenas metadata.

        Args:
            pii_found: Lista de PIIs encontrados

        Returns:
            Dicionário com resultado estruturado
        """
        if not pii_found:
            return self._empty_result()

        # Separar PII real de sinais contextuais
        pii_reais = [item for item in pii_found if item[0] in self.TIPOS_PII_REAIS]
        sinais_contextuais = [item for item in pii_found if item[0] in self.TIPOS_CONTEXTUAIS]

        # Só considera que contém PII se houver PII REAL
        if not pii_reais:
            return self._empty_result()

        # Extrair tipos únicos de PII real
        tipos = list(set(item[0] for item in pii_reais))

        # Maior confiança entre PIIs reais
        confianca = max(item[2] for item in pii_reais)

        return {
            'contem_pii': True,
            'tipos_detectados': tipos,
            'detalhes': pii_reais,
            'sinais_contextuais': sinais_contextuais,  # Metadata adicional
            'confianca': round(confianca, 2)
        }

    def _empty_result(self) -> Dict[str, Any]:
        """Retorna resultado vazio (sem PII)."""
        return {
            'contem_pii': False,
            'tipos_detectados': [],
            'detalhes': [],
            'sinais_contextuais': [],
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
