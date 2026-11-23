"""AI search for the best whole flight strategy at each wind speed (cross-entropy method over 9 control parameters), for two kites. Trained on one set of random gusts and judged on unseen flights.
Parameters: figure-8 width, elevation, reel-out factor, turn gain, retract elevation, retract power setting, retract speed, minimum tension held on retract, tension limit."""
import json, time
import numpy as np
import kite_sim as K
LO = np.array([.20, .30, .12, .6, .65, .02, .3, 10., 60.]); HI = np.array([.65, .95, .45, 3.0, 1.35, .45, 3.5, 120., 260.])
def auto(st, c, rng, X):
    n = len(st["az"]); a0, e0, gam, kp, er, pr, vi, Tm, Tx = X.T; Tmax = Tx * c.S; st["phase"] = np.where(st["r"] >= c.rmax, 1., np.where(st["r"] <= c.rmin + 1, 0., st["phase"])); tr = st["phase"] == 0
    st["side"] = np.where(st["az"] > a0, -1., np.where(st["az"] < -a0, 1., st["side"])); aa = np.where(tr, st["side"] * a0 * 1.25, 0.); ae = np.where(tr, e0, er); psi = np.arctan2(st["ve"], st["va"] + 1e-6); pd = np.arctan2(ae - st["el"], (aa - st["az"]) * np.cos(st["el"])); err = K.wrap(pd - psi); A = np.maximum(st["A"] * (1 + c.noise * rng.normal(size=n)), 1.5); m = c.ms * c.S + .011 * st["r"] / 3
    ub = np.clip(2 * m * kp * err / (K.RHO * A * c.S * (c.CLd + (c.CL - c.CLd) * st["pw"])), -c.bmax, c.bmax); over = np.maximum(st["T"] - Tmax, 0) / (.25 * Tmax); short = np.maximum(Tm - st["T"], 0) / max(1., 1.); uv = np.where(tr, gam * A / 5 + over, -(vi + np.minimum(short / 25, 3.)) + over); up = np.where(tr, np.clip(1 - 1.2 * over, .1, 1), np.clip(pr + short / 150, 0, 1)); return ub, up, uv
def run(V, X, c, seed, T):
    rng = np.random.default_rng(seed); n = len(X); st = K.init(n, V, c, rng); st["A"] = np.full(n, 4.)
    for _ in range(int(T / K.DT)): ub, up, uv = auto(st, c, rng, X); K.physics(st, ub, up, uv, c, rng)
    return st
if __name__ != "__main__": raise_guard = True
KITES = {"standard 12 m² (0.55 kg/m²)": dict(S=12., ms=.55, CD=.20), "ultralight 16 m² (0.28 kg/m²)": dict(S=16., ms=.28, CD=.19)}; R = {}; t0 = time.time()
for kn, kw in KITES.items():
    c = K.Cfg(**kw); R[kn] = {}
    for V in (2.5, 3, 3.5, 4, 5, 6, 8, 10):
        rng = np.random.default_rng(int(V * 10)); mu = (LO + HI) / 2; sd = (HI - LO) / 3; elite = None
        for g in range(9):
            P = np.clip(rng.normal(mu, sd, (32, 9)), LO, HI); 
            if elite is not None: P[:4] = elite[:4]
            X = np.repeat(P, 4, 0); s = run(V, X, c, 100 + g, 240.); f = ((s["E"] / 240.) - 900 * (~s["alive"])).reshape(32, 4).mean(1); o = np.argsort(-f); elite = P[o[:7]]; mu = elite.mean(0); sd = elite.std(0) + .03 * (HI - LO)
        X = np.repeat(elite[:1], 256, 0); s = run(V, X, c, 7777, 900.); h = s["tflown"].sum() / 3600; R[kn][str(V)] = dict(survive=float(s["alive"].mean()), crash_h=float((~s["alive"]).sum() / max(h, 1e-3)), W=float(s["E"].sum() / max(s["tflown"].sum(), 1)), params=elite[0].tolist())
        q = R[kn][str(V)]; print(f"{kn[:12]} {V:4.1f} m/s: survive 15 min {q['survive']*100:3.0f}%  {q['crash_h']:6.2f} crashes/h  {q['W']:5.0f} W net  ({time.time()-t0:.0f}s)", flush=True); json.dump(R, open("out/kite_opt.json", "w"), indent=1)
