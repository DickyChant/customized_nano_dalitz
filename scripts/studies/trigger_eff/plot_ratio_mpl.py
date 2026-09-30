"""Efficiency binned in the generated (perfect-resolution) vs reconstructed pair variable,
same events, with the reco/gen ratio underneath."""
import json, sys, numpy as np
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from cmsplot import *

d = json.load(open(sys.argv[1] if len(sys.argv) > 1 else "trigeff_ratio_M125.json"))
TRIGS = [("Dipho30_22", "Diphoton30_22, Mass90", BLUE, "s"),
         ("Dipho30_18", "Diphoton30_18, Mass55", GREEN, "^"),
         ("OR", "OR of the two", GREY, "D")]
PANELS = [("mgs", r"$m_{\gamma^{*}}$ [GeV]", (0, 60)),
          ("dRee", r"$\Delta R(e,e)$", (0, 1))]

fig, axes = plt.subplots(2, 2, figsize=(15, 8.6), sharex="col",
                         gridspec_kw={"height_ratios": [2.4, 1], "hspace": 0.06, "wspace": 0.42})
for col, (v, xlabel, xlim) in enumerate(PANELS):
    top, bot = axes[0][col], axes[1][col]
    gen, reco = d[v]["gen"], d[v]["reco"]
    edges = [gen[0]["lo"]] + [r["hi"] for r in gen]
    for key, label, c, mk in TRIGS:
        g = np.array([r[key][0] for r in gen]);  ge = np.array([r[key][1] for r in gen])
        r_ = np.array([r[key][0] for r in reco]); re = np.array([r[key][1] for r in reco])
        ge_edges = np.asarray(edges, float)
        top.step(ge_edges, np.append(g, g[-1]), where="post", color=c, lw=1.4, alpha=0.9, zorder=2)
        band(top, edges, r_, re, re, color=c, marker=mk,
             label=f"{label}" if col == 0 else None, zorder=3)
        ok = g > 0
        ratio = np.where(ok, r_ / np.where(ok, g, 1), np.nan)
        rerr = np.where(ok, ratio * np.sqrt((re / np.where(r_ > 0, r_, np.inf))**2 +
                                            (ge / np.where(ok, g, np.inf))**2), np.nan)
        band(bot, edges, ratio, rerr, rerr, color=c, marker=mk)
    yields(top, edges, [x["den"] for x in reco])
    style(top, "", "Trigger efficiency", ylim=(0, 1.05), xlim=xlim)
    top.tick_params(labelbottom=False)
    cms(top, sub="Simulation Preliminary", right="13 TeV")
    style(bot, xlabel, "reco / gen", ylim=(0, 1.25), xlim=xlim)
    bot.axhline(1.0, color="0.4", lw=1.2, ls="--", zorder=1)
leg = axes[0][0].legend(loc="lower right", fontsize=12, frameon=True, framealpha=0.95,
                        edgecolor="0.8", title="markers: reconstructed\nlines: generated",
                        title_fontsize=11, handletextpad=0.6)
leg._legend_box.align = "left"
for ext in ("png", "pdf"): fig.savefig(f"trigeff_gen_vs_reco_ratio.{ext}")
print("wrote trigeff_gen_vs_reco_ratio.png/pdf")
