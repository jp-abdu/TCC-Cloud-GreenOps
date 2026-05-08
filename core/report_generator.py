"""
core/report_generator.py
-------------------------
Gera um relatorio PDF com os resultados do GreenArch.
Usa reportlab — sem dependencias externas alem do pip install reportlab.

Uso:
    from core.report_generator import generate_report

    pdf_bytes = generate_report(result, instance_label)
    with open("relatorio.pdf", "wb") as f:
        f.write(pdf_bytes)
"""

import io
from datetime import datetime

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

# ── Paleta de cores ────────────────────────────────────────
GREEN_DARK  = colors.HexColor("#1A5E3A")
GREEN_MID   = colors.HexColor("#1A8C4E")
GREEN_LIGHT = colors.HexColor("#E8F5E9")
BLUE_DARK   = colors.HexColor("#1A3A6B")
BLUE_MID    = colors.HexColor("#2E5FAC")
BLUE_LIGHT  = colors.HexColor("#F0F4FF")
ORANGE      = colors.HexColor("#E65100")
GRAY        = colors.HexColor("#666666")
GRAY_LIGHT  = colors.HexColor("#F5F5F5")
WHITE       = colors.white
BLACK       = colors.black


def _build_styles():
    """Cria estilos customizados para o relatorio."""
    base = getSampleStyleSheet()

    styles = {
        "title": ParagraphStyle(
            "title", parent=base["Normal"],
            fontSize=28, fontName="Helvetica-Bold",
            textColor=BLUE_DARK, spaceAfter=4,
            alignment=TA_CENTER,
        ),
        "subtitle": ParagraphStyle(
            "subtitle", parent=base["Normal"],
            fontSize=11, fontName="Helvetica",
            textColor=GRAY, spaceAfter=2,
            alignment=TA_CENTER,
        ),
        "h1": ParagraphStyle(
            "h1", parent=base["Normal"],
            fontSize=14, fontName="Helvetica-Bold",
            textColor=BLUE_DARK, spaceBefore=16, spaceAfter=6,
        ),
        "h2": ParagraphStyle(
            "h2", parent=base["Normal"],
            fontSize=11, fontName="Helvetica-Bold",
            textColor=GREEN_DARK, spaceBefore=10, spaceAfter=4,
        ),
        "body": ParagraphStyle(
            "body", parent=base["Normal"],
            fontSize=9, fontName="Helvetica",
            textColor=BLACK, spaceAfter=4, leading=14,
        ),
        "caption": ParagraphStyle(
            "caption", parent=base["Normal"],
            fontSize=8, fontName="Helvetica",
            textColor=GRAY, spaceAfter=3, leading=12,
        ),
        "highlight": ParagraphStyle(
            "highlight", parent=base["Normal"],
            fontSize=10, fontName="Helvetica-Bold",
            textColor=GREEN_DARK, spaceAfter=4,
        ),
        "footer": ParagraphStyle(
            "footer", parent=base["Normal"],
            fontSize=7, fontName="Helvetica",
            textColor=GRAY, alignment=TA_CENTER,
        ),
        "metric_value": ParagraphStyle(
            "metric_value", parent=base["Normal"],
            fontSize=18, fontName="Helvetica-Bold",
            textColor=BLUE_DARK, alignment=TA_CENTER,
        ),
        "metric_label": ParagraphStyle(
            "metric_label", parent=base["Normal"],
            fontSize=8, fontName="Helvetica",
            textColor=GRAY, alignment=TA_CENTER,
        ),
    }
    return styles


def _metric_table(metrics: list) -> Table:
    """
    Cria uma linha de metricas de destaque.
    metrics = [(label, value, unit), ...]
    """
    data = [[
        Paragraph(f'<font size="16" color="#1A3A6B"><b>{v}</b></font><br/>'
                  f'<font size="7" color="#888888">{u}</font><br/>'
                  f'<font size="8" color="#444444">{l}</font>', _build_styles()["body"])
        for l, v, u in metrics
    ]]
    col_width = 6.5 * inch / len(metrics)
    t = Table(data, colWidths=[col_width] * len(metrics))
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), BLUE_LIGHT),
        ("BOX", (0, 0), (-1, -1), 0.5, BLUE_MID),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#C5D5F0")),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ]))
    return t


def _data_table(headers: list, rows: list, col_widths: list,
                highlight_row: int = None) -> Table:
    """Cria tabela de dados formatada."""
    styles = _build_styles()

    header_cells = [
        Paragraph(f'<b>{h}</b>', ParagraphStyle(
            "th", fontSize=8, fontName="Helvetica-Bold",
            textColor=WHITE, alignment=TA_CENTER,
        ))
        for h in headers
    ]

    data = [header_cells]
    for ri, row in enumerate(rows):
        cells = []
        for ci, cell in enumerate(row):
            align = TA_LEFT if ci <= 1 else TA_RIGHT
            style = ParagraphStyle(
                f"td_{ri}_{ci}", fontSize=8, fontName="Helvetica",
                textColor=BLACK, alignment=align,
            )
            cells.append(Paragraph(str(cell), style))
        data.append(cells)

    t = Table(data, colWidths=col_widths)

    ts = [
        ("BACKGROUND", (0, 0), (-1, 0), BLUE_DARK),
        ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [GRAY_LIGHT, WHITE]),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#CCCCCC")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]

    if highlight_row is not None and highlight_row > 0:
        ts += [
            ("BACKGROUND", (0, highlight_row), (-1, highlight_row), GREEN_LIGHT),
            ("TEXTCOLOR", (0, highlight_row), (-1, highlight_row), GREEN_DARK),
            ("FONTNAME", (0, highlight_row), (-1, highlight_row), "Helvetica-Bold"),
        ]

    t.setStyle(TableStyle(ts))
    return t


def generate_report(result: dict, instance_label: str = "") -> bytes:
    """
    Gera o relatorio PDF completo a partir do resultado do ScenarioEngine.

    Parametros:
        result         : dict retornado por ScenarioEngine.compare()
        instance_label : nome da instancia base

    Retorna:
        bytes do PDF gerado
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=0.75 * inch,
        leftMargin=0.75 * inch,
        topMargin=0.6 * inch,
        bottomMargin=0.75 * inch,
        title="GreenArch — Relatorio de Analise",
        author="GreenArch",
    )

    styles  = _build_styles()
    story   = []
    base    = result["base_scenario"]
    now     = datetime.now().strftime("%d/%m/%Y %H:%M")

    # Filtra tudo para apenas a instância selecionada — sem equivalentes
    instance_base = instance_label.strip() if instance_label else (base["instance_type"] if base else "")
    all_scenarios = [sc for sc in result.get("all_scenarios", []) if sc["instance_type"] == instance_base]

    # Recalcula Pareto do zero para o conjunto filtrado
    # (os flags originais do engine incluíam equivalentes)
    def _dominated(row, rows):
        for other in rows:
            if other is row:
                continue
            if (other["sci_score"] <= row["sci_score"] and
                other["cost_usd_month"] <= row["cost_usd_month"] and
                (other["sci_score"] < row["sci_score"] or
                 other["cost_usd_month"] < row["cost_usd_month"])):
                return True
        return False

    for sc in all_scenarios:
        sc["pareto_optimal"] = not _dominated(sc, all_scenarios)

    pareto = [sc for sc in all_scenarios if sc["pareto_optimal"]]

    # Reconstroi summary baseado nos dados filtrados
    all_sorted_tmp = sorted(all_scenarios, key=lambda x: x["sci_score"])
    best_sci_f  = all_sorted_tmp[0] if all_sorted_tmp else None
    best_cost_f = sorted(all_scenarios, key=lambda x: x["cost_usd_month"])[0] if all_scenarios else None
    s = {
        "total_scenarios": len(all_scenarios),
        "pareto_count": len(pareto),
        "best_sci_scenario": best_sci_f,
        "best_cost_scenario": best_cost_f,
        "sci_reduction_vs_base": round(
            (base["sci_score"] - best_sci_f["sci_score"]) / base["sci_score"] * 100, 1
        ) if best_sci_f and base else 0,
    }

    # ── CABECALHO ──────────────────────────────────────────────────────
    story.append(Paragraph("GreenArch", styles["title"]))
    story.append(Paragraph(f"Relatorio gerado em {now}", styles["caption"]))
    story.append(HRFlowable(width="100%", thickness=2, color=BLUE_DARK, spaceBefore=4, spaceAfter=12))

    # ── CONFIGURACAO DO WORKLOAD ────────────────────────────────────────
    story.append(Paragraph("Configuracao Analisada", styles["h1"]))

    if base:
        config_rows = [
            ["Instancia base", instance_label or base["instance_type"]],
            ["Regiao base", f"{base['region']} ({base['region_name']})"],
            ["SCI do cenario base", f"{base['sci_score']:.4f} gCO2eq/hora"],
            ["Custo do cenario base", f"${base['cost_usd_month']:.2f}/mes"],
            ["Cenarios calculados", str(s["total_scenarios"])],
            ["Solucoes Pareto-otimas", str(s["pareto_count"])],
        ]
        t = Table(config_rows, colWidths=[2.5 * inch, 4.0 * inch])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (0, -1), GRAY_LIGHT),
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#DDDDDD")),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]))
        story.append(t)

    story.append(Spacer(1, 0.15 * inch))

    # ── METRICAS DE DESTAQUE ───────────────────────────────────────────
    story.append(Paragraph("Resultados Principais", styles["h1"]))

    best_sci  = s.get("best_sci_scenario")
    best_cost = s.get("best_cost_scenario")

    metrics = [
        ("Cenario base — SCI", f"{base['sci_score']:.4f}" if base else "—", "gCO2eq/hora"),
        ("Menor SCI encontrado", f"{best_sci['sci_score']:.4f}" if best_sci else "—", "gCO2eq/hora"),
        ("Reducao maxima de SCI", f"{s['sci_reduction_vs_base']:.1f}%" if s.get('sci_reduction_vs_base') else "—", "vs. cenario base"),
        ("Pareto-otimos", str(s["pareto_count"]), f"de {s['total_scenarios']} cenarios"),
    ]
    story.append(_metric_table(metrics))
    story.append(Spacer(1, 0.1 * inch))

    # Banner da melhor alternativa
    if best_sci and base:
        sci_gain   = s.get("sci_reduction_vs_base", 0)
        cost_diff  = best_sci["cost_usd_month"] - base["cost_usd_month"]
        custo_str  = (f"${abs(cost_diff):.2f}/mes mais barato"
                      if cost_diff < 0 else
                      f"${cost_diff:.2f}/mes a mais" if cost_diff > 0
                      else "mesmo custo")

        banner_text = (
            f"Melhor alternativa Pareto: <b>{best_sci['instance_type']} @ {best_sci['region']}</b> — "
            f"<b>{sci_gain:.1f}% menos carbono</b> e {custo_str} vs. cenario base."
        )
        banner_style = ParagraphStyle(
            "banner", fontSize=9, fontName="Helvetica",
            textColor=GREEN_DARK, backColor=GREEN_LIGHT,
            borderColor=GREEN_MID, borderWidth=1, borderPadding=8,
            spaceAfter=8,
        )
        story.append(Paragraph(banner_text, banner_style))

    # ── PARETO-FRONT ───────────────────────────────────────────────────
    story.append(Spacer(1, 0.1 * inch))
    story.append(Paragraph("Solucoes Pareto-Otimas", styles["h1"]))
    story.append(Paragraph(
        "Nenhuma outra combinacao de instancia e regiao e simultaneamente "
        "mais barata E com menor carbono do que as listadas abaixo.",
        styles["caption"]
    ))
    story.append(Spacer(1, 0.05 * inch))

    if pareto:
        pareto_rows = []
        for p in pareto:
            delta_sci  = p["sci_score"] - (base["sci_score"] if base else 0)
            delta_cost = p["cost_usd_month"] - (base["cost_usd_month"] if base else 0)
            pareto_rows.append([
                p["instance_type"],
                p["region"],
                f"${p['cost_usd_month']:.2f}",
                f"{p['sci_score']:.4f}",
                f"{p['carbon_intensity']:.0f}",
                f"{delta_sci:+.4f}",
                f"{delta_cost:+.2f}",
            ])

        story.append(_data_table(
            headers=["Instancia", "Regiao", "Custo/mes", "SCI (gCO2/h)",
                     "Grid (gCO2/kWh)", "Delta SCI", "Delta Custo ($)"],
            rows=pareto_rows,
            col_widths=[1.1*inch, 1.0*inch, 0.85*inch, 0.9*inch,
                        1.0*inch, 0.85*inch, 0.85*inch],
        ))
    else:
        story.append(Paragraph("Nenhuma solucao Pareto-otima encontrada.", styles["body"]))

    # ── TODOS OS CENARIOS ──────────────────────────────────────────────
    story.append(Spacer(1, 0.2 * inch))
    story.append(HRFlowable(width="100%", thickness=0.5, color=GRAY, spaceAfter=8))
    story.append(Paragraph("Todos os Cenarios Calculados", styles["h1"]))
    story.append(Paragraph(
        "Ordenados por SCI crescente. Verde = Pareto-otimo.",
        styles["caption"]
    ))
    story.append(Spacer(1, 0.05 * inch))

    all_sorted = sorted(all_scenarios, key=lambda x: x["sci_score"])

    all_rows = []
    pareto_rows_idx = []
    for ri, sc in enumerate(all_sorted):
        all_rows.append([
            sc["instance_type"],
            sc["region"],
            f"${sc['cost_usd_month']:.2f}",
            f"{sc['sci_score']:.4f}",
            f"{sc['carbon_intensity']:.0f}",
            f"{sc['operational_carbon']:.4f}",
            f"{sc['embodied_carbon']:.2f}",
            "Pareto" if sc["pareto_optimal"] else "—",
        ])
        if sc["pareto_optimal"]:
            pareto_rows_idx.append(ri + 1)  # +1 por causa do header

    t = Table(
        [[Paragraph(f'<b>{h}</b>', ParagraphStyle(
            "th2", fontSize=7, fontName="Helvetica-Bold",
            textColor=WHITE, alignment=TA_CENTER))
          for h in ["Instancia", "Regiao", "Custo/mes", "SCI",
                    "Grid", "C. oper.", "C. emb.", "Status"]]
        ] + [
            [Paragraph(str(cell), ParagraphStyle(
                f"td2_{ri}_{ci}", fontSize=7, fontName="Helvetica",
                alignment=TA_RIGHT if ci >= 2 else TA_LEFT))
             for ci, cell in enumerate(row)]
            for ri, row in enumerate(all_rows)
        ],
        colWidths=[1.05*inch, 0.9*inch, 0.75*inch, 0.72*inch,
                   0.6*inch, 0.72*inch, 0.62*inch, 0.6*inch],
    )

    ts = [
        ("BACKGROUND", (0, 0), (-1, 0), BLUE_DARK),
        ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
        ("FONTSIZE", (0, 0), (-1, -1), 7),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [GRAY_LIGHT, WHITE]),
        ("GRID", (0, 0), (-1, -1), 0.2, colors.HexColor("#CCCCCC")),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]
    for pi in pareto_rows_idx:
        ts += [
            ("BACKGROUND", (0, pi), (-1, pi), GREEN_LIGHT),
            ("TEXTCOLOR", (0, pi), (-1, pi), GREEN_DARK),
            ("FONTNAME", (0, pi), (-1, pi), "Helvetica-Bold"),
        ]
    t.setStyle(TableStyle(ts))
    story.append(t)

    # ── METODOLOGIA ────────────────────────────────────────────────────
    story.append(Spacer(1, 0.2 * inch))
    story.append(HRFlowable(width="100%", thickness=0.5, color=GRAY, spaceAfter=8))
    story.append(Paragraph("Metodologia", styles["h2"]))
    story.append(Paragraph(
        "O SCI (Software Carbon Intensity) e calculado pela formula ISO/IEC 21031:2024: "
        "<b>SCI = (E x I + M) / R</b>, onde E = energia consumida (kWh), "
        "I = intensidade de carbono do grid eletrico (gCO2eq/kWh), "
        "M = carbono embutido no hardware (gCO2eq/hora, amortizado) e "
        "R = unidade funcional (1 hora de compute).",
        styles["body"]
    ))
    story.append(Spacer(1, 0.04 * inch))
    story.append(Paragraph(
        "Fontes: AWS Pricing Bulk API (precos EC2/RDS) · "
        "Cloud Carbon Footprint — ThoughtWorks (consumo kWh por instancia) · "
        "Electricity Maps / EPA eGRID / IEA (intensidade de carbono por regiao, medias anuais 2022-2023).",
        styles["caption"]
    ))
    story.append(Paragraph(
        "Limitacao: intensidade de carbono baseada em medias anuais. "
        "Valores podem variar sazonalmente, especialmente em grids hidro-dominados.",
        styles["caption"]
    ))

    # ── RODAPE ─────────────────────────────────────────────────────────
    story.append(Spacer(1, 0.1 * inch))
    story.append(HRFlowable(width="100%", thickness=0.5, color=GRAY, spaceAfter=4))
    story.append(Paragraph(
        f"GreenArch — Carbon and Cost Architecture Advisor · ISO/IEC 21031:2024 · {now}",
        styles["footer"]
    ))

    doc.build(story)
    buffer.seek(0)
    return buffer.read()

def generate_report_arch(arch_df, base_region: str, base_sci: float,
                          base_cost: float, reduction: float,
                          arch_name: str = "Arquitetura") -> bytes:
    """Gera PDF para a aba de Arquitetura."""
    from io import BytesIO
    buffer  = BytesIO()
    styles  = _build_styles()
    story   = []
    now     = datetime.now().strftime("%d/%m/%Y %H:%M")

    best = arch_df.loc[arch_df["sci_score"].idxmin()]
    pareto_df = arch_df[arch_df["pareto_optimal"]] if "pareto_optimal" in arch_df.columns else arch_df

    doc = SimpleDocTemplate(
        buffer, pagesize=letter,
        leftMargin=0.85*inch, rightMargin=0.85*inch,
        topMargin=0.6*inch, bottomMargin=0.75*inch,
    )

    # Cabeçalho
    story.append(Paragraph("GreenArch", styles["title"]))
    story.append(Paragraph(f"Relatorio gerado em {now}", styles["caption"]))
    story.append(HRFlowable(width="100%", thickness=2, color=BLUE_DARK, spaceBefore=4, spaceAfter=12))

    # Configuração analisada
    story.append(Paragraph("Arquitetura Analisada", styles["h1"]))
    story.append(_data_table(
        ["Parametro", "Valor"],
        [
            ["Nome da arquitetura",   arch_name],
            ["Regiao base",           base_region],
            ["SCI da regiao base",    f"{base_sci:.4f} gCO2eq/hora"],
            ["Custo da regiao base",  f"${base_cost:.2f}/mes"],
            ["Regioes comparadas",    str(len(arch_df))],
            ["Solucoes Pareto-otimas", str(len(pareto_df))],
        ],
        [200, 300],
    ))

    # Resultados principais
    story.append(Spacer(1, 0.15*inch))
    story.append(Paragraph("Resultados Principais", styles["h1"]))
    story.append(_metric_table([
        (f"{base_sci:.4f}", "gCO2eq/hora", "Regiao base — SCI"),
        (f"{best['sci_score']:.4f}", "gCO2eq/hora", "Menor SCI encontrado"),
        (f"{reduction}%", "vs. regiao base", "Reducao maxima de SCI"),
        (str(len(pareto_df)), f"de {len(arch_df)} regioes", "Pareto-otimas"),
    ]))

    best_row = arch_df.loc[arch_df["sci_score"].idxmin()]
    cost_diff = best_row["cost_usd_month"] - base_cost
    cost_str = (f"${abs(cost_diff):.2f}/mes mais barata"
                if cost_diff < 0 else f"${cost_diff:.2f}/mes a mais"
                if cost_diff > 0 else "mesmo custo")
    story.append(Paragraph(
        f"Melhor regiao: <b>{best_row['region']}</b> — "
        f"<b>{reduction}% menos carbono</b> e {cost_str} vs. {base_region}.",
        styles["highlight"]
    ))

    # Tabela Pareto
    story.append(Spacer(1, 0.1*inch))
    story.append(HRFlowable(width="100%", thickness=0.5, color=GRAY, spaceAfter=8))
    story.append(Paragraph("Solucoes Pareto-Otimas", styles["h1"]))
    story.append(Paragraph(
        "Nenhuma outra regiao e simultaneamente mais barata E com menor carbono.",
        styles["caption"]
    ))

    if len(pareto_df) > 0:
        pareto_sorted = pareto_df.sort_values("sci_score")
        rows = []
        for _, p in pareto_sorted.iterrows():
            rows.append([
                p["region"],
                f"${p['cost_usd_month']:.2f}",
                f"{p['sci_score']:.4f}",
                f"{p.get('carbon_intensity', 0):.0f}",
                f"{p['cost_usd_month'] - base_cost:+.2f}",
            ])
        story.append(_data_table(
            ["Regiao", "Custo/mes", "SCI (gCO2/h)", "Grid (gCO2/kWh)", "Delta Custo ($)"],
            rows, [130, 80, 90, 90, 90],
        ))
    else:
        story.append(Paragraph("Nenhuma solucao Pareto-otima encontrada.", styles["body"]))

    # Todos os cenários
    story.append(Spacer(1, 0.2*inch))
    story.append(HRFlowable(width="100%", thickness=0.5, color=GRAY, spaceAfter=8))
    story.append(Paragraph("Todas as Regioes Calculadas", styles["h1"]))
    story.append(Paragraph("Ordenadas por SCI crescente.", styles["caption"]))

    all_sorted = arch_df.sort_values("sci_score")
    all_rows = []
    for _, sc in all_sorted.iterrows():
        is_p = sc.get("pareto_optimal", False)
        all_rows.append([
            sc["region"],
            f"${sc['cost_usd_month']:.2f}",
            f"{sc['sci_score']:.4f}",
            f"{sc.get('carbon_intensity', 0):.0f}",
            "Pareto" if is_p else "—",
        ])
    story.append(_data_table(
        ["Regiao", "Custo/mes", "SCI (gCO2/h)", "Grid (gCO2/kWh)", "Status"],
        all_rows, [130, 80, 90, 90, 90],
    ))

    # Metodologia
    story.append(Spacer(1, 0.2*inch))
    story.append(HRFlowable(width="100%", thickness=0.5, color=GRAY, spaceAfter=8))
    story.append(Paragraph("Metodologia", styles["h2"]))
    story.append(Paragraph(
        "O SCI total da arquitetura e a soma dos SCI individuais de cada componente "
        "(EC2, RDS, Lambda), calculados pela formula ISO/IEC 21031:2024: "
        "<b>SCI = (E x I + M) / R</b>. CPU fixada em 50% (baseline Cloud Carbon Footprint). "
        "Horas fixadas em 730h/mes (operacao continua 24/7).",
        styles["body"]
    ))
    story.append(Spacer(1, 0.04*inch))
    story.append(Paragraph(
        "Fontes: AWS Pricing Bulk API · Cloud Carbon Footprint (ThoughtWorks) · "
        "Electricity Maps / EPA eGRID / IEA (medias anuais 2022-2023).",
        styles["caption"]
    ))

    # Rodapé
    story.append(Spacer(1, 0.1*inch))
    story.append(HRFlowable(width="100%", thickness=0.5, color=GRAY, spaceAfter=4))
    story.append(Paragraph(
        f"GreenArch — Carbon and Cost Architecture Advisor · ISO/IEC 21031:2024 · {now}",
        styles["footer"]
    ))

    doc.build(story)
    buffer.seek(0)
    return buffer.read()
