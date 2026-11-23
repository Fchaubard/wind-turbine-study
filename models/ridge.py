"""RIDGE STUDY on the real ~126 m coastal hill near Punta Mita (public 90 m elevation model).
Hill speed-up from the upwind profile in 16 directions (Jackson-Hunt style: dS = 1.6 h/L, capped 0.8, decaying with height). Because this is unmeasured, every result is shown at 25%, 50% (base) and 100% of theory.
Machines: Dandelion array on the crest; RIDGE LINE (sail train on a cable hung peak to peak, 5 m end posts); CREST FENCE (sail train along the ridge on many short posts with ski-lift sheaves).
All carry a 1.5 km wire to the beach, structural loads scaled by the hill speed-up, and access costs."""
import json, math, itertools
import numpy as np
import zipline2 as Z
W0, D0 = Z.Z.WS, Z.Z.WD; F = json.load(open("out/terrain_fine.json")); C = json.load(open("out/terrain.json"))
def grid(g): return np.array(g["lats"]), np.array(g["lons"]), np.array(g["elev"])
FL, FO, FE = grid(F); CL, CO, CE = grid(C)
def elev(la, lo):
    if FL[0] <= la <= FL[-1] and FO[0] <= lo <= FO[-1]: return float(FE[np.abs(FL - la).argmin(), np.abs(FO - lo).argmin()])
    return float(CE[np.abs(CL - la).argmin(), np.abs(CO - lo).argmin()])
def xy(la, lo): return (lo + 105.52) * 104e3, (la - 20.77) * 111e3
def hill(la, lo):
    z0 = elev(la, lo); out = []
    for d in np.arange(0, 360, 22.5):
        r = np.arange(90, 2600, 90.); p = np.array([elev(la + x * math.cos(math.radians(d)) / 111e3, lo + x * math.sin(math.radians(d)) / 104e3) for x in r]); h = max(z0 - p.min(), 0)
        if h < 5: out.append((0., 300.)); continue
        k = np.argmax(p <= z0 - h / 2); Lh = float(r[k]); out.append((min(1.6 * h / Lh, .8), Lh))
    return np.array(out)
def speed(H, z, f):
    k = (np.round(D0 / 22.5).astype(int)) % 16; return 1 + f * H[k, 0] * np.exp(-3 * z / H[k, 1])
RUN = 1500 * 2.5 + 500
def tab_energy(tb, v, az, cap):
    th = np.radians(D0 - az); n, a = np.clip(v * np.abs(np.cos(th)), 0, Z.VN[-1] - 1e-6), np.clip(v * np.abs(np.sin(th)), 0, Z.VA[-1] - 1e-6); i, j = n.astype(int), (a / 2).astype(int); x, y = n - i, a / 2 - j
    P = tb[i, j] * (1 - x) * (1 - y) + tb[i + 1, j] * x * (1 - y) + tb[i, j + 1] * (1 - x) * y + tb[i + 1, j + 1] * x * y; return float((np.minimum(P * .75 * .92 * .84 * .95, cap) * (v <= 11.)).mean()) * .97 * .95
def wire_size(L, h, c, n, smax, post):
    S = n * h * c; N17 = .5 * Z.RHO * (17 * smax)**2 * S * 1.3; N12 = .5 * Z.RHO * (12 * smax)**2 * S * 1.3 * 1.2; sw = (8 * n + .7 * S) * Z.G / 2; KG = {"1/4": .22, "5/16": .35, "3/8": .5, "1/2": .9, "5/8": 1.4}; best = None
    for wn, (Ac, Fb, wc) in Z.WIRE.items():
        for fr in (.1, .15, .2, .25):
            T0 = fr * Fb; s17, T17 = Z.sag(N17 / 2, Ac, T0); s12, T12 = Z.sag(N12 / 2, Ac, T0)
            if Fb / T17 < 1.25 or Fb / T12 < 2 or s17 > .1: continue
            droop = sw * L / (4 * T0) + KG[wn] * Z.G * L * L / (8 * T0)
            for pn, (o, w, pc) in Z.PIPE.items():
                i = o - 2 * w; Ap, Ip = math.pi / 4 * (o*o - i*i), math.pi / 64 * (o**4 - i**4); C17 = 4 * T17 + Ap * 7850 * post * Z.G; Cap = min(math.pi**2 * Z.E * Ip / post**2, 250e6 * Ap)
                if Cap / C17 < 1.25 or Cap / (C17 * T12 / T17) < 2: continue
                st = dict(wire=wn, pipe=pn, droop=droop, T17=T17, sf_wire=Fb / T17, sf_pole=Cap / C17, wire_cost=2 * L * wc + 8 * post * 1.41 * wc, steel=2 * post * pc * 1.15, anchors=1500, H=post)
                if best is None or st["steel"] * 1.15 + st["wire_cost"] < best["steel"] * 1.15 + best["wire_cost"]: best = st
                break
    return best
A, B = (20.782, -105.524), (20.785, -105.521); HA, HB = hill(*A), hill(*B); H = HA if HA[:, 0].mean() >= HB[:, 0].mean() else HB
ax, ay = xy(*A); bx, by = xy(*B); SPAN = math.hypot(bx - ax, by - ay); AZ = (math.degrees(math.atan2(bx - ax, by - ay)) + 90) % 180
prof = np.array([elev(A[0] + t * (B[0] - A[0]), A[1] + t * (B[1] - A[1])) for t in np.linspace(0, 1, 41)]); chord = prof[0] + (prof[-1] - prof[0]) * np.linspace(0, 1, 41); clear = chord - prof
print(f"crests {prof[0]:.0f} m and {prof[-1]:.0f} m, {SPAN:.0f} m apart; lowest ground {prof.min():.0f} m; max clearance under cable {clear.max():.0f} m; line normal {AZ:.0f}°; hill speed-up theory mean {H[:, 0].mean():.2f}, max {H[:, 0].max():.2f}", flush=True)
RES = {"terrain": dict(span=SPAN, elev_a=prof[0], elev_b=prof[-1], low=prof.min(), clear=clear.max(), az=AZ, ds_mean=H[:, 0].mean(), ds_max=H[:, 0].max())}
dd = json.load(open("out/dandelion_final.json")); AD = math.pi * 25; base = W0 * math.cos(math.radians(10))
def dand(v): return np.minimum(AD * .5 * Z.RHO * v**3, 1e9)
vb = base; lo_k, hi_k = .01, .6
for _ in range(50):
    k = .5 * (lo_k + hi_k); w = float(np.mean(np.minimum(k * dand(vb), 1200) * (vb >= 2.5)))
    if w < dd["W"]: lo_k = k
    else: hi_k = k
for f, lab in ((.25, "low"), (.5, "base"), (1., "high")):
    rows = {}
    s10 = speed(H, 10, f); v = base * s10; w1 = float(np.mean(np.minimum(k * dand(v), 1200) * (v >= 2.5))); sm = float(np.percentile(s10, 99)); life1 = 5820 + 1324 * (sm * sm - 1)
    rows["Dandelion array on crest"] = min((dict(units=u, W=u * w1 * .95, cap=u * 3309 * (1 + .4 * (sm * sm - 1)) + RUN, usd=(u * life1 + RUN) / (u * w1 * .95 * 8.766 * 20 / 1000)) for u in (1, 2, 4, 6, 8, 12)), key=lambda r: r["usd"])
    best_r = best_f = None
    for h, c, n in itertools.product((5, 9, 12, 18), (1.5, 2, 3), (2, 4, 8, 12)):
        L = SPAN
        if L - (n - 1) * 2.5 * c < 40: continue
        sm_r = 1 + f * H[:, 0].max() * .7; st = wire_size(L, h, c, n, sm_r, 5.)
        if st and clear.max() > h + st["droop"] + 3:
            tb = Z.table(L, h, c, 15, n); z = max(clear.max() - st["droop"] - h / 2, 5); v = W0 * (z / 10)**.14 * speed(H, z, f * .7)
            for ng in (2, 4, 8, 12):
                cap, wear, life = Z.cost(L, h, c, ng, st, n); cap += RUN + 1500; life += RUN + 1500; W = tab_energy(tb, v, AZ, 1200 * ng)
                if W > 1 and (best_r is None or life / W < best_r["life"] / best_r["W"]): best_r = dict(h=h, c=c, n=n, ng=ng, W=W, cap=cap, life=life, usd=life / (W * 8.766 * 20 / 1000), droop=st["droop"], wire=st["wire"], pipe=st["pipe"], sf=st["sf_wire"], z=z)
    for h, c, n, Lf in itertools.product((3, 5, 7), (1.5, 2, 3), (2, 4, 8, 16), (120, 240, 400)):
        if Lf > SPAN or Lf - (n - 1) * 2.5 * c < 30: continue
        sm_f = 1 + f * H[:, 0].max(); st = wire_size(25., h, c, max(1, min(n, 2)), sm_f, h + 2.)
        if not st: continue
        posts = int(Lf / 25) + 1; st = dict(st, wire_cost=2 * Lf * Z.WIRE[st["wire"]][2], steel=posts * (h + 2) * Z.PIPE[st["pipe"]][2] * 1.15 + posts * 90, anchors=posts * 100 + 1000); tb = Z.table(Lf, h, c, 15, n); z = 2 + h / 2; v = W0 * (z / 10)**.14 * speed(H, z, f)
        for ng in (2, 4, 8, 12):
            cap, wear, life = Z.cost(Lf, h, c, ng, st, n); cap += RUN + 1000; life += RUN + 1000; W = tab_energy(tb, v, AZ, 1200 * ng)
            if W > 1 and (best_f is None or life / W < best_f["life"] / best_f["W"]): best_f = dict(L=Lf, h=h, c=c, n=n, ng=ng, W=W, cap=cap, life=life, usd=life / (W * 8.766 * 20 / 1000), posts=posts)
    if best_r: rows["Ridge Line, peak to peak"] = best_r
    if best_f: rows["Crest Fence"] = best_f
    RES[lab] = rows; print(lab.upper(), f"(speed-up {int(f*100)}% of theory, 10 m crest mean factor {s10.mean():.2f})", flush=True)
    for nm, r in sorted(rows.items(), key=lambda kv: kv[1]["usd"]): print(f"  {nm}: ${r['usd']:.0f}/MWh, {r['W']:.0f} W, build ${r['cap']:,.0f} | " + ", ".join(f"{a}={round(b, 2) if isinstance(b, float) else b}" for a, b in r.items() if a not in ("usd", "W", "cap", "life")), flush=True)
json.dump(RES, open("out/ridge.json", "w"), indent=1, default=float)
