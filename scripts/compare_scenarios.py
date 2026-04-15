"""
scripts/compare_scenarios.py
----------------------------
Testa o Modulo 2 — comparador automatico de cenarios com Pareto-front.
Explora todas as combinacoes de regiao x instancia equivalente.

Uso:
    python scripts/compare_scenarios.py
    python scripts/compare_scenarios.py --instance m5.large --region us-east-1
"""

import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.scenario_engine import ScenarioEngine


def main():
    parser = argparse.ArgumentParser(description="Compara cenarios AWS automaticamente")
    parser.add_argument("--instance", default="t3.medium")
    parser.add_argument("--region",   default="us-east-1")
    parser.add_argument("--hours",    type=int,   default=730)
    parser.add_argument("--cpu",      type=float, default=0.5)
    args = parser.parse_args()

    engine = ScenarioEngine()

    equiv = engine.get_equivalent_instances(args.instance)
    print(f"\nInstancias equivalentes a {args.instance}: {equiv}")
    print(f"Regioes: todas ({len(engine.calc.__class__.__name__)} regioes)")
    print(f"Total de cenarios a calcular: {len(equiv) * 19}")
    print("\nCalculando... (pode demorar no primeiro acesso por regiao)\n")

    result = engine.compare(
        instance_type=args.instance,
        region=args.region,
        hours_per_month=args.hours,
        cpu_utilization=args.cpu,
    )

    s = result["summary"]
    base = result["base_scenario"]

    print("=" * 65)
    print(f"  CENARIO BASE: {args.instance} @ {args.region}")
    print(f"  Custo/mes : ${base['cost_usd_month']}")
    print(f"  SCI score : {base['sci_score']} gCO2/h")
    print("=" * 65)
    print(f"  Cenarios calculados : {s['total_scenarios']}")
    print(f"  Pareto-otimos       : {s['pareto_count']}")
    print(f"  Dominados           : {s['dominated_count']}")
    if s['errors']:
        print(f"  Erros               : {len(s['errors'])}")
    print("=" * 65)

    print("\n  PARETO-FRONT (ordenado por menor SCI):\n")
    print(f"  {'Instancia':<16} {'Regiao':<18} {'Custo/mes':>10} {'SCI':>10}  {'vs base':>10}")
    print("  " + "-" * 68)

    for p in result["pareto_front"]:
        delta_sci  = p["sci_score"] - base["sci_score"]
        delta_cost = p["cost_usd_month"] - base["cost_usd_month"]
        base_marker = " <-- BASE" if p["is_base"] else ""
        print(
            f"  {p['instance_type']:<16} {p['region']:<18} "
            f"${p['cost_usd_month']:>8.2f}  {p['sci_score']:>9.4f}  "
            f"SCI {delta_sci:+.4f} / custo {delta_cost:+.2f}{base_marker}"
        )

    best = s["best_sci_scenario"]
    if best and not best["is_base"]:
        print(f"\n  MELHOR ALTERNATIVA:")
        print(f"  {best['instance_type']} @ {best['region']}")
        print(f"  Reducao de SCI : {s['sci_reduction_vs_base']}% vs. cenario base")
        print(f"  Custo          : ${best['cost_usd_month']}/mes")
    print()


if __name__ == "__main__":
    main()
