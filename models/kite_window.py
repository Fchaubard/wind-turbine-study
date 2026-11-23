"""Re-costs the simulated kite trains if the kite is reeled in outside its safe wind window (3.5-6 m/s at 10 m), using the saved flights. Launch and landing are still not simulated."""
import json, io, contextlib, itertools
import numpy as np
with contextlib.redirect_stdout(io.StringIO()):
    import zoo as Z
F = json.load(open("out/kite_train.json"))["flight"]; RB = json.load(open("out/kite_robust.json")); IT = RB["items"]; BASE = RB["capex"] - IT["kite"] - IT["tether"]; VS = [3.5, 4., 5., 6.]; rows = []
v = Z.WS[(Z.WS >= 3.5) & (Z.WS <= 6.)]; hrs = len(v) / len(Z.WS) * 8766 * .85
for key, o in F.items():
    w, N = key.split("|"); N = int(N); g = lambda k: np.array([o[str(x)][k] for x in VS]); P = float(np.interp(v, VS, np.maximum(g("net"), 0)).mean()); av = float(np.interp(v, VS, g("av")).mean()); lam = float(np.interp(v, VS, g("lam")).mean()); fly = hrs * av; mwh = P * hrs / 1e6
    for pr, li, ex in itertools.product((50, 150, 250), (1500, 5000), (.7, 1.)):
        ground = BASE * (N * 12 / 16)**ex; kite = N * pr; teth = IT["tether"] * N * 12 / 16; yr = kite * fly / li + .05 * lam * fly * pr + teth * fly / 1500 + .03 * ground; L = ground + kite + teth + yr * 19 + .18 * ground; rows.append(dict(wind=w, N=N, price=pr, life=li, ex=ex, W=P * hrs / 8766, capex=ground + kite + teth, crashes_yr=lam * fly, usd=L / (mwh * 20), fly_h=fly))
json.dump(rows, open("out/kite_window.json", "w"), indent=1)
pick = lambda p, l, e: min((r for r in rows if r["wind"] == "gusty" and r["price"] == p and r["life"] == l and r["ex"] == e), key=lambda r: r["usd"])
for c in ((50, 5000, .7), (50, 1500, 1.), (150, 1500, .7), (150, 1500, 1.), (250, 1500, 1.)):
    r = pick(*c); print(c, f"best {r['N']} kites, {r['W']:.0f} W, build ${r['capex']:,.0f}, {r['crashes_yr']:.0f} crashes/yr, flies {r['fly_h']:.0f} h/yr, ${r['usd']:.0f}/MWh")
