# VIGIL — Resumo Executivo

**Autor:** Iúri Leão de Almeida
**Telefone:** (61) 99645-1390
**E-mail:** iurileao@gmail.com

**1º Hackathon em Controle Social: Desafio Participa DF**
**Categoria:** Acesso à Informação
**Repositório:** https://github.com/iurileao-hub/vigil-pii-detector

---

## Objetivo

O VIGIL é uma solução automatizada para identificar pedidos de acesso à informação que contenham dados pessoais (PII) e que, portanto, deveriam ser classificados como não públicos.

---

## Tipos de PII Detectados

Conforme item 2.2.I do Edital nº 10/2025:

| Tipo | Descrição |
|------|-----------|
| **CPF** | Cadastro de Pessoa Física |
| **RG** | Registro Geral |
| **Nome** | Nome completo de pessoa física |
| **Telefone** | Números de telefone brasileiros |
| **E-mail** | Endereços de correio eletrônico |

---

## Arquitetura da Solução

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
│ • Filtros anti-FP: SEI, NUP, CDA, CNH        │
└──────────────────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────────┐
│ Camada 3: NER (NOMES)                        │
│ • BERTimbau NER (HuggingFace)                │
│ • 130+ exclusões de nomes institucionais     │
└──────────────────────────────────────────────┘
       │
       ▼
   Resultado: contem_pii = True/False
```

---

## Resultados na Amostra Oficial

Testes realizados com os 99 registros da amostra oficial:

| Métrica | Valor |
|---------|-------|
| **Registros analisados** | 99 |
| **Verdadeiros Positivos (VP)** | 29 |
| **Falsos Positivos (FP)** | 1 |
| **Verdadeiros Negativos (VN)** | 69 |
| **Falsos Negativos (FN)** | 0 |
| **Precisão** | 96,7% |
| **Recall (Sensibilidade)** | 100% |
| **F1-Score (P1)** | 0,983 |

---

## Diferencial: Sistema de Revisão Humana

O VIGIL inclui um módulo inovador que identifica automaticamente casos ambíguos para revisão manual:

- **Contextos detectados:** Artístico, acadêmico, jurídico, servidor público
- **Priorização automática:** Alta, média e baixa prioridade
- **Fundamentação legal:** Baseado na LGPD (Art. 4º, II e Art. 7º, § 4º)

---

## Instalação Rápida

```bash
# 1. Clone o repositório
git clone https://github.com/iurileao-hub/vigil-pii-detector.git
cd vigil-pii-detector

# 2. Crie e ative o ambiente virtual
python3 -m venv venv
source venv/bin/activate  # Linux/macOS

# 3. Instale as dependências
pip install -r requirements.txt

# 4. Execute
python main.py --input analise/AMOSTRA_e-SIC.xlsx --output resultado.csv
```

---

## Tecnologias Utilizadas

| Componente | Tecnologia |
|------------|------------|
| Linguagem | Python 3.9+ |
| NER | BERTimbau (HuggingFace) |
| ML Framework | Transformers |
| Processamento | pandas, regex |

---

## Uso de Inteligência Artificial

Conforme item 13.9 do Edital nº 10/2025:

- **Ferramenta:** Claude Code (Anthropic)
- **Modelo NER:** BERTimbau NER (pierreguillou/ner-bert-base-cased-pt-lenerbr)
- **Atividades assistidas:** Análise exploratória, geração de regex, implementação, testes e documentação
- **Responsabilidade:** Código integralmente revisado e compreendido pela equipe

---

## Estrutura do Projeto

```
vigil-pii-detector/
├── main.py                   # CLI principal
├── requirements.txt          # Dependências
├── README.md                 # Documentação completa
├── src/                      # Código-fonte
│   ├── constants.py         # Constantes centralizadas
│   ├── detector.py          # Classe PIIDetector
│   ├── exclusions.py        # Nomes institucionais
│   ├── human_review.py      # Revisão humana
│   ├── patterns.py          # Padrões regex
│   ├── preprocessor.py      # Normalização
│   └── utils.py             # Utilitários compartilhados
├── tests/                    # 173 testes automatizados
├── scripts/                  # Scripts de avaliação
├── analise/                  # Análise de acurácia
└── docs/                     # Documentação adicional
```

---

## Licença

Projeto desenvolvido para o **1º Hackathon em Controle Social: Desafio Participa DF**.

Controladoria-Geral do Distrito Federal (CGDF) — Janeiro 2026.
