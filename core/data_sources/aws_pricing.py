"""
aws_pricing.py
--------------
Busca preços on-demand de instâncias EC2 via AWS Pricing Bulk API.
Sem autenticação, sem conta AWS, sem boto3.

Fonte: https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonEC2/current/{region}/index.json
Documentação: https://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/price-changes.html

Cache otimizado: em vez de salvar o JSON completo da AWS (~100MB por região),
salva apenas os preços das instâncias suportadas pelo GreenArch (~50KB por região).
"""

import json
import requests
from pathlib import Path

# ─────────────────────────────────────────────────────────────────────────────
# Mapeamento: região AWS → nome por extenso
# ─────────────────────────────────────────────────────────────────────────────
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

# Instâncias suportadas pelo GreenArch (todas as que estão no instance_energy.py)
SUPPORTED_INSTANCES = [
    'c5.12xlarge', 'c5.18xlarge', 'c5.24xlarge', 'c5.2xlarge', 'c5.4xlarge',
    'c5.9xlarge', 'c5.large', 'c5.xlarge', 'c6g.12xlarge', 'c6g.16xlarge',
    'c6g.2xlarge', 'c6g.4xlarge', 'c6g.8xlarge', 'c6g.large', 'c6g.xlarge',
    'g4dn.12xlarge', 'g4dn.16xlarge', 'g4dn.2xlarge', 'g4dn.4xlarge',
    'g4dn.8xlarge', 'g4dn.xlarge', 'm5.12xlarge', 'm5.16xlarge', 'm5.24xlarge',
    'm5.2xlarge', 'm5.4xlarge', 'm5.8xlarge', 'm5.large', 'm5.xlarge',
    'm6g.12xlarge', 'm6g.16xlarge', 'm6g.2xlarge', 'm6g.4xlarge', 'm6g.8xlarge',
    'm6g.large', 'm6g.xlarge', 'm6i.2xlarge', 'm6i.4xlarge', 'm6i.large',
    'm6i.xlarge', 'p3.16xlarge', 'p3.2xlarge', 'p3.8xlarge', 'p4d.24xlarge',
    'r5.12xlarge', 'r5.16xlarge', 'r5.24xlarge', 'r5.2xlarge', 'r5.4xlarge',
    'r5.8xlarge', 'r5.large', 'r5.xlarge', 'r6g.2xlarge', 'r6g.4xlarge',
    'r6g.large', 'r6g.xlarge', 't3.2xlarge', 't3.large', 't3.medium',
    't3.micro', 't3.nano', 't3.small', 't3.xlarge', 't4g.2xlarge', 't4g.large',
    't4g.medium', 't4g.micro', 't4g.nano', 't4g.small', 't4g.xlarge',
    'x1.16xlarge', 'x1.32xlarge', 'x2gd.large', 'x2gd.xlarge',
]

SUPPORTED_OS = ["Linux", "Windows"]

PRICING_URL = (
    "https://pricing.us-east-1.amazonaws.com"
    "/offers/v1.0/aws/AmazonEC2/current/{region}/index.json"
)

# Cache em memória para a sessão atual
_cache: dict[str, dict] = {}


def _cache_dir() -> Path:
    return Path(__file__).parent.parent.parent / ".cache"


def _cache_file(region: str) -> Path:
    return _cache_dir() / f"aws_pricing_{region}.json"


def _extract_prices(data: dict) -> dict:
    """
    Extrai do JSON completo da AWS apenas os preços das instâncias suportadas.
    Retorna dict: { "t3.medium_Linux": {"price_usd_hour": 0.0416, "vcpu": "2", "memory_gib": "4 GiB"} }
    """
    prices = {}
    supported_set = set(SUPPORTED_INSTANCES)

    # Passo 1: mapeia SKU → (instance_type, os, vcpu, memory)
    sku_map = {}
    for sku, product in data.get("products", {}).items():
        attrs = product.get("attributes", {})
        instance_type = attrs.get("instanceType", "")
        os = attrs.get("operatingSystem", "")

        if (
            instance_type in supported_set
            and os in SUPPORTED_OS
            and attrs.get("tenancy") == "Shared"
            and attrs.get("preInstalledSw") == "NA"
            and attrs.get("capacitystatus") == "Used"
        ):
            sku_map[sku] = {
                "instance_type": instance_type,
                "os": os,
                "vcpu": attrs.get("vcpu", "N/A"),
                "memory_gib": attrs.get("memory", "N/A"),
            }

    # Passo 2: extrai preços on-demand para cada SKU encontrado
    on_demand = data.get("terms", {}).get("OnDemand", {})
    for sku, info in sku_map.items():
        sku_terms = on_demand.get(sku, {})
        price = None
        for term_value in sku_terms.values():
            for dim in term_value.get("priceDimensions", {}).values():
                usd = dim.get("pricePerUnit", {}).get("USD")
                if usd is not None:
                    price = float(usd)
                    break
            if price is not None:
                break

        if price is not None:
            key = f"{info['instance_type']}_{info['os']}"
            prices[key] = {
                "price_usd_hour": price,
                "vcpu": info["vcpu"],
                "memory_gib": info["memory_gib"],
            }

    return prices


def _fetch_pricing_data(region: str) -> dict:
    """
    Retorna dicionário filtrado de preços para a região.
    Usa cache leve em disco (~50KB) em vez do JSON completo (~100MB).
    """
    if region in _cache:
        return _cache[region]

    cache_file = _cache_file(region)

    if cache_file.exists():
        print(f"[aws_pricing] Carregando cache de disco: {cache_file.name}")
        with open(cache_file) as f:
            prices = json.load(f)
        _cache[region] = prices
        return prices

    # Baixa o JSON completo da AWS
    url = PRICING_URL.format(region=region)
    print(f"[aws_pricing] Baixando preços para região {region}...")
    print(f"[aws_pricing] URL: {url}")

    response = requests.get(url, timeout=120)
    response.raise_for_status()
    data = response.json()

    # Extrai só os preços necessários
    prices = _extract_prices(data)

    # Salva cache leve em disco
    _cache_dir().mkdir(parents=True, exist_ok=True)
    with open(cache_file, "w") as f:
        json.dump(prices, f)
    print(f"[aws_pricing] Cache salvo em: {cache_file.name} ({len(prices)} instâncias)")

    _cache[region] = prices
    return prices


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
            "price_usd_month": float,
            "vcpu": str,
            "memory_gib": str,
        }
    """
    if region not in REGION_NAMES:
        raise ValueError(
            f"Região '{region}' não reconhecida. "
            f"Regiões suportadas: {list(REGION_NAMES.keys())}"
        )

    prices = _fetch_pricing_data(region)
    key = f"{instance_type}_{os}"

    if key not in prices:
        raise ValueError(
            f"Instância '{instance_type}' ({os}) não encontrada em '{region}'. "
            "Verifique se o tipo de instância existe nessa região."
        )

    info = prices[key]
    return {
        "instance_type": instance_type,
        "region": region,
        "region_name": REGION_NAMES[region],
        "os": os,
        "price_usd_hour": info["price_usd_hour"],
        "price_usd_month": round(info["price_usd_hour"] * 730, 4),
        "vcpu": info["vcpu"],
        "memory_gib": info["memory_gib"],
    }