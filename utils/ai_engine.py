import os
import json
import time
import random
from openai import OpenAI
try:
    from openai import RateLimitError as _OAIRateLimit
except ImportError:
    _OAIRateLimit = None

def get_client():
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError("Groq API key not set")
    return OpenAI(
        api_key=api_key,
        base_url="https://api.groq.com/openai/v1"
    )

MODEL = "llama-3.3-70b-versatile"

def truncate_text(text, max_chars=12000):
    return text[:max_chars] if len(text) > max_chars else text


def _is_rate_limit(e):
    """Detect rate limit errors regardless of client (OpenAI, Groq, etc.)."""
    if _OAIRateLimit and isinstance(e, _OAIRateLimit):
        return True
    err = str(e).lower()
    return any(x in err for x in ["rate limit", "rate_limit", "429", "quota", "too many requests", "ratelimit"])

def call_llm(client, messages, max_tokens=1500, temperature=0.2):
    """Central LLM caller with exponential backoff on rate limit."""
    max_retries = 5
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
            if _is_rate_limit(e) and attempt < max_retries - 1:
                wait = (5 * (2 ** attempt)) + random.uniform(0, 3)
                time.sleep(wait)
                continue
            raise


def extract_rfp_signals(rfp_text):
    """Extract key RFP signals to ground all subsequent analysis in real document data."""
    client = get_client()
    prompt = """Read this RFP and extract key signals. Respond ONLY with valid JSON:
{
  "org_name": "exact org name from RFP",
  "industry": "specific industry vertical",
  "geography": "country/region of operations",
  "scale": "number of users/endpoints/locations if mentioned",
  "compliance": ["list of specific compliance frameworks mentioned e.g. ISO 27001, GDPR, RBI, PCI-DSS, NIST"],
  "incumbent_tools": ["any existing tools mentioned e.g. Splunk, Active Directory, Office 365"],
  "budget_signals": "any budget range, tier, or cost sensitivity signals mentioned",
  "preferred_vendors": ["any vendor names explicitly mentioned or implied"],
  "blacklisted_vendors": ["any vendors excluded or discouraged"],
  "key_pain_points": ["top 3-5 specific problems stated or implied in the RFP"],
  "evaluation_criteria": ["specific evaluation criteria or weightings if mentioned"],
  "timeline": "project timeline or go-live dates if mentioned",
  "deal_type": "net new / renewal / expansion / migration",
  "decision_maker_signals": ["titles or roles of decision makers mentioned"]
}
If a field cannot be determined from the RFP, use null. Be specific - extract actual text signals, not generic guesses.

RFP:
""" + rfp_text[:8000]

    raw = call_llm(client, [{"role": "user", "content": prompt}], max_tokens=1000, temperature=0.1)
    raw = raw.strip()
    if "```json" in raw: raw = raw.split("```json")[1].split("```")[0].strip()
    elif "```" in raw: raw = raw.split("```")[1].split("```")[0].strip()
    start, end = raw.find("{"), raw.rfind("}") + 1
    if start != -1 and end > start: raw = raw[start:end]
    try:
        return json.loads(raw)
    except:
        return {}




def detect_rfp_type(rfp_text):
    """Detect the type/domain of RFP to drive domain-aware analysis."""
    client = get_client()
    prompt = """Read this RFP and classify it. Respond ONLY with valid JSON:
{
  "rfp_type": "one of: Cybersecurity | Infrastructure Services | Application Managed Services | End User Computing | Digital Workplace | Data & Analytics | Multi-Tower | Other",
  "primary_domains": ["list of 3-6 primary service domains in this RFP e.g. SOC Operations, Cloud Migration, Helpdesk L1/L2, SAP AMS, Network Management"],
  "technology_stack": ["key technologies, platforms, or tools mentioned"],
  "service_model": "one of: Managed Service | Project-based | Hybrid | Staff Augmentation | Outsourcing",
  "consultant_persona": "the type of expert who should analyse this - e.g. Senior Cybersecurity Architect | Infrastructure Solutions Architect | IT Service Delivery Manager | Application Services Lead",
  "vendor_landscape": ["top 5-8 vendors relevant to this specific RFP type and domains"],
  "key_metrics": ["the 2-4 most important SLA/KPI metrics for this type of RFP e.g. MTTR, P1 response time, uptime SLA, ticket resolution rate"]
}

Examples:
- SOC + SIEM + EDR RFP -> Cybersecurity, consultant_persona: Senior Cybersecurity Architect
- DC migration + cloud + network RFP -> Infrastructure Services, consultant_persona: Infrastructure Solutions Architect  
- SAP support + L2/L3 AMS RFP -> Application Managed Services, consultant_persona: Application Services Lead
- Helpdesk + desktop + M365 RFP -> End User Computing, consultant_persona: IT Service Delivery Manager
- SOC + helpdesk + infra all in one -> Multi-Tower, consultant_persona: IT Managed Services Director

RFP:
""" + rfp_text[:5000]

    raw = call_llm(client, [{"role": "user", "content": prompt}], max_tokens=600, temperature=0.1)
    raw = raw.strip()
    if "```json" in raw: raw = raw.split("```json")[1].split("```")[0].strip()
    elif "```" in raw: raw = raw.split("```")[1].split("```")[0].strip()
    s, e = raw.find("{"), raw.rfind("}") + 1
    if s != -1 and e > s: raw = raw[s:e]
    try:
        return json.loads(raw)
    except:
        return {
            "rfp_type": "Other",
            "primary_domains": [],
            "technology_stack": [],
            "service_model": "Managed Service",
            "consultant_persona": "Senior Solutions Architect",
            "vendor_landscape": [],
            "key_metrics": ["SLA adherence", "Response time", "Resolution rate"]
        }

def generate_customer_brief(rfp_text):
    """One-pager: who is the customer, context, why this RFP now"""
    client = get_client()
    rfp_meta = detect_rfp_type(rfp_text)
    persona  = rfp_meta.get("consultant_persona", "Senior Solutions Architect")
    domains  = ", ".join(rfp_meta.get("primary_domains", []))
    prompt = f"""You are a {persona} preparing a customer intelligence brief before a major proposal.

RFP Type: {rfp_meta.get("rfp_type","Unknown")}
Primary Domains: {domains}

Analyze this RFP and produce a sharp ONE-PAGER a presales consultant can read in 2 minutes before walking into a customer meeting.

Structure your response EXACTLY as:

## CUSTOMER SNAPSHOT
4-5 sentences: who they are, industry, size/scale, business model, market position. Be specific.

## WHY THIS RFP NOW
2-3 sentences: business trigger. What event, pressure, or initiative is driving this procurement? What happens if they do not act?

## WHAT THEY ARE ACTUALLY BUYING
The real ask beneath the stated requirements. What outcome does the customer want - not just what they wrote in the scope.

## KEY DECISION MAKERS & INFLUENCERS
Who is evaluating this? Who signs? Who influences? Infer from job titles, evaluation criteria, and RFP language.

## STRATEGIC PRIORITIES
The 3-4 business priorities this RFP is trying to serve. Think beyond IT - cost reduction, regulatory pressure, M&A, digital transformation.

## RELATIONSHIP ENTRY POINTS
Where is the best opportunity to build trust and differentiate before submission? What would make them remember us?

## RED FLAGS & WATCH-OUTS
What in this RFP suggests a difficult customer, a wired deal, or unrealistic expectations?

RFP:
{truncate_text(rfp_text)}

Every insight must be specific to this RFP. No generic statements."""

    return call_llm(client, [{"role": "user", "content": prompt}], max_tokens=1500, temperature=0.3)



def generate_pain_analysis(rfp_text):
    """Deep pain point and requirements analysis - domain agnostic"""
    client = get_client()
    rfp_meta = detect_rfp_type(rfp_text)
    persona  = rfp_meta.get("consultant_persona", "Senior Solutions Architect")
    rfp_type = rfp_meta.get("rfp_type", "IT Services")
    metrics  = ", ".join(rfp_meta.get("key_metrics", ["SLA adherence", "response time"]))
    prompt = f"""You are a {persona} with deep experience winning {rfp_type} deals.

Analyze this RFP and produce a deep pain point analysis. Go beyond what is written - understand what the customer truly needs.

## RANKED PAIN POINTS
List the top 5-7 pain points in order of business impact. For each:
- Pain: what is the problem
- Business impact: cost, risk, compliance, reputation
- Evidence: quote or reference from the RFP that signals this pain

## SURFACE REQUIREMENTS vs REAL NEEDS
What the RFP says vs what the customer actually needs. 3-5 examples where the stated requirement understates or misrepresents the underlying business need.

## COMPLIANCE & REGULATORY PRESSURES
Specific regulations, frameworks, or audit findings driving this RFP. What are the consequences of non-compliance?

## TECHNICAL DEBT & LEGACY CONSTRAINTS
What existing systems, contracts, or technical limitations will constrain the solution?

## OPERATIONAL PAIN
Day-to-day problems the current team faces. Staffing gaps, tool sprawl, manual processes, escalation failures.

## KEY SLA/KPI REQUIREMENTS
The specific measurable commitments the customer expects: {metrics}. Map each to its business justification.

## COMMERCIAL SENSITIVITIES
Budget signals, cost pressure, make-vs-buy tensions, incumbent disadvantage or advantage.

## WHAT WILL MAKE OR BREAK THE PROPOSAL
The 2-3 requirements where winning or losing this deal will be decided.

RFP:
{truncate_text(rfp_text)}"""

    return call_llm(client, [{"role": "user", "content": prompt}], max_tokens=2000, temperature=0.2)



def generate_solution_recommendation(rfp_text):
    """Strategic solution recommendation - domain agnostic"""
    client = get_client()
    rfp_meta = detect_rfp_type(rfp_text)
    persona  = rfp_meta.get("consultant_persona", "Senior Solutions Architect")
    rfp_type = rfp_meta.get("rfp_type", "IT Services")
    domains  = ", ".join(rfp_meta.get("primary_domains", []))
    tech     = ", ".join(rfp_meta.get("technology_stack", []))
    prompt = f"""You are a {persona} designing the winning solution for a {rfp_type} RFP.

RFP Domains: {domains}
Technology Stack: {tech}

Produce a structured solution recommendation a presales team can use to build a winning proposal.

## SOLUTION PHILOSOPHY
In 3-5 sentences: what is the core strategic approach? Why this over alternatives? What is the headline value proposition?

## RECOMMENDED ARCHITECTURE / OPERATING MODEL
The proposed solution structure. How does it work? What are the key components? How do they integrate? Use specific product names and service models where relevant.

## IMPLEMENTATION APPROACH & PHASING
Phase 1 / Phase 2 / Phase 3 with timelines, key milestones, and what the customer gets at each stage. Be realistic.

## TEAM & GOVERNANCE MODEL
Who delivers this? What roles, where located, what governance structure? How does the customer interact with the delivery team day-to-day?

## SLA & SERVICE LEVELS
Proposed SLAs for each major service tower. How do they meet or exceed the RFP requirements?

## IN-SCOPE VOLUME SUMMARY
Produce a markdown table of ALL quantified volumes from the RFP. Columns: Service Tower | Item | Volume/Quantity | Unit | Notes.
Example rows: Cybersecurity | Endpoints under EDR | 8,500 | Devices | Windows only | or | EUC | Helpdesk tickets/month | ~3,500 | Tickets | Estimated from user count.
Extract every number from the RFP - users, endpoints, servers, tickets, locations, applications, VMs, storage, etc. If a volume is not stated, mark as TBC.

## POC / PILOT STRATEGY
What should the POC demonstrate? How long? What success criteria? What does a winning POC look like for THIS customer?

## COMMERCIAL STRATEGY
Pricing model, deal structure, how to present TCO. What is the anchor message on value?

## KEY RISKS & MITIGATIONS
Top 3-4 delivery risks for this engagement and how we mitigate them in the proposal.

RFP:
{truncate_text(rfp_text)}

Be specific and commercially grounded. Every recommendation must be defensible against the RFP. The volume table must be populated from actual RFP data."""

    return call_llm(client, [{"role": "user", "content": prompt}], max_tokens=2000, temperature=0.2)



def generate_competitive_landscape(rfp_text):
    """RFP-grounded competitive intelligence - signals extracted first, then analysis."""
    client  = get_client()
    signals = extract_rfp_signals(rfp_text)

    sig_block = f"""
CONFIRMED RFP SIGNALS (base your entire analysis on these - do not invent):
- Organisation: {signals.get('org_name') or 'Unknown'}
- Industry: {signals.get('industry') or 'Unknown'}
- Geography: {signals.get('geography') or 'Unknown'}
- Scale: {signals.get('scale') or 'Unknown'}
- Compliance requirements: {', '.join(signals.get('compliance') or ['Not specified'])}
- Existing tools (incumbents): {', '.join(signals.get('incumbent_tools') or ['None identified'])}
- Vendors mentioned in RFP: {', '.join(signals.get('preferred_vendors') or ['None'])}
- Budget signals: {signals.get('budget_signals') or 'Not specified'}
- Key pain points: {', '.join(signals.get('key_pain_points') or ['Not specified'])}
- Evaluation criteria: {', '.join(signals.get('evaluation_criteria') or ['Not specified'])}
- Deal type: {signals.get('deal_type') or 'Unknown'}
- Decision makers: {', '.join(signals.get('decision_maker_signals') or ['Not specified'])}
"""

    rfp_meta = detect_rfp_type(rfp_text)
    rfp_type = rfp_meta.get("rfp_type", "IT Services") or "IT Services"
    persona  = rfp_meta.get("consultant_persona", "Senior Solutions Architect") or "Senior Solutions Architect"
    prompt = f"""You are a competitive intelligence expert in {rfp_type} with deep knowledge of how enterprise deals are won and lost. You have just read an RFP in detail.

{sig_block}

INSTRUCTIONS - every point must be anchored to the RFP signals above:

## WHO IS LIKELY BIDDING
Based on the industry ({signals.get('industry') or 'Unknown'}), geography ({signals.get('geography') or 'Unknown'}), compliance requirements, and scale - name the specific vendors most likely bidding on this deal and WHY each one fits this specific opportunity. Do not list generic vendors - derive from the signals.

## COMPETITIVE THREAT ASSESSMENT
For each likely bidder, provide a table row:
Vendor | Threat Level (High/Med/Low) | Their strongest card for THIS deal | Their weakness for THIS deal

## INCUMBENT ADVANTAGE ANALYSIS
Based on existing tools ({', '.join(signals.get('incumbent_tools') or ['unknown'])}) - which vendor has an existing relationship advantage? How do we counter or leverage this?

## WHERE WE WIN vs WHERE WE LOSE
For this specific RFP requirements - where does our solution clearly win? Where are we vulnerable? Be honest.

## COUNTER-STRATEGY
For each top 2-3 competitors - specific counter-moves based on THIS deal compliance needs, geography, and scale.

## WINNING CONDITIONS
What 3-5 things must happen to win THIS specific deal based on the evaluation criteria and decision maker signals?

## LANDMINES
What mistakes would cause us to lose this specific deal?

RFP (for additional context):
{truncate_text(rfp_text, 6000)}

Be specific to this deal. Every insight must reference actual RFP signals. No generic competitive analysis."""

    return call_llm(client, [{"role": "user", "content": prompt}], max_tokens=2500, temperature=0.2)



def generate_product_mapping(rfp_text):
    """RFP-grounded product mapping - signals extracted first, recommendations derived from actual requirements."""
    client  = get_client()
    signals = extract_rfp_signals(rfp_text)

    sig_block = f"""
CONFIRMED RFP SIGNALS:
- Organisation: {signals.get('org_name','Unknown')} | Industry: {signals.get('industry','Unknown')} | Geography: {signals.get('geography','Unknown')}
- Scale: {signals.get('scale','Unknown')}
- Compliance: {', '.join(signals.get('compliance') or ['Not specified'])}
- Existing tools: {', '.join(signals.get('incumbent_tools') or ['None'])}
- Vendors mentioned: {', '.join(signals.get('preferred_vendors') or ['None'])}
- Blacklisted vendors: {', '.join(signals.get('blacklisted_vendors') or ['None'])}
- Key pain points: {', '.join(signals.get('key_pain_points') or ['Not specified'])}
- Budget signals: {signals.get('budget_signals','Not specified')}
"""

    rfp_meta = detect_rfp_type(rfp_text)
    rfp_type = rfp_meta.get("rfp_type", "IT Services")
    persona  = rfp_meta.get("consultant_persona", "Senior Solutions Architect")
    vendors  = rfp_meta.get("vendor_landscape", [])
    prompt = f"""You are a {persona} specialising in {rfp_type} deals. You have read this RFP carefully.

{sig_block}

Produce a DETAILED product mapping for each domain the RFP specifically requires. Do NOT include domains not mentioned in the RFP.

For each required domain, structure your response as:

### [EXACT DOMAIN NAME FROM RFP]
**What this customer specifically needs:** (2-3 sentences referencing actual RFP requirements)

**PRIMARY RECOMMENDATION: [Vendor - Specific Product Name]**
- Why this fits THIS customer: (must reference industry, geography, compliance, existing tools)
- Key capabilities matching their requirements: (specific to what the RFP asked for)
- Integration with their existing environment: ({', '.join(signals.get('incumbent_tools') or ['existing stack'])})
- Compliance coverage: (which of their specific compliance requirements this addresses)

**ALTERNATIVE: [Vendor - Specific Product]**
- When to recommend instead: (specific scenario for THIS customer)
- Trade-off vs primary: (honest comparison)

**COMMERCIAL NOTE:** Licensing model, typical deal size for {signals.get('scale','this scale')}, and any relevant pricing signals.

IMPORTANT: Only recommend vendors, tools, and platforms that genuinely fit this {rfp_type} RFP for {signals.get('industry','this industry')} in {signals.get('geography','this geography')}. Examples of relevant vendor landscapes by type: Infrastructure (VMware, HPE, Dell, Cisco, AWS, Azure, NetApp), AMS (SAP, Oracle, ServiceNow, JIRA, Infosys, TCS, Wipro, IBM), EUC (ServiceNow, SOTI, Ivanti, Nexthink, Microsoft, Citrix, VMware Workspace ONE), Cybersecurity (Palo Alto, Microsoft, CrowdStrike, SentinelOne, Splunk, IBM QRadar, Zscaler, CyberArk). Do NOT include vendors irrelevant to this RFP type. Every recommendation must be defensible.

RFP:
{truncate_text(rfp_text, 6000)}"""

    return call_llm(client, [{"role": "user", "content": prompt}], max_tokens=3000, temperature=0.15)



def generate_executive_summary(rfp_text):
    """Board-ready executive summary - domain agnostic"""
    client = get_client()
    rfp_meta = detect_rfp_type(rfp_text)
    rfp_type = rfp_meta.get("rfp_type", "IT Services")
    domains  = ", ".join(rfp_meta.get("primary_domains", []))
    prompt = f"""You are a Chief Solutions Strategist writing the executive summary for a winning proposal. This will be read by the CIO, CFO, and potentially the Board.

RFP Type: {rfp_type} | Domains: {domains}

Write a powerful executive summary (500-600 words):

**[Opening - 2-3 sentences]**
Acknowledge the organisation by name, their strategic position, and the significance of this investment. Show you understand their business.

**The Business Imperative [1 paragraph]**
Articulate the specific challenges facing this organisation. Use industry context. Show urgency without fearmongering.

**Our Understanding of Your Requirements [1 paragraph]**
Demonstrate deep understanding of their specific requirements. Reference scale, compliance, integration needs. This says "we read your RFP carefully."

**Proposed Solution Approach [2 paragraphs]**
Describe the solution philosophy and approach. Speak in outcomes - measurable improvements, not feature lists.

**Business Value [1 paragraph]**
Quantify the value. Cost reduction, risk mitigation, efficiency gains, faster delivery. Use numbers where possible.

**Why Us [1 paragraph]**
The unique value proposition. Industry experience, similar deployments, local presence, support model.

**Call to Action [2-3 sentences]**
Confident close. Next steps. Partnership commitment.

TONE: Confident, business-first. No acronyms without explanation. Write as if this document alone could win the deal.

RFP:
{truncate_text(rfp_text)}"""

    return call_llm(client, [{"role": "user", "content": prompt}], max_tokens=1200, temperature=0.3)



def classify_domains(rfp_text):
    """Domain classification - works for any RFP type"""
    client = get_client()
    rfp_meta = detect_rfp_type(rfp_text)
    rfp_type = rfp_meta.get("rfp_type", "IT Services") or "IT Services"
    time.sleep(2)  # brief pause between consecutive API calls to avoid rate limit
    prompt = f"""Analyze this RFP and identify all service domains and sub-towers required.
RFP Type detected: {rfp_type}

Respond ONLY with valid JSON:
{{
  "rfp_type": "{rfp_type}",
  "detected_domains": ["Domain 1", "Domain 2"],
  "domain_details": {{
    "Domain 1": "2-sentence description of what is required in this domain",
    "Domain 2": "2-sentence description"
  }},
  "service_model": "Managed Service / Project / Hybrid / Outsourcing",
  "key_metrics": ["SLA metric 1", "SLA metric 2"],
  "reasoning": "2-3 sentences explaining why these domains were identified"
}}

Domains can include ANY IT service area: SOC/SIEM, EDR, Network Security, Cloud Infrastructure, DC Operations,
Application Managed Services, SAP Support, L1/L2/L3 Helpdesk, End User Computing, Digital Workplace,
M365 Administration, ITSM, DevOps, Data Platform, BI/Analytics, Testing Services, etc.

Do NOT limit to cybersecurity. Extract whatever domains the RFP actually covers.

RFP: {truncate_text(rfp_text)}"""

    content_raw = call_llm(client, [{"role": "user", "content": prompt}], max_tokens=800, temperature=0.1).strip()
    if "```json" in content_raw:
        content_raw = content_raw.split("```json")[1].split("```")[0].strip()
    elif "```" in content_raw:
        content_raw = content_raw.split("```")[1].split("```")[0].strip()
    start = content_raw.find("{")
    end = content_raw.rfind("}") + 1
    if start != -1 and end > start:
        content_raw = content_raw[start:end]
    try:
        result = json.loads(content_raw)
        if not isinstance(result, dict):
            raise ValueError("Not a dict")
        return result
    except:
        return {
            "rfp_type": rfp_type,
            "detected_domains": rfp_meta.get("primary_domains", ["General IT Services"]),
            "domain_details": {},
            "service_model": rfp_meta.get("service_model", "Managed Service"),
            "key_metrics": rfp_meta.get("key_metrics", ["SLA adherence"]),
            "reasoning": f"RFP classified as {rfp_type}."
        }

def chat_with_rfp(rfp_text, question, history=None):
    """Domain-aware RFP Q&A - persona adapts to the type of RFP."""
    client   = get_client()
    rfp_meta = detect_rfp_type(rfp_text)
    rfp_type = rfp_meta.get("rfp_type", "IT Services")
    persona  = rfp_meta.get("consultant_persona", "Senior Solutions Architect")
    domains  = ", ".join(rfp_meta.get("primary_domains", []))

    system_msg = (
        "You are a " + persona + " who has thoroughly read this " + rfp_type + " RFP covering: " + domains + ".\n"
        "Answer questions with precision, depth, and commercial awareness. "
        "Be specific - reference actual RFP content where possible.\n"
        "If the answer is not in the RFP, say so and provide your expert inference clearly labelled as inference.\n"
        "Keep answers concise but complete. Use bullet points where helpful."
    )

    messages = [{"role": "system", "content": system_msg + f"\n\nRFP DOCUMENT:\n{truncate_text(rfp_text, 8000)}"}]
    if history:
        for i in range(0, len(history)-1, 2):
            if i < len(history):
                messages.append({"role": "user",      "content": history[i]})
            if i+1 < len(history):
                messages.append({"role": "assistant", "content": history[i+1]})
    messages.append({"role": "user", "content": question})

    return call_llm(client, messages, max_tokens=1200, temperature=0.3)




def suggest_competitors(rfp_text):
    import json as _j
    client   = get_client()
    signals  = extract_rfp_signals(rfp_text)
    rfp_meta = detect_rfp_type(rfp_text)
    rfp_type = rfp_meta.get("rfp_type", "IT Services")
    org  = signals.get("org_name", "this organisation")
    geo  = signals.get("geography", "this region")
    prompt = (
        "You are a competitive intelligence expert. Based on this " + rfp_type
        + " RFP for " + org + " in " + geo + ", identify the 2-3 most likely global MSP "
        "competitors who would bid on this deal.\n"
        "Global MSP leaders to choose from: TCS, Infosys, Wipro, HCL Technologies, IBM, "
        "Accenture, Capgemini, Cognizant, DXC Technology, NTT DATA, Fujitsu, Atos, "
        "LTIMindtree, Tech Mahindra, Unisys, Kyndryl, Rackspace, Leidos, CGI Group.\n\n"
        "Respond ONLY with a JSON array of 2-3 names. No explanation. Just the array.\n\n"
        "RFP:\n" + rfp_text[:3000]
    )
    raw = call_llm(client, [{"role": "user", "content": prompt}], max_tokens=80, temperature=0.1)
    raw = raw.strip()
    if "```" in raw:
        raw = raw.split("```")[1].split("```")[0].strip()
    s, e = raw.find("["), raw.rfind("]") + 1
    if s != -1 and e > s:
        try:
            return _j.loads(raw[s:e])
        except Exception:
            pass
    return ["TCS", "Infosys", "HCL Technologies"]


def generate_competitive_with_competitors(rfp_text, competitor_names):
    client   = get_client()
    signals  = extract_rfp_signals(rfp_text)
    rfp_meta = detect_rfp_type(rfp_text)
    rfp_type = rfp_meta.get("rfp_type", "IT Services") or "IT Services"

    org        = str(signals.get("org_name")      or "Unknown")
    industry   = str(signals.get("industry")       or "Unknown")
    geo        = str(signals.get("geography")      or "Unknown")
    scale      = str(signals.get("scale")          or "Unknown")
    compliance = ", ".join(signals.get("compliance")          or ["Not specified"])
    tools      = ", ".join(signals.get("incumbent_tools")     or ["None identified"])
    pains      = ", ".join(signals.get("key_pain_points")     or ["Not specified"])
    criteria   = ", ".join(signals.get("evaluation_criteria") or ["Not specified"])
    first_comp = str(competitor_names).split(",")[0].strip() or "the leading competitor"

    prompt = (
        "You are a competitive intelligence expert for a " + rfp_type + " deal.\n"
        "Named competitors bidding: " + competitor_names + "\n\n"
        "RFP SIGNALS:\n"
        "- Organisation: " + org + "\n"
        "- Industry: " + industry + "\n"
        "- Geography: " + geo + "\n"
        "- Scale: " + scale + "\n"
        "- Compliance: " + compliance + "\n"
        "- Existing tools: " + tools + "\n"
        "- Key pain points: " + pains + "\n"
        "- Evaluation criteria: " + criteria + "\n\n"
        "Produce deal-specific competitive intelligence grounded in these signals.\n\n"
        "## COMPETITOR PROFILES\n"
        "For each competitor in [" + competitor_names + "], provide:\n"
        "### [Name]\n"
        "**Threat Level:** High / Medium / Low and WHY\n"
        "**Strongest Card:** Their best angle for THIS deal\n"
        "**Key Weakness:** Where they are vulnerable\n"
        "**Counter-Strategy:** Exactly how we beat them\n\n"
        "## COMPETITIVE THREAT TABLE\n"
        "| Competitor | Threat | Strongest Card | Key Weakness | Counter-Move |\n"
        "|------------|--------|---------------|--------------|--------------|\n"
        "(one row per competitor)\n\n"
        "## WHERE WE WIN\n"
        "Where our solution is clearly superior to all named competitors.\n\n"
        "## WHERE WE ARE VULNERABLE\n"
        "Where any competitor has an edge and what we must address.\n\n"
        "## PROPOSAL LANDMINES\n"
        "The 3 mistakes that would hand this deal to " + first_comp + ".\n\n"
        "## WINNING CONDITIONS\n"
        "The 4-5 things that must be true to win against these competitors.\n\n"
        "RFP:\n" + truncate_text(rfp_text, 6000)
    )

    return call_llm(client, [{"role": "user", "content": prompt}], max_tokens=2500, temperature=0.2)
