"""
core/architecture_calculator.py
--------------------------------
Calcula o SCI score e custo total de uma arquitetura AWS completa,
composta por multiplos componentes: EC2, RDS e Lambda.

Uso:
    from core.architecture_calculator import ArchitectureCalculator

    calc = ArchitectureCalculator()
    result = calc.calculate({
        "name": "Startup web simples",
        "region": "us-east-1",
        "components": [
            {"type": "ec2", "instance": "t3.medium", "hours": 730, "cpu": 0.4},
            {"type": "rds", "instance": "db.t3.micro", "hours": 730, "cpu": 0.3, "engine": "MySQL"},
            {"type": "lambda", "invocations": 5000000, "duration_ms": 200, "memory_mb": 512},
        ]
    })
"""

from .sci_calculator import SCICalculator
from .data_sources.rds_pricing import get_rds_ondemand_price
from .data_sources.lambda_pricing import get_lambda_cost
from .data_sources.carbon_intensity import get_carbon_intensity

# Carbono embutido estimado para RDS (gCO2eq/hora)
RDS_EMBODIED_GRAMS_PER_HOUR = {
    "db.t3.micro":    1.0,
    "db.t3.small":    1.5,
    "db.t3.medium":   2.0,
    "db.t3.large":    3.5,
    "db.t3.xlarge":   6.0,
    "db.t3.2xlarge":  10.0,
    "db.t4g.micro":   0.8,
    "db.t4g.small":   1.2,
    "db.t4g.medium":  1.8,
    "db.t4g.large":   3.0,
    "db.m5.large":    3.5,
    "db.m5.xlarge":   6.0,
    "db.m5.2xlarge":  10.0,
    "db.m5.4xlarge":  18.0,
    "db.m6g.large":   2.8,
    "db.m6g.xlarge":  5.0,
    "db.m6g.2xlarge": 9.0,
    "db.r5.large":    4.0,
    "db.r5.xlarge":   7.0,
    "db.r5.2xlarge":  12.0,
    "db.r6g.large":   3.2,
    "db.r6g.xlarge":  6.0,
}

# Lambda: carbono embutido negligenciavel (hardware compartilhado e efimero)
LAMBDA_EMBODIED_GRAMS_PER_HOUR = 0.05


class ArchitectureCalculator:
    """
    Calcula SCI e custo total de uma arquitetura AWS com multiplos componentes.
    """

    def __init__(self):
        self.sci_calc = SCICalculator()

    def calculate(self, architecture: dict) -> dict:
        """
        Calcula o SCI e custo total de uma arquitetura completa.

        Parametros (architecture dict):
            name       : nome da arquitetura
            region     : regiao AWS base
            components : lista de componentes (ec2, rds, lambda)

        Retorna dict com SCI total, custo total e detalhes por componente.
        """
        name   = architecture.get("name", "Arquitetura sem nome")
        region = architecture.get("region", "us-east-1")
        components = architecture.get("components", [])

        carbon = get_carbon_intensity(region)
        I = carbon["carbon_intensity_gco2_kwh"]

        results = []
        total_cost_month = 0.0
        total_energy_kwh_hour = 0.0
        total_operational_carbon = 0.0
        total_embodied_carbon = 0.0
        errors = []

        for comp in components:
            comp_type = comp.get("type", "").lower()

            try:
                if comp_type == "ec2":
                    r = self.sci_calc.calculate({
                        "instance_type": comp["instance"],
                        "region": region,
                        "hours_per_month": comp.get("hours", 730),
                        "cpu_utilization": comp.get("cpu", 0.5),
                        "os": comp.get("os", "Linux"),
                    })
                    component_result = {
                        "type": "ec2",
                        "label": f"EC2 {comp['instance']}",
                        "cost_usd_month": r["cost_usd_month"],
                        "energy_kwh_hour": r["energy_kwh_hour_with_pue"],
                        "operational_carbon_gco2_hour": r["operational_carbon_gco2_hour"],
                        "embodied_carbon_gco2_hour": r["embodied_carbon_gco2_hour"],
                        "sci_score": r["sci_score_gco2_per_hour"],
                    }

                elif comp_type == "rds":
                    r = get_rds_ondemand_price(
                        instance_type=comp["instance"],
                        region=region,
                        engine=comp.get("engine", "MySQL"),
                        multi_az=comp.get("multi_az", False),
                        cpu_utilization=comp.get("cpu", 0.5),
                    )
                    hours = comp.get("hours", 730)
                    cost_month = r["price_usd_hour"] * hours
                    E = r["energy_kwh_hour"]
                    operational = E * I
                    M = RDS_EMBODIED_GRAMS_PER_HOUR.get(comp["instance"], 3.0)

                    component_result = {
                        "type": "rds",
                        "label": f"RDS {comp['instance']} ({r['engine']})",
                        "cost_usd_month": round(cost_month, 4),
                        "energy_kwh_hour": E,
                        "operational_carbon_gco2_hour": round(operational, 4),
                        "embodied_carbon_gco2_hour": M,
                        "sci_score": round(operational + M, 4),
                    }

                elif comp_type == "lambda":
                    r = get_lambda_cost(
                        region=region,
                        invocations_per_month=comp.get("invocations", 1000000),
                        avg_duration_ms=comp.get("duration_ms", 200),
                        memory_mb=comp.get("memory_mb", 512),
                        architecture=comp.get("architecture", "x86"),
                    )
                    E = r["energy_kwh_hour"]
                    operational = E * I
                    M = LAMBDA_EMBODIED_GRAMS_PER_HOUR

                    component_result = {
                        "type": "lambda",
                        "label": f"Lambda ({comp.get('invocations', 1000000)/1e6:.1f}M inv/mes)",
                        "cost_usd_month": r["price_usd_month"],
                        "energy_kwh_hour": E,
                        "operational_carbon_gco2_hour": round(operational, 6),
                        "embodied_carbon_gco2_hour": M,
                        "sci_score": round(operational + M, 6),
                    }

                else:
                    errors.append(f"Tipo de componente desconhecido: {comp_type}")
                    continue

                results.append(component_result)
                total_cost_month        += component_result["cost_usd_month"]
                total_energy_kwh_hour   += component_result["energy_kwh_hour"]
                total_operational_carbon += component_result["operational_carbon_gco2_hour"]
                total_embodied_carbon   += component_result["embodied_carbon_gco2_hour"]

            except Exception as e:
                errors.append(f"{comp_type} {comp.get('instance','')}: {e}")

        total_sci = total_operational_carbon + total_embodied_carbon

        return {
            "name": name,
            "region": region,
            "carbon_intensity_gco2_kwh": I,
            "components": results,
            "totals": {
                "cost_usd_month": round(total_cost_month, 2),
                "energy_kwh_hour": round(total_energy_kwh_hour, 6),
                "operational_carbon_gco2_hour": round(total_operational_carbon, 4),
                "embodied_carbon_gco2_hour": round(total_embodied_carbon, 4),
                "sci_score_gco2_per_hour": round(total_sci, 4),
            },
            "errors": errors,
        }
