"""Étape 1 parameters, the single source of numbers for calc.py (and for the Atoll configuration).

Every value is copied from the hypotheses table in 01-cahier-des-charges/README.md.
The ID in each comment (A3, B1, D4…) is the row of that table.
"""

# --- A. Spectrum (Band 3 = our study, Band 20 = 800 MHz comparison only) ---------------------------
F_UL = {"B3": 1720.0, "B20": 847.0}   # MHz, uplink centre (A3; B20 UL 832-862, A5)
F_DL = {"B3": 1815.0, "B20": 806.0}   # MHz, downlink centre (A3; B20 DL 791-821, A5)
N_RB = {"B3": 100, "B20": 50}         # resource blocks: 20 MHz (B3) vs 10 MHz per operator (B20, A5)

# --- B. Equipment ----------------------------------------------------------------------------
P_ENB = {"B3": 46.0, "B20": 43.0}     # dBm: same power per RB in both cases (B1: 15.2 dBm RS EPRE)
L_ENB = 1.0                           # dB, Tx and Rx losses, remote radio head (B6)
NF_ENB = 5.0                          # dB (B2)
P_UE, G_UE, NF_UE = 23.0, 0.0, 8.0    # dBm, dBi, dB (B9-B11)
L_BODY = 0.0                          # dB, data services (B13)
H_BS, H_MS = 30.0, 1.5                # m (B8; 1.5 m = Hata standard mobile height)

# Antenna configurations for R-2 (gain dBi, site-area coefficient k: A_site = k * R^2)
CONFIGS = {
    "omni":        {"gain": 11.0, "k": 2.60, "label": "Omni 11 dBi"},     # B4
    "tri-secteur": {"gain": 18.0, "k": 1.95, "label": "3 x 65° 18 dBi"},  # B3
    "6-secteurs":  {"gain": 21.0, "k": 2.60, "label": "6 x 33° 21 dBi"},  # B5
}

# --- C. Services and Atoll bearers ------------------------------------------------------------
DL_EDGE_KBPS, UL_EDGE_KBPS = 1024.0, 128.0   # cell-edge objective (C1)
BEARER_MIN = 4                               # lowest bearer our services accept (C table)
APP_SCALING = 0.95                           # application throughput scaling factor (C, Atoll)
# bearer index: (SINR threshold dB [C2], efficiency bits/symbol [S01-09])
BEARERS = {
    1: (-6.5, 0.1523), 2: (-4.0, 0.2344), 3: (-2.6, 0.3770), 4: (-1.0, 0.6016),
    5: (1.0, 0.8770), 6: (3.0, 1.1758), 7: (6.6, 1.4766), 8: (10.0, 1.9141),
    9: (11.4, 2.4063), 10: (11.8, 2.7305), 11: (13.0, 3.3223), 12: (13.8, 3.9023),
    13: (15.6, 4.5234), 14: (16.8, 5.1152), 15: (17.6, 5.5547),
}
# Usable resource elements per RB per 1 ms (the LTE version of "total channels - signalling", U-2)
RE_TOTAL = 12 * 14        # 12 subcarriers x 14 OFDM symbols
RE_DL = RE_TOTAL - 36 - 12  # minus PDCCH (3 symbols x 12) and CRS of 2 antenna ports in the data region
RE_UL = RE_TOTAL - 24       # minus the demodulation reference signal (1 symbol per slot x 12)

# --- D/E. Propagation, margins, objectives ----------------------------------------------------
AREA_PROB = 0.95                         # 95 % of the area (D4, E1/E2)
SIGMA = {"urbain": 8.0, "rural": 6.0}    # dB (D3)
M_INT_UL, M_INT_DL = 2.0, 3.0            # dB (D6)
M_FADING = 0.0                           # dB, justified in D5 (sensitivity line uses 10 dB)
L_INDOOR = {"urbain": 15.0, "rural": 0.0}  # urban objective indoor (E1), rural outdoor (E2)

# --- Zone (computed from our rasters, 03-cartes/atoll/) --------------------------------------
URBAN_DENSITY_MIN = 1000.0   # hab/km²: urban core = 100 m pixels at or above this density
MASSIF_ALT_MIN = 600.0       # m: no-objective zone = massif / national park above 600 m (E3)

# --- F. Traffic ------------------------------------------------------------------------------
PENETRATION = 0.939   # mobile data subscriptions per inhabitant (F3)
MARKET_SHARE = 0.30   # (F4)
LTE_SHARE = 0.93      # LTE-capable terminals (F5)
GB_PER_MONTH = 9.5    # (F6)
BUSY_HOUR = 0.10      # share of daily traffic in the busy hour (F7)
DL_SHARE = 0.90       # (F8)
LOAD_MAX = 0.80       # max average cell load at the busy hour, LTE analogue of the Erlang-B GoS
GROWTH_2Y = 9.5 / 6.8 # data volume growth over 2 years, INTT 6.8 GB (TR4-2023) -> 9.5 GB (TR4-2025) (F6)
HORIZON_Y = 5         # years, for the "is it future-proof?" line of the 800 vs 1800 comparison
