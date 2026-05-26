"""
dashboard/app.py
----------------
GreenArch Dashboard — redesign minimalista tecnico
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
    page_title="GreenArch — Carbon and Cost Intelligence for AWS",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Tema fixo — dark mode

# ── Meta tags via JavaScript injection (Streamlit não suporta <head> direto) ──
st.markdown("""
<script>
(function() {
    // Meta description
    var meta = document.querySelector('meta[name="description"]');
    if (!meta) {
        meta = document.createElement('meta');
        meta.name = 'description';
        document.head.appendChild(meta);
    }
    meta.content = 'GreenArch calcula o Software Carbon Intensity (SCI) e o custo de arquiteturas AWS antes do deploy. Compare regiões, visualize o Pareto-front custo × carbono e tome decisões mais sustentáveis.';

    // Keywords
    var kw = document.querySelector('meta[name="keywords"]');
    if (!kw) { kw = document.createElement('meta'); kw.name = 'keywords'; document.head.appendChild(kw); }
    kw.content = 'AWS, carbon intensity, SCI, Software Carbon Intensity, cloud sustainability, GreenOps, FinOps, ISO 21031';

    // Preconnect para fontes
    ['https://fonts.googleapis.com', 'https://fonts.gstatic.com'].forEach(function(href) {
        if (!document.querySelector('link[href="' + href + '"]')) {
            var link = document.createElement('link');
            link.rel = 'preconnect';
            link.href = href;
            if (href.includes('gstatic')) link.crossOrigin = 'anonymous';
            document.head.appendChild(link);
        }
    });
})();
</script>
""", unsafe_allow_html=True)

# ── CSS injection — sistema de design completo ────────────────────────────
def inject_css(dark: bool):
    # Dark mode fixo
    bg         = "#0D0F0E"
    bg2        = "#141714"
    bg3        = "#1C201C"
    border     = "#252825"
    text       = "#E8EDE9"
    text2      = "#C8D8CA"
    text3      = "#A8BCA8"
    green      = "#3DBA6F"
    green_dim  = "#1F5E38"
    green_glow = "rgba(61,186,111,0.12)"
    red        = "#E05252"
    tab_active = "#3DBA6F"
    tab_text   = "#C8D8CA"
    input_bg   = "#1C201C"
    metric_bg  = "#141714"
    chart_bg   = "#0D0F0E"
    chart_grid = "#1C201C"
    chart_text = "#C8D8CA"

    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@300;400;500;600&display=swap');
    /* font-display: swap garantido via display=swap na URL */

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
        font-size: 32px;
        font-weight: 500;
        color: {text};
        letter-spacing: -1px;
    }}
    .ga-wordmark span {{
        color: {green};
    }}
    .ga-tagline {{
        font-size: 13px;
        color: {text3};
        letter-spacing: 0.6px;
        text-transform: uppercase;
        margin-top: 4px;
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
        font-size: 26px !important;
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
        font-size: 14px;
        font-weight: 600;
        color: {text3};
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 14px;
        margin-top: 28px;
    }}
    .ga-title {{
        font-family: 'IBM Plex Sans', sans-serif;
        font-size: 24px;
        font-weight: 600;
        color: {text};
        margin-bottom: 6px;
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
        "chart_text": chart_text,
    }

dark = True  # fixo
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
    "África / ME":   ["af-south-1", "me-south-1"],
}
DEFAULT_REGIONS = ["us-east-1", "us-west-2", "eu-central-1", "eu-north-1", "eu-west-1", "sa-east-1"]

# Regiões AWS com 100% energia renovável (matched) — Fonte: Amazon Sustainability Report 2024
# https://sustainability.aboutamazon.com/products-services/aws-cloud
RENEWABLE_REGIONS = {
    "us-east-1", "us-east-2", "us-west-1", "us-west-2",
    "ca-central-1", "eu-west-1", "eu-west-2", "eu-west-3",
    "eu-central-1", "eu-north-1", "eu-south-1",
    "ap-south-1", "ap-northeast-1", "ap-northeast-2",
    "sa-east-1",
}
# Latência inter-região AWS em ms (P50, média 7 dias) — Fonte: CloudPing.co
# https://www.cloudping.co — medições em tempo real via TCP entre regiões AWS
INTER_REGION_LATENCY = {
    ("us-east-1",   "us-east-1"):    1,
    ("us-east-1",   "us-east-2"):   13,
    ("us-east-1",   "us-west-1"):   61,
    ("us-east-1",   "us-west-2"):   68,
    ("us-east-1",   "ca-central-1"): 17,
    ("us-east-1",   "eu-west-1"):   76,
    ("us-east-1",   "eu-west-2"):   77,
    ("us-east-1",   "eu-west-3"):   84,
    ("us-east-1",   "eu-central-1"): 91,
    ("us-east-1",   "eu-north-1"):  112,
    ("us-east-1",   "eu-south-1"):  102,
    ("us-east-1",   "ap-south-1"):  214,
    ("us-east-1",   "ap-northeast-1"): 149,
    ("us-east-1",   "ap-northeast-2"): 181,
    ("us-east-1",   "ap-southeast-1"): 219,
    ("us-east-1",   "ap-southeast-2"): 207,
    ("us-east-1",   "sa-east-1"):   114,
    ("us-east-1",   "af-south-1"):  225,
    ("us-east-1",   "me-south-1"):  165,
    ("us-west-2",   "us-east-1"):   68,
    ("us-west-2",   "us-west-1"):   21,
    ("us-west-2",   "ca-central-1"): 61,
    ("us-west-2",   "eu-west-1"):   118,
    ("us-west-2",   "eu-central-1"): 144,
    ("us-west-2",   "eu-north-1"):  155,
    ("us-west-2",   "ap-south-1"):  233,
    ("us-west-2",   "ap-northeast-1"): 105,
    ("us-west-2",   "ap-southeast-1"): 165,
    ("us-west-2",   "ap-southeast-2"): 145,
    ("us-west-2",   "sa-east-1"):   184,
    ("eu-central-1","us-east-1"):   91,
    ("eu-central-1","eu-west-1"):   21,
    ("eu-central-1","eu-north-1"):  23,
    ("eu-central-1","eu-west-2"):   15,
    ("eu-central-1","eu-west-3"):   10,
    ("eu-north-1",  "us-east-1"):   112,
    ("eu-north-1",  "eu-west-1"):   37,
    ("eu-north-1",  "eu-central-1"): 23,
    ("sa-east-1",   "us-east-1"):   114,
    ("sa-east-1",   "eu-west-1"):   178,
    ("ap-south-1",  "us-east-1"):   214,
    ("ap-south-1",  "eu-central-1"): 133,
    ("af-south-1",  "eu-west-1"):   157,
    ("me-south-1",  "eu-central-1"): 85,
    # sa-east-1 como origem
    ("sa-east-1",   "us-west-2"):   184,
    ("sa-east-1",   "eu-west-1"):   178,
    ("sa-east-1",   "eu-west-2"):   188,
    ("sa-east-1",   "eu-central-1"): 204,
    ("sa-east-1",   "eu-north-1"):  223,
    ("sa-east-1",   "ca-central-1"): 126,
    ("sa-east-1",   "ap-south-1"):  323,
    ("sa-east-1",   "ap-northeast-1"): 260,
    ("sa-east-1",   "ap-southeast-1"): 329,
    ("sa-east-1",   "af-south-1"):  337,
    # eu-north-1 como origem
    ("eu-north-1",  "us-west-2"):   155,
    ("eu-north-1",  "us-east-2"):   122,
    ("eu-north-1",  "ca-central-1"): 104,
    ("eu-north-1",  "eu-west-2"):   30,
    ("eu-north-1",  "eu-west-3"):   33,
    ("eu-north-1",  "eu-south-1"):  32,
    ("eu-north-1",  "ap-south-1"):  145,
    ("eu-north-1",  "ap-northeast-1"): 249,
    ("eu-north-1",  "sa-east-1"):   223,
    ("eu-north-1",  "af-south-1"):  172,
    ("eu-north-1",  "me-south-1"):  104,
    # eu-west-1 como origem
    ("eu-west-1",   "us-west-2"):   118,
    ("eu-west-1",   "us-east-2"):   79,
    ("eu-west-1",   "ca-central-1"): 69,
    ("eu-west-1",   "eu-north-1"):  37,
    ("eu-west-1",   "eu-central-1"): 21,
    ("eu-west-1",   "ap-south-1"):  149,
    ("eu-west-1",   "ap-northeast-1"): 202,
    ("eu-west-1",   "sa-east-1"):   178,
    # eu-central-1 como origem (complementos)
    ("eu-central-1","sa-east-1"):   204,
    ("eu-central-1","ap-south-1"):  130,
    ("eu-central-1","ap-northeast-1"): 230,
    ("eu-central-1","ap-southeast-1"): 160,
    ("eu-central-1","af-south-1"):  153,
    ("eu-central-1","me-south-1"):  85,
    # ap-south-1 como origem (complementos)
    ("ap-south-1",  "eu-west-1"):   149,
    ("ap-south-1",  "eu-north-1"):  145,
    ("ap-south-1",  "ap-northeast-1"): 129,
    ("ap-south-1",  "ap-southeast-1"): 63,
    ("ap-south-1",  "sa-east-1"):   323,
    ("ap-south-1",  "af-south-1"):  157,
}

def get_latency(origin, dest):
    v = INTER_REGION_LATENCY.get((origin, dest))
    if v is None:
        v = INTER_REGION_LATENCY.get((dest, origin))
    return v

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
st.markdown(f"""
<div class="ga-header">
    <div>
        <div class="ga-wordmark">Green<span>Arch</span></div>
        <div class="ga-tagline">Carbono e Custo — Inteligência para AWS</div>
    </div>
    <div class="ga-badge">ISO/IEC 21031:2024</div>
</div>
""", unsafe_allow_html=True)

# ── Abas ───────────────────────────────────────────────────────────────────
tab0, tab1, tab2 = st.tabs(["Visão Geral", "Instância", "Arquitetura"])
tab3 = None  # Family Comparison oculta temporariamente


# ══════════════════════════════════════════════════════════════════════════
# TAB 1 — INSTANCE
# ══════════════════════════════════════════════════════════════════════════
with tab0:
    g  = C["green"]
    bg = C["green_glow"]
    bd = C["green_dim"]
    t  = C["text"]
    t2 = C["text2"]
    t3 = C["text3"]
    br = C["border"]
    b3 = C["bg3"]

    # ── O que é o GreenArch ───────────────────────────────────────────────
    st.markdown(f"""
    <div style="padding:28px 0 8px 0;">
        <div style="font-size:28px;font-weight:700;color:{t};font-family:'IBM Plex Sans',sans-serif;margin-bottom:10px;">
            O que é o GreenArch?
        </div>
        <div style="font-size:15px;color:{t2};line-height:1.8;font-family:'IBM Plex Sans',sans-serif;max-width:820px;">
            O <b style="color:{t}">GreenArch</b> é uma ferramenta que calcula o custo e o impacto de carbono
            de arquiteturas AWS <b style="color:{t}">antes do deploy</b> — ajudando desenvolvedores e equipes
            a escolher onde e como hospedar seus sistemas de forma mais eficiente e sustentável.<br><br>
            A maioria das ferramentas de nuvem mostra apenas o custo histórico, depois que os recursos
            já estão rodando. O GreenArch responde a pergunta que nenhuma outra ferramenta responde:
        </div>
        <div style="margin:20px 0;padding:16px 24px;background:{bg};border-left:3px solid {g};
                    border-radius:6px;font-size:16px;color:{t};font-style:italic;font-family:'IBM Plex Sans',sans-serif;">
            "Onde devo hospedar esta arquitetura para minimizar o carbono sem aumentar o custo?"
        </div>
        <div style="font-size:15px;color:{t2};line-height:1.8;font-family:'IBM Plex Sans',sans-serif;max-width:820px;">
            Os cálculos seguem o padrão <b style="color:{t}">ISO/IEC 21031:2024</b> — Software Carbon Intensity (SCI) —
            usando dados públicos da AWS Pricing API, Cloud Carbon Footprint (ThoughtWorks),
            Electricity Maps, EPA eGRID e Boavizta. Nenhuma conta AWS é necessária.
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<hr style='border-color:{};margin:8px 0 24px 0'>".format(C["border"]), unsafe_allow_html=True)

    # ── O que é o SCI ────────────────────────────────────────────────────
    st.markdown(f"""
    <div style="background:{bg};border:1px solid {bd};
                border-left:3px solid {g};border-radius:6px;
                padding:20px 24px;margin-bottom:24px;">
        <div style="font-size:13px;font-weight:600;color:{g};margin-bottom:10px;
                    font-family:'IBM Plex Sans',sans-serif;text-transform:uppercase;letter-spacing:0.8px;">
            O padrão SCI — Software Carbon Intensity
        </div>
        <div style="font-size:14px;color:{t};line-height:1.7;font-family:'IBM Plex Sans',sans-serif;margin-bottom:14px;">
            O <b>Software Carbon Intensity (SCI)</b> é um padrão ISO (21031:2024) que mede
            a pegada de carbono de um software por unidade de uso. Aqui, a unidade é <b>uma hora de uso da instância</b>.
        </div>
        <div style="margin:14px 0 16px 0;font-size:22px;font-weight:700;
                    color:{g};letter-spacing:1px;text-align:center;
                    font-family:'IBM Plex Mono',monospace;">
            SCI = ( E &times; I + M ) / R
        </div>
        <div style="display:flex;gap:24px;flex-wrap:wrap;">
            <div style="font-size:12px;color:{t};min-width:200px;">
                <b style="color:{g};font-size:15px;">E</b> — Energia consumida (kWh/h)<br>
                <span style="color:{t2};font-size:11px;">Fonte: Cloud Carbon Footprint (ThoughtWorks), baseado em benchmarks SPECpower</span>
            </div>
            <div style="font-size:12px;color:{t};min-width:200px;">
                <b style="color:{g};font-size:15px;">I</b> — Intensidade de carbono do grid elétrico (gCO₂/kWh)<br>
                <span style="color:{t2};font-size:11px;">Fonte: Electricity Maps, EPA eGRID, IEA — médias anuais por região AWS</span>
            </div>
            <div style="font-size:12px;color:{t};min-width:200px;">
                <b style="color:{g};font-size:15px;">M</b> — Carbono embutido do hardware (gCO₂/h)<br>
                <span style="color:{t2};font-size:11px;">Emissões de fabricação amortizadas pela vida útil. Fonte: Boavizta dataset</span>
            </div>
            <div style="font-size:12px;color:{t};min-width:120px;">
                <b style="color:{g};font-size:15px;">R</b> — Unidade funcional<br>
                <span style="color:{t2};font-size:11px;">1 hora de uso</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Como usar ─────────────────────────────────────────────────────────
    st.markdown(f"""
    <div style="font-size:20px;font-weight:700;color:{t};font-family:'IBM Plex Sans',sans-serif;margin-bottom:16px;">
        Como usar o GreenArch
    </div>
    """, unsafe_allow_html=True)

    col_a, col_b = st.columns(2, gap="large")

    with col_a:
        st.markdown(f"""
        <div style="background:{b3};border:1px solid {br};border-radius:8px;padding:20px 22px;height:100%;">
            <div style="font-size:13px;font-weight:600;color:{g};text-transform:uppercase;
                        letter-spacing:0.8px;margin-bottom:12px;font-family:'IBM Plex Sans',sans-serif;">
                Aba — Instância
            </div>
            <div style="font-size:13px;color:{t2};line-height:1.8;font-family:'IBM Plex Sans',sans-serif;">
                Compare o SCI e o custo de uma <b style="color:{t}">instância EC2 específica</b>
                entre diferentes regiões AWS.<br><br>
                <b style="color:{t}">Como usar:</b><br>
                1. Selecione a instância base (ex: c5.4xlarge)<br>
                2. Ajuste a utilização de CPU e as horas de uso mensais<br>
                3. Escolha as regiões que deseja comparar<br>
                4. Clique em <b style="color:{t}">Calcular</b><br><br>
                O resultado mostra o <b style="color:{t}">Pareto-front</b> — as regiões onde
                não existe outra opção simultaneamente mais barata e com menos carbono.
                Use o <b style="color:{t}">Índice de Eficiência</b> para ponderar entre
                custo e carbono conforme sua prioridade.
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col_b:
        st.markdown(f"""
        <div style="background:{b3};border:1px solid {br};border-radius:8px;padding:20px 22px;height:100%;">
            <div style="font-size:13px;font-weight:600;color:{g};text-transform:uppercase;
                        letter-spacing:0.8px;margin-bottom:12px;font-family:'IBM Plex Sans',sans-serif;">
                Aba — Arquitetura
            </div>
            <div style="font-size:13px;color:{t2};line-height:1.8;font-family:'IBM Plex Sans',sans-serif;">
                Compare o SCI e o custo de uma <b style="color:{t}">arquitetura completa</b>
                (combinação de EC2, RDS e Lambda) entre regiões.<br><br>
                <b style="color:{t}">Como usar:</b><br>
                1. Carregue uma arquitetura de benchmark pronta (ex: API REST) ou monte a sua<br>
                2. Para montar: adicione componentes EC2, RDS e Lambda com seus parâmetros<br>
                3. Selecione a região base e as regiões de comparação<br>
                4. Clique em <b style="color:{t}">Calcular arquitetura</b><br><br>
                O resultado mostra o SCI total da arquitetura em cada região,
                com o mesmo Pareto-front e Índice de Eficiência da aba de instância.
                É possível exportar os resultados em PDF.
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)

    # ── O que é o Pareto-front ───────────────────────────────────────────
    st.markdown(f"""
    <div style="background:{b3};border:1px solid {br};border-radius:8px;padding:20px 22px;margin-top:4px;">
        <div style="font-size:13px;font-weight:600;color:{g};text-transform:uppercase;
                    letter-spacing:0.8px;margin-bottom:10px;font-family:'IBM Plex Sans',sans-serif;">
            O que é o Pareto-front?
        </div>
        <div style="font-size:13px;color:{t2};line-height:1.8;font-family:'IBM Plex Sans',sans-serif;">
            O <b style="color:{t}">Pareto-front</b> é um conceito de otimização multi-objetivo.
            Em vez de escolher apenas "o mais barato" ou "o com menos carbono",
            ele identifica todas as soluções onde <b style="color:{t}">não existe outra opção que seja
            simultaneamente mais barata e com menos carbono</b>.<br><br>
            Exemplo: se Oregon custa igual a Virginia mas tem 34% menos carbono,
            não há nenhum motivo racional para escolher Virginia — ela é <b style="color:{t}">dominada</b>.
            Oregon está no Pareto-front; Virginia não.<br><br>
            <span style="color:{t3};font-size:12px;">
            No gráfico: círculos verdes = Pareto-ótimo · cinza = dominado · estrela laranja = cenário base escolhido
            </span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    # ── Quando a otimização de região faz sentido ─────────────────────────
    st.markdown(f"""
    <div style="background:{b3};border:1px solid {br};border-radius:8px;padding:20px 22px;margin-top:4px;">
        <div style="font-size:13px;font-weight:600;color:{g};text-transform:uppercase;
                    letter-spacing:0.8px;margin-bottom:10px;font-family:'IBM Plex Sans',sans-serif;">
            Quando a otimização de região faz sentido?
        </div>
        <div style="font-size:13px;color:{t2};line-height:1.8;font-family:'IBM Plex Sans',sans-serif;margin-bottom:16px;">
            Migrar para uma região de menor carbono como <b style="color:{t}">eu-north-1</b> (Estocolmo)
            reduz o SCI em até 43% — mas introduz latência de rede que pode ser incompatível com
            algumas aplicações. O GreenArch exibe a latência junto com o SCI e o custo para que
            essa decisão seja tomada com informação completa.
        </div>
        <div style="display:flex;gap:16px;flex-wrap:wrap;">
            <div style="background:{bg};border:1px solid {bd};border-radius:6px;
                        padding:14px 16px;flex:1;min-width:200px;">
                <div style="font-size:12px;font-weight:600;color:{g};margin-bottom:8px;">
                    Menor restrição de latência
                </div>
                <div style="font-size:12px;color:{t2};line-height:1.7;">
                    Processamento batch e pipelines de dados<br>
                    Treinamento de modelos de machine learning<br>
                    Jobs noturnos e tarefas agendadas<br>
                    Geração de relatórios e ETL<br>
                    Armazenamento e backup de longo prazo
                </div>
            </div>
            <div style="background:{b3};border:1px solid {br};border-radius:6px;
                        padding:14px 16px;flex:1;min-width:200px;">
                <div style="font-size:12px;font-weight:600;color:{t};margin-bottom:8px;">
                    Maior restrição de latência
                </div>
                <div style="font-size:12px;color:{t2};line-height:1.7;">
                    APIs com usuários finais na mesma região<br>
                    Bancos de dados com queries síncronas frequentes<br>
                    Sistemas de tempo real e streaming<br>
                    Aplicações interativas com SLA de latência definido
                </div>
            </div>
            <div style="background:{b3};border:1px solid {br};border-radius:6px;
                        padding:14px 16px;flex:1;min-width:200px;">
                <div style="font-size:12px;font-weight:600;color:{t};margin-bottom:8px;">
                    Arquiteturas híbridas
                </div>
                <div style="font-size:12px;color:{t2};line-height:1.7;">
                    Frontend em região próxima ao usuário e backend de processamento
                    em região de baixo carbono. Separar camadas com diferentes
                    requisitos de latência permite otimizar carbono sem sacrificar
                    a experiência do usuário final.
                </div>
            </div>
        </div>
        <div style="font-size:11px;color:{t3};margin-top:12px;">
            A seção Latência de Rede nas abas de análise mostra os valores RTT P50
            entre regiões com base em medições do CloudPing.co.
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    # ── Energia renovável ────────────────────────────────────────────────
    st.markdown(f"""
    <div style="background:{b3};border:1px solid {br};border-radius:8px;padding:20px 22px;margin-top:4px;">
        <div style="font-size:13px;font-weight:600;color:{g};text-transform:uppercase;
                    letter-spacing:0.8px;margin-bottom:10px;font-family:'IBM Plex Sans',sans-serif;">
            Certificação de energia renovável por região AWS
        </div>
        <div style="font-size:13px;color:{t2};line-height:1.8;font-family:'IBM Plex Sans',sans-serif;margin-bottom:14px;">
            A Amazon reportou a compensação de <b style="color:{t}">100% da eletricidade</b> consumida
            globalmente com fontes renováveis em 2023 e 2024. Esse resultado é calculado pelo
            <b style="color:{t}">método market-based</b>: a Amazon adquire certificados de energia renovável
            (RECs e Guarantees of Origin) equivalentes ao volume consumido, mas a eletricidade que
            chega fisicamente aos data centers pode vir de qualquer fonte do grid local.
        </div>
        <div style="font-size:13px;color:{t2};line-height:1.8;font-family:'IBM Plex Sans',sans-serif;margin-bottom:14px;">
            O GreenArch utiliza o <b style="color:{t}">método location-based</b>, que mede a carbon intensity
            real do grid elétrico local de cada região. Esse é o método recomendado pelo
            ISO/IEC 21031:2024 para o cálculo do SCI e explica por que regiões com certificação
            de 100% renovável, como <b style="color:{t}">us-east-1 (391 gCO₂/kWh)</b>, ainda apresentam
            SCI elevado — pois o grid local da Virgínia continua sendo majoritariamente termal.
        </div>
        <div style="display:flex;gap:16px;flex-wrap:wrap;margin-bottom:12px;">
            <div style="font-size:12px;color:{t2};min-width:180px;line-height:1.8;">
                <b style="color:{t}">Américas — certificadas</b><br>
                us-east-1 · us-east-2 · us-west-1<br>us-west-2 · ca-central-1
            </div>
            <div style="font-size:12px;color:{t2};min-width:180px;line-height:1.8;">
                <b style="color:{t}">Europa — certificadas</b><br>
                eu-north-1 · eu-west-1 · eu-west-2<br>eu-west-3 · eu-central-1 · eu-south-1
            </div>
            <div style="font-size:12px;color:{t2};min-width:180px;line-height:1.8;">
                <b style="color:{t}">Ásia Pacífico / América do Sul — certificadas</b><br>
                ap-south-1 · ap-northeast-1<br>ap-northeast-2 · sa-east-1
            </div>
            <div style="font-size:12px;color:{t3};min-width:180px;line-height:1.8;">
                <b style="color:{t}">Sem certificação confirmada</b><br>
                ap-southeast-1 · ap-southeast-2<br>af-south-1 · me-south-1
            </div>
        </div>
        <div style="font-size:11px;color:{t3};">
            Fonte: Amazon Sustainability Report 2024 — sustainability.aboutamazon.com/products-services/aws-cloud
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    # ── Fontes de dados ───────────────────────────────────────────────────
    st.markdown(f"""
    <div style="background:{b3};border:1px solid {br};border-radius:8px;padding:20px 22px;margin-top:4px;">
        <div style="font-size:13px;font-weight:600;color:{g};text-transform:uppercase;
                    letter-spacing:0.8px;margin-bottom:10px;font-family:'IBM Plex Sans',sans-serif;">
            Fontes de dados
        </div>
        <div style="display:flex;gap:24px;flex-wrap:wrap;">
            <div style="font-size:12px;color:{t2};min-width:200px;line-height:1.7;">
                <b style="color:{t}">Preços AWS</b><br>
                AWS Pricing Bulk API — dados em tempo real, sem autenticação
            </div>
            <div style="font-size:12px;color:{t2};min-width:200px;line-height:1.7;">
                <b style="color:{t}">Consumo de energia</b><br>
                Cloud Carbon Footprint (ThoughtWorks) — benchmarks SPECpower
            </div>
            <div style="font-size:12px;color:{t2};min-width:200px;line-height:1.7;">
                <b style="color:{t}">Intensidade de carbono do grid</b><br>
                Electricity Maps, EPA eGRID, IEA — médias anuais 2022–2023
            </div>
            <div style="font-size:12px;color:{t2};min-width:200px;line-height:1.7;">
                <b style="color:{t}">Carbono embutido do hardware</b><br>
                Boavizta dataset — ciclo de vida dos servidores
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


with tab1:

    col_main, col_side = st.columns([3, 1], gap="large")

    with col_side:
        st.markdown('<div class="ga-section">Configurar</div>', unsafe_allow_html=True)
        with st.form("form_instance"):
            instance_type = st.selectbox(
                "Instância base",
                options=ALL_INSTANCES,
                index=ALL_INSTANCES.index("c5.4xlarge"),
            )
            base_region_t1 = st.selectbox(
                "Região base",
                options=list(CARBON_INTENSITY_STATIC.keys()),
                index=list(CARBON_INTENSITY_STATIC.keys()).index("us-east-1"),
                key="t1_base_region",
                help="Região onde o workload está hospedado hoje. Usada como referência para calcular latência e delta de SCI."
            )
            os_type  = "Linux"  # fixo

            st.markdown('<div class="ga-section" style="margin-top:12px">Parâmetros de uso</div>',
                        unsafe_allow_html=True)
            st.markdown(f'''
            <div style="background:{C["bg3"]};border:1px solid {C["border"]};
                        border-radius:5px;padding:10px 14px;margin:4px 0 8px 0;">
                <div style="font-size:12px;color:{C["text2"]};line-height:1.7;">
                    <b style="color:{C["text"]}">Utilização de CPU:</b> padrão de <b>50%</b>
                    — baseline do Cloud Carbon Footprint (ThoughtWorks) para workloads de
                    propósito geral. Afeta diretamente o SCI — quanto maior a CPU, maior o
                    consumo de energia e portanto maior o carbono operacional.<br>
                    <b style="color:{C["text"]}">Horas por mês:</b> padrão de <b>730h</b>
                    — operação contínua 24/7. Afeta o custo total mensal mas não o SCI,
                    que é calculado por hora. Use ~180h para ambiente de desenvolvimento,
                    ~730h para produção contínua.
                </div>
            </div>
            ''', unsafe_allow_html=True)
            cpu_util = st.slider("Utilização de CPU (%)", 1, 100, 50, key="t1_cpu") / 100.0
            hours    = st.slider("Horas por mês", 1, 730, 730, key="t1_hours")

            st.markdown('<div class="ga-section" style="margin-top:16px">Regiões</div>',
                        unsafe_allow_html=True)
            selected_regions = []
            for continent, regs in REGION_GROUPS.items():
                with st.expander(continent, expanded=(continent == "North America")):
                    for reg in regs:
                        if st.checkbox(reg,
                                       value=reg in DEFAULT_REGIONS,
                                       key=f"t1_{reg}"):
                            selected_regions.append(reg)

            submitted1 = st.form_submit_button("Calcular", type="primary",
                                               use_container_width=True)

        st.caption(f"Cenários a calcular: {len(selected_regions)}")

    with col_main:
        if submitted1:
            if not selected_regions:
                st.warning("Selecione ao menos uma região.")
            else:
                engine = ScenarioEngine()
                with st.spinner(f"Calculando {len(selected_regions)} cenários..."):
                    result1 = engine.compare(
                        instance_type=instance_type,
                        region=base_region_t1,
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
            base    = result1["base_scenario"]
            # Filtra só a instância selecionada — sem equivalentes
            pareto  = [p for p in result1["pareto_front"] if p["instance_type"] == instance_type]
            df1     = pd.DataFrame(result1["all_scenarios"])
            df1     = df1[df1["instance_type"] == instance_type].copy()
            df1["Status"] = df1["pareto_optimal"].map(
                {True: "Pareto ótimo", False: "Dominado"})

            # Recalcula Pareto-front do zero para a instancia filtrada
            # (os flags pareto_optimal do engine incluiam equivalentes)
            def _is_dominated(row, df):
                """Retorna True se existir outro cenario melhor em SCI E custo."""
                return any(
                    (other["sci_score"] <= row["sci_score"] and
                     other["cost_usd_month"] <= row["cost_usd_month"] and
                     (other["sci_score"] < row["sci_score"] or
                      other["cost_usd_month"] < row["cost_usd_month"]))
                    for _, other in df.iterrows()
                    if other.name != row.name
                )

            if len(df1) > 0:
                df1["pareto_optimal"] = [
                    not _is_dominated(row, df1)
                    for _, row in df1.iterrows()
                ]
                df1["Status"] = df1["pareto_optimal"].map(
                    {True: "Pareto ótimo", False: "Dominado"})
                pareto = df1[df1["pareto_optimal"]].to_dict("records")
            
            _best_sci_row  = df1.loc[df1["sci_score"].idxmin()] if len(df1) > 0 else None
            _best_cost_row = df1.loc[df1["cost_usd_month"].idxmin()] if len(df1) > 0 else None
            s = {
                "pareto_count": int(df1["pareto_optimal"].sum()) if len(df1) > 0 else 0,
                "total_scenarios": len(df1),
                "best_sci_scenario":  _best_sci_row.to_dict() if _best_sci_row is not None else None,
                "best_cost_scenario": _best_cost_row.to_dict() if _best_cost_row is not None else None,
                "sci_reduction_vs_base": round(
                    (base["sci_score"] - _best_sci_row["sci_score"]) / base["sci_score"] * 100, 1
                ) if _best_sci_row is not None and base else 0,
            }

            # Metricas
            st.markdown(f'<div class="ga-title">{label1}</div>', unsafe_allow_html=True)
            st.markdown('<div class="ga-subtitle">Resultados da análise de cenários</div>',
                        unsafe_allow_html=True)

            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Cenário base", f"${base['cost_usd_month']:.2f}/mo",
                      f"{base['sci_score']:.4f} gCO₂/h")
            best_sci  = s["best_sci_scenario"]
            best_cost = s["best_cost_scenario"]
            if best_sci:
                c2.metric("Menor SCI encontrado", f"{best_sci['sci_score']:.4f} gCO₂/h",
                          f"{best_sci['instance_type']} · {best_sci['region']}")
            if best_cost:
                c3.metric("Menor custo", f"${best_cost['cost_usd_month']:.2f}/mo",
                          f"{best_cost['instance_type']} · {best_cost['region']}")
            c4.metric("Pareto ótimo", s["pareto_count"],
                      f"de {s['total_scenarios']} cenários")

            # Banner
            if best_sci and base:
                sci_gain  = s.get("sci_reduction_vs_base", 0)
                cost_diff = best_sci["cost_usd_month"] - base["cost_usd_month"]
                custo_str = (f"${abs(cost_diff):.2f}/mês mais barato" if cost_diff < 0
                             else f"${cost_diff:.2f}/mês a mais" if cost_diff > 0
                             else "mesmo custo")
                if sci_gain > 0:
                    st.markdown(
                        f'<div class="ga-banner">Melhor alternativa Pareto: '
                        f'<b>{best_sci["instance_type"]} · {best_sci["region"]}</b> — '
                        f'<b>{sci_gain}% less carbon</b> and {custo_str} vs. base.</div>',
                        unsafe_allow_html=True
                    )

            # Indice de eficiencia
            st.markdown('<hr>', unsafe_allow_html=True)
            st.markdown('<div class="ga-section">Índice de Eficiência</div>',
                        unsafe_allow_html=True)
            st.caption("Pontuação composta que combina SCI e custo. Ajuste o peso para priorizar carbono ou custo.")

            peso_carbono = st.slider(
                "Prioridade: Custo — Carbono",
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
                    "instance_type": "Instância", "region": "Região",
                    "cost_usd_month": "Custo/mês", "sci_score": "SCI (gCO₂/h)",
                    "score": "Score",
                })

            def hl_pareto(row):
                if row["Status"] == "Pareto ótimo":
                    return [f"color: {C['green']}; font-weight: 500"] * len(row)
                return [""] * len(row)

            st.dataframe(
                df_score.style.apply(hl_pareto, axis=1).format({
                    "Custo/mês": "${:.2f}", "SCI (gCO₂/h)": "{:.4f}", "Score": "{:.1f}",
                }),
                use_container_width=True, hide_index=True,
            )

            # Pareto-front chart
            st.markdown('<hr>', unsafe_allow_html=True)
            st.markdown('<div class="ga-section">Pareto Front — Custo vs. Carbono</div>',
                        unsafe_allow_html=True)

            # Explicação Pareto
            st.markdown(f'''
            <div style="background:{C["bg3"]};border:1px solid {C["border"]};
                        border-radius:6px;padding:14px 18px;margin-bottom:12px;">
                <div style="font-size:13px;font-weight:600;color:{C["text2"]};margin-bottom:6px;
                            font-family:'IBM Plex Sans',sans-serif;">
                    O que é o Pareto-front?
                </div>
                <div style="font-size:13px;color:{C["text2"]};line-height:1.7;font-family:'IBM Plex Sans',sans-serif;">
                    Cada ponto no gráfico é um cenário (instância + região). Um cenário é
                    <b style="color:{C["green"]}">Pareto ótimo</b> quando <b>não existe nenhum outro
                    cenário que seja simultaneamente mais barato E com menos carbono</b>.
                    Escolher qualquer solução Pareto ótima garante que não há outra opção melhor nas duas dimensões ao mesmo tempo.<br>
                    <span style="color:{C["text3"]};font-size:12px;">
                    Círculo = família base · Diamante = família equivalente · Estrela = cenário atual
                    </span>
                </div>
            </div>
            ''', unsafe_allow_html=True)

            st.caption("Verde = Pareto ótimo  ·  Cinza = Dominado  ·  Estrela = cenário base")

            # Marca qual familia e base vs equivalente
            base_family = instance_type.split(".")[0]  # ex: "t3" de "t3.medium"
            df1["family"] = df1["instance_type"].apply(
                lambda x: "Base family" if x.split(".")[0] == base_family else "Equivalent"
            )

            # Grafico simples — so a instancia selecionada
            fig1 = go.Figure()

            for status, color, opacity in [
                ("Pareto ótimo", C["green"], 0.95),
                ("Dominado",     C["text3"], 0.45),
            ]:
                sub = df1[df1["Status"] == status]
                if not len(sub): continue
                fig1.add_trace(go.Scatter(
                    x=sub["cost_usd_month"], y=sub["sci_score"],
                    mode="markers",
                    name=status,
                    marker=dict(
                        symbol="circle", size=9,
                        color=color, opacity=opacity,
                        line=dict(width=0.5, color=C["bg"]),
                    ),
                    customdata=sub[["instance_type","region","carbon_intensity"]].values,
                    hovertemplate=(
                        "<b>%{customdata[0]} · %{customdata[1]}</b><br>"
                        "Custo: $%{x:.2f}/mês<br>"
                        "SCI: %{y:.4f} gCO₂/h<br>"
                        "Grid: %{customdata[2]:.0f} gCO₂/kWh<extra></extra>"
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
                xaxis_title="Custo mensal (USD)",
                yaxis_title="SCI score (gCO₂eq/h)",
            )
            st.plotly_chart(fig1, use_container_width=True)

            # Tabela Pareto
            st.markdown('<div class="ga-section">Soluções Pareto-Ótimas</div>',
                        unsafe_allow_html=True)
            st.caption("Nenhuma outra combinação é simultaneamente mais barata E com menos carbono.")
            if pareto:
                _pdf = pd.DataFrame(pareto)
                _cols_available = [c for c in
                    ["instance_type", "region", "cost_usd_month", "sci_score",
                     "carbon_intensity", "operational_carbon"]
                    if c in _pdf.columns
                ]
                pareto_df = _pdf[_cols_available].rename(columns={
                    "instance_type": "Instância", "region": "Região",
                    "cost_usd_month": "Custo/mês", "sci_score": "SCI",
                    "carbon_intensity": "Intensidade de carbono (gCO₂/kWh)",
                    "operational_carbon": "C. Operacional",
                }).sort_values("SCI")
                fmt = {k: v for k, v in {
                    "Custo/mês": "${:.2f}", "SCI": "{:.4f}",
                    "Grid (gCO₂/kWh)": "{:.0f}", "C. Operacional": "{:.4f}"
                }.items() if k in pareto_df.columns}
                st.dataframe(
                    pareto_df.style
                        .format(fmt)
                        .background_gradient(subset=["SCI"], cmap="RdYlGn_r"),
                    use_container_width=True, hide_index=True,
                )
            else:
                st.info("Nenhuma solução Pareto encontrada para esta instância nas regiões selecionadas.")

            with st.expander("Todos os cenários calculados"):
                full_df = df1[["instance_type", "region", "cost_usd_month",
                               "sci_score", "carbon_intensity", "Status"]].rename(columns={
                    "instance_type": "Instância", "region": "Região",
                    "cost_usd_month": "Custo/mês", "sci_score": "SCI",
                    "carbon_intensity": "Intensidade de carbono (gCO₂/kWh)",
                }).sort_values("SCI")
                st.dataframe(
                    full_df.style.apply(hl_pareto, axis=1).format({
                        "Custo/mês": "${:.2f}", "SCI": "{:.4f}", "Grid (gCO₂/kWh)": "{:.0f}",
                    }),
                    use_container_width=True, hide_index=True,
                )

            # SCI decomposition
            st.markdown('<hr>', unsafe_allow_html=True)
            st.markdown('<div class="ga-section">Decomposição do SCI</div>',
                        unsafe_allow_html=True)
            st.caption("Operacional = E × I (energia × intensidade do grid)  ·  Embutido = M (fabricação do hardware)")

            cmp = ([base] if base else []) + [p for p in pareto if not p["is_base"]]
            cdf = pd.DataFrame(cmp)
            cdf["lbl"] = cdf.apply(
                lambda r: f"{r['instance_type']}\n{r['region']}" +
                          (" (base)" if r["is_base"] else ""), axis=1)

            show_embodied = st.checkbox(
                "Incluir carbono embutido (M) — emissões de fabricação do hardware",
                value=False, key="show_embodied"
            )
            if show_embodied:
                st.caption(
                    "O carbono embutido (M) é constante em todas as regiões — representa as emissões de "
                    "fabricação do hardware amortizadas pela vida útil do servidor. Não varia com a escolha de região."
                )

            fig_bar = go.Figure()
            fig_bar.add_trace(go.Bar(
                name="Operacional (E×I)",
                x=cdf["lbl"], y=cdf["operational_carbon"],
                marker_color=C["green"], marker_opacity=0.85
            ))
            if show_embodied:
                fig_bar.add_trace(go.Bar(
                    name="Embutido (M)",
                    x=cdf["lbl"], y=cdf["embodied_carbon"],
                    marker_color=C["text3"], marker_opacity=0.6
                ))
            fig_bar.update_layout(barmode="stack", **chart_layout(320, legend_title=""))
            fig_bar.update_layout(yaxis_title="gCO₂eq/h")
            st.plotly_chart(fig_bar, use_container_width=True)

            # ── Latência inter-região ──────────────────────────────────
            st.markdown('<div class="ga-section">Latência de rede</div>', unsafe_allow_html=True)
            st.markdown(f"""
            <div style="background:{C['bg3']};border:1px solid {C['border']};border-radius:6px;
                        padding:12px 16px;margin-bottom:8px;font-size:12px;color:{C['text2']};line-height:1.7;">
                Latência aproximada entre a região base
                <b style="color:{C['text']}">{base_region_t1}</b> e cada região calculada (RTT P50).
                Valores altos impactam aplicações com chamadas síncronas ao banco de dados.
                Fonte: <b>CloudPing.co</b> — medições em tempo real entre regiões AWS.
            </div>
            """, unsafe_allow_html=True)

            lat_rows = []
            for _, row in df1.sort_values("sci_score").iterrows():
                reg = row["region"]
                lat = get_latency(base_region_t1, reg)
                if lat is None:
                    flag = "—"
                elif lat < 80:
                    flag = f"🟢 {lat} ms"
                elif lat < 150:
                    flag = f"🟡 {lat} ms"
                else:
                    flag = f"🔴 {lat} ms"
                lat_rows.append({
                    "Região": reg,
                    "SCI (gCO₂/h)": f"{row['sci_score']:.4f}",
                    "Latência da região base": flag,
                    "Status": row["Status"],
                })
            if lat_rows:
                st.dataframe(pd.DataFrame(lat_rows), use_container_width=True, hide_index=True)
            st.caption("🟢 < 80 ms · 🟡 80–150 ms · 🔴 > 150 ms")

            # PDF export
            st.markdown('<hr>', unsafe_allow_html=True)
            st.markdown('<div class="ga-section">Exportar</div>', unsafe_allow_html=True)

            if st.button("Gerar relatório PDF", key="btn_pdf1"):
                with st.spinner("Gerando relatório..."):
                    try:
                        pdf_bytes = generate_report(result1, label1)
                        st.session_state["pdf1_bytes"] = pdf_bytes
                        st.session_state["pdf1_label"] = label1
                    except Exception as e:
                        st.error(f"Erro: {e}")

            if "pdf1_bytes" in st.session_state:
                st.download_button(
                    label="Baixar PDF",
                    data=st.session_state["pdf1_bytes"],
                    file_name=f"greenarch_{st.session_state['pdf1_label'].replace('.','_')}.pdf",
                    mime="application/pdf",
                    key="dl_pdf1",
                )


# ══════════════════════════════════════════════════════════════════════════
# TAB 2 — ARCHITECTURE
# ══════════════════════════════════════════════════════════════════════════
with tab2:
    st.markdown('<div class="ga-title">Construtor de Arquitetura</div>', unsafe_allow_html=True)
    st.markdown('<div class="ga-subtitle">Carregue uma arquitetura de benchmark ou monte a sua. Compare o SCI total entre regiões.</div>', unsafe_allow_html=True)

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
        st.markdown('<div class="ga-section">Arquiteturas de benchmark</div>',
                    unsafe_allow_html=True)
        st.caption("Carregue uma arquitetura pré-definida como ponto de partida.")

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
                                "hours": 730,
                                "cpu": 0.5,
                                "os": "Linux",
                                "label": f"EC2 {c.get('instance')} — 730h · 50% CPU",
                            })
                        elif ct == "rds":
                            loaded.append({
                                "type": "rds",
                                "instance": c.get("instance", "db.t3.micro"),
                                "engine": c.get("engine", "MySQL"),
                                "cpu": 0.5,
                                "multi_az": c.get("multi_az", False),
                                "hours": 730,
                                "label": f"RDS {c.get('instance')} — {c.get('engine','MySQL')}",
                            })
                        elif ct == "lambda":
                            inv = c.get("invocations", 1000000)
                            loaded.append({
                                "type": "lambda",
                                "invocations": inv,
                                "duration_ms": c.get("duration_ms", 200),
                                "memory_mb": c.get("memory_mb", 512),
                                "architecture": c.get("architecture", "x86"),
                                "label": f"Lambda — {inv/1e6:.1f}M invocações  {c.get('duration_ms',200)}ms  {c.get('memory_mb',512)}MB",
                            })
                    st.session_state["arch_components"] = loaded
                    st.session_state.pop("arch_results", None)
                    st.rerun()

        st.markdown('<hr>', unsafe_allow_html=True)

    col_build, col_arch = st.columns([1, 2], gap="large")

    with col_build:
        st.markdown('<div class="ga-section">Região base</div>', unsafe_allow_html=True)
        base_region = st.selectbox(
            "Região", options=list(CARBON_INTENSITY_STATIC.keys()),
            index=list(CARBON_INTENSITY_STATIC.keys()).index("us-east-1"),
            key="arch_region", label_visibility="collapsed",
        )

        if "arch_components" not in st.session_state:
            st.session_state["arch_components"] = []

        st.markdown('<div class="ga-section">Adicionar componente</div>', unsafe_allow_html=True)
        with st.expander("+ Adicionar componente",
                          expanded=len(st.session_state["arch_components"]) == 0):
            comp_type = st.selectbox("Tipo de componente", ["EC2", "RDS", "Lambda"], key="new_comp_type")

            if comp_type == "EC2":
                new_inst  = st.selectbox("Instância", ALL_INSTANCES, key="new_ec2_inst")
                new_cpu   = st.slider("CPU (%)", 1, 100, 50, key="new_ec2_cpu")
                new_hours = st.slider("Horas/mês", 1, 730, 730, key="new_ec2_h")
                new_os    = "Linux"
                preview   = f"EC2  {new_inst} — {new_hours}h · {new_cpu}% CPU"

            elif comp_type == "RDS":
                new_rds_inst   = st.selectbox("Instância", RDS_INSTANCES, key="new_rds_inst")
                new_rds_engine = st.selectbox("Engine",
                                              ["MySQL", "PostgreSQL", "MariaDB"],
                                              key="new_rds_eng")
                new_rds_cpu    = st.slider("CPU (%)", 1, 100, 30, key="new_rds_cpu")
                new_rds_hours  = st.slider("Horas/mês", 1, 730, 730, key="new_rds_h")
                new_rds_multi  = st.checkbox("Multi-AZ", key="new_rds_multi")
                preview = f"RDS  {new_rds_inst}  {new_rds_engine} — {new_rds_hours}h · {new_rds_cpu}% CPU"

            elif comp_type == "Lambda":
                new_inv  = st.number_input("Invocations/mo (M)", 0.1, 1000.0,
                                           1.0, 0.1, key="new_lambda_inv")
                new_dur  = st.number_input("Avg duration (ms)", 1, 30000,
                                           200, key="new_lambda_dur")
                new_mem  = st.selectbox("Memória Lambda (MB)",
                                        [128, 256, 512, 1024, 2048, 4096],
                                        index=2, key="new_lambda_mem")
                new_arch = st.selectbox("Arquitetura", ["x86", "arm"], key="new_lambda_arch")
                preview  = f"Lambda — {new_inv:.1f}M invocações  {new_dur}ms  {new_mem}MB"

            st.caption(preview)
            if st.button("Adicionar", type="primary", key="add_comp"):
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
                        "multi_az": new_rds_multi, "hours": int(new_rds_hours),
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
            st.markdown('<div class="ga-section">Componentes</div>',
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
            st.markdown('<div class="ga-section">Comparar regiões</div>',
                        unsafe_allow_html=True)
            arch_regions = []
            for reg in list(CARBON_INTENSITY_STATIC.keys()):
                if st.checkbox(reg,
                               value=reg in DEFAULT_REGIONS,
                               key=f"arch_reg_{reg}"):
                    arch_regions.append(reg)

            if st.button("Calcular arquitetura", type="primary",
                         use_container_width=True, key="calc_arch"):
                if not arch_regions:
                    st.warning("Selecione ao menos uma região.")
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

            if st.button("Limpar", key="clear_arch"):
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
            m1.metric("SCI — Região base", f"{base_sci_a:.4f} gCO₂/h", arch_base)
            m2.metric("Menor SCI encontrado", f"{best_a['sci_score']:.4f} gCO₂/h", best_a["region"])
            m3.metric("Redução de carbono", f"{reduction}%", f"vs. {arch_base}")
            m4.metric("Custo — Região base", f"${base_cost_a:.2f}/mo")

            if reduction > 0:
                custo_str = (f"${abs(cost_diff):.2f}/mês mais barato" if cost_diff < 0
                             else f"${cost_diff:.2f}/mês a mais" if cost_diff > 0
                             else "mesmo custo")
                st.markdown(
                    f'<div class="ga-banner">Melhor região para esta arquitetura: <b>{best_a["region"]}</b>, '
                    f'<b>{reduction}% menos carbono</b> e {custo_str} vs. {arch_base}.</div>',
                    unsafe_allow_html=True
                )

            # Recalcula Pareto para arquitetura
            def _arch_dominated(row, df):
                for _, other in df.iterrows():
                    if other.name == row.name: continue
                    if (other["sci_score"] <= row["sci_score"] and
                        other["cost_usd_month"] <= row["cost_usd_month"] and
                        (other["sci_score"] < row["sci_score"] or
                         other["cost_usd_month"] < row["cost_usd_month"])):
                        return True
                return False

            arch_df["pareto_optimal"] = [not _arch_dominated(r, arch_df)
                                         for _, r in arch_df.iterrows()]
            arch_df["Status"] = arch_df["pareto_optimal"].map(
                {True: "Pareto ótimo", False: "Dominado"})

            st.markdown('<div class="ga-section">Pareto Front — Custo vs. Carbono</div>',
                        unsafe_allow_html=True)
            st.markdown(f'''
            <div style="background:{C["bg3"]};border:1px solid {C["border"]};
                        border-radius:6px;padding:14px 18px;margin-bottom:12px;">
                <div style="font-size:13px;color:{C["text2"]};line-height:1.7;font-family:'IBM Plex Sans',sans-serif;">
                    Cada ponto representa esta arquitetura hospedada em uma região diferente.
                    <b style="color:{C["green"]}">Pareto ótimo</b> significa que não existe outra região
                    simultaneamente mais barata e com menos carbono.
                </div>
            </div>
            ''', unsafe_allow_html=True)

            fig_arch = go.Figure()
            for status, color, opacity in [
                ("Pareto ótimo", C["green"], 0.95),
                ("Dominado",     C["text3"], 0.45),
            ]:
                sub = arch_df[arch_df["Status"] == status]
                if not len(sub): continue
                fig_arch.add_trace(go.Scatter(
                    x=sub["cost_usd_month"], y=sub["sci_score"],
                    mode="markers", name=status,
                    marker=dict(symbol="circle", size=10, color=color,
                                opacity=opacity, line=dict(width=0.5, color=C["bg"])),
                    customdata=sub[["region", "carbon_intensity"]].values,
                    hovertemplate=(
                        "<b>%{customdata[0]}</b><br>"
                        "Custo: $%{x:.2f}/mês<br>"
                        "SCI: %{y:.4f} gCO₂/h<br>"
                        "Grid: %{customdata[1]:.0f} gCO₂/kWh<extra></extra>"
                    ),
                ))
            if len(base_row) > 0:
                fig_arch.add_trace(go.Scatter(
                    x=[base_row["cost_usd_month"].values[0]],
                    y=[base_row["sci_score"].values[0]],
                    mode="markers", name="Região base",
                    marker=dict(symbol="star", size=16, color="#E8963A",
                                line=dict(width=1, color=C["bg"])),
                    customdata=[[arch_base]],
                    hovertemplate="<b>Base: %{customdata[0]}</b><br>Custo: $%{x:.2f}/mês<br>SCI: %{y:.4f} gCO₂/h<extra></extra>",
                ))
            fig_arch.update_layout(**chart_layout(380, legend_title=""))
            fig_arch.update_layout(
                xaxis_title="Custo total/mês (USD)",
                yaxis_title="SCI total (gCO₂eq/h)"
            )
            st.caption("Verde = Pareto ótimo  ·  Cinza = Dominado  ·  Estrela = região base")
            st.plotly_chart(fig_arch, use_container_width=True)

            # ── Índice de Eficiência (igual tab1) ─────────────────────
            st.markdown('<div class="ga-section">Índice de Eficiência</div>',
                        unsafe_allow_html=True)
            st.caption("Pontuação composta que combina SCI e custo. Ajuste o peso para priorizar carbono ou custo.")
            arch_w = st.slider("Prioridade: Custo — Carbono", 0, 100, 50,
                               key="arch_weight", format="%d%%")
            sci_n  = (arch_df["sci_score"] - arch_df["sci_score"].min()) / (arch_df["sci_score"].max() - arch_df["sci_score"].min() + 1e-9)
            cost_n = (arch_df["cost_usd_month"] - arch_df["cost_usd_month"].min()) / (arch_df["cost_usd_month"].max() - arch_df["cost_usd_month"].min() + 1e-9)
            arch_df["score"] = -(sci_n * (arch_w/100) + cost_n * (1 - arch_w/100)) * 100
            eff_tbl = arch_df[["region", "cost_usd_month", "sci_score", "score", "Status"]].sort_values("score", ascending=False).rename(columns={
                "region": "Região", "cost_usd_month": "Custo/mês",
                "sci_score": "SCI (gCO₂/h)", "score": "Score", "Status": "Status"
            })

            def _color_status_arch(val):
                if val == "Pareto ótimo": return f"color: {C['green']}; font-weight:600"
                return f"color: {C['text3']}"

            st.dataframe(
                eff_tbl.style
                    .format({"Custo/mês": "${:.2f}", "SCI (gCO₂/h)": "{:.4f}", "Score": "{:.1f}"})
                    .map(_color_status_arch, subset=["Status"])
                    .map(lambda v: f"color:{C['green']};font-weight:600" if isinstance(v, str) and "ótimo" in v else "", subset=["Região"])
                    .background_gradient(subset=["Score"], cmap="RdYlGn"),
                use_container_width=True, hide_index=True,
            )

            # ── Latência inter-região ──────────────────────────────────
            st.markdown('<div class="ga-section">Latência de rede</div>', unsafe_allow_html=True)
            st.markdown(f"""
            <div style="background:{C['bg3']};border:1px solid {C['border']};border-radius:6px;
                        padding:12px 16px;margin-bottom:8px;font-size:12px;color:{C['text2']};line-height:1.7;">
                Latência aproximada entre a região base
                <b style="color:{C['text']}">{arch_base}</b> e cada região calculada (RTT, P50).
                Valores altos impactam aplicações com chamadas síncronas frequentes ao banco de dados.
                Fonte: <b>CloudPing.co</b> — medições em tempo real entre regiões AWS.
            </div>
            """, unsafe_allow_html=True)

            arch_lat_rows = []
            for _, row in arch_df.sort_values("sci_score").iterrows():
                reg  = row["region"]
                lat  = get_latency(arch_base, reg)
                flag = "—" if lat is None else (
                    f"🟢 {lat} ms" if lat < 80
                    else f"🟡 {lat} ms" if lat < 150
                    else f"🔴 {lat} ms"
                )
                arch_lat_rows.append({
                    "Região": reg,
                    "SCI total (gCO₂/h)": f"{row['sci_score']:.4f}",
                    "Custo/mês": f"${row['cost_usd_month']:.2f}",
                    "Latência (ms)": flag,
                    "Status": row["Status"],
                })
            if arch_lat_rows:
                arch_lat_df = pd.DataFrame(arch_lat_rows)
                st.dataframe(arch_lat_df, use_container_width=True, hide_index=True)
            st.caption("🟢 < 80 ms · 🟡 80–150 ms · 🔴 > 150 ms")

            # ── Export PDF ────────────────────────────────────────────────
            st.markdown('<div class="ga-section">Exportar</div>', unsafe_allow_html=True)
            if st.button("Gerar relatório PDF", key="arch_pdf_btn"):
                try:
                    from core.report_generator import generate_report_arch as _gen_arch
                    _label = st.session_state.get("arch_name", "Arquitetura")
                    _pdf   = _gen_arch(arch_df, arch_base, base_sci_a, base_cost_a, reduction, _label)
                    st.download_button("Baixar PDF", _pdf,
                                       file_name="greenarch_arquitetura.pdf",
                                       mime="application/pdf", key="arch_pdf_dl")
                except Exception as e:
                    st.error(f"Erro ao gerar PDF: {e}")


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

if tab3 is not None:
  with tab3:
      st.markdown('<div class="ga-title">Comparação de Famílias</div>', unsafe_allow_html=True)
      st.markdown(
          '<div class="ga-subtitle">Given a vCPU and memory requirement, compare all instance '
          'que atendem o requisito — mostrando SCI e custo por arquitetura de processador.</div>',
          unsafe_allow_html=True
      )

      with st.form("form_family"):
          ff1, ff2, ff3, ff4 = st.columns(4)
          with ff1:
              req_vcpu = st.selectbox(
                  "vCPUs necessários",
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
                  "Memória necessária (GiB)",
                  options=mem_opts,
                  key="req_mem",
              )
          with ff3:
              fam_region = st.selectbox(
                  "Região",
                  options=list(CARBON_INTENSITY_STATIC.keys()),
                  index=list(CARBON_INTENSITY_STATIC.keys()).index("us-east-1"),
                  key="fam_region",
              )
          with ff4:
              fam_cpu = st.slider("Utilização de CPU (%)", 1, 100, 50, key="fam_cpu")

          submitted_fam = st.form_submit_button("Comparar famílias", type="primary")

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
                              "Instância": inst,
                              "Family": spec["family"],
                              "Processor": spec["proc"],
                              "Tipo de componente": spec["type"],
                              "vCPU": spec["vcpu"],
                              "Memory (GiB)": spec["mem_gib"],
                              "SCI (gCO2/h)": r["sci_score_gco2_per_hour"],
                              "Custo/mês": r["cost_usd_month"],
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
          best_cost = fam_df.loc[fam_df["Custo/mês"].idxmin()]
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
          m1.metric("Menor SCI encontrado", f"{best_sci['SCI (gCO2/h)']:.4f} gCO₂/h",
                    best_sci["Instância"])
          m2.metric("Menor custo", f"${best_cost['Custo/mês']:.2f}/mo",
                    best_cost["Instância"])
          m3.metric("Highest SCI", f"{worst_sci['SCI (gCO2/h)']:.4f} gCO₂/h",
                    worst_sci["Instância"])
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
          st.caption("Todas as instâncias têm os mesmos recursos de compute. As diferenças revelam eficiência do hardware.")

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
                  x=sub["Custo/mês"], y=sub["SCI (gCO2/h)"],
                  mode="markers+text",
                  name=proc,
                  text=sub["Instância"],
                  textposition="middle right",
                  textfont=dict(size=10),
                  marker=dict(
                      size=12,
                      color=proc_colors.get(proc, "#888888"),
                      line=dict(width=0.5, color="#0D0F0E"),
                  ),
                  customdata=sub[["Family", "Tipo de componente", "Energy (kWh/h)"]].values,
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
              xaxis_title="Custo mensal (USD)",
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
              name="Operacional (E×I)",
              x=fam_sorted["Instância"],
              y=fam_sorted["Operational C."],
              marker_color=C["green"], marker_opacity=0.85,
          ))
          fig_fam_bar.add_trace(go.Bar(
              name="Embutido (M)",
              x=fam_sorted["Instância"],
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
              "Instância", "Family", "Processor", "Tipo de componente",
              "SCI (gCO2/h)", "Custo/mês", "Operational C.", "Embodied C.", "Energy (kWh/h)"
          ]].sort_values("SCI (gCO2/h)")
          st.dataframe(
              display_fam.style
                  .format({
                      "SCI (gCO2/h)": "{:.4f}",
                      "Custo/mês": "${:.2f}",
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
    f'<span>Carbon intensity baseada em médias anuais 2022–2023. Fontes: Electricity Maps, EPA eGRID, IEA.</span>'
    f'</div>',
    unsafe_allow_html=True
)
