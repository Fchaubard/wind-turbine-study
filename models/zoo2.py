"""Second pass: fair drag for small rotors, a charge controller (MPPT) instead of a fixed resistor, usable storage, dune speed-up."""
import io, contextlib, json
with contextlib.redirect_stdout(io.StringIO()):
    import zoo_run as R
Z = R.Z; MPPT = 178.46; BATT = 519.99     # ATO 500/1000 W wind MPPT; LiTime 24 V 100 Ah (both seen on the sellers' pages)
rows = []
def run(c, label, extra=0.0, **kw):
    q = dict(c, name=label, capex=c["capex"] + extra, **kw); r = Z.evaluate(q); rows.append(r); return r
run(R.disc("x", 1.25, 0.25, 4.0, 192, "M", "", n=16, gen_unit=180.0, tower_f=1.4, field=0.85), "16 small props, low-drag generators", q_rotor=0.03, q_motor=0.05)
run(R.disc("x", 2.5, 0.27, 5.0, 320, "M", "", n=4, gen_unit=300.0, tower_f=1.25, field=0.85), "4 props, 2.5 m, low-drag generators", q_rotor=0.3, q_motor=0.2)
run(R.disc("x", 2.0, 0.293, 2.19, 260, "L", "", field=0.85), "Corkscrew 2 m, best claimed Cp, low drag", q_rotor=0.2, q_motor=0.2)
for D in (5, 6, 7, 8):
    for hub in (6, 8):
        if hub >= D / 2 + 2.5:
            run(R.sail(float(D), hub=float(hub)), f"Sail {D} m, hub {hub} m, fixed resistor")
            run(R.sail(float(D), hub=float(hub)), f"Sail {D} m, hub {hub} m, MPPT", MPPT - 40, mppt=True)
            run(R.wood(float(D), hub=float(hub)), f"Wood {D} m, hub {hub} m, MPPT", MPPT - 40, mppt=True)
rows.sort(key=lambda r: r["usd_per_MWh"] or 1e12)
for r in rows[:9]: print(f"{r['name']:44s} {r['avg_W']:6.1f} W  ${r['capex']:5.0f}  ${r['usd_per_MWh']:5.0f}/MWh  gear {r['ratio']}")
print("...")
for r in rows:
    if r["name"].startswith(("16 small", "4 props", "Corkscrew")): print(f"{r['name']:44s} {r['avg_W']:6.1f} W  ${r['capex']:5.0f}  ${r['usd_per_MWh']:5.0f}/MWh")
b = rows[0]; nm = b["name"]; D = int(nm.split()[1]); hub = int(nm.split("hub ")[1].split()[0]); fn = R.sail if nm.startswith("Sail") else R.wood
base = fn(float(D), hub=float(hub)); ex = MPPT - 40 if "MPPT" in nm else 0; kw = dict(mppt=True) if "MPPT" in nm else {}
scen = {"Winner, dataset wind": run(base, "a", ex, **kw), "+ battery so the power is usable": run(base, "b", ex + BATT, **kw),
        "Winner, beach 1.1× windier (dune)": run(base, "c", ex, speedup=1.1, **kw), "Winner, beach 1.3× windier": run(base, "d", ex, speedup=1.3, **kw), "Winner, beach 0.85× (sheltered)": run(base, "e", ex, speedup=0.85, **kw)}
for k, r in scen.items(): print(f"{k:40s} {r['avg_W']:6.1f} W  ${r['capex']:5.0f}  ${r['usd_per_MWh']:5.0f}/MWh")
json.dump(dict(top=rows[:12], winner=b, scenarios={k: {a: v for a, v in r.items()} for k, r in scen.items()}), open("out/zoo2.json", "w"), indent=1, default=float)
