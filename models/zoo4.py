"""Brute-force design search: 30 machine types x sizes x hub heights x towers x generators x end uses, in hourly Punta Mita wind.
Every coefficient is a stated assumption with a (low, base, high) range; 'evidence' says whether it rests on a measurement.
M = measured in the literature check, A = my assumption (no usable test found). Costs are parts, 5 years, including wear."""
import json, math, itertools
import numpy as np
import zoo as Z

RHO = Z.RHO; VG = np.arange(0.0, 20.01, 0.25); YEARS = 5
#         name                                   type  cp_lo cp   cp_hi tsr  $/m2  wear/m2/yr yaw    Dmax evid
FAM = [("Hand-carved wood 3-blade",               "h", .20, .27, .30, 5.0, 20, 0.5, "free", 8, "M"),
       ("PVC-pipe blades",                        "h", .10, .20, .28, 4.0,  9, 1.5, "free", 4, "M"),
       ("Cloth-sail (Cretan) rotor",              "h", .18, .23, .30, 1.4, 12, 2.1, "free", 8, "M"),
       ("Double-skin sailwing",                   "h", .22, .32, .38, 4.0, 18, 3.0, "free", 7, "A"),
       ("Farm-style multiblade, bamboo + tarp",   "h", .11, .20, .28, 1.0, 16, 1.5, "free", 6, "M"),
       ("Giant bicycle wheel, rim drives generator", "h", .18, .27, .33, 2.5, 26, 1.0, "free", 6, "A"),
       ("Coned downwind rotor, no tail",          "h", .16, .24, .30, 4.0, 19, 0.7, "down", 7, "A"),
       ("Tip-vane / ring-tip wood rotor",         "h", .22, .30, .34, 4.5, 30, 0.7, "free", 5, "M"),
       ("Corkscrew, growing diameter, sheet",     "h", .07, .18, .29, 2.0, 70, 1.0, "free", 3, "M"),
       ("Corkscrew cone, fabric on wire",         "h", .05, .14, .25, 1.5, 25, 3.0, "free", 4, "A"),
       ("Spiral radiating sails, angled out",     "h", .10, .20, .27, 1.3, 15, 2.1, "free", 6, "A"),
       ("Wind-lens duct",                         "h", .35, .45, .55, 5.0, 140, 1.0, "free", 3, "M"),
       ("Spinnaker bag on a rotating arm",        "h", .03, .08, .15, 0.4, 10, 3.0, "free", 7, "A"),
       ("4 rotors on one frame, one belt",        "h", .18, .25, .29, 5.0, 34, 0.6, "free", 7, "M"),
       ("16 drone-style props, one belt",         "h", .10, .20, .26, 4.0, 60, 1.0, "free", 6, "A"),
       ("Savonius, tarp",                         "v", .15, .22, .26, 0.9, 13, 1.3, "omni", 4, "M"),
       ("Savonius, split oil drums",              "v", .12, .18, .24, 0.9, 25, 0.3, "omni", 3, "M"),
       ("Twisted Savonius",                       "v", .12, .20, .25, 0.9, 30, 1.3, "omni", 3, "A"),
       ("H-rotor (straight blades)",              "v", .15, .22, .24, 1.2, 46, 0.5, "omni", 5, "M"),
       ("Twisted Darrieus",                       "v", .08, .14, .20, 0.5, 62, 0.5, "omni", 4, "M"),
       ("Hybrid Savonius-Darrieus",               "v", .12, .22, .26, 2.0, 62, 0.8, "omni", 4, "M"),
       ("Self-flipping sail carousel",            "v", .06, .13, .20, 0.4, 14, 3.0, "omni", 6, "A"),
       ("Spinnaker drag carousel",                "v", .03, .08, .15, 0.33, 20, 3.0, "omni", 6, "A"),
       ("Cross-flow fan rotor",                   "v", .06, .20, .30, 0.5, 55, 0.5, "omni", 4, "M"),
       ("Magnus spinning cylinders",              "h", .02, .07, .10, 1.0, 70, 1.0, "free", 4, "M"),
       ("Oscillating wing on a pivot",            "h", .03, .10, .18, 0.5, 30, 1.0, "free", 4, "A"),
       ("Bladeless oscillating mast",             "v", .005, .03, .06, 1.0, 90, 0.5, "omni", 2, "M"),
       ("Flutter ribbon",                         "v", .002, .02, .03, 1.0, 45, 3.0, "omni", 2, "M"),
       ("Rotary kite ring (no tower)",            "h", .03, .05, .09, 2.2, 30, 5.0, "kite", 6, "M"),
       ("Pumping soft kite on a winch",           "h", .03, .07, .12, 3.0, 12, 6.0, "kite", 8, "A")]
#        tower: cost at a 5 m rotor, 6 m hub; wear as a fraction per year; wind and field multipliers; max rotor diameter
TOWERS = {"steel tripod": (350, 0.02, 1.00, 1.00, 10), "bamboo tripod": (150, 0.25, 1.00, 0.97, 7), "roof or balcony mount": (120, 0.02, 0.95, 0.85, 4), "guyed pole": (210, 0.03, 1.00, 1.00, 7)}
#       generator: $, efficiency, cogging N·m at the generator, rated W, best rpm (assumptions except the hub motor's price)
GENS = {"e-bike hub motor": (261, 0.82, 1.0, 1200, 300), "salvaged washing-machine motor": (75, 0.75, 0.6, 500, 250), "treadmill DC motor": (55, 0.68, 0.5, 900, 1500), "car alternator": (50, 0.45, 0.6, 700, 2500)}
USES = {"electricity, MPPT controller": (178 + 53, 0.95), "hot water, heater element in a tank": (60, 0.92)}
HIST = {}


def hist(hub, yaw, tf):
    key = (hub, yaw, tf)
    if key not in HIST:
        y = {"free": "free", "down": "free", "omni": "omni", "kite": "free"}[yaw]
        v = Z.wind_at(hub, y) * tf * (math.cos(math.radians(20)) / math.cos(math.radians(10)) if yaw == "down" else 1.0)
        HIST[key] = np.histogram(np.clip(v, 0, 20), bins=np.r_[VG - 0.125, 20.125])[0] / len(v)
    return HIST[key]


def design(f, D, hub, tn, gn, un):
    name, typ, lo, cp, hi, tsr, c2, w2, yaw, Dm, ev = f
    A = math.pi * D * D / 4 if typ == "h" else D * D * 0.75; R = D / 2
    kite = yaw == "kite"
    tb, tw, tf, ff, tD = TOWERS[tn]; g = GENS[gn]; u = USES[un]
    if kite: hub = max(hub, 20.0); tower = 140.0; tw = 0.3
    else: tower = tb * (A / 19.6) ** 0.6 * (hub / 6) ** 1.3
    rpm5 = tsr * 5.0 / R * 60 / (2 * math.pi); gear = max(1.0, g[4] / rpm5)
    stages = 0 if gear <= 1.2 else (1 if gear <= 4.5 else (2 if gear <= 18 else 3))
    drive_eta = 0.95 ** stages; drive = (35 + 45 * stages) if stages else 35
    yawc = 70 if yaw == "free" else (25 if yaw == "down" else 0)
    capex = g[0] + drive + tower + yawc + c2 * A + u[0] + 117           # 117 = power logger, kept in every design
    wear = w2 * A + tw * tower
    return dict(fam=name, ev=ev, D=D, hub=hub, tower=tn if not kite else "tether + anchor", gen=gn, use=un, A=A, R=R, cp=cp, lo=lo, hi=hi, tsr=tsr, yaw=yaw, tf=tf if not kite else 1.0, ff=ff, gear=gear, stages=stages,
                eta=drive_eta * g[1] * u[1], qd=(0.12 * A / 19.6 * 3.0 / 0.12 * 1.0) + g[2] * gear / max(drive_eta, .5), cap=g[3] * u[1], capex=capex, wear=wear, avail=0.6 if kite else 0.97)


def power(d, wind=1.0, cp=None, qf=1.0):
    v = VG * wind; c = (d["cp"] if cp is None else cp) * 0.75 * d["ff"]
    Pa = c * 0.5 * RHO * v**3 * d["A"]; Pd = d["qd"] * qf * d["tsr"] * v / d["R"]
    P = np.minimum(np.maximum(Pa - Pd, 0) * d["eta"], d["cap"]) * (VG * wind <= 12.0)
    return float(P @ hist(d["hub"], d["yaw"], d["tf"])) * d["avail"]


def usd_mwh(d, W, cost=1.0): return (d["capex"] * cost + d["wear"] * (YEARS - 1)) / (W * 8.766 * YEARS / 1000) if W > 0.1 else 1e7


if __name__ == "__main__":
    rows = []
    for f in FAM:
        for D, hub, tn, gn, un in itertools.product(np.arange(2.0, f[9] + .01, 0.5), (4.0, 5.0, 6.0, 8.0, 10.0, 12.0), TOWERS, GENS, USES):
            if D > TOWERS[tn][4] or (f[1] == "h" and hub < D / 2 + 2.5) or (f[1] == "v" and hub < D * 0.5 + 2.0) or (tn.startswith("roof") and hub > 6): continue
            d = design(f, float(D), float(hub), tn, gn, un); W = power(d)
            if W > 0.5: d["W"] = W; d["usd"] = usd_mwh(d, W); rows.append(d)
    print(len(rows), "designs evaluated")
    for label, key in (("ELECTRICITY", "electricity, MPPT controller"), ("HOT WATER", "hot water, heater element in a tank")):
        best = {}
        for r in rows:
            if r["use"] == key and (r["fam"] not in best or r["usd"] < best[r["fam"]]["usd"]): best[r["fam"]] = r
        L = sorted(best.values(), key=lambda r: r["usd"])
        rng = np.random.default_rng(5); N = 3000; res = np.zeros((N, len(L)))
        for i in range(N):
            w = rng.uniform(.85, 1.5)
            for j, d in enumerate(L):
                res[i, j] = usd_mwh(d, power(d, w, rng.triangular(d["lo"], d["cp"], d["hi"]), rng.uniform(.6, 2.0)), rng.uniform(.85, 1.35))
        wins = np.bincount(res.argmin(1), minlength=len(L)) / N
        print(f"\n{label}: best design of each type (win = share of 3,000 random assumption sets where it is cheapest)")
        for j, d in enumerate(L):
            d["win"] = float(wins[j]); d["med"] = float(np.median(res[:, j])); d["p10"] = float(np.percentile(res[:, j], 10)); d["p90"] = float(np.percentile(res[:, j], 90))
            if j < 14: print(f" {d['fam'][:38]:38s} {d['ev']} {d['D']:.1f} m hub {d['hub']:.0f} | {d['tower'][:14]:14s}| {d['gen'][:18]:18s}| {d['W']:6.1f} W ${d['capex']:5.0f} ${d['usd']:6.0f}/MWh | win {100*wins[j]:3.0f}% median ${d['med']:.0f} ({d['p10']:.0f}–{d['p90']:.0f})")
        json.dump(L, open(f"out/zoo4_{'elec' if label[0]=='E' else 'heat'}.json", "w"), indent=1, default=float)
