import json, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt, matplotlib.image as mi
F = json.load(open("out/dandelion_final.json")); c = {x["name"]: x for x in F["cases"]}
fig = plt.figure(figsize=(6, 10), dpi=170, facecolor="#faf9f5"); ax = fig.add_axes([.08, .43, .84, .47]); ax.imshow(mi.imread("out/cad4/iso.png")[70:-40, 110:-110]); ax.axis("off")
fig.text(.06, .955, "The Dandelion", fontsize=22, weight="bold", color="#1f1e1d"); fig.text(.06, .925, "10 m fabric blades on free hinges, downwind, no tail", fontsize=11, color="#5e5d59")
for i, (b, s) in enumerate(((f"\\${F['usd']:.0f}", "per MWh, 20 years"), (f"{F['W']:.0f} W", f"average, {F['W']*8.766:,.0f} kWh/yr"), (f"\\${F['capex']:,.0f}", "parts"))):
    x = .06 + i * .31; fig.text(x, .385, b, fontsize=22, weight="bold", color="#c2552d" if i == 0 else "#1f1e1d"); fig.text(x, .362, s, fontsize=8.8, color="#5e5d59")
ax2 = fig.add_axes([.31, .19, .6, .14]); N = ["Dandelion", "Sail Ladder", "10 m wood rotor"]; V = [F["usd"], 130, 134]; ax2.barh(N[::-1], V[::-1], color=["#b9b5aa", "#b9b5aa", "#c2552d"], height=.56); ax2.set_xlim(0, 165); ax2.set_facecolor("#faf9f5")
for s in ax2.spines.values(): s.set_visible(False)
ax2.tick_params(length=0, labelsize=9.5); ax2.set_xticks([])
for i, v in enumerate(V[::-1]): ax2.text(v + 3, i, f"\\${v:.0f}", va="center", fontsize=9.5)
L = ["Still far from \\$10. About 22% cheaper than the rotor.", f"Survives 17 m/s with every safety failed (safety factor {c['17 m/s, ALL safeties failed']['sf']:.2f}).", "Needs a 9 t pad. Lower the tower for hurricanes.", "Unproven: sailwing efficiency, hinges, governor. Prices partly estimated."]
for i, t in enumerate(L): fig.text(.06, .155 - i * .033, t, fontsize=9.6, color="#1f1e1d")
fig.savefig("out/dandelion_summary.png", facecolor=fig.get_facecolor())
