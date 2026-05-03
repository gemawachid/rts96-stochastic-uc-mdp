"""Stage 2 adaptive dispatch MDP solved by backward value iteration."""

import numpy as np

from .config import ETA_C, ETA_D, STORAGE_CAP_MWH, STORAGE_DEG_COST, STORAGE_POW_MW, VOLL
from .data import T

class MDPDispatch:
    N_E = 10

    def __init__(self, generators, commitment, transition_matrix,
                 bin_centers, n_storage_actions=7):
        self.generators  = generators
        self.commitment  = commitment
        self.P           = transition_matrix
        self.bin_centers = bin_centers
        self.N_L         = len(bin_centers)
        self.G           = len(generators)
        self.soc_bins    = np.linspace(0.0, 1.0, self.N_E)
        self.actions     = np.linspace(-STORAGE_POW_MW, STORAGE_POW_MW, n_storage_actions)
        self.V               = np.zeros((T+1, self.N_L, self.N_E))
        self.policy_b        = np.zeros((T, self.N_L, self.N_E))
        self.policy_unserved = np.zeros((T, self.N_L, self.N_E))
        self._build_merit_cache()

    def _build_merit_cache(self):
        self._merit = []
        for t in range(T):
            committed = sorted(
                [(g, self.generators[g]) for g in range(self.G)
                 if self.commitment[g,t] == 1],
                key=lambda x: x[1].cost_b
            )
            self._merit.append(committed)

    def _eco_dispatch(self, t, demand_mw, avail=None):
        if demand_mw <= 0: return 0.0, 0.0
        merit = self._merit[t]
        if avail is not None:
            merit = [(g,gen) for g,gen in merit if avail[g]]
        if not merit: return VOLL*demand_mw, demand_mw
        remaining = demand_mw; cost = 0.0
        for g,gen in merit:
            if remaining <= 0: break
            p = min(remaining, gen.p_max)
            p = max(p, gen.p_min) if remaining >= gen.p_min else gen.p_min
            cost += gen.cost_a + gen.cost_b*p + gen.cost_c*p**2
            remaining -= p
        unserved = max(0.0, remaining)
        return cost + VOLL*unserved, unserved

    def _clip_b(self, e, b):
        soc = self.soc_bins[e]
        return float(np.clip(b,
            -min(STORAGE_POW_MW, soc*STORAGE_CAP_MWH*ETA_D),
             min(STORAGE_POW_MW, (1-soc)*STORAGE_CAP_MWH/ETA_C)))

    def _next_e(self, e, b):
        soc  = self.soc_bins[e]
        delta = b*ETA_C/STORAGE_CAP_MWH if b>=0 else b/(ETA_D*STORAGE_CAP_MWH)
        return int(np.argmin(np.abs(self.soc_bins - np.clip(soc+delta, 0.0, 1.0))))

    def _reward(self, t, l, e, b_raw):
        b = self._clip_b(e, b_raw)
        cost, unserved = self._eco_dispatch(t, self.bin_centers[l]+b)
        return -(cost + STORAGE_DEG_COST*abs(b)), unserved, self._next_e(e,b)

    def solve(self, verbose=True):
        if verbose: print("  Running value iteration...")
        self.V[T] = 0.0
        for t in range(T-1,-1,-1):
            for l in range(self.N_L):
                for e in range(self.N_E):
                    best_q, best_b, best_u = -np.inf, 0.0, 0.0
                    for b_raw in self.actions:
                        r,u,e2 = self._reward(t,l,e,b_raw)
                        q = r + float(np.dot(self.P[t,l,:], self.V[t+1,:,e2]))
                        if q > best_q:
                            best_q, best_b, best_u = q, b_raw, u
                    self.V[t,l,e]               = best_q
                    self.policy_b[t,l,e]        = best_b
                    self.policy_unserved[t,l,e] = best_u
        if verbose:
            print(f"  Done. V[t=0] in [{self.V[0].min():.0f}, {self.V[0].max():.0f}]")

    def dispatch(self, t, net_load_mw, soc, avail=None):
        l = int(np.clip(np.argmin(np.abs(self.bin_centers-net_load_mw)), 0, self.N_L-1))
        e = int(np.clip(np.argmin(np.abs(self.soc_bins-soc)),            0, self.N_E-1))
        b = self._clip_b(e, self.policy_b[t,l,e])
        cost, unserved = self._eco_dispatch(t, net_load_mw+b, avail)
        return b, unserved, cost

