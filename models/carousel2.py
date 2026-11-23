"""KITE CAROUSEL on the ocean pad: 2-4 arms on a turntable, each holding a line with a train of inflatable 12 m2 kites. The crank motion of each arm pays line out on the downwind half (kite powered) and takes it back on the upwind half (kite depowered).
Uses the 3D kite flight simulator with steering, gusts, slack and crash detection. Version 2: kite is steered to the zenith on the return stroke and a slip clutch limits line tension. Energy recirculates mechanically between arms. Arms, turntable and low-speed gearing are sized from simulated peak tension. Kite flies only at 3.5-6 m/s at 10 m and is reeled in otherwise. Launch, landing and line tangling between arms are NOT simulated."""
import json, io, contextlib, itertools, math
import numpy as np
with contextlib.redirect_stdout(io.StringIO()):
    import zoo as Z
import kite_sim as K
VS = np.array([3.5, 4., 5., 6.]); AP = ((.3, .55), (.45, .65)); T = 150.
def flight(Ra, f, m, V):
    S = 12. * m; c = K.Cfg(S=S, rmin=100., rmax=170., ms=.30, CL=.81 if m > 1 else .9, CD=.20 + .1 * (math.sqrt(m) - 1) / (12 * m), CLd=.25, CDd=.12, turb=.15, delay=.15 * m**.5, eta_out=.95, eta_in=.95); best = None; amp = f * V; Om = amp / Ra
    for a0, e0 in AP:
        rng = np.random.default_rng(int(100 * V) + m); ph = rng.uniform(0, 2 * math.pi, 24); tick = [0]
        def pol(st, ub, up, uv, cc):
            cc.rmin = 0.; t = tick[0] * K.DT; tick[0] += 1; cr = np.cos(Om * t + ph); st["phase"] = (cr < 0) * 1.; b, up_, _ = K.autopilot(st, cc, rng, a0=a0, e0=e0); Tm = 170 * cc.S; over = np.maximum(st["T"] - Tm, 0) / (.25 * Tm); return b, up_, amp * .8 * cr + over
        s = K.fly(float(V), c, T=T, seed=int(V * 10) + m, n=24, policy=pol); fl = float(s["tflown"].sum()); Pf = float(s["E"].sum() / max(fl, 1)); lam = float((~s["alive"]).sum()) / max(fl / 3600, 1e-3); av = 1 / (1 + lam / 3); net = Pf * av
        if best is None or net > best["net"]: best = dict(Pf=Pf, lam=lam, av=av, net=net, surv=float(s["alive"].mean()), Tpk=float(np.percentile(s["Tpk"], 95)))
    return best
v = Z.WS[(Z.WS >= 3.5) & (Z.WS <= 6.)]; hrs = len(v) / len(Z.WS) * 8766 * .85
def econ(Ra, m, arms, o, price, life):
    g = lambda k: np.array([o[float(x)][k] for x in VS]); Pm = np.maximum(g("net"), 0) * arms * .9 * .78; P = float(np.interp(v, VS, Pm).mean()); av = float(np.interp(v, VS, g("av")).mean()); lam = float(np.interp(v, VS, g("lam")).mean()) * arms; Tp = float(g("Tpk").max()); fly = hrs * av; mwh = P * hrs / 1e6
    if mwh <= 0: return None
    Tp = min(Tp, 170 * m * 12 * 1.3); Marm = Tp * Ra; dep = max(.35, Ra / 5); armkg = arms * Ra * 7850 * 2.8 * Marm / (60e6 * dep); armc = armkg * 3.2 + arms * 60; Q = Tp * Ra * max(arms / 2, 1); slew = 600 + .012 * Tp * arms * 2.5; gear = 250 + .08 * Q; elec = 350 + 500 * max(float(Pm.max()) / 1000, .5); pods = 450 * arms; kites = arms * m * price; line = arms * 160 * m * 12 / 16; other = 240; cap = armc + slew + gear + elec + pods + kites + line + other; yr = kites * fly / life + .05 * lam * fly * price + line * fly / 1500 + .03 * (cap - kites - line); L = cap + yr * 19 + .3 * (elec + pods); return dict(Ra=Ra, m=m, arms=arms, price=price, life=life, W=P * hrs / 8766, capex=cap, usd=L / (mwh * 20), crashes_yr=lam * fly, Tpk=Tp, Q=Q, arm_cost=armc, gear=gear, slew=slew, elec=elec, surv=float(g("surv").min()))
R = []; F = {}
for Ra, f, m in itertools.product((3., 5., 8.), (.2, .3, .4), (2, 4, 8, 16)):
    o = {float(V): flight(Ra, f, m, float(V)) for V in VS}; F[f"{Ra}|{f}|{m}"] = {str(k): x for k, x in o.items()}; print(f"Ra {Ra} speed {f} kites/arm {m}: " + " ".join(f"{V:g}:{x['net']:.0f}W/{x['surv']*100:.0f}%" for V, x in o.items()), flush=True)
    for arms, pr, li in itertools.product((2, 3, 4), (50, 150), (1500, 5000)):
        e = econ(Ra, m, arms, o, pr, li)
        if e: e["f"] = f; R.append(e)
json.dump(dict(flight=F, econ=R), open("out/carousel2.json", "w"), indent=1, default=float)
for pr, li in ((50, 5000), (50, 1500), (150, 1500)):
    b = min((r for r in R if r["price"] == pr and r["life"] == li), key=lambda r: r["usd"]); print(f"${pr} kite, {li} h: {b['arms']} arms × {b['m']} kites, arm {b['Ra']} m | {b['W']:.0f} W, build ${b['capex']:,.0f}, {b['crashes_yr']:.0f} crashes/yr, worst survival {b['surv']*100:.0f}% | ${b['usd']:.0f}/MWh | peak line {b['Tpk']/1000:.1f} kN, torque {b['Q']/1000:.0f} kNm, gear ${b['gear']:.0f}, arms ${b['arm_cost']:.0f}, turntable ${b['slew']:.0f}")
