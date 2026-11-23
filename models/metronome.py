"""METRONOME WING: one wing on a long arm pivoted at the pad, swinging side to side like an upside-down pendulum, pitch flipping at each end, springs returning the energy, generator on the swing axle.
Time-domain strip model with momentum induction on the swept sector, stall polar, pitch flip, spring, gravity, end stops. Structure is sized from the simulated loads: stayed steel spar (buckling, 17 m/s stuck-open, 10^8-cycle fatigue), yaw bearing, spring, and pad weight."""
import json, math, itertools, io, contextlib
import numpy as np
with contextlib.redirect_stdout(io.StringIO()):
    import zoo as Z
RHO, G, E = 1.18, 9.81, 200e9; VS = np.array([2., 3., 4., 5., 6., 7.]); KF = np.array([.1, .2, .35, .6, 1., 1.7, 3.]); DT = .01; NT = 9000; NE = 10
def polar(a, AR):
    x = np.abs(a); st = math.radians(14); cl = np.where(x < st, 5.2 * x, 1.1 * np.abs(np.sin(2 * x)) + .15); cl = np.sign(a) * np.minimum(cl, 1.25); return cl, .03 + cl * cl / (math.pi * .85 * AR) + 1.2 * np.sin(np.minimum(x, 1.57))**2 * (x > st)
def sim(R, r1, c0, th, beta, wn, mw, ms, cap):
    r = r1 + (np.arange(NE) + .5) / NE * (R - r1); dr = (R - r1) / NE; c = c0 * (1 - .57 * (r - r1) / (R - r1)); S = float(np.sum(c) * dr); AR = (R - r1)**2 / S; rc = float(np.sum(c * r) / np.sum(c)); I = mw * rc * rc + ms * R * R / 3; mgr = (mw * rc + ms * R / 2) * G; kt = I * wn * wn + mgr; A = th * (R * R - r1 * r1); U, Kx = np.meshgrid(VS, KF, indexing="ij"); U, Kx = U.ravel(), Kx.ravel(); K = Kx * I * wn; a = np.full(U.shape, .15); bt = math.radians(beta)
    for it in range(3):
        q = np.full(U.shape, .25); w = np.full(U.shape, .1); Pg = Tn = 0.; n = 0; Mf = np.zeros(U.shape); Me = np.zeros(U.shape); Tt = np.zeros(U.shape)
        for s in range(NT):
            ax = U * (1 - a); vt = w[:, None] * r; ph = np.arctan2(ax[:, None], np.abs(vt)); pit = bt * np.tanh(w / .15); al = ph - np.abs(pit)[:, None]; cl, cd = polar(al, AR); Q = .5 * RHO * (ax[:, None]**2 + vt * vt) * c * dr; ft = Q * (cl * np.sin(ph) - cd * np.cos(ph)); fn = Q * (cl * np.cos(ph) + cd * np.sin(ph)); tq = np.sign(w) * np.sum(ft * r, 1); mfl = np.sum(fn * r, 1); thr = np.sum(fn, 1)
            tg = np.clip(K * w, -cap / np.maximum(np.abs(w), .02), cap / np.maximum(np.abs(w), .02)); over = np.maximum(np.abs(q) - th, 0) * np.sign(q); stop = 2e6 * over + 2e4 * w * (over != 0); tor = tq - tg - kt * q + mgr * np.sin(q) - .012 * I * wn * w - stop; ac = tor / I
            if s * DT > 40: Pg = Pg + tg * w; Tn = Tn + thr; n += 1; Mf = np.maximum(Mf, np.abs(mfl)); Me = np.maximum(Me, np.abs(tor) + np.abs(tg) + kt * np.abs(q))
            w = w + ac * DT; q = q + w * DT
        Tm = Tn / n; ct = Tm / (.5 * RHO * U * U * A); an = .5 * (1 - np.sqrt(np.maximum(1 - np.minimum(ct, .96), 0))); a = .5 * a + .5 * np.minimum(an, .45)
    P = (Pg / n).reshape(len(VS), len(KF)); j = P.argmax(1); ix = np.arange(len(VS)); return dict(P=P[ix, j], Mf=(Mf.reshape(P.shape))[ix, j], Me=(Me.reshape(P.shape))[ix, j], T=Tm.reshape(P.shape)[ix, j], A=A, S=S, I=I, kt=kt, a=a.reshape(P.shape)[ix, j])
TUBES = [(.0483, .0037), (.0603, .0039), (.073, .0052), (.0889, .0055), (.1143, .006), (.1683, .0071), (.2191, .0082), (.2731, .0093)]
def size(R, x, th, vf):
    k = np.interp(vf, VS, x["Mf"]); M12 = k * 1.3; M17 = k * (17 / vf)**2; Mfat = float(np.interp(5, VS, x["Mf"])); Me = float(np.interp(vf, VS, x["Me"])); best = None
    for b in (3., 4.5, 6.):
        Ts = M17 / b; Ls = R / 3
        for od, w in TUBES:
            i = od - 2 * w; Ap, Ip = math.pi / 4 * (od*od - i*i), math.pi / 64 * (od**4 - i**4); Sc = Ip / (od / 2); bk = min(math.pi**2 * E * Ip / Ls**2, 250e6 * Ap)
            for nt in (1, 3):
                d = .45 if nt == 3 else od; An, Ib = nt * Ap, (Ip if nt == 1 else 3 * Ip + 2 * Ap * (d / 1.73)**2); Pb = min(math.pi**2 * E * Ib / Ls**2, 250e6 * An); sfat = (Mfat * .25 / (Ib / max(d / 1.5, od / 2)) + Mfat / b / An)
                if Pb / max(Ts, 1) < 1.25 or sfat > 25e6 or Me * .4 / (Ib / max(d / 1.5, od / 2)) > 90e6: continue
                kg = An * 7850 * R; cost = kg * 3.2 + 2 * (R * 1.2) * max(Ts / 90e3, .5) * 6
                if best is None or cost < best["spar_cost"]: best = dict(b=b, od=od, nt=nt, spar_kg=kg, spar_cost=cost, M17=M17, stay=Ts, sfat=sfat)
    return best
def econ(d, x, st, ng, vf, s=1.):
    z = 2 + .55 * d["R"]; v = Z.WS * (z / 10)**.14 * s; Pm = np.interp(v, np.r_[0, VS], np.r_[0, x["P"]]) * (v <= vf); W = float(np.mean(np.minimum(Pm * .75 * .92 * .84, 1200 * ng))) * .92; pad = st["M17"] / (2. * G * 1000); elec = 518 * ng + 150; spring = .5 * x["kt"] * d["th"]**2 / 250 * 3; yaw = 450 * max(st["M17"] / 5e4, .5)**.5; cap = elec + 26 * x["S"] + st["spar_cost"] + yaw + spring + 350 + 100 * max(pad - 10, 0) + 600; wear = x["S"] * 26 / 8 + spring / 5 + 350 / 5 + 90; life = cap + wear * 19 + .3 * elec; return W, cap, life, pad
if __name__ == "__main__":
    n = sim(22, 4, 1.4, 1.19, 7, 1.06, 26, 68, 6000); print("Neon's exact design: Cp at 4 m/s (mech)", round(float(n["P"][2] / (.5 * RHO * 64 * n["A"])), 3), "| flap moment at 4 m/s", round(float(n["Mf"][2] / 1000)), "kNm | at 7 m/s", round(float(n["Mf"][-1] / 1000)), "kNm | P mech", np.round(n["P"]), flush=True); s0 = size(22, n, 1.19, 7.); print("  Neon spar passes real checks with:", s0, flush=True); R = []
    for Rr, c0, th, bt, wn in itertools.product((6, 9, 12, 16, 22), (.5, .8, 1.2), (.7, 1.0, 1.19), (4, 8, 12), (.8, 1.4, 2.2)):
        r1 = max(1.5, .18 * Rr); x = sim(float(Rr), r1, c0 * Rr / 12, th, bt, wn, 1.5 * c0 * Rr / 12 * (Rr - r1) * .8, 2.8 * Rr, 1500 * max(Rr / 6, 1)**2)
        for vf in (6., 7.):
            st = size(float(Rr), x, th, vf)
            if not st: continue
            d = dict(R=Rr, c0=c0, th=th, beta=bt, wn=wn, vf=vf)
            for ng in (1, 2, 4):
                W, cap, life, pad = econ(d, x, st, ng, vf)
                if W > 1: R.append(dict(d, ng=ng, W=W, cap=cap, life=life, usd=life / (W * 8.766 * 20 / 1000), pad=pad, A=x["A"], S=x["S"], cp4=float(x["P"][2] / (.5 * RHO * 64 * x["A"])), **st))
    R.sort(key=lambda r: r["usd"]); json.dump(dict(neon=dict(P=n["P"].tolist(), Mf=n["Mf"].tolist(), A=n["A"], sized=s0), best=R[:25]), open("out/metronome.json", "w"), indent=1, default=float); print(len(R), "passing designs"); seen = set()
    for r in R:
        if r["R"] in seen: continue
        seen.add(r["R"]); print(f"R {r['R']} m | swept {r['A']:.0f} m², wing {r['S']:.1f} m², Cp {r['cp4']:.2f} | {r['W']:.0f} W ${r['cap']:,.0f} ${r['usd']:.0f}/MWh | spar {r['spar_kg']:.0f} kg ({r['nt']}×{r['od']*1000:.0f} mm) | 17 m/s moment {r['M17']/1000:.0f} kNm, pad {r['pad']:.0f} t")
