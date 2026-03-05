import os
import json
from openai import OpenAI

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


def generate_customer_brief(rfp_text):
    """One-pager: who is the customer, context, why this RFP now"""
    client = get_client()
    prompt = f"""You are a senior cybersecurity presales consultant preparing a customer intelligence brief before a major proposal.

Analyze this RFP and produce a sharp, insightful ONE-PAGER that a presales consultant can read in 2 minutes before walking into a customer meeting.

Structure your response EXACTLY as follows:

## CUSTOMER SNAPSHOT
Provide 4-5 sentences covering: who they are, industry vertical, size/scale, business model, market position. Make it specific — not generic industry description.

## BUSINESS CONTEXT & TRIGGERS
Why is this RFP being released NOW? What business events, regulatory pressures, incidents, or strategic initiatives are likely driving this? Think like a detective — read between the lines of the RFP. What pain forced them to write this document?

## ORGANIZATIONAL SCALE
Summarize the environment in crisp bullet points: users, endpoints, locations, cloud platforms, applications, transaction volumes — whatever is mentioned. This is for quick reference.

## KEY DECISION MAKERS (LIKELY)
Based on the RFP content, who in the organization is likely involved in this decision? CISO, CTO, CFO, CRO, Board? What are their likely priorities and concerns?

## STRATEGIC PRIORITIES
What are the top 3 things this organization is trying to achieve with this investment? Not technical features — business outcomes.

## RELATIONSHIP ENTRY POINTS
What aspects of this RFP give a smart presales consultant the best opportunity to build rapport, demonstrate expertise, and differentiate from competition?

RFP:
{truncate_text(rfp_text)}

Be specific, insightful, and sharp. Avoid generic statements. Every line should be directly derived from or intelligently inferred from the RFP content."""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=1500,
        temperature=0.3
    )
    return response.choices[0].message.content


def generate_pain_analysis(rfp_text):
    """Deep pain point and requirements analysis"""
    client = get_client()
    prompt = f"""You are a world-class cybersecurity presales consultant with 20 years of experience winning enterprise deals. You have a gift for understanding what customers REALLY need — not just what they wrote in the RFP.

Analyze this RFP and produce a deep pain point analysis structured as follows:

## SURFACE REQUIREMENTS vs UNDERLYING PAINS
For each major requirement area, identify:
- What they ASKED for (surface requirement)
- What they ACTUALLY NEED (underlying business pain)
- The RISK they are trying to mitigate
- The COST of inaction (business impact if not solved)

## TOP 5 CRITICAL PAIN POINTS (RANKED)
Rank the 5 most critical pain points this organization is experiencing. For each:
1. Pain point name
2. Evidence from RFP (quote or reference the specific requirement)
3. Business impact if not addressed
4. Urgency level (Critical/High/Medium)

## COMPLIANCE & REGULATORY PRESSURE
What regulatory obligations are driving this? What are the consequences of non-compliance? Be specific about penalties, deadlines, and audit implications.

## TECHNICAL DEBT & LEGACY CHALLENGES
Based on the requirements, what legacy technology problems are they likely trying to solve? What does their current environment tell you about their technical debt?

## QUICK WINS vs LONG-TERM TRANSFORMATION
Which requirements represent immediate tactical fixes vs strategic transformation? This helps structure the proposal and implementation approach.

## RED FLAGS & RISKS FOR VENDOR
What requirements could be problematic? Unrealistic timelines? Overly complex integrations? Budget misalignment? Flag these honestly so the presales team is prepared.

RFP:
{truncate_text(rfp_text)}

Be analytical, honest, and commercially aware. A great presales consultant uses this analysis to build a proposal that speaks directly to pain — not just features."""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=2000,
        temperature=0.2
    )
    return response.choices[0].message.content


def generate_solution_recommendation(rfp_text):
    """What should we propose and why — presales recommendation"""
    client = get_client()
    prompt = f"""You are a Principal Solution Architect and presales strategist. Your job is to tell the sales team exactly what solution to propose and why — with full commercial and technical rationale.

Based on this RFP, produce a Solution Recommendation Report:

## RECOMMENDED SOLUTION ARCHITECTURE
Describe the proposed solution at a high level. What is the overall architecture? Platform approach vs best-of-breed? On-premise, cloud, or hybrid? Why is this the right architectural approach for THIS customer?

## CORE SOLUTION COMPONENTS (What to propose for each domain)
For each domain required in the RFP:
- Recommended solution component
- Specific reason it fits THIS customer's requirements
- Key capabilities to highlight
- Implementation consideration

## SOLUTION DIFFERENTIATORS
What makes our proposed solution uniquely suited for this customer? What 3-5 points should the proposal hammer home repeatedly?

## PROPOSED IMPLEMENTATION PHASING
How should the solution be delivered? Propose a phased approach that:
- Delivers quick wins in Phase 1 to build confidence
- Addresses the most critical requirements first
- Manages risk appropriately
- Aligns with their stated timeline

## COMMERCIAL STRATEGY
- What pricing model works best for this customer?
- Where is there room to be competitive?
- What can be bundled to increase deal value?
- What managed services opportunities exist?

## PROPOSAL MESSAGING FRAMEWORK
The 5 key messages that should run through the entire proposal:
1. Message about understanding their business
2. Message about technical fit
3. Message about risk reduction
4. Message about ROI/value
5. Message about partnership/long-term

## POC STRATEGY
What should be demonstrated in the POC to maximize win probability? What KPIs should be measured? What use cases show the solution at its best?

RFP:
{truncate_text(rfp_text)}

This is a strategic recommendation document. Be opinionated, specific, and commercially smart."""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=2000,
        temperature=0.3
    )
    return response.choices[0].message.content


def generate_competitive_landscape(rfp_text):
    """Who else is bidding and how to win"""
    client = get_client()
    prompt = f"""You are a competitive intelligence expert in enterprise cybersecurity with deep knowledge of how deals are won and lost.

Based on this RFP, produce a competitive landscape analysis:

## LIKELY COMPETITORS IN THIS DEAL
Based on the requirements, scale, and industry — which vendors are most likely to bid? For each likely competitor:
- Vendor name
- Why they are a likely bidder
- Their typical approach for deals like this
- Their likely pricing strategy

## COMPETITIVE THREAT ASSESSMENT
| Vendor | Threat Level | Their Strongest Cards | Their Weaknesses |
Provide this analysis for top 4-5 competitors.

## WHERE WE WIN vs WHERE WE LOSE
Against each major competitor:
- Where our solution is clearly superior
- Where they may outperform us
- The specific requirements where the battle will be won or lost

## CUSTOMER EVALUATION BIASES
Based on the RFP language, evaluation criteria, and requirements — what does this tell us about the customer's existing vendor relationships? Any incumbents? Any obvious preferences?

## COUNTER-STRATEGY
For each major competitor, what is the counter-strategy?
- What FUD (Fear, Uncertainty, Doubt) can we legitimately raise about their solution?
- What proof points, case studies, or references should we lead with?
- What TCO arguments work in our favor?

## WINNING CONDITIONS
What 3-5 things must happen for us to win this deal? What are the absolute must-haves in our proposal and POC to beat the competition?

## LANDMINES TO AVOID
What mistakes do vendors typically make in deals like this that cause them to lose? What should we NOT do?

RFP:
{truncate_text(rfp_text)}

Be realistic, honest, and strategically sharp. The goal is to help the sales team go in with eyes wide open."""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=2000,
        temperature=0.3
    )
    return response.choices[0].message.content


def generate_product_mapping(rfp_text):
    """Detailed vendor and product recommendations"""
    client = get_client()
    prompt = f"""You are a senior cybersecurity solution architect with commercial awareness. You know every major vendor platform deeply — their strengths, weaknesses, pricing models, and ideal use cases.

Analyze this RFP and produce a DETAILED product mapping for EACH domain:

For every cybersecurity domain required in this RFP, provide:

### [DOMAIN NAME]
**Requirement Summary:** (2-3 sentences on what the customer specifically needs)

**PRIMARY RECOMMENDATION: [Vendor - Specific Product]**
- Why this fits: (3-4 specific reasons tied to THIS RFP's requirements)
- Key capabilities addressing requirements: (bullet list)
- Deployment model for this customer: (how it would be deployed)
- Typical deal size for this scale: (rough pricing indication)
- Reference customers in same industry: (if known)

**ALTERNATIVE: [Vendor - Specific Product]**  
- When to recommend this instead: (specific scenario)
- Key differentiator vs primary: (what they do better)
- Potential concern: (honest weakness)

**INTEGRATION NOTE:** How does this solution integrate with other recommended components?

Cover ALL of these domains if relevant to the RFP:
- SIEM/SOC Platform
- Endpoint Detection & Response (EDR/XDR)  
- Zero Trust / Identity & Access Management
- Cloud Security (CSPM/CWPP/CNAPP)
- Network Security (NGFW/IDS/WAF)
- Governance, Risk & Compliance (GRC)
- Privileged Access Management (PAM)
- Threat Intelligence

Vendors to reference: Palo Alto Networks (Cortex XSIAM, XDR, Prisma Cloud, NGFW), Microsoft (Sentinel, Defender XDR, Entra ID, Defender for Cloud, Purview), CrowdStrike (Falcon platform), SentinelOne (Singularity), Splunk (Enterprise Security), IBM QRadar, Okta (Identity Cloud), CyberArk (Privileged Access), BeyondTrust, Zscaler (ZIA/ZPA), Fortinet (FortiGate/FortiSIEM), Check Point, Tenable (Vulnerability Management), Rapid7, Wiz, Orca Security.

RFP:
{truncate_text(rfp_text)}

Be specific, opinionated, and commercially grounded. Every recommendation must be justified by actual RFP requirements."""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=3000,
        temperature=0.2
    )
    return response.choices[0].message.content


def generate_executive_summary(rfp_text):
    """Board-ready executive summary for proposal"""
    client = get_client()
    prompt = f"""You are a Chief Security Strategist writing the executive summary for a winning proposal. This will be read by the CISO, CTO, CFO, and potentially the Board.

Write a powerful, persuasive executive summary (500-600 words) structured as:

**[Opening — 2-3 sentences]**
Acknowledge the organization by name (if mentioned), their strategic position, and the significance of this security investment decision. Show you understand their business — not just their IT.

**The Security Imperative [1 paragraph]**
Articulate the specific threats and challenges facing this organization in their industry context. Use industry statistics and threat landscape data relevant to their sector. Show urgency without fearmongering.

**Our Understanding of Your Requirements [1 paragraph]**
Demonstrate deep understanding of their specific requirements. Reference key aspects — scale, compliance obligations, integration needs. This paragraph says "we read your RFP carefully."

**Proposed Solution Approach [2 paragraphs]**
Describe the solution philosophy and approach. Why platform over point solutions? How does the architecture address their specific environment? Speak in outcomes — "your SOC team will detect threats in under 5 minutes" not "our SIEM has ML-based correlation."

**Business Value & Risk Reduction [1 paragraph]**
Quantify the value. Breach cost reduction, compliance risk mitigation, operational efficiency gains, faster incident response. Use numbers where possible.

**Why [Us/This Solution] [1 paragraph]**
The unique value proposition. What makes this proposal the right choice. References to industry experience, similar deployments, local presence, support model.

**Call to Action [2-3 sentences]**
Confident close. Next steps. Expression of partnership commitment.

TONE: Confident, authoritative, business-first. No acronyms without explanation. Write as if this document alone could win the deal.

RFP:
{truncate_text(rfp_text)}"""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=1200,
        temperature=0.3
    )
    return response.choices[0].message.content


def classify_domains(rfp_text):
    """Domain classification"""
    client = get_client()
    prompt = f"""Analyze this RFP and identify cybersecurity domains required.

Respond with ONLY valid JSON:
{{
  "detected_domains": ["Domain 1", "Domain 2"],
  "domain_details": {{
    "Domain 1": "Specific requirements from RFP",
    "Domain 2": "Specific requirements from RFP"
  }},
  "reasoning": "Overall analysis",
  "priority_domains": ["Most critical", "Second most critical"],
  "coverage_score": "High/Medium/Low"
}}

RFP: {truncate_text(rfp_text)}"""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=800,
        temperature=0.1
    )
    content = response.choices[0].message.content.strip()
    if "```json" in content:
        content = content.split("```json")[1].split("```")[0].strip()
    elif "```" in content:
        content = content.split("```")[1].split("```")[0].strip()
    start = content.find("{")
    end = content.rfind("}") + 1
    if start != -1 and end > start:
        content = content[start:end]
    try:
        result = json.loads(content)
        if not isinstance(result, dict):
            raise ValueError("Not a dict")
        if "detected_domains" not in result:
            result["detected_domains"] = ["SIEM/SOC", "Network Security"]
        if "reasoning" not in result:
            result["reasoning"] = "Domains detected from RFP content."
        return result
    except:
        return {
            "detected_domains": ["SIEM/SOC", "Endpoint Security", "Network Security", "Compliance & GRC"],
            "domain_details": {},
            "reasoning": "Multiple cybersecurity domains identified.",
            "priority_domains": ["SIEM/SOC", "Endpoint Security"],
            "coverage_score": "High"
        }


def chat_with_rfp(rfp_text, question, chat_history):
    """Interactive Q&A"""
    client = get_client()
    messages = [{
        "role": "system",
        "content": f"""You are an expert cybersecurity presales consultant. You have thoroughly analyzed this RFP and answer questions with precision, depth, and commercial awareness.

When answering:
- Be specific and reference actual RFP content
- Provide presales context and recommendations
- Flag ambiguities or areas needing clarification
- Use structured responses for complex questions

RFP: {truncate_text(rfp_text, 8000)}"""
    }]

    history = chat_history[-12:] if len(chat_history) > 12 else chat_history
    for i in range(0, len(history), 2):
        if i < len(history):
            messages.append({"role": "user", "content": history[i]})
        if i+1 < len(history):
            messages.append({"role": "assistant", "content": history[i+1]})
    messages.append({"role": "user", "content": question})

    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        max_tokens=800,
        temperature=0.2
    )
    return response.choices[0].message.content
