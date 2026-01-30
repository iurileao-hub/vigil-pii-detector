#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de análise de erros do detector de PII.

Analisa falsos negativos (FN) e falsos positivos (FP) para:
- Identificar padrões de erro
- Sugerir melhorias nos padrões regex
- Ajustar thresholds de detecção

Uso:
    python scripts/analyze_errors.py --predictions resultado.csv --ground-truth gabarito.csv
    python scripts/analyze_errors.py --predictions resultado.csv --sample AMOSTRA_e-SIC.xlsx

Se não houver gabarito, analisa apenas os resultados da detecção.
"""

import argparse
import sys
from pathlib import Path

import pandas as pd

# Permitir importar src/ quando executado como script
sys.path.insert(0, str(Path(__file__).parent.parent))
from src.utils import normalize_boolean as _normalize_boolean_series


def load_file(filepath: str) -> pd.DataFrame:
    """Carrega arquivo CSV ou XLSX."""
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {filepath}")

    if path.suffix.lower() == '.xlsx':
        return pd.read_excel(filepath)
    else:
        try:
            return pd.read_csv(filepath, encoding='utf-8')
        except UnicodeDecodeError:
            return pd.read_csv(filepath, encoding='latin-1')


def analyze_predictions(df: pd.DataFrame, text_column: str = 'Texto Mascarado'):
    """
    Analisa predições sem gabarito.

    Mostra estatísticas e exemplos de cada tipo de detecção.
    """
    print("\n" + "=" * 70)
    print("ANÁLISE DE PREDIÇÕES (SEM GABARITO)")
    print("=" * 70)

    total = len(df)
    with_pii = df['contem_pii'].sum() if 'contem_pii' in df.columns else 0

    print(f"\nTotal de registros: {total}")
    print(f"Com PII detectado:  {with_pii} ({100*with_pii/total:.1f}%)")
    print(f"Sem PII detectado:  {total - with_pii} ({100*(total-with_pii)/total:.1f}%)")

    # Análise por tipo
    if 'tipos_detectados' in df.columns:
        print("\n" + "-" * 50)
        print("DISTRIBUIÇÃO POR TIPO DE PII:")
        print("-" * 50)

        from collections import Counter
        all_tipos = []
        for t in df['tipos_detectados'].dropna():
            if t:
                all_tipos.extend([x.strip() for x in str(t).split(',')])

        for tipo, count in Counter(all_tipos).most_common():
            pct = 100 * count / total
            bar = '█' * int(pct / 2)
            print(f"  {tipo:20s}: {count:4d} ({pct:5.1f}%) {bar}")

    # Exemplos de detecções
    if text_column in df.columns and 'tipos_detectados' in df.columns:
        print("\n" + "-" * 50)
        print("EXEMPLOS DE DETECÇÕES:")
        print("-" * 50)

        tipos_unicos = set()
        for t in df['tipos_detectados'].dropna():
            if t:
                tipos_unicos.update([x.strip() for x in str(t).split(',')])

        for tipo in sorted(tipos_unicos):
            mask = df['tipos_detectados'].astype(str).str.contains(tipo, na=False)
            exemplos = df[mask].head(2)

            print(f"\n  [{tipo.upper()}]")
            for _, row in exemplos.iterrows():
                texto = str(row[text_column])[:100]
                print(f"    ID {row.get('ID', '?')}: {texto}...")

    # Análise de confiança
    if 'confianca' in df.columns:
        print("\n" + "-" * 50)
        print("DISTRIBUIÇÃO DE CONFIANÇA:")
        print("-" * 50)

        conf_pii = df[df['contem_pii'] == True]['confianca']
        if len(conf_pii) > 0:
            print(f"  Mínima:  {conf_pii.min():.2f}")
            print(f"  Média:   {conf_pii.mean():.2f}")
            print(f"  Máxima:  {conf_pii.max():.2f}")

            # Histograma simples
            bins = [0, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
            print("\n  Histograma:")
            for i in range(len(bins) - 1):
                count = ((conf_pii >= bins[i]) & (conf_pii < bins[i+1])).sum()
                bar = '█' * (count // 2)
                print(f"    {bins[i]:.1f}-{bins[i+1]:.1f}: {count:4d} {bar}")


def analyze_errors_with_truth(df_pred: pd.DataFrame, df_truth: pd.DataFrame,
                               id_column: str = 'ID',
                               text_column: str = 'Texto Mascarado'):
    """
    Analisa erros comparando predições com gabarito.

    Identifica FN e FP com exemplos e contexto.
    """
    print("\n" + "=" * 70)
    print("ANÁLISE DE ERROS (COM GABARITO)")
    print("=" * 70)

    # Normalizar colunas de predição
    pred_col = 'contem_pii'
    truth_col = 'contem_pii' if 'contem_pii' in df_truth.columns else 'tem_pii'

    # Merge
    df = df_pred.merge(
        df_truth[[id_column, truth_col]],
        on=id_column,
        suffixes=('_pred', '_true')
    )

    # Normalizar para booleano
    def to_bool(series):
        return _normalize_boolean_series(series)

    y_pred = to_bool(df[f'{pred_col}_pred']) if f'{pred_col}_pred' in df.columns else to_bool(df[pred_col])
    y_true = to_bool(df[truth_col]) if truth_col in df.columns else to_bool(df[f'{truth_col}_true'])

    # Calcular erros
    fn_mask = (y_true == True) & (y_pred == False)
    fp_mask = (y_true == False) & (y_pred == True)
    tp_mask = (y_true == True) & (y_pred == True)
    tn_mask = (y_true == False) & (y_pred == False)

    fn_count = fn_mask.sum()
    fp_count = fp_mask.sum()
    tp_count = tp_mask.sum()
    tn_count = tn_mask.sum()

    print(f"\n📊 Resumo:")
    print(f"  Verdadeiros Positivos (TP): {tp_count}")
    print(f"  Verdadeiros Negativos (TN): {tn_count}")
    print(f"  Falsos Positivos (FP):      {fp_count}")
    print(f"  Falsos Negativos (FN):      {fn_count} {'⚠️ CRÍTICO' if fn_count > 0 else '✅'}")

    # Análise de Falsos Negativos
    if fn_count > 0:
        print("\n" + "-" * 50)
        print(f"❌ FALSOS NEGATIVOS ({fn_count} registros)")
        print("   PII existe mas NÃO foi detectado - CRÍTICO!")
        print("-" * 50)

        fn_df = df[fn_mask]
        for _, row in fn_df.iterrows():
            print(f"\n  ID: {row[id_column]}")
            if text_column in df_pred.columns:
                texto_orig = df_pred[df_pred[id_column] == row[id_column]][text_column].values
                if len(texto_orig) > 0:
                    print(f"  Texto: {str(texto_orig[0])[:200]}...")
            print("  → Ação: Verificar por que PII não foi detectado")

    # Análise de Falsos Positivos
    if fp_count > 0:
        print("\n" + "-" * 50)
        print(f"⚠️ FALSOS POSITIVOS ({fp_count} registros)")
        print("   PII detectado mas NÃO existe")
        print("-" * 50)

        fp_df = df[fp_mask]
        for _, row in fp_df.head(10).iterrows():
            tipos = row.get('tipos_detectados', '')
            print(f"\n  ID: {row[id_column]}")
            print(f"  Tipos detectados: {tipos}")
            if text_column in df_pred.columns:
                texto_orig = df_pred[df_pred[id_column] == row[id_column]][text_column].values
                if len(texto_orig) > 0:
                    print(f"  Texto: {str(texto_orig[0])[:150]}...")

        if fp_count > 10:
            print(f"\n  ... e mais {fp_count - 10} registros")

    # Sugestões de melhoria
    print("\n" + "-" * 50)
    print("💡 SUGESTÕES DE MELHORIA:")
    print("-" * 50)

    if fn_count > 0:
        print("\n  Para reduzir FN:")
        print("    - Verificar padrões regex não cobertos")
        print("    - Adicionar mais sinais contextuais")
        print("    - Reduzir threshold de confiança")

    if fp_count > 0:
        print("\n  Para reduzir FP:")
        print("    - Expandir lista de exclusões (nomes institucionais)")
        print("    - Adicionar mais filtros anti-FP")
        print("    - Verificar se modelo NER está disponível")


def main():
    """Função principal."""
    parser = argparse.ArgumentParser(
        description='Analisa erros do detector de PII',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        '--predictions', '-p',
        required=True,
        help='Arquivo CSV com predições'
    )

    parser.add_argument(
        '--ground-truth', '-g',
        help='Arquivo CSV com gabarito (opcional)'
    )

    parser.add_argument(
        '--sample', '-s',
        help='Arquivo com dados originais (para mostrar texto)'
    )

    parser.add_argument(
        '--id-column',
        default='ID',
        help='Nome da coluna de ID'
    )

    parser.add_argument(
        '--text-column',
        default='Texto Mascarado',
        help='Nome da coluna de texto'
    )

    args = parser.parse_args()

    try:
        # Carregar predições
        print(f"Carregando predições de: {args.predictions}")
        df_pred = load_file(args.predictions)

        # Se tiver arquivo de amostra, fazer merge para ter o texto
        if args.sample:
            print(f"Carregando dados originais de: {args.sample}")
            df_sample = load_file(args.sample)
            if args.text_column in df_sample.columns and args.text_column not in df_pred.columns:
                df_pred = df_pred.merge(
                    df_sample[[args.id_column, args.text_column]],
                    on=args.id_column,
                    how='left'
                )

        # Análise com ou sem gabarito
        if args.ground_truth:
            print(f"Carregando gabarito de: {args.ground_truth}")
            df_truth = load_file(args.ground_truth)
            analyze_errors_with_truth(df_pred, df_truth, args.id_column, args.text_column)
        else:
            analyze_predictions(df_pred, args.text_column)

        return 0

    except Exception as e:
        print(f"Erro: {e}", file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
