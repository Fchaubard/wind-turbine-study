"""Bill of materials for the final 16 m Dandelion. Reconstructs the model's parts budget with the cheapest sourcing and checks it matches the verified build cost."""
import json
d = json.load(open("out/dandelion_fin_16_12_3.json")); p = d["pick"]; F = next(r for r in json.load(open("out/final_pick.json")) if r["D"] == 16 and r["ng"] == 3); fab = F["fabric_m2"]; steel = p["tower"] + d["capex"] - p["capex"]; fit = 3 * (6 * 2 + 8) + 3 * 35 + 3 * p["mt"]; spars = p["blade"] - fab * 7 * 1.15 - fit
I = [("Generators, 3, with shared controller", 733 * 3 - 295 * 3 + 120), ("Extra pad concrete, 16.7 t", 110 * (p["pad_t"] - 10)), ("Used steel tripod and head", steel * .65), ("Hub, yaw, drivetrain, hardware", 1059.), ("Laminated pine blade spars, 3", spars), ("Blade governors", 225.), ("Blade hinges and fittings", fit), ("Used sailcloth, %.0f m²" % fab, fab * 1.5 * 1.15)]; T = sum(x[1] for x in I); print(round(T), round(F["build"])); assert abs(T - F["build"]) < 2
json.dump(dict(items=I, total=T, design=F), open("out/final_bom.json", "w"), indent=1, default=float)
for n, c in I: print(f"{n:42s} ${c:,.0f}")
print({k: (round(v, 2) if isinstance(v, float) else v) for k, v in F.items() if k != "file"})
