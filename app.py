import streamlit as st
import os
from utils.document_processor import extract_text_from_file
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

SAMPLE_RFP = """
REQUEST FOR PROPOSAL - CYBERSECURITY SOLUTION
Organization: HDFC Securities Limited
RFP Reference: RFP-HDFC-CSEC-2025-047
Date: March 2025
Estimated Value: INR 45-60 Crores | Contract: 3+2 Years

EXECUTIVE OVERVIEW
HDFC Securities Limited, a leading stockbroking firm with 3.2 million active clients and INR 8,000 crores daily transaction volume, is undertaking a comprehensive cybersecurity transformation. Operating across 287 branches, 3 data centers, and hybrid cloud (AWS + Azure), the organization requires an integrated security platform addressing SIEM, EDR, Zero Trust, Cloud Security, Network Security, and GRC.

ENVIRONMENT: 12,500 employees, 8,500 Windows endpoints, 1,200 Linux servers, 650 Mac devices, 3,400 mobile devices, 47 critical applications, 1,200 network devices.

REQUIREMENTS:
SIEM: 50,000 EPS ingestion, UEBA, SOAR with 50 playbooks, ServiceNow integration, 7-year retention, BFSI threat rules.
EDR: Full coverage across all endpoints, ransomware auto-isolation in 30 seconds, MDR 24x7, air-gapped trading floor support.
IAM/PAM: MFA for 12,500 users, PAM for 380 privileged accounts, JIT/JEA, SSO for 47 apps, passwordless auth.
Cloud: CSPM for AWS/Azure, CWPP for 350 VMs, container security for 40 Kubernetes clusters, 120 API protection.
Network: NGFW for 3 DCs, IDS/IPS, WAF for 23 apps, SD-WAN for 287 branches, DDoS 500Gbps, ZTNA for 4,300 contractors.
GRC: RBI Cybersecurity Framework, SEBI CSCRF, PCI-DSS v4.0, ISO 27001:2022, automated audit evidence, 200 vendor assessments.

COMMERCIAL: 24x7x365 SOC support IST, offices mandatory in 5 cities, Indian data residency required, 45-day mandatory POC, Phase 1 delivery 90 days.
"""

st.set_page_config(page_title="CyberPresales AI", page_icon="🛡️", layout="wide", initial_sidebar_state="expanded")

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
.export-bar{background:var(--surface2);border:1px solid var(--border);border-radius:10px;padding:1rem 1.5rem;margin-bottom:1.5rem;display:flex;align-items:center;gap:1rem;}
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

# Session state
for key in ["rfp_text","file_name","customer_brief","pain_analysis","solution_rec","competitive","product_map","exec_summary","domains","vis_cmo","vis_fmo","vis_threat","vis_traceability","vis_vendor"]:
    if key not in st.session_state:
        st.session_state[key] = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Sidebar
with st.sidebar:
    st.markdown("<div style='font-family:Playfair Display,serif;font-size:1rem;font-weight:700;color:#e8eaf0;padding:0 0.5rem 0.3rem'>CyberPresales <span style=\"color:#4f8ef7\">AI</span></div>", unsafe_allow_html=True)
    st.markdown("<div style='font-size:0.7rem;color:#5c6480;padding:0 0.5rem 1.2rem;font-family:IBM Plex Mono,monospace'>by Yash Mehrotra · v3.0</div>", unsafe_allow_html=True)
    st.markdown("---")
    api_key = st.secrets.get("GROQ_API_KEY", "") or st.text_input("Groq API Key", type="password", placeholder="gsk_...")
if api_key:
    os.environ["GROQ_API_KEY"] = api_key
    st.success("✓ Connected")
    st.markdown("---")
    st.markdown("<div style='font-size:0.63rem;font-weight:600;letter-spacing:0.12em;text-transform:uppercase;color:#5c6480;margin-bottom:0.6rem'>Intelligence Modules</div>", unsafe_allow_html=True)
    modules = ["Customer Brief", "Pain Analysis", "Solution Recommendation", "Competitive Intelligence", "Product Mapping", "Executive Summary", "Domain Classification", "Chat with RFP"]
    for m in modules:
        st.markdown(f"<div style='font-size:0.76rem;color:#9aa0b4;padding:0.15rem 0'>· {m}</div>", unsafe_allow_html=True)
    if st.session_state.rfp_text:
        st.markdown("---")
        st.markdown(f"<div style='font-size:0.63rem;color:#5c6480;font-weight:600;letter-spacing:0.1em;text-transform:uppercase'>Active Document</div><div style='font-size:0.78rem;color:#4f8ef7;margin-top:0.3rem'>📄 {st.session_state.file_name}</div><div style='font-size:0.7rem;color:#5c6480;margin-top:0.2rem'>{len(st.session_state.rfp_text.split()):,} words</div>", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("↺ Reset Session"):
            for key in ["rfp_text","file_name","customer_brief","pain_analysis","solution_rec","competitive","product_map","exec_summary","domains","vis_cmo","vis_fmo","vis_threat","vis_traceability","vis_vendor"]:
                st.session_state[key] = None
            st.session_state.chat_history = []
            st.rerun()

# Header
st.markdown("""
<div class='corp-header'>
    <div>
        <div class='corp-title'>Cyber<span>Presales</span> AI · v3</div>
        <div class='corp-sub'>Enterprise Presales Intelligence Platform · Customer Brief · Solution Architecture · Competitive Intel</div>
        <div style='margin-top:0.6rem'>
            <span class='corp-badge'>CUSTOMER INTEL</span><span class='corp-badge'>PAIN ANALYSIS</span>
            <span class='corp-badge'>SOLUTION REC</span><span class='corp-badge'>COMPETITIVE</span>
            <span class='corp-badge'>EXPORT DOCX+PPTX</span>
        </div>
    </div>
    <div style='text-align:right'>
        <div style='font-family:IBM Plex Mono,monospace;font-size:0.63rem;color:#5c6480;letter-spacing:0.05em'>POWERED BY</div>
        <div style='font-family:Playfair Display,serif;font-size:1rem;color:#9aa0b4;margin-top:0.2rem'>Groq · LLaMA 3.3 · 70B</div>
    </div>
</div>
""", unsafe_allow_html=True)

# Upload
if not st.session_state.rfp_text:
    col1, col2 = st.columns([3,2])
    with col1:
        st.markdown("<div class='section-label'>Document Upload</div>", unsafe_allow_html=True)
        uploaded = st.file_uploader("Upload RFP (PDF or Word)", type=["pdf","docx"], label_visibility="collapsed")
        if uploaded:
            if not api_key:
                st.warning("Please enter your Groq API Key in the sidebar.")
            else:
                with st.spinner("Extracting document..."):
                    text = extract_text_from_file(uploaded)
                    if text:
                        st.session_state.rfp_text = text
                        st.session_state.file_name = uploaded.name
                        st.rerun()
                    else:
                        st.error("Could not extract text from this file.")
        st.markdown("<br><div style='text-align:center;color:#5c6480;font-size:0.73rem;margin-bottom:0.8rem'>— or load sample —</div>", unsafe_allow_html=True)
        c1,c2,c3 = st.columns([1,2,1])
        with c2:
            if st.button("Load Sample RFP →", use_container_width=True):
                if not api_key:
                    st.warning("Please enter your Groq API Key in the sidebar.")
                else:
                    st.session_state.rfp_text = SAMPLE_RFP
                    st.session_state.file_name = "HDFC_Cybersecurity_RFP_2025.pdf"
                    st.rerun()
    with col2:
        st.markdown("<div class='section-label'>What You Get</div>", unsafe_allow_html=True)
        for cap, desc in [
            ("Customer Intelligence Brief", "Who they are, why this RFP, decision makers"),
            ("Pain Point Analysis", "What they really need vs what they wrote"),
            ("Solution Recommendation", "What to propose and exactly why"),
            ("Competitive Landscape", "Who's bidding and how to win"),
            ("Product Mapping", "Vendor-by-vendor with deal strategy"),
            ("Word & PPT Export", "Ready-to-use proposal documents"),
        ]:
            st.markdown(f"<div class='info-row'><div class='info-label'>{cap}</div><div>{desc}</div></div>", unsafe_allow_html=True)

# Main
else:
    # Metrics
    cols = st.columns(4)
    metrics = [
        ("Words Extracted", f"{len(st.session_state.rfp_text.split()):,}"),
        ("Modules Run", str(sum(1 for k in ["customer_brief","pain_analysis","solution_rec","competitive","product_map","exec_summary"] if st.session_state.get(k)))),
        ("Domains", str(len(st.session_state.domains.get("detected_domains",[]))) if isinstance(st.session_state.domains,dict) else "—"),
        ("Chat Q&A", str(len(st.session_state.chat_history)//2)),
    ]
    for col, (label, val) in zip(cols, metrics):
        with col:
            st.markdown(f"<div class='metric-card'><div class='metric-label'>{label}</div><div class='metric-value'>{val}</div></div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Export bar
    st.markdown("<div class='section-label'>Export & Deliverables</div>", unsafe_allow_html=True)
    ec1, ec2, ec3, ec4 = st.columns([2,1,1,2])
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
                            st.download_button("⬇️ Download Word", f, file_name="CyberPresales_Proposal.docx",
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
                            st.download_button("⬇️ Download PPT", f, file_name="CyberPresales_Presentation.pptx",
                                mime="application/vnd.openxmlformats-officedocument.presentationml.presentation", key="dl_ppt")
                    except Exception as e:
                        st.error(f"Export error: {e}")
    with ec4:
        st.markdown("<div style='font-size:0.73rem;color:#5c6480;padding:0.4rem 0'>Tip: Run all analysis tabs first for richer exports</div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    tab1,tab2,tab3,tab4,tab5,tab6,tab7,tab8,tab9 = st.tabs([
        "  Customer Brief  ","  Pain Analysis  ","  Solution Rec  ",
        "  Competitive  ","  Product Mapping  ","  Executive Summary  ",
        "  Domains  ","  Visuals  ","  Chat  "
    ])

    def render_tab(tab, session_key, btn_label, btn_key, generator_fn, title, about):
        with tab:
            st.markdown(f"<div class='section-label'>{title}</div>", unsafe_allow_html=True)
            if not st.session_state[session_key]:
                st.markdown(f"<div class='info-row'><div class='info-label'>About</div><div>{about}</div></div>", unsafe_allow_html=True)
                if st.button(f"  {btn_label}  ", key=btn_key):
                    with st.spinner(f"Generating {title.lower()}..."):
                        st.session_state[session_key] = generator_fn(st.session_state.rfp_text)
                        st.rerun()
            else:
                st.markdown(f"<div class='content-card'><p>{st.session_state[session_key]}</p></div>", unsafe_allow_html=True)
                if st.button("↺ Regenerate", key=f"regen_{session_key}"):
                    st.session_state[session_key] = None
                    st.rerun()

    render_tab(tab1, "customer_brief", "Generate Customer Brief", "btn_brief", generate_customer_brief,
        "Customer Intelligence Brief",
        "One-pager covering who the customer is, why this RFP was released, key decision makers, strategic priorities, and relationship entry points. Read this before any customer meeting.")

    render_tab(tab2, "pain_analysis", "Run Pain Analysis", "btn_pain", generate_pain_analysis,
        "Pain Point & Requirements Analysis",
        "Deep analysis of surface requirements vs underlying business pains, ranked pain points with business impact, compliance pressures, technical debt, and red flags for vendors.")

    render_tab(tab3, "solution_rec", "Generate Solution Recommendation", "btn_solrec", generate_solution_recommendation,
        "Solution Recommendation for Presales",
        "Strategic recommendation on what solution to propose, architecture approach, implementation phasing, commercial strategy, proposal messaging framework, and POC strategy.")

    render_tab(tab4, "competitive", "Analyze Competitive Landscape", "btn_comp", generate_competitive_landscape,
        "Competitive Intelligence",
        "Who is likely bidding, threat assessment by competitor, where we win vs lose, customer evaluation biases, counter-strategies, and winning conditions for this deal.")

    render_tab(tab5, "product_map", "Map Products & Vendors", "btn_prodmap", generate_product_mapping,
        "Detailed Product & Vendor Mapping",
        "Domain-by-domain vendor recommendations with primary and alternative options, specific justification tied to RFP requirements, integration notes, and deal strategy.")

    render_tab(tab6, "exec_summary", "Generate Executive Summary", "btn_execsum", generate_executive_summary,
        "Executive Summary · Proposal Ready",
        "Board-ready 500-600 word executive summary for C-level stakeholders. Covers security imperative, solution approach, business value, and value proposition. Ready to paste into your proposal.")

    # Domains tab
    with tab7:
        st.markdown("<div class='section-label'>Cybersecurity Domain Classification</div>", unsafe_allow_html=True)
        if not isinstance(st.session_state.domains, dict):
            if st.button("  Classify Domains  ", key="btn_domains"):
                with st.spinner("Classifying domains..."):
                    st.session_state.domains = classify_domains(st.session_state.rfp_text)
                    st.rerun()
        else:
            domains_list = st.session_state.domains.get("detected_domains", [])
            pill_colors = ["pill-blue","pill-green","pill-amber","pill-red","pill-purple","pill-teal","pill-blue","pill-green"]
            tags = "".join([f"<span class='domain-pill {pill_colors[i%len(pill_colors)]}'>{d}</span>" for i,d in enumerate(domains_list)])
            st.markdown(f"<div class='content-card'><div class='info-label'>Detected Domains · {len(domains_list)} identified</div><div style='margin-top:0.8rem'>{tags}</div></div>", unsafe_allow_html=True)

            details = st.session_state.domains.get("domain_details", {})
            if details:
                st.markdown("<div class='content-card'><div class='info-label'>Domain Details</div>", unsafe_allow_html=True)
                for domain, detail in details.items():
                    st.markdown(f"<div style='margin-bottom:0.8rem'><div style='font-size:0.8rem;color:#e8eaf0;font-weight:500;margin-bottom:0.3rem'>{domain}</div><div style='font-size:0.82rem;color:#9aa0b4;line-height:1.7'>{detail}</div></div>", unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)

            reasoning = st.session_state.domains.get("reasoning", "")
            if reasoning:
                st.markdown(f"<div class='content-card'><div class='info-label'>Strategic Analysis</div><p>{reasoning}</p></div>", unsafe_allow_html=True)

    # Visuals tab
    with tab8:
        st.markdown("<div class='section-label'>Visual Intelligence · CMO · FMO · Threat Coverage · Traceability · Vendor Map</div>", unsafe_allow_html=True)
        if not VISUALS_AVAILABLE:
            st.warning('Visuals require: pip install plotly matplotlib')
        else:
            vcol1, vcol2 = st.columns(2)
            with vcol1:
                if st.button('  Generate CMO Diagram  ', key='btn_cmo'):
                    with st.spinner('Analyzing current environment...'):
                        st.session_state.vis_cmo = extract_cmo_data(st.session_state.rfp_text)
                        st.rerun()
                if st.button('  Generate FMO Diagram  ', key='btn_fmo'):
                    with st.spinner('Building future architecture...'):
                        st.session_state.vis_fmo = extract_fmo_data(st.session_state.rfp_text)
                        st.rerun()
                if st.button('  Threat Coverage Matrix  ', key='btn_threat'):
                    with st.spinner('Mapping threat coverage...'):
                        st.session_state.vis_threat = extract_threat_coverage(st.session_state.rfp_text)
                        st.rerun()
            with vcol2:
                if st.button('  Requirements Traceability  ', key='btn_trace'):
                    with st.spinner('Building traceability matrix...'):
                        st.session_state.vis_traceability = extract_requirements_traceability(st.session_state.rfp_text)
                        st.rerun()
                if st.button('  Vendor Positioning Map  ', key='btn_vendor'):
                    with st.spinner('Analyzing vendor landscape...'):
                        st.session_state.vis_vendor = extract_vendor_positioning(st.session_state.rfp_text)
                        st.rerun()
                if any([st.session_state.vis_cmo, st.session_state.vis_fmo, st.session_state.vis_threat, st.session_state.vis_traceability, st.session_state.vis_vendor]):
                    if st.button('↺ Clear All Visuals', key='btn_clrvis'):
                        for vk in ['vis_cmo','vis_fmo','vis_threat','vis_traceability','vis_vendor']:
                            st.session_state[vk] = None
                        st.rerun()

            if st.session_state.vis_cmo:
                st.markdown("<div class='section-label' style='margin-top:1.5rem'>Current Mode of Operations</div>", unsafe_allow_html=True)
                st.plotly_chart(render_cmo(st.session_state.vis_cmo), use_container_width=True)
            if st.session_state.vis_fmo:
                st.markdown("<div class='section-label' style='margin-top:1rem'>Future Mode of Operations</div>", unsafe_allow_html=True)
                st.plotly_chart(render_fmo(st.session_state.vis_fmo), use_container_width=True)
            if st.session_state.vis_threat:
                st.markdown("<div class='section-label' style='margin-top:1rem'>Threat Coverage Matrix</div>", unsafe_allow_html=True)
                st.plotly_chart(render_threat_coverage(st.session_state.vis_threat), use_container_width=True)
            if st.session_state.vis_traceability:
                st.markdown("<div class='section-label' style='margin-top:1rem'>Requirements Traceability Matrix</div>", unsafe_allow_html=True)
                st.plotly_chart(render_requirements_traceability(st.session_state.vis_traceability), use_container_width=True)
            if st.session_state.vis_vendor:
                st.markdown("<div class='section-label' style='margin-top:1rem'>Vendor Positioning Map</div>", unsafe_allow_html=True)
                st.plotly_chart(render_vendor_positioning(st.session_state.vis_vendor), use_container_width=True)

    # Chat tab
    with tab9:
        st.markdown("<div class='section-label'>Interactive RFP Intelligence</div>", unsafe_allow_html=True)
        for i in range(0, len(st.session_state.chat_history), 2):
            if i < len(st.session_state.chat_history):
                st.markdown(f"<div class='chat-bubble-user'><div class='chat-who user'>You</div>{st.session_state.chat_history[i]}</div>", unsafe_allow_html=True)
            if i+1 < len(st.session_state.chat_history):
                st.markdown(f"<div class='chat-bubble-ai'><div class='chat-who ai'>AI Consultant</div>{st.session_state.chat_history[i+1]}</div>", unsafe_allow_html=True)
        if not st.session_state.chat_history:
            st.markdown("<div style='color:#5c6480;font-size:0.72rem;margin-bottom:0.8rem;text-transform:uppercase;font-weight:600;letter-spacing:0.08em'>Suggested Questions</div>", unsafe_allow_html=True)
            suggestions = ["What is the total contract value and commercial model?","What are the mandatory vs preferred requirements?","What is the implementation timeline and key milestones?","Which compliance frameworks are mandatory?","What support model is required?","What makes this deal strategically important?"]
            cols = st.columns(2)
            for idx, sug in enumerate(suggestions):
                with cols[idx%2]:
                    if st.button(sug, key=f"sug_{idx}", use_container_width=True):
                        with st.spinner("Analyzing..."):
                            answer = chat_with_rfp(st.session_state.rfp_text, sug, st.session_state.chat_history)
                            st.session_state.chat_history.extend([sug, answer])
                            st.rerun()
        st.markdown("<br>", unsafe_allow_html=True)
        user_q = st.text_input("Ask anything about this RFP...", placeholder="e.g. What are the data residency requirements?", key="chat_input")
        c1,c2 = st.columns([5,1])
        with c2:
            if st.button("Send →", key="btn_send", use_container_width=True) and user_q:
                with st.spinner("Analyzing..."):
                    answer = chat_with_rfp(st.session_state.rfp_text, user_q, st.session_state.chat_history)
                    st.session_state.chat_history.extend([user_q, answer])
                    st.rerun()
        if st.session_state.chat_history:
            if st.button("Clear Chat", key="btn_clearchat"):
                st.session_state.chat_history = []
                st.rerun()
