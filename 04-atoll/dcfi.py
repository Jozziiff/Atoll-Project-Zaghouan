"""L-11: DCFI (inverse cumulative distribution = P(throughput >= x)) for the Monte-Carlo groups MC-10/100/1000.

Run from projet-atoll/:
    .venv/bin/python 04-atoll/dcfi.py [tag]
Reads 04-atoll/exports/montecarlo/MC<N>_simXX.txt (Atoll: simulation > Mobiles > Actions > Export, tab-separated).
With a tag (e.g. "apres"), reads MC<N>_<tag>_simXX.txt instead, for the before/after of the optimisation.

One row = one drawn user. Rejected users (status not "Connected...") count as 0 kbps: the DCFI stays honest.
Main curves = High Speed Internet users (the service of our objective C1: 1 024 kbps DL / 128 kbps UL at RLC level,
i.e. 972.8 / 121.6 kbps at application level after the 0.95 scaling factor).
"""
import csv
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
MC = ROOT / "04-atoll" / "exports" / "montecarlo"
tag = sys.argv[1] if len(sys.argv) > 1 else ""
mid = f"_{tag}" if tag else ""
GROUPS = (10, 100, 1000)
DL, UL = "Application User Throughput (DL) (kbps)", "Application User Throughput (UL) (kbps)"
APP = 0.95
DEMAND = {"High Speed Internet": (1024, 128), "Mobile Internet Access": (128, 64), "VoIP": (12.2, 12.2)}  # max DL, UL


def load(n):
    rows = []
    files = sorted(MC.glob(f"MC{n}{mid}_sim*.txt"))
    for f in files:
        r = list(csv.reader(f.open(encoding="latin-1"), delimiter="\t"))
        rows += [dict(zip(r[0], x)) for x in r[1:] if x]
    return files, rows


def num(s):
    try:
        return float(s.replace(",", ""))
    except ValueError:
        return 0.0


data, lines = {}, []
lines += [f"## DCFI Monte-Carlo{' — ' + tag if tag else ''} (L-11)", "",
          "DCFI(x) = part des utilisateurs dont le débit applicatif est ≥ x. Rejetés comptés à 0 kbps.", "",
          "| Groupe | Fichiers | Utilisateurs tirés | Rejetés | HSI : % à 100 % du débit DL demandé | HSI : débit DL médian | "
          "HSI : % ≥ 128 kbps UL | Tous services : % servis à 100 % (DL) |",
          "|---|---|---|---|---|---|---|---|"]
for n in GROUPS:
    files, rows = load(n)
    if not rows:
        lines.append(f"| MC-{n} | 0 | — | — | — | — | — | — |")
        continue
    ok = [r["Connection Status"].startswith("Connected") for r in rows]
    dl = np.array([num(r[DL]) if c else 0.0 for r, c in zip(rows, ok)])
    ul = np.array([num(r[UL]) if c else 0.0 for r, c in zip(rows, ok)])
    svc = np.array([r["Service"] for r in rows])
    hsi = svc == "High Speed Internet"
    full = np.array([d >= APP * DEMAND.get(s, (0, 0))[0] - 0.5 for d, s in zip(dl, svc)])
    data[n] = (np.sort(dl[hsi]), np.sort(ul[hsi]))
    lines.append(f"| MC-{n} | {len(files)} | {len(rows)} ({len(rows) / len(files):.1f} / simulation) | "
                 f"{100 * (1 - np.mean(ok)):.1f} % | {100 * np.mean(dl[hsi] >= APP * 1024 - 0.5):.1f} % | "
                 f"{np.median(dl[hsi]):.0f} kbps | {100 * np.mean(ul[hsi] >= APP * 128 - 0.5):.1f} % | "
                 f"{100 * np.mean(full):.1f} % |")
lines.append("")
out = ROOT / "04-atoll" / "exports" / f"dcfi{mid}.md"
out.write_text("\n".join(lines) + "\n", encoding="utf-8")
print("\n".join(lines))

# Figure: 3 curves on the same graph (L-11), DL and UL side by side. Sequential blue = 10 -> 1000 users (ordered load).
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

INK, INK2, MUTED, GRID, BG = "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#fcfcfb"
SHADES = {10: "#8fbbef", 100: "#2a78d6", 1000: "#123f78"}
plt.rcParams.update({"font.size": 11, "axes.edgecolor": "#c3c2b7", "axes.labelcolor": INK2, "xtick.color": MUTED,
                     "ytick.color": MUTED, "axes.spines.top": False, "axes.spines.right": False,
                     "figure.facecolor": BG, "axes.facecolor": BG, "savefig.bbox": "tight"})
fig, axes = plt.subplots(1, 2, figsize=(12, 4.8))
for ax, k, target, name in ((axes[0], 0, 1024, "DL"), (axes[1], 1, 128, "UL")):
    for n, (d, u) in data.items():
        x = (d, u)[k]
        p = 1 - np.arange(len(x)) / len(x)          # P(X >= x_i) on the sorted sample
        ax.step(x, 100 * p, where="post", color=SHADES[n], lw=2, label=f"MC-{n} ({len(x)} utilisateurs HSI)")
    ax.axvline(APP * target, color=INK2, lw=1, ls="--")
    ax.text(APP * target, 103, f" demande HSI\n {APP * target:.1f} kbps", fontsize=9, color=INK2, va="bottom", ha="right")
    ax.set_xlabel(f"Débit applicatif utilisateur {name} (kbps)")
    ax.set_ylim(0, 112)
    ax.set_xlim(0, APP * target * 1.08)
    ax.grid(color=GRID, lw=0.6)
    ax.set_title(f"{name} — utilisateurs High Speed Internet", loc="left", fontsize=11, color=INK)
axes[0].set_ylabel("Part des utilisateurs avec débit ≥ x (%)")
axes[0].legend(loc="lower left", frameon=True, facecolor=BG, edgecolor=GRID, fontsize=9)
fig.suptitle(f"DCFI des débits — Monte-Carlo 10 / 100 / 1000 utilisateurs{' (' + tag + ')' if tag else ''}",
             x=0.06, ha="left", fontsize=12, color=INK)
png = ROOT / "04-atoll" / "exports" / f"L-11_DCFI{mid}.png"
fig.savefig(png, dpi=150)
print("figure:", png.relative_to(ROOT))

# With a tag: before/after figure for MC-1000 (same seed = same users drawn), all HSI users, DL and UL (L-12, P-4/P-5).
if tag and 1000 in data:
    mid_saved, mid = mid, ""
    _, rows0 = load(1000)
    mid = mid_saved

    def hsi(rows):
        ok = [r["Connection Status"].startswith("Connected") for r in rows]
        d = np.sort([num(r[DL]) if c else 0.0 for r, c in zip(rows, ok) if r["Service"] == "High Speed Internet"])
        u = np.sort([num(r[UL]) if c else 0.0 for r, c in zip(rows, ok) if r["Service"] == "High Speed Internet"])
        return d, u

    before, after = hsi(rows0), data[1000]
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.8))
    for ax, k, target, name in ((axes[0], 0, 1024, "DL"), (axes[1], 1, 128, "UL")):
        for (d, u), lab, col in ((before, "réseau initial", "#9a9890"), (after, f"réseau {tag}", "#2a78d6")):
            x = (d, u)[k]
            ax.step(x, 100 * (1 - np.arange(len(x)) / len(x)), where="post", color=col, lw=2, label=f"MC-1000 {lab}")
        ax.axvline(APP * target, color=INK2, lw=1, ls="--")
        ax.text(APP * target, 103, f" demande HSI\n {APP * target:.1f} kbps", fontsize=9, color=INK2, va="bottom", ha="right")
        ax.set_xlabel(f"Débit applicatif utilisateur {name} (kbps)")
        ax.set_ylim(0, 112)
        ax.set_xlim(0, APP * target * 1.08)
        ax.grid(color=GRID, lw=0.6)
        ax.set_title(f"{name} — utilisateurs High Speed Internet", loc="left", fontsize=11, color=INK)
    axes[0].set_ylabel("Part des utilisateurs avec débit ≥ x (%)")
    axes[0].legend(loc="lower left", frameon=True, facecolor=BG, edgecolor=GRID, fontsize=9)
    fig.suptitle("DCFI MC-1000 — avant / après optimisation (mêmes utilisateurs tirés, graine 1)", x=0.06, ha="left",
                 fontsize=12, color=INK)
    png2 = ROOT / "04-atoll" / "exports" / f"L-11_DCFI_MC1000_avant_apres{mid}.png"
    fig.savefig(png2, dpi=150)
    print("figure:", png2.relative_to(ROOT))
