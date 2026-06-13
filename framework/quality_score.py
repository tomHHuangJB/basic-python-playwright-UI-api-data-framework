from dataclasses import dataclass

@dataclass(frozen=True)
class QualitySignals:
    health_passed: bool
    ui_passed: bool
    api_passed: bool
    runtime_error_count: int
    p95_latency_ms: float

def quality_score(signals: QualitySignals) -> int:
    score = 100
    if not signals.health_passed:
        score -= 35
    if not signals.ui_passed:
        score -= 20
    if not signals.api_passed:
        score -= 25
    score -= min(signals.runtime_error_count * 5, 20)
    if signals.p95_latency_ms > 1000:
        score -= 10
    return max(0, score)