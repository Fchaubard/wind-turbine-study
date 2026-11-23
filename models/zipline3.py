"""Extends the Zipline sail-train search past the edge of the first grid: longer tracks, taller sails, more sails, more generators."""
import itertools, json
import numpy as np
import zipline2 as Z
R = []; rej = 0
for L, h, c, dl, n in itertools.product((90, 130, 180, 250), (7, 9, 12), (1.5, 2, 3), (15, 20), (4, 8, 12, 16, 24)):
    if L - (n - 1) * 2.5 * c < 15: continue
    st = Z.structure(L, h, c, n)
    if not st: rej += 1; continue
    tb = Z.table(L, h, c, dl, n); zc = 1.5 + h / 2; az = max(range(0, 180, 20), key=lambda a: Z.energy(tb, zc, a, 1e6))
    for ng in (2, 3, 5, 8):
        cap, wear, life = Z.cost(L, h, c, ng, st, n); W = Z.energy(tb, zc, az, 1200 * ng)
        if W > 1: R.append(dict(L=L, h=h, c=c, delta=dl, n=n, ng=ng, az=az, W=W, cap=cap, life=life, usd=life / (W * 8.766 * 20 / 1000), usd13=life / (Z.energy(tb, zc, az, 1200 * ng, 1.3) * 8.766 * 20 / 1000), S=n * h * c, A=L * h, **st))
R.sort(key=lambda r: r["usd"]); json.dump(R[:30], open("out/zipline_ext.json", "w"), indent=1, default=float)
print("no structure found for", rej, "geometries;", len(R), "designs")
seen = set()
for r in R:
    if r["L"] in seen: continue
    seen.add(r["L"]); print(f"L {r['L']} m: {r['n']} sails {r['h']}×{r['c']} m, {r['S']:.0f} m² sail, {r['A']} m² swept, {r['ng']} gen, {r['W']:.0f} W, ${r['cap']:,.0f}, ${r['usd']:.0f}/MWh (1.3× ${r['usd13']:.0f}) | {r['wire']} wire, {r['pipe']} poles, {r['H']:.0f} m, SF {r['sf_wire17']:.2f}/{r['sf_pole17']:.2f}")
