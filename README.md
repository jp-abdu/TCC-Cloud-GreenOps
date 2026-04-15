# GreenArch

**A Carbon and Cost Architecture Advisor for AWS**

Calcula o SCI score (ISO/IEC 21031:2024) e o custo estimado de arquiteturas AWS antes do deploy, usando apenas dados públicos e gratuitos. Compara cenários automaticamente e expõe o trade-off custo × carbono.

---

## Estrutura do projeto

```
GreenArch/
├── core/
│   ├── sci_calculator.py          # Módulo 1 — Motor SCI (E × I + M) / R
│   └── data_sources/
│       ├── aws_pricing.py         # Preços EC2 via AWS Bulk API (sem auth)
│       ├── carbon_intensity.py    # Intensidade de carbono por região AWS
│       └── instance_energy.py     # Consumo kWh por instância (CCF dataset)
├── dashboard/
│   └── app.py                     # Módulo 3 — Dashboard Streamlit
├── scripts/
│   ├── check_setup.py             # Verifica se o ambiente está ok
│   ├── demo_sci.py                # Calcula SCI para uma instância
│   └── compare_regions.py         # Compara todas as regiões AWS
├── benchmarks/
│   └── architectures/             # JSONs das arquiteturas benchmark
├── tests/
│   └── test_data_sources.py       # Testes unitários
├── .gitignore
├── requirements.txt
└── README.md
```

---

## Instalação

```bash
git clone https://github.com/seu-usuario/greenarch
cd greenarch
pip install -r requirements.txt
```

---

## Verificar se tudo está funcionando

```bash
python scripts/check_setup.py
```

---

## Scripts de uso rápido

**Calcular SCI de uma instância:**
```bash
python scripts/demo_sci.py
python scripts/demo_sci.py --instance m5.large --region eu-north-1
```

**Comparar todas as regiões:**
```bash
python scripts/compare_regions.py
python scripts/compare_regions.py --instance c5.2xlarge
```

**Rodar o dashboard:**
```bash
streamlit run dashboard/app.py
```

---

## Fontes de dados (todas públicas, sem autenticação)

| Dado | Fonte | Custo |
|---|---|---|
| Preço on-demand EC2 | AWS Pricing Bulk API | Grátis |
| Intensidade de carbono | Electricity Maps / EPA eGRID / IEA | Grátis |
| Consumo kWh por instância | Cloud Carbon Footprint (ThoughtWorks) | Grátis |
| PUE dos datacenters AWS | AWS Sustainability Report | Grátis |
| Fórmula SCI | ISO/IEC 21031:2024 (Green Software Foundation) | Grátis |

---

## Fórmula SCI (ISO/IEC 21031:2024)

```
SCI = (E × I + M) / R
```

- **E** = energia consumida (kWh/hora)
- **I** = intensidade de carbono do grid (gCO₂eq/kWh)
- **M** = carbono embutido no hardware (gCO₂eq/hora)
- **R** = unidade funcional (1 hora de compute)

---

## Status

- [x] Fase 0 — Revisão de literatura e gap documentado
- [x] Fase 1 — Módulo 1: Motor de cálculo SCI
- [ ] Fase 2 — Módulo 2: Comparador de cenários + Pareto-front
- [ ] Fase 3 — Módulo 3: Dashboard interativo
- [ ] Fase 4 — Benchmarks e artigo científico

---

## Referências

- Green Software Foundation. *SCI Specification*. ISO/IEC 21031:2024.
- Radovanovic et al. *Carbon-Aware Computing for Datacenters*. IEEE Trans. Power Systems, 2022.
- Sukprasert et al. *On the Limitations of Carbon-Aware Workload Shifting*. EuroSys, 2024.
- FinOps Foundation. *State of FinOps Report 2025*.
