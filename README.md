# GreenArch

**Ferramenta de análise de carbono e custo para arquiteturas AWS antes do deploy**

GreenArch calcula o **Software Carbon Intensity (SCI)** e o custo estimado de instâncias e arquiteturas AWS antes do deploy, usando dados públicos e gratuitos. Compara cenários entre regiões automaticamente e apresenta o trade-off custo e carbono via Pareto-front interativo.

> Desenvolvido como Trabalho de Conclusão de Curso (TCC) em Análise e Desenvolvimento de Sistemas, IBMEC Rio de Janeiro, 2026.

---

## O problema que o GreenArch resolve

Instâncias idênticas em Oregon (`us-west-2`) e Virginia (`us-east-1`) custam o mesmo, mas Oregon tem **76% menos carbono**. Essa informação é invisível para qualquer ferramenta de FinOps disponível hoje. O GreenArch torna essa comparação possível antes de qualquer recurso ser criado na nuvem.

---

## Funcionalidades

- Cálculo de SCI seguindo o padrão **ISO/IEC 21031:2024**
- Comparação de instâncias EC2 entre todas as regiões AWS
- Comparação de arquiteturas completas com EC2, RDS e Lambda
- Pareto-front custo e carbono para identificar soluções ótimas
- Índice de Eficiência com ponderação configurável entre custo e carbono
- Latência de rede inter-região como dado contextual de decisão
- 4 arquiteturas de benchmark prontas para uso
- Export de relatório em PDF
- Duas interfaces: dashboard Streamlit e frontend React com API FastAPI
- Funciona sem conta AWS

---

## Estrutura do projeto

```
TCC-Cloud-GreenOps/
├── core/                          # Motor de cálculo — compartilhado entre as interfaces
│   ├── sci_calculator.py          # Fórmula SCI — ISO/IEC 21031:2024
│   ├── scenario_engine.py         # Comparador de cenários e Pareto-front
│   ├── architecture_calculator.py # Cálculo de arquiteturas mistas
│   ├── report_generator.py        # Gerador de relatório PDF
│   └── data_sources/
│       ├── aws_pricing.py         # Preços EC2 via AWS Bulk Pricing API
│       ├── rds_pricing.py         # Preços RDS via AWS Bulk Pricing API
│       ├── lambda_pricing.py      # Preços Lambda via AWS Bulk Pricing API
│       ├── carbon_intensity.py    # Intensidade de carbono por região AWS
│       └── instance_energy.py     # Consumo kWh por instância (CCF dataset)
├── dashboard_streamlit/
│   └── app.py                     # Interface Streamlit com 3 abas
├── api/
│   └── main.py                    # API FastAPI — expõe o core para o frontend React
├── frontend/
│   └── src/                       # Frontend React com Vite
├── benchmarks/
│   └── architectures/             # JSONs das arquiteturas de benchmark
│       ├── 01_startup_web.json
│       ├── 02_api_rest.json
│       ├── 06_microsservicos.json
│       └── 07_data_warehouse.json
├── scripts/
│   ├── check_setup.py             # Verifica se o ambiente está ok
│   ├── demo_sci.py                # Calcula SCI para uma instância
│   ├── compare_regions.py         # Compara todas as regiões AWS
│   └── run_benchmarks.py          # Roda todos os benchmarks
├── tests/
│   └── test_data_sources.py       # Testes unitários
├── requirements.txt               # Dependências Python
└── README.md
```

---

## Instalação e execução

### Pré-requisitos

- Python 3.10+
- Node.js 18+ (apenas para o frontend React)

### 1. Clonar o repositório

```bash
git clone https://github.com/jp-abdu/TCC-Cloud-GreenOps.git
cd TCC-Cloud-GreenOps
```

### 2. Instalar dependências Python

```bash
pip install -r requirements.txt
```

### 3. Verificar o ambiente

```bash
python scripts/check_setup.py
```

Se tudo estiver ok, a saída será `Tudo funcionando. Pode rodar o dashboard.`

---

## Interface Streamlit

A forma mais simples de rodar o projeto:

```bash
streamlit run dashboard_streamlit/app.py
```

Acesse `http://localhost:8501` no navegador.

---

## Interface React (requer Node.js 18+)

Modo desenvolvimento:

```bash
# Terminal 1 — API
uvicorn api.main:app --reload --port 8002

# Terminal 2 — Frontend
cd frontend
npm install
npm run dev
```

Acesse `http://localhost:5173` no navegador.

Build de produção:

```bash
cd frontend
npm run build
npm run preview
```

Acesse `http://localhost:4173` no navegador.

---

## Scripts de uso rápido

```bash
# Calcular SCI de uma instância
python scripts/demo_sci.py
python scripts/demo_sci.py --instance m5.large --region eu-north-1

# Comparar todas as regiões
python scripts/compare_regions.py
python scripts/compare_regions.py --instance c5.4xlarge

# Rodar benchmarks completos
python scripts/run_benchmarks.py
```

---

## Resultados dos benchmarks

Mudança de região reduz o SCI em média **47.1%** sem alterar arquitetura ou código.

| Arquitetura | SCI base (us-east-1) | Melhor SCI | Redução | Melhor região |
|---|---|---|---|---|
| Startup Web Simples | 5.9780 gCO₂/h | 3.5340 gCO₂/h | 40.9% | eu-north-1 (+$1.18/mês) |
| API REST Média Escala | 32.0200 gCO₂/h | 16.5809 gCO₂/h | 48.2% | eu-north-1 (+$32.32/mês) |
| Microsserviços com Lambda | 24.9169 gCO₂/h | 12.9612 gCO₂/h | 48.0% | eu-north-1 (+$26.18/mês) |
| Data Warehouse e Analytics | 50.2602 gCO₂/h | 24.5347 gCO₂/h | 51.2% | eu-north-1 (+$43.46/mês) |

---

## Fontes de dados

Todas públicas e gratuitas, sem autenticação necessária.

| Dado | Fonte |
|---|---|
| Preços EC2, RDS e Lambda | AWS Pricing Bulk API |
| Intensidade de carbono por região | Electricity Maps, EPA eGRID, IEA (médias anuais 2022–2023) |
| Consumo de energia por instância | Cloud Carbon Footprint (ThoughtWorks), benchmarks SPECpower |
| Carbono embutido do hardware | Boavizta dataset |
| Latência inter-região | CloudPing.co (RTT P50) |
| Fórmula SCI | ISO/IEC 21031:2024, Green Software Foundation |

---

## Fórmula SCI (ISO/IEC 21031:2024)

```
SCI = (E × I + M) / R
```

| Variável | Significado | Unidade |
|---|---|---|
| E | Energia consumida pela instância | kWh/h |
| I | Intensidade de carbono do grid elétrico | gCO₂/kWh |
| M | Carbono embutido do hardware, amortizado pela vida útil | gCO₂/h |
| R | Unidade funcional: 1 hora de uso | adimensional |

---

## Parâmetros de cálculo

| Parâmetro | Padrão | Observação |
|---|---|---|
| Utilização de CPU | 50% | Baseline do Cloud Carbon Footprint para workloads gerais. Configurável. |
| Horas por mês | 730h | Operação contínua 24/7. Configurável. |
| Sistema operacional | Linux | Fixo |

---

## Regiões AWS cobertas

`us-east-1` `us-east-2` `us-west-1` `us-west-2` `ca-central-1` `eu-west-1` `eu-west-2` `eu-west-3` `eu-central-1` `eu-north-1` `eu-south-1` `ap-southeast-1` `ap-southeast-2` `ap-northeast-1` `ap-northeast-2` `ap-south-1` `sa-east-1` `af-south-1` `me-south-1`

---

## Validação empírica

O GreenArch foi validado subindo a própria ferramenta em uma instância `t3.medium` em `us-east-1`.

| Métrica | Previsto pelo GreenArch | Medido na AWS | Diferença |
|---|---|---|---|
| Custo por hora | $0.041603 | $0.041600 | ~0% |
| SCI com CPU 50% | 4.3237 gCO₂/h | referência | referência |
| SCI com CPU real (31.6%) | 3.6465 gCO₂/h | recalculado | 15.7% abaixo do baseline |

A diferença de custo foi de 0%, confirmando a precisão da AWS Pricing API. A variação no SCI reflete a diferença entre CPU assumida e medida na prática, a principal limitação declarada do modelo.

---

## Lighthouse (frontend React em produção)

| Categoria | Score |
|---|---|
| Performance | 100 |
| Accessibility | 96 |
| Best Practices | 100 |
| SEO | 82 |

---

## Status do projeto

- [x] Motor de cálculo SCI (ISO/IEC 21031:2024)
- [x] Comparador de cenários com Pareto-front
- [x] Calculadora de arquiteturas com EC2, RDS e Lambda
- [x] Dashboard Streamlit com 3 abas
- [x] Frontend React com API FastAPI
- [x] 4 arquiteturas de benchmark com resultados completos
- [x] Export de relatório PDF
- [x] Latência inter-região com dados reais do CloudPing.co
- [x] Validação empírica de custo na AWS
- [ ] Artigo científico (em desenvolvimento)

---
## Demo online

- **Frontend:** https://tcc-cloud-green-ops.vercel.app
- **API:** https://jpabdu-greenarch-api.hf.space/docs
  
## Referências

- Green Software Foundation. *SCI Specification*. ISO/IEC 21031:2024.
- Radovanovic et al. *Carbon-Aware Computing for Datacenters*. IEEE Trans. Power Systems, 2022.
- Sukprasert et al. *On the Limitations of Carbon-Aware Workload Shifting in the Cloud*. EuroSys, 2024.
- Dodge et al. *Measuring the Carbon Intensity of AI in Cloud Instances*. ACM FAccT, 2022.
- Hanafy et al. *CarbonScaler: Leveraging Cloud Workload Elasticity for Optimizing Carbon-Efficiency*. ACM SIGMETRICS, 2024.
- ThoughtWorks. *Cloud Carbon Footprint Methodology*. 2023.
