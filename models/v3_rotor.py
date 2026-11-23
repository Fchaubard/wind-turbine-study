"""Machine v3 rotor: 10 m, 3 rigid laminated-wood blades. BEM with Prandtl tip/root loss and Buhl high-induction correction, thick low-Re airfoil polar (assumed, NACA 44xx-like, roughened).
Blade: straight-taper chord and linear twist so it can be cut from planks. Sizes thickness for stress. Writes out/v3_rotor.json."""
import json, math
import numpy as np
RHO, B, R, RIN = 1.18, 3, 5.0, 0.55
E_W, RHO_W, F_ALLOW, F_FAT = 11e9, 560.0, 28e6, 7e6   # laminated pine, epoxy; allowable static and fully reversed fatigue stress (assumed, conservative)
def polar(a, tc=.18):
    d = math.degrees(a); stall = 11.0; k = 1 + .6 * max(tc - .18, 0) / .12
    cl = .42 + .10 * d if d < stall else max(.42 + .10 * stall - .025 * (d - stall), .75) if d < 35 else 1.1 * math.sin(2 * a)
    if d < -8: cl = -.4 + .03 * (d + 8)
    cd = (.016 + .00035 * (d - 2)**2) * k if abs(d) < stall else .09 + 1.7 * math.sin(a)**2
    return cl, cd
def bem(geo, lam, n=32):
    rs = np.linspace(RIN, R * .985, n); dr = rs[1] - rs[0]; ct = cq = 0.0; dT = []
    for r in rs:
        c, th, tc = geo(r); sig = B * c / (2 * math.pi * r); lr = lam * r / R; a, ap = .3, .01
        for _ in range(120):
            phi = math.atan2(1 - a, lr * (1 + ap)); s, co = math.sin(phi), math.cos(phi)
            if abs(s) < 1e-4: s = 1e-4
            ft = 2 / math.pi * math.acos(min(1, math.exp(-B * (R - r) / (2 * r * abs(s))))); fr = 2 / math.pi * math.acos(min(1, math.exp(-B * (r - RIN * .8) / (2 * r * abs(s))))); F = max(ft * fr, .02)
            cl, cd = polar(phi - th, tc); cn = cl * co + cd * s; ctg = cl * s - cd * co; K = sig * cn / (4 * F * s * s)
            CTl = sig * (1 - a)**2 * cn / (s * s)
            if CTl <= .96 * F: an = K / (1 + K)
            else: an = (18 * F - 20 - 3 * math.sqrt(max(CTl * (50 - 36 * F) + 12 * F * (3 * F - 4), 0))) / (36 * F - 50)
            apn = sig * ctg / (4 * F * s * co - sig * ctg) if abs(4 * F * s * co - sig * ctg) > 1e-5 else ap
            a2, ap2 = .7 * a + .3 * min(max(an, -.2), 1.2), .7 * ap + .3 * min(max(apn, -.3), .6)
            if abs(a2 - a) + abs(ap2 - ap) < 1e-5: a, ap = a2, ap2; break
            a, ap = a2, ap2
        W2 = (1 - a)**2 + (lr * (1 + ap))**2; fn = sig * W2 * cn * r * dr * 2 * math.pi / (math.pi * R * R); ft_ = sig * W2 * ctg * r * dr * 2 * math.pi / (math.pi * R * R)
        ct += fn; cq += ft_ * r / R; dT.append(fn)
    return lam * cq, ct, rs, np.array(dT)
def geometry(cr, ct_, tw_r, tw_t, tr=.13, tt=.04):
    def g(r):
        x = (r - RIN) / (R - RIN); c = cr + (ct_ - cr) * x; t = tr + (tt - tr) * x; return c, math.radians(tw_r + (tw_t - tw_r) * x), min(max(t / c, .12), .45)
    return g
CONE = math.radians(5.0)
def blade(g, v, lam, G=9.81):
    cp, ct, rs, dT = bem(g, lam); dr = rs[1] - rs[0]; A = math.pi * R * R; Fi = dT * .5 * RHO * v * v * A / B; om = lam * v / R
    c = np.array([g(r)[0] for r in rs]); t = c * np.array([g(r)[2] for r in rs]); Af = .68 * c * t; S = .11 * c * t * t; Se = .11 * t * c * c; I = .036 * c * t**3; m = Af * RHO_W * dr
    M = np.array([np.sum(Fi[i:] * (rs[i:] - rs[i])) for i in range(len(rs))]); Mg = np.array([np.sum(m[i:] * G * (rs[i:] - rs[i])) for i in range(len(rs))]); Nc = np.array([np.sum(m[i:] * om * om * rs[i:]) for i in range(len(rs))])
    th = np.cumsum(M / (E_W * I)) * dr; sf = M / S + Nc / Af + Mg / Se
    return dict(mass=float(m.sum()), vol=float((Af * dr).sum()), sig=float(sf.max()), at=float(rs[int(sf.argmax())]), tip=float(th.sum() * dr), Mroot=float(M[0]), fat=float((.3 * M / S + Mg / Se).max()))
if __name__ == "__main__":
    best = None; n = 0
    for tr in (.11, .13, .15, .18, .22):
        for tt in (.035, .05, .065):
            for cr in (.40, .50, .60, .70):
                for ctp in (.12, .16, .20):
                    g0 = geometry(cr, ctp, 12, -2, tr, tt); b = blade(g0, 17.0, 7.0)
                    if F_ALLOW / b["sig"] < 1.5 or b["fat"] > F_FAT or b["tip"] > .9: continue
                    for twr in (6, 9, 12, 16, 20):
                        for twt in (-4, -2, 0, 2):
                            g = geometry(cr, ctp, twr, twt, tr, tt); cp, l = max((bem(g, x, 16)[0], x) for x in (5, 6, 7, 8)); n += 1
                            score = cp - .35 * b["vol"]
                            if best is None or score > best[0]: best = (score, cr, ctp, twr, twt, tr, tt, cp, l, b)
    _, cr, ctp, twr, twt, tr, tt, cp, l, b = best; g = geometry(cr, ctp, twr, twt, tr, tt); LS = np.arange(1.5, 11.01, .25); CP, CT = zip(*[bem(g, x)[:2] for x in LS]); CP, CT = np.array(CP), np.array(CT); il = int(CP.argmax())
    print(f"{n} blades passed; chord {cr}->{ctp} m, thick {tr*1000:.0f}->{tt*1000:.0f} mm, twist {twr}->{twt}: Cp {CP[il]:.3f} at TSR {LS[il]:.2f}, CT {CT[il]:.2f}; volume {b['vol']*1000:.0f} L, {b['mass']:.0f} kg each, 17 m/s stress {b['sig']/1e6:.1f} MPa, tip bends {b['tip']*1000:.0f} mm")
    json.dump(dict(R=R, r_in=RIN, B=B, chord=(cr, ctp), twist=(twr, twt), thick=(tr, tt), tsr=LS.tolist(), cp=CP.tolist(), ct=CT.tolist(), peak_cp=float(CP[il]), peak_tsr=float(LS[il])), open("out/v3_rotor.json", "w"), indent=1)
