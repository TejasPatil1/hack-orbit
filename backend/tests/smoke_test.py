"""
Person 3 smoke test -- validates all 5 demo scenarios (spec section 12).

Run: python tests/smoke_test.py
  or: python -m pytest tests/smoke_test.py -v

Asserts spec-required properties for each scenario so any regression
is immediately visible before the demo. Must pass with no API key.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.schemas.telemetry import DEMO_TELEMETRY, DEMO_CONJUNCTION, DEMO_KP
from app.api.ai import (
    _stub_health_score,
    _stub_check_anomaly,
    _stub_failure_prob,
    _stub_collision_risk,
    _build_maneuver_actions,
)
from app.services.ai_copilot import copilot as _copilot_svc
from app.services.ai_copilot.context_builder import build_context as _build_context

PASS = "[PASS]"
FAIL = "[FAIL]"
_failures = []


def check(name: str, condition: bool, detail: str = ""):
    if condition:
        print(f"  {PASS} {name}")
    else:
        print(f"  {FAIL} {name}  {detail}")
        _failures.append(name)


def run_scenario(scenario: str) -> dict:
    readings = dict(DEMO_TELEMETRY[scenario])
    score, status = _stub_health_score(readings)
    is_anomaly, flagged, anomaly_score = _stub_check_anomaly(readings)
    failure_prob, top_driver = _stub_failure_prob(score)

    conj_data = DEMO_CONJUNCTION.get(scenario)
    risk_level, risk_score, maneuver_advised = "low", 10, False
    time_to_conj = 99.0
    if conj_data:
        risk_level, risk_score, maneuver_advised = _stub_collision_risk(
            conj_data["miss_distance_km"],
            conj_data["relative_velocity_km_s"],
            conj_data["time_to_conjunction_hours"],
        )
        time_to_conj = conj_data["time_to_conjunction_hours"]

    kp = DEMO_KP[scenario]
    posture, actions, summary = _build_maneuver_actions(
        score, failure_prob, flagged, risk_level, maneuver_advised, kp, time_to_conj
    )

    conj_obj_id = conj_data["object_id"] if conj_data else None
    context = _build_context(
        telemetry=readings,
        health_score=score,
        status=status,
        is_anomaly=is_anomaly,
        flagged_features=flagged,
        anomaly_score=anomaly_score,
        failure_probability=failure_prob,
        top_driver=top_driver,
        collision_risk_level=risk_level,
        risk_score=risk_score,
        maneuver_advised=maneuver_advised,
        time_to_conjunction_hours=time_to_conj,
        conjunction_object_id=conj_obj_id,
        kp_index=kp,
        posture=posture,
        actions=actions,
    )
    copilot_reply, _ = _copilot_svc.chat("What should I do right now?", context)

    return {
        "score": score, "status": status,
        "is_anomaly": is_anomaly, "flagged": [f["feature"] for f in flagged],
        "failure_prob": failure_prob, "top_driver": top_driver,
        "risk_level": risk_level, "maneuver_advised": maneuver_advised,
        "posture": posture, "actions": actions,
        "copilot_reply": copilot_reply,
    }


def test_healthy():
    print("\n-- Scenario: healthy")
    r = run_scenario("healthy")
    print(f"  score={r['score']}  anomaly={r['is_anomaly']}  failure={r['failure_prob']}%  posture={r['posture']}")
    check("score in 85-95",   85 <= r["score"] <= 95,  f"got {r['score']}")
    check("is_anomaly False",  r["is_anomaly"] is False)
    check("failure < 25%",     r["failure_prob"] < 25,  f"got {r['failure_prob']}")
    check("posture nominal",   r["posture"] == "nominal")
    check("copilot non-empty", len(r["copilot_reply"]) > 10)


def test_anomaly():
    print("\n-- Scenario: anomaly")
    r = run_scenario("anomaly")
    print(f"  score={r['score']}  anomaly={r['is_anomaly']}  failure={r['failure_prob']}%  flagged={r['flagged']}")
    check("is_anomaly True",       r["is_anomaly"] is True)
    check("thruster_temp flagged", "thruster_temp" in r["flagged"])
    check("score < 70",            r["score"] < 70,         f"got {r['score']}")
    check("failure > 60%",         r["failure_prob"] > 60,  f"got {r['failure_prob']}")
    check("posture critical",      r["posture"] == "critical")


def test_debris():
    print("\n-- Scenario: debris")
    r = run_scenario("debris")
    print(f"  risk_level={r['risk_level']}  maneuver_advised={r['maneuver_advised']}")
    check("risk high or critical", r["risk_level"] in ("high", "critical"), f"got {r['risk_level']}")
    check("maneuver_advised True",  r["maneuver_advised"] is True)


def test_solar_storm():
    print("\n-- Scenario: solar_storm")
    r = run_scenario("solar_storm")
    kp = DEMO_KP["solar_storm"]
    delay_actions = [a for a in r["actions"] if "delay" in a["action"].lower()]
    print(f"  score={r['score']}  kp={kp}  delay_actions={len(delay_actions)}")
    check("Kp >= 7",                kp >= 7)
    check("delay-maneuver fires",   len(delay_actions) > 0, "storm-gating did not fire")
    check("score < 55",             r["score"] < 55, f"got {r['score']}")


def test_resolution():
    print("\n-- Scenario: resolution")
    r_anomaly = run_scenario("anomaly")
    r_res = run_scenario("resolution")
    print(f"  anomaly_score={r_anomaly['score']} -> resolution_score={r_res['score']}")
    check("recovered score > anomaly score",
          r_res["score"] > r_anomaly["score"],
          f"{r_res['score']} not > {r_anomaly['score']}")


def test_whatif():
    print("\n-- What-If: reduce thruster 340 -> 40")
    before = dict(DEMO_TELEMETRY["anomaly"])
    after = {**before, "thruster_temp": 40.0}
    before_score, _ = _stub_health_score(before)
    after_score, _ = _stub_health_score(after)
    print(f"  before={before_score}  after={after_score}  delta={after_score - before_score:+d}")
    check("what-if improves score", after_score > before_score,
          f"{after_score} not > {before_score}")


def test_copilot_fallback():
    print("\n-- Copilot fallback (no API key needed)")
    r = run_scenario("solar_storm")
    reply = r["copilot_reply"]
    print(f"  reply[:100]: {reply[:100]}")
    check("fallback non-empty", len(reply) > 20)
    check("mentions storm or Kp",
          any(word in reply.lower() for word in ["storm", "kp", "g3", "maneuver"]))


if __name__ == "__main__":
    SEP = "=" * 50
    print(SEP)
    print("  Hack Orbit - Person 3 Smoke Test")
    print(SEP)

    test_healthy()
    test_anomaly()
    test_debris()
    test_solar_storm()
    test_resolution()
    test_whatif()
    test_copilot_fallback()

    print(f"\n{SEP}")
    if _failures:
        print(f"  FAILED: {len(_failures)} assertion(s)")
        for f in _failures:
            print(f"    - {f}")
        sys.exit(1)
    else:
        print("  ALL CHECKS PASSED")
    print(f"{SEP}\n")
