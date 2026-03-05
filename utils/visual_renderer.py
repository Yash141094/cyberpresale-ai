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
    """Current Mode of Operations — layered risk diagram"""
    layers = data.get("layers", [])
    org = data.get("org_name", "Customer")
    risk = data.get("risk_level", "High")
    gaps = data.get("key_gaps", [])

    layer_names = [l["name"] for l in layers]
    issues_text = ["<br>".join(l.get("issues", [])) for l in layers]
    items_text  = ["<br>".join(l.get("items",  [])) for l in layers]
    colors_map  = {"red": RED, "orange": AMBER, "yellow": "#fde68a", "green": GREEN}
    bar_colors  = [colors_map.get(l.get("color","orange"), AMBER) for l in layers]
    risk_scores = [3 if l.get("color")=="red" else 2 if l.get("color")=="orange" else 1 for l in layers]

    fig = go.Figure()

    # Risk bars
    fig.add_trace(go.Bar(
        x=layer_names,
        y=risk_scores,
        marker_color=bar_colors,
        marker_line_color=BORDER,
        marker_line_width=1,
        text=[f"<b>{l['name']}</b><br><span style='font-size:10px;color:{TEXT2}'>{items_text[i]}</span>" for i, l in enumerate(layers)],
        textposition="inside",
        hovertemplate="<b>%{x}</b><br>Issues: " + "<br>".join(["%{customdata}"])+"<extra></extra>",
        customdata=issues_text,
        name="Risk Level",
        width=0.6,
    ))

    fig.update_layout(
        **_base_layout(f"CMO — Current Mode of Operations  ·  {org}  ·  Risk: {risk}", height=420),
        xaxis=dict(showgrid=False, tickfont=dict(color=TEXT, size=11)),
        yaxis=dict(showgrid=False, showticklabels=False, range=[0, 4]),
        showlegend=False,
        bargap=0.25,
    )

    # Add annotation for key gaps
    if gaps:
        fig.add_annotation(
            text="⚠  Key Gaps: " + "  ·  ".join(gaps),
            xref="paper", yref="paper",
            x=0.0, y=-0.12,
            showarrow=False,
            font=dict(color=AMBER, size=10),
            align="left",
        )

    return fig


def render_fmo(data):
    """Future Mode of Operations — solution architecture diagram"""
    layers = data.get("layers", [])
    arch   = data.get("architecture_name", "Integrated Security Platform")
    outcomes = data.get("key_outcomes", [])
    integration = data.get("integration_layer", "Unified Security Fabric")

    layer_names = [l["name"] for l in layers]
    vendors     = [l.get("vendor", "") for l in layers]
    caps_text   = ["<br>".join(l.get("capabilities", [])) for l in layers]
    sols_text   = ["<br>".join(l.get("solutions", [])) for l in layers]

    # All green — this is the future state
    layer_colors = [GREEN, TEAL, ACCENT, PURPLE, AMBER, "#ec4899"]

    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=layer_names,
        y=[3] * len(layers),
        marker_color=layer_colors[:len(layers)],
        marker_line_color=BORDER,
        marker_line_width=1,
        marker_opacity=0.85,
        text=[f"<b>{l['name']}</b><br><span style='font-size:9px'>{sols_text[i]}</span>" for i, l in enumerate(layers)],
        textposition="inside",
        hovertemplate="<b>%{x}</b><br>Solutions: %{customdata[0]}<br>Capabilities: %{customdata[1]}<extra></extra>",
        customdata=list(zip(sols_text, caps_text)),
        name="Solution Coverage",
        width=0.6,
    ))

    # Integration layer band
    fig.add_hrect(
        y0=2.85, y1=3.15,
        fillcolor=ACCENT, opacity=0.08,
        line_width=0,
    )

    fig.update_layout(
        **_base_layout(f"FMO — Future Mode of Operations  ·  {arch}", height=420),
        xaxis=dict(showgrid=False, tickfont=dict(color=TEXT, size=11)),
        yaxis=dict(showgrid=False, showticklabels=False, range=[0, 3.5]),
        showlegend=False,
        bargap=0.25,
    )

    if integration:
        fig.add_annotation(
            text=f"🔗  Integration Layer: {integration}",
            xref="paper", yref="paper",
            x=0.0, y=-0.10,
            showarrow=False,
            font=dict(color=ACCENT, size=10),
            align="left",
        )

    if outcomes:
        fig.add_annotation(
            text="✓  Outcomes: " + "  ·  ".join(outcomes),
            xref="paper", yref="paper",
            x=0.0, y=-0.17,
            showarrow=False,
            font=dict(color=GREEN, size=10),
            align="left",
        )

    return fig


def render_threat_coverage(data):
    """Threat Coverage Heatmap"""
    threats   = data.get("threats", [])
    solutions = data.get("solutions", [])
    coverage  = data.get("coverage", {})

    # Build matrix
    matrix = []
    for threat in threats:
        row = coverage.get(threat, [0] * len(solutions))
        if len(row) < len(solutions):
            row = row + [0] * (len(solutions) - len(row))
        matrix.append(row[:len(solutions)])

    # Custom colorscale: 0=red, 1=orange, 2=yellow-green, 3=green
    colorscale = [
        [0.0,  "#2d1b1b"],
        [0.33, "#7f1d1d"],
        [0.34, "#78350f"],
        [0.67, "#064e3b"],
        [1.0,  "#059669"],
    ]

    labels = [["No Coverage", "Partial", "Good", "Strong"][v] for row in matrix for v in row]
    labels_2d = [labels[i*len(solutions):(i+1)*len(solutions)] for i in range(len(threats))]

    fig = go.Figure(data=go.Heatmap(
        z=matrix,
        x=solutions,
        y=threats,
        colorscale=colorscale,
        zmin=0, zmax=3,
        text=labels_2d,
        texttemplate="%{text}",
        textfont=dict(size=10, color=TEXT),
        hoverongaps=False,
        showscale=True,
        colorbar=dict(
            title=dict(text="Coverage", font=dict(color=TEXT2, size=11)),
            tickvals=[0, 1, 2, 3],
            ticktext=["None", "Partial", "Good", "Strong"],
            tickfont=dict(color=TEXT2, size=10),
            bgcolor=SURFACE,
            bordercolor=BORDER,
        ),
    ))

    fig.update_layout(
        **_base_layout("Threat Coverage Matrix  ·  Solution vs Threat Mapping", height=480),
        xaxis=dict(side="top", tickfont=dict(color=TEXT, size=11), tickangle=-20, showgrid=False),
        yaxis=dict(tickfont=dict(color=TEXT, size=11), showgrid=False, autorange="reversed"),
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
        **_base_layout("Requirements Traceability Matrix  ·  RFP Requirements → Proposed Solutions",
                       height=max(400, len(reqs) * 30 + 80)),
    )
    fig.update_layout(margin=dict(l=10, r=10, t=50, b=10))

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
        xaxis=dict(title=dict(text="Solution Completeness →", font=dict(color=TEXT2, size=11)),
                   range=[0, 10.5], showgrid=True,
                   gridcolor=BORDER, tickfont=dict(color=TEXT2)),
        yaxis=dict(title=dict(text="Ease of Implementation →", font=dict(color=TEXT2, size=11)),
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
