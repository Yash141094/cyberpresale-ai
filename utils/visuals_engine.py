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
    """Extract current environment data for CMO diagram"""
    client = get_client()
    prompt = f"""Analyze this RFP and extract the customer's CURRENT environment (before the new solution).

Respond ONLY with valid JSON:
{{
  "org_name": "Organization name",
  "industry": "Industry vertical",
  "layers": [
    {{
      "name": "Users & Devices",
      "items": ["8500 Windows endpoints", "1200 Linux servers"],
      "issues": ["No EDR", "Unmanaged devices"],
      "color": "red"
    }},
    {{
      "name": "Network",
      "items": ["Legacy firewalls", "No IDS/IPS"],
      "issues": ["Flat network", "No microsegmentation"],
      "color": "orange"
    }},
    {{
      "name": "Identity & Access",
      "items": ["Active Directory", "Basic MFA"],
      "issues": ["No PAM", "Weak privileged access"],
      "color": "red"
    }},
    {{
      "name": "Cloud",
      "items": ["AWS workloads", "Azure M365"],
      "issues": ["No CSPM", "Unmonitored"],
      "color": "orange"
    }},
    {{
      "name": "Security Operations",
      "items": ["Basic SIEM", "Manual incident response"],
      "issues": ["No SOAR", "Slow detection"],
      "color": "red"
    }},
    {{
      "name": "Compliance & GRC",
      "items": ["Manual audits", "Spreadsheet tracking"],
      "issues": ["RBI gaps", "PCI-DSS gaps"],
      "color": "red"
    }}
  ],
  "key_gaps": ["No unified visibility", "Manual processes", "Compliance risk", "No threat hunting"],
  "risk_level": "High"
}}

RFP: {truncate(rfp_text)}

Infer current state from what they are ASKING FOR — if they want EDR, they likely don't have one. Be specific."""

    content = call_llm(client, [{"role": "user", "content": prompt}], max_tokens=1200, temperature=0.1).strip()
    if "```json" in content: content = content.split("```json")[1].split("```")[0].strip()
    elif "```" in content: content = content.split("```")[1].split("```")[0].strip()
    start, end = content.find("{"), content.rfind("}") + 1
    if start != -1 and end > start: content = content[start:end]
    try:
        return json.loads(content)
    except:
        return {"org_name": "Customer", "industry": "Enterprise", "layers": [
            {"name": "Users & Devices", "items": ["Mixed endpoints"], "issues": ["No EDR"], "color": "red"},
            {"name": "Network", "items": ["Legacy infrastructure"], "issues": ["Limited visibility"], "color": "orange"},
            {"name": "Identity & Access", "items": ["Active Directory"], "issues": ["No PAM"], "color": "red"},
            {"name": "Cloud", "items": ["Cloud workloads"], "issues": ["No CSPM"], "color": "orange"},
            {"name": "Security Operations", "items": ["Basic monitoring"], "issues": ["No SOAR"], "color": "red"},
            {"name": "Compliance & GRC", "items": ["Manual processes"], "issues": ["Compliance gaps"], "color": "red"},
        ], "key_gaps": ["Limited visibility", "Manual processes", "Compliance risk"],
        "risk_level": "High"}


def extract_fmo_data(rfp_text):
    """Extract future state data for FMO diagram"""
    client = get_client()
    prompt = f"""Analyze this RFP and extract the FUTURE state — the proposed integrated security architecture.

Respond ONLY with valid JSON:
{{
  "architecture_name": "Integrated Security Platform",
  "layers": [
    {{
      "name": "Users & Devices",
      "solutions": ["CrowdStrike Falcon EDR", "Device Control", "MDR 24x7"],
      "capabilities": ["Real-time threat detection", "Auto-isolation", "Threat hunting"],
      "color": "green",
      "vendor": "CrowdStrike / SentinelOne"
    }},
    {{
      "name": "Network Security",
      "solutions": ["Palo Alto NGFW", "IDS/IPS", "WAF"],
      "capabilities": ["Deep packet inspection", "Microsegmentation", "DDoS protection"],
      "color": "green",
      "vendor": "Palo Alto Networks"
    }},
    {{
      "name": "Identity & Zero Trust",
      "solutions": ["Okta Identity Cloud", "CyberArk PAM", "MFA"],
      "capabilities": ["Zero standing privileges", "JIT access", "Session recording"],
      "color": "green",
      "vendor": "Okta / CyberArk"
    }},
    {{
      "name": "Cloud Security",
      "solutions": ["Prisma Cloud CSPM", "CWPP", "CNAPP"],
      "capabilities": ["Posture management", "Container security", "API protection"],
      "color": "green",
      "vendor": "Palo Alto Prisma"
    }},
    {{
      "name": "Security Operations",
      "solutions": ["Microsoft Sentinel SIEM", "SOAR", "UEBA"],
      "capabilities": ["50K EPS ingestion", "Automated response", "Threat intelligence"],
      "color": "green",
      "vendor": "Microsoft / Splunk"
    }},
    {{
      "name": "Compliance & GRC",
      "solutions": ["GRC Platform", "Automated audit", "Risk management"],
      "capabilities": ["RBI/SEBI compliance", "Auto-evidence collection", "Vendor risk"],
      "color": "green",
      "vendor": "ServiceNow / Archer"
    }}
  ],
  "integration_layer": "Unified Security Data Lake + SOAR Orchestration",
  "key_outcomes": ["90% faster detection", "Automated compliance", "Unified visibility", "Zero Trust achieved"],
  "maturity_target": "Optimized"
}}

RFP: {truncate(rfp_text)}

Base recommendations on actual RFP requirements. Be specific about vendors."""

    content = call_llm(client, [{"role": "user", "content": prompt}], max_tokens=1500, temperature=0.2).strip()
    if "```json" in content: content = content.split("```json")[1].split("```")[0].strip()
    elif "```" in content: content = content.split("```")[1].split("```")[0].strip()
    start, end = content.find("{"), content.rfind("}") + 1
    if start != -1 and end > start: content = content[start:end]
    try:
        return json.loads(content)
    except:
        return {"architecture_name": "Integrated Security Platform",
        "layers": [
            {"name": "Users & Devices", "solutions": ["EDR/XDR Platform"], "capabilities": ["Real-time protection"], "color": "green", "vendor": "CrowdStrike"},
            {"name": "Network Security", "solutions": ["NGFW + IDS/IPS"], "capabilities": ["Deep inspection"], "color": "green", "vendor": "Palo Alto"},
            {"name": "Identity & Zero Trust", "solutions": ["IAM + PAM"], "capabilities": ["Zero Trust"], "color": "green", "vendor": "Okta/CyberArk"},
            {"name": "Cloud Security", "solutions": ["CNAPP Platform"], "capabilities": ["Posture management"], "color": "green", "vendor": "Prisma Cloud"},
            {"name": "Security Operations", "solutions": ["SIEM + SOAR"], "capabilities": ["Automated response"], "color": "green", "vendor": "Microsoft Sentinel"},
            {"name": "Compliance & GRC", "solutions": ["GRC Platform"], "capabilities": ["Auto compliance"], "color": "green", "vendor": "ServiceNow"},
        ],
        "integration_layer": "Unified Security Fabric",
        "key_outcomes": ["Faster detection", "Automated compliance", "Zero Trust"],
        "maturity_target": "Optimized"}


def extract_threat_coverage(rfp_text):
    """Extract threat vs solution coverage matrix"""
    client = get_client()
    prompt = f"""You are a senior cybersecurity architect. Read this RFP carefully and build a realistic threat coverage matrix based ONLY on what this specific customer needs.

STEP 1 - Identify the top 6-8 threats most relevant to THIS customer based on their industry, size, and requirements mentioned in the RFP.

STEP 2 - Identify 5-6 solution categories they need based on the RFP domains.

STEP 3 - Score each threat vs solution honestly:
- 0 = This solution does NOT address this threat
- 1 = Partial coverage only
- 2 = Good coverage
- 3 = Strong, primary coverage

Be realistic — most cells should be 0 or 1. Only assign 2 or 3 when there is a genuine strong relationship between that solution and that threat.

Respond ONLY with valid JSON, no explanation, no markdown:
{{
  "threats": ["Threat 1", "Threat 2", "Threat 3", "Threat 4", "Threat 5", "Threat 6", "Threat 7", "Threat 8"],
  "solutions": ["Solution 1", "Solution 2", "Solution 3", "Solution 4", "Solution 5", "Solution 6"],
  "coverage": {{
    "Threat 1": [0, 1, 2, 3, 0, 1],
    "Threat 2": [3, 2, 0, 1, 2, 0]
  }}
}}

Each coverage array must have exactly the same number of values as solutions.
Threat names: keep short, max 4 words.
Solution names: use standard names like SIEM/SOC, EDR/XDR, Zero Trust/IAM, Cloud Security, Network Security, GRC/Compliance, PAM, Threat Intel.

RFP: {truncate(rfp_text, 5000)}"""

    content = call_llm(client, [{"role": "user", "content": prompt}], max_tokens=1000, temperature=0.1).strip()
    if "```json" in content: content = content.split("```json")[1].split("```")[0].strip()
    elif "```" in content: content = content.split("```")[1].split("```")[0].strip()
    start, end = content.find("{"), content.rfind("}") + 1
    if start != -1 and end > start: content = content[start:end]
    try:
        return json.loads(content)
    except:
        return {
            "threats": ["Ransomware","APT","Insider Threat","Phishing","Cloud Misconfig","Privilege Abuse","DDoS","Data Exfiltration"],
            "solutions": ["SIEM/SOC","EDR/XDR","Zero Trust","Cloud Security","Network Security","GRC"],
            "coverage": {
                "Ransomware": [2,3,1,0,2,0],
                "APT": [3,3,2,1,2,0],
                "Insider Threat": [3,2,3,1,1,2],
                "Phishing": [2,2,3,1,1,1],
                "Cloud Misconfig": [2,1,1,3,1,2],
                "Privilege Abuse": [3,2,3,1,1,1],
                "DDoS": [1,0,0,1,3,0],
                "Data Exfiltration": [3,2,2,3,2,1],
            }
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
