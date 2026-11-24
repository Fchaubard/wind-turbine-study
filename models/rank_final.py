"""Ranks every structurally screened Dandelion with the cheapest sourcing and priced pad concrete, on both wind datasets. Score is the geometric mean of the two costs, so the design is not tuned to one dataset. Tip clearance at least 3 m."""
import json, math
import numpy as np
src_ = open("blimp.py").read(); exec(src_[:src_.index("GAS = {")])
def adj(r):
    fab = (r["wear"] - 70 - .02 * r["tower"]) / 1.6; dcap = 110 * max(r["pad_t"] - 10, 0) + (-295 * r["ng"] + 120) - .35 * r["tower"] - fab * 5.5 * 1.15; dlife = 110 * max(r["pad_t"] - 10, 0) + (-295 * r["ng"] + 120) * 1.3 - .35 * r["tower"] * 1.2 + (-fab * 5.5 * 1.15 + fab * 1.5 * 1.15 * 3 - fab * 7 * .8); return dcap, dlife
def wr(r, s): v = wind(r["hub"], s) * math.cos(math.radians(10)); return float(np.mean(np.minimum(k * .5 * RHO * math.pi * r["D"]**2 / 4 * v**3, 1200 * r["ng"]) * (v >= 2.5))) * .95
R = []
for r in json.load(open("out/dandelion4.json")):
    if r["hub"] - r["D"] / 2 < 3: continue
    dc, dl = adj(r); L = r["usd"] * r["W"] * 8.766 * 20 / 1000 + dl; wn = r["W"] * .95; we = wn * wr(r, "ERA5") / wr(r, "NASA"); un, ue = L / (wn * 8.766 * 20 / 1000), L / (we * 8.766 * 20 / 1000); R.append(dict(r, cap2=r["capex"] + dc, L2=L, W_n=wn, W_e=we, usd_n=un, usd_e=ue, score=math.sqrt(un * ue)))
R.sort(key=lambda r: r["score"]); seen = set(); top = []
for r in R:
    t = (r["D"], r["hub"], r["ng"])
    if t in seen: continue
    seen.add(t); top.append(r)
json.dump(top[:12], open("out/rank_final.json", "w"), indent=1, default=float)
for r in top[:10]: print(f"{r['D']} m rotor, hub {r['hub']:.0f}, {r['ng']} gens, {r['spar'][-10:]}, {r['leg']} | {r['W_n']:.0f}/{r['W_e']:.0f} W | ${r['cap2']:,.0f} | ${r['usd_n']:.0f} / ${r['usd_e']:.0f}/MWh | score {r['score']:.0f} | pad {r['pad_t']:.1f} t")
