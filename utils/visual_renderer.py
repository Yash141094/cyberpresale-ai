"""
Visual Renderer for CyberPresales AI
Renders beautiful charts and diagrams from structured data
"""
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np

# Corporate color palette
BG       = "#0d0f14"
SURFACE  = "#13161e"
SURFACE2 = "#191d28"
BORDER   = "#252b38"
ACCENT   = "#4f8ef7"
GREEN    = "#34d399"
AMBER    = "#fbbf24"
RED      = "#f87171"
PURPLE   = "#a78bfa"
TEAL     = "#38bdf8"
TEXT     = "#e8eaf0"
TEXT2    = "#9aa0b4"
TEXT3    = "#5c6480"


def _base_layout(title="", height=500):
    return dict(
        title=dict(text=title, font=dict(color=TEXT, size=16, family="IBM Plex Sans"), x=0.02, xanchor="left"),
        paper_bgcolor=SURFACE,
        plot_bgcolor=SURFACE2,
        font=dict(color=TEXT2, family="IBM Plex Sans", size=12),
        margin=dict(l=20, r=20, t=50, b=20),
        height=height,
    )


def render_cmo(data):
    """Current Mode of Operations — horizontal layered table diagram"""
    layers = data.get("layers", [])
    org    = data.get("org_name", "Customer")
    risk   = data.get("risk_level", "High")
    gaps   = data.get("key_gaps", [])

    if not layers:
        return None

    colors_map = {"red": "#ef4444", "orange": "#f59e0b", "yellow": "#fde68a", "green": "#10b981"}
    risk_label = {"red": "HIGH RISK", "orange": "MEDIUM RISK", "yellow": "LOW RISK", "green": "SECURED"}

    # Build table rows — one row per layer
    layer_names   = [f"<b>{l['name']}</b>" for l in layers]
    current_state = ["<br>".join(l.get("items", ["Not specified"])) for l in layers]
    issues        = ["<br>".join(l.get("issues", ["No issues identified"])) for l in layers]
    risk_labels   = [risk_label.get(l.get("color", "orange"), "MEDIUM RISK") for l in layers]

    row_colors_name  = [colors_map.get(l.get("color", "orange"), AMBER) + "22" for l in layers]
    row_colors_issue = [colors_map.get(l.get("color", "orange"), AMBER) + "33" for l in layers]
    risk_colors      = [colors_map.get(l.get("color", "orange"), AMBER) + "55" for l in layers]

    fig = go.Figure(data=[go.Table(
        columnwidth=[160, 280, 280, 100],
        header=dict(
            values=[
                "<b>Security Domain</b>",
                "<b>Current State (What exists today)</b>",
                "<b>Gaps & Issues Identified</b>",
                "<b>Risk Level</b>",
            ],
            fill_color=["#1e1b4b", "#1e1b4b", "#7f1d1d", "#1e1b4b"],
            font=dict(color=TEXT, size=11, family="IBM Plex Sans"),
            align="left",
            height=36,
            line_color=BORDER,
        ),
        cells=dict(
            values=[layer_names, current_state, issues, risk_labels],
            fill_color=[
                row_colors_name,
                [SURFACE2] * len(layers),
                row_colors_issue,
                risk_colors,
            ],
            font=dict(color=TEXT2, size=10, family="IBM Plex Sans"),
            align="left",
            height=40,
            line_color=BORDER,
        ),
    )])

    title = f"CMO — Current Mode of Operations  ·  {org}  ·  Overall Risk: {risk}"
    fig.update_layout(
        **_base_layout(title, height=max(380, len(layers) * 50 + 100)),
        margin=dict(l=10, r=10, t=50, b=60),
    )

    if gaps:
        fig.add_annotation(
            text="⚠  Key Gaps: " + "  ·  ".join(gaps),
            xref="paper", yref="paper",
            x=0.0, y=-0.12,
            showarrow=False,
            font=dict(color=AMBER, size=11),
            align="left",
        )

    return fig


def render_fmo(data):
    """Future Mode of Operations — horizontal layered architecture table"""
    layers      = data.get("layers", [])
    arch        = data.get("architecture_name", "Integrated Security Platform")
    outcomes    = data.get("key_outcomes", [])
    integration = data.get("integration_layer", "Unified Security Fabric")

    if not layers:
        return None

    layer_colors_list = [GREEN, TEAL, ACCENT, PURPLE, AMBER, "#ec4899", "#f97316", "#06b6d4"]

    layer_names = [f"<b>{l['name']}</b>" for l in layers]
    vendors     = [l.get("vendor", "TBD") for l in layers]
    solutions   = ["<br>".join(l.get("solutions", [])) for l in layers]
    capabilities= ["<br>".join(l.get("capabilities", [])) for l in layers]

    row_bg   = [c + "22" for c in layer_colors_list[:len(layers)]]
    sol_bg   = [SURFACE2] * len(layers)
    cap_bg   = [c + "11" for c in layer_colors_list[:len(layers)]]
    vend_bg  = [c + "33" for c in layer_colors_list[:len(layers)]]

    fig = go.Figure(data=[go.Table(
        columnwidth=[160, 200, 240, 220],
        header=dict(
            values=[
                "<b>Security Layer</b>",
                "<b>Recommended Vendor</b>",
                "<b>Proposed Solutions</b>",
                "<b>Key Capabilities Delivered</b>",
            ],
            fill_color=["#064e3b", "#064e3b", "#064e3b", "#064e3b"],
            font=dict(color=TEXT, size=11, family="IBM Plex Sans"),
            align="left",
            height=36,
            line_color=BORDER,
        ),
        cells=dict(
            values=[layer_names, vendors, solutions, capabilities],
            fill_color=[row_bg, vend_bg, sol_bg, cap_bg],
            font=dict(color=TEXT2, size=10, family="IBM Plex Sans"),
            align="left",
            height=40,
            line_color=BORDER,
        ),
    )])

    title = f"FMO — Future Mode of Operations  ·  {arch}"
    fig.update_layout(
        **_base_layout(title, height=max(400, len(layers) * 50 + 120)),
        margin=dict(l=10, r=10, t=50, b=80),
    )

    if integration:
        fig.add_annotation(
            text=f"🔗  Integration Layer: {integration}",
            xref="paper", yref="paper",
            x=0.0, y=-0.1,
            showarrow=False,
            font=dict(color=ACCENT, size=11),
            align="left",
        )

    if outcomes:
        fig.add_annotation(
            text="✓  Key Outcomes: " + "  ·  ".join(outcomes),
            xref="paper", yref="paper",
            x=0.0, y=-0.18,
            showarrow=False,
            font=dict(color=GREEN, size=11),
            align="left",
        )

    return fig


def render_threat_coverage(data):
    """Threat Coverage Matrix — readable table format"""
    threats   = data.get("threats", [])
    solutions = data.get("solutions", [])
    coverage  = data.get("coverage", {})

    if not threats or not solutions:
        return None

    # Label and colour per score
    score_label = {0: "✗  None", 1: "◑  Partial", 2: "●  Good", 3: "★  Strong"}
    score_color = {0: "#450a0a", 1: "#78350f", 2: "#064e3b", 3: "#065f46"}
    score_text  = {0: "#ef4444", 1: "#f59e0b", 2: "#34d399", 3: "#10b981"}

    # Build cell values and colours per solution column
    col_values = []
    col_fill   = []
    col_font   = []

    for sol in solutions:
        col_vals  = []
        col_fills = []
        col_fonts = []
        for threat in threats:
            row = coverage.get(threat, [0] * len(solutions))
            if len(row) < len(solutions):
                row = row + [0] * (len(solutions) - len(row))
            idx = solutions.index(sol) if sol in solutions else 0
            score = row[idx] if idx < len(row) else 0
            col_vals.append(score_label[score])
            col_fills.append(score_color[score])
            col_fonts.append(score_text[score])
        col_values.append(col_vals)
        col_fill.append(col_fills)
        col_font.append(col_fonts)

    header_vals = ["<b>Threat / Attack Vector</b>"] + [f"<b>{s}</b>" for s in solutions]
    col_widths  = [180] + [120] * len(solutions)

    fig = go.Figure(data=[go.Table(
        columnwidth=col_widths,
        header=dict(
            values=header_vals,
            fill_color=["#1e1b4b"] + ["#1e3a5f"] * len(solutions),
            font=dict(color=TEXT, size=11, family="IBM Plex Sans"),
            align="center",
            height=38,
            line_color=BORDER,
        ),
        cells=dict(
            values=[[f"<b>{t}</b>" for t in threats]] + col_values,
            fill_color=[[SURFACE2] * len(threats)] + col_fill,
            font=dict(
                color=[TEXT] + col_font,
                size=10,
                family="IBM Plex Sans"
            ),
            align=["left"] + ["center"] * len(solutions),
            height=34,
            line_color=BORDER,
        ),
    )])

    fig.update_layout(
        **_base_layout("Threat Coverage Matrix  ·  Based on RFP Requirements & Current Market Threats",
                       height=max(420, len(threats) * 38 + 100)),
        margin=dict(l=10, r=10, t=50, b=60),
    )

    fig.add_annotation(
        text="★ Strong Coverage  ·  ● Good Coverage  ·  ◑ Partial Coverage  ·  ✗ No Coverage",
        xref="paper", yref="paper",
        x=0.0, y=-0.1,
        showarrow=False,
        font=dict(color=TEXT2, size=10),
        align="left",
    )

    return fig


def render_requirements_traceability(data):
    """Requirements Traceability Matrix as interactive table"""
    reqs = data.get("requirements", [])
    if not reqs:
        return None

    ids       = [r.get("id","") for r in reqs]
    domains   = [r.get("domain","") for r in reqs]
    req_texts = [r.get("requirement","")[:60]+"..." if len(r.get("requirement",""))>60 else r.get("requirement","") for r in reqs]
    priorities= [r.get("priority","") for r in reqs]
    solutions = [r.get("proposed_solution","") for r in reqs]
    coverage  = [r.get("coverage","") for r in reqs]
    notes     = [r.get("notes","") for r in reqs]

    # Color coverage cells
    cov_colors = []
    for c in coverage:
        if c == "Full":    cov_colors.append("#064e3b")
        elif c == "Partial": cov_colors.append("#78350f")
        else:              cov_colors.append("#7f1d1d")

    pri_colors = []
    for p in priorities:
        if p == "Mandatory": pri_colors.append("#1e3a5f")
        elif p == "Preferred": pri_colors.append("#3b2a6e")
        else:                 pri_colors.append(SURFACE2)

    fig = go.Figure(data=[go.Table(
        columnwidth=[60, 110, 280, 100, 180, 90, 200],
        header=dict(
            values=["<b>ID</b>", "<b>Domain</b>", "<b>Requirement</b>",
                    "<b>Priority</b>", "<b>Proposed Solution</b>",
                    "<b>Coverage</b>", "<b>Notes</b>"],
            fill_color=ACCENT,
            font=dict(color=TEXT, size=11, family="IBM Plex Sans"),
            align="left",
            height=32,
            line_color=BORDER,
        ),
        cells=dict(
            values=[ids, domains, req_texts, priorities, solutions, coverage, notes],
            fill_color=[
                [SURFACE2]*len(ids),
                [SURFACE2]*len(domains),
                [SURFACE2]*len(req_texts),
                pri_colors,
                [SURFACE2]*len(solutions),
                cov_colors,
                [SURFACE2]*len(notes),
            ],
            font=dict(color=TEXT2, size=10, family="IBM Plex Sans"),
            align="left",
            height=28,
            line_color=BORDER,
        ),
    )])

    fig.update_layout(
        **_base_layout("Requirements Traceability Matrix  -  RFP Requirements to Proposed Solutions",
                       height=max(400, len(reqs) * 32 + 100)),
        margin=dict(l=10, r=10, t=50, b=10),
    )

    return fig


def render_vendor_positioning(data):
    """Vendor Positioning Map — 2x2 quadrant chart"""
    vendors = data.get("vendors", [])
    recommended = data.get("recommended_vendor", "")
    rationale = data.get("rationale", "")

    if not vendors:
        return None

    names        = [v["name"] for v in vendors]
    completeness = [v.get("completeness", 5) for v in vendors]
    ease         = [v.get("ease", 5) for v in vendors]
    quadrants    = [v.get("quadrant", "Niche") for v in vendors]
    strengths    = [v.get("key_strength", "") for v in vendors]
    risks        = [v.get("key_risk", "") for v in vendors]

    # Colors by quadrant
    q_colors = {"Leader": GREEN, "Challenger": ACCENT, "Niche": AMBER, "Visionary": PURPLE}
    colors = [q_colors.get(q, TEXT2) for q in quadrants]

    # Bubble sizes proportional to completeness
    sizes = [c * 8 for c in completeness]

    fig = go.Figure()

    # Quadrant background shading
    fig.add_shape(type="rect", x0=5, x1=10.5, y0=5, y1=10.5,
                  fillcolor=f"rgba(52,211,153,0.04)", line_width=0)
    fig.add_shape(type="rect", x0=0, x1=5, y0=5, y1=10.5,
                  fillcolor=f"rgba(167,139,250,0.04)", line_width=0)
    fig.add_shape(type="rect", x0=5, x1=10.5, y0=0, y1=5,
                  fillcolor=f"rgba(79,142,247,0.04)", line_width=0)
    fig.add_shape(type="rect", x0=0, x1=5, y0=0, y1=5,
                  fillcolor=f"rgba(248,113,113,0.04)", line_width=0)

    # Quadrant divider lines
    fig.add_shape(type="line", x0=5, x1=5, y0=0, y1=10.5,
                  line=dict(color=BORDER, width=1, dash="dot"))
    fig.add_shape(type="line", x0=0, x1=10.5, y0=5, y1=5,
                  line=dict(color=BORDER, width=1, dash="dot"))

    # Quadrant labels
    for label, x, y in [("LEADERS", 7.5, 10.2), ("VISIONARIES", 2.5, 10.2),
                         ("CHALLENGERS", 7.5, 0.3), ("NICHE", 2.5, 0.3)]:
        fig.add_annotation(text=label, x=x, y=y, showarrow=False,
                           font=dict(color=TEXT3, size=9, family="IBM Plex Sans"),
                           xanchor="center")

    # Vendor bubbles
    for i, name in enumerate(names):
        is_recommended = (name == recommended)
        fig.add_trace(go.Scatter(
            x=[completeness[i]],
            y=[ease[i]],
            mode="markers+text",
            marker=dict(
                size=sizes[i],
                color=colors[i],
                opacity=0.85,
                line=dict(color="white" if is_recommended else BORDER,
                          width=3 if is_recommended else 1),
            ),
            text=[f"  {name}{'  ★' if is_recommended else ''}"],
            textposition="middle right",
            textfont=dict(color=TEXT if is_recommended else TEXT2, size=11,
                          family="IBM Plex Sans"),
            hovertemplate=(
                f"<b>{name}</b><br>"
                f"Completeness: {completeness[i]}/10<br>"
                f"Ease of Implementation: {ease[i]}/10<br>"
                f"Quadrant: {quadrants[i]}<br>"
                f"Strength: {strengths[i]}<br>"
                f"Risk: {risks[i]}"
                "<extra></extra>"
            ),
            name=name,
            showlegend=False,
        ))

    fig.update_layout(
        **_base_layout("Vendor Positioning Map  ·  Solution Completeness vs Implementation Ease", height=520),
        xaxis=dict(title=dict(text="Solution Completeness", font=dict(color=TEXT2, size=11)),
                   range=[0, 10.5], showgrid=True,
                   gridcolor=BORDER, tickfont=dict(color=TEXT2)),
        yaxis=dict(title=dict(text="Ease of Implementation", font=dict(color=TEXT2, size=11)),
                   range=[0, 10.5], showgrid=True,
                   gridcolor=BORDER, tickfont=dict(color=TEXT2)),
        showlegend=False,
    )

    if rationale:
        fig.add_annotation(
            text=f"★  Recommended: {recommended}  ·  {rationale}",
            xref="paper", yref="paper",
            x=0.0, y=-0.1,
            showarrow=False,
            font=dict(color=GREEN, size=10),
            align="left",
        )

    return fig
