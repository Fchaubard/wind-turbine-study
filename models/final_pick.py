"""Applies cheapest sourcing and priced pad concrete to the designs that passed the full frame, buckling and vibration checks, on both wind datasets."""
import json, math, glob
import numpy as np
src_ = open("blimp.py").read(); exec(src_[:src_.index("GAS = {")])
def wr(p, s): v = wind(p["hub"], s) * math.cos(math.radians(10)); v = np.nan_to_num(v); return float(np.mean(np.minimum(k * .5 * RHO * math.pi * p["D"]**2 / 4 * v**3, 1200 * p["ng"]) * (v >= 2.5))) * .95
R = []
for f in sorted(glob.glob("out/dandelion_fin_*.json")):
    d = json.load(open(f)); p = d["pick"]; steel = p["tower"] + d["capex"] - p["capex"]; fab = (p["wear"] - 70 - .02 * p["tower"]) / 1.6; L0 = d["usd"] * d["W"] * 8.766 * 20 / 1000; conc = 110 * max(p["pad_t"] - 10, 0); ctl = -295 * p["ng"] + 120; dc = conc + ctl - .35 * steel - fab * 5.5 * 1.15; dl = conc + ctl * 1.3 - .35 * steel * 1.2 + (-fab * 5.5 * 1.15 + fab * 1.5 * 1.15 * 3 - fab * 7 * .8); L = L0 + dl; wn = d["W"]; we = wn * wr(p, "ERA5") / wr(p, "NASA"); R.append(dict(file=f, D=p["D"], hub=p["hub"], ng=p["ng"], spar=p["spar"], leg=d["leg"], braces=d["nbr"], head=d["head"], overhang=d["overhang"], W=wn, W_weak=we, build=d["capex"] + dc, life=L, usd=L / (wn * 8.766 * 20 / 1000), usd_weak=L / (we * 8.766 * 20 / 1000), score=math.sqrt(L / (wn * 8.766 * 20 / 1000) * L / (we * 8.766 * 20 / 1000)), pad_t=p["pad_t"], steel=steel * .65, fabric_m2=fab, minSF=min(c["sf"] for c in d["cases"]), foot_pull=max(c["pull_kg"] for c in d["cases"]), tower_hz=d["tower_hz"], p1=d["p1"], p3=d["p3"], concrete=conc))
R.sort(key=lambda r: r["score"]); json.dump(R, open("out/final_pick.json", "w"), indent=1, default=float)
for r in R: print(f"{r['D']} m, hub {r['hub']:.0f}, {r['ng']} gens, {r['leg']} legs, {r['head']} head | {r['W']:.0f}/{r['W_weak']:.0f} W | build ${r['build']:,.0f} | ${r['usd']:.0f} / ${r['usd_weak']:.0f}/MWh | pad {r['pad_t']:.1f} t | SF {r['minSF']:.2f} | tower {r['tower_hz']:.1f} Hz vs 3P {r['p3']:.2f}")
