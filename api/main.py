"""
api/main.py
-----------
FastAPI backend para o GreenArch.
Expõe os endpoints de cálculo de SCI e custo para o frontend React.

Rodar:
    uvicorn api.main:app --reload --port 8002
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import sys
import os

# Garante que o core é importável a partir da raiz do projeto
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.sci_calculator import SCICalculator
from core.scenario_engine import ScenarioEngine
from core.architecture_calculator import ArchitectureCalculator
from core.data_sources.carbon_intensity import CARBON_INTENSITY_STATIC
from core.data_sources.instance_energy import list_supported_instances

app = FastAPI(
    title="GreenArch API",
    description="Carbon and Cost Intelligence for AWS — ISO/IEC 21031:2024",
    version="1.0.0",
)

# CORS — permite o frontend React (localhost:5173) acessar a API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Instâncias ────────────────────────────────────────────────────────────────

engine      = ScenarioEngine()
arch_calc   = ArchitectureCalculator()
sci_calc    = SCICalculator()


# ── Schemas ───────────────────────────────────────────────────────────────────

class InstanceRequest(BaseModel):
    instance_type: str
    base_region: str = "us-east-1"
    regions: list[str]
    cpu_utilization: float = 0.5    # 0.0 a 1.0
    hours_per_month: int = 730


class ArchComponent(BaseModel):
    model_config = {"extra": "ignore"}
    type: str                        # "ec2", "rds", "lambda"
    instance: Optional[str] = None
    hours: int = 730
    cpu: float = 0.5
    os: str = "Linux"
    engine: Optional[str] = "MySQL"
    multi_az: bool = False
    invocations: Optional[int] = 1_000_000
    duration_ms: Optional[int] = 200
    memory_mb: Optional[int] = 512
    architecture: Optional[str] = "x86"
    label: Optional[str] = None


class ArchitectureRequest(BaseModel):
    name: str = "Arquitetura"
    base_region: str = "us-east-1"
    regions: list[str]
    components: list[ArchComponent]


# ── Helpers ───────────────────────────────────────────────────────────────────

def compute_pareto(scenarios: list[dict]) -> list[dict]:
    """Recalcula Pareto-front para um conjunto de cenários filtrados."""
    def dominated(row, rows):
        for other in rows:
            if other is row:
                continue
            if (other["sci_score"] <= row["sci_score"] and
                other["cost_usd_month"] <= row["cost_usd_month"] and
                (other["sci_score"] < row["sci_score"] or
                 other["cost_usd_month"] < row["cost_usd_month"])):
                return True
        return False

    for sc in scenarios:
        sc["pareto_optimal"] = not dominated(sc, scenarios)
    return scenarios


# ── Dados estáticos ───────────────────────────────────────────────────────────

# Latência inter-região AWS (P50 ms) — Fonte: CloudPing.co
INTER_REGION_LATENCY = {
    ("us-east-1", "us-east-1"):    1,
    ("us-east-1", "us-east-2"):   13,
    ("us-east-1", "us-west-1"):   61,
    ("us-east-1", "us-west-2"):   68,
    ("us-east-1", "ca-central-1"): 17,
    ("us-east-1", "eu-west-1"):   76,
    ("us-east-1", "eu-west-2"):   77,
    ("us-east-1", "eu-west-3"):   84,
    ("us-east-1", "eu-central-1"): 91,
    ("us-east-1", "eu-north-1"):  112,
    ("us-east-1", "eu-south-1"):  102,
    ("us-east-1", "ap-south-1"):  214,
    ("us-east-1", "ap-northeast-1"): 149,
    ("us-east-1", "ap-northeast-2"): 181,
    ("us-east-1", "ap-southeast-1"): 219,
    ("us-east-1", "ap-southeast-2"): 207,
    ("us-east-1", "sa-east-1"):   114,
    ("us-east-1", "af-south-1"):  225,
    ("us-east-1", "me-south-1"):  165,
    ("us-west-2", "us-west-1"):   21,
    ("us-west-2", "ca-central-1"): 61,
    ("us-west-2", "eu-west-1"):   118,
    ("us-west-2", "eu-central-1"): 144,
    ("us-west-2", "eu-north-1"):  155,
    ("us-west-2", "ap-south-1"):  233,
    ("us-west-2", "ap-northeast-1"): 105,
    ("us-west-2", "ap-southeast-1"): 165,
    ("us-west-2", "ap-southeast-2"): 145,
    ("us-west-2", "sa-east-1"):   184,
    ("eu-central-1", "eu-west-1"):  21,
    ("eu-central-1", "eu-north-1"): 23,
    ("eu-central-1", "eu-west-2"):  15,
    ("eu-central-1", "eu-west-3"):  10,
    ("eu-central-1", "sa-east-1"): 204,
    ("eu-central-1", "ap-south-1"): 130,
    ("eu-north-1", "eu-west-1"):   37,
    ("eu-north-1", "us-west-2"):  155,
    ("eu-north-1", "sa-east-1"):  223,
    ("sa-east-1", "eu-west-1"):   178,
    ("sa-east-1", "us-west-2"):   184,
    ("sa-east-1", "eu-north-1"):  223,
    ("sa-east-1", "eu-central-1"): 204,
    ("ap-south-1", "eu-west-1"):  149,
    ("ap-south-1", "ap-northeast-1"): 129,
    ("ap-south-1", "ap-southeast-1"): 63,
}

RENEWABLE_REGIONS = {
    "us-east-1", "us-east-2", "us-west-1", "us-west-2",
    "ca-central-1", "eu-west-1", "eu-west-2", "eu-west-3",
    "eu-central-1", "eu-north-1", "eu-south-1",
    "ap-south-1", "ap-northeast-1", "ap-northeast-2", "sa-east-1",
}


def get_latency(origin: str, dest: str) -> int | None:
    v = INTER_REGION_LATENCY.get((origin, dest))
    if v is None:
        v = INTER_REGION_LATENCY.get((dest, origin))
    return v


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.get("/")
def root():
    return {"name": "GreenArch API", "version": "1.0.0", "status": "ok"}


@app.get("/regions")
def get_regions():
    """Retorna todas as regiões AWS disponíveis com carbon intensity e info de renovável."""
    return {
        "regions": [
            {
                "id": region,
                "carbon_intensity": intensity,
                "renewable": region in RENEWABLE_REGIONS,
            }
            for region, intensity in CARBON_INTENSITY_STATIC.items()
        ]
    }


@app.get("/instances")
def get_instances():
    """Retorna todas as instâncias EC2 suportadas."""
    return {"instances": list_supported_instances()}


@app.post("/calculate/instance")
def calculate_instance(req: InstanceRequest):
    """
    Calcula SCI e custo de uma instância EC2 em múltiplas regiões.
    Retorna cenários, Pareto-front e latência.
    """
    if not req.regions:
        raise HTTPException(status_code=400, detail="Selecione ao menos uma região.")

    if req.instance_type not in list_supported_instances():
        raise HTTPException(status_code=400, detail=f"Instância {req.instance_type} não suportada.")

    try:
        result = engine.compare(
            instance_type=req.instance_type,
            region=req.base_region,
            hours_per_month=req.hours_per_month,
            cpu_utilization=req.cpu_utilization,
            os="Linux",
            regions=req.regions,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    # Filtra só a instância base (sem equivalentes)
    all_scenarios = [
        sc for sc in result.get("all_scenarios", [])
        if sc["instance_type"] == req.instance_type
    ]

    # Recalcula Pareto para o conjunto filtrado
    all_scenarios = compute_pareto(all_scenarios)
    pareto = [sc for sc in all_scenarios if sc["pareto_optimal"]]

    base = result.get("base_scenario", {})

    # Adiciona latência a cada cenário
    for sc in all_scenarios:
        lat = get_latency(req.base_region, sc["region"])
        sc["latency_ms"] = lat
        sc["renewable"] = sc["region"] in RENEWABLE_REGIONS

    best_sci  = min(all_scenarios, key=lambda x: x["sci_score"]) if all_scenarios else None
    best_cost = min(all_scenarios, key=lambda x: x["cost_usd_month"]) if all_scenarios else None

    sci_reduction = 0.0
    if best_sci and base:
        sci_reduction = round(
            (base["sci_score"] - best_sci["sci_score"]) / base["sci_score"] * 100, 1
        )

    return {
        "base": base,
        "all_scenarios": all_scenarios,
        "pareto": pareto,
        "summary": {
            "total_scenarios": len(all_scenarios),
            "pareto_count": len(pareto),
            "best_sci": best_sci,
            "best_cost": best_cost,
            "sci_reduction_pct": sci_reduction,
        },
    }


@app.post("/calculate/architecture")
def calculate_architecture(req: ArchitectureRequest):
    print("=== REQUEST RECEBIDO ===")
    print("name:", req.name)
    print("base_region:", req.base_region)
    print("regions:", req.regions)
    print("components:", len(req.components))
    for c in req.components:
        print(" -", c.model_dump())
    print("========================")
    """
    Calcula SCI e custo total de uma arquitetura AWS em múltiplas regiões.
    """
    if not req.regions:
        raise HTTPException(status_code=400, detail="Selecione ao menos uma região.")

    if not req.components:
        raise HTTPException(status_code=400, detail="Adicione ao menos um componente.")

    results = []
    for region in req.regions:
        try:
            # Normaliza componentes — remove campos extras e força defaults
            comps = []
            for c in req.components:
                d = c.model_dump()
                d.pop("label", None)
                comps.append(d)

            r = arch_calc.calculate({
                "name":   req.name,
                "region": region,
                "components": comps,
            })
            lat = get_latency(req.base_region, region)
            results.append({
                "region":           region,
                "sci_score":        r["totals"]["sci_score_gco2_per_hour"],
                "cost_usd_month":   r["totals"]["cost_usd_month"],
                "carbon_intensity": r.get("carbon_intensity_gco2_kwh", 0),
                "components":       r.get("components", []),
                "latency_ms":       lat,
                "renewable":        region in RENEWABLE_REGIONS,
            })
        except Exception as e:
            results.append({
                "region": region,
                "error": str(e),
            })

    valid = [r for r in results if "error" not in r]
    valid = compute_pareto(valid)
    pareto = [r for r in valid if r.get("pareto_optimal")]

    base_row = next((r for r in valid if r["region"] == req.base_region), None)
    if not base_row and valid:
        base_row = valid[0]

    best_sci  = min(valid, key=lambda x: x["sci_score"]) if valid else None
    best_cost = min(valid, key=lambda x: x["cost_usd_month"]) if valid else None

    sci_reduction = 0.0
    if best_sci and base_row:
        sci_reduction = round(
            (base_row["sci_score"] - best_sci["sci_score"]) / base_row["sci_score"] * 100, 1
        )

    return {
        "base": base_row,
        "all_scenarios": valid,
        "pareto": pareto,
        "summary": {
            "total_scenarios": len(valid),
            "pareto_count": len(pareto),
            "best_sci": best_sci,
            "best_cost": best_cost,
            "sci_reduction_pct": sci_reduction,
        },
    }


@app.get("/benchmarks")
def get_benchmarks():
    """Retorna as arquiteturas de benchmark disponíveis."""
    import json
    from pathlib import Path

    bench_dir = Path(__file__).parent.parent / "benchmarks" / "architectures"
    benchmarks = []
    for f in sorted(bench_dir.glob("*.json")):
        with open(f) as fp:
            data = json.load(fp)
            benchmarks.append({
                "id":          f.stem,
                "name":        data.get("name", f.stem),
                "description": data.get("description", ""),
                "components":  data.get("components", []),
                "base_region": data.get("base_region", "us-east-1"),
            })
    return {"benchmarks": benchmarks}
