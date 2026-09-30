"""Shared plot style: mplhep CMS + an Okabe-Ito (colourblind-safe) palette."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import mplhep as hep
import numpy as np

hep.style.use(hep.style.CMS)
plt.rcParams.update({
    "figure.dpi": 140, "savefig.dpi": 200, "savefig.bbox": "tight",
    "axes.labelsize": 20, "axes.titlesize": 17,
    "xtick.labelsize": 16, "ytick.labelsize": 16, "legend.fontsize": 13,
})

# Okabe-Ito
BLUE, VERM, GREEN, ORANGE, PURPLE, SKY, GREY = (
    "#0072B2", "#D55E00", "#009E73", "#E69F00", "#CC79A7", "#56B4E9", "#555555")

def cms(ax, sub="Simulation", right="2018 UL (13 TeV)"):
    hep.cms.text(sub, ax=ax, fontsize=19)
    ax.text(1.0, 1.005, right, transform=ax.transAxes, ha="right", va="bottom", fontsize=15)

def style(ax, xlabel, ylabel="Trigger efficiency", ylim=(0, 1.05), xlim=None):
    ax.set_xlabel(xlabel); ax.set_ylabel(ylabel)
    ax.set_ylim(*ylim)
    if xlim: ax.set_xlim(*xlim)
    ax.grid(True, which="major", color="0.88", lw=0.8)
    ax.set_axisbelow(True)
    ax.tick_params(which="both", direction="in", top=True, right=True)

def band(ax, edges, y, ylo=None, yhi=None, **kw):
    """Draw per-bin values as horizontal bin markers with vertical error bars."""
    edges = np.asarray(edges, float); y = np.asarray(y, float)
    x = 0.5 * (edges[:-1] + edges[1:]); xerr = 0.5 * (edges[1:] - edges[:-1])
    yerr = None if ylo is None else np.vstack([ylo, yhi])
    return ax.errorbar(x, y, xerr=xerr, yerr=yerr, ls="none", marker=kw.pop("marker", "o"),
                       ms=kw.pop("ms", 6), lw=1.6, capsize=0, **kw)


def yields(ax, edges, counts, label="Candidates / bin", color="0.80", logy=True):
    """Draw the per-bin candidate yield as a filled histogram behind the markers,
    on a twin right-hand axis. Returns the twin axis."""
    import numpy as np
    edges = np.asarray(edges, float); counts = np.asarray(counts, float)
    tw = ax.twinx()
    tw.fill_between(edges, np.append(counts, counts[-1]), step="post", color=color,
                    linewidth=0, zorder=0)
    tw.set_ylabel(label, fontsize=15, color="0.35")
    tw.tick_params(axis="y", labelsize=12, colors="0.35", direction="in")
    if logy:
        tw.set_yscale("log")
        pos = counts[counts > 0]
        if len(pos): tw.set_ylim(pos.min() * 0.5, counts.max() * 60)
    else:
        tw.set_ylim(0, counts.max() * 3.0)
    tw.set_zorder(0); ax.set_zorder(1); ax.patch.set_visible(False)
    return tw
