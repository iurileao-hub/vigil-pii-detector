# -*- coding: utf-8 -*-
"""
Sistema de Revisão Humana para casos incertos.

Identifica detecções que merecem revisão manual baseado em:
1. Score de confiança baixo do modelo NER
2. Contextos suspeitos que podem gerar falsos positivos

Estratégia: Mesmo priorizando recall, é útil sinalizar casos
duvidosos para revisão humana posterior sem rejeitar a detecção.
"""

import re
import csv
import json
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class ReviewPriority(Enum):
    """Prioridade de revisão humana."""
    HIGH = "alta"      # Revisar com urgência
    MEDIUM = "media"   # Revisar quando possível
    LOW = "baixa"      # Revisão opcional


class ReviewReason(Enum):
    """Motivo para revisão humana."""
    LOW_CONFIDENCE = "score_baixo"
    MEDIUM_CONFIDENCE = "score_medio"
    ARTISTIC_CONTEXT = "contexto_artistico"
    ACADEMIC_CONTEXT = "contexto_academico"
    JOURNALISTIC_CONTEXT = "contexto_jornalistico"
    PUBLIC_OFFICIAL_CONTEXT = "contexto_cargo_publico"
    LEGAL_CONTEXT = "contexto_juridico"
    AUTHORSHIP_CONTEXT = "contexto_autoria"
    SINGLE_NAME_ONLY = "nome_unico"
    INSTITUTIONAL_AMBIGUITY = "ambiguidade_institucional"


@dataclass
class ReviewItem:
    """Item marcado para revisão humana."""
    id: str
    texto_trecho: str
    tipo_pii: str
    valor_detectado: str
    score: float
    motivo: ReviewReason
    prioridade: ReviewPriority
    contexto_adicional: str = ""


@dataclass
class HumanReviewConfig:
    """Configuração dos thresholds de revisão.

    Attributes:
        high_confidence_threshold: Score acima do qual é alta confiança (default: 0.95)
        medium_confidence_threshold: Score acima do qual é média confiança (default: 0.80)
        low_confidence_threshold: Score abaixo do qual é baixa confiança (default: 0.80)
        context_window: Caracteres ao redor do PII para exibir contexto (default: 100)
        check_artistic_context: Verificar contextos de arte/patrimônio (default: True)
        check_academic_context: Verificar contextos acadêmicos (default: True)
    """
    high_confidence_threshold: float = 0.95
    medium_confidence_threshold: float = 0.80
    low_confidence_threshold: float = 0.80
    context_window: int = 100
    check_artistic_context: bool = True
    check_academic_context: bool = True


class HumanReviewAnalyzer:
    """
    Analisa detecções de PII e identifica casos para revisão humana.

    NÃO rejeita detecções — apenas marca para revisão posterior.
    Mantém estratégia recall-first do projeto.
    """

    # Padrões de contexto artístico/patrimônio (podem gerar FP com nomes de artistas)
    # NOTA: Padrões refinados para evitar falsos alertas com termos comuns
    ARTISTIC_PATTERNS = [
        # Vitrais e mosaicos são específicos o suficiente
        r'\b(vitral|vitrais|mosaico|mosaicos|escultura|esculturas|afresco|afrescos)\b',
        # "painel" apenas em contexto artístico (não "painel de controle/atenção")
        r'\b(painéis?)\s+(artístico|de\s+arte|decorativo|azulejo)',
        r'\bpainéis\s+(?:de\s+)?[A-Z][a-záàâãéêíóôõúç]+',  # "painéis Athos Bulcão"
        r'\b(obra|obras)\s+de\s+arte\b',
        r'\b(artista|artistas|pintor|pintores|escultor|escultores)\b',
        # Patrimônio em contexto cultural (não "patrimônio líquido")
        r'\bpatrimônio\s+(cultural|histórico|artístico|tombado)\b',
        r'\b(tombado|tombamento)\b',
        # Museu em contexto de arte (não museu de transportes, ciência, etc.)
        r'\bmuseu\s+(?:de\s+)?(?:arte|belas\s+artes)\b',
        r'\bgaleria\s+(?:de\s+)?arte\b',
        r'\b(lustre|lustres|luminária|luminárias)\s+(?:antiga|antigo|históric)',
    ]

    # Padrões de contexto acadêmico (nomes podem ser dados públicos)
    # NOTA: Padrões refinados para evitar órgãos públicos como "Instituto de Defesa"
    ACADEMIC_PATTERNS = [
        r'\b(pesquisador|pesquisadora|orientador|orientadora)\b',
        r'\b(prof\.|profa\.|professor|professora)\s+[A-Z]',  # Seguido de nome
        r'\bDr\.?\s+[A-Z]',  # Dr. seguido de nome
        r'\bDoutora?\.?\s+[A-Z]',  # Doutor(a) seguido de nome
        r'\b(mestrado|doutorado|tese|dissertação|pós-graduação)\b',
        # Universidade/Faculdade são específicos
        r'\buniversidade\s+(?:de|do|da|federal|estadual|católica)\b',
        r'\bfaculdade\s+(?:de|do|da)\b',
        # Instituto apenas em contexto acadêmico (não "Instituto de Defesa")
        r'\binstituto\s+(?:brasileiro\s+de\s+)?(?:ensino|pesquisa|educação)\b',
        r'\b(artigo|publicação|pesquisa)\s+(?:científica|acadêmica)\b',
        r'\bprojeto\s+(?:de\s+)?(?:pesquisa|tcc|final)\b',
    ]

    # Padrões de contexto jornalístico (exceção LGPD para fins jornalísticos)
    JOURNALISTIC_PATTERNS = [
        r'\b(segundo|conforme|de\s+acordo\s+com)\s+(?:a\s+)?(?:reportagem|matéria|notícia)\b',
        r'\b(publicado|publicada)\s+(?:no|na|em)\s+(?:jornal|revista|site)\b',
        r'\bfonte[:\s]+[A-Z]',  # "Fonte: Nome"
        r'\b(jornalista|repórter|colunista)\s+[A-Z]',
    ]

    # Padrões de contexto de cargo público (dados públicos por natureza)
    PUBLIC_OFFICIAL_PATTERNS = [
        r'\b(governador|governadora)\s+[A-Z]',
        r'\b(secretário|secretária)\s+(?:de\s+estado\s+)?[A-Z]',
        r'\b(ministro|ministra)\s+[A-Z]',
        r'\b(prefeito|prefeita)\s+[A-Z]',
        r'\b(deputado|deputada|senador|senadora)\s+[A-Z]',
        r'\b(presidente|vice-presidente)\s+[A-Z]',
        r'\bex-(?:governador|prefeito|ministro|presidente)\b',
    ]

    # Padrões de contexto jurídico (advogados, OAB)
    LEGAL_PATTERNS = [
        r'\bOAB[/\s]?[A-Z]{2}[:\s]*\d+',  # OAB/SP 12345
        r'\badvogado\s+[A-Z]',
        r'\badvogada\s+[A-Z]',
        r'\bprocurador\s+[A-Z]',
        r'\bdefensor\s+[A-Z]',
        r'\bjuiz\s+[A-Z]',
        r'\bjuíza\s+[A-Z]',
        r'\bdesembargador\s+[A-Z]',
    ]

    # Padrões de contexto de autoria (referências bibliográficas)
    AUTHORSHIP_PATTERNS = [
        r'\b(?:autor|autora|escrito\s+por)\s+[A-Z]',
        r'\bsegundo\s+[A-Z][a-záàâãéêíóôõúç]+\s+\(\d{4}\)',  # Segundo Silva (2020)
        r'\b[A-Z][A-Z]+,\s+[A-Z][a-z]+\.\s+\(\d{4}\)',  # SILVA, João. (2020)
        r'\bapud\s+[A-Z]',
        r'\bin:\s+[A-Z]',
    ]

    # Nomes de artistas famosos brasileiros (expandir conforme necessário)
    KNOWN_ARTISTS = [
        'athos bulcão', 'athos bulsão',  # Variações de grafia
        'burle marx', 'roberto burle marx',
        'oscar niemeyer',
        'cândido portinari', 'portinari',
        'di cavalcanti',
        'tarsila do amaral',
        'alfredo volpi',
        'marianne peretti',
        'gugon',  # Detectado no ID 15
    ]

    def __init__(self, config: Optional[HumanReviewConfig] = None):
        """
        Inicializa o analisador de revisão humana.

        Args:
            config: Configuração de thresholds. Se None, usa valores padrão.
        """
        self.config = config or HumanReviewConfig()

        # Compilar padrões regex
        self._artistic_regex = [
            re.compile(p, re.IGNORECASE) for p in self.ARTISTIC_PATTERNS
        ]
        self._academic_regex = [
            re.compile(p, re.IGNORECASE) for p in self.ACADEMIC_PATTERNS
        ]
        self._journalistic_regex = [
            re.compile(p, re.IGNORECASE) for p in self.JOURNALISTIC_PATTERNS
        ]
        self._public_official_regex = [
            re.compile(p, re.IGNORECASE) for p in self.PUBLIC_OFFICIAL_PATTERNS
        ]
        self._legal_regex = [
            re.compile(p, re.IGNORECASE) for p in self.LEGAL_PATTERNS
        ]
        self._authorship_regex = [
            re.compile(p, re.IGNORECASE) for p in self.AUTHORSHIP_PATTERNS
        ]

    def analyze(
        self,
        record_id: str,
        text: str,
        detection_result: Dict[str, Any]
    ) -> List[ReviewItem]:
        """
        Analisa uma detecção e retorna itens para revisão humana.

        Args:
            record_id: ID do registro
            text: Texto original analisado
            detection_result: Resultado do PIIDetector.detect()

        Returns:
            Lista de ReviewItems (pode ser vazia se não houver itens para revisão)
        """
        review_items = []

        if not detection_result.get('contem_pii'):
            return review_items

        detalhes = detection_result.get('detalhes', [])

        for tipo, valor, score in detalhes:
            reasons = self._check_review_reasons(tipo, valor, score, text)

            for reason, priority in reasons:
                # Extrair trecho do texto com contexto
                trecho = self._extract_context(text, valor)

                item = ReviewItem(
                    id=record_id,
                    texto_trecho=trecho,
                    tipo_pii=tipo,
                    valor_detectado=valor,
                    score=score,
                    motivo=reason,
                    prioridade=priority,
                    contexto_adicional=self._get_context_explanation(reason)
                )
                review_items.append(item)

        # Consolidar duplicatas antes de retornar
        return self._consolidate_items(review_items)

    def _consolidate_items(self, items: List[ReviewItem]) -> List[ReviewItem]:
        """
        Consolida itens duplicados em uma única entrada por (ID + nome).

        Mantém o contexto mais relevante de acordo com a prioridade:
        1. contexto_artistico (ALTA)
        2. contexto_academico (MÉDIA)
        3. contexto_juridico (MÉDIA)
        4. contexto_cargo_publico (BAIXA)
        5. score_medio (BAIXA)

        Args:
            items: Lista de ReviewItems (pode ter duplicatas)

        Returns:
            Lista consolidada de ReviewItems
        """
        if not items:
            return items

        # Ordem de prioridade dos motivos (menor = mais prioritário)
        reason_priority = {
            ReviewReason.ARTISTIC_CONTEXT: 1,
            ReviewReason.ACADEMIC_CONTEXT: 2,
            ReviewReason.LEGAL_CONTEXT: 3,
            ReviewReason.PUBLIC_OFFICIAL_CONTEXT: 4,
            ReviewReason.MEDIUM_CONFIDENCE: 5,
            ReviewReason.LOW_CONFIDENCE: 6,
            ReviewReason.JOURNALISTIC_CONTEXT: 7,
            ReviewReason.AUTHORSHIP_CONTEXT: 8,
            ReviewReason.SINGLE_NAME_ONLY: 9,
            ReviewReason.INSTITUTIONAL_AMBIGUITY: 10,
        }

        # Agrupar por (ID + valor_detectado)
        consolidated = {}
        for item in items:
            key = (item.id, item.valor_detectado.lower())

            if key not in consolidated:
                consolidated[key] = item
            else:
                # Manter o item com motivo mais prioritário
                existing_priority = reason_priority.get(consolidated[key].motivo, 99)
                new_priority = reason_priority.get(item.motivo, 99)

                if new_priority < existing_priority:
                    consolidated[key] = item

        return list(consolidated.values())

    def _check_review_reasons(
        self,
        tipo: str,
        valor: str,
        score: float,
        text: str
    ) -> List[tuple]:
        """
        Verifica motivos para revisão humana.

        Returns:
            Lista de tuplas (ReviewReason, ReviewPriority)
        """
        reasons = []

        # 1. Verificar score de confiança
        if score < self.config.low_confidence_threshold:
            reasons.append((ReviewReason.LOW_CONFIDENCE, ReviewPriority.HIGH))
        elif score < self.config.high_confidence_threshold:
            reasons.append((ReviewReason.MEDIUM_CONFIDENCE, ReviewPriority.LOW))

        # 2. Verificar contextos suspeitos (apenas para nomes)
        if tipo == 'nome':
            # Contexto artístico/patrimônio (ALTA prioridade - comum FP)
            if self.config.check_artistic_context:
                if self._has_artistic_context(text):
                    reasons.append((ReviewReason.ARTISTIC_CONTEXT, ReviewPriority.HIGH))

                # Verificar se é nome de artista conhecido
                if self._is_known_artist(valor):
                    reasons.append((ReviewReason.ARTISTIC_CONTEXT, ReviewPriority.HIGH))

            # Contexto acadêmico (MÉDIA prioridade - exceção LGPD)
            if self.config.check_academic_context:
                if self._has_academic_context(text):
                    reasons.append((ReviewReason.ACADEMIC_CONTEXT, ReviewPriority.MEDIUM))

            # Contexto jornalístico (MÉDIA prioridade - exceção LGPD)
            if self._has_journalistic_context(text):
                reasons.append((ReviewReason.JOURNALISTIC_CONTEXT, ReviewPriority.MEDIUM))

            # Contexto de cargo público (BAIXA prioridade - dados públicos)
            if self._has_public_official_context(text):
                reasons.append((ReviewReason.PUBLIC_OFFICIAL_CONTEXT, ReviewPriority.LOW))

            # Contexto jurídico/OAB (BAIXA prioridade - dados profissionais)
            if self._has_legal_context(text):
                reasons.append((ReviewReason.LEGAL_CONTEXT, ReviewPriority.LOW))

            # Contexto de autoria (BAIXA prioridade - referência bibliográfica)
            if self._has_authorship_context(text):
                reasons.append((ReviewReason.AUTHORSHIP_CONTEXT, ReviewPriority.LOW))

        return reasons

    def _has_artistic_context(self, text: str) -> bool:
        """Verifica se o texto contém contexto artístico/patrimônio."""
        for pattern in self._artistic_regex:
            if pattern.search(text):
                return True
        return False

    def _has_academic_context(self, text: str) -> bool:
        """Verifica se o texto contém contexto acadêmico."""
        for pattern in self._academic_regex:
            if pattern.search(text):
                return True
        return False

    def _has_journalistic_context(self, text: str) -> bool:
        """Verifica se o texto contém contexto jornalístico."""
        for pattern in self._journalistic_regex:
            if pattern.search(text):
                return True
        return False

    def _has_public_official_context(self, text: str) -> bool:
        """Verifica se o texto contém contexto de cargo público."""
        for pattern in self._public_official_regex:
            if pattern.search(text):
                return True
        return False

    def _has_legal_context(self, text: str) -> bool:
        """Verifica se o texto contém contexto jurídico/OAB."""
        for pattern in self._legal_regex:
            if pattern.search(text):
                return True
        return False

    def _has_authorship_context(self, text: str) -> bool:
        """Verifica se o texto contém contexto de autoria/referência."""
        for pattern in self._authorship_regex:
            if pattern.search(text):
                return True
        return False

    def _is_known_artist(self, name: str) -> bool:
        """Verifica se o nome é de um artista conhecido."""
        name_lower = name.lower().strip()
        for artist in self.KNOWN_ARTISTS:
            if artist in name_lower or name_lower in artist:
                return True
        return False

    def _extract_context(self, text: str, value: str) -> str:
        """Extrai trecho do texto com contexto ao redor do valor detectado."""
        window = self.config.context_window

        # Encontrar posição do valor no texto
        pos = text.lower().find(value.lower())
        if pos == -1:
            # Valor não encontrado exatamente, retornar início do texto
            return text[:window * 2] + ('...' if len(text) > window * 2 else '')

        # Extrair contexto ao redor
        start = max(0, pos - window)
        end = min(len(text), pos + len(value) + window)

        trecho = text[start:end]

        # Adicionar reticências se truncado
        if start > 0:
            trecho = '...' + trecho
        if end < len(text):
            trecho = trecho + '...'

        return trecho

    def _get_context_explanation(self, reason: ReviewReason) -> str:
        """Retorna explicação do motivo de revisão."""
        explanations = {
            ReviewReason.LOW_CONFIDENCE: (
                "Score de confiança do modelo NER abaixo do threshold. "
                "Maior chance de falso positivo."
            ),
            ReviewReason.MEDIUM_CONFIDENCE: (
                "Score de confiança moderado. Provavelmente correto, "
                "mas vale verificar."
            ),
            ReviewReason.ARTISTIC_CONTEXT: (
                "Texto contém referências a arte/patrimônio. "
                "Nome pode ser de artista, não dado pessoal do solicitante."
            ),
            ReviewReason.ACADEMIC_CONTEXT: (
                "Texto contém contexto acadêmico. "
                "Nome pode ser dado manifestamente público (LGPD Art. 7º, § 4º)."
            ),
            ReviewReason.JOURNALISTIC_CONTEXT: (
                "Texto contém contexto jornalístico. "
                "LGPD não se aplica a fins jornalísticos (Art. 4º, II, a)."
            ),
            ReviewReason.PUBLIC_OFFICIAL_CONTEXT: (
                "Nome de autoridade/cargo público detectado. "
                "Dados de agentes públicos são públicos por natureza."
            ),
            ReviewReason.LEGAL_CONTEXT: (
                "Contexto jurídico detectado (OAB, advogado, juiz). "
                "Dados profissionais públicos, não dados pessoais sensíveis."
            ),
            ReviewReason.AUTHORSHIP_CONTEXT: (
                "Contexto de autoria/referência bibliográfica. "
                "Nome pode ser de autor citado, não do solicitante."
            ),
            ReviewReason.SINGLE_NAME_ONLY: (
                "Apenas primeiro nome detectado, sem sobrenome. "
                "Pode não permitir identificação direta."
            ),
            ReviewReason.INSTITUTIONAL_AMBIGUITY: (
                "Nome pode ser institucional ou de pessoa física. "
                "Requer análise do contexto."
            ),
        }
        return explanations.get(reason, "Verificação manual recomendada.")


def export_review_items(
    items: List[ReviewItem],
    output_path: str,
    output_format: str = 'csv'
) -> None:
    """
    Exporta itens de revisão para arquivo.

    Args:
        items: Lista de ReviewItems
        output_path: Caminho do arquivo de saída
        output_format: Formato de saída ('csv' ou 'json')
    """
    if not items:
        logger.info("Nenhum item para revisão humana.")
        return

    if output_format == 'csv':
        _export_csv(items, output_path)
    elif output_format == 'json':
        _export_json(items, output_path)
    else:
        raise ValueError(f"Formato não suportado: {output_format}")

    logger.info(f"Exportados {len(items)} itens para revisão em {output_path}")


def _export_csv(items: List[ReviewItem], output_path: str) -> None:
    """Exporta para CSV."""
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)

        # Header
        writer.writerow([
            'ID',
            'Prioridade',
            'Tipo PII',
            'Valor Detectado',
            'Score',
            'Motivo',
            'Texto (Trecho)',
            'Explicacao'
        ])

        # Ordenar por prioridade (alta primeiro)
        priority_order = {
            ReviewPriority.HIGH: 0,
            ReviewPriority.MEDIUM: 1,
            ReviewPriority.LOW: 2
        }
        items_sorted = sorted(items, key=lambda x: priority_order[x.prioridade])

        for item in items_sorted:
            writer.writerow([
                item.id,
                item.prioridade.value,
                item.tipo_pii,
                item.valor_detectado,
                f"{item.score:.2f}",
                item.motivo.value,
                item.texto_trecho.replace('\n', ' '),
                item.contexto_adicional
            ])


def _export_json(items: List[ReviewItem], output_path: str) -> None:
    """Exporta para JSON."""
    data = []
    for item in items:
        data.append({
            'id': item.id,
            'prioridade': item.prioridade.value,
            'tipo_pii': item.tipo_pii,
            'valor_detectado': item.valor_detectado,
            'score': item.score,
            'motivo': item.motivo.value,
            'texto_trecho': item.texto_trecho,
            'explicacao': item.contexto_adicional
        })

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# Função de conveniência para uso direto
def analyze_for_review(
    record_id: str,
    text: str,
    detection_result: Dict[str, Any],
    config: Optional[HumanReviewConfig] = None
) -> List[ReviewItem]:
    """
    Função de conveniência para analisar um registro.

    Args:
        record_id: ID do registro
        text: Texto original
        detection_result: Resultado do PIIDetector.detect()
        config: Configuração (opcional)

    Returns:
        Lista de itens para revisão humana
    """
    analyzer = HumanReviewAnalyzer(config)
    return analyzer.analyze(record_id, text, detection_result)
