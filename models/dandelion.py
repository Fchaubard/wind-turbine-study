"""THE DANDELION: downwind rotor, 3 double-skin sailwing blades (fabric sleeve on a thin spar, taut trailing-edge wire), each on a free hinge at the hub.
Thrust folds a blade back, centrifugal force pulls it flat; the blade finds its own cone angle so the spar carries tension rather than root bending. Above rated rpm the generator holds speed, so thrust wins and the rotor folds, shedding power and load.
BEM with a sailwing polar; quasi-static hinge equilibrium at each wind speed; spar stress along span; tripod statics; itemised cost; same hourly wind, field factor and 20-year accounting as the $134 rotor."""
import json, math, io, contextlib
import numpy as np
with contextlib.redirect_stdout(io.StringIO()):
    import zoo as Z
import v3_rotor as Rt
RHO, G, FX, FY, E = 1.18, 9.81, 18.5, 230e6, 200e9; WS = Z.WS; FIELD = .75; CPCAP = .36; BMAX = math.radians(75)
def sail_polar(a, tc=.12):
    d = math.degrees(a)
    if d < -2: return 0.0, .12 + .02 * abs(d + 2)            # fabric luffs at negative incidence
    if d < 11: cl = .38 + .075 * d; return cl, .040 + .0007 * (d - 3)**2
    return max(1.2 - .03 * (d - 11), .6), .14 + 1.5 * math.sin(a)**2
Rt.polar = sail_polar; Rt.R = 6.0; Rt.RIN = .6
best = None
for cr in (.5, .7, .9, 1.1):
    for ct in (.25, .4, .55):
        for tw0 in (10, 14, 18, 24):
            for tw1 in (-2, 0, 2, 4):
                g = Rt.geometry(cr, ct, tw0, tw1, .06, .03); cp, l = max((Rt.bem(g, x, 14)[0], x) for x in (3.5, 4.5, 5.5, 6.5)); s = cp - .03 * (cr + ct)
                if best is None or s > best[0]: best = (s, cr, ct, tw0, tw1)
_, cr, ct, tw0, tw1 = best; g = Rt.geometry(cr, ct, tw0, tw1, .06, .03); LS = np.arange(.5, 11.01, .25); tab = [Rt.bem(g, x, 20)[:2] for x in LS]; CPt = np.maximum(np.array([a for a, _ in tab]), -.05); CTt = np.maximum(np.array([b for _, b in tab]), 0)
il = int(CPt.argmax()); LO = float(LS[il]); PK = float(CPt[il]); scale = min(CPCAP / PK, 1.0); CPt = CPt * scale
print(f"sailwing: chord/R {cr/6:.3f} -> {ct/6:.3f}, twist {tw0} -> {tw1}; clean BEM Cp {PK:.3f} at TSR {LO}, used {PK*scale:.2f}; CT {CTt[il]:.2f}", flush=True)
SPAR = {"1-1/4 in conduit": (.0386, .00165, 329 / 3 / FX), "1-1/2 in Sch 40": (.0483, .0037, 300 / FX), "2 in Sch 40": (.0603, .00391, 300 / FX * 1.25)}
def props(od, w): i = od - 2 * w; return math.pi / 4 * (od**2 - i**2), math.pi / 64 * (od**4 - i**4), math.pi / 32 * (od**4 - i**4) / od
LEG = {"73 mm post tube": (.073, .0012, 545 / 3.05), "2-1/2 in Sch 40": (.073, .00516, 520), "3 in Sch 40": (.0889, .00549, 680)}
VG = np.arange(.5, 45.01, .5)
def machine(D, mt, Vr, sp):
    R = D / 2; od, w, _ = SPAR[sp]; As, Is, Ss = props(od, w); rs = np.linspace(.08 * R, R, 40); dr = rs[1] - rs[0]; x = rs / R; ch = (cr + (ct - cr) * x) * R / 6; m = As * 7850 + .45 * 2 * ch + .12; Ib = float(np.sum(m * rs * rs) * dr) + mt * R * R; S1 = float(np.sum(m * rs) * dr) + mt * R; OMr = LO * Vr / R; out = []
    for V in VG:
        Om = LO * V / R if V <= Vr else OMr; lam = Om * R / V; cpv, ctv = float(np.interp(lam, LS, CPt)), float(np.interp(lam, LS, CTt)); q = .5 * RHO * V * V; A = math.pi * R * R
        f = lambda b: ctv * q * A * math.cos(b)**3 / 3 * (.68 * R) - Ib * Om * Om * math.sin(b) * math.cos(b)
        lo, hi = 0.0, BMAX
        if f(hi) > 0: b = hi
        else:
            for _ in range(40):
                mid = (lo + hi) / 2
                if f(mid) > 0: lo = mid
                else: hi = mid
            b = (lo + hi) / 2
        T = ctv * q * A * math.cos(b)**4; P = max(cpv, 0) * FIELD * q * V * A * math.cos(b)**5
        fn = ctv * q * A * math.cos(b)**3 / 3 * (2 * x / np.sum(2 * x * dr)) ; net = fn - m * Om * Om * rs * math.sin(b) * math.cos(b); tipF = mt * Om * Om * R * math.sin(b) * math.cos(b)
        Mb = np.array([np.sum(net[i:] * (rs[i:] - rs[i])) * dr - tipF * (R - rs[i]) for i in range(len(rs))]); Mg = np.array([np.sum(m[i:] * G * (rs[i:] - rs[i])) * dr + mt * G * (R - rs[i]) for i in range(len(rs))]); Nc = np.array([np.sum(m[i:] * Om * Om * rs[i:]) * dr for i in range(len(rs))]) + mt * Om * Om * R
        out.append((V, Om, b, T, P, float(np.max((np.abs(Mb) + Mg) / Ss + Nc / As))))
    return np.array(out), Ib, S1
def tripod(hub, Tmax, W):
    az = hub - .25; Rb = 2.0; L = math.hypot(az, Rb); feet = np.array([[Rb * math.cos(a), Rb * math.sin(a), -az] for a in np.radians((90, 210, 330))]) / L; U = feet.T; c = 0; t = 0
    for a in np.radians(np.arange(0, 360, 15)):
        f = np.linalg.solve(U, -np.array([Tmax * math.cos(a), Tmax * math.sin(a), -W])); c = max(c, -f.min()); t = max(t, f.max())
    return c, t, L
def energy(tb, hub, cap, eta, s=1.0):
    v = WS * (hub / 10) ** .14 * math.cos(math.radians(10)) * s; return float(np.mean(np.minimum(np.interp(v, tb[:, 0], tb[:, 4]) * .95 * eta, cap))) * .97
R_ = []
for D in (8, 10, 12, 14, 16):
    for sp in SPAR:
        for mt in (0, 1.5, 3, 5, 8):
            for Vr in (5.5, 6.5, 7.5, 8.5):
                tb, Ib, S1 = machine(float(D), mt, Vr, sp); idx25 = tb[:, 0] <= 25
                if tb[idx25, 5].max() > FY / 1.6: continue
                Tmax = float(tb[idx25, 3].max()); Pk = float(tb[idx25, 4].max()); ws = tb[tb[:, 0] <= Vr, 2].max()
                if Pk * .8 > 2600: continue
                A = math.pi * D * D / 4; mb = 3 * (props(*SPAR[sp][:2])[0] * 7850 * D / 2 + .45 * .6 * D / 2 * 1.5 + mt) + 35
                Tj = float(.85 * .5 * RHO * 289 * A * .85)                     # hinge seized at working cone, 17 m/s
                for hub in (8.0, 10.0, 12.0):
                    if hub < D / 2 + 2.0: continue
                    c, tn, L = tripod(hub, Tmax, (mb + 60) * G); cj, tj, _ = tripod(hub, Tj, (mb + 60) * G)
                    for ln, (od, w2, mx) in LEG.items():
                        Al, Il, _ = props(od, w2); ok = None
                        for br in (1, 2, 3, 4):
                            cap = min(math.pi**2 * E * Il / (L / (br + 1))**2, FY * Al)
                            if cap / c >= 2.0 and cap / cj >= 1.0: ok = br; break
                        if ok is None: continue
                        st = 3 * L * mx / FX + ok * 3 * 2.4 * 150 / FX; blade = 3 * (D / 2 * SPAR[sp][2] + D / 2 * float(cr + ct) / 2 * (D / 12) * 2 * 7 * 1.15 + 6 * 2 + 8) + 3 * 35 + 3 * 40 + 3 * mt * .8
                        common = st + blade + 112 * 2 + 170 + 140 + 220 + 90 + 135 + 80
                        for use, elec, cap_w, eta, rb in (("electricity", 733., 1200., .84 * .95, 220.), ("hot water", 330., 2400., .70, 100.)):
                            W = energy(tb, hub, cap_w, eta); c20 = common + elec; wear = 1.6 * 3 * D / 2 * (cr + ct) / 2 * (D / 12) * 2 + 60 + .02 * st; usd = (c20 + wear * 19 + rb + blade * .5) / (W * 8.766 * 20 / 1000) if W > 5 else 1e6
                            R_.append(dict(D=D, spar=sp, mt=mt, Vr=Vr, hub=hub, leg=ln, br=ok, use=use, W=W, capex=c20, usd=usd, usd13=(c20 + wear * 19 + rb + blade * .5) / (energy(tb, hub, cap_w, eta, 1.3) * 8.766 * 20 / 1000), Tmax=Tmax, Tjam=Tj, cone=math.degrees(ws), fold25=float(np.degrees(np.interp(25, tb[:, 0], tb[:, 2]))), Pk=Pk, tower=st, blade=blade, sig=float(tb[idx25, 5].max()), comp=c, comp_j=cj, pull_kg=tn * (hub - .25) / L / G))
                        break
    print("done D", D, len(R_), flush=True)
R_.sort(key=lambda r: r["usd"]); json.dump(dict(top=R_[:60], cr=cr, ct=ct, tw=(tw0, tw1), tsr=LO, cp=PK * scale), open("out/dandelion.json", "w"), indent=1, default=float)
for u in ("electricity", "hot water"):
    print(u)
    for r in [x for x in R_ if x["use"] == u][:4]: print(f" {r['D']} m hub {r['hub']:.0f} {r['spar']} tip {r['mt']} kg rated {r['Vr']} m/s | {r['leg']} br{r['br']} | {r['W']:.0f} W ${r['capex']:,.0f} ${r['usd']:.0f}/MWh (1.3× ${r['usd13']:.0f}) | cone {r['cone']:.0f}° fold@25 {r['fold25']:.0f}° | thrust max {r['Tmax']/1000:.1f} kN (seized {r['Tjam']/1000:.1f}) spar {r['sig']/1e6:.0f} MPa pull {r['pull_kg']:.0f} kg")
