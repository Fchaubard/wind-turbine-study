"""Final ranking: buildable gearing only (at most two bicycle chains), every concept with a charge controller so no rotor is mismatched to its load."""
import io, contextlib, json, math
with contextlib.redirect_stdout(io.StringIO()):
    import zoo_run as R
Z = R.Z; Z.RATIOS = (1.0, 2.0, 3.43, 4.0, 6.86); MPPT = 138.46
def run(c, label, **kw):
    r = Z.evaluate(dict(c, name=label, capex=c["capex"] + MPPT, mppt=True, **kw)); r["ev"] = c.get("ev"); return r
L = [run(R.wood(8.0, hub=8.0), "Wood 3-blade, 8 m"), run(R.wood(6.0, hub=6.0), "Wood 3-blade, 6 m"), run(R.wood(5.0, hub=6.0), "Wood 3-blade, 5 m"), run(R.sail(8.0, hub=8.0), "Cloth sails, 8 m"), run(R.sail(6.0, hub=6.0), "Cloth sails, 6 m"), run(R.sail(5.0, hub=6.0), "Cloth sails, 5 m"),
     run(R.disc("x", 2.5, 0.27, 5.0, 320, "M", "", n=4, gen_unit=300.0, tower_f=1.25, field=0.85), "4 props on a frame, 2.5 m", q_rotor=0.3, q_motor=0.2),
     run(R.disc("x", 1.25, 0.25, 4.0, 192, "M", "", n=16, gen_unit=180.0, tower_f=1.4, field=0.85), "16 small props (drone style)", q_rotor=0.03, q_motor=0.05),
     run(R.disc("x", 2.0, 0.293, 2.19, 260, "L", "", field=0.85), "Corkscrew, best claimed", q_rotor=0.2, q_motor=0.2)]
for c in R.C:
    for pre, lab in (("Savonius", "Savonius S-rotor"), ("H-rotor", "H-rotor"), ("Spinnaker", "Spinnaker carousel (theory cap)"), ("Wind-lens", "Wind-lens duct"), ("Cross-flow", "Cross-flow fan rotor")):
        if c["name"].startswith(pre): L.append(run(c, lab))
L.sort(key=lambda r: r["usd_per_MWh"] or 1e12)
for r in L: print(f"{r['name']:34s} {str(r['ev']):5s}{r['avg_W']:7.1f} W  ${r['capex']:5.0f}  ${r['usd_per_MWh']:6.0f}/MWh  gear {r['ratio']}")
json.dump(L, open("out/zoo3.json", "w"), indent=1, default=float)
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
D = "\\$"; S = L[:13]; fig, ax = plt.subplots(figsize=(6, 9.2), dpi=160); fig.suptitle("Every idea, same Punta Mita wind", fontsize=17, weight="bold", y=.98); fig.text(.5, .943, "cost per MWh over 5 years, lower is better (log scale)", ha="center", fontsize=9.5, color="#555")
for i, r in enumerate(S):
    y = len(S) - i; col = "#1d9e75" if r["name"].startswith(("Wood", "Cloth")) else "#b4b2a9"
    ax.barh(y, math.log10(r["usd_per_MWh"]) - 2, left=2, color=col, height=.62); ax.text(1.98, y, r["name"], ha="right", va="center", fontsize=9.3)
    ax.text(math.log10(r["usd_per_MWh"]) + .02, y, f"{D}{r['usd_per_MWh']:,.0f}  ·  {r['avg_W']:.0f} W", va="center", fontsize=8.8, weight="bold")
ax.set_xlim(.75, 4.65); ax.set_ylim(.4, len(S) + .6); ax.axis("off"); fig.subplots_adjust(left=.01, right=.99, top=.93, bottom=.17)
for j, (t, w) in enumerate((("No idea gets near $10 at this wind speed. Rotor size and site matter most.", "bold"), ("Corkscrew, tiny props, ducts: lose on cost using published test data.", "normal"), ("A beach just 1.3× windier than the data cuts cost per MWh by more than half.", "normal"), ("So measure your exact spot first: a $99 wind meter is the next buy.", "bold"))):
    fig.text(.05, .125 - j * .029, t.replace("$", D), fontsize=9.6, weight=w)
fig.savefig("out/zoo_rank.png")
