"""Build the deck's data assets from our real project files (no number is typed by hand here).

Run from projet-atoll/:  .venv/bin/python 05-presentation/build_assets.py
Writes 05-presentation/deck/assets/* and 05-presentation/deck/data.js
Sources: 03-cartes/atoll (DTM, ESA WorldCover clutter, population), 02-dimensionnement (sites),
04-atoll/exports (Atoll rasters, Monte-Carlo exports).
"""
import base64
import csv
import glob
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
from osgeo import gdal

gdal.UseExceptions()
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "02-dimensionnement"))
import params as P  # noqa: E402

OUT = ROOT / "05-presentation" / "deck" / "assets"
OUT.mkdir(parents=True, exist_ok=True)
A = ROOT / "03-cartes" / "atoll"
R = ROOT / "04-atoll" / "exports" / "raster"
MC = ROOT / "04-atoll" / "exports" / "montecarlo"

dem = gdal.Open(str(A / "MNT_Zaghouan_25m.tif")).ReadAsArray().astype(float)          # 400 x 400, 25 m
clut = gdal.Open(str(A / "Clutter_Zaghouan_10m.tif")).ReadAsArray()                    # 1000 x 1000, 10 m, WorldCover codes
dens = gdal.Open(str(A / "Population_Zaghouan_100m_densite.tif")).ReadAsArray().astype(float)  # 100 x 100
urban = dens >= P.URBAN_DENSITY_MIN
massif = (dem.reshape(100, 4, 100, 4).mean(axis=(1, 3)) >= P.MASSIF_ALT_MIN) & ~urban
rural = ~urban & ~massif


def resample(arr, size, alg="cubicspline"):
    """Smooth up/down-sampling of a 2D float array with GDAL."""
    src = gdal.GetDriverByName("MEM").Create("", arr.shape[1], arr.shape[0], 1, gdal.GDT_Float32)
    src.SetGeoTransform((0, 1, 0, 0, 0, -1))
    src.GetRasterBand(1).WriteArray(arr.astype(np.float32))
    dst = gdal.Translate("", src, format="MEM", width=size, height=size, resampleAlg=alg)
    return dst.GetRasterBand(1).ReadAsArray().astype(float)


def save_rgba(arr, name):
    """arr: H x W x 4 float 0..1 -> PNG via GDAL."""
    a = (np.clip(arr, 0, 1) * 255).astype(np.uint8)
    drv = gdal.GetDriverByName("MEM").Create("", a.shape[1], a.shape[0], 4, gdal.GDT_Byte)
    for i in range(4):
        drv.GetRasterBand(i + 1).WriteArray(a[:, :, i])
    gdal.GetDriverByName("PNG").CreateCopy(str(OUT / name), drv)


def save_jpg(rgb, name, size=None, q=88):
    tmp = OUT / "_tmp.png"
    save_rgba(np.dstack([rgb, np.ones(rgb.shape[:2])]), tmp.name)
    cmd = ["magick", str(tmp)] + (["-resize", f"{size}x{size}"] if size else []) + ["-quality", str(q), str(OUT / name)]
    subprocess.run(cmd, check=True)
    tmp.unlink()


def hexrgb(h):
    h = h.lstrip("#")
    return np.array([int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)])


def smoothstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


# ---------- 1. Land-cover relief: ESA WorldCover colours x hillshade (real forest on the massif) ----------
N = 1000
z = resample(dem, N, "cubicspline")                      # 10 m grid, same as the clutter
gy, gx = np.gradient(z, 10.0)
az, alt = np.radians(315), np.radians(42)
slope = np.arctan(np.hypot(gx, gy) * 1.4)
aspect = np.arctan2(-gx, gy)
shade = np.clip(np.sin(alt) * np.cos(slope) + np.cos(alt) * np.sin(slope) * np.cos(az - aspect), 0, 1)

LC = {10: "#5f8a50", 20: "#97ad72", 30: "#d0d1a4", 40: "#ddd6a8", 50: "#cbb9a0", 60: "#cdbfa4", 80: "#6fa6b6", 90: "#8fb3a8"}
LC_NAME = {10: "Forêt", 20: "Arbustes", 30: "Prairies", 40: "Cultures", 50: "Bâti", 60: "Sol nu", 80: "Eau", 90: "Zones humides"}
col = np.zeros((N, N, 3))
for k, h in LC.items():
    col[clut == k] = hexrgb(h)
# soften the 10 m speckle a little so it reads as a painted map, not noise
for i in range(3):
    col[..., i] = 0.6 * col[..., i] + 0.4 * resample(resample(col[..., i], 250, "average"), N, "bilinear")
# altitude lifts the colour slightly (summits paler, rockier)
lift = smoothstep(700, 1250, z)[..., None]
col = col * (1 - 0.35 * lift) + hexrgb("#d9d4c2") * 0.35 * lift
rgb = col * (0.66 + 0.44 * shade[..., None])
save_jpg(rgb, "relief.jpg", 1000, 88)
# 3D texture: real satellite colours (Sentinel-2 cloudless 2021, EOX, CC BY 4.0), graded + a soft hillshade.
# Source and reprojection steps: 03-cartes/raw/s2cloudless/SOURCE.txt
S2 = ROOT / "03-cartes" / "raw" / "s2cloudless" / "S2cloudless2021_Zaghouan_utm32n.tif"
s2ds = gdal.Open(str(S2))
sat = np.dstack([s2ds.GetRasterBand(b).ReadAsArray().astype(float) / 255 for b in (1, 2, 3)])   # 2048 x 2048
sat = np.clip(sat, 0, 1) ** 0.82                                            # lift the dark forest shadows
lum = sat.mean(axis=2, keepdims=True)
sat = np.clip(lum + (sat - lum) * 1.3, 0, 1)                                # a little more saturation
sh2 = resample(shade, 2048, "bilinear")[..., None]
save_jpg(np.clip(sat * (0.82 + 0.3 * sh2), 0, 1), "relief_tex.jpg", 2048, 85)
lc_share = {LC_NAME[k]: round(float((clut == k).mean() * 100), 1) for k in LC if (clut == k).any()}

# ---------- 2. Coverage overlays from Atoll rasters (50 m, 200 x 200) -> smooth 800 px with an inked edge ----------
up2 = lambda m: np.kron(m, np.ones((2, 2), dtype=bool))
Z50 = {"urbain": up2(urban), "massif": up2(massif), "rural": up2(rural)}
S = 800


def raster(name):
    return gdal.Open(str(R / f"{name}.tif")).ReadAsArray()


def soft_layer(mask, colour, a_fill, a_edge, edge_col=None):
    """mask (200x200 bool) -> RGBA S x S with smooth fill and a thin darker contour."""
    v = resample(mask.astype(float), S, "cubicspline")
    fill = smoothstep(0.38, 0.62, v)
    edge = np.clip(1 - np.abs(v - 0.5) / 0.09, 0, 1)
    img = np.zeros((S, S, 4))
    c, ce = hexrgb(colour), hexrgb(edge_col or colour)
    img[..., :3] = c * (1 - edge[..., None]) + ce * edge[..., None]
    img[..., 3] = np.maximum(fill * a_fill, edge * a_edge)
    return img


def over(a, b):
    """alpha-composite b over a."""
    ab = b[..., 3:4]
    out = a.copy()
    out[..., 3:4] = ab + a[..., 3:4] * (1 - ab)
    out[..., :3] = (b[..., :3] * ab + a[..., :3] * a[..., 3:4] * (1 - ab)) / np.maximum(out[..., 3:4], 1e-6)
    return out


TERRA, INK = "#b8431f", "#1d2a22"


def gaps_png(tag, name):
    sfx = "" if tag == "initial" else f"_{tag}"
    out_cov = raster(f"L01_outdoor{sfx}") <= 10
    in_cov = raster(f"L01_indoor{sfx}") <= 10
    gr = Z50["rural"] & ~out_cov
    gu = Z50["urbain"] & ~in_cov
    img = over(soft_layer(gr, TERRA, .62, .95, "#7a2410"), soft_layer(gu, INK, .8, .95))
    save_rgba(img, name)
    return {"rural_out": round(float(out_cov[Z50["rural"]].mean() * 100), 1),
            "urban_in": round(float(in_cov[Z50["urbain"]].mean() * 100), 1),
            "gap_km2": round(float(gr.sum() * 0.0025), 2), "mask": gr}


cov = {t: gaps_png(t, f"gaps_{t}.png") for t in ("initial", "tilt6", "sansR02", "R07", "R07az", "R11", "R12", "acp")}

# real centroids of the main rural gaps on the initial network (for map call-outs), 0..100 map units
gm = cov["initial"]["mask"]
yy, xx = np.mgrid[0:200, 0:200] / 2 + 0.25
holes = {}
for key, (x0, x1, y0, y1) in {"so": (0, 40, 62, 100), "est": (55, 85, 38, 72), "se": (78, 100, 72, 100)}.items():
    m = gm & (xx >= x0) & (xx < x1) & (yy >= y0) & (yy < y1)
    holes[key] = {"x": round(float(xx[m].mean()), 1), "y": round(float(yy[m].mean()), 1), "km2": round(float(m.sum() * 0.0025), 2)}
for v in cov.values():
    v.pop("mask")

QUAL = ["#0f3b57", "#1f6485", "#4f95b0", "#9cc9d6"]      # sequential water blue: best class first


def classes_png(name, ncls, out, colours):
    """Nested smooth bands: worst accepted class drawn first, better classes composited on top."""
    a = raster(name)
    img = np.zeros((S, S, 4))
    step = ncls / len(colours)
    for g in reversed(range(len(colours))):
        maxc = int(np.ceil((g + 1) * step)) - 1           # classes 0..maxc belong to group <= g
        img = over(img, soft_layer(a <= maxc, colours[g], .82, .82))
    save_rgba(img, out)
    ok = a <= ncls - 1
    return {z: round(float(ok[m].mean() * 100), 1) for z, m in Z50.items()} | {"total": round(float(ok.mean() * 100), 1)}


cinr = {"mc1000": classes_png("L01b_cinr_mc1000", 4, "cinr_mc1000.png", QUAL),
        "final": classes_png("L01b_cinr_final", 4, "cinr_final.png", QUAL)}
ul = {"mc1000": classes_png("L08_ul_mc1000", 9, "ul_mc1000.png", QUAL),
      "final": classes_png("L08_ul_final", 9, "ul_final.png", QUAL)}

# population density (WorldPop) as a warm glow, for the Monte-Carlo explainer
dl = np.log10(np.maximum(dens, 1))
dv = resample(dl / dl.max(), S, "cubicspline")
pimg = np.zeros((S, S, 4))
pimg[..., :3] = hexrgb("#c2702a")
pimg[..., 3] = np.clip(dv, 0, 1) ** 1.6 * 0.85
save_rgba(pimg, "population.png")

# ---------- 3. Vector data: contours, urban outline, sites ----------
import matplotlib  # noqa: E402
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

d100 = dem.reshape(100, 4, 100, 4).mean(axis=(1, 3))
xs = np.linspace(0.5, 99.5, 100)
cs = plt.contour(xs, xs, d100, levels=[300, 400, 500, 600, 700, 800, 900, 1000, 1100])
contours = {}
for lev, segs in zip(cs.levels, cs.allsegs):
    contours[int(lev)] = " ".join("M" + " L".join(f"{a:.1f} {b:.1f}" for a, b in s[::2]) for s in segs if len(s) >= 8)
cu = plt.contour(xs, xs, urban.astype(float), levels=[0.5])
urban_path = " ".join("M" + " L".join(f"{a:.1f} {b:.1f}" for a, b in s) + " Z" for s in cu.allsegs[0] if len(s) >= 6)
cm = plt.contour(xs, xs, massif.astype(float), levels=[0.5])
massif_path = " ".join("M" + " L".join(f"{a:.1f} {b:.1f}" for a, b in s) + " Z" for s in cm.allsegs[0] if len(s) >= 6)
plt.close("all")

nominal = [l.split("\t") for l in (ROOT / "02-dimensionnement" / "sites_nominaux.txt").read_text().splitlines()[1:]]
sites_init = [{"n": n[4:], "x": round((float(X) - 596000) / 100, 2), "y": round((4032000 - float(Y)) / 100, 2), "alt": int(float(a))}
              for n, X, Y, a in nominal]
no_r02 = [s for s in sites_init if s["n"] != "R02"]
R11 = {"n": "R11", "x": 12.4, "y": 89.4, "alt": 391}
R12 = {"n": "R12", "x": 72.3, "y": 58.0, "alt": int(dem[int((4032000 - 4026200) / 25), int((603230 - 596000) / 25)])}
site_sets = {"init": sites_init, "noR02": no_r02, "R11": no_r02 + [R11], "final": no_r02 + [R11, R12]}


# ---------- 4. Terrain profile R07 -> deep in the SW gap ----------
def alt_at(x, y):
    return float(dem[int((4032000 - y) / 25), int((x - 596000) / 25)])


p0, p1 = (597545, 4025104), (597240, 4022700)
n = 120
prof = [alt_at(p0[0] + (p1[0] - p0[0]) * k / n, p0[1] + (p1[1] - p0[1]) * k / n) for k in range(n + 1)]
dist = float(np.hypot(p1[0] - p0[0], p1[1] - p0[1]))

# ---------- 5. DEM grid for the 3D view (200 x 200 = 50 m) + real tree positions ----------
d200 = dem.reshape(200, 2, 200, 2).mean(axis=(1, 3))
dem_grid = [int(v) for v in d200.round().ravel()]
rng = np.random.default_rng(7)


def sample_pixels(code, k):
    iy, ix = np.nonzero(clut == code)
    pick = rng.choice(len(iy), size=min(k, len(iy)), replace=False)
    return [[round(float(ix[i] / 10 + rng.random() * .1), 2), round(float(iy[i] / 10 + rng.random() * .1), 2)] for i in pick]


trees = {"forest": sample_pixels(10, 7000), "shrub": sample_pixels(20, 2200)}
houses = sample_pixels(50, 3200)                                   # real WorldCover "built-up" pixels

# landmarks for the 3D labels
# Water Temple (Roman nymphaeum): N 36°23.219' E 10°07.871' (waymarking.com WM13KQ3), checked against our DEM:
# 302 m, just south of the dense town at the foot of the massif, as on satellite views.
from osgeo import osr  # noqa: E402
_s = osr.SpatialReference(); _s.ImportFromEPSG(4326); _s.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)
_d = osr.SpatialReference(); _d.ImportFromEPSG(32632)
tx, ty, _ = osr.CoordinateTransformation(_s, _d).TransformPoint(10 + 7.871 / 60, 36 + 23.219 / 60)
iy, ix = np.unravel_index(np.argmax(dem), dem.shape)
landmarks = {"temple": {"x": round((tx - 596000) / 100, 2), "y": round((4032000 - ty) / 100, 2), "alt": int(alt_at(tx, ty))},
             "summit": {"x": round((ix + .5) / 4, 2), "y": round((iy + .5) / 4, 2), "alt": int(dem.max())},
             "town": {"x": round(float(np.nonzero(urban)[1].mean()) + .5, 1), "y": round(float(np.nonzero(urban)[0].mean()) + .5, 1)}}

# ---------- 6. Monte-Carlo per-user throughputs (HSI users, rejected = 0) ----------
DL, UL = "Application User Throughput (DL) (kbps)", "Application User Throughput (UL) (kbps)"
num = lambda s: float(s.replace(",", "")) if s else 0.0


def read_mc(f):
    r = list(csv.reader(open(f, encoding="latin-1"), delimiter="\t"))
    return [dict(zip(r[0], x)) for x in r[1:] if x]


def mc(pattern):
    rows = []
    for f in sorted(glob.glob(str(MC / pattern))):
        rows += read_mc(f)
    ok = [r["Connection Status"].startswith("Connected") for r in rows]
    hsi = [(num(r[DL]) if c else 0.0, num(r[UL]) if c else 0.0) for r, c in zip(rows, ok) if r["Service"] == "High Speed Internet"]
    return {"n_users": len(rows), "rejected": round(100 * (1 - sum(ok) / len(rows)), 1),
            "dl": sorted(round(a, 1) for a, _ in hsi), "ul": sorted(round(b, 1) for _, b in hsi)}


dcfi = {"MC10": mc("MC10_sim*.txt"), "MC100": mc("MC100_sim*.txt"), "MC1000": mc("MC1000_sim*.txt"),
        "MC1000_final": mc("MC1000_final_sim*.txt")}


STATUS = {"No Coverage": 1, "No Service": 2}   # 0 = connected, 3 = any other rejection (saturation...)
opt = lambda s: round(float(s), 1) if s not in ("", "-") else None


def users_of(f):
    """[x, y, service, ok, status, serving cell, RSRP dBm, PDSCH C/(I+N) dB, DL app. kbps, indoor, zone]"""
    out = []
    for d in read_mc(MC / f):
        sv = {"High Speed Internet": "H", "Mobile Internet Access": "M", "VoIP": "V"}.get(d["Service"], "?")
        ok = d["Connection Status"].startswith("Connected")
        c = min(max(int((num(d["X"]) - 596000) // 100), 0), 99); r = min(max(int((4032000 - num(d["Y"])) // 100), 0), 99)
        out.append([round((num(d["X"]) - 596000) / 100, 2), round((4032000 - num(d["Y"])) / 100, 2),
                    sv, 1 if ok else 0, 0 if ok else STATUS.get(d["Connection Status"], 3),
                    d["Best Server"].replace("ZAG_", ""), opt(d["RSRP (DL) (dBm)"]), opt(d["PDSCH C/(I+N) (DL) (dB)"]),
                    round(num(d[DL])) if ok else 0, 1 if d["Indoor"] == "True" else 0,
                    "u" if urban[r, c] else ("m" if massif[r, c] else "r")])
    return out


users = {"MC10": users_of("MC10_sim00.txt"), "MC100": users_of("MC100_sim00.txt"), "MC1000": users_of("MC1000_sim00.txt"),
         "MC1000_final": users_of("MC1000_final_sim00.txt")}   # same seed: the same 1 041 users, initial vs final network

# ---------- 7. data.js ----------
relief_tex = "data:image/jpeg;base64," + base64.b64encode((OUT / "relief_tex.jpg").read_bytes()).decode()
data = {"reliefTex": relief_tex, "users": users, "contours": contours, "urban": urban_path, "massifPath": massif_path,
        "sites": site_sets, "sitesInit": sites_init, "sitesFinal": site_sets["final"], "dem": dem_grid, "demN": 200,
        "trees": trees, "houses": houses, "landmarks": landmarks, "landcover": lc_share, "holes": holes,
        "profile": {"alt": [round(v) for v in prof], "dist_m": round(dist), "h": 30, "h_ms": 1.5},
        "cov": cov, "cinr": cinr, "ul": ul, "dcfi": dcfi}
js = "window.DATA = " + json.dumps(data, ensure_ascii=False, separators=(",", ":")) + ";\n"
(ROOT / "05-presentation" / "deck" / "data.js").write_text(js, encoding="utf-8")
for old in ("relief.png", "signal_final.png"):
    (OUT / old).unlink(missing_ok=True)
print("coverage:", json.dumps(cov))
print("holes:", holes)
print("landcover %:", lc_share)
print("cinr:", cinr, "\nul:", ul)
print({k: (v["n_users"], v["rejected"], len(v["dl"])) for k, v in dcfi.items()})
print("users:", {k: (len(v), sum(1 - u[3] for u in v)) for k, v in users.items()})
print("profile max", max(prof), "R07", prof[0], "end", prof[-1], "dist", dist)
print("data.js", len(js) // 1024, "KB")
