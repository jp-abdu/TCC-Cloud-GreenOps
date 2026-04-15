"""
scripts/compare_regions.py
--------------------------
Compara o SCI score e custo de uma instancia em multiplas regioes AWS.
Mostra o trade-off custo x carbono de forma tabular.

Uso:
    python scripts/compare_regions.py
    python scripts/compare_regions.py --instance m5.large
"""

import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.sci_calculator import SCICalculator

# Regioes padrão para comparação
DEFAULT_REGIONS = [
    "us-east-1",
    "us-east-2",
    "us-west-1",
    "us-west-2",
    "ca-central-1",
    "eu-west-1",
    "eu-west-3",
    "eu-central-1",
    "eu-north-1",
    "sa-east-1",
    "ap-south-1",
    "ap-southeast-1",
    "ap-northeast-1",
]


def main():
    parser = argparse.ArgumentParser(description="Compara SCI e custo por regiao AWS")
    parser.add_argument("--instance", default="t3.medium", help="Tipo de instancia EC2")
    parser.add_argument("--hours", type=int, default=730, help="Horas de uso por mes")
    parser.add_argument("--cpu", type=float, default=0.5, help="Utilizacao de CPU")
    args = parser.parse_args()

    calc = SCICalculator()
    results = []

    print(f"\nComparando regioes para {args.instance} ({int(args.cpu*100)}% CPU, {args.hours}h/mes)...\n")

    for region in DEFAULT_REGIONS:
        try:
            r = calc.calculate({
                "instance_type": args.instance,
                "region": region,
                "hours_per_month": args.hours,
                "cpu_utilization": args.cpu,
            })
            results.append(r)
        except Exception as e:
            print(f"  [{region}] ignorado: {e}")

    # Ordena por SCI score
    results.sort(key=lambda x: x["sci_score_gco2_per_hour"])

    # Referencia: us-east-1
    ref = next((r for r in results if r["region"] == "us-east-1"), results[0])
    ref_sci = ref["sci_score_gco2_per_hour"]
    ref_cost = ref["cost_usd_month"]

    # Cabecalho
    print(f"{'Regiao':<28} {'Custo/mes':>10} {'SCI (gCO2/h)':>14} {'vs Virginia':>12}")
    print("-" * 68)

    for r in results:
        delta_sci = ((r["sci_score_gco2_per_hour"] - ref_sci) / ref_sci) * 100
        delta_cost = r["cost_usd_month"] - ref_cost
        delta_str = f"{delta_sci:+.0f}% SCI"

        marker = ""
        if r["region"] == "us-east-1":
            marker = " <-- baseline"
        elif delta_sci < -20 and abs(delta_cost) < 5:
            marker = " *** PARETO"

        cost_str = f"${r['cost_usd_month']}"
        if delta_cost != 0:
            cost_str += f" ({delta_cost:+.2f})"

        print(f"{r['region']:<28} {cost_str:>10} {r['sci_score_gco2_per_hour']:>14.4f} {delta_str:>12}{marker}")

    print("-" * 68)
    print("\n*** PARETO = mesmo custo (ou quase) com SCI significativamente menor\n")


if __name__ == "__main__":
    main()
