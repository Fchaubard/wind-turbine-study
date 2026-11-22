"""What would have to be true for wind to cost under $10/MWh?
Each 'belief' runs from the study's base value (t=0) to a floor with a named real-world analogue (t=1).
1. floor: every belief at t=1, design re-optimised, per architecture -> is $10 reachable at all?
2. least-stretch: minimise sum(t_i^2) subject to LCOE <= 10 -> the cheapest set of beliefs that gets there."""
import json, sys
import numpy as np
from scipy.optimize import minimize
import lcoe_opt as L

TARGET = float(sys.argv[1]) if len(sys.argv) > 1 else 10.0
B = [  # key, label, base, floor, analogue
    ("drive", "On-wing turbine + generator + converter, $/kW", 620.0, 100.0, "EV drive units are $15–25/kW in volume; add propeller, HV DC-DC, mounts"),
    ("wing", "Wing cost, $/m² (fabric wings; rigid wings $1,800 → $1,000)", 150.0, 60.0, "paraglider / sailcloth structures in volume are $40–80/m²; turbine blades are ~$1,000–2,000/m²"),
    ("wlife", "Wing life, years", 5.0, 12.0, "PVDF/PTFE architectural membranes last 15–25 yr outdoors; flexing wings less"),
    ("teth", "Tether fibre, $/kg", 60.0, 25.0, "commodity UHMWPE yarn is $15–25/kg"),
    ("tlife", "Tether life, years", 5.0, 10.0, "static (non-reeled) mooring-grade rope"),
    ("bos", "Balance of system, $/kW", 250.0, 120.0, "utility solar electrical BOS + interconnect"),
    ("gconv", "Ground converter + grid tie, $/kW", 80.0, 40.0, "central PV inverters are ~$40/kW"),
    ("om", "Other O&M, % of capex per year", 2.0, 1.0, "utility solar O&M is ~1 %"),
    ("avail", "Availability, %", 92.0, 97.0, "modern wind turbines reach 97 %"),
    ("wacc", "Cost of capital, %", 7.0, 4.0, "regulated utility / sovereign-backed debt"),
    ("life", "Project life, years", 25.0, 35.0, "ground hardware only; wings and tether are consumables"),
    ("wind", "Site mean wind at 90 m, m/s", 7.5, 11.0, "best onshore sites: Patagonia, Tehuantepec, Turkana, Great Plains ridges"),
]
BASE = L.snapshot()

def val(i, t):
    return B[i][2] + t * (B[i][3] - B[i][2])

def apply(t):
    L.restore(BASE)
    v = {b[0]: val(i, t[i]) for i, b in enumerate(B)}
    L.DRIVE.update(onwing=v["drive"], tether_life=v["tlife"], pump_tether_life=v["tlife"] * 0.6, ground_fg=v["gconv"], pump_gen=330.0 - (330.0 - 120.0) * t[0])
    f = v["wing"] / 150.0
    tw = (150.0 - v["wing"]) / 90.0; tl = (v["wlife"] - 5.0) / 7.0
    for k, w in L.WINGS.items():
        if k == "rigid":      # composite wings are blade-like: floor $1,000/m² (−45 %), life 20 → 25 yr
            w["cost"] = w["cost"] * (1 - 0.45 * tw); w["life"] = w["life"] * (1 + 0.25 * tl)
        else:
            w["cost"] = w["cost"] * f; w["life"] = w["life"] * v["wlife"] / 5.0
    L.DYN["cost_kg"] = v["teth"]; L.AWE_SITE["onshore"]["bos_kW"] = v["bos"]; L.OM["frac"] = v["om"] / 100
    L.AVAIL["awe"] = v["avail"] / 100; L.FIN.update(r=v["wacc"] / 100, n=int(round(v["life"])))
    return dict(L.SITES["onshore"], vmean=v["wind"], label=f"Onshore, {v['wind']:.1f} m/s at 90 m")

out = dict(target=TARGET, beliefs=[dict(key=b[0], label=b[1], base=b[2], floor=b[3], analogue=b[4]) for b in B])
# 1. floor per architecture
ones = np.ones(len(B)); floors = []
for arch, wing, name in L.CASES[1:]:
    site = apply(ones); r = L.optimise(site, arch, wing, maxiter=100)
    floors.append(dict(name=name, **L.brief(r))); print(f"floor  {name:46s} ${r['lcoe']:5.1f}  CF {r['cf']:.2f}  ${r['capex_per_MW']/1e6:.2f}M/MW  {r['label']}", flush=True)
site = apply(ones); L.FIN.update(r=0.04, n=35); h = L.optimise(site, "hawt", None, maxiter=100)
floors.append(dict(name="Conventional turbine, same site and finance (its own costs unchanged)", **L.brief(h))); print(f"floor  turbine ${h['lcoe']:.1f} {h['label']}")
out["floors"] = floors
bestf = min(floors[:-1], key=lambda r: r["lcoe"]); ci = [f["name"] for f in floors].index(bestf["name"]); arch, wing, _ = L.CASES[1 + ci]
out["floor_best"] = bestf
# one-at-a-time: each belief alone at its floor, and all-but-one at floor (which beliefs are indispensable)
site = apply(ones); rb = L.optimise(site, arch, wing, maxiter=100); xb = rb["x"]; fn = L.ARCH[arch]
rows = []
for i, b in enumerate(B):
    t = ones.copy(); t[i] = 0.0; site = apply(t); without = fn(site, xb, wing)["lcoe"]
    rows.append(dict(key=b[0], label=b[1], base=b[2], floor=b[3], lcoe_without=without))
    print(f"   without {b[1]:48s} ${without:5.1f}")
out["indispensable"] = rows
# 2. least-stretch set of beliefs that reaches the target (design fixed at the floor optimum, then re-optimised once)
if bestf["lcoe"] < TARGET:
    x = xb
    for rnd in range(2):
        def g(t): return fn(apply(np.clip(t, 0, 1)), x, wing)["lcoe"]
        res = minimize(lambda t: float(np.sum(t**2)), ones * 0.8, method="SLSQP", bounds=[(0, 1)] * len(B),
                       constraints=[dict(type="ineq", fun=lambda t: TARGET - g(t))], options=dict(maxiter=200, ftol=1e-6))
        t = np.clip(res.x, 0, 1); site = apply(t); r = L.optimise(site, arch, wing, maxiter=100); x = r["x"]
        print(f"least-stretch round {rnd}: LCOE at fixed design ${g(t):.2f}, re-optimised ${r['lcoe']:.2f}", flush=True)
    out["least"] = dict(t=t.tolist(), values=[val(i, t[i]) for i in range(len(B))], **L.brief(r), items=r["items"], capex=r["capex"], opex=r["opex"], aep_kwh=r["aep_kwh"])
    for i, b in enumerate(B): print(f"   {b[1]:48s} {b[2]:7.1f} → {val(i, t[i]):7.1f}   (floor {b[3]}, stretch {t[i]*100:.0f} %)")
L.restore(BASE)
json.dump(out, open("out/target10.json", "w"), indent=1, default=float)
