"""Final check of the CAD geometry of v3: frame FEA (true overhang, tail section, gyroscopic yaw moment), tower and blade natural frequencies against 1P/3P, main shaft fatigue, blade-root bolts, pad tipping."""
import json, math, io, contextlib, os
import numpy as np, scipy.linalg as SL
with contextlib.redirect_stdout(io.StringIO()):
    import sail_fea as F
import v3_rotor as Rt
C = json.load(open("out/cad3/v3.json")); RT = json.load(open("out/v3_rotor.json")); D = json.load(open("out/v3_design.json"))
G, RHO, FY, E = 9.81, 1.18, 250e6, 200e9; R = 5.0; A = math.pi * R * R; LP, CTP, CP = RT["peak_tsr"], D["ctp"], RT["peak_cp"]; HUB, OV, NBR, FOOT = float(os.environ.get("V3_HUB", C["hub"])), float(os.environ.get("V3_OV", C["over"])), int(os.environ.get("V3_NBR", C["nbr"])), 2.0; AZ = HUB - .25
LEG = {"2-1/2 in Sch 40": (.0730, .00516), "3 in Sch 40": (.0889, .00549), "4 in Sch 40": (.1143, .00602)}[os.environ.get("V3_LEG", C["leg"])]
F.SEC.update(leg=F.tube_props(*LEG), head=F.tube_props(.1413, .00655), tail=F.tube_props(.0730, .00701)); b = F.tube_props(.0483, .0037); F.SEC["brace"] = dict(b, I_real=b["I"], I=b["I"] * .01, J=b["J"] * .01)
geo = Rt.geometry(*RT["chord"], *RT["twist"], *RT["thick"]); BM = Rt.blade(geo, 8, LP)["mass"]; rs = np.linspace(.55, R, 60); dr = rs[1] - rs[0]
c = np.array([geo(min(r, R * .985))[0] for r in rs]); t = c * np.array([geo(min(r, R * .985))[2] for r in rs]); m = .68 * c * t * Rt.RHO_W; I_rot = 3 * float(np.sum(m * rs * rs) * dr)
def frame(yaw):
    N, B = [], []
    def nd(p): N.append(np.array(p, float)); return len(N) - 1
    apx = np.array([0, 0, AZ]); ap = nd(apx); feet = []; zs = [AZ * (k + 1) / (NBR + 1) for k in range(NBR)]; rings = {z: [] for z in zs}
    for a in np.radians((90, 210, 330)):
        f = np.array([FOOT * math.cos(a), FOOT * math.sin(a), 0]); fn = nd(f); feet.append(fn); pv = fn
        for z in zs: q = nd(f + (apx - f) * z / AZ); rings[z].append(q); B.append((pv, q, "leg", "leg")); pv = q
        B.append((pv, ap, "leg", "leg"))
    for r in rings.values():
        for i, j in ((0, 1), (1, 2), (2, 0)): B.append((r[i], r[j], "brace", "brace"))
    n = np.array([math.cos(yaw), math.sin(yaw), 0]); top = nd([0, 0, HUB]); B.append((ap, top, "head", "yaw post")); h = nd(N[top] - n * OV); B.append((top, h, "head", "head beam")); tl = nd(N[top] + n * 3.9); B.append((top, tl, "tail", "tail boom"))
    return np.array(N), B, feet, top, h, tl, n
ROT = 3 * BM + 45; CASES = [("8 m/s working", 8, "run", .5), ("12 m/s, furl fails", 12, "run", .5), ("17 m/s, furl fails", 17, "run", .5), ("25 m/s, furled, braked", 25, "park", 0), ("35 m/s, parked", 35, "park", 0), ("45 m/s, parked", 45, "park", 0)]; out = []
for name, v, st, yr in CASES:
    sfm = 9e9; wh = ""; pull = 0
    for yd in range(0, 360, 30):
        N, B, feet, top, h, tl, n = frame(math.radians(yd)); Fv = np.zeros(len(N) * 6); q = .5 * RHO * v * v
        for i, j, s, g_ in B:
            L = np.linalg.norm(N[j] - N[i]); w = F.SEC[s]["A"] * 7850 * L * G / 2; Fv[6 * i + 2] -= w; Fv[6 * j + 2] -= w
            if g_ in ("leg", "brace", "yaw post"): d = q * 1.2 * F.SEC[s]["od"] * L / 2 * n; Fv[6 * i:6 * i + 3] += d; Fv[6 * j:6 * j + 3] += d
        Fv[6 * h + 2] -= ROT * G; Fv[6 * top + 2] -= 60 * G; Fv[6 * tl + 2] -= 25 * G
        T = CTP * q * A if st == "run" else q * 1.3 * 3 * float(np.sum(c) * dr); Fv[6 * h:6 * h + 3] += n * T; Om = LP * v / R if st == "run" else 0
        if st == "run": Fv[6 * h + 3:6 * h + 6] += n * min(CP / LP * q * A * R, 900.0); Fv[6 * h + 3:6 * h + 6] += np.array([-n[1], n[0], 0]) * I_rot * Om * yr     # gyroscopic moment, yawing at yr rad/s
        else: Fv[6 * tl:6 * tl + 3] += n * q * 1.2 * 2.5
        U, _, cache, Rr = F.solve(N, B, [], {f: (0, 1, 2) for f in feet}, Fv)
        for (i, j, s, g_), (dof, Tm, kl, L) in zip(B, cache):
            fl = kl @ (Tm @ U[dof]); S = F.SEC[s]; Nx = -fl[0]; Mm = max(math.hypot(fl[4], fl[5]), math.hypot(fl[10], fl[11])); sf = FY / max(abs(Nx) / S["A"] + Mm / S["S"], 1); cc = max(-Nx, 0)
            if cc > 1: sf = min(sf, math.pi**2 * E * S.get("I_real", S["I"]) / L**2 / cc)
            if sf < sfm: sfm, wh = sf, g_
        pull = max(pull, max(-min(Rr[6 * f + 2] for f in feet), 0))
    out.append(dict(name=name, v=v, sf=sfm, where=wh, pull_kg=pull / G)); print(f"{name:26s} SF {sfm:5.2f} at {wh:10s} foot pull {pull/G:5.0f} kg")
# tower bending frequency: head on a free yaw bearing, so rotor, head and tail are lumped at the tower top
N, B, feet, top, h, tl, n = frame(0.0); B = [e for e in B if e[3] not in ("head beam", "tail boom")]; nn = len(N) * 6; K = np.zeros((nn, nn)); Mv = np.full(nn, 1e-6)
for i, j, s_, g_ in B:
    kg, *_ = F.beam_k(N[i], N[j], F.SEC[s_]); dof = np.r_[6 * i:6 * i + 6, 6 * j:6 * j + 6]; K[np.ix_(dof, dof)] += kg; mm = F.SEC[s_]["A"] * 7850 * np.linalg.norm(N[j] - N[i]) / 2
    for k in (i, j): Mv[6 * k:6 * k + 3] += mm; Mv[6 * k + 3:6 * k + 6] += mm * .005
Mv[6 * top:6 * top + 3] += ROT + 85; Mv[6 * top + 3:6 * top + 6] += 30.0
fx = sorted(6 * f + d for f in feet for d in (0, 1, 2)) + [6 * h + d for d in range(6)] + [6 * tl + d for d in range(6)] + [6 * top + 5]; fr = np.setdiff1d(np.arange(nn), fx)
vals, vecs = SL.eigh(K[np.ix_(fr, fr)] + 1e-3 * np.eye(len(fr)), np.diag(Mv[fr]), subset_by_index=[0, 11]); idx = {d: k for k, d in enumerate(fr)}; fT = []
for k in range(len(vals)):
    ux, uy = vecs[idx[6 * top], k], vecs[idx[6 * top + 1], k]; rz = max(abs(vecs[idx[6 * q + 5], k]) for q in range(len(N)) if 6 * q + 5 in idx)
    if math.hypot(ux, uy) > .25 * np.abs(vecs[:, k]).max(): fT.append(math.sqrt(abs(vals[k])) / (2 * math.pi))
fT = fT[:2] or [0.0, 0.0]
rpm_max = LP * 6.2 / R * 60 / (2 * math.pi); w = (rs - .55)**2 / (R - .55)**2; ww = 2 / (R - .55)**2; I = .036 * c * t**3; fB = math.sqrt(float(np.sum(Rt.E_W * I * ww**2) * dr / (np.sum(m * w * w) * dr))) / (2 * math.pi)
print(f"tower bending {fT[0]:.2f} Hz; rotor max {rpm_max:.0f} rpm: 1P {rpm_max/60:.2f} Hz, 3P {rpm_max/20:.2f} Hz; blade flap {fB:.2f} Hz")
St = F.SEC["tail"]; fTail = math.sqrt(3 * E * St["I"] / (3.9**3 * (25 + .24 * St["A"] * 7850 * 3.9))) / (2 * math.pi); print(f"tail boom {fTail:.2f} Hz")
hit = [f"{fT[0]:.2f} Hz is within 15% of 1P"] if fT[0] < 1.15 * rpm_max / 60 else []
if fTail < 1.15 * rpm_max / 60: hit.append(f"tail {fTail:.2f} Hz is within 15% of 1P")
# non-rotating trailer-axle spindle (7,000 lb class), 4140 steel: steady bending plus occasional gyroscopic moment
Mb = ROT * G * .20; Mg = I_rot * (LP * 12 / R) * .2; shaft = {}          # hydraulic yaw damper limits yaw rate to 0.2 rad/s
for d in (.04445, .05):
    sb = (Mb + Mg) / (math.pi * d**3 / 32); shaft[d] = sb; print(f"spindle {d*1000:.1f} mm with yaw damper: {sb/1e6:.0f} MPa, SF on 620 MPa yield {620e6/sb:.2f}")
Mr = Rt.blade(geo, 17, LP)["Mroot"]; bolt = Mr / (.40 * 4); bear = 8e6 * .016 * float(RT["thick"][0]); print(f"blade root: {Mr/1000:.1f} kN·m; 8 M16 bolts at 400 mm: {bolt/1000:.1f} kN per bolt; wood bearing capacity {bear/1000:.1f} kN, SF {bear/bolt:.2f}")
T17 = CTP * .5 * RHO * 289 * A; pad = 1.5 * T17 * HUB / (2.0 * G); print(f"pad + machine must weigh at least {pad/1000:.1f} t for SF 1.5 against tipping at 17 m/s (4 x 4 m pad, thickness {pad/(16*2400):.2f} m)")
print("JSON"+json.dumps(dict(hub=HUB,leg=os.environ.get("V3_LEG",C["leg"]),nbr=NBR,f=fT[0],tail=fTail,where={c["name"]:c["where"] for c in out},sf={c["name"]:c["sf"] for c in out},pull=max(c["pull_kg"] for c in out),pad=pad/1000,hit=bool(hit))))
json.dump(dict(cases=out, tail_hz=fTail, tower_hz=list(fT), blade_hz=fB, rpm_max=rpm_max, hit=hit, shaft={str(k): v for k, v in shaft.items()}, I_rot=I_rot, bolt_kN=bolt / 1000, bolt_cap_kN=bear / 1000, pad_t=pad / 1000), open("out/v3_verify.json", "w"), indent=1, default=float)
