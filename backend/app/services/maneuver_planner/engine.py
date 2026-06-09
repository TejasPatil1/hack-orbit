"""
Maneuver recommendation engine — rules + ML signals (spec §8).

Inputs:
  health_score     : int 0–100 (from scorer service)
  failure_prob     : int 0–100 (from predictor service)
  flagged_features : list[dict] (from detector service)
  risk_level       : str  (from collision engine)
  maneuver_advised : bool (from collision engine)
  kp_index         : float (from weather endpoint)
  time_to_conj_h   : float (hours to closest approach, 99 if no conjunction)

Returns: (posture: str, actions: list[dict], summary: str)

The storm-gating rule (§8, step 1) is the single most impressive
reasoning in the product — it shows the system weighing two risks
against each other rather than reacting to one signal.
"""
from __future__ import annotations
from typing import List, Tuple


def recommend(
    health_score: int,
    failure_prob: int,
    flagged_features: List[dict],
    risk_level: str = "low",
    maneuver_advised: bool = False,
    kp_index: float = 2.0,
    time_to_conj_h: float = 99.0,
) -> Tuple[str, List[dict], str]:
    """
    Returns (posture, actions, summary).
    Actions are priority-sorted; priority 1 = most urgent.
    """
    actions: List[dict] = []
    flagged_names = {f["feature"] for f in flagged_features}
    priority = 1

    # Determine overall posture from failure probability
    if failure_prob >= 70:
        posture = "critical"
    elif failure_prob >= 40:
        posture = "elevated"
    else:
        posture = "nominal"

    # ── 1. Conjunction handling, gated by space weather ──────────────────────
    # This is the key reasoning moment: if a burn is needed AND a storm is
    # active, we DELAY rather than compound the risk. (spec §8, step 1)
    if maneuver_advised and time_to_conj_h < 6.0:
        if kp_index >= 5.0:
            actions.append({
                "priority": priority,
                "action": f"DELAY avoidance burn — wait for storm to pass (Kp={kp_index})",
                "reason": (
                    f"Firing thrusters during Kp≥{int(kp_index)} storm risks "
                    f"compounding the existing anomaly. Wait for Kp < 5."
                ),
            })
        else:
            actions.append({
                "priority": priority,
                "action": f"Plan avoidance burn — conjunction in {time_to_conj_h:.1f}h",
                "reason": (
                    f"Collision risk {risk_level} with {time_to_conj_h:.1f}h to "
                    f"closest approach. Maneuver window closing."
                ),
            })
        priority += 1

    # ── 2. Storm posture ──────────────────────────────────────────────────────
    if kp_index >= 5.0:
        actions.append({
            "priority": priority,
            "action": "Enter radiation-safe configuration",
            "reason": (
                f"Kp {kp_index} exceeds G2 threshold — elevated particle flux "
                f"risks single-event upsets in electronics."
            ),
        })
        priority += 1

    # ── 3. Per-subsystem actions from flagged features ────────────────────────
    if "thruster_temp" in flagged_names:
        actions.append({
            "priority": priority,
            "action": "Reduce thruster duty cycle to 30%",
            "reason": "Thruster temperature above safe limit — thermal runaway risk",
        })
        priority += 1
        actions.append({
            "priority": priority,
            "action": "Monitor thruster temperature every 15 minutes",
            "reason": "Active thermal anomaly requires continuous tracking",
        })
        priority += 1

    if "battery_voltage" in flagged_names or "battery_temp" in flagged_names:
        actions.append({
            "priority": priority,
            "action": "Switch to power-safe mode — shed non-essential loads",
            "reason": "Battery anomaly detected — prevent deep discharge or thermal event",
        })
        priority += 1

    if "gyro_rate" in flagged_names or "reaction_wheel_rpm" in flagged_names:
        actions.append({
            "priority": priority,
            "action": "Engage attitude stabilization backup",
            "reason": "Attitude control anomaly — risk of uncontrolled tumble",
        })
        priority += 1

    if "solar_panel_current" in flagged_names:
        actions.append({
            "priority": priority,
            "action": "Check solar panel orientation and shadowing",
            "reason": "Current drop may indicate panel damage or eclipse entry",
        })
        priority += 1

    if "radiation_dose" in flagged_names:
        actions.append({
            "priority": priority,
            "action": "Enable radiation hardening mode on avionics",
            "reason": "Elevated radiation dose — risk of memory corruption",
        })
        priority += 1

    # ── 4. General critical posture ───────────────────────────────────────────
    if failure_prob >= 70:
        already_safe_mode = any("safe-mode" in a["action"].lower() for a in actions)
        if not already_safe_mode:
            actions.append({
                "priority": priority,
                "action": "Prepare contingency safe-mode sequence",
                "reason": f"Failure probability {failure_prob}% exceeds critical threshold (70%)",
            })
            priority += 1

    # Summary line
    summaries = {
        "critical": "Critical posture — immediate action required.",
        "elevated": "Elevated posture — close monitoring required.",
        "nominal": "Nominal posture — no immediate action required.",
    }

    return posture, actions, summaries[posture]
