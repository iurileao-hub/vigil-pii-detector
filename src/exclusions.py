# -*- coding: utf-8 -*-
"""
Lista de nomes institucionais a serem excluídos da detecção de PII.

Evita falsos positivos quando o NER detecta nomes de:
- Órgãos públicos do GDF
- Regiões administrativas e lugares do DF
- Títulos e tratamentos formais
- Termos técnicos e jurídicos
- Universidades e instituições de ensino

Estes termos podem ser detectados como "PESSOA" pelo NER,
mas não representam dados pessoais de cidadãos.
"""

# Lista de nomes institucionais que NÃO são PII
INSTITUTIONAL_NAMES = [
    # =========================================================================
    # ÓRGÃOS DO GOVERNO DO DISTRITO FEDERAL
    # =========================================================================
    'Distrito Federal',
    'Governo do Distrito Federal',
    'GDF',
    'Controladoria Geral',
    'Controladoria-Geral',
    'CGDF',
    'Secretaria de Estado',
    'Secretaria de Governo',
    'Secretaria de Fazenda',
    'Secretaria de Saúde',
    'Secretaria de Educação',
    'Secretaria de Segurança',
    'Polícia Civil',
    'PCDF',
    'Polícia Militar',
    'PMDF',
    'Corpo de Bombeiros',
    'CBMDF',
    'Tribunal de Contas',
    'TCDF',
    'Ministério Público',
    'MPDFT',
    'Defensoria Pública',
    'Câmara Legislativa',
    'CLDF',
    'Detran',
    'DETRAN-DF',
    'BRB',
    'Banco de Brasília',
    'CEB',
    'Caesb',
    'Novacap',
    'Terracap',
    'Metrô-DF',

    # =========================================================================
    # REGIÕES ADMINISTRATIVAS DO DF
    # =========================================================================
    'Plano Piloto',
    'Asa Norte',
    'Asa Sul',
    'Lago Norte',
    'Lago Sul',
    'Sudoeste',
    'Octogonal',
    'Cruzeiro',
    'Candangolândia',
    'Núcleo Bandeirante',
    'Riacho Fundo',
    'Park Way',
    'Águas Claras',
    'Taguatinga',
    'Ceilândia',
    'Samambaia',
    'Gama',
    'Santa Maria',
    'Recanto das Emas',
    'Sobradinho',
    'Planaltina',
    'Paranoá',
    'São Sebastião',
    'Jardim Botânico',
    'Itapoã',
    'SIA',
    'SCIA',
    'Estrutural',
    'Varjão',
    'Fercal',
    'Sol Nascente',
    'Pôr do Sol',
    'Arniqueira',
    'Vicente Pires',
    'Brazlândia',

    # =========================================================================
    # LUGARES E REFERÊNCIAS GEOGRÁFICAS
    # =========================================================================
    'Planaltina de Goiás',
    'Formosa',
    'Valparaíso',
    'Novo Gama',
    'Cidade Ocidental',
    'Luziânia',
    'Entorno do DF',
    'Esplanada dos Ministérios',
    'Praça dos Três Poderes',
    'Congresso Nacional',
    'Palácio do Planalto',
    'Palácio da Alvorada',
    'Supremo Tribunal Federal',
    'STF',
    'Superior Tribunal de Justiça',
    'STJ',

    # =========================================================================
    # TÍTULOS E TRATAMENTOS FORMAIS
    # =========================================================================
    'Vossa Senhoria',
    'Vossa Excelência',
    'Vossas Senhorias',
    'Ilustríssimo',
    'Ilustríssima',
    'Excelentíssimo',
    'Excelentíssima',
    'Meritíssimo',
    'Meritíssima',
    'Prezados Senhores',
    'Prezadas Senhoras',
    'Senhor Secretário',
    'Senhora Secretária',
    'Senhor Governador',
    'Senhora Governadora',
    'Senhor Presidente',
    'Senhora Presidente',
    'Senhor Diretor',
    'Senhora Diretora',
    'Ilustres Servidores',

    # =========================================================================
    # TERMOS TÉCNICOS E JURÍDICOS
    # =========================================================================
    'Constituição Federal',
    'Constituição da República',
    'Lei Orgânica',
    'Lei de Acesso',
    'Lei de Acesso à Informação',
    'LAI',
    'Lei Maria da Penha',
    'Lei Complementar',
    'Código Civil',
    'Código Penal',
    'Código de Processo',
    'Programa de Integridade',
    'Gestão de Riscos',
    'Controle Interno',
    'Ouvidoria Geral',
    'Corregedoria',
    'Procuradoria Geral',
    'Advocacia Geral',

    # =========================================================================
    # UNIVERSIDADES E INSTITUIÇÕES DE ENSINO
    # =========================================================================
    'Universidade de Brasília',
    'UnB',
    'Universidade Católica',
    'UCB',
    'Centro Universitário',
    'UniCEUB',
    'IESB',
    'Instituto Federal',
    'IFB',
    'Escola de Governo',

    # =========================================================================
    # OUTROS TERMOS COMUNS
    # =========================================================================
    'Sistema Eletrônico',
    'SEI',
    'e-SIC',
    'Fala.BR',
    'Portal da Transparência',
    'Diário Oficial',
    'DODF',
    'Nota Fiscal',
    'Pregão Eletrônico',
    'Tomada de Preços',
    'Concorrência Pública',
]

# Converter para lowercase para comparação case-insensitive
INSTITUTIONAL_NAMES_LOWER = frozenset(name.lower() for name in INSTITUTIONAL_NAMES)


def is_institutional_name(name: str) -> bool:
    """
    Verifica se um nome é institucional (não é PII).

    Verifica correspondência exata e se o nome contém um termo institucional.
    NÃO verifica se o nome é substring de um termo institucional, pois isso
    causaria falsos negativos (ex: "Ana" contido em "Candangolândia").

    Args:
        name: Nome a ser verificado

    Returns:
        True se for nome institucional, False caso contrário
    """
    if not name:
        return False

    name_lower = name.lower().strip()

    # Verificar correspondência exata (O(1) com frozenset)
    if name_lower in INSTITUTIONAL_NAMES_LOWER:
        return True

    # Verificar se o nome CONTÉM algum termo institucional
    # (ex: "Secretaria de Estado de Saúde" contém "Secretaria de Estado")
    # NÃO verificar o inverso (name_lower in institutional) pois causa
    # falsos negativos com nomes curtos como "Ana", "Gama", etc.
    for institutional in INSTITUTIONAL_NAMES_LOWER:
        if institutional in name_lower:
            return True

    return False
