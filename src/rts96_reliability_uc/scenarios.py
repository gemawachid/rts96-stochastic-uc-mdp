"""VRE scenario generation and Markov transition estimation."""

import numpy as np

from .config import RNG_SEED
from .data import ANNUAL_PEAK_MW, DEMAND, T

def generate_vre_scenarios(penetration, n_scenarios, seed=RNG_SEED,
                           return_components=False):
    rng = np.random.default_rng(seed)
    vre_cap   = penetration * ANNUAL_PEAK_MW / 0.35
    wind_cap  = 0.60 * vre_cap
    solar_cap = 0.40 * vre_cap
    scenarios = np.zeros((n_scenarios, T))
    wind_scenarios = np.zeros((n_scenarios, T))
    solar_scenarios = np.zeros((n_scenarios, T))
    for s in range(n_scenarios):
        wcf = np.zeros(T); wcf[0] = rng.beta(2, 3)
        for t in range(1, T):
            wcf[t] = np.clip(0.85*wcf[t-1] + 0.15*0.30 + rng.normal(0,0.08), 0, 1)
        hrs = np.arange(T)
        env = np.where((hrs>=6)&(hrs<=18), np.sin(np.pi*(hrs-6)/12), 0.0)
        scf = env * rng.beta(4,2) * rng.uniform(0.7, 1.0, T)
        wind_scenarios[s] = wcf*wind_cap
        solar_scenarios[s] = scf*solar_cap
        scenarios[s] = wind_scenarios[s] + solar_scenarios[s]
    if return_components:
        return scenarios, np.ones(n_scenarios)/n_scenarios, {
            "wind": wind_scenarios,
            "solar": solar_scenarios,
        }
    return scenarios, np.ones(n_scenarios)/n_scenarios


def estimate_net_load_transition(scenarios, n_bins=10):
    net_loads   = DEMAND[np.newaxis,:] - scenarios
    bin_edges   = np.linspace(net_loads.min()-1, net_loads.max()+1, n_bins+1)
    bin_centers = 0.5*(bin_edges[:-1]+bin_edges[1:])
    def dig(nl): return np.clip(np.digitize(nl, bin_edges)-1, 0, n_bins-1)
    bins = dig(net_loads)
    P    = np.zeros((T, n_bins, n_bins))
    for t in range(T-1):
        for s in range(scenarios.shape[0]):
            P[t, bins[s,t], bins[s,t+1]] += 1
    P += 1e-6; P /= P.sum(axis=2, keepdims=True)
    P[T-1] = P[T-2]
    return P, bin_edges, bin_centers
