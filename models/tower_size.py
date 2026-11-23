"""Size real towers from Home Depot Mexico sections for cloth-sail rotors, then re-rank rotor size with the true tower cost.
Two towers: a guyed tilt-up pole (guys must attach below the blade tips, so the top is a cantilever) and a guyless tripod.
Criteria: yield SF >= 2 and buckling SF >= 2 at 12 m/s with sails set; both >= 1.25 at 17 m/s with sails set (squall before reefing)."""
import json, math
import numpy as np
import zoo4 as Z4

E, FY, G, FX = 200e9, 230e6, 9.81, 18.5
CT = 1025.0 / (0.5 * 1.18 * 144 * 19.63)         # thrust coefficient from the 5 m whole-system simulation at 12 m/s
# OD m, wall m, MXN per length, length m. Thick-wall conduit walls and lengths are assumed (the listing did not show them)
SEC = {"73 mm post tube, 1.2 mm wall": (0.073, 0.0012, 545, 3.05), "1-1/2 in thick-wall conduit": (0.0483, 0.0030, 579, 3.0), "2 in thick-wall conduit": (0.0603, 0.0034, 839, 3.0)}


def props(od, w):
    i = od - 2 * w; return math.pi / 4 * (od**2 - i**2), math.pi / 64 * (od**4 - i**4), math.pi / 32 * (od**4 - i**4) / od


def thrust(D, v): return CT * 0.5 * 1.18 * v * v * math.pi * D * D / 4


def guyed(D, hub):
    guy_z = hub - D / 2 - 0.3; arm = hub - guy_z; out = []
    for nm, (od, w, mx, ln) in SEC.items():
        A, I, S = props(od, w)
        for bundle in (1, 2, 3):                       # tubes clamped side by side at the top section
            Mcap = FY * S * bundle
            sf12, sf17 = Mcap / (thrust(D, 12) * arm), Mcap / (thrust(D, 17) * arm)
            if sf12 >= 2 and sf17 >= 1.25:
                n = math.ceil(hub / ln) + (bundle - 1) * math.ceil((arm + 1.0) / ln)
                cost = n * mx / FX + (4 * math.hypot(guy_z, 0.7 * guy_z) * 27 + 16 * 22) / FX + 4 * 25 + 45        # cable, clamps, 4 buried anchors, hinge
                out.append(dict(type="guyed tilt-up", section=nm, bundle=bundle, tubes=n, cost=cost, sf12=min(sf12, 99), sf17=sf17, uplift_kg=thrust(D, 17) * hub / (1.4 * guy_z) / G)); break
    return min(out, key=lambda r: r["cost"]) if out else None


def tripod(D, hub):
    apex = hub - 0.25; out = []
    for ratio in (0.30, 0.40, 0.50):
        Rb = ratio * apex; L = math.hypot(apex, Rb)
        feet = [np.array([Rb * math.cos(a), Rb * math.sin(a), 0.0]) for a in np.radians((90, 210, 330))]
        U = np.column_stack([(f - np.array([0, 0, apex])) / L for f in feet]); W = (2.2 * D**2 + 25) * G
        c = {}
        for v in (12, 17):
            c[v] = max(-np.linalg.solve(U, -np.array([thrust(D, v) * math.cos(a), thrust(D, v) * math.sin(a), -W])).min() for a in np.radians(np.arange(0, 360, 10)))
        for nm, (od, w, mx, ln) in SEC.items():
            A, I, S = props(od, w)
            for braces in (0, 1, 2):
                Le = L / (braces + 1)
                b12, b17 = min(math.pi**2 * E * I / Le**2, FY * A) / c[12], min(math.pi**2 * E * I / Le**2, FY * A) / c[17]
                if b12 >= 2 and b17 >= 1.25:
                    n = 3 * math.ceil(L / ln); cost = n * mx / FX + braces * 3 * 2 * Rb * 0.6 / 3 * 249 / FX + 3 * 25 + 40
                    out.append(dict(type="tripod", section=nm, bundle=1, tubes=n, braces=braces, base_radius=Rb, cost=cost, sf12=b12, sf17=b17, uplift_kg=c[17] * apex / L / G * 0.8)); break
    return min(out, key=lambda r: r["cost"]) if out else None


fam = next(f for f in Z4.FAM if f[0].startswith("Cloth-sail")); rows = []
for D in (3.0, 4.0, 5.0, 6.0, 7.0):
    for hub in (6.0, 8.0, 10.0, 12.0):
        if hub < D / 2 + 2.5: continue
        for t in (guyed(D, hub), tripod(D, hub)):
            if not t: continue
            for gn in ("e-bike hub motor", "salvaged washing-machine motor"):
                d = Z4.design(fam, D, hub, "steel tripod", gn, "electricity, MPPT controller")
                tw0 = 350 * (d["A"] / 19.6) ** 0.6 * (hub / 6) ** 1.3
                d["capex"] += t["cost"] - tw0; d["wear"] += 0.02 * (t["cost"] - tw0)
                W = Z4.power(d); rows.append(dict(D=D, hub=hub, gen=gn, tower=t, W=W, capex=d["capex"], usd=Z4.usd_mwh(d, W), usd13=Z4.usd_mwh(d, Z4.power(d, 1.3))))
rows.sort(key=lambda r: r["usd"]); seen = set()
print("best per rotor size (dataset wind):")
for r in rows:
    if r["D"] in seen: continue
    seen.add(r["D"]); t = r["tower"]
    print(f" {r['D']:.0f} m hub {r['hub']:.0f} | {t['type']:13s} {t['tubes']:2d} × {t['section'][:27]:27s}{' ×'+str(t['bundle']) if t['bundle']>1 else ''} ${t['cost']:4.0f} SF {t['sf12']:.1f}/{t['sf17']:.1f} uplift {t['uplift_kg']:.0f} kg | {r['gen'][:9]} | {r['W']:5.1f} W ${r['capex']:5.0f} ${r['usd']:4.0f}/MWh (1.3× wind ${r['usd13']:.0f})")
json.dump(rows[:60], open("out/tower_size.json", "w"), indent=1, default=float)
