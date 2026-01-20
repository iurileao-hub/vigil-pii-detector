#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Detector de Dados Pessoais em Pedidos de Acesso à Informação

1º Hackathon em Controle Social: Desafio Participa DF
Categoria: Acesso à Informação

Este script processa arquivos CSV ou XLSX contendo textos de pedidos
de acesso à informação e identifica aqueles que contêm dados pessoais
(PII - Personally Identifiable Information).

Tipos de PII detectados:
- CPF (formatado e numérico)
- Email
- Telefone (fixo e celular)
- RG
- Nomes completos de pessoas

Uso:
    python main.py --input pedidos.csv --output resultado.csv
    python main.py --input AMOSTRA_e-SIC.xlsx --output resultado.csv

Autor: Desenvolvido com auxílio de IA (Claude Code)
"""

import argparse
import sys
import logging
from pathlib import Path

import pandas as pd

from src.detector import PIIDetector


def setup_logging(verbose: bool = False):
    """
    Configura o sistema de logging.

    Args:
        verbose: Se True, mostra logs de DEBUG
    """
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )


def load_data(input_path: str, text_column: str) -> pd.DataFrame:
    """
    Carrega dados de arquivo CSV ou XLSX.

    Args:
        input_path: Caminho do arquivo de entrada
        text_column: Nome da coluna com o texto

    Returns:
        DataFrame com os dados carregados

    Raises:
        FileNotFoundError: Se o arquivo não existir
        ValueError: Se a coluna de texto não existir
    """
    path = Path(input_path)

    if not path.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {input_path}")

    # Carregar conforme extensão
    if path.suffix.lower() == '.xlsx':
        df = pd.read_excel(input_path)
    elif path.suffix.lower() == '.csv':
        # Tentar detectar encoding
        try:
            df = pd.read_csv(input_path, encoding='utf-8')
        except UnicodeDecodeError:
            df = pd.read_csv(input_path, encoding='latin-1')
    else:
        raise ValueError(f"Formato não suportado: {path.suffix}")

    # Verificar se a coluna existe
    if text_column not in df.columns:
        available = ', '.join(df.columns.tolist())
        raise ValueError(
            f"Coluna '{text_column}' não encontrada. "
            f"Colunas disponíveis: {available}"
        )

    logging.info(f"Carregados {len(df)} registros de {input_path}")
    return df


def process_data(df: pd.DataFrame, text_column: str, use_ner: bool = True) -> pd.DataFrame:
    """
    Processa os dados e detecta PII.

    Args:
        df: DataFrame com os dados
        text_column: Nome da coluna com o texto
        use_ner: Se True, usa modelo NER para detecção de nomes

    Returns:
        DataFrame com colunas adicionais de resultado
    """
    # Inicializar detector
    logging.info("Inicializando detector de PII...")
    detector = PIIDetector(use_ner=use_ner)

    if detector.ner_available:
        logging.info("Modelo NER carregado com sucesso")
    else:
        logging.warning("Modelo NER não disponível, usando fallback")

    # Processar textos
    texts = df[text_column].fillna('').astype(str).tolist()
    total = len(texts)

    logging.info(f"Processando {total} registros...")

    results = []
    for i, text in enumerate(texts, 1):
        if i % 20 == 0 or i == total:
            logging.info(f"Progresso: {i}/{total} ({100*i/total:.1f}%)")

        result = detector.detect(text)
        results.append(result)

    # Adicionar colunas ao DataFrame
    df = df.copy()
    df['contem_pii'] = [r['contem_pii'] for r in results]
    df['tipos_detectados'] = [', '.join(r['tipos_detectados']) for r in results]
    df['confianca'] = [r['confianca'] for r in results]

    # Estatísticas
    total_pii = df['contem_pii'].sum()
    logging.info(f"Detecção concluída: {total_pii}/{total} registros contêm PII ({100*total_pii/total:.1f}%)")

    return df


def save_results(df: pd.DataFrame, output_path: str):
    """
    Salva os resultados em arquivo CSV.

    Args:
        df: DataFrame com resultados
        output_path: Caminho do arquivo de saída
    """
    # Criar diretório se necessário
    output_dir = Path(output_path).parent
    if output_dir and not output_dir.exists():
        output_dir.mkdir(parents=True, exist_ok=True)

    # Salvar como CSV
    df.to_csv(output_path, index=False, encoding='utf-8')
    logging.info(f"Resultados salvos em: {output_path}")


def main():
    """
    Função principal do script.

    Processa argumentos de linha de comando e executa a detecção de PII.
    """
    parser = argparse.ArgumentParser(
        description='Detector de Dados Pessoais em Pedidos de Acesso à Informação',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  python main.py --input pedidos.csv --output resultado.csv
  python main.py --input AMOSTRA_e-SIC.xlsx --output resultado.csv
  python main.py --input dados.xlsx --output out.csv --text-column "Texto"

Tipos de PII detectados:
  - CPF (formatado e numérico)
  - Email
  - Telefone (fixo e celular)
  - RG
  - Nomes completos de pessoas
        """
    )

    parser.add_argument(
        '--input', '-i',
        required=True,
        help='Arquivo de entrada (CSV ou XLSX)'
    )

    parser.add_argument(
        '--output', '-o',
        required=True,
        help='Arquivo de saída (CSV)'
    )

    parser.add_argument(
        '--text-column', '-t',
        default='Texto Mascarado',
        help='Nome da coluna com o texto (padrão: "Texto Mascarado")'
    )

    parser.add_argument(
        '--no-ner',
        action='store_true',
        help='Desabilita modelo NER (mais rápido, menos preciso para nomes)'
    )

    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Mostra logs detalhados'
    )

    args = parser.parse_args()

    # Configurar logging
    setup_logging(args.verbose)

    try:
        # Carregar dados
        df = load_data(args.input, args.text_column)

        # Processar
        use_ner = not args.no_ner
        df_result = process_data(df, args.text_column, use_ner=use_ner)

        # Salvar resultados
        save_results(df_result, args.output)

        # Resumo final
        total = len(df_result)
        total_pii = df_result['contem_pii'].sum()
        print(f"\n{'='*50}")
        print(f"RESUMO DA DETECÇÃO")
        print(f"{'='*50}")
        print(f"Total de registros: {total}")
        print(f"Registros com PII:  {total_pii} ({100*total_pii/total:.1f}%)")
        print(f"Registros sem PII:  {total - total_pii} ({100*(total-total_pii)/total:.1f}%)")
        print(f"Arquivo de saída:   {args.output}")
        print(f"{'='*50}")

        return 0

    except FileNotFoundError as e:
        logging.error(str(e))
        return 1
    except ValueError as e:
        logging.error(str(e))
        return 1
    except Exception as e:
        logging.error(f"Erro inesperado: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
