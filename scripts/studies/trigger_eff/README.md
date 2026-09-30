# HLT efficiency for H→γ*γ→eeγ signal (UL18 MC)

Runs on cmslpc inside `cmsenv` of `CMSSW_15_0_20`. The plotters use `../cmsplot.py` (mplhep CMS style,
Okabe-Ito palette). Every script writes its JSON/PNG/PDF into the current directory, so run it from a
scratch directory.

Inputs are the signal nano in `/store/user/cromerom/nanoDalitz_v3` (all six production modes, M125).
Each producer takes about 3 min with 8 threads and writes a JSON. The plotters read the JSON back.

| producer | measures | plotter |
|---|---|---|
| `trigeff.py [M125]` | efficiency vs generated m_γ* and ΔR(e,e); two denominators (`genAcc`, `recoMatch`) | `plot_trigeff_mpl.py trigeff_M125.json recoMatch` |
| `trigeff_reco.py` | the same vs reconstructed quantities (di-GSF-track mass/ΔR for merged, di-electron for resolved) | `plot_trigeff_mpl.py trigeff_reco_M125.json reco` |
| `trigeff_ratio.py` | generated-binned (full sample) vs reconstructed-binned histograms, plus resolved/merged counts per bin | `plot_ratio_mpl.py`, `plot_combined_mpl.py` |
| `trigeff_bycat.py` | efficiency split by reconstruction category (merged 2-GSF / 1-GSF / resolved) | `plot_bycat_mpl.py [OR\|Dipho30_22\|Dipho30_18]` |
| `leg_decomp2.py` | Diphoton30_22 split into the R9Id leg, the IsoCaloId leg and the Mass90 filter, using TrigObj filter bits 14/15 | `plot_decomp_mpl.py` |
| `reco_compose.py` | category composition of the reconstructed-ΔR bins (prints a table) | — |

The OR is `Diphoton30_22_..._Mass90 || Diphoton30_18_..._NoPixelVeto_Mass55`. DiEle27 is not included.
In UL18 nano, only the ET30 photon filter bits (14 = R9Id, 15 = IsoCaloId) are filled. The ET22
unseeded bits (16/17) are never set.
