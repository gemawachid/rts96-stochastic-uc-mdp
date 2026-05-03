"""Configuration constants for the RTS-96 reliability study."""

RNG_SEED = 42

# Storage (augmented; not in original RTS-96)
STORAGE_CAP_MWH = 1000.0
STORAGE_POW_MW = 400.0
ETA_C = 0.92
ETA_D = 0.92
STORAGE_DEG_COST = 0.5

# System constants
VOLL = 15_000.0
N_SCENARIOS = 30
N_MC = 5_000
LOLP_EPS = 0.08
VRE_PENETRATION = 0.40
