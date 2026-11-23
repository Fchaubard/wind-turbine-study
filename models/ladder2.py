"""Sail Ladder, real sizing. A 4-leg lattice mast stands INSIDE the rope loop (nothing may cross the sail path), on a turntable ring on the 4 x 4 m pad. Frame FEA at 12 m/s, 17 m/s with feathering failed, flagged 25 m/s and bare 45 m/s;
mast frequency vs sail-passing frequency; pad tipping; itemised cost. Criteria match the v3 rotor: SF >= 2 at 12 m/s, >= 1.25 at 17 m/s with the safety failed."""
import json, math, io, contextlib, sys
import numpy as np, scipy.linalg as SL
with contextlib.redirect_stdout(io.StringIO()):
    import zoo as Z, sail_fea as F
import loop_sim as Lp
RHO, G, FY, E, FX = 1.18, 9.81, 250e6, 200e9, 18.5; WS = Z.WS; CRR = .03; FIELD = .75; ELEC = 733.; CLR = 2.5
PIPE = {"2 in Sch 40": (.0603, .00391, 300), "2-1/2 in Sch 40": (.0730, .00516, 520), "3 in Sch 40": (.0889, .00549, 680), "4 in Sch 40": (.1143, .00602, 960)}
CPC = {}
def aero(H, d, sig):
    k = (H, d, sig)
    if k not in CPC:
        g = Lp.polygon("line", float(H), 160, depth=d); best = None
        for lam in (1.25, 1.5, 1.75, 2.0):
            for CL in (.8, 1.0):
                cp, ct = Lp.cp_dir(g, sig, lam, math.pi / 2, CL=CL, ny=24); net = max(cp - CRR * ct * lam, 0) * .92
                if best is None or net > best[0]: best = (net, ct, lam, CL)
        CPC[k] = best
    return CPC[k]
def energy(Cp, A, z, ng, s=1.0, vf=9.0):
    v = WS * (z / 10) ** .14 * s; ve = np.minimum(v, vf); P = np.minimum(np.maximum(Cp * FIELD * .5 * RHO * ve**3 * A - 8 * ve, 0) * .92 * .84 * .95, 1200. * ng) * (v <= 25); return float(P.mean()) * .97
CABLES = {"3/16 in": (11.2e-6, 13.3e3, 27), "1/4 in": (20e-6, 23.5e3, 40), "5/16 in": (31e-6, 36e3, 58)}
def mast(H, d, w, sec, T12, ct, b, top_m, cab="3/16 in"):
    F.CAB["x"] = dict(EA=100e9 * CABLES[cab][0], cap=CABLES[cab][1], name=cab)
    od, t, _ = PIPE[sec]; F.SEC["leg"] = F.tube_props(od, t); br = F.tube_props(.0483, .0037); F.SEC["brace"] = dict(br, I_real=br["I"], I=br["I"] * .02, J=br["J"] * .02)
    z0, zt = CLR, CLR + H; nb = max(3, round(zt / 1.8)); zs = np.linspace(0, zt, nb + 1); N = []; B = []
    for z in zs:
        for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1)): N.append(np.array([sx * d / 2, sy * w / 2, z]))
    N = np.array(N); Cb = []
    for k in range(nb + 1):
        q = [4 * k + i for i in range(4)]
        for i in range(4): B.append((q[i], q[(i + 1) % 4], "brace", "brace"))
        if k < nb:
            for i in range(4):
                B.append((q[i], q[i] + 4, "leg", "leg")); Cb.append((q[i], q[(i + 1) % 4] + 4, "x", f"x{k}{i}a")); Cb.append((q[(i + 1) % 4], q[i] + 4, "x", f"x{k}{i}b"))
    fixed = {i: (0, 1, 2) for i in range(4)}; res = {}
    for name, v, mode in (("12", 12, "on"), ("17", 17, "on"), ("25", 25, "flag"), ("45", 45, "bare")):
        worst = 9e9; pull = 0; tmax = 0
        for yd in (0, 20, -20, 90):
            n = np.array([math.cos(math.radians(yd)), math.sin(math.radians(yd)), 0]); q = .5 * RHO * v * v; Fv = np.zeros(len(N) * 6)
            for i, j, s, _ in B:
                L = np.linalg.norm(N[j] - N[i]); wt = F.SEC[s]["A"] * 7850 * L * G / 2; Fv[6 * i + 2] -= wt; Fv[6 * j + 2] -= wt; dr = q * 1.2 * F.SEC[s]["od"] * L / 2 * n; Fv[6 * i:6 * i + 3] += dr; Fv[6 * j:6 * j + 3] += dr
            T = ct * q * H * b if mode == "on" else q * H * b * .10 if mode == "flag" else q * .25
            T *= abs(math.cos(math.radians(yd))) if mode == "on" else 1
            idx = [k for k in range(len(N)) if N[k][2] >= z0 - .01]; fn = T / len(idx)
            for k in idx: Fv[6 * k:6 * k + 3] += fn * n; Fv[6 * k + 2] -= top_m * G / len(idx)
            U, ten, cache, Rr = F.solve(N, B, Cb, fixed, Fv); tmax = max(tmax, max(ten))
            for (i, j, s, g_), (dof, Tm, kl, L) in zip(B, cache):
                fl = kl @ (Tm @ U[dof]); S = F.SEC[s]; Nx = -fl[0]; Mm = max(math.hypot(fl[4], fl[5]), math.hypot(fl[10], fl[11])); sf = FY / max(abs(Nx) / S["A"] + Mm / S["S"], 1); c = max(-Nx, 0)
                if c > 1: sf = min(sf, math.pi**2 * E * S.get("I_real", S["I"]) / L**2 / c)
                worst = min(worst, sf)
            pull = max(pull, max(-min(Rr[6 * f + 2] for f in range(4)), 0))
        worst = min(worst, CABLES[cab][1] / 1.25 / max(tmax, 1) * 1.25); res[name] = dict(sf=worst, pull=pull / G, cable=tmax)
    nn = len(N) * 6; K = np.zeros((nn, nn)); Mv = np.full(nn, 1e-5)
    for i, j, s, _ in B:
        kg, *_ = F.beam_k(N[i], N[j], F.SEC[s]); dof = np.r_[6 * i:6 * i + 6, 6 * j:6 * j + 6]; K[np.ix_(dof, dof)] += kg; mm = F.SEC[s]["A"] * 7850 * np.linalg.norm(N[j] - N[i]) / 2
        for k in (i, j): Mv[6 * k:6 * k + 3] += mm; Mv[6 * k + 3:6 * k + 6] += mm * .003
    for i, j, _, _ in Cb:
        dv = N[j] - N[i]; Lc = np.linalg.norm(dv); uu = dv / Lc; kk = .5 * F.CAB["x"]["EA"] / Lc * np.outer(uu, uu); di, dj = np.r_[6 * i:6 * i + 3], np.r_[6 * j:6 * j + 3]; K[np.ix_(di, di)] += kk; K[np.ix_(dj, dj)] += kk; K[np.ix_(di, dj)] -= kk; K[np.ix_(dj, di)] -= kk
    idx = [k for k in range(len(N)) if N[k][2] >= z0 - .01]
    for k in idx: Mv[6 * k:6 * k + 3] += top_m / len(idx)
    fr = np.setdiff1d(np.arange(nn), [6 * f + x for f in range(4) for x in (0, 1, 2)]); val = SL.eigh(K[np.ix_(fr, fr)] + 1e-2 * np.eye(len(fr)), np.diag(Mv[fr]), eigvals_only=True, subset_by_index=[0, 8]); fs = np.sqrt(np.abs(val)) / (2 * np.pi)
    res["f"] = float(next((x for x in fs if x > .05), fs[0])); return res, nb
def cost(H, b, d, w, sec, nb, n, ng, sa, cab="3/16 in"):
    legm = 4 * (CLR + H); brm = (nb + 1) * 2 * (d + w); cbm = nb * 2 * 2 * (math.hypot(d, (CLR + H) / nb) + math.hypot(w, (CLR + H) / nb)); ncb = nb * 8; per = 2 * H + 2 * d
    I = dict(mast=legm * PIPE[sec][2] / FX, braces=brm * 150 / FX, cables=cbm * CABLES[cab][2] / FX + ncb * 2 * 22 / FX + ncb * 45 / FX, weld=(300 + nb * 45), turntable=420, sheaves=4 * (35 + 25 * d), shafts=2 * b * 14, bearings=8 * 22, ropes=2 * per * 2.2 + 90, sails=sa * 7, spars=n * b * 7, trolleys=n * 4 * 9, trim=n * 22, drive=240, electrics=ELEC * ng, anchors=170, lift=135, paint=120)
    return sum(I.values()), I
rows = []; ng_opts = (1, 2)
for H in (10, 12, 14, 16):
    for b in (8, 10, 12, 14):
        for d in (1.2, 1.6, 2.2):
            w = min(math.sqrt(max(4 * 1.8**2 - d * d, .01)), b * .55)
            for n in (3, 4, 6):
                sig = n / (2 * H + 2 * d); Cp, ct, lam, CL = aero(H, d, round(sig, 3)); sa = n * b; rotm = n * (b * 3.2 + 7) + 2 * b * 4.5 + 4 * 25 + 60
                if 2 * H / n > 9: pass
                done = False
                for sec, cab in ((a, c) for a in PIPE for c in CABLES):
                    if done: break
                    r, nb = mast(H, d, w, sec, 0, ct, b, rotm, cab)
                    fp = n * lam * 9.0 / (2 * H + 2 * d); ok = r["12"]["sf"] >= 2 and r["17"]["sf"] >= 1.25 and r["25"]["sf"] >= 1.5 and r["45"]["sf"] >= 1.0 and (r["f"] >= 1.2 * fp)
                    if not ok: continue
                    T17 = ct * .5 * RHO * 289 * H * b; zt = CLR + H / 2; pad = 1.5 * T17 * zt / (1.8 * G) / 1000
                    if pad > 10.1: continue
                    for ng in ng_opts:
                        c, I = cost(H, b, d, w, sec, nb, n, ng, sa, cab); W = energy(Cp, H * b, CLR + H / 2, ng); wear = sa * 1.6 + n * 5 + 75 + .02 * (I["mast"] + I["braces"]); rebuild = .3 * ELEC * ng
                        rows.append(dict(cab=cab, H=H, b=b, d=d, w=w, n=n, sec=sec, nb=nb, ng=ng, Cp=Cp, ct=ct, lam=lam, CL=CL, W=W, capex=c, wear=wear, usd=(c + wear * 19 + rebuild) / (W * 8.766 * 20 / 1000), usd13=(c + wear * 19 + rebuild) / (energy(Cp, H * b, CLR + H / 2, ng, 1.3) * 8.766 * 20 / 1000), sf12=r["12"]["sf"], sf17=r["17"]["sf"], sf25=r["25"]["sf"], sf45=r["45"]["sf"], f=r["f"], fp=fp, pad=pad, pull=max(r[k]["pull"] for k in ("12", "17", "25", "45")), items=I))
                    done = True
    print("done H", H, len(rows), flush=True)
rows.sort(key=lambda r: r["usd"]); json.dump(rows[:40], open("out/ladder2.json", "w"), indent=1, default=float)
for r in rows[:6]: print(f"{r['H']}×{r['b']} m depth {r['d']} width {r['w']:.1f} | {r['n']} sails {r['sec']} + {r['cab']} cable, gens {r['ng']} | Cp {r['Cp']:.2f} TSR {r['lam']} | {r['W']:.0f} W ${r['capex']:,.0f} ${r['usd']:.0f}/MWh (1.3× ${r['usd13']:.0f}) | SF {r['sf12']:.1f}/{r['sf17']:.1f}/{r['sf25']:.1f}/{r['sf45']:.1f} | f {r['f']:.1f} vs pass {r['fp']:.1f} Hz | pad {r['pad']:.1f} t pull {r['pull']:.0f} kg")
