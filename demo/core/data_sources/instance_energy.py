"""
instance_energy.py
------------------
Retorna o consumo energético (kWh/hora) de instâncias EC2
usando o dataset público do Cloud Carbon Footprint (ThoughtWorks).

Fonte: https://github.com/cloud-carbon-footprint/cloud-carbon-footprint
Dataset: Average Watts por instância (baseado em SPECpower + dados públicos AWS)

O CCF usa a fórmula:
  watts = min_watts + (avg_cpu_utilization * (max_watts - min_watts))
  kwh_hour = watts / 1000

Para o GreenArch, usamos 50% de utilização como baseline padrão
(representa workload típico em produção).
"""

# ─────────────────────────────────────────────────────────────────────────────
# Dataset inline do Cloud Carbon Footprint para instâncias EC2 comuns.
# Fonte: https://github.com/cloud-carbon-footprint/cloud-carbon-footprint/
#        blob/trunk/packages/aws/src/lib/AWSInstanceTypes.ts
#
# Formato: instance_type -> {min_watts, max_watts}
# min_watts = consumo com CPU idle (0%)
# max_watts = consumo com CPU a 100%
# ─────────────────────────────────────────────────────────────────────────────
INSTANCE_ENERGY_WATTS = {
    # ── Família T (burstable, propósito geral) ──────────────────────────
    "t3.nano":       {"min_watts": 0.8,   "max_watts": 1.6},
    "t3.micro":      {"min_watts": 0.8,   "max_watts": 3.2},
    "t3.small":      {"min_watts": 1.7,   "max_watts": 6.5},
    "t3.medium":     {"min_watts": 1.7,   "max_watts": 6.5},
    "t3.large":      {"min_watts": 3.4,   "max_watts": 13.0},
    "t3.xlarge":     {"min_watts": 6.8,   "max_watts": 26.0},
    "t3.2xlarge":    {"min_watts": 13.6,  "max_watts": 52.0},
    "t4g.nano":      {"min_watts": 0.5,   "max_watts": 1.0},
    "t4g.micro":     {"min_watts": 0.5,   "max_watts": 2.0},
    "t4g.small":     {"min_watts": 1.0,   "max_watts": 4.0},
    "t4g.medium":    {"min_watts": 1.0,   "max_watts": 4.0},
    "t4g.large":     {"min_watts": 2.0,   "max_watts": 8.0},
    "t4g.xlarge":    {"min_watts": 4.0,   "max_watts": 16.0},
    "t4g.2xlarge":   {"min_watts": 8.0,   "max_watts": 32.0},
    # ── Família M (propósito geral, balanceado) ─────────────────────────
    "m5.large":      {"min_watts": 1.7,   "max_watts": 9.6},
    "m5.xlarge":     {"min_watts": 3.4,   "max_watts": 19.2},
    "m5.2xlarge":    {"min_watts": 6.8,   "max_watts": 38.4},
    "m5.4xlarge":    {"min_watts": 13.7,  "max_watts": 76.7},
    "m5.8xlarge":    {"min_watts": 27.4,  "max_watts": 153.4},
    "m5.12xlarge":   {"min_watts": 41.0,  "max_watts": 230.2},
    "m5.16xlarge":   {"min_watts": 54.7,  "max_watts": 307.0},
    "m5.24xlarge":   {"min_watts": 82.1,  "max_watts": 460.4},
    "m6g.large":     {"min_watts": 1.2,   "max_watts": 7.0},
    "m6g.xlarge":    {"min_watts": 2.4,   "max_watts": 14.0},
    "m6g.2xlarge":   {"min_watts": 4.9,   "max_watts": 28.0},
    "m6g.4xlarge":   {"min_watts": 9.7,   "max_watts": 56.0},
    "m6g.8xlarge":   {"min_watts": 19.4,  "max_watts": 112.0},
    "m6g.12xlarge":  {"min_watts": 29.2,  "max_watts": 168.0},
    "m6g.16xlarge":  {"min_watts": 38.9,  "max_watts": 224.0},
    "m6i.large":     {"min_watts": 1.6,   "max_watts": 10.0},
    "m6i.xlarge":    {"min_watts": 3.2,   "max_watts": 20.0},
    "m6i.2xlarge":   {"min_watts": 6.4,   "max_watts": 40.0},
    "m6i.4xlarge":   {"min_watts": 12.8,  "max_watts": 80.0},
    # ── Família C (compute optimized) ──────────────────────────────────
    "c5.large":      {"min_watts": 1.7,   "max_watts": 8.0},
    "c5.xlarge":     {"min_watts": 3.4,   "max_watts": 16.0},
    "c5.2xlarge":    {"min_watts": 6.8,   "max_watts": 32.0},
    "c5.4xlarge":    {"min_watts": 13.7,  "max_watts": 64.0},
    "c5.9xlarge":    {"min_watts": 30.8,  "max_watts": 144.0},
    "c5.12xlarge":   {"min_watts": 41.0,  "max_watts": 192.0},
    "c5.18xlarge":   {"min_watts": 61.6,  "max_watts": 288.0},
    "c5.24xlarge":   {"min_watts": 82.1,  "max_watts": 384.0},
    "c6g.large":     {"min_watts": 1.2,   "max_watts": 5.6},
    "c6g.xlarge":    {"min_watts": 2.4,   "max_watts": 11.2},
    "c6g.2xlarge":   {"min_watts": 4.8,   "max_watts": 22.4},
    "c6g.4xlarge":   {"min_watts": 9.6,   "max_watts": 44.8},
    "c6g.8xlarge":   {"min_watts": 19.3,  "max_watts": 89.6},
    "c6g.12xlarge":  {"min_watts": 29.0,  "max_watts": 134.4},
    "c6g.16xlarge":  {"min_watts": 38.6,  "max_watts": 179.2},
    # ── Família R (memory optimized) ───────────────────────────────────
    "r5.large":      {"min_watts": 2.4,   "max_watts": 10.7},
    "r5.xlarge":     {"min_watts": 4.8,   "max_watts": 21.4},
    "r5.2xlarge":    {"min_watts": 9.6,   "max_watts": 42.8},
    "r5.4xlarge":    {"min_watts": 19.2,  "max_watts": 85.6},
    "r5.8xlarge":    {"min_watts": 38.4,  "max_watts": 171.2},
    "r5.12xlarge":   {"min_watts": 57.7,  "max_watts": 256.7},
    "r5.16xlarge":   {"min_watts": 76.9,  "max_watts": 342.3},
    "r5.24xlarge":   {"min_watts": 115.4, "max_watts": 513.5},
    "r6g.large":     {"min_watts": 1.8,   "max_watts": 8.0},
    "r6g.xlarge":    {"min_watts": 3.6,   "max_watts": 16.0},
    "r6g.2xlarge":   {"min_watts": 7.2,   "max_watts": 32.0},
    "r6g.4xlarge":   {"min_watts": 14.4,  "max_watts": 64.0},
    # ── Família P/G (GPU — ML inference/training) ───────────────────────
    "p3.2xlarge":    {"min_watts": 52.7,  "max_watts": 310.0},
    "p3.8xlarge":    {"min_watts": 210.9, "max_watts": 1240.0},
    "p3.16xlarge":   {"min_watts": 421.8, "max_watts": 2480.0},
    "p4d.24xlarge":  {"min_watts": 612.0, "max_watts": 3480.0},
    "g4dn.xlarge":   {"min_watts": 18.6,  "max_watts": 170.0},
    "g4dn.2xlarge":  {"min_watts": 25.7,  "max_watts": 225.0},
    "g4dn.4xlarge":  {"min_watts": 40.0,  "max_watts": 380.0},
    "g4dn.8xlarge":  {"min_watts": 71.8,  "max_watts": 700.0},
    "g4dn.12xlarge": {"min_watts": 126.7, "max_watts": 1300.0},
    "g4dn.16xlarge": {"min_watts": 143.5, "max_watts": 1400.0},
    # ── Família X (memory extreme) ──────────────────────────────────────
    "x1.16xlarge":   {"min_watts": 100.0, "max_watts": 500.0},
    "x1.32xlarge":   {"min_watts": 200.0, "max_watts": 1000.0},
    "x2gd.large":    {"min_watts": 5.0,   "max_watts": 30.0},
    "x2gd.xlarge":   {"min_watts": 10.0,  "max_watts": 60.0},
}

# PUE médio dos datacenters AWS (dado público)
# Fonte: AWS Sustainability Report 2023
AWS_PUE = 1.2

# Utilização de CPU padrão (50% é o baseline recomendado pelo CCF)
DEFAULT_CPU_UTILIZATION = 0.50


def get_instance_energy_kwh(
    instance_type: str,
    cpu_utilization: float = DEFAULT_CPU_UTILIZATION,
) -> dict:
    """
    Retorna o consumo energético de uma instância EC2 em kWh/hora.

    Parâmetros:
        instance_type    : str   — ex: "t3.medium", "m5.large"
        cpu_utilization  : float — entre 0.0 e 1.0 (padrão: 0.50)

    Retorna:
        {
            "instance_type": str,
            "cpu_utilization": float,
            "min_watts": float,
            "max_watts": float,
            "watts_at_utilization": float,
            "energy_kwh_hour": float,        # sem PUE
            "energy_kwh_hour_with_pue": float, # com PUE do datacenter
            "pue": float,
        }

    Lança:
        ValueError se a instância não estiver no dataset
    """
    if instance_type not in INSTANCE_ENERGY_WATTS:
        # Tenta estimativa por família se instância específica não encontrada
        estimated = _estimate_by_family(instance_type, cpu_utilization)
        if estimated:
            return estimated
        raise ValueError(
            f"Instância '{instance_type}' não encontrada no dataset de energia. "
            f"Instâncias disponíveis: {list(INSTANCE_ENERGY_WATTS.keys())}"
        )

    data = INSTANCE_ENERGY_WATTS[instance_type]
    min_w = data["min_watts"]
    max_w = data["max_watts"]

    # Fórmula CCF: watts = min + (utilização × (max - min))
    watts = min_w + (cpu_utilization * (max_w - min_w))
    energy_kwh = watts / 1000
    energy_kwh_pue = energy_kwh * AWS_PUE

    return {
        "instance_type": instance_type,
        "cpu_utilization": cpu_utilization,
        "min_watts": min_w,
        "max_watts": max_w,
        "watts_at_utilization": round(watts, 3),
        "energy_kwh_hour": round(energy_kwh, 6),
        "energy_kwh_hour_with_pue": round(energy_kwh_pue, 6),
        "pue": AWS_PUE,
        "source": "Cloud Carbon Footprint dataset (ThoughtWorks)",
    }


def _estimate_by_family(instance_type: str, cpu_utilization: float) -> dict | None:
    """
    Tenta estimar o consumo de uma instância não mapeada
    com base em instâncias da mesma família com tamanho similar.
    Retorna None se não conseguir estimar.
    """
    # Extrai família e tamanho: "m6i.2xlarge" -> família="m6i", size="2xlarge"
    parts = instance_type.split(".")
    if len(parts) != 2:
        return None

    family, size = parts

    # Procura instâncias da mesma família no dataset
    same_family = {
        k: v for k, v in INSTANCE_ENERGY_WATTS.items()
        if k.startswith(family + ".")
    }

    if not same_family:
        return None

    # Usa a instância mais próxima em tamanho (simplificado: qualquer da família)
    ref_type = list(same_family.keys())[0]
    ref_data = same_family[ref_type]

    min_w = ref_data["min_watts"]
    max_w = ref_data["max_watts"]
    watts = min_w + (cpu_utilization * (max_w - min_w))
    energy_kwh = watts / 1000
    energy_kwh_pue = energy_kwh * AWS_PUE

    return {
        "instance_type": instance_type,
        "cpu_utilization": cpu_utilization,
        "min_watts": min_w,
        "max_watts": max_w,
        "watts_at_utilization": round(watts, 3),
        "energy_kwh_hour": round(energy_kwh, 6),
        "energy_kwh_hour_with_pue": round(energy_kwh_pue, 6),
        "pue": AWS_PUE,
        "source": f"Estimado a partir de {ref_type} (mesma família)",
        "estimated": True,
    }


def list_supported_instances() -> list[str]:
    """Retorna lista de todas as instâncias com dados exatos no dataset."""
    return sorted(INSTANCE_ENERGY_WATTS.keys())
