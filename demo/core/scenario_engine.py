"""
core/scenario_engine.py
-----------------------
Modulo 2 — Comparador automatico de cenarios com Pareto-front.

Dado um workload descrito (instancia base + regiao base), o motor:
  1. Identifica instancias equivalentes em poder computacional
  2. Combina todas as regioes com todas as instancias equivalentes
  3. Calcula SCI e custo para cada combinacao
  4. Retorna o Pareto-front: solucoes onde nenhuma outra e melhor
     simultaneamente em custo E carbono

Criterio de equivalencia (revisado):
  - Mesmo numero de vCPUs
  - Memoria dentro de ±25%
  - Mesmo perfil de uso (burstable com burstable, steady com steady)
  - Familias T (burstable) NAO sao agrupadas com familias M (steady)
    pois servem cargas diferentes

Fonte: https://aws.amazon.com/ec2/instance-types/
"""

from .sci_calculator import SCICalculator
from .data_sources.carbon_intensity import CARBON_INTENSITY_STATIC

# ─────────────────────────────────────────────────────────────────────────────
# Grupos de equivalencia computacional — revisados
#
# BURSTABLE (T): workloads com uso moderado e picos ocasionais
#   T3 (Intel) ↔ T4g (Graviton2) — mesmo perfil, Graviton mais eficiente
#
# GERAL BALANCEADO (M): workloads steady, bancos, microservicos
#   M5 (Intel) ↔ M6i (Intel 3a gen) ↔ M6g (Graviton2)
#
# COMPUTE OPTIMIZED (C): batch, encoding, servidores web de alta performance
#   C5 (Intel) ↔ C6g (Graviton2)
#
# MEMORY OPTIMIZED (R): bancos in-memory, analytics
#   R5 (Intel) ↔ R6g (Graviton2)
#
# GPU: ML inference
#   Grupos separados por tamanho
# ─────────────────────────────────────────────────────────────────────────────
EQUIVALENT_GROUPS = {

    # ── BURSTABLE: 2 vCPU / 4 GiB ──────────────────────────────────────
    # T3 e T4g sao equivalentes diretos (mesmo perfil burstable)
    # M6g NAO entra — e steady e tem perfil diferente
    "t3.medium":   ["t3.medium",  "t4g.medium"],
    "t4g.medium":  ["t3.medium",  "t4g.medium"],

    # ── BURSTABLE: 2 vCPU / 8 GiB ──────────────────────────────────────
    "t3.large":    ["t3.large",   "t4g.large"],
    "t4g.large":   ["t3.large",   "t4g.large"],

    # ── BURSTABLE: 4 vCPU / 16 GiB ─────────────────────────────────────
    "t3.xlarge":   ["t3.xlarge",  "t4g.xlarge"],
    "t4g.xlarge":  ["t3.xlarge",  "t4g.xlarge"],

    # ── BURSTABLE: 8 vCPU / 32 GiB ─────────────────────────────────────
    "t3.2xlarge":  ["t3.2xlarge", "t4g.2xlarge"],
    "t4g.2xlarge": ["t3.2xlarge", "t4g.2xlarge"],

    # ── GERAL BALANCEADO: 2 vCPU / 8 GiB ───────────────────────────────
    "m5.large":    ["m5.large",   "m6g.large",  "m6i.large"],
    "m6g.large":   ["m5.large",   "m6g.large",  "m6i.large"],
    "m6i.large":   ["m5.large",   "m6g.large",  "m6i.large"],

    # ── GERAL BALANCEADO: 4 vCPU / 16 GiB ──────────────────────────────
    "m5.xlarge":   ["m5.xlarge",  "m6g.xlarge", "m6i.xlarge"],
    "m6g.xlarge":  ["m5.xlarge",  "m6g.xlarge", "m6i.xlarge"],
    "m6i.xlarge":  ["m5.xlarge",  "m6g.xlarge", "m6i.xlarge"],

    # ── GERAL BALANCEADO: 8 vCPU / 32 GiB ──────────────────────────────
    "m5.2xlarge":  ["m5.2xlarge", "m6g.2xlarge"],
    "m6g.2xlarge": ["m5.2xlarge", "m6g.2xlarge"],

    # ── GERAL BALANCEADO: 16 vCPU / 64 GiB ─────────────────────────────
    "m5.4xlarge":  ["m5.4xlarge", "m6g.4xlarge"],
    "m6g.4xlarge": ["m5.4xlarge", "m6g.4xlarge"],

    # ── COMPUTE OPTIMIZED: 2 vCPU / 4 GiB ──────────────────────────────
    "c5.large":    ["c5.large",   "c6g.large"],
    "c6g.large":   ["c5.large",   "c6g.large"],

    # ── COMPUTE OPTIMIZED: 4 vCPU / 8 GiB ──────────────────────────────
    "c5.xlarge":   ["c5.xlarge",  "c6g.xlarge"],
    "c6g.xlarge":  ["c5.xlarge",  "c6g.xlarge"],

    # ── COMPUTE OPTIMIZED: 8 vCPU / 16 GiB ─────────────────────────────
    "c5.2xlarge":  ["c5.2xlarge", "c6g.2xlarge"],
    "c6g.2xlarge": ["c5.2xlarge", "c6g.2xlarge"],

    # ── COMPUTE OPTIMIZED: 16 vCPU / 32 GiB ────────────────────────────
    "c5.4xlarge":  ["c5.4xlarge", "c6g.4xlarge"],
    "c6g.4xlarge": ["c5.4xlarge", "c6g.4xlarge"],

    # ── MEMORY OPTIMIZED: 2 vCPU / 16 GiB ──────────────────────────────
    "r5.large":    ["r5.large",   "r6g.large"],
    "r6g.large":   ["r5.large",   "r6g.large"],

    # ── MEMORY OPTIMIZED: 4 vCPU / 32 GiB ──────────────────────────────
    "r5.xlarge":   ["r5.xlarge",  "r6g.xlarge"],
    "r6g.xlarge":  ["r5.xlarge",  "r6g.xlarge"],

    # ── MEMORY OPTIMIZED: 8 vCPU / 64 GiB ──────────────────────────────
    "r5.2xlarge":  ["r5.2xlarge", "r6g.2xlarge"],
    "r6g.2xlarge": ["r5.2xlarge", "r6g.2xlarge"],

    # ── MEMORY OPTIMIZED: 16 vCPU / 128 GiB ────────────────────────────
    "r5.4xlarge":  ["r5.4xlarge", "r6g.4xlarge"],
    "r6g.4xlarge": ["r5.4xlarge", "r6g.4xlarge"],

    # ── GPU — ML Inference: 4 vCPU / 16 GiB + 1 GPU ────────────────────
    "g4dn.xlarge":  ["g4dn.xlarge"],   # sem equivalente direto na mesma classe

    # ── GPU — ML Inference: 8 vCPU / 32 GiB + 1 GPU ────────────────────
    "g4dn.2xlarge": ["g4dn.2xlarge"],

    # ── GPU — ML Inference: 16 vCPU / 64 GiB + 1 GPU ───────────────────
    "g4dn.4xlarge": ["g4dn.4xlarge"],

    # ── GPU — ML Training: 8 vCPU / 61 GiB + 1 V100 ────────────────────
    "p3.2xlarge":   ["p3.2xlarge"],
}

ALL_REGIONS = list(CARBON_INTENSITY_STATIC.keys())


def _is_pareto_optimal(candidate: dict, others: list) -> bool:
    """
    Retorna True se nenhum outro cenario domina o candidato.
    A domina B se A e melhor ou igual em AMBAS as dimensoes
    e estritamente melhor em pelo menos uma.
    """
    for other in others:
        if other is candidate:
            continue
        cost_ok = other["cost_usd_month"] <= candidate["cost_usd_month"]
        sci_ok  = other["sci_score"]      <= candidate["sci_score"]
        stricter = (
            other["cost_usd_month"] < candidate["cost_usd_month"] or
            other["sci_score"]      < candidate["sci_score"]
        )
        if cost_ok and sci_ok and stricter:
            return False
    return True


class ScenarioEngine:
    """
    Compara automaticamente todas as combinacoes de regiao x instancia
    equivalente e retorna o Pareto-front.
    """

    def __init__(self):
        self.calc = SCICalculator()

    def get_equivalent_instances(self, instance_type: str) -> list:
        return EQUIVALENT_GROUPS.get(instance_type, [instance_type])

    def compare(
        self,
        instance_type: str,
        region: str = "us-east-1",
        hours_per_month: int = 730,
        cpu_utilization: float = 0.5,
        os: str = "Linux",
        regions: list = None,
    ) -> dict:
        """
        Gera todos os cenarios possiveis e calcula o Pareto-front.
        """
        target_regions = regions if regions else ALL_REGIONS
        equivalent_instances = self.get_equivalent_instances(instance_type)

        all_scenarios = []
        errors = []

        for inst in equivalent_instances:
            for reg in target_regions:
                try:
                    r = self.calc.calculate({
                        "instance_type": inst,
                        "region": reg,
                        "hours_per_month": hours_per_month,
                        "cpu_utilization": cpu_utilization,
                        "os": os,
                    })
                    all_scenarios.append({
                        "instance_type": inst,
                        "region": reg,
                        "region_name": r["region_name"],
                        "cost_usd_month": r["cost_usd_month"],
                        "sci_score": r["sci_score_gco2_per_hour"],
                        "carbon_intensity": r["carbon_intensity_gco2_kwh"],
                        "operational_carbon": r["operational_carbon_gco2_hour"],
                        "embodied_carbon": r["embodied_carbon_gco2_hour"],
                        "energy_kwh": r["energy_kwh_hour_with_pue"],
                        "vcpu": r["vcpu"],
                        "memory_gib": r["memory_gib"],
                        "price_usd_hour": r["price_usd_hour"],
                        "label": f"{inst} @ {reg}",
                        "is_base": inst == instance_type and reg == region,
                    })
                except Exception as e:
                    errors.append(f"{inst}@{reg}: {e}")

        for s in all_scenarios:
            s["pareto_optimal"] = _is_pareto_optimal(s, all_scenarios)

        pareto_front = [s for s in all_scenarios if s["pareto_optimal"]]
        dominated    = [s for s in all_scenarios if not s["pareto_optimal"]]

        base = next((s for s in all_scenarios if s["is_base"]), None)
        if base is None and all_scenarios:
            base = min(all_scenarios, key=lambda x: x["cost_usd_month"])

        best_sci  = min(pareto_front, key=lambda x: x["sci_score"])   if pareto_front else None
        best_cost = min(pareto_front, key=lambda x: x["cost_usd_month"]) if pareto_front else None

        def pct(base_val, new_val):
            if not base_val:
                return 0
            return round((base_val - new_val) / base_val * 100, 1)

        summary = {
            "total_scenarios": len(all_scenarios),
            "pareto_count": len(pareto_front),
            "dominated_count": len(dominated),
            "errors": errors,
            "base_cost": base["cost_usd_month"] if base else None,
            "base_sci": base["sci_score"] if base else None,
            "best_sci_scenario": best_sci,
            "best_cost_scenario": best_cost,
            "sci_reduction_vs_base":  pct(base["sci_score"] if base else 0,
                                          best_sci["sci_score"] if best_sci else 0),
            "cost_reduction_vs_base": pct(base["cost_usd_month"] if base else 0,
                                          best_cost["cost_usd_month"] if best_cost else 0),
        }

        return {
            "base_scenario": base,
            "all_scenarios": all_scenarios,
            "pareto_front": sorted(pareto_front, key=lambda x: x["sci_score"]),
            "dominated":    sorted(dominated,    key=lambda x: x["sci_score"]),
            "summary": summary,
        }
