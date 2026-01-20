#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de avaliação de métricas do detector de PII.

Calcula métricas de desempenho comparando predições com gabarito:
- Precisão (Precision)
- Recall (Sensibilidade)
- F1-Score
- Matriz de confusão

Uso:
    python scripts/evaluate.py --predictions resultado.csv --ground-truth gabarito.csv

Formato esperado dos arquivos:
- predictions: CSV com coluna 'contem_pii' (True/False ou 1/0)
- ground-truth: CSV com coluna 'contem_pii' (True/False ou 1/0)

Nota: Ambos os arquivos devem ter uma coluna de ID para fazer o join.
"""

import argparse
import sys
from pathlib import Path

import pandas as pd


def load_csv(filepath: str) -> pd.DataFrame:
    """
    Carrega arquivo CSV.

    Args:
        filepath: Caminho do arquivo

    Returns:
        DataFrame carregado
    """
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {filepath}")

    try:
        return pd.read_csv(filepath)
    except Exception as e:
        raise ValueError(f"Erro ao ler {filepath}: {e}")


def normalize_boolean(df: pd.DataFrame, column: str) -> pd.Series:
    """
    Normaliza coluna para valores booleanos.

    Aceita: True/False, 1/0, 'true'/'false', 'sim'/'não', etc.

    Args:
        df: DataFrame
        column: Nome da coluna

    Returns:
        Series com valores booleanos
    """
    values = df[column].astype(str).str.lower().str.strip()

    # Mapear para booleano
    true_values = ['true', '1', '1.0', 'sim', 'yes', 's', 'y', 'verdadeiro']
    return values.isin(true_values)


def calculate_metrics(y_true: pd.Series, y_pred: pd.Series) -> dict:
    """
    Calcula métricas de classificação.

    Args:
        y_true: Valores verdadeiros (ground truth)
        y_pred: Valores preditos

    Returns:
        Dicionário com métricas
    """
    # Matriz de confusão
    tp = ((y_true == True) & (y_pred == True)).sum()   # Verdadeiro Positivo
    tn = ((y_true == False) & (y_pred == False)).sum() # Verdadeiro Negativo
    fp = ((y_true == False) & (y_pred == True)).sum()  # Falso Positivo
    fn = ((y_true == True) & (y_pred == False)).sum()  # Falso Negativo

    # Métricas
    total = len(y_true)
    accuracy = (tp + tn) / total if total > 0 else 0
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0

    return {
        'total': total,
        'tp': tp,
        'tn': tn,
        'fp': fp,
        'fn': fn,
        'accuracy': accuracy,
        'precision': precision,
        'recall': recall,
        'f1': f1,
    }


def print_report(metrics: dict):
    """
    Imprime relatório de métricas formatado.

    Args:
        metrics: Dicionário com métricas calculadas
    """
    print("\n" + "=" * 60)
    print("RELATÓRIO DE AVALIAÇÃO DO DETECTOR DE PII")
    print("=" * 60)

    print("\n📊 MATRIZ DE CONFUSÃO:")
    print("-" * 40)
    print(f"                    Predito")
    print(f"                 SEM PII  COM PII")
    print(f"Real SEM PII      {metrics['tn']:5d}    {metrics['fp']:5d}")
    print(f"Real COM PII      {metrics['fn']:5d}    {metrics['tp']:5d}")

    print("\n📈 MÉTRICAS:")
    print("-" * 40)
    print(f"Total de registros:     {metrics['total']}")
    print(f"Verdadeiros Positivos:  {metrics['tp']}")
    print(f"Verdadeiros Negativos:  {metrics['tn']}")
    print(f"Falsos Positivos:       {metrics['fp']}")
    print(f"Falsos Negativos:       {metrics['fn']} {'⚠️ CRÍTICO' if metrics['fn'] > 0 else '✅'}")

    print("\n🎯 SCORES:")
    print("-" * 40)
    print(f"Acurácia:    {metrics['accuracy']:.4f} ({metrics['accuracy']*100:.2f}%)")
    print(f"Precisão:    {metrics['precision']:.4f} ({metrics['precision']*100:.2f}%)")
    print(f"Recall:      {metrics['recall']:.4f} ({metrics['recall']*100:.2f}%)")
    print(f"F1-Score:    {metrics['f1']:.4f} ({metrics['f1']*100:.2f}%)")

    print("\n" + "=" * 60)
    print("⚠️  Critério de desempate: Menor FN > Menor FP > Maior F1")
    print("=" * 60 + "\n")


def analyze_errors(df_pred: pd.DataFrame, df_truth: pd.DataFrame,
                   id_column: str, pred_column: str, truth_column: str):
    """
    Analisa e lista erros (FP e FN).

    Args:
        df_pred: DataFrame com predições
        df_truth: DataFrame com ground truth
        id_column: Coluna de ID
        pred_column: Coluna de predição
        truth_column: Coluna de verdade
    """
    # Merge dos dataframes
    df = df_pred[[id_column, pred_column]].merge(
        df_truth[[id_column, truth_column]],
        on=id_column
    )

    y_pred = normalize_boolean(df, pred_column)
    y_true = normalize_boolean(df, truth_column)

    # Falsos Negativos
    fn_mask = (y_true == True) & (y_pred == False)
    fn_ids = df.loc[fn_mask, id_column].tolist()

    # Falsos Positivos
    fp_mask = (y_true == False) & (y_pred == True)
    fp_ids = df.loc[fp_mask, id_column].tolist()

    if fn_ids:
        print("\n❌ FALSOS NEGATIVOS (PII não detectado):")
        print("-" * 40)
        for id_val in fn_ids[:10]:  # Limitar a 10
            print(f"  - ID: {id_val}")
        if len(fn_ids) > 10:
            print(f"  ... e mais {len(fn_ids) - 10} registros")

    if fp_ids:
        print("\n⚠️ FALSOS POSITIVOS (PII incorretamente detectado):")
        print("-" * 40)
        for id_val in fp_ids[:10]:  # Limitar a 10
            print(f"  - ID: {id_val}")
        if len(fp_ids) > 10:
            print(f"  ... e mais {len(fp_ids) - 10} registros")


def main():
    """Função principal."""
    parser = argparse.ArgumentParser(
        description='Avalia métricas do detector de PII',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplo:
    python scripts/evaluate.py --predictions resultado.csv --ground-truth gabarito.csv
        """
    )

    parser.add_argument(
        '--predictions', '-p',
        required=True,
        help='Arquivo CSV com predições'
    )

    parser.add_argument(
        '--ground-truth', '-g',
        required=True,
        help='Arquivo CSV com gabarito (ground truth)'
    )

    parser.add_argument(
        '--id-column',
        default='ID',
        help='Nome da coluna de ID (padrão: "ID")'
    )

    parser.add_argument(
        '--pred-column',
        default='contem_pii',
        help='Nome da coluna de predição (padrão: "contem_pii")'
    )

    parser.add_argument(
        '--truth-column',
        default='contem_pii',
        help='Nome da coluna de verdade (padrão: "contem_pii")'
    )

    parser.add_argument(
        '--show-errors',
        action='store_true',
        help='Mostra IDs dos erros (FP e FN)'
    )

    args = parser.parse_args()

    try:
        # Carregar dados
        print(f"Carregando predições de: {args.predictions}")
        df_pred = load_csv(args.predictions)

        print(f"Carregando gabarito de: {args.ground_truth}")
        df_truth = load_csv(args.ground_truth)

        # Verificar colunas
        if args.id_column not in df_pred.columns:
            raise ValueError(f"Coluna '{args.id_column}' não encontrada em predições")
        if args.pred_column not in df_pred.columns:
            raise ValueError(f"Coluna '{args.pred_column}' não encontrada em predições")
        if args.id_column not in df_truth.columns:
            raise ValueError(f"Coluna '{args.id_column}' não encontrada em gabarito")
        if args.truth_column not in df_truth.columns:
            raise ValueError(f"Coluna '{args.truth_column}' não encontrada em gabarito")

        # Merge
        df = df_pred[[args.id_column, args.pred_column]].merge(
            df_truth[[args.id_column, args.truth_column]],
            on=args.id_column
        )

        if len(df) == 0:
            raise ValueError("Nenhum registro encontrado após merge. Verifique a coluna de ID.")

        print(f"Registros para avaliação: {len(df)}")

        # Normalizar valores
        y_pred = normalize_boolean(df, args.pred_column)
        y_true = normalize_boolean(df, args.truth_column)

        # Calcular métricas
        metrics = calculate_metrics(y_true, y_pred)

        # Imprimir relatório
        print_report(metrics)

        # Mostrar erros se solicitado
        if args.show_errors:
            analyze_errors(df_pred, df_truth, args.id_column,
                          args.pred_column, args.truth_column)

        return 0

    except FileNotFoundError as e:
        print(f"Erro: {e}", file=sys.stderr)
        return 1
    except ValueError as e:
        print(f"Erro: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Erro inesperado: {e}", file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
