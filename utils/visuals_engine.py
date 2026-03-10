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
    """Extract CMO as structured requirements table with support/coverage terms from RFP."""
    client = get_client()
    prompt = """You are a senior cybersecurity managed services consultant working with global enterprise customers. Read this RFP carefully and extract the customer's CURRENT state as a detailed service requirements table.

Respond ONLY with valid JSON, no explanation, no markdown:
{
  "org_name": "Organization name from RFP",
  "industry": "Industry sector",
  "rows": [
    {
      "requirement": "SIEM / Security Operations",
      "sub_requirement": "Real-time log ingestion and correlation",
      "current_tool": "Splunk (basic license)",
      "licence_owner": "Customer",
      "support_hours": "8x5",
      "timezone": "IST",
      "vm_frequency": "Monthly",
      "requirement_brief": "Customer requires ingestion from 5000+ endpoints. Currently only collecting firewall logs with manual review."
    }
  ]
}

FIELD RULES:
requirement: Parent domain (SIEM/SOC, EDR/XDR, Identity & IAM, Cloud Security, Network Security, GRC/Compliance, PAM, Threat Intel, Vulnerability Management)
sub_requirement: Specific measurable deliverable within that domain
current_tool: Actual product name if inferable, else "Unknown" or "None"
licence_owner: Exactly one of "Customer", "Supplier", "Shared", "None"
support_hours: Infer from RFP SLAs — "8x5", "12x5", "24x5", "24x7", "P1 On-Call", "Business Hours". Default "8x5" if silent.
timezone: Infer from RFP — "IST", "GMT", "EST", "Multi-region", "Follow-the-Sun", "APAC+EMEA". Use "As per RFP" if unknown.
vm_frequency: Service review or vulnerability scan frequency — "Continuous", "Weekly", "Monthly", "Quarterly", "Ad-hoc". Infer from context.
requirement_brief: 1-2 sentences. What the RFP asks for AND what the current gap is.

Extract 12-18 rows. Each domain should have 2-3 sub-requirements. Be specific.

RFP:
""" + truncate(rfp_text)

    content_raw = call_llm(client, [{"role": "user", "content": prompt}], max_tokens=3500, temperature=0.1).strip()
    if "```json" in content_raw: content_raw = content_raw.split("```json")[1].split("```")[0].strip()
    elif "```" in content_raw: content_raw = content_raw.split("```")[1].split("```")[0].strip()
    start, end = content_raw.find("{"), content_raw.rfind("}") + 1
    if start != -1 and end > start: content_raw = content_raw[start:end]
    try:
        return json.loads(content_raw)
    except:
        return {"org_name": "Customer", "industry": "Enterprise", "rows": [
            {"requirement": "SIEM / SOC", "sub_requirement": "Log ingestion and correlation", "current_tool": "Unknown", "licence_owner": "None", "support_hours": "8x5", "timezone": "IST", "vm_frequency": "Monthly", "requirement_brief": "RFP requires centralized log management and real-time correlation across all environments."},
            {"requirement": "SIEM / SOC", "sub_requirement": "24x7 SOC monitoring", "current_tool": "None", "licence_owner": "None", "support_hours": "24x7", "timezone": "Multi-region", "vm_frequency": "Weekly", "requirement_brief": "No active SOC. RFP mandates continuous monitoring with P1 response SLA."},
            {"requirement": "Endpoint Security", "sub_requirement": "EDR agent deployment", "current_tool": "Legacy AV", "licence_owner": "Customer", "support_hours": "8x5", "timezone": "IST", "vm_frequency": "Quarterly", "requirement_brief": "Existing AV insufficient. EDR with behavioural detection and isolation required."},
            {"requirement": "Identity & Access", "sub_requirement": "Privileged access management", "current_tool": "None", "licence_owner": "None", "support_hours": "8x5", "timezone": "IST", "vm_frequency": "Quarterly", "requirement_brief": "No PAM in place. RFP mandates JIT access and session recording."},
        ]}


def extract_fmo_data(solution_rec_text):
    """Extract FMO as structured recommendations table from solution recommendation output."""
    client = get_client()
    prompt = """You are a senior cybersecurity architect. Read this solution recommendation and structure it as a formal Future Mode of Operations table for a global enterprise proposal.

Respond ONLY with valid JSON, no explanation, no markdown:
{
  "architecture_name": "Proposed architecture name",
  "rows": [
    {
      "requirement": "SIEM / Security Operations",
      "sub_requirement": "Real-time log ingestion and correlation",
      "recommended_solution": "Microsoft Sentinel",
      "vendor": "Microsoft",
      "support_model": "24x7 Managed SOC",
      "timezone_coverage": "Follow-the-Sun (IST + GMT + EST)",
      "vm_frequency": "Continuous",
      "fit_rationale": "Native Azure integration reduces deployment time by 60% and eliminates need for additional connectors."
    },
    {
      "requirement": "SIEM / Security Operations",
      "sub_requirement": "24x7 SOC monitoring and incident response",
      "recommended_solution": "Managed SOC via Sentinel + Defender XDR",
      "vendor": "Microsoft / MSSP",
      "support_model": "24x7 + P1 On-Call (15 min SLA)",
      "timezone_coverage": "Global (Follow-the-Sun)",
      "vm_frequency": "Weekly",
      "fit_rationale": "Unified XDR platform reduces analyst workload and enables automated Tier-1 response."
    }
  ],
  "key_outcomes": ["90% faster detection", "Automated compliance reporting", "Zero Trust achieved"],
  "integration_note": "All components integrated via unified security data lake and SOAR orchestration."
}

FIELD RULES:
requirement: Parent domain — must mirror the CMO requirement categories
sub_requirement: Specific deliverable — must mirror CMO sub-requirements where possible
recommended_solution: Specific product name (e.g. Microsoft Sentinel, CrowdStrike Falcon, Prisma Cloud CNAPP)
vendor: Vendor name only
support_model: Proposed service level — "8x5 Business Hours", "24x7 NOC/SOC", "24x7 + P1 On-Call", "Managed Service", "Self-Managed"
timezone_coverage: Coverage scope — "IST Business Hours", "Follow-the-Sun (IST+GMT+EST)", "Global 24x7", "APAC+EMEA", specific timezone if mentioned in RFP
vm_frequency: Proposed scan or review cadence — "Continuous", "Weekly", "Monthly", "Quarterly"
fit_rationale: 1 sentence. Why THIS specific solution for THIS customer based on the recommendation.

Extract 12-18 rows matching the CMO structure. Base ALL recommendations strictly on the solution recommendation text provided.

Solution Recommendation:
""" + truncate(solution_rec_text, 6000)

    content_raw = call_llm(client, [{"role": "user", "content": prompt}], max_tokens=3500, temperature=0.1).strip()
    if "```json" in content_raw: content_raw = content_raw.split("```json")[1].split("```")[0].strip()
    elif "```" in content_raw: content_raw = content_raw.split("```")[1].split("```")[0].strip()
    start, end = content_raw.find("{"), content_raw.rfind("}") + 1
    if start != -1 and end > start: content_raw = content_raw[start:end]
    try:
        return json.loads(content_raw)
    except:
        return {"architecture_name": "Integrated Security Platform", "rows": [
            {"requirement": "SIEM / SOC", "sub_requirement": "Log ingestion and correlation", "recommended_solution": "Microsoft Sentinel", "vendor": "Microsoft", "support_model": "24x7 Managed SOC", "timezone_coverage": "Follow-the-Sun", "vm_frequency": "Continuous", "fit_rationale": "Native Azure integration aligns with existing M365 investment."},
            {"requirement": "Endpoint Security", "sub_requirement": "EDR agent deployment", "recommended_solution": "CrowdStrike Falcon", "vendor": "CrowdStrike", "support_model": "24x7 + P1 On-Call", "timezone_coverage": "Global 24x7", "vm_frequency": "Continuous", "fit_rationale": "Industry-leading detection with lightweight agent, rapid deployment."},
        ], "key_outcomes": ["Faster detection", "Automated compliance", "Zero Trust"], "integration_note": "Unified via SOAR orchestration layer."}


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
