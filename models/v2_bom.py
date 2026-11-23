"""Energy, order list and build guide for machine v2. Assumptions: NASA POWER wind, 4 x 4 m pad, hub-motor generator. 'seen' = price read on the seller's page 22 Nov 2026."""
import json, math
import numpy as np, io, contextlib
with contextlib.redirect_stdout(io.StringIO()):
    import zoo4 as Z4
FX = 18.5; HD = "https://www.homedepot.com.mx"
C = json.load(open("out/cad2/v2.json")); FE = json.load(open("out/v2_fea.json")); fam = next(f for f in Z4.FAM if f[0].startswith("Cloth-sail"))
d = Z4.design(fam, 7.0, 12.0, "steel tripod", "e-bike hub motor", "electricity, MPPT controller")
k = d["cp"] * .75 * .5 * 1.18 * d["A"] * d["R"] / d["tsr"]; REEF = min(12.0, math.sqrt(500 / k)); v = Z4.VG
def W(s=1.0): return float(np.minimum(np.maximum(d["cp"] * .75 * .5 * 1.18 * (v * s)**3 * d["A"] - d["qd"] * d["tsr"] * v * s / d["R"], 0) * d["eta"], d["cap"]) * (v * s <= REEF) @ Z4.hist(12.0, "free", 1.0)) * .97
curve = {u: float(min(max(d["cp"] * .75 * .5 * 1.18 * u**3 * d["A"] - d["qd"] * d["tsr"] * u / d["R"], 0) * d["eta"], d["cap"])) for u in (3, 4, 5, 6, 7)}
B = [("Carry in from the US", "48 V 1,200 W direct-drive REAR hub motor wheel, 700C", 1, 239.99, "USD", "seen", "https://ebikeling.com/products/waterproof-48v-1200w-700c-direct-drive-front-rear-ebike-motor-wheel-only", "Generator. Confirm it has a screw-on freewheel thread before paying."),
 ("Carry in from the US", "1,000 W wind MPPT charge controller, 12/24/48 V", 1, 178.46, "USD", "seen", "https://www.ato.com/1000w-wind-turbine-mppt-charge-controller", "Holds the rotor at its best speed."),
 ("Carry in from the US", "3-phase bridge rectifier, 90 A", 1, 20.65, "USD", "seen", "https://windandsolar.com/products/3-phase-rectifier-90-amp", ""),
 ("Carry in from the US", "300 W dump resistor, 2.9 ohm", 4, 10.55, "USD", "seen", "https://windandsolar.com/products/300-watt-divert-load-resistor", "Test load and overspeed protection."),
 ("Carry in from the US", "Victron SmartShunt 500 A", 1, 117.30, "USD", "seen", "https://shopsolarkits.com/products/victron-smartshunt", "Logs power to your phone."),
 ("Home Depot Las Juntas", "Galvanised post tube 73 mm x 3.05 m", 12, 545, "MXN", "seen", HD + "/p/tauro-tuberia-para-postes-73-mm-std-305-m-851969", "Three legs, four tubes each."),
 ("Home Depot Las Juntas", "Thin-wall conduit 1 in x 3 m", 21, 249, "MXN", "seen", HD + "/p/rymco-tubo-conduit-metal-pared-delgada-1-pulgada-sin-rosca-830785", "9 braces, 12 cut into 36 one-metre leg splints."),
 ("Home Depot Las Juntas", "Thin-wall conduit 1-1/4 in x 3 m", 17, 329, "MXN", "seen", HD + "/b/electrico/conduit-cajas-y-accesorios/tuberia-conduit", "8 spars of two sleeved lengths, plus bowsprit. Wall thickness not shown online: check it is about 1.65 mm."),
 ("Home Depot Las Juntas", "Polyethylene tarp 9.14 x 6.09 m", 1, 2315, "MXN", "seen", HD + "/p/everbilt-lona-para-pintar-uso-general-914-x-609-m-polietileno-impermeable-152701-152701", "Eight sails. Replace about yearly."),
 ("Home Depot Las Juntas", "Polyester rope 6.3 mm x 30 m", 3, 219, "MXN", "seen", HD + "/p/cuerda-de-poliester-trenzada-63-mm-304-m-mfp4100-992046", "16 stays, sheets, lashings."),
 ("Home Depot Las Juntas", "Plywood 15 mm, 1.22 x 2.44 m", 2, 599, "MXN", "seen", HD + "/p/marini-triplay-cdx-15-mm-para-construccion-165700", "Hub discs and tail vane. Seal with paint."),
 ("Puerto Vallarta, estimate", "Welding shop: apex plate, yaw post and head beam (2 in Sch 80), 3 base plates with hinges", 1, 4500, "MXN", "estimate", "", "Two feet hinged so the tower can be lowered."),
 ("Puerto Vallarta, estimate", "Two trailer wheel hubs with spindles", 2, 900, "MXN", "estimate", "", "Sealed bearings: one for yaw, one for the rotor."),
 ("Puerto Vallarta, estimate", "Motorcycle 428 chain, 53T and 14T sprockets", 1, 1100, "MXN", "estimate", "", "First gear stage."),
 ("Puerto Vallarta, estimate", "Bicycle chain, 48T ring, 12T freewheel, jackshaft, 2 pillow blocks", 1, 1400, "MXN", "estimate", "", "Second gear stage, 15:1 overall."),
 ("Puerto Vallarta, estimate", "Epoxy anchors M16 stainless (12), stainless U-bolts, bolts", 1, 4000, "MXN", "estimate", "", "Foot bolts must hold 1,700 kg per foot."),
 ("Puerto Vallarta, estimate", "Zinc primer, marine paint, 3-core cable 20 m, lugs, grease", 1, 2200, "MXN", "estimate", "", "Salt protection."),
 ("Puerto Vallarta, estimate", "Hand winch, 12 m of 3/16 in cable, gin pole", 1, 2500, "MXN", "estimate", "", "To raise and lower the tower.")]
rows = [dict(group=g, item=i, qty=q, unit=u, cur=c, usd=q * u / (FX if c == "MXN" else 1), status=s, url=l, note=n) for g, i, q, u, c, s, l, n in B]
total = sum(r["usd"] for r in rows); wear = 2315 / FX + 40; c5 = total + 4 * wear; a = W(); a13 = W(1.3)
R = dict(total=total, wear=wear, reef=REEF, W=a, kWh=a * 8.766, usd=c5 / (a * 8.766 * 5 / 1000), W13=a13, usd13=c5 / (a13 * 8.766 * 5 / 1000), curve=curve, seen=sum(r["usd"] for r in rows if r["status"] == "seen"), rows=rows)
json.dump(R, open("out/v2_bom.json", "w"), indent=1, default=float)
g = {}; [g.setdefault(r["group"], []).append(r) for r in rows]
md = ["# Punta Mita wind machine v2", "", "7 m cloth-sail rotor that turns into the wind, on a 12 m steel tripod bolted to a concrete pad. Supersedes `SAIL_WINDMILL.md`.", "", "![CAD](cad2/iso.png)", "",
      "**Assumptions:** NASA POWER wind for 2022–2024 unchanged at this spot, a sound 4 x 4 m pad, published sail-rotor efficiency, and estimated prices where marked.", "",
      f"- **Output:** {a:.0f} W average, {a*8.766:.0f} kWh a year ({a13:.0f} W if the spot is 1.3× windier).", f"- **Parts:** about ${total:,.0f}, of which ${R['seen']:,.0f} is at prices seen on seller pages.", f"- **Cost of energy:** about ${R['usd']:,.0f} per MWh over five years (${R['usd13']:,.0f} at 1.3× wind).", f"- **Reef the sails above {REEF:.1f} m/s.** Lower the tower for any tropical storm or hurricane warning.", "",
      "## Structural simulation (12 wind directions)", "", "| Case | Lowest safety factor | Where | Pull per foot |", "|---|---|---|---|"] + [f"| {c['name']} | {c['min_SF']:.2f} | {c['where']} | {c['bolt_pull_kg']:.0f} kg |" for c in FE] + ["", "A safety factor below 1 means failure. **The standing tower does not survive 35 m/s or more, so it must be lowered before a storm.**", "", "## Order list", ""]
for n, rs in g.items():
    md += [f"### {n} (about ${sum(r['usd'] for r in rs):,.0f})", "", "| Item | Qty | Unit | Price | Note |", "|---|---|---|---|---|"] + [f"| {('['+r['item']+']('+r['url']+')') if r['url'] else r['item']} | {r['qty']} | {'MX$' if r['cur']=='MXN' else '$'}{r['unit']:,.2f} | {r['status']} | {r['note']} |" for r in rs] + [""]
md += ["## Not verified", "", "- Welds, bolted splices and the plywood hub are not simulated. Have the welder check the head.", "- Fatigue, gust dynamics and yaw stability are not simulated.", "- Pad condition and anchor pull-out strength must be checked on site.", "- Raising a 12 m tower can kill someone: use the winch and gin pole, keep everyone outside the fall zone.", ""]
open("BUILD_V2.md", "w").write("\n".join(md))
print(f"total ${total:,.0f} (seen ${R['seen']:,.0f}); {a:.1f} W, {a*8.766:.0f} kWh/yr, reef {REEF:.1f} m/s, ${R['usd']:.0f}/MWh; 1.3x wind {a13:.0f} W, ${R['usd13']:.0f}/MWh; W at 3-7 m/s", {k: round(x) for k, x in curve.items()})
