"""Why Diphoton30_22 loses efficiency: R9Id branch vs IsoCaloId branch vs the Mass90 filter."""
import json, numpy as np
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from cmsplot import *

d = json.load(open("leg_decomp.json"))
BINS = [(0,1),(1,2),(2,4),(4,6),(6,10),(10,15),(15,20),(20,30),(30,40),(40,50),(50,60)]
EDGES = [b[0] for b in BINS] + [BINS[-1][1]]

def eff(num, den="N"):
    y, e = [], []
    for lo, _ in BINS:
        r = d[str(lo)]; N = r[den]
        p = r[num] / N if N > 0 else 0.0
        y.append(p); e.append(np.sqrt(max(p * (1 - p), 1e-9) / max(N, 1)))
    return np.array(y), np.array(e)

fig, (a1, a2) = plt.subplots(1, 2, figsize=(15, 6.2))

for num, label, col, mk in [
    ("ee_Iso", "IsoCaloId: hltEG30LIso60CaloId15b35eHE12R9Id50b80e", BLUE, "s"),
    ("ee_R9",  "R9Id: hltEG30LR9Id85b90eHE12R9Id50b80e", VERM, "o"),
    ("ee_any", r"R9Id $\cup$ IsoCaloId (leg requirement)", GREY, "D")]:
    y, e = eff(num); band(a1, EDGES, y, e, e, color=col, marker=mk, label=label)
style(a1, r"generated $m_{\gamma^{*}}$ [GeV]", r"Leg filter efficiency, $e^{\pm}$ candidate", xlim=(0, 60))
cms(a1)
a1.legend(loc="lower right", frameon=True, framealpha=0.95, edgecolor="0.8", fontsize=10.5,
          title=r"$p_{T}^{\mathrm{leg}}>35$ GeV (offline)", title_fontsize=11)

for num, den, label, col, mk in [
    ("legsOK", "N", r"both EG legs satisfy R9Id $\cup$ IsoCaloId", GREEN, "^"),
    ("massGivenLegs", "legsOK", r"Mass90 filter: $m_{\mathrm{EG,EG}}>90$ GeV, conditional on legs", PURPLE, "v"),
    ("pass", "N", "HLT_Diphoton30_22_R9Id_OR_IsoCaloId_AND_HE_R9Id_Mass90", GREY, "o")]:
    y, e = eff(num, den); band(a2, EDGES, y, e, e, color=col, marker=mk, label=label)
style(a2, r"generated $m_{\gamma^{*}}$ [GeV]", "Efficiency", xlim=(0, 60))
cms(a2)
a2.legend(loc="lower right", frameon=True, framealpha=0.95, edgecolor="0.8", fontsize=10.5,
          title=r"$p_{T}^{\mathrm{leg}}>35$ GeV (offline)", title_fontsize=11)

fig.tight_layout()
for ext in ("png", "pdf"): fig.savefig(f"diphoton30_22_decomposition_v2.{ext}")
print("wrote diphoton30_22_decomposition_v2.png/pdf")
