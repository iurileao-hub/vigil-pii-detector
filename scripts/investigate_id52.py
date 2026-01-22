#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para investigar por que o NER não detectou nomes no ID 52.

Analisa possíveis causas:
1. Truncamento do texto (limite de 512 tokens)
2. Formato dos nomes com títulos
3. Posição dos nomes no texto
4. Comportamento do modelo com diferentes partes do texto
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd


def investigate_id52():
    """Investiga a não-detecção de nomes no ID 52."""

    # Carregar amostra
    project_root = Path(__file__).parent.parent
    sample_path = project_root / "analise" / "AMOSTRA_e-SIC.xlsx"

    df = pd.read_excel(sample_path)
    row = df[df['ID'] == 52].iloc[0]
    text = str(row['Texto Mascarado'])

    print("=" * 70)
    print("INVESTIGAÇÃO: Por que o NER não detectou nomes no ID 52?")
    print("=" * 70)

    # 1. Análise do tamanho do texto
    print("\n1. ANÁLISE DO TAMANHO DO TEXTO")
    print("-" * 50)
    print(f"   Comprimento total: {len(text)} caracteres")
    print(f"   Palavras aproximadas: {len(text.split())}")

    # O modelo BERTimbau tem limite de 512 tokens
    # Em português, ~1 token = ~4-5 caracteres em média
    estimated_tokens = len(text) // 4
    print(f"   Tokens estimados: ~{estimated_tokens}")
    print(f"   Limite do modelo: 512 tokens")

    if estimated_tokens > 512:
        print(f"   ⚠️  TEXTO EXCEDE LIMITE! Será truncado em ~{512*4} caracteres")

    # 2. Onde estão os nomes?
    print("\n2. LOCALIZAÇÃO DOS NOMES NO TEXTO")
    print("-" * 50)

    names_to_find = [
        "Carolina Guimarães Neves",
        "Fátima Lima",
    ]

    for name in names_to_find:
        pos = text.find(name)
        if pos >= 0:
            pct = (pos / len(text)) * 100
            in_first_1500 = "SIM ✓" if pos < 1500 else "NÃO ✗"
            print(f"   '{name}':")
            print(f"      Posição: {pos} ({pct:.1f}% do texto)")
            print(f"      Dentro do limite de 1500 chars: {in_first_1500}")
        else:
            print(f"   '{name}': NÃO ENCONTRADO")

    # 3. Testar com modelo NER diretamente
    print("\n3. TESTE DIRETO COM MODELO NER")
    print("-" * 50)

    try:
        from transformers import pipeline

        print("   Carregando modelo NER...")
        ner = pipeline(
            "ner",
            model="pierreguillou/ner-bert-base-cased-pt-lenerbr",
            aggregation_strategy="simple"
        )

        # 3a. Texto completo truncado (como o detector faz)
        print("\n   3a. Texto completo (truncado em 1500 chars):")
        text_truncated = text[:1500]
        entities = ner(text_truncated)
        person_entities = [e for e in entities if e['entity_group'] in ('PER', 'PESSOA', 'PERSON')]

        if person_entities:
            for e in person_entities:
                print(f"       - {e['word']} (score: {e['score']:.3f})")
        else:
            print("       Nenhuma entidade PESSOA detectada!")

        # 3b. Apenas a parte final com os nomes
        print("\n   3b. Apenas a parte final (últimos 500 chars):")
        text_final = text[-500:]
        entities_final = ner(text_final)
        person_entities_final = [e for e in entities_final if e['entity_group'] in ('PER', 'PESSOA', 'PERSON')]

        if person_entities_final:
            for e in person_entities_final:
                print(f"       - {e['word']} (score: {e['score']:.3f})")
        else:
            print("       Nenhuma entidade PESSOA detectada!")

        # 3c. Apenas os nomes isolados
        print("\n   3c. Nomes isolados com contexto mínimo:")
        test_texts = [
            "Carolina Guimarães Neves",
            "Profª. Doutorª. Fátima Lima",
            "Orientador: Profª. Doutorª. Fátima Lima",
            "Cordialmente, Carolina Guimarães Neves",
            "Pesquisadora do Instituto: Carolina Guimarães Neves",
        ]

        for test_text in test_texts:
            entities_test = ner(test_text)
            person_test = [e for e in entities_test if e['entity_group'] in ('PER', 'PESSOA', 'PERSON')]
            if person_test:
                names = ", ".join([f"{e['word']} ({e['score']:.2f})" for e in person_test])
                print(f"       '{test_text[:50]}...' → {names}")
            else:
                print(f"       '{test_text[:50]}...' → NENHUM")

        # 3d. Contexto exato do texto original
        print("\n   3d. Contexto exato do texto original:")
        # Encontrar a parte com a assinatura
        signature_start = text.find("Cordialmente,")
        if signature_start >= 0:
            signature_text = text[signature_start:]
            print(f"       Texto da assinatura ({len(signature_text)} chars):")
            print(f"       '{signature_text[:200]}...'")

            entities_sig = ner(signature_text)
            person_sig = [e for e in entities_sig if e['entity_group'] in ('PER', 'PESSOA', 'PERSON')]
            if person_sig:
                for e in person_sig:
                    print(f"       DETECTADO: {e['word']} (score: {e['score']:.3f})")
            else:
                print("       ⚠️  NENHUMA PESSOA DETECTADA NA ASSINATURA!")

    except Exception as e:
        print(f"   Erro ao carregar modelo NER: {e}")
        print("   Instale transformers: pip install transformers torch")

    # 4. Conclusões
    print("\n" + "=" * 70)
    print("4. CONCLUSÕES PRELIMINARES")
    print("=" * 70)

    print("""
   Possíveis causas da não-detecção:

   A) TRUNCAMENTO: O detector limita o texto a 1500 caracteres.
      Os nomes estão na posição ~1450-1600, podendo ser truncados.

   B) FORMATO DOS TÍTULOS: "Profª. Doutorª." pode confundir o modelo,
      já que são abreviações não convencionais.

   C) ESTRUTURA DA ASSINATURA: O formato "Nome: Cargo. Descrição."
      pode não ser reconhecido como padrão de nome de pessoa.

   D) CONTEXTO DO MODELO: O modelo LeNER-BR foi treinado em textos
      jurídicos, que podem ter padrões diferentes de contexto acadêmico.

   RECOMENDAÇÃO: Aumentar o limite de truncamento ou processar o
   texto em chunks para não perder informação do final.
    """)

    return 0


if __name__ == "__main__":
    sys.exit(investigate_id52())
