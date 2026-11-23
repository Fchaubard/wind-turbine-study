"""ZIPLINE SAIL: one vertical fabric wing rides two horizontal cables between guyed poles, tacking back and forth and pulling a rope loop to a reversing generator.
Time-stepped pass (start, cruise, regenerative stop, sail flip), fixed sheet angle with stall polar, induced drag, trolley friction, rope drag, momentum induction on the swept area,
hourly speed AND direction, cable sag solved with elastic stretch. Structure passes at 12 m/s operating (SF 2) and 17 m/s with the sail stuck open broadside (SF 1.25)."""
import json, math, io, contextlib, itertools
import numpy as np
with contextlib.redirect_stdout(io.StringIO()):
    import zoo as Z
RHO, G, E, EW = 1.18, 9.81, 200e9, 100e9
VN = np.arange(0., 13.); VA = np.arange(0., 9., 2.); RAT = np.array([.6, 1., 1.5, 2., 2.75]); DT, NS = .1, 450; FLIP, AB, MU = 1.5, 2.5, .03
PIPE = {"3 in": (.0889, .00549, 34), "4 in": (.1143, .00602, 52), "6 in": (.1683, .00711, 110), "8 in": (.2191, .00818, 165)}
WIRE = {"1/4": (24e-6, 25e3, 1.6), "5/16": (38e-6, 39e3, 2.3), "3/8": (56e-6, 60e3, 4.), "1/2": (100e-6, 105e3, 6.5), "5/8": (157e-6, 165e3, 9.5)}
CD0 = [.07]
def polar(a, AR):
    cd0 = CD0[0]
    d = np.degrees(a); cl = np.where(d < 14, .25 + .07 * d, np.maximum(1.23 - .012 * (d - 14), .75)); cl = np.where(d < -3.5, 0., cl); stall = np.maximum(d - 14, 0) / 40
    return cl, cd0 + cl * cl / (math.pi * .75 * AR) + 1.3 * np.minimum(stall, 1) * np.sin(np.clip(a, 0, math.pi / 2))**2
def passes(L0, h, c, delta, Vn, Va, ur, n=1):
    L = L0 - (n - 1) * 2.5 * c; S, AR, A = n * h * c, h / c, L0 * h; m = 8 * n + .7 * S + .06 * L0 + n * RHO * math.pi * c * c / 4 * h; dl = math.radians(delta); a = np.full(Vn.shape, .1)
    for _ in range(3):
        x, u = np.zeros(Vn.shape), np.full(Vn.shape, .05); E_, Tn, t = [np.zeros(Vn.shape) for _ in range(3)]; live = np.ones(Vn.shape, bool); brk = np.zeros(Vn.shape, bool); tgt = np.maximum(ur * np.hypot(Vn, Va), .3)
        for _s in range(NS):
            wn, wa = Vn * (1 - a), u - Va; W2 = wn * wn + wa * wa; b = np.arctan2(wn, wa); cl, cd = polar(b - dl, AR); q = .5 * RHO * W2 * S
            Fx, N = q * (cl * np.sin(b) - cd * np.cos(b)), q * (cl * np.cos(b) + cd * np.sin(b)); Fr = MU * np.abs(N) + .5 * RHO * u * u * (.25 + math.pi * .006 * 2 * L * .01) + 3
            net = Fx - Fr; brk = brk | (x + u * u / (2 * AB) >= L); hold = (u >= tgt) & (net > 0) & ~brk; Fg = np.where(brk, np.maximum(net + m * AB, 0.), np.where(hold, net, 0.)); ac = np.where(brk, -AB, np.where(hold, 0., net / m)); ok = live & ~(brk & (u <= AB * DT))
            E_ += np.where(ok, Fg * u * DT, 0.); Tn += np.where(ok, N * DT, 0.); t += ok * DT; x = np.where(ok, x + u * DT, x); u = np.where(ok, np.maximum(u + ac * DT, .02), u); live = ok
            if not live.any(): break
        tp = np.where(live, 1e9, t + FLIP); Pm = np.where(live, 0., E_ / tp); Ct = np.where(Vn > .1, (Tn / tp) / (.5 * RHO * np.maximum(Vn, .1)**2 * A), 0.); an = .5 * (1 - np.sqrt(np.maximum(1 - np.minimum(Ct, .96), 0))); a = .5 * a + .5 * np.minimum(an, .45)
    return Pm, N, a
def table(L, h, c, delta, n=1):
    vn, va, r = np.meshgrid(VN, np.r_[-VA[:0:-1], VA], RAT, indexing="ij"); P, _, _ = passes(L, h, c, delta, vn, va, r, n); n = len(VA) - 1; both = .5 * (P + P[:, ::-1, :]); return both.max(2)[:, n:]
def energy(tab, zc, az, cap, s=1., f=.75):
    v = Z.WS * (zc / 10)**.14 * s; th = np.radians(Z.WD - az); n, a = np.clip(v * np.abs(np.cos(th)), 0, VN[-1] - 1e-6), np.clip(v * np.abs(np.sin(th)), 0, VA[-1] - 1e-6); i, j = n.astype(int), (a / 2).astype(int); fx, fy = n - i, a / 2 - j
    P = tab[i, j] * (1 - fx) * (1 - fy) + tab[i + 1, j] * fx * (1 - fy) + tab[i, j + 1] * (1 - fx) * fy + tab[i + 1, j + 1] * fx * fy
    return float((np.minimum(P * f * .92 * .84 * .95, cap) * (v <= 11.)).mean()) * .97 * .95
def sag(N, Ac, T0):
    lo, hi = 1e-4, .45
    for _ in range(50):
        r = .5 * (lo + hi); T = T0 + EW * Ac * 2 * r * r
        if 4 * T * r > N: hi = r
        else: lo = r
    return r, T0 + EW * Ac * 2 * r * r
def structure(L, h, c, n=1):
    S = n * h * c; H = 1.5 + h + .5; N17 = .5 * RHO * 289 * S * 1.3; N12 = .5 * RHO * 144 * S * 1.3 * 1.2
    for wn, (Ac, F, wc) in WIRE.items():
        T0 = .1 * F; s17, T17 = sag(N17 / 2, Ac, T0); s12, T12 = sag(N12 / 2, Ac, T0)
        if F / T17 < 1.25 or F / T12 < 2 or s17 > .1: continue
        for pn, (o, w, pc) in PIPE.items():
            i = o - 2 * w; Ap, Ip = math.pi / 4 * (o*o - i*i), math.pi / 64 * (o**4 - i**4); C17 = 2 * (T17 + T17) + Ap * 7850 * H * G; Cap = min(math.pi**2 * E * Ip / H**2, 250e6 * Ap)
            if Cap / C17 < 1.25 or Cap / (C17 * T12 / T17) < 2: continue
            gl = H / math.sin(math.radians(45)); wire = 2 * L * wc + 2 * 4 * gl * wc; steel = 2 * H * pc * 1.15; return dict(wire=wn, pipe=pn, H=H, T17=T17, sag17=s17, sf_wire17=F / T17, sf_wire12=F / T12, sf_pole17=Cap / C17, wire_cost=wire, steel=steel, anchors=6 * 250)
    return None
def cost(L, h, c, ng, st, n=1):
    S = n * h * c; elec = 518 * ng + 150; sail = S * 8 + n * (h * 10 + 120); rope = 2 * L * 1.2; cap = st["steel"] * 1.15 + st["wire_cost"] + st["anchors"] + elec + sail + rope + 250 + 400 + 300; wear = S * 8 / 4 + rope / 3 + 40 * n + 30 + .02 * st["steel"]; return cap, wear, cap + wear * 19 + .3 * elec

def run(tag):
    R = []
    for L, h, c, dl, n in itertools.product((25, 40, 60, 90), (5, 7, 9), (1.5, 2, 3), (15, 20), (1, 2, 4, 6, 8, 12)):
        if L - (n - 1) * 2.5 * c < 10: continue
        st = structure(L, h, c, n)
        if not st: continue
        tb = table(L, h, c, dl, n); zc = 1.5 + h / 2; az = max(range(0, 180, 20), key=lambda a: energy(tb, zc, a, 1e6))
        for ng in (1, 2, 3):
            cap, wear, life = cost(L, h, c, ng, st, n); W = energy(tb, zc, az, 1200 * ng)
            if W > 1: R.append(dict(L=L, h=h, c=c, delta=dl, n=n, ng=ng, az=az, W=W, cap=cap, life=life, usd=life / (W * 8.766 * 20 / 1000), usd13=life / (energy(tb, zc, az, 1200 * ng, 1.3) * 8.766 * 20 / 1000), S=n * h * c, A=L * h, cp=float(np.max(tb[3:11, 0] / (.5 * RHO * VN[3:11]**3 * L * h))), **st))
    R.sort(key=lambda r: r["usd"]); r = R[0]; print(f"{tag}: {r['n']} sails {r['h']}×{r['c']} m on {r['L']} m track, {r['S']:.0f} m² sail, {r['A']} m² swept, Cp {r['cp']:.2f}, {r['ng']} gen, {r['W']:.0f} W, ${r['cap']:,.0f}, ${r['usd']:.0f}/MWh (1.3× wind ${r['usd13']:.0f}) | {r['wire']} wire {r['pipe']} poles H {r['H']:.0f} m SF {r['sf_wire17']:.2f}/{r['sf_pole17']:.2f}", flush=True); return R
if __name__ == "__main__":
    import zipline2 as me
    base = run("BASE"); CD0[0] = .035; gl = globals(); gl["MU"] = .015; opt = run("OPTIMISTIC (clean sail, half friction)"); json.dump(dict(base=base[:20], optimistic=opt[:20]), open("out/zipline_train.json", "w"), indent=1, default=float)
