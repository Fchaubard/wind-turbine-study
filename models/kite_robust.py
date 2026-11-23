"""Try to break the kite result. Train on a deliberately worse kite (lower lift and glide, heavier with pod, 25% turbulence, slow actuators, noisy sensors, fabric collapses at low tension), test on unseen flights,
then compute cost per MWh on the real hourly wind with kite and tether wear, crash repairs, launch/landing time and no flying outside the safe wind window."""
import json, time
import numpy as np
import kite_sim as K, kite_ctrl as C
with __import__("contextlib").redirect_stdout(__import__("io").StringIO()):
    import zoo as Z
GOOD = dict(S=16., ms=.28, CD=.19); BAD = dict(S=16., ms=.42, CD=.27, CL=.85, CLd=.25, turb=.25, delay=.40, noise=.07)
def cfg(k): c = K.Cfg(**k); c.Tslack = 2.5 * c.S; return c
WV = (3, 3.5, 4, 5, 6, 7); P = {}; R = {}; t0 = time.time(); ct = cfg(BAD)
for V in WV:
    rng = np.random.default_rng(int(V * 100)); mu = (C.LO + C.HI) / 2; sd = (C.HI - C.LO) / 3; el = None
    for g in range(10):
        X = np.clip(rng.normal(mu, sd, (32, 9)), C.LO, C.HI)
        if el is not None: X[:4] = el[:4]
        s = C.run(V, np.repeat(X, 4, 0), ct, 300 + g, 240.); f = ((s["E"] / 240.) - 1500 * (~s["alive"])).reshape(32, 4).mean(1); o = np.argsort(-f); el = X[o[:7]]; mu = el.mean(0); sd = el.std(0) + .03 * (C.HI - C.LO)
    P[V] = el[0]; row = {}
    for nm, k in (("as designed", GOOD), ("worse kite", BAD)):
        s = C.run(V, np.repeat(el[:1], 240, 0), cfg(k), 9000 + int(V * 10), 1800.); h = s["tflown"].sum() / 3600; cr = int((~s["alive"]).sum()); row[nm] = dict(hours=h, crashes=cr, crash_h=cr / max(h, 1e-3), W=float(s["E"].sum() / max(s["tflown"].sum(), 1)))
    R[V] = row; print(f"{V:3.1f} m/s | as designed {row['as designed']['W']:5.0f} W {row['as designed']['crashes']:3d} crashes in {row['as designed']['hours']:.0f} h | worse kite {row['worse kite']['W']:5.0f} W {row['worse kite']['crashes']:3d} crashes in {row['worse kite']['hours']:.0f} h  ({time.time()-t0:.0f}s)", flush=True)
V10 = Z.WS; hrs = 8766.; CAP = dict(kite=950, pod=450, tether=160, winch=450, generator=400, inverter=450, buffer=350, mast=350, anchors=60, sensors=60, wiring=120); capex = sum(CAP.values()); out = {}
for nm in ("as designed", "worse kite"):
    vs = np.array(WV, float); W = np.array([R[v][nm]["W"] for v in WV]); cr = np.array([R[v][nm]["crash_h"] for v in WV]); ok = np.array([R[v][nm]["crash_h"] <= .05 for v in WV])
    if not ok.any(): out[nm] = dict(W=0, usd={}, note="no safe wind"); print(nm, "no wind speed is safe"); continue
    vmin, vmax = vs[ok].min(), vs[ok].max(); fly = (V10 >= vmin) & (V10 <= vmax); fh = fly.mean() * hrs * .75; Pw = float(np.interp(V10[fly], vs, np.maximum(W, 0)).mean()); mwh = Pw * fh / 1e6; crh = max(float(np.mean(np.interp(V10[fly], vs, cr))), 1.5 / max(sum(R[v][nm]["hours"] for v in vs[ok]), 1)); u = {}
    for life in (500, 1500, 5000):
        yr = (CAP["kite"] * .55 + 0) * fh / life + CAP["tether"] * fh / min(life, 1500) + crh * fh * 90 + .03 * (capex - CAP["kite"] - CAP["tether"]); u[life] = (capex + yr * 19 + .3 * (CAP["inverter"] + CAP["generator"] + CAP["pod"])) / (mwh * 20)
    out[nm] = dict(vmin=vmin, vmax=vmax, fly_h=fh, avgW=Pw * fh / hrs, MWh=mwh, crash_h=crh, crash_yr=crh * fh, usd=u); print(f"{nm}: flies {vmin}-{vmax} m/s, {fh:.0f} h/yr, {Pw*fh/hrs:.0f} W year-average, {mwh:.2f} MWh/yr, about {crh*fh:.0f} crashes/yr | $/MWh at kite life 500/1500/5000 h: {u[500]:.0f} / {u[1500]:.0f} / {u[5000]:.0f}", flush=True)
json.dump(dict(cases={str(k): v for k, v in R.items()}, econ=out, capex=capex, items=CAP, params={str(k): v.tolist() for k, v in P.items()}), open("out/kite_robust.json", "w"), indent=1, default=float)
