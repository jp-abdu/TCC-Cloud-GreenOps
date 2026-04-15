"""
aws_pricing.py
--------------
Busca preços on-demand de instâncias EC2 via AWS Pricing Bulk API.
Sem autenticação, sem conta AWS, sem boto3.

Fonte: https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonEC2/current/{region}/index.json
Documentação: https://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/price-changes.html

Estrutura do JSON da AWS:
  data["products"]  → dict de SKUs com atributos (instanceType, operatingSystem, etc.)
  data["terms"]["OnDemand"] → dict de SKUs com preços on-demand
  O offerTermCode on-demand é sempre "JRTCKXETXF"
"""

import json
import requests
from pathlib import Path

# ─────────────────────────────────────────────
# Mapeamento: região AWS → nome por extenso
# Necessário porque a AWS usa o nome por extenso no JSON de preços
# ─────────────────────────────────────────────
REGION_NAMES = {
    "us-east-1":      "US East (N. Virginia)",
    "us-east-2":      "US East (Ohio)",
    "us-west-1":      "US West (N. California)",
    "us-west-2":      "US West (Oregon)",
    "ca-central-1":   "Canada (Central)",
    "eu-west-1":      "Europe (Ireland)",
    "eu-west-2":      "Europe (London)",
    "eu-west-3":      "Europe (Paris)",
    "eu-central-1":   "Europe (Frankfurt)",
    "eu-north-1":     "Europe (Stockholm)",
    "eu-south-1":     "Europe (Milan)",
    "ap-southeast-1": "Asia Pacific (Singapore)",
    "ap-southeast-2": "Asia Pacific (Sydney)",
    "ap-northeast-1": "Asia Pacific (Tokyo)",
    "ap-northeast-2": "Asia Pacific (Seoul)",
    "ap-south-1":     "Asia Pacific (Mumbai)",
    "sa-east-1":      "South America (Sao Paulo)",
    "af-south-1":     "Africa (Cape Town)",
    "me-south-1":     "Middle East (Bahrain)",
}

# URL base da AWS Pricing Bulk API (sem autenticação)
PRICING_URL = (
    "https://pricing.us-east-1.amazonaws.com"
    "/offers/v1.0/aws/AmazonEC2/current/{region}/index.json"
)

# Cache local para evitar baixar o mesmo arquivo várias vezes
_cache: dict[str, dict] = {}


def _fetch_pricing_data(region: str) -> dict:
    """
    Baixa e faz cache do JSON de preços da AWS para uma região.
    O arquivo é grande (~50-200 MB por região), então o cache é essencial.
    """
    if region in _cache:
        return _cache[region]

    # Verifica se há cache em disco (evita re-download entre execuções)
    cache_dir = Path(__file__).parent.parent.parent / ".cache"
    cache_file = cache_dir / f"aws_pricing_{region}.json"

    if cache_file.exists():
        print(f"[aws_pricing] Carregando cache de disco: {cache_file.name}")
        with open(cache_file) as f:
            data = json.load(f)
        _cache[region] = data
        return data

    # Baixa da AWS
    url = PRICING_URL.format(region=region)
    print(f"[aws_pricing] Baixando preços para região {region}...")
    print(f"[aws_pricing] URL: {url}")

    response = requests.get(url, timeout=60)
    response.raise_for_status()
    data = response.json()

    # Salva cache em disco
    cache_dir.mkdir(parents=True, exist_ok=True)
    with open(cache_file, "w") as f:
        json.dump(data, f)
    print(f"[aws_pricing] Cache salvo em: {cache_file.name}")

    _cache[region] = data
    return data


def get_ec2_ondemand_price(
    instance_type: str,
    region: str,
    os: str = "Linux",
) -> dict:
    """
    Retorna o preço on-demand por hora de uma instância EC2.

    Parâmetros:
        instance_type : str  — ex: "t3.medium", "m5.large", "c5.2xlarge"
        region        : str  — ex: "us-east-1", "eu-north-1", "sa-east-1"
        os            : str  — "Linux" (padrão) ou "Windows"

    Retorna:
        {
            "instance_type": str,
            "region": str,
            "os": str,
            "price_usd_hour": float,
            "vcpu": str,
            "memory_gib": str,
        }

    Lança:
        ValueError se a instância não for encontrada na região
        requests.HTTPError se a URL falhar
    """
    if region not in REGION_NAMES:
        raise ValueError(
            f"Região '{region}' não reconhecida. "
            f"Regiões suportadas: {list(REGION_NAMES.keys())}"
        )

    data = _fetch_pricing_data(region)

    # ── Passo 1: encontrar o SKU correto nos produtos ──────────────────
    # Filtra por: instanceType + operatingSystem + tenancy Shared
    # + sem software pré-instalado + capacitystatus Used
    target_sku = None
    vcpu = None
    memory = None

    for sku, product in data.get("products", {}).items():
        attrs = product.get("attributes", {})

        if (
            attrs.get("instanceType") == instance_type
            and attrs.get("operatingSystem") == os
            and attrs.get("tenancy") == "Shared"
            and attrs.get("preInstalledSw") == "NA"
            and attrs.get("capacitystatus") == "Used"
        ):
            target_sku = sku
            vcpu = attrs.get("vcpu", "N/A")
            memory = attrs.get("memory", "N/A")
            break

    if target_sku is None:
        raise ValueError(
            f"Instância '{instance_type}' ({os}) não encontrada em '{region}'. "
            "Verifique se o tipo de instância existe nessa região."
        )

    # ── Passo 2: extrair o preço on-demand do SKU ─────────────────────
    # O offerTermCode on-demand é sempre "JRTCKXETXF" (documentado pela AWS)
    on_demand_terms = data.get("terms", {}).get("OnDemand", {})
    sku_terms = on_demand_terms.get(target_sku, {})

    price_usd_hour = None
    for term_key, term_value in sku_terms.items():
        price_dimensions = term_value.get("priceDimensions", {})
        for dim_key, dim in price_dimensions.items():
            usd = dim.get("pricePerUnit", {}).get("USD")
            if usd is not None:
                price_usd_hour = float(usd)
                break
        if price_usd_hour is not None:
            break

    if price_usd_hour is None:
        raise ValueError(
            f"Preço on-demand não encontrado para SKU {target_sku} "
            f"({instance_type}, {region})."
        )

    return {
        "instance_type": instance_type,
        "region": region,
        "region_name": REGION_NAMES[region],
        "os": os,
        "price_usd_hour": price_usd_hour,
        "price_usd_month": round(price_usd_hour * 730, 4),
        "vcpu": vcpu,
        "memory_gib": memory,
    }
