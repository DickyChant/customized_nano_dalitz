"""Trigger efficiency, generated (lines) vs reconstructed (markers), with the reco/gen ratio.
Marker colour = HLT path; marker fill opacity = resolved / (resolved + merged) in the bin,
counted over all candidates (no trigger requirement)."""
import json, sys, numpy as np
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from cmsplot import *
from matplotlib.colors import to_rgba, LinearSegmentedColormap
from matplotlib.cm import ScalarMappable

d = json.load(open(sys.argv[1] if len(sys.argv) > 1 else "trigeff_ratio_M125.json"))
TRIGS = [("Dipho30_22", "Diphoton30_22, Mass90", BLUE, "s"),
         ("Dipho30_18", "Diphoton30_18, Mass55", GREEN, "^"),
         ("OR", "OR of the two", GREY, "D")]
PANELS = [("mgs", r"$m_{\gamma^{*}}$ [GeV]", (0, 60)),
          ("dRee", r"$\Delta R(e,e)$", (0, 1))]
GREYS = LinearSegmentedColormap.from_list("fill", ["white", "black"])

def fres(rows):
    r = np.array([x["nRes"] for x in rows]); m = np.array([x["nMer"] for x in rows])
    tot = r + m
    return np.where(tot > 0, r / np.where(tot > 0, tot, 1), 0.0)

def shaded(ax, x, xe, y, ye, colour, marker, alpha, label=None):
    """errorbars in the path colour; marker face = path colour at the given opacity."""
    ax.errorbar(x, y, xerr=xe, yerr=ye, ls="none", color=colour, lw=1.6, zorder=3)
    faces = [to_rgba(colour, a) for a in np.clip(alpha, 0, 1)]
    ax.scatter(x, y, marker=marker, s=70, facecolors=faces, edgecolors=colour,
               linewidths=1.5, zorder=4, label=label)

fig, axes = plt.subplots(2, 2, figsize=(16, 8.8), sharex="col",
                         gridspec_kw={"height_ratios": [2.4, 1], "hspace": 0.06, "wspace": 0.42})
for col, (v, xlabel, xlim) in enumerate(PANELS):
    top, bot = axes[0][col], axes[1][col]
    gen, reco = d[v]["gen"], d[v]["reco"]
    edges = np.array([gen[0]["lo"]] + [r["hi"] for r in gen], float)
    x = 0.5*(edges[:-1] + edges[1:]); xe = 0.5*np.diff(edges)
    a_reco = fres(reco)
    for key, label, c, mk in TRIGS:
        g = np.array([r[key][0] for r in gen]);  ge = np.array([r[key][1] for r in gen])
        r_ = np.array([r[key][0] for r in reco]); re = np.array([r[key][1] for r in reco])
        top.step(edges, np.append(g, g[-1]), where="post", color=c, lw=1.4, zorder=2)
        shaded(top, x, xe, r_, re, c, mk, a_reco, label=label if col == 0 else None)
        ok = g > 0
        ratio = np.where(ok, r_ / np.where(ok, g, 1), np.nan)
        rerr = np.where(ok & (r_ > 0), ratio*np.sqrt((re/np.where(r_ > 0, r_, 1))**2 + (ge/np.where(ok, g, 1))**2), np.nan)
        shaded(bot, x, xe, ratio, rerr, c, mk, a_reco)
    yields(top, edges, [r["den"] for r in reco], color="0.90")
    style(top, "", "Trigger efficiency", ylim=(0, 1.05), xlim=xlim)
    top.tick_params(labelbottom=False)
    cms(top, sub="Simulation Preliminary", right="13 TeV")
    style(bot, xlabel, "reco / gen", ylim=(0, 1.25), xlim=xlim)
    bot.axhline(1.0, color="0.4", lw=1.2, ls="--", zorder=1)

leg = axes[0][0].legend(loc="lower right", fontsize=12, frameon=True, framealpha=0.95,
                        edgecolor="0.8", title="markers: reconstructed\nlines: generated",
                        title_fontsize=11)
leg._legend_box.align = "left"
for h in leg.legend_handles: h.set_facecolor(h.get_edgecolor())     # legend markers fully filled
cb = fig.colorbar(ScalarMappable(cmap=GREYS, norm=plt.Normalize(0, 1)), ax=axes[:, 1].tolist(),
                  pad=0.1, fraction=0.035)
cb.set_label("resolved / (resolved + merged)", fontsize=15); cb.ax.tick_params(labelsize=13)
for ext in ("png", "pdf"): fig.savefig(f"trigeff_combined.{ext}")
print("wrote trigeff_combined.png/pdf")
