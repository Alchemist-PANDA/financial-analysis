"""
SCORING ENGINE
Converts computed metrics into sub-scores and total health score.
Deterministic. Supports both Credit Mode and Investment Mode.
"""

from .constants import (
    SCORING_MODEL_VERSION,
    CREDIT_MODE_WEIGHTS,
    INVESTMENT_MODE_WEIGHTS,
    BUSINESS_QUALITY_WEIGHTS,
    CASH_FLOW_WEIGHTS,
    SAFETY_WEIGHTS,
    GROWTH_WEIGHTS,
    VALUATION_WEIGHTS,
    THRESHOLDS,
    HEALTH_BANDS,
    INVERTED_METRICS,
)


def score_metric(metric_name: str, value: float, weight: int) -> float:
    """
    Maps a metric value to a score between 0 and weight.
    Uses linear interpolation between thresholds.
    """
    if metric_name not in THRESHOLDS:
        return weight / 2

    excellent, good, weak = THRESHOLDS[metric_name]
    inverted = metric_name in INVERTED_METRICS or excellent < weak

    if inverted:
        if value <= excellent:
            return float(weight)
        if value >= weak:
            return 0.0
        ratio = (weak - value) / max(weak - excellent, 0.001)
        return ratio * weight

    if value >= excellent:
        return float(weight)
    if value <= weak:
        return 0.0
    ratio = (value - weak) / max(excellent - weak, 0.001)
    return ratio * weight


def _score_pillar(metrics: dict, weights: dict) -> dict:
    scores = {k: score_metric(k, metrics.get(k, 0), v) for k, v in weights.items()}
    total = sum(scores.values())
    return {"score": round(total, 1), "breakdown": scores}


def score_business_quality(metrics: dict) -> dict:
    return _score_pillar(metrics, BUSINESS_QUALITY_WEIGHTS)


def score_cash_flow(metrics: dict) -> dict:
    return _score_pillar(metrics, CASH_FLOW_WEIGHTS)


def score_safety(metrics: dict) -> dict:
    return _score_pillar(metrics, SAFETY_WEIGHTS)


def score_growth(metrics: dict) -> dict:
    return _score_pillar(metrics, GROWTH_WEIGHTS)


def score_valuation(metrics: dict) -> dict:
    return _score_pillar(metrics, VALUATION_WEIGHTS)


def aggregate_health_score(sub_scores: dict, mode: str = "credit") -> dict:
    """
    Aggregates sub-scores into weighted total.
    Returns health_score (0-100), health_band, color, and version.
    """
    weights = CREDIT_MODE_WEIGHTS if mode == "credit" else INVESTMENT_MODE_WEIGHTS
    pillar_maxes = {
        "business_quality": sum(BUSINESS_QUALITY_WEIGHTS.values()),
        "cash_flow": sum(CASH_FLOW_WEIGHTS.values()),
        "safety": sum(SAFETY_WEIGHTS.values()),
        "growth": sum(GROWTH_WEIGHTS.values()),
        "valuation": sum(VALUATION_WEIGHTS.values()),
    }

    weighted_score = 0.0
    total_weight = sum(weights.values())

    for pillar, pillar_weight in weights.items():
        if pillar_weight == 0:
            continue
        raw = sub_scores.get(pillar, {}).get("score", 0)
        max_raw = pillar_maxes.get(pillar, 25)
        normalized = (raw / max(max_raw, 0.001)) * 100
        weighted_score += (normalized * pillar_weight) / total_weight

    health_score = round(min(max(weighted_score, 0), 100))
    band, color = "Unknown", "gray"
    for low, high, label, c in HEALTH_BANDS:
        if low <= health_score <= high:
            band, color = label, c
            break

    return {
        "health_score": health_score,
        "health_band": band,
        "color": color,
        "scoring_model_version": SCORING_MODEL_VERSION,
        "scoring_mode": mode,
    }
