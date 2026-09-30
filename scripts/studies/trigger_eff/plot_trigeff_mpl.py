"""Trigger efficiency vs m_gamma* and dR(e,e) -- modern (mplhep) version."""
import json, sys, numpy as np
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from cmsplot import *

d = json.load(open(sys.argv[1] if len(sys.argv) > 1 else "trigeff_M125.json"))
DEN = sys.argv[2] if len(sys.argv) > 2 else "recoMatch"
TRIGS = [
    ("HLT_Diphoton30_22_R9Id_OR_IsoCaloId_AND_HE_R9Id_Mass90", "HLT_Diphoton30_22_R9Id_OR_IsoCaloId_AND_HE_R9Id_Mass90", BLUE, "s"),
    ("HLT_Diphoton30_18_R9IdL_AND_HE_AND_IsoCaloId_NoPixelVeto_Mass55", "HLT_Diphoton30_18_R9IdL_AND_HE_AND_IsoCaloId_NoPixelVeto_Mass55", GREEN, "^"),
]
LEVEL = "reconstructed" if DEN == "reco" else "generated"
PANELS = [("mgs", rf"{LEVEL} $m_{{\gamma^{{*}}}}$ [GeV]", (0, 60)),
          ("dRee", rf"{LEVEL} $\Delta R(e,e)$", (0, 1))]

fig, axes = plt.subplots(1, 2, figsize=(15, 6.2))
for ax, (v, xlabel, xlim) in zip(axes, PANELS):
    rows = d[DEN][v]
    edges = [rows[0]["lo"]] + [r["hi"] for r in rows]
    for key, label, col, mk in TRIGS:
        y = [r[key][0] for r in rows]
        lo = [r[key][1] for r in rows]; hi = [r[key][2] for r in rows]
        band(ax, edges, y, lo, hi, color=col, marker=mk, label=label)
    yields(ax, edges, [r["den"] for r in rows])
    style(ax, xlabel, xlim=xlim)
    cms(ax, sub="Simulation Preliminary")
axes[0].legend(loc="upper left", frameon=True, framealpha=0.95, edgecolor="0.8", fontsize=11,
               handletextpad=0.5, borderpad=0.7,
               title=r"H$\to\gamma^{*}\gamma\to ee\gamma$, $m_{H}=125$ GeV", title_fontsize=11)
fig.tight_layout()
for ext in ("png", "pdf"): fig.savefig(f"trigeff_M125_{DEN}_v2.{ext}")
print("wrote trigeff_M125_%s_v2.png/pdf" % DEN)
