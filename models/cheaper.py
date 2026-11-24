"""Cost-down of the structurally checked 14 m Dandelion (10 m hub). Geometry and structure are unchanged; only part sourcing changes. Adds the extra pad concrete that earlier numbers left out. Savings are budget estimates, cumulative in the order shown."""
import json, math
import numpy as np
src_ = open("blimp.py").read(); exec(src_[:src_.index("GAS = {")])
d = D14; p = d["pick"]; dC = d["capex"] - p["capex"]; fab = (p["wear"] - 70 - .02 * p["tower"]) / 1.6; ng = p["ng"]; rb = 220. * ng; L0 = p["capex"] + p["wear"] * 19 + rb + fab * 7 + 40 + dC * 1.38; print(f"reconstructed life ${L0:,.0f} vs model ${LIFE14:,.0f}; fabric {fab:.0f} m², steel ${p['tower'] + dC:,.0f}, rotor ${p['blade']:,.0f}, electronics ${733 * ng:,.0f}")
A = math.pi * 49
def W(s, eff=1., cap=2400., cut=2.5): v = wind(10, s) * math.cos(math.radians(10)); return float(np.mean(np.minimum(k * eff * .5 * RHO * A * v**3, cap) * (v >= cut))) * .95
steel = p["tower"] + dC; steps = []; L = L0; cap = d["capex"]; eff, gcap, cut = 1., 2400., 2.5
def add(name, dcap, dlife, e=None, c=None, ct=None):
    global L, cap, eff, gcap, cut
    cap += dcap; L += dlife
    if e: eff = e
    if c: gcap = c
    if ct: cut = ct
    steps.append(dict(name=name, build=cap, life=L, W_NASA=W("NASA", eff, gcap, cut), W_ERA5=W("ERA5", eff, gcap, cut), usd_NASA=L / (W("NASA", eff, gcap, cut) * 8.766 * 20 / 1000), usd_ERA5=L / (W("ERA5", eff, gcap, cut) * 8.766 * 20 / 1000)))
add("Verified 14 m Dandelion", 0, 0)
add("Add the extra 7 t of pad concrete", 770, 770)
add("One shared open-source controller", -(178 + 117) * ng + 120, (-(178 + 117) * ng + 120) * 1.3)
s = -.35 * steel; add("Used pipe for the tripod, repainted", s, s * 1.2)
f = -fab * 5.5 * 1.15; add("Used sailcloth, replaced twice as often", f, f + fab * 1.5 * 1.15 * 3 - fab * 7 * .8)
g = (75 * 4 - 261 * ng); add("Four salvaged washer motors", g + 80, (g + 80) * 1.3, e=.75 / .84, c=1800., ct=3.)
json.dump(dict(steps=steps), open("out/cheaper.json", "w"), indent=1)
for x in steps: print(f"{x['name']:42s} build ${x['build']:6,.0f} life ${x['life']:6,.0f} | NASA {x['W_NASA']:.0f} W ${x['usd_NASA']:.0f}/MWh | ERA5 {x['W_ERA5']:.0f} W ${x['usd_ERA5']:.0f}/MWh")
