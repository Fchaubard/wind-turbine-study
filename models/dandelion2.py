"""Dandelion v2, corrected. (1) Above rated wind a flyweight governor pitches the blades toward feather so shaft power never exceeds what the generator can absorb. (2) Spars must pass rotating-gravity fatigue.
(3) Tower must pass the same criteria as the $134 rotor: SF 2 in normal operation, SF 1.25 at 17 m/s with every safety system failed (full thrust)."""
import json, math, io, contextlib
import numpy as np
with contextlib.redirect_stdout(io.StringIO()):
    import zoo as Z
import v3_rotor as Rt
RHO, G, FX, E = 1.18, 9.81, 18.5, 200e9; WS = Z.WS; FIELD = .75; BMAX = math.radians(75)
def sail_polar(a, tc=.12):
    d = math.degrees(a)
    if d < -2: return 0.0, .12 + .02 * abs(d + 2)
    if d < 11: return .38 + .075 * d, .040 + .0007 * (d - 3)**2
    return max(1.2 - .03 * (d - 11), .6), .14 + 1.5 * math.sin(a)**2
Rt.polar = sail_polar; Rt.R = 6.0; Rt.RIN = .6; cr, ct, tw0, tw1 = .083 * 6 / .0 if False else 1.1, .25, 18, -2
LS = np.arange(.5, 10.01, .5); DL = np.arange(0, 37, 3.0); CPm = np.zeros((len(DL), len(LS))); CTm = CPm.copy()
for i, dl in enumerate(DL):
    g = Rt.geometry(cr, ct, tw0 + dl, tw1 + dl, .06, .03)
    for j, x in enumerate(LS): CPm[i, j], CTm[i, j] = Rt.bem(g, float(x), 14)[:2]
CTm = np.maximum(CTm, 0); LO = float(LS[CPm[0].argmax()]); print(f"table done: peak Cp {CPm[0].max():.3f} at TSR {LO}", flush=True)
def rect(b, h): return b * h, b * h**3 / 12, b * h * h / 6
def tube(o, w): i = o - 2 * w; A = math.pi / 4 * (o**2 - i**2); I = math.pi / 64 * (o**4 - i**4); return A, I, I / (o / 2)
#            section props, density, static allow, fatigue allow, $/m
SPAR = {"steel 2 in Sch 40": (tube(.0603, .00391), 7850, 145e6, 45e6, 20.3), "aluminium 3 in x 3 mm": (tube(.0762, .003), 2700, 150e6, 30e6, 14.0), "laminated pine 76x89 mm": (rect(.089, .076), 560, 17e6, 7e6, 10.0), "laminated pine 114x89 mm": (rect(.089, .114), 560, 17e6, 7e6, 15.0)}
LEG = {"73 mm post tube": (.073, .0012, 545 / 3.05), "2-1/2 in Sch 40": (.073, .00516, 520), "3 in Sch 40": (.0889, .00549, 680)}
VG = np.arange(.5, 25.01, .5)
def table(D, mt, Vr, Pr, sp):
    (As, Is, Ss), rho, _, _, _ = SPAR[sp]; R = D / 2; A = math.pi * R * R; rs = np.linspace(.1 * R, R, 36); dr = rs[1] - rs[0]; x = rs / R; ch = (cr + (ct - cr) * x) * R / 6; m = As * rho + .45 * 2 * ch + .15; Ib = float(np.sum(m * rs * rs) * dr) + mt * R * R; Om_r = LO * Vr / R; out = []
    Mg = np.array([np.sum(m[i:] * G * (rs[i:] - rs[i])) * dr + mt * G * (R - rs[i]) for i in range(len(rs))])
    for V in VG:
        Om = LO * V / R if V <= Vr else Om_r; lam = min(Om * R / V, 10.0); q = .5 * RHO * V * V; cps = np.array([np.interp(lam, LS, CPm[i]) for i in range(len(DL))]); cts = np.array([np.interp(lam, LS, CTm[i]) for i in range(len(DL))])
        k = 0
        if V > Vr:
            while k < len(DL) - 1 and cps[k] * FIELD * q * V * A > Pr: k += 1
        cpv, ctv = max(cps[k], 0), cts[k]
        f = lambda b: ctv * q * A * math.cos(b)**3 / 3 * (.68 * R) - Ib * Om * Om * math.sin(b) * math.cos(b); lo, hi = 0.0, BMAX
        if f(hi) > 0: b = hi
        else:
            for _ in range(36):
                mid = (lo + hi) / 2
                if f(mid) > 0: lo = mid
                else: hi = mid
            b = (lo + hi) / 2
        T = ctv * q * A * math.cos(b)**4; P = min(cpv * FIELD * q * V * A * math.cos(b)**5, Pr); fn = ctv * q * A * math.cos(b)**3 / 3 * (2 * x / np.sum(2 * x * dr)); net = fn - m * Om * Om * rs * math.sin(b) * math.cos(b); tipF = mt * Om * Om * R * math.sin(b) * math.cos(b)
        Mb = np.array([np.sum(net[i:] * (rs[i:] - rs[i])) * dr - tipF * (R - rs[i]) for i in range(len(rs))]); Nc = np.array([np.sum(m[i:] * Om * Om * rs[i:]) * dr for i in range(len(rs))]) + mt * Om * Om * R
        out.append((V, Om, b, T, P, float(np.max((np.abs(Mb) + Mg) / Ss + Nc / As)), float(np.max((.3 * np.abs(Mb) + Mg) / Ss)), DL[k]))
    return np.array(out), float(np.sum(m) * dr + mt)
def tripod(hub, Th, W):
    az = hub - .25; Rb = 2.0; L = math.hypot(az, Rb); U = (np.array([[Rb * math.cos(a), Rb * math.sin(a), -az] for a in np.radians((90, 210, 330))]) / L).T; c = t = 0
    for a in np.radians(np.arange(0, 360, 15)):
        f = np.linalg.solve(U, -np.array([Th * math.cos(a), Th * math.sin(a), -W])); c = max(c, -f.min()); t = max(t, f.max())
    return c, t, L
def energy(tb, hub, cap, eta, s=1.0):
    v = WS * (hub / 10) ** .14 * math.cos(math.radians(10)) * s; return float(np.mean(np.minimum(np.interp(np.minimum(v, 25), tb[:, 0], tb[:, 4]) * .95 * eta, cap))) * .97
rows = []
for D in (8, 10, 12, 14):
    A = math.pi * D * D / 4
    for sp, (_, _, sa, fa, cm) in SPAR.items():
        for mt in (0, 2, 4):
            for ng in (1, 2):
                Pr = 1200 * ng / (.84 * .95 * .95); Vr = (Pr / (CPm[0].max() * FIELD * .5 * RHO * A))**(1 / 3); tb, mbl = table(float(D), mt, Vr, Pr, sp)
                if tb[:, 5].max() > sa or tb[tb[:, 0] <= 12, 6].max() > fa: continue
                Tmax = float(tb[:, 3].max()); Tj = .85 * .5 * RHO * 289 * A
                for hub in (8.0, 10.0, 12.0):
                    if hub < D / 2 + 2.0: continue
                    W = (3 * mbl + 75) * G; c, tn, L = tripod(hub, Tmax, W); cj, tj, _ = tripod(hub, Tj, W); pick = None
                    for ln, (od, w2, mx) in LEG.items():
                        Al, Il, _ = tube(od, w2)
                        for br in (1, 2, 3, 4):
                            cap = min(math.pi**2 * E * Il / (L / (br + 1))**2, 230e6 * Al)
                            if cap / c >= 2 and cap / cj >= 1.25:
                                st = 3 * L * mx / FX + br * 3 * 2.4 * 150 / FX
                                if pick is None or st < pick[0]: pick = (st, ln, br)
                                break
                    if not pick: continue
                    st, ln, br = pick; fab = 3 * D / 2 * (cr + ct) / 2 * (D / 12) * 2; blade = 3 * D / 2 * cm + fab * 7 * 1.15 + 3 * (6 * 2 + 8) + 3 * 35 + 3 * mt; gov = 3 * 45 + 90
                    common = st + blade + gov + 224 + 170 + 140 + 220 + 90 + 135 + 80
                    for use, elec, cap_w, eta, rb in (("electricity", 733. * ng, 1200. * ng, .84 * .95, 220. * ng), ("hot water", 330. * ng, 1200. * ng, .70, 100. * ng)):
                        Wv = energy(tb, hub, cap_w, eta); c20 = common + elec; wear = 1.6 * fab + 70 + .02 * st; life = c20 + wear * 19 + rb + (fab * 7 + 40); usd = life / (Wv * 8.766 * 20 / 1000)
                        rows.append(dict(D=D, spar=sp, mt=mt, ng=ng, Vr=Vr, hub=hub, leg=ln, br=br, use=use, W=Wv, capex=c20, wear=wear, usd=usd, usd13=life / (energy(tb, hub, cap_w, eta, 1.3) * 8.766 * 20 / 1000), Tmax=Tmax, Tjam=Tj, pitch25=float(tb[-1, 7]), cone=float(np.degrees(tb[tb[:, 0] <= Vr, 2].max())), sig=float(tb[:, 5].max()), fat=float(tb[tb[:, 0] <= 12, 6].max()), tower=st, blade=blade, mass=3 * mbl, pull_kg=tj * (hub - .25) / L / G, pad_t=1.5 * Tj * hub / (2 * G) / 1000))
    print("done D", D, len(rows), flush=True)
rows.sort(key=lambda r: r["usd"]); json.dump(rows[:60], open("out/dandelion2.json", "w"), indent=1, default=float)
for u in ("electricity", "hot water"):
    print(u)
    for r in [x for x in rows if x["use"] == u][:4]: print(f" {r['D']} m hub {r['hub']:.0f} {r['spar']} tip {r['mt']} kg gens {r['ng']} rated {r['Vr']:.1f} | {r['leg']} br{r['br']} | {r['W']:.0f} W ${r['capex']:,.0f} ${r['usd']:.0f}/MWh (1.3× ${r['usd13']:.0f}) | cone {r['cone']:.0f}° | thrust {r['Tmax']/1000:.1f} kN, all-safeties-failed {r['Tjam']/1000:.1f} | spar {r['sig']/1e6:.0f}/{r['fat']/1e6:.1f} MPa | rotor {r['mass']:.0f} kg | pad {r['pad_t']:.1f} t")
