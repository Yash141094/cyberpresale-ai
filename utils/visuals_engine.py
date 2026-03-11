"""
Visuals Engine for CyberPresales AI
AI extracts structured data → Python renders beautiful charts and diagrams
"""
import json
import os
import time
from openai import OpenAI

def get_client():
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError("Groq API key not set")
    return OpenAI(api_key=api_key, base_url="https://api.groq.com/openai/v1")

MODEL = "llama-3.3-70b-versatile"

def truncate(text, max_chars=8000):
    return text[:max_chars] if len(text) > max_chars else text

def call_llm(client, messages, max_tokens=1000, temperature=0.1):
    max_retries = 4
    wait_times  = [10, 20, 40, 60]
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
            )
            return response.choices[0].message.content
        except Exception as e:
            err = str(e).lower()
            is_rate_limit = "rate" in err or "429" in err or "limit" in err or "quota" in err
            if is_rate_limit and attempt < max_retries - 1:
                time.sleep(wait_times[attempt])
                continue
            raise

def extract_cmo_data(rfp_text):
    """Extract CMO as structured requirements table — works for any RFP type."""
    client = get_client()

    # Detect RFP type first
    type_prompt = """Read this RFP and extract in JSON only:
{"rfp_type": "Cybersecurity|Infrastructure|Application Managed Services|End User Computing|Digital Workplace|Data & Analytics|Multi-Tower|Other",
 "primary_domains": ["domain1","domain2","domain3"],
 "consultant_persona": "type of expert e.g. Infrastructure Solutions Architect"}
RFP: """ + rfp_text[:3000]
    raw = call_llm(client, [{"role":"user","content":type_prompt}], max_tokens=300, temperature=0.1).strip()
    if "```json" in raw: raw = raw.split("```json")[1].split("```")[0].strip()
    elif "```" in raw: raw = raw.split("```")[1].split("```")[0].strip()
    s,e = raw.find("{"), raw.rfind("}")+1
    try:    meta = json.loads(raw[s:e]) if s!=-1 and e>s else {}
    except: meta = {}
    rfp_type = meta.get("rfp_type","IT Services")
    persona  = meta.get("consultant_persona","Senior Solutions Architect")
    domains  = ", ".join(meta.get("primary_domains",[]))

    prompt = f"""You are a {persona}. Read this {rfp_type} RFP and extract the customer's CURRENT state as a detailed service requirements table.

This is a {rfp_type} RFP covering: {domains}

Respond ONLY with valid JSON, no explanation:
{{
  "org_name": "Organization name",
  "industry": "Industry sector",
  "rfp_type": "{rfp_type}",
  "rows": [
    {{
      "requirement": "Parent service domain from RFP",
      "sub_requirement": "Specific measurable deliverable",
      "current_tool": "Current product/tool/platform in use or None",
      "licence_owner": "Customer|Supplier|Shared|None",
      "support_hours": "8x5|12x5|24x5|24x7|P1 On-Call|Business Hours",
      "timezone": "IST|GMT|EST|Multi-region|Follow-the-Sun|As per RFP",
      "vm_frequency": "Continuous|Weekly|Monthly|Quarterly|Ad-hoc",
      "requirement_brief": "1-2 sentences: what RFP asks for AND current gap"
    }}
  ]
}}

RULES:
- Requirement domains must come from the ACTUAL RFP — not generic IT domains
- For {rfp_type}: use appropriate domain names e.g.
  * Infrastructure: DC Operations, Cloud Management, Network Operations, Storage Management
  * App Managed Services: L1/L2/L3 Application Support, Release Management, Incident Management
  * End User Computing: Service Desk, Desktop Support, Device Management, M365 Administration
  * Cybersecurity: SOC Operations, EDR Management, Identity & Access, Cloud Security
  * Multi-Tower: use whatever towers the RFP specifies
- current_tool: name actual tools if mentioned (ServiceNow, Jira, SAP, VMware, etc.)
- support_hours/timezone: infer from SLA requirements in the RFP
- vm_frequency: service review cadence — for infra/apps use patch/review frequency
- Extract 12-18 rows. 2-3 sub-requirements per domain.

RFP:
""" + truncate(rfp_text)

    content_raw = call_llm(client, [{"role":"user","content":prompt}], max_tokens=3500, temperature=0.1).strip()
    if "```json" in content_raw: content_raw = content_raw.split("```json")[1].split("```")[0].strip()
    elif "```" in content_raw: content_raw = content_raw.split("```")[1].split("```")[0].strip()
    s,e = content_raw.find("{"), content_raw.rfind("}")+1
    if s!=-1 and e>s: content_raw = content_raw[s:e]
    try:
        return json.loads(content_raw)
    except:
        return {"org_name":"Customer","industry":"Enterprise","rfp_type":rfp_type,"rows":[
            {"requirement":"Service Operations","sub_requirement":"Incident management and resolution","current_tool":"Unknown","licence_owner":"None","support_hours":"8x5","timezone":"IST","vm_frequency":"Monthly","requirement_brief":"RFP requires structured incident management with defined SLAs."},
            {"requirement":"Service Operations","sub_requirement":"24x7 monitoring and alerting","current_tool":"None","licence_owner":"None","support_hours":"24x7","timezone":"Multi-region","vm_frequency":"Weekly","requirement_brief":"No active monitoring. RFP mandates round-the-clock coverage."},
        ]}



def extract_fmo_data(solution_rec_text):
    """Extract FMO as structured recommendations table — domain agnostic."""
    client = get_client()

    prompt = """You are a senior solutions architect. Read this solution recommendation and structure it as a formal Future Mode of Operations table.

The solution recommendation may cover any IT domain — Infrastructure, Applications, End User Computing, Cybersecurity, or multi-tower. Extract whatever domains are covered.

Respond ONLY with valid JSON:
{
  "architecture_name": "Proposed solution/platform name",
  "rfp_type": "type of RFP this covers",
  "rows": [
    {
      "requirement": "Parent service domain",
      "sub_requirement": "Specific deliverable",
      "recommended_solution": "Specific product or service name",
      "vendor": "Vendor name",
      "support_model": "8x5 Business Hours|24x7 NOC/SOC|24x7 + P1 On-Call|Managed Service|Self-Managed",
      "timezone_coverage": "IST Business Hours|Follow-the-Sun (IST+GMT+EST)|Global 24x7|APAC+EMEA",
      "vm_frequency": "Continuous|Weekly|Monthly|Quarterly",
      "fit_rationale": "1 sentence: why this specific solution for this customer"
    }
  ],
  "key_outcomes": ["outcome 1", "outcome 2", "outcome 3"],
  "integration_note": "How the components integrate"
}

RULES:
- Mirror the CMO requirement structure where possible
- Use specific product/vendor names (ServiceNow, SAP, VMware, AWS, Azure, etc.)
- support_model and timezone_coverage must reflect the actual SLAs proposed
- Extract 12-18 rows covering all domains in the recommendation
- fit_rationale must be specific — why THIS solution for THIS customer

Solution Recommendation:
""" + truncate(solution_rec_text, 6000)

    content_raw = call_llm(client, [{"role":"user","content":prompt}], max_tokens=3500, temperature=0.1).strip()
    if "```json" in content_raw: content_raw = content_raw.split("```json")[1].split("```")[0].strip()
    elif "```" in content_raw: content_raw = content_raw.split("```")[1].split("```")[0].strip()
    s,e = content_raw.find("{"), content_raw.rfind("}")+1
    if s!=-1 and e>s: content_raw = content_raw[s:e]
    try:
        return json.loads(content_raw)
    except:
        return {"architecture_name":"Integrated Managed Services Platform","rfp_type":"IT Services","rows":[
            {"requirement":"Service Operations","sub_requirement":"Incident management","recommended_solution":"ServiceNow ITSM","vendor":"ServiceNow","support_model":"24x7 Managed Service","timezone_coverage":"Follow-the-Sun","vm_frequency":"Continuous","fit_rationale":"Industry-standard ITSM with proven integration capabilities."},
        ],"key_outcomes":["Improved SLA adherence","Reduced operational cost","Enhanced user experience"],"integration_note":"Unified service management platform with API integrations."}



def extract_threat_coverage(rfp_text):
    """Coverage matrix — works for security (threats) or non-security (service areas vs capabilities)."""
    client = get_client()

    # Detect RFP type
    type_prompt = """Read this RFP and return JSON only: {"rfp_type": "Cybersecurity|Infrastructure|Application Managed Services|End User Computing|Multi-Tower|Other", "is_security": true_or_false}
RFP: """ + rfp_text[:2000]
    raw = call_llm(client, [{"role":"user","content":type_prompt}], max_tokens=150, temperature=0.1).strip()
    if "```json" in raw: raw = raw.split("```json")[1].split("```")[0].strip()
    elif "```" in raw: raw = raw.split("```")[1].split("```")[0].strip()
    s,e = raw.find("{"), raw.rfind("}")+1
    try:    meta = json.loads(raw[s:e]) if s!=-1 and e>s else {}
    except: meta = {}
    is_security = meta.get("is_security", True)
    rfp_type    = meta.get("rfp_type", "IT Services")

    if is_security:
        # Security RFP — threats vs solutions matrix
        step1 = """Read this RFP and extract ONLY:
{"threats": ["specific threat types relevant to this customer - max 8, short names"],
 "solutions": ["solution categories being procured - max 6"]}
Be specific to this customer industry and geography. Do not use generic lists.
RFP: """ + rfp_text[:5000]
        raw2 = call_llm(client, [{"role":"user","content":step1}], max_tokens=400, temperature=0.1).strip()
        if "```json" in raw2: raw2 = raw2.split("```json")[1].split("```")[0].strip()
        elif "```" in raw2: raw2 = raw2.split("```")[1].split("```")[0].strip()
        s,e = raw2.find("{"), raw2.rfind("}")+1
        try:
            sig = json.loads(raw2[s:e]) if s!=-1 and e>s else {}
            rows    = sig.get("threats",   ["Ransomware","APT","Insider Threat","Phishing","Cloud Misconfig","DDoS","Data Exfiltration","Privilege Abuse"])
            columns = sig.get("solutions", ["SIEM/SOC","EDR/XDR","Zero Trust/IAM","Cloud Security","Network Security","GRC"])
        except:
            rows    = ["Ransomware","APT","Insider Threat","Phishing","Cloud Misconfig","DDoS","Data Exfiltration","Privilege Abuse"]
            columns = ["SIEM/SOC","EDR/XDR","Zero Trust/IAM","Cloud Security","Network Security","GRC"]
        row_label   = "Threat / Attack Vector"
        score_guide = "0=No coverage, 1=Partial/indirect, 2=Good coverage, 3=Strong/primary. Most cells should be 0 or 1."
    else:
        # Non-security RFP — service areas vs capabilities matrix
        step1 = f"""Read this {rfp_type} RFP and extract:
{{"service_areas": ["top 6-8 service areas or requirements from the RFP - short names"],
  "capabilities": ["top 5-6 capabilities or solution components being proposed - short names"]}}
Examples for Infrastructure: service_areas=[DC Operations, Network Mgmt, Cloud Migration, Storage, Backup, Monitoring], capabilities=[Automation, Observability, ITSM Integration, Self-Healing, Reporting, Compliance]
Examples for AMS: service_areas=[L1 Support, L2 Support, L3 Engineering, Release Mgmt, Testing, Documentation], capabilities=[ServiceNow, JIRA, CI/CD, Monitoring, SLA Reporting, Knowledge Base]
RFP: """ + rfp_text[:5000]
        raw2 = call_llm(client, [{"role":"user","content":step1}], max_tokens=400, temperature=0.1).strip()
        if "```json" in raw2: raw2 = raw2.split("```json")[1].split("```")[0].strip()
        elif "```" in raw2: raw2 = raw2.split("```")[1].split("```")[0].strip()
        s,e = raw2.find("{"), raw2.rfind("}")+1
        try:
            sig = json.loads(raw2[s:e]) if s!=-1 and e>s else {}
            rows    = sig.get("service_areas", ["Service Desk","Desktop Support","Application Support","Infrastructure","Network","Cloud"])
            columns = sig.get("capabilities",  ["Automation","ITSM Platform","Monitoring","Reporting","Self-Service","Compliance"])
        except:
            rows    = ["Service Desk","Desktop Support","Application Support","Infrastructure","Network","Cloud"]
            columns = ["Automation","ITSM Platform","Monitoring","Reporting","Self-Service","Compliance"]
        row_label   = "Service Area / Requirement"
        score_guide = "0=Not addressed, 1=Partially addressed, 2=Well addressed, 3=Fully covered as primary capability."

    # Score matrix
    matrix_prompt = f"""Score this matrix for a {rfp_type} RFP.

Rows: {rows}
Columns: {columns}
{score_guide}

Respond ONLY with valid JSON:
{{
  "threats": {rows},
  "solutions": {columns},
  "coverage": {{
    "Row Name": [score_per_column_in_order]
  }}
}}

Each coverage array must have exactly {len(columns)} values. Be realistic and specific to this RFP.

RFP context: {rfp_text[:2000]}"""

    raw3 = call_llm(client, [{"role":"user","content":matrix_prompt}], max_tokens=800, temperature=0.1).strip()
    if "```json" in raw3: raw3 = raw3.split("```json")[1].split("```")[0].strip()
    elif "```" in raw3: raw3 = raw3.split("```")[1].split("```")[0].strip()
    s,e = raw3.find("{"), raw3.rfind("}")+1
    if s!=-1 and e>s: raw3 = raw3[s:e]
    try:
        result = json.loads(raw3)
        result["row_label"] = row_label
        return result
    except:
        return {
            "threats": rows,
            "solutions": columns,
            "coverage": {r: [1]*len(columns) for r in rows},
            "row_label": row_label
        }



def extract_requirements_traceability(rfp_text):
    """Map every RFP requirement to a solution"""
    client = get_client()
    prompt = f"""Create a requirements traceability matrix from this RFP.

Respond ONLY with valid JSON:
{{
  "requirements": [
    {{
      "id": "REQ-01",
      "domain": "SIEM/SOC",
      "requirement": "Real-time log ingestion from 5000+ endpoints",
      "priority": "Mandatory",
      "proposed_solution": "Microsoft Sentinel / Splunk ES",
      "capability": "50K EPS ingestion with cloud-native scaling",
      "coverage": "Full",
      "notes": "Native connectors for all mentioned log sources"
    }}
  ]
}}

Coverage values: "Full", "Partial", "Gap"
Priority values: "Mandatory", "Preferred", "Optional"

Extract 15-20 key requirements from the RFP, one per major requirement.
RFP: {truncate(rfp_text)}"""

    content = call_llm(client, [{"role": "user", "content": prompt}], max_tokens=2000, temperature=0.1).strip()
    if "```json" in content: content = content.split("```json")[1].split("```")[0].strip()
    elif "```" in content: content = content.split("```")[1].split("```")[0].strip()
    start, end = content.find("{"), content.rfind("}") + 1
    if start != -1 and end > start: content = content[start:end]
    try:
        return json.loads(content)
    except:
        return {"requirements": [
            {"id":"REQ-01","domain":"SIEM/SOC","requirement":"Real-time log ingestion","priority":"Mandatory","proposed_solution":"Microsoft Sentinel","capability":"50K EPS ingestion","coverage":"Full","notes":"Cloud-native scaling"},
            {"id":"REQ-02","domain":"EDR","requirement":"Ransomware auto-isolation","priority":"Mandatory","proposed_solution":"CrowdStrike Falcon","capability":"30-second automated response","coverage":"Full","notes":"Proven in BFSI sector"},
        ]}


def extract_vendor_positioning(rfp_text):
    """Vendor landscape quadrant — domain agnostic."""
    client = get_client()

    # Detect RFP type to get relevant vendor landscape
    type_prompt = """Read this RFP. Return JSON only:
{"rfp_type": "Cybersecurity|Infrastructure Services|Application Managed Services|End User Computing|Digital Workplace|Data & Analytics|Multi-Tower|Other",
 "primary_domains": ["domain1","domain2"],
 "relevant_vendors": ["list 6-8 vendors most relevant to THIS specific RFP type and domains"]}
RFP: """ + rfp_text[:3000]
    raw = call_llm(client, [{"role":"user","content":type_prompt}], max_tokens=300, temperature=0.1).strip()
    if "```json" in raw: raw = raw.split("```json")[1].split("```")[0].strip()
    elif "```" in raw: raw = raw.split("```")[1].split("```")[0].strip()
    s, e = raw.find("{"), raw.rfind("}")+1
    try:    meta = json.loads(raw[s:e]) if s!=-1 and e>s else {}
    except: meta = {}
    rfp_type = meta.get("rfp_type","IT Services")
    vendors  = meta.get("relevant_vendors",[])
    domains  = ", ".join(meta.get("primary_domains",[]))

    prompt = f"""You are a senior {rfp_type} analyst. Position the top vendors for this specific RFP on two axes:
- X axis: Completeness of Solution (0-10) — how well they cover ALL requirements in this RFP
- Y axis: Ease of Implementation (0-10) — how easy to deploy/onboard for THIS customer

RFP Type: {rfp_type}
Primary Domains: {domains}
Vendors to consider (adjust based on RFP): {vendors}

Respond ONLY with valid JSON:
{{
  "vendors": [
    {{"name": "Vendor Name", "completeness": 8.5, "ease": 7.0, "quadrant": "Leader|Challenger|Niche|Caution", "key_strength": "specific strength for this RFP", "key_risk": "specific concern for this customer"}}
  ],
  "recommended_vendor": "Name of top recommendation",
  "rationale": "1-2 sentences explaining why, tied to this RFP's specific requirements"
}}

Quadrant rules: Leader = high completeness + high ease, Challenger = high completeness + lower ease OR vice versa, Niche = specialised but not complete, Caution = concerns.

Position 6-8 vendors. Scores must reflect THIS RFP's requirements — not generic market position.

Vendor reference by type:
- Infrastructure: Cisco, HPE, Dell Technologies, VMware (Broadcom), NetApp, IBM, HCL, Wipro
- AMS / Application: SAP, Oracle, ServiceNow, IBM, Infosys, TCS, Wipro, HCL, Accenture, Capgemini
- EUC / Helpdesk: ServiceNow, Nexthink, Citrix, Ivanti, Microsoft, HCL, DXC, Unisys
- Cybersecurity: Palo Alto Networks, Microsoft Security, CrowdStrike, SentinelOne, IBM QRadar, Splunk, Fortinet, Zscaler
- Multi-Tower: TCS, Infosys, Wipro, HCL, IBM, Accenture, Capgemini, DXC Technology

Only use vendors relevant to THIS RFP type. Do not include security vendors for an infra RFP.

RFP: {truncate(rfp_text, 4000)}"""

    raw2 = call_llm(client, [{"role":"user","content":prompt}], max_tokens=1200, temperature=0.2).strip()
    if "```json" in raw2: raw2 = raw2.split("```json")[1].split("```")[0].strip()
    elif "```" in raw2: raw2 = raw2.split("```")[1].split("```")[0].strip()
    s, e = raw2.find("{"), raw2.rfind("}")+1
    if s!=-1 and e>s: raw2 = raw2[s:e]
    try:
        return json.loads(raw2)
    except:
        # Fallback vendors based on detected type
        fallback_map = {
            "Infrastructure Services": [
                {"name":"HPE","completeness":8.5,"ease":7.0,"quadrant":"Leader","key_strength":"Full infrastructure stack","key_risk":"Premium pricing"},
                {"name":"Dell Technologies","completeness":8.0,"ease":7.5,"quadrant":"Leader","key_strength":"Strong storage and compute","key_risk":"Services capability varies"},
                {"name":"Cisco","completeness":7.5,"ease":7.0,"quadrant":"Challenger","key_strength":"Network leadership","key_risk":"Multi-domain coverage gaps"},
                {"name":"IBM","completeness":7.0,"ease":6.0,"quadrant":"Challenger","key_strength":"Managed services depth","key_risk":"Cost and complexity"},
                {"name":"HCL","completeness":7.0,"ease":8.0,"quadrant":"Challenger","key_strength":"Cost-effective delivery","key_risk":"Premium tool depth"},
            ],
            "Application Managed Services": [
                {"name":"TCS","completeness":9.0,"ease":7.5,"quadrant":"Leader","key_strength":"Broadest AMS coverage","key_risk":"Large team, slower agility"},
                {"name":"Infosys","completeness":8.5,"ease":7.5,"quadrant":"Leader","key_strength":"Digital and AI-led AMS","key_risk":"Premium for smaller deals"},
                {"name":"Wipro","completeness":8.0,"ease":8.0,"quadrant":"Leader","key_strength":"Strong delivery model","key_risk":"Niche platform depth"},
                {"name":"IBM","completeness":7.5,"ease":6.5,"quadrant":"Challenger","key_strength":"SAP and Oracle expertise","key_risk":"Cost structure"},
                {"name":"HCL","completeness":7.5,"ease":8.0,"quadrant":"Challenger","key_strength":"Competitive pricing","key_risk":"Innovation perception"},
            ],
            "End User Computing": [
                {"name":"ServiceNow","completeness":8.5,"ease":7.5,"quadrant":"Leader","key_strength":"ITSM + EUC integration","key_risk":"Licensing cost"},
                {"name":"DXC Technology","completeness":8.0,"ease":7.5,"quadrant":"Leader","key_strength":"End-to-end EUC managed service","key_risk":"Transformation speed"},
                {"name":"HCL","completeness":7.5,"ease":8.0,"quadrant":"Challenger","key_strength":"Cost-effective helpdesk","key_risk":"Tool depth"},
                {"name":"Unisys","completeness":7.5,"ease":7.0,"quadrant":"Challenger","key_strength":"Strong EUC heritage","key_risk":"Market perception"},
                {"name":"Nexthink","completeness":6.5,"ease":8.5,"quadrant":"Niche","key_strength":"DEX analytics","key_risk":"Point solution only"},
            ],
            "Cybersecurity": [
                {"name":"Palo Alto Networks","completeness":9.2,"ease":7.5,"quadrant":"Leader","key_strength":"Most complete platform","key_risk":"Premium pricing"},
                {"name":"Microsoft Security","completeness":8.5,"ease":9.0,"quadrant":"Leader","key_strength":"M365 integration","key_risk":"Best-of-breed gaps"},
                {"name":"CrowdStrike","completeness":7.5,"ease":8.5,"quadrant":"Challenger","key_strength":"Best EDR/XDR","key_risk":"SIEM still maturing"},
                {"name":"IBM QRadar","completeness":7.5,"ease":6.0,"quadrant":"Challenger","key_strength":"BFSI SIEM depth","key_risk":"Legacy perception"},
                {"name":"Splunk","completeness":7.0,"ease":6.5,"quadrant":"Challenger","key_strength":"Gold standard SIEM","key_risk":"High cost"},
            ],
        }
        vendors_fb = fallback_map.get(rfp_type, fallback_map["Cybersecurity"])
        return {"vendors": vendors_fb, "recommended_vendor": vendors_fb[0]["name"],
                "rationale": f"Best completeness and fit for this {rfp_type} RFP."}



def extract_requirements_traceability(rfp_text):
    """Map every RFP requirement to a solution"""
    client = get_client()
    prompt = f"""Create a requirements traceability matrix from this RFP.

Respond ONLY with valid JSON:
{{
  "requirements": [
    {{
      "id": "REQ-01",
      "domain": "SIEM/SOC",
      "requirement": "Real-time log ingestion from 5000+ endpoints",
      "priority": "Mandatory",
      "proposed_solution": "Microsoft Sentinel / Splunk ES",
      "capability": "50K EPS ingestion with cloud-native scaling",
      "coverage": "Full",
      "notes": "Native connectors for all mentioned log sources"
    }}
  ]
}}

Coverage values: "Full", "Partial", "Gap"
Priority values: "Mandatory", "Preferred", "Optional"

Extract 15-20 key requirements from the RFP, one per major requirement.
RFP: {truncate(rfp_text)}"""

    content = call_llm(client, [{"role": "user", "content": prompt}], max_tokens=2000, temperature=0.1).strip()
    if "```json" in content: content = content.split("```json")[1].split("```")[0].strip()
    elif "```" in content: content = content.split("```")[1].split("```")[0].strip()
    start, end = content.find("{"), content.rfind("}") + 1
    if start != -1 and end > start: content = content[start:end]
    try:
        return json.loads(content)
    except:
        return {"requirements": [
            {"id":"REQ-01","domain":"SIEM/SOC","requirement":"Real-time log ingestion","priority":"Mandatory","proposed_solution":"Microsoft Sentinel","capability":"50K EPS ingestion","coverage":"Full","notes":"Cloud-native scaling"},
            {"id":"REQ-02","domain":"EDR","requirement":"Ransomware auto-isolation","priority":"Mandatory","proposed_solution":"CrowdStrike Falcon","capability":"30-second automated response","coverage":"Full","notes":"Proven in BFSI sector"},
        ]}


def extract_vendor_positioning(rfp_text):
    """Generate vendor landscape positioning data"""
    client = get_client()
    prompt = f"""Based on this RFP, position the top cybersecurity vendors on two axes:
- X axis: Completeness of Solution (0-10, how well they cover ALL requirements)
- Y axis: Ease of Implementation (0-10, how easy to deploy for this customer)

Respond ONLY with valid JSON:
{{
  "vendors": [
    {{"name": "Palo Alto Networks", "completeness": 9.2, "ease": 7.5, "quadrant": "Leader", "key_strength": "Most complete platform, XSIAM covers SIEM+SOAR+EDR", "key_risk": "Premium pricing, complex deployment"}},
    {{"name": "Microsoft Security", "completeness": 8.5, "ease": 9.0, "quadrant": "Leader", "key_strength": "Deep M365 integration, best value for Microsoft shops", "key_risk": "Best-of-breed gaps vs specialists"}},
    {{"name": "CrowdStrike", "completeness": 7.5, "ease": 8.5, "quadrant": "Challenger", "key_strength": "Best EDR/XDR in market, Falcon platform expanding", "key_risk": "SIEM capabilities still maturing"}},
    {{"name": "Splunk", "completeness": 7.0, "ease": 6.5, "quadrant": "Challenger", "key_strength": "Gold standard SIEM, deepest analytics", "key_risk": "High cost, requires skilled team"}},
    {{"name": "IBM Security", "completeness": 7.5, "ease": 6.0, "quadrant": "Challenger", "key_strength": "QRadar Suite strong for BFSI, good India presence", "key_risk": "Legacy platform perception, slower innovation"}},
    {{"name": "SentinelOne", "completeness": 6.5, "ease": 8.0, "quadrant": "Niche", "key_strength": "AI-native EDR, autonomous response", "key_risk": "Limited SIEM/GRC coverage"}},
    {{"name": "Fortinet", "completeness": 7.0, "ease": 7.5, "quadrant": "Challenger", "key_strength": "Best network security + SD-WAN combo", "key_risk": "Security Fabric can be complex to manage"}},
    {{"name": "Zscaler", "completeness": 5.5, "ease": 8.5, "quadrant": "Niche", "key_strength": "Best Zero Trust Network Access", "key_risk": "Narrow focus, needs complementary solutions"}}
  ],
  "recommended_vendor": "Palo Alto Networks",
  "rationale": "Most complete coverage of all RFP requirements with XSIAM platform"
}}

Customize based on actual RFP requirements.
RFP: {truncate(rfp_text, 4000)}"""

    content = call_llm(client, [{"role": "user", "content": prompt}], max_tokens=1200, temperature=0.2).strip()
    if "```json" in content: content = content.split("```json")[1].split("```")[0].strip()
    elif "```" in content: content = content.split("```")[1].split("```")[0].strip()
    start, end = content.find("{"), content.rfind("}") + 1
    if start != -1 and end > start: content = content[start:end]
    try:
        return json.loads(content)
    except:
        return {"vendors": [
            {"name": "Palo Alto Networks", "completeness": 9.2, "ease": 7.5, "quadrant": "Leader", "key_strength": "Most complete platform", "key_risk": "Premium pricing"},
            {"name": "Microsoft Security", "completeness": 8.5, "ease": 9.0, "quadrant": "Leader", "key_strength": "Best M365 integration", "key_risk": "Best-of-breed gaps"},
            {"name": "CrowdStrike", "completeness": 7.5, "ease": 8.5, "quadrant": "Challenger", "key_strength": "Best EDR in market", "key_risk": "SIEM maturing"},
            {"name": "IBM Security", "completeness": 7.5, "ease": 6.0, "quadrant": "Challenger", "key_strength": "Strong BFSI presence", "key_risk": "Legacy perception"},
            {"name": "Splunk", "completeness": 7.0, "ease": 6.5, "quadrant": "Challenger", "key_strength": "Gold standard SIEM", "key_risk": "High cost"},
        ], "recommended_vendor": "Palo Alto Networks", "rationale": "Most complete platform coverage"}
