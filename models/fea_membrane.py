"""
Nonlinear membrane FEA of the windsock cone (geometrically nonlinear CST
elements, St.Venant-Kirchhoff, tension-field wrinkling, follower pressure),
solved by dynamic relaxation with kinetic damping.

Geometry: cone, mouth R = 63 m (x = 0) -> fabric ends at r = 6.3 m where it
clamps onto a rigid steel nozzle that necks down to the d/100 throat.
Axis = +x (downwind), z = up.  Mouth ring + nozzle edge are pinned; their
reactions are written out for the frame FEA.
"""
import json, math, sys, os
os.environ.setdefault("OMP_NUM_THREADS", "1"); os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
import numpy as np

R, L = 63.0, 126.0
R_IN = 6.3                       # fabric -> rigid nozzle transition
NTH = 96
ET, NU = 800e3, 0.35             # PVC-polyester: E*t ~ 800 kN/m (biaxial avg), Poisson
S0 = 2.0e3                       # prestress N/m
FAB_MASS = 1.05                  # kg/m^2 (Type III/IV)
RHO = 1.225
TAN = (R - 0) / L                # cone: r(x) = R - x*R/L  (apex at x = L)

FABRICS = [  # name, strip tensile strength kN/m (warp), fabricated $/m^2 (assumed from vendor ranges)
    ("PVC-polyester Type I", 60, 22), ("PVC-polyester Type II", 84, 26),
    ("PVC-polyester Type III", 110, 30), ("PVC-polyester Type IV", 150, 36),
    ("PVC-polyester Type V", 180, 42), ("PTFE-glass (heavy)", 160, 95),
    ("UHMWPE/aramid laminate (sail-grade)", 400, 160)]


def mesh():
    rings = [R]
    dth = 2 * math.pi / NTH
    slope = math.hypot(1, 1 / TAN)            # ds/dr along the generator... ds = dr * sqrt(1+(L/R)^2)
    while rings[-1] > R_IN:
        r = rings[-1]
        rings.append(r - r * dth / slope)
    rings[-1] = R_IN
    rings = np.array(rings)
    xs = (R - rings) / TAN
    th = np.arange(NTH) * dth
    X = np.stack([np.repeat(xs, NTH),
                  np.outer(rings, np.cos(th)).ravel(),
                  np.outer(rings, np.sin(th)).ravel()], 1)
    tris = []
    nr = len(rings)
    for i in range(nr - 1):
        for j in range(NTH):
            a, b = i * NTH + j, i * NTH + (j + 1) % NTH
            c, d = a + NTH, b + NTH
            if (i + j) % 2:
                tris += [(a, b, d), (a, d, c)]
            else:
                tris += [(a, b, c), (b, d, c)]
    return X, np.array(tris), nr, xs, rings


def cp_out(xn, cosang, yaw_amp):
    """External pressure on the separated outer cone surface: strong suction at the lip,
    relaxing downstream, plus a yaw/gust asymmetry around the circumference."""
    s = xn / L
    return -0.45 - 0.65 * np.exp(-s / 0.08) + yaw_amp * cosang


def solve(V, yaw_amp=0.25, max_it=16000, tol=3e-4, verbose=False):
    X0, T, nr, xs, rings = mesh()
    n = len(X0)
    qd = 0.5 * RHO * V**2
    # reference (local 2D) shape-function gradients per triangle
    P0 = X0[T]                                   # (ne,3,3)
    e1 = P0[:, 1] - P0[:, 0]; e1 /= np.linalg.norm(e1, axis=1)[:, None]
    nrm = np.cross(P0[:, 1] - P0[:, 0], P0[:, 2] - P0[:, 0])
    A0 = 0.5 * np.linalg.norm(nrm, axis=1); nrm /= (2 * A0)[:, None]
    e2 = np.cross(nrm, e1)
    loc = np.stack([np.einsum("eij,ej->ei", P0 - P0[:, :1], e1), np.einsum("eij,ej->ei", P0 - P0[:, :1], e2)], 2)
    # gradN (ne,3,2):  N_a = alpha + beta.x
    M = np.concatenate([np.ones((len(T), 3, 1)), loc], 2)
    Minv = np.linalg.inv(M)
    G = np.transpose(Minv[:, 1:, :], (0, 2, 1))            # (ne,3,2)
    lam = ET / (1 - NU**2)
    C = lam * np.array([[1, NU, 0], [NU, 1, 0], [0, 0, (1 - NU) / 2]])
    fixed = np.zeros(n, bool); fixed[:NTH] = True; fixed[-NTH:] = True
    # fictitious masses (Barnes): m_i ~ sum Et*A/h^2 * safety
    h = np.sqrt(2 * A0)
    m = np.zeros(n); np.add.at(m, T.ravel(), np.repeat(ET * A0 / h**2, 3) * 2.2)
    x = X0.copy(); v = np.zeros_like(x)
    KE_prev = 0.0
    xn_tri = P0[:, :, 0].mean(1)
    cosang = (P0[:, :, 2].mean(1)) / np.hypot(P0[:, :, 1].mean(1), P0[:, :, 2].mean(1))  # top=+1 (yaw/gust side)
    dp = qd * (1.0 - cp_out(xn_tri, cosang, yaw_amp))       # net outward pressure (inside stagnation Cp=+1)
    def forces(x):
        P = x[T]
        F = np.einsum("eai,eaj->eij", P, G)                 # (ne,3,2) deformation gradient
        Cg = np.einsum("eki,ekj->eij", F, F)
        E = 0.5 * (Cg - np.eye(2))
        Ev = np.stack([E[:, 0, 0], E[:, 1, 1], 2 * E[:, 0, 1]], 1)
        Sv = Ev @ C.T + np.array([S0, S0, 0])
        S = np.stack([np.stack([Sv[:, 0], Sv[:, 2]], 1), np.stack([Sv[:, 2], Sv[:, 1]], 1)], 1)
        # tension field: drop compressive principal stress (wrinkling)
        w_, V_ = np.linalg.eigh(S)
        wr = w_ < 0
        w_ = np.maximum(w_, 0)
        S = np.einsum("eij,ej,ekj->eik", V_, w_, V_)
        fint = -A0[:, None, None] * np.einsum("eij,ejk,eak->eai", F, S, G)
        # follower pressure
        cr = np.cross(P[:, 1] - P[:, 0], P[:, 2] - P[:, 0])           # = 2*area*normal
        # outward normal: our tri ordering gives normals pointing... make them outward (away from axis)
        radial = P.mean(1).copy(); radial[:, 0] = 0
        sgn = np.sign((cr * radial).sum(1))[:, None]
        fp = (dp[:, None] * 0.5 * cr * sgn / 3.0)[:, None, :].repeat(3, 1)
        fg = np.zeros_like(fp); fg[:, :, 2] = -9.81 * FAB_MASS * A0[:, None] / 3
        f = np.zeros((n, 3))
        np.add.at(f, T.ravel(), (fint + fp + fg).reshape(-1, 3))
        return f, w_, wr, F
    ext_scale = (dp * A0).sum()
    for it in range(max_it):
        f, w_, wr, F = forces(x)
        f[fixed] = 0
        res = np.linalg.norm(f) / ext_scale * math.sqrt(n)
        v += f / m[:, None]
        KE = (m[:, None] * v**2).sum()
        if KE < KE_prev:                                  # kinetic damping peak -> reset
            x -= 0.5 * v * 1.0 * 0  # (simple variant: just zero velocity)
            v[:] = 0
            KE = 0
        KE_prev = KE
        x += v
        if verbose and it % 2000 == 0:
            print(it, res, flush=True)
        if it > 500 and res < tol:
            break
    f_full, w_, wr, F = forces(x)
    react = -f_full                                        # reaction = -(unbalanced) at supports
    stretch = np.linalg.norm(F, axis=1)
    # principal membrane forces (Cauchy ~ 2PK for small strain), kN/m
    s1 = w_[:, 1] / 1e3; s2 = w_[:, 0] / 1e3
    disp = np.linalg.norm(x - X0, axis=1)
    return dict(V=V, q=qd, it=it, res=float(res), X0=X0, x=x, T=T, s1=s1, s2=s2, wrinkled=wr.any(1),
                disp=disp, react_mouth=react[:NTH], react_nozzle=react[-NTH:], A0=A0, dp=dp)


def main():
    cases = [("rated 11.4 m/s", 11.4), ("furl limit 15 m/s + 1.35 gust", 15 * 1.35), ("cut-out 25 m/s", 25.0), ("storm 50 m/s (unfurled)", 50.0)]
    out = {"L": L, "R": R, "R_in": R_IN, "Et_kN_m": ET / 1e3, "cases": []}
    from multiprocessing import Pool
    with Pool(4) as pool:
        sols = pool.map(solve, [V for _, V in cases])
    for (name, V), r in zip(cases, sols):
        Fm = r["react_mouth"].sum(0); Fn = r["react_nozzle"].sum(0)
        c = dict(name=name, V=V, q=r["q"], iters=int(r["it"]), residual=r["res"],
                 max_tension_kN_m=float(r["s1"].max()), p99_tension_kN_m=float(np.percentile(r["s1"], 99)),
                 wrinkled_frac=float(r["wrinkled"].mean()), max_disp_m=float(r["disp"].max()),
                 mouth_reaction_N=Fm.tolist(), nozzle_reaction_N=Fn.tolist(),
                 total_drag_on_fabric_MN=float(-(Fm[0] + Fn[0]) / 1e6),
                 ring_inward_line_load_kN_m=float(np.mean(-(r["react_mouth"][:, 1] * r["X0"][:NTH, 1] + r["react_mouth"][:, 2] * r["X0"][:NTH, 2]) / R) / (2 * math.pi * R / NTH) / 1e3 * -1),
                 ring_axial_line_load_kN_m=float(np.mean(r["react_mouth"][:, 0]) / (2 * math.pi * R / NTH) / 1e3))
        print(json.dumps({k: v for k, v in c.items() if "reaction" not in k}), flush=True)
        out["cases"].append(c)
        if V == 15 * 1.35:
            design = r
            # export mesh + stress for 3D viewer (deformed shape, element stress)
            np.savez_compressed("out/fea_membrane_mesh.npz", X0=r["X0"], x=r["x"], T=r["T"], s1=r["s1"], wr=r["wrinkled"])
            out["mouth_node_reactions_design_N"] = r["react_mouth"].tolist()
            out["mouth_node_xyz"] = r["X0"][:NTH].tolist()
    # fabric choice: SF 5 on design case (fabric codes use 4-6 for long-term creep/biaxial/seams)
    need = out["cases"][1]["max_tension_kN_m"] * 5.0
    for nm, strength, price in FABRICS:
        if strength >= need:
            out["fabric_grade"], out["fabric_strength_kN_m"], out["fabric_cost_m2"] = nm, strength, price
            break
    out["required_strength_kN_m_SF5"] = need
    need50 = out["cases"][3]["max_tension_kN_m"] * 2.0
    out["storm_required_strength_kN_m_SF2"] = need50
    out["storm_verdict"] = "fabric survives" if need50 < 180 else "no architectural fabric survives: must furl/drop"
    with open("out/fea_membrane.json", "w") as fh:
        json.dump(out, fh, indent=1)
    print("fabric:", out.get("fabric_grade"), "need", need, "storm need", need50, out["storm_verdict"])


if __name__ == "__main__":
    main()
