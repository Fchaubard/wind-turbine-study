"""Tower on the concrete pad: the footprint now limits the tripod. For each square pad size, find the cheapest energy design.
Foot anchors are bolts into concrete (allowance $60). Reports bolt pull per foot and the pad weight needed not to tip in a 17 m/s squall (SF 1.5)."""
import json, math, io, contextlib
import numpy as np
with contextlib.redirect_stdout(io.StringIO()):
    import rotor_limits as RL
T = RL.T; Z4 = T.Z4; FX, G = 18.5, 9.81; rows = []


def tripod_pad(D, hub, Rb):
    apex = hub - 0.25; L = math.hypot(apex, Rb); best = None
    feet = [np.array([Rb * math.cos(a), Rb * math.sin(a), 0.0]) for a in np.radians((90, 210, 330))]
    U = np.column_stack([(f - np.array([0, 0, apex])) / L for f in feet]); W = (2.2 * D**2 + 25) * G; c = {}; ten = 0.0
    for v in (12, 17):
        ts = [np.linalg.solve(U, -np.array([T.thrust(D, v) * math.cos(a), T.thrust(D, v) * math.sin(a), -W])) for a in np.radians(np.arange(0, 360, 10))]
        c[v] = max(-t.min() for t in ts); ten = max(ten, max(t.max() for t in ts))
    for nm, (od, w, mx, ln) in T.SEC.items():
        A, I, S = T.props(od, w)
        for br in (0, 1, 2, 3):
            Le = L / (br + 1); cap = min(math.pi**2 * 200e9 * I / Le**2, 230e6 * A)
            if cap / c[12] >= 2 and cap / c[17] >= 1.25:
                cost = 3 * math.ceil(L / ln) * mx / FX + br * 3 * max(1, math.ceil(1.2 * Rb / 3)) * 249 / FX + 60 + 40
                if best is None or cost < best["cost"]: best = dict(section=nm, braces=br, tubes=3 * math.ceil(L / ln), cost=cost, sf12=cap / c[12], sf17=cap / c[17], bolt_kg=ten * apex / L / G)
                break
    return best


fam = T.fam
for pad in (2.0, 3.0, 4.0, 5.0, 6.0, 8.0):
    Rb = 0.5 * pad; best = None
    for D in (4.0, 5.0, 6.0, 7.0):
        for hub in (6.0, 8.0, 10.0, 12.0):
            if hub < D / 2 + 2.5: continue
            apex = hub - .25; rt = Rb * max(apex - (hub - D / 2), 0) / apex; over = rt + .25 - D / 2 * math.sin(math.radians(8)) + .22
            if over > 1.5: continue
            t = tripod_pad(D, hub, Rb)
            if not t: continue
            for sn, (od, w, mx) in RL.SP.items():
                if 88.3 * (D / 5) ** 3 * RL.S1 / T.props(od, w)[2] > 115: continue
                pieces = 8 * math.ceil((D / 2) / 3) + 1; sail = (765 if D <= 5 else 1229 if D <= 6 else 2315) / FX; rotor = pieces * mx / FX + sail + 3 * 219 / FX + 60
                d = Z4.design(fam, D, hub, "steel tripod", "salvaged washing-machine motor", "electricity, MPPT controller")
                d["capex"] += 130 + t["cost"] - 350 * (d["A"] / 19.6) ** .6 * (hub / 6) ** 1.3 + rotor - 12 * d["A"]
                vc = min(12.0, math.sqrt(600 / (d["cp"] * .75 * .5 * 1.18 * d["A"] * d["R"] / d["tsr"])))
                v = Z4.VG; f = lambda s: float(np.minimum(np.maximum(d["cp"] * .75 * .5 * 1.18 * (v * s)**3 * d["A"] - d["qd"] * d["tsr"] * v * s / d["R"], 0) * d["eta"], d["cap"]) * (v * s <= vc) @ Z4.hist(hub, "free", 1.0)) * .97
                W = f(1.0); c5 = d["capex"] + 4 * (sail + .02 * t["cost"]); usd = c5 / (W * 8.766 * 5 / 1000)
                if best is None or usd < best["usd"]:
                    mass = 1.5 * T.thrust(D, 17) * hub / (0.5 * Rb * G) ; best = dict(pad=pad, D=D, hub=hub, spar=sn, W=W, capex=d["capex"], usd=usd, usd13=c5 / (f(1.3) * 8.766 * 5 / 1000), overhang=over, tower=t, pad_mass_kg=mass)
                break
    if best:
        rows.append(best); t = best["tower"]
        print(f"pad {pad:.0f}×{pad:.0f} m → {best['D']:.0f} m rotor, hub {best['hub']:.0f} m | {t['tubes']} × {t['section'][:22]}, {t['braces']} brace levels | {best['W']:.0f} W ${best['capex']:.0f} ${best['usd']:.0f}/MWh (1.3× ${best['usd13']:.0f}) | bolt pull {t['bolt_kg']:.0f} kg/foot | pad+tower must weigh {best['pad_mass_kg']/1000:.1f} t")
    else: print(f"pad {pad:.0f}×{pad:.0f} m → no feasible design")
json.dump(rows, open("out/pad_design.json", "w"), indent=1, default=float)
