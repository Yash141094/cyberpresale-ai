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
        title=dict(text=title, font=dict(color=TEXT, size=16, family="Arial"), x=0.02, xanchor="left"),
        paper_bgcolor=SURFACE,
        plot_bgcolor=SURFACE2,
        font=dict(color=TEXT2, family="Arial", size=12),
        margin=dict(l=20, r=20, t=50, b=20),
        height=height,
    )


def _safe_join(val, default="Not specified"):
    """Safely join a value that might be a list, string, or None."""
    if val is None:
        return default
    if isinstance(val, list):
        return "<br>".join(str(v) for v in val) if val else default
    return str(val)  # AI returned a string — use it directly


def _safe_list(val, default=None):
    """Ensure a value is always a list."""
    if val is None:
        return default or []
    if isinstance(val, list):
        return val
    return [val]  # wrap string in list


def render_cmo(data):
    """CMO — Requirements table with support hours, timezone, VM frequency"""
    rows    = data.get("rows", [])
    org     = data.get("org_name", "Customer")
    industry= data.get("industry", "Enterprise")

    if not rows:
        return None

    # Colour code licence owner
    def licence_color(val):
        m = {"Customer": "#1e3a5f", "Supplier": "#064e3b", "Shared": "#3b2a6e", "None": "#450a0a"}
        return m.get(str(val), SURFACE2)

    # Colour code support hours
    def hours_color(val):
        v = str(val)
        if "24x7" in v: return "#064e3b"
        if "On-Call" in v or "P1" in v: return "#1e3a5f"
        if "12x" in v: return "#3b2a6e"
        return SURFACE2

    col_req      = [str(r.get("requirement", "")) for r in rows]
    col_sub      = [str(r.get("sub_requirement", "")) for r in rows]
    col_tool     = [str(r.get("current_tool", "Unknown")) for r in rows]
    col_owner    = [str(r.get("licence_owner", "None")) for r in rows]
    col_hours    = [str(r.get("support_hours", "8x5")) for r in rows]
    col_tz       = [str(r.get("timezone", "IST")) for r in rows]
    col_vm       = [str(r.get("vm_frequency", "Monthly")) for r in rows]
    col_brief    = [str(r.get("requirement_brief", ""))[:120] + ("..." if len(str(r.get("requirement_brief",""))) > 120 else "") for r in rows]

    owner_colors = [licence_color(v) for v in col_owner]
    hours_colors = [hours_color(v) for v in col_hours]

    fig = go.Figure(data=[go.Table(
        columnwidth=[130, 160, 120, 90, 80, 110, 90, 260],
        header=dict(
            values=[
                "<b>Requirement</b>",
                "<b>Sub-Requirement</b>",
                "<b>Current Tool</b>",
                "<b>Licence Owner</b>",
                "<b>Support Hours</b>",
                "<b>Timezone</b>",
                "<b>VM Frequency</b>",
                "<b>Requirement Brief</b>",
            ],
            fill_color="#1e1b4b",
            font=dict(color=TEXT, size=10, family="Arial"),
            align="left",
            height=34,
            line_color=BORDER,
        ),
        cells=dict(
            values=[col_req, col_sub, col_tool, col_owner, col_hours, col_tz, col_vm, col_brief],
            fill_color=[
                SURFACE2, SURFACE2, SURFACE2,
                owner_colors,
                hours_colors,
                SURFACE2, SURFACE2, SURFACE2,
            ],
            font=dict(color=TEXT2, size=9, family="Arial"),
            align="left",
            height=36,
            line_color=BORDER,
        ),
    )])

    fig.update_layout(
        **_base_layout(
            f"CMO - Current Mode of Operations  |  {org}  |  {industry}",
            height=max(420, len(rows) * 40 + 100)
        ),
    )

    fig.add_annotation(
        text="Licence: Blue=Customer  Green=Supplier  Purple=Shared  Red=None  |  Hours: Green=24x7  Blue=On-Call  Grey=8x5",
        xref="paper", yref="paper", x=0.0, y=-0.06,
        showarrow=False, font=dict(color=TEXT2, size=9), align="left",
    )

    return fig


def render_fmo(data):
    """FMO — Recommended solutions table with support model and timezone coverage"""
    rows        = data.get("rows", [])
    arch        = data.get("architecture_name", "Integrated Security Platform")
    outcomes    = _safe_list(data.get("key_outcomes", []))
    integration = str(data.get("integration_note", ""))

    if not rows:
        return None

    def support_color(val):
        v = str(val)
        if "24x7" in v: return "#064e3b"
        if "On-Call" in v or "P1" in v: return "#1e3a5f"
        if "Managed" in v: return "#3b2a6e"
        return SURFACE2

    col_req   = [str(r.get("requirement", "")) for r in rows]
    col_sub   = [str(r.get("sub_requirement", "")) for r in rows]
    col_sol   = [str(r.get("recommended_solution", "")) for r in rows]
    col_vend  = [str(r.get("vendor", "")) for r in rows]
    col_supp  = [str(r.get("support_model", "")) for r in rows]
    col_tz    = [str(r.get("timezone_coverage", "")) for r in rows]
    col_vm    = [str(r.get("vm_frequency", "")) for r in rows]
    col_fit   = [str(r.get("fit_rationale", ""))[:120] + ("..." if len(str(r.get("fit_rationale",""))) > 120 else "") for r in rows]

    supp_colors = [support_color(v) for v in col_supp]

    fig = go.Figure(data=[go.Table(
        columnwidth=[130, 160, 140, 100, 120, 130, 80, 260],
        header=dict(
            values=[
                "<b>Requirement</b>",
                "<b>Sub-Requirement</b>",
                "<b>Recommended Solution</b>",
                "<b>Vendor</b>",
                "<b>Support Model</b>",
                "<b>Timezone Coverage</b>",
                "<b>VM Frequency</b>",
                "<b>Why This Fits</b>",
            ],
            fill_color="#064e3b",
            font=dict(color=TEXT, size=10, family="Arial"),
            align="left",
            height=34,
            line_color=BORDER,
        ),
        cells=dict(
            values=[col_req, col_sub, col_sol, col_vend, col_supp, col_tz, col_vm, col_fit],
            fill_color=[
                SURFACE2, SURFACE2, SURFACE2, SURFACE2,
                supp_colors,
                SURFACE2, SURFACE2, SURFACE2,
            ],
            font=dict(color=TEXT2, size=9, family="Arial"),
            align="left",
            height=36,
            line_color=BORDER,
        ),
    )])

    fig.update_layout(
        **_base_layout(
            f"FMO - Future Mode of Operations  |  {arch}",
            height=max(420, len(rows) * 40 + 120)
        ),
    )

    annotations = []
    if integration:
        annotations.append(f"Integration: {integration[:120]}")
    if outcomes:
        annotations.append("Outcomes: " + "  |  ".join(str(o) for o in outcomes[:4]))
    if annotations:
        fig.add_annotation(
            text="  //  ".join(annotations),
            xref="paper", yref="paper", x=0.0, y=-0.06,
            showarrow=False, font=dict(color=GREEN, size=9), align="left",
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

    row_label   = data.get("row_label", "Threat / Attack Vector")
    header_vals = [f"<b>{row_label}</b>"] + [f"<b>{s}</b>" for s in solutions]
    col_widths  = [180] + [120] * len(solutions)

    fig = go.Figure(data=[go.Table(
        columnwidth=col_widths,
        header=dict(
            values=header_vals,
            fill_color="#1e1b4b",
            font=dict(color=TEXT, size=11, family="Arial"),
            align="center",
            height=38,
            line_color=BORDER,
        ),
        cells=dict(
            values=[[f"<b>{t}</b>" for t in threats]] + col_values,
            fill_color=SURFACE2,
            font=dict(
                color=[TEXT] + col_font,
                size=10,
                family="Arial"
            ),
            align=["left"] + ["center"] * len(solutions),
            height=34,
            line_color=BORDER,
        ),
    )])

    fig.update_layout(
        **_base_layout("Threat Coverage Matrix - Based on RFP Requirements & Current Market Threats",
                       height=max(420, len(threats) * 38 + 100)),
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
    """Requirements Traceability Matrix — with RFP Section reference column"""
    reqs = data.get("requirements", [])
    if not reqs:
        return None

    ids       = [str(r.get("id","")) for r in reqs]
    sections  = [str(r.get("rfp_section","—")) for r in reqs]
    domains   = [str(r.get("domain","")) for r in reqs]
    req_texts = [str(r.get("requirement",""))[:70]+"…" if len(str(r.get("requirement","")))>70 else str(r.get("requirement","")) for r in reqs]
    priorities= [str(r.get("priority","")) for r in reqs]
    solutions = [str(r.get("proposed_solution","")) for r in reqs]
    coverage  = [str(r.get("coverage","")) for r in reqs]
    notes     = [str(r.get("notes",""))[:60] for r in reqs]

    cov_colors = []
    cov_font   = []
    for c in coverage:
        if c == "Full":
            cov_colors.append("#064e3b"); cov_font.append("#34d399")
        elif c == "Partial":
            cov_colors.append("#78350f"); cov_font.append("#f59e0b")
        else:
            cov_colors.append("#7f1d1d"); cov_font.append("#ef4444")

    pri_colors = []
    for p in priorities:
        if p == "Mandatory":  pri_colors.append("#1e1b4b")
        elif p == "Preferred": pri_colors.append("#3b2a6e")
        else:                  pri_colors.append(SURFACE2)

    fig = go.Figure(data=[go.Table(
        columnwidth=[55, 130, 100, 230, 90, 150, 75, 160],
        header=dict(
            values=[
                "<b>ID</b>",
                "<b>RFP Section</b>",
                "<b>Domain</b>",
                "<b>Requirement</b>",
                "<b>Priority</b>",
                "<b>Proposed Solution</b>",
                "<b>Coverage</b>",
                "<b>Notes</b>",
            ],
            fill_color=ACCENT,
            font=dict(color=TEXT, size=10, family="Arial"),
            align="left",
            height=34,
            line_color=BORDER,
        ),
        cells=dict(
            values=[ids, sections, domains, req_texts, priorities, solutions, coverage, notes],
            fill_color=[
                SURFACE2,
                "#0f172a",   # dark blue for section column — stands out
                SURFACE2,
                SURFACE2,
                pri_colors,
                SURFACE2,
                cov_colors,
                SURFACE2,
            ],
            font=dict(
                color=[TEXT2, "#93c5fd", TEXT2, TEXT2, TEXT2, TEXT2, cov_font, TEXT2],
                size=[9, 9, 9, 9, 9, 9, 9, 8.5],
                family="Arial",
            ),
            align=["center","left","left","left","center","left","center","left"],
            height=30,
            line_color=BORDER,
        ),
    )])

    met   = sum(1 for c in coverage if c == "Full")
    part  = sum(1 for c in coverage if c == "Partial")
    gap   = sum(1 for c in coverage if c == "Gap")

    fig.update_layout(
        **_base_layout(
            f"Requirements Traceability Matrix  |  ✅ {met} Full  ·  ◑ {part} Partial  ·  ✗ {gap} Gap",
            height=max(420, len(reqs) * 32 + 110)
        ),
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
                           font=dict(color=TEXT3, size=9, family="Arial"),
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
                          family="Arial"),
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


def render_compliance_scoring(data):
    """Compliance scoring matrix — Met / Partial / Gap per framework control."""
    reqs    = data.get("requirements", [])
    summary = data.get("summary", {})
    score   = data.get("overall_compliance_score", 0)
    gaps    = data.get("critical_gaps", [])
    narrative = data.get("compliance_narrative", "")

    if not reqs:
        return None

    status_color = {"Met": "#064e3b", "Partial": "#78350f", "Gap": "#450a0a"}
    status_text  = {"Met": "#34d399",  "Partial": "#f59e0b",  "Gap": "#ef4444"}
    status_icon  = {"Met": "✅ Met",   "Partial": "◑ Partial","Gap": "✗ Gap"}

    col_fw   = [str(r.get("framework","")) for r in reqs]
    col_ref  = [str(r.get("control_ref","")) for r in reqs]
    col_req  = [str(r.get("requirement",""))[:60] for r in reqs]
    col_ev   = [str(r.get("evidence_in_rfp",""))[:80] for r in reqs]
    col_risk = [str(r.get("risk_if_gap",""))[:70] for r in reqs]
    statuses = [str(r.get("status","Gap")) for r in reqs]
    col_stat = [status_icon.get(s, s) for s in statuses]
    fill_stat = [status_color.get(s, "#450a0a") for s in statuses]
    font_stat = [status_text.get(s,  "#ef4444") for s in statuses]

    fig = go.Figure(data=[go.Table(
        columnwidth=[120, 70, 160, 200, 170, 90],
        header=dict(
            values=["<b>Framework</b>","<b>Ref</b>","<b>Requirement</b>",
                    "<b>RFP Evidence</b>","<b>Risk if Gap</b>","<b>Status</b>"],
            fill_color="#1e1b4b",
            font=dict(color=TEXT, size=10, family="Arial"),
            align="left", height=36, line_color=BORDER,
        ),
        cells=dict(
            values=[col_fw, col_ref, col_req, col_ev, col_risk, col_stat],
            fill_color=[SURFACE2, SURFACE2, SURFACE2, SURFACE2, SURFACE2, fill_stat],
            font=dict(color=[TEXT2, TEXT2, TEXT2, TEXT2, TEXT2, font_stat], size=9, family="Arial"),
            align=["left","center","left","left","left","center"],
            height=34, line_color=BORDER,
        ),
    )])

    met = summary.get("met", 0)
    partial = summary.get("partial", 0)
    gap = summary.get("gap", 0)
    total = met + partial + gap or 1

    fig.update_layout(**_base_layout(
        f"Compliance Scoring Matrix  |  Score: {score}/100  |  ✅ {met} Met  ·  ◑ {partial} Partial  ·  ✗ {gap} Gap",
        height=max(420, len(reqs) * 36 + 120)
    ))

    annotations = []
    if narrative:
        annotations.append(narrative[:140])
    if gaps:
        annotations.append("Critical gaps: " + "  |  ".join(str(g)[:60] for g in gaps[:3]))
    if annotations:
        fig.add_annotation(
            text="  //  ".join(annotations),
            xref="paper", yref="paper", x=0.0, y=-0.07,
            showarrow=False, font=dict(color="#f59e0b", size=9), align="left",
        )

    return fig


def render_bid_scoring(data):
    """Bid scoring dashboard — radar chart + flags table."""
    dims      = data.get("dimensions", {})
    score     = int(data.get("overall_score", 0))
    decision  = str(data.get("bid_decision", "—"))
    rationale = str(data.get("bid_decision_rationale", ""))
    green     = data.get("green_flags", [])
    red       = data.get("red_flags", [])
    risks     = data.get("commercial_risks", [])
    complexity= str(data.get("technical_complexity", "—"))
    themes    = data.get("win_themes", [])
    landmines = data.get("landmines", [])
    actions   = data.get("recommended_actions", [])

    decision_color = {
        "Bid — Strong Pursuit": "#064e3b",
        "Bid with Conditions":  "#78350f",
        "Bid Selectively":      "#1e3a5f",
        "No Bid":               "#450a0a",
    }.get(decision, "#1e1b4b")

    from plotly.subplots import make_subplots
    fig = make_subplots(
        rows=1, cols=2,
        specs=[[{"type": "polar"}, {"type": "table"}]],
        column_widths=[0.42, 0.58],
        horizontal_spacing=0.04,
    )

    # Radar chart
    dim_names = list(dims.keys())
    dim_vals  = [int(v) for v in dims.values()]
    if dim_names:
        fig.add_trace(go.Scatterpolar(
            r=dim_vals + [dim_vals[0]],
            theta=dim_names + [dim_names[0]],
            fill="toself",
            fillcolor="rgba(99,102,241,0.25)",
            line=dict(color="#6366f1", width=2),
            name="Bid Score",
        ), row=1, col=1)

    # Flags table
    max_rows = max(len(green), len(red), len(risks), 1)
    def pad(lst, n): return [str(x)[:70] for x in lst] + [""] * (n - len(lst))

    tbl_green = pad(green, max_rows)
    tbl_red   = pad(red,   max_rows)
    tbl_risk  = pad(risks, max_rows)

    fill_green = ["#064e3b" if v else SURFACE2 for v in tbl_green]
    fill_red   = ["#450a0a" if v else SURFACE2 for v in tbl_red]
    fill_risk  = ["#1e3a5f" if v else SURFACE2 for v in tbl_risk]
    font_green = ["#34d399" if v else TEXT2 for v in tbl_green]
    font_red   = ["#ef4444" if v else TEXT2 for v in tbl_red]
    font_risk  = ["#93c5fd" if v else TEXT2 for v in tbl_risk]

    fig.add_trace(go.Table(
        columnwidth=[200, 200, 200],
        header=dict(
            values=["<b>✅ Green Flags</b>","<b>🚩 Red Flags</b>","<b>💰 Commercial Risks</b>"],
            fill_color=["#064e3b","#450a0a","#1e3a5f"],
            font=dict(color=TEXT, size=10, family="Arial"),
            align="left", height=34, line_color=BORDER,
        ),
        cells=dict(
            values=[tbl_green, tbl_red, tbl_risk],
            fill_color=[fill_green, fill_red, fill_risk],
            font=dict(color=[font_green, font_red, font_risk], size=9, family="Arial"),
            align="left", height=32, line_color=BORDER,
        ),
    ), row=1, col=2)

    fig.update_polars(
        bgcolor=SURFACE,
        radialaxis=dict(visible=True, range=[0,100], color=BORDER, gridcolor=BORDER,
                        tickfont=dict(color=TEXT2, size=8)),
        angularaxis=dict(color=TEXT2, tickfont=dict(size=9, color=TEXT2)),
    )

    complexity_badge = {"Low":"🟢","Medium":"🟡","High":"🟠","Very High":"🔴"}.get(complexity,"⚪")
    title = (f"Bid Intelligence  |  Score: {score}/100  |  {decision}  |  "
             f"Complexity: {complexity_badge} {complexity}")

    fig.update_layout(
        **_base_layout(title, height=480),
        showlegend=False,
    )
    fig.update_layout(paper_bgcolor=SURFACE, plot_bgcolor=SURFACE)

    annotation_parts = []
    if rationale:
        annotation_parts.append(rationale[:130])
    if themes:
        annotation_parts.append("Win themes: " + "  ·  ".join(str(t)[:40] for t in themes[:3]))
    if actions:
        annotation_parts.append("Actions: " + "  ·  ".join(str(a)[:50] for a in actions[:3]))

    if annotation_parts:
        fig.add_annotation(
            text="  //  ".join(annotation_parts),
            xref="paper", yref="paper", x=0.0, y=-0.07,
            showarrow=False, font=dict(color=GREEN, size=9), align="left",
        )

    return fig
