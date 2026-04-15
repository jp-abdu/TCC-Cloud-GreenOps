"""
dashboard/app.py
----------------
GreenArch Dashboard — redesign minimalista tecnico.
Dark / Light mode. Verde como acento cirurgico. Sem emojis.

Rodar:
    python -m streamlit run dashboard/app.py
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

from core.scenario_engine import ScenarioEngine, EQUIVALENT_GROUPS
from core.architecture_calculator import ArchitectureCalculator
from core.data_sources.instance_energy import list_supported_instances
from core.data_sources.carbon_intensity import CARBON_INTENSITY_STATIC
from core.report_generator import generate_report

# ── Page config ───────────────────────────────────────────────────────────
st.set_page_config(
    page_title="GreenArch",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Dark / Light mode toggle via session_state ────────────────────────────
if "dark_mode" not in st.session_state:
    st.session_state["dark_mode"] = True

# ── CSS injection — sistema de design completo ────────────────────────────
def inject_css(dark: bool):
    if dark:
        bg         = "#0D0F0E"
        bg2        = "#141714"
        bg3        = "#1C201C"
        border     = "#252825"
        text       = "#E8EDE9"
        text2      = "#8A9B8C"
        text3      = "#5C6B5E"
        green      = "#3DBA6F"
        green_dim  = "#1F5E38"
        green_glow = "rgba(61,186,111,0.12)"
        red        = "#E05252"
        tab_active = "#3DBA6F"
        tab_text   = "#8A9B8C"
        input_bg   = "#1C201C"
        metric_bg  = "#141714"
        chart_bg   = "#0D0F0E"
        chart_grid = "#1C201C"
        chart_text = "#8A9B8C"
        toggle_icon = "☀"
        toggle_label = "Light"
    else:
        bg         = "#F7F8F7"
        bg2        = "#FFFFFF"
        bg3        = "#EFF2EF"
        border     = "#DDE4DE"
        text       = "#111411"
        text2      = "#4A5C4C"
        text3      = "#8A9B8C"
        green      = "#1F8C4B"
        green_dim  = "#D4EDE0"
        green_glow = "rgba(31,140,75,0.08)"
        red        = "#C0392B"
        tab_active = "#1F8C4B"
        tab_text   = "#4A5C4C"
        input_bg   = "#FFFFFF"
        metric_bg  = "#FFFFFF"
        chart_bg   = "#FFFFFF"
        chart_grid = "#EFF2EF"
        chart_text = "#4A5C4C"
        toggle_icon = "◑"
        toggle_label = "Dark"

    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@300;400;500;600&display=swap');

    /* ── Reset & base ── */
    html, body, [class*="css"] {{
        font-family: 'IBM Plex Sans', sans-serif !important;
        background-color: {bg} !important;
        color: {text} !important;
    }}

    .stApp {{
        background-color: {bg} !important;
    }}

    /* ── Header customizado ── */
    .ga-header {{
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 24px 0 20px 0;
        border-bottom: 1px solid {border};
        margin-bottom: 28px;
    }}
    .ga-wordmark {{
        font-family: 'IBM Plex Mono', monospace;
        font-size: 20px;
        font-weight: 500;
        color: {text};
        letter-spacing: -0.5px;
    }}
    .ga-wordmark span {{
        color: {green};
    }}
    .ga-tagline {{
        font-size: 11px;
        color: {text3};
        letter-spacing: 0.8px;
        text-transform: uppercase;
        margin-top: 2px;
    }}
    .ga-badge {{
        font-family: 'IBM Plex Mono', monospace;
        font-size: 10px;
        color: {green};
        border: 1px solid {green_dim};
        background: {green_glow};
        padding: 3px 8px;
        border-radius: 3px;
        letter-spacing: 0.5px;
    }}

    /* ── Abas ── */
    .stTabs [data-baseweb="tab-list"] {{
        background: transparent !important;
        border-bottom: 1px solid {border} !important;
        gap: 0 !important;
        padding: 0 !important;
    }}
    .stTabs [data-baseweb="tab"] {{
        font-family: 'IBM Plex Sans', sans-serif !important;
        font-size: 13px !important;
        font-weight: 400 !important;
        color: {tab_text} !important;
        background: transparent !important;
        border: none !important;
        border-bottom: 2px solid transparent !important;
        padding: 10px 20px !important;
        margin: 0 !important;
        letter-spacing: 0.2px !important;
    }}
    .stTabs [aria-selected="true"] {{
        color: {tab_active} !important;
        border-bottom: 2px solid {tab_active} !important;
        font-weight: 500 !important;
    }}
    .stTabs [data-baseweb="tab-panel"] {{
        padding-top: 24px !important;
    }}

    /* ── Metricas ── */
    [data-testid="stMetric"] {{
        background: {metric_bg} !important;
        border: 1px solid {border} !important;
        border-radius: 6px !important;
        padding: 16px 20px !important;
    }}
    [data-testid="stMetricLabel"] {{
        font-size: 11px !important;
        font-weight: 500 !important;
        color: {text3} !important;
        text-transform: uppercase !important;
        letter-spacing: 0.6px !important;
    }}
    [data-testid="stMetricValue"] {{
        font-family: 'IBM Plex Mono', monospace !important;
        font-size: 22px !important;
        font-weight: 500 !important;
        color: {text} !important;
    }}
    [data-testid="stMetricDelta"] {{
        font-family: 'IBM Plex Mono', monospace !important;
        font-size: 11px !important;
    }}

    /* ── Inputs / Selects / Sliders ── */
    .stSelectbox > div > div,
    .stMultiSelect > div > div {{
        background: {input_bg} !important;
        border: 1px solid {border} !important;
        border-radius: 4px !important;
        font-size: 13px !important;
        color: {text} !important;
    }}
    .stSlider [data-baseweb="slider"] {{
        padding: 0 !important;
    }}
    .stSlider [data-testid="stThumbValue"] {{
        font-family: 'IBM Plex Mono', monospace !important;
        font-size: 11px !important;
        color: {green} !important;
    }}

    /* ── Botoes ── */
    .stButton > button {{
        font-family: 'IBM Plex Sans', sans-serif !important;
        font-size: 13px !important;
        font-weight: 500 !important;
        border-radius: 4px !important;
        border: 1px solid {border} !important;
        background: transparent !important;
        color: {text} !important;
        padding: 6px 16px !important;
        transition: all 0.15s ease !important;
        letter-spacing: 0.2px !important;
    }}
    .stButton > button:hover {{
        border-color: {green} !important;
        color: {green} !important;
        background: {green_glow} !important;
    }}
    .stButton > button[kind="primary"] {{
        background: {green} !important;
        border-color: {green} !important;
        color: {'#0D0F0E' if dark else '#FFFFFF'} !important;
    }}
    .stButton > button[kind="primary"]:hover {{
        opacity: 0.88 !important;
    }}
    .stDownloadButton > button {{
        font-family: 'IBM Plex Sans', sans-serif !important;
        font-size: 13px !important;
        font-weight: 500 !important;
        border-radius: 4px !important;
        border: 1px solid {green} !important;
        background: {green_glow} !important;
        color: {green} !important;
        padding: 6px 16px !important;
    }}

    /* ── Formularios ── */
    [data-testid="stForm"] {{
        background: {bg2} !important;
        border: 1px solid {border} !important;
        border-radius: 6px !important;
        padding: 20px !important;
    }}

    /* ── Dataframes / tabelas ── */
    [data-testid="stDataFrame"] {{
        border: 1px solid {border} !important;
        border-radius: 6px !important;
        overflow: hidden !important;
    }}

    /* ── Expander ── */
    [data-testid="stExpander"] {{
        border: 1px solid {border} !important;
        border-radius: 6px !important;
        background: {bg2} !important;
    }}
    [data-testid="stExpander"] summary {{
        font-size: 13px !important;
        color: {text2} !important;
        font-weight: 400 !important;
    }}

    /* ── Alerts / banners ── */
    [data-testid="stAlert"] {{
        border-radius: 4px !important;
        font-size: 13px !important;
    }}

    /* ── Divider ── */
    hr {{
        border: none !important;
        border-top: 1px solid {border} !important;
        margin: 20px 0 !important;
    }}

    /* ── Labels / captions ── */
    .stMarkdown p, .stCaption {{
        font-size: 13px !important;
        color: {text2} !important;
        line-height: 1.6 !important;
    }}
    label[data-testid="stWidgetLabel"] p {{
        font-size: 12px !important;
        font-weight: 500 !important;
        color: {text2} !important;
        text-transform: uppercase !important;
        letter-spacing: 0.5px !important;
    }}

    /* ── Checkboxes ── */
    .stCheckbox label p {{
        font-size: 12px !important;
        font-family: 'IBM Plex Mono', monospace !important;
        color: {text2} !important;
        text-transform: none !important;
        letter-spacing: 0 !important;
    }}
    .stCheckbox [data-testid="stCheckbox"] input:checked + div {{
        background: {green} !important;
        border-color: {green} !important;
    }}

    /* ── Secoes de titulo ── */
    .ga-section {{
        font-family: 'IBM Plex Sans', sans-serif;
        font-size: 13px;
        font-weight: 600;
        color: {text3};
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 12px;
        margin-top: 24px;
    }}
    .ga-title {{
        font-family: 'IBM Plex Sans', sans-serif;
        font-size: 18px;
        font-weight: 500;
        color: {text};
        margin-bottom: 4px;
    }}
    .ga-subtitle {{
        font-family: 'IBM Plex Sans', sans-serif;
        font-size: 12px;
        color: {text3};
        margin-bottom: 20px;
    }}

    /* ── Banner de resultado ── */
    .ga-banner {{
        background: {green_glow};
        border: 1px solid {green_dim};
        border-left: 3px solid {green};
        border-radius: 4px;
        padding: 12px 16px;
        font-size: 13px;
        color: {text};
        margin: 16px 0;
        line-height: 1.6;
    }}
    .ga-banner b {{
        color: {green};
        font-weight: 600;
    }}

    /* ── Toggle dark/light ── */
    .ga-toggle-btn {{
        display: inline-flex;
        align-items: center;
        gap: 6px;
        font-family: 'IBM Plex Mono', monospace;
        font-size: 11px;
        color: {text3};
        cursor: pointer;
        border: 1px solid {border};
        border-radius: 4px;
        padding: 4px 10px;
        background: transparent;
    }}

    /* ── Scrollbar ── */
    ::-webkit-scrollbar {{ width: 4px; height: 4px; }}
    ::-webkit-scrollbar-track {{ background: {bg}; }}
    ::-webkit-scrollbar-thumb {{ background: {border}; border-radius: 2px; }}
    ::-webkit-scrollbar-thumb:hover {{ background: {text3}; }}

    /* ── Oculta elementos Streamlit padrao ── */
    #MainMenu, footer, header [data-testid="stToolbar"] {{ display: none !important; }}
    .stDeployButton {{ display: none !important; }}
    [data-testid="stSidebarCollapsedControl"] {{ display: none !important; }}

    </style>
    """, unsafe_allow_html=True)

    return {
        "bg": bg, "bg2": bg2, "bg3": bg3,
        "border": border, "text": text, "text2": text2, "text3": text3,
        "green": green, "green_dim": green_dim, "green_glow": green_glow,
        "red": red, "chart_bg": chart_bg, "chart_grid": chart_grid,
        "chart_text": chart_text, "toggle_icon": toggle_icon,
        "toggle_label": toggle_label,
    }

dark = st.session_state["dark_mode"]
C = inject_css(dark)

# ── Chart theme helper ─────────────────────────────────────────────────────
def chart_layout(height=440, **kwargs):
    return dict(
        height=height,
        font=dict(family="IBM Plex Mono, monospace", size=11, color=C["chart_text"]),
        plot_bgcolor=C["chart_bg"],
        paper_bgcolor=C["chart_bg"],
        xaxis=dict(showgrid=True, gridcolor=C["chart_grid"],
                   gridwidth=1, zeroline=False, tickfont=dict(size=10)),
        yaxis=dict(showgrid=True, gridcolor=C["chart_grid"],
                   gridwidth=1, zeroline=False, tickfont=dict(size=10)),
        legend=dict(font=dict(size=10, color=C["chart_text"]),
                    bgcolor="rgba(0,0,0,0)", borderwidth=0),
        margin=dict(t=24, b=40, l=48, r=120),
        **kwargs,
    )

# ── Constantes ─────────────────────────────────────────────────────────────
REGION_GROUPS = {
    "North America": ["us-east-1", "us-east-2", "us-west-1", "us-west-2", "ca-central-1"],
    "Europe":        ["eu-west-1", "eu-west-2", "eu-west-3", "eu-central-1", "eu-north-1", "eu-south-1"],
    "Asia Pacific":  ["ap-southeast-1", "ap-southeast-2", "ap-northeast-1", "ap-northeast-2", "ap-south-1"],
    "South America": ["sa-east-1"],
    "Africa / ME":   ["af-south-1", "me-south-1"],
}
DEFAULT_REGIONS = [
    "us-east-1", "us-west-2", "eu-north-1", "eu-west-1",
    "eu-central-1", "sa-east-1", "ap-south-1", "ap-northeast-1",
]
ALL_INSTANCES = list_supported_instances()
RDS_INSTANCES = [
    "db.t3.micro", "db.t3.small", "db.t3.medium", "db.t3.large",
    "db.t3.xlarge", "db.t3.2xlarge", "db.t4g.micro", "db.t4g.small",
    "db.t4g.medium", "db.t4g.large", "db.m5.large", "db.m5.xlarge",
    "db.m5.2xlarge", "db.m5.4xlarge", "db.m6g.large", "db.m6g.xlarge",
    "db.r5.large", "db.r5.xlarge", "db.r5.2xlarge",
    "db.r6g.large", "db.r6g.xlarge",
]

# ── Header ─────────────────────────────────────────────────────────────────
col_logo, col_toggle = st.columns([5, 1])
with col_logo:
    st.markdown(f"""
    <div class="ga-header">
        <div>
            <div class="ga-wordmark">Green<span>Arch</span></div>
            <div class="ga-tagline">Carbon &amp; Cost Intelligence for AWS</div>
        </div>
        <div class="ga-badge">ISO/IEC 21031:2024</div>
    </div>
    """, unsafe_allow_html=True)
with col_toggle:
    st.markdown("<div style='padding-top: 24px'>", unsafe_allow_html=True)
    if st.button(
        f"{C['toggle_icon']}  {C['toggle_label']} mode",
        key="toggle_theme",
        help="Alternar entre dark e light mode",
    ):
        st.session_state["dark_mode"] = not st.session_state["dark_mode"]
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

# ── Abas ───────────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["Instance", "Architecture", "Family Comparison"])


# ══════════════════════════════════════════════════════════════════════════
# TAB 1 — INSTANCE
# ══════════════════════════════════════════════════════════════════════════
with tab1:
    col_main, col_side = st.columns([3, 1], gap="large")

    with col_side:
        st.markdown('<div class="ga-section">Configure</div>', unsafe_allow_html=True)
        with st.form("form_instance"):
            instance_type = st.selectbox(
                "Base instance",
                options=ALL_INSTANCES,
                index=ALL_INSTANCES.index("t3.medium"),
            )
            hours    = st.slider("Hours / month", 1, 730, 730)
            cpu_util = st.slider("CPU utilization (%)", 1, 100, 50) / 100.0
            os_type  = st.selectbox("Operating system", ["Linux", "Windows"])

            st.markdown('<div class="ga-section" style="margin-top:16px">Regions</div>',
                        unsafe_allow_html=True)
            selected_regions = []
            for continent, regs in REGION_GROUPS.items():
                with st.expander(continent, expanded=(continent == "North America")):
                    for reg in regs:
                        intensity = CARBON_INTENSITY_STATIC.get(reg, 0)
                        if st.checkbox(f"{reg}  ·  {intensity}g",
                                       value=reg in DEFAULT_REGIONS,
                                       key=f"t1_{reg}"):
                            selected_regions.append(reg)

            submitted1 = st.form_submit_button("Calculate", type="primary",
                                               use_container_width=True)

        equiv = EQUIVALENT_GROUPS.get(instance_type, [instance_type])
        st.caption(f"Equivalent instances: {', '.join(equiv)}")
        st.caption(f"Scenarios to calculate: {len(equiv) * len(selected_regions)}")

    with col_main:
        if submitted1:
            if not selected_regions:
                st.warning("Select at least one region.")
            else:
                engine = ScenarioEngine()
                with st.spinner(f"Running {len(equiv) * len(selected_regions)} scenarios..."):
                    result1 = engine.compare(
                        instance_type=instance_type,
                        region=selected_regions[0],
                        hours_per_month=hours,
                        cpu_utilization=cpu_util,
                        os=os_type,
                        regions=selected_regions,
                    )
                st.session_state["result1"] = result1
                st.session_state["label1"]  = instance_type

        if "result1" not in st.session_state:
            st.markdown(
                '<div style="margin-top:80px; text-align:center; color:#5C6B5E; '
                'font-family:\'IBM Plex Mono\', monospace; font-size:13px;">'
                'Configure the workload and click Calculate.</div>',
                unsafe_allow_html=True
            )
        else:
            result1 = st.session_state["result1"]
            label1  = st.session_state["label1"]
            s       = result1["summary"]
            base    = result1["base_scenario"]
            pareto  = result1["pareto_front"]
            df1     = pd.DataFrame(result1["all_scenarios"])
            df1["Status"] = df1["pareto_optimal"].map(
                {True: "Pareto optimal", False: "Dominated"})

            # Metricas
            st.markdown(f'<div class="ga-title">{label1}</div>', unsafe_allow_html=True)
            st.markdown('<div class="ga-subtitle">Scenario analysis results</div>',
                        unsafe_allow_html=True)

            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Base scenario", f"${base['cost_usd_month']:.2f}/mo",
                      f"{base['sci_score']:.4f} gCO₂/h")
            best_sci  = s["best_sci_scenario"]
            best_cost = s["best_cost_scenario"]
            if best_sci:
                c2.metric("Lowest SCI", f"{best_sci['sci_score']:.4f} gCO₂/h",
                          f"{best_sci['instance_type']} · {best_sci['region']}")
            if best_cost:
                c3.metric("Lowest cost", f"${best_cost['cost_usd_month']:.2f}/mo",
                          f"{best_cost['instance_type']} · {best_cost['region']}")
            c4.metric("Pareto optimal", s["pareto_count"],
                      f"of {s['total_scenarios']} scenarios")

            # Banner
            if best_sci and base:
                sci_gain  = s.get("sci_reduction_vs_base", 0)
                cost_diff = best_sci["cost_usd_month"] - base["cost_usd_month"]
                custo_str = (f"${abs(cost_diff):.2f}/mo cheaper" if cost_diff < 0
                             else f"${cost_diff:.2f}/mo more" if cost_diff > 0
                             else "same cost")
                if sci_gain > 0:
                    st.markdown(
                        f'<div class="ga-banner">Best Pareto alternative: '
                        f'<b>{best_sci["instance_type"]} · {best_sci["region"]}</b> — '
                        f'<b>{sci_gain}% less carbon</b> and {custo_str} vs. base.</div>',
                        unsafe_allow_html=True
                    )

            # Indice de eficiencia
            st.markdown('<hr>', unsafe_allow_html=True)
            st.markdown('<div class="ga-section">Efficiency Index</div>',
                        unsafe_allow_html=True)
            st.caption("Composite score combining SCI and cost. Adjust weight to prioritize carbon or cost.")

            peso_carbono = st.slider(
                "Priority: Cost — Carbon",
                0, 100, 50, 10, format="%d%%",
                key="peso_t1",
            ) / 100.0
            peso_custo = 1 - peso_carbono

            sci_min  = df1["sci_score"].min()
            sci_max  = df1["sci_score"].max()
            cost_min = df1["cost_usd_month"].min()
            cost_max = df1["cost_usd_month"].max()

            def norm(val, vmin, vmax):
                return 0.5 if vmax == vmin else (val - vmin) / (vmax - vmin)

            df1["score"] = (1 - (
                peso_carbono * df1["sci_score"].apply(lambda v: norm(v, sci_min, sci_max)) +
                peso_custo   * df1["cost_usd_month"].apply(lambda v: norm(v, cost_min, cost_max))
            ) * 100).round(1)

            df_score = df1[["instance_type", "region", "cost_usd_month",
                            "sci_score", "score", "Status"]].sort_values(
                "score", ascending=False).head(10).rename(columns={
                    "instance_type": "Instance", "region": "Region",
                    "cost_usd_month": "Cost/mo", "sci_score": "SCI (gCO₂/h)",
                    "score": "Score",
                })

            def hl_pareto(row):
                if row["Status"] == "Pareto optimal":
                    return [f"color: {C['green']}; font-weight: 500"] * len(row)
                return [""] * len(row)

            st.dataframe(
                df_score.style.apply(hl_pareto, axis=1).format({
                    "Cost/mo": "${:.2f}", "SCI (gCO₂/h)": "{:.4f}", "Score": "{:.1f}",
                }),
                use_container_width=True, hide_index=True,
            )

            # Pareto-front chart
            st.markdown('<hr>', unsafe_allow_html=True)
            st.markdown('<div class="ga-section">Pareto Front — Cost vs. Carbon</div>',
                        unsafe_allow_html=True)

            # Mostra as familias equivalentes exploradas
            equiv_list = EQUIVALENT_GROUPS.get(instance_type, [instance_type])
            base_fam   = instance_type.split(".")[0]
            equiv_fams = sorted(set(
                e.split(".")[0] for e in equiv_list if e.split(".")[0] != base_fam
            ))
            if equiv_fams:
                equiv_note = (
                    f"Exploring <b>{instance_type}</b> (base, circle) "
                    f"and equivalent families: <b>{'</b>, <b>'.join(equiv_fams)}</b> (diamond). "
                    f"Equivalent instances have the same vCPU count and workload profile."
                )
            else:
                equiv_note = f"Exploring <b>{instance_type}</b> only — no equivalent families defined."

            st.markdown(
                f'<div style="font-size:12px; color:{C["text2"]}; margin-bottom:8px;">' +
                equiv_note + '</div>',
                unsafe_allow_html=True
            )
            st.caption("Green = Pareto optimal  ·  Gray = Dominated  ·  Star = base  ·  Circle = base family  ·  Diamond = equivalent")

            # Marca qual familia e base vs equivalente
            base_family = instance_type.split(".")[0]  # ex: "t3" de "t3.medium"
            df1["family"] = df1["instance_type"].apply(
                lambda x: "Base family" if x.split(".")[0] == base_family else "Equivalent"
            )

            # Grafico sem texto — hover rico, formas diferentes por familia
            fig1 = go.Figure()

            for status, color in [("Pareto optimal", C["green"]), ("Dominated", C["text3"])]:
                for family, symbol in [("Base family", "circle"), ("Equivalent", "diamond")]:
                    mask = (df1["Status"] == status) & (df1["family"] == family)
                    sub  = df1[mask]
                    if len(sub) == 0:
                        continue
                    fig1.add_trace(go.Scatter(
                        x=sub["cost_usd_month"], y=sub["sci_score"],
                        mode="markers",
                        name=f"{status} · {family}",
                        marker=dict(
                            symbol=symbol, size=9,
                            color=color,
                            opacity=0.9 if status == "Pareto optimal" else 0.45,
                            line=dict(width=0.5, color=C["bg"]),
                        ),
                        customdata=sub[["instance_type","region","family"]].assign(
                            ci=sub["carbon_intensity"] if "carbon_intensity" in sub.columns else 0
                        ).values,
                        hovertemplate=(
                            "<b>%{customdata[0]} · %{customdata[1]}</b><br>"
                            "Cost: $%{x:.2f}/mo<br>"
                            "SCI: %{y:.4f} gCO₂/h<br>"
                            "Grid: %{customdata[3]:.0f} gCO₂/kWh<br>"
                            "Family: %{customdata[2]}<extra></extra>"
                        ),
                    ))

            # Estrela para o cenario base
            if base:
                fig1.add_trace(go.Scatter(
                    x=[base["cost_usd_month"]], y=[base["sci_score"]],
                    mode="markers",
                    marker=dict(symbol="star", size=16, color="#E8963A",
                                line=dict(width=1, color=C["bg"])),
                    name="Base",
                    hovertemplate=(
                        f"<b>Base: {base['instance_type']} · {base['region']}</b><br>"
                        f"Cost: ${base['cost_usd_month']:.2f}/mo<br>"
                        f"SCI: {base['sci_score']:.4f} gCO₂/h<extra></extra>"
                    ),
                ))

            fig1.update_layout(**chart_layout(500))
            fig1.update_layout(
                legend=dict(itemsizing="constant"),
                xaxis_title="Monthly cost (USD)",
                yaxis_title="SCI score (gCO₂eq/h)",
            )
            st.plotly_chart(fig1, use_container_width=True)

            # Tabela Pareto
            st.markdown('<div class="ga-section">Pareto Optimal Solutions</div>',
                        unsafe_allow_html=True)
            st.caption("No other combination is simultaneously cheaper and lower-carbon.")
            pareto_df = pd.DataFrame(pareto)[[
                "instance_type", "region", "cost_usd_month", "sci_score",
                "carbon_intensity", "operational_carbon", "embodied_carbon",
            ]].rename(columns={
                "instance_type": "Instance", "region": "Region",
                "cost_usd_month": "Cost/mo", "sci_score": "SCI",
                "carbon_intensity": "Grid (gCO₂/kWh)",
                "operational_carbon": "Operational C.", "embodied_carbon": "Embodied C.",
            }).sort_values("SCI")
            st.dataframe(
                pareto_df.style
                    .format({"Cost/mo": "${:.2f}", "SCI": "{:.4f}",
                             "Grid (gCO₂/kWh)": "{:.0f}",
                             "Operational C.": "{:.4f}", "Embodied C.": "{:.2f}"})
                    .background_gradient(subset=["SCI"], cmap="RdYlGn_r"),
                use_container_width=True, hide_index=True,
            )

            with st.expander("All calculated scenarios"):
                full_df = df1[["instance_type", "region", "cost_usd_month",
                               "sci_score", "carbon_intensity", "Status"]].rename(columns={
                    "instance_type": "Instance", "region": "Region",
                    "cost_usd_month": "Cost/mo", "sci_score": "SCI",
                    "carbon_intensity": "Grid (gCO₂/kWh)",
                }).sort_values("SCI")
                st.dataframe(
                    full_df.style.apply(hl_pareto, axis=1).format({
                        "Cost/mo": "${:.2f}", "SCI": "{:.4f}", "Grid (gCO₂/kWh)": "{:.0f}",
                    }),
                    use_container_width=True, hide_index=True,
                )

            # SCI decomposition
            st.markdown('<hr>', unsafe_allow_html=True)
            st.markdown('<div class="ga-section">SCI Decomposition</div>',
                        unsafe_allow_html=True)
            st.caption("Operational = E × I (energy × grid intensity)  ·  Embodied = M (hardware manufacturing)")

            cmp = ([base] if base else []) + [p for p in pareto if not p["is_base"]]
            cdf = pd.DataFrame(cmp)
            cdf["lbl"] = cdf.apply(
                lambda r: f"{r['instance_type']}\n{r['region']}" +
                          (" (base)" if r["is_base"] else ""), axis=1)
            fig_bar = go.Figure()
            fig_bar.add_trace(go.Bar(name="Operational (E×I)",
                                     x=cdf["lbl"], y=cdf["operational_carbon"],
                                     marker_color=C["green"], marker_opacity=0.85))
            fig_bar.add_trace(go.Bar(name="Embodied (M)",
                                     x=cdf["lbl"], y=cdf["embodied_carbon"],
                                     marker_color=C["text3"], marker_opacity=0.6))
            fig_bar.update_layout(barmode="stack",
                                  **chart_layout(320, legend_title=""))
            fig_bar.update_layout(yaxis_title="gCO₂eq/h")
            st.plotly_chart(fig_bar, use_container_width=True)

            # PDF export
            st.markdown('<hr>', unsafe_allow_html=True)
            st.markdown('<div class="ga-section">Export</div>', unsafe_allow_html=True)

            if st.button("Generate PDF report", key="btn_pdf1"):
                with st.spinner("Generating report..."):
                    try:
                        pdf_bytes = generate_report(result1, label1)
                        st.session_state["pdf1_bytes"] = pdf_bytes
                        st.session_state["pdf1_label"] = label1
                    except Exception as e:
                        st.error(f"Error: {e}")

            if "pdf1_bytes" in st.session_state:
                st.download_button(
                    label="Download PDF",
                    data=st.session_state["pdf1_bytes"],
                    file_name=f"greenarch_{st.session_state['pdf1_label'].replace('.','_')}.pdf",
                    mime="application/pdf",
                    key="dl_pdf1",
                )


# ══════════════════════════════════════════════════════════════════════════
# TAB 2 — ARCHITECTURE
# ══════════════════════════════════════════════════════════════════════════
with tab2:
    st.markdown('<div class="ga-title">Architecture Builder</div>', unsafe_allow_html=True)
    st.markdown('<div class="ga-subtitle">Load a benchmark architecture or compose your own. Compare total SCI across regions.</div>', unsafe_allow_html=True)

    # ── Seletor de benchmarks ──────────────────────────────────────────────
    import json as _json
    from pathlib import Path as _Path

    BENCH_DIR = _Path(__file__).parent.parent / "benchmarks" / "architectures"
    BENCH_FILES = sorted(BENCH_DIR.glob("*.json"))
    BENCH_OPTIONS = {}
    for bf in BENCH_FILES:
        try:
            with open(bf) as _f:
                _d = _json.load(_f)
            BENCH_OPTIONS[_d["name"]] = _d
        except:
            pass

    if BENCH_OPTIONS:
        st.markdown('<div class="ga-section">Benchmark architectures</div>',
                    unsafe_allow_html=True)
        st.caption("Load a pre-defined benchmark architecture as starting point.")

        bench_cols = st.columns(4)
        for bi, (bname, bdata) in enumerate(BENCH_OPTIONS.items()):
            with bench_cols[bi % 4]:
                n_comps = len(bdata.get("components", []))
                types   = ", ".join(sorted(set(
                    c["type"].upper() for c in bdata.get("components", [])
                )))
                if st.button(
                    bname,
                    key=f"bench_{bi}",
                    help=f"{n_comps} components: {types}",
                    use_container_width=True,
                ):
                    # Converte JSON para formato interno de componentes
                    loaded = []
                    for c in bdata.get("components", []):
                        ct = c.get("type", "").lower()
                        if ct == "ec2":
                            loaded.append({
                                "type": "ec2",
                                "instance": c.get("instance", "t3.medium"),
                                "hours": c.get("hours", 730),
                                "cpu": c.get("cpu", 0.5),
                                "os": c.get("os", "Linux"),
                                "label": f"EC2  {c.get('instance')}  {c.get('hours',730)}h  {int(c.get('cpu',0.5)*100)}% CPU",
                            })
                        elif ct == "rds":
                            loaded.append({
                                "type": "rds",
                                "instance": c.get("instance", "db.t3.micro"),
                                "engine": c.get("engine", "MySQL"),
                                "cpu": c.get("cpu", 0.3),
                                "multi_az": c.get("multi_az", False),
                                "hours": c.get("hours", 730),
                                "label": f"RDS  {c.get('instance')}  {c.get('engine','MySQL')}",
                            })
                        elif ct == "lambda":
                            inv = c.get("invocations", 1000000)
                            loaded.append({
                                "type": "lambda",
                                "invocations": inv,
                                "duration_ms": c.get("duration_ms", 200),
                                "memory_mb": c.get("memory_mb", 512),
                                "architecture": c.get("architecture", "x86"),
                                "label": f"Lambda  {inv/1e6:.1f}M inv  {c.get('duration_ms',200)}ms  {c.get('memory_mb',512)}MB",
                            })
                    st.session_state["arch_components"] = loaded
                    st.session_state.pop("arch_results", None)
                    st.rerun()

        st.markdown('<hr>', unsafe_allow_html=True)

    col_build, col_arch = st.columns([1, 2], gap="large")

    with col_build:
        st.markdown('<div class="ga-section">Base region</div>', unsafe_allow_html=True)
        base_region = st.selectbox(
            "Region", options=list(CARBON_INTENSITY_STATIC.keys()),
            index=list(CARBON_INTENSITY_STATIC.keys()).index("us-east-1"),
            key="arch_region", label_visibility="collapsed",
        )

        if "arch_components" not in st.session_state:
            st.session_state["arch_components"] = []

        st.markdown('<div class="ga-section">Add component</div>', unsafe_allow_html=True)
        with st.expander("+ New component",
                          expanded=len(st.session_state["arch_components"]) == 0):
            comp_type = st.selectbox("Type", ["EC2", "RDS", "Lambda"], key="new_comp_type")

            if comp_type == "EC2":
                new_inst  = st.selectbox("Instance", ALL_INSTANCES, key="new_ec2_inst")
                new_hours = st.number_input("Hours/mo", 1, 730, 730, key="new_ec2_h")
                new_cpu   = st.slider("CPU (%)", 1, 100, 50, key="new_ec2_cpu")
                new_os    = st.selectbox("OS", ["Linux", "Windows"], key="new_ec2_os")
                preview   = f"EC2  {new_inst}  {new_hours}h  {new_cpu}% CPU"

            elif comp_type == "RDS":
                new_rds_inst   = st.selectbox("Instance", RDS_INSTANCES, key="new_rds_inst")
                new_rds_engine = st.selectbox("Engine",
                                              ["MySQL", "PostgreSQL", "MariaDB"],
                                              key="new_rds_eng")
                new_rds_cpu    = st.slider("CPU (%)", 1, 100, 30, key="new_rds_cpu")
                new_rds_multi  = st.checkbox("Multi-AZ", key="new_rds_multi")
                preview = f"RDS  {new_rds_inst}  {new_rds_engine}"

            elif comp_type == "Lambda":
                new_inv  = st.number_input("Invocations/mo (M)", 0.1, 1000.0,
                                           1.0, 0.1, key="new_lambda_inv")
                new_dur  = st.number_input("Avg duration (ms)", 1, 30000,
                                           200, key="new_lambda_dur")
                new_mem  = st.selectbox("Memory (MB)",
                                        [128, 256, 512, 1024, 2048, 4096],
                                        index=2, key="new_lambda_mem")
                new_arch = st.selectbox("Arch", ["x86", "arm"], key="new_lambda_arch")
                preview  = f"Lambda  {new_inv:.1f}M inv  {new_dur}ms  {new_mem}MB"

            st.caption(preview)
            if st.button("Add", type="primary", key="add_comp"):
                if comp_type == "EC2":
                    st.session_state["arch_components"].append({
                        "type": "ec2", "instance": new_inst,
                        "hours": int(new_hours), "cpu": new_cpu/100, "os": new_os,
                        "label": preview,
                    })
                elif comp_type == "RDS":
                    st.session_state["arch_components"].append({
                        "type": "rds", "instance": new_rds_inst,
                        "engine": new_rds_engine, "cpu": new_rds_cpu/100,
                        "multi_az": new_rds_multi, "hours": 730,
                        "label": preview,
                    })
                elif comp_type == "Lambda":
                    st.session_state["arch_components"].append({
                        "type": "lambda",
                        "invocations": int(new_inv * 1_000_000),
                        "duration_ms": int(new_dur), "memory_mb": int(new_mem),
                        "architecture": new_arch, "label": preview,
                    })
                st.rerun()

        # Lista de componentes
        if st.session_state["arch_components"]:
            st.markdown('<div class="ga-section">Components</div>',
                        unsafe_allow_html=True)
            for i, comp in enumerate(st.session_state["arch_components"]):
                c_lbl, c_rm = st.columns([5, 1])
                with c_lbl:
                    icon = {"ec2": "EC2", "rds": "RDS", "lambda": "FN"}.get(comp["type"], "?")
                    st.markdown(
                        f'<div style="font-family:\'IBM Plex Mono\',monospace; '
                        f'font-size:11px; color:{C["text2"]}; padding:4px 0;">'
                        f'<span style="color:{C["green"]};font-weight:600">{icon}</span>'
                        f'  {comp["label"]}</div>',
                        unsafe_allow_html=True
                    )
                with c_rm:
                    if st.button("×", key=f"rm_{i}"):
                        st.session_state["arch_components"].pop(i)
                        st.rerun()

            # Regioes
            st.markdown('<div class="ga-section">Compare regions</div>',
                        unsafe_allow_html=True)
            arch_regions = []
            for reg in list(CARBON_INTENSITY_STATIC.keys()):
                intensity = CARBON_INTENSITY_STATIC[reg]
                if st.checkbox(f"{reg}  ·  {intensity}g",
                               value=reg in DEFAULT_REGIONS,
                               key=f"arch_reg_{reg}"):
                    arch_regions.append(reg)

            if st.button("Calculate architecture", type="primary",
                         use_container_width=True, key="calc_arch"):
                if not arch_regions:
                    st.warning("Select at least one region.")
                else:
                    arch_calc = ArchitectureCalculator()
                    arch_results = []
                    with st.spinner("Calculating..."):
                        for reg in arch_regions:
                            try:
                                r = arch_calc.calculate({
                                    "name": "Custom",
                                    "region": reg,
                                    "components": st.session_state["arch_components"],
                                })
                                arch_results.append({
                                    "region": reg,
                                    "cost_usd_month": r["totals"]["cost_usd_month"],
                                    "sci_score": r["totals"]["sci_score_gco2_per_hour"],
                                    "operational_carbon": r["totals"]["operational_carbon_gco2_hour"],
                                    "embodied_carbon": r["totals"]["embodied_carbon_gco2_hour"],
                                    "carbon_intensity": r["carbon_intensity_gco2_kwh"],
                                    "components": r["components"],
                                })
                            except Exception as e:
                                st.warning(f"{reg}: {e}")
                    st.session_state["arch_results"] = arch_results
                    st.session_state["arch_base"] = base_region

            if st.button("Clear", key="clear_arch"):
                st.session_state["arch_components"] = []
                st.session_state.pop("arch_results", None)
                st.rerun()

    with col_arch:
        if "arch_results" not in st.session_state or not st.session_state["arch_results"]:
            st.markdown(
                f'<div style="margin-top:120px; text-align:center; '
                f'color:{C["text3"]}; font-family:\'IBM Plex Mono\',monospace; '
                f'font-size:12px;">Add components and click Calculate.</div>',
                unsafe_allow_html=True
            )
        else:
            arch_df   = pd.DataFrame(st.session_state["arch_results"])
            arch_base = st.session_state.get("arch_base", "us-east-1")
            base_row  = arch_df[arch_df["region"] == arch_base]
            base_sci_a  = base_row["sci_score"].values[0] if len(base_row) > 0 else arch_df["sci_score"].min()
            base_cost_a = base_row["cost_usd_month"].values[0] if len(base_row) > 0 else arch_df["cost_usd_month"].min()
            best_a    = arch_df.loc[arch_df["sci_score"].idxmin()]
            reduction = round((base_sci_a - best_a["sci_score"]) / base_sci_a * 100, 1)
            cost_diff = best_a["cost_usd_month"] - base_cost_a

            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Base SCI", f"{base_sci_a:.4f} gCO₂/h", arch_base)
            m2.metric("Lowest SCI", f"{best_a['sci_score']:.4f} gCO₂/h", best_a["region"])
            m3.metric("SCI reduction", f"{reduction}%", f"vs. {arch_base}")
            m4.metric("Base cost", f"${base_cost_a:.2f}/mo")

            if reduction > 0:
                custo_str = (f"${abs(cost_diff):.2f}/mo cheaper" if cost_diff < 0
                             else f"${cost_diff:.2f}/mo more" if cost_diff > 0
                             else "same cost")
                st.markdown(
                    f'<div class="ga-banner">Best region: <b>{best_a["region"]}</b> — '
                    f'<b>{reduction}% less carbon</b> and {custo_str} vs. {arch_base}.</div>',
                    unsafe_allow_html=True
                )

            fig_arch = px.scatter(
                arch_df, x="cost_usd_month", y="sci_score",
                text="region", color="sci_score",
                color_continuous_scale=[[0, C["green"]], [0.5, "#E8963A"], [1, C["red"]]],
                hover_data={"cost_usd_month": ":.2f", "sci_score": ":.4f",
                            "carbon_intensity": True},
                labels={"cost_usd_month": "Total cost/mo (USD)",
                        "sci_score": "Total SCI (gCO₂eq/h)"},
            )
            fig_arch.update_traces(textposition="middle right",
                                   marker=dict(size=10, line=dict(width=0)))
            if len(base_row) > 0:
                fig_arch.add_trace(go.Scatter(
                    x=[base_row["cost_usd_month"].values[0]],
                    y=[base_row["sci_score"].values[0]],
                    mode="markers",
                    marker=dict(symbol="star", size=16, color="#E8963A",
                                line=dict(width=1, color=C["bg"])),
                    name="Base region", showlegend=True,
                ))
            fig_arch.update_layout(**chart_layout(380), coloraxis_showscale=False)
            st.plotly_chart(fig_arch, use_container_width=True)

            tbl = arch_df[["region", "cost_usd_month", "sci_score",
                           "carbon_intensity"]].sort_values("sci_score").rename(columns={
                "region": "Region", "cost_usd_month": "Cost/mo",
                "sci_score": "SCI (gCO₂/h)", "carbon_intensity": "Grid (gCO₂/kWh)",
            })
            st.dataframe(
                tbl.style
                    .format({"Cost/mo": "${:.2f}", "SCI (gCO₂/h)": "{:.4f}",
                             "Grid (gCO₂/kWh)": "{:.0f}"})
                    .background_gradient(subset=["SCI (gCO₂/h)"], cmap="RdYlGn_r"),
                use_container_width=True, hide_index=True,
            )

            if len(base_row) > 0:
                base_comps = base_row["components"].values[0]
                st.markdown(f'<div class="ga-section">Component breakdown — {arch_base}</div>',
                            unsafe_allow_html=True)
                cmp_df = pd.DataFrame(base_comps)
                fig_cmp = go.Figure()
                fig_cmp.add_trace(go.Bar(
                    name="Operational", x=cmp_df["label"],
                    y=cmp_df["operational_carbon_gco2_hour"],
                    marker_color=C["green"], marker_opacity=0.85,
                ))
                fig_cmp.add_trace(go.Bar(
                    name="Embodied", x=cmp_df["label"],
                    y=cmp_df["embodied_carbon_gco2_hour"],
                    marker_color=C["text3"], marker_opacity=0.6,
                ))
                fig_cmp.update_layout(barmode="stack", **chart_layout(300))
                fig_cmp.update_layout(yaxis_title="gCO₂eq/h")
                st.plotly_chart(fig_cmp, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════
# TAB 3 — FAMILY COMPARISON
# ══════════════════════════════════════════════════════════════════════════

# Specs de instancias: vcpu, memoria, processador
INSTANCE_SPECS = {
    "t3.nano":    {"vcpu": 2,  "mem_gib": 0.5,  "proc": "Intel Skylake",    "family": "t3",   "type": "Burstable"},
    "t3.micro":   {"vcpu": 2,  "mem_gib": 1,    "proc": "Intel Skylake",    "family": "t3",   "type": "Burstable"},
    "t3.small":   {"vcpu": 2,  "mem_gib": 2,    "proc": "Intel Skylake",    "family": "t3",   "type": "Burstable"},
    "t3.medium":  {"vcpu": 2,  "mem_gib": 4,    "proc": "Intel Skylake",    "family": "t3",   "type": "Burstable"},
    "t3.large":   {"vcpu": 2,  "mem_gib": 8,    "proc": "Intel Skylake",    "family": "t3",   "type": "Burstable"},
    "t3.xlarge":  {"vcpu": 4,  "mem_gib": 16,   "proc": "Intel Skylake",    "family": "t3",   "type": "Burstable"},
    "t3.2xlarge": {"vcpu": 8,  "mem_gib": 32,   "proc": "Intel Skylake",    "family": "t3",   "type": "Burstable"},
    "t4g.nano":   {"vcpu": 2,  "mem_gib": 0.5,  "proc": "Graviton2",        "family": "t4g",  "type": "Burstable"},
    "t4g.micro":  {"vcpu": 2,  "mem_gib": 1,    "proc": "Graviton2",        "family": "t4g",  "type": "Burstable"},
    "t4g.small":  {"vcpu": 2,  "mem_gib": 2,    "proc": "Graviton2",        "family": "t4g",  "type": "Burstable"},
    "t4g.medium": {"vcpu": 2,  "mem_gib": 4,    "proc": "Graviton2",        "family": "t4g",  "type": "Burstable"},
    "t4g.large":  {"vcpu": 2,  "mem_gib": 8,    "proc": "Graviton2",        "family": "t4g",  "type": "Burstable"},
    "t4g.xlarge": {"vcpu": 4,  "mem_gib": 16,   "proc": "Graviton2",        "family": "t4g",  "type": "Burstable"},
    "t4g.2xlarge":{"vcpu": 8,  "mem_gib": 32,   "proc": "Graviton2",        "family": "t4g",  "type": "Burstable"},
    "m5.large":   {"vcpu": 2,  "mem_gib": 8,    "proc": "Intel Xeon",       "family": "m5",   "type": "General"},
    "m5.xlarge":  {"vcpu": 4,  "mem_gib": 16,   "proc": "Intel Xeon",       "family": "m5",   "type": "General"},
    "m5.2xlarge": {"vcpu": 8,  "mem_gib": 32,   "proc": "Intel Xeon",       "family": "m5",   "type": "General"},
    "m5.4xlarge": {"vcpu": 16, "mem_gib": 64,   "proc": "Intel Xeon",       "family": "m5",   "type": "General"},
    "m6g.large":  {"vcpu": 2,  "mem_gib": 8,    "proc": "Graviton2",        "family": "m6g",  "type": "General"},
    "m6g.xlarge": {"vcpu": 4,  "mem_gib": 16,   "proc": "Graviton2",        "family": "m6g",  "type": "General"},
    "m6g.2xlarge":{"vcpu": 8,  "mem_gib": 32,   "proc": "Graviton2",        "family": "m6g",  "type": "General"},
    "m6g.4xlarge":{"vcpu": 16, "mem_gib": 64,   "proc": "Graviton2",        "family": "m6g",  "type": "General"},
    "m6i.large":  {"vcpu": 2,  "mem_gib": 8,    "proc": "Intel Ice Lake",   "family": "m6i",  "type": "General"},
    "m6i.xlarge": {"vcpu": 4,  "mem_gib": 16,   "proc": "Intel Ice Lake",   "family": "m6i",  "type": "General"},
    "m6i.2xlarge":{"vcpu": 8,  "mem_gib": 32,   "proc": "Intel Ice Lake",   "family": "m6i",  "type": "General"},
    "m6i.4xlarge":{"vcpu": 16, "mem_gib": 64,   "proc": "Intel Ice Lake",   "family": "m6i",  "type": "General"},
    "c5.large":   {"vcpu": 2,  "mem_gib": 4,    "proc": "Intel Xeon",       "family": "c5",   "type": "Compute"},
    "c5.xlarge":  {"vcpu": 4,  "mem_gib": 8,    "proc": "Intel Xeon",       "family": "c5",   "type": "Compute"},
    "c5.2xlarge": {"vcpu": 8,  "mem_gib": 16,   "proc": "Intel Xeon",       "family": "c5",   "type": "Compute"},
    "c5.4xlarge": {"vcpu": 16, "mem_gib": 32,   "proc": "Intel Xeon",       "family": "c5",   "type": "Compute"},
    "c6g.large":  {"vcpu": 2,  "mem_gib": 4,    "proc": "Graviton2",        "family": "c6g",  "type": "Compute"},
    "c6g.xlarge": {"vcpu": 4,  "mem_gib": 8,    "proc": "Graviton2",        "family": "c6g",  "type": "Compute"},
    "c6g.2xlarge":{"vcpu": 8,  "mem_gib": 16,   "proc": "Graviton2",        "family": "c6g",  "type": "Compute"},
    "c6g.4xlarge":{"vcpu": 16, "mem_gib": 32,   "proc": "Graviton2",        "family": "c6g",  "type": "Compute"},
    "r5.large":   {"vcpu": 2,  "mem_gib": 16,   "proc": "Intel Xeon",       "family": "r5",   "type": "Memory"},
    "r5.xlarge":  {"vcpu": 4,  "mem_gib": 32,   "proc": "Intel Xeon",       "family": "r5",   "type": "Memory"},
    "r5.2xlarge": {"vcpu": 8,  "mem_gib": 64,   "proc": "Intel Xeon",       "family": "r5",   "type": "Memory"},
    "r5.4xlarge": {"vcpu": 16, "mem_gib": 128,  "proc": "Intel Xeon",       "family": "r5",   "type": "Memory"},
    "r6g.large":  {"vcpu": 2,  "mem_gib": 16,   "proc": "Graviton2",        "family": "r6g",  "type": "Memory"},
    "r6g.xlarge": {"vcpu": 4,  "mem_gib": 32,   "proc": "Graviton2",        "family": "r6g",  "type": "Memory"},
    "r6g.2xlarge":{"vcpu": 8,  "mem_gib": 64,   "proc": "Graviton2",        "family": "r6g",  "type": "Memory"},
    "r6g.4xlarge":{"vcpu": 16, "mem_gib": 128,  "proc": "Graviton2",        "family": "r6g",  "type": "Memory"},
    "g4dn.xlarge": {"vcpu": 4, "mem_gib": 16,   "proc": "Intel + NVIDIA T4","family": "g4dn", "type": "GPU"},
    "g4dn.2xlarge":{"vcpu": 8, "mem_gib": 32,   "proc": "Intel + NVIDIA T4","family": "g4dn", "type": "GPU"},
    "g4dn.4xlarge":{"vcpu": 16,"mem_gib": 64,   "proc": "Intel + NVIDIA T4","family": "g4dn", "type": "GPU"},
}

with tab3:
    st.markdown('<div class="ga-title">Family Comparison</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="ga-subtitle">Given a vCPU and memory requirement, compare all instance '
        'families that meet it — showing SCI and cost per processor architecture.</div>',
        unsafe_allow_html=True
    )

    with st.form("form_family"):
        ff1, ff2, ff3, ff4 = st.columns(4)
        with ff1:
            req_vcpu = st.selectbox(
                "vCPUs required",
                options=[2, 4, 8, 16],
                index=0, key="req_vcpu",
            )
        with ff2:
            # Opcoes de memoria para o vcpu selecionado
            mem_opts = sorted(set(
                v["mem_gib"] for k, v in INSTANCE_SPECS.items()
                if v["vcpu"] == req_vcpu
            ))
            req_mem = st.selectbox(
                "Memory required (GiB)",
                options=mem_opts,
                key="req_mem",
            )
        with ff3:
            fam_region = st.selectbox(
                "Region",
                options=list(CARBON_INTENSITY_STATIC.keys()),
                index=list(CARBON_INTENSITY_STATIC.keys()).index("us-east-1"),
                key="fam_region",
            )
        with ff4:
            fam_cpu = st.slider("CPU utilization (%)", 1, 100, 50, key="fam_cpu")

        submitted_fam = st.form_submit_button("Compare families", type="primary")

    if submitted_fam:
        from core.sci_calculator import SCICalculator as _SCI
        _calc = _SCI()

        # Filtra instancias que atendem requisitos
        candidates = [
            k for k, v in INSTANCE_SPECS.items()
            if v["vcpu"] == req_vcpu and v["mem_gib"] == req_mem
        ]

        if not candidates:
            st.warning(f"No instances found with {req_vcpu} vCPUs and {req_mem} GiB.")
        else:
            rows_fam = []
            with st.spinner(f"Calculating {len(candidates)} instances..."):
                for inst in candidates:
                    try:
                        r = _calc.calculate({
                            "instance_type": inst,
                            "region": fam_region,
                            "hours_per_month": 730,
                            "cpu_utilization": fam_cpu / 100.0,
                        })
                        spec = INSTANCE_SPECS[inst]
                        rows_fam.append({
                            "Instance": inst,
                            "Family": spec["family"],
                            "Processor": spec["proc"],
                            "Type": spec["type"],
                            "vCPU": spec["vcpu"],
                            "Memory (GiB)": spec["mem_gib"],
                            "SCI (gCO2/h)": r["sci_score_gco2_per_hour"],
                            "Cost/mo": r["cost_usd_month"],
                            "Operational C.": r["operational_carbon_gco2_hour"],
                            "Embodied C.": r["embodied_carbon_gco2_hour"],
                            "Energy (kWh/h)": r["energy_kwh_hour_with_pue"],
                        })
                    except Exception as e:
                        pass

            st.session_state["fam_results"] = rows_fam
            st.session_state["fam_res_region"] = fam_region
            st.session_state["fam_res_vcpu"] = req_vcpu
            st.session_state["fam_res_mem"] = req_mem

    if "fam_results" in st.session_state and st.session_state["fam_results"]:
        fam_df     = pd.DataFrame(st.session_state["fam_results"])
        fam_region = st.session_state["fam_res_region"]
        fam_vcpu   = st.session_state["fam_res_vcpu"]
        fam_mem    = st.session_state["fam_res_mem"]

        best_sci  = fam_df.loc[fam_df["SCI (gCO2/h)"].idxmin()]
        best_cost = fam_df.loc[fam_df["Cost/mo"].idxmin()]
        worst_sci = fam_df.loc[fam_df["SCI (gCO2/h)"].idxmax()]
        sci_gap   = round((worst_sci["SCI (gCO2/h)"] - best_sci["SCI (gCO2/h)"]) /
                          worst_sci["SCI (gCO2/h)"] * 100, 1)

        st.markdown(
            f'<div class="ga-title" style="margin-top:16px">'
            f'{fam_vcpu} vCPU / {fam_mem} GiB — {fam_region}</div>',
            unsafe_allow_html=True
        )
        st.markdown(
            f'<div class="ga-subtitle">{len(fam_df)} instances across '
            f'{fam_df["Family"].nunique()} families</div>',
            unsafe_allow_html=True
        )

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Lowest SCI", f"{best_sci['SCI (gCO2/h)']:.4f} gCO₂/h",
                  best_sci["Instance"])
        m2.metric("Lowest cost", f"${best_cost['Cost/mo']:.2f}/mo",
                  best_cost["Instance"])
        m3.metric("Highest SCI", f"{worst_sci['SCI (gCO2/h)']:.4f} gCO₂/h",
                  worst_sci["Instance"])
        m4.metric("SCI gap (best vs worst)", f"{sci_gap}%",
                  "same vCPU and memory")

        st.markdown(
            f'<div class="ga-banner">Instances with the same resources (<b>{fam_vcpu} vCPU / '
            f'{fam_mem} GiB</b>) differ by up to <b>{sci_gap}% in SCI</b> — '
            f'purely due to processor architecture and hardware efficiency.</div>',
            unsafe_allow_html=True
        )

        # Grafico SCI x Custo por instancia
        st.markdown('<hr>', unsafe_allow_html=True)
        st.markdown('<div class="ga-section">SCI vs. Cost — by instance family</div>',
                    unsafe_allow_html=True)
        st.caption("All instances have identical compute resources. Differences reveal hardware efficiency.")

        # Cor por tipo de processador
        proc_colors = {
            "Graviton2":        "#3DBA6F",
            "Intel Skylake":    "#5B8FD4",
            "Intel Xeon":       "#4A7BC4",
            "Intel Ice Lake":   "#3A6BB4",
            "Intel + NVIDIA T4":"#E8963A",
            "Intel + NVIDIA V100":"#D4783A",
        }

        fig_fam = go.Figure()
        for proc in fam_df["Processor"].unique():
            sub = fam_df[fam_df["Processor"] == proc]
            fig_fam.add_trace(go.Scatter(
                x=sub["Cost/mo"], y=sub["SCI (gCO2/h)"],
                mode="markers+text",
                name=proc,
                text=sub["Instance"],
                textposition="middle right",
                textfont=dict(size=10),
                marker=dict(
                    size=12,
                    color=proc_colors.get(proc, "#888888"),
                    line=dict(width=0.5, color="#0D0F0E"),
                ),
                customdata=sub[["Family", "Type", "Energy (kWh/h)"]].values,
                hovertemplate=(
                    "<b>%{text}</b><br>"
                    "Processor: " + proc + "<br>"
                    "Cost: $%{x:.2f}/mo<br>"
                    "SCI: %{y:.4f} gCO₂/h<br>"
                    "Energy: %{customdata[2]:.5f} kWh/h<extra></extra>"
                ),
            ))

        fig_fam.update_layout(
            **chart_layout(440),
            xaxis_title="Monthly cost (USD)",
            yaxis_title="SCI score (gCO₂eq/h)",
            legend_title="Processor",
        )
        st.plotly_chart(fig_fam, use_container_width=True)

        # Grafico de barras SCI por instancia
        st.markdown('<div class="ga-section">SCI decomposition by instance</div>',
                    unsafe_allow_html=True)
        st.caption("Operational = E × I  ·  Embodied = M")

        fam_sorted = fam_df.sort_values("SCI (gCO2/h)")
        fig_fam_bar = go.Figure()
        fig_fam_bar.add_trace(go.Bar(
            name="Operational (E×I)",
            x=fam_sorted["Instance"],
            y=fam_sorted["Operational C."],
            marker_color=C["green"], marker_opacity=0.85,
        ))
        fig_fam_bar.add_trace(go.Bar(
            name="Embodied (M)",
            x=fam_sorted["Instance"],
            y=fam_sorted["Embodied C."],
            marker_color=C["text3"], marker_opacity=0.6,
        ))
        fig_fam_bar.update_layout(
            barmode="stack", **chart_layout(340),
            yaxis_title="gCO₂eq/h",
        )
        st.plotly_chart(fig_fam_bar, use_container_width=True)

        # Tabela completa
        st.markdown('<div class="ga-section">Full comparison</div>',
                    unsafe_allow_html=True)
        display_fam = fam_df[[
            "Instance", "Family", "Processor", "Type",
            "SCI (gCO2/h)", "Cost/mo", "Operational C.", "Embodied C.", "Energy (kWh/h)"
        ]].sort_values("SCI (gCO2/h)")
        st.dataframe(
            display_fam.style
                .format({
                    "SCI (gCO2/h)": "{:.4f}",
                    "Cost/mo": "${:.2f}",
                    "Operational C.": "{:.4f}",
                    "Embodied C.": "{:.2f}",
                    "Energy (kWh/h)": "{:.5f}",
                })
                .background_gradient(subset=["SCI (gCO2/h)"], cmap="RdYlGn_r"),
            use_container_width=True, hide_index=True,
        )

# ── Footer ─────────────────────────────────────────────────────────────────
st.markdown('<hr>', unsafe_allow_html=True)
st.markdown(
    f'<div style="font-family:\'IBM Plex Mono\',monospace; font-size:10px; '
    f'color:{C["text3"]}; display:flex; justify-content:space-between; padding:4px 0;">'
    f'<span>AWS Pricing Bulk API  ·  Electricity Maps  ·  EPA eGRID  ·  '
    f'Cloud Carbon Footprint (ThoughtWorks)</span>'
    f'<span>Carbon intensity based on 2022-2023 annual averages.</span>'
    f'</div>',
    unsafe_allow_html=True
)
