"""SKY LINE: the Zipline sail train with its steel poles replaced by lifters (kite, helium balloon, or both) at each end of the track.
Deliberately generous screen: launch, landing, storms, kite drag on the stays, and tether weight are NOT charged. Lift needed at each end = half the airborne weight + vertical pull of the stay holding cable tension.
Hours count only when the lifters can hold that load. 'Free lift' is the upper bound if lifting cost nothing."""
import itertools, json, math
import numpy as np
import zipline2 as Z
BINS = np.arange(0, 20.01, .25); PHI = math.tan(math.radians(30)); DL = 15; AV = .97 * .95
SC = {"base": dict(kite=25., life=3000., he=20., leak=.005, avail=.85), "optimistic": dict(kite=10., life=20000., he=10., leak=.002, avail=.95)}
def normal(L, h, c, n):
    v = Z.VN[1:]; best = np.zeros(len(v)); ra = np.ones(len(v)); aa = np.zeros(len(v))
    for r in Z.RAT:
        P, _, a = Z.passes(L, h, c, DL, v, np.zeros_like(v), np.full_like(v, r), n); up = P > best; best = np.where(up, P, best); ra = np.where(up, r, ra); aa = np.where(up, a, aa)
    wn, u = v * (1 - aa), ra * v; b = np.arctan2(wn, u); cl, cd = Z.polar(b - math.radians(DL), h / c); return np.r_[0, .5 * Z.RHO * (wn*wn + u*u) * n * h * c * (cl * np.cos(b) + cd * np.sin(b))]
def binned(tb, H, h):
    zc = H - h / 2; az = max(range(0, 180, 20), key=lambda a: Z.energy(tb, zc, a, 1e6)); v = Z.Z.WS * (zc / 10)**.14; th = np.radians(Z.Z.WD - az); x, y = np.clip(v * np.abs(np.cos(th)), 0, 11.99), np.clip(v * np.abs(np.sin(th)), 0, 7.99); i, j = x.astype(int), (y / 2).astype(int); fx, fy = x - i, y / 2 - j
    P = (tb[i, j] * (1 - fx) * (1 - fy) + tb[i + 1, j] * fx * (1 - fy) + tb[i, j + 1] * (1 - fx) * fy + tb[i + 1, j + 1] * fx * fy) * .75 * .92 * .84 * .95; k = np.digitize(v, BINS) - 1; f = np.bincount(k, minlength=len(BINS)) / len(v); s = np.bincount(k, P, minlength=len(BINS)) / len(v); return f, s
VC = BINS + .125; out = {k: {} for k in SC}; free = None; AK = (0, 25, 50, 100, 200, 400, 800); VB = (0, 25, 50, 100, 200, 400, 800)
for L, h, c, n in itertools.product((40, 60, 90, 130), (5, 9, 12), (1.5, 2), (1, 2, 4, 8)):
    if L - (n - 1) * 2.5 * c < 12: continue
    tb = Z.table(L, h, c, DL, n); Nv = normal(L, h, c, n); S = n * h * c; Wt = (8 * n + .7 * S + .02 * 2 * L) * Z.G; Nb = np.interp(VC, Z.VN, Nv, right=Nv[-1])
    for H, sg in itertools.product((20, 40, 60), (.1, .2, .3)):
        if H < h + 2 + sg * L * .15: continue
        f, s = binned(tb, H, h); R = Wt / 2 + PHI * Nb / (4 * sg); line = 3 * (2 * L + 4 * H / math.sin(math.radians(30)) + 2 * H)
        for vcut, ng in itertools.product((5, 6, 8, 10), (1, 2, 3, 5)):
            elec = 518 * ng + 150; rope = 2 * L * 1.2; sail = S * 8 + n * (h * 10 + 120); base = line + 1500 + elec + sail + rope + 950; wear = S * 2 + rope / 3 + 40 * n + 30; life0 = base + wear * 19 + .3 * elec; mask = VC <= vcut; Pc = np.minimum(np.where(f > 0, s / np.maximum(f, 1e-12), 0), 1200 * ng) * f
            W = float((Pc * mask).sum()) * AV
            if W > 1 and (free is None or life0 / (W * 8.766 * 20 / 1000) < free['usd']): free = dict(L=L, h=h, c=c, n=n, H=H, sag=sg, vcut=vcut, ng=ng, W=W, usd=life0 / (W * 8.766 * 20 / 1000))
            for sc, q in SC.items():
                for Ak, Vb in itertools.product(AK, VB):
                    if Ak == 0 and Vb == 0: continue
                    B = max(Vb - .2 * 4.84 * Vb**(2 / 3), 0) * Z.G if Vb else 0.; Lk = np.maximum(.5 * Z.RHO * VC**2 * .9 * Ak - .2 * Ak * Z.G, 0); ok = mask & (B + Lk >= R); W = float((Pc * ok).sum()) * AV * (q["avail"] if Ak else 1)
                    if W <= 1: continue
                    fly = float((f * ok).sum()) * 8766; env = 12 * 4.84 * Vb**(2 / 3) if Vb else 0; cap = 2 * (Ak * q["kite"] + (500 if Ak else 0) + env + Vb * q["he"]); yr = 2 * (Ak * q["kite"] * fly / q["life"] + env / 5 + Vb * q["he"] * q["leak"] * 365); life = life0 + cap + yr * 20
                    u = life / (W * 8.766 * 20 / 1000); cat = 'kite only' if Vb == 0 else ('helium only' if Ak == 0 else 'both')
                    if cat not in out[sc] or u < out[sc][cat][0]: out[sc][cat] = (u, W, base + cap, L, h, c, n, H, sg, vcut, ng, Ak, Vb, float((f * ok).sum()), yr)
    print("done", L, h, c, n, flush=True)
res = {"free_lift": free}; print("FREE LIFT bound:", {k: round(v, 2) for k, v in free.items()})
keys = ("usd", "W", "cap", "L", "h", "c", "n", "H", "sag", "vcut", "ng", "kite_m2_each", "helium_m3_each", "hours_share", "lifter_per_year")
for sc, cats in out.items():
    print(sc.upper())
    for nm, x in sorted(cats.items(), key=lambda kv: kv[1][0]):
        res[sc + "_" + nm] = dict(zip(keys, x)); print(f"  {nm}: ${x[0]:.0f}/MWh, {x[1]:.0f} W, build ${x[2]:,.0f}, {x[6]} sails {x[4]}x{x[5]} m, {x[3]} m span, {x[7]} m high, sag {x[8]}, cut {x[9]} m/s, kite {x[11]} m2, helium {x[12]} m3 each end, runs {100*x[13]:.0f}% of hours, lifter upkeep ${x[14]:,.0f}/yr")
json.dump(res, open("out/skyline.json", "w"), indent=1, default=float)
