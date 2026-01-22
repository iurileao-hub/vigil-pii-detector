# CLAUDE.md — Guia de Desenvolvimento com IA

Este arquivo fornece orientações para o assistente de programação **Claude Code** (Anthropic) ao trabalhar com o código deste repositório.

## Visão Geral do Projeto

**Projeto:** Detector de Dados Pessoais em Pedidos de Acesso à Informação
**Hackathon:** 1º Hackathon em Controle Social: Desafio Participa DF
**Categoria:** Acesso à Informação
**Objetivo:** Identificar automaticamente pedidos de acesso à informação que contenham dados pessoais (PII)

### Tipos de PII a Detectar

Conforme item 2.2.I do Edital nº 10/2025:
- **CPF** — Cadastro de Pessoa Física
- **RG** — Registro Geral
- **Nome** — Nome completo de pessoa física
- **Telefone** — Números de telefone brasileiros
- **E-mail** — Endereços de correio eletrônico

### Prioridade Estratégica

**Recall-first** — Minimizar falsos negativos (FN) é crítico.

Critérios de desempate (item 8.1.5.4 do edital):
1. Menor número de FN (prioridade máxima)
2. Menor número de FP (secundário)
3. Maior nota P1/F1-Score (terciário)

## Comandos de Execução

```bash
# Configurar ambiente
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
pip install -r requirements.txt

# Executar detecção (gera resultado.csv + revisao_humana.csv automaticamente)
python main.py --input analise/AMOSTRA_e-SIC.xlsx --output resultado.csv

# Saída em JSON (detecta pela extensão)
python main.py --input analise/AMOSTRA_e-SIC.xlsx --output resultado.json

# Entrada e saída em JSON
python main.py --input dados.json --output resultado.json

# Executar sem revisão humana
python main.py --input analise/AMOSTRA_e-SIC.xlsx --output resultado.csv --no-review

# Executar com NER desabilitado (mais rápido)
python main.py --input analise/AMOSTRA_e-SIC.xlsx --output resultado.csv --no-ner

# Avaliar métricas (se houver gabarito)
python scripts/evaluate.py --predictions resultado.csv --ground-truth gabarito.csv

# Executar testes
python -m pytest tests/ -v
```

## Arquitetura Implementada

```
Texto de Entrada
       │
       ▼
┌──────────────────────────────────────────────┐
│ Camada 1: PRÉ-PROCESSAMENTO                  │
│ • Normalização Unicode (NFKC)                │
│ • Preservação de dígitos e acentos           │
└──────────────────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────────┐
│ Camada 2: PADRÕES REGEX                      │
│ • CPF: formatado e numérico com contexto     │
│ • Email, Telefone, RG                        │
│ • Filtros anti-FP (SEI, NUP, CDA, CNH)       │
└──────────────────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────────┐
│ Camada 3: NER (NOMES)                        │
│ • BERTimbau NER (se disponível)              │
│ • Fallback: contextos explícitos             │
│ • Filtro de nomes institucionais             │
└──────────────────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────────┐
│ Camada 4: SINAIS CONTEXTUAIS                 │
│ • Metadados (não contam como PII)            │
│ • Usados apenas para análise                 │
└──────────────────────────────────────────────┘
       │
       ▼
   Resultado: contem_pii = True/False
```

## Estrutura do Projeto

```
hackathon-participa-df/
├── main.py                   # CLI principal
├── requirements.txt          # Dependências
├── README.md                 # Documentação completa
├── CLAUDE.md                 # Este arquivo
│
├── src/                      # Código-fonte
│   ├── __init__.py          # Exportações
│   ├── detector.py          # Classe PIIDetector (orquestrador)
│   ├── patterns.py          # Padrões regex e filtros
│   ├── exclusions.py        # Nomes institucionais (130+)
│   ├── preprocessor.py      # Normalização de texto
│   └── human_review.py      # Sistema de revisão humana
│
├── tests/                    # Testes automatizados
│   ├── test_patterns.py     # Testes de regex
│   ├── test_detector.py     # Testes de integração
│   └── test_human_review.py # Testes de revisão humana
│
├── scripts/                  # Scripts auxiliares
│   ├── evaluate.py          # Métricas (F1, Precision, Recall)
│   └── analyze_errors.py    # Análise de FN/FP
│
├── analise/                  # Análise de acurácia
│   ├── AMOSTRA_e-SIC.xlsx   # Amostra oficial (99 registros)
│   ├── RELATORIO_ANALISE.md # Relatório com fundamentação legal
│   ├── resultado.csv        # Resultado da execução
│   ├── resultado_v2.csv     # Validação de consistência
│   └── revisao_humana.csv   # Itens para revisão humana
│
├── docs/                     # Documentação
│   └── DODF-hackathon.md    # Edital do hackathon
│
└── data/                     # Dados (não versionados)
```

## Critérios de Avaliação P2 (Documentação)

| Critério | Pontos | Status |
|----------|--------|--------|
| 1.a Pré-requisitos (Python 3.9+) | 1 | ✅ |
| 1.b requirements.txt funcional | 2 | ✅ |
| 1.c Comandos sequenciais de instalação | 1 | ✅ |
| 2.a Comandos de execução com exemplos | 2 | ✅ |
| 2.b Formato entrada/saída documentado | 1 | ✅ |
| 3.a README com objetivo e arquivos | 1 | ✅ |
| 3.b Comentários em código complexo | 1 | ✅ |
| 3.c Estrutura lógica de arquivos | 1 | ✅ |
| **Total** | **10** | ✅ |

## Padrões Regex Implementados

```python
# CPF formatado (XXX.XXX.XXX-XX)
CPF_FORMATTED = r'\d{3}\.\d{3}\.\d{3}-\d{2}'

# CPF parcial (XXXXXXXXX-XX)
CPF_PARTIAL = r'\b\d{9}-\d{2}\b'

# CPF numérico com contexto
CPF_NUMERIC = r'(?:CPF\s*[:\s]*)\b(\d{11})\b'

# Email
EMAIL = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'

# Telefone brasileiro
PHONE = r'\(\d{2}\)\s*\d{4,5}-?\d{4}'
PHONE_INTL = r'\+55\s*\(?\d{2}\)?\s*\d{4,5}[-\s]?\d{4}'

# RG com contexto
RG = r'\bRG[:\s]*[\d.-]+'
```

## Filtros Anti-Falso-Positivo

- **Processos SEI/NUP:** Números que seguem padrão de protocolo são excluídos
- **CDA, CNH, NIS, matrícula:** Números de 11 dígitos com esses contextos são ignorados
- **Nomes institucionais:** 130+ exclusões (Distrito Federal, Secretaria, etc.)
- **Word boundaries:** Evitar "rg" em "órgão"

## Dados da Amostra

Arquivo `analise/AMOSTRA_e-SIC.xlsx`:
- **99 registros** de pedidos de acesso à informação
- Colunas: `ID`, `Texto Mascarado`
- CPFs na amostra são **sintéticos** (dígitos verificadores inválidos)
- Contém processos SEI/NUP que podem gerar falsos positivos

## Diretrizes de Código

1. **Linguagem:** Comentários e documentação em **português brasileiro**
2. **Estilo:** PEP 8, docstrings em todas as funções públicas
3. **Segurança:** Nenhum dado pessoal real no repositório
4. **IA:** Uso documentado conforme item 13.9 do edital

## Submissão

- Repositório público no GitHub/GitLab
- Executável após `git clone` → `pip install -r requirements.txt` → `python main.py`
- Sem modificações após prazo (30/01/2026)
- Tag: `submission_v1`
