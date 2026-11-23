import json, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
K = json.load(open("out/kite_vs.json")); B = K["best_kite"]["usd"]; D = K["dandelion"]
fig = plt.figure(figsize=(6, 7.6), dpi=170, facecolor="#faf9f5"); fig.text(.06, .94, "Can AI make kites win here?", fontsize=20, weight="bold", color="#1f1e1d"); fig.text(.06, .905, "Lifetime cost per MWh, Punta Mita wind", fontsize=11, color="#5e5d59")
N = ["Dandelion, \$80 controller", "Perfect kite, lasts 5,000 h", "Perfect kite, lasts 1,500 h", "Realistic kite, stress test"]; V = [D["usd"], B["5000"], B["1500"], None]
ax = fig.add_axes([.42, .50, .47, .36]); y = [3, 2, 1, 0]; vals = [V[0], V[1], V[2], 0]; ax.barh(y, vals, color=["#c2552d", "#b9b5aa", "#b9b5aa", "#b9b5aa"], height=.55); ax.set_yticks(y); ax.set_yticklabels(N, fontsize=9.3); ax.set_xticks([]); ax.tick_params(length=0); ax.set_xlim(0, max(vals) * 1.3); ax.set_facecolor("#faf9f5")
for s in ax.spines.values(): s.set_visible(False)
for a, v in zip(y, vals): ax.text(v + max(vals) * .02, a, f"\\${v:,.0f}" if v else "crashes", va="center", fontsize=10, weight="bold" if a == 3 else "normal")
L = ["AI did solve flight for an ideal kite: no crashes at 3.5–5 m/s.", "A slightly worse kite in rougher wind crashed constantly.", "Wind is too light 6 hours in 10, so the kite sits on the ground.", "Fabric and tether wear cost more than control.", "", f"Best machine: Dandelion, about \\${D['usd']:.0f}/MWh, \\${D['capex']:,.0f} in parts.", "Still simulated only, and still far from \\$10."]
for i, t in enumerate(L): fig.text(.06, .42 - i * .05, t, fontsize=10, color="#1f1e1d", weight="bold" if i == 5 else "normal")
fig.savefig("out/kite_summary.png", facecolor=fig.get_facecolor())
