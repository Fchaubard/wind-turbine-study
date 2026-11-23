"""Dandelion hill-siting sweep: every local hill in the fine elevation grid, hub heights 7-14 m (speed-up is strongest near the ground), 1 to 12 machines sharing one wire to the nearest shore.
Costs: the $5,820 lifetime Dandelion, with its 40% structural share scaled by hub height and hill-wind load. Wire $2.50/m plus $500 access. Speed-up shown at 25/50/100% of theory."""
import json, math
import numpy as np
src = open("ridge.py").read(); exec(src[:src.index("A, B = (20.782")])
dd = json.load(open("out/dandelion_final.json")); AD = math.pi * 25; base = W0 * math.cos(math.radians(10))
lo_k, hi_k = .01, .6
for _ in range(50):
    k = .5 * (lo_k + hi_k); w = float(np.mean(np.minimum(k * AD * .5 * Z.RHO * base**3, 1200) * (base >= 2.5)))
    if w < dd["W"]: lo_k = k
    else: hi_k = k
sea = np.argwhere(FE <= 0); P = []
for r in range(2, FE.shape[0] - 2):
    for c in range(2, FE.shape[1] - 2):
        if FE[r, c] >= 12 and FE[r, c] == FE[r-2:r+3, c-2:c+3].max():
            d = float(np.min(np.hypot((sea[:, 0] - r) * 111., (sea[:, 1] - c) * 104.))); P.append((float(FE[r, c]), float(FL[r]), float(FO[c]), d))
def evalu(H, run, f, u, hub):
    s = speed(H, hub, f); v = base * (hub / 10)**.14 * s; w1 = float(np.mean(np.minimum(k * AD * .5 * Z.RHO * v**3, 1200) * (v >= 2.5))); sm = float(np.percentile(s, 99)); struct = 1324 * ((hub / 10)**1.5 * sm * sm - 1); wire = max(run, 200) * 2.5 + 500; W = u * w1 * .95; return dict(usd=(u * (5820 + struct) + wire) / (W * 8.766 * 20 / 1000), W=W, cap=u * (3309 + struct) + wire, wire=wire, hub=hub, units=u)
R = []
for e, la, lo, d in P:
    H = hill(la, lo)
    for u in (1, 2, 4, 12):
        b = min((evalu(H, d, .5, u, hb) for hb in (7, 8, 10, 14)), key=lambda x: x["usd"]); R.append(dict(elev=e, lat=la, lon=lo, shore_m=d, ds=float(H[:, 0].mean()), low=evalu(H, d, .25, u, b["hub"])["usd"], high=evalu(H, d, 1., u, b["hub"])["usd"], **b))
out = {}
for u in (1, 2, 4, 12):
    x = sorted((r for r in R if r["units"] == u), key=lambda r: r["usd"]); out[u] = x[0]; r = x[0]; print(f"{u} machines: best hill {r['elev']:.0f} m, {r['shore_m']:.0f} m from shore, hub {r['hub']} m: ${r['usd']:.0f}/MWh (range ${r['high']:.0f}-${r['low']:.0f}), {r['W']:.0f} W, build ${r['cap']:,.0f}, wire ${r['wire']:,.0f}")
json.dump(dict(best=out, n_hills=len(P)), open("out/ridge2.json", "w"), indent=1, default=float); print(len(P), "hills checked")
