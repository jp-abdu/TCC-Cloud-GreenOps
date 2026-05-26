"""
core/data_sources/rds_pricing.py
---------------------------------
Busca preços on-demand de instâncias RDS via AWS Pricing Bulk API.
Mesma abordagem do aws_pricing.py — HTTP GET público, sem autenticação.

Cache otimizado: salva apenas os preços das instâncias suportadas (~50KB)
em vez do JSON completo da AWS (~100MB por região).

URL: https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonRDS/current/{region}/index.json
"""

import json
import requests
from pathlib import Path

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

PRICING_URL = (
    "https://pricing.us-east-1.amazonaws.com"
    "/offers/v1.0/aws/AmazonRDS/current/{region}/index.json"
)

# Instâncias RDS suportadas pelo GreenArch
SUPPORTED_RDS_INSTANCES = [
    "db.t3.micro", "db.t3.small", "db.t3.medium", "db.t3.large",
    "db.t3.xlarge", "db.t3.2xlarge", "db.t4g.micro", "db.t4g.small",
    "db.t4g.medium", "db.t4g.large", "db.m5.large", "db.m5.xlarge",
    "db.m5.2xlarge", "db.m5.4xlarge", "db.m6g.large", "db.m6g.xlarge",
    "db.m6g.2xlarge", "db.r5.large", "db.r5.xlarge", "db.r5.2xlarge",
    "db.r6g.large", "db.r6g.xlarge",
]

SUPPORTED_ENGINES = ["MySQL", "PostgreSQL", "MariaDB"]
SUPPORTED_DEPLOYMENTS = ["Single-AZ", "Multi-AZ"]

# Consumo energético estimado para RDS (kWh/hora)
RDS_ENERGY_WATTS = {
    "db.t3.micro":    {"min_watts": 1.0,  "max_watts": 5.0},
    "db.t3.small":    {"min_watts": 1.5,  "max_watts": 8.0},
    "db.t3.medium":   {"min_watts": 2.0,  "max_watts": 12.0},
    "db.t3.large":    {"min_watts": 3.5,  "max_watts": 20.0},
    "db.t3.xlarge":   {"min_watts": 6.0,  "max_watts": 35.0},
    "db.t3.2xlarge":  {"min_watts": 10.0, "max_watts": 60.0},
    "db.t4g.micro":   {"min_watts": 0.8,  "max_watts": 4.0},
    "db.t4g.small":   {"min_watts": 1.2,  "max_watts": 6.0},
    "db.t4g.medium":  {"min_watts": 1.8,  "max_watts": 10.0},
    "db.t4g.large":   {"min_watts": 3.0,  "max_watts": 18.0},
    "db.m5.large":    {"min_watts": 3.5,  "max_watts": 18.0},
    "db.m5.xlarge":   {"min_watts": 6.0,  "max_watts": 32.0},
    "db.m5.2xlarge":  {"min_watts": 10.0, "max_watts": 56.0},
    "db.m5.4xlarge":  {"min_watts": 18.0, "max_watts": 100.0},
    "db.m6g.large":   {"min_watts": 2.8,  "max_watts": 15.0},
    "db.m6g.xlarge":  {"min_watts": 5.0,  "max_watts": 28.0},
    "db.m6g.2xlarge": {"min_watts": 9.0,  "max_watts": 50.0},
    "db.r5.large":    {"min_watts": 4.0,  "max_watts": 22.0},
    "db.r5.xlarge":   {"min_watts": 7.0,  "max_watts": 40.0},
    "db.r5.2xlarge":  {"min_watts": 12.0, "max_watts": 70.0},
    "db.r6g.large":   {"min_watts": 3.2,  "max_watts": 18.0},
    "db.r6g.xlarge":  {"min_watts": 6.0,  "max_watts": 34.0},
}

AWS_PUE = 1.2
DEFAULT_ENERGY_WATTS = {"min_watts": 5.0, "max_watts": 25.0}

_cache: dict = {}


def _cache_dir() -> Path:
    return Path(__file__).parent.parent.parent / ".cache"


def _cache_file(region: str) -> Path:
    return _cache_dir() / f"rds_pricing_{region}.json"


def _extract_prices(data: dict) -> dict:
    """
    Extrai do JSON completo apenas os preços das instâncias suportadas.
    Retorna dict: { "db.t3.medium_MySQL_Single-AZ": 0.068 }
    """
    prices = {}
    supported_set = set(SUPPORTED_RDS_INSTANCES)

    # Mapeia SKU → atributos relevantes
    sku_map = {}
    for sku, product in data.get("products", {}).items():
        attrs = product.get("attributes", {})
        instance_type = attrs.get("instanceType", "")
        engine = attrs.get("databaseEngine", "")
        deployment = attrs.get("deploymentOption", "")

        if (
            instance_type in supported_set
            and engine in SUPPORTED_ENGINES
            and deployment in SUPPORTED_DEPLOYMENTS
        ):
            sku_map[sku] = {
                "instance_type": instance_type,
                "engine": engine,
                "deployment": deployment,
            }

    # Extrai preços on-demand
    on_demand = data.get("terms", {}).get("OnDemand", {})
    for sku, info in sku_map.items():
        sku_terms = on_demand.get(sku, {})
        price = None
        for term in sku_terms.values():
            for dim in term.get("priceDimensions", {}).values():
                usd = dim.get("pricePerUnit", {}).get("USD")
                if usd is not None:
                    price = float(usd)
                    break
            if price is not None:
                break

        if price is not None:
            key = f"{info['instance_type']}_{info['engine']}_{info['deployment']}"
            prices[key] = price

    return prices


def _fetch_rds_pricing(region: str) -> dict:
    """
    Retorna dicionário filtrado de preços RDS para a região.
    Usa cache leve em disco (~50KB) em vez do JSON completo (~100MB).
    """
    if region in _cache:
        return _cache[region]

    cache_file = _cache_file(region)

    if cache_file.exists():
        print(f"[rds_pricing] Carregando cache: {cache_file.name}")
        with open(cache_file) as f:
            prices = json.load(f)
        _cache[region] = prices
        return prices

    url = PRICING_URL.format(region=region)
    print(f"[rds_pricing] Baixando preços RDS para {region}...")
    response = requests.get(url, timeout=120)
    response.raise_for_status()
    data = response.json()

    # Extrai só os preços necessários
    prices = _extract_prices(data)

    _cache_dir().mkdir(parents=True, exist_ok=True)
    with open(cache_file, "w") as f:
        json.dump(prices, f)
    print(f"[rds_pricing] Cache salvo: {cache_file.name} ({len(prices)} entradas)")

    _cache[region] = prices
    return prices


def get_rds_ondemand_price(
    instance_type: str,
    region: str,
    engine: str = "MySQL",
    multi_az: bool = False,
    cpu_utilization: float = 0.5,
) -> dict:
    """
    Retorna o preço on-demand e energia de uma instância RDS.

    Parâmetros:
        instance_type  : ex: "db.t3.medium", "db.m5.large"
        region         : ex: "us-east-1"
        engine         : "MySQL", "PostgreSQL", "MariaDB" (padrão: MySQL)
        multi_az       : True para Multi-AZ
        cpu_utilization: 0.0 a 1.0 (padrão: 0.5)
    """
    if region not in REGION_NAMES:
        raise ValueError(f"Região '{region}' não reconhecida.")

    prices = _fetch_rds_pricing(region)
    deployment = "Multi-AZ" if multi_az else "Single-AZ"

    # Tenta a chave exata
    key = f"{instance_type}_{engine}_{deployment}"
    price_usd_hour = prices.get(key)

    # Fallback: qualquer engine disponível para essa instância e deployment
    if price_usd_hour is None:
        for k, v in prices.items():
            if k.startswith(f"{instance_type}_") and k.endswith(f"_{deployment}"):
                price_usd_hour = v
                break

    if price_usd_hour is None:
        raise ValueError(
            f"RDS '{instance_type}' ({engine}, {deployment}) não encontrado em '{region}'."
        )

    # Calcula energia
    energy_data = RDS_ENERGY_WATTS.get(instance_type, DEFAULT_ENERGY_WATTS)
    watts = energy_data["min_watts"] + cpu_utilization * (
        energy_data["max_watts"] - energy_data["min_watts"]
    )
    energy_kwh = (watts / 1000) * AWS_PUE

    return {
        "service": "rds",
        "instance_type": instance_type,
        "region": region,
        "engine": engine,
        "multi_az": multi_az,
        "cpu_utilization": cpu_utilization,
        "price_usd_hour": price_usd_hour,
        "price_usd_month": round(price_usd_hour * 730, 4),
        "energy_kwh_hour": round(energy_kwh, 6),
    }
