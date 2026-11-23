"""SEA KITE: an unmanned sail catamaran on a tether from a winch on the pad. It sweeps crosswind on an arc downwind of the pad, pulling tether out (power), then luffs its sail and is winched back (small cost).
Water carries its weight, so it cannot fall. Vectorised time simulation with gusts, trim lag, hull drag, wave drag, capsize limit. Cross-entropy search tunes the control at each wind speed; tests use unseen gusts, a worse boat and rough water."""
import json, math, time, io, contextlib
import numpy as np
with contextlib.redirect_stdout(io.StringIO()):
    import zoo as Z
RHO, RW, G, DT = 1.18, 1025., 9.81, .05
class Boat:
    def __init__(s, S=20., beam=2.6, L0=35., L1=80., drag=1., cd=.14, clmax=1.25, turb=.15, lag=1.2, waves=1.):
        s.S, s.beam, s.L0, s.L1, s.drag, s.cd, s.clmax, s.turb, s.lag, s.waves = S, beam, L0, L1, drag, cd, clmax, turb, lag, waves; s.m = 110 + 7 * S; s.h = 1.65 * math.sqrt(S); s.zce = .9 + .42 * s.h; s.a = 3.5 * (s.m / 200) ** (2 / 3) * drag * waves; s.b = .05 * (s.m / 200) * drag * waves; s.madd = s.m * 1.25
LO = np.array([.25, .12, .25, .25, .35]); HI = np.array([1.25, .50, 2.2, 1.0, 1.0])     # arc half-angle, reel-out/wind, reel-in speed, tack threshold speed, trim fraction
def sim(V10, X, c, seed, T):
    n = len(X); rng = np.random.default_rng(seed); th = rng.uniform(-.2, .2, n); u = rng.uniform(.2, 1, n) * rng.choice([-1., 1.], n); L = np.full(n, c.L0 + 1.); vr = np.zeros(n); g = rng.normal(0, c.turb, n); cl = np.zeros(n); dirn = np.sign(u); phase = np.zeros(n); E = np.zeros(n); alive = np.ones(n, bool); am, gam, vin, _, trim = X.T; heelF = .78 * c.m * G * (c.beam / 2)
    for _ in range(int(T / DT)):
        g += -g * DT / 8 + c.turb * np.sqrt(2 * DT / 8) * rng.normal(size=n); V = V10 * (c.zce / 10) ** .14 * np.maximum(1 + g, .15); phase = np.where(L >= c.L1, 1., np.where(L <= c.L0, 0., phase)); dirn = np.where(th > am, -1., np.where(th < -am, 1., dirn))
        er = np.column_stack([np.cos(th), np.sin(th)]); et = np.column_stack([-np.sin(th), np.cos(th)]); vb = vr[:, None] * er + u[:, None] * et; Wv = np.column_stack([V, np.zeros(n)]) - vb; A = np.maximum(np.linalg.norm(Wv, axis=1), .1); ua = Wv / A[:, None]; nr = np.column_stack([-ua[:, 1], ua[:, 0]]); s = np.sign(np.sum(nr * (dirn[:, None] * et), 1)); s = np.where(s == 0, 1, s); lift = nr * s[:, None]
        q = .5 * RHO * A * A; hc = heelF / np.maximum(q * c.S * c.zce, 1e-3); cmd = np.where(phase == 0, np.minimum(trim * c.clmax, hc * .82), 0.); cl += (cmd - cl) * min(DT / c.lag, 1); cd = c.cd * (.45 + .55 * np.minimum(cl / c.clmax, 1)) + .06 * cl * cl; F = (q * c.S)[:, None] * (cl[:, None] * lift + cd[:, None] * ua); heel = q * c.S * np.sqrt(cl * cl + cd * cd) * c.zce; alive &= heel <= heelF * 1.16
        sp = np.sqrt(u * u + vr * vr) + 1e-3; D = (c.a * sp * sp + c.b * sp**4); Fh = -(D / sp)[:, None] * vb; Ft = np.sum((F + Fh) * et, 1); Fr = np.sum((F + Fh) * er, 1) + c.m * u * u / L; Tn = np.maximum(Fr, 5.); vc = np.where(phase == 0, gam * V, -vin); vr += np.clip(vc - vr, -.8 * DT, .8 * DT); Pm = Tn * vr; Pe = np.where(Pm > 0, Pm * .72, Pm / .78); E += Pe * DT * alive; u += DT * (Ft / c.madd - u * vr / L); u = np.where(alive, u, 0.); th = np.clip(th + DT * u / L, -1.45, 1.45); u = np.where(np.abs(th) >= 1.45, 0., u); L = np.clip(L + DT * vr, c.L0 - 1, c.L1 + 1)
    return E / T, alive
def train(V, c, seed):
    r = np.random.default_rng(seed); mu, sd = (LO + HI) / 2, (HI - LO) / 3; el = None
    for g in range(11):
        X = np.clip(r.normal(mu, sd, (36, 5)), LO, HI)
        if el is not None: X[:4] = el[:4]
        w, a = sim(V, np.repeat(X, 4, 0), c, seed + g, 300.); f = (w - 250 * (~a)).reshape(36, 4).mean(1); o = np.argsort(-f); el = X[o[:8]]; mu = el.mean(0); sd = el.std(0) + .03 * (HI - LO)
    return el[0]
if __name__ == "__main__":
    W10 = Z.WS; t0 = time.time(); R = {}; VS = (1.5, 2, 2.5, 3, 3.5, 4, 5, 6, 7, 9)
    for S in (12., 20., 30.):
        c = Boat(S=S, beam=2.2 + S / 25); bad = Boat(S=S, beam=2.2 + S / 25, drag=1.45, cd=.20, clmax=1.05, turb=.25, lag=2.2, waves=1.25); tb = {}
        for V in VS:
            x = train(V, bad, int(V * 100 + S)); a, sa = sim(V, np.repeat(x[None], 160, 0), c, 7000 + int(V * 10), 1200.); b, sb = sim(V, np.repeat(x[None], 160, 0), bad, 8000 + int(V * 10), 1200.); tb[V] = dict(W=float(a.mean()), ok=float(sa.mean()), Wbad=float(b.mean()), okbad=float(sb.mean()), x=x.tolist())
            print(f"S {S:.0f} V {V}: good boat {a.mean():6.0f} W, upright {sa.mean()*100:3.0f}% | worse boat, rough water {b.mean():6.0f} W, upright {sb.mean()*100:3.0f}%  ({time.time()-t0:.0f}s)", flush=True)
        R[S] = tb; json.dump({str(k): {str(a): b for a, b in v.items()} for k, v in R.items()}, open("out/seakite.json", "w"), indent=1)
