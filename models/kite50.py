"""Inflatable kite test from the pad: 12 m2 leading-edge-inflatable kites (0.30 kg/m2, CL .9, CD .2), alone or as a train of 2/4/8 on one line, pumping a ground generator, autopilot tuned per wind.
Storms cost nothing: the kite is reeled in. Crashes cost 20 minutes each to relaunch and 1 in 20 destroys a kite. Prices: the user's $50 and a realistic $250 DIY kite; life 500, 1500, 5000 flight hours."""
import json, io, contextlib, itertools
import numpy as np
with contextlib.redirect_stdout(io.StringIO()):
    import zoo as Z
import kite_sim as K
RB = json.load(open("out/kite_robust.json")); IT = RB["items"]; BASE = RB["capex"] - IT["kite"] - IT["tether"]; VS = np.array([3., 3.5, 4., 5., 6., 8.]); PG = [(a, e, g) for a, e, g in itertools.product((.3, .45), (.45, .65), (.22, .33))]
print("ground and control parts (excluding kite and tether): $", round(BASE), {k: round(v) for k, v in IT.items()}, flush=True)
def run(N, turb):
    S = 12. * N; out = {}
    for V in VS:
        c = K.Cfg(S=S, ms=.30, CL=.9, CD=.20, CLd=.25, CDd=.12, turb=turb, delay=.15 * N**.5, bmax=.14); best = None
        for p in PG:
            r = np.random.default_rng(int(V * 10) + N); pol = lambda st, ub, up, uv, cc: K.autopilot(st, cc, r, a0=p[0], e0=p[1], gamma=p[2]); s = K.fly(float(V), c, T=180., seed=int(V * 10), n=24, policy=pol); fl = float(s["tflown"].sum()); Pf = float(s["E"].sum() / max(fl, 1)); crashes = float((~s["alive"]).sum()); lam = crashes / max(fl / 3600, 1e-3); av = 1 / (1 + lam / 3); net = Pf * av
            if best is None or net > best["net"]: best = dict(Pf=Pf, lam=lam, av=av, net=net, surv=float(s["alive"].mean()), p=p)
        out[float(V)] = best
    return out
def econ(N, o, price, life):
    v = Z.WS[(Z.WS >= 3.) & (Z.WS <= 9.)]; nets = np.array([max(o[float(x)]["net"], 0) for x in VS]); lams = np.array([o[float(x)]["lam"] for x in VS]); avs = np.array([o[float(x)]["av"] for x in VS]); share = len(v) / len(Z.WS); hrs = share * 8766 * .85; P = float(np.interp(v, VS, nets).mean()); av = float(np.interp(v, VS, avs).mean()); lam = float(np.interp(v, VS, lams).mean()); mwh = P * hrs / 1e6; fly = hrs * av; ground = BASE * (N * 12 / 16)**.7; kite = N * price; teth = IT["tether"] * max(N, 1)**.5; yr = kite * fly / life + .05 * lam * fly * price + teth * fly / 1500 + .03 * ground; life20 = ground + kite + teth + yr * 19 + .3 * ground * .6; return dict(N=N, price=price, life=life, W=P * hrs / 8766, MWh=mwh, usd=life20 / (mwh * 20) if mwh > 0 else 1e9, capex=ground + kite + teth, crashes_yr=lam * fly, ground=ground)
R = {}; rows = []
for turb, tn in ((.08, "smooth wind"), (.15, "normal gusts")):
    for N in (1, 2, 4, 8):
        o = run(N, turb); R[f"{tn}|{N}"] = {str(k): v for k, v in o.items()}; print(f"{tn}, {N} kite(s): " + " ".join(f"{v:g}m/s {x['net']:.0f}W/{x['surv']*100:.0f}%" for v, x in o.items()), flush=True)
        for price, life in itertools.product((50, 250), (500, 1500, 5000)): rows.append(dict(econ(N, o, price, life), wind=tn))
json.dump(dict(flight=R, econ=rows), open("out/kite50.json", "w"), indent=1, default=float)
for tn in ("smooth wind", "normal gusts"):
    for price, life in ((50, 5000), (50, 1500), (250, 1500)):
        x = [r for r in rows if r["wind"] == tn and r["price"] == price and r["life"] == life]; b = min(x, key=lambda r: r["usd"]); print(f"{tn}, ${price} kite, {life} h life: best {b['N']} kite(s), {b['W']:.0f} W year average, ${b['capex']:,.0f}, {b['crashes_yr']:.0f} crashes/yr, ${b['usd']:.0f}/MWh")
