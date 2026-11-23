"""Étape 1: analytical dimensioning of the Zaghouan LTE network (Band 3, 1800 MHz).

Run from projet-atoll/:   .venv/bin/python 02-dimensionnement/calc.py
Outputs: 02-dimensionnement/resultats.md (all tables) and 02-dimensionnement/figures/*.png

Sections follow the PDF requirements:
  1. Zone (E1-2, E1-4)          2. Margins (E1-2, E1-3)       3. Link budget -> R (R-1)
  4. Sites by coverage (R-2)    5. Capacity (U-1..U-5)        6. Final count (E1-5, E1-6)
  7. Reuse + frequencies (E1-7, E1-8, R-3..R-5)               8. 800 vs 1800
Every number comes from params.py (= hypotheses.md v1.0) or is computed here.
"""
import math
from pathlib import Path

import numpy as np
from osgeo import gdal

import params as P

gdal.UseExceptions()
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "02-dimensionnement"
FIG = OUT / "figures"
FIG.mkdir(exist_ok=True)
md = []  # lines of resultats.md


def table(header, rows):
    md.append("| " + " | ".join(header) + " |")
    md.append("|" + "---|" * len(header))
    for r in rows:
        md.append("| " + " | ".join(str(c) for c in r) + " |")
    md.append("")


def db(x):
    return 10 * math.log10(x)


# ================================================================================================
# 1. ZONE: urban core, massif, rural area, population split (E1-2, E1-4)
# ================================================================================================
A = ROOT / "03-cartes" / "atoll"
dens = gdal.Open(str(A / "Population_Zaghouan_100m_densite.tif")).ReadAsArray().astype(float)  # hab/km², 100 m
dem = gdal.Open(str(A / "MNT_Zaghouan_25m.tif")).ReadAsArray().astype(float)                    # m, 25 m
dem100 = dem.reshape(100, 4, 100, 4).mean(axis=(1, 3))     # same 100 m grid as the population
people = dens * 0.01                                        # one 100 m pixel = 0.01 km²

urban = dens >= P.URBAN_DENSITY_MIN
massif = (dem100 >= P.MASSIF_ALT_MIN) & ~urban
rural = ~urban & ~massif
A_ZONE = 100.0
A_URB, A_MAS, A_RUR = urban.sum() * 0.01, massif.sum() * 0.01, rural.sum() * 0.01
POP_TOT, POP_URB = people.sum(), people[urban].sum()
POP_RUR = POP_TOT - POP_URB

md += ["# Étape 1: dimensionnement analytique (généré par `calc.py`, ne pas éditer à la main)", "",
       "## 1. Zone d'étude (E1-2, E1-4)", ""]
table(["Zone", "Définition", "Surface (km²)", "Population (WorldPop 2020)"], [
    ["Centre urbain", f"densité ≥ {P.URBAN_DENSITY_MIN:.0f} hab/km²", f"{A_URB:.2f}", f"{POP_URB:,.0f}"],
    ["Massif / parc (sans objectif)", f"altitude ≥ {P.MASSIF_ALT_MIN:.0f} m", f"{A_MAS:.2f}", f"{people[massif].sum():,.0f}"],
    ["Rural (objectif outdoor)", "le reste", f"{A_RUR:.2f}", f"{people[rural].sum():,.0f}"],
    ["Total", "10 × 10 km", f"{A_ZONE:.0f}", f"{POP_TOT:,.0f}"],
])

# ================================================================================================
# 2. MARGINS: Jakes formula, 95 % of the area -> shadowing margin (E1-2, E1-3)
# ================================================================================================
N_SLOPE = (44.9 - 6.55 * math.log10(P.H_BS)) / 10   # Hata distance slope, = path-loss index α


def jakes_area(margin, sigma, n):
    """Fraction of the cell area above threshold (Jakes), for an edge margin in dB."""
    a = -margin / (sigma * math.sqrt(2))
    b = 10 * n * math.log10(math.e) / (sigma * math.sqrt(2))
    return 0.5 * (1 - math.erf(a) + math.exp((1 - 2 * a * b) / b**2) * (1 - math.erf((1 - a * b) / b)))


def shadow_margin(sigma, target=P.AREA_PROB, n=N_SLOPE):
    lo, hi = 0.0, 30.0
    for _ in range(60):  # bisection
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if jakes_area(mid, sigma, n) < target else (lo, mid)
    return mid


M_SH = {z: shadow_margin(s) for z, s in P.SIGMA.items()}
EDGE = {z: 0.5 * (1 + math.erf(M_SH[z] / (P.SIGMA[z] * math.sqrt(2)))) for z in P.SIGMA}
md += ["## 2. Marges (E1-2, E1-3)", "",
       f"Pente de Hata pour h_b = {P.H_BS:.0f} m : 44,9 − 6,55·log h_b = {N_SLOPE*10:.1f} dB/décade → **α = {N_SLOPE:.2f}**.", ""]
table(["Zone", "σ (dB)", "Objectif surface", "Proba. en bord de cellule", "Marge de masque (dB)"],
      [[z, f"{P.SIGMA[z]:.0f}", f"{P.AREA_PROB:.0%}", f"{EDGE[z]:.1%}", f"{M_SH[z]:.1f}"] for z in P.SIGMA])

# ================================================================================================
# 3. LINK BUDGET -> MAPL -> RADIUS (R-1)
# ================================================================================================
def rb_needed(kbps, re_per_rb):
    """RBs a cell-edge user needs at the lowest allowed bearer."""
    eff = P.BEARERS[P.BEARER_MIN][1]
    kbps_per_rb = eff * re_per_rb * 1000 * P.APP_SCALING / 1000   # bits/ms = kbps
    return math.ceil(kbps / kbps_per_rb), kbps_per_rb


def hata_loss(f, d, band):
    """COST-231 Hata (B3, 1500-2000 MHz) or Okumura-Hata (B20, < 1500 MHz), medium city, C_m = 0."""
    a_hm = (1.1 * math.log10(f) - 0.7) * P.H_MS - (1.56 * math.log10(f) - 0.8)
    if band == "B3":
        base = 46.3 + 33.9 * math.log10(f)
    else:
        base = 69.55 + 26.16 * math.log10(f)
    return base - 13.82 * math.log10(P.H_BS) - a_hm + (44.9 - 6.55 * math.log10(P.H_BS)) * math.log10(d)


def radius(mapl, f, band):
    return 10 ** ((mapl - hata_loss(f, 1.0, band)) / (10 * N_SLOPE))


SINR_MIN = P.BEARERS[P.BEARER_MIN][0]
RB_UL, KBPS_RB_UL = rb_needed(P.UL_EDGE_KBPS, P.RE_UL)
RB_DL, KBPS_RB_DL = rb_needed(P.DL_EDGE_KBPS, P.RE_DL)


def budget(direction, zone, gain, band="B3", fading=P.M_FADING):
    """Return the budget lines (label, value) and the MAPL, for one direction / zone / antenna gain."""
    if direction == "UL":   # UE -> eNodeB, the UE spreads 23 dBm over RB_UL resource blocks
        eirp = P.P_UE + P.G_UE - P.L_BODY
        noise = -174 + db(RB_UL * 180e3) + P.NF_ENB
        rx_gain, m_int, f = gain - P.L_ENB, P.M_INT_UL, P.F_UL[band]
        lines = [("Puissance UE (dBm)", P.P_UE), ("Pertes corporelles (dB)", -P.L_BODY), ("PIRE UE (dBm)", eirp),
                 (f"Bruit thermique sur {RB_UL} RB + NF eNB {P.NF_ENB:.0f} dB (dBm)", noise)]
    else:                   # eNodeB -> UE, power per RB (the UE receives its RBs at the per-RB power)
        p_rb = P.P_ENB[band] - db(P.N_RB[band])
        eirp = p_rb + gain - P.L_ENB
        noise = -174 + db(180e3) + P.NF_UE
        rx_gain, m_int, f = P.G_UE - P.L_BODY, P.M_INT_DL, P.F_DL[band]
        lines = [(f"Puissance eNB par RB ({P.P_ENB[band]:.0f} dBm / {P.N_RB[band]} RB)", p_rb),
                 (f"Gain antenne − pertes ({gain:.0f} − {P.L_ENB:.0f} dB)", gain - P.L_ENB),
                 ("PIRE par RB (dBm)", eirp), (f"Bruit thermique sur 1 RB + NF UE {P.NF_UE:.0f} dB (dBm)", noise)]
    sens = noise + SINR_MIN
    margins = M_SH[zone] + m_int + P.L_INDOOR[zone] + fading
    mapl = eirp + rx_gain - sens - margins
    lines += [(f"SINR requis, bearer {P.BEARER_MIN} (dB)", SINR_MIN), ("Sensibilité (dBm)", sens)]
    if direction == "UL":
        lines += [(f"Gain antenne eNB − pertes ({gain:.0f} − {P.L_ENB:.0f} dB)", rx_gain)]
    lines += [("Marge de masque (dB)", -M_SH[zone]), ("Marge d'interférence (dB)", -m_int),
              ("Pertes indoor (dB)", -P.L_INDOOR[zone]), ("Marge d'évanouissement rapide (dB)", -fading),
              ("**MAPL (dB)**", mapl), ("**Rayon R (km)**", radius(mapl, f, band))]
    return lines, mapl, f


md += ["## 3. Bilan de liaison → rayon de cellule (R-1)", "",
       f"Utilisateur en bord de cellule au bearer {P.BEARER_MIN} (SINR ≥ {SINR_MIN} dB) : "
       f"UL {P.UL_EDGE_KBPS:.0f} kbps → **{RB_UL} RB** ({KBPS_RB_UL:.1f} kbps/RB), "
       f"DL {P.DL_EDGE_KBPS:.0f} kbps → **{RB_DL} RB** ({KBPS_RB_DL:.1f} kbps/RB).", "",
       f"Modèle COST-231 Hata, h_b = {P.H_BS:.0f} m, h_m = {P.H_MS} m, ville moyenne (C_m = 0) : "
       f"L(1 km) = {hata_loss(P.F_UL['B3'], 1, 'B3'):.1f} dB à {P.F_UL['B3']:.0f} MHz (UL), "
       f"{hata_loss(P.F_DL['B3'], 1, 'B3'):.1f} dB à {P.F_DL['B3']:.0f} MHz (DL).", ""]

R = {}  # R[(zone, config)] = min(UL, DL) radius, km
for zone in ("urbain", "rural"):
    g = P.CONFIGS["tri-secteur"]["gain"]
    bl_ul, mapl_ul, _ = budget("UL", zone, g)
    bl_dl, mapl_dl, _ = budget("DL", zone, g)
    md += [f"### {zone.capitalize()} ({'indoor' if P.L_INDOOR[zone] else 'outdoor'}, antenne tri-secteur)", ""]
    md.append("| UL | valeur | DL | valeur |")
    md.append("|---|---|---|---|")
    for i in range(max(len(bl_ul), len(bl_dl))):
        a = bl_ul[i] if i < len(bl_ul) else ("", "")
        b = bl_dl[i] if i < len(bl_dl) else ("", "")
        fa = f"{(a[1] or 0.0):.2f}" if isinstance(a[1], float) else a[1]   # "or 0.0" turns -0.00 into 0.00
        fb = f"{(b[1] or 0.0):.2f}" if isinstance(b[1], float) else b[1]
        md.append(f"| {a[0]} | {fa} | {b[0]} | {fb} |")
    md.append("")
    lim = "UL" if mapl_ul < mapl_dl else "DL"
    md += [f"→ Liaison limitante : **{lim}** (MAPL UL {mapl_ul:.1f} dB vs DL {mapl_dl:.1f} dB, écart {abs(mapl_dl-mapl_ul):.1f} dB).", ""]

for zone in ("urbain", "rural"):
    for c, cfg in P.CONFIGS.items():
        rul = budget("UL", zone, cfg["gain"])
        rdl = budget("DL", zone, cfg["gain"])
        R[(zone, c)] = min(radius(rul[1], rul[2], "B3"), radius(rdl[1], rdl[2], "B3"))

# Sensitivity line: course fading margin 10 dB
r_fad = radius(budget("UL", "urbain", 18.0, fading=10.0)[1], P.F_UL["B3"], "B3")
md += [f"**Sensibilité** : avec la marge d'évanouissement du cours (10 dB), R urbain = {r_fad:.2f} km "
       f"au lieu de {R[('urbain','tri-secteur')]:.2f} km → ×{(R[('urbain','tri-secteur')]/r_fad)**2:.1f} sites.", ""]

# ================================================================================================
# 4. NUMBER OF SITES BY COVERAGE (R-2)
# ================================================================================================
md += ["## 4. Nombre de sites par la couverture (R-2)", "",
       "Surface couverte par un site : A_site = k·R² (omni k = 2,6 ; tri-secteur k = 1,95 ; 6 secteurs k = 2,6). "
       "Chaque configuration a son propre R car le gain d'antenne change le bilan.", ""]
rows, N_COV = [], {}
for c, cfg in P.CONFIGS.items():
    nu = math.ceil(A_URB / (cfg["k"] * R[("urbain", c)] ** 2))
    nr = math.ceil(A_RUR / (cfg["k"] * R[("rural", c)] ** 2))
    N_COV[c] = (nu, nr)
    rows.append([cfg["label"], f"{R[('urbain', c)]:.2f}", nu, f"{R[('rural', c)]:.2f}", nr, nu + nr])
table(["Configuration", "R urbain (km)", "Sites urbains", "R rural (km)", "Sites ruraux", "Total"], rows)

# ================================================================================================
# 5. CAPACITY (U-1..U-5): course C/I formula evaluated over the whole cell
# ================================================================================================
def sinr_over_cell(alpha=N_SLOPE, n_pts=400_000, seed=1):
    """C/I at uniformly spread points of a hexagonal cell, 6 co-channel interferers at D = √3·R (K = 1).

    Same assumptions as the course (slide 31: 6 first-ring interferers, path-loss index α), but evaluated
    everywhere in the cell instead of only at the worst point. Full load, omni = conservative.
    Interference-limited (noise neglected) -> the result does not depend on R.
    """
    rng = np.random.default_rng(seed)
    x, y = rng.uniform(-1, 1, (2, n_pts))
    inside = (np.abs(y) <= math.sqrt(3) / 2) & (math.sqrt(3) * np.abs(x) + np.abs(y) <= math.sqrt(3))
    x, y = x[inside], y[inside]
    ang = np.arange(6) * np.pi / 3 + np.pi / 6
    D = math.sqrt(3)
    c = np.hypot(x, y).clip(1e-3) ** -alpha
    i = sum(np.hypot(x - D * math.cos(t), y - D * math.sin(t)) ** -alpha for t in ang)
    return 10 * np.log10(c / i)


sinr = sinr_over_cell()
thr = np.array([P.BEARERS[b][0] for b in sorted(P.BEARERS)])
eff = np.array([0.0] + [P.BEARERS[b][1] for b in sorted(P.BEARERS)])
bearer = np.searchsorted(thr, sinr, side="right")            # 0 = below bearer 1
served = bearer >= P.BEARER_MIN
EFF_MEAN = np.where(served, eff[bearer], 0).mean()          # bits per resource element, area average
OUTAGE = 1 - served.mean()


def cell_throughput(band, re, eff_mean=EFF_MEAN):
    return eff_mean * re * P.N_RB[band] * 1000 * P.APP_SCALING / 1e6   # Mbps


THR_DL = cell_throughput("B3", P.RE_DL)
THR_UL = cell_throughput("B3", P.RE_UL)
KBPS_BH = P.GB_PER_MONTH * 8e9 / 30 * P.BUSY_HOUR / 3600 / 1000    # busy-hour kbps per subscriber
KBPS_DL, KBPS_UL = KBPS_BH * P.DL_SHARE, KBPS_BH * (1 - P.DL_SHARE)


def users(pop):
    return pop * P.PENETRATION * P.MARKET_SHARE * P.LTE_SHARE


def capacity(pop, band="B3", growth=1.0):
    thr_dl = cell_throughput(band, P.RE_DL)
    subs_cell = math.floor(thr_dl * 1000 * P.LOAD_MAX / (KBPS_DL * growth))   # U-3
    cells = math.ceil(users(pop) / subs_cell)                                 # U-4
    return subs_cell, cells, math.ceil(cells / 3)                            # U-5


SUBS_CELL, CELLS_CAP, SITES_CAP = capacity(POP_URB)
md += ["## 5. Dimensionnement par la capacité, centre urbain (U-1 … U-5)", "",
       "### Traduction GSM → LTE", ""]
table(["PDF (logique GSM)", "Notre équivalent LTE", "Valeur"], [
    ["U-1 Fréquences par cellule", "1 porteuse de 20 MHz, réutilisation 1", f"{P.N_RB['B3']} RB par cellule"],
    ["U-2 Canaux de trafic = total − 2 de signalisation",
     "ressources par RB = total − PDCCH − signaux de référence",
     f"DL {P.RE_DL}/{P.RE_TOTAL} RE ({P.RE_DL/P.RE_TOTAL:.0%}), UL {P.RE_UL}/{P.RE_TOTAL} ({P.RE_UL/P.RE_TOTAL:.0%})"],
    ["U-3 Abonnés par cellule (Erlang B, GoS)", f"débit cellule × charge max {P.LOAD_MAX:.0%} / débit par abonné", f"{SUBS_CELL} abonnés"],
    ["U-4 Cellules = abonnés / abonnés par cellule", "idem", f"{CELLS_CAP} cellules"],
    ["U-5 Sites = cellules / 3", "idem (tri-secteur)", f"**{SITES_CAP} sites**"],
])
md += ["### Débit moyen d'une cellule", "",
       f"Formule du cours (diapo 31, 6 interféreurs, α = {N_SLOPE:.2f}) appliquée en **chaque point** de la cellule, "
       f"puis C/I → bearer Atoll (seuils C2) → efficacité. Pire cas du cours (bord, (q−1)) : "
       f"{db((math.sqrt(3)-1)**N_SLOPE/6):.1f} dB ; distribution réelle : "
       f"5 % des points sous {np.percentile(sinr,5):.1f} dB, médiane {np.median(sinr):.1f} dB.", ""]
table(["Grandeur", "Valeur"], [
    ["Efficacité moyenne (bits/RE)", f"{EFF_MEAN:.2f}"],
    [f"Surface sous le bearer {P.BEARER_MIN} (non servie au débit de service)", f"{OUTAGE:.1%}"],
    ["Surface au-dessus de 12 dB (MIMO possible, non compté → prudent)", f"{(sinr > 12).mean():.0%}"],
    ["Débit moyen cellule DL / UL (Mbps)", f"{THR_DL:.1f} / {THR_UL:.1f}"],
])
md += ["### Demande", ""]
table(["Grandeur", "Calcul", "Valeur"], [
    ["Débit heure chargée par abonné", f"{P.GB_PER_MONTH} Go × 8 / 30 j × {P.BUSY_HOUR:.0%} / 3600 s",
     f"{KBPS_BH:.1f} kbps (DL {KBPS_DL:.1f}, UL {KBPS_UL:.1f})"],
    ["Abonnés LTE, centre urbain", f"{POP_URB:,.0f} × {P.PENETRATION} × {P.MARKET_SHARE} × {P.LTE_SHARE}", f"{users(POP_URB):,.0f}"],
    ["Demande DL heure chargée, centre", "abonnés × débit DL", f"{users(POP_URB)*KBPS_DL/1000:.0f} Mbps"],
    ["Abonnés LTE, hors centre (rural + massif)", f"{POP_RUR:,.0f} hab.", f"{users(POP_RUR):,.0f}"],
])

# ================================================================================================
# 6. FINAL COUNT + STRATEGY (E1-5, E1-6)
# ================================================================================================
nu_cov, nr_cov = N_COV["tri-secteur"]
rural_cells_needed = math.ceil(users(POP_RUR) / SUBS_CELL)
N_URB = max(nu_cov, SITES_CAP)
N_RUR = max(nr_cov, math.ceil(rural_cells_needed / 3))
md += ["## 6. Nombre final de sites (E1-5, E1-6)", ""]
table(["Zone", "Couverture", "Capacité", "Retenu", "Contrainte dimensionnante"], [
    ["Centre urbain", nu_cov, SITES_CAP, N_URB, "couverture indoor" if nu_cov >= SITES_CAP else "capacité"],
    ["Rural", nr_cov, math.ceil(rural_cells_needed / 3), N_RUR, "couverture outdoor"],
    ["**Total**", "", "", f"**{N_URB + N_RUR}**", ""],
])

# ================================================================================================
# 7. REUSE + FREQUENCY PLAN (E1-7, E1-8, R-3..R-5)
# ================================================================================================
md += ["## 7. Motif de réutilisation et plan de fréquences (E1-7, E1-8, R-3 … R-5)", "",
       f"Formules du cours : D = √(3K)·R, q = D/R, C/I = (q − 1)^α / 6 (α = {N_SLOPE:.2f}).", ""]
rows = []
for K, ij in [(1, "1,0"), (3, "1,1"), (4, "2,0"), (7, "2,1"), (9, "3,0")]:
    q = math.sqrt(3 * K)
    ci = db((q - 1) ** N_SLOPE / 6)
    rows.append([K, ij, f"{q:.2f}", f"{ci:.1f}", "oui" if ci >= 9 else "non",
                 "oui" if ci >= SINR_MIN else "non", f"{20 / K:.1f}"])
table(["K", "(i,j)", "q", "C/I pire cas (dB)", "GSM ≥ 9 dB", f"LTE ≥ {SINR_MIN} dB", "MHz par cellule"], rows)
md += ["**Choix : K = 1** (même porteuse de 20 MHz, EARFCN 1300, sur toutes les cellules). Le pire cas du cours dit "
       "K = 3, mais il place les 6 interféreurs au plus près en même temps ; la distribution réelle (section 5) montre "
       f"seulement {OUTAGE:.0%} de la surface sous le seuil, et K = 1 donne 3× plus de spectre par cellule. "
       "Le bord de cellule est géré par l'ordonnanceur, le tilt et l'azimut (Étape 2).", ""]
table(["R-4 / R-5", "Valeur"], [
    ["Porteuses disponibles", "1 × 20 MHz (bande 3, par opérateur)"],
    ["Canaux par porteuse", f"{P.N_RB['B3']} RB"],
    ["Fréquences par site", "1 porteuse, réutilisée sur les 3 secteurs"],
    ["Allocation (LTE)", "même fréquence partout ; on planifie les **PCI** : site s → PCI 3s, 3s+1, 3s+2 "
                         "(les 3 secteurs d'un site ont des PCI mod 3 différents)"],
])

# ================================================================================================
# 8. 800 MHz (Band 20, 10 MHz) vs 1800 MHz (Band 3, 20 MHz)
# ================================================================================================
md += ["## 8. Pourquoi 1800 et pas 800 ?", "",
       "Mêmes marges, mêmes antennes, même puissance par RB : seuls le modèle (Okumura-Hata à 800) "
       "et la largeur de bande changent. Hypothèse prudente pour 800 : même perte indoor (en réalité plus faible).", ""]
growth = P.GROWTH_2Y ** (P.HORIZON_Y / 2)
rows, X1 = [], {}
for band in ("B20", "B3"):
    r_u = min(radius(budget("UL", "urbain", 18.0, band)[1], P.F_UL[band], band),
              radius(budget("DL", "urbain", 18.0, band)[1], P.F_DL[band], band))
    r_r = min(radius(budget("UL", "rural", 18.0, band)[1], P.F_UL[band], band),
              radius(budget("DL", "rural", 18.0, band)[1], P.F_DL[band], band))
    cov_u, cov_r = math.ceil(A_URB / (1.95 * r_u**2)), math.ceil(A_RUR / (1.95 * r_r**2))
    cap_now = capacity(POP_URB, band)[2]
    cap_fut = capacity(POP_URB, band, growth)[2]
    X1[band] = (r_u, r_r, cov_u, cov_r, cap_now, cap_fut)
    rows.append([("800 MHz, 10 MHz" if band == "B20" else "1800 MHz, 20 MHz"), f"{r_u:.2f}", f"{r_r:.2f}",
                 cov_u + cov_r, cap_now, max(cov_u, cap_now) + cov_r, cap_fut, max(cov_u, cap_fut) + cov_r])
table(["Bande", "R urbain (km)", "R rural (km)", "Sites couverture", "Sites capacité (centre)",
       "Total aujourd'hui", f"Sites capacité dans {P.HORIZON_Y} ans (×{growth:.1f})", f"Total dans {P.HORIZON_Y} ans"], rows)

(OUT / "resultats.md").write_text("\n".join(md) + "\n", encoding="utf-8")

# ================================================================================================
# FIGURES (French labels, light background for the slides)
# ================================================================================================
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

BLUE, ORANGE, INK, INK2, MUTED, GRID = "#2a78d6", "#eb6834", "#0b0b0b", "#52514e", "#898781", "#e1e0d9"
plt.rcParams.update({"font.size": 11, "axes.edgecolor": "#c3c2b7", "axes.labelcolor": INK2, "xtick.color": MUTED,
                     "ytick.color": MUTED, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6, "figure.dpi": 150,
                     "savefig.bbox": "tight", "figure.facecolor": "#fcfcfb", "axes.facecolor": "#fcfcfb"})

# Fig 1: path loss vs distance, 800 vs 1800, with the MAPL lines
d = np.logspace(-1, math.log10(8), 200)
fig, ax = plt.subplots(figsize=(8, 4.6))
ax.plot(d, [hata_loss(P.F_UL["B3"], x, "B3") for x in d], color=BLUE, lw=2)
ax.plot(d, [hata_loss(P.F_UL["B20"], x, "B20") for x in d], color=ORANGE, lw=2)
ax.text(8.4, hata_loss(P.F_UL["B3"], 8, "B3"), "1800 MHz\n(COST-231)", color=INK, va="center")
ax.text(8.4, hata_loss(P.F_UL["B20"], 8, "B20"), "800 MHz\n(Okumura)", color=INK, va="center")
for zone, ls in (("urbain", "--"), ("rural", ":")):
    m = budget("UL", zone, 18.0)[1]
    ax.axhline(m, color=MUTED, lw=1, ls=ls)
    ax.text(0.105, m + 0.8, f"MAPL {zone} {m:.1f} dB", color=INK2, fontsize=9)
for band, col in (("B3", BLUE), ("B20", ORANGE)):
    for zone in ("urbain", "rural"):
        m = budget("UL", zone, 18.0, band)[1]
        r = radius(m, P.F_UL[band], band)
        ax.plot([r], [m], "o", ms=8, color=col, mec="#fcfcfb", mew=2)
ax.set_xscale("log")
ax.set_xlim(0.09, 25)
ax.set_xlabel("Distance (km, échelle log)")
ax.set_ylabel("Affaiblissement de parcours (dB)")
ax.set_title("Affaiblissement en liaison montante : le rayon est là où la courbe croise le MAPL", loc="left", color=INK)
fig.savefig(FIG / "fig1_affaiblissement_800_1800.png")
plt.close(fig)

# Fig 2: UL urban link budget as a waterfall
steps = [("PIRE UE", P.P_UE), ("Gain eNB − pertes", 18.0 - P.L_ENB), ("− Sensibilité eNB", -(-174 + db(RB_UL*180e3) + P.NF_ENB + SINR_MIN)),
         ("Marge de masque", -M_SH["urbain"]), ("Interférence", -P.M_INT_UL), ("Indoor", -P.L_INDOOR["urbain"])]
fig, ax = plt.subplots(figsize=(8, 4.4))
level = 0
for i, (lab, v) in enumerate(steps):
    col = BLUE if v >= 0 else ORANGE
    ax.bar(i, v, bottom=level, color=col, width=0.6)
    ax.text(i, level + v + (2 if v >= 0 else -2), f"{v:+.1f}", ha="center", va="bottom" if v >= 0 else "top", color=INK, fontsize=9)
    level += v
ax.bar(len(steps), level, color="#256abf", width=0.6)
ax.text(len(steps), level + 2, f"{level:.1f} dB", ha="center", va="bottom", color=INK, fontsize=10, weight="bold")
ax.set_xticks(range(len(steps) + 1), [s[0] for s in steps] + ["MAPL"], rotation=20, ha="right")
ax.set_ylim(0, 185)
ax.set_ylabel("dB")
ax.set_title("Bilan de liaison UL, urbain indoor (bleu : gains, orange : pertes et marges)", loc="left", color=INK)
fig.savefig(FIG / "fig2_bilan_UL_urbain.png")
plt.close(fig)

# Fig 3: C/I distribution over the cell vs course worst case and bearer thresholds
fig, ax = plt.subplots(figsize=(8, 4.4))
xs = np.sort(sinr)
ax.plot(xs, np.arange(1, xs.size + 1) / xs.size * 100, color=BLUE, lw=2)
worst = db((math.sqrt(3) - 1) ** N_SLOPE / 6)
ax.axvline(worst, color=ORANGE, lw=1.5, ls="--")
ax.text(worst + 0.4, 85, f"pire cas du cours\n(q−1) : {worst:.1f} dB", color=INK2, fontsize=9)
ax.axvline(SINR_MIN, color=MUTED, lw=1, ls=":")
ax.text(SINR_MIN + 0.4, 50, f"bearer {P.BEARER_MIN} : {SINR_MIN} dB", color=INK2, fontsize=9)
ax.axvline(12, color=MUTED, lw=1, ls=":")
ax.text(12.4, 20, "MIMO : 12 dB", color=INK2, fontsize=9)
ax.set_xlim(-15, 30)
ax.set_xlabel("C/I (dB)")
ax.set_ylabel("% de la surface de la cellule sous ce C/I")
ax.set_title("C/I sur toute la cellule (K = 1, 6 interféreurs, pleine charge)", loc="left", color=INK)
fig.savefig(FIG / "fig3_CI_cellule.png")
plt.close(fig)

# Fig 4: nominal site plan (R-2 "position"): hexagonal tri-sector grid, ISD = 1.5 R
def lattice(isd, mask, x0=596000, y0=4032000):
    pts = []
    for j in range(int(10000 / (isd * math.sqrt(3) / 2)) + 2):
        for i in range(int(10000 / isd) + 2):
            x = isd / 2 + i * isd + (isd / 2 if j % 2 else 0)
            y = isd / 2 + j * isd * math.sqrt(3) / 2
            col, row = int(x // 100), int(y // 100)
            if col < 100 and row < 100 and mask[row, col]:
                pts.append((x0 + x, y0 - y))
    return pts


isd_u = 1.5 * R[("urbain", "tri-secteur")] * 1000
isd_r = 1.5 * R[("rural", "tri-secteur")] * 1000
s_u, s_r = lattice(isd_u, urban), lattice(isd_r, rural)
fig, ax = plt.subplots(figsize=(7, 7))
ext = (596, 606, 4022, 4032)
ax.imshow(dem, extent=ext, cmap="Greys", alpha=0.55)
ax.contour(np.linspace(596, 606, 400), np.linspace(4032, 4022, 400), dem, levels=[P.MASSIF_ALT_MIN], colors=[INK2], linewidths=1)
ax.contourf(np.linspace(596.05, 605.95, 100), np.linspace(4031.95, 4022.05, 100), urban.astype(float), levels=[0.5, 1.5], colors=[ORANGE], alpha=0.25)
ax.plot(*np.array(s_u).T / 1000, "^", color=ORANGE, ms=9, mec="#fcfcfb", mew=1.5, label=f"sites urbains ({len(s_u)})")
ax.plot(*np.array(s_r).T / 1000, "^", color=BLUE, ms=9, mec="#fcfcfb", mew=1.5, label=f"sites ruraux ({len(s_r)})")
ax.text(599.2, 4024.2, f"massif > {P.MASSIF_ALT_MIN:.0f} m\n(pas d'objectif, pas de site)", color=INK2, fontsize=9)
ax.set_xlabel("X UTM 32N (km)")
ax.set_ylabel("Y UTM 32N (km)")
ax.grid(False)
ax.legend(loc="upper left", frameon=True, facecolor="#fcfcfb", edgecolor=GRID)
ax.set_title("Plan nominal : grille hexagonale tri-secteur (point de départ pour Atoll)", loc="left", color=INK, fontsize=11)
fig.savefig(FIG / "fig4_plan_nominal.png")
plt.close(fig)

# ---- console summary ----
print(f"Zone: urban {A_URB:.2f} km² ({POP_URB:,.0f} hab), massif {A_MAS:.2f} km², rural {A_RUR:.2f} km²")
print(f"Margins: urban {M_SH['urbain']:.2f} dB, rural {M_SH['rural']:.2f} dB, alpha {N_SLOPE:.3f}")
print(f"RB edge: UL {RB_UL}, DL {RB_DL}")
for k, v in R.items():
    print(f"R {k}: {v:.3f} km")
print(f"Coverage sites: {N_COV}")
print(f"Capacity: eff {EFF_MEAN:.3f}, outage {OUTAGE:.3f}, cell DL {THR_DL:.1f} Mbps, subs/cell {SUBS_CELL}, cells {CELLS_CAP}, sites {SITES_CAP}")
print(f"Final: urban {N_URB}, rural {N_RUR}, total {N_URB + N_RUR}; nominal grid {len(s_u)} + {len(s_r)}")
print(f"800 vs 1800: {X1}")

# ---- site list for Atoll (A-3): tab-separated, paste into the Sites table ----
alt = lambda x, y: int(dem[int((4032000 - y) // 25), int((x - 596000) // 25)])
with open(OUT / "sites_nominaux.txt", "w", encoding="utf-8") as f:
    f.write("Name\tX\tY\tAltitude_DTM_m\n")
    for prefix, pts in (("ZAG_U", s_u), ("ZAG_R", s_r)):
        for k, (x, y) in enumerate(sorted(pts, key=lambda p: (-p[1], p[0])), 1):
            f.write(f"{prefix}{k:02d}\t{x:.0f}\t{y:.0f}\t{alt(x, y)}\n")
print("sites_nominaux.txt written")
