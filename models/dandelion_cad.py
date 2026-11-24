"""Runs the Dandelion full frame FEA, modal and clearance check on larger rotors, without the earlier self-imposed 10 t pad cap. Usage: dandelion_big.py D hub"""
"""Final check of the Dandelion that fits the real limits (pad <= 10 t, blade tips >= 3 m up): full frame FEA at 12 wind directions, tower vs 1P/3P, swept clearance, CAD. Energy is cut 5% for downwind tower shadow."""
import json, math, io, contextlib, warnings, sys, os
import cadquery as cq
import numpy as np, scipy.linalg as SL
with contextlib.redirect_stdout(io.StringIO()):
    import sail_fea as F
warnings.filterwarnings("ignore")
rows = json.load(open("out/dandelion4.json")); TD, TH = int(sys.argv[1]), float(sys.argv[2]); P = min((x for x in rows if x["use"] == "electricity" and x["D"] == TD and x["hub"] == TH and x["ng"] == int(sys.argv[3])), key=lambda x: x["usd"]); H = P
G, RHO, FY, E = 9.81, 1.18, 230e6, 200e9; D, HUB, R = P["D"], P["hub"], P["D"] / 2; AZ = HUB - .25; FOOT = 2.0; NBR = P["br"]; LEG = {"73 mm post tube": (.073, .0012), "2-1/2 in Sch 40": (.073, .00516), "3 in Sch 40": (.0889, .00549)}[P["leg"]]; A = math.pi * R * R; ROT = P["mass"] + 40; LAM = 5.5; STOP = math.radians(3); CONE = math.radians(max(P["cone"], 6))
feet = [np.array([FOOT * math.cos(a), FOOT * math.sin(a), 0.]) for a in np.radians((90, 210, 330))]; apex = np.array([0, 0, AZ])
def clear(o):
    best = 9.
    for s in np.linspace(.5, R, 30):
        x = o + s * math.sin(STOP) - .25 * ((1.1 + (.25 - 1.1) * s / R) * R / 6); rho = s * math.cos(STOP)
        for y in np.radians(np.arange(0, 360, 6)):
            n = np.array([math.cos(y), math.sin(y), 0])
            for f in feet:
                p = f + np.linspace(0, 1, 80)[:, None] * (apex - f); r = p - [0, 0, HUB]; a = r @ n; q = np.linalg.norm(r - a[:, None] * n, axis=1); best = min(best, float(np.hypot(a - x, q - rho).min()))
    return best - LEG[0] / 2
OV = .5
while clear(OV) < .30: OV += .05
OV = round(OV, 2)
def run(head):
    F.SEC.update(leg=F.tube_props(*LEG), head=F.tube_props(*head)); b = F.tube_props(.0334, .0034); F.SEC["brace"] = dict(b, I_real=b["I"], I=b["I"] * .01, J=b["J"] * .01); res = []
    Om = LAM * P["Vr"] / R; Irot = ROT * R * R / 4
    for name, v, T, mom in (("8 m/s working", 8, P["Tmax"] * .8, 1), ("Peak governed thrust", 12, P["Tmax"], 1), ("17 m/s, ALL safeties failed", 17, P["Tjam"], 1), ("25 m/s governed", 25, P["Tmax"], 0), ("45 m/s, folded, parked", 45, .5 * RHO * 45**2 * 1.2 * 2.6, 0)):
        sf = 9e9; wh = ""; pull = 0
        for yd in range(0, 360, 30):
            N, B = [], []
            def nd(p): N.append(np.array(p, float)); return len(N) - 1
            ap = nd(apex); fn = []; zs = [AZ * (k + 1) / (NBR + 1) for k in range(NBR)]; rg = {z: [] for z in zs}
            for f in feet:
                i = nd(f); fn.append(i); pv = i
                for z in zs: q = nd(f + (apex - f) * z / AZ); rg[z].append(q); B.append((pv, q, "leg", "leg")); pv = q
                B.append((pv, ap, "leg", "leg"))
            for r in rg.values():
                for i, j in ((0, 1), (1, 2), (2, 0)): B.append((r[i], r[j], "brace", "brace"))
            n = np.array([math.cos(math.radians(yd)), math.sin(math.radians(yd)), 0]); top = nd([0, 0, HUB]); B.append((ap, top, "head", "yaw post")); h = nd(N[top] + n * OV); B.append((top, h, "head", "head beam"))
            Fv = np.zeros(len(N) * 6); q = .5 * RHO * v * v
            for i, j, s, g_ in B:
                L = np.linalg.norm(N[j] - N[i]); w = F.SEC[s]["A"] * 7850 * L * G / 2; Fv[6 * i + 2] -= w; Fv[6 * j + 2] -= w
                if g_ != "head beam": d = q * 1.2 * F.SEC[s]["od"] * L / 2 * n; Fv[6 * i:6 * i + 3] += d; Fv[6 * j:6 * j + 3] += d
            Fv[6 * h + 2] -= ROT * G; Fv[6 * top + 2] -= 35 * G; Fv[6 * h:6 * h + 3] += n * T
            if mom: Fv[6 * h + 3:6 * h + 6] += n * min(P["W"] / .75 / max(Om, .1) * 3, 800) + np.array([-n[1], n[0], 0]) * .25 * Irot * Om * .5
            U, _, cache, Rr = F.solve(np.array(N), B, [], {f: (0, 1, 2) for f in fn}, Fv)
            for (i, j, s, g_), (dof, Tm, kl, L) in zip(B, cache):
                fl = kl @ (Tm @ U[dof]); S = F.SEC[s]; Nx = -fl[0]; Mm = max(math.hypot(fl[4], fl[5]), math.hypot(fl[10], fl[11])); x = FY / max(abs(Nx) / S["A"] + Mm / S["S"], 1); c = max(-Nx, 0)
                if c > 1: x = min(x, math.pi**2 * E * S.get("I_real", S["I"]) / L**2 / c)
                if x < sf: sf, wh = x, g_
            pull = max(pull, max(-min(Rr[6 * f + 2] for f in fn), 0))
        res.append(dict(name=name, v=v, T=T, sf=sf, where=wh, pull_kg=pull / G))
    B2 = [e for e in B if e[3] != "head beam"]; nn = len(N) * 6; K = np.zeros((nn, nn)); Mv = np.full(nn, 1e-6)
    for i, j, s, _ in B2:
        kg, *_ = F.beam_k(N[i], N[j], F.SEC[s]); dof = np.r_[6 * i:6 * i + 6, 6 * j:6 * j + 6]; K[np.ix_(dof, dof)] += kg; m = F.SEC[s]["A"] * 7850 * np.linalg.norm(N[j] - N[i]) / 2
        for k in (i, j): Mv[6 * k:6 * k + 3] += m; Mv[6 * k + 3:6 * k + 6] += m * .005
    Mv[6 * top:6 * top + 3] += ROT + 35; Mv[6 * top + 3:6 * top + 6] += 20
    fx = sorted(6 * f + d for f in fn for d in (0, 1, 2)) + [6 * h + d for d in range(6)] + [6 * top + 5]; fr = np.setdiff1d(np.arange(nn), fx); val, vec = SL.eigh(K[np.ix_(fr, fr)] + 1e-3 * np.eye(len(fr)), np.diag(Mv[fr]), subset_by_index=[0, 11]); ix = {d: k for k, d in enumerate(fr)}
    fb = next((math.sqrt(abs(val[k])) / (2 * math.pi) for k in range(len(val)) if math.hypot(vec[ix[6 * top], k], vec[ix[6 * top + 1], k]) > .25 * np.abs(vec[:, k]).max()), 0.)
    return res, fb, Om
HEADS = {"2-1/2 in Sch 40": (.073, .00516), "3 in Sch 40": (.0889, .00549), "4 in Sch 40": (.1143, .00602), "5 in Sch 40": (.1413, .00655), "6 in Sch 40": (.1683, .00711), "8 in Sch 40": (.2191, .00818)}
LEGS = {"73 mm post tube": (.073, .0012, 545 / 3.05), "2-1/2 in Sch 40": (.073, .00516, 520), "3 in Sch 40": (.0889, .00549, 680), "4 in Sch 40": (.1143, .00602, 960), "5 in Sch 40": (.1413, .00655, 1400), "6 in Sch 40": (.1683, .00711, 1900)}; HP = {"2-1/2 in Sch 40": 520, "3 in Sch 40": 680, "4 in Sch 40": 960, "5 in Sch 40": 1400, "6 in Sch 40": 1900, "8 in Sch 40": 3050}; FX = 18.5; L0 = math.hypot(AZ, FOOT)
def steel(ln, br, hn): return 3 * L0 * LEGS[ln][2] / FX + br * 3 * 2.4 * 150 / FX + (OV + .5) * HP[hn] / FX
base = steel(P["leg"], P["br"], "2-1/2 in Sch 40"); cand = []; worst = []
for ln in LEGS:
    LEG = LEGS[ln][:2]
    for NBR in (1, 2, 3, 4):
        for hn, hd in HEADS.items():
            OV = .5
            while clear(OV) < .30: OV += .05
            OV = round(OV, 2); r_, f_, Om = run(hd); q_ = {x["name"]: x["sf"] for x in r_}; worst.append((min(q_[k] for k in q_ if "ALL" not in k), q_["17 m/s, ALL safeties failed"], round(f_, 2), round(1 * Om / (2 * math.pi), 2), ln, NBR, hn)); okf = f_ > 1.2 * 3 * Om / (2 * math.pi) or (f_ > 1.2 * Om / (2 * math.pi) and f_ < .8 * 3 * Om / (2 * math.pi))
            if min(q_[k] for k in q_ if "ALL" not in k) >= 2 and q_["17 m/s, ALL safeties failed"] >= 1.25 and okf: cand.append((steel(ln, NBR, hn), ln, NBR, hn, OV, r_, f_)); break
if not cand: print("closest:", max(worst, key=lambda w: min(w[0] / 2, w[1] / 1.25))); raise SystemExit("no tower passes")
cst, ln, NBR, hn, OV, res, fb = min(cand, key=lambda c: c[0]); LEG = LEGS[ln][:2]; dC = cst - base; print(f"cheapest passing tower: {ln}, {NBR} brace levels, head {hn}, steel ${cst:.0f} (+${dC:.0f})")
p1, p3 = Om / (2 * math.pi), 3 * Om / (2 * math.pi)
for r in res: print(f"{r['name']:30s} thrust {r['T']/1000:5.1f} kN  SF {r['sf']:.2f} at {r['where']}  foot pull {r['pull_kg']:.0f} kg")
print(f"head {hn}; overhang {OV} m; tower {fb:.2f} Hz; 1P {p1:.2f}, 3P {p3:.2f} Hz; resonance {'CLEAR' if fb > 1.2 * p3 or (fb > 1.2 * p1 and fb < .8 * p3) else 'RISK'}")
k = lambda r: r["usd"] * r["W"] * 8.766 * 20 / 1000 + dC * 1.38; W = P["W"] * .95; usd = k(P) / (W * 8.766 * 20 / 1000); Wh = H["W"] * .95; usdh = k(H) / (Wh * 8.766 * 20 / 1000); cap = P["capex"] + dC; u13 = (P["usd13"] * P["W"] / P["W"]) * (usd / (P["usd"])); print(f"final: {W:.0f} W, {W*8.766:.0f} kWh/yr, ${cap:,.0f}, ${usd:.0f}/MWh electric (1.3x ${u13:.0f}); hot water {Wh:.0f} W ${usdh:.0f}/MWh")
json.dump(dict(pick=P, heat=H, cases=res, tower_hz=fb, p1=p1, p3=p3, overhang=OV, head=hn, W=W, usd=usd, capex=cap, leg=ln, nbr=NBR, usd13=u13, heat_W=Wh, heat_usd=usdh), open(f"out/dandelion_fin_{TD}_{int(TH)}_{sys.argv[3]}.json", "w"), indent=1, default=float)
os.makedirs('out/cad5', exist_ok=True)
V = cq.Vector; parts = []
def tube(a, b, od, idd=0.):
    a, b = V(*map(float, a)), V(*map(float, b)); d = b - a; s = cq.Solid.makeCylinder(od / 2, d.Length, a, d); return s.cut(cq.Solid.makeCylinder(idd / 2, d.Length, a, d)) if idd else s
def add(n, s, c): parts.append((n, s, c))
add("pad", cq.Solid.makeBox(4.0, 4.0, .70, V(-2.0, -2.0, -.71)), "#b9b5aa")
for f in feet: add("leg", tube(f, apex, LEG[0], LEG[0] - 2 * LEG[1]), "#6b7078")
for k in range(NBR):
    z = AZ * (k + 1) / (NBR + 1); pts = [f + (apex - f) * z / AZ for f in feet]
    for a, b in ((0, 1), (1, 2), (2, 0)): add("brace", tube(pts[a], pts[b], .0334, .0266), "#8a8f96")
hb = np.array([OV, 0, HUB]); add("yaw", tube(apex, apex + [0, 0, .25], HEADS[hn][0]), "#d85a30"); add("head", tube([0, 0, HUB], hb, HEADS[hn][0]), "#22252a"); add("generator", tube(hb - [.42, 0, .32], hb - [.24, 0, .32], .30), "#1d9e75"); add("hub", tube(hb, hb + [.06, 0, 0], .62), "#3a3d42")
def foil(tc=.11, n=16):
    x = (1 - np.cos(np.linspace(0, math.pi, n))) / 2; yt = 5 * tc * (.2969 * np.sqrt(x) - .126 * x - .3516 * x**2 + .2843 * x**3 - .1036 * x**4); yc = .05 * np.sin(math.pi * x); return np.vstack([np.column_stack([x, yc + yt])[::-1], np.column_stack([x, yc - yt])[1:-1]])
for i in range(3):
    a = 2 * math.pi * i / 3 + math.pi / 2; dr = np.array([math.sin(CONE), math.cos(CONE) * math.cos(a), math.cos(CONE) * math.sin(a)]); tg = np.array([0, -math.sin(a), math.cos(a)]); ax = np.cross(dr, tg); W_ = []
    for s in np.linspace(.45, R, 8):
        c = (1.1 + (.25 - 1.1) * (s - .45) / (R - .45)) * R / 6; th = math.radians(18 - 20 * (s - .45) / (R - .45)); p = foil() - [.3, 0]; pts = [hb + [.03, 0, 0] + dr * s + tg * c * (u * math.cos(th) - v * math.sin(th)) + ax * c * (u * math.sin(th) + v * math.cos(th)) for u, v in p]; W_.append(cq.Wire.assembleEdges([cq.Edge.makeSpline([V(*q) for q in pts] + [V(*pts[0])])]))
    add("blade", cq.Solid.makeLoft(W_), "#e8e3d3"); add("hinge", tube(hb + [.03, 0, 0] + dr * .28, hb + [.03, 0, 0] + dr * .48, .10), "#d85a30")
asm = cq.Assembly(name="dandelion")
for k, (n, s, c) in enumerate(parts): asm.add(s, name=f"{n}_{k}", color=cq.Color(*[int(c[i:i + 2], 16) / 255 for i in (1, 3, 5)]))
asm.export("out/cad5/dandelion.step"); cq.exporters.export(cq.Compound.makeCompound([s for n, s, _ in parts if n != "pad"]), "out/cad5/dandelion.stl", tolerance=.008, angularTolerance=.3); print(len(parts), "solids, all valid:", all(s.isValid() for _, s, _ in parts))
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
fig = plt.figure(figsize=(6, 7), dpi=170); ax = fig.add_subplot(111, projection="3d")
for _, s, c in parts:
    vs, tr = s.tessellate(.015, .5); v = np.array([[q.x, q.y, q.z] for q in vs]); ax.add_collection3d(Poly3DCollection(v[np.array(tr)], facecolor=c, edgecolor="#8f8a7a" if c == "#e8e3d3" else "none", linewidth=.08, alpha=.97))
ax.set_xlim(-8.5, 8.5); ax.set_ylim(-8.5, 8.5); ax.set_zlim(-.8, HUB + 8.5); ax.set_box_aspect((17, 17, HUB + 9.3)); ax.view_init(12, -55); ax.set_axis_off(); fig.subplots_adjust(0, 0, 1, 1); fig.savefig("out/cad5/iso.png"); plt.close(fig)
