"""
sci_calculator.py
-----------------
Motor de cálculo SCI (Software Carbon Intensity) — Módulo 1 do GreenArch.

Implementa a fórmula ISO/IEC 21031:2024:
    SCI = (E × I + M) / R

onde:
    E = energia consumida (kWh)
    I = intensidade de carbono do grid (gCO₂eq/kWh)
    M = carbono embutido no hardware (gCO₂eq), amortizado pelo tempo de uso
    R = unidade funcional (padrão: 1 hora de compute)

Referência: https://sci.greensoftware.foundation
"""

from .data_sources.aws_pricing import get_ec2_ondemand_price
from .data_sources.instance_energy import get_instance_energy_kwh
from .data_sources.carbon_intensity import get_carbon_intensity

# ─────────────────────────────────────────────────────────────────────────────
# Carbono embutido (embodied carbon) estimado por instância EC2.
# Representa a fração do carbono de fabricação do hardware
# alocada ao tempo de uso da instância.
#
# Fonte: Cloud Carbon Footprint methodology + Boavizta dataset
# Unidade: gCO₂eq por hora de uso
#
# Cálculo simplificado:
#   M_total (gCO₂eq) = carbono de fabricação do servidor
#   M_hora = M_total / (vida_útil_horas × resource_share)
#
# Para instâncias compartilhadas (Shared tenancy), o resource_share
# é aproximado pela proporção de vCPUs da instância vs. servidor host.
# ─────────────────────────────────────────────────────────────────────────────
EMBODIED_CARBON_GRAMS_PER_HOUR = {
    # ── Família T ────────────────────────────────────────────
    "t3.nano":       0.6,
    "t3.micro":      1.2,
    "t3.small":      2.4,
    "t3.medium":     2.4,
    "t3.large":      4.8,
    "t3.xlarge":     9.6,
    "t3.2xlarge":    19.2,
    "t4g.nano":      0.4,
    "t4g.micro":     0.8,
    "t4g.small":     1.6,
    "t4g.medium":    1.6,
    "t4g.large":     3.2,
    "t4g.xlarge":    6.4,
    "t4g.2xlarge":   12.8,
    # ── Família M ────────────────────────────────────────────
    "m5.large":      3.0,
    "m5.xlarge":     6.0,
    "m5.2xlarge":    12.0,
    "m5.4xlarge":    24.0,
    "m5.8xlarge":    48.0,
    "m5.12xlarge":   72.0,
    "m5.16xlarge":   96.0,
    "m5.24xlarge":   144.0,
    "m6g.large":     2.2,
    "m6g.xlarge":    4.4,
    "m6g.2xlarge":   8.8,
    "m6g.4xlarge":   17.6,
    "m6g.8xlarge":   35.2,
    "m6i.large":     2.8,
    "m6i.xlarge":    5.6,
    "m6i.2xlarge":   11.2,
    "m6i.4xlarge":   22.4,
    # ── Família C ────────────────────────────────────────────
    "c5.large":      2.8,
    "c5.xlarge":     5.6,
    "c5.2xlarge":    11.2,
    "c5.4xlarge":    22.4,
    "c5.9xlarge":    50.4,
    "c5.12xlarge":   67.2,
    "c5.18xlarge":   100.8,
    "c5.24xlarge":   134.4,
    "c6g.large":     2.0,
    "c6g.xlarge":    4.0,
    "c6g.2xlarge":   8.0,
    "c6g.4xlarge":   16.0,
    "c6g.8xlarge":   32.0,
    # ── Família R ────────────────────────────────────────────
    "r5.large":      3.5,
    "r5.xlarge":     7.0,
    "r5.2xlarge":    14.0,
    "r5.4xlarge":    28.0,
    "r5.8xlarge":    56.0,
    "r5.12xlarge":   84.0,
    "r5.16xlarge":   112.0,
    "r5.24xlarge":   168.0,
    "r6g.large":     2.5,
    "r6g.xlarge":    5.0,
    "r6g.2xlarge":   10.0,
    "r6g.4xlarge":   20.0,
    # ── Família G/P (GPU) ─────────────────────────────────────
    "g4dn.xlarge":   15.0,
    "g4dn.2xlarge":  22.0,
    "g4dn.4xlarge":  36.0,
    "g4dn.8xlarge":  65.0,
    "g4dn.12xlarge": 110.0,
    "g4dn.16xlarge": 130.0,
    "p3.2xlarge":    45.0,
    "p3.8xlarge":    180.0,
    "p3.16xlarge":   360.0,
}

# Carbono embutido padrão para instâncias não mapeadas (estimativa conservadora)
DEFAULT_EMBODIED_GRAMS_PER_HOUR = 5.0

# Horas padrão por mês (730 = 365 dias × 24h / 12 meses)
HOURS_PER_MONTH = 730


class SCICalculator:
    """
    Calcula o SCI score (ISO/IEC 21031:2024) e o custo estimado
    de uma arquitetura AWS.

    Uso:
        calc = SCICalculator()
        result = calc.calculate({
            "instance_type": "t3.medium",
            "region": "us-east-1",
            "hours_per_month": 730,
            "os": "Linux",
            "cpu_utilization": 0.5,
        })
    """

    def calculate(self, config: dict) -> dict:
        """
        Calcula SCI e custo para uma instância EC2.

        Parâmetros (config):
            instance_type    : str   — ex: "t3.medium"
            region           : str   — ex: "us-east-1"
            hours_per_month  : int   — padrão: 730
            os               : str   — "Linux" ou "Windows" (padrão: "Linux")
            cpu_utilization  : float — 0.0 a 1.0 (padrão: 0.5)

        Retorna:
            {
                "instance_type": str,
                "region": str,
                "os": str,
                "hours_per_month": int,
                "cpu_utilization": float,

                # Custo
                "price_usd_hour": float,
                "cost_usd_month": float,

                # Energia
                "energy_kwh_hour": float,        # sem PUE
                "energy_kwh_hour_with_pue": float, # com PUE

                # Carbono
                "carbon_intensity_gco2_kwh": float,
                "embodied_carbon_gco2_hour": float,
                "operational_carbon_gco2_hour": float,  # E × I
                "total_carbon_gco2_hour": float,         # E × I + M

                # SCI
                "sci_score_gco2_per_hour": float,  # = total_carbon / R
                "functional_unit": str,

                # Hardware
                "vcpu": str,
                "memory_gib": str,
            }
        """
        instance_type = config["instance_type"]
        region = config["region"]
        hours = config.get("hours_per_month", HOURS_PER_MONTH)
        os = config.get("os", "Linux")
        cpu_util = config.get("cpu_utilization", 0.5)

        # ── 1. Busca preço on-demand ──────────────────────────────────────
        pricing = get_ec2_ondemand_price(instance_type, region, os)

        # ── 2. Busca consumo energético ───────────────────────────────────
        energy = get_instance_energy_kwh(instance_type, cpu_util)

        # ── 3. Busca intensidade de carbono ───────────────────────────────
        carbon = get_carbon_intensity(region)

        # ── 4. Aplica fórmula SCI: (E × I + M) / R ───────────────────────
        E = energy["energy_kwh_hour_with_pue"]    # energia com PUE (kWh/h)
        I = carbon["carbon_intensity_gco2_kwh"]    # intensidade (gCO₂eq/kWh)
        M = EMBODIED_CARBON_GRAMS_PER_HOUR.get(   # carbono embutido (gCO₂eq/h)
            instance_type,
            DEFAULT_EMBODIED_GRAMS_PER_HOUR
        )
        R = 1  # unidade funcional: 1 hora de compute

        operational_carbon = E * I   # gCO₂eq/hora (parte operacional)
        total_carbon = operational_carbon + M  # gCO₂eq/hora (total)
        sci_score = total_carbon / R  # SCI = gCO₂eq por hora

        return {
            # Identificação
            "instance_type": instance_type,
            "region": region,
            "region_name": pricing["region_name"],
            "os": os,
            "hours_per_month": hours,
            "cpu_utilization": cpu_util,

            # Custo
            "price_usd_hour": pricing["price_usd_hour"],
            "cost_usd_month": round(pricing["price_usd_hour"] * hours, 2),

            # Energia
            "energy_kwh_hour": energy["energy_kwh_hour"],
            "energy_kwh_hour_with_pue": E,
            "pue": energy["pue"],

            # Carbono
            "carbon_intensity_gco2_kwh": I,
            "embodied_carbon_gco2_hour": round(M, 4),
            "operational_carbon_gco2_hour": round(operational_carbon, 4),
            "total_carbon_gco2_hour": round(total_carbon, 4),

            # SCI (ISO/IEC 21031:2024)
            "sci_score_gco2_per_hour": round(sci_score, 4),
            "functional_unit": "gCO2eq per compute-hour",

            # Hardware
            "vcpu": pricing["vcpu"],
            "memory_gib": pricing["memory_gib"],
        }
