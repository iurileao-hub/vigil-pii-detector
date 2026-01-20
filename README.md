# Detector de Dados Pessoais em Pedidos de Acesso à Informação

**1º Hackathon em Controle Social: Desafio Participa DF**
**Categoria: Acesso à Informação**

## Objetivo

Este projeto implementa um detector automático de dados pessoais (PII - Personally Identifiable Information) em textos de pedidos de acesso à informação. O sistema identifica se um pedido contém informações que deveriam ter sido marcadas como sigilosas, mas foram incorretamente classificadas como públicas.

### Tipos de PII Detectados

- **CPF**: Formato XXX.XXX.XXX-XX e numérico (11 dígitos com contexto)
- **Email**: Endereços de correio eletrônico
- **Telefone**: Números brasileiros (fixo e celular)
- **RG**: Registro Geral com contexto explícito
- **Nomes**: Nomes completos de pessoas físicas

## Pré-requisitos

- **Python**: 3.9 ou superior
- **pip**: Gerenciador de pacotes Python
- **venv**: Módulo de ambiente virtual (incluso no Python 3.9+)

### Dependências principais

- `pandas` >= 1.5.0 - Manipulação de dados
- `openpyxl` >= 3.1.0 - Leitura de arquivos Excel
- `transformers` >= 4.30.0 - Modelos de NLP (opcional, para NER)
- `torch` >= 2.0.0 - Backend para transformers (opcional)
- `pytest` >= 7.0.0 - Testes automatizados

## Instalação

### 1. Clonar o repositório

```bash
git clone https://github.com/seu-usuario/hackathon-participa-df.git
cd hackathon-participa-df
```

### 2. Criar ambiente virtual

```bash
python3 -m venv venv
```

### 3. Ativar ambiente virtual

**Linux/macOS:**
```bash
source venv/bin/activate
```

**Windows:**
```bash
venv\Scripts\activate
```

### 4. Instalar dependências

```bash
pip install -r requirements.txt
```

### 5. (Opcional) Baixar modelo NER

Para melhor detecção de nomes, o sistema pode usar um modelo NER pré-treinado. O download é automático na primeira execução, mas pode demorar (~500MB).

Para pular o modelo NER e usar o fallback mais rápido:
```bash
python main.py --input arquivo.csv --output resultado.csv --no-ner
```

## Execução

### Comando básico

```bash
python main.py --input <arquivo_entrada> --output <arquivo_saida>
```

### Exemplos

**Processar arquivo Excel da amostra:**
```bash
python main.py --input AMOSTRA_e-SIC.xlsx --output resultado.csv
```

**Processar arquivo CSV:**
```bash
python main.py --input pedidos.csv --output resultado.csv
```

**Especificar coluna de texto:**
```bash
python main.py --input dados.xlsx --output resultado.csv --text-column "Texto"
```

**Modo rápido (sem modelo NER):**
```bash
python main.py --input dados.xlsx --output resultado.csv --no-ner
```

**Modo detalhado:**
```bash
python main.py --input dados.xlsx --output resultado.csv --verbose
```

### Parâmetros

| Parâmetro | Obrigatório | Descrição |
|-----------|-------------|-----------|
| `--input`, `-i` | Sim | Arquivo de entrada (CSV ou XLSX) |
| `--output`, `-o` | Sim | Arquivo de saída (CSV) |
| `--text-column`, `-t` | Não | Nome da coluna com texto (padrão: "Texto Mascarado") |
| `--no-ner` | Não | Desabilita modelo NER (mais rápido) |
| `--verbose`, `-v` | Não | Mostra logs detalhados |

## Formato de Entrada/Saída

### Entrada

Arquivo CSV ou XLSX com pelo menos duas colunas:
- `ID`: Identificador único do registro
- `Texto Mascarado`: Texto do pedido de acesso à informação

**Exemplo:**
```csv
ID,Texto Mascarado
1,"Solicito informações sobre o processo SEI 00015-12345/2026"
2,"Meu CPF é 123.456.789-00 e preciso de um documento"
```

### Saída

Arquivo CSV com as colunas originais mais:
- `contem_pii`: `True` se PII foi detectado, `False` caso contrário
- `tipos_detectados`: Lista de tipos de PII encontrados
- `confianca`: Maior nível de confiança da detecção (0.0 a 1.0)

**Exemplo:**
```csv
ID,Texto Mascarado,contem_pii,tipos_detectados,confianca
1,"Solicito informações sobre o processo...",False,"",0.0
2,"Meu CPF é 123.456.789-00...",True,"cpf, contexto_1pessoa",0.95
```

## Estrutura do Projeto

```
hackathon-participa-df/
├── README.md                 # Este arquivo (documentação)
├── requirements.txt          # Dependências do projeto
├── main.py                   # Ponto de entrada CLI
│
├── src/                      # Código-fonte principal
│   ├── __init__.py          # Exportações do módulo
│   ├── detector.py          # Classe principal PIIDetector
│   ├── patterns.py          # Padrões regex e filtros anti-FP
│   ├── exclusions.py        # Lista de nomes institucionais
│   └── preprocessor.py      # Normalização de texto
│
├── tests/                    # Testes automatizados
│   ├── test_patterns.py     # Testes de padrões regex
│   └── test_detector.py     # Testes de integração
│
├── scripts/                  # Scripts auxiliares
│   └── evaluate.py          # Avaliação de métricas (F1, Precision, Recall)
│
└── data/                     # Dados (não versionados)
    └── .gitkeep
```

### Descrição dos Arquivos

| Arquivo | Descrição |
|---------|-----------|
| `main.py` | Script principal com interface CLI. Processa arquivos e gera resultados. |
| `src/detector.py` | Classe `PIIDetector` que combina regex, NER e sinais contextuais. |
| `src/patterns.py` | Classe `PIIPatterns` com regex para CPF, email, telefone, RG. |
| `src/exclusions.py` | Lista de 130+ nomes institucionais para evitar falsos positivos. |
| `src/preprocessor.py` | Normalização de texto preservando dígitos e acentuação. |
| `scripts/evaluate.py` | Calcula métricas de avaliação comparando com gabarito. |

## Arquitetura

O detector usa uma abordagem em camadas para maximizar recall:

```
Texto de Entrada
       │
       ▼
┌──────────────────────────────────────┐
│ Camada 1: PRÉ-PROCESSAMENTO          │
│ • Normalização Unicode               │
│ • Remoção de caracteres de controle  │
└──────────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────┐
│ Camada 2: PADRÕES REGEX              │
│ • CPF (formatado e numérico)         │
│ • Email, Telefone, RG                │
│ • Filtros anti-FP (SEI, NUP, CDA)    │
└──────────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────┐
│ Camada 3: NER (Nomes)                │
│ • Modelo BERTimbau (se disponível)   │
│ • Fallback: heurística de padrões    │
│ • Filtro de nomes institucionais     │
└──────────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────┐
│ Camada 4: SINAIS CONTEXTUAIS         │
│ • Marcadores de 1ª pessoa            │
│ • Indicadores de endereço/contato    │
└──────────────────────────────────────┘
       │
       ▼
   contem_pii = ANY(camadas)
```

### Estratégia: Recall-First

O detector prioriza **minimizar falsos negativos** (FN), conforme critério de desempate do hackathon:
1. Menor número de FN (crítico)
2. Menor número de FP (secundário)
3. Maior F1-Score (terciário)

## Testes

### Executar todos os testes

```bash
pip install pytest
python -m pytest tests/ -v
```

### Executar testes específicos

```bash
# Testes de padrões regex
python -m pytest tests/test_patterns.py -v

# Testes do detector
python -m pytest tests/test_detector.py -v
```

## Avaliação de Métricas

Para avaliar o desempenho com um gabarito:

```bash
python scripts/evaluate.py --predictions resultado.csv --ground-truth gabarito.csv
```

**Parâmetros:**
- `--predictions`: Arquivo CSV com as predições
- `--ground-truth`: Arquivo CSV com o gabarito
- `--show-errors`: Mostra IDs dos falsos positivos e negativos

## Uso de Inteligência Artificial

Este projeto foi desenvolvido com auxílio de **Claude Code** (Anthropic), utilizado para:

- Análise exploratória da amostra de dados
- Geração de código Python
- Otimização de padrões regex
- Criação de testes automatizados
- Documentação do projeto

Conforme item 13.9 do edital, o uso de IA generativa é permitido desde que:
- O código seja compreendido pela equipe
- Seja feita declaração de uso
- O resultado final seja de responsabilidade da equipe

## Limitações Conhecidas

1. **CPFs sintéticos**: A amostra contém CPFs com dígitos verificadores inválidos. O detector NÃO valida dígitos verificadores para evitar falsos negativos.

2. **Detecção de nomes**: O fallback para detecção de nomes (sem modelo NER) pode gerar falsos positivos com nomes próprios em contextos não-PII.

3. **Tamanho de texto**: Textos muito longos (>1500 caracteres) são truncados para o modelo NER.

## Licença

Este projeto foi desenvolvido para o 1º Hackathon em Controle Social: Desafio Participa DF.

## Contato

Para dúvidas ou sugestões, abra uma issue no repositório.

---

**Hackathon Participa DF - Janeiro 2026**
