# Oliv Dormant Pipeline Revival Agent

A small prototype exploring a gap in Oliv's product surface: **dormant/lost pipeline**. While Oliv captures deal intelligence from live conversations, this agent re-evaluates *historically dead deals* against new account signals to decide which ones are actually worth reviving.

**Live app:** [add link]
**Walkthrough (2 min):** [add link]

## What it does

For each dormant deal, the agent is given the original lost/stalled reason and a recent account signal, then makes a live call to Gemini to decide whether that signal actually neutralizes the original blocker, or is just noise (a hiring announcement, an office move, etc).

Every decision, and the reasoning behind it, is written to a persisted trace (`decision_log.json`) rather than disappearing after the inference. The idea: the "why" behind a revival call should be auditable later, not a one-shot output.

## Design choice worth noting

The system prompt is deliberately skeptical. It defaults to `LOW` / `NOT_RECOMMENDED` unless a signal directly addresses the specific reason the deal died. An agent that flags too many false positives burns rep trust fast, so precision is prioritized over recall here.

## What's real vs mocked

- **The reasoning is live** — every evaluation is a real Gemini API call, not a scripted output.
- **The deal data is mocked** — `MOCK_DEALS` in `interface.py` is a hand-built dataset of six deals, built to demonstrate the pattern, not pulled from a real CRM.
- In production, deal history would come from the CRM (or Oliv's own captured deal intelligence), and the "recent signal" side would need external sources: news/funding APIs, job-change tracking, intent-data providers, or company blog/RSS feeds.

## Stack

Streamlit + Gemini 2.5 Flash (`google-genai`). No database — the trace is a flat JSON file for simplicity in this prototype.

## Run it locally

```
pip install -r requirements.txt
# add GEMINI_API_KEY to .streamlit/secrets.toml
streamlit run interface.py
```
