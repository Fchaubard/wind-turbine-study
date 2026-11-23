import json, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt, matplotlib.image as mi
B = json.load(open("out/v3_bom.json"))["best"]; V = json.load(open("out/v3_verify.json")); c = {x["name"]: x for x in V["cases"]}
fig = plt.figure(figsize=(6, 9.6), dpi=170, facecolor="#faf9f5"); ax = fig.add_axes([.04, .36, .92, .54]); ax.imshow(mi.imread("out/cad3/iso.png")[60:-40, 90:-90]); ax.axis("off")
fig.text(.06, .95, "10 m wood rotor, CAD and FEA done", fontsize=18, weight="bold", color="#1f1e1d"); fig.text(.06, .92, "12 m steel tripod on your concrete pad", fontsize=11.5, color="#5e5d59")
for i, (big, small) in enumerate(((f"\\${B['u20']:.0f}", "per MWh, 20 years"), (f"{B['W']:.0f} W", f"average, {B['W']*8.766:,.0f} kWh/yr"), (f"\\${B['capex']:,.0f}", "parts"))):
    x = .06 + i * .31; fig.text(x, .29, big, fontsize=22, weight="bold", color="#c2552d" if i == 0 else "#1f1e1d"); fig.text(x, .265, small, fontsize=8.8, color="#5e5d59")
L = [f"Was \\$339/MWh with the 7 m sails in the same model. Target \\$10 not reached.", f"Hot water instead: \\${B['heat20']:.0f}/MWh.  If your beach is 1.3× windier: \\${B['u20w']:.0f}.", f"Passes: 17 m/s with furl failed (safety {c['17 m/s, furl fails']['sf']:.1f}), no tower resonance.", f"Pad must weigh 10 t or more. Foot bolts must hold {max(x['pull_kg'] for x in V['cases'])/1000:.1f} t each.", "Lower the tower for any hurricane warning.", "Not tested: real blades, welds, fatigue. Steel and wood prices are estimates."]
for i, t in enumerate(L): fig.text(.06, .215 - i * .034, t, fontsize=9.6, color="#1f1e1d")
fig.savefig("out/v3_summary.png", facecolor=fig.get_facecolor())
