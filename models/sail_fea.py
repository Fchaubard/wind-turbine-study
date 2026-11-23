"""Structural FEA of the Punta Mita sail windmill: 3D frame (12-DOF beam elements) with tension-only cables.
Geometry comes from the same parameter file as the CAD model. Load cases use the thrust and torque from the
whole-system simulation (out/sail_opt.json). Reports member stresses, cable tensions, buckling, anchor loads, deflection."""
import json, math
import numpy as np
from cad_params import P

E, Gs, RHO_S, FY, G0 = 200e9, 77e9, 7850.0, 230e6, 9.81


def tube_props(od, wall):
    idia = od - 2 * wall; A = math.pi / 4 * (od**2 - idia**2); I = math.pi / 64 * (od**4 - idia**4)
    return dict(A=A, I=I, J=2 * I, S=I / (od / 2), od=od)

SEC = dict(pole=tube_props(P["pole_od"], P["pole_wall"]), spar=tube_props(P["spar_od"], P["spar_wall"]),
           arm=dict(A=math.pi / 4 * 0.04**2, I=math.pi / 64 * 0.04**4, J=math.pi / 32 * 0.04**4, S=math.pi / 32 * 0.04**3, od=0.04))
CAB = dict(guy=dict(EA=100e9 * 11.2e-6, cap=1360 * G0, name="3/16 in steel cable"), stay=dict(EA=3e9 * 31e-6, cap=4500.0, name="6.3 mm polyester rope (break load assumed 4.5 kN)"))


def build():
    N, B, C = [], [], []                                  # nodes, beams (i, j, sec, group), cables (i, j, kind, name)
    def node(p): N.append(np.array(p, float)); return len(N) - 1
    def beam(i, j, sec, grp): B.append((i, j, sec, grp))
    zs = [0.0, P["pole_seg"], P["prop_top_z"], P["guy_top_z"], P["hub_z"], P["pole_h"]]
    pole = [node((0, 0, z)) for z in zs]
    for a, b in zip(pole[:-1], pole[1:]): beam(a, b, "pole", "pole")
    pb = node((P["prop_base_x"], 0, 0)); pmid = node((P["prop_base_x"] / 2, 0, P["prop_top_z"] / 2))
    beam(pb, pmid, "pole", "prop"); beam(pmid, pole[2], "pole", "prop")
    hub = node((P["hub_x"], 0, P["hub_z"])); beam(pole[4], hub, "arm", "nacelle")
    bow = node((P["hub_x"] - P["bowsprit_len"], 0, P["hub_z"])); beam(hub, bow, "spar", "bowsprit")
    load_nodes, tips, dirs = [], [], []
    for i in range(P["n_sails"]):
        a = 2 * math.pi * i / P["n_sails"] + math.pi / 2; c = P["cone"]
        d = np.array([-math.sin(c), math.cos(c) * math.cos(a), math.cos(c) * math.sin(a)])
        h = N[hub]; n1 = node(h + d * 0.65 * P["R"]); n2 = node(h + d * P["R"])
        beam(hub, n1, "spar", "spar"); beam(n1, n2, "spar", "spar"); load_nodes.append(n1); tips.append(n2)
        dirs.append(np.array([0.0, -math.sin(a), math.cos(a)]))        # tangential direction in the rotor plane
        C.append((bow, n2, "stay", f"stay {i+1}"))
        if P.get("stay_mid"):
            C.append((bow, n1, "stay", f"mid stay {i+1}"))
    anchors = {}
    for az in P["guy_az"]:
        a = math.radians(az)
        for nm, pn, r in (("top", pole[3], P["guy_top_r"]), ("joint", pole[1], P["guy_mid_r"])):
            g = node((r * math.cos(a), r * math.sin(a), 0)); anchors[f"{nm} guy {az:.0f}°"] = g
            C.append((pn, g, "guy", f"{nm} guy {az:.0f}°"))
    fixed = {pole[0]: (0, 1, 2, 5), pb: (0, 1, 2)}
    for g in anchors.values(): fixed[g] = (0, 1, 2, 3, 4, 5)
    return np.array(N), B, C, fixed, dict(pole=pole, pb=pb, hub=hub, bow=bow, load=load_nodes, tips=tips, dirs=dirs, anchors=anchors)


def beam_k(p0, p1, s):
    L = np.linalg.norm(p1 - p0); x = (p1 - p0) / L
    ref = np.array([0, 0, 1.0]) if abs(x[2]) < 0.95 else np.array([1.0, 0, 0])
    y = np.cross(ref, x); y /= np.linalg.norm(y); z = np.cross(x, y)
    R3 = np.vstack([x, y, z]); T = np.zeros((12, 12))
    for k in range(4): T[3 * k:3 * k + 3, 3 * k:3 * k + 3] = R3
    A, I, J = s["A"], s["I"], s["J"]; k = np.zeros((12, 12))
    a = E * A / L; t = Gs * J / L; b1, b2, b3, b4 = 12 * E * I / L**3, 6 * E * I / L**2, 4 * E * I / L, 2 * E * I / L
    for i, j, v in ((0, 0, a), (0, 6, -a), (6, 6, a), (3, 3, t), (3, 9, -t), (9, 9, t),
                    (1, 1, b1), (1, 5, b2), (1, 7, -b1), (1, 11, b2), (5, 5, b3), (5, 7, -b2), (5, 11, b4), (7, 7, b1), (7, 11, -b2), (11, 11, b3),
                    (2, 2, b1), (2, 4, -b2), (2, 8, -b1), (2, 10, -b2), (4, 4, b3), (4, 8, b2), (4, 10, b4), (8, 8, b1), (8, 10, b2), (10, 10, b3)):
        k[i, j] = v; k[j, i] = v
    return T.T @ k @ T, T, k, L


def solve(N, B, C, fixed, F):
    n = len(N) * 6; active = [True] * len(C)
    for _ in range(12):
        K = np.zeros((n, n)); cache = []
        for (i, j, sec, grp) in B:
            kg, T, kl, L = beam_k(N[i], N[j], SEC[sec]); dof = np.r_[6 * i:6 * i + 6, 6 * j:6 * j + 6]
            K[np.ix_(dof, dof)] += kg; cache.append((dof, T, kl, L))
        for a, (i, j, kind, nm) in zip(active, C):
            if not a: continue
            d = N[j] - N[i]; L = np.linalg.norm(d); u = d / L; kk = CAB[kind]["EA"] / L * np.outer(u, u)
            di, dj = np.r_[6 * i:6 * i + 3], np.r_[6 * j:6 * j + 3]
            K[np.ix_(di, di)] += kk; K[np.ix_(dj, dj)] += kk; K[np.ix_(di, dj)] -= kk; K[np.ix_(dj, di)] -= kk
        fx = sorted(6 * nd + d for nd, ds in fixed.items() for d in ds); free = np.setdiff1d(np.arange(n), fx)
        Kff = K[np.ix_(free, free)] + np.eye(len(free)) * 1e-3
        U = np.zeros(n); U[free] = np.linalg.solve(Kff, F[free])
        ten = []
        for (i, j, kind, nm) in C:
            d = N[j] - N[i]; L = np.linalg.norm(d); u = d / L
            ten.append(CAB[kind]["EA"] / L * float(u @ (U[6 * j:6 * j + 3] - U[6 * i:6 * i + 3])))
        new = [(t > 0) if a else False for a, t in zip(active, ten)]
        # a slack cable may re-engage if its ends move apart
        new = [bool(t > 0) for t in ten]
        if new == active: break
        active = new
    Rr = K @ U - F
    return U, [t if a else 0.0 for a, t in zip(active, ten)], cache, Rr


def run():
    N, B, C, fixed, M = build()
    opt = json.load(open("out/sail_opt.json"))["pick"]; ops = {int(o["v"]): o for o in opt["ops"]}
    cad = json.load(open("out/cad/sail_windmill.json"))
    cases = [("Dead load, no wind", 0.0, 0.0, 1.0), ("7 m/s, working (reef point)", ops[7]["thrust"], ops[7]["Q"], 1.0),
             ("12 m/s gust, sails still set", ops[12]["thrust"], ops[12]["Q"], 1.0), ("17 m/s squall, sails still set (worst case)", ops[12]["thrust"] * (17 / 12) ** 2, ops[12]["Q"] * (17 / 12) ** 2, 1.0),
             ("17 m/s from behind, sails reefed", -250.0, 0.0, 1.0)]
    out = dict(cases=[], sections={k: {a: float(b) for a, b in v.items()} for k, v in SEC.items()})
    for name, T, Q, gf in cases:
        F = np.zeros(len(N) * 6)
        for (i, j, sec, grp) in B:                              # self-weight
            w = SEC[sec]["A"] * RHO_S * np.linalg.norm(N[j] - N[i]) * G0 * gf / 2; F[6 * i + 2] -= w; F[6 * j + 2] -= w
        F[6 * M["hub"] + 2] -= (4.5 + cad["group_mass_kg"]["sails"]) * G0             # hub discs, bolts, sails
        F[6 * M["pole"][4] + 2] -= cad["group_mass_kg"]["drive"] * G0                 # bicycle drivetrain + hub motor
        for ln, d in zip(M["load"], M["dirs"]):
            F[6 * ln + 0] += T / P["n_sails"]; F[6 * ln:6 * ln + 3] += d * Q / (P["n_sails"] * 0.65 * P["R"])
        U, ten, cache, Rr = solve(N, B, C, fixed, F)
        worst = {}
        for (i, j, sec, grp), (dof, Tm, kl, L) in zip(B, cache):
            f = kl @ (Tm @ U[dof]); s = SEC[sec]
            Nax = -f[0]; Mmax = max(math.hypot(f[4], f[5]), math.hypot(f[10], f[11]))
            sig = abs(Nax) / s["A"] + Mmax / s["S"]
            if grp not in worst or sig > worst[grp]["stress_MPa"] * 1e6:
                worst[grp] = dict(stress_MPa=sig / 1e6, SF=FY / max(sig, 1.0), axial_N=Nax, moment_Nm=Mmax)
        def euler(I, L): return math.pi**2 * E * I / L**2
        comp = {g: max(0.0, -min((-(kl @ (Tm @ U[dof]))[0]) for (i, j, s_, grp), (dof, Tm, kl, L) in zip(B, cache) if grp == g)) for g in ("pole", "prop", "bowsprit")}
        buck = dict(pole=euler(SEC["pole"]["I"], P["prop_top_z"]) / max(comp["pole"], 1.0), prop=euler(SEC["pole"]["I"], math.hypot(P["prop_base_x"], P["prop_top_z"])) / max(comp["prop"], 1.0),
                    bowsprit=euler(SEC["spar"]["I"], P["bowsprit_len"]) / max(comp["bowsprit"], 1.0))
        cab = {}
        for (i, j, kind, nm), t in zip(C, ten):
            k = "stays" if kind == "stay" else nm
            if k not in cab or t > cab[k]["tension_N"]: cab[k] = dict(tension_N=t, SF=CAB[kind]["cap"] / max(t, 1.0))
        react = {"pole foot": Rr[6 * M["pole"][0]:6 * M["pole"][0] + 3].tolist(), "back-prop foot": Rr[6 * M["pb"]:6 * M["pb"] + 3].tolist()}
        for nm, g in M["anchors"].items(): react[nm] = Rr[6 * g:6 * g + 3].tolist()
        tipd = max(np.linalg.norm(U[6 * t:6 * t + 3]) for t in M["tips"]); tipx = max(U[6 * t] for t in M["tips"])
        res = dict(name=name, thrust_N=T, torque_Nm=Q, worst=worst, buckling_SF=buck, compression_N=comp, cables=cab, reactions_N=react,
                   tip_deflection_m=float(tipd), tip_downwind_m=float(tipx), hub_deflection_m=float(np.linalg.norm(U[6 * M["hub"]:6 * M["hub"] + 3])),
                   pole_top_deflection_m=float(np.linalg.norm(U[6 * M["pole"][5]:6 * M["pole"][5] + 3])),
                   joint_moment_Nm=float(max(math.hypot((kl @ (Tm @ U[dof]))[10], (kl @ (Tm @ U[dof]))[11]) for (i, j, s_, grp), (dof, Tm, kl, L) in zip(B, cache) if grp == "pole" and j == M["pole"][1])))
        out["cases"].append(res)
        print(f"\n{name}: thrust {T:.0f} N, torque {Q:.0f} N·m")
        for g, w in worst.items(): print(f"   {g:9s} stress {w['stress_MPa']:6.1f} MPa  SF {w['SF']:5.1f}  (axial {w['axial_N']:7.0f} N, moment {w['moment_Nm']:6.0f} N·m)")
        print("   buckling SF:", {k: round(v, 1) for k, v in buck.items()}, "| compression N:", {k: round(v) for k, v in comp.items()})
        print("   cables:", {k: f"{v['tension_N']:.0f} N (SF {v['SF']:.0f})" for k, v in cab.items()})
        print("   reactions [x, y, z] N:", {k: [round(a) for a in v] for k, v in react.items()})
        print(f"   tip deflection {tipd*1000:.0f} mm ({tipx*1000:.0f} mm downwind), hub {res['hub_deflection_m']*1000:.0f} mm, pole top {res['pole_top_deflection_m']*1000:.0f} mm, pole joint moment {res['joint_moment_Nm']:.0f} N·m")
    json.dump(out, open("out/sail_fea.json", "w"), indent=1, default=float)


def summary(out):
    c12, c17 = out["cases"][2], out["cases"][3]
    def minsf(c): return min(min(w["SF"] for w in c["worst"].values()), min(c["buckling_SF"].values()))
    return dict(sf12=minsf(c12), sf17=minsf(c17), spar17=c17["worst"]["spar"]["SF"], pole17=c17["worst"]["pole"]["SF"], prop_buck17=c17["buckling_SF"]["prop"],
                uplift12=-c12["reactions_N"]["pole foot"][2], uplift17=-c17["reactions_N"]["pole foot"][2], prop_down17=c17["reactions_N"]["back-prop foot"][2], prop_horiz17=-c17["reactions_N"]["back-prop foot"][0])


if __name__ == "__main__":
    import sys, io, contextlib
    if len(sys.argv) > 1 and sys.argv[1] == "sweep":
        for stay_mid in (False, True):
            for bx, tz in ((2.6, 5.5), (2.2, 5.7), (3.0, 5.3), (3.4, 5.05)):
                for wall in (0.0012,):
                    P.update(prop_base_x=bx, prop_top_z=tz, stay_mid=stay_mid)
                    with contextlib.redirect_stdout(io.StringIO()):
                        run()
                    s = summary(json.load(open("out/sail_fea.json")))
                    print(f"prop foot {bx} m back, top at {tz} m, mid stays {stay_mid}: min SF 12 m/s {s['sf12']:.1f} | 17 m/s {s['sf17']:.2f} (spar {s['spar17']:.1f}, pole {s['pole17']:.1f}, prop buckling {s['prop_buck17']:.1f}) "
                          f"| pole-foot uplift {s['uplift12']:.0f} / {s['uplift17']:.0f} N | prop foot down {s['prop_down17']:.0f} N, sideways {s['prop_horiz17']:.0f} N")
    else:
        run()
