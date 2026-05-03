"""IEEE RTS-96 data tables and generator fleet."""

from dataclasses import dataclass
from typing import List

import numpy as np

@dataclass
class Generator:
    name:     str
    bus:      int     # 1-indexed bus number
    p_min:    float   # MW minimum stable output
    p_max:    float   # MW maximum output
    ramp_up:  float   # MW/h ramp-up limit
    ramp_dn:  float   # MW/h ramp-down limit
    min_up:   int     # h minimum up-time
    min_dn:   int     # h minimum down-time
    cost_a:   float   # USD/h no-load (fixed when online)
    cost_b:   float   # USD/MWh linear fuel cost
    cost_c:   float   # USD/MW²h quadratic fuel cost
    su_cost:  float   # USD start-up cost
    sd_cost:  float   # USD shut-down cost
    for_rate: float   # forced outage rate [0,1]


# ── Complete IEEE RTS-96 single-area generator fleet ─────────────────────────
# 32 units, 3405 MW total installed capacity, 2850 MW peak load
# Columns: name, bus, p_min, p_max, ramp_up, ramp_dn, min_up, min_dn,
#          cost_a, cost_b, cost_c, su_cost, sd_cost, for_rate
#
# Cost data: Kazarlis et al. 1996 / Wood & Wollenberg, scaled to RTS unit sizes
# Ramp/min-up/min-dn: IEEE standard Table 3 + engineering judgment per unit class
RTS96_GENERATORS: List[Generator] = [
    # ── U12 (5 units: 2 at bus 1, 1 at bus 2, 2 at bus 15) ──────────────────
    Generator("U12-1",  1,  2.4,  12,  12,  12, 4, 2,    0, 14.00, 0.00683,    0,    0, 0.02),
    Generator("U12-2",  1,  2.4,  12,  12,  12, 4, 2,    0, 14.00, 0.00683,    0,    0, 0.02),
    Generator("U12-3",  2,  2.4,  12,  12,  12, 4, 2,    0, 14.00, 0.00683,    0,    0, 0.02),
    Generator("U12-4", 15,  2.4,  12,  12,  12, 4, 2,    0, 14.00, 0.00683,    0,    0, 0.02),
    Generator("U12-5", 15,  2.4,  12,  12,  12, 4, 2,    0, 14.00, 0.00683,    0,    0, 0.02),
    # ── U20 (4 units: 2 at bus 1, 2 at bus 2) ────────────────────────────────
    Generator("U20-1",  1,  4.0,  20,  16,  16, 5, 3,    0, 13.32, 0.00200,    0,    0, 0.02),
    Generator("U20-2",  1,  4.0,  20,  16,  16, 5, 3,    0, 13.32, 0.00200,    0,    0, 0.02),
    Generator("U20-3",  2,  4.0,  20,  16,  16, 5, 3,    0, 13.32, 0.00200,    0,    0, 0.02),
    Generator("U20-4",  2,  4.0,  20,  16,  16, 5, 3,    0, 13.32, 0.00200,    0,    0, 0.02),
    # ── U50 (6 units: buses 1, 2, 7, 13, 15, 16) ─────────────────────────────
    Generator("U50-1",  1, 10.0,  50,  25,  25, 5, 3,    0, 12.39, 0.00150,  500,  100, 0.01),
    Generator("U50-2",  2, 10.0,  50,  25,  25, 5, 3,    0, 12.39, 0.00150,  500,  100, 0.01),
    Generator("U50-3",  7, 10.0,  50,  25,  25, 5, 3,    0, 12.39, 0.00150,  500,  100, 0.01),
    Generator("U50-4", 13, 10.0,  50,  25,  25, 5, 3,    0, 12.39, 0.00150,  500,  100, 0.01),
    Generator("U50-5", 15, 10.0,  50,  25,  25, 5, 3,    0, 12.39, 0.00150,  500,  100, 0.01),
    Generator("U50-6", 16, 10.0,  50,  25,  25, 5, 3,    0, 12.39, 0.00150,  500,  100, 0.01),
    # ── U76 (4 units: 3 at bus 7, 1 at bus 13) ───────────────────────────────
    Generator("U76-1",  7, 15.2,  76,  30,  30, 8, 5,  240, 11.85, 0.00080,  800,  300, 0.02),
    Generator("U76-2",  7, 15.2,  76,  30,  30, 8, 5,  240, 11.85, 0.00080,  800,  300, 0.02),
    Generator("U76-3",  7, 15.2,  76,  30,  30, 8, 5,  240, 11.85, 0.00080,  800,  300, 0.02),
    Generator("U76-4", 13, 15.2,  76,  30,  30, 8, 5,  240, 11.85, 0.00080,  800,  300, 0.02),
    # ── U100 (3 units: buses 7, 13, 23) ──────────────────────────────────────
    Generator("U100-1", 7, 25.0, 100,  40,  40, 8, 5,    0, 15.00, 0.00070, 1000,  400, 0.04),
    Generator("U100-2",13, 25.0, 100,  40,  40, 8, 5,    0, 15.00, 0.00070, 1000,  400, 0.04),
    Generator("U100-3",23, 25.0, 100,  40,  40, 8, 5,    0, 15.00, 0.00070, 1000,  400, 0.04),
    # ── U155 (4 units: buses 15, 16, 21, 23) ─────────────────────────────────
    Generator("U155-1",15, 54.3, 155,  80,  80, 8, 5,  560, 10.52, 0.00060, 1200,  600, 0.04),
    Generator("U155-2",16, 54.3, 155,  80,  80, 8, 5,  560, 10.52, 0.00060, 1200,  600, 0.04),
    Generator("U155-3",21, 54.3, 155,  80,  80, 8, 5,  560, 10.52, 0.00060, 1200,  600, 0.04),
    Generator("U155-4",23, 54.3, 155,  80,  80, 8, 5,  560, 10.52, 0.00060, 1200,  600, 0.04),
    # ── U197 (3 units: bus 13) — slack area ──────────────────────────────────
    Generator("U197-1",13, 69.0, 197, 120, 120, 8, 5, 1200,  7.92, 0.00040, 2400,  800, 0.05),
    Generator("U197-2",13, 69.0, 197, 120, 120, 8, 5, 1200,  7.92, 0.00040, 2400,  800, 0.05),
    Generator("U197-3",13, 69.0, 197, 120, 120, 8, 5, 1200,  7.92, 0.00040, 2400,  800, 0.05),
    # ── U350 (1 unit: bus 22) ─────────────────────────────────────────────────
    Generator("U350-1",22, 75.0, 350, 210, 210,12, 8, 2000,  8.60, 0.00030, 2800, 1100, 0.08),
    # ── U400 (2 units: buses 18, 21) ─────────────────────────────────────────
    Generator("U400-1",18,100.0, 400, 280, 280,12, 8, 2400,  7.97, 0.00020, 3500, 1400, 0.12),
    Generator("U400-2",21,100.0, 400, 280, 280,12, 8, 2400,  7.97, 0.00020, 3500, 1400, 0.12),
]

assert sum(g.p_max for g in RTS96_GENERATORS) == 3405, \
    f"Total capacity check failed: {sum(g.p_max for g in RTS96_GENERATORS)} ≠ 3405 MW"

# ── Bus data (IEEE RTS-96, Table 4) ──────────────────────────────────────────
# Buses 1-10: 138 kV   Buses 11-24: 230 kV
BUS_VOLTAGE_KV = {b: 138 if b <= 10 else 230 for b in range(1, 25)}

# ── Bus loads at annual peak (MW, MVAr) ──────────────────────────────────────
# Source: IEEE RTS-96 Table 4, total = 2850 MW
BUS_LOAD = {
     1: (108, 22),  2: ( 97, 20),  3: (180, 37),  4: ( 74, 15),
     5: ( 71, 14),  6: (136, 28),  7: (125, 25),  8: (171, 35),
     9: (175, 36), 10: (195, 40), 13: (265, 54), 14: (194, 39),
    15: (317, 64), 16: (100, 20), 18: (333, 68), 19: (181, 37),
    20: (128, 26),
    # Buses 11,12,17,21,22,23,24 have no load
}
assert sum(v[0] for v in BUS_LOAD.values()) == 2850, "Load total mismatch"

# ── Weekly peak load (% of annual peak) — Table 6, IEEE RTS-96 ───────────────
WEEKLY_PEAK_PCT = [
    86.2, 90.0, 87.8, 83.4, 88.0, 84.1, 83.2, 80.6, 74.0, 73.7,
    71.5, 72.7, 70.4, 75.0, 72.1, 80.0, 75.4, 83.7, 87.0, 88.0,
    85.6, 81.1, 90.0, 88.7, 89.6, 86.1, 75.5, 81.6, 80.1, 88.0,
    72.2, 77.6, 80.0, 72.9, 72.6, 70.5, 78.0, 69.5, 72.4, 72.4,
    74.3, 74.4, 80.0, 88.1, 88.5, 90.9, 94.0, 89.0, 94.2, 97.0,
    100.0, 95.2,
]  # 52 weeks

# ── Daily peak load (% of weekly peak) — Table 7, IEEE RTS-96 ────────────────
DAILY_PEAK_PCT = {
    'Mon': 93, 'Tue': 100, 'Wed': 98,
    'Thu': 96, 'Fri': 94,  'Sat': 77, 'Sun': 75,
}

# ── Hourly load profiles (% of daily peak) — Table 8, IEEE RTS-96 ────────────
HOURLY_PROFILE = {
    # Winter weekday (used as base case — most stressed condition)
    'winter_weekday': [67,63,60,59,59,60,74,86,95,96,96,95,95,95,93,94,99,100,100,96,90,88,80,73],
    # Winter weekend
    'winter_weekend': [78,72,68,66,64,65,66,70,80,88,90,91,90,88,87,87,91,100,99,97,94,92,87,81],
    # Summer weekday
    'summer_weekday': [64,60,58,56,56,58,64,76,87,95,99,100,99,100,100,97,96,96,93,92,92,93,87,72],
    # Summer weekend
    'summer_weekend': [74,70,66,65,64,62,62,66,81,86,91,93,93,92,91,91,92,94,95,95,100,93,88,80],
}

# Base case: winter weekday at annual peak (100% weekly, Tuesday = 100% daily)
ANNUAL_PEAK_MW = 2850.0
T              = 24
# Hourly demand at annual peak condition
DEMAND = np.array(HOURLY_PROFILE['winter_weekday']) / 100.0 * ANNUAL_PEAK_MW
