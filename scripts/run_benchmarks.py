"""
scripts/run_benchmarks.py
--------------------------
Processa todos os JSONs de arquitetura em benchmarks/architectures/
e gera a tabela consolidada para o artigo cientifico.

Para cada arquitetura, calcula:
  - SCI total e custo total no cenario base (us-east-1, on-demand)
  - Compara com a melhor regiao alternativa disponivel no dataset
  - Documenta o gap: quanto seria economizado em carbono mudando so de regiao

Uso:
    python scripts/run_benchmarks.py
    python scripts/run_benchmarks.py --output resultados.csv
"""

import sys
import json
import argparse
import csv
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.architecture_calculator import ArchitectureCalculator
from core.data_sources.carbon_intensity import CARBON_INTENSITY_STATIC

# Regioes a comparar em cada benchmark
BENCHMARK_REGIONS = [
    "us-east-1",   # baseline
    "us-west-2",   # Oregon — hidro, mesmo custo
    "eu-north-1",  # Estocolmo — mais limpo da Europa
    "eu-west-1",   # Irlanda — Europa comum
    "ca-central-1",# Canada — hidro
    "sa-east-1",   # Sao Paulo — hidro dominante
    "ap-south-1",  # Mumbai — comparativo sujo
]


def run_benchmark(arch_path: Path, calc: ArchitectureCalculator) -> dict:
    """Processa uma arquitetura e retorna os resultados por regiao."""
    with open(arch_path) as f:
        arch = json.load(f)

    name   = arch["name"]
    base_region = arch.get("base_region", "us-east-1")
    print(f"\n{'='*60}")
    print(f"  {name}")
    print(f"{'='*60}")

    results_by_region = {}
    for region in BENCHMARK_REGIONS:
        arch_copy = dict(arch)
        arch_copy["region"] = region
        try:
            result = calc.calculate(arch_copy)
            results_by_region[region] = result
            print(f"  {region:<20} SCI: {result['totals']['sci_score_gco2_per_hour']:.4f} gCO2/h  "
                  f"Custo: ${result['totals']['cost_usd_month']:.2f}/mes")
        except Exception as e:
            print(f"  {region:<20} ERRO: {e}")

    return {
        "name": name,
        "arch_file": arch_path.name,
        "base_region": base_region,
        "results": results_by_region,
    }


def analyze(benchmark: dict) -> dict:
    """Calcula gaps e metricas comparativas para o artigo."""
    results  = benchmark["results"]
    base_reg = benchmark["base_region"]

    if base_reg not in results:
        return {}

    base = results[base_reg]["totals"]
    base_sci  = base["sci_score_gco2_per_hour"]
    base_cost = base["cost_usd_month"]

    # Melhor SCI disponivel
    best_sci_region = min(results, key=lambda r: results[r]["totals"]["sci_score_gco2_per_hour"])
    best_sci = results[best_sci_region]["totals"]["sci_score_gco2_per_hour"]
    best_sci_cost = results[best_sci_region]["totals"]["cost_usd_month"]

    # Melhor custo
    best_cost_region = min(results, key=lambda r: results[r]["totals"]["cost_usd_month"])
    best_cost = results[best_cost_region]["totals"]["cost_usd_month"]

    # Pareto: melhor SCI sem piorar custo
    pareto_region = None
    pareto_sci    = base_sci
    for region, res in results.items():
        if region == base_reg:
            continue
        sci  = res["totals"]["sci_score_gco2_per_hour"]
        cost = res["totals"]["cost_usd_month"]
        if sci < pareto_sci and cost <= base_cost * 1.05:  # tolerancia de 5% no custo
            pareto_sci    = sci
            pareto_region = region

    sci_reduction = round((base_sci - best_sci) / base_sci * 100, 1) if base_sci > 0 else 0
    cost_diff = round(best_sci_cost - base_cost, 2)

    return {
        "name":             benchmark["name"],
        "base_sci":         base_sci,
        "base_cost":        base_cost,
        "best_sci":         best_sci,
        "best_sci_region":  best_sci_region,
        "best_sci_cost":    best_sci_cost,
        "sci_reduction_pct":sci_reduction,
        "cost_diff":        cost_diff,
        "pareto_region":    pareto_region,
        "pareto_sci":       pareto_sci,
        "pareto_sci_reduction": round((base_sci - pareto_sci) / base_sci * 100, 1) if base_sci > 0 else 0,
    }


def print_summary(analyses: list):
    """Imprime tabela consolidada para o artigo."""
    print(f"\n\n{'='*90}")
    print("  TABELA CONSOLIDADA — RESULTADOS DOS BENCHMARKS")
    print(f"{'='*90}")
    print(f"  {'Arquitetura':<28} {'SCI base':>10} {'Melhor SCI':>11} {'Reducao':>9} {'Custo diff':>12} {'Melhor regiao':<18}")
    print(f"  {'-'*88}")

    for a in analyses:
        cost_str = f"+${a['cost_diff']:.2f}" if a['cost_diff'] > 0 else f"-${abs(a['cost_diff']):.2f}"
        print(
            f"  {a['name']:<28} "
            f"{a['base_sci']:>9.4f}  "
            f"{a['best_sci']:>10.4f}  "
            f"{a['sci_reduction_pct']:>8.1f}%  "
            f"{cost_str:>11}  "
            f"{a['best_sci_region']:<18}"
        )

    avg_reduction = sum(a["sci_reduction_pct"] for a in analyses) / len(analyses)
    print(f"  {'-'*88}")
    print(f"  {'MEDIA':<28} {'':>10} {'':>11} {avg_reduction:>8.1f}%")
    print(f"{'='*90}")
    print(f"\n  Conclusao: mudanca de regiao reduz SCI em media {avg_reduction:.1f}% sem alteracao de arquitetura.\n")


def save_csv(analyses: list, output_path: str):
    """Salva resultados em CSV."""
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "name", "base_sci", "base_cost", "best_sci", "best_sci_region",
            "best_sci_cost", "sci_reduction_pct", "cost_diff",
            "pareto_region", "pareto_sci", "pareto_sci_reduction"
        ])
        writer.writeheader()
        writer.writerows(analyses)
    print(f"\n  Resultados salvos em: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Roda benchmarks de arquiteturas AWS")
    parser.add_argument("--output", default="", help="Salvar resultados em CSV")
    args = parser.parse_args()

    arch_dir = Path(__file__).parent.parent / "benchmarks" / "architectures"
    arch_files = sorted(arch_dir.glob("*.json"))

    if not arch_files:
        print("Nenhum arquivo JSON encontrado em benchmarks/architectures/")
        sys.exit(1)

    print(f"\nGreenArch — Benchmark Runner")
    print(f"Arquiteturas encontradas: {len(arch_files)}")
    print(f"Regioes a comparar: {len(BENCHMARK_REGIONS)}")
    print(f"Total de calculos: {len(arch_files) * len(BENCHMARK_REGIONS)}")

    calc = ArchitectureCalculator()
    analyses = []

    for arch_file in arch_files:
        benchmark = run_benchmark(arch_file, calc)
        analysis  = analyze(benchmark)
        if analysis:
            analyses.append(analysis)

    if analyses:
        print_summary(analyses)
        if args.output:
            save_csv(analyses, args.output)


if __name__ == "__main__":
    main()
