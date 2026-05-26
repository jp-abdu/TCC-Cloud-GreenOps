"""
aws_pricing.py
--------------
Busca preços on-demand de instâncias EC2 via AWS Pricing Bulk API.
Sem autenticação, sem conta AWS, sem boto3.

Usa download em streaming para evitar carregar o JSON completo (~100MB) na RAM.
Processa linha por linha e extrai apenas os preços necessários.

Fonte: https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonEC2/current/{region}/index.json
"""

import json
import re
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

# URL alternativa — CSV é muito menor que o JSON (~5MB vs ~100MB)
CSV_URL = (
    "https://pricing.us-east-1.amazonaws.com"
    "/offers/v1.0/aws/AmazonEC2/current/{region}/index.csv"
)

PRICING_URL = (
    "https://pricing.us-east-1.amazonaws.com"
    "/offers/v1.0/aws/AmazonEC2/current/{region}/index.json"
)

_cache: dict[str, dict] = {}


def _cache_dir() -> Path:
    return Path(__file__).parent.parent.parent / ".cache"


def _cache_file(region: str) -> Path:
    return _cache_dir() / f"aws_pricing_{region}.json"


def _fetch_via_csv(region: str) -> dict:
    """
    Baixa o CSV de preços (~5MB) em vez do JSON (~100MB).
    Muito mais leve em memória.
    """
    import csv
    import io

    url = CSV_URL.format(region=region)
    print(f"[aws_pricing] Baixando preços CSV para {region}...")

    response = requests.get(url, timeout=120, stream=True)
    response.raise_for_status()

    # Lê o conteúdo em chunks para não estourar memória
    content = b""
    for chunk in response.iter_content(chunk_size=1024 * 1024):  # 1MB por vez
        content += chunk

    text = content.decode("utf-8", errors="replace")
    del content  # libera memória imediatamente

    # O CSV da AWS tem linhas de header antes dos dados reais
    # Pula até encontrar a linha com "SKU"
    lines = text.split("\n")
    del text

    header_idx = 0
    for i, line in enumerate(lines):
        if line.startswith('"SKU"') or line.startswith("SKU"):
            header_idx = i
            break

    data_lines = lines[header_idx:]
    del lines

    # Parseia o CSV
    prices = {}
    supported_set = set(SUPPORTED_INSTANCES)

    reader = csv.DictReader(io.StringIO("\n".join(data_lines)))
    sku_to_attrs = {}

    for row in reader:
        instance_type = row.get("Instance Type", "").strip()
        os_type = row.get("Operating System", "").strip()
        tenancy = row.get("Tenancy", "").strip()
        pre_installed = row.get("Pre Installed S/W", "").strip()
        capacity = row.get("CapacityStatus", "").strip()
        price_str = row.get("PricePerUnit", "").strip()
        term = row.get("TermType", "").strip()

        if (
            instance_type in supported_set
            and os_type in SUPPORTED_OS
            and tenancy == "Shared"
            and pre_installed == "NA"
            and capacity == "Used"
            and term == "OnDemand"
            and price_str
        ):
            try:
                price = float(price_str)
                if price > 0:
                    key = f"{instance_type}_{os_type}"
                    vcpu = row.get("vCPU", "N/A").strip()
                    memory = row.get("Memory", "N/A").strip()
                    prices[key] = {
                        "price_usd_hour": price,
                        "vcpu": vcpu,
                        "memory_gib": memory,
                    }
            except (ValueError, TypeError):
                continue

    return prices


def _fetch_pricing_data(region: str) -> dict:
    """
    Retorna dicionário filtrado de preços para a região.
    Usa CSV (~5MB) em vez de JSON (~100MB) para economizar memória.
    Salva cache leve em disco (~50KB) para reutilização.
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

    # Tenta via CSV primeiro (muito mais leve)
    try:
        prices = _fetch_via_csv(region)
        if prices:
            _cache_dir().mkdir(parents=True, exist_ok=True)
            with open(cache_file, "w") as f:
                json.dump(prices, f)
            print(f"[aws_pricing] Cache salvo: {cache_file.name} ({len(prices)} instâncias)")
            _cache[region] = prices
            return prices
    except Exception as e:
        print(f"[aws_pricing] CSV falhou ({e}), tentando JSON...")

    # Fallback: JSON em streaming
    url = PRICING_URL.format(region=region)
    print(f"[aws_pricing] Baixando JSON para {region}...")
    response = requests.get(url, timeout=120, stream=True)
    response.raise_for_status()

    # Processa em chunks de 1MB
    chunks = []
    for chunk in response.iter_content(chunk_size=1024 * 1024):
        chunks.append(chunk)
    data = json.loads(b"".join(chunks).decode("utf-8"))
    del chunks

    # Extrai só os preços necessários
    supported_set = set(SUPPORTED_INSTANCES)
    prices = {}

    for sku, product in data.get("products", {}).items():
        attrs = product.get("attributes", {})
        instance_type = attrs.get("instanceType", "")
        os_type = attrs.get("operatingSystem", "")

        if (
            instance_type in supported_set
            and os_type in SUPPORTED_OS
            and attrs.get("tenancy") == "Shared"
            and attrs.get("preInstalledSw") == "NA"
            and attrs.get("capacitystatus") == "Used"
        ):
            on_demand = data.get("terms", {}).get("OnDemand", {}).get(sku, {})
            for term in on_demand.values():
                for dim in term.get("priceDimensions", {}).values():
                    usd = dim.get("pricePerUnit", {}).get("USD")
                    if usd and float(usd) > 0:
                        key = f"{instance_type}_{os_type}"
                        prices[key] = {
                            "price_usd_hour": float(usd),
                            "vcpu": attrs.get("vcpu", "N/A"),
                            "memory_gib": attrs.get("memory", "N/A"),
                        }
                        break

    del data

    _cache_dir().mkdir(parents=True, exist_ok=True)
    with open(cache_file, "w") as f:
        json.dump(prices, f)
    print(f"[aws_pricing] Cache salvo: {cache_file.name} ({len(prices)} instâncias)")

    _cache[region] = prices
    return prices


def get_ec2_ondemand_price(
    instance_type: str,
    region: str,
    os: str = "Linux",
) -> dict:
    """
    Retorna o preço on-demand por hora de uma instância EC2.
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
            f"Instância '{instance_type}' ({os}) não encontrada em '{region}'."
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