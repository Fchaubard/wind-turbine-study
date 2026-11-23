"""Train a neural controller on top of the classical autopilot with evolution strategies, with randomised wind, gusts and sensor noise. Then test on unseen flights: survival, crashes per flying hour, power, by wind speed."""
import json, time
import numpy as np
import kite_sim as K
NI, NH, NO = 12, 12, 3; DIM = NI * NH + NH + NH * NO + NO
def unpack(P):
    n = len(P); i = 0; a = P[:, i:i + NI * NH].reshape(n, NI, NH); i += NI * NH; b = P[:, i:i + NH]; i += NH; c = P[:, i:i + NH * NO].reshape(n, NH, NO); i += NH * NO; return a, b, c, P[:, i:]
def obs(st, c):
    psi = np.arctan2(st["ve"], st["va"] + 1e-6); return np.column_stack([st["az"] / .6, (st["el"] - .6) / .4, np.sin(psi), np.cos(psi), st["A"] / 15 - 1, st["T"] / (170 * c.S) - .5, (st["r"] - c.rmin) / (c.rmax - c.rmin) - .5, st["phase"] - .5, st["vr"] / 4, st["pw"] - .5, st["b"] / c.bmax, st["side"]])
def make_policy(P, idx):
    a, b, d, e = unpack(P); A, B, D, E = a[idx], b[idx], d[idx], e[idx]
    def pol(st, ub, up, uv, c):
        h = np.tanh(np.einsum("nij,ni->nj", A, obs(st, c)) + B); o = np.tanh(np.einsum("nij,ni->nj", D, h) + E); return ub + o[:, 0] * c.bmax * .6, up + o[:, 1] * .35, uv + o[:, 2] * 1.5
    return pol
WINDS = np.array([3.5, 4., 5., 6., 8., 10.]); BASE = np.array([250., 400., 800., 1100., 1600., 2500.])
def fitness(P, seed, c, T=100.):
    npop = len(P); nw = len(WINDS); rep = 3; idx = np.repeat(np.arange(npop), nw * rep); V = np.tile(np.repeat(WINDS, rep), npop); b = np.tile(np.repeat(BASE, rep), npop); rng = np.random.default_rng(seed); st = K.init(len(idx), V, c, rng); st["A"] = np.full(len(idx), 4.); pol = make_policy(P, idx)
    for _ in range(int(T / K.DT)):
        ub, up, uv = K.autopilot(st, c, rng); ub, up, uv = pol(st, ub, up, uv, c); K.physics(st, ub, up, uv, c, rng)
    r = st["E"] / T / b - 2.5 * (~st["alive"]); return np.bincount(idx, r, npop) / (nw * rep)
def evaluate(P1, c, seed=999, T=600., n=192):
    out = {}
    for V in (2.5, 3, 3.5, 4, 5, 6, 7, 8, 10, 12):
        res = {}
        for name, p in (("auto", None), ("ai", P1)):
            rng = np.random.default_rng(seed + int(V * 10)); st = K.init(n, V, c, rng); st["A"] = np.full(n, 4.); pol = make_policy(p[None], np.zeros(n, int)) if p is not None else None
            for _ in range(int(T / K.DT)):
                ub, up, uv = K.autopilot(st, c, rng)
                if pol: ub, up, uv = pol(st, ub, up, uv, c)
                K.physics(st, ub, up, uv, c, rng)
            hrs = st["tflown"].sum() / 3600; crash = int((~st["alive"]).sum()); res[name] = dict(survive=float(st["alive"].mean()), crash_per_h=crash / max(hrs, 1e-3), W_flying=float(st["E"].sum() / max(st["tflown"].sum(), 1)))
        out[V] = res; print(f"{V:4.1f} m/s | autopilot: survive {res['auto']['survive']*100:3.0f}% {res['auto']['crash_per_h']:6.1f} crashes/h {res['auto']['W_flying']:5.0f} W | AI: survive {res['ai']['survive']*100:3.0f}% {res['ai']['crash_per_h']:6.1f} crashes/h {res['ai']['W_flying']:5.0f} W", flush=True)
    return out
if __name__ == "__main__":
    c = K.Cfg(); rng = np.random.default_rng(11); th = np.zeros(DIM); th[:NI * NH] = rng.normal(0, .25, NI * NH); th[NI * NH:NI * NH + NH] = rng.normal(0, .1, NH); m, v = np.zeros(DIM), np.zeros(DIM); sig, lr, NP = .04, .025, 12; best = (-1e9, th.copy()); t0 = time.time()
    for g in range(70):
        e = rng.normal(size=(NP, DIM)); P = np.vstack([th + sig * e, th - sig * e, th]); f = fitness(P, 1000 + g, c); base = f[-1]; fp, fm = f[:NP], f[NP:2 * NP]; rk = np.argsort(np.argsort(np.r_[fp, fm])) / (2 * NP - 1) - .5; gr = ((rk[:NP] - rk[NP:])[:, None] * e).mean(0) / sig
        m = .9 * m + .1 * gr; v = .999 * v + .001 * gr * gr; th = th + lr * m / (np.sqrt(v / (1 - .999 ** (g + 1))) + 1e-8) * .1
        if base > best[0]: best = (base, P[-1].copy())
        if g % 5 == 0: print(f"gen {g} score {base:.3f} best {best[0]:.3f} {time.time()-t0:.0f}s", flush=True); np.save("out/kite_policy.npy", best[1])
    fin = fitness(np.vstack([th, best[1]]), 5000, c); pick = th if fin[0] >= fin[1] else best[1]; np.save("out/kite_policy.npy", pick); print("final validation scores", fin.round(3), flush=True); r = evaluate(pick, c); json.dump({str(k): v for k, v in r.items()}, open("out/kite_ai.json", "w"), indent=1)
