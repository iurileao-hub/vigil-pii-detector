# Detector de Dados Pessoais em Pedidos de Acesso à Informação

![Python](https://img.shields.io/badge/Python-3.9%2B-blue?logo=python&logoColor=white)
![License](https://img.shields.io/badge/Licença-CGDF-green)
![Hackathon](https://img.shields.io/badge/Hackathon-Participa%20DF%202026-orange)
![NER](https://img.shields.io/badge/NER-BERTimbau-purple?logo=huggingface&logoColor=white)
![Status](https://img.shields.io/badge/Status-Pronto%20para%20Submissão-brightgreen)

> **1º Hackathon em Controle Social: Desafio Participa DF**
> **Categoria:** Acesso à Informação
> **Organizador:** Controladoria-Geral do Distrito Federal (CGDF)

---

## Quick Start

```bash
# 1. Clone e entre no diretório
git clone https://github.com/seu-usuario/hackathon-participa-df.git
cd hackathon-participa-df

# 2. Crie e ative o ambiente virtual
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# ou: .\venv\Scripts\Activate.ps1  # Windows PowerShell

# 3. Instale as dependências
pip install -r requirements.txt

# 4. Execute a detecção
python main.py --input analise/AMOSTRA_e-SIC.xlsx --output resultado.csv
```

---

## Índice

1. [Objetivo](#1-objetivo)
2. [Pré-requisitos](#2-pré-requisitos)
3. [Instalação](#3-instalação)
4. [Execução](#4-execução)
5. [Formato de Dados](#5-formato-de-dados)
6. [Estrutura do Projeto](#6-estrutura-do-projeto)
7. [Arquitetura da Solução](#7-arquitetura-da-solução)
8. [Revisão Humana (Diferencial)](#8-revisão-humana-diferencial)
9. [Avaliação de Métricas](#9-avaliação-de-métricas)
10. [Testes Automatizados](#10-testes-automatizados)
11. [Uso de Inteligência Artificial](#11-uso-de-inteligência-artificial)
12. [Limitações Conhecidas](#12-limitações-conhecidas)
13. [Análise de Acurácia](#13-análise-de-acurácia)
14. [Licença](#14-licença)
15. [Referências](#15-referências)

---

## 1. Objetivo

Este projeto implementa um detector automático de dados pessoais (PII - *Personally Identifiable Information*) em textos de pedidos de acesso à informação. A solução identifica automaticamente pedidos que contêm informações pessoais e que, portanto, deveriam ser classificados como não públicos.

### 1.1. Tipos de Dados Pessoais Detectados

Conforme item 2.2.I do Edital nº 10/2025:

| Tipo | Descrição | Exemplos |
|------|-----------|----------|
| **CPF** | Cadastro de Pessoa Física | `123.456.789-00`, `12345678900` |
| **RG** | Registro Geral | `RG: 12.345.678-9` |
| **Nome** | Nome completo de pessoa física | `João da Silva Santos` |
| **Telefone** | Números de telefone brasileiros | `(61) 99999-8888` |
| **E-mail** | Endereços de correio eletrônico | `usuario@dominio.com` |

## 2. Pré-requisitos

### 2.1. Software Necessário

| Requisito | Versão Mínima | Verificação |
|-----------|---------------|-------------|
| **Python** | 3.9+ | `python3 --version` |
| **pip** | 20.0+ | `pip --version` |
| **venv** | Incluso no Python 3.9+ | `python3 -m venv --help` |

### 2.2. Sistema Operacional

O projeto foi testado em:
- Linux (Ubuntu 20.04+)
- macOS (12.0+)
- Windows 10/11

## 3. Instalação

### 3.1. Clonar o Repositório

```bash
git clone https://github.com/seu-usuario/hackathon-participa-df.git
cd hackathon-participa-df
```

### 3.2. Criar Ambiente Virtual

```bash
python3 -m venv venv
```

### 3.3. Ativar Ambiente Virtual

**Linux/macOS:**
```bash
source venv/bin/activate
```

**Windows (PowerShell):**
```powershell
.\venv\Scripts\Activate.ps1
```

**Windows (CMD):**
```cmd
venv\Scripts\activate.bat
```

### 3.4. Instalar Dependências

```bash
pip install -r requirements.txt
```

### 3.5. Verificar Instalação

```bash
python3 -c "from src import PIIDetector; print('Instalação OK')"
```

## 4. Execução

### 4.1. Comando Básico

```bash
python main.py --input <arquivo_entrada> --output <arquivo_saida>
```

### 4.2. Exemplos de Uso

**Processar arquivo Excel (formato da amostra):**
```bash
python main.py --input analise/AMOSTRA_e-SIC.xlsx --output resultado.csv
```

**Processar arquivo CSV:**
```bash
python main.py --input pedidos.csv --output resultado.csv
```

**Especificar coluna de texto diferente:**
```bash
python main.py --input dados.xlsx --output resultado.csv --text-column "Descrição"
```

**Modo rápido (sem modelo NER):**
```bash
python main.py --input analise/AMOSTRA_e-SIC.xlsx --output resultado.csv --no-ner
```

**Modo detalhado (verbose):**
```bash
python main.py --input analise/AMOSTRA_e-SIC.xlsx --output resultado.csv --verbose
```

### 4.3. Parâmetros Disponíveis

| Parâmetro | Abreviação | Obrigatório | Descrição |
|-----------|------------|-------------|-----------|
| `--input` | `-i` | Sim | Arquivo de entrada (CSV ou XLSX) |
| `--output` | `-o` | Sim | Arquivo de saída (CSV) |
| `--text-column` | `-t` | Não | Coluna com o texto (padrão: `Texto Mascarado`) |
| `--no-ner` | — | Não | Desabilita modelo NER para execução mais rápida |
| `--verbose` | `-v` | Não | Exibe logs detalhados durante a execução |
| `--no-review` | — | Não | Desabilita geração do arquivo de revisão humana |
| `--review-output` | — | Não | Caminho personalizado para o arquivo de revisão humana |
| `--output-format` | `-f` | Não | Formato de saída: `csv` ou `json` (auto-detecta pela extensão) |

## 5. Formato de Dados

### 5.1. Formatos Suportados

| Direção | Formatos | Extensões |
|---------|----------|-----------|
| **Entrada** | CSV, Excel, JSON | `.csv`, `.xlsx`, `.json` |
| **Saída** | CSV, JSON | `.csv`, `.json` |

### 5.2. Entrada

Arquivo contendo pelo menos duas colunas/campos:

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `ID` | Inteiro | Identificador único do registro |
| `Texto Mascarado` | Texto | Conteúdo do pedido de acesso à informação |

**Exemplo CSV:**
```csv
ID,Texto Mascarado
1,"Solicito informações sobre o processo SEI 00015-12345/2026"
2,"Meu CPF é 123.456.789-00 e preciso de cópia do documento"
```

**Exemplo JSON (array de objetos):**
```json
[
  {"ID": 1, "Texto Mascarado": "Solicito informações..."},
  {"ID": 2, "Texto Mascarado": "Meu CPF é 123.456.789-00..."}
]
```

**Exemplo JSON (objeto com array):**
```json
{
  "registros": [
    {"ID": 1, "Texto Mascarado": "..."},
    {"ID": 2, "Texto Mascarado": "..."}
  ]
}
```

### 5.3. Saída CSV

Arquivo CSV com as colunas originais mais três colunas de resultado:

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| `contem_pii` | Booleano | `True` se dados pessoais foram detectados |
| `tipos_detectados` | Lista | Tipos de PII encontrados |
| `confianca` | Decimal | Maior nível de confiança (0.0 a 1.0) |

### 5.4. Saída JSON

Estrutura completa com metadados, resultados e estatísticas:

```json
{
  "metadata": {
    "versao": "1.0.0",
    "timestamp": "2026-01-22T14:36:13Z",
    "arquivo_entrada": "dados.xlsx",
    "total_registros": 99,
    "total_com_pii": 30,
    "configuracao": {
      "ner_habilitado": true,
      "modelo_ner": "pierreguillou/ner-bert-base-cased-pt-lenerbr"
    }
  },
  "resultados": [
    {
      "id": 1,
      "texto": "Meu CPF é 123.456.789-00...",
      "contem_pii": true,
      "confianca": 0.95,
      "tipos_detectados": ["cpf"],
      "detalhes": [
        {
          "tipo": "cpf",
          "valor_detectado": "123.456.789-00",
          "score": 0.95,
          "metodo": "regex"
        }
      ]
    }
  ],
  "estatisticas": {
    "por_tipo": {"cpf": 15, "nome": 22, "email": 8},
    "percentual_com_pii": 30.3
  }
}
```

O formato JSON é ideal para **integrações com outros sistemas** e APIs.

## 6. Estrutura do Projeto

```
hackathon-participa-df/
├── README.md                 # Documentação principal (este arquivo)
├── CLAUDE.md                 # Instruções para desenvolvimento com IA
├── requirements.txt          # Dependências do projeto
├── main.py                   # Ponto de entrada CLI
│
├── src/                      # Código-fonte principal
│   ├── __init__.py          # Exportações do módulo
│   ├── detector.py          # Classe PIIDetector (orquestrador)
│   ├── patterns.py          # Padrões regex e filtros anti-FP
│   ├── exclusions.py        # Lista de nomes institucionais
│   ├── preprocessor.py      # Normalização de texto
│   └── human_review.py      # Sistema de revisão humana (diferencial)
│
├── tests/                    # Testes automatizados
│   ├── test_patterns.py     # Testes de padrões regex
│   └── test_detector.py     # Testes de integração
│
├── scripts/                  # Scripts auxiliares
│   ├── evaluate.py          # Avaliação de métricas (F1, Precision, Recall)
│   └── analyze_errors.py    # Análise detalhada de FN/FP
│
├── docs/                     # Documentação adicional
│   └── DODF-hackathon.md    # Edital completo do hackathon
│
└── data/                     # Dados (não versionados)
    └── .gitkeep
```

### 6.1. Descrição dos Arquivos

| Arquivo | Função |
|---------|--------|
| `main.py` | Interface de linha de comando. Processa arquivos CSV/XLSX e gera resultados. |
| `src/detector.py` | Classe principal `PIIDetector`. Orquestra detecção por regex, NER e contexto. |
| `src/patterns.py` | Padrões regex para CPF, email, telefone, RG. Inclui filtros anti-falso-positivo. |
| `src/exclusions.py` | Lista de 130+ nomes institucionais para evitar falsos positivos em nomes. |
| `src/preprocessor.py` | Normalização de texto Unicode, preservando dígitos e acentuação. |
| `src/human_review.py` | Sistema de revisão humana para casos duvidosos. Detecta contextos especiais (artístico, acadêmico, jurídico, etc.) e gera relatório priorizado. |
| `scripts/evaluate.py` | Calcula métricas P1 (F1-Score) comparando predições com gabarito. |
| `scripts/analyze_errors.py` | Análise detalhada de falsos negativos e falsos positivos. |

## 7. Arquitetura da Solução

O detector utiliza uma arquitetura em camadas para maximizar a sensibilidade (recall):

```
┌─────────────────────────────────────────────────────────────┐
│                     TEXTO DE ENTRADA                        │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              CAMADA 1: PRÉ-PROCESSAMENTO                    │
│  • Normalização Unicode (NFKC)                              │
│  • Remoção de caracteres de controle                        │
│  • Preservação de dígitos e separadores                     │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              CAMADA 2: PADRÕES ESTRUTURADOS (REGEX)         │
│  • CPF: XXX.XXX.XXX-XX e numérico com contexto              │
│  • E-mail: padrão RFC 5322 simplificado                     │
│  • Telefone: formatos brasileiros (DDD + 8/9 dígitos)       │
│  • RG: padrão com contexto explícito                        │
│  • Filtros anti-FP: SEI, NUP, CDA, CNH, matrícula           │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              CAMADA 3: NER (NOMES DE PESSOAS)               │
│  • Modelo BERTimbau NER (se disponível)                     │
│  • Fallback: heurísticas com contexto explícito             │
│  • Filtro de nomes institucionais (130+ exclusões)          │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              CAMADA 4: SINAIS CONTEXTUAIS                   │
│  • Marcadores de 1ª pessoa: "meu CPF", "meu nome"           │
│  • Indicadores de contato: "endereço", "WhatsApp"           │
│  • Metadados para análise (não contam como PII)             │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    RESULTADO FINAL                          │
│  contem_pii = True se CPF, RG, Nome, Telefone ou Email      │
└─────────────────────────────────────────────────────────────┘
```

### 7.1. Estratégia: Recall-First

O detector prioriza **minimizar falsos negativos** (FN), conforme critério de desempate do edital (item 8.1.5.4):

1. **Menor número de FN** (crítico) — pedidos com PII que não foram detectados
2. **Menor número de FP** (secundário) — pedidos sem PII classificados incorretamente
3. **Maior nota P1** (terciário) — F1-Score

## 8. Revisão Humana (Diferencial)

> **🎯 Recurso Diferencial:** Este módulo representa um diferencial importante deste projeto, gerando automaticamente um relatório de casos ambíguos com fundamentação legal para revisão humana.

### 8.1. Visão Geral

O sistema de **Revisão Humana** é executado automaticamente junto com a detecção de PII. Ele identifica casos que merecem atenção especial, priorizando-os por nível de incerteza e fornecendo fundamentação legal para auxiliar na decisão final.

**Comportamento padrão:**
```bash
python main.py --input dados.xlsx --output resultado.csv
# Gera automaticamente:
# - resultado.csv (detecções)
# - revisao_humana.csv (casos para revisão)
```

**Para desabilitar a revisão humana:**
```bash
python main.py --input dados.xlsx --output resultado.csv --no-review
```

**Benefícios:**
- 📋 Priorização automática de casos duvidosos
- ⚖️ Fundamentação legal baseada na LGPD
- 🎯 Foco no que realmente importa (evita revisão manual de milhares de registros)
- 📊 Relatório exportável em CSV para análise

### 8.2. Quando Usar

O módulo de revisão humana é útil quando:
- A detecção automática encontrou nomes em contextos especiais
- O score de confiança do modelo NER está em faixa intermediária
- Há necessidade de auditoria ou validação dos resultados

### 8.3. Contextos Detectados

O sistema identifica automaticamente contextos que podem representar exceções à proteção de dados pessoais:

| Contexto | Indicadores | Fundamento Legal |
|----------|-------------|------------------|
| **Artístico** | Nomes de artistas, obras, patrimônio cultural | Não são PII do solicitante |
| **Acadêmico** | Pesquisadores, orientadores, publicações | LGPD Art. 4º, II, b e Art. 7º, § 4º |
| **Jornalístico** | Reportagens, entrevistas, fontes | LGPD Art. 4º, II, a |
| **Servidor Público** | Cargos, funções públicas | Dados manifestamente públicos |
| **Histórico** | Homenagens, memoriais, falecidos | Contexto de memória coletiva |
| **Jurídico** | Advogados (OAB), procuradores | Atuação profissional pública |
| **Autoria** | Autores, responsáveis por documentos | Identificação funcional |

### 8.4. Níveis de Prioridade

| Prioridade | Critério | Ação Recomendada |
|------------|----------|------------------|
| 🔴 **Alta** | Contexto especial detectado com score alto | Revisar imediatamente |
| 🟡 **Média** | Contexto especial com score moderado | Revisar quando possível |
| 🟢 **Baixa** | Score intermediário sem contexto especial | Revisar se houver tempo |

### 8.5. Como Usar (Para Avaliadores)

#### Uso via Linha de Comando (Recomendado)

O relatório de revisão humana é gerado **automaticamente** ao executar o programa:

```bash
python main.py --input analise/AMOSTRA_e-SIC.xlsx --output resultado.csv
```

**Saída esperada:**
```
============================================================
RESUMO DA DETECÇÃO
============================================================
Total de registros:  99
Registros com PII:   30 (30.3%)
Registros sem PII:   69 (69.7%)
Arquivo de saída:    resultado.csv
Revisão humana:      revisao_humana.csv (35 itens)
============================================================
```

#### Uso Programático (Avançado)

```python
from src import PIIDetector
from src.human_review import HumanReviewAnalyzer, export_review_items

# 1. Processar texto
detector = PIIDetector()
result = detector.detect("Texto com nome de Athos Bulcão nos painéis...")

# 2. Analisar se precisa de revisão
analyzer = HumanReviewAnalyzer()
items = analyzer.analyze(record_id=1, text="...", detection_result=result)

# 3. Exportar relatório
export_review_items(items, 'revisao.csv', format='csv')
```

#### Saída Gerada

O arquivo `revisao_humana.csv` contém:

| Coluna | Descrição |
|--------|-----------|
| `ID` | Identificador do registro original |
| `Prioridade` | alta, media, baixa |
| `Tipo PII` | Tipo de dado pessoal detectado |
| `Valor Detectado` | O dado específico encontrado |
| `Score` | Confiança da detecção (0.0 a 1.0) |
| `Motivo` | Razão para revisão (ex: contexto_artistico) |
| `Texto (Trecho)` | Trecho do texto original para contexto |
| `Explicacao` | Fundamentação legal para a decisão |

#### Exemplo de Saída

```csv
ID,Prioridade,Tipo PII,Valor Detectado,Score,Motivo,Texto (Trecho),Explicacao
15,alta,nome,Athos Bulcão,1.00,contexto_artistico,"...painéis Athos Bulcão...",Texto contém referências a arte/patrimônio...
52,media,nome,Carolina Guimarães,1.00,contexto_academico,"...Pesquisadora do Instituto...",Texto contém contexto acadêmico...
```

### 8.6. Interpretação dos Resultados

**Para cada item de revisão, o avaliador deve considerar:**

1. **O nome identificado é do próprio solicitante?**
   - Se NÃO → Provavelmente não é PII relevante

2. **O contexto justifica exceção à LGPD?**
   - Artístico: Nomes de artistas em obras não são dados do cidadão
   - Acadêmico: Art. 4º, II, b exclui fins acadêmicos
   - Jornalístico: Art. 4º, II, a exclui fins jornalísticos

3. **O dado é manifestamente público?**
   - Servidores em função pública
   - Advogados identificados por OAB
   - Autores de publicações

### 8.7. Arquivos Gerados na Análise

```
analise/
├── resultado.csv           # Detecção completa
├── resultado_v2.csv        # Validação de consistência
└── revisao_humana.csv      # Itens para revisão (15 registros)
```

## 9. Avaliação de Métricas

### 9.1. Executar Avaliação

```bash
python scripts/evaluate.py --predictions resultado.csv --ground-truth gabarito.csv
```

### 9.2. Parâmetros da Avaliação

| Parâmetro | Descrição |
|-----------|-----------|
| `--predictions` | Arquivo CSV com as predições do modelo |
| `--ground-truth` | Arquivo CSV com o gabarito de referência |
| `--show-errors` | Exibe IDs dos falsos positivos e negativos |

### 9.3. Métricas Calculadas

| Métrica | Fórmula | Descrição |
|---------|---------|-----------|
| **Precisão** | VP / (VP + FP) | Exatidão das classificações positivas |
| **Sensibilidade** | VP / (VP + FN) | Capacidade de encontrar casos relevantes |
| **F1-Score (P1)** | 2 × (P × S) / (P + S) | Média harmônica de precisão e sensibilidade |

## 10. Testes Automatizados

### 10.1. Executar Todos os Testes

```bash
pip install pytest
python -m pytest tests/ -v
```

### 10.2. Executar Testes Específicos

```bash
# Testes de padrões regex
python -m pytest tests/test_patterns.py -v

# Testes do detector completo
python -m pytest tests/test_detector.py -v

# Testes do módulo de revisão humana
python -m pytest tests/test_human_review.py -v
```

## 11. Uso de Inteligência Artificial

Conforme item 13.9 do Edital nº 10/2025, este projeto foi desenvolvido com auxílio de:

### 11.1. Ferramenta Utilizada

- **Claude Code** (Anthropic) — Assistente de programação baseado em IA

### 11.2. Modelos e Bibliotecas de IA

| Componente | Modelo/Biblioteca | Fonte |
|------------|-------------------|-------|
| NER (Nomes) | BERTimbau NER | [HuggingFace](https://huggingface.co/pierreguillou/ner-bert-base-cased-pt-lenerbr) |
| Tokenização | Transformers 4.30+ | [HuggingFace](https://huggingface.co/docs/transformers) |

### 11.3. Atividades Assistidas por IA

- Análise exploratória da amostra de dados
- Geração e otimização de padrões regex
- Implementação de código Python
- Criação de testes automatizados
- Documentação do projeto

### 11.4. Responsabilidade

O código foi integralmente revisado e compreendido pela equipe, sendo de responsabilidade exclusiva dos participantes, conforme estabelecido no edital.

## 12. Limitações Conhecidas

1. **CPFs Sintéticos**: A amostra contém CPFs com dígitos verificadores inválidos. O detector **não valida** dígitos verificadores para evitar falsos negativos.

2. **Detecção de Nomes (sem NER)**: O fallback para detecção de nomes requer contexto explícito ("meu nome é", "CPF de...") para evitar falsos positivos.

3. **Textos Muito Longos**: Textos são processados em chunks para garantir que nomes no final do texto também sejam detectados (corrigido na versão atual).

## 13. Análise de Acurácia

O detector foi submetido a uma análise rigorosa de acurácia utilizando a amostra oficial de 99 registros. Os resultados e a metodologia estão documentados na pasta `analise/`.

### 13.1. Resultados Obtidos (com NER)

| Métrica | Valor |
|---------|-------|
| **Registros analisados** | 99 |
| **Verdadeiros Positivos (VP)** | 29 |
| **Falsos Positivos (FP)** | 1 |
| **Verdadeiros Negativos (VN)** | 69 |
| **Falsos Negativos (FN)** | 0 |
| **Precisão** | 96,7% |
| **Recall (Sensibilidade)** | 100% |
| **F1-Score estimado** | 0,983 |

> **Nota:** Os resultados acima foram obtidos com o modelo NER (BERTimbau) habilitado.
> Com a flag `--no-ner`, o detector usa heurísticas mais conservadoras para nomes,
> resultando em menos detecções mas também menos falsos positivos. Recomendamos
> executar com NER para máxima sensibilidade.

### 13.2. Destaques da Análise

- **Zero falsos negativos**: Todos os registros com PII real foram detectados
- **Consistência**: Resultados 100% reprodutíveis entre múltiplas execuções
- **Fundamentação legal**: Decisões de classificação baseadas na LGPD e no edital
- **Sistema de Revisão Humana**: 15 itens sinalizados para revisão opcional

### 13.3. Casos Especiais Documentados

A análise inclui discussão detalhada de casos ambíguos com fundamentação legal:

| Caso | Decisão | Fundamento |
|------|---------|------------|
| Nomes de artistas em contexto de patrimônio | Considerado FP | Não são PII do solicitante |
| Nomes em contexto acadêmico (pesquisadores) | Considerado VN | Art. 4º, II, b e Art. 7º, § 4º da LGPD |
| Nomes únicos sem sobrenome | Considerado VN | Não permite identificação direta |

### 13.4. Arquivos de Análise

```
analise/
├── AMOSTRA_e-SIC.xlsx      # Amostra oficial (99 registros)
├── RELATORIO_ANALISE.md    # Relatório completo com fundamentação
├── resultado.csv           # Resultado da 1ª execução
├── resultado_v2.csv        # Validação de consistência
└── revisao_humana.csv      # Itens para revisão humana (15 registros)
```

Para detalhes completos, consulte [`analise/RELATORIO_ANALISE.md`](analise/RELATORIO_ANALISE.md).

## 14. Licença

Projeto desenvolvido para o **1º Hackathon em Controle Social: Desafio Participa DF**.

Controladoria-Geral do Distrito Federal (CGDF) — Janeiro 2026.

---

## 15. Referências

- [Edital nº 10/2025 - Desafio Participa DF](docs/DODF-hackathon.md)
- [BERTimbau NER - HuggingFace](https://huggingface.co/pierreguillou/ner-bert-base-cased-pt-lenerbr)
- [Lei de Acesso à Informação (LAI) - Lei nº 12.527/2011](http://www.planalto.gov.br/ccivil_03/_ato2011-2014/2011/lei/l12527.htm)
- [LGPD - Lei nº 13.709/2018](http://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709.htm)
