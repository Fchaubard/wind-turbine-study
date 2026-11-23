"""Do the rotor and bicycle drivetrain survive at each size? Spar stress is scaled from the 5 m frame FEA (88 MPa at 12 m/s, 1 in conduit, two stays).
Thin-wall conduit dimensions above 1 in are assumed from the EMT standard. A bicycle crank is limited to 150 N·m continuous (assumption), so the rotor must be reefed before that."""
import json, math, io, contextlib
import numpy as np
with contextlib.redirect_stdout(io.StringIO()):
    import tower_size as T
Z4 = T.Z4; FX = 18.5
SP = {"1 in": (0.0295, 0.0012, 249), "1-1/4 in": (0.0386, 0.00165, 329), "1-1/2 in": (0.0445, 0.00165, 389), "2 in": (0.0572, 0.00165, 479)}
S1 = T.props(0.0295, 0.0012)[2]; fam = T.fam; out = []
for D in (4.0, 5.0, 6.0, 7.0):
    best = None
    for hub in (6.0, 8.0, 10.0, 12.0):
        if hub < D / 2 + 2.5: continue
        tw = T.tripod(D, hub)
        if not tw: continue
        for sn, (od, w, mx) in SP.items():
            s12 = 88.3 * (D / 5) ** 3 * S1 / T.props(od, w)[2]
            if s12 > 115: continue
            pieces = 8 * math.ceil((D / 2) / 3.0) + 1; spars = pieces * mx / FX
            sail = (765 if D <= 5 else 1229 if D <= 6 else 2315) / FX
            rotor = spars + sail + 3 * 219 / FX + 60
            for gn in ("e-bike hub motor", "salvaged washing-machine motor"):
                d = Z4.design(fam, D, hub, "steel tripod", gn, "electricity, MPPT controller")
                d["capex"] += 130 + tw["cost"] - 350 * (d["A"] / 19.6) ** 0.6 * (hub / 6) ** 1.3 + rotor - 12 * d["A"]
                k = d["cp"] * .75 * .5 * 1.18 * d["A"] * d["R"] / d["tsr"]; vq = math.sqrt(600 / k); vc = min(12.0, vq)
                v = Z4.VG; Pa = d["cp"] * .75 * d["ff"] * .5 * 1.18 * v**3 * d["A"]; Pd = d["qd"] * d["tsr"] * v / d["R"]
                P = np.minimum(np.maximum(Pa - Pd, 0) * d["eta"], d["cap"]) * (v <= vc); W = float(P @ Z4.hist(hub, "free", 1.0)) * .97
                W13 = float(np.minimum(np.maximum(d["cp"]*.75*.5*1.18*(v*1.3)**3*d["A"]-d["qd"]*d["tsr"]*v*1.3/d["R"],0)*d["eta"],d["cap"])*(v*1.3<=vc) @ Z4.hist(hub,"free",1.0))*.97
                wear = sail + 0.02 * tw["cost"]; c5 = d["capex"] + 4 * wear; usd = c5 / (W * 8.766 * 5 / 1000)
                r = dict(D=D, hub=hub, spar=sn, spar_MPa=s12, gen=gn, reef=vc, W=W, capex=d["capex"], usd=usd, usd13=c5 / (W13 * 8.766 * 5 / 1000), tower=tw, sail_per_year=sail)
                if best is None or usd < best["usd"]: best = r
    out.append(best); t = best["tower"]
    print(f"{D:.0f} m, hub {best['hub']:.0f} m | spars {best['spar']} ({best['spar_MPa']:.0f} MPa at 12 m/s) | reef at {best['reef']:.1f} m/s | {best['gen'][:9]} | tripod {t['tubes']} tubes, {t['uplift_kg']:.0f} kg per foot | {best['W']:.0f} W  ${best['capex']:.0f}  ${best['usd']:.0f}/MWh  (1.3x wind ${best['usd13']:.0f})")
json.dump(out, open("out/rotor_limits_moto.json", "w"), indent=1, default=float)
