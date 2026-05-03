"""Tests for VRE scenario generation and Markov chain estimation."""

import numpy as np
import pytest

from rts96_reliability_uc.data import ANNUAL_PEAK_MW, DEMAND, T
from rts96_reliability_uc.scenarios import estimate_net_load_transition, generate_vre_scenarios


def test_scenario_shape():
    scenarios, probs = generate_vre_scenarios(0.40, n_scenarios=10, seed=0)
    assert scenarios.shape == (10, T)
    assert probs.shape == (10,)


def test_probabilities_sum_to_one():
    _, probs = generate_vre_scenarios(0.40, n_scenarios=10, seed=0)
    assert abs(probs.sum() - 1.0) < 1e-9


def test_vre_nonnegative():
    scenarios, _ = generate_vre_scenarios(0.40, n_scenarios=20, seed=1)
    assert (scenarios >= 0).all()


def test_vre_bounded_by_capacity():
    penetration = 0.40
    vre_cap = penetration * ANNUAL_PEAK_MW / 0.35
    scenarios, _ = generate_vre_scenarios(penetration, n_scenarios=20, seed=2)
    assert (scenarios <= vre_cap * 1.01).all()


def test_reproducibility():
    s1, _ = generate_vre_scenarios(0.40, n_scenarios=5, seed=42)
    s2, _ = generate_vre_scenarios(0.40, n_scenarios=5, seed=42)
    np.testing.assert_array_equal(s1, s2)


def test_different_seeds_differ():
    s1, _ = generate_vre_scenarios(0.40, n_scenarios=5, seed=0)
    s2, _ = generate_vre_scenarios(0.40, n_scenarios=5, seed=1)
    assert not np.array_equal(s1, s2)


def test_markov_chain_shape():
    scenarios, _ = generate_vre_scenarios(0.40, n_scenarios=10, seed=0)
    P, edges, centers = estimate_net_load_transition(scenarios, n_bins=10)
    assert P.shape == (T, 10, 10)
    assert len(edges) == 11
    assert len(centers) == 10


def test_markov_rows_sum_to_one():
    scenarios, _ = generate_vre_scenarios(0.40, n_scenarios=10, seed=0)
    P, _, _ = estimate_net_load_transition(scenarios, n_bins=10)
    row_sums = P.sum(axis=2)
    np.testing.assert_allclose(row_sums, np.ones((T, 10)), atol=1e-6)


def test_net_load_within_demand_range():
    scenarios, _ = generate_vre_scenarios(0.40, n_scenarios=10, seed=0)
    net_loads = DEMAND[np.newaxis, :] - scenarios
    assert (net_loads <= DEMAND.max() * 1.01).all()
