"""GIANT WHISK: guyed Darrieus with tension-shaped fabric-sleeve cable blades, generator on the pad, guy cables to anchors beyond the pad. Double-multiple-streamtube aerodynamics with a fixed-pitch symmetric polar,
parabolic blade strips, wind shear, hourly wind, column buckling and fatigue, guy sizing, column frequency vs 1P/2P/3P, itemised parts. Pass criteria match the Dandelion: SF 2 at 12 m/s and 1.25 at 17 m/s with safeties failed."""
import json, math, io, contextlib
import numpy as np
with contextlib.redirect_stdout(io.StringIO()):
    import zoo as Z
RHO, G, E = 1.18, 9.81, 200e9; WS = Z.WS; TH = np.radians(np.linspace(-85, 85, 35)); DTH = TH[1] - TH[0]
def polar(a, cd0, stall=10., clmax=.95):
    d = np.degrees(a); ad = np.abs(d); cl = np.where(ad < stall, .105 * d, np.sign(d) * np.maximum(clmax - .025 * (ad - stall), .55)); cl = np.where(np.abs(cl) > clmax, np.sign(cl) * clmax, cl); cd = np.where(ad < stall, cd0 + .00018 * ad**2, .12 + 1.6 * np.sin(a)**2); return cl, cd
def half(sig, lam, V0, cd0, side):
    a = np.full(len(TH), .12); ct_ = np.cos(TH); st = np.sin(TH) * side
    for _ in range(30):
        Vn = V0 * (1 - a) * ct_; Vt = lam + V0 * (1 - a) * st; W2 = Vn * Vn + Vt * Vt; al = np.arctan2(Vn, Vt); cl, cd = polar(al, cd0); Cn = cl * np.cos(al) + cd * np.sin(al); Ct = cl * np.sin(al) - cd * np.cos(al); CTt = np.maximum(sig / np.pi * (W2 / np.maximum(V0 * V0, 1e-4)) * (Cn * ct_ - Ct * st) / ct_, 0); an = np.where(CTt < .96, .5 * (1 - np.sqrt(np.maximum(1 - CTt, 0))), .4 + (CTt - .96) / 3.2); a = .65 * a + .35 * np.minimum(an, .8)
    Q = float(np.sum(sig / (2 * np.pi) * W2 * Ct) * DTH); Tx = float(np.sum(sig / (2 * np.pi) * W2 * (Cn * ct_ - Ct * st)) * DTH); return Q, Tx, a
def strip(sig, lam, cd0):
    Q1, T1, a = half(sig, lam, 1.0, cd0, 1); V2 = np.maximum(1 - 2 * a.mean(), .1); Q2, T2, _ = half(sig, lam, V2, cd0, -1); return lam * (Q1 + Q2), T1 + T2
def rotor(D, H, B, c, cd0):
    z = (np.arange(14) + .5) / 14; rr = 1 - (2 * z - 1)**2; r = rr * D / 2; dz = H / 14; Af = 2 * r * dz; best = None
    for lam in (2.5, 3, 3.5, 4, 4.5, 5, 6):
        vals = [strip(min(B * c / (2 * max(x, .15)), 1.2), lam * x / (D / 2), cd0) for x in r]; cp = sum(v[0] * a for v, a in zip(vals, Af)) / Af.sum(); ct = sum(v[1] * a for v, a in zip(vals, Af)) / Af.sum()
        if best is None or cp > best[0]: best = (cp, ct, lam)
    return best, float(Af.sum())
PIPE = {"4 in": (.1143, .00602, 52), "6 in": (.1683, .00711, 110), "8 in": (.2191, .00818, 165), "10 in": (.2731, .00927, 230), "12 in": (.3239, .0095, 300)}; GUY = {"3/8": (56e-6, 60e3, 4.), "1/2": (100e-6, 105e3, 6.5), "5/8": (157e-6, 165e3, 9.5), "3/4": (226e-6, 235e3, 13.)}
def props(o, w): i = o - 2 * w; A = math.pi / 4 * (o*o - i*i); I = math.pi / 64 * (o**4 - i**4); return A, I, I / (o / 2)
def energy(cp, A, zc, cap, s=1.0, f=.75):
    v = WS * (zc / 10) ** .14 * s; P = np.minimum(cp * f * .5 * RHO * v**3 * A * .92 * .84 * .95, cap) * (v >= 3.0) * (v <= 14.); return float(P.mean()) * .97 * .95
def size(D, H, B, c, cp, ct, lam, A, ng):
    z0 = 2.5; Lc = H + 1.5; zc = z0 + H / 2; L_b = H * (1 + (8 / 3) * (D / 2 / H)**2) if D / H < 1 else H * 1.25; sa = B * L_b * c * 2; T12 = ct * .5 * RHO * 144 * A; T17 = ct * .5 * RHO * 289 * A; phi = math.radians(40); anchor_r = (z0 + H + .5) / math.tan(phi); gl = (z0 + H + .5) / math.sin(phi); om = lam * 9. / (D / 2); pick = None
    for pn, (o, w, pc) in PIPE.items():
        Ap, Ip, Sp = props(o, w)
        for gn, (Ag, Fg, gc) in GUY.items():
            Tg = T17 / 2 / math.cos(phi) * 1.3 + .12 * Fg; Cc = (Tg + 2 * .12 * Fg) * math.sin(phi) + (B * L_b * (2.0 + c * .9) + Ap * 7850 * Lc) * G + 2 * T17 * .08; Pcr = math.pi**2 * E * Ip / Lc**2; yl = min(Pcr, 250e6 * Ap); M12 = T12 * Lc / 12; sf12 = 1 / ((Cc * 144 / 289 + .5 * .12 * Fg) / yl + M12 / (250e6 * Sp)); sf17 = 1 / (Cc / yl + T17 * Lc / 12 / (250e6 * Sp)); fat = (T12 * (8 / 12)**2 * Lc / 12) / Sp; f1 = math.pi / (2 * Lc * Lc) * math.sqrt(E * Ip / (Ap * 7850 + B * 2.5)); pf = 3 * om / (2 * math.pi)
            if Fg / Tg < 2 or sf12 < 2 or sf17 < 1.25 or fat > 45e6 or f1 < 1.15 * pf: continue
            st = Lc * pc * 1.15 + 3 * gl * gc + 3 * 250; pick = dict(pipe=pn, guy=gn, steel=st, sf12=sf12, sf17=sf17, f1=f1, pf=pf, fat=fat, Tg=Tg, anchor_r=anchor_r, gl=gl); break
        if pick: break
    if not pick: return None
    Q = cp * .5 * RHO * 9**3 * A / om; elec = 518. * ng; blade = 2.5 * (B * L_b * (4 + 3) + sa * 7 * 1.15); drive = 200 + .35 * min(Q, 2 * 1300 * ng / max(om, .1)); bear = 120 + 200 + 60 * (A / 100); erect = 400 + 2 * H * 8; cap = pick["steel"] * 1.15 + elec + blade + drive + bear + erect + 300; wear = 1.6 * sa + 90 + .02 * pick["steel"]; life = cap + wear * 19 + .3 * elec + .5 * blade; return dict(D=D, H=H, B=B, c=c, cp=cp, ct=ct, lam=lam, A=A, ng=ng, zc=zc, cap=cap, life=life, wear=wear, sa=sa, T17=T17, blade=blade, elec=elec, drive=drive, **pick)
if __name__ == "__main__":
    print("VALIDATION: clean airfoil, solidity .15:", round(max(strip(.15, l, .012)[0] for l in (3, 4, 5, 6, 7)), 3), "(published Darrieus peak 0.35-0.42)", flush=True); R = []
    for D in (10, 14, 18, 24, 30):
        for HD in (1.0, 1.3, 1.6):
            H = D * HD
            for B in (2, 3):
                for c in (.3, .45, .6, .8, 1.1):
                    (cp, ct, lam), A = rotor(D, H, B, c, .020)
                    if cp < .05: continue
                    for ng in (1, 2, 3, 5):
                        d = size(D, H, B, c, cp, ct, lam, A, ng)
                        if d: d["W"] = energy(cp, A, d["zc"], 1200 * ng); d["usd"] = d["life"] / (d["W"] * 8.766 * 20 / 1000); d["usd13"] = d["life"] / (energy(cp, A, d["zc"], 1200 * ng, 1.3) * 8.766 * 20 / 1000); R.append(d)
        print("done D", D, len(R), flush=True)
    R.sort(key=lambda r: r["usd"]); json.dump(R[:40], open("out/whisk_rigid.json", "w"), indent=1, default=float)
    for r in R[:7]: print(f"{r['D']}×{r['H']:.0f} m, {r['B']} blades c {r['c']} | {r['A']:.0f} m² Cp {r['cp']:.2f} TSR {r['lam']} | {r['ng']} gens | {r['W']:.0f} W ${r['cap']:,.0f} ${r['usd']:.0f}/MWh (1.3× ${r['usd13']:.0f}) | {r['pipe']} column, {r['guy']} guys to {r['anchor_r']:.0f} m | SF {r['sf12']:.1f}/{r['sf17']:.2f} | col {r['f1']:.1f} Hz vs 3P {r['pf']:.1f}")
