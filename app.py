import streamlit as st
import os
from utils.document_processor import extract_text_from_file, extract_multiple_files
from utils.ai_engine import (
    generate_customer_brief,
    generate_pain_analysis,
    generate_solution_recommendation,
    generate_competitive_landscape,
    generate_product_mapping,
    generate_executive_summary,
    classify_domains,
    chat_with_rfp
)
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

# ── Sample RFPs ────────────────────────────────────────────────────────────────
SAMPLE_RFPS = {
    "Cybersecurity — HDFC Securities": """
REQUEST FOR PROPOSAL — CYBERSECURITY MANAGED SERVICES
Organisation: HDFC Securities Limited | RFP: RFP-HDFC-CSEC-2025-047
Estimated Value: INR 45-60 Crores | Contract: 3+2 Years

OVERVIEW: HDFC Securities (3.2M active clients, INR 8,000Cr daily transactions) requires an integrated cybersecurity platform across 287 branches, 3 DCs, and hybrid cloud (AWS+Azure).
Environment: 12,500 employees, 8,500 Windows endpoints, 1,200 Linux servers, 650 Mac, 3,400 mobile, 47 critical apps.

REQUIREMENTS:
SIEM: 50,000 EPS, UEBA, SOAR (50 playbooks), ServiceNow integration, 7-year retention.
EDR: Full endpoint coverage, ransomware auto-isolation in 30s, MDR 24x7, air-gapped trading floor.
IAM/PAM: MFA for 12,500 users, PAM for 380 privileged accounts, SSO for 47 apps.
Cloud: CSPM for AWS/Azure, CWPP for 350 VMs, container security (40 Kubernetes clusters).
Network: NGFW for 3 DCs, WAF for 23 apps, SD-WAN for 287 branches.
GRC: RBI Cybersecurity Framework, SEBI CSCRF, PCI-DSS v4.0, ISO 27001:2022.
SOC: 24x7x365 IST-based SOC, Indian data residency mandatory, 45-day POC.
""",
    "Infrastructure Services — TCS": """
REQUEST FOR PROPOSAL — MANAGED INFRASTRUCTURE SERVICES
Organisation: Tata Consultancy Services | RFP: TCS-INFRA-2025-112
Estimated Value: INR 80-100 Crores | Contract: 5 Years

OVERVIEW: TCS consolidating 3 legacy data centres into hybrid cloud. 80% on-prem VMware vSphere 6.5 (EoL Q2 2026).
Scope: 2,400 physical servers, 18,000 VMs, 3 petabytes storage, 500Gbps inter-DC connectivity.

REQUIREMENTS:
Compute: VMware refresh or HCI (Nutanix/HPE), 99.99% availability SLA.
Storage: SAN/NAS refresh, 3-2-1 backup, DR within 4-hour RTO.
Network: LAN/WAN, SD-WAN for 45 offices, firewall management.
Cloud: Azure landing zone, lift-and-shift 400 workloads, FinOps.
Monitoring: Unified NOC (24x7), Dynatrace/Datadog, ITSM with ServiceNow.
Compliance: ISO 20000, ISO 27001, SOC 2 Type II.
""",
    "End User Computing — HDFC Bank": """
REQUEST FOR PROPOSAL — END USER COMPUTING & HELPDESK
Organisation: HDFC Bank Limited | RFP: HDFC-EUC-2025-088
Estimated Value: INR 35-50 Crores | Contract: 3 Years

OVERVIEW: 12,000 endpoints across 500+ branches. Current helpdesk SLA 68%, target 95%.
Scope: 12,000 Windows PCs, 1,200 MACs, 500 printers, 8,000 mobile devices.

REQUIREMENTS:
Service Desk: 24x7 L1 helpdesk, <2hr first response, CSAT >4.2/5, self-service portal.
Desktop Management: Imaging, patch management (72hr SLA), asset lifecycle.
M365 Administration: Exchange, Teams, SharePoint, OneDrive — 14,000 users.
Device Management: Microsoft Intune MDM/MAM, BYOD enforcement.
VDI: Citrix Virtual Apps for 3,500 contact centre agents, 99.9% availability.
ITSM: ServiceNow integration with CMDB.
""",
    "Application Managed Services — Reliance": """
REQUEST FOR PROPOSAL — SAP APPLICATION MANAGED SERVICES
Organisation: Reliance Industries Limited | RFP: RIL-AMS-2025-045
Estimated Value: INR 60-80 Crores | Contract: 3+2 Years

OVERVIEW: SAP S/4HANA 2023 across 12 business units. Seeking AMS partner for support, enhancements, releases.
Landscape: SAP S/4HANA, BTP, Analytics Cloud, IBP, Ariba, SuccessFactors — 18,000 SAP users.

REQUIREMENTS:
L1 Functional Support: 24x7 helpdesk, <4hr P2 response, knowledge base.
L2 Technical Support: Config changes, workflow fixes, 72-hour SLA.
L3 Engineering: Root cause analysis, ABAP development, <5 business days P1.
Release Management: Monthly patches, bi-annual enhancement packs, regression testing.
DevOps: CI/CD on SAP BTP, TOSCA automated testing, transport management.
Compliance: SOX controls, internal audit support.
""",
}

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Clarivo · RFP Intelligence",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Global CSS — Claude-inspired: white bg, charcoal text, warm amber accent ───
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=DM+Sans:wght@300;400;500;600&family=DM+Mono:wght@400;500&display=swap');

:root {
    /* Base */
    --bg:       #fafaf8;
    --surface:  #ffffff;
    --surface2: #f5f4f0;
    --surface3: #eeece6;

    /* Borders */
    --border:   #e8e5de;
    --border2:  #d6d2c8;

    /* Amber-orange accent — warm, Claude-like */
    --accent:       #d97706;
    --accent-light: #fef3c7;
    --accent-mid:   #f59e0b;
    --accent-dark:  #92400e;
    --accent-glow:  rgba(217, 119, 6, 0.12);

    /* Text */
    --text:     #1a1915;
    --text2:    #57534e;
    --text3:    #a8a29e;
    --text4:    #d6d3cd;

    /* Status */
    --green:    #059669;
    --green-bg: #ecfdf5;
    --red:      #dc2626;
    --red-bg:   #fef2f2;
    --blue:     #2563eb;
    --blue-bg:  #eff6ff;
}

/* Reset */
html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
    background: var(--bg);
    color: var(--text);
}
.stApp { background: var(--bg); }

/* Sidebar */
section[data-testid="stSidebar"] {
    background: var(--text) !important;
    border-right: none !important;
}
section[data-testid="stSidebar"] * { color: #e8e5de !important; }
section[data-testid="stSidebar"] .stButton > button {
    background: rgba(255,255,255,0.06) !important;
    color: #e8e5de !important;
    border: 1px solid rgba(255,255,255,0.12) !important;
}
section[data-testid="stSidebar"] .stButton > button:hover {
    background: rgba(217,119,6,0.2) !important;
    border-color: var(--accent-mid) !important;
    color: #fbbf24 !important;
}
section[data-testid="stSidebar"] .stTextInput input {
    background: rgba(255,255,255,0.08) !important;
    border: 1px solid rgba(255,255,255,0.15) !important;
    color: #f5f4f0 !important;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    background: var(--surface2) !important;
    border-radius: 10px !important;
    padding: 4px !important;
    border: 1px solid var(--border) !important;
    gap: 2px !important;
}
.stTabs [data-baseweb="tab"] {
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.78rem !important;
    font-weight: 500 !important;
    color: var(--text3) !important;
    border-radius: 7px !important;
    padding: 0.4rem 0.85rem !important;
    transition: all 0.15s !important;
}
.stTabs [aria-selected="true"] {
    background: var(--surface) !important;
    color: var(--text) !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.08) !important;
}

/* Buttons */
.stButton > button {
    background: var(--surface) !important;
    color: var(--text) !important;
    border: 1px solid var(--border2) !important;
    border-radius: 8px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.82rem !important;
    font-weight: 500 !important;
    padding: 0.5rem 1.2rem !important;
    transition: all 0.15s ease !important;
    box-shadow: 0 1px 2px rgba(0,0,0,0.05) !important;
}
.stButton > button:hover {
    background: var(--accent-light) !important;
    border-color: var(--accent) !important;
    color: var(--accent-dark) !important;
    box-shadow: 0 2px 8px var(--accent-glow) !important;
}

/* Inputs */
.stTextInput input, .stTextArea textarea, .stSelectbox select {
    background: var(--surface) !important;
    border: 1px solid var(--border2) !important;
    color: var(--text) !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.85rem !important;
    border-radius: 8px !important;
}
.stTextInput input:focus, .stTextArea textarea:focus {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 3px var(--accent-glow) !important;
}

/* File uploader */
[data-testid="stFileUploader"] {
    background: var(--surface) !important;
    border: 1.5px dashed var(--border2) !important;
    border-radius: 12px !important;
}

/* Scrollbar */
::-webkit-scrollbar { width: 4px; height: 4px; }
::-webkit-scrollbar-track { background: var(--bg); }
::-webkit-scrollbar-thumb { background: var(--border2); border-radius: 4px; }

/* Success/warning/error override */
.stSuccess { background: var(--green-bg) !important; color: var(--green) !important; }
.stWarning { background: #fffbeb !important; }

hr { border-color: var(--border) !important; margin: 0.8rem 0 !important; }

/* ── Custom components ── */

.cl-wordmark {
    font-family: 'Instrument Serif', serif;
    font-size: 1.5rem;
    color: #fafaf8;
    letter-spacing: -0.01em;
}
.cl-wordmark span {
    color: #fbbf24;
}

.cl-page-title {
    font-family: 'Instrument Serif', serif;
    font-size: 2.6rem;
    font-weight: 400;
    color: var(--text);
    line-height: 1.15;
    letter-spacing: -0.02em;
}
.cl-page-title em {
    font-style: italic;
    color: var(--accent);
}

.cl-sub {
    font-size: 0.95rem;
    color: var(--text2);
    font-weight: 300;
    line-height: 1.6;
    margin-top: 0.5rem;
    max-width: 520px;
}

.cl-badge {
    display: inline-block;
    background: var(--accent-light);
    color: var(--accent-dark);
    border: 1px solid #fde68a;
    border-radius: 100px;
    font-size: 0.68rem;
    font-weight: 600;
    letter-spacing: 0.05em;
    padding: 0.18rem 0.7rem;
    margin-right: 0.3rem;
    margin-top: 0.3rem;
    font-family: 'DM Mono', monospace;
}

.cl-label {
    font-size: 0.68rem;
    font-weight: 600;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: var(--text3);
    margin-bottom: 0.6rem;
}

.cl-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 1.6rem 1.8rem;
    margin-bottom: 1rem;
    box-shadow: 0 1px 4px rgba(0,0,0,0.04);
}

.cl-card-accent {
    background: var(--surface);
    border: 1px solid var(--border);
    border-top: 3px solid var(--accent);
    border-radius: 12px;
    padding: 1.6rem 1.8rem;
    margin-bottom: 1rem;
    box-shadow: 0 1px 4px rgba(0,0,0,0.04);
}

.cl-card p {
    font-size: 0.88rem;
    line-height: 1.85;
    color: var(--text2);
    white-space: pre-wrap;
    margin: 0;
}

.cl-metric {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 1rem 1.2rem;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}
.cl-metric-val {
    font-family: 'Instrument Serif', serif;
    font-size: 1.8rem;
    color: var(--accent);
    line-height: 1;
}
.cl-metric-label {
    font-size: 0.68rem;
    font-weight: 600;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: var(--text3);
    margin-bottom: 0.3rem;
}

.cl-info {
    background: var(--surface2);
    border-radius: 8px;
    padding: 0.9rem 1.2rem;
    margin-bottom: 0.6rem;
    font-size: 0.82rem;
    color: var(--text2);
    line-height: 1.65;
}
.cl-info-label {
    font-size: 0.65rem;
    font-weight: 600;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: var(--text3);
    margin-bottom: 0.25rem;
}

.cl-pill {
    display: inline-flex;
    align-items: center;
    padding: 0.28rem 0.75rem;
    border-radius: 100px;
    font-size: 0.75rem;
    font-weight: 500;
    margin: 0.15rem;
    border: 1px solid;
}
.pill-amber { background: var(--accent-light); border-color: #fde68a; color: var(--accent-dark); }
.pill-stone { background: var(--surface2); border-color: var(--border2); color: var(--text2); }
.pill-green { background: var(--green-bg); border-color: #a7f3d0; color: var(--green); }
.pill-red   { background: var(--red-bg); border-color: #fecaca; color: var(--red); }
.pill-blue  { background: var(--blue-bg); border-color: #bfdbfe; color: var(--blue); }

.cl-oos {
    background: var(--red-bg);
    border: 1px solid #fecaca;
    border-left: 4px solid var(--red);
    border-radius: 8px;
    padding: 1rem 1.4rem;
    margin: 0.8rem 0;
}
.cl-oos-title { font-size: 0.75rem; font-weight: 700; color: var(--red); letter-spacing: 0.06em; text-transform: uppercase; margin-bottom: 0.35rem; }
.cl-oos-body  { font-size: 0.82rem; color: var(--text2); line-height: 1.65; }

.cl-nudge {
    background: var(--accent-light);
    border: 1px solid #fde68a;
    border-radius: 8px;
    padding: 0.8rem 1.2rem;
    font-size: 0.82rem;
    color: var(--accent-dark);
    margin-bottom: 1rem;
}

.cl-type-tag {
    display: inline-block;
    background: var(--accent-light);
    border: 1px solid #fde68a;
    color: var(--accent-dark);
    padding: 0.2rem 0.65rem;
    border-radius: 100px;
    font-size: 0.68rem;
    font-weight: 600;
    font-family: 'DM Mono', monospace;
    letter-spacing: 0.04em;
    margin-left: 0.6rem;
    vertical-align: middle;
}

.cl-section-title {
    font-family: 'Instrument Serif', serif;
    font-size: 1.2rem;
    color: var(--text);
    margin-bottom: 0.2rem;
    font-weight: 400;
}

.chat-user {
    background: var(--surface2);
    border: 1px solid var(--border);
    border-left: 3px solid var(--accent);
    border-radius: 0 8px 8px 0;
    padding: 0.8rem 1.1rem;
    margin-bottom: 0.5rem;
    font-size: 0.84rem;
    color: var(--text);
}
.chat-ai {
    background: var(--surface);
    border: 1px solid var(--border);
    border-left: 3px solid var(--green);
    border-radius: 0 8px 8px 0;
    padding: 0.8rem 1.1rem;
    margin-bottom: 0.9rem;
    font-size: 0.84rem;
    color: var(--text2);
    line-height: 1.75;
    white-space: pre-wrap;
}
.chat-who {
    font-size: 0.62rem;
    font-weight: 600;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    margin-bottom: 0.3rem;
    font-family: 'DM Mono', monospace;
}
.chat-who.u { color: var(--accent); }
.chat-who.a { color: var(--green); }

.divider {
    height: 1px;
    background: var(--border);
    margin: 1.2rem 0;
}

/* Animate in */
@keyframes fadeUp {
    from { opacity: 0; transform: translateY(12px); }
    to   { opacity: 1; transform: translateY(0); }
}
.cl-card, .cl-metric, .cl-info { animation: fadeUp 0.25s ease both; }
</style>
""", unsafe_allow_html=True)

# ── Session state ──────────────────────────────────────────────────────────────
for key in ["rfp_text","file_name","customer_brief","pain_analysis","solution_rec",
            "competitive","product_map","exec_summary","domains","vis_cmo","vis_fmo",
            "vis_threat","vis_traceability","vis_vendor","doc_summaries"]:
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
    st.markdown("""
    <div class='cl-nudge'>
        <strong>Tip:</strong> Run <strong>Domain Classification</strong> first (Domains tab)
        to enable scope detection — modules will automatically mark as In Scope or Out of Scope.
    </div>""", unsafe_allow_html=True)

def out_of_scope_banner(reason):
    st.markdown(f"""
    <div class='cl-oos'>
        <div class='cl-oos-title'>⊘ Out of Scope for This RFP</div>
        <div class='cl-oos-body'>{reason}</div>
    </div>""", unsafe_allow_html=True)

def dynamic_desc():
    t = get_rfp_type() or "IT Services"
    return {
        "customer_brief": f"Who the customer is, why this {t} RFP exists, decision makers, strategic priorities, and entry points.",
        "pain_analysis":  f"Surface requirements vs real business pains for this {t} engagement — ranked, with business impact and evidence.",
        "solution_rec":   f"What to propose for this {t} RFP — architecture, service model, phasing, commercial strategy, and POC.",
        "competitive":    f"Who is likely bidding on this {t} deal, threat by competitor, where we win vs lose, counter-strategies.",
        "product_map":    f"Domain-by-domain vendor and product recommendations for this {t} RFP — justified against actual requirements.",
        "exec_summary":   f"Board-ready 500-600 word executive summary — business case, solution, value, and why us.",
    }

def get_chat_suggestions():
    t = get_rfp_type() or ""
    base = ["What is the contract value and duration?", "What are the mandatory requirements?",
            "What compliance frameworks are specified?", "What is the implementation timeline?"]
    extras = {
        "Cybersecurity":             ["What SOC model is required?", "Which security tools are specified or preferred?"],
        "Infrastructure Services":   ["What are the uptime SLAs and penalty clauses?", "Is cloud migration in scope?"],
        "Application Managed Services": ["What support tiers are required — L1, L2, L3?", "What are the P1 resolution SLAs?"],
        "End User Computing":        ["What is the endpoint count and device split?", "Is VDI in scope?"],
        "Multi-Tower":               ["Which towers are mandatory vs optional?", "Is this a full outsourcing deal?"],
    }
    return (base[:3] + extras.get(t, ["What support model is required?", "What existing tools must be retained?"]))[:6]

# ── Sidebar — dark panel, Claude-like ─────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style='padding: 1.2rem 0.8rem 0.8rem'>
        <div class='cl-wordmark'>Clari<span>vo</span></div>
        <div style='font-family:DM Mono,monospace;font-size:0.65rem;color:#a8a29e;margin-top:0.3rem'>
            RFP Intelligence · v3.1
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<div style='height:1px;background:rgba(255,255,255,0.08);margin:0 0.8rem 1rem'></div>", unsafe_allow_html=True)

    api_key = st.secrets.get("GROQ_API_KEY", "") if hasattr(st, "secrets") else ""
    if not api_key:
        api_key = st.text_input("Groq API Key", type="password", placeholder="gsk_...")
    if api_key:
        os.environ["GROQ_API_KEY"] = api_key
        st.markdown("<div style='font-size:0.75rem;color:#6ee7b7;padding:0.3rem 0.5rem;display:flex;align-items:center;gap:0.4rem'>✓ &nbsp;Connected</div>", unsafe_allow_html=True)

    st.markdown("<div style='height:1px;background:rgba(255,255,255,0.08);margin:0.8rem 0.8rem'></div>", unsafe_allow_html=True)

    rfp_t = get_rfp_type()
    if rfp_t:
        st.markdown(f"""
        <div style='padding:0 0.5rem 0.8rem'>
            <div style='font-size:0.62rem;font-weight:600;letter-spacing:0.1em;text-transform:uppercase;color:#78716c;margin-bottom:0.3rem'>RFP Type</div>
            <div style='font-size:0.82rem;color:#fbbf24;font-weight:600'>{rfp_t}</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<div style='padding:0 0.5rem'>", unsafe_allow_html=True)
    st.markdown("<div style='font-size:0.62rem;font-weight:600;letter-spacing:0.1em;text-transform:uppercase;color:#78716c;margin-bottom:0.6rem'>Modules</div>", unsafe_allow_html=True)
    mods = ["Customer Brief","Pain Analysis","Solution Recommendation","Competitive Intelligence",
            "Product & Vendor Mapping","Executive Summary","Domain Classification","Visual Intelligence","Chat"]
    for m in mods:
        st.markdown(f"<div style='font-size:0.76rem;color:#a8a29e;padding:0.18rem 0'>· {m}</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    if st.session_state.rfp_text:
        st.markdown("<div style='height:1px;background:rgba(255,255,255,0.08);margin:0.8rem'></div>", unsafe_allow_html=True)
        doms = get_domains_list()
        dom_str = f"{len(doms)} domains" if doms else "Not classified"
        st.markdown(f"""
        <div style='padding:0 0.5rem'>
            <div style='font-size:0.62rem;font-weight:600;letter-spacing:0.1em;text-transform:uppercase;color:#78716c;margin-bottom:0.4rem'>Active Document</div>
            <div style='font-size:0.78rem;color:#fbbf24'>📄 {st.session_state.file_name}</div>
            <div style='font-size:0.7rem;color:#78716c;margin-top:0.2rem'>{len(st.session_state.rfp_text.split()):,} words · {dom_str}</div>
        </div>""", unsafe_allow_html=True)
        if st.session_state.doc_summaries:
            for doc in st.session_state.doc_summaries:
                icon  = "✓" if doc["status"] == "success" else "✗"
                color = "#6ee7b7" if doc["status"] == "success" else "#fca5a5"
                st.markdown(f"<div style='font-size:0.7rem;color:{color};padding:0.1rem 0.5rem'>{icon} {doc['name']}</div>", unsafe_allow_html=True)
        st.markdown("<div style='padding:0.8rem 0.5rem 0'>", unsafe_allow_html=True)
        if st.button("↺ Reset Session"):
            for key in ["rfp_text","file_name","customer_brief","pain_analysis","solution_rec",
                        "competitive","product_map","exec_summary","domains","vis_cmo","vis_fmo",
                        "vis_threat","vis_traceability","vis_vendor","doc_summaries"]:
                st.session_state[key] = None
            st.session_state.chat_history = []
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# UPLOAD SCREEN
# ══════════════════════════════════════════════════════════════════════════════
if not st.session_state.rfp_text:

    # Hero
    st.markdown("""
    <div style='padding: 3.5rem 0 2rem'>
        <div class='cl-page-title'>Turn any RFP into<br>a <em>winning proposal.</em></div>
        <div class='cl-sub'>
            Upload an RFP — Clarivo reads it, classifies the service domain, detects what's in scope,
            and generates proposal-ready intelligence in minutes.
        </div>
        <div style='margin-top:1.2rem'>
            <span class='cl-badge'>CYBERSECURITY</span>
            <span class='cl-badge'>INFRASTRUCTURE</span>
            <span class='cl-badge'>AMS</span>
            <span class='cl-badge'>END USER COMPUTING</span>
            <span class='cl-badge'>MULTI-TOWER</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([3, 2], gap="large")

    with col1:
        st.markdown("<div class='cl-label'>Upload RFP · PDF or Word · Single or Multiple Files</div>", unsafe_allow_html=True)
        uploaded_files = st.file_uploader(
            "Upload RFP",
            type=["pdf", "docx"],
            accept_multiple_files=True,
            label_visibility="collapsed"
        )
        if uploaded_files:
            if not api_key:
                st.warning("Enter your Groq API Key in the sidebar to continue.")
            else:
                with st.spinner(f"Reading {len(uploaded_files)} document(s)..."):
                    if len(uploaded_files) == 1:
                        text = extract_text_from_file(uploaded_files[0])
                        summaries = [{"name": uploaded_files[0].name,
                                      "words": len(text.split()) if text else 0,
                                      "status": "success" if text else "failed"}]
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
                        st.error("Could not extract text. Check your files and try again.")

        st.markdown("""
        <div style='text-align:center;color:var(--text3);font-size:0.75rem;margin:1.2rem 0 0.8rem'>
            — or try a sample —
        </div>""", unsafe_allow_html=True)

        sample_choice = st.selectbox("Sample RFP type", list(SAMPLE_RFPS.keys()), label_visibility="collapsed")
        c1, c2, c3 = st.columns([1, 2, 1])
        with c2:
            if st.button("Load Sample →", use_container_width=True):
                if not api_key:
                    st.warning("Enter your Groq API Key in the sidebar first.")
                else:
                    t = SAMPLE_RFPS[sample_choice]
                    st.session_state.rfp_text      = t
                    st.session_state.file_name     = sample_choice + ".txt"
                    st.session_state.doc_summaries = [{"name": sample_choice, "words": len(t.split()), "status": "success"}]
                    st.rerun()

    with col2:
        st.markdown("<div class='cl-label'>Works for any RFP type</div>", unsafe_allow_html=True)
        for rfp_t, desc in [
            ("Cybersecurity",              "SOC, SIEM, EDR, Zero Trust, GRC"),
            ("Infrastructure Services",    "DC ops, cloud migration, network, storage"),
            ("Application Managed Services", "SAP/ERP, L1–L3 support, releases"),
            ("End User Computing",         "Helpdesk, M365, device management, VDI"),
            ("Digital Workplace",          "Teams, SharePoint, Purview, identity"),
            ("Data & Analytics",           "Data platform, BI, ETL, governance"),
            ("Multi-Tower",                "Any combination of the above"),
        ]:
            st.markdown(f"""
            <div class='cl-info'>
                <div class='cl-info-label'>{rfp_t}</div>
                <div>{desc}</div>
            </div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# MAIN ANALYSIS SCREEN
# ══════════════════════════════════════════════════════════════════════════════
else:
    # Page title — adapts to RFP type
    rfp_t    = get_rfp_type()
    fn_short = st.session_state.file_name[:50] + ("…" if len(st.session_state.file_name) > 50 else "")
    type_str = f" · <em>{rfp_t}</em>" if rfp_t else ""

    st.markdown(f"""
    <div style='padding:2rem 0 1.2rem'>
        <div class='cl-page-title' style='font-size:1.9rem'>
            {fn_short}{type_str}
        </div>
        <div style='font-size:0.82rem;color:var(--text3);margin-top:0.3rem;font-family:DM Mono,monospace'>
            {len(st.session_state.rfp_text.split()):,} words extracted
            {'· ' + str(len(get_domains_list())) + ' domains identified' if get_domains_list() else ''}
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Metrics
    cols = st.columns(5, gap="small")
    n_modules = sum(1 for k in ["customer_brief","pain_analysis","solution_rec","competitive","product_map","exec_summary"] if st.session_state.get(k))
    for col, (label, val, highlight) in zip(cols, [
        ("Words",        f"{len(st.session_state.rfp_text.split()):,}", False),
        ("RFP Type",     rfp_t or "—",                                   bool(rfp_t)),
        ("Domains",      str(len(get_domains_list())) if get_domains_list() else "—", False),
        ("Modules Run",  str(n_modules) + " / 6",                        False),
        ("Chat Q&A",     str(len(st.session_state.chat_history)//2),     False),
    ]):
        with col:
            color = "var(--accent)" if highlight else "var(--text)"
            st.markdown(f"""
            <div class='cl-metric'>
                <div class='cl-metric-label'>{label}</div>
                <div class='cl-metric-val' style='color:{color};font-size:1.3rem'>{val}</div>
            </div>""", unsafe_allow_html=True)

    st.markdown("<div style='height:1.5rem'></div>", unsafe_allow_html=True)

    # Export row
    st.markdown("<div class='cl-label'>Export</div>", unsafe_allow_html=True)
    ec1, ec2, ec3, ec4 = st.columns([3, 1, 1, 2], gap="small")
    with ec1:
        st.markdown("<div style='font-size:0.82rem;color:var(--text2);padding:0.45rem 0'>Generate proposal documents from your completed analysis:</div>", unsafe_allow_html=True)
    with ec2:
        if st.button("📄 Word", key="btn_word", use_container_width=True):
            if not any([st.session_state.customer_brief, st.session_state.exec_summary]):
                st.warning("Run Customer Brief or Executive Summary first.")
            else:
                with st.spinner("Generating Word doc..."):
                    try:
                        from utils.export_word import generate_word_doc
                        path = generate_word_doc(st.session_state)
                        with open(path, "rb") as f:
                            st.download_button("⬇ Download", f, file_name="Clarivo_Proposal.docx",
                                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document", key="dl_word")
                    except Exception as e:
                        st.error(f"Export error: {e}")
    with ec3:
        if st.button("📊 PPT", key="btn_ppt", use_container_width=True):
            if not any([st.session_state.customer_brief, st.session_state.exec_summary]):
                st.warning("Run Customer Brief or Executive Summary first.")
            else:
                with st.spinner("Generating PowerPoint..."):
                    try:
                        from utils.export_ppt import generate_ppt
                        path = generate_ppt(st.session_state)
                        with open(path, "rb") as f:
                            st.download_button("⬇ Download", f, file_name="Clarivo_Presentation.pptx",
                                mime="application/vnd.openxmlformats-officedocument.presentationml.presentation", key="dl_ppt")
                    except Exception as e:
                        st.error(f"Export error: {e}")
    with ec4:
        st.markdown("<div style='font-size:0.75rem;color:var(--text3);padding:0.45rem 0'>Run Domain Classification first for the richest, scope-aware exports</div>", unsafe_allow_html=True)

    st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)

    # ── Tabs ──────────────────────────────────────────────────────────────────
    tab1,tab2,tab3,tab4,tab5,tab6,tab7,tab8,tab9 = st.tabs([
        "Customer Brief","Pain Analysis","Solution Rec",
        "Competitive","Product Mapping","Exec Summary",
        "Domains","Visuals","Chat",
    ])

    descs = dynamic_desc()

    def render_tab(tab, sk, btn_label, btn_key, fn, title, always=False):
        with tab:
            st.markdown(f"<div style='height:0.3rem'></div>", unsafe_allow_html=True)
            st.markdown(f"<div class='cl-section-title'>{title}{rfp_type_tag()}</div>", unsafe_allow_html=True)
            st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)

            if not get_rfp_type() and sk not in ("customer_brief","exec_summary"):
                classify_nudge()

            if not st.session_state[sk]:
                st.markdown(f"<div class='cl-info'><div class='cl-info-label'>About</div><div>{descs.get(sk,'')}</div></div>", unsafe_allow_html=True)
                if st.button(btn_label, key=btn_key):
                    with st.spinner(f"Generating {title.lower()}..."):
                        st.session_state[sk] = fn(st.session_state.rfp_text)
                        st.rerun()
            else:
                content = st.session_state[sk]
                if sk == "product_map":
                    sections = content.split("### ")
                    for sec in sections:
                        if not sec.strip(): continue
                        lines = sec.strip().split("\n")
                        dtitle = lines[0].strip()
                        body   = "\n".join(lines[1:]).strip()
                        st.markdown(f"""
                        <div class='cl-card-accent'>
                            <div style='font-size:0.95rem;font-weight:600;color:var(--text);margin-bottom:0.6rem'>{dtitle}</div>
                        </div>""", unsafe_allow_html=True)
                        st.markdown(body)
                else:
                    st.markdown(f"<div class='cl-card'><p>{content}</p></div>", unsafe_allow_html=True)
                if st.button("↺ Regenerate", key=f"regen_{sk}"):
                    st.session_state[sk] = None
                    st.rerun()

    render_tab(tab1,"customer_brief","Generate Customer Brief","btn_brief",generate_customer_brief,"Customer Intelligence Brief",True)
    render_tab(tab2,"pain_analysis","Run Pain Analysis","btn_pain",generate_pain_analysis,"Pain Point Analysis",True)
    render_tab(tab3,"solution_rec","Generate Solution Recommendation","btn_solrec",generate_solution_recommendation,"Solution Recommendation",True)
    render_tab(tab4,"competitive","Analyse Competitive Landscape","btn_comp",generate_competitive_landscape,"Competitive Intelligence",True)
    render_tab(tab5,"product_map","Map Products & Vendors","btn_prodmap",generate_product_mapping,"Product & Vendor Mapping",True)
    render_tab(tab6,"exec_summary","Generate Executive Summary","btn_execsum",generate_executive_summary,"Executive Summary",True)

    # ── Domains tab ───────────────────────────────────────────────────────────
    with tab7:
        st.markdown("<div style='height:0.3rem'></div>", unsafe_allow_html=True)
        st.markdown(f"<div class='cl-section-title'>Domain & Scope Classification{rfp_type_tag()}</div>", unsafe_allow_html=True)
        st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
        st.markdown("""
        <div class='cl-info'>
            <div class='cl-info-label'>Why run this first</div>
            <div>Clarivo reads the RFP, detects its type (Cybersecurity, Infrastructure, AMS, EUC, Multi-Tower, etc.),
            identifies in-scope service domains, and flags out-of-scope towers — so every other module
            adapts its language, vendors, and recommendations accordingly.</div>
        </div>""", unsafe_allow_html=True)

        if not isinstance(st.session_state.domains, dict):
            if st.button("Classify Domains & Detect Scope", key="btn_domains"):
                with st.spinner("Classifying RFP type and service domains..."):
                    st.session_state.domains = classify_domains(st.session_state.rfp_text)
                    st.rerun()
        else:
            d              = st.session_state.domains
            rfp_type_val   = d.get("rfp_type","Unknown")
            service_model  = d.get("service_model","—")
            key_metrics    = d.get("key_metrics",[])
            domains_list   = d.get("detected_domains",[])
            domain_details = d.get("domain_details",{})
            reasoning      = d.get("reasoning","")

            # Type + model
            st.markdown(f"""
            <div class='cl-card-accent'>
                <div style='display:flex;gap:2rem;align-items:flex-start'>
                    <div>
                        <div class='cl-info-label'>RFP Type</div>
                        <div style='font-family:Instrument Serif,serif;font-size:1.4rem;color:var(--accent)'>{rfp_type_val}</div>
                    </div>
                    <div style='border-left:1px solid var(--border);padding-left:2rem'>
                        <div class='cl-info-label'>Service Model</div>
                        <div style='font-size:0.9rem;font-weight:500;color:var(--text)'>{service_model}</div>
                    </div>
                </div>
            </div>""", unsafe_allow_html=True)

            # In-scope domains
            if domains_list:
                pill_classes = ["pill-amber","pill-green","pill-blue","pill-stone","pill-amber","pill-green","pill-blue","pill-stone"]
                tags = "".join([f"<span class='cl-pill {pill_classes[i%len(pill_classes)]}'>{d_}</span>" for i,d_ in enumerate(domains_list)])
                st.markdown(f"""
                <div class='cl-card'>
                    <div class='cl-info-label'>In-Scope Service Domains · {len(domains_list)} identified</div>
                    <div style='margin-top:0.6rem'>{tags}</div>
                </div>""", unsafe_allow_html=True)

            # Key metrics
            if key_metrics:
                mtags = "".join([f"<span class='cl-pill pill-stone'>{m}</span>" for m in key_metrics])
                st.markdown(f"""
                <div class='cl-card'>
                    <div class='cl-info-label'>Key SLA / KPI Metrics</div>
                    <div style='margin-top:0.6rem'>{mtags}</div>
                </div>""", unsafe_allow_html=True)

            # Domain details
            if domain_details:
                st.markdown("<div class='cl-card'><div class='cl-info-label'>Domain Details</div>", unsafe_allow_html=True)
                for dom, detail in domain_details.items():
                    st.markdown(f"""
                    <div style='margin-top:0.8rem;padding-top:0.8rem;border-top:1px solid var(--border)'>
                        <div style='font-size:0.82rem;font-weight:600;color:var(--text);margin-bottom:0.25rem'>{dom}</div>
                        <div style='font-size:0.8rem;color:var(--text2);line-height:1.65'>{detail}</div>
                    </div>""", unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)

            # Out-of-scope callout
            all_towers = [
                ("Cybersecurity / SOC",              ["cybersecurity","siem","soc","edr","threat","zero trust","grc"]),
                ("Infrastructure / DC Operations",   ["infrastructure","data centre","dc ops","compute","storage","cloud migration"]),
                ("Application Managed Services",     ["application","ams","sap","erp","l1","l2","l3","release","devops"]),
                ("End User Computing / Helpdesk",    ["end user","helpdesk","desktop","euc","m365","device management","vdi"]),
                ("Digital Workplace",                ["digital workplace","teams","sharepoint","intranet","collaboration","purview"]),
                ("Data & Analytics",                 ["data platform","analytics","bi","etl","data warehouse","mlops"]),
            ]
            domain_str = " ".join(domains_list).lower() + " " + rfp_type_val.lower()
            oos = [name for name, kws in all_towers if not any(kw in domain_str for kw in kws)]

            if oos:
                oos_pills = "".join([f"<span class='cl-pill pill-red'>{t}</span>" for t in oos])
                st.markdown(f"""
                <div class='cl-oos'>
                    <div class='cl-oos-title'>⊘ Out of Scope Service Towers</div>
                    <div class='cl-oos-body' style='margin-bottom:0.6rem'>
                        The following service areas were <strong>not identified</strong> in this RFP.
                        These should be explicitly excluded from your proposal or marked as Not in Scope
                        in your solution summary.
                    </div>
                    {oos_pills}
                </div>""", unsafe_allow_html=True)

            if reasoning:
                st.markdown(f"<div class='cl-info'><div class='cl-info-label'>Classification Reasoning</div><div>{reasoning}</div></div>", unsafe_allow_html=True)

            if st.button("↺ Reclassify", key="btn_reclassify"):
                st.session_state.domains = None
                st.rerun()

    # ── Visuals tab ───────────────────────────────────────────────────────────
    with tab8:
        st.markdown("<div style='height:0.3rem'></div>", unsafe_allow_html=True)
        cov_label = "Threat Coverage Matrix" if (rfp_t and "cyber" in rfp_t.lower()) else "Service Coverage Matrix"
        st.markdown(f"<div class='cl-section-title'>Visual Intelligence{rfp_type_tag()}</div>", unsafe_allow_html=True)
        st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)

        if not VISUALS_AVAILABLE:
            st.warning("Visuals require: pip install plotly")
        else:
            if not get_rfp_type():
                classify_nudge()
            vcol1, vcol2 = st.columns(2, gap="medium")
            with vcol1:
                if st.button("Generate CMO", key="btn_cmo"):
                    with st.spinner("Analysing current environment..."):
                        st.session_state.vis_cmo = extract_cmo_data(st.session_state.rfp_text)
                        st.rerun()
                if st.button("Generate FMO", key="btn_fmo"):
                    if not st.session_state.solution_rec:
                        st.warning("Run Solution Recommendation (Tab 3) first — FMO is built from the proposed solution.")
                    else:
                        with st.spinner("Building future architecture..."):
                            st.session_state.vis_fmo = extract_fmo_data(st.session_state.solution_rec)
                            st.rerun()
                if st.button(cov_label, key="btn_threat"):
                    with st.spinner("Mapping coverage..."):
                        st.session_state.vis_threat = extract_threat_coverage(st.session_state.rfp_text)
                        st.rerun()
            with vcol2:
                if st.button("Requirements Traceability", key="btn_trace"):
                    with st.spinner("Building traceability matrix..."):
                        st.session_state.vis_traceability = extract_requirements_traceability(st.session_state.rfp_text)
                        st.rerun()
                if st.button("Vendor Positioning Map", key="btn_vendor"):
                    with st.spinner("Analysing vendor landscape..."):
                        st.session_state.vis_vendor = extract_vendor_positioning(st.session_state.rfp_text)
                        st.rerun()
                if any([st.session_state.vis_cmo,st.session_state.vis_fmo,st.session_state.vis_threat,
                        st.session_state.vis_traceability,st.session_state.vis_vendor]):
                    if st.button("↺ Clear Visuals", key="btn_clrvis"):
                        for vk in ["vis_cmo","vis_fmo","vis_threat","vis_traceability","vis_vendor"]:
                            st.session_state[vk] = None
                        st.rerun()

            for vis_key, vis_label, render_fn in [
                ("vis_cmo",          "Current Mode of Operations",  render_cmo),
                ("vis_fmo",          "Future Mode of Operations",   render_fmo),
                ("vis_threat",       cov_label,                     render_threat_coverage),
                ("vis_traceability", "Requirements Traceability",   render_requirements_traceability),
                ("vis_vendor",       "Vendor Positioning Map",      render_vendor_positioning),
            ]:
                if st.session_state[vis_key]:
                    st.markdown(f"<div class='divider'></div><div class='cl-label'>{vis_label}</div>", unsafe_allow_html=True)
                    st.plotly_chart(render_fn(st.session_state[vis_key]), use_container_width=True)

    # ── Chat tab ──────────────────────────────────────────────────────────────
    with tab9:
        st.markdown("<div style='height:0.3rem'></div>", unsafe_allow_html=True)
        st.markdown(f"<div class='cl-section-title'>Chat with your RFP{rfp_type_tag()}</div>", unsafe_allow_html=True)
        st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)

        for i in range(0, len(st.session_state.chat_history), 2):
            if i < len(st.session_state.chat_history):
                st.markdown(f"<div class='chat-user'><div class='chat-who u'>You</div>{st.session_state.chat_history[i]}</div>", unsafe_allow_html=True)
            if i+1 < len(st.session_state.chat_history):
                st.markdown(f"<div class='chat-ai'><div class='chat-who a'>Clarivo</div>{st.session_state.chat_history[i+1]}</div>", unsafe_allow_html=True)

        if not st.session_state.chat_history:
            st.markdown("<div class='cl-label'>Suggested questions</div>", unsafe_allow_html=True)
            suggs = get_chat_suggestions()
            c1, c2 = st.columns(2)
            for idx, sug in enumerate(suggs):
                with (c1 if idx % 2 == 0 else c2):
                    if st.button(sug, key=f"sug_{idx}", use_container_width=True):
                        with st.spinner("Analysing..."):
                            answer = chat_with_rfp(st.session_state.rfp_text, sug, st.session_state.chat_history)
                            st.session_state.chat_history.extend([sug, answer])
                            st.rerun()

        st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
        user_q = st.text_input("Ask anything about this RFP…", placeholder="e.g. What are the data residency requirements?", key="chat_input")
        qc1, qc2 = st.columns([6, 1])
        with qc2:
            if st.button("Send", key="btn_send", use_container_width=True) and user_q:
                with st.spinner("Analysing..."):
                    answer = chat_with_rfp(st.session_state.rfp_text, user_q, st.session_state.chat_history)
                    st.session_state.chat_history.extend([user_q, answer])
                    st.rerun()
        if st.session_state.chat_history:
            if st.button("Clear conversation", key="btn_clearchat"):
                st.session_state.chat_history = []
                st.rerun()
