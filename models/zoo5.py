"""Independent check of the best ideas from Astra and Gemini on equal terms: same hourly wind, same structure cost scaled from the
simulated 7 m machine, and the same 5- and 20-year accounting. Products differ, so each is priced per MWh of its own product."""
import json, math, io, contextlib
import numpy as np
with contextlib.redirect_stdout(io.StringIO()):
    import zoo4 as Z4
#              product            conversion $, efficiency, drag N·m at machine, machine rpm, rated W, extra: output per shaft unit
P = {"electricity": (735, .74, 1.0, 300, 1200, 1.0), "hot water": (320, .92, .2, 60, 5000, 1.0), "pumped water": (450, .62, .5, 40, 3000, 1.0), "cooling": (1500, .75, 4.0, 800, 3000, 2.6 * .75)}
#      idea                                   from      product       cp range      tsr  $/m2 wear yaw   h/v  sizes
I = [("7 m cloth sails (current build)",      "Claude", "electricity", (.18,.23,.30), 1.4, 12, 3.2, "free","h",(7,)),
     ("Rigid 2-blade rotor, tilt-down",       "Gemini", "electricity", (.26,.36,.40), 7.0, 40, .5, "free","h",(5,6,7,8,10,12)),
     ("Efficient wooden rotor",               "Astra",  "electricity", (.28,.38,.42), 6.0, 40, .5, "free","h",(5,6,7,8,10)),
     ("Spoked bicycle-wheel rim drive",       "Gemini", "electricity", (.16,.26,.33), 2.5, 26, 2.0, "free","h",(6,8,10,12,14)),
     ("Sailwing → A/C compressor, ice",       "Gemini", "cooling",     (.18,.25,.33), 4.0, 18, 2.0, "free","h",(6,8,10)),
     ("Vertical rotor → refrigeration",       "Astra",  "cooling",     (.15,.26,.32), 2.0, 50, .8, "omni","v",(4,5,6,7)),
     ("Cambered fabric sailwheel → pump",     "Astra",  "pumped water",(.12,.25,.30), 1.5, 14, 2.5, "free","h",(5,6,7,8,10)),
     ("Cretan sails → diaphragm pump",        "Gemini", "pumped water",(.12,.18,.25), 1.3, 12, 2.5, "free","h",(5,6,8,10)),
     ("Darrieus → paddle churn hot water",    "Gemini", "hot water",   (.15,.26,.34), 3.5, 45, .5, "omni","v",(4,5,6,7,8)),
     ("Rigid rotor → paddle churn hot water", "Claude", "hot water",   (.26,.36,.40), 5.0, 40, .5, "free","h",(5,6,7,8,10))]
CT = 0.615; rows = []
def build(f, D):
    name, src, pr, (lo, cp, hi), tsr, c2, w2, yaw, typ, _ = f; A = math.pi * D * D / 4 if typ == "h" else D * D * .75; R = D / 2; hub = max(8.0, D / 2 + 3.5) if typ == "h" else max(5.0, D * .6 + 2.5)
    conv, eta, qm, rpm, cap, mult = P[pr]; rpm5 = tsr * 5 / R * 60 / (2 * math.pi); gear = max(1.0, rpm / rpm5); st = 0 if gear <= 1.2 else 1 if gear <= 4.5 else 2 if gear <= 18 else 3
    struct = 1330 * (A / 38.5) ** .85 * (hub / 12) * (.8 if yaw == "omni" else 1); conv2 = conv * (1 + .4 * max(A / 38.5 - 1, 0))
    capex = struct + c2 * A + conv2 + 180; wear = w2 * A + .02 * struct + .03 * conv2
    d = dict(fam=name, src=src, prod=pr, D=D, hub=hub, A=A, R=R, cp=cp, lo=lo, hi=hi, tsr=tsr, yaw=yaw, tf=1.0, ff=1.0, eta=eta * .95 ** st * mult, qd=3.0 * A / 19.6 + qm * gear / .9, cap=cap * mult, avail=.97, capex=capex, wear=wear, conv=conv2)
    T17 = CT * .5 * 1.18 * 289 * A * (.6 if tsr >= 4 else 1); d["pad_t"] = 1.5 * T17 * hub / (2.0 * 9.81) / 1000; return d
def usd(d, W, y, cost=1.0): return ((d["capex"] + d["wear"] * (y - 1) + (d["conv"] * .3 if y > 10 else 0)) * cost) / (W * 8.766 * y / 1000) if W > .1 else 1e7
rng = np.random.default_rng(9); out = []
for f in I:
    best = min((build(f, float(D)) for D in f[9]), key=lambda d: usd(d, Z4.power(d), 20)); W = Z4.power(best); samp = []
    for _ in range(1500):
        samp.append(usd(best, Z4.power(best, rng.uniform(.85, 1.5), rng.triangular(best["lo"], best["cp"], best["hi"]), rng.uniform(.6, 2)), 20, rng.uniform(.85, 1.6)))
    best.update(W=W, u5=usd(best, W, 5), u20=usd(best, W, 20), u20w=usd(best, Z4.power(best, 1.3), 20), p10=float(np.percentile(samp, 10)), p90=float(np.percentile(samp, 90))); out.append(best)
out.sort(key=lambda d: d["u20"])
print(f"{'idea':38s}{'from':8s}{'product':13s}{'size':>5s}{'output':>8s}{'capex':>7s}{'$/MWh 5y':>9s}{'20y':>6s}{'20y@1.3×':>9s}  20y range   pad t")
for d in out: print(f"{d['fam'][:37]:38s}{d['src']:8s}{d['prod']:13s}{d['D']:4.0f}m{d['W']:7.0f}W{d['capex']:7.0f}{d['u5']:9.0f}{d['u20']:6.0f}{d['u20w']:9.0f}  {d['p10']:.0f}–{d['p90']:.0f}   {d['pad_t']:.1f}")
json.dump(out, open("out/zoo5.json", "w"), indent=1, default=float)
