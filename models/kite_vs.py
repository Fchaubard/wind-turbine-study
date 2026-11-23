import json, io, contextlib
import numpy as np
with contextlib.redirect_stdout(io.StringIO()):
    import zoo as Z
O = json.load(open("out/kite_opt.json"))["ultralight 16 m² (0.28 kg/m²)"]; RB = json.load(open("out/kite_robust.json")); CAP = RB["items"]; capex = RB["capex"]; V10 = Z.WS
vs = np.array([3.5, 4, 5, 6]); W = np.array([O[k]["W"] for k in ("3.5", "4", "5", "6")]); fly = (V10 >= 3.5) & (V10 <= 6.); fh = fly.mean() * 8766 * .75; P = float(np.interp(V10[fly], vs, W).mean()); mwh = P * fh / 1e6; res = {}
for life in (500, 1500, 5000, 20000):
    yr = CAP["kite"] * .55 * fh / life + CAP["tether"] * fh / min(life, 1500) + .03 * (capex - CAP["kite"] - CAP["tether"]); res[life] = (capex + yr * 19 + .3 * (CAP["inverter"] + CAP["generator"] + CAP["pod"])) / (mwh * 20)
print(f"BEST-CASE kite (ideal ultralight, AI tuned, no crashes, no fabric collapse): flies {fly.mean()*100:.0f}% of hours x 75% = {fh:.0f} h/yr, {P:.0f} W while flying, {P*fh/8766:.0f} W year-average, {mwh:.2f} MWh/yr")
print("  $/MWh by kite life (h):", {k: round(v) for k, v in res.items()})
F = json.load(open("out/dandelion_final.json")); E = F["W"] * 8.766 * 20 / 1000; life = F["usd"] * E; save = 178.46 + 117.30 - 80; new = (life - save - .3 * save) / E; print(f"Dandelion with $80 open-source controller: capex ${F['capex']-save:,.0f}, ${new:.0f}/MWh (was ${F['usd']:.0f})")
json.dump(dict(best_kite=dict(W=P * fh / 8766, MWh=mwh, fly_h=fh, usd={str(k): v for k, v in res.items()}), dandelion=dict(capex=F["capex"] - save, usd=new, W=F["W"])), open("out/kite_vs.json", "w"), indent=1)
