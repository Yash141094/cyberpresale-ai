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
except Exception as _ve:
    VISUALS_AVAILABLE = False

# ── Sample RFPs — one per type so tester can see it's not just cybersecurity ──
SAMPLE_RFPS = {
    "Cybersecurity (HDFC Securities)": """
REQUEST FOR PROPOSAL — CYBERSECURITY MANAGED SERVICES
Organisation: HDFC Securities Limited | RFP: RFP-HDFC-CSEC-2025-047
Estimated Value: INR 45-60 Crores | Contract: 3+2 Years

OVERVIEW: HDFC Securities (3.2M active clients, INR 8,000Cr daily transactions) requires an integrated cybersecurity platform across 287 branches, 3 DCs, and hybrid cloud (AWS+Azure).
Environment: 12,500 employees, 8,500 Windows endpoints, 1,200 Linux servers, 650 Mac, 3,400 mobile, 47 critical apps.

REQUIREMENTS:
SIEM: 50,000 EPS, UEBA, SOAR (50 playbooks), ServiceNow integration, 7-year retention, BFSI threat rules.
EDR: Full endpoint coverage, ransomware auto-isolation in 30s, MDR 24x7, air-gapped trading floor.
IAM/PAM: MFA for 12,500 users, PAM for 380 privileged accounts, SSO for 47 apps.
Cloud: CSPM for AWS/Azure, CWPP for 350 VMs, container security (40 Kubernetes clusters).
Network: NGFW for 3 DCs, WAF for 23 apps, SD-WAN for 287 branches, DDoS 500Gbps.
GRC: RBI Cybersecurity Framework, SEBI CSCRF, PCI-DSS v4.0, ISO 27001:2022.
SOC: 24x7x365 IST-based SOC, offices in 5 cities, Indian data residency mandatory, 45-day POC.
""",
    "Infrastructure Services (TCS)": """
REQUEST FOR PROPOSAL — MANAGED INFRASTRUCTURE SERVICES
Organisation: Tata Consultancy Services | RFP: TCS-INFRA-2025-112
Estimated Value: INR 80-100 Crores | Contract: 5 Years

OVERVIEW: TCS is consolidating 3 legacy data centres into a hybrid cloud model. Current state is 80% on-prem VMware vSphere 6.5 (EoL Q2 2026). Seeking a managed infrastructure partner.
Scope: 2,400 physical servers, 18,000 VMs, 3 petabytes storage, 500Gbps inter-DC connectivity.

REQUIREMENTS:
Compute: VMware refresh or migration to HCI (Nutanix/HPE SimpliVity), 99.99% availability SLA.
Storage: SAN/NAS refresh — NetApp or Dell EMC preferred, 3-2-1 backup policy, DR within 4-hour RTO.
Network: LAN/WAN refresh, SD-WAN for 45 offices, BGP routing, firewall management.
Cloud: Azure landing zone, lift-and-shift for 400 workloads, FinOps cost management.
Monitoring: Unified NOC (24x7), observability (Dynatrace/Datadog), ITSM integration with ServiceNow.
Compliance: ISO 20000, ISO 27001, SOC 2 Type II audit support.
SLAs: P1 response 15 min, P2 response 1 hour, monthly SLA reports, CSAT >4.5/5.
""",
    "End User Computing (HDFC Bank)": """
REQUEST FOR PROPOSAL — END USER COMPUTING & HELPDESK
Organisation: HDFC Bank Limited | RFP: HDFC-EUC-2025-088
Estimated Value: INR 35-50 Crores | Contract: 3 Years

OVERVIEW: HDFC Bank operates 12,000 endpoints across 500+ branches and 3 corporate offices. Current helpdesk SLA is 68% — target is 95%. Seeking a managed EUC partner.
Scope: 12,000 Windows PCs + 1,200 MACs, 500 branch network printers, 8,000 mobile devices (BYOD + corporate).

REQUIREMENTS:
Service Desk: 24x7 L1 helpdesk (Hindi + English), <2 hour first response, CSAT target 4.2/5, self-service portal.
Desktop Management: Automated imaging, patch management (72-hour SLA), asset lifecycle, remote support tool.
M365 Administration: Exchange Online, Teams, SharePoint, OneDrive — 14,000 licensed users.
Device Management: Microsoft Intune MDM/MAM, BYOD policy enforcement, device encryption.
VDI: Citrix Virtual Apps for 3,500 contact centre agents, 99.9% availability.
ITSM: ServiceNow ITSM platform (bank-owned licence), full integration with existing CMDB.
Compliance: RBI IT Framework, ISO 20000, quarterly audit support.
""",
    "Application Managed Services (Reliance)": """
REQUEST FOR PROPOSAL — SAP APPLICATION MANAGED SERVICES
Organisation: Reliance Industries Limited | RFP: RIL-AMS-2025-045
Estimated Value: INR 60-80 Crores | Contract: 3+2 Years

OVERVIEW: Reliance Industries runs SAP S/4HANA 2023 across 12 business units (Retail, Jio, O2C, E&P). Seeking an AMS partner for ongoing support, enhancements, and releases.
Landscape: SAP S/4HANA, SAP BTP, SAP Analytics Cloud, SAP IBP, Ariba, SuccessFactors — 18,000 SAP users.

REQUIREMENTS:
L1 Functional Support: 24x7 helpdesk for SAP users, <4 hour response for P2, knowledge base management.
L2 Technical Support: Configuration changes, workflow fixes, master data corrections — 72-hour SLA.
L3 Engineering: Root cause analysis, ABAP development, architecture decisions — <5 business days for P1.
Release Management: Monthly patch releases, bi-annual enhancement packs, full regression testing.
DevOps: CI/CD pipeline on SAP BTP, automated testing (TOSCA), transport management.
Reporting: Monthly SLA dashboards, JIRA-based ticketing, quarterly business reviews.
Compliance: SOX controls, internal audit support, change management documentation.
""",
}

st.set_page_config(
    page_title="Presales AI · Intelligence Platform",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;600;700&family=IBM+Plex+Sans:wght@300;400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap');
:root {
    --bg:#0d0f14; --surface:#13161e; --surface2:#191d28; --surface3:#1e2330;
    --border:#252b38; --border2:#2e3547;
    --accent:#4f8ef7; --green:#34d399; --amber:#fbbf24; --red:#f87171; --purple:#a78bfa;
    --text:#e8eaf0; --text2:#9aa0b4; --text3:#5c6480;
}
html,body,[class*="css"]{font-family:'IBM Plex Sans',sans-serif;background:var(--bg);color:var(--text);}
.stApp{background:var(--bg);}
section[data-testid="stSidebar"]{background:var(--surface)!important;border-right:1px solid var(--border)!important;}
.corp-header{background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:1.8rem 2.5rem;margin-bottom:1.5rem;display:flex;align-items:center;justify-content:space-between;}
.corp-title{font-family:'Playfair Display',serif;font-size:1.7rem;font-weight:700;color:var(--text);}
.corp-title span{color:var(--accent);}
.corp-sub{font-size:0.8rem;color:var(--text3);margin-top:0.3rem;font-weight:300;}
.corp-badge{display:inline-flex;align-items:center;background:rgba(79,142,247,0.08);border:1px solid rgba(79,142,247,0.2);color:var(--accent);padding:0.2rem 0.65rem;border-radius:4px;font-size:0.68rem;font-family:'IBM Plex Mono',monospace;margin-right:0.4rem;margin-top:0.7rem;}
.section-label{font-size:0.65rem;font-weight:600;letter-spacing:0.15em;text-transform:uppercase;color:var(--text3);margin-bottom:0.8rem;padding-bottom:0.4rem;border-bottom:1px solid var(--border);}
.content-card{background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:1.8rem;margin-bottom:1rem;}
.content-card p{font-size:0.875rem;line-height:1.9;color:var(--text2);white-space:pre-wrap;}
.metric-card{background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:1.2rem 1.4rem;}
.metric-label{font-size:0.65rem;font-weight:600;letter-spacing:0.12em;text-transform:uppercase;color:var(--text3);margin-bottom:0.5rem;}
.metric-value{font-family:'Playfair Display',serif;font-size:1.9rem;font-weight:700;color:var(--accent);line-height:1;}
.domain-pill{display:inline-flex;align-items:center;padding:0.35rem 0.9rem;border-radius:6px;font-size:0.78rem;font-weight:500;margin:0.2rem;border:1px solid;}
.pill-blue{background:rgba(79,142,247,0.08);border-color:rgba(79,142,247,0.25);color:#7eb3ff;}
.pill-green{background:rgba(52,211,153,0.08);border-color:rgba(52,211,153,0.25);color:#6ee7b7;}
.pill-amber{background:rgba(251,191,36,0.08);border-color:rgba(251,191,36,0.25);color:#fcd34d;}
.pill-red{background:rgba(248,113,113,0.08);border-color:rgba(248,113,113,0.25);color:#fca5a5;}
.pill-purple{background:rgba(167,139,250,0.08);border-color:rgba(167,139,250,0.25);color:#c4b5fd;}
.pill-teal{background:rgba(56,189,248,0.08);border-color:rgba(56,189,248,0.25);color:#7dd3fc;}
.info-row{background:var(--surface2);border:1px solid var(--border);border-radius:8px;padding:1rem 1.4rem;margin-bottom:0.8rem;font-size:0.82rem;color:var(--text2);line-height:1.7;}
.info-label{font-size:0.65rem;font-weight:600;letter-spacing:0.1em;text-transform:uppercase;color:var(--text3);margin-bottom:0.3rem;}
.chat-bubble-user{background:var(--surface2);border:1px solid var(--border2);border-left:3px solid var(--accent);padding:0.9rem 1.2rem;border-radius:0 8px 8px 0;margin-bottom:0.6rem;font-size:0.85rem;color:var(--text);}
.chat-bubble-ai{background:var(--surface);border:1px solid var(--border);border-left:3px solid var(--green);padding:0.9rem 1.2rem;border-radius:0 8px 8px 0;margin-bottom:1rem;font-size:0.85rem;color:var(--text2);line-height:1.8;white-space:pre-wrap;}
.chat-who{font-size:0.63rem;font-weight:600;letter-spacing:0.1em;text-transform:uppercase;margin-bottom:0.4rem;}
.chat-who.user{color:var(--accent);} .chat-who.ai{color:var(--green);}
.out-of-scope{background:rgba(248,113,113,0.06);border:1px solid rgba(248,113,113,0.25);border-left:4px solid #f87171;border-radius:8px;padding:1.2rem 1.6rem;margin-bottom:1rem;}
.out-of-scope-title{font-size:0.78rem;font-weight:700;color:#f87171;letter-spacing:0.08em;text-transform:uppercase;margin-bottom:0.4rem;}
.out-of-scope-body{font-size:0.82rem;color:#9aa0b4;line-height:1.7;}
.classify-nudge{background:rgba(79,142,247,0.06);border:1px solid rgba(79,142,247,0.2);border-radius:8px;padding:0.9rem 1.3rem;margin-bottom:1rem;font-size:0.82rem;color:var(--text2);}
.rfp-type-badge{display:inline-block;background:rgba(52,211,153,0.1);border:1px solid rgba(52,211,153,0.3);color:#34d399;padding:0.25rem 0.8rem;border-radius:4px;font-size:0.7rem;font-weight:600;letter-spacing:0.06em;font-family:'IBM Plex Mono',monospace;margin-left:0.8rem;vertical-align:middle;}
.stButton>button{background:var(--surface2)!important;color:var(--text)!important;border:1px solid var(--border2)!important;border-radius:6px!important;font-family:'IBM Plex Sans',sans-serif!important;font-size:0.82rem!important;font-weight:500!important;padding:0.5rem 1.3rem!important;transition:all 0.15s!important;}
.stButton>button:hover{background:var(--surface3)!important;border-color:var(--accent)!important;color:var(--accent)!important;}
.stTabs [data-baseweb="tab-list"]{background:var(--surface);border-radius:8px;padding:0.3rem;border:1px solid var(--border);gap:0.1rem;}
.stTabs [data-baseweb="tab"]{font-family:'IBM Plex Sans',sans-serif!important;font-size:0.78rem!important;font-weight:500!important;color:var(--text3)!important;border-radius:6px!important;padding:0.45rem 0.9rem!important;}
.stTabs [aria-selected="true"]{background:var(--surface3)!important;color:var(--text)!important;}
.stTextInput input,.stTextArea textarea{background:var(--surface2)!important;border:1px solid var(--border2)!important;color:var(--text)!important;font-family:'IBM Plex Sans',sans-serif!important;font-size:0.85rem!important;border-radius:6px!important;}
hr{border-color:var(--border)!important;margin:1rem 0!important;}
::-webkit-scrollbar{width:4px;height:4px;} ::-webkit-scrollbar-track{background:var(--bg);} ::-webkit-scrollbar-thumb{background:var(--border2);border-radius:4px;}
[data-testid="stFileUploader"]{background:var(--surface)!important;border:1px dashed var(--border2)!important;border-radius:10px!important;}
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
    """Return detected RFP type string, or None if not classified yet."""
    if isinstance(st.session_state.domains, dict):
        return st.session_state.domains.get("rfp_type") or None
    return None

def get_domains_list():
    if isinstance(st.session_state.domains, dict):
        return st.session_state.domains.get("detected_domains", [])
    return []

def is_module_in_scope(module_key):
    """
    Determine if a module is in scope based on detected RFP type and domains.
    Returns (in_scope: bool, reason: str)
    """
    rfp_type = get_rfp_type()
    if not rfp_type:
        # Domains not classified yet — assume in scope, show nudge
        return True, ""

    domains = get_domains_list()
    domains_lower = [d.lower() for d in domains]
    rfp_lower = rfp_type.lower()

    # Rules: map each module to what domain types make it in scope
    scope_rules = {
        "customer_brief":  (True, ""),   # Always in scope — universal
        "exec_summary":    (True, ""),   # Always in scope — universal
        "pain_analysis":   (True, ""),   # Always in scope — universal
        "solution_rec":    (True, ""),   # Always in scope — universal
        "competitive":     (True, ""),   # Always in scope — universal

        # Product mapping — in scope for all, but description changes
        "product_map": (True, ""),

        # Competitive — always in scope
    }

    # For visual modules — check domain relevance
    visual_scope = {
        "vis_cmo":          (True, ""),   # CMO always relevant — shows current state
        "vis_fmo":          (True, ""),   # FMO always relevant — shows future state
        "vis_threat": _check_threat_scope(rfp_lower, domains_lower),
        "vis_traceability": (True, ""),   # RTM always relevant
        "vis_vendor":       (True, ""),   # Vendor map always relevant
    }

    if module_key in scope_rules:
        return scope_rules[module_key]
    if module_key in visual_scope:
        return visual_scope[module_key]
    return True, ""

def _check_threat_scope(rfp_lower, domains_lower):
    """Threat/coverage matrix — label changes but is always in scope. Just rename it contextually."""
    return True, ""

def out_of_scope_banner(reason):
    st.markdown(f"""
    <div class='out-of-scope'>
        <div class='out-of-scope-title'>⊘ Out of Scope for This RFP</div>
        <div class='out-of-scope-body'>{reason}</div>
    </div>
    """, unsafe_allow_html=True)

def classify_nudge():
    """Show a small prompt to run domain classification first."""
    st.markdown("""
    <div class='classify-nudge'>
        <strong style='color:#4f8ef7'>Tip:</strong> Run <strong>Domain Classification</strong> (Domains tab) first
        to enable scope detection — the platform will automatically mark modules as In Scope or Out of Scope
        based on your RFP type.
    </div>
    """, unsafe_allow_html=True)

def rfp_type_label():
    t = get_rfp_type()
    if t:
        return f"<span class='rfp-type-badge'>{t}</span>"
    return ""

def dynamic_tab_descriptions():
    """Return module descriptions tuned to the detected RFP type."""
    t = get_rfp_type() or "IT Services"
    descs = {
        "customer_brief": f"One-pager covering who the customer is, why this {t} RFP was released, key decision makers, strategic priorities, and entry points.",
        "pain_analysis":  f"Deep analysis of surface requirements vs underlying business pains for this {t} engagement — ranked pain points, compliance pressures, technical debt, red flags.",
        "solution_rec":   f"Strategic recommendation on what to propose for this {t} RFP — architecture approach, service model, phasing, commercial strategy, and POC strategy.",
        "competitive":    f"Who is likely bidding on this {t} deal, threat assessment by competitor, where we win vs lose, and specific counter-strategies.",
        "product_map":    f"Domain-by-domain vendor and product recommendations for this {t} RFP — primary and alternative options justified against actual RFP requirements.",
        "exec_summary":   f"Board-ready 500-600 word executive summary for C-level stakeholders — covers the business case, solution approach, value, and why us.",
    }
    return descs

def get_chat_suggestions():
    """Domain-aware suggested questions for the chat tab."""
    t = get_rfp_type() or ""
    universal = [
        "What is the total contract value and duration?",
        "What are the mandatory vs preferred requirements?",
        "What is the implementation timeline?",
        "What compliance frameworks are specified?",
        "What makes this deal strategically important?",
    ]
    domain_specific = {
        "Cybersecurity": [
            "What SOC model is required — 24x7 or follow-the-sun?",
            "Which security frameworks are mandatory vs optional?",
            "What EDR and SIEM tools are specified or preferred?",
        ],
        "Infrastructure Services": [
            "What are the uptime SLAs and penalty clauses?",
            "Is cloud migration in scope or just DC operations?",
            "What monitoring and ITSM tools are specified?",
        ],
        "Application Managed Services": [
            "What support tiers are required — L1, L2, L3?",
            "What are the P1 and P2 resolution SLAs?",
            "Is enhancement development in scope or support only?",
        ],
        "End User Computing": [
            "What is the endpoint count and device split?",
            "Is VDI or DaaS in scope?",
            "What ITSM platform does the customer use?",
        ],
        "Multi-Tower": [
            "Which towers are mandatory vs optional?",
            "Is this a full outsourcing or selective engagement?",
            "What are the governance and reporting requirements?",
        ],
    }
    extras = domain_specific.get(t, [
        "What support model and SLAs are required?",
        "What existing tools or platforms must be retained?",
    ])
    return (universal[:3] + extras)[:6]

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("<div style='font-family:Playfair Display,serif;font-size:1rem;font-weight:700;color:#e8eaf0;padding:0 0.5rem 0.3rem'>Presales <span style=\"color:#4f8ef7\">AI</span></div>", unsafe_allow_html=True)
    st.markdown("<div style='font-size:0.7rem;color:#5c6480;padding:0 0.5rem 1.2rem;font-family:IBM Plex Mono,monospace'>by Yash Mehrotra · v3.1</div>", unsafe_allow_html=True)
    st.markdown("---")
    api_key = st.secrets.get("GROQ_API_KEY", "") if hasattr(st, "secrets") else ""
    if not api_key:
        api_key = st.text_input("Groq API Key", type="password", placeholder="gsk_...")
    if api_key:
        os.environ["GROQ_API_KEY"] = api_key
        st.success("✓ Connected")
    st.markdown("---")

    # RFP type badge in sidebar
    rfp_t = get_rfp_type()
    if rfp_t:
        st.markdown(f"<div style='font-size:0.63rem;font-weight:600;letter-spacing:0.1em;text-transform:uppercase;color:#5c6480;margin-bottom:0.4rem'>RFP Type Detected</div><div style='font-size:0.8rem;color:#34d399;font-weight:600;margin-bottom:1rem'>{rfp_t}</div>", unsafe_allow_html=True)

    st.markdown("<div style='font-size:0.63rem;font-weight:600;letter-spacing:0.12em;text-transform:uppercase;color:#5c6480;margin-bottom:0.6rem'>Intelligence Modules</div>", unsafe_allow_html=True)
    modules = [
        "Customer Intelligence Brief",
        "Pain Point Analysis",
        "Solution Recommendation",
        "Competitive Intelligence",
        "Product & Vendor Mapping",
        "Executive Summary",
        "Domain Classification",
        "Visual Intelligence (CMO/FMO)",
        "Chat with RFP",
    ]
    for m in modules:
        st.markdown(f"<div style='font-size:0.76rem;color:#9aa0b4;padding:0.15rem 0'>· {m}</div>", unsafe_allow_html=True)

    if st.session_state.rfp_text:
        st.markdown("---")
        doms = get_domains_list()
        dom_str = f"{len(doms)} domains" if doms else "Not classified"
        st.markdown(f"""
        <div style='font-size:0.63rem;color:#5c6480;font-weight:600;letter-spacing:0.1em;text-transform:uppercase'>Active Document</div>
        <div style='font-size:0.78rem;color:#4f8ef7;margin-top:0.3rem'>📄 {st.session_state.file_name}</div>
        <div style='font-size:0.7rem;color:#5c6480;margin-top:0.2rem'>{len(st.session_state.rfp_text.split()):,} words · {dom_str}</div>
        """, unsafe_allow_html=True)
        if st.session_state.doc_summaries:
            for doc in st.session_state.doc_summaries:
                icon  = "✓" if doc["status"] == "success" else "✗"
                color = "#34d399" if doc["status"] == "success" else "#f87171"
                st.markdown(f"<div style='font-size:0.7rem;color:{color};padding:0.1rem 0'>{icon} {doc['name']} · {doc.get('words',0):,}w</div>", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("↺ Reset Session"):
            for key in ["rfp_text","file_name","customer_brief","pain_analysis","solution_rec",
                        "competitive","product_map","exec_summary","domains","vis_cmo","vis_fmo",
                        "vis_threat","vis_traceability","vis_vendor","doc_summaries"]:
                st.session_state[key] = None
            st.session_state.chat_history = []
            st.rerun()

# ── Header ─────────────────────────────────────────────────────────────────────
rfp_type_display = get_rfp_type() or "Any RFP Type"
st.markdown(f"""
<div class='corp-header'>
    <div>
        <div class='corp-title'>Presales <span>AI</span> · v3.1</div>
        <div class='corp-sub'>Enterprise Presales Intelligence · Works for Cybersecurity · Infrastructure · AMS · EUC · Digital Workplace · Multi-Tower RFPs</div>
        <div style='margin-top:0.6rem'>
            <span class='corp-badge'>CUSTOMER INTEL</span>
            <span class='corp-badge'>PAIN ANALYSIS</span>
            <span class='corp-badge'>SOLUTION REC</span>
            <span class='corp-badge'>COMPETITIVE</span>
            <span class='corp-badge'>SCOPE DETECTION</span>
            <span class='corp-badge'>EXPORT DOCX+PPTX</span>
        </div>
    </div>
    <div style='text-align:right'>
        <div style='font-family:IBM Plex Mono,monospace;font-size:0.63rem;color:#5c6480;letter-spacing:0.05em'>ACTIVE RFP TYPE</div>
        <div style='font-family:Playfair Display,serif;font-size:1rem;color:#34d399;margin-top:0.2rem;font-weight:600'>{rfp_type_display}</div>
        <div style='font-family:IBM Plex Mono,monospace;font-size:0.6rem;color:#5c6480;margin-top:0.3rem'>Groq · LLaMA 3.3 · 70B</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# UPLOAD SCREEN
# ══════════════════════════════════════════════════════════════════════════════
if not st.session_state.rfp_text:
    col1, col2 = st.columns([3, 2])
    with col1:
        st.markdown("<div class='section-label'>Document Upload · PDF or Word · Single or Multiple Files</div>", unsafe_allow_html=True)
        uploaded_files = st.file_uploader(
            "Upload RFP Documents",
            type=["pdf", "docx"],
            accept_multiple_files=True,
            label_visibility="collapsed"
        )
        if uploaded_files:
            if not api_key:
                st.warning("Please enter your Groq API Key in the sidebar.")
            else:
                with st.spinner(f"Extracting {len(uploaded_files)} document(s)..."):
                    if len(uploaded_files) == 1:
                        text = extract_text_from_file(uploaded_files[0])
                        summaries = [{"name": uploaded_files[0].name, "words": len(text.split()) if text else 0,
                                      "status": "success" if text else "failed", "size": f"{uploaded_files[0].size//1024} KB"}]
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
                        st.error("Could not extract text. Please check your files.")

        st.markdown("<br><div style='text-align:center;color:#5c6480;font-size:0.73rem;margin-bottom:0.8rem'>— or load a sample —</div>", unsafe_allow_html=True)
        sample_choice = st.selectbox("Choose sample RFP type:", list(SAMPLE_RFPS.keys()), label_visibility="collapsed")
        c1, c2, c3 = st.columns([1, 2, 1])
        with c2:
            if st.button(f"Load Sample →", use_container_width=True):
                if not api_key:
                    st.warning("Please enter your Groq API Key in the sidebar.")
                else:
                    sample_text = SAMPLE_RFPS[sample_choice]
                    st.session_state.rfp_text      = sample_text
                    st.session_state.file_name     = sample_choice.replace(" ", "_") + ".txt"
                    st.session_state.doc_summaries = [{"name": sample_choice, "words": len(sample_text.split()), "status": "success", "size": "sample"}]
                    st.rerun()

    with col2:
        st.markdown("<div class='section-label'>Works For Any RFP Type</div>", unsafe_allow_html=True)
        for rfp_t, desc in [
            ("Cybersecurity",             "SOC, SIEM, EDR, Zero Trust, GRC, Compliance"),
            ("Infrastructure Services",   "DC operations, cloud migration, network, storage"),
            ("Application Managed Services", "SAP/ERP, L1-L3 support, release management"),
            ("End User Computing",        "Helpdesk, desktop, M365, device management, VDI"),
            ("Digital Workplace",         "Teams, SharePoint, Purview, identity, collaboration"),
            ("Data & Analytics",          "Data platform, BI, ETL, data governance, ML"),
            ("Multi-Tower",               "Any combination of the above"),
        ]:
            st.markdown(f"<div class='info-row'><div class='info-label'>{rfp_t}</div><div>{desc}</div></div>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# MAIN ANALYSIS SCREEN
# ══════════════════════════════════════════════════════════════════════════════
else:
    # Metrics bar
    cols = st.columns(5)
    rfp_t = get_rfp_type()
    metrics = [
        ("Words Extracted",  f"{len(st.session_state.rfp_text.split()):,}"),
        ("RFP Type",         rfp_t or "Not Classified"),
        ("Domains Found",    str(len(get_domains_list())) if get_domains_list() else "—"),
        ("Modules Run",      str(sum(1 for k in ["customer_brief","pain_analysis","solution_rec","competitive","product_map","exec_summary"] if st.session_state.get(k)))),
        ("Chat Q&A",         str(len(st.session_state.chat_history)//2)),
    ]
    for col, (label, val) in zip(cols, metrics):
        with col:
            color = "#34d399" if (label == "RFP Type" and rfp_t) else "#4f8ef7"
            st.markdown(f"<div class='metric-card'><div class='metric-label'>{label}</div><div class='metric-value' style='font-size:1.3rem;color:{color}'>{val}</div></div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Export bar
    st.markdown("<div class='section-label'>Export & Deliverables</div>", unsafe_allow_html=True)
    ec1, ec2, ec3, ec4 = st.columns([2, 1, 1, 2])
    with ec1:
        st.markdown("<div style='font-size:0.8rem;color:#9aa0b4;padding:0.4rem 0'>Generate proposal documents from your analysis:</div>", unsafe_allow_html=True)
    with ec2:
        if st.button("📄 Export Word", key="btn_word", use_container_width=True):
            if not any([st.session_state.customer_brief, st.session_state.exec_summary]):
                st.warning("Run at least Customer Brief and Executive Summary first.")
            else:
                with st.spinner("Generating Word document..."):
                    try:
                        from utils.export_word import generate_word_doc
                        path = generate_word_doc(st.session_state)
                        with open(path, "rb") as f:
                            st.download_button("⬇️ Download Word", f, file_name="Presales_Proposal.docx",
                                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document", key="dl_word")
                    except Exception as e:
                        st.error(f"Export error: {e}")
    with ec3:
        if st.button("📊 Export PPT", key="btn_ppt", use_container_width=True):
            if not any([st.session_state.customer_brief, st.session_state.exec_summary]):
                st.warning("Run at least Customer Brief and Executive Summary first.")
            else:
                with st.spinner("Generating PowerPoint..."):
                    try:
                        from utils.export_ppt import generate_ppt
                        path = generate_ppt(st.session_state)
                        with open(path, "rb") as f:
                            st.download_button("⬇️ Download PPT", f, file_name="Presales_Presentation.pptx",
                                mime="application/vnd.openxmlformats-officedocument.presentationml.presentation", key="dl_ppt")
                    except Exception as e:
                        st.error(f"Export error: {e}")
    with ec4:
        st.markdown("<div style='font-size:0.73rem;color:#5c6480;padding:0.4rem 0'>Tip: Run Domain Classification first, then all analysis tabs for a richer, scope-aware export</div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Tabs ──────────────────────────────────────────────────────────────────
    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9 = st.tabs([
        "  Customer Brief  ",
        "  Pain Analysis  ",
        "  Solution Rec  ",
        "  Competitive  ",
        "  Product Mapping  ",
        "  Executive Summary  ",
        "  Domains  ",
        "  Visuals  ",
        "  Chat  ",
    ])

    descs = dynamic_tab_descriptions()

    # ── Generic tab renderer with scope awareness ─────────────────────────────
    def render_tab(tab, session_key, btn_label, btn_key, generator_fn, title, about, always_in_scope=False):
        with tab:
            # Header with RFP type badge
            st.markdown(f"<div class='section-label'>{title}{rfp_type_label()}</div>", unsafe_allow_html=True)

            # Classify nudge if not done yet (only for non-domain-aware modules)
            if not get_rfp_type() and session_key not in ("customer_brief", "exec_summary"):
                classify_nudge()

            # Scope check
            if not always_in_scope and get_rfp_type():
                in_scope, reason = is_module_in_scope(session_key)
                if not in_scope:
                    out_of_scope_banner(reason)
                    return

            if not st.session_state[session_key]:
                st.markdown(f"<div class='info-row'><div class='info-label'>About This Module</div><div>{about}</div></div>", unsafe_allow_html=True)
                if st.button(f"  {btn_label}  ", key=btn_key):
                    with st.spinner(f"Generating {title.lower()}..."):
                        st.session_state[session_key] = generator_fn(st.session_state.rfp_text)
                        st.rerun()
            else:
                content = st.session_state[session_key]
                if session_key == "product_map":
                    sections = content.split("### ")
                    for section in sections:
                        if not section.strip():
                            continue
                        lines = section.strip().split("\n")
                        domain_title = lines[0].strip()
                        body = "\n".join(lines[1:]).strip()
                        st.markdown(f"<div class='content-card' style='border-left:3px solid #4f8ef7;padding-left:1.2rem'>"
                                    f"<div style='font-size:1rem;font-weight:700;color:#e8eaf0;margin-bottom:0.6rem'>{domain_title}</div>"
                                    f"</div>", unsafe_allow_html=True)
                        st.markdown(body)
                else:
                    st.markdown(f"<div class='content-card'><p>{content}</p></div>", unsafe_allow_html=True)
                if st.button("↺ Regenerate", key=f"regen_{session_key}"):
                    st.session_state[session_key] = None
                    st.rerun()

    # ── Tab 1: Customer Brief ─────────────────────────────────────────────────
    render_tab(tab1, "customer_brief", "Generate Customer Brief", "btn_brief",
               generate_customer_brief,
               "Customer Intelligence Brief", descs["customer_brief"], always_in_scope=True)

    # ── Tab 2: Pain Analysis ──────────────────────────────────────────────────
    render_tab(tab2, "pain_analysis", "Run Pain Analysis", "btn_pain",
               generate_pain_analysis,
               "Pain Point & Requirements Analysis", descs["pain_analysis"], always_in_scope=True)

    # ── Tab 3: Solution Recommendation ───────────────────────────────────────
    render_tab(tab3, "solution_rec", "Generate Solution Recommendation", "btn_solrec",
               generate_solution_recommendation,
               "Solution Recommendation", descs["solution_rec"], always_in_scope=True)

    # ── Tab 4: Competitive ────────────────────────────────────────────────────
    render_tab(tab4, "competitive", "Analyze Competitive Landscape", "btn_comp",
               generate_competitive_landscape,
               "Competitive Intelligence", descs["competitive"], always_in_scope=True)

    # ── Tab 5: Product Mapping ────────────────────────────────────────────────
    render_tab(tab5, "product_map", "Map Products & Vendors", "btn_prodmap",
               generate_product_mapping,
               "Product & Vendor Mapping", descs["product_map"], always_in_scope=True)

    # ── Tab 6: Executive Summary ──────────────────────────────────────────────
    render_tab(tab6, "exec_summary", "Generate Executive Summary", "btn_execsum",
               generate_executive_summary,
               "Executive Summary · Proposal Ready", descs["exec_summary"], always_in_scope=True)

    # ── Tab 7: Domain Classification ─────────────────────────────────────────
    with tab7:
        rfp_t = get_rfp_type()
        label = f"Domain & Scope Classification{rfp_type_label()}" if rfp_t else "Domain & Scope Classification"
        st.markdown(f"<div class='section-label'>{label}</div>", unsafe_allow_html=True)
        st.markdown("""
        <div class='info-row'>
            <div class='info-label'>Why classify first?</div>
            <div>Classification detects the RFP type (Cybersecurity, Infrastructure, AMS, EUC, Multi-Tower, etc.)
            and identifies in-scope service domains. Once classified, every other module adapts its language,
            vendor recommendations, and scope markers accordingly. Out of scope modules will show a clear banner
            instead of generating irrelevant analysis.</div>
        </div>
        """, unsafe_allow_html=True)

        if not isinstance(st.session_state.domains, dict):
            if st.button("  Classify Domains & Detect Scope  ", key="btn_domains"):
                with st.spinner("Classifying RFP type and service domains..."):
                    st.session_state.domains = classify_domains(st.session_state.rfp_text)
                    st.rerun()
        else:
            d = st.session_state.domains
            rfp_type_val = d.get("rfp_type", "Unknown")
            service_model = d.get("service_model", "—")
            key_metrics   = d.get("key_metrics", [])
            domains_list  = d.get("detected_domains", [])
            domain_details = d.get("domain_details", {})
            reasoning     = d.get("reasoning", "")

            # RFP type + service model header
            st.markdown(f"""
            <div class='content-card' style='border-left:4px solid #34d399'>
                <div style='display:flex;align-items:center;gap:1rem;margin-bottom:0.8rem'>
                    <div>
                        <div class='info-label'>RFP Type Detected</div>
                        <div style='font-size:1.2rem;font-weight:700;color:#34d399'>{rfp_type_val}</div>
                    </div>
                    <div style='border-left:1px solid #252b38;padding-left:1rem'>
                        <div class='info-label'>Service Model</div>
                        <div style='font-size:0.9rem;color:#e8eaf0;font-weight:500'>{service_model}</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # In-scope domains
            if domains_list:
                pill_colors = ["pill-blue","pill-green","pill-amber","pill-red","pill-purple","pill-teal","pill-blue","pill-green"]
                tags = "".join([f"<span class='domain-pill {pill_colors[i%len(pill_colors)]}'>{d_}</span>" for i, d_ in enumerate(domains_list)])
                st.markdown(f"""
                <div class='content-card'>
                    <div class='info-label'>In-Scope Service Domains · {len(domains_list)} Identified</div>
                    <div style='margin-top:0.8rem'>{tags}</div>
                </div>
                """, unsafe_allow_html=True)

            # Key metrics
            if key_metrics:
                metrics_html = "".join([f"<span class='domain-pill pill-amber'>{m}</span>" for m in key_metrics])
                st.markdown(f"""
                <div class='content-card'>
                    <div class='info-label'>Key SLA / KPI Metrics Expected</div>
                    <div style='margin-top:0.8rem'>{metrics_html}</div>
                </div>
                """, unsafe_allow_html=True)

            # Domain details
            if domain_details:
                st.markdown("<div class='content-card'><div class='info-label'>Domain Details</div>", unsafe_allow_html=True)
                for domain, detail in domain_details.items():
                    st.markdown(f"""
                    <div style='margin-bottom:0.9rem;padding-bottom:0.9rem;border-bottom:1px solid #252b38'>
                        <div style='font-size:0.82rem;color:#e8eaf0;font-weight:600;margin-bottom:0.3rem'>{domain}</div>
                        <div style='font-size:0.8rem;color:#9aa0b4;line-height:1.7'>{detail}</div>
                    </div>
                    """, unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)

            # Out-of-scope callout — anything NOT in domains list from common service towers
            all_towers = [
                ("Cybersecurity / SOC", ["cybersecurity","siem","soc","edr","threat","zero trust","grc"]),
                ("Infrastructure / DC Operations", ["infrastructure","data centre","dc ops","compute","network","storage","cloud migration"]),
                ("Application Managed Services", ["application","ams","sap","erp","l1","l2","l3","release","devops"]),
                ("End User Computing / Helpdesk", ["end user","helpdesk","desktop","euc","m365","device management","vdi"]),
                ("Digital Workplace", ["digital workplace","teams","sharepoint","intranet","collaboration","purview"]),
                ("Data & Analytics", ["data platform","analytics","bi","etl","data warehouse","mlops","machine learning"]),
            ]
            domains_str = " ".join(domains_list).lower() + " " + rfp_type_val.lower()
            out_of_scope_towers = []
            for tower_name, keywords in all_towers:
                if not any(kw in domains_str for kw in keywords):
                    out_of_scope_towers.append(tower_name)

            if out_of_scope_towers:
                oos_tags = "".join([f"<span class='domain-pill pill-red'>{t}</span>" for t in out_of_scope_towers])
                st.markdown(f"""
                <div class='out-of-scope' style='margin-top:0.5rem'>
                    <div class='out-of-scope-title'>⊘ Out of Scope Service Towers</div>
                    <div class='out-of-scope-body' style='margin-bottom:0.8rem'>
                        The following service areas were <strong>not identified</strong> in this RFP.
                        These should be explicitly excluded from your proposal scope, or called out as
                        "Not in Scope" in the solution summary.
                    </div>
                    <div>{oos_tags}</div>
                </div>
                """, unsafe_allow_html=True)

            # Strategic reasoning
            if reasoning:
                st.markdown(f"<div class='content-card'><div class='info-label'>Classification Reasoning</div><p>{reasoning}</p></div>", unsafe_allow_html=True)

            if st.button("↺ Reclassify", key="btn_reclassify"):
                st.session_state.domains = None
                st.rerun()

    # ── Tab 8: Visuals ────────────────────────────────────────────────────────
    with tab8:
        rfp_t = get_rfp_type()
        # Rename threat/coverage matrix based on RFP type
        coverage_label = "Threat Coverage Matrix" if (rfp_t and "cyber" in rfp_t.lower()) else "Service Coverage Matrix"
        st.markdown(f"<div class='section-label'>Visual Intelligence{rfp_type_label()} · CMO · FMO · {coverage_label} · Traceability · Vendor Map</div>", unsafe_allow_html=True)

        if not VISUALS_AVAILABLE:
            st.warning("Visuals require: pip install plotly matplotlib")
        else:
            # Scope-aware visual panel
            if not get_rfp_type():
                classify_nudge()

            vcol1, vcol2 = st.columns(2)
            with vcol1:
                if st.button("  Generate CMO  ", key="btn_cmo"):
                    with st.spinner("Analysing current environment..."):
                        st.session_state.vis_cmo = extract_cmo_data(st.session_state.rfp_text)
                        st.rerun()

                # FMO requires solution rec to be generated first
                if st.button("  Generate FMO  ", key="btn_fmo"):
                    if not st.session_state.solution_rec:
                        st.warning("⚠️ Run **Solution Recommendation** (Tab 3) first — FMO is built from the proposed solution.")
                    else:
                        with st.spinner("Building future architecture..."):
                            st.session_state.vis_fmo = extract_fmo_data(st.session_state.solution_rec)
                            st.rerun()

                if st.button(f"  {coverage_label}  ", key="btn_threat"):
                    with st.spinner("Mapping coverage matrix..."):
                        st.session_state.vis_threat = extract_threat_coverage(st.session_state.rfp_text)
                        st.rerun()

            with vcol2:
                if st.button("  Requirements Traceability  ", key="btn_trace"):
                    with st.spinner("Building traceability matrix..."):
                        st.session_state.vis_traceability = extract_requirements_traceability(st.session_state.rfp_text)
                        st.rerun()

                if st.button("  Vendor Positioning Map  ", key="btn_vendor"):
                    with st.spinner("Analysing vendor landscape..."):
                        st.session_state.vis_vendor = extract_vendor_positioning(st.session_state.rfp_text)
                        st.rerun()

                if any([st.session_state.vis_cmo, st.session_state.vis_fmo, st.session_state.vis_threat,
                        st.session_state.vis_traceability, st.session_state.vis_vendor]):
                    if st.button("↺ Clear All Visuals", key="btn_clrvis"):
                        for vk in ["vis_cmo","vis_fmo","vis_threat","vis_traceability","vis_vendor"]:
                            st.session_state[vk] = None
                        st.rerun()

            # Render visuals
            if st.session_state.vis_cmo:
                st.markdown("<div class='section-label' style='margin-top:1.5rem'>Current Mode of Operations (CMO)</div>", unsafe_allow_html=True)
                st.plotly_chart(render_cmo(st.session_state.vis_cmo), use_container_width=True)

            if st.session_state.vis_fmo:
                st.markdown("<div class='section-label' style='margin-top:1rem'>Future Mode of Operations (FMO)</div>", unsafe_allow_html=True)
                st.plotly_chart(render_fmo(st.session_state.vis_fmo), use_container_width=True)

            if st.session_state.vis_threat:
                st.markdown(f"<div class='section-label' style='margin-top:1rem'>{coverage_label}</div>", unsafe_allow_html=True)
                st.plotly_chart(render_threat_coverage(st.session_state.vis_threat), use_container_width=True)

            if st.session_state.vis_traceability:
                st.markdown("<div class='section-label' style='margin-top:1rem'>Requirements Traceability Matrix</div>", unsafe_allow_html=True)
                st.plotly_chart(render_requirements_traceability(st.session_state.vis_traceability), use_container_width=True)

            if st.session_state.vis_vendor:
                st.markdown("<div class='section-label' style='margin-top:1rem'>Vendor Positioning Map</div>", unsafe_allow_html=True)
                st.plotly_chart(render_vendor_positioning(st.session_state.vis_vendor), use_container_width=True)

    # ── Tab 9: Chat ───────────────────────────────────────────────────────────
    with tab9:
        rfp_t = get_rfp_type()
        chat_title = f"Chat with RFP{rfp_type_label()}"
        st.markdown(f"<div class='section-label'>{chat_title}</div>", unsafe_allow_html=True)

        for i in range(0, len(st.session_state.chat_history), 2):
            if i < len(st.session_state.chat_history):
                st.markdown(f"<div class='chat-bubble-user'><div class='chat-who user'>You</div>{st.session_state.chat_history[i]}</div>", unsafe_allow_html=True)
            if i+1 < len(st.session_state.chat_history):
                st.markdown(f"<div class='chat-bubble-ai'><div class='chat-who ai'>AI Consultant</div>{st.session_state.chat_history[i+1]}</div>", unsafe_allow_html=True)

        if not st.session_state.chat_history:
            st.markdown("<div style='color:#5c6480;font-size:0.72rem;margin-bottom:0.8rem;text-transform:uppercase;font-weight:600;letter-spacing:0.08em'>Suggested Questions</div>", unsafe_allow_html=True)
            suggestions = get_chat_suggestions()
            cols = st.columns(2)
            for idx, sug in enumerate(suggestions):
                with cols[idx % 2]:
                    if st.button(sug, key=f"sug_{idx}", use_container_width=True):
                        with st.spinner("Analysing..."):
                            answer = chat_with_rfp(st.session_state.rfp_text, sug, st.session_state.chat_history)
                            st.session_state.chat_history.extend([sug, answer])
                            st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)
        user_q = st.text_input("Ask anything about this RFP...", placeholder="e.g. What are the data residency requirements?", key="chat_input")
        c1, c2 = st.columns([5, 1])
        with c2:
            if st.button("Send →", key="btn_send", use_container_width=True) and user_q:
                with st.spinner("Analysing..."):
                    answer = chat_with_rfp(st.session_state.rfp_text, user_q, st.session_state.chat_history)
                    st.session_state.chat_history.extend([user_q, answer])
                    st.rerun()
        if st.session_state.chat_history:
            if st.button("Clear Chat", key="btn_clearchat"):
                st.session_state.chat_history = []
                st.rerun()
