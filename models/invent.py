"""Six invented machines, simulated in 3 years of hourly wind (speed + direction) with the same field factor (.75), generator and 20-year accounting as the v3 rotor ($134/MWh).
SAIL LADDER: sails run up and down a vertical rope loop, like a bucket elevator, on a frame that turns on a ring rail on the pad. DELTA LOOP: sails run round a rope triangle on 3 posts.
BEACH LINE: same on a straight loop, fixed facing. TACKING SHUTTLE: one big sail shuttles on a cable. RIDGE DRUM: cross-flow drum along the roof ridge (free tower, speed-up). NODDING SAIL: rocking wing on the pad."""
import json, math, io, contextlib
import numpy as np
with contextlib.redirect_stdout(io.StringIO()):
    import zoo as Z
import loop_sim as L
RHO, FX = 1.18, 18.5; WS, WD = Z.WS, Z.WD; DIRS = np.arange(15, 360, 30); ELEC = 733.; CRR = .03; FIELD = .75
def best_cp(kind, size, sig, th_list, depth=None):
    g = L.polygon(kind, size, 240); out = None
    for lam in (1.0, 1.25, 1.5, 1.75, 2.0, 2.5):
        for CL in (.7, 1.0):
            c = [L.cp_dir(g, sig, lam, t, CL=CL) for t in th_list]; cp = np.array([max(a - CRR * b * lam, 0) for a, b in c]); ct = np.array([b for _, b in c]); w = np.ones(len(cp))
            if out is None or cp.mean() > out[0].mean(): out = (cp, ct, lam, CL)
    return out
def energy(cp_by_dir, width_by_dir, H, z, ngen, vf=9.0, s=1.0, eta=.92 * .84 * .95, drag=8.0, frac=1.0):
    v = WS * (z / 10) ** .14 * s; i = ((WD % 360) / 30).astype(int) % 12; cp = cp_by_dir[i] * FIELD * frac; A = width_by_dir[i] * H; ve = np.minimum(v, vf)
    P = np.minimum(np.maximum(cp * .5 * RHO * ve**3 * A - drag * ve, 0) * eta, 1200. * ngen) * (v <= 25); return float(P.mean()) * .97
def u(capex, wear, W, y=20, rebuild=0.): return (capex + wear * (y - 1) + rebuild + .3 * ELEC) / (W * 8.766 * y / 1000) if W > 1 else 1e7
def sails(area, n, span):  return area * 7.0 + n * (span * 6.0 + 2 * 18.0)          # PVC-coated tarp $7/m2, spar $6/m, 2 trolleys $18
def wear_s(area, n): return area * 1.6 + n * 3.0 + 55                               # sail life about 4-5 years, trolley wear, rope replacement
R = []
# 1 SAIL LADDER: loop height Hl, sail span b. Frame on a turntable always faces the wind.
for Hl in (8, 10, 12, 14, 16):
    for b in (4, 5, 6, 8, 10):
        for sig in (.1, .15, .2, .3):
            cp, ct, lam, CL = best_cp("line", float(Hl), sig, [math.pi / 2]); Cp = float(cp[0]) * .92; A = Hl * b; z = 2.5 + Hl / 2
            T = float(ct[0]) * .5 * RHO * 144 * A; M = T * (2.5 + Hl / 2); steel = 520 + 1368 * M / 132e3; n = max(2, round(sig * 2 * Hl / 1.0)); sa = n * b * 1.0; ropes = 2 * 2.2 * Hl * 1.6 + 260
            for ng in (1, 2):
                cap = steel + 380 + sails(sa, n, b) + ropes + 240 + ELEC * ng + 700; W = energy(np.full(12, Cp), np.full(12, float(b)), Hl, z, ng)
                R.append(dict(name="Sail Ladder", size=f"{Hl}×{b} m", A=A, W=W, capex=cap, usd=u(cap, wear_s(sa, n) + .02 * steel, W), cp=Cp, lam=lam, sig=sig, T12=T, ng=ng, Hl=Hl, b=b, n=n, z=z))
# 2 DELTA LOOP and 3 BEACH LINE
for kind, name in (("triangle", "Delta Loop"), ("line", "Beach Line")):
    for S in (12, 16, 20, 25, 30):
        for H in (3, 4, 5, 6):
            for sig in (.1, .15, .2):
                ths = np.radians(DIRS) if kind == "triangle" else np.radians(DIRS - 315 + 90); cp, ct, lam, CL = best_cp(kind, float(S), sig, list(ths))
                g = L.polygon(kind, float(S), 240)[0]; wid = np.array([np.ptp(g @ np.array([-math.sin(t), math.cos(t)])) for t in ths]); per = 3 * S if kind == "triangle" else 2 * S + 3
                z = 2.5 + H / 2; w_n = float(ct.max()) * .5 * RHO * 144 * H; Tc = w_n / 2 * 30 * S / 8; dia = max(.0064, math.sqrt(3 * Tc / (.33 * 1570e6 * math.pi / 4)) ); cabl = 2 * per * 2.5 * (dia / .0064)**2 * 1.5
                np_ = 3 if kind == "triangle" else 4; Fh = 1.73 * Tc * 2; steel = np_ * (H + 3.5) * 37 * max(1, (Fh / 30e3) ** .5) + np_ * 2 * (H + 3.5) * 1.6 * 2 + np_ * 3 * 45; n = max(3, round(sig * per)); sa = n * H
                for ng in (1, 2):
                    cap = steel + cabl + sails(sa, n, H) + per * 1.6 + 240 + ELEC * ng + 450; W = energy(cp, wid, H, z, ng)
                    R.append(dict(name=name, size=f"{S} m × {H} m", A=S * H, W=W, capex=cap, usd=u(cap, wear_s(sa, n) + .02 * steel + .04 * cabl, W), cp=float(cp.mean()), lam=lam, sig=sig, T12=w_n * S, ng=ng))
# 4 TACKING SHUTTLE: one sail, reversal loss 25%
for S in (15, 25, 35):
    for H in (4, 6, 8):
        sig = 2.0 / (2 * S); ths = np.radians(DIRS - 315 + 90); cp, ct, lam, CL = best_cp("line", float(S), max(sig, .03), list(ths)); wid = np.abs(np.cos(ths - math.pi / 2)) * S + 1.5; steel = 2 * (H + 3.5) * 45 + 300; cap = steel + S * 8 + H * 2 * 12 + 240 + ELEC + 550; W = energy(cp, wid, H, 2.5 + H / 2, 1, frac=.75)
        R.append(dict(name="Tacking Shuttle", size=f"{S} m × {H} m", A=S * H, W=W, capex=cap, usd=u(cap, 70 + H * 2 * 1.6 + .02 * steel, W), cp=float(cp.mean()) * .75, ng=1))
# 5 RIDGE DRUM on the roof: assumes a free 7 m ridge and 1.25x speed-up, wind counted only across the ridge
for Lr in (6, 10, 14):
    for D in (1.0, 1.5, 2.0):
        c = np.abs(np.cos(np.radians(DIRS - 315))); cp = np.full(12, .20) * c**3; A = Lr * D; W = energy(cp, np.full(12, float(D)), Lr, 7.0, 1, s=1.25, eta=.95 * .84 * .95); cap = A * 34 + 480 + 240 + ELEC
        R.append(dict(name="Ridge Drum", size=f"{Lr} m × {D} m", A=A, W=W, capex=cap, usd=u(cap, 2.0 * A + 35, W), cp=.20, ng=1))
# 6 NODDING SAIL
for b in (6, 10):
    for sw in (5, 8):
        A = b * sw; W = energy(np.full(12, .14), np.full(12, float(b)), sw, 7, 1, eta=.70 * .84 * .95); cap = 900 + 34 * A * .6 + ELEC + 620; R.append(dict(name="Nodding Sail", size=f"{b} × {sw} m", A=A, W=W, capex=cap, usd=u(cap, 1.6 * A + 80, W), cp=.14, ng=1))
best = {}
for r in R:
    if r["name"] not in best or r["usd"] < best[r["name"]]["usd"]: best[r["name"]] = r
L_ = sorted(best.values(), key=lambda r: r["usd"]); print(len(R), "designs")
for r in L_: print(f"{r['name']:16s} {r['size']:12s} area {r['A']:5.0f} m²  Cp {r['cp']:.2f}  {r['W']:5.0f} W  ${r['capex']:6,.0f}  ${r['usd']:5.0f}/MWh  gens {r.get('ng')} {('thrust@12 ' + format(r['T12']/1000,'.1f') + ' kN') if 'T12' in r else ''}")
print("reference v3 rotor: 78.5 m², 400 W, $5,427, $134/MWh")
json.dump(dict(best=L_, n=len(R)), open("out/invent.json", "w"), indent=1, default=float)
