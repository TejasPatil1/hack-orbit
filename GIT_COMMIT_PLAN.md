# Hack Orbit — Remaining Git Commits (Parts 2, 3, 4)

Commit 1 is already pushed. Run these commands in order to push the remaining 3 parts.
Each commit tells one chapter of the Person-3 story for the judges.

---

## Commit 2: Deterministic Services — Collision Engine + Storm-Gated Maneuver Planner

```powershell
cd c:/Users/tp396/Desktop/hack_orbit

git add backend/app/services/collision_engine/__init__.py `
        backend/app/services/collision_engine/risk_scorer.py `
        backend/app/services/maneuver_planner/__init__.py `
        backend/app/services/maneuver_planner/engine.py

git commit -m "feat(services): collision risk engine + storm-gated maneuver planner

- collision_engine/risk_scorer.py: probability-of-collision model using
  Gaussian hard-body miss-distance formula; outputs LOW/MEDIUM/HIGH/CRITICAL
- maneuver_planner/engine.py: 6 action categories with full storm-gating rule:
  Kp>=5 AND maneuver_advised AND time<6h -> DELAY burn (key demo moment)
- All outputs are deterministic and explainable — no LLM dependency
- Both services lazy-load with graceful no-data fallbacks"

git push origin main
```

---

## Commit 3: AI Copilot — Kimi K2.6 (HuggingFace) with Deterministic Fallback

```powershell
cd c:/Users/tp396/Desktop/hack_orbit

git add backend/app/services/ai_copilot/__init__.py `
        backend/app/services/ai_copilot/context_builder.py `
        backend/app/services/ai_copilot/copilot.py `
        backend/app/services/ai_copilot/prompt_builder.py

git commit -m "feat(copilot): Kimi K2.6 via HuggingFace router with 3-level fallback

- context_builder.py: assembles grounding dict from all deterministic services;
  LLM never originates facts — it only narrates what the engines computed
- prompt_builder.py: COPILOT_SYSTEM_PROMPT + REPORT_SYSTEM_PROMPT templates
- copilot.py: provider chain HuggingFace (Kimi K2.6 novita) -> Bedrock
  (openai.gpt-oss-120b-1:0) -> Anthropic -> deterministic fallback
- Kimi K2.6 is a reasoning model: max_tokens=2000 (chat), 4000 (report)
  to accommodate internal thinking budget before text output
- Deterministic fallback is storm-aware and produces full incident reports
  — demo survives no internet, no API key, zero degradation"

git push origin main
```

---

## Commit 4: REST API Wiring — 8 Endpoints + Live Health Scorer + Tests

```powershell
cd c:/Users/tp396/Desktop/hack_orbit

git add backend/app/api/ai.py `
        backend/app/api/health.py `
        backend/app/main.py `
        backend/tests/smoke_test.py

git commit -m "feat(api): wire 8 REST endpoints with live health scoring and smoke tests

- api/ai.py: 8 endpoints — /health-check, /telemetry, /anomaly, /failure,
  /collision-risk, /maneuver, /copilot, /incident-report, /inject-anomaly
- inject-anomaly: scenario switcher for 5 demo states (healthy/anomaly/
  debris/solar_storm/resolution) — key for live judge demo
- api/health.py: GET /api/health-score now calls compute_health_score() live
  instead of hardcoded values — consistent with all AI endpoints
- main.py: load_dotenv() at startup so HF_TOKEN + AWS creds load from .env
- _run_maneuver() wrapper: prefers maneuver_planner engine with inline fallback
- tests/smoke_test.py: 19 assertions across all 5 scenarios, all passing"

git push origin main
```

---

### Story the commit history tells the judges

| # | Commit | What it shows |
|---|--------|---------------|
| 1 | Real-world ML training | We used actual NOAA + CelesTrak datasets, not toy data |
| 2 | Deterministic engines | Collision risk + storm-gated maneuvers work without any LLM |
| 3 | AI Copilot layer | LLM narrates, never originates facts; survives offline |
| 4 | REST API + tests | Clean wiring, 19 smoke tests, 5 demo scenarios ready |
