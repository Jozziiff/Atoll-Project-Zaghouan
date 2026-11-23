"""Wide (20x20 km) preview of the Zaghouan area to choose the 10x10 km study extent.

Usage: .venv/bin/python 03-cartes/scripts/preview.py <dem.tif> <landcover.tif> <pop.tif> <out.png>
Inputs are already reprojected to EPSG:32632 on the same extent.
"""
import sys

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import BoundaryNorm, ListedColormap, LightSource
from matplotlib.patches import Patch, Rectangle
from osgeo import gdal

dem_p, lc_p, pop_p, out_p = sys.argv[1:5]


def load(path):
    ds = gdal.Open(path)
    gt = ds.GetGeoTransform()
    arr = ds.GetRasterBand(1).ReadAsArray().astype(float)
    nd = ds.GetRasterBand(1).GetNoDataValue()
    if nd is not None:
        arr[arr == nd] = np.nan
    ext = [gt[0], gt[0] + gt[1] * ds.RasterXSize, gt[3] + gt[5] * ds.RasterYSize, gt[3]]
    return arr, [e / 1000 for e in ext]  # km


dem, ext = load(dem_p)
lc, _ = load(lc_p)
pop, _ = load(pop_p)

# ESA WorldCover v200 classes
wc = {10: ("Arbres", "#006400"), 20: ("Arbustes", "#ffbb22"), 30: ("Prairie", "#ffff4c"),
      40: ("Cultures", "#f096ff"), 50: ("Bâti", "#fa0000"), 60: ("Sol nu", "#b4b4b4"),
      70: ("Neige", "#f0f0f0"), 80: ("Eau", "#0064c8"), 90: ("Zone humide", "#0096a0"),
      95: ("Mangrove", "#00cf75"), 100: ("Mousses", "#fae6a0")}
codes = sorted(wc)
cmap_lc = ListedColormap([wc[c][1] for c in codes])
norm_lc = BoundaryNorm([c - 0.5 for c in codes] + [codes[-1] + 0.5], len(codes))

town = (602.485, 4029.245)                      # NGA GeoNames, converted to UTM 32N (km)
park = [(600.206, 4025.235), (599.768, 4023.554)]  # park reference points (2 sources)
box = (596, 4022, 10, 10)                       # proposed study extent (km)

fig, axs = plt.subplots(1, 3, figsize=(18, 6.4), constrained_layout=True)

ls = LightSource(azdeg=315, altdeg=45)
rgb = ls.shade(dem, cmap=plt.cm.terrain, vert_exag=2, blend_mode="soft",
               vmin=0, vmax=np.nanmax(dem) * 1.05)
axs[0].imshow(rgb, extent=ext)
cs = axs[0].contour(np.flipud(dem), levels=range(200, 1400, 200), colors="k", linewidths=0.3,
                    extent=ext, origin="lower")
axs[0].clabel(cs, fontsize=6, fmt="%d m")
axs[0].set_title(f"Relief (Copernicus GLO-30) — {np.nanmin(dem):.0f} à {np.nanmax(dem):.0f} m")

present = [c for c in codes if np.any(lc == c)]
axs[1].imshow(lc, cmap=cmap_lc, norm=norm_lc, extent=ext, interpolation="nearest")
axs[1].legend(handles=[Patch(color=wc[c][1], label=f"{c} {wc[c][0]}") for c in present],
              loc="lower left", fontsize=7, framealpha=0.85)
axs[1].set_title("Occupation du sol (ESA WorldCover 2021, 10 m)")

im = axs[2].imshow(pop, cmap="magma_r", extent=ext, interpolation="nearest")
fig.colorbar(im, ax=axs[2], shrink=0.8, label="habitants / pixel 100 m")
axs[2].set_title(f"Population (WorldPop 2020) — total {np.nansum(pop):,.0f} hab.".replace(",", " "))

for ax in axs:
    ax.add_patch(Rectangle(box[:2], box[2], box[3], fill=False, ec="cyan", lw=2, ls="--"))
    ax.plot(*town, marker="*", ms=14, mfc="yellow", mec="k")
    for p in park:
        ax.plot(*p, marker="^", ms=9, mfc="white", mec="k")
    ax.set_xlabel("X UTM 32N (km)")
    ax.set_ylabel("Y UTM 32N (km)")

fig.suptitle("Zaghouan — aperçu 20×20 km | ★ ville  ▲ parc national (réf.)  ⬚ emprise proposée 10×10 km",
             fontsize=12)
fig.savefig(out_p, dpi=110)

# numbers for the log
x0, y0 = ext[0], ext[3]
def box_sum(arr, res_km):
    c0 = int(round((box[0] - x0) / res_km)); r0 = int(round((y0 - (box[1] + box[3])) / res_km))
    n = int(round(box[2] / res_km))
    return arr[r0:r0 + n, c0:c0 + n]
sub = box_sum(pop, 0.1)
print(f"Population in proposed box: {np.nansum(sub):,.0f}")
print(f"Population in wide 20x20 area: {np.nansum(pop):,.0f}")
dsub = box_sum(dem, 0.03)
print(f"DEM in box: min {np.nanmin(dsub):.0f} m, max {np.nanmax(dsub):.0f} m")
lsub = box_sum(lc, 0.01)
for c in present:
    print(f"  class {c} {wc[c][0]}: {np.mean(lsub == c) * 100:.1f} %")
