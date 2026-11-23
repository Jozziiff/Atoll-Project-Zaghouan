"""Per-zone share of an Atoll class raster that meets a threshold (A-7: objective vs obtained, per zone).

Run from projet-atoll/:
    .venv/bin/python 04-atoll/zones_raster.py <raster name without .tif> <max class> "<label>"
e.g. L01b_cinr_mc1000 3 "C/(I+N) >= -1 dB"   (classes 0..3 of the L-01b legend = >= -1 dB)
     L08_ul_mc1000    8 "UL >= 128 kbps"     (classes 0..8 of the L-08 legend = >= 128 kbps)
Atoll exports the legend class per 50 m pixel (0 = best class); the last class index = "not covered".
Zones = Étape 1 zones (same code as analyse_couverture.py). Appends a table to exports/zones_<raster>.md.
"""
import sys
from pathlib import Path

import numpy as np
from osgeo import gdal

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "02-dimensionnement"))
import params as P  # noqa: E402

gdal.UseExceptions()
ROOT = Path(__file__).resolve().parents[1]
name, max_class, label = sys.argv[1], int(sys.argv[2]), sys.argv[3]

A = ROOT / "03-cartes" / "atoll"
dens = gdal.Open(str(A / "Population_Zaghouan_100m_densite.tif")).ReadAsArray().astype(float)
dem = gdal.Open(str(A / "MNT_Zaghouan_25m.tif")).ReadAsArray().astype(float)
urban = dens >= P.URBAN_DENSITY_MIN
massif = (dem.reshape(100, 4, 100, 4).mean(axis=(1, 3)) >= P.MASSIF_ALT_MIN) & ~urban
up = lambda m: np.kron(m, np.ones((2, 2), dtype=bool))
Z = {"urbain": up(urban), "massif": up(massif), "rural": up(~urban & ~massif)}
people = np.kron(dens * 0.01, np.ones((2, 2))) / 4

ds = gdal.Open(str(ROOT / "04-atoll" / "exports" / "raster" / f"{name}.tif"))
assert ds.GetGeoTransform()[:2] == (596000.0, 50.0), ds.GetGeoTransform()
ok = ds.ReadAsArray() <= max_class

lines = [f"## {label} par zone — `{name}`", "", "| Zone | Surface (km²) | % surface | % population |", "|---|---|---|---|"]
for z, m in Z.items():
    lines.append(f"| {z} | {m.sum() * 0.0025:.2f} | {ok[m].mean() * 100:.1f} % | {people[m][ok[m]].sum() / people[m].sum() * 100:.1f} % |")
lines.append(f"| **total** | 100.00 | {ok.mean() * 100:.1f} % | {people[ok].sum() / people.sum() * 100:.1f} % |")
out = ROOT / "04-atoll" / "exports" / f"zones_{name}.md"
out.write_text("\n".join(lines) + "\n", encoding="utf-8")
print("\n".join(lines))
