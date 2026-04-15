"""
core/data_sources/lambda_pricing.py
-------------------------------------
Calcula custo e consumo energetico do AWS Lambda.

Lambda nao tem arquivo de precos por regiao da mesma forma que EC2/RDS.
Os precos sao fixos globalmente com pequenas variacoes por regiao.
Usamos os precos publicos documentados pela AWS.

Preco Lambda (us-east-1, x86):
  - Requests: $0.20 por 1 milhao de requisicoes
  - Duration: $0.0000166667 por GB-segundo

Energia Lambda (Cloud Carbon Footprint methodology):
  - Lambda compartilha servidores fisicos com outros workloads
  - O CCF estima ~0.0000011 kWh por GB-segundo (incluindo PUE)
  - Fonte: https://www.cloudcarbonfootprint.org/docs/methodology/#lambda
"""

# Precos Lambda por regiao (USD por GB-segundo, on-demand x86)
# Fonte: https://aws.amazon.com/lambda/pricing/
LAMBDA_PRICE_PER_GBS = {
    "us-east-1":      0.0000166667,
    "us-east-2":      0.0000166667,
    "us-west-1":      0.0000166667,
    "us-west-2":      0.0000166667,
    "ca-central-1":   0.0000166667,
    "eu-west-1":      0.0000182570,
    "eu-west-2":      0.0000182570,
    "eu-west-3":      0.0000182570,
    "eu-central-1":   0.0000182570,
    "eu-north-1":     0.0000182570,
    "eu-south-1":     0.0000228000,
    "ap-southeast-1": 0.0000182570,
    "ap-southeast-2": 0.0000182570,
    "ap-northeast-1": 0.0000209050,
    "ap-northeast-2": 0.0000209050,
    "ap-south-1":     0.0000166667,
    "sa-east-1":      0.0000210834,
    "af-south-1":     0.0000221000,
    "me-south-1":     0.0000185000,
}

LAMBDA_PRICE_PER_REQUEST = 0.0000002  # $0.20 por 1M requests

# Energia por GB-segundo (kWh) — metodologia Cloud Carbon Footprint
# Inclui PUE medio da AWS (1.2)
LAMBDA_ENERGY_KWH_PER_GBS = 0.0000011


def get_lambda_cost(
    region: str,
    invocations_per_month: int,
    avg_duration_ms: float,
    memory_mb: int = 512,
    architecture: str = "x86",
) -> dict:
    """
    Calcula custo e energia do Lambda para um workload mensal.

    Parametros:
        region               : ex: "us-east-1"
        invocations_per_month: numero de invocacoes por mes
        avg_duration_ms      : duracao media de cada invocacao em ms
        memory_mb            : memoria alocada em MB (padrao: 512)
        architecture         : "x86" ou "arm" (arm e 20% mais barato)

    Retorna dict com custo, energia e SCI parcial.
    """
    price_per_gbs = LAMBDA_PRICE_PER_GBS.get(region, 0.0000166667)

    # Graviton2 (arm) e 20% mais barato por GB-segundo
    if architecture == "arm":
        price_per_gbs *= 0.80

    # GB-segundos = invocacoes x (duracao_s) x (memoria_GB)
    duration_s = avg_duration_ms / 1000
    memory_gb  = memory_mb / 1024
    total_gbs  = invocations_per_month * duration_s * memory_gb

    # Custo
    request_cost  = invocations_per_month * LAMBDA_PRICE_PER_REQUEST
    duration_cost = total_gbs * price_per_gbs
    total_cost    = request_cost + duration_cost

    # Energia (kWh/mes)
    energy_kwh_month = total_gbs * LAMBDA_ENERGY_KWH_PER_GBS

    # Energia por hora equivalente (para consistencia com EC2/RDS)
    energy_kwh_hour = energy_kwh_month / 730

    return {
        "service": "lambda",
        "region": region,
        "invocations_per_month": invocations_per_month,
        "avg_duration_ms": avg_duration_ms,
        "memory_mb": memory_mb,
        "architecture": architecture,
        "total_gb_seconds": round(total_gbs, 2),
        "price_usd_month": round(total_cost, 4),
        "price_usd_hour": round(total_cost / 730, 6),
        "energy_kwh_month": round(energy_kwh_month, 8),
        "energy_kwh_hour": round(energy_kwh_hour, 8),
    }
