"""Zipline sail train with gravity: poles are raised by the real vertical droop of cable plus sails, pretension is searched, and pole and wire are re-sized for that tension."""
import itertools, json, math
import numpy as np
import zipline2 as Z
KG = {"1/4": .22, "5/16": .35, "3/8": .5, "1/2": .9, "5/8": 1.4}
def structure(L, h, c, n):
    S = n * h * c; N17 = .5 * Z.RHO * 289 * S * 1.3; N12 = .5 * Z.RHO * 144 * S * 1.3 * 1.2; sail_w = (8 * n + .7 * S) * Z.G / 2; best = None
    for wn, (Ac, F, wc) in Z.WIRE.items():
        for fr in (.1, .15, .2, .25):
            T0 = fr * F; s17, T17 = Z.sag(N17 / 2, Ac, T0); s12, T12 = Z.sag(N12 / 2, Ac, T0)
            if F / T17 < 1.25 or F / T12 < 2 or s17 > .1: continue
            droop = sail_w * L / (4 * T0) + KG[wn] * Z.G * L * L / (8 * T0); H = 2 + h + droop
            if droop > .08 * L: continue
            for pn, (o, w, pc) in Z.PIPE.items():
                i = o - 2 * w; Ap, Ip = math.pi / 4 * (o*o - i*i), math.pi / 64 * (o**4 - i**4); C17 = 4 * T17 + Ap * 7850 * H * Z.G; Cap = min(math.pi**2 * Z.E * Ip / H**2, 250e6 * Ap)
                if Cap / C17 < 1.25 or Cap / (C17 * T12 / T17) < 2: continue
                gl = H / math.sin(math.radians(45)); wire = 2 * L * wc + 8 * gl * wc; steel = 2 * H * pc * 1.15; d = dict(wire=wn, pipe=pn, H=H, droop=droop, pre=fr, T17=T17, sag17=s17, sf_wire17=F / T17, sf_wire12=F / T12, sf_pole17=Cap / C17, wire_cost=wire, steel=steel, anchors=6 * 250)
                if best is None or steel * 1.15 + wire < best["steel"] * 1.15 + best["wire_cost"]: best = d
                break
    return best
R = []; rej = 0
for L, h, c, dl, n in itertools.product((90, 130), (12, 15, 18), (1, 1.5, 2), (15, 20), (2, 4, 6, 8)):
    if L - (n - 1) * 2.5 * c < 12: continue
    st = structure(L, h, c, n)
    if not st: rej += 1; continue
    tb = Z.table(L, h, c, dl, n); zc = st["H"] - st["droop"] - h / 2; az = max(range(0, 180, 20), key=lambda a: Z.energy(tb, zc, a, 1e6))
    for ng in (1, 2, 3, 5, 8):
        cap, wear, life = Z.cost(L, h, c, ng, st, n); W = Z.energy(tb, zc, az, 1200 * ng)
        if W > 1: R.append(dict(L=L, h=h, c=c, delta=dl, n=n, ng=ng, az=az, W=W, cap=cap, life=life, usd=life / (W * 8.766 * 20 / 1000), usd13=life / (Z.energy(tb, zc, az, 1200 * ng, 1.3) * 8.766 * 20 / 1000), S=n * h * c, A=L * h, **st))
R.sort(key=lambda r: r["usd"]); json.dump(R[:30], open("out/zipline_tall_check.json", "w"), indent=1, default=float)
print("no structure for", rej, "geometries;", len(R), "designs"); seen = set()
for r in R:
    if r["L"] in seen: continue
    seen.add(r["L"]); print(f"L {r['L']} m: {r['n']} sails {r['h']}×{r['c']} m, {r['S']:.0f} m² sail, {r['ng']} gen, {r['W']:.0f} W, ${r['cap']:,.0f}, ${r['usd']:.0f}/MWh (1.3× ${r['usd13']:.0f}) | {r['wire']} wire pre {r['pre']:.2f}, {r['pipe']} poles {r['H']:.1f} m, droop {r['droop']:.1f} m, SF {r['sf_wire17']:.2f}/{r['sf_pole17']:.2f}")
