"""Regression tests for ``scripts/pipeline/transform/immunogenicity_stats.py``."""

from __future__ import annotations

import math
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from pipeline.transform.immunogenicity_stats import (  # noqa: E402
    power_gmc_ni,
    simulate_gmc_ni_pass_rate,
)


def test_simulation_is_reproducible_with_seed():
    a = simulate_gmc_ni_pass_rate(340, 0.9, 1.0, margins=(2 / 3, 0.5), n_sim=5_000, seed=7)
    b = simulate_gmc_ni_pass_rate(340, 0.9, 1.0, margins=(2 / 3, 0.5), n_sim=5_000, seed=7)
    assert a == b
    assert a["pass_rate"][0.5] >= a["pass_rate"][2 / 3]


def test_simulation_agrees_with_analytic_power():
    sim = simulate_gmc_ni_pass_rate(340, 0.9, 1.0, n_sim=40_000, seed=20261119)
    analytic = power_gmc_ni(340, 0.9, 2 / 3, 1.0)
    assert math.isclose(sim["pass_rate"][2 / 3], analytic, abs_tol=0.01)
    lo, hi = sim["expected_ci"]
    assert lo < 0.9 < hi


@pytest.mark.parametrize(
    "kwargs",
    [
        {"n_eval_per_arm": 1, "ratio_expected": 0.9, "sigma_ln": 1.0},
        {"n_eval_per_arm": 100, "ratio_expected": 0.0, "sigma_ln": 1.0},
        {"n_eval_per_arm": 100, "ratio_expected": 0.9, "sigma_ln": -1.0},
        {"n_eval_per_arm": 100, "ratio_expected": 0.9, "sigma_ln": 1.0, "margins": (0.0,)},
        {"n_eval_per_arm": 100, "ratio_expected": 0.9, "sigma_ln": 1.0, "n_sim": 0},
    ],
)
def test_simulation_rejects_invalid_input(kwargs):
    with pytest.raises(ValueError):
        simulate_gmc_ni_pass_rate(**kwargs)
