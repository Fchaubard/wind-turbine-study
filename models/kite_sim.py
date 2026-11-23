"""Tethered pumping-kite flight simulator: 3D point mass on a reeled tether, bank and depower actuators with rate limits, sensor noise, turbulent gusts, shear, slack and crash detection.
Vectorised so thousands of flights run at once. Includes a classical figure-8 autopilot, on which a neural controller can add corrections."""
import numpy as np
RHO, G, DT, NS = 1.18, 9.81, .05, 6
class Cfg:
    def __init__(s, S=12., rmin=60., rmax=140., CL=1.0, CD=.20, CLd=.25, CDd=.12, ms=.55, turb=.15, tau=8., eta_out=.80, eta_in=.85, vrmax=8., noise=.03, delay=.15, bmax=.14):
        s.bmax = bmax; s.Tbreak = 520. * S; s.Tslack = 8.
        s.S, s.rmin, s.rmax, s.CL, s.CD, s.CLd, s.CDd, s.ms, s.turb, s.tau, s.eta_out, s.eta_in, s.vrmax, s.noise, s.delay = S, rmin, rmax, CL, CD, CLd, CDd, ms, turb, tau, eta_out, eta_in, vrmax, noise, delay
def wrap(a): return (a + np.pi) % (2 * np.pi) - np.pi
def init(n, V10, c, rng):
    return dict(az=rng.uniform(-.25, .25, n), el=rng.uniform(.65, .85, n), va=rng.uniform(1, 3, n), ve=rng.uniform(-.5, .5, n), r=np.full(n, c.rmin) + rng.uniform(0, 8, n), vr=np.zeros(n), b=np.zeros(n), pw=np.ones(n), g=rng.normal(0, c.turb, n), alive=np.ones(n, bool), slack=np.zeros(n), phase=np.zeros(n), side=rng.choice([-1., 1.], n), E=np.zeros(n), T=np.zeros(n), V10=np.asarray(V10) * np.ones(n), tflown=np.zeros(n), cb=np.zeros(n), Tpk=np.zeros(n))
def physics(st, ub, up, uv, c, rng):
    n = len(st["az"]); st["g"] += -st["g"] * DT / c.tau + c.turb * np.sqrt(2 * DT / c.tau) * rng.normal(size=n)
    st["cb"] += (np.clip(ub, -c.bmax, c.bmax) - st["cb"]) * min(DT / max(c.delay, DT), 1); st["b"] += np.clip(st["cb"] - st["b"], -.6 * DT, .6 * DT); st["pw"] += np.clip(np.clip(up, 0, 1) - st["pw"], -.9 * DT, .9 * DT); st["vr"] += np.clip(np.clip(uv, -c.vrmax, c.vrmax) - st["vr"], -2.5 * DT, 2.5 * DT)
    h = DT / NS
    for _ in range(NS):
        ca, sa, ce, se = np.cos(st["az"]), np.sin(st["az"]), np.cos(st["el"]), np.sin(st["el"]); p = np.column_stack([ce * ca, ce * sa, se]); eaz = np.column_stack([-sa, ca, np.zeros(n)]); eel = np.column_stack([-se * ca, -se * sa, ce])
        z = np.maximum(st["r"] * se, 1.); Vw = st["V10"] * (z / 10) ** .14 * np.maximum(1 + st["g"], .1); vk = st["vr"][:, None] * p + st["va"][:, None] * eaz + st["ve"][:, None] * eel; Va = np.column_stack([Vw, np.zeros(n), np.zeros(n)]) - vk; A = np.maximum(np.linalg.norm(Va, axis=1), .05); ua = Va / A[:, None]
        l0 = p - np.sum(p * ua, 1)[:, None] * ua; l0 /= np.maximum(np.linalg.norm(l0, axis=1, keepdims=True), 1e-4); side = np.cross(ua, l0); l = np.cos(st["b"])[:, None] * l0 + np.sin(st["b"])[:, None] * side
        CLv = c.CLd + (c.CL - c.CLd) * st["pw"]; CDv = c.CDd + (c.CD - c.CDd) * st["pw"] + .25 * .004 * st["r"] / c.S; q = .5 * RHO * A * A * c.S; m = c.ms * c.S + .011 * st["r"] / 3
        F = (q * CLv)[:, None] * l + (q * CDv)[:, None] * ua; F[:, 2] -= m * G
        Fa, Fe = np.sum(F * eaz, 1), np.sum(F * eel, 1); T = np.sum(F * p, 1) + m * (st["va"]**2 + st["ve"]**2) / st["r"]; te = np.tan(np.clip(st["el"], -1.4, 1.4))
        st["va"] += h * (Fa / m + st["va"] * st["ve"] * te / st["r"] - st["vr"] * st["va"] / st["r"]); st["ve"] += h * (Fe / m - st["va"]**2 * te / st["r"] - st["vr"] * st["ve"] / st["r"]); 
        st["az"] = wrap(st["az"] + h * st["va"] / (st["r"] * np.maximum(ce, .1))); st["el"] = np.clip(st["el"] + h * st["ve"] / st["r"], -.2, 1.5); st["r"] = np.clip(st["r"] + h * st["vr"], c.rmin - 8, c.rmax + 8)
        T = np.maximum(T, 0); Pm = T * st["vr"]; Pe = np.where(Pm > 0, Pm * c.eta_out, Pm / c.eta_in); st["T"] = T; st["Tpk"] = np.maximum(st["Tpk"], T) if _ == NS - 1 else st["Tpk"]; st["slack"] = np.where(T < c.Tslack, st["slack"] + h, 0.); st["E"] += Pe * h * st["alive"]; st["tflown"] += h * st["alive"]
    crash = st["alive"] & ((st["r"] * np.sin(st["el"]) < 5) | (st["slack"] > 2.5) | (np.abs(st["az"]) > 1.45) | (st["Tpk"] > c.Tbreak)); st["alive"] &= ~crash
    for k in ("va", "ve", "vr"): st[k] = np.where(st["alive"], st[k], 0.)
    st["A"] = A
def autopilot(st, c, rng, a0=.42, e0=.55, gamma=.28, kpsi=1.6):
    n = len(st["az"]); st["phase"] = np.where(st["r"] >= c.rmax, 1., np.where(st["r"] <= c.rmin + 1, 0., st["phase"])); tr = st["phase"] == 0
    st["side"] = np.where(st["az"] > a0, -1., np.where(st["az"] < -a0, 1., st["side"])); aim_a = np.where(tr, st["side"] * a0 * 1.25, 0.); aim_e = np.where(tr, e0, .95)
    psi = np.arctan2(st["ve"], st["va"] + 1e-6); psid = np.arctan2(aim_e - st["el"], (aim_a - st["az"]) * np.cos(st["el"])); err = wrap(psid - psi); A = np.maximum(st["A"] * (1 + c.noise * rng.normal(size=n)), 1.5); m = c.ms * c.S + .011 * st["r"] / 3
    ub = np.clip(2 * m * kpsi * err / (RHO * A * c.S * (c.CLd + (c.CL - c.CLd) * st["pw"])), -c.bmax, c.bmax); Tmax = 170 * c.S; vest = A / 5.0; over = np.maximum(st["T"] - Tmax, 0) / (.25 * Tmax)
    uv = np.where(tr, gamma * vest + over, -np.clip(.45 * vest + .6, .8, 3.0) + over); up = np.where(tr, np.clip(1 - 1.2 * over, .1, 1.), .12); return ub, up, uv
def fly(V10, c, T=240., seed=0, n=64, policy=None):
    rng = np.random.default_rng(seed); st = init(n, V10, c, rng); st["A"] = np.full(n, 4.)
    for _ in range(int(T / DT)):
        ub, up, uv = autopilot(st, c, rng)
        if policy is not None: ub, up, uv = policy(st, ub, up, uv, c)
        physics(st, ub, up, uv, c, rng)
    return st
if __name__ == "__main__":
    c = Cfg(); print("autopilot only, 12 m2 kite, 64 flights of 4 min per wind speed at 10 m")
    for V in (2, 3, 4, 5, 6, 8, 10, 12):
        s = fly(V, c, seed=V); W = s["E"] / 240.; print(f" {V:2d} m/s: survived {s['alive'].mean()*100:4.0f}%  mean power incl. crashes {W.mean():7.0f} W  mean flight {s['tflown'].mean():4.0f} s  peak tension {s['T'].max():.0f} N")
