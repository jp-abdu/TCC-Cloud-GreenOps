"""
carbon_intensity.py
-------------------
Retorna a intensidade de carbono (gCO₂eq/kWh) das regiões AWS.

Estratégia em camadas:
  1. Tenta o Carbon Aware SDK (Green Software Foundation) — dados em tempo real
  2. Fallback: tabela estática baseada em médias anuais do Electricity Maps / IPCC
     (suficiente para benchmarks e análise pré-deploy)

A tabela estática é adequada para o GreenArch porque:
  - O objetivo é comparar regiões entre si (análise relativa)
  - Os valores médios anuais são estáveis o suficiente para decisões arquiteturais
  - O Carbon Aware SDK pode ser integrado opcionalmente para dados em tempo real

Fontes da tabela estática:
  - Electricity Maps (médias anuais 2023)
  - EPA eGRID 2023 (regiões norte-americanas)
  - IEA 2023 (regiões internacionais)
  - AWS Customer Carbon Footprint Tool (valores declarados pela AWS)
"""

# ─────────────────────────────────────────────────────────────────────────────
# Intensidade de carbono média anual por região AWS (gCO₂eq/kWh)
# Valores baseados em médias de 2022-2023
# ─────────────────────────────────────────────────────────────────────────────
CARBON_INTENSITY_STATIC = {
    # ── América do Norte ─────────────────────────────────────────────────
    "us-east-1":      391.0,  # N. Virginia — grid PJM, alta participação carvão/gás
    "us-east-2":      436.0,  # Ohio — grid AEP, alta participação carvão
    "us-west-1":      221.0,  # N. California — grid CAISO, solar + eólico
    "us-west-2":       94.0,  # Oregon — hidro dominante (Pacific Northwest)
    "ca-central-1":    35.0,  # Canadá — hidro + nuclear (~95% limpo)

    # ── Europa ───────────────────────────────────────────────────────────
    "eu-west-1":      316.0,  # Irlanda — gás dominante, crescendo em eólico
    "eu-west-2":      225.0,  # Londres — mix diversificado, nuclear + eólico
    "eu-west-3":       67.0,  # Paris — nuclear dominante (~70%)
    "eu-central-1":   366.0,  # Frankfurt — carvão + gás, transição energética
    "eu-north-1":      13.0,  # Estocolmo — hidro + nuclear, grid mais limpo da Europa
    "eu-south-1":     234.0,  # Milão — mix gas + renovável

    # ── Ásia-Pacífico ────────────────────────────────────────────────────
    "ap-southeast-1": 408.0,  # Singapura — gás natural dominante
    "ap-southeast-2": 650.0,  # Sydney — carvão dominante (NEM grid)
    "ap-northeast-1": 506.0,  # Tóquio — gás + carvão pós-Fukushima
    "ap-northeast-2": 415.0,  # Seoul — carvão + nuclear
    "ap-south-1":     713.0,  # Mumbai — carvão dominante (grid indiano)

    # ── América do Sul ───────────────────────────────────────────────────
    "sa-east-1":       74.0,  # São Paulo — hidro dominante (~65-80%)
                               # Atenção: oscila muito em anos de seca

    # ── África e Oriente Médio ───────────────────────────────────────────
    "af-south-1":     800.0,  # Cidade do Cabo — carvão dominante (Eskom)
    "me-south-1":     499.0,  # Bahrein — gás natural
}

# Fator de eficiência de rede (overhead de transmissão)
# Fonte: Cloud Carbon Footprint methodology
NETWORK_OVERHEAD_FACTOR = 1.0  # simplificado — sem ajuste de rede nesta versão


def get_carbon_intensity(region: str) -> dict:
    """
    Retorna a intensidade de carbono de uma região AWS em gCO₂eq/kWh.

    Parâmetros:
        region : str — código da região AWS (ex: "us-east-1")

    Retorna:
        {
            "region": str,
            "carbon_intensity_gco2_kwh": float,
            "source": str,
            "note": str,
        }

    Lança:
        ValueError se a região não for reconhecida
    """
    if region not in CARBON_INTENSITY_STATIC:
        raise ValueError(
            f"Região '{region}' não encontrada na tabela de intensidade de carbono. "
            f"Regiões disponíveis: {list(CARBON_INTENSITY_STATIC.keys())}"
        )

    intensity = CARBON_INTENSITY_STATIC[region]

    return {
        "region": region,
        "carbon_intensity_gco2_kwh": intensity,
        "source": "Electricity Maps / EPA eGRID / IEA (médias anuais 2022-2023)",
        "note": "Valor médio anual — adequado para análise comparativa pré-deploy",
    }


def get_all_regions_intensity() -> dict[str, float]:
    """
    Retorna dict com intensidade de carbono de todas as regiões.
    Útil para o comparador de cenários (Módulo 2).
    """
    return dict(CARBON_INTENSITY_STATIC)


def rank_regions_by_carbon(ascending: bool = True) -> list[dict]:
    """
    Retorna regiões ordenadas por intensidade de carbono.

    Parâmetros:
        ascending : bool — True = mais limpa primeiro (padrão)

    Retorna:
        Lista de dicts com region e carbon_intensity_gco2_kwh
    """
    sorted_regions = sorted(
        CARBON_INTENSITY_STATIC.items(),
        key=lambda x: x[1],
        reverse=not ascending,
    )
    return [
        {"region": r, "carbon_intensity_gco2_kwh": v}
        for r, v in sorted_regions
    ]
