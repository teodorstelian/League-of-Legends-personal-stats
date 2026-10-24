import pytest
from scripts.investigate_benchmarks import fit_slope


def test_phase_fit_requires_both_outcomes_and_duration_variation():
    assert fit_slope([]) is None
    assert fit_slope([{'win': True, 'minutes': 20, 'raw': 500}] * 50) is None
    assert fit_slope([{'win': win, 'minutes': 30, 'raw': 500} for win in (True, False) for _ in range(20)]) is None


def test_phase_fit_recovers_shrunk_known_relationship():
    rows = [{'win': win, 'minutes': minutes, 'raw': 100 * (minutes / 30) ** 2 - 1}
            for win in (True, False) for minutes in (20, 40) for _ in range(20)]
    assert fit_slope(rows) == pytest.approx(2 * 80 / 180)
    constant = [{**row, 'raw': 500} for row in rows]
    assert fit_slope(constant) == pytest.approx(0)
