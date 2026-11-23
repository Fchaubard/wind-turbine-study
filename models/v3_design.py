"""Machine v3 sizing: blade stress/deflection along span, then a 3D frame FEA of tripod + head at 12 wind directions for each leg section and hub height, plus energy and cost. Picks the cheapest energy design that passes."""
import json, math, io, contextlib, sys
import numpy as np
with contextlib.redirect_stdout(io.StringIO()):
    import sail_fea as F, zoo4 as Z4
import v3_rotor as Rt
RT = json.load(open("out/v3_rotor.json")); FX, G, RHO, FY, E = 18.5, 9.81, 1.18, 250e6, 200e9; LS, CPc, CTc = map(np.array, (RT["tsr"], RT["cp"], RT["ct"])); R = RT["R"]; A = math.pi * R * R; LP = RT["peak_tsr"]; CP = RT["peak_cp"]; CTP = float(np.interp(LP, LS, CTc))
geo = Rt.geometry(RT["chord"][0], RT["chord"][1], RT["twist"][0], RT["twist"][1], RT["thick"][0], RT["thick"][1]); CPU = min(CP, .38)          # energy uses Cp capped at .38: hand-built blades rarely reach clean BEM
def blade(v=17.0, lam=None): return Rt.blade(geo, v, lam or LP)
BL = {v: blade(v) for v in (8, 12, 17)}; RUN = blade(12.0, float(LS[np.where(CPc > 0)[0].max()]))
for v, b in BL.items(): print(f"blade {v} m/s: stress {b['sig']/1e6:.1f} MPa at r={b['at']:.1f} (SF {Rt.F_ALLOW/b['sig']:.1f}), tip bends {b['tip']*1000:.0f} mm, root moment {b['Mroot']/1000:.1f} kN·m, mass {b['mass']:.0f} kg")
print(f"runaway 12 m/s: {RUN['sig']/1e6:.1f} MPa; working fatigue stress {BL[8]['fat']/1e6:.1f} MPa vs {Rt.F_FAT/1e6:.0f} allowable")
# leg: od, wall, MXN per metre (estimates for Sch 40 black pipe, galvanised and painted on site)
LEGS = {"73 mm x 1.2 post tube": (.073, .0012, 545 / 3.05), "2-1/2 in Sch 40": (.0730, .00516, 520), "3 in Sch 40": (.0889, .00549, 680), "4 in Sch 40": (.1143, .00602, 960)}
HEAD = F.tube_props(.1143, .00602); BR = F.tube_props(.0483, .0037)
F.SEC.update(head=HEAD, brace=dict(BR, I_real=BR["I"], I=BR["I"] * .01, J=BR["J"] * .01)); FOOT = 2.0
def run(od, w, hub, nbr, cases):
    F.SEC["leg"] = F.tube_props(od, w); az = hub - .25; zs = [az * (k + 1) / (nbr + 1) for k in range(nbr)]; rtip = FOOT * max(az - (hub - R), 0) / az; over = round(rtip + .30 + max(BL[17]["tip"] - R * math.sin(Rt.CONE), 0), 2); res = []
    for name, v, st in cases:
        W = dict(y=9e9, b=9e9, g=""); pull = down = 0.0; hubm = 0.0
        for yd in range(0, 360, 30):
            yaw = math.radians(yd); N, Bm = [], []
            def nd(p): N.append(np.array(p, float)); return len(N) - 1
            apx = np.array([0, 0, az]); ap = nd(apx); feet = []; rings = {z: [] for z in zs}
            for a in np.radians((90, 210, 330)):
                f = np.array([FOOT * math.cos(a), FOOT * math.sin(a), 0.0]); fn = nd(f); feet.append(fn); pv = fn
                for z in zs: m = nd(f + (apx - f) * z / az); rings[z].append(m); Bm.append((pv, m, "leg", "leg")); pv = m
                Bm.append((pv, ap, "leg", "leg"))
            for r in rings.values():
                for i, j in ((0, 1), (1, 2), (2, 0)): Bm.append((r[i], r[j], "brace", "brace"))
            n = np.array([math.cos(yaw), math.sin(yaw), 0]); top = nd([0, 0, hub]); Bm.append((ap, top, "head", "yaw post")); h = nd(N[top] - n * over); Bm.append((top, h, "head", "head beam")); tl = nd(N[top] + n * 4.0); Bm.append((top, tl, "head", "tail boom"))
            Fv = np.zeros(len(N) * 6); q = .5 * RHO * v * v
            for i, j, s, g_ in Bm:
                L = np.linalg.norm(N[j] - N[i]); wg = F.SEC[s]["A"] * 7850 * L * G / 2; Fv[6 * i + 2] -= wg; Fv[6 * j + 2] -= wg
                if g_ in ("leg", "brace", "yaw post"): d = q * 1.2 * F.SEC[s]["od"] * L / 2 * n; Fv[6 * i:6 * i + 3] += d; Fv[6 * j:6 * j + 3] += d
            rm = 3 * BL[8]["mass"] + 45; Fv[6 * h + 2] -= rm * G; Fv[6 * top + 2] -= 60 * G; Fv[6 * tl + 2] -= 25 * G
            T = CTP * q * A if st == "run" else q * 1.3 * 3 * .34 * (R - .55); Fv[6 * h:6 * h + 3] += n * T
            if st == "run": Fv[6 * h + 3:6 * h + 6] += n * min(CP / LP * q * A * R, 900.0)
            if st == "park": Fv[6 * tl:6 * tl + 3] += n * q * 1.2 * 1.5
            U, ten, cache, Rr = F.solve(np.array(N), Bm, [], {f: (0, 1, 2) for f in feet}, Fv)
            for (i, j, s, g_), (dof, Tm, kl, L) in zip(Bm, cache):
                fl = kl @ (Tm @ U[dof]); S = F.SEC[s]; Nx = -fl[0]; Mm = max(math.hypot(fl[4], fl[5]), math.hypot(fl[10], fl[11])); sig = abs(Nx) / S["A"] + Mm / S["S"]; c = max(-Nx, 0)
                W["y"] = min(W["y"], FY / max(sig, 1)); bk = math.pi**2 * E * S.get("I_real", S["I"]) / L**2 / c if c > 1 else 999
                if bk < W["b"]: W["b"] = bk
                if FY / max(sig, 1) <= W["y"] + 1e-9 or bk <= W["b"] + 1e-9: W["g"] = g_
            rz = [Rr[6 * f + 2] for f in feet]; pull = max(pull, max(-min(rz), 0)); down = max(down, max(rz)); hubm = max(hubm, np.linalg.norm(U[6 * h:6 * h + 3]))
        res.append(dict(name=name, v=v, sf=min(W["y"], W["b"]), y=W["y"], b=W["b"], where=W["g"], pull_kg=pull / G, down_kg=down / G, hub_mm=hubm * 1000))
    return res, over
CASES = [("8 m/s working", 8, "run"), ("12 m/s, furl fails", 12, "run"), ("17 m/s, furl fails", 17, "run"), ("25 m/s, furled and braked", 25, "park"), ("35 m/s, parked", 35, "park"), ("45 m/s, parked", 45, "park")]
def energy(hub, cap, s=1.0):
    d = dict(hub=hub, yaw="free", tf=1.0); h = Z4.hist(hub, "free", 1.0); v = Z4.VG * s; eta = .95 * .84 * .95
    P = np.minimum(np.maximum(CPU * .75 * .5 * RHO * v**3 * A - 14 * LP * v / R, 0) * eta, cap); return float(P @ h) * .97
rows = []
for hub in (8.5, 10.0, 12.0):
    for nm, (od, w, mxm) in LEGS.items():
        for nbr in (1, 2, 3):
            r, over = run(od, w, hub, nbr, CASES); s = {c["name"]: c for c in r}
            ok = s["12 m/s, furl fails"]["sf"] >= 2 and s["17 m/s, furl fails"]["sf"] >= 1.25 and s["25 m/s, furled and braked"]["sf"] >= 1.25
            legm = 3 * math.hypot(hub - .25, FOOT); tw = legm * mxm / FX + nbr * 3 * 2.2 * 75 / FX
            rows.append(dict(hub=hub, leg=nm, nbr=nbr, over=over, ok=ok, tower_usd=tw, cases=r))
            print(f"hub {hub:4.1f} {nm:22s} braces {nbr}: {'PASS' if ok else 'fail'} SF 12:{s['12 m/s, furl fails']['sf']:.2f} 17:{s['17 m/s, furl fails']['sf']:.2f} 25:{s['25 m/s, furled and braked']['sf']:.2f} 45:{s['45 m/s, parked']['sf']:.2f} ({s['17 m/s, furl fails']['where']}) pull {s['17 m/s, furl fails']['pull_kg']:.0f} kg | steel ${tw:.0f}", flush=True)
json.dump(dict(rows=rows, blade={str(k): v for k, v in BL.items()}, run=RUN, cp=CP, tsr=LP, ctp=CTP, e={str(h): {str(c): energy(h, c) for c in (1200, 2000, 3000)} for h in (8.5, 10., 12.)}), open("out/v3_design.json", "w"), indent=1, default=float)
print(json.dumps({h: {c: round(energy(h, c)) for c in (1200, 2000, 3000)} for h in (8.5, 10., 12.)}))
