from framework.quality_score import QualitySignals, quality_score

def test_quality_score_penalizes_runtime_failures():
    assert quality_score(QualitySignals(True, True, True, 0, 250)) == 100
    assert quality_score(QualitySignals(True, False, True, 2, 250)) == 70
    assert quality_score(QualitySignals(False, True, True, 0, 250)) == 65
