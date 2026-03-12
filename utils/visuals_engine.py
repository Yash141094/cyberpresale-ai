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

FAST_MODEL = "llama3-8b-8192"        # detection calls — higher TPM limit
MAIN_MODEL = "llama-3.3-70b-versatile"  # content generation

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
    try:    return json.loads(raw)
    except: return {}

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
    "requirement_brief":"1-2 sentences on what RFP requires and current gap"}}
]}}
Extract 12-18 rows using domain names from the RFP. Name actual tools if mentioned.
RFP: {truncate(rfp_text)}"""
    raw = call_llm(client,[{"role":"user","content":prompt}],max_tokens=2500,temperature=0.1)
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
   "vendor":"Vendor","support_model":"24x7 Managed Service","timezone_coverage":"Follow-the-Sun",
   "vm_frequency":"Continuous","fit_rationale":"Why this for this customer"}
],"key_outcomes":["outcome1","outcome2"],"integration_note":"How it integrates"}
Extract 12-18 rows with specific product/vendor names.
Solution Recommendation:
""" + truncate(solution_rec_text, 5000)
    raw = call_llm(client,[{"role":"user","content":prompt}],max_tokens=2500,temperature=0.1)
    r = _parse_json(raw)
    if r and isinstance(r.get("rows"),list) and r["rows"]: return r
    return {"architecture_name":"Integrated Managed Services","rfp_type":"IT Services","rows":[
        {"requirement":"Service Operations","sub_requirement":"Incident management",
         "recommended_solution":"ServiceNow ITSM","vendor":"ServiceNow",
         "support_model":"24x7 Managed Service","timezone_coverage":"Follow-the-Sun",
         "vm_frequency":"Continuous","fit_rationale":"Industry-standard ITSM."}],
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

    raw = call_llm(client,[{"role":"user","content":prompt}],max_tokens=1000,temperature=0.1)
    r = _parse_json(raw)
    if r and r.get("threats") and r.get("solutions") and r.get("coverage"):
        r["row_label"] = row_label
        return r
    rows = ["Ransomware","APT","Insider Threat","Phishing","Cloud Misconfig","DDoS"]
    cols = ["SIEM/SOC","EDR/XDR","Zero Trust/IAM","Cloud Security","Network Security","GRC"]
    return {"threats":rows,"solutions":cols,"coverage":{r:[1]*len(cols) for r in rows},"row_label":row_label}


def extract_requirements_traceability(rfp_text):
    client = get_client()
    prompt = f"""Create a requirements traceability matrix from this RFP.
Respond ONLY with valid JSON:
{{"requirements":[
  {{"id":"REQ-01","domain":"Domain","requirement":"What is required",
    "priority":"Mandatory|Preferred|Optional","proposed_solution":"Product name",
    "capability":"What our solution delivers","coverage":"Full|Partial|Gap","notes":"Brief note"}}
]}}
Extract 12-18 key requirements. RFP: {truncate(rfp_text)}"""
    raw = call_llm(client,[{"role":"user","content":prompt}],max_tokens=2000,temperature=0.1)
    r = _parse_json(raw)
    if r and isinstance(r.get("requirements"),list) and r["requirements"]: return r
    return {"requirements":[
        {"id":"REQ-01","domain":"Service Operations","requirement":"24x7 service desk",
         "priority":"Mandatory","proposed_solution":"ServiceNow ITSM",
         "capability":"Omnichannel 24x7 support","coverage":"Full","notes":"Integrated portal+voice+chat"}]}


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
