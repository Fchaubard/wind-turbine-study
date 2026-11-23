"""Run every concept through zoo.py using measured coefficients from the literature check, then size sweeps and a Monte Carlo on the leaders.
Evidence: H = measured, read at source; M = one test or secondary; L = snippet or simulation; none = no measurement, theory cap used."""
import json, math
import numpy as np
import zoo as Z


def capex(area, hub, rotor, yaw=True, gens=1, gen_unit=420.0, tower_f=1.0):
    return gen_unit * gens + 130 * (gens if gens < 3 else 2) + tower_f * 350 * (area / 19.6) ** 0.6 * (hub / 6) ** 1.3 + (70 if yaw else 0) + rotor


def disc(name, D, cp, tsr, rotor, ev, source, hub=None, wear=0.0, field=0.75, n=1, gen_unit=420.0, tower_f=1.0, **kw):
    a = math.pi * D * D / 4; h = hub or max(6.0, D / 2 + 3.5)
    return dict(name=name, cp=cp, tsr=tsr, area=a, radius=D / 2, hub=h, yaw="free", n=n, field=field, ev=ev, source=source, wear_per_year=wear,
                capex=capex(a * n, h, rotor, True, n, gen_unit, tower_f), q_rotor=3.0 * (D / 5) ** 2, q_motor=1.0 if n == 1 else 0.3, **kw)


def vawt(name, H, Dia, cp, tsr, rotor, ev, source, wear=0.0, **kw):
    a = H * Dia; h = max(4.0, H / 2 + 2.5)
    return dict(name=name, cp=cp, tsr=tsr, area=a, radius=Dia / 2, hub=h, yaw="omni", ev=ev, source=source, wear_per_year=wear, capex=capex(a, h, rotor, False), q_rotor=2.0, q_motor=1.0, **kw)


def sail(D, **kw):
    A = math.pi * D * D / 4
    return disc(kw.pop("name", f"Cloth-sail rotor, {D:g} m"), D, 0.23, 1.4, 230 * A / 19.6, "H", "Chowdhury 1987; Klabklay 2021", wear=41 * A / 19.6, **kw)


def wood(D, **kw):
    return disc(kw.pop("name", f"Hand-carved 3-blade wood rotor, {D:g} m"), D, 0.27, 5.0, 190 * (D / 3.6) ** 2.5, "H", "Singh & Ahmed (field, 1.26 m)", wear=10, field=0.85, width=0.7, **kw)


C = [sail(5.0), wood(3.6),
     disc("Corkscrew spiral, 2 m (best claimed Cp)", 2.0, 0.293, 2.19, 260, "L", "Jeju simulation + field", field=0.85),
     disc("Corkscrew spiral, 2 m (independently measured)", 2.0, 0.072 / 0.8, 0.5, 260, "M", "Mercu Buana, 272 mm", field=1.0),
     disc("16 small props on one frame, 1.25 m each", 1.25, 0.25, 4.0, 16 * 12.0, "M", "Singh & Ahmed Cp; +1.8% array gain (Vestas)", n=16, gen_unit=180.0, tower_f=1.4, field=0.85),
     disc("4 props on one frame, 2.5 m each", 2.5, 0.27, 5.0, 4 * 80.0, "M", "Singh & Ahmed Cp", n=4, gen_unit=300.0, tower_f=1.25, field=0.85),
     vawt("H-rotor (straight-blade), 3 × 3 m", 3.0, 3.0, 0.225, 1.2, 420, "H", "Keisar, Technion"),
     vawt("Twisted Darrieus, 3 × 3 m", 3.0, 3.0, 0.14, 0.5, 560, "L", "tunnel snippet"),
     vawt("Savonius S-rotor, tarp, 4 × 2 m", 4.0, 2.0, 0.24, 0.9, 260, "H", "Sandia SAND76-0131", wear=25),
     vawt("Hybrid Savonius-Darrieus, 3 × 3 m", 3.0, 3.0, 0.26, 2.7, 560, "L", "micro-scale snippet"),
     vawt("Spinnaker drag carousel, 4 × 3 m (theory cap)", 4.0, 3.0, 0.15, 0.33, 240, "none", "no measurement; drag-device limit about 0.15", wear=40),
     disc("Wind-lens duct on a 1.8 m rotor", 2.05, 0.50, 5.0, 620, "H", "Kanya & Visser, on exit area", field=0.85),
     disc("Cross-flow (fan) rotor with vanes, 2.8 m equivalent", 2.8, 0.30, 0.5, 340, "M", "Almaaitah 1 × 1 m; other test 0.059"),
     disc("Magnus spinning cylinders, 3 m", 3.0, 0.075, 1.0, 520, "L", "AIA review"),
     vawt("Bladeless oscillating mast, 2 × 1 m", 2.0, 1.0, 0.06, 1.0, 180, "M", "modelled only (Breen 2025)"),
     vawt("Flutter ribbon, 2 × 1 m", 2.0, 1.0, 0.023, 1.0, 90, "M", "UVic tunnel")]
rank = sorted((dict(Z.evaluate(c), ev=c["ev"]) for c in C), key=lambda r: r["usd_per_MWh"] or 1e12)
print(f"{'concept':54s}{'evid':>5s}{'W avg':>7s}{'capex':>7s}{'$/MWh':>8s}  gear  ohm  reef")
for r in rank: print(f"{r['name'][:53]:54s}{r['ev']:>5s}{r['avg_W']:7.1f}{r['capex']:7.0f}{(r['usd_per_MWh'] or 0):8.0f}  {r['ratio']}  {r['R_load']}  {r['v_reef']}")
sw = []
for fam, fn in (("sail", sail), ("wood", wood)):
    for D in (3.0, 4.0, 5.0, 6.0, 7.0, 8.0):
        for hub in (6.0, 8.0, 10.0, 12.0):
            if hub < D / 2 + 2.5: continue
            r = Z.evaluate(fn(D, hub=hub)); r.update(family=fam, D=D); sw.append(r)
sw.sort(key=lambda r: r["usd_per_MWh"]); print("\nsize and height sweep, best five:")
for r in sw[:5]: print(f"  {r['family']} {r['D']:g} m, hub {r['hub']:g} m: {r['avg_W']:.1f} W, ${r['capex']:.0f}, ${r['usd_per_MWh']:.0f}/MWh, gear {r['ratio']}, {r['R_load']} ohm, reef {r['v_reef']}")
bs = {f: min((r for r in sw if r["family"] == f), key=lambda r: r["usd_per_MWh"]) for f in ("sail", "wood")}
lead = {"sail": sail(bs["sail"]["D"], hub=bs["sail"]["hub"]), "wood": wood(bs["wood"]["D"], hub=bs["wood"]["hub"]),
        "savonius": next(c for c in C if c["name"].startswith("Savonius")), "h-rotor": next(c for c in C if c["name"].startswith("H-rotor"))}
rng = np.random.default_rng(3); wins = {k: 0 for k in lead}; dist = {k: [] for k in lead}; N = 120
for _ in range(N):
    wind = float(rng.uniform(0.85, 1.5)); res = {}
    for k, c in lead.items():
        q = dict(c, cp=c["cp"] * float(rng.uniform(0.75, 1.15)), capex=c["capex"] * float(rng.uniform(0.85, 1.35)), speedup=wind, q_rotor=c["q_rotor"] * float(rng.uniform(0.6, 2.0)))
        res[k] = Z.evaluate(q)["usd_per_MWh"] or 1e9; dist[k].append(res[k])
    wins[min(res, key=res.get)] += 1
print("\nMonte Carlo (wind ×0.85–1.5, Cp −25/+15%, cost −15/+35%, drag ×0.6–2):")
for k in lead: print(f"  {k:9s} wins {100*wins[k]/N:3.0f}%   median ${np.median(dist[k]):.0f}/MWh  (10–90%: ${np.percentile(dist[k],10):.0f}–${np.percentile(dist[k],90):.0f})")
heat = dict(lead[max(bs, key=lambda f: -bs[f]["usd_per_MWh"]) if False else min(bs, key=lambda f: bs[f]["usd_per_MWh"])]); heat.update(name="Best rotor → direct hot water (no battery or inverter)")
json.dump(dict(rank=rank, sweep=sw[:40], best=bs, mc={k: dict(win=wins[k] / N, median=float(np.median(dist[k])), p10=float(np.percentile(dist[k], 10)), p90=float(np.percentile(dist[k], 90))) for k in lead}), open("out/zoo.json", "w"), indent=1, default=float)
