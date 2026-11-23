"""3D frame FEA of machine v2 at 12 wind directions, including tower drag and storm cases with sails reefed or removed."""
import json, math, sys
import numpy as np
import sail_fea as F
P = json.load(open("out/cad2/v2.json"))["params"]
for k, v in dict(leg=(P["leg_od"], P["leg_w"]), brace=(P["brace_od"], P["brace_w"]), head=(P["head_od"], P["head_w"]), spar2=(P["spar_od"], P["spar_w"])).items(): F.SEC[k] = F.tube_props(*v)
_b = F.SEC["brace"]; F.SEC["brace"] = dict(_b, I_real=_b["I"], I=_b["I"] * 0.01, J=_b["J"] * 0.01)     # braces are U-bolted: near-pinned ends, so they carry axial load only
RHO, G, FY, E = 1.18, 9.81, 230e6, 200e9; CT = 1025.0 / (0.5 * 1.18 * 144 * 19.63); A = math.pi * P["R"]**2; Qk = .23 * .75 * .5 * RHO * A * P["R"] / 1.4


def build(yaw):
    N, B, C = [], [], []
    def node(p): N.append(np.array(p, float)); return len(N) - 1
    apx = np.array([0, 0, P["apex_z"]]); ap = node(apx); feet = []; rings = {z: [] for z in P["brace_z"]}
    for a in np.radians((90, 210, 330)):
        f = np.array([P["foot_r"] * math.cos(a), P["foot_r"] * math.sin(a), 0.0]); fn = node(f); feet.append(fn); prev = fn
        for z in P["brace_z"]:
            m = node(f + (apx - f) * z / P["apex_z"]); rings[z].append(m); B.append((prev, m, "leg", "leg")); prev = m
        B.append((prev, ap, "leg", "leg"))
    for z, r in rings.items():
        for i, j in ((0, 1), (1, 2), (2, 0)): B.append((r[i], r[j], "brace", "brace"))
    n = np.array([math.cos(yaw), math.sin(yaw), 0.0]); s = np.array([-n[1], n[0], 0.0]); z_ = np.array([0, 0, 1.0])
    top = node([0, 0, P["hub_z"]]); B.append((ap, top, "head", "yaw post"))
    hub = node(N[top] - n * P["overhang"]); B.append((top, hub, "head", "head beam"))
    tail = node(N[top] + n * (P["tail_boom"] + .25)); B.append((top, tail, "head", "tail boom"))
    bow = node(N[hub] - n * P["bow"]); B.append((hub, bow, "spar2", "bowsprit")); load, tang = [], []
    c = P["cone"]
    for i in range(P["n"]):
        a = 2 * math.pi * i / P["n"] + math.pi / 2; d = -math.sin(c) * n + math.cos(c) * (math.cos(a) * s + math.sin(a) * z_)
        m = node(N[hub] + d * .65 * P["R"]); t = node(N[hub] + d * P["R"]); B.append((hub, m, "spar2", "spar")); B.append((m, t, "spar2", "spar")); load.append(m); tang.append(-math.sin(a) * s + math.cos(a) * z_)
        C.append((bow, t, "stay", f"tip stay {i}")); C.append((bow, m, "stay", f"mid stay {i}"))
    fixed = {f: (0, 1, 2) for f in feet}
    return np.array(N), B, C, fixed, dict(feet=feet, hub=hub, top=top, tail=tail, load=load, tang=tang, n=n)


CASES = [("7.8 m/s, working", 7.8, "up"), ("12 m/s gust, sails up", 12.0, "up"), ("17 m/s squall, sails up", 17.0, "up"), ("25 m/s storm, sails reefed", 25.0, "reef"), ("30 m/s, sails removed", 30.0, "bare"), ("35 m/s, sails removed", 35.0, "bare"), ("40 m/s, sails removed", 40.0, "bare"), ("45 m/s hurricane, sails removed", 45.0, "bare")]
out = []
for name, v, st in CASES:
    worst = {}; cab = 0.0; ft = fc = 0.0; tip = 0.0
    for yd in range(0, 360, 30):
        N, B, C, fixed, M = build(math.radians(yd)); Fv = np.zeros(len(N) * 6); nv = M["n"]; q = .5 * RHO * v * v
        for i, j, sec, g_ in B:
            L = np.linalg.norm(N[j] - N[i]); w = F.SEC[sec]["A"] * 7850 * L * G / 2; Fv[6 * i + 2] -= w; Fv[6 * j + 2] -= w
            if g_ in ("leg", "brace", "yaw post"):
                dr = q * 1.2 * F.SEC[sec]["od"] * L / 2 * nv; Fv[6 * i:6 * i + 3] += dr; Fv[6 * j:6 * j + 3] += dr
        Fv[6 * M["hub"] + 2] -= 12 * G; Fv[6 * M["top"] + 2] -= 32 * G; Fv[6 * M["tail"] + 2] -= 14 * G
        T = CT * q * A if st == "up" else q * 1.2 * (8 * P["spar_od"] * 3.25 + (8 * .08 * 2.6 if st == "reef" else 0)); Q = min(Qk * v * v, 600.0) if st == "up" else 0.0
        for ln, t in zip(M["load"], M["tang"]): Fv[6 * ln:6 * ln + 3] += nv * T / P["n"] + t * Q / (P["n"] * .65 * P["R"])
        U, ten, cache, Rr = F.solve(N, B, C, fixed, Fv)
        for (i, j, sec, g_), (dof, Tm, kl, L) in zip(B, cache):
            f = kl @ (Tm @ U[dof]); s = F.SEC[sec]; Nx = -f[0]; Mm = max(math.hypot(f[4], f[5]), math.hypot(f[10], f[11])); sig = abs(Nx) / s["A"] + Mm / s["S"]
            comp = max(-Nx, 0.0); bk = math.pi**2 * E * s.get("I_real", s["I"]) / L**2 / comp if comp > 1 else 999.0
            cr = min(FY / sig, 999.0); W = worst.setdefault(g_, dict(yield_SF=999.0, buckling_SF=999.0))
            W["yield_SF"] = min(W["yield_SF"], cr); W["buckling_SF"] = min(W["buckling_SF"], bk)
        cab = max(cab, max(ten)); rz = [Rr[6 * f + 2] for f in M["feet"]]; ft = max(ft, max(-min(rz), 0.0)); fc = max(fc, max(rz)); tip = max(tip, max(np.linalg.norm(U[6 * n_:6 * n_ + 3]) for n_ in [M["hub"]]))
    mn = min(min(w["yield_SF"], w["buckling_SF"]) for w in worst.values()); wg = min(worst, key=lambda g: min(worst[g]["yield_SF"], worst[g]["buckling_SF"]))
    out.append(dict(name=name, min_SF=mn, where=wg, worst=worst, stay_N=cab, bolt_pull_kg=ft / G, foot_down_kg=fc / G, hub_move_mm=tip * 1000))
    print(f"{name:34s} min SF {mn:5.2f} at {wg:10s} | leg y {worst['leg']['yield_SF']:.1f} b {worst['leg']['buckling_SF']:.1f} | spar {worst['spar']['yield_SF']:.1f} | head {worst['head beam']['yield_SF']:.1f} | brace b {worst['brace']['buckling_SF']:.1f} | stay {cab:.0f} N | bolt {ft/G:.0f} kg | hub moves {tip*1000:.0f} mm")
json.dump(out, open("out/v2_fea.json", "w"), indent=1, default=float)
