"""Two ways to show which reconstruction category drives the trigger performance.

  A: efficiency per category + stacked composition underneath
  B: one curve, marker fill shaded white->black by the resolved fraction in the bin
"""
import json, sys, numpy as np
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from cmsplot import *
from matplotlib.lines import Line2D

d = json.load(open("trigeff_bycat_M125.json"))
PANELS = [("mgs", r"generated $m_{\gamma^{*}}$ [GeV]", (0, 60)),
          ("dRee", r"generated $\Delta R(e,e)$", (0, 1))]
TRIG = sys.argv[1] if len(sys.argv) > 1 else "OR"
TLABEL = {"OR": "OR of the diphoton paths",
          "Dipho30_22": "Diphoton30_22, Mass90", "Dipho30_18": "Diphoton30_18, Mass55"}[TRIG]
CATS = [("merged2Gsf", "merged, 2 GSF tracks", BLUE, "o"),
        ("merged1Gsf", "merged, 1 GSF track", SKY, "s"),
        ("resolved", "resolved", ORANGE, "^")]
MINDEN = 1000.0   # skip markers in bins with too few weighted events to be meaningful

# ---------------------------------------------------------------- version A
fig, axes = plt.subplots(2, 2, figsize=(15, 8.8), sharex="col",
                         gridspec_kw={"height_ratios": [2.2, 1], "hspace": 0.07, "wspace": 0.2})
for col, (v, xlabel, xlim) in enumerate(PANELS):
    top, bot = axes[0][col], axes[1][col]
    rows_all = d[v]["all"]
    edges = np.array([rows_all[0]["lo"]] + [r["hi"] for r in rows_all], float)
    for key, label, c, mk in CATS:
        r = d[v][key]
        y = np.array([x[TRIG][0] for x in r]); e = np.array([x[TRIG][1] for x in r])
        nn = np.array([x["den"] for x in r])
        y = np.where(nn >= MINDEN, y, np.nan)
        band(top, edges, y, e, e, color=c, marker=mk, label=label if col == 0 else None)
    den_k = sum(np.array([x["den"] for x in d[v][k]]) for k, *_ in CATS)
    pass_k = sum(np.array([x["den"]*x[TRIG][0] for x in d[v][k]]) for k, *_ in CATS)
    y = np.where(den_k > 0, pass_k / np.where(den_k > 0, den_k, 1), np.nan)
    top.step(edges, np.append(y, y[-1]), where="post", color="0.25", lw=1.6,
             label="merged + resolved" if col == 0 else None)
    style(top, "", f"Efficiency ({TLABEL})", ylim=(0, 1.15), xlim=xlim)
    top.tick_params(labelbottom=False); cms(top, sub="Simulation Preliminary")
    # stacked candidate yields
    bottom = np.zeros(len(rows_all))
    for key, label, c, _ in CATS:
        n = np.array([x["den"] for x in d[v][key]])
        bot.bar(edges[:-1], n, width=np.diff(edges), bottom=bottom, align="edge",
                color=c, edgecolor="white", lw=0.5, label=label if col == 0 else None)
        bottom += n
    style(bot, xlabel, "Candidates / bin", ylim=(None, None), xlim=xlim)
    bot.set_yscale("log"); bot.set_ylim(bottom[bottom > 0].min()*0.5, bottom.max()*8)
    bot.grid(False)
axes[0][0].legend(loc="lower right", fontsize=11, frameon=True, framealpha=0.95, edgecolor="0.8")
for ext in ("png", "pdf"): fig.savefig(f"trigeff_bycat_stacked_{TRIG}.{ext}")

# ---------------------------------------------------------------- version B
fig2, axes2 = plt.subplots(1, 2, figsize=(15, 6.2))
cmap = plt.get_cmap("Greys")
for col, (v, xlabel, xlim) in enumerate(PANELS):
    ax = axes2[col]
    rows_all = d[v]["all"]
    edges = np.array([rows_all[0]["lo"]] + [r["hi"] for r in rows_all], float)
    x = 0.5*(edges[:-1]+edges[1:]); xe = 0.5*np.diff(edges)
    den_k = sum(np.array([x["den"] for x in d[v][k]]) for k, *_ in CATS)
    pass_k = sum(np.array([x["den"]*x[TRIG][0] for x in d[v][k]]) for k, *_ in CATS)
    tot = np.where(den_k > 0, den_k, 1)
    fres = np.array([r["den"] for r in d[v]["resolved"]]) / tot     # 0 = all merged, 1 = all resolved
    y = pass_k / tot
    e = np.sqrt(np.clip(y*(1-y), 0, None) / tot)
    ax.errorbar(x, y, xerr=xe, yerr=e, ls="none", ecolor="0.4", lw=1.4, zorder=2)
    sc = ax.scatter(x, y, c=fres, cmap=cmap, vmin=0, vmax=1, s=130, edgecolor="0.2",
                    linewidth=1.2, zorder=3)
    style(ax, xlabel, f"Efficiency, {TLABEL}", ylim=(0, 1.05), xlim=xlim)
    cms(ax, sub="Simulation Preliminary")
    if col == 1:
        cb = fig2.colorbar(sc, ax=ax, pad=0.02)
        cb.set_label("resolved fraction in bin", fontsize=15); cb.ax.tick_params(labelsize=13)
fig2.tight_layout()
for ext in ("png", "pdf"): fig2.savefig(f"trigeff_bycat_shaded_{TRIG}.{ext}")
print(f"wrote trigeff_bycat_stacked_{TRIG}.png and trigeff_bycat_shaded_{TRIG}.png")
