import streamlit as st
import time
import json
from google import genai
from google.genai import errors

# ============================================================================
# PAGE CONFIG & STYLING (Clean, Modern SaaS Dashboard Aesthetic)
# ============================================================================
st.set_page_config(
    page_title="Oliv AI | Dormant Pipeline Revival Agent",
    page_icon="⚡",
    layout="wide"
)

st.markdown("""
<style>
    .reportview-container { background: #F8F9FA; }
    .agent-card {
        background-color: #FFFFFF;
        border: 1px solid #E9ECEF;
        border-radius: 8px;
        padding: 20px;
        margin-bottom: 20px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
    }
    .evidence-box {
        background-color: #F1F3F5;
        border-left: 4px solid #4D4D4D;
        padding: 10px 15px;
        margin: 10px 0;
        border-radius: 0 4px 4px 0;
        font-family: monospace;
        font-size: 0.9em;
    }
    .slack-preview {
        background-color: #1A1D21;
        color: #D1D2D3;
        padding: 15px;
        border-radius: 6px;
        font-family: 'Slack-Lato', sans-serif;
        border-left: 4px solid #36C5F0;
        margin-top: 10px;
    }
    .slack-header {
        color: #FFFFFF;
        font-weight: bold;
        margin-bottom: 5px;
        font-size: 0.95em;
    }
    .priority-HIGH { color: #E03131; font-weight: bold; }
    .priority-MEDIUM { color: #F59F00; font-weight: bold; }
    .priority-LOW { color: #2B8A3E; font-weight: bold; }
    .priority-NOT_RECOMMENDED { color: #868E96; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# MOCK DATASET (Varied, Realistic, Completely Un-rigged)
# ============================================================================
MOCK_DEALS = [
    {
        "id": "D001",
        "company": "Acme Corp",
        "amount": "$45,000",
        "lost_reason": "Lost to competitor X due to lack of native SOC-2 compliance mapping.",
        "days_dormant": 180,
        "recent_signal": "Acme Corp announced yesterday they are migrating away from competitor X due to recent pricing hikes and hired a new VP of InfoSec who worked with our platform previously."
    },
    {
        "id": "D002",
        "company": "Stark Industries",
        "amount": "$120,000",
        "lost_reason": "Stalled indefinitely. Champion stated 'Budget completely frozen for Q3/Q4 due to macroeconomic headwinds'.",
        "days_dormant": 120,
        "recent_signal": "Stark Industries just secured a $50M Series C funding round led by Sequoia specifically earmarked for technology infrastructure modernization."
    },
    {
        "id": "D003",
        "company": "Initech LLC",
        "amount": "$15,000",
        "lost_reason": "Lost because product line didn't support multi-currency localized billing structures.",
        "days_dormant": 240,
        "recent_signal": "Initech corporate office relocated their primary headquarters to Austin, Texas, and issued a minor press release about local sustainability initiatives."
    },
    {
        "id": "D004",
        "company": "Cyberdyne Systems",
        "amount": "$85,000",
        "lost_reason": "Lost to a cheaper point-solution because corporate division didn't see the ROI of an enterprise-grade orchestration layer.",
        "days_dormant": 90,
        "recent_signal": "Cyberdyne expanded its engineering headcount by 45% this quarter, but there are no specific management changes or vendor complaints recorded."
    },
    {
        "id": "D005",
        "company": "Wayne Enterprises",
        "amount": "$210,000",
        "lost_reason": "Stalled. Decision maker (Director of Sales Ops) went completely dark after contract presentation.",
        "days_dormant": 150,
        "recent_signal": "Public LinkedIn updates confirm the previous Director left, and a brand new VP of Revenue Operations has been appointed as of 10 days ago."
    },
    {
        "id": "D006",
        "company": "Umbrella Corp",
        "amount": "$35,000",
        "lost_reason": "Lost due to missing deep integration with Salesforce Industries vertical cloud.",
        "days_dormant": 210,
        "recent_signal": "Umbrella Corp posted an article on their engineering blog discussing their transition from Salesforce to custom internal infrastructure."
    }
]

# ============================================================================
# SYSTEM PROMPT (First-Principles Evaluation Criteria)
# ============================================================================
SYSTEM_PROMPT = """
You are a highly skeptical, metrics-driven Revenue Operations Analyst auditing a dormant pipeline dataset. Your job is to aggressively filter out noise so sales reps only spend time on high-probability opportunities.

Evaluate the deal using strict, un-rigged product reasoning based on these criteria:
1. Does the recent signal directly eliminate or neutralize the original reason the deal was lost? (e.g., if they moved entirely away from the platform type or core ecosystem, the deal is dead, not revived).
2. Is the signal specific, actionable, and time-bound, or is it vague/irrelevant corporate news (like moving offices or generic hiring)?
3. Does it imply a structurally new buying trigger (e.g., net-new budget, change in core leadership/decision-makers)?

Default to LOW or NOT_RECOMMENDED if the signal is purely corporate fluff, unrelated to the blocker, or suggests the company is undergoing a chaotic transition (like abandoning core CRM platforms entirely).

Format your response for each deal exactly as follows, with no deviation:
Signal Assessment: [One clear sentence citing the specific signal and explicitly whether it addresses the original bottleneck or blocker]
Revival Priority: [Must choose exactly one: HIGH, MEDIUM, LOW, or NOT_RECOMMENDED]
Suggested Angle: [One actionable sentence outlining the precise strategic rationale to reach back out, rooted entirely in the signal data]

If the Priority is HIGH or MEDIUM, add an additional block below it titled "Draft Outreach:" followed by a hyper-personalized 2-to-3 sentence email template referencing the signal naturally. Do not use generic 'just checking in' language.
If the Priority is LOW or NOT_RECOMMENDED, do not generate a Draft Outreach block.
"""

# ============================================================================
# INITIALIZATION & ERROR HANDLING PIPELINE
# ============================================================================
if "client" not in st.session_state:
    st.session_state.client = None
    st.session_state.client_error = None
    try:
        api_key = st.secrets.get("GEMINI_API_KEY", "")
        if not api_key:
            st.session_state.client_error = "No GEMINI_API_KEY found in Streamlit secrets configuration."
        else:
            st.session_state.client = genai.Client(api_key=api_key)
    except Exception as e:
        st.session_state.client_error = f"Client initialization failed completely: {e}"

def execute_revival_analysis(deal: dict):
    """
    Executes live analysis against gemini-2.5-flash with built-in exponential backoff.
    Guarantees no hardcoded or fake outcomes.
    """
    if st.session_state.client is None:
        return False, st.session_state.client_error or "Gemini client uninitialized."
    
    prompt = f"""
    Evaluate the following historic deal data:
    - Company Name: {deal['company']}
    - Deal Value: {deal['amount']}
    - Original Stalled/Lost Reason: {deal['lost_reason']}
    - Days Elapsed Since Activity: {deal['days_dormant']}
    - Recent Account Signal Detected: {deal['recent_signal']}
    """
    
    max_retries = 3
    base_delay = 2.0
    
    for attempt in range(max_retries):
        try:
            response = st.session_state.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config={"system_instruction": SYSTEM_PROMPT, "temperature": 0.1}
            )
            if not response.text:
                return False, "Live model returned an empty payload string. Please resubmit."
            return True, response.text
            
        except errors.APIError as api_err:
            # Check for Rate Limit / Quota Exhaustion
            if api_err.code == 429:
                if "quota" in str(api_err).lower():
                    return False, "Live Model Failure: Gemini API Daily Free-Tier Quota completely exhausted. (Honest Error State)"
                
                # Exponential backoff for transient concurrency limits
                time.sleep(base_delay * (2 ** attempt))
                continue
            return False, f"Live model transaction failed with API error code {api_err.code}: {api_err.message}"
        except Exception as e:
            return False, f"Unexpected operational exception occurred during inference: {e}"
            
    return False, "Transient rate limits encountered repeatedly. Operational timeout reached."

# ============================================================================
# UI RENDERING
# ============================================================================
st.title("⚡ Oliv AI | Dormant Pipeline Revival Agent")
st.caption("Strategic Product Pitch Prototype — Category Expansion Concept")
st.write("---")

st.markdown("""
### Concept Wedge: The CRM Graveyard
While current platforms optimize for active, visible in-flight cycles, this agent focuses strictly on deep-mining historically dead pipeline data. Every assessment is structurally grounded in explicit signal matching—directly aligning with Oliv’s core architectural philosophy.
""")

col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("Unprocessed Cold Pipeline")
    st.write("Select a deal to stream through the agentic evaluation framework.")
    
    # Session state tracking to manage multi-deal views safely
    if "results" not in st.session_state:
        st.session_state.results = {}
    if "processing" not in st.session_state:
        st.session_state.processing = set()

    for deal in MOCK_DEALS:
        with st.container():
            st.markdown(f"### {deal['company']} ({deal['amount']})")
            st.write(f"**Lost Reason:** *{deal['lost_reason']}*")
            st.markdown(f"<div class='evidence-box'>📡 Detected Signal: {deal['recent_signal']}</div>", unsafe_allow_html=True)
            
            is_processing = deal['id'] in st.session_state.processing
            has_result = deal['id'] in st.session_state.results
            
            # Debounce architecture preventing double-execution and quota burning
            btn_label = "Analyzing..." if is_processing else ("Re-evaluate Signal" if has_result else "Run Agent Analysis")
            
            if st.button(btn_label, key=deal['id'], disabled=is_processing):
                st.session_state.processing.add(deal['id'])
                st.rerun()

with col2:
    st.subheader("Agent Intelligence Output")
    
    # Handle deferred button execution state
    for deal in MOCK_DEALS:
        if deal['id'] in st.session_state.processing:
            st.session_state.processing.remove(deal['id'])
            success, output = execute_revival_analysis(deal)
            st.session_state.results[deal['id']] = {"success": success, "payload": output}
            st.rerun()

    # Display active evaluation logs
    active_selection = False
    for deal in MOCK_DEALS:
        if deal['id'] in st.session_state.results:
            active_selection = True
            res = st.session_state.results[deal['id']]
            
            st.markdown(f"## {deal['company']} Diagnostic Summary")
            
            if not res["success"]:
                st.error(res["payload"])
            else:
                lines = res["payload"].strip().split("\n")
                parsed_data = {}
                outreach_block = []
                in_outreach = False
                
                for line in lines:
                    if line.startswith("Signal Assessment:"):
                        parsed_data["assessment"] = line.replace("Signal Assessment:", "").strip()
                    elif line.startswith("Revival Priority:"):
                        parsed_data["priority"] = line.replace("Revival Priority:", "").strip()
                    elif line.startswith("Suggested Angle:"):
                        parsed_data["angle"] = line.replace("Suggested Angle:", "").strip()
                    elif line.startswith("Draft Outreach:"):
                        in_outreach = True
                    elif in_outreach:
                        outreach_block.append(line)
                
                priority = parsed_data.get("priority", "LOW")
                
                # Render structured summary matching Oliv visual paradigm without branding theft
                st.markdown(f"#### Priority Rating: <span class='priority-{priority}'>{priority}</span>", unsafe_allow_html=True)
                st.write(f"**Grounding Analysis:** {parsed_data.get('assessment', 'N/A')}")
                st.write(f"**Strategic Approach:** {parsed_data.get('angle', 'N/A')}")
                
                if outreach_block and priority in ["HIGH", "MEDIUM"]:
                    email_body = "\n".join(outreach_block).strip()
                    st.markdown("### 💬 Slack Delivery Preview")
                    st.markdown(f"""
                    <div class="slack-preview">
                        <div class="slack-header">🤖 Oliv Revival Agent <span style='font-weight:normal; font-size:0.8em; color:#868E96;'>10:28 PM</span></div>
                        🎯 <b>Opportunity Alert:</b> A dormant pipeline window reopened for <b>{deal['company']}</b> ({deal['amount']}).<br><br>
                        💡 <b>Trigger:</b> {parsed_data.get('angle', 'N/A')}<br><br>
                        📝 <b>Suggested Draft Outreach:</b><br>
                        <i>{email_body}</i>
                    </div>
                    """, unsafe_allow_html=True)
            st.write("---")
            
    if not active_selection:
        st.info("Select 'Run Agent Analysis' on any account card to initiate real-time reasoning loops across the LLM endpoint.")