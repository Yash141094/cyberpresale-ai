import streamlit as st
import os
import html as _html
from utils.document_processor import extract_text_from_file, extract_multiple_files
from utils.ai_engine import (
    generate_customer_brief,
    generate_pain_analysis,
    generate_solution_recommendation,
    generate_competitive_landscape,
    generate_product_mapping,
    generate_executive_summary,
    classify_domains,
    chat_with_rfp,
)
try:
    from utils.ai_engine import suggest_competitors, generate_competitive_with_competitors
    COMPETITOR_FEATURES = True
except ImportError:
    COMPETITOR_FEATURES = False
    def suggest_competitors(rfp_text): return ["TCS", "Infosys", "HCL Technologies"]
    def generate_competitive_with_competitors(rfp_text, names): return generate_competitive_landscape(rfp_text)
try:
    from utils.visuals_engine import (
        extract_cmo_data, extract_fmo_data, extract_threat_coverage,
        extract_requirements_traceability, extract_vendor_positioning
    )
    from utils.visual_renderer import (
        render_cmo, render_fmo, render_threat_coverage,
        render_requirements_traceability, render_vendor_positioning
    )
    import plotly.graph_objects as go
    VISUALS_AVAILABLE = True
except Exception:
    VISUALS_AVAILABLE = False

st.set_page_config(
    page_title="Clarivo · RFP Intelligence",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=DM+Sans:opsz,wght@9..40,300;9..40,400;9..40,500;9..40,600&family=DM+Mono:wght@400;500&display=swap');

:root {
    --bg:           #f9f8f5;
    --surface:      #ffffff;
    --surface2:     #f3f2ee;
    --surface3:     #eceae3;
    --border:       #e5e2d9;
    --border2:      #d4d0c4;
    --accent:       #c2550a;
    --accent-light: #fff4ed;
    --accent-mid:   #ea7c2b;
    --accent-glow:  rgba(194,85,10,0.10);
    --text:         #18170f;
    --text2:        #44403a;
    --text3:        #888274;
    --text4:        #c5bfb0;
    --green:        #166534;
    --green-bg:     #f0fdf4;
    --green-border: #bbf7d0;
    --red:          #991b1b;
    --red-bg:       #fff1f2;
    --red-border:   #fecdd3;
    --blue:         #1e40af;
    --blue-bg:      #eff6ff;
    --blue-border:  #bfdbfe;
}

/* ── Base ── */
html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
    background: var(--bg);
    color: var(--text);
    font-size: 14px;
}
.stApp { background: var(--bg); }

/* ── Sidebar — dark, structured like a chat sidebar ── */
section[data-testid="stSidebar"] {
    background: #161410 !important;
    border-right: 1px solid #2a2620 !important;
    width: 240px !important;
}
section[data-testid="stSidebar"] .stButton > button {
    background: rgba(255,255,255,0.05) !important;
    color: #d4cfc5 !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
    font-size: 0.78rem !important;
    padding: 0.35rem 0.9rem !important;
}
section[data-testid="stSidebar"] .stButton > button:hover {
    background: rgba(194,85,10,0.15) !important;
    border-color: rgba(194,85,10,0.4) !important;
    color: #ea7c2b !important;
}
section[data-testid="stSidebar"] .stTextInput input {
    background: rgba(255,255,255,0.07) !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
    color: #e8e3d8 !important;
    font-size: 0.8rem !important;
    border-radius: 6px !important;
}
section[data-testid="stSidebar"] .stSuccess {
    background: rgba(22,101,52,0.2) !important;
    border: none !important;
}

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
    background: var(--surface2) !important;
    border-radius: 8px !important;
    padding: 3px !important;
    border: 1px solid var(--border) !important;
    gap: 1px !important;
}
.stTabs [data-baseweb="tab"] {
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.76rem !important;
    font-weight: 500 !important;
    color: var(--text3) !important;
    border-radius: 6px !important;
    padding: 0.35rem 0.8rem !important;
}
.stTabs [aria-selected="true"] {
    background: var(--surface) !important;
    color: var(--text) !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.07) !important;
}

/* ── Buttons ── */
.stButton > button {
    background: var(--surface) !important;
    color: var(--text) !important;
    border: 1px solid var(--border2) !important;
    border-radius: 7px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.8rem !important;
    font-weight: 500 !important;
    padding: 0.42rem 1.1rem !important;
    transition: all 0.12s ease !important;
    box-shadow: 0 1px 2px rgba(0,0,0,0.04) !important;
}
.stButton > button:hover {
    background: var(--accent-light) !important;
    border-color: var(--accent-mid) !important;
    color: var(--accent) !important;
}

/* ── Inputs ── */
.stTextInput input, .stTextArea textarea {
    background: var(--surface) !important;
    border: 1px solid var(--border2) !important;
    color: var(--text) !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.84rem !important;
    border-radius: 7px !important;
}
.stTextInput input:focus, .stTextArea textarea:focus {
    border-color: var(--accent-mid) !important;
    box-shadow: 0 0 0 3px var(--accent-glow) !important;
}

/* ── File uploader ── */
[data-testid="stFileUploader"] {
    background: var(--surface) !important;
    border: 1.5px dashed var(--border2) !important;
    border-radius: 10px !important;
}
[data-testid="stFileUploader"]:hover {
    border-color: var(--accent-mid) !important;
    background: var(--accent-light) !important;
}

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 3px; height: 3px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: var(--border2); border-radius: 4px; }

hr { border-color: var(--border) !important; margin: 0.75rem 0 !important; }

/* ════════════════════════════════════════
   CUSTOM COMPONENTS — document-grade typography
   ════════════════════════════════════════ */

/* Response content — dark, readable, document-like */
.cl-doc {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 1.8rem 2rem;
    margin-bottom: 1rem;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    color: var(--text);                 /* near-black, not grey */
    line-height: 1.75;
}
.cl-doc h2 {
    font-family: 'DM Sans', sans-serif;
    font-size: 0.82rem;
    font-weight: 700;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    color: var(--accent);
    margin: 1.2rem 0 0.35rem;
    padding-bottom: 0.25rem;
    border-bottom: 1px solid var(--border);
}
.cl-doc h3 {
    font-family: 'DM Sans', sans-serif;
    font-size: 0.82rem;
    font-weight: 600;
    color: var(--text);
    margin: 0.8rem 0 0.2rem;
}
.cl-doc p, .cl-doc li {
    font-size: 0.84rem;
    color: var(--text2);
    margin: 0 0 0.4rem;
}
.cl-doc strong { color: var(--text); font-weight: 600; }
.cl-doc table {
    width: 100%;
    border-collapse: collapse;
    margin: 0.8rem 0;
    font-size: 0.82rem;
}
.cl-doc th {
    background: var(--surface2);
    color: var(--text);
    font-weight: 600;
    font-size: 0.75rem;
    letter-spacing: 0.04em;
    text-transform: uppercase;
    padding: 0.5rem 0.75rem;
    border: 1px solid var(--border);
    text-align: left;
}
.cl-doc td {
    padding: 0.45rem 0.75rem;
    border: 1px solid var(--border);
    color: var(--text2);
    vertical-align: top;
}
.cl-doc tr:nth-child(even) td { background: var(--surface2); }

/* Wordmark */
.cl-wordmark {
    font-family: 'Instrument Serif', serif;
    font-size: 1.15rem;
    color: #f0ebe0;
    letter-spacing: -0.01em;
}
.cl-wordmark span { color: #ea7c2b; }

/* Page hero */
.cl-hero-title {
    font-family: 'Instrument Serif', serif;
    font-size: 2.1rem;
    font-weight: 400;
    color: var(--text);
    line-height: 1.2;
    letter-spacing: -0.02em;
}
.cl-hero-title em { font-style: italic; color: var(--accent); }
.cl-hero-sub {
    font-size: 0.88rem;
    color: var(--text3);
    font-weight: 400;
    line-height: 1.6;
    margin-top: 0.5rem;
}

/* Section title */
.cl-section-title {
    font-family: 'DM Sans', sans-serif;
    font-size: 0.95rem;
    font-weight: 600;
    color: var(--text);
    margin-bottom: 0.1rem;
}

/* Label */
.cl-label {
    font-size: 0.66rem;
    font-weight: 600;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: var(--text3);
    margin-bottom: 0.5rem;
}

/* Metric card */
.cl-metric {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 0.8rem 1rem;
    box-shadow: 0 1px 2px rgba(0,0,0,0.03);
}
.cl-metric-val {
    font-family: 'Instrument Serif', serif;
    font-size: 1.45rem;
    color: var(--accent);
    line-height: 1;
    margin-top: 0.2rem;
}

/* Info row */
.cl-info {
    background: var(--surface2);
    border-radius: 7px;
    padding: 0.75rem 1rem;
    margin-bottom: 0.5rem;
    font-size: 0.82rem;
    color: var(--text2);
    line-height: 1.6;
}
.cl-info-label {
    font-size: 0.64rem;
    font-weight: 600;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: var(--text3);
    margin-bottom: 0.2rem;
}

/* Domain pie description row */
.cl-domain-row {
    display: flex;
    align-items: center;
    padding: 0.4rem 0;
    border-bottom: 1px solid var(--border);
    font-size: 0.82rem;
    color: var(--text2);
}
.cl-domain-dot {
    width: 10px; height: 10px;
    border-radius: 50%;
    margin-right: 0.6rem;
    flex-shrink: 0;
}

/* Pills */
.cl-pill {
    display: inline-flex;
    align-items: center;
    padding: 0.22rem 0.65rem;
    border-radius: 100px;
    font-size: 0.73rem;
    font-weight: 500;
    margin: 0.12rem;
    border: 1px solid;
}
.pill-amber { background: var(--accent-light); border-color: #fbbf9a; color: var(--accent); }
.pill-stone { background: var(--surface2); border-color: var(--border2); color: var(--text2); }
.pill-green { background: var(--green-bg); border-color: var(--green-border); color: var(--green); }
.pill-red   { background: var(--red-bg); border-color: var(--red-border); color: var(--red); }
.pill-blue  { background: var(--blue-bg); border-color: var(--blue-border); color: var(--blue); }

/* Type tag inline */
.cl-type-tag {
    display: inline-block;
    background: var(--accent-light);
    border: 1px solid #fbbf9a;
    color: var(--accent);
    padding: 0.15rem 0.6rem;
    border-radius: 100px;
    font-size: 0.66rem;
    font-weight: 600;
    font-family: 'DM Mono', monospace;
    letter-spacing: 0.04em;
    margin-left: 0.5rem;
    vertical-align: middle;
}

/* Nudge */
.cl-nudge {
    background: var(--accent-light);
    border: 1px solid #fbbf9a;
    border-radius: 7px;
    padding: 0.65rem 1rem;
    font-size: 0.8rem;
    color: var(--accent);
    margin-bottom: 0.8rem;
}

/* Out-of-scope */
.cl-oos {
    background: var(--red-bg);
    border: 1px solid var(--red-border);
    border-left: 3px solid var(--red);
    border-radius: 7px;
    padding: 0.8rem 1.2rem;
    margin: 0.6rem 0;
}
.cl-oos-title { font-size: 0.72rem; font-weight: 700; color: var(--red); text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 0.25rem; }
.cl-oos-body  { font-size: 0.8rem; color: var(--text2); line-height: 1.6; }

/* Chat */
.chat-user {
    background: var(--surface2);
    border: 1px solid var(--border);
    border-left: 2px solid var(--accent-mid);
    border-radius: 0 7px 7px 0;
    padding: 0.65rem 1rem;
    margin-bottom: 0.4rem;
    font-size: 0.83rem;
    color: var(--text);
}
.chat-ai {
    background: var(--surface);
    border: 1px solid var(--border);
    border-left: 2px solid var(--green);
    border-radius: 0 7px 7px 0;
    padding: 0.65rem 1rem;
    margin-bottom: 0.75rem;
    font-size: 0.83rem;
    color: var(--text2);
    line-height: 1.75;
    white-space: pre-wrap;
}
.chat-who {
    font-size: 0.61rem;
    font-weight: 600;
    letter-spacing: 0.09em;
    text-transform: uppercase;
    margin-bottom: 0.25rem;
    font-family: 'DM Mono', monospace;
}
.chat-who.u { color: var(--accent); }
.chat-who.a { color: var(--green); }

/* Competitor chip */
.comp-chip {
    display: inline-flex; align-items: center;
    background: var(--surface2);
    border: 1px solid var(--border2);
    border-radius: 100px;
    padding: 0.2rem 0.65rem;
    font-size: 0.75rem;
    color: var(--text2);
    margin: 0.15rem;
    cursor: pointer;
}
.comp-chip:hover { background: var(--accent-light); border-color: var(--accent-mid); color: var(--accent); }

/* Fade-in */
@keyframes fadeUp { from { opacity:0; transform:translateY(8px); } to { opacity:1; transform:translateY(0); } }
.cl-doc, .cl-metric, .cl-info { animation: fadeUp 0.2s ease both; }
</style>
""", unsafe_allow_html=True)

# ── Session state ──────────────────────────────────────────────────────────────
for key in ["rfp_text","file_name","customer_brief","pain_analysis","solution_rec",
            "competitive","product_map","exec_summary","domains","vis_cmo","vis_fmo",
            "vis_threat","vis_traceability","vis_vendor","doc_summaries","rfp_context",
            "competitor_names","suggested_competitors"]:
    if key not in st.session_state:
        st.session_state[key] = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# ── Helpers ────────────────────────────────────────────────────────────────────
def get_rfp_type():
    if isinstance(st.session_state.domains, dict):
        return st.session_state.domains.get("rfp_type") or None
    return None

def get_domains_list():
    if isinstance(st.session_state.domains, dict):
        return st.session_state.domains.get("detected_domains", [])
    return []

def rfp_type_tag():
    t = get_rfp_type()
    return f"<span class='cl-type-tag'>{t}</span>" if t else ""

def classify_nudge():
    st.markdown("<div class='cl-nudge'>💡 <strong>Run Domain Classification first</strong> — Clarivo will detect scope, classify the RFP type, and adapt every module accordingly.</div>", unsafe_allow_html=True)

def render_doc_content(content, session_key=None):
    """Render LLM markdown as clean document HTML — dark text, structured headings, tables."""
    import re
    if not content:
        return
    # Convert markdown to document HTML
    html = content
    # H2 → section heading (amber uppercase)
    html = re.sub(r'^## (.+)$', r"<h2>\1</h2>", html, flags=re.MULTILINE)
    # H3 → subheading
    html = re.sub(r'^### (.+)$', r"<h3>\1</h3>", html, flags=re.MULTILINE)
    # Bold
    html = re.sub(r'\*\*(.+?)\*\*', r"<strong>\1</strong>", html)
    # Bullet lists
    lines = html.split('\n')
    out, in_list, in_table = [], False, False
    thead_done = False
    for line in lines:
        stripped = line.strip()
        # Table rows
        if stripped.startswith('|') and stripped.endswith('|'):
            if not in_table:
                out.append('<table>')
                in_table = True
                thead_done = False
            cells = [c.strip() for c in stripped[1:-1].split('|')]
            # separator row
            if all(set(c.replace('-','').replace(':','').replace(' ','')) == set() or c.strip('-: ') == '' for c in cells):
                out.append('<thead><tr>' + ''.join(f'<th>{c}</th>' for c in _last_row_cells) + '</tr></thead><tbody>')
                thead_done = True
                continue
            _last_row_cells = cells
            if thead_done:
                out.append('<tr>' + ''.join(f'<td>{c}</td>' for c in cells) + '</tr>')
            else:
                _last_row_cells = cells
            continue
        else:
            if in_table:
                if not thead_done:
                    # no separator — just plain table
                    out.append('<thead><tr>' + ''.join(f'<th>{c}</th>' for c in _last_row_cells) + '</tr></thead><tbody>')
                out.append('</tbody></table>')
                in_table = False
                thead_done = False

        # Bullet
        if stripped.startswith('* ') or stripped.startswith('- '):
            if not in_list: out.append('<ul>'); in_list = True
            out.append(f"<li>{stripped[2:]}</li>")
        else:
            if in_list: out.append('</ul>'); in_list = False
            if stripped.startswith('<h') or not stripped:
                out.append(stripped if stripped else '')
            else:
                out.append(f"<p>{stripped}</p>")

    if in_list: out.append('</ul>')
    if in_table: out.append('</tbody></table>')

    final_html = '\n'.join(out)
    st.markdown(f"<div class='cl-doc'>{final_html}</div>", unsafe_allow_html=True)

    if session_key and st.button("↺ Regenerate", key=f"regen_{session_key}"):
        st.session_state[session_key] = None
        st.rerun()

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    # Wordmark
    st.markdown("""
    <div style='padding:1.1rem 0.9rem 0.6rem'>
        <div class='cl-wordmark'>Clari<span>vo</span></div>
        <div style='font-size:0.65rem;color:#5a5248;font-family:DM Mono,monospace;margin-top:0.2rem'>RFP Intelligence · v3.2</div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("<div style='height:1px;background:#2a2620;margin:0 0.9rem 0.9rem'></div>", unsafe_allow_html=True)

    # API key
    api_key = st.secrets.get("GROQ_API_KEY", "") if hasattr(st, "secrets") else ""
    if not api_key:
        api_key = st.text_input("Groq API Key", type="password", placeholder="gsk_...")
    if api_key:
        os.environ["GROQ_API_KEY"] = api_key
        st.markdown("<div style='font-size:0.75rem;color:#6ee7b7;padding:0.2rem 0.9rem 0.6rem'>✓ Connected</div>", unsafe_allow_html=True)

    st.markdown("<div style='height:1px;background:#2a2620;margin:0 0.9rem 0.75rem'></div>", unsafe_allow_html=True)

    # RFP type if classified
    rfp_t = get_rfp_type()
    if rfp_t:
        st.markdown(f"""
        <div style='padding:0 0.9rem 0.75rem'>
            <div style='font-size:0.6rem;font-weight:600;letter-spacing:0.1em;text-transform:uppercase;color:#5a5248;margin-bottom:0.2rem'>RFP TYPE</div>
            <div style='font-size:0.82rem;color:#ea7c2b;font-weight:600'>{rfp_t}</div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("<div style='height:1px;background:#2a2620;margin:0 0.9rem 0.75rem'></div>", unsafe_allow_html=True)

    # Module list
    module_states = {
        "Customer Brief": bool(st.session_state.customer_brief),
        "Pain Analysis": bool(st.session_state.pain_analysis),
        "Solution Rec": bool(st.session_state.solution_rec),
        "Competitive": bool(st.session_state.competitive),
        "Product Mapping": bool(st.session_state.product_map),
        "Exec Summary": bool(st.session_state.exec_summary),
        "Domain Classification": isinstance(st.session_state.domains, dict),
    }
    module_rows_html = ""
    for m, done in module_states.items():
        dot_col = "#ea7c2b" if done else "#3a3630"
        txt_col = "#c8c0b4" if done else "#5a5248"
        module_rows_html += f"<div style='display:flex;align-items:center;gap:0.5rem;padding:0.2rem 0'><div style='width:6px;height:6px;border-radius:50%;background:{dot_col};flex-shrink:0'></div><div style='font-size:0.75rem;color:{txt_col}'>{_html.escape(m)}</div></div>"
    st.markdown(f"<div style='padding:0 0.9rem'><div style='font-size:0.6rem;font-weight:600;letter-spacing:0.1em;text-transform:uppercase;color:#5a5248;margin-bottom:0.5rem'>MODULES</div>{module_rows_html}</div>", unsafe_allow_html=True)

    # Document info + reset
    if st.session_state.rfp_text:
        st.markdown("<div style='height:1px;background:#2a2620;margin:0.75rem 0.9rem'></div>", unsafe_allow_html=True)
        doms = get_domains_list()
        st.markdown(f"""
        <div style='padding:0 0.9rem'>
            <div style='font-size:0.6rem;font-weight:600;letter-spacing:0.1em;text-transform:uppercase;color:#5a5248;margin-bottom:0.3rem'>DOCUMENT</div>
            <div style='font-size:0.75rem;color:#ea7c2b;word-break:break-all'>{st.session_state.file_name}</div>
            <div style='font-size:0.68rem;color:#5a5248;margin-top:0.15rem'>{len(st.session_state.rfp_text.split()):,} words</div>
        </div>
        """, unsafe_allow_html=True)
        with st.container():
            if st.button("↺ New Document", use_container_width=True):
                for key in ["rfp_text","file_name","customer_brief","pain_analysis","solution_rec",
                            "competitive","product_map","exec_summary","domains","vis_cmo","vis_fmo",
                            "vis_threat","vis_traceability","vis_vendor","doc_summaries","rfp_context",
                            "competitor_names","suggested_competitors"]:
                    st.session_state[key] = None
                st.session_state.chat_history = []
                st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# UPLOAD SCREEN
# ══════════════════════════════════════════════════════════════════════════════
if not st.session_state.rfp_text:

    st.markdown("<div style='height:2.5rem'></div>", unsafe_allow_html=True)

    # Greeting hero
    st.markdown("""
    <div style='max-width:640px;margin-bottom:2rem'>
        <div class='cl-hero-title'>Hello. I'm here to help you build<br><em>clear, sound intelligence</em> from any RFP.</div>
        <div class='cl-hero-sub' style='margin-top:0.75rem'>
            Upload your RFP and Clarivo reads it end-to-end — classifying scope, mapping vendors, surfacing pains,
            and generating proposal-ready content across any IT service domain.
        </div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([3, 2], gap="large")

    with col1:
        # Optional context hint
        st.markdown("<div class='cl-label'>Upload RFP · PDF or Word</div>", unsafe_allow_html=True)
        uploaded_files = st.file_uploader(
            "Upload RFP", type=["pdf","docx"],
            accept_multiple_files=True,
            label_visibility="collapsed"
        )

        # Optional context box
        with st.expander("Add context or focus area (optional)", expanded=False):
            st.session_state.rfp_context = st.text_area(
                "Focus area",
                placeholder="e.g. This is a hybrid IT outsourcing deal — focus on infrastructure and AMS towers. We are bidding against TCS and HCL.",
                height=80,
                label_visibility="collapsed"
            )

        if uploaded_files:
            if not api_key:
                st.warning("Enter your Groq API Key in the sidebar to continue.")
            else:
                with st.spinner(f"Reading {len(uploaded_files)} document(s)..."):
                    if len(uploaded_files) == 1:
                        text = extract_text_from_file(uploaded_files[0])
                        summaries = [{"name": uploaded_files[0].name, "words": len(text.split()) if text else 0, "status": "success" if text else "failed"}]
                        file_name = uploaded_files[0].name
                    else:
                        text, summaries = extract_multiple_files(uploaded_files)
                        file_name = f"{len(uploaded_files)} documents merged"
                    if text:
                        st.session_state.rfp_text      = text
                        st.session_state.file_name     = file_name
                        st.session_state.doc_summaries = summaries
                        st.rerun()
                    else:
                        st.error("Could not extract text. Check your files.")

    with col2:
        st.markdown("<div class='cl-label'>What Clarivo gives you</div>", unsafe_allow_html=True)
        for cap, desc in [
            ("Customer Intelligence", "Who they are, why now, decision makers"),
            ("Pain Analysis", "Real needs beneath the stated requirements"),
            ("Solution Recommendation", "What to propose, how to phase, volume tables"),
            ("Competitive Intelligence", "Who's bidding and exactly how to beat them"),
            ("Domain Scope Map", "Pie chart of scope across all IT towers"),
            ("PPT + Word Export", "Charts, architecture, tables — ready to send"),
        ]:
            st.markdown(f"<div class='cl-info'><div class='cl-info-label'>{cap}</div>{desc}</div>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# MAIN ANALYSIS SCREEN
# ══════════════════════════════════════════════════════════════════════════════
else:
    rfp_t     = get_rfp_type()
    fn_raw    = st.session_state.file_name[:55] + ("…" if len(st.session_state.file_name) > 55 else "")
    fn_short  = _html.escape(fn_raw)
    type_disp = f" · <em style='color:var(--accent);font-style:italic'>{_html.escape(rfp_t)}</em>" if rfp_t else ""

    st.markdown(f"""
    <div style='padding:1.8rem 0 1rem'>
        <div style='font-family:Instrument Serif,serif;font-size:1.5rem;font-weight:400;color:var(--text);letter-spacing:-0.01em'>
            {fn_short}{type_disp}
        </div>
        <div style='font-size:0.72rem;color:var(--text3);margin-top:0.2rem;font-family:DM Mono,monospace'>
            {len(st.session_state.rfp_text.split()):,} words extracted
            {'&nbsp;·&nbsp;' + str(len(get_domains_list())) + ' domains' if get_domains_list() else ''}
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Compact metrics
    m_cols = st.columns(5, gap="small")
    n_mod = sum(1 for k in ["customer_brief","pain_analysis","solution_rec","competitive","product_map","exec_summary"] if st.session_state.get(k))
    for col, (lbl, val, hl) in zip(m_cols, [
        ("Words",        f"{len(st.session_state.rfp_text.split()):,}", False),
        ("RFP Type",     rfp_t or "—",                                   bool(rfp_t)),
        ("Domains",      str(len(get_domains_list())) if get_domains_list() else "—", False),
        ("Modules",      f"{n_mod}/6",                                   False),
        ("Chat Q&A",     str(len(st.session_state.chat_history)//2),     False),
    ]):
        with col:
            val_col = "var(--accent)" if hl else "var(--text)"
            st.markdown(f"""
            <div class='cl-metric'>
                <div class='cl-label' style='margin-bottom:0.15rem'>{lbl}</div>
                <div class='cl-metric-val' style='color:{val_col}'>{val}</div>
            </div>""", unsafe_allow_html=True)

    st.markdown("<div style='height:0.75rem'></div>", unsafe_allow_html=True)

    # Export row — minimal
    ex1, ex2, ex3, ex4 = st.columns([3,1,1,2], gap="small")
    with ex1:
        st.markdown("<div style='font-size:0.8rem;color:var(--text3);padding:0.4rem 0'>Export your analysis as a proposal document:</div>", unsafe_allow_html=True)
    with ex2:
        if st.button("📄 Word", key="btn_word", use_container_width=True):
            if not any([st.session_state.customer_brief, st.session_state.exec_summary]):
                st.warning("Run at least one module first.")
            else:
                with st.spinner("Generating…"):
                    try:
                        from utils.export_word import generate_word_doc
                        path = generate_word_doc(st.session_state)
                        with open(path,"rb") as f:
                            st.download_button("⬇ Download",f,file_name="Clarivo_Proposal.docx",
                                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",key="dl_word")
                    except Exception as e: st.error(f"Error: {e}")
    with ex3:
        if st.button("📊 PPT", key="btn_ppt", use_container_width=True):
            if not any([st.session_state.customer_brief, st.session_state.exec_summary]):
                st.warning("Run at least one module first.")
            else:
                with st.spinner("Generating…"):
                    try:
                        from utils.export_ppt import generate_ppt
                        path = generate_ppt(st.session_state)
                        with open(path,"rb") as f:
                            st.download_button("⬇ Download",f,file_name="Clarivo_Presentation.pptx",
                                mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",key="dl_ppt")
                    except Exception as e: st.error(f"Error: {e}")
    with ex4:
        st.markdown("<div style='font-size:0.72rem;color:var(--text4);padding:0.4rem 0'>PPT includes charts, architecture, and domain scope visuals</div>", unsafe_allow_html=True)

    st.markdown("<div style='height:0.3rem'></div>", unsafe_allow_html=True)

    # ── Tabs ──────────────────────────────────────────────────────────────────
    tabs = st.tabs(["Customer Brief","Pain Analysis","Solution Rec",
                    "Competitive","Product Mapping","Exec Summary",
                    "Domains","Visuals","Chat"])
    tab1,tab2,tab3,tab4,tab5,tab6,tab7,tab8,tab9 = tabs

    def tab_header(title, show_type=True):
        tag = rfp_type_tag() if show_type else ""
        st.markdown(f"<div style='height:0.25rem'></div><div class='cl-section-title'>{title}{tag}</div><div style='height:0.5rem'></div>", unsafe_allow_html=True)

    def about_row(text):
        st.markdown(f"<div class='cl-info'><div class='cl-info-label'>About this module</div>{text}</div>", unsafe_allow_html=True)

    def simple_tab(tab, sk, btn_label, btn_key, fn, title, about_text):
        with tab:
            tab_header(title)
            if not get_rfp_type():
                classify_nudge()
            if not st.session_state[sk]:
                about_row(about_text)
                if st.button(btn_label, key=btn_key):
                    status = st.status(f"Running {title}…", expanded=True)
                    with status:
                        try:
                            st.write(f"📄 Reading RFP ({len(st.session_state.rfp_text.split()):,} words)…")
                            st.write("🤖 Generating analysis — this takes 15–40 seconds…")
                            ctx = st.session_state.rfp_context or ""
                            st.session_state[sk] = fn(st.session_state.rfp_text + ("\n\nCONTEXT:\n" + ctx if ctx else ""))
                            status.update(label=f"{title} complete ✓", state="complete", expanded=False)
                            st.rerun()
                        except Exception as e:
                            err_str = str(e).lower()
                            if any(x in err_str for x in ["rate limit","429","quota","too many"]):
                                status.update(label="Rate limit — please wait 30s and retry", state="error", expanded=True)
                                st.error("⚠️ Groq API rate limit hit. Wait 30–60 seconds then click again.")
                            else:
                                status.update(label="Error", state="error", expanded=True)
                                st.error(f"Error: {str(e)[:200]}")
            else:
                render_doc_content(st.session_state[sk], sk)

    simple_tab(tab1,"customer_brief","Generate Customer Brief","btn_brief",generate_customer_brief,
               "Customer Intelligence Brief",
               "Who the customer is, why this RFP now, decision makers, entry points, red flags.")

    simple_tab(tab2,"pain_analysis","Run Pain Analysis","btn_pain",generate_pain_analysis,
               "Pain Point Analysis",
               "Surface requirements vs real needs — ranked pains, compliance pressures, legacy constraints, what wins or loses the deal.")

    simple_tab(tab3,"solution_rec","Generate Solution Recommendation","btn_solrec",generate_solution_recommendation,
               "Solution Recommendation",
               "Architecture, phasing, team model, SLAs, POC strategy, commercial approach. Includes volume/scope tables.")

    simple_tab(tab6,"exec_summary","Generate Executive Summary","btn_execsum",generate_executive_summary,
               "Executive Summary",
               "Board-ready 500-600 word executive summary — business case, solution approach, value, and why us.")

    simple_tab(tab5,"product_map","Map Products & Vendors","btn_prodmap",generate_product_mapping,
               "Product & Vendor Mapping",
               "Domain-by-domain recommendations — primary and alternatives, justified against actual RFP requirements.")

    # ── Tab 4: Competitive — with competitor input ────────────────────────────
    with tab4:
        tab_header("Competitive Intelligence")
        if not get_rfp_type():
            classify_nudge()

        # Competitor input panel
        st.markdown("<div class='cl-info'><div class='cl-info-label'>Competitor Input</div>Name the competitors you know are bidding, or let Clarivo suggest the most likely ones based on the RFP.</div>", unsafe_allow_html=True)

        c_input_col, c_btn_col = st.columns([4,1], gap="small")
        with c_input_col:
            comp_input = st.text_input(
                "Competitor names",
                placeholder="e.g. TCS, HCL, Wipro — or leave blank to auto-suggest",
                label_visibility="collapsed",
                key="comp_input_field"
            )
        with c_btn_col:
            if st.button("Suggest", key="btn_suggest_comp", use_container_width=True):
                with st.spinner("Identifying likely bidders…"):
                    st.session_state.suggested_competitors = suggest_competitors(st.session_state.rfp_text)
                    st.rerun()

        # Show suggestions as clickable chips
        if st.session_state.suggested_competitors:
            chips_html = "".join([f"<span class='comp-chip'>{_html.escape(c)}</span>" for c in st.session_state.suggested_competitors])
            st.markdown(f"""<div style='margin:0.4rem 0 0.6rem'>
                <div class='cl-label'>Suggested competitors — click to add:</div>
                <div style='margin-top:0.3rem'>{chips_html}</div>
                <div style='font-size:0.73rem;color:var(--text3);margin-top:0.3rem'>Copy any names above into the input field, then click Analyse.</div>
            </div>""", unsafe_allow_html=True)

        st.markdown("<div style='height:0.3rem'></div>", unsafe_allow_html=True)

        if not st.session_state.competitive:
            btn_label = "Analyse Competitive Landscape"
            if st.button(btn_label, key="btn_comp"):
                status = st.status("Generating competitive intelligence…", expanded=True)
                with status:
                    ctx = st.session_state.rfp_context or ""
                    rfp_plus = st.session_state.rfp_text + ("\n\nCONTEXT:\n" + ctx if ctx else "")
                    named = comp_input.strip() or (", ".join(st.session_state.suggested_competitors) if st.session_state.suggested_competitors else "")
                    if named:
                        st.write(f"🎯 Analysing named competitors: {named}…")
                    else:
                        st.write("🔍 Auto-detecting likely bidders and threat vectors…")
                    st.write("⏳ Building competitive analysis — 20–50 seconds…")
                    if named:
                        st.session_state.competitive = generate_competitive_with_competitors(rfp_plus, named)
                    else:
                        st.session_state.competitive = generate_competitive_landscape(rfp_plus)
                    status.update(label="Competitive analysis complete ✓", state="complete", expanded=False)
                st.rerun()
        else:
            render_doc_content(st.session_state.competitive, "competitive")

    # ── Tab 7: Domains — pie chart ────────────────────────────────────────────
    with tab7:
        tab_header("Domain & Scope Classification")
        st.markdown("<div class='cl-info'><div class='cl-info-label'>What this does</div>Clarivo reads the RFP and builds a percentage scope breakdown across all IT service towers — visualised as a pie chart. For hybrid multi-tower deals, each domain gets a proportional weight based on requirements depth.</div>", unsafe_allow_html=True)

        if not isinstance(st.session_state.domains, dict):
            if st.button("Classify & Map Domain Scope", key="btn_domains"):
                status = st.status("Analysing RFP domain scope…", expanded=True)
                with status:
                    try:
                        ctx = st.session_state.rfp_context or ""
                        rfp_plus = st.session_state.rfp_text + ("\n\nCONTEXT:\n" + ctx if ctx else "")
                        # Reuse cached rfp_type if already known — saves one full API call
                        cached_type = get_rfp_type()
                        if cached_type:
                            st.write(f"✅ RFP type already detected: **{cached_type}** — skipping re-detection…")
                        else:
                            st.write("🔍 Detecting RFP type and context…")
                        st.write("🗂️ Mapping service towers and calculating domain weights…")
                        st.write("⏳ This may take 20–40 seconds…")
                        st.session_state.domains = classify_domains(rfp_plus, rfp_type_hint=cached_type)
                        status.update(label="Domain classification complete ✓", state="complete", expanded=False)
                        st.rerun()
                    except Exception as e:
                        err_str = str(e).lower()
                        if any(x in err_str for x in ["rate limit","429","quota","too many"]):
                            status.update(label="Rate limit hit — please wait 30–60s", state="error", expanded=True)
                            st.error("⚠️ Groq free tier rate limit reached. Wait 30–60 seconds then click again — it clears automatically.")
                        else:
                            status.update(label="Error occurred", state="error", expanded=True)
                            st.error(f"Error: {str(e)[:200]}")
        else:
            d             = st.session_state.domains
            rfp_type_val  = d.get("rfp_type","Unknown")
            service_model = d.get("service_model","—")
            key_metrics   = d.get("key_metrics",[])
            domains_list  = d.get("detected_domains",[])
            domain_details = d.get("domain_details",{})
            reasoning     = d.get("reasoning","")

            # ── PIE CHART ────────────────────────────────────────────────────
            import plotly.graph_objects as go
            DOMAIN_COLORS = [
                "#c2550a","#ea7c2b","#d97706","#92400e","#fbbf24",
                "#166534","#1e40af","#6b21a8","#0e7490","#be185d",
                "#374151","#065f46",
            ]

            # Build domain weights — we weight by keyword density in RFP
            rfp_lower = st.session_state.rfp_text.lower()
            tower_keywords = {
                "Cybersecurity / SOC":           ["siem","soc","edr","threat","grc","pen test","vulnerability","firewall","ztna","zero trust","dlp","soar"],
                "Infrastructure & DC Ops":       ["server","data centre","dc","compute","vmware","hci","storage","san","nas","backup","dr","network","sd-wan"],
                "Application Managed Services":  ["sap","erp","ams","l1","l2","l3","application support","release","devops","change management","jira","servicenow ticket"],
                "End User Computing":            ["helpdesk","desktop","endpoint","euc","m365","intune","vdi","citrix","dex","service desk","patch"],
                "Digital Workplace":             ["sharepoint","teams","intranet","collaboration","purview","governance","power platform","onedrive","m365"],
                "Cloud & Migration":             ["cloud","aws","azure","gcp","migration","lift-and-shift","cloud native","kubernetes","container","finops"],
                "Data & Analytics":              ["data lake","analytics","bi","etl","data warehouse","mlops","machine learning","power bi","tableau","databricks"],
                "Networking":                    ["wan","lan","bgp","routing","switching","mpls","sd-wan","network operations","noc","wireless"],
            }
            weights = {}
            for tower, kws in tower_keywords.items():
                count = sum(rfp_lower.count(kw) for kw in kws)
                if count > 0:
                    weights[tower] = count

            # Also include detected domains with a baseline weight if not already present
            for dom in domains_list:
                if dom not in weights:
                    weights[dom] = 5  # baseline

            if not weights:
                weights = {d_: 10 for d_ in (domains_list or ["General IT Services"])}

            labels = list(weights.keys())
            values = list(weights.values())
            total  = sum(values)
            pcts   = [round(v/total*100, 1) for v in values]
            colors = DOMAIN_COLORS[:len(labels)]

            fig = go.Figure(go.Pie(
                labels=labels,
                values=values,
                hole=0.52,
                marker=dict(colors=colors, line=dict(color='#f9f8f5', width=2)),
                textinfo='percent',
                textfont=dict(size=12, family='DM Sans'),
                hovertemplate='<b>%{label}</b><br>Share: %{percent}<extra></extra>',
                sort=True,
                direction='clockwise',
            ))
            fig.update_layout(
                showlegend=True,
                legend=dict(
                    orientation="v", x=1.02, y=0.5,
                    font=dict(size=11, family='DM Sans', color='#44403a'),
                    bgcolor='rgba(0,0,0,0)',
                    traceorder='normal',
                ),
                margin=dict(t=10, b=10, l=10, r=10),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                annotations=[dict(
                    text=f"<b>{rfp_type_val}</b>",
                    x=0.5, y=0.5, showarrow=False,
                    font=dict(size=13, family='Instrument Serif', color='#18170f'),
                    xanchor='center', yanchor='middle',
                )],
                height=360,
            )

            pie_col, info_col = st.columns([3,2], gap="large")
            with pie_col:
                st.markdown("<div class='cl-label'>Scope Distribution</div>", unsafe_allow_html=True)
                st.plotly_chart(fig, use_container_width=True)
            with info_col:
                st.markdown("<div class='cl-label'>Domain Breakdown</div>", unsafe_allow_html=True)
                for i, (lbl, pct) in enumerate(zip(labels, pcts)):
                    color = colors[i] if i < len(colors) else "#888"
                    detail = domain_details.get(lbl, "") or ""
                    detail_safe = _html.escape(str(detail))[:120]
                    detail_html = f'<div style="font-size:0.75rem;color:var(--text3);line-height:1.5;margin-top:0.1rem">{detail_safe}</div>' if detail_safe else ""
                    lbl_safe = _html.escape(str(lbl))
                    st.markdown(f"""
                    <div style='display:flex;align-items:flex-start;gap:0.6rem;padding:0.45rem 0;border-bottom:1px solid var(--border)'>
                        <div style='width:10px;height:10px;border-radius:50%;background:{color};margin-top:0.3rem;flex-shrink:0'></div>
                        <div>
                            <div style='font-size:0.8rem;font-weight:600;color:var(--text)'>{lbl_safe} <span style="color:var(--accent);font-size:0.75rem">{pct}%</span></div>
                            {detail_html}
                        </div>
                    </div>""", unsafe_allow_html=True)

            # Key metrics + service model
            st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
            mc1, mc2 = st.columns(2, gap="small")
            with mc1:
                st.markdown(f"<div class='cl-info'><div class='cl-info-label'>Service Model</div><strong>{service_model}</strong></div>", unsafe_allow_html=True)
            with mc2:
                if key_metrics:
                    metrics_str = "  ·  ".join(key_metrics)
                    st.markdown(f"<div class='cl-info'><div class='cl-info-label'>Key SLA / KPI Metrics</div>{metrics_str}</div>", unsafe_allow_html=True)

            # Out-of-scope towers
            all_towers = [
                ("Cybersecurity / SOC",          ["cybersecurity","siem","soc","edr","threat","zero trust","grc"]),
                ("Infrastructure & DC Ops",      ["infrastructure","data centre","dc ops","compute","storage","cloud migration","vmware"]),
                ("Application Managed Services", ["application","ams","sap","erp","l1","l2","l3","release","devops"]),
                ("End User Computing",           ["end user","helpdesk","desktop","euc","m365","device management","vdi"]),
                ("Digital Workplace",            ["digital workplace","teams","sharepoint","intranet","collaboration","purview"]),
                ("Data & Analytics",             ["data platform","analytics","bi","etl","data warehouse","mlops"]),
            ]
            domain_str = " ".join(domains_list).lower() + " " + rfp_type_val.lower()
            oos = [name for name, kws in all_towers if not any(kw in domain_str for kw in kws)]
            if oos:
                oos_pills = "".join([f"<span class='cl-pill pill-red'>{t}</span>" for t in oos])
                st.markdown(f"""
                <div class='cl-oos'>
                    <div class='cl-oos-title'>⊘ Out of Scope</div>
                    <div class='cl-oos-body'>Not identified in this RFP — exclude from proposal scope or mark explicitly as Not in Scope.</div>
                    <div style='margin-top:0.4rem'>{oos_pills}</div>
                </div>""", unsafe_allow_html=True)

            if reasoning:
                st.markdown(f"<div class='cl-info' style='margin-top:0.5rem'><div class='cl-info-label'>Classification Notes</div>{reasoning}</div>", unsafe_allow_html=True)

            if st.button("↺ Reclassify", key="btn_reclassify"):
                st.session_state.domains = None
                st.rerun()

    # ── Tab 8: Visuals ────────────────────────────────────────────────────────
    with tab8:
        tab_header("Visual Intelligence")
        cov_label = "Threat Coverage Matrix" if (rfp_t and "cyber" in rfp_t.lower()) else "Service Coverage Matrix"
        if not VISUALS_AVAILABLE:
            st.warning("Visuals require: pip install plotly")
        else:
            if not get_rfp_type(): classify_nudge()
            vc1, vc2 = st.columns(2, gap="medium")
            with vc1:
                if st.button("Generate CMO", key="btn_cmo"):
                    with st.spinner("Analysing current environment…"):
                        st.session_state.vis_cmo = extract_cmo_data(st.session_state.rfp_text); st.rerun()
                if st.button("Generate FMO", key="btn_fmo"):
                    if not st.session_state.solution_rec:
                        st.warning("Run Solution Recommendation first — FMO is built from the proposed solution.")
                    else:
                        with st.spinner("Building future architecture…"):
                            st.session_state.vis_fmo = extract_fmo_data(st.session_state.solution_rec); st.rerun()
                if st.button(cov_label, key="btn_threat"):
                    with st.spinner("Mapping coverage…"):
                        st.session_state.vis_threat = extract_threat_coverage(st.session_state.rfp_text); st.rerun()
            with vc2:
                if st.button("Requirements Traceability", key="btn_trace"):
                    with st.spinner("Building RTM…"):
                        st.session_state.vis_traceability = extract_requirements_traceability(st.session_state.rfp_text); st.rerun()
                if st.button("Vendor Positioning Map", key="btn_vendor"):
                    with st.spinner("Analysing vendor landscape…"):
                        st.session_state.vis_vendor = extract_vendor_positioning(st.session_state.rfp_text); st.rerun()
                if any([st.session_state.vis_cmo, st.session_state.vis_fmo, st.session_state.vis_threat, st.session_state.vis_traceability, st.session_state.vis_vendor]):
                    if st.button("↺ Clear", key="btn_clrvis"):
                        for vk in ["vis_cmo","vis_fmo","vis_threat","vis_traceability","vis_vendor"]: st.session_state[vk] = None
                        st.rerun()
            for vis_key, vis_label, rfn in [
                ("vis_cmo","Current Mode of Operations",render_cmo),
                ("vis_fmo","Future Mode of Operations",render_fmo),
                ("vis_threat",cov_label,render_threat_coverage),
                ("vis_traceability","Requirements Traceability",render_requirements_traceability),
                ("vis_vendor","Vendor Positioning Map",render_vendor_positioning),
            ]:
                if st.session_state[vis_key]:
                    st.markdown(f"<div class='cl-label' style='margin-top:1rem'>{vis_label}</div>", unsafe_allow_html=True)
                    st.plotly_chart(rfn(st.session_state[vis_key]), use_container_width=True)

    # ── Tab 9: Chat ───────────────────────────────────────────────────────────
    with tab9:
        tab_header("Chat with RFP")
        for i in range(0, len(st.session_state.chat_history), 2):
            if i < len(st.session_state.chat_history):
                st.markdown(f"<div class='chat-user'><div class='chat-who u'>You</div>{st.session_state.chat_history[i]}</div>", unsafe_allow_html=True)
            if i+1 < len(st.session_state.chat_history):
                st.markdown(f"<div class='chat-ai'><div class='chat-who a'>Clarivo</div>{st.session_state.chat_history[i+1]}</div>", unsafe_allow_html=True)
        if not st.session_state.chat_history:
            st.markdown("<div class='cl-label'>Suggested questions</div>", unsafe_allow_html=True)
            rfp_t2 = get_rfp_type() or ""
            base_suggs = ["What is the contract value and duration?","What are the mandatory requirements?",
                          "What compliance frameworks are specified?","What is the implementation timeline?"]
            domain_suggs = {
                "Cybersecurity": ["What SOC model is required?","Which security tools are specified?"],
                "Infrastructure Services": ["What are the uptime SLAs?","Is cloud migration in scope?"],
                "Application Managed Services": ["What support tiers are required?","What are the P1 SLAs?"],
                "End User Computing": ["What is the endpoint count?","Is VDI in scope?"],
            }
            suggs = (base_suggs[:3] + domain_suggs.get(rfp_t2, ["What support model is required?","What existing tools must be retained?"]))[:6]
            sc1, sc2 = st.columns(2)
            for idx, sug in enumerate(suggs):
                with (sc1 if idx%2==0 else sc2):
                    if st.button(sug, key=f"sug_{idx}", use_container_width=True):
                        with st.spinner("…"):
                            answer = chat_with_rfp(st.session_state.rfp_text, sug, st.session_state.chat_history)
                            st.session_state.chat_history.extend([sug, answer]); st.rerun()
        st.markdown("<div style='height:0.4rem'></div>", unsafe_allow_html=True)
        user_q = st.text_input("Ask anything about this RFP…", placeholder="e.g. What are the data residency requirements?", key="chat_input")
        qc1, qc2 = st.columns([6,1])
        with qc2:
            if st.button("Send", key="btn_send", use_container_width=True) and user_q:
                with st.spinner("…"):
                    answer = chat_with_rfp(st.session_state.rfp_text, user_q, st.session_state.chat_history)
                    st.session_state.chat_history.extend([user_q, answer]); st.rerun()
        if st.session_state.chat_history:
            if st.button("Clear conversation", key="btn_clearchat"):
                st.session_state.chat_history = []; st.rerun()
