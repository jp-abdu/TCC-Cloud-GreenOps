"""
demo/app.py
-----------
GreenArch — versao de apresentacao.
Light mode, fonte neutra, tudo explicado, 2 arquiteturas.

Rodar a partir da pasta demo/:
    python -m streamlit run app.py
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import streamlit as st
import plotly.graph_objects as go
import pandas as pd

from core.scenario_engine import ScenarioEngine, EQUIVALENT_GROUPS
from core.architecture_calculator import ArchitectureCalculator
from core.data_sources.instance_energy import list_supported_instances
from core.data_sources.carbon_intensity import CARBON_INTENSITY_STATIC

st.set_page_config(
    page_title="GreenArch",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif !important;
    background-color: #FFFFFF !important;
    color: #111111 !important;
}
.stApp { background-color: #FFFFFF !important; }

/* Margem e largura */
.block-container {
    padding-top: 28px !important;
    padding-bottom: 40px !important;
    padding-left: 48px !important;
    padding-right: 48px !important;
    max-width: 100% !important;
}

/* Abas */
.stTabs [data-baseweb="tab-list"] {
    background: transparent !important;
    border-bottom: 1px solid #E5E5E5 !important;
    gap: 0 !important; padding: 0 !important;
}
.stTabs [data-baseweb="tab"] {
    font-family: 'Inter', sans-serif !important;
    font-size: 14px !important; font-weight: 400 !important;
    color: #888888 !important; background: transparent !important;
    border: none !important; border-bottom: 2px solid transparent !important;
    padding: 10px 24px !important; margin: 0 !important;
}
.stTabs [aria-selected="true"] {
    color: #16A34A !important;
    border-bottom: 2px solid #16A34A !important;
    font-weight: 500 !important;
}
.stTabs [data-baseweb="tab-panel"] { padding-top: 28px !important; }

/* Metricas */
[data-testid="stMetric"] {
    background: #F9FAFB !important;
    border: 1px solid #E5E7EB !important;
    border-radius: 8px !important;
    padding: 20px 24px !important;
}
[data-testid="stMetricLabel"] {
    font-family: 'Inter', sans-serif !important;
    font-size: 11px !important; font-weight: 500 !important;
    color: #6B7280 !important; text-transform: uppercase !important;
    letter-spacing: 0.6px !important;
}
[data-testid="stMetricValue"] {
    font-family: 'Inter', sans-serif !important;
    font-size: 22px !important; font-weight: 600 !important;
    color: #111111 !important;
}
[data-testid="stMetricDelta"] {
    font-family: 'Inter', sans-serif !important;
    font-size: 12px !important;
}

/* Inputs */
.stSelectbox > div > div {
    background: #FFFFFF !important; border: 1px solid #D1D5DB !important;
    border-radius: 6px !important; font-size: 14px !important;
    color: #111111 !important;
}

/* Botoes */
.stButton > button {
    font-family: 'Inter', sans-serif !important;
    font-size: 14px !important; font-weight: 500 !important;
    border-radius: 6px !important; border: 1px solid #D1D5DB !important;
    background: #FFFFFF !important; color: #374151 !important;
    padding: 7px 18px !important; transition: all 0.12s ease !important;
}
.stButton > button:hover {
    border-color: #16A34A !important; color: #16A34A !important;
    background: #F0FDF4 !important;
}
.stButton > button[kind="primary"] {
    background: #16A34A !important; border-color: #16A34A !important;
    color: #FFFFFF !important; font-weight: 600 !important;
}
.stButton > button[kind="primary"]:hover { background: #15803D !important; border-color: #15803D !important; }

/* Forms */
[data-testid="stForm"] {
    background: #F9FAFB !important; border: 1px solid #E5E7EB !important;
    border-radius: 8px !important; padding: 20px !important;
}

/* Expander */
[data-testid="stExpander"] {
    border: 1px solid #E5E7EB !important; border-radius: 8px !important;
    background: #FFFFFF !important;
}
[data-testid="stExpander"] summary { color: #374151 !important; font-size: 13px !important; }

/* Dataframe */
[data-testid="stDataFrame"] {
    border: 1px solid #E5E7EB !important; border-radius: 8px !important;
}

/* Checkbox */
.stCheckbox label p {
    font-size: 13px !important; color: #374151 !important;
    text-transform: none !important; letter-spacing: 0 !important;
}

/* Labels */
label[data-testid="stWidgetLabel"] p {
    font-size: 12px !important; font-weight: 500 !important;
    color: #6B7280 !important; text-transform: uppercase !important;
    letter-spacing: 0.5px !important;
}

/* Caption */
.stMarkdown p { font-size: 13px !important; color: #6B7280 !important; line-height: 1.6 !important; }

/* Scrollbar */
::-webkit-scrollbar { width: 4px; height: 4px; }
::-webkit-scrollbar-track { background: #F9FAFB; }
::-webkit-scrollbar-thumb { background: #D1D5DB; border-radius: 2px; }

/* Ocultar chrome Streamlit */
#MainMenu, footer, header [data-testid="stToolbar"] { display: none !important; }
.stDeployButton { display: none !important; }
[data-testid="stSidebarCollapsedControl"] { display: none !important; }
</style>
""", unsafe_allow_html=True)

# ── Helpers ────────────────────────────────────────────────────────────────
def chart_layout(height=440, **kw):
    return dict(
        height=height,
        font=dict(family="Inter, sans-serif", size=12, color="#6B7280"),
        plot_bgcolor="#FFFFFF", paper_bgcolor="#FFFFFF",
        xaxis=dict(showgrid=True, gridcolor="#F3F4F6", gridwidth=1,
                   zeroline=False, tickfont=dict(size=11), linecolor="#E5E7EB"),
        yaxis=dict(showgrid=True, gridcolor="#F3F4F6", gridwidth=1,
                   zeroline=False, tickfont=dict(size=11), linecolor="#E5E7EB"),
        legend=dict(font=dict(size=11, color="#6B7280"),
                    bgcolor="rgba(0,0,0,0)", borderwidth=0),
        margin=dict(t=16, b=48, l=56, r=130),
        **kw,
    )

def divider():
    st.markdown('<hr style="border:none;border-top:1px solid #E5E7EB;margin:24px 0 20px 0;">',
                unsafe_allow_html=True)

def section(label, desc=None):
    html = (f'<div style="font-size:11px;font-weight:600;color:#9CA3AF;'
            f'text-transform:uppercase;letter-spacing:1px;margin:20px 0 8px 0;">'
            f'{label}</div>')
    if desc:
        html += (f'<div style="font-size:13px;color:#6B7280;margin-bottom:12px;'
                 f'line-height:1.6;">{desc}</div>')
    st.markdown(html, unsafe_allow_html=True)

def banner(html, color="#16A34A", bg="#F0FDF4", border="#BBF7D0"):
    st.markdown(
        f'<div style="background:{bg};border:1px solid {border};'
        f'border-left:3px solid {color};border-radius:6px;'
        f'padding:14px 18px;font-size:14px;color:#111111;'
        f'margin:16px 0;line-height:1.7;">{html}</div>',
        unsafe_allow_html=True
    )

def explain_box(title, items):
    """Caixa de explicacao com lista de items (label, valor, desc)."""
    rows = "".join(
        f'<div style="display:flex;gap:12px;padding:10px 0;border-bottom:1px solid #F3F4F6;">'
        f'<div style="font-size:22px;font-weight:700;color:#16A34A;width:28px;'
        f'flex-shrink:0;line-height:1.2;">{label}</div>'
        f'<div><div style="font-size:13px;font-weight:600;color:#111111;">{val}</div>'
        f'<div style="font-size:12px;color:#6B7280;margin-top:2px;">{desc}</div></div>'
        f'</div>'
        for label, val, desc in items
    )
    st.markdown(
        f'<div style="background:#F9FAFB;border:1px solid #E5E7EB;border-radius:8px;'
        f'padding:16px 20px;margin:12px 0;">'
        f'<div style="font-size:12px;font-weight:600;color:#9CA3AF;text-transform:uppercase;'
        f'letter-spacing:0.8px;margin-bottom:4px;">{title}</div>'
        f'{rows}</div>',
        unsafe_allow_html=True
    )

# ── Constantes ─────────────────────────────────────────────────────────────
REGION_GROUPS = {
    "North America": ["us-east-1", "us-east-2", "us-west-1", "us-west-2", "ca-central-1"],
    "Europe":        ["eu-west-1", "eu-west-2", "eu-west-3", "eu-central-1", "eu-north-1", "eu-south-1"],
    "Asia Pacific":  ["ap-southeast-1", "ap-southeast-2", "ap-northeast-1", "ap-northeast-2", "ap-south-1"],
    "South America": ["sa-east-1"],
    "Africa / ME":   ["af-south-1", "me-south-1"],
}
DEFAULT_REGIONS = ["us-east-1", "us-west-2", "eu-north-1", "eu-west-1", "sa-east-1"]
ALL_INSTANCES   = list_supported_instances()

BENCH_ALLOWED = {"Startup Web Simples", "API REST Media Escala"}

# ── Header compacto ────────────────────────────────────────────────────────
st.markdown("""
<div style="padding:12px 0 16px 0; border-bottom:1px solid #E5E7EB; margin-bottom:0;">
    <div style="display:flex;align-items:center;justify-content:space-between;">
        <div style="display:flex;align-items:baseline;gap:16px;">
            <div style="font-size:26px;font-weight:700;color:#111111;letter-spacing:-0.5px;">
                Green<span style="color:#16A34A">Arch</span>
            </div>
            <div style="font-size:13px;color:#9CA3AF;font-weight:400;">
                Inteligencia de Custo e Carbono para AWS
            </div>
        </div>
        <div style="font-size:11px;color:#16A34A;border:1px solid #BBF7D0;
                    background:#F0FDF4;padding:3px 10px;border-radius:4px;letter-spacing:0.4px;">
            ISO/IEC 21031:2024
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ── Abas ───────────────────────────────────────────────────────────────────
tab1, tab2 = st.tabs(["Analise de Instancia", "Arquitetura"])


# ══════════════════════════════════════════════════════════════════════════
# TAB 1 — INSTANCE
# ══════════════════════════════════════════════════════════════════════════
with tab1:

    # Explicacao do SCI — sempre visivel no topo
    st.markdown("""
    <div style="background:#F0FDF4;border:1px solid #BBF7D0;border-radius:8px;
                padding:16px 20px;margin-bottom:20px;">
        <div style="font-size:13px;font-weight:600;color:#15803D;margin-bottom:6px;">
            O que e o SCI score?
        </div>
        <div style="font-size:13px;color:#374151;line-height:1.7;">
            O <b>Software Carbon Intensity (SCI)</b> e um padrao ISO (21031:2024)
            que mede a pegada de carbono de um workload de software por unidade de uso.
            Aqui, a unidade e <b>uma hora de compute</b>.
        </div>
        <div style="margin-top:12px;font-size:18px;font-weight:700;
                    color:#15803D;letter-spacing:0.5px;text-align:center;">
            SCI = ( E &times; I + M ) / R
        </div>
        <div style="display:flex;gap:24px;margin-top:12px;flex-wrap:wrap;">
            <div style="font-size:12px;color:#374151;">
                <b style="color:#15803D;">E</b> — Energy consumed (kWh/h)<br>
                <span style="color:#6B7280;">Fonte: Cloud Carbon Footprint dataset
                (ThoughtWorks), baseado em benchmarks SPECpower</span>
            </div>
            <div style="font-size:12px;color:#374151;">
                <b style="color:#15803D;">I</b> — Carbon intensity of the power grid (gCO&#x2082;/kWh)<br>
                <span style="color:#6B7280;">Fonte: Electricity Maps, EPA eGRID, IEA
                — medias anuais por regiao AWS</span>
            </div>
            <div style="font-size:12px;color:#374151;">
                <b style="color:#15803D;">M</b> — Embodied carbon of the hardware (gCO&#x2082;/h)<br>
                <span style="color:#6B7280;">Emissoes de fabricacao amortizadas ao longo
                da vida util da instancia. Fonte: Boavizta dataset</span>
            </div>
            <div style="font-size:12px;color:#374151;">
                <b style="color:#15803D;">R</b> — Functional unit<br>
                <span style="color:#6B7280;">1 hora de compute nesta analise</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    col_main, col_side = st.columns([3, 1], gap="large")

    with col_side:
        section("Configurar workload",
                "Selecione um tipo de instancia e as regioes que deseja comparar.")
        with st.form("form_inst"):
            instance_type = st.selectbox(
                "Tipo de instancia", ALL_INSTANCES,
                index=ALL_INSTANCES.index("t3.medium"),
            )
            os_type = st.selectbox("Sistema operacional", ["Linux", "Windows"])

            st.markdown(
                '<div style="font-size:12px;color:#9CA3AF;padding:8px 0;">'
                'Utilizacao de CPU fixada em <b>50%</b> '
                '(baseline Cloud Carbon Footprint) &nbsp;·&nbsp; '
                '<b>730 horas/mes</b> (operacao 24/7)</div>',
                unsafe_allow_html=True
            )

            section("Regioes a comparar")
            selected_regions = []
            for continent, regs in REGION_GROUPS.items():
                with st.expander(continent, expanded=(continent == "North America")):
                    for reg in regs:
                        intensity = CARBON_INTENSITY_STATIC.get(reg, 0)
                        if st.checkbox(
                            f"{reg}  ·  {intensity} gCO₂/kWh",
                            value=reg in DEFAULT_REGIONS,
                            key=f"i1_{reg}",
                        ):
                            selected_regions.append(reg)

            go_btn = st.form_submit_button(
                "Calcular", type="primary", use_container_width=True
            )

        equiv = EQUIVALENT_GROUPS.get(instance_type, [instance_type])
        st.caption(
            f"O comparador tambem explorara familias de instancia equivalentes: "
            f"**{', '.join(equiv)}**. These have the same vCPU and memory profile "
            f"but different processor architectures (Intel vs. Graviton)."
        )
        st.caption(f"Total de cenarios a calcular: **{len(equiv) * len(selected_regions)}**")

    with col_main:
        if go_btn:
            if not selected_regions:
                st.warning("Select at least one region.")
            else:
                engine = ScenarioEngine()
                with st.spinner("Buscando precos AWS e calculando todos os cenarios..."):
                    result = engine.compare(
                        instance_type=instance_type,
                        region=selected_regions[0],
                        hours_per_month=730,
                        cpu_utilization=0.50,
                        os=os_type,
                        regions=selected_regions,
                    )
                st.session_state["demo_result"] = result
                st.session_state["demo_label"]  = instance_type

        if "demo_result" not in st.session_state:
            st.markdown("""
            <div style="margin-top:80px;text-align:center;padding:40px;">
                <div style="font-size:15px;color:#9CA3AF;margin-bottom:8px;">
                    Selecione um tipo de instancia e regioes, depois clique em Calcular.
                </div>
                <div style="font-size:13px;color:#D1D5DB;">
                    Os precos sao obtidos em tempo real da API publica da AWS —
                    sem necessidade de conta ou credenciais.
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            res    = st.session_state["demo_result"]
            label  = st.session_state["demo_label"]
            s      = res["summary"]
            base   = res["base_scenario"]
            pareto = res["pareto_front"]
            df     = pd.DataFrame(res["all_scenarios"])
            df["Status"] = df["pareto_optimal"].map(
                {True: "Pareto otimo", False: "Dominated"})

            st.markdown(
                f'<div style="font-size:22px;font-weight:700;color:#111111;'
                f'margin-bottom:4px;">{label}</div>',
                unsafe_allow_html=True
            )
            st.markdown(
                f'<div style="font-size:13px;color:#6B7280;margin-bottom:20px;">'
                f'{s["total_scenarios"]} cenarios calculados em '
                f'{len(selected_regions)} regioes · '
                f'Base: {base["region"]} · 730h/mes · 50% CPU</div>',
                unsafe_allow_html=True
            )

            c1, c2, c3, c4 = st.columns(4)
            best_sci  = s["best_sci_scenario"]
            best_cost = s["best_cost_scenario"]
            c1.metric("Cenario base",
                      f"${base['cost_usd_month']:.2f}/mo",
                      f"SCI {base['sci_score']:.4f} gCO₂/h")
            if best_sci:
                c2.metric("Menor SCI encontrado",
                          f"{best_sci['sci_score']:.4f} gCO₂/h",
                          f"{best_sci['instance_type']} · {best_sci['region']}")
            if best_cost:
                c3.metric("Menor custo encontrado",
                          f"${best_cost['cost_usd_month']:.2f}/mo",
                          f"{best_cost['instance_type']} · {best_cost['region']}")
            c4.metric("Pareto otimo",
                      s["pareto_count"],
                      f"de {s['total_scenarios']} cenarios")

            if best_sci and base:
                sci_gain  = s.get("sci_reduction_vs_base", 0)
                cost_diff = best_sci["cost_usd_month"] - base["cost_usd_month"]
                cost_str  = (f"${abs(cost_diff):.2f}/mo cheaper" if cost_diff < 0
                             else f"${cost_diff:.2f}/mo more" if cost_diff > 0
                             else "mesmo custo")
                if sci_gain > 0:
                    banner(
                        f"Melhor alternativa Pareto: "
                        f"<b>{best_sci['instance_type']} in {best_sci['region']}</b> — "
                        f"<b>{sci_gain}% menos carbono</b> e {cost_str} vs. base scenario."
                    )

            divider()

            section(
                "Pareto Front — Custo vs. Carbono",
                "Each point is one scenario (instance + region). "
                "Green points are Pareto optimal: no other scenario is "
                "simultaneously cheaper AND lower-carbon. "
                "The orange star marks your base scenario. "
                "Circles = base instance family · Diamonds = equivalent families."
            )

            base_fam = instance_type.split(".")[0]
            df["fam_type"] = df["instance_type"].apply(
                lambda x: "Base family" if x.split(".")[0] == base_fam else "Equivalent"
            )

            fig = go.Figure()
            for status, color, opacity in [
                ("Pareto otimo", "#16A34A", 0.95),
                ("Dominated",      "#D1D5DB", 0.9),
            ]:
                for fam, sym in [("Base family","circle"), ("Equivalent","diamond")]:
                    sub = df[(df["Status"]==status) & (df["fam_type"]==fam)]
                    if not len(sub): continue
                    fig.add_trace(go.Scatter(
                        x=sub["cost_usd_month"], y=sub["sci_score"],
                        mode="markers", name=f"{status} · {fam}",
                        marker=dict(
                            symbol=sym, size=10, color=color, opacity=opacity,
                            line=dict(width=1, color="#FFFFFF"),
                        ),
                        customdata=sub[["instance_type","region","carbon_intensity"]].values,
                        hovertemplate=(
                            "<b>%{customdata[0]} in %{customdata[1]}</b><br>"
                            "Cost: $%{x:.2f}/mo<br>"
                            "SCI: %{y:.4f} gCO₂/h<br>"
                            "Grid intensity: %{customdata[2]:.0f} gCO₂/kWh<extra></extra>"
                        ),
                    ))

            if base:
                fig.add_trace(go.Scatter(
                    x=[base["cost_usd_month"]], y=[base["sci_score"]],
                    mode="markers", name="Cenario base",
                    marker=dict(symbol="star", size=18, color="#F59E0B",
                                line=dict(width=1, color="#FFFFFF")),
                    hovertemplate=(
                        f"<b>Base: {base['instance_type']} in {base['region']}</b><br>"
                        f"Cost: ${base['cost_usd_month']:.2f}/mo<br>"
                        f"SCI: {base['sci_score']:.4f} gCO₂/h<extra></extra>"
                    ),
                ))

            fig.update_layout(**chart_layout(480))
            fig.update_layout(
                xaxis_title="Custo mensal (USD)",
                yaxis_title="SCI score (gCO2eq por hora de compute)",
                legend=dict(itemsizing="constant"),
            )
            st.plotly_chart(fig, use_container_width=True)

            divider()

            section(
                "Solucoes Pareto Otimas",
                "These are the only scenarios where no other combination of instance "
                "and region is simultaneously cheaper and lower-carbon. "
                "Moving to any of these is a strict improvement over the base scenario."
            )

            pdf = pd.DataFrame(pareto)[[
                "instance_type","region","cost_usd_month",
                "sci_score","carbon_intensity",
            ]].rename(columns={
                "instance_type": "Instancia",
                "region": "Regiao",
                "cost_usd_month": "Custo / mes (USD)",
                "sci_score": "SCI (gCO₂/h)",
                "carbon_intensity": "Grid intensity (gCO2/kWh)",
            }).sort_values("SCI (gCO₂/h)")

            st.dataframe(
                pdf.style
                    .format({
                        "Custo / mes (USD)": "${:.2f}",
                        "SCI (gCO₂/h)": "{:.4f}",
                        "Grid intensity (gCO2/kWh)": "{:.0f}",
                    })
                    .background_gradient(subset=["SCI (gCO₂/h)"], cmap="RdYlGn_r"),
                use_container_width=True, hide_index=True,
            )


# ══════════════════════════════════════════════════════════════════════════
# TAB 2 — ARCHITECTURE
# ══════════════════════════════════════════════════════════════════════════
with tab2:

    st.markdown("""
    <div style="background:#F0FDF4;border:1px solid #BBF7D0;border-radius:8px;
                padding:16px 20px;margin-bottom:20px;">
        <div style="font-size:13px;font-weight:600;color:#15803D;margin-bottom:6px;">
            Como funciona a analise de arquitetura?
        </div>
        <div style="font-size:13px;color:#374151;line-height:1.7;">
            A real AWS deployment is not just one instance — it typically combines
            <b>EC2</b> (virtual machines), <b>RDS</b> (managed databases),
            and <b>Lambda</b> (serverless functions).
            GreenArch calculates the <b>total SCI score</b> for the entire architecture
            and compares it across AWS regions, so you can see where it would be
            cheapest and lowest-carbon <b>before deploying</b>.
        </div>
        <div style="font-size:13px;color:#374151;line-height:1.7;margin-top:8px;">
            Pricing data is fetched in real time from the
            <b>AWS Pricing Bulk API</b> (public, no credentials required).
            Carbon intensity per region comes from
            <b>Electricity Maps, EPA eGRID and IEA</b> (2022–2023 annual averages).
        </div>
    </div>
    """, unsafe_allow_html=True)

    import json as _json
    from pathlib import Path as _Path
    BENCH_DIR = _Path(__file__).parent / "benchmarks" / "architectures"
    BENCH_OPTIONS = {}
    for bf in sorted(BENCH_DIR.glob("*.json")):
        try:
            with open(bf) as _f:
                _d = _json.load(_f)
            if _d["name"] in BENCH_ALLOWED:
                BENCH_OPTIONS[_d["name"]] = _d
        except:
            pass

    section("Escolha uma arquitetura",
            "Dois padroes tipicos de implantacao AWS. Clique em um para carrega-lo.")

    cols = st.columns(2)
    ARCH_DESCRIPTIONS = {
        "Startup Web Simples": (
            "A small web application with one EC2 instance as the application server "
            "and one RDS instance as the relational database. "
            "Typical of MVPs and early-stage products."
        ),
        "API REST Media Escala": (
            "A medium-scale REST API with three EC2 instances behind a load balancer "
            "and a Multi-AZ PostgreSQL RDS database for high availability. "
            "Typical of growing SaaS products."
        ),
    }

    for ci, (bname, bdata) in enumerate(BENCH_OPTIONS.items()):
        comps = bdata.get("components", [])
        types = " + ".join(sorted(set(c["type"].upper() for c in comps)))
        desc  = ARCH_DESCRIPTIONS.get(bname, "")
        def _comp_label(c):
            if c["type"] == "lambda":
                return f"Lambda {c.get('invocations',0)//1_000_000}M inv"
            return f"{c['type'].upper()} {c.get('instance','')}"
        comp_lines = "  ·  ".join(_comp_label(c) for c in comps)
        with cols[ci]:
            st.markdown(
                f'<div style="border:1px solid #E5E7EB;border-radius:8px;'
                f'padding:20px;background:#FAFAFA;height:100%;">'
                f'<div style="font-size:16px;font-weight:600;color:#111111;'
                f'margin-bottom:6px;">{bname}</div>'
                f'<div style="font-size:12px;color:#9CA3AF;margin-bottom:10px;">'
                f'{len(comps)} components &nbsp;·&nbsp; {types}</div>'
                f'<div style="font-size:13px;color:#374151;line-height:1.6;'
                f'margin-bottom:12px;">{desc}</div>'
                f'<div style="font-size:11px;color:#9CA3AF;font-family:monospace;">'
                f'{comp_lines}</div>'
                f'</div>',
                unsafe_allow_html=True
            )
            st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
            if st.button(f"Carregar — {bname}", key=f"load_{ci}",
                         use_container_width=True, type="primary"):
                loaded = []
                for c in comps:
                    ct = c.get("type","").lower()
                    if ct == "ec2":
                        loaded.append({
                            "type":"ec2","instance":c.get("instance","t3.medium"),
                            "hours":c.get("hours",730),"cpu":c.get("cpu",0.5),
                            "os":c.get("os","Linux"),
                            "label":f"EC2  {c.get('instance')}",
                        })
                    elif ct == "rds":
                        loaded.append({
                            "type":"rds","instance":c.get("instance","db.t3.micro"),
                            "engine":c.get("engine","MySQL"),
                            "cpu":c.get("cpu",0.3),
                            "multi_az":c.get("multi_az",False),
                            "hours":730,
                            "label":f"RDS  {c.get('instance')} ({c.get('engine','MySQL')})",
                        })
                    elif ct == "lambda":
                        inv = c.get("invocations",1000000)
                        loaded.append({
                            "type":"lambda","invocations":inv,
                            "duration_ms":c.get("duration_ms",200),
                            "memory_mb":c.get("memory_mb",512),
                            "architecture":c.get("architecture","x86"),
                            "label":f"Lambda  {inv/1e6:.1f}M inv/mo",
                        })
                st.session_state["demo_arch_comps"] = loaded
                st.session_state["demo_arch_name"]  = bname
                st.session_state.pop("demo_arch_results", None)
                st.rerun()

    if "demo_arch_comps" in st.session_state and st.session_state["demo_arch_comps"]:
        divider()
        arch_name = st.session_state.get("demo_arch_name","Architecture")
        comps     = st.session_state["demo_arch_comps"]

        st.markdown(
            f'<div style="font-size:20px;font-weight:700;color:#111111;'
            f'margin-bottom:4px;">{arch_name}</div>',
            unsafe_allow_html=True
        )
        comp_str = "  ·  ".join(c["label"] for c in comps)
        st.markdown(
            f'<div style="font-size:12px;color:#9CA3AF;margin-bottom:20px;">'
            f'{comp_str}</div>',
            unsafe_allow_html=True
        )

        col_cfg, col_res = st.columns([1, 2], gap="large")

        with col_cfg:
            section("Selecionar regioes",
                    "The system will calculate the total SCI and cost of this "
                    "architecture in each selected region.")
            arch_regs = []
            for reg in list(CARBON_INTENSITY_STATIC.keys()):
                intensity = CARBON_INTENSITY_STATIC[reg]
                if st.checkbox(
                    f"{reg}  ·  {intensity} gCO₂/kWh",
                    value=reg in DEFAULT_REGIONS,
                    key=f"ar2_{reg}",
                ):
                    arch_regs.append(reg)

            if st.button("Calcular", type="primary",
                         use_container_width=True, key="calc_arch2"):
                if not arch_regs:
                    st.warning("Select at least one region.")
                else:
                    calc = ArchitectureCalculator()
                    results = []
                    with st.spinner("Calculando..."):
                        for reg in arch_regs:
                            try:
                                r = calc.calculate({
                                    "name": arch_name, "region": reg,
                                    "components": comps,
                                })
                                results.append({
                                    "region": reg,
                                    "cost_usd_month": r["totals"]["cost_usd_month"],
                                    "sci_score": r["totals"]["sci_score_gco2_per_hour"],
                                    "carbon_intensity": r["carbon_intensity_gco2_kwh"],
                                })
                            except Exception as e:
                                st.warning(f"{reg}: {e}")
                    st.session_state["demo_arch_results"] = results

            if st.button("Limpar selecao", key="clear2"):
                st.session_state.pop("demo_arch_comps", None)
                st.session_state.pop("demo_arch_results", None)
                st.session_state.pop("demo_arch_name", None)
                st.rerun()

        with col_res:
            if "demo_arch_results" in st.session_state and \
               st.session_state["demo_arch_results"]:
                arch_df  = pd.DataFrame(st.session_state["demo_arch_results"])
                base_row = arch_df[arch_df["region"] == "us-east-1"]
                bsci  = (base_row["sci_score"].values[0] if len(base_row) > 0
                         else arch_df["sci_score"].max())
                bcost = (base_row["cost_usd_month"].values[0] if len(base_row) > 0
                         else arch_df["cost_usd_month"].max())
                best  = arch_df.loc[arch_df["sci_score"].idxmin()]
                red   = round((bsci - best["sci_score"]) / bsci * 100, 1)
                diff  = best["cost_usd_month"] - bcost

                m1, m2, m3 = st.columns(3)
                m1.metric("Base (us-east-1)",
                          f"{bsci:.2f} gCO₂/h", f"${bcost:.0f}/mo")
                m2.metric("Melhor regiao", best["region"],
                          f"{best['sci_score']:.2f} gCO₂/h")
                m3.metric("Reducao de carbono", f"{red}%",
                          f"${abs(diff):.0f}/mes {'mais barato' if diff<0 else 'a mais'}")

                cost_str = (f"${abs(diff):.2f}/mes mais barato" if diff < 0
                            else f"${diff:.2f}/mes a mais" if diff > 0
                            else "mesmo custo")
                banner(
                    f"Implantar <b>{arch_name}</b> em <b>{best['region']}</b> "
                    f"em vez de us-east-1 reduz o carbono em <b>{red}%</b> "
                    f"e custa {cost_str} — sem alterar nenhum codigo ou configuracao."
                )

                fig_a = go.Figure()
                fig_a.add_trace(go.Scatter(
                    x=arch_df["cost_usd_month"], y=arch_df["sci_score"],
                    mode="markers+text", text=arch_df["region"],
                    textposition="middle right",
                    textfont=dict(size=11, color="#6B7280", family="Inter, sans-serif"),
                    marker=dict(
                        size=11,
                        color=arch_df["sci_score"],
                        colorscale=[[0,"#16A34A"],[0.5,"#F59E0B"],[1,"#DC2626"]],
                        line=dict(width=1, color="#FFFFFF"),
                    ),
                    hovertemplate=(
                        "<b>%{text}</b><br>Cost: $%{x:.2f}/mo<br>"
                        "SCI: %{y:.4f} gCO₂/h<extra></extra>"
                    ),
                    showlegend=False,
                ))
                if len(base_row) > 0:
                    fig_a.add_trace(go.Scatter(
                        x=[base_row["cost_usd_month"].values[0]],
                        y=[base_row["sci_score"].values[0]],
                        mode="markers", name="us-east-1 (base)",
                        marker=dict(symbol="star", size=18, color="#F59E0B",
                                    line=dict(width=1, color="#FFFFFF")),
                    ))
                fig_a.update_layout(
                    **chart_layout(360),
                    xaxis_title="Custo total / mes (USD)",
                    yaxis_title="SCI total (gCO2eq/h)",
                )
                st.plotly_chart(fig_a, use_container_width=True)

                tbl = arch_df[["region","cost_usd_month","sci_score","carbon_intensity"]
                              ].sort_values("sci_score").rename(columns={
                    "region":"Regiao",
                    "cost_usd_month":"Custo / mes (USD)",
                    "sci_score":"SCI total (gCO2/h)",
                    "carbon_intensity":"Grid intensity (gCO2/kWh)",
                })
                st.dataframe(
                    tbl.style
                        .format({
                            "Custo / mes (USD)": "${:.2f}",
                            "SCI total (gCO2/h)": "{:.4f}",
                            "Grid intensity (gCO2/kWh)": "{:.0f}",
                        })
                        .background_gradient(
                            subset=["SCI total (gCO2/h)"], cmap="RdYlGn_r"
                        ),
                    use_container_width=True, hide_index=True,
                )

# ── Footer ─────────────────────────────────────────────────────────────────
st.markdown("""
<div style="border-top:1px solid #E5E7EB;margin-top:40px;padding:16px 0;
            display:flex;justify-content:space-between;
            font-size:12px;color:#9CA3AF;">
    <span>AWS Pricing Bulk API &nbsp;·&nbsp; Electricity Maps &nbsp;·&nbsp;
          EPA eGRID &nbsp;·&nbsp; Cloud Carbon Footprint (ThoughtWorks)</span>
    <span>SCI — ISO/IEC 21031:2024</span>
</div>
""", unsafe_allow_html=True)
