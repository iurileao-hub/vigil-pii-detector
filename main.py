#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VIGIL — Detector de Dados Pessoais em Pedidos de Acesso à Informação

1º Hackathon em Controle Social: Desafio Participa DF
Categoria: Acesso à Informação

Este script processa arquivos CSV, XLSX ou JSON contendo textos de pedidos
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
import json
import sys
import logging
import traceback
from collections import Counter
from datetime import datetime
from pathlib import Path

import pandas as pd

from src.detector import PIIDetector
from src.human_review import HumanReviewAnalyzer, export_review_items
from src.constants import MAX_FILE_SIZE_BYTES, MAX_FILE_SIZE_MB, JSON_ARRAY_KEYS, MAX_JSON_RECORDS


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
    Carrega dados de arquivo CSV, XLSX ou JSON.

    Args:
        input_path: Caminho do arquivo de entrada
        text_column: Nome da coluna/campo com o texto

    Returns:
        DataFrame com os dados carregados

    Raises:
        FileNotFoundError: Se o arquivo não existir
        ValueError: Se a coluna de texto não existir

    Formatos JSON suportados:
        1. Array de objetos: [{"ID": 1, "Texto Mascarado": "..."}, ...]
        2. Objeto com array "registros": {"registros": [...]}
        3. Objeto com array "data": {"data": [...]}
    """
    path = Path(input_path)

    if not path.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {input_path}")

    file_size = path.stat().st_size
    if file_size > MAX_FILE_SIZE_BYTES:
        raise ValueError(
            f"Arquivo muito grande ({file_size / (1024*1024):.0f} MB). "
            f"Limite: {MAX_FILE_SIZE_MB} MB."
        )

    # Carregar conforme extensão
    if path.suffix.lower() == '.xlsx':
        df = pd.read_excel(input_path)
    elif path.suffix.lower() == '.csv':
        # Tentar detectar encoding
        try:
            df = pd.read_csv(input_path, encoding='utf-8')
        except UnicodeDecodeError:
            df = pd.read_csv(input_path, encoding='latin-1')
    elif path.suffix.lower() == '.json':
        with open(input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Validar estrutura JSON
        if isinstance(data, list):
            if len(data) > MAX_JSON_RECORDS:
                raise ValueError(
                    f"JSON contém {len(data)} registros. "
                    f"Limite: {MAX_JSON_RECORDS}."
                )
            df = pd.DataFrame(data)
        elif isinstance(data, dict):
            records = None
            for key in JSON_ARRAY_KEYS:
                if key in data:
                    records = data[key]
                    break
            if records is None:
                raise ValueError(
                    "JSON deve conter array de objetos ou chave "
                    "'registros', 'data' ou 'resultados'"
                )
            if not isinstance(records, list):
                raise ValueError(f"Chave '{key}' deve conter um array")
            if len(records) > MAX_JSON_RECORDS:
                raise ValueError(
                    f"JSON contém {len(records)} registros. "
                    f"Limite: {MAX_JSON_RECORDS}."
                )
            df = pd.DataFrame(records)
        else:
            raise ValueError("Formato JSON inválido")
    else:
        raise ValueError(f"Formato não suportado: {path.suffix}. Use CSV, XLSX ou JSON.")

    # Verificar se a coluna existe
    if text_column not in df.columns:
        logging.debug("Colunas disponíveis: %s", ', '.join(df.columns.tolist()))
        raise ValueError(
            f"Coluna '{text_column}' não encontrada no arquivo de entrada. "
            f"Verifique o nome da coluna com --text-column."
        )

    logging.info("Carregados %d registros de %s", len(df), input_path)
    return df


def process_data(df: pd.DataFrame, text_column: str, use_ner: bool = True) -> tuple:
    """
    Processa os dados e detecta PII.

    Args:
        df: DataFrame com os dados
        text_column: Nome da coluna com o texto
        use_ner: Se True, usa modelo NER para detecção de nomes

    Returns:
        Tupla com (DataFrame com resultados, lista de resultados detalhados)
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

    logging.info("Processando %d registros...", total)

    results = []
    for i, text in enumerate(texts, 1):
        if i % 20 == 0 or i == total:
            logging.info("Progresso: %d/%d (%.1f%%)", i, total, 100 * i / total)

        result = detector.detect(text)
        results.append(result)

    # Adicionar colunas ao DataFrame
    df = df.copy()
    df['contem_pii'] = [r['contem_pii'] for r in results]
    df['tipos_detectados'] = [', '.join(r['tipos_detectados']) for r in results]
    df['confianca'] = [r['confianca'] for r in results]

    # Estatísticas
    total_pii = df['contem_pii'].sum()
    pct_pii = 100 * total_pii / total if total > 0 else 0
    logging.info("Detecção concluída: %d/%d registros contêm PII (%.1f%%)", total_pii, total, pct_pii)

    return df, results


def save_results(df: pd.DataFrame, output_path: str, output_format: str = 'csv',
                 results: list = None, input_path: str = None, use_ner: bool = True):
    """
    Salva os resultados em arquivo CSV ou JSON.

    Args:
        df: DataFrame com resultados
        output_path: Caminho do arquivo de saída
        output_format: Formato de saída ('csv' ou 'json')
        results: Lista de resultados detalhados (necessário para JSON)
        input_path: Caminho do arquivo de entrada (para metadados JSON)
        use_ner: Se NER foi usado (para metadados JSON)
    """
    # Criar diretório se necessário
    output_dir = Path(output_path).parent
    if output_dir and not output_dir.exists():
        output_dir.mkdir(parents=True, exist_ok=True)

    if output_format == 'json':
        # Estrutura JSON completa
        total_pii = int(df['contem_pii'].sum())

        # Contagem por tipo
        tipos_count = Counter()
        if results:
            for r in results:
                tipos_count.update(r.get('tipos_detectados', []))

        # Construir resultados detalhados
        resultados_json = []
        for i, (_, row) in enumerate(df.iterrows()):
            registro = {
                'id': row.get('ID', i + 1),
                'texto': row.get('Texto Mascarado', ''),
                'contem_pii': bool(row['contem_pii']),
                'confianca': float(row['confianca']),
                'tipos_detectados': row['tipos_detectados'].split(', ') if row['tipos_detectados'] else []
            }

            # Adicionar detalhes se disponíveis
            # detalhes é uma lista de tuplas (tipo, valor, confianca)
            if results and i < len(results):
                detalhes = []
                for det in results[i].get('detalhes', []):
                    # det é uma tupla (tipo, valor, confianca)
                    if isinstance(det, tuple) and len(det) >= 3:
                        detalhes.append({
                            'tipo': det[0],
                            'valor_detectado': det[1],
                            'score': float(det[2]),
                            'metodo': 'ner' if det[0] == 'nome' else 'regex'
                        })
                registro['detalhes'] = detalhes

            resultados_json.append(registro)

        # Estrutura final
        output_data = {
            'metadata': {
                'versao': '1.0.0',
                'timestamp': datetime.now().isoformat(),
                'arquivo_entrada': input_path or 'desconhecido',
                'total_registros': len(df),
                'total_com_pii': total_pii,
                'configuracao': {
                    'ner_habilitado': use_ner,
                    'modelo_ner': 'pierreguillou/ner-bert-base-cased-pt-lenerbr' if use_ner else None
                }
            },
            'resultados': resultados_json,
            'estatisticas': {
                'por_tipo': tipos_count,
                'percentual_com_pii': round(100 * total_pii / len(df), 1) if len(df) > 0 else 0
            }
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)

        logging.info("Resultados salvos em JSON: %s", output_path)
    else:
        # CSV padrão
        df.to_csv(output_path, index=False, encoding='utf-8')
        logging.info("Resultados salvos em CSV: %s", output_path)


def generate_human_review(df: pd.DataFrame, results: list, text_column: str,
                          output_path: str) -> int:
    """
    Gera arquivo de revisão humana para casos duvidosos.

    Args:
        df: DataFrame original com os dados
        results: Lista de resultados detalhados da detecção
        text_column: Nome da coluna com o texto
        output_path: Caminho do arquivo de saída para revisão

    Returns:
        Número de itens gerados para revisão
    """
    logging.info("Analisando casos para revisão humana...")

    analyzer = HumanReviewAnalyzer()
    all_review_items = []

    # Obter IDs e textos
    ids = df['ID'].tolist() if 'ID' in df.columns else list(range(1, len(df) + 1))
    texts = df[text_column].fillna('').astype(str).tolist()

    for record_id, text, result in zip(ids, texts, results):
        items = analyzer.analyze(
            record_id=record_id,
            text=text,
            detection_result=result
        )
        all_review_items.extend(items)

    # Exportar se houver itens
    if all_review_items:
        export_review_items(all_review_items, output_path, output_format='csv')
        logging.info("Revisão humana: %d itens salvos em %s", len(all_review_items), output_path)
    else:
        logging.info("Revisão humana: nenhum caso duvidoso identificado")

    return len(all_review_items)


def main():
    """
    Função principal do script.

    Processa argumentos de linha de comando e executa a detecção de PII.
    """
    parser = argparse.ArgumentParser(
        description='VIGIL — Detector de Dados Pessoais em Pedidos de Acesso à Informação',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  python main.py --input pedidos.csv --output resultado.csv
  python main.py --input AMOSTRA_e-SIC.xlsx --output resultado.csv
  python main.py --input dados.json --output resultado.json
  python main.py --input dados.xlsx --output out.csv --text-column "Texto"
  python main.py --input pedidos.csv --output resultado.csv --no-review

Formatos suportados:
  Entrada: CSV, XLSX, JSON
  Saída:   CSV, JSON (detectado pela extensão ou via --output-format)

Tipos de PII detectados:
  - CPF (formatado e numérico)
  - Email
  - Telefone (fixo e celular)
  - RG
  - Nomes completos de pessoas

Revisão Humana:
  Por padrão, o programa gera um arquivo 'revisao_humana.csv' com casos
  que merecem atenção especial (contextos artísticos, acadêmicos, etc.).
  Use --no-review para desabilitar este recurso.
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

    parser.add_argument(
        '--no-review',
        action='store_true',
        help='Desabilita geração do arquivo de revisão humana'
    )

    parser.add_argument(
        '--review-output',
        default=None,
        help='Caminho do arquivo de revisão humana (padrão: mesmo diretório do output)'
    )

    parser.add_argument(
        '--output-format', '-f',
        choices=['csv', 'json'],
        default=None,
        help='Formato de saída (csv ou json). Se não especificado, detecta pela extensão do arquivo.'
    )

    args = parser.parse_args()

    # Configurar logging
    setup_logging(args.verbose)

    try:
        # Carregar dados
        df = load_data(args.input, args.text_column)

        # Processar
        use_ner = not args.no_ner
        df_result, results = process_data(df, args.text_column, use_ner=use_ner)

        # Determinar formato de saída
        if args.output_format:
            output_format = args.output_format
        else:
            # Detectar pela extensão
            output_ext = Path(args.output).suffix.lower()
            output_format = 'json' if output_ext == '.json' else 'csv'

        # Salvar resultados
        save_results(
            df_result, args.output,
            output_format=output_format,
            results=results,
            input_path=args.input,
            use_ner=use_ner
        )

        # Gerar revisão humana (habilitado por padrão)
        review_count = 0
        review_path = None
        if not args.no_review:
            # Determinar caminho do arquivo de revisão
            if args.review_output:
                review_path = args.review_output
            else:
                # Mesmo diretório do output, com nome revisao_humana.csv
                output_dir = Path(args.output).parent
                review_path = str(output_dir / 'revisao_humana.csv') if output_dir else 'revisao_humana.csv'

            review_count = generate_human_review(
                df_result, results, args.text_column, review_path
            )

        # Resumo final
        total = len(df_result)
        total_pii = df_result['contem_pii'].sum()
        pct_pii = 100 * total_pii / total if total > 0 else 0
        pct_sem = 100 * (total - total_pii) / total if total > 0 else 0
        print(f"\n{'='*60}")
        print(f"RESUMO DA DETECÇÃO")
        print(f"{'='*60}")
        print(f"Total de registros:  {total}")
        print(f"Registros com PII:   {total_pii} ({pct_pii:.1f}%)")
        print(f"Registros sem PII:   {total - total_pii} ({pct_sem:.1f}%)")
        print(f"Arquivo de saída:    {args.output}")
        if not args.no_review and review_count > 0:
            print(f"Revisão humana:      {review_path} ({review_count} itens)")
        elif not args.no_review:
            print(f"Revisão humana:      Nenhum caso duvidoso identificado")
        print(f"{'='*60}")

        return 0

    except FileNotFoundError as e:
        logging.error(str(e))
        return 1
    except ValueError as e:
        logging.error(str(e))
        return 1
    except Exception as e:
        logging.error("Erro inesperado: %s", e)
        if args.verbose:
            traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
