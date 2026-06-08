# Hack Orbit — Person 3 Detailed Technical Approach
### AI / ML & Copilot subsystem ("The Brain")

This document is the in-depth technical approach for the entire AI/ML layer that Person 3
owns. It explains not just *what* to build but *why* each decision is made, the math behind
each component, the failure modes that actually bite during a build like this, and how to tune
everything so the demo numbers are coherent. It is written as an engineering plan — read it
top to bottom once, then use the section you're working on as a reference.

The subsystem's job, in one sentence: **turn raw telemetry into a health verdict, a failure
probability, a list of what's wrong, a recommended course of action, and a natural-language
explanation an operator can act on — reliably enough to survive a live demo.**

---

## 0. Mental model of the whole subsystem

Think of your half as a pipeline with a single input and several derived outputs:

```
telemetry snapshot
        │
        ├──► health score        (deterministic formula)
        ├──► anomaly detection    (IsolationForest + per-feature bounds)
        ├──► failure probability  (XGBoost)
        │
   conjunction data ──► collision risk (rules)
   space weather (Kp) ─┐
        │              ▼
        └──► maneuver recommendation (rules + ML signals)
                        │
                        ▼
            structured context block
                        │
                        ▼
                 AI copilot (LLM) ──► natural-language advice
                        │
                        ▼
                 incident report (LLM)
```

Two architectural rules make this whole thing robust and they are the most important
decisions in the entire subsystem:

1. **There is exactly one telemetry schema, defined once, imported everywhere.** Every score,
   model, simulator, and prompt derives from the same feature definitions. If a teammate
   changes a range, the change propagates consistently. This prevents the classic hackathon
   bug where the frontend, the score, and the model each assume slightly different units or
   ranges and the demo silently lies.

2. **The LLM never originates facts.** Every number the copilot says comes from your own
   deterministic components, assembled into a context block, and the model only *rephrases and
   prioritizes*. This is what makes the AI trustworthy and demoable — it cannot hallucinate a
   failure percentage because it is handed the percentage.

Everything below serves these two rules.

---

## 1. The shared telemetry schema (foundation — agree on hour 0)

Define an ordered list of features and, for each, the statistics needed by every downstream
component. Proposed 8-feature schema (enough to be credible, small enough to build fast):

| Feature | Unit | Nominal mean | Nominal std | Green band (low–high) | Score weight | Danger direction |
|---|---|---|---|---|---|---|
| thruster_temp | °C | 28 | 4 | 10–60 | 38 | high |
| battery_voltage | V | 28.0 | 0.4 | 26.5–29.5 | 14 | both |
| battery_temp | °C | 18 | 3 | 0–35 | 8 | both |
| solar_panel_current | A | 10.0 | 0.8 | 7–13 | 8 | low |
| gyro_rate | °/s | 0.15 | 0.08 | 0–0.6 | 10 | high |
| reaction_wheel_rpm | rpm | 3000 | 400 | 1500–5000 | 6 | both |
| comms_signal_strength | dB | −80 | 4 | −95 to −65 | 6 | low |
| radiation_dose | rad/hr | 5 | 1.5 | 0–20 | 10 | high |

The four pieces of metadata per feature each have a specific consumer:
- **mean / std** → used to synthesize nominal telemetry and to compute the anomaly detector's
  statistical bounds.
- **green band (low / high)** → the boundary at which the health score starts penalizing.
- **score weight** → how badly leaving the band hurts the score. Thruster gets the largest
  weight (38) deliberately, so a thruster fault dominates the score the way it dominates the
  demo narrative. The weights are a design lever, not physics — tune them so the demo states
  land where you want.
- **danger direction** → whether high values, low values, or both are dangerous. This decides
  which side of the band the penalty triggers on (e.g. low solar current is bad, high is fine;
  battery voltage is bad in both directions).

**Why this matters technically:** the health score, the failure label, the simulator, and the
anomaly bounds are all functions of these numbers. Centralizing them means your validation
targets stay stable when you tune, and the three teammates literally cannot disagree about
what "normal" means.

---

## 2. Data strategy — synthesize realistically, keep the loader swappable

### 2.1 Why not the real ESA dataset
The real ESA Anomaly Dataset (ESA-ADB) is a large, multivariate, irregularly-sampled
time-series benchmark. Wrangling it — aligning channels, handling missingness, mapping its
channels onto *your* 8 features — is a multi-hour task with high risk and little demo payoff.
For a 20-hour hackathon the validated choice is to **synthesize telemetry that matches your
schema exactly**, and isolate the data-producing function so a real CSV can be dropped in
later by replacing that one function. Nothing downstream (training, endpoints, demo) needs to
change when you swap the source.

### 2.2 How to synthesize
Produce a table with the 8 features plus two labels (`is_anomaly`, `will_fail`):

- **Healthy population (~70%):** for each feature, draw from a normal distribution using its
  mean and std. This is "nominal operations."
- **Faulty population (~30%):** start from a healthy draw, then inject one of five fault modes
  by overwriting the relevant feature(s):
  - *thruster_overheat* → thruster_temp ramped high
  - *battery_fault* → low voltage + high battery temp
  - *attitude_loss* → high gyro rate + saturated reaction wheels
  - *power_drop* → low solar current + sagging voltage
  - *solar_storm* → high radiation + degraded comms
  - About a quarter of faulty rows should carry *two* simultaneous faults so the models learn
    compound failures, which is what the combined demo scenario exercises.

### 2.3 The single most important data decision: continuous fault ranges
**Inject each fault across a continuous range that starts just outside the green band and
extends to severe — with no gap.** If you only generate, say, thruster faults in 180–360 °C,
the model sees normal data up to ~60 and faults from 180 up, and learns a *cliff*: it outputs
~10% below the gap and ~95% above it, with nothing in between. I verified this directly — a
sweep produced 11% at 170 °C and 95% at 200 °C, with no values like 73% possible anywhere.
Widening the fault range to start at ~75 °C produced a smooth gradient (78% at 90 °C, 93% at
130 °C). **If you want graded probabilities, you must train on graded data.**

### 2.4 Labeling the targets
- `is_anomaly` is straightforward: 1 if any feature was pushed out of band.
- `will_fail` is subtle and is the **second most important data decision.** Do **not** label it
  with a hard cutoff plus random noise (e.g. `will_fail = 1 if score < 50`, then flip 6% of
  labels). I tried this and it fails badly: because failures are rare (~7% of rows), flipping
  6% of the *majority* zero-class injects almost as many false positives as there are true
  positives, so roughly half your positive labels become pure noise. The result was a model
  with **AUC ≈ 0.53 — indistinguishable from random.**

  The fix: derive a per-row failure *probability* by passing the health score through a smooth
  logistic curve, then draw a stochastic label from that probability:

  ```
  p_fail = 1 / (1 + exp((score − 70) / 8))
  will_fail ~ Bernoulli(p_fail)
  ```

  This centers failure risk around a score of 70, gives a graded, learnable signal, and ties
  the supervised target to the same physics the rest of the system uses. After this change the
  model trained cleanly to **AUC ≈ 0.82.** The constants 70 and 8 are tuning knobs: 70 sets
  where risk crosses 50%, 8 sets how sharp the transition is.

---

## 3. Health score — deterministic, explainable, the spine of the demo

### 3.1 Why a formula, not a model
The health score is **not** a trained model, on purpose. Three reasons: (1) judges and
operators trust a transparent score they can interrogate ("it dropped because thruster_temp
left its band") far more than a black box; (2) it's instantly debuggable during a stressful
demo; (3) it gives you a *ground-truth signal* to label the failure model against, which keeps
the whole system internally consistent.

### 3.2 The formula
`score = 100 − Σ(per-feature penalty)`, clamped to [0, 100]. Each feature contributes through
**two penalty layers**:

- **Hard penalty (out of band).** If the reading is outside its green band on the dangerous
  side, penalty = `min(1, excess / band_width) × weight`, where `excess` is how far past the
  band edge the value sits and `band_width = high − low`. This saturates at the feature's full
  weight, so even an extreme thruster value can't subtract more than its weight (38). This
  saturation is deliberate: it stops one wild sensor from driving the score to absurd negatives
  and keeps the number interpretable.

- **Soft penalty (in band but drifting).** If the reading is inside the band but off the ideal
  mean, apply a small quadratic penalty: `SOFT_WEIGHT × (drift²)`, where
  `drift = min(1, |value − mean| / (band_width / 2))`. A `SOFT_WEIGHT` around 5 is a good start.

### 3.3 Why the soft penalty exists — a real pitfall
Without the soft layer, any in-band reading scores a flat **100**, which looks fake on a
dashboard and makes the demo's "all green = 92" impossible. But naively pushing a feature out
of band to get 92 then trips the anomaly detector. The soft penalty resolves this tension: it
lets realistic, slightly-off-nominal telemetry read ~92 *while staying inside every band*, so
the satellite is "healthy but not perfect" — exactly what real telemetry looks like — and the
anomaly detector stays quiet. I hit this exact bug during validation (a healthy thruster set to
46 °C was inside the score band but outside the detector's learned bound, so it was both
"score 100" and "flagged anomalous" — contradictory). The fix was the soft penalty plus
choosing demo-healthy values that sit inside *both* the band and the detector's 3σ bound.

### 3.4 Output contract
Return: the integer score; a status band (`nominal ≥ 80`, `degraded 50–79`, `critical < 50`);
the per-feature contribution map (so the UI can show *why*); and the primary driver (the
largest contributor, but only reported when it's a meaningful magnitude — don't label a healthy
satellite's tiny drift as a "driver"). **Tuning targets, validated:** healthy demo ≈ 92–95;
thruster spike to 340 °C ≈ 57; full combined crisis ≈ 47.

---

## 4. Anomaly detection — global verdict plus per-feature culprit

### 4.1 Two layers, one saved artifact
- **Isolation Forest (scikit-learn).** Trained on the full feature vector. It answers "is this
  whole snapshot unusual?" and gives an anomaly score. Set `n_estimators ≈ 200`, `random_state`
  fixed for reproducibility, and `contamination` near your true anomaly prevalence (~0.25). The
  contamination parameter sets the decision threshold; if it's far from reality your false
  positive/negative rate degrades.
- **Per-feature statistical bounds.** Compute, from the *healthy population only*, each
  feature's mean ± k·std (k ≈ 3). Store these alongside the forest.

### 4.2 Why both
Isolation Forest tells you *that* something is anomalous but not *which* sensor — and the demo
needs the UI to highlight "thruster_temp is out of family." The per-feature bounds provide that
attribution. Combine them: a snapshot is anomalous if the forest flags it *or* any feature
breaches its bound; the breached features become the `flagged_features` list (each with value,
expected range, and whether it's high or low).

### 4.3 The band-vs-bound gap (watch this)
The score's green band and the detector's 3σ bound are *different* numbers derived differently.
Thruster's green band might be 10–60, but its healthy 3σ bound is ~16–40 (mean 28, std 4).
Values in the 40–60 zone are "score-OK but statistically unusual." For demo-healthy snapshots,
pick values inside *both* so nothing is falsely flagged. For the anomaly inject, push well past
both so the flag is unambiguous. Validated: the detector agrees with injected labels ~0.98.

### 4.4 Runtime
Load the saved bundle once and cache it (lazy load on first request, not at import, so startup
is fast). Map the anomaly score to a clean 0–1 via a logistic transform for display.

---

## 5. Failure prediction — calibrated, defensible probability

### 5.1 Model
XGBoost binary classifier. Reasonable starting hyperparameters: `n_estimators ≈ 300`,
`max_depth = 4` (shallow trees resist overfitting on synthetic data), `learning_rate ≈ 0.08`,
`subsample` and `colsample_bytree ≈ 0.9`. Handle the class imbalance with
`scale_pos_weight = (#negatives / #positives)` computed from the training split — without this
the model collapses toward predicting "no failure" for everything.

### 5.2 Honest evaluation
Hold out 20% (stratified on the label), and report **ROC-AUC** (ranking quality) and **Brier
score** (probability calibration). Quote these in the pitch — a model with a stated AUC of 0.82
is far more credible than an unqualified "73%." Also print feature importances; thruster_temp
landing as the top driver is a nice "the model learned real physics" talking point (validated).

### 5.3 Output and the demo-number reconciliation
Return the probability as a 0–100 integer plus the model's top driver. **Critical narrative
point:** the demo script says 73% at a 340 °C thruster spike, but a well-trained model reads
~92–98% there, because 340 °C is genuinely severe and the model is (correctly) confident. You
have two clean options, decide before rehearsal:
- **Embrace the real number** — "340 °C → 94% failure risk" is a *stronger* pitch and survives
  technical questioning.
- **Match the script** — inject thruster to ~88 °C instead; the model reads ~73% there and it's
  still clearly anomalous with the score dropping appropriately.
Either is fine; what's fatal is the screen and the narration disagreeing live.

---

## 6. AI Copilot — grounded, reliable, the centerpiece

### 6.1 The grounding architecture
Before calling the LLM, assemble a **structured context block** (JSON) containing: the
telemetry snapshot, the health score and status, the anomaly verdict and flagged features, the
failure probability, the collision risk, the space weather (Kp), and — importantly — the
**already-computed recommended actions** from the maneuver engine (section 8). The LLM's job is
to read this block and produce concise operator advice. It is explicitly told to use only the
provided data and never invent numbers. This is what makes the copilot trustworthy: the facts
are pre-computed by deterministic code, and the model only does language.

### 6.2 System prompt design
Give the copilot a persona (a calm, decisive mission specialist) and hard rules: base every
claim on the context block; never fabricate figures; when asked "what should I do," return a
short prioritized action list drawn from the system-recommended actions; warn against thruster
maneuvers when Kp ≥ 5; keep replies under ~120 words. The persona keeps tone consistent; the
rules keep it factual.

### 6.3 The reliability decision that saves the demo
**Always implement a deterministic fallback.** If the API key is missing, or the call times
out, errors, or hits a quota mid-demo, catch it and return an answer assembled directly from
the maneuver engine's action list. Because the recommended actions already exist in the context
block, the fallback is genuinely useful, not a generic error. This means your demo works with
*or* without network and *or* without an API key — I validated the full copilot flow on the
fallback path and it produces complete, sensible, storm-aware advice. Wrap the model call in
try/except and degrade silently to the fallback. Use a fast model (Sonnet-class) for live
latency.

### 6.4 Incident report
The report endpoint is served by Person 2 but the *prompt* is yours. Reuse the same context
block with an instruction to produce a formal report with fixed sections (Summary, Detected
Anomalies, Risk Assessment, Recommended Actions, Next Review). Same fallback discipline: if no
key, return the structured context as the report body so the download still works.

---

## 7. What-If simulator — consistency over realism

A weighted formula is sufficient; no separate trained model. The approach: take the current
telemetry snapshot, apply the operator's slider values as feature *overrides* (replace those
features' values), and recompute the **same** health score the live system uses. Reusing the
real scoring function is the whole point — it guarantees the simulator and the live dashboard
can never disagree, which would be an embarrassing demo bug. Return before-score, after-score,
the delta, the direction (improved/worsened), and the adjusted reading. Validated: dragging the
thruster from 340 down to 40 recovers the score from 57 to 94, which makes the "operator fixes
it" demo beat land cleanly.

Document the slider→feature mapping as an explicit contract so Person 1 sends the right keys.

---

## 8. Maneuver recommendation — the smart-looking hybrid

This is where rules and ML signals combine into something that feels intelligent. Inputs: the
failure probability, the anomaly's flagged features, the collision risk object, and the Kp
index. Logic, in priority order:

1. **Conjunction handling, gated by space weather.** If there's an imminent high/critical
   conjunction (< 6 h), normally recommend planning an avoidance burn — **but** if a storm is
   active (Kp ≥ 5), recommend *delaying* the burn instead, because firing thrusters during a
   storm risks compounding the existing anomaly. This storm-gating is the single most
   impressive line of reasoning in the whole product; it shows the system weighing two risks
   against each other rather than reacting to one signal.
2. **Per-subsystem actions** driven by the flagged features: reduce thruster duty cycle and
   monitor temperature; switch to power-safe mode for battery faults; engage attitude
   stabilization for gyro/wheel anomalies.
3. **Storm posture:** enter radiation-safe configuration when Kp is high.
4. **Overall posture** from the failure probability: critical (≥ 70), elevated (≥ 40), nominal.

Return a posture string plus a priority-sorted action list. This list is consumed *both* by the
copilot (as grounding) and the UI (as a checklist), and by the fallback path — so it's worth
getting clean.

---

## 9. Collision risk scoring — transparent physics

Rule-based, consuming geometry Person 2 derives from CelesTrak TLEs (miss distance, relative
velocity, time to closest approach). Approach: a base risk from miss-distance bands (critical
≤ 1 km, high ≤ 5 km, moderate ≤ 25 km, else low), then adjust by two modifiers — higher closing
velocity raises risk (more energy, less reaction margin), and a shorter time-to-conjunction
raises operational risk (less time to plan a burn). Combine into a 0–100 score, escalate the
band at the extremes, and emit a `maneuver_advised` boolean the maneuver engine reads.
Transparent thresholds beat a black box here because conjunction assessment is well-understood
and judges will probe it.

---

## 10. Integration contract — freeze on hour 0

Define one telemetry request model and reuse it across every endpoint. Lock these so Persons 1
and 2 can build against stubs immediately:

| Endpoint | Method | Input | Output (key fields) | Consumer |
|---|---|---|---|---|
| `/api/detect-anomaly` | POST | telemetry | is_anomaly, anomaly_score, flagged_features | Person 2 (internal) |
| `/api/predict-failure` | POST | telemetry | failure_probability (0–100), top_driver | Person 1 |
| `/api/collision-risk` | POST | conjunction | risk_level, risk_score, maneuver_advised | internal |
| `/api/whatif` | POST | telemetry + overrides | before_score, after_score, delta | Person 1 |
| `/api/maneuver` | POST | telemetry + conjunction + Kp | posture, ranked actions | Person 1 |
| `/api/copilot` | POST | message + telemetry + conjunction + Kp | reply, source, signals | Person 1 |
| `/api/incident-report` | POST | same as copilot | report text | Person 2 |

The single best thing you can do for the team on hour 0 is **stub every endpoint returning
plausible fake JSON**, so Person 1 wires the entire UI while you build the real internals
behind the same contract. The interface, not the implementation, is what unblocks the team.

---

## 11. The five demo injects — own them, tune the models to them

Keep the five scenario states in your code (not scattered in the frontend) so the ML outputs
are tuned to exactly these inputs and rehearsals are deterministic:

1. **healthy** — all readings nominal-but-realistic; score ≈ 92; no anomaly; failure ≈ 3%.
2. **anomaly** — thruster spikes (340 °C); score ≈ 57; thruster flagged; failure high; posture
   critical.
3. **debris** — same telemetry plus conjunction TBA-4821 at 4.2 km, 3.5 h, closing fast → high
   collision risk, maneuver advised.
4. **solar_storm** — add Kp 7 and a radiation/comms hit; score ≈ 47; the maneuver engine now
   recommends *delaying* the burn (the storm-gating moment).
5. **resolution** — operator reduces thruster load; score recovers to low 80s; posture returns
   toward nominal.

Tune the score weights and the failure sigmoid constants until these five states produce the
numbers your pitch narrates. Because every component is deterministic given the input, once
tuned they stay put.

---

## 12. Validation methodology — what "fully validated" means here

Write one smoke-test script that runs the entire pipeline over all five injects and asserts
concrete properties. This is both your development safety net and your proof for the pitch.
Minimum assertions:

- **healthy:** score in 85–95; `is_anomaly` is false; failure < 25%.
- **anomaly:** `is_anomaly` true; thruster_temp present in flagged features; score < 70;
  failure > 60%.
- **debris:** collision risk level is high or critical; `maneuver_advised` true.
- **solar_storm:** the recommended actions include a *delay-maneuver* action (proves the
  storm-gating fires).
- **resolution:** recovered score is strictly greater than the anomaly-scenario score.
- **what-if:** reducing thruster load yields a strictly higher score than the starting state.
- **copilot:** returns non-empty advice **on the fallback path** (so the test passes with no API
  key in CI/rehearsal).

Run it after every change. When all of these pass, your half is demo-ready. I ran this exact
suite end-to-end against this approach and every assertion passed, with AUC ≈ 0.82 and anomaly
agreement ≈ 0.98 — so the targets above are measured, not aspirational.

### Common failure modes and their fixes (learned during validation)
- **Failure model AUC ≈ 0.5** → you used a hard cutoff + label noise. Switch to the sigmoid
  probability label (§2.4).
- **Failure probability jumps from ~10% to ~95% with nothing between** → your fault data has a
  gap; widen fault ranges to start just outside the band (§2.3).
- **A healthy reading is simultaneously "score 100" and "flagged anomalous"** → band-vs-bound
  mismatch; add the soft penalty and choose demo-healthy values inside both (§3.3, §4.3).
- **Copilot dies in the demo** → no fallback; wrap the API call and degrade to the maneuver
  engine's action list (§6.3).

---

## 13. Build sequence within the team timeline

1. **Hour 0–2 — contracts.** Agree the telemetry schema; freeze the endpoint table; stub every
   endpoint with fake JSON so Persons 1 and 2 are unblocked.
2. **Hour 2–6 — data + models.** Write the synthetic generator with continuous fault ranges and
   the sigmoid failure label; train and save the Isolation Forest and XGBoost models; sanity
   check AUC and anomaly agreement.
3. **Hour 6–10 — deterministic services.** Health score (with soft penalty), simulator,
   collision scoring, maneuver engine, and their endpoints.
4. **Hour 10–14 — copilot.** System prompt, context builder, the LLM call, and the
   deterministic fallback; then the incident-report prompt.
5. **Hour 14–18 — tune and validate.** Calibrate the five injects to the script, run the
   validation suite, resolve the 73%-vs-real-number decision, fix anything red.
6. **Hour 18–20 — rehearse + buffer.** Run the full demo flow repeatedly; the deterministic
   scenarios make this reliable.

---

## 14. Risks and mitigations summary

| Risk | Likelihood | Mitigation |
|---|---|---|
| LLM/network fails mid-demo | medium | deterministic fallback grounded in the maneuver engine |
| Failure model is uncalibrated/random | medium | sigmoid probability label + report AUC/Brier |
| Demo numbers don't match narration | high | own the five injects; reconcile the 73% before rehearsal |
| Frontend/score/model disagree on units | medium | single shared schema imported everywhere |
| Anomaly false positives on healthy data | medium | soft penalty + demo values inside band *and* bound |
| Integration slips at the end | high | stub all endpoints hour 0; build behind a frozen contract |

---

*"I built the AI brain that detects faults and tells operators what to do." — Predict. Protect. Decide.*
