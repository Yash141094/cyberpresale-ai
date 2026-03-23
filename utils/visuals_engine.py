"""
Visuals Engine for CyberPresales AI
Optimised: fast model for detection, main model for generation, delays, retry.
"""
import json
import os
import time
import random
from openai import OpenAI

def get_client():
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError("Groq API key not set")
    return OpenAI(api_key=api_key, base_url="https://api.groq.com/openai/v1")

FAST_MODEL = "llama-3.1-8b-instant"   # detection calls
MAIN_MODEL = "llama-3.1-8b-instant"   # all generation — consistent with ai_engine.py

def truncate(text, max_chars=6000):
    return text[:max_chars] if len(text) > max_chars else text

def _is_rate_limit(e):
    err = str(e).lower()
    return any(x in err for x in ["rate limit","rate_limit","429","quota","too many requests","ratelimit"])

def call_llm(client, messages, max_tokens=1000, temperature=0.1, model=None):
    use_model = model or MAIN_MODEL
    for attempt in range(4):
        try:
            r = client.chat.completions.create(model=use_model, messages=messages,
                                               max_tokens=max_tokens, temperature=temperature)
            return r.choices[0].message.content
        except Exception as e:
            if _is_rate_limit(e) and attempt < 3:
                time.sleep((5 * (2**attempt)) + random.uniform(0,3))
                continue
            raise

def _parse_json(raw):
    if "```json" in raw: raw = raw.split("```json")[1].split("```")[0]
    elif "```" in raw:   raw = raw.split("```")[1].split("```")[0]
    raw = raw.strip()
    s, e = raw.find("{"), raw.rfind("}")+1
    if s != -1 and e > s: raw = raw[s:e]
    try:
        return json.loads(raw)
    except Exception:
        # Recovery: find all complete JSON objects in any array and rebuild
        try:
            import re
            # Find the array content
            arr_match = re.search(r'"requirements"\s*:\s*\[', raw)
            if arr_match:
                arr_start = arr_match.end()
                # Find all complete objects {...} within the array
                depth, obj_start, objects = 0, None, []
                for i, ch in enumerate(raw[arr_start:], arr_start):
                    if ch == '{':
                        if depth == 0: obj_start = i
                        depth += 1
                    elif ch == '}':
                        depth -= 1
                        if depth == 0 and obj_start is not None:
                            try:
                                obj = json.loads(raw[obj_start:i+1])
                                objects.append(obj)
                            except Exception:
                                pass
                            obj_start = None
                if objects:
                    return {"requirements": objects}
        except Exception:
            pass
        return {}

def _detect_rfp_type(client, rfp_text):
    """Single lightweight detection call using fast model."""
    prompt = ('Return JSON only: {"rfp_type":"Cybersecurity|Infrastructure|Application Managed Services|'
              'End User Computing|Digital Workplace|Data & Analytics|Multi-Tower|Other",'
              '"is_security":true_or_false,"primary_domains":["d1","d2"],'
              '"consultant_persona":"role"}\nRFP: ' + rfp_text[:2000])
    raw = call_llm(client,[{"role":"user","content":prompt}],max_tokens=200,temperature=0.1,model=FAST_MODEL)
    m = _parse_json(raw)
    return (m.get("rfp_type") or "IT Services", bool(m.get("is_security",True)),
            m.get("primary_domains") or [], m.get("consultant_persona") or "Senior Solutions Architect")


def extract_cmo_data(rfp_text, rfp_type_hint=None):
    client = get_client()
    if rfp_type_hint:
        rfp_type, persona, domains = rfp_type_hint, "Senior Solutions Architect", []
    else:
        rfp_type, _, domains, persona = _detect_rfp_type(client, rfp_text)
        time.sleep(2)
    domains_str = ", ".join(domains) if domains else rfp_type
    prompt = f"""You are a {persona}. Read this {rfp_type} RFP and extract the customer's CURRENT state.
Respond ONLY with valid JSON:
{{"org_name":"Org","industry":"Sector","rfp_type":"{rfp_type}","rows":[
  {{"requirement":"Parent domain","sub_requirement":"Deliverable","current_tool":"Tool or None",
    "licence_owner":"Customer|Supplier|Shared|None","support_hours":"8x5|24x7|etc",
    "timezone":"IST|GMT|Multi-region|Follow-the-Sun","vm_frequency":"Continuous|Weekly|Monthly",
    "requirement_brief":"1 sentence on current gap"}}
]}}
Extract 8-10 rows only. Name actual tools if mentioned. Keep requirement_brief under 80 chars.
RFP: {truncate(rfp_text)}"""
    raw = call_llm(client,[{"role":"user","content":prompt}],max_tokens=1200,temperature=0.1)
    r = _parse_json(raw)
    if r and isinstance(r.get("rows"),list) and r["rows"]: return r
    return {"org_name":"Customer","industry":"Enterprise","rfp_type":rfp_type,"rows":[
        {"requirement":"Service Operations","sub_requirement":"Incident management","current_tool":"Unknown",
         "licence_owner":"None","support_hours":"8x5","timezone":"Local","vm_frequency":"Monthly",
         "requirement_brief":"RFP requires structured incident management with defined SLAs."}]}


def extract_fmo_data(solution_rec_text):
    client = get_client()
    prompt = """Read this solution recommendation and produce a Future Mode of Operations table.
Respond ONLY with valid JSON:
{"architecture_name":"Solution name","rfp_type":"type","rows":[
  {"requirement":"Domain","sub_requirement":"Deliverable","recommended_solution":"Product",
   "vendor":"Vendor","support_model":"24x7 Managed","timezone_coverage":"Follow-the-Sun",
   "fit_rationale":"Why this fits this customer"}
],"key_outcomes":["outcome1","outcome2"],"integration_note":"How it integrates"}
Extract 8-10 rows maximum with specific product/vendor names. Keep fit_rationale under 80 chars.
Solution Recommendation:
""" + truncate(solution_rec_text, 3000)
    raw = call_llm(client,[{"role":"user","content":prompt}],max_tokens=1200,temperature=0.1)
    r = _parse_json(raw)
    if r and isinstance(r.get("rows"),list) and r["rows"]: return r
    return {"architecture_name":"Integrated Managed Services","rfp_type":"IT Services","rows":[
        {"requirement":"Service Operations","sub_requirement":"Incident management",
         "recommended_solution":"ServiceNow ITSM","vendor":"ServiceNow",
         "support_model":"24x7 Managed Service","timezone_coverage":"Follow-the-Sun",
         "fit_rationale":"Industry-standard ITSM."}],
        "key_outcomes":["Improved SLA","Reduced cost","Better UX"],
        "integration_note":"Unified platform with API integrations."}


def extract_threat_coverage(rfp_text, rfp_type_hint=None, is_security_hint=None):
    """Combined axis extraction + scoring in a SINGLE API call (was 4 calls)."""
    client = get_client()
    if rfp_type_hint is not None:
        rfp_type, is_security = rfp_type_hint, (is_security_hint if is_security_hint is not None else False)
    else:
        rfp_type, is_security, _, _ = _detect_rfp_type(client, rfp_text)
        time.sleep(2)

    if is_security:
        prompt = f"""Read this Cybersecurity RFP. Identify 6-8 threat types and 5-6 solution categories, then score coverage.
Respond ONLY with valid JSON:
{{"threats":["Ransomware","APT","Insider Threat","Phishing","Cloud Misconfig","DDoS"],
  "solutions":["SIEM/SOC","EDR/XDR","Zero Trust/IAM","Cloud Security","Network Security","GRC"],
  "coverage":{{"Ransomware":[2,3,1,0,1,0],"APT":[3,2,1,1,0,1]}}}}
Each coverage array must match solutions count. 0=No coverage,1=Partial,2=Good,3=Strong.
RFP: {truncate(rfp_text,4000)}"""
        row_label = "Threat / Attack Vector"
    else:
        prompt = f"""Read this {rfp_type} RFP. Identify 6-8 service areas and 5-6 capabilities, then score coverage.
Respond ONLY with valid JSON:
{{"threats":["Service Area 1","Service Area 2"],
  "solutions":["Capability 1","Capability 2"],
  "coverage":{{"Service Area 1":[2,1,3,0,1,2]}}}}
Each coverage array must match solutions count. 0=Not addressed,1=Partial,2=Good,3=Fully covered.
RFP: {truncate(rfp_text,4000)}"""
        row_label = "Service Area / Requirement"

    raw = call_llm(client,[{"role":"user","content":prompt}],max_tokens=700,temperature=0.1)
    r = _parse_json(raw)
    if r and r.get("threats") and r.get("solutions") and r.get("coverage"):
        r["row_label"] = row_label
        return r
    rows = ["Ransomware","APT","Insider Threat","Phishing","Cloud Misconfig","DDoS"]
    cols = ["SIEM/SOC","EDR/XDR","Zero Trust/IAM","Cloud Security","Network Security","GRC"]
    return {"threats":rows,"solutions":cols,"coverage":{r:[1]*len(cols) for r in rows},"row_label":row_label}


def extract_requirements_traceability(rfp_text):
    client = get_client()

    # Pass 1 — extract requirements with section references (concise fields)
    prompt = f"""Extract a requirements traceability matrix from this RFP.
Respond ONLY with valid JSON. Keep all field values SHORT (under 10 words each).
{{
  "requirements": [
    {{
      "id": "REQ-01",
      "rfp_section": "Section 4.1",
      "domain": "Cybersecurity",
      "requirement": "24x7 SOC with SIEM and SOAR",
      "priority": "Mandatory",
      "proposed_solution": "Microsoft Sentinel + SOAR playbooks",
      "coverage": "Full",
      "notes": "Covers detection and auto-response"
    }}
  ]
}}
Rules:
- rfp_section: use the exact section number or heading from the RFP text (e.g. "Section 4.4", "Clause 3.2")
- Extract 8-10 requirements maximum — quality over quantity
- priority: exactly Mandatory, Preferred, or Optional
- coverage: exactly Full, Partial, or Gap
- Every field must be SHORT — no sentences, just key phrases
RFP:
{truncate(rfp_text, 4000)}"""

    raw = call_llm(client, [{"role": "user", "content": prompt}], max_tokens=1500, temperature=0.1)
    r = _parse_json(raw)

    if r and isinstance(r.get("requirements"), list) and len(r["requirements"]) > 1:
        return r

    # Fallback — minimal valid structure
    return {"requirements": [
        {"id": "REQ-01", "rfp_section": "Section 1", "domain": "Service Operations",
         "requirement": "24x7 service desk", "priority": "Mandatory",
         "proposed_solution": "ServiceNow ITSM", "coverage": "Full",
         "notes": "Retry — JSON parse failed"},
    ]}


def extract_vendor_positioning(rfp_text, rfp_type_hint=None):
    client = get_client()
    if rfp_type_hint:
        rfp_type, domains = rfp_type_hint, []
    else:
        rfp_type, _, domains, _ = _detect_rfp_type(client, rfp_text)
        time.sleep(2)
    vendor_refs = {
        "Cybersecurity": "Palo Alto Networks, Microsoft Security, CrowdStrike, SentinelOne, IBM QRadar, Splunk, Fortinet, Zscaler",
        "Infrastructure": "HPE, Dell Technologies, Cisco, IBM, HCL, Wipro, NTT, Fujitsu",
        "Application Managed Services": "TCS, Infosys, Wipro, HCL, IBM, Accenture, Capgemini, Cognizant",
        "End User Computing": "ServiceNow, DXC Technology, HCL, Unisys, Nexthink, Ivanti, Microsoft",
        "Multi-Tower": "TCS, Infosys, Wipro, HCL, IBM, Accenture, Capgemini, DXC Technology, Fujitsu",
        "Digital Workplace": "Microsoft, ServiceNow, Citrix, VMware, HCL, Unisys, DXC",
    }
    vendors_str = vendor_refs.get(rfp_type, vendor_refs["Multi-Tower"])
    domains_str = ", ".join(domains) if domains else rfp_type
    prompt = f"""Position vendors for this {rfp_type} RFP (domains: {domains_str}).
X=Completeness(0-10), Y=Ease of Implementation(0-10).
Relevant vendors: {vendors_str}
Respond ONLY with valid JSON:
{{"vendors":[
  {{"name":"Vendor","completeness":8.5,"ease":7.0,
    "quadrant":"Leader|Challenger|Niche|Caution",
    "key_strength":"strength for this RFP","key_risk":"concern for this customer"}}
],"recommended_vendor":"Best vendor","rationale":"1-2 sentences tied to this RFP"}}
Position 6-8 vendors. Leader=high both, Challenger=one strong, Niche=narrow, Caution=concerns.
RFP: {truncate(rfp_text,3000)}"""
    raw = call_llm(client,[{"role":"user","content":prompt}],max_tokens=1200,temperature=0.2)
    r = _parse_json(raw)
    if r and isinstance(r.get("vendors"),list) and r["vendors"]: return r
    fallback = {
        "Cybersecurity":[
            {"name":"Palo Alto Networks","completeness":9.2,"ease":7.5,"quadrant":"Leader","key_strength":"Most complete platform","key_risk":"Premium pricing"},
            {"name":"Microsoft Security","completeness":8.5,"ease":9.0,"quadrant":"Leader","key_strength":"M365 integration","key_risk":"Best-of-breed gaps"},
            {"name":"CrowdStrike","completeness":7.5,"ease":8.5,"quadrant":"Challenger","key_strength":"Best EDR","key_risk":"SIEM maturing"},
            {"name":"IBM QRadar","completeness":7.5,"ease":6.0,"quadrant":"Challenger","key_strength":"BFSI SIEM depth","key_risk":"Legacy perception"},
            {"name":"Splunk","completeness":7.0,"ease":6.5,"quadrant":"Challenger","key_strength":"Gold standard SIEM","key_risk":"High cost"},
        ],
        "Multi-Tower":[
            {"name":"TCS","completeness":9.0,"ease":7.5,"quadrant":"Leader","key_strength":"Broadest coverage","key_risk":"Slower agility"},
            {"name":"Infosys","completeness":8.5,"ease":7.5,"quadrant":"Leader","key_strength":"AI-led delivery","key_risk":"Premium pricing"},
            {"name":"Wipro","completeness":8.0,"ease":8.0,"quadrant":"Leader","key_strength":"Strong delivery","key_risk":"Niche depth"},
            {"name":"HCL","completeness":7.5,"ease":8.0,"quadrant":"Challenger","key_strength":"Competitive pricing","key_risk":"Innovation perception"},
            {"name":"IBM","completeness":7.5,"ease":6.5,"quadrant":"Challenger","key_strength":"SAP/Oracle expertise","key_risk":"Cost structure"},
        ],
    }
    v = fallback.get(rfp_type, fallback["Multi-Tower"])
    return {"vendors":v,"recommended_vendor":v[0]["name"],"rationale":f"Best fit for {rfp_type} RFP."}


def extract_compliance_scoring(rfp_text, rfp_type_hint=None):
    """Extract compliance framework requirements and score coverage."""
    client = get_client()
    rfp_short = truncate(rfp_text, 4000)

    prompt = f"""Read this RFP and identify all compliance, regulatory, and security framework requirements mentioned or implied.
For each requirement, assess the status a responding vendor would typically claim.
Respond ONLY with valid JSON:
{{
  "frameworks_detected": ["ISO 27001", "APRA CPS 234"],
  "requirements": [
    {{
      "framework": "ISO 27001",
      "control_ref": "A.12.6",
      "requirement": "Technical vulnerability management programme",
      "status": "Met",
      "evidence_in_rfp": "RFP Section 4.4 requires VM covering all 32,000 assets",
      "risk_if_gap": "Regulatory non-compliance, potential contract penalty"
    }}
  ],
  "summary": {{"met": 8, "partial": 4, "gap": 2}},
  "overall_compliance_score": 72,
  "critical_gaps": ["Gap 1 description", "Gap 2 description"],
  "compliance_narrative": "2-sentence summary of compliance posture"
}}
Status must be exactly one of: Met / Partial / Gap
Extract 10-15 requirements covering all frameworks mentioned. RFP:
{rfp_short}"""

    raw = call_llm(client, [{"role": "user", "content": prompt}], max_tokens=1200, temperature=0.1)
    r = _parse_json(raw)
    if r and isinstance(r.get("requirements"), list) and r["requirements"]:
        return r
    # Fallback
    return {
        "frameworks_detected": ["ISO 27001", "General IT Security"],
        "requirements": [
            {"framework": "ISO 27001", "control_ref": "A.12.6", "requirement": "Vulnerability Management",
             "status": "Partial", "evidence_in_rfp": "Implied by security requirements", "risk_if_gap": "Compliance exposure"},
        ],
        "summary": {"met": 0, "partial": 1, "gap": 0},
        "overall_compliance_score": 50,
        "critical_gaps": ["Unable to extract — retry"],
        "compliance_narrative": "Compliance extraction failed. Please retry."
    }


def extract_bid_scoring(rfp_text, rfp_type_hint=None):
    """Generate bid/no-bid scoring with green flags, red flags, and risk signals."""
    client = get_client()
    rfp_short = truncate(rfp_text, 4000)

    prompt = f"""You are a senior bid director reviewing this RFP to make a bid/no-bid recommendation.
Analyse the RFP across strategic fit, technical complexity, commercial viability, competitive risk, and delivery risk.
Respond ONLY with valid JSON:
{{
  "overall_score": 74,
  "bid_decision": "Bid — Strong Pursuit",
  "bid_decision_rationale": "2-sentence explanation of the bid recommendation",
  "dimensions": {{
    "Strategic Fit": 85,
    "Technical Complexity": 60,
    "Commercial Viability": 75,
    "Competitive Risk": 65,
    "Delivery Risk": 70
  }},
  "green_flags": [
    "Strong alignment with our core cybersecurity capabilities",
    "Multi-year contract with renewal options"
  ],
  "red_flags": [
    "Aggressive 180-day transition timeline",
    "Mandatory CPS 234 Level 4 within 12 months"
  ],
  "commercial_risks": [
    "AUD $180-240M envelope is fixed — limited room to negotiate scope",
    "At-risk margin element creates revenue variability"
  ],
  "technical_complexity": "High",
  "win_themes": ["Theme 1", "Theme 2", "Theme 3"],
  "landmines": ["Risk 1 that could lose the deal", "Risk 2"],
  "recommended_actions": ["Action 1", "Action 2", "Action 3"]
}}
bid_decision must be one of: Bid — Strong Pursuit / Bid with Conditions / Bid Selectively / No Bid
technical_complexity must be: Low / Medium / High / Very High
Scores are 0-100. Be specific to this RFP — no generic answers.
RFP: {rfp_short}"""

    raw = call_llm(client, [{"role": "user", "content": prompt}], max_tokens=1000, temperature=0.2)
    r = _parse_json(raw)
    if r and r.get("overall_score") and r.get("dimensions"):
        return r
    return {
        "overall_score": 65,
        "bid_decision": "Bid with Conditions",
        "bid_decision_rationale": "Unable to fully extract bid signals. Review RFP manually.",
        "dimensions": {"Strategic Fit": 65, "Technical Complexity": 60, "Commercial Viability": 65, "Competitive Risk": 60, "Delivery Risk": 65},
        "green_flags": ["Retry for full analysis"],
        "red_flags": ["Extraction failed — check API"],
        "commercial_risks": ["Unable to extract"],
        "technical_complexity": "Medium",
        "win_themes": [],
        "landmines": [],
        "recommended_actions": ["Retry the analysis"]
    }
