"""
2D lattice-Boltzmann CFD (D2Q9, BGK + Smagorinsky) of a windsock / funnel
concentrator with an actuator-disk "turbine" at the throat.

Question it answers: if a funnel with mouth width d feeds a turbine of
width d/10, does the turbine see (anything like) the power of an open
turbine of width d?

Cases
  open_d    : open actuator of width d            (the conventional big rotor)
  open_d10  : open actuator of width d/10         (small rotor, no funnel)
  funnel    : funnel d -> d/10, actuator at throat
  funnel_dif: funnel d -> d/10, actuator at throat, then 2.5x diffuser
The actuator is a momentum sink F = -k*rho*ux; power = -sum(F*u).
Each run sweeps one k; runner.py sweeps k and takes the best (max power).

Usage: python lbm_cfd.py <case> <k> [steps]
"""
import sys, json, os
os.environ.setdefault("OMP_NUM_THREADS", "1")
import numpy as np

NX, NY = 600, 320
D = 60                      # mouth width (cells)
U0 = 0.08                   # inflow velocity (lattice units)
TAU0 = 0.51
CS = 0.17                   # Smagorinsky constant
XM = 170                    # x of the mouth / actuator plane
YC = NY // 2

c = np.array([[0, 0], [1, 0], [0, 1], [-1, 0], [0, -1], [1, 1], [-1, 1], [-1, -1], [1, -1]])
w = np.array([4/9] + [1/9]*4 + [1/36]*4)
opp = [0, 3, 4, 1, 2, 7, 8, 5, 6]


def feq(rho, ux, uy):
    rho = rho.astype(np.float32); ux = ux.astype(np.float32); uy = uy.astype(np.float32)
    cu = 3 * (c[:, 0, None, None] * ux + c[:, 1, None, None] * uy)
    usq = 1.5 * (ux**2 + uy**2)
    return (rho * w[:, None, None].astype(np.float32) * (1 + cu + 0.5 * cu**2 - usq)).astype(np.float32)


def line_mask(mask, x0, y0, x1, y1, th=1.5):
    X, Y = np.meshgrid(np.arange(NX), np.arange(NY), indexing="ij")
    px, py = x1 - x0, y1 - y0
    L2 = px * px + py * py
    t = np.clip(((X - x0) * px + (Y - y0) * py) / L2, 0, 1)
    dist = np.hypot(X - (x0 + t * px), Y - (y0 + t * py))
    mask |= dist <= th


def geometry(case):
    solid = np.zeros((NX, NY), bool)
    act = np.zeros((NX, NY), bool)
    dt = D // 10
    if case == "open_d":
        act[XM:XM + 2, YC - D // 2:YC + D // 2] = True
    elif case == "open_d10":
        act[XM:XM + 2, YC - dt // 2:YC + dt // 2] = True
    elif case in ("funnel", "funnel_dif"):
        L = D                       # funnel length = mouth width (cone half-angle ~24 deg)
        xt = XM + L
        for s in (-1, 1):
            line_mask(solid, XM, YC + s * (D / 2 + 1.5), xt, YC + s * (dt / 2 + 1.5))
            line_mask(solid, xt, YC + s * (dt / 2 + 1.5), xt + 12, YC + s * (dt / 2 + 1.5))
            if case == "funnel_dif":
                de = 2.5 * dt
                line_mask(solid, xt + 12, YC + s * (dt / 2 + 1.5), xt + 12 + 6 * dt, YC + s * (de / 2 + 1.5))
        act[xt + 4:xt + 6, YC - dt // 2:YC + dt // 2 + 1] = True
        act &= ~solid
    return solid, act


def run(case, k, steps=8000, avg_from=6000, save_field=False):
    solid, act = geometry(case)
    rho = np.ones((NX, NY))
    ux = np.full((NX, NY), U0); uy = np.zeros((NX, NY))
    ux[solid] = 0
    f = feq(rho, ux, uy)
    f_in = feq(np.ones((1, NY)), np.full((1, NY), U0), np.zeros((1, NY)))[:, 0, :]
    P_acc, n_acc, mdot_acc = 0.0, 0, 0.0
    ux_acc = np.zeros((NX, NY)); uy_acc = np.zeros((NX, NY))
    for it in range(steps):
        rho = f.sum(0)
        jx = (f * c[:, 0, None, None]).sum(0); jy = (f * c[:, 1, None, None]).sum(0)
        # actuator force (implicit-ish so large k stays stable): F = -k rho ux
        Fx = np.zeros_like(rho)
        uxa = jx[act] / rho[act]
        Fx[act] = -k * rho[act] * uxa / (1 + 0.5 * k)
        ux = (jx + 0.5 * Fx) / rho; uy = jy / rho
        ux[solid] = 0; uy[solid] = 0
        fe = feq(rho, ux, uy)
        fneq = f - fe
        Pxx = (fneq * (c[:, 0]**2)[:, None, None]).sum(0)
        Pyy = (fneq * (c[:, 1]**2)[:, None, None]).sum(0)
        Pxy = (fneq * (c[:, 0] * c[:, 1])[:, None, None]).sum(0)
        Q = np.sqrt(2 * (Pxx**2 + Pyy**2 + 2 * Pxy**2))
        tau = 0.5 * (TAU0 + np.sqrt(TAU0**2 + 18 * CS**2 * Q / rho))
        f = f - fneq / tau
        f += (w[:, None, None] * 3 * c[:, 0, None, None]) * Fx * (1 - 0.5 / tau)
        # bounce-back for solids (fullway)
        fs = f[:, solid]
        f[:, solid] = fs[opp]
        # stream
        for i in range(9):
            f[i] = np.roll(np.roll(f[i], c[i, 0], 0), c[i, 1], 1)
        # boundaries: inflow equilibrium left, top/bottom free stream, outflow zero-gradient
        f[:, 0, :] = f_in
        f[:, :, 0] = f_in[:, :1]; f[:, :, -1] = f_in[:, :1]
        f[:, -1, :] = f[:, -2, :]
        if it >= avg_from:
            P_acc += -(Fx[act] * ux[act]).sum()
            n_acc += 1
            ux_acc += ux; uy_acc += uy
            mdot_acc += (rho[act] * ux[act]).sum() / 2.0   # actuator is 2 cells thick
        if not np.isfinite(f[1, XM, YC]):
            return {"case": case, "k": k, "diverged": True}
    P = P_acc / n_acc
    P_ref = 0.5 * 1.0 * U0**3 * D      # wind power through the mouth width d (per unit depth)
    out = {"case": case, "k": k, "P": P, "Cp_vs_mouth_d": P / P_ref,
           "mdot_actuator": mdot_acc / n_acc, "mdot_freestream_through_d": U0 * D, "diverged": False}
    if save_field:
        np.savez_compressed(f"out/lbm/field_{case}_{k}.npz", ux=ux_acc / n_acc, uy=uy_acc / n_acc, solid=solid, act=act)
    return out


if __name__ == "__main__":
    case, k = sys.argv[1], float(sys.argv[2])
    steps = int(sys.argv[3]) if len(sys.argv) > 3 else 9000
    save = True
    r = run(case, k, steps=steps, avg_from=int(steps * 0.65), save_field=save)
    os.makedirs("out/lbm", exist_ok=True)
    with open(f"out/lbm/{case}_{k}.json", "w") as fh:
        json.dump(r, fh)
    print(json.dumps(r))
