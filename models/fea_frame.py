"""
3D frame FEA (Euler-Bernoulli 12-DOF beams + tension-only cables) of the
windsock support structure, with automatic member sizing.

Structure ("bicycle-wheel" mouth):
  * mouth ring  : steel CHS, R = 63 m, 48 nodes, centre at hub height H
  * spoke hub   : 8-node hub ring (r = 4 m) on the axial boom, 60 m upwind
  * spokes      : 48 cross-laced Dyneema/steel cables hub -> ring (tension only)
  * axial boom  : CHS along the sock axis (inside the dead-air sock), hub -> nacelle at x = 126
  * tower       : tapered CHS at x = 40, ground -> boom
Loads come from the membrane FEA reactions (fea_membrane.json).
"""
import json, math
import numpy as np

E, Gm, RHO_S = 210e9, 81e9, 7850.0
FY = 355e6
SIG_ALLOW = FY / 1.1                # factored loads, material factor 1.1
H = 72.0
R = 63.0
NR = 48
X_HUB, X_TOWER, X_NAC = -60.0, 0.0, 126.0
G = 9.81


def chs(Do, t):
    Di = Do - 2 * t
    A = math.pi / 4 * (Do**2 - Di**2)
    I = math.pi / 64 * (Do**4 - Di**4)
    return dict(A=A, Iy=I, Iz=I, J=2 * I, W=I / (Do / 2), D=Do, t=t)


def cable(dia):
    A = math.pi / 4 * dia**2 * 0.75
    return dict(A=A, Iy=1e-12, Iz=1e-12, J=1e-12, W=1e-12, D=dia, t=dia / 2)


def build(sec):
    nodes, elems = [], []
    def add(p):
        nodes.append(np.array(p, float)); return len(nodes) - 1
    ring = [add([0, R * math.cos(2 * math.pi * i / NR), H + R * math.sin(2 * math.pi * i / NR)]) for i in range(NR)]
    for i in range(NR):
        elems.append(dict(a=ring[i], b=ring[(i + 1) % NR], g="ring"))
    boom_x = [X_HUB, -30, X_TOWER, 40, 80, X_NAC]
    boom = [add([x, 0, H]) for x in boom_x]
    for i in range(len(boom) - 1):
        elems.append(dict(a=boom[i], b=boom[i + 1], g="boom"))
    NH = 16
    hubs = []
    for bx, lace in ((X_HUB, 0), (40.0, 1)):         # front hub: radial spokes; rear hub (inside the sock): laced for torsion
        bn = boom[boom_x.index(bx)]
        hub = [add([bx, 8 * math.cos(2 * math.pi * i / NH), H + 8 * math.sin(2 * math.pi * i / NH)]) for i in range(NH)]
        for i, h in enumerate(hub):
            elems.append(dict(a=bn, b=h, g="hubarm"))
            elems.append(dict(a=h, b=hub[(i + 1) % NH], g="hubarm"))
        for i in range(NR):
            hidx = (round(i * NH / NR) + (lace if i % 2 else -lace)) % NH
            elems.append(dict(a=hub[hidx], b=ring[i], g="spoke"))
        hubs += hub
    hub = hubs
    tz = np.linspace(0, H, 7)
    tower = [add([X_TOWER, 0, z]) for z in tz[:-1]] + [boom[boom_x.index(X_TOWER)]]
    for i in range(len(tower) - 1):
        elems.append(dict(a=tower[i], b=tower[i + 1], g=f"tower{i}"))
    # rear mast at the nozzle: rides a circular yaw rail (front tower = yaw pivot)
    mz = np.linspace(0, H, 4)
    mast = [add([X_NAC, 0, z]) for z in mz[:-1]] + [boom[-1]]
    for i in range(len(mast) - 1):
        elems.append(dict(a=mast[i], b=mast[i + 1], g="mast"))
    return np.array(nodes), elems, dict(ring=ring, boom=boom, hub=hub, tower=tower, mast=mast)


def k_local(L, s):
    A, Iy, Iz, J = s["A"], s["Iy"], s["Iz"], s["J"]
    k = np.zeros((12, 12))
    def put(i, j, v): k[i, j] += v; k[j, i] += v if i != j else 0
    ea = E * A / L; gj = Gm * J / L
    for (i, j, v) in [(0, 0, ea), (6, 6, ea), (0, 6, -ea), (3, 3, gj), (9, 9, gj), (3, 9, -gj)]:
        put(i, j, v)
    for (Iv, d, r, sgn) in [(Iz, 1, 5, 1), (Iy, 2, 4, -1)]:
        c = E * Iv / L**3
        put(d, d, 12 * c); put(d + 6, d + 6, 12 * c); put(d, d + 6, -12 * c)
        put(r, r, 4 * c * L**2); put(r + 6, r + 6, 4 * c * L**2); put(r, r + 6, 2 * c * L**2)
        put(d, r, sgn * 6 * c * L); put(d, r + 6, sgn * 6 * c * L)
        put(d + 6, r, -sgn * 6 * c * L); put(d + 6, r + 6, -sgn * 6 * c * L)
    return k


def transform(pa, pb):
    ex = pb - pa; L = np.linalg.norm(ex); ex /= L
    ref = np.array([0, 0, 1.0]) if abs(ex[2]) < 0.95 else np.array([1.0, 0, 0])
    ey = np.cross(ref, ex); ey /= np.linalg.norm(ey); ez = np.cross(ex, ey)
    lam = np.array([ex, ey, ez])
    T = np.zeros((12, 12))
    for i in range(4):
        T[3 * i:3 * i + 3, 3 * i:3 * i + 3] = lam
    return T, L


def solve(nodes, elems, sec, loads, fixed_nodes, active):
    n = len(nodes); K = np.zeros((6 * n, 6 * n))
    cache = []
    for e, act in zip(elems, active):
        s = sec[e["g"]]
        if e["g"] == "spoke" and not act:
            s = dict(s, A=s["A"] * 1e-6)
        T, L = transform(nodes[e["a"]], nodes[e["b"]])
        kl = k_local(L, s)
        kg = T.T @ kl @ T
        idx = np.r_[6 * e["a"]:6 * e["a"] + 6, 6 * e["b"]:6 * e["b"] + 6]
        K[np.ix_(idx, idx)] += kg
        cache.append((T, kl, idx, L, s))
    free = np.ones(6 * n, bool)
    for fn in fixed_nodes:
        free[6 * fn:6 * fn + 6] = False
    # cables have no rotational stiffness at ring/hub nodes, but ring/hub beams cover those DOFs.
    u = np.zeros(6 * n)
    u[free] = np.linalg.solve(K[np.ix_(free, free)], loads[free])
    res = []
    for (T, kl, idx, L, s) in cache:
        fl = kl @ (T @ u[idx])
        N = -fl[0]                                     # +tension
        M = max(math.hypot(fl[4], fl[5]), math.hypot(fl[10], fl[11]))
        res.append(dict(N=fl[6], M=M, L=L))
    reac = K @ u - loads
    return u, res, reac


def run(lc, sec, mem):
    nodes, elems, ids = build(sec)
    n = len(nodes)
    F = np.zeros(6 * n)
    # self weight (factor 1.1) lumped to element ends
    for e in elems:
        s = sec[e["g"]]
        L = np.linalg.norm(nodes[e["b"]] - nodes[e["a"]])
        rho = 975 if e["g"] == "spoke" else RHO_S
        w = s["A"] * L * rho * G * 1.1 / 2
        F[6 * e["a"] + 2] -= w; F[6 * e["b"] + 2] -= w
    F[6 * ids["boom"][-1] + 2] -= 25e3 * G * 1.1     # nozzle + small turbine + nacelle
    if lc == "operating":
        rx = np.array(mem["mouth_node_reactions_design_N"])        # (96,3) force from support on fabric
        for j in range(len(rx)):
            ring_node = ids["ring"][(j * NR // len(rx)) % NR]
            F[6 * ring_node:6 * ring_node + 3] += -rx[j] * 1.35      # wind load factor 1.35
        noz = np.array(mem["cases"][1]["nozzle_reaction_N"])
        F[6 * ids["boom"][-1]:6 * ids["boom"][-1] + 3] += -noz * 1.35
        qd = 0.5 * 1.225 * (15 * 1.35) ** 2
    else:                                                          # storm: sock furled onto the boom
        qd = 0.5 * 1.225 * 50.0**2
        for b0, b1 in zip(ids["boom"][1:-1], ids["boom"][2:]):     # furled fabric bundle ~2.5 m dia, Cd 1.2
            L = abs(nodes[b1][0] - nodes[b0][0])
            f = 1.35 * qd * 1.2 * 2.5 * L / 2
            F[6 * b0 + 1] += f; F[6 * b1 + 1] += f                  # wind along +y (side-on worst)
        for e in elems:                                             # member drag, side-on wind (+y)
            pa, pb = nodes[e["a"]], nodes[e["b"]]
            d = pb - pa; L = np.linalg.norm(d); dn = d / L
            proj = math.sqrt(max(0.0, 1 - dn[1] ** 2))
            f = 1.35 * qd * (0.7 if e["g"] != "spoke" else 1.2) * sec[e["g"]]["D"] * L * proj / 2
            F[6 * e["a"] + 1] += f; F[6 * e["b"] + 1] += f
    # tower drag in both cases
    for t0, t1 in zip(ids["tower"][:-1], ids["tower"][1:]):
        g = [e for e in elems if e["a"] == t0 and e["b"] == t1][0]["g"]
        f = 1.35 * qd * 0.7 * sec[g]["D"] * (H / 6) / 2
        dirn = 0 if lc == "operating" else 1
        F[6 * t0 + dirn] += f; F[6 * t1 + dirn] += f
    # pretensioned spokes (bicycle wheel): linear spokes + self-equilibrated pretension case.
    active = [True] * len(elems)
    u, res, reac = solve(nodes, elems, sec, F, [ids["tower"][0], ids["mast"][0]], active)
    sp_min = min(r["N"] for e, r in zip(elems, res) if e["g"] == "spoke")
    T0 = max(0.0, -sp_min) * 1.25 + 30e3
    Fp = np.zeros_like(F)
    for e in elems:
        if e["g"] == "spoke":
            d = nodes[e["b"]] - nodes[e["a"]]; d /= np.linalg.norm(d)
            Fp[6 * e["a"]:6 * e["a"] + 3] += T0 * d; Fp[6 * e["b"]:6 * e["b"] + 3] -= T0 * d
    up, resp, _ = solve(nodes, elems, sec, Fp, [ids["tower"][0], ids["mast"][0]], active)
    u = u + up
    res = [dict(N=r["N"] + rp["N"] + (T0 if e["g"] == "spoke" else 0), M=r["M"] + rp["M"], L=r["L"])
           for e, r, rp in zip(elems, res, resp)]
    util = []
    for e, r, act in zip(elems, res, active):
        s = sec[e["g"]]
        if e["g"] == "spoke":
            sig = max(r["N"], 0) / s["A"]
            util.append(sig / (3.5e9 / 2.5))   # Dyneema SK78 cable, SF 2.5 on break (with load factors)
        else:
            sig = abs(r["N"]) / s["A"] + r["M"] / s["W"]
            # local shell buckling knock-down for thin CHS (D/t): EN 1993-1-6 style rough factor
            kb = min(1.0, 1.3 - 0.0025 * s["D"] / s["t"])
            util.append(sig / (SIG_ALLOW * max(kb, 0.5)))
    base = ids["tower"][0]
    Mbase = math.hypot(reac[6 * base + 3], reac[6 * base + 4])
    return dict(nodes=nodes, elems=elems, ids=ids, u=u, res=res, util=util, active=active, T0=T0,
                Mbase=Mbase, Fbase=reac[6 * base:6 * base + 3])


def masses(sec, nodes, elems):
    m = {}
    for e in elems:
        L = np.linalg.norm(nodes[e["b"]] - nodes[e["a"]])
        rho = 975 if e["g"] == "spoke" else RHO_S
        grp = "tower" if e["g"].startswith("tower") else e["g"]
        m[grp] = m.get(grp, 0) + sec[e["g"]]["A"] * L * rho / 1e3
    return m


def main():
    mem = json.load(open("out/fea_membrane.json"))
    tower_D = np.linspace(6.0, 3.5, 6)
    sec = dict(ring=chs(1.6, 0.012), boom=chs(8.0, 0.012), hubarm=chs(1.0, 0.02), mast=chs(2.5, 0.02), spoke=cable(0.04))
    for i, Dt in enumerate(tower_D):
        sec[f"tower{i}"] = chs(Dt, 0.02)
    hist = []
    for itn in range(30):
        rs = [run("operating", sec, mem), run("storm", sec, mem)]
        nodes, elems = rs[0]["nodes"], rs[0]["elems"]
        umax = {}
        for r in rs:
            for e, u_ in zip(elems, r["util"]):
                umax[e["g"]] = max(umax.get(e["g"], 0), u_)
        hist.append({k: round(v, 3) for k, v in umax.items()})
        done = all(0.6 < v <= 0.9 for v in umax.values())
        for g, u_ in umax.items():
            s = sec[g]
            f = (u_ / 0.8) ** 0.7
            if g == "spoke":
                sec[g] = cable(max(0.012, s["D"] * math.sqrt(f)))
            else:
                t_new = s["t"] * f
                D_new = s["D"] * (max(t_new / 0.06, 1.0)) ** 0.5    # grow diameter once wall hits 60 mm
                sec[g] = chs(D_new, float(np.clip(t_new, 0.008, 0.06)))
        if done:
            break
    rs = [run("operating", sec, mem), run("storm", sec, mem)]
    nodes, elems = rs[0]["nodes"], rs[0]["elems"]
    m = masses(sec, nodes, elems)
    # ring in-plane buckling (conservative, ignoring spoke support): w_cr = 3EI/R^3
    ring_N = max(abs(r["N"]) for e, r in zip(elems, rs[0]["res"]) if e["g"] == "ring")
    w_cr = 3 * E * sec["ring"]["Iz"] / R**3
    w_act = ring_N / R
    # spoke-supported ring: buckling between spokes as arch with n = NR/2 waves: w_cr ~ (n^2-1) EI/R^3
    w_cr_sp = (NR**2 / 4 - 1) * E * sec["ring"]["Iz"] / R**3
    M_hawt = 1.35 * 0.80e6 * 90 + 2.0e6 * 9.81 * 0      # rated thrust x hub height, factored
    out = dict(
        sections={k: {kk: float(vv) for kk, vv in v.items()} for k, v in sec.items()},
        sizing_history=hist,
        ring_mass_t=m["ring"], spoke_mass_t=m["spoke"] + m["hubarm"] + m["boom"] + m["mast"], boom_mass_t=m["boom"],
        tower_mass_t=m["tower"], mast_mass_t=m["mast"], masses_t=m,
        base_moment_MNm={"operating": rs[0]["Mbase"] / 1e6, "storm_furled": rs[1]["Mbase"] / 1e6},
        hawt_base_moment_MNm=M_hawt / 1e6,
        base_moment_ratio_vs_hawt=max(rs[0]["Mbase"], rs[1]["Mbase"]) / M_hawt,
        max_disp_m={"operating": float(np.abs(rs[0]["u"].reshape(-1, 6)[:, :3]).max()),
                    "storm_furled": float(np.abs(rs[1]["u"].reshape(-1, 6)[:, :3]).max())},
        ring_compression_MN=ring_N / 1e6,
        ring_buckling_factor_no_spokes=w_cr / w_act, ring_buckling_factor_spoke_supported=w_cr_sp / w_act,
        spoke_pretension_kN={"operating": rs[0]["T0"] / 1e3, "storm": rs[1]["T0"] / 1e3},
        max_util={"operating": max(rs[0]["util"]), "storm_furled": max(rs[1]["util"])},
        hawt_tower_mass_t=347.5,
    )
    # geometry + utilization for 3D viewer
    out["viz"] = dict(nodes=nodes.tolist(), elems=[[e["a"], e["b"], e["g"], float(u)] for e, u in zip(elems, np.maximum(rs[0]["util"], rs[1]["util"]))])
    json.dump(out, open("out/fea_frame.json", "w"), indent=1)
    print(json.dumps({k: v for k, v in out.items() if k not in ("viz", "sections")}, indent=1))
    print(json.dumps(out["sections"], indent=0))


if __name__ == "__main__":
    main()
