"""Tests for deterministic UC and merit-order dispatch baselines."""

import numpy as np
import pytest

from rts96_reliability_uc.baselines import deterministic_uc_baseline, simple_merit_dispatch_baseline
from rts96_reliability_uc.data import RTS96_GENERATORS, T
from rts96_reliability_uc.scenarios import generate_vre_scenarios


@pytest.fixture(scope="module")
def scenarios():
    scen, probs = generate_vre_scenarios(0.40, n_scenarios=5, seed=0)
    return scen, probs


def test_commitment_shape(scenarios):
    scen, _ = scenarios
    comm, _ = deterministic_uc_baseline(RTS96_GENERATORS, scen)
    assert comm.shape == (len(RTS96_GENERATORS), T)


def test_commitment_binary(scenarios):
    scen, _ = scenarios
    comm, _ = deterministic_uc_baseline(RTS96_GENERATORS, scen)
    assert set(comm.flatten().tolist()).issubset({0, 1})


def test_at_least_one_unit_committed_per_hour(scenarios):
    scen, _ = scenarios
    comm, _ = deterministic_uc_baseline(RTS96_GENERATORS, scen)
    assert (comm.sum(axis=0) >= 1).all()


def test_info_dict_has_committed_hours(scenarios):
    scen, _ = scenarios
    _, info = deterministic_uc_baseline(RTS96_GENERATORS, scen)
    assert "committed_hours" in info
    assert info["committed_hours"] > 0


def test_simple_merit_returns_lolp(scenarios):
    scen, _ = scenarios
    comm, _ = deterministic_uc_baseline(RTS96_GENERATORS, scen)
    result = simple_merit_dispatch_baseline(
        RTS96_GENERATORS, comm, scen, n_samples=50, seed=0
    )
    assert "LOLP" in result
    assert 0.0 <= result["LOLP"] <= 1.0


def test_simple_merit_eens_nonnegative(scenarios):
    scen, _ = scenarios
    comm, _ = deterministic_uc_baseline(RTS96_GENERATORS, scen)
    result = simple_merit_dispatch_baseline(
        RTS96_GENERATORS, comm, scen, n_samples=50, seed=0
    )
    assert result["EENS_MWh"] >= 0.0
