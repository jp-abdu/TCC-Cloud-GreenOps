"""
core/data_sources/rds_pricing.py
---------------------------------
Busca precos on-demand de instancias RDS via AWS Pricing Bulk API.
Mesma abordagem do aws_pricing.py — HTTP GET publico, sem autenticacao.

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

# Consumo energetico estimado para RDS (kWh/hora)
# Baseado em dados do Cloud Carbon Footprint para RDS
# RDS tem overhead adicional do Multi-AZ e storage I/O
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


def _fetch_rds_pricing(region: str) -> dict:
    if region in _cache:
        return _cache[region]

    cache_dir = Path(__file__).parent.parent.parent / ".cache"
    cache_file = cache_dir / f"rds_pricing_{region}.json"

    if cache_file.exists():
        print(f"[rds_pricing] Carregando cache: {cache_file.name}")
        with open(cache_file) as f:
            data = json.load(f)
        _cache[region] = data
        return data

    url = PRICING_URL.format(region=region)
    print(f"[rds_pricing] Baixando precos RDS para {region}...")
    response = requests.get(url, timeout=60)
    response.raise_for_status()
    data = response.json()

    cache_dir.mkdir(parents=True, exist_ok=True)
    with open(cache_file, "w") as f:
        json.dump(data, f)
    print(f"[rds_pricing] Cache salvo: {cache_file.name}")

    _cache[region] = data
    return data


def get_rds_ondemand_price(
    instance_type: str,
    region: str,
    engine: str = "MySQL",
    multi_az: bool = False,
    cpu_utilization: float = 0.5,
) -> dict:
    """
    Retorna o preco on-demand e energia de uma instancia RDS.

    Parametros:
        instance_type  : ex: "db.t3.medium", "db.m5.large"
        region         : ex: "us-east-1"
        engine         : "MySQL", "PostgreSQL", "MariaDB" (padrao: MySQL)
        multi_az       : True para Multi-AZ (dobra o preco)
        cpu_utilization: 0.0 a 1.0 (padrao: 0.5)

    Retorna dict com preco, energia e SCI parcial.
    """
    if region not in REGION_NAMES:
        raise ValueError(f"Regiao '{region}' nao reconhecida.")

    data = _fetch_rds_pricing(region)

    deployment = "Multi-AZ" if multi_az else "Single-AZ"

    target_sku = None
    for sku, product in data.get("products", {}).items():
        attrs = product.get("attributes", {})
        if (
            attrs.get("instanceType") == instance_type
            and attrs.get("databaseEngine") == engine
            and attrs.get("deploymentOption") == deployment
        ):
            target_sku = sku
            break

    # Fallback: tenta sem filtro de engine
    if target_sku is None:
        for sku, product in data.get("products", {}).items():
            attrs = product.get("attributes", {})
            if (
                attrs.get("instanceType") == instance_type
                and attrs.get("deploymentOption") == deployment
            ):
                target_sku = sku
                break

    if target_sku is None:
        raise ValueError(
            f"RDS '{instance_type}' ({engine}, {deployment}) nao encontrado em '{region}'."
        )

    on_demand = data.get("terms", {}).get("OnDemand", {})
    sku_terms = on_demand.get(target_sku, {})
    price_usd_hour = None

    for term in sku_terms.values():
        for dim in term.get("priceDimensions", {}).values():
            usd = dim.get("pricePerUnit", {}).get("USD")
            if usd is not None:
                price_usd_hour = float(usd)
                break
        if price_usd_hour is not None:
            break

    if price_usd_hour is None:
        raise ValueError(f"Preco nao encontrado para {instance_type} em {region}.")

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
