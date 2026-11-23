"""Coverage per objective zone, from Atoll signal-level exports (A-7: objectives vs obtained).

Run from projet-atoll/:
    .venv/bin/python 04-atoll/analyse_couverture.py <tag>
e.g. tag = "initial" reads 04-atoll/exports/raster/L01_indoor.tif and L01_outdoor.tif
(for later runs, export to L01_indoor_<tag>.tif / L01_outdoor_<tag>.tif).

The Atoll export is a class raster (legend index): 0 = ">= -70 dBm" ... 10 = ">= -120 dBm", 11 = not covered.
Zones are the same as Étape 1 (02-dimensionnement/params.py): urban core, massif (no objective), rural.
Objectives (hypotheses E1/E2): urban INDOOR >= 95 % of the area, rural OUTDOOR >= 95 % of the area.
"""
import sys
from pathlib import Path

import numpy as np
from osgeo import gdal

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "02-dimensionnement"))
import params as P  # noqa: E402

gdal.UseExceptions()
ROOT = Path(__file__).resolve().parents[1]
RASTER = ROOT / "04-atoll" / "exports" / "raster"
tag = sys.argv[1] if len(sys.argv) > 1 else "initial"
suffix = "" if tag == "initial" else f"_{tag}"
COVERED_MAX_CLASS = 10   # classes 0..10 = signal >= -120 dBm

# Zones on the 100 m grid (same rule as calc.py), upsampled to the 50 m Atoll grid
A = ROOT / "03-cartes" / "atoll"
dens = gdal.Open(str(A / "Population_Zaghouan_100m_densite.tif")).ReadAsArray().astype(float)
dem = gdal.Open(str(A / "MNT_Zaghouan_25m.tif")).ReadAsArray().astype(float)
dem100 = dem.reshape(100, 4, 100, 4).mean(axis=(1, 3))
urban = dens >= P.URBAN_DENSITY_MIN
massif = (dem100 >= P.MASSIF_ALT_MIN) & ~urban
rural = ~urban & ~massif
up = lambda m: np.kron(m, np.ones((2, 2), dtype=bool))
Z = {"urbain": up(urban), "massif": up(massif), "rural": up(rural)}
people50 = np.kron(dens * 0.01, np.ones((2, 2))) / 4   # inhabitants per 50 m pixel


def load(name):
    ds = gdal.Open(str(RASTER / f"{name}{suffix}.tif"))
    gt = ds.GetGeoTransform()
    assert (gt[0], gt[3], gt[1]) == (596000.0, 4032000.0, 50.0), f"unexpected grid {gt}"
    return ds.ReadAsArray() <= COVERED_MAX_CLASS


cov = {"indoor": load("L01_indoor"), "outdoor": load("L01_outdoor")}

rows = []
for zone, mask in Z.items():
    area = mask.sum() * 0.0025
    for mode in ("indoor", "outdoor"):
        c = cov[mode][mask]
        rows.append((zone, mode, area, c.mean() * 100, people50[mask][c].sum() / people50[mask].sum() * 100))

obj = {("urbain", "indoor"): 95, ("rural", "outdoor"): 95}
lines = [f"## Couverture par zone — réseau `{tag}` (signal ≥ −120 dBm, ombrage 86 %)", "",
         "| Zone | Mode | Surface (km²) | % surface couverte | % population couverte | Objectif | Verdict |",
         "|---|---|---|---|---|---|---|"]
for zone, mode, area, pa, pp in rows:
    o = obj.get((zone, mode))
    verdict = "" if o is None else ("✅ atteint" if pa >= o else f"❌ manque {o - pa:.1f} pts")
    lines.append(f"| {zone} | {mode} | {area:.2f} | {pa:.1f} % | {pp:.1f} % | {'' if o is None else f'≥ {o} %'} | {verdict} |")
lines.append("")
out = ROOT / "04-atoll" / "exports" / f"couverture_zones_{tag}.md"
out.write_text("\n".join(lines) + "\n", encoding="utf-8")
print("\n".join(lines))

# Figure: where the objective is NOT met (uncovered pixels inside objective zones) -> guides optimisation
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

fig, ax = plt.subplots(figsize=(7, 7))
ext = (596, 606, 4022, 4032)
ax.imshow(dem, extent=ext, cmap="Greys", alpha=0.5)
gap_u = Z["urbain"] & ~cov["indoor"]
gap_r = Z["rural"] & ~cov["outdoor"]
img = np.zeros((200, 200, 4))
img[gap_r] = (0.165, 0.471, 0.839, 0.85)   # blue: rural outdoor gap
img[gap_u] = (0.922, 0.408, 0.204, 0.95)   # orange: urban indoor gap
ax.imshow(img, extent=ext)
ax.contour(np.linspace(596, 606, 400), np.linspace(4032, 4022, 400), dem, levels=[P.MASSIF_ALT_MIN],
           colors=["#52514e"], linewidths=1)
sites = [l.split("\t") for l in (ROOT / "02-dimensionnement" / "sites_nominaux.txt").read_text().splitlines()[1:]]
for name, x, y, _ in sites:
    ax.plot(float(x) / 1000, float(y) / 1000, "^", color="#0b0b0b", ms=6)
    ax.text(float(x) / 1000 + 0.08, float(y) / 1000 + 0.08, name[4:], fontsize=7, color="#0b0b0b")
ax.set_title(f"Trous de couverture dans les zones à objectif — réseau {tag}\n"
             "orange : centre urbain non couvert en indoor · bleu : zone rurale non couverte en outdoor",
             loc="left", fontsize=10, color="#0b0b0b")
ax.set_xlabel("X UTM 32N (km)")
ax.set_ylabel("Y UTM 32N (km)")
fig.savefig(ROOT / "04-atoll" / "exports" / f"trous_couverture_{tag}.png", dpi=150, bbox_inches="tight")
print("figure:", f"04-atoll/exports/trous_couverture_{tag}.png")
