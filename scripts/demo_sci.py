"""
scripts/demo_sci.py
-------------------
Demonstracao basica do motor SCI para uma instancia em uma regiao.

Uso:
    python scripts/demo_sci.py
    python scripts/demo_sci.py --instance t3.medium --region us-east-1
"""

import sys
import argparse
from pathlib import Path

# Garante que o root do projeto esta no path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.sci_calculator import SCICalculator


def main():
    parser = argparse.ArgumentParser(description="Calcula SCI score de uma instancia AWS")
    parser.add_argument("--instance", default="t3.medium", help="Tipo de instancia EC2")
    parser.add_argument("--region", default="us-east-1", help="Regiao AWS")
    parser.add_argument("--hours", type=int, default=730, help="Horas de uso por mes")
    parser.add_argument("--cpu", type=float, default=0.5, help="Utilizacao de CPU (0.0 a 1.0)")
    args = parser.parse_args()

    calc = SCICalculator()

    print(f"\nCalculando SCI para {args.instance} em {args.region}...\n")

    result = calc.calculate({
        "instance_type": args.instance,
        "region": args.region,
        "hours_per_month": args.hours,
        "cpu_utilization": args.cpu,
    })

    print("=" * 55)
    print(f"  Instancia : {result['instance_type']}  ({result['vcpu']} vCPU, {result['memory_gib']})")
    print(f"  Regiao    : {result['region_name']}")
    print(f"  CPU util  : {int(result['cpu_utilization'] * 100)}%")
    print("=" * 55)
    print(f"  Custo/hora  : ${result['price_usd_hour']}")
    print(f"  Custo/mes   : ${result['cost_usd_month']}")
    print("-" * 55)
    print(f"  Energia/hora (com PUE): {result['energy_kwh_hour_with_pue']} kWh")
    print(f"  Grid carbono          : {result['carbon_intensity_gco2_kwh']} gCO2/kWh")
    print(f"  Carbono operacional   : {result['operational_carbon_gco2_hour']} gCO2/h")
    print(f"  Carbono embutido (M)  : {result['embodied_carbon_gco2_hour']} gCO2/h")
    print("-" * 55)
    print(f"  SCI SCORE : {result['sci_score_gco2_per_hour']} gCO2eq/hora")
    print("=" * 55)
    print()


if __name__ == "__main__":
    main()
