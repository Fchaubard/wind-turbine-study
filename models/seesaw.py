"""KITE SEESAW: two kite trains on the two ends of one rope over a drum on the pad. The powered train pulls out at the same speed the depowered train is hauled in, so return energy moves directly through the rope. A one-way clutch keeps the generator turning one way.
No arms, turntable, winch storage or large low-speed gear. Uses the 3D kite simulator (gusts, steering, slack, crash detection). Flies at 3.5-6 m/s at 10 m and is reeled in otherwise. Launch, landing and tangling are NOT simulated. Prices are budget estimates."""
import json, io, contextlib, itertools, math
import numpy as np
with contextlib.redirect_stdout(io.StringIO()):
    import zoo as Z
import kite_sim as K
VS = np.array([3.5, 4., 5., 6.]); AP = ((.3, .5), (.45, .6)); v = Z.WS[(Z.WS >= 3.5) & (Z.WS <= 6.)]; hrs = len(v) / len(Z.WS) * 8766 * .85
def flight(f, m, V):
    S = 12. * m; c = K.Cfg(S=S, ms=.30, CL=.81 if m > 1 else .9, CD=.20 + .1 * (math.sqrt(m) - 1) / (12 * m), CLd=.25, CDd=.12, turb=.15, delay=.15 * m**.5, eta_out=.95, eta_in=.95); best = None; amp = max(f * V, .5)
    for a0, e0 in AP:
        rng = np.random.default_rng(int(100 * V) + m)
        def pol(st, ub, up, uv, cc):
            b, u, _ = K.autopilot(st, cc, rng, a0=a0, e0=e0); tr = st["phase"] == 0; Tm = 170 * cc.S; over = np.maximum(st["T"] - Tm, 0) / (.25 * Tm); return b, u, np.where(tr, amp, -amp) + over
        s = K.fly(float(V), c, T=300., seed=int(V * 10) + m, n=24, policy=pol); fl = float(s["tflown"].sum()); Pf = float(s["E"].sum() / max(fl, 1)); lam = float((~s["alive"]).sum()) / max(fl / 3600, 1e-3); av = 1 / (1 + lam / 3); net = Pf * av
        if best is None or net > best["net"]: best = dict(Pf=Pf, lam=lam, av=av, net=net, surv=float(s["alive"].mean()), Tpk=float(np.percentile(s["Tpk"], 95)))
    return best
def econ(f, m, pairs, o, price, life, line_life):
    g = lambda k: np.array([o[float(x)][k] for x in VS]); Pm = np.maximum(g("net"), 0) * 2 * pairs * .9 * .78; P = float(np.interp(v, VS, Pm).mean()); av = float(np.interp(v, VS, g("av")).mean()); lam = float(np.interp(v, VS, g("lam")).mean()) * 2 * pairs; fly = hrs * av; mwh = P * hrs / 1e6
    if mwh <= 0: return None
    Tp = min(float(g("Tpk").max()), 170 * m * 12 * 1.3); Q = Tp * .15; items = dict(kites=2 * pairs * m * price, lines=2 * pairs * 120 * m, pods=2 * pairs * 450, drums_clutches=pairs * 400, gear=pairs * (250 + .08 * Q), fairleads=2 * pairs * 150, frame=250 + 150 * pairs, generator_inverter=350 + 500 * max(float(Pm.max()) / 1000, .5), sensors_wiring=240); cap = sum(items.values()); yr = items["kites"] * fly / life + .05 * lam * fly * price + items["lines"] * fly / line_life + .03 * (cap - items["kites"] - items["lines"]); L = cap + yr * 19 + .3 * (items["generator_inverter"] + items["pods"]); return dict(f=f, m=m, pairs=pairs, price=price, life=life, line_life=line_life, W=P * hrs / 8766, capex=cap, usd=L / (mwh * 20), crashes_yr=lam * fly, Tpk=Tp, Q=Q, surv=float(g("surv").min()), items=items, yearly=yr)
R, F = [], {}
for f, m in itertools.product((.2, .3, .4), (4, 8, 16, 32)):
    o = {float(V): flight(f, m, float(V)) for V in VS}; F[f"{f}|{m}"] = {str(k): x for k, x in o.items()}; print(f"speed {f}, {m} kites/train: " + " ".join(f"{V:g}:{x['net']:.0f}W/{x['surv']*100:.0f}%" for V, x in o.items()), flush=True)
    for pairs, pr, li, ll in itertools.product((1, 2, 4), (50, 150), (1500, 5000), (1500, 5000)):
        e = econ(f, m, pairs, o, pr, li, ll)
        if e: R.append(e)
json.dump(dict(flight=F, econ=R), open("out/seesaw.json", "w"), indent=1, default=float)
for pr, li, ll in ((50, 5000, 5000), (50, 5000, 1500), (150, 1500, 5000), (150, 1500, 1500)):
    b = min((r for r in R if r["price"] == pr and r["life"] == li and r["line_life"] == ll), key=lambda r: r["usd"]); print(f"${pr} kite, kite {li} h, line {ll} h: {b['pairs']} pair(s) × {b['m']} kites, speed {b['f']} | {b['W']:.0f} W, build ${b['capex']:,.0f}, {b['crashes_yr']:.0f} crashes/yr, worst survival {b['surv']*100:.0f}% | ${b['usd']:.0f}/MWh | peak line {b['Tpk']/1000:.1f} kN, upkeep ${b['yearly']:,.0f}/yr")
