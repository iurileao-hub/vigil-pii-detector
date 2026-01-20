# Detector de Dados Pessoais em Pedidos de Acesso à Informação

**1º Hackathon em Controle Social: Desafio Participa DF**
**Categoria: Acesso à Informação**

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
python main.py --input AMOSTRA_e-SIC.xlsx --output resultado.csv
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
python main.py --input AMOSTRA_e-SIC.xlsx --output resultado.csv --no-ner
```

**Modo detalhado (verbose):**
```bash
python main.py --input AMOSTRA_e-SIC.xlsx --output resultado.csv --verbose
```

### 4.3. Parâmetros Disponíveis

| Parâmetro | Abreviação | Obrigatório | Descrição |
|-----------|------------|-------------|-----------|
| `--input` | `-i` | Sim | Arquivo de entrada (CSV ou XLSX) |
| `--output` | `-o` | Sim | Arquivo de saída (CSV) |
| `--text-column` | `-t` | Não | Coluna com o texto (padrão: `Texto Mascarado`) |
| `--no-ner` | — | Não | Desabilita modelo NER para execução mais rápida |
| `--verbose` | `-v` | Não | Exibe logs detalhados durante a execução |

## 5. Formato de Dados

### 5.1. Entrada

Arquivo CSV ou XLSX contendo pelo menos duas colunas:

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| `ID` | Inteiro | Identificador único do registro |
| `Texto Mascarado` | Texto | Conteúdo do pedido de acesso à informação |

**Exemplo de entrada (CSV):**
```csv
ID,Texto Mascarado
1,"Solicito informações sobre o processo SEI 00015-12345/2026"
2,"Meu CPF é 123.456.789-00 e preciso de cópia do documento"
3,"Informo meu e-mail: contato@exemplo.com para resposta"
```

### 5.2. Saída

Arquivo CSV com as colunas originais mais três colunas de resultado:

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| `contem_pii` | Booleano | `True` se dados pessoais foram detectados |
| `tipos_detectados` | Lista | Tipos de PII encontrados (ex: `['cpf', 'nome']`) |
| `confianca` | Decimal | Maior nível de confiança da detecção (0.0 a 1.0) |

**Exemplo de saída (CSV):**
```csv
ID,Texto Mascarado,contem_pii,tipos_detectados,confianca
1,"Solicito informações sobre o processo SEI 00015-12345/2026",False,[],0.0
2,"Meu CPF é 123.456.789-00 e preciso de cópia do documento",True,['cpf'],0.95
3,"Informo meu e-mail: contato@exemplo.com para resposta",True,['email'],0.95
```

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
│   └── preprocessor.py      # Normalização de texto
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

## 8. Avaliação de Métricas

### 8.1. Executar Avaliação

```bash
python scripts/evaluate.py --predictions resultado.csv --ground-truth gabarito.csv
```

### 8.2. Parâmetros da Avaliação

| Parâmetro | Descrição |
|-----------|-----------|
| `--predictions` | Arquivo CSV com as predições do modelo |
| `--ground-truth` | Arquivo CSV com o gabarito de referência |
| `--show-errors` | Exibe IDs dos falsos positivos e negativos |

### 8.3. Métricas Calculadas

| Métrica | Fórmula | Descrição |
|---------|---------|-----------|
| **Precisão** | VP / (VP + FP) | Exatidão das classificações positivas |
| **Sensibilidade** | VP / (VP + FN) | Capacidade de encontrar casos relevantes |
| **F1-Score (P1)** | 2 × (P × S) / (P + S) | Média harmônica de precisão e sensibilidade |

## 9. Testes Automatizados

### 9.1. Executar Todos os Testes

```bash
pip install pytest
python -m pytest tests/ -v
```

### 9.2. Executar Testes Específicos

```bash
# Testes de padrões regex
python -m pytest tests/test_patterns.py -v

# Testes do detector completo
python -m pytest tests/test_detector.py -v
```

## 10. Uso de Inteligência Artificial

Conforme item 13.9 do Edital nº 10/2025, este projeto foi desenvolvido com auxílio de:

### 10.1. Ferramenta Utilizada

- **Claude Code** (Anthropic) — Assistente de programação baseado em IA

### 10.2. Modelos e Bibliotecas de IA

| Componente | Modelo/Biblioteca | Fonte |
|------------|-------------------|-------|
| NER (Nomes) | BERTimbau NER | [HuggingFace](https://huggingface.co/pierreguillou/ner-bert-base-cased-pt-lenerbr) |
| Tokenização | Transformers 4.30+ | [HuggingFace](https://huggingface.co/docs/transformers) |

### 10.3. Atividades Assistidas por IA

- Análise exploratória da amostra de dados
- Geração e otimização de padrões regex
- Implementação de código Python
- Criação de testes automatizados
- Documentação do projeto

### 10.4. Responsabilidade

O código foi integralmente revisado e compreendido pela equipe, sendo de responsabilidade exclusiva dos participantes, conforme estabelecido no edital.

## 11. Limitações Conhecidas

1. **CPFs Sintéticos**: A amostra contém CPFs com dígitos verificadores inválidos. O detector **não valida** dígitos verificadores para evitar falsos negativos.

2. **Detecção de Nomes (sem NER)**: O fallback para detecção de nomes requer contexto explícito ("meu nome é", "CPF de...") para evitar falsos positivos.

3. **Truncamento**: Textos com mais de 1.500 caracteres são truncados para o modelo NER.

## 12. Licença

Projeto desenvolvido para o **1º Hackathon em Controle Social: Desafio Participa DF**.
Controladoria-Geral do Distrito Federal (CGDF) — Janeiro 2026.

## 13. Contato

Para dúvidas ou sugestões sobre este projeto, entre em contato através do repositório.

---

**Hackathon Participa DF — Conectando Governo e Cidadão**
*Controladoria-Geral do Distrito Federal*
