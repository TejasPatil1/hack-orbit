"""
AI Copilot service -LLM call with deterministic fallback (spec §6.3).

Provider priority: AWS Bedrock -> Anthropic API -> deterministic fallback.
The fallback MUST work perfectly without any API key or network.
The demo must survive: no internet, quota failure, timeout, invalid key.
Never allow this module to raise -always return a useful response.
"""
from __future__ import annotations
import logging
import os
from datetime import datetime, timezone
from typing import Tuple

from app.services.ai_copilot.prompt_builder import (
    COPILOT_SYSTEM_PROMPT,
    REPORT_SYSTEM_PROMPT,
    build_chat_prompt,
    build_report_prompt,
)

logger = logging.getLogger(__name__)

_HF_MODEL = os.getenv("HF_MODEL", "moonshotai/Kimi-K2.6:novita")
_HF_BASE_URL = "https://router.huggingface.co/v1"
_BEDROCK_MODEL = os.getenv("BEDROCK_MODEL", "openai.gpt-oss-120b-1:0")
_BEDROCK_REGION = os.getenv("AWS_REGION_NAME", os.getenv("AWS_DEFAULT_REGION", "us-east-1"))
_CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-6")
_TIMEOUT = 12


def _call_hf(system_prompt: str, user_message: str, max_tokens: int) -> str:
    """Calls HuggingFace router (OpenAI-compatible). Raises on any failure."""
    from openai import OpenAI
    client = OpenAI(base_url=_HF_BASE_URL, api_key=os.getenv("HF_TOKEN"))
    completion = client.chat.completions.create(
        model=_HF_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        max_tokens=max_tokens,
    )
    return completion.choices[0].message.content.strip()


def _call_bedrock(system_prompt: str, user_message: str, max_tokens: int) -> str:
    """Calls AWS Bedrock Converse API. Raises on any failure."""
    import boto3
    client = boto3.client("bedrock-runtime", region_name=_BEDROCK_REGION)
    response = client.converse(
        modelId=_BEDROCK_MODEL,
        system=[{"text": system_prompt}],
        messages=[{"role": "user", "content": [{"text": user_message}]}],
        inferenceConfig={"maxTokens": max_tokens},
    )
    content = response["output"]["message"]["content"]
    text = next((b["text"] for b in content if "text" in b), None)
    if text is None:
        raise ValueError("No text block in Bedrock response")
    return text.strip()


def _has_hf() -> bool:
    return bool(os.getenv("HF_TOKEN"))


def _has_bedrock() -> bool:
    return bool(os.getenv("AWS_ACCESS_KEY_ID") or os.getenv("BEDROCK_KEY"))


def _has_anthropic() -> bool:
    key = os.getenv("ANTHROPIC_API_KEY", "")
    return bool(key) and not key.startswith("sk-ant-...")


def chat(message: str, context: dict) -> Tuple[str, str]:
    """
    Returns (reply: str, source: "llm" | "fallback").
    Never raises.
    """
    # 1. Try HuggingFace (Kimi K2.6)
    if _has_hf():
        try:
            reply = _call_hf(COPILOT_SYSTEM_PROMPT, build_chat_prompt(context, message), max_tokens=2000)
            logger.info("Copilot HF reply (%d chars, model=%s)", len(reply), _HF_MODEL)
            return reply, "llm"
        except Exception as exc:
            logger.warning("HF chat failed (%s) -trying next provider", exc)

    # 2. Try Bedrock
    if _has_bedrock():
        try:
            reply = _call_bedrock(COPILOT_SYSTEM_PROMPT, build_chat_prompt(context, message), max_tokens=200)
            logger.info("Copilot Bedrock reply (%d chars, model=%s)", len(reply), _BEDROCK_MODEL)
            return reply, "llm"
        except Exception as exc:
            logger.warning("Bedrock chat failed (%s) -trying next provider", exc)

    # 3. Try Anthropic
    if _has_anthropic():
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"), timeout=_TIMEOUT)
            response = client.messages.create(
                model=_CLAUDE_MODEL,
                max_tokens=200,
                system=COPILOT_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": build_chat_prompt(context, message)}],
            )
            reply = next(b.text for b in response.content if b.type == "text").strip()
            logger.info("Copilot Anthropic reply (%d chars)", len(reply))
            return reply, "llm"
        except Exception as exc:
            logger.warning("Anthropic chat failed (%s) -using fallback", exc)

    return _fallback_chat(message, context), "fallback"


def generate_report(context: dict) -> Tuple[str, str]:
    """
    Returns (report: str, source: "llm" | "fallback").
    Never raises.
    """
    # 1. Try HuggingFace (Kimi K2.6)
    if _has_hf():
        try:
            report = _call_hf(REPORT_SYSTEM_PROMPT, build_report_prompt(context), max_tokens=4000)
            logger.info("Incident report HF (%d chars, model=%s)", len(report), _HF_MODEL)
            return report, "llm"
        except Exception as exc:
            logger.warning("HF report failed (%s) -trying next provider", exc)

    # 2. Try Bedrock
    if _has_bedrock():
        try:
            report = _call_bedrock(REPORT_SYSTEM_PROMPT, build_report_prompt(context), max_tokens=600)
            logger.info("Incident report Bedrock (%d chars)", len(report))
            return report, "llm"
        except Exception as exc:
            logger.warning("Bedrock report failed (%s) -trying next provider", exc)

    # 3. Try Anthropic
    if _has_anthropic():
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"), timeout=20)
            response = client.messages.create(
                model=_CLAUDE_MODEL,
                max_tokens=600,
                system=REPORT_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": build_report_prompt(context)}],
            )
            report = next(b.text for b in response.content if b.type == "text").strip()
            logger.info("Incident report Anthropic (%d chars)", len(report))
            return report, "llm"
        except Exception as exc:
            logger.warning("Anthropic report failed (%s) -using fallback", exc)

    return _fallback_report(context), "fallback"


# ---------------------------------------------------------------------------
# Deterministic fallbacks -complete, sensible, storm-aware (spec §6.3)
# ---------------------------------------------------------------------------

def _fallback_chat(message: str, context: dict) -> str:
    score = context["health_score"]
    prob = context["failure_probability_pct"]
    posture = context["posture"]
    kp = context["kp_index"]
    flagged = context["flagged_features"]
    maneuver_advised = context["maneuver_advised"]
    storm_active = context["storm_active"]
    actions = context.get("_actions_full", [])

    lines = []

    if posture == "nominal":
        lines.append(f"ORBIT: All systems nominal. Health {score}/100, failure risk {prob}%.")
    elif posture == "elevated":
        lines.append(f"ORBIT: Elevated concern. Health {score}/100, failure risk {prob}%.")
    else:
        lines.append(f"ORBIT: Critical. Health {score}/100, failure risk {prob}%.")

    if flagged:
        names = ", ".join(f.split(" =")[0] for f in flagged)
        lines.append(f"Anomalies: {names}.")

    if kp >= 7:
        lines.append(f"G3 storm active (Kp {kp}) - DO NOT execute thruster burn until storm passes.")
    elif kp >= 5:
        lines.append(f"Geomagnetic activity elevated (Kp {kp}) - caution on maneuvers.")

    if maneuver_advised:
        obj = context.get("conjunction_object") or "object"
        ttc = context.get("time_to_conjunction_hours")
        if storm_active:
            lines.append(f"Conjunction with {obj} in {ttc:.1f}h - burn DELAYED due to storm.")
        else:
            lines.append(f"Conjunction with {obj} in {ttc:.1f}h - avoidance burn recommended.")

    if actions:
        lines.append("Priority actions:")
        for a in sorted(actions, key=lambda x: x["priority"])[:3]:
            lines.append(f"  {a['priority']}. {a['action']}")

    return " ".join(lines) if len(lines) <= 2 else "\n".join(lines)


def _fallback_report(context: dict) -> str:
    score = context["health_score"]
    status = context["health_status"].upper()
    prob = context["failure_probability_pct"]
    posture = context["posture"].upper()
    is_anomaly = context["is_anomaly"]
    flagged = context["flagged_features"]
    anomaly_score = context["anomaly_score"]
    top_driver = context["top_failure_driver"]
    risk_level = context["collision_risk_level"].upper()
    maneuver_advised = context["maneuver_advised"]
    kp = context["kp_index"]
    satellite_id = context.get("satellite_id", "SAT-001")
    actions = context.get("_actions_full", [])

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    review = "15 minutes" if score < 50 else ("1 hour" if score < 80 else "24 hours")

    flagged_lines = "\n".join(f"  - {f}" for f in flagged) or "  None detected."
    action_lines = "\n".join(
        f"  {a['priority']}. {a['action']}"
        for a in sorted(actions, key=lambda x: x["priority"])
    ) or "  No actions required."

    return f"""HACK ORBIT -- SATELLITE INCIDENT REPORT
Generated : {now}
Satellite : {satellite_id}

SUMMARY
  Health Score     : {score}/100  [{status}]
  Anomaly Detected : {"YES" if is_anomaly else "NO"}  (score: {anomaly_score:.2f})
  Failure Risk     : {prob}%
  Posture          : {posture}

DETECTED ANOMALIES
{flagged_lines}

RISK ASSESSMENT
  Primary Driver   : {top_driver}
  Anomaly Score    : {anomaly_score:.2f} / 1.00
  Collision Risk   : {risk_level}
  Maneuver Advised : {"YES" if maneuver_advised else "NO"}
  Kp Index         : {kp}  {"[STORM ACTIVE]" if kp >= 5 else ""}

RECOMMENDED ACTIONS
{action_lines}

NEXT REVIEW
  {review}

-- Hack Orbit | Predict. Protect. Decide. --
"""
