#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para testar o sistema de revisão humana na amostra.

Executa a detecção e análise de revisão humana,
mostrando quais casos seriam marcados para revisão.
"""

import sys
import os
from pathlib import Path

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
from src import PIIDetector
from src.human_review import (
    HumanReviewAnalyzer,
    HumanReviewConfig,
    export_review_items,
    ReviewPriority,
)


def main():
    """Executa teste de revisão humana na amostra."""

    # Configurar caminhos
    project_root = Path(__file__).parent.parent
    sample_path = project_root / "analise" / "AMOSTRA_e-SIC.xlsx"
    output_path = project_root / "analise" / "revisao_humana.csv"

    if not sample_path.exists():
        print(f"Erro: Arquivo não encontrado: {sample_path}")
        return 1

    print("=" * 60)
    print("TESTE DO SISTEMA DE REVISÃO HUMANA")
    print("=" * 60)

    # Carregar amostra
    print(f"\nCarregando amostra: {sample_path}")
    df = pd.read_excel(sample_path)
    print(f"Total de registros: {len(df)}")

    # Inicializar detector e analisador
    print("\nInicializando detector de PII...")
    detector = PIIDetector(use_ner=True)
    print(f"NER disponível: {detector.ner_available}")

    # Configurar thresholds para teste
    config = HumanReviewConfig(
        high_confidence_threshold=0.95,
        medium_confidence_threshold=0.80,
        low_confidence_threshold=0.80,
        context_window=100,
        check_artistic_context=True,
        check_academic_context=True,
    )

    print(f"\nConfigurações de threshold:")
    print(f"  - Alta confiança: >= {config.high_confidence_threshold}")
    print(f"  - Média confiança: >= {config.medium_confidence_threshold}")
    print(f"  - Baixa confiança: < {config.low_confidence_threshold}")

    analyzer = HumanReviewAnalyzer(config)

    # Processar amostra
    print("\nProcessando registros...")
    all_review_items = []
    detections_with_pii = 0
    detections_for_review = 0

    for idx, row in df.iterrows():
        record_id = str(row.get('ID', idx + 1))
        text = str(row.get('Texto Mascarado', ''))

        if not text.strip():
            continue

        # Detectar PII
        result = detector.detect(text)

        if result['contem_pii']:
            detections_with_pii += 1

            # Analisar para revisão
            review_items = analyzer.analyze(record_id, text, result)

            if review_items:
                detections_for_review += 1
                all_review_items.extend(review_items)

    # Resultados
    print("\n" + "=" * 60)
    print("RESULTADOS")
    print("=" * 60)

    print(f"\nDetecções com PII: {detections_with_pii}")
    print(f"Detecções marcadas para revisão: {detections_for_review}")
    print(f"Total de itens de revisão: {len(all_review_items)}")

    # Estatísticas por prioridade
    priority_counts = {p: 0 for p in ReviewPriority}
    for item in all_review_items:
        priority_counts[item.prioridade] += 1

    print("\nItens por prioridade:")
    for priority, count in priority_counts.items():
        print(f"  - {priority.value.upper()}: {count}")

    # Estatísticas por motivo
    reason_counts = {}
    for item in all_review_items:
        reason = item.motivo.value
        reason_counts[reason] = reason_counts.get(reason, 0) + 1

    print("\nItens por motivo:")
    for reason, count in sorted(reason_counts.items(), key=lambda x: -x[1]):
        print(f"  - {reason}: {count}")

    # Listar casos de ALTA prioridade
    high_priority = [i for i in all_review_items if i.prioridade == ReviewPriority.HIGH]

    if high_priority:
        print("\n" + "-" * 60)
        print("CASOS DE ALTA PRIORIDADE (requerem revisão)")
        print("-" * 60)

        for item in high_priority:
            print(f"\n[ID {item.id}] {item.tipo_pii.upper()}: {item.valor_detectado}")
            print(f"  Score: {item.score:.2f}")
            print(f"  Motivo: {item.motivo.value}")
            print(f"  Explicação: {item.contexto_adicional}")
            # Mostrar trecho limitado
            trecho = item.texto_trecho[:150] + "..." if len(item.texto_trecho) > 150 else item.texto_trecho
            print(f"  Trecho: {trecho}")

    # Exportar arquivo de revisão
    if all_review_items:
        print(f"\nExportando arquivo de revisão: {output_path}")
        export_review_items(all_review_items, str(output_path), format='csv')
        print(f"Arquivo criado com sucesso!")

    print("\n" + "=" * 60)
    print("CONCLUSÃO")
    print("=" * 60)

    if high_priority:
        print(f"\n⚠️  {len(high_priority)} itens requerem revisão humana prioritária.")
        print("   Verifique o arquivo revisao_humana.csv para detalhes.")
    else:
        print("\n✓ Nenhum item de alta prioridade para revisão.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
