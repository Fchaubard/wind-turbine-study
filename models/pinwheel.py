"""GIANT PINWHEEL on the ocean pad: triangular fabric vanes (a cut-and-folded square), constant local solidity, constant fold pitch. BEM with Prandtl tip loss and Buhl high-induction correction, curved-plate polar.
Costed against the Dandelion's own breakdown: same electronics and common parts, tower scaled with the 17 m/s all-safeties-failed thrust, pad weight scaled likewise. Fabric is lowered for hurricanes."""
import json, math, itertools, io, contextlib
import numpy as np
with contextlib.redirect_stdout(io.StringIO()):
    import zoo as Z
RHO = 1.18; d = json.load(open("out/dandelion_final.json")); p = d["pick"]; WS = Z.WS * math.cos(math.radians(10)); LIFE_D = d["usd"] * d["W"] * 8.766 * 20 / 1000
TOWER_D = p["tower"] + d["capex"] - p["capex"]; COMMON = d["capex"] - p["blade"] - TOWER_D; FAB_D = (p["wear"] - 70 - .02 * p["tower"]) / 1.6; RESID = LIFE_D - (d["capex"] + p["wear"] * 19 + FAB_D * 7 + 40)
def polar(a):
    x = np.degrees(a); cl = np.where(x < 12, .45 + .095 * x, np.maximum(1.59 - .012 * (x - 12), .8)); cl = np.where(x < -5, .095 * (x + 5), cl); return cl, .035 + .012 * cl * cl + np.where(x > 12, 1.5 * np.sin(np.clip(a, 0, math.pi / 2))**2 * np.minimum((x - 12) / 40, 1), 0)
RS = (np.arange(16) + .5) / 16 * .92 + .08
def bem(B, s, th, lam):
    t = math.radians(th); lr = lam * RS; a, ap = np.full(16, .25), np.full(16, .05)
    for _ in range(90):
        phi = np.arctan2(1 - a, lr * (1 + ap)); sp, cp = np.maximum(np.sin(phi), .02), np.cos(phi); cl, cd = polar(phi - t); cn, ct = cl * cp + cd * sp, cl * sp - cd * cp; F = np.maximum(2 / math.pi * np.arccos(np.clip(np.exp(-B / 2 * (1 - RS) / (RS * sp)), 0, 1)), .03)
        k = s * cn / (4 * F * sp * sp); an = k / (1 + k); CTl = s * (1 - a)**2 * cn / (sp * sp); hi = CTl > .96 * F
        an = np.where(hi, (18 * F - 20 - 3 * np.sqrt(np.maximum(CTl * (50 - 36 * F) + 12 * F * (3 * F - 4), 0))) / (36 * F - 50), an); apn = 1 / np.maximum(4 * F * sp * cp / np.maximum(s * ct, 1e-4) - 1, 1e-3) * (ct > 0); a = .7 * a + .3 * np.clip(an, 0, .95); ap = .7 * ap + .3 * np.clip(apn, 0, 1)
    phi = np.arctan2(1 - a, lr * (1 + ap)); W2 = (1 - a)**2 + (lr * (1 + ap))**2; cl, cd = polar(phi - t); ct_ = cl * np.sin(phi) - cd * np.cos(phi); cn = cl * np.cos(phi) + cd * np.sin(phi); dr = .92 / 16
    return float(np.sum(2 * s * W2 * ct_ * lam * RS * RS * dr)), float(np.sum(2 * s * W2 * cn * RS * dr))
LAMS = (.5, .75, 1, 1.25, 1.5, 2, 2.5, 3, 4); R = []
print("validation, farm-style rotor (solidity .7, pitch 35°): peak Cp", round(max(bem(12, .7, 35, l)[0] for l in LAMS), 3), "(published multiblade about 0.25-0.32)", flush=True)
for B, s, th in itertools.product((4, 6, 8), (.15, .25, .4, .6, .8), (10, 15, 20, 25, 30, 40, 50)):
    c = [bem(B, s, th, l) for l in LAMS]; cp, ct = max(c, key=lambda x: x[0]); lam = LAMS[[x[0] for x in c].index(cp)]
    if cp < .05: continue
    for D, ng in itertools.product((5, 7, 8, 10, 12, 14), (1, 2)):
        A = math.pi * D * D / 4; hub = max(10., D / 2 + 2.); v = WS * (hub / 10)**.14; eta = .84 * .95 * .95 * (.95 if lam < 2 else 1); W = float(np.mean(np.minimum(cp * .75 * .5 * RHO * v**3 * A * .95 * eta, 1200 * ng) * (v >= 2.))) * .97 * .95
        T17 = max(ct, .5) * .5 * RHO * 289 * A; tower = TOWER_D * (T17 / p["Tjam"])**.8 * (hub / 10)**1.3; fab = s * A; spar = (B / 3) * 570 * (D / 10)**2.5; rotor = fab * 8 + spar + B * D / 2 * 2; gear = 100 if lam < 2 else 0; cap = COMMON + (ng - 1) * 518 + tower + rotor + gear; wear = 1.6 * fab + 70 + .02 * tower; life = cap + wear * 19 + fab * 7 + 40 + RESID
        R.append(dict(B=B, s=s, th=th, D=D, ng=ng, hub=hub, cp=cp, ct=ct, lam=lam, W=W, cap=cap, life=life, usd=life / (W * 8.766 * 20 / 1000), tower=tower, rotor=rotor, T17=T17, pad_t=p["pad_t"] * T17 / p["Tjam"] * (hub / 10)))
R.sort(key=lambda r: r["usd"]); json.dump(dict(best=R[:20], dandelion=dict(usd=d["usd"], W=d["W"], cap=d["capex"], life=LIFE_D, common=COMMON, tower=TOWER_D)), open("out/pinwheel.json", "w"), indent=1, default=float)
print(f"Dandelion breakdown: common ${COMMON:.0f}, tower ${TOWER_D:.0f}, rotor ${p['blade']:.0f}, life ${LIFE_D:.0f}")
seen = set()
for r in R:
    if r["D"] in seen: continue
    seen.add(r["D"]); print(f"D {r['D']} m: {r['B']} vanes, solidity {r['s']}, fold {r['th']}°, TSR {r['lam']}, Cp {r['cp']:.2f}, CT {r['ct']:.2f} | {r['W']:.0f} W, ${r['cap']:,.0f}, ${r['usd']:.0f}/MWh | rotor ${r['rotor']:.0f}, tower ${r['tower']:.0f}, pad {r['pad_t']:.1f} t")
print("TRUE PINWHEEL (solidity 0.4 or more, what a folded sheet actually is):"); tp = {}
for r in R:
    if r["s"] >= .4 and r["D"] not in tp: tp[r["D"]] = r; print(f" D {r['D']} m: {r['B']} vanes, solidity {r['s']}, fold {r['th']}°, TSR {r['lam']}, Cp {r['cp']:.2f}, CT {r['ct']:.2f} | {r['W']:.0f} W, ${r['cap']:,.0f}, ${r['usd']:.0f}/MWh | pad {r['pad_t']:.1f} t")
json.dump(dict(json.load(open("out/pinwheel.json")), true_pinwheel=list(tp.values())), open("out/pinwheel.json", "w"), indent=1, default=float)
