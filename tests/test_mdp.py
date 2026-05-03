"""Tests for MDP value iteration and dispatch."""

import numpy as np
import pytest

from rts96_reliability_uc.baselines import deterministic_uc_baseline
from rts96_reliability_uc.data import DEMAND, RTS96_GENERATORS, T
from rts96_reliability_uc.evaluation import monte_carlo_reliability
from rts96_reliability_uc.mdp import MDPDispatch
from rts96_reliability_uc.scenarios import estimate_net_load_transition, generate_vre_scenarios


@pytest.fixture(scope="module")
def mdp_fixture():
    scen, _ = generate_vre_scenarios(0.40, n_scenarios=5, seed=0)
    P, _, centers = estimate_net_load_transition(scen)
    comm, _ = deterministic_uc_baseline(RTS96_GENERATORS, scen)
    mdp = MDPDispatch(RTS96_GENERATORS, comm, P, centers)
    mdp.solve(verbose=False)
    return mdp, comm, scen


def test_value_function_shape(mdp_fixture):
    mdp, _, _ = mdp_fixture
    assert mdp.V.shape == (T + 1, mdp.N_L, mdp.N_E)


def test_policy_shape(mdp_fixture):
    mdp, _, _ = mdp_fixture
    assert mdp.policy_b.shape == (T, mdp.N_L, mdp.N_E)


def test_terminal_value_is_zero(mdp_fixture):
    mdp, _, _ = mdp_fixture
    np.testing.assert_array_equal(mdp.V[T], 0.0)


def test_value_function_finite(mdp_fixture):
    mdp, _, _ = mdp_fixture
    assert np.isfinite(mdp.V).all()


def test_dispatch_returns_valid_storage_action(mdp_fixture):
    mdp, _, _ = mdp_fixture
    from rts96_reliability_uc.config import STORAGE_POW_MW
    b, unserved, cost = mdp.dispatch(t=12, net_load_mw=2000.0, soc=0.5)
    assert abs(b) <= STORAGE_POW_MW + 1e-6
    assert unserved >= 0.0
    assert cost >= 0.0


def test_mc_reliability_returns_ci(mdp_fixture):
    mdp, comm, scen = mdp_fixture
    result = monte_carlo_reliability(mdp, RTS96_GENERATORS, comm, scen, n_samples=100, seed=0)
    assert "LOLP_CI95" in result
    assert "EENS_CI95" in result
    lo, hi = result["LOLP_CI95"]
    assert lo <= result["LOLP"] <= hi


def test_mc_lolp_in_unit_interval(mdp_fixture):
    mdp, comm, scen = mdp_fixture
    result = monte_carlo_reliability(mdp, RTS96_GENERATORS, comm, scen, n_samples=100, seed=0)
    assert 0.0 <= result["LOLP"] <= 1.0


def test_mc_eens_nonnegative(mdp_fixture):
    mdp, comm, scen = mdp_fixture
    result = monte_carlo_reliability(mdp, RTS96_GENERATORS, comm, scen, n_samples=100, seed=0)
    assert result["EENS_MWh"] >= 0.0
