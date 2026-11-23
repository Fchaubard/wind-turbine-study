"""Long kite trains on one line from the ocean pad: 8 to 64 inflatable 12 m2 kites. Compared with kite50.py this charges: 10% lift loss from kites flying in each other's flow, line strength and cost growing with load, thicker-line drag, slower steering, and pad pull.
Costs are shown for kite prices $50/$150/$250, life 1500/5000 h, and ground gear scaling either favorably (power 0.7) or linearly. Launch and landing of the train are NOT simulated."""
import json, io, contextlib, itertools, math
import numpy as np
with contextlib.redirect_stdout(io.StringIO()):
    import zoo as Z
import kite_sim as K
RB = json.load(open("out/kite_robust.json")); IT = RB["items"]; BASE = RB["capex"] - IT["kite"] - IT["tether"]; VS = np.array([3., 3.5, 4., 5., 6., 8.]); PG = list(itertools.product((.3, .45), (.45, .65), (.22, .33)))
def run(N, turb):
    S = 12. * N; out = {}
    for V in VS:
        c = K.Cfg(S=S, ms=.30, CL=.81, CD=.20 + .1 * (math.sqrt(N) - 1) / (12 * N), CLd=.25, CDd=.12, turb=turb, delay=.15 * N**.5, bmax=.14); best = None
        for p in PG:
            r = np.random.default_rng(int(V * 10) + N); pol = lambda st, ub, up, uv, cc: K.autopilot(st, cc, r, a0=p[0], e0=p[1], gamma=p[2]); s = K.fly(float(V), c, T=180., seed=int(V * 10) + 7, n=32, policy=pol); fl = float(s["tflown"].sum()); Pf = float(s["E"].sum() / max(fl, 1)); lam = float((~s["alive"]).sum()) / max(fl / 3600, 1e-3); av = 1 / (1 + lam / 3); net = Pf * av
            if best is None or net > best["net"]: best = dict(Pf=Pf, lam=lam, av=av, net=net, surv=float(s["alive"].mean()), Tmax=float(s["Tpk"].max()))
        out[float(V)] = best
    return out
def econ(N, o, price, life, ex):
    v = Z.WS[(Z.WS >= 3.) & (Z.WS <= 9.)]; g = lambda k: np.array([o[float(x)][k] for x in VS]); hrs = len(v) / len(Z.WS) * 8766 * .85; P = float(np.interp(v, VS, np.maximum(g("net"), 0)).mean()); av = float(np.interp(v, VS, g("av")).mean()); lam = float(np.interp(v, VS, g("lam")).mean()); mwh = P * hrs / 1e6; fly = hrs * av; ground = BASE * (N * 12 / 16)**ex; kite = N * price; teth = IT["tether"] * N * 12 / 16; yr = kite * fly / life + .05 * lam * fly * price + teth * fly / 1500 + .03 * ground; L = ground + kite + teth + yr * 19 + .18 * ground; Tm = float(g("Tmax").max()); return dict(N=N, price=price, life=life, ex=ex, W=P * hrs / 8766, usd=L / (mwh * 20), capex=ground + kite + teth, crashes_yr=lam * fly, pull_t=Tm * .75 / 9810, ground=ground, tether=teth)
F, rows = {}, []
for turb, tn in ((.08, "smooth"), (.15, "gusty")):
    for N in (8, 16, 32, 64):
        o = run(N, turb); F[f"{tn}|{N}"] = {str(k): x for k, x in o.items()}; print(tn, N, " ".join(f"{v:g}:{x['net']/1000:.1f}kW/{x['surv']*100:.0f}%" for v, x in o.items()), flush=True)
        for pr, li, ex in itertools.product((50, 150, 250), (1500, 5000), (.7, 1.)): rows.append(dict(econ(N, o, pr, li, ex), wind=tn))
json.dump(dict(flight=F, econ=rows), open("out/kite_train.json", "w"), indent=1, default=float)
print("cost per MWh, gusty wind:")
for pr, li, ex in ((50, 5000, .7), (50, 1500, 1.), (150, 1500, .7), (150, 1500, 1.), (250, 1500, 1.)):
    print(f" kite ${pr}, {li} h, ground exponent {ex}: " + " | ".join(f"{r['N']}: ${r['usd']:.0f}" for r in rows if r["wind"] == "gusty" and r["price"] == pr and r["life"] == li and r["ex"] == ex))
for N in (8, 16, 32, 64):
    r = next(x for x in rows if x["wind"] == "gusty" and x["N"] == N and x["price"] == 150 and x["life"] == 1500 and x["ex"] == 1.); print(f"N {N}: {r['W']:.0f} W, build ${r['capex']:,.0f}, {r['crashes_yr']:.0f} crashes/yr, pad pull {r['pull_t']:.1f} t")
