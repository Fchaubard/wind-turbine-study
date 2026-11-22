"""Punta Mita prototype: bill of materials (prices seen 22 Nov 2026) and predicted performance -> out/proto_bom.json + PROTOTYPE.md"""
import json, math
import numpy as np
import proto as PR

MXN = 1 / 18.5      # USD per peso, rough; local items are small
V = "verified"; S = "search result only"; N = "not priced"
# (group, item, qty, unit USD, status, where, url, note)
BOM = [
 ("Carry from the US", "Pultruded carbon tube 10 mm OD × 7.3 mm ID × 48 in (DragonPlate)", 40, 21.06, V, "DragonPlate", "https://dragonplate.com/dragonplate-carbon-tube-394od-x-288id-x-48",
  "6 blade spars + 5 rings × 6 tubes + 4 spares. $21.06 is the 10+ price. Confirm 40 are in stock before paying."),
 ("Carry from the US", "Solid fibreglass rod 1/4 in × 48 in, cut into 10 cm ferrules to join ring tubes", 3, 15.00, V, "Into The Wind", "https://intothewind.com/products/fiberglass-rod",
  "6.35 mm rod inside a 7.3 mm bore: wrap with tape for a snug fit, glue one side."),
 ("Carry from the US", "UHMWPE braided line 2.0 mm, 1,000 lb, 100 ft spool", 5, 23.95, V, "Emma Kites", "https://www.emmakites.com/products/750lb-1000lb-uhmwpe-braided-line-spool",
  "6 shaft lines × 14 m + blade bridles. Peak line load in the simulation is 131 N; safe working load is about 890 N."),
 ("Carry from the US", "UHMWPE braided line 3 mm, 2,200 lb, 100 ft spool", 2, 34.95, V, "Emma Kites", "https://www.emmakites.com/products/1500lb-2200lb-5500lb-uhmwpe-braided-line-spool",
  "Lifter line and anchor strop."),
 ("Carry from the US", "Lifter kite: Jumbo Power Sled 36 (about 4 m², 5–20 mph)", 1, 195.95, V, "Into The Wind", "https://intothewind.com/products/jumbo-power-sled-36",
  "Holds the shaft up. A Peter Lynn Pilot 8 m² ($260, ships from New Zealand) lifts twice as much if it can arrive in time."),
 ("Carry from the US", "48 V 1,200 W direct-drive rear hub motor wheel, 700C", 1, 239.99, V, "ebikeling", "https://ebikeling.com/products/waterproof-48v-1200w-700c-direct-drive-front-rear-ebike-motor-wheel-only",
  "Used as the generator. Order the REAR version and confirm it has a screw-on freewheel thread; about 7 kg in checked luggage."),
 ("Carry from the US", "Single-speed freewheel, 16 tooth, standard thread", 1, 15.00, N, "any bike shop", "", "Drives the hub motor from the chain. Price is my estimate."),
 ("Carry from the US", "3-phase bridge rectifier, 90 A 1,000 V", 1, 20.65, V, "Missouri Wind and Solar", "https://windandsolar.com/products/3-phase-rectifier-90-amp", "Bolt to an aluminium plate as a heat sink."),
 ("Carry from the US", "300 W load resistor, 24 V version (2.9 ohm)", 3, 10.55, V, "Missouri Wind and Solar", "https://windandsolar.com/products/300-watt-divert-load-resistor",
  "One alone for 6 m/s wind, two in series for light wind, two in parallel for strong wind."),
 ("Carry from the US", "Victron SmartShunt 500 A (logs volts, amps, watt-hours to a phone)", 1, 117.30, V, "Shop Solar Kits", "https://shopsolarkits.com/products/victron-smartshunt", "Works from 6.5 V, so it reads from about 4 m/s wind upward."),
 ("Carry from the US", "Rigging swivel between lifter line and rotor hub", 1, 79.95, V, "HowNOT2", "https://hownot2.com/products/swivel", "Price seen; the 5 kN working load is from a search result, check the product page."),
 ("Carry from the US", "Kestrel 1000 wind meter", 1, 99.00, V, "Kestrel", "https://kestrelinstruments.com/kestrel-1000-pocket-wind-meter", "Or the Steren HER-445 locally (MX$495)."),
 ("Buy in Puerto Vallarta", "Foamular F-250 XPS foam board 1 in × 1.22 × 2.44 m", 2, 499 * MXN, V, "Home Depot Las Juntas", "https://www.homedepot.com.mx/p/owens-corning-foamular-1-pulgada-122-x-244-m-f-250-281354",
  "Blades: 6 × 1.2 m × 0.20 m, plus spares. Store stock was not shown online."),
 ("Buy in Puerto Vallarta", "3M duct tape 48 mm × 55 m (blade skin and leading edge)", 2, 199 * MXN, V, "Home Depot Las Juntas", "https://www.homedepot.com.mx/s/cinta%20ducto", ""),
 ("Buy in Puerto Vallarta", "Epoxy resin + hardener, 250 ml each (bond spars into foam)", 1, 438 * MXN, V, "Home Depot Las Juntas", "https://www.homedepot.com.mx/s/resina%20epoxica", ""),
 ("Buy in Puerto Vallarta", "Rectangular aluminium tube 1 × 2 in × 3 m (ground spider arms and deadman anchor)", 4, 249 * MXN, V, "Home Depot Las Juntas", "https://www.homedepot.com.mx/s/tubo%20aluminio", "3 arms cut to 2.4 m; the fourth is buried as the sand anchor."),
 ("Buy in Puerto Vallarta", "Stainless shackles 1/4 in and quick links", 6, 69 * MXN, V, "Zaragoza Marine", "https://www.zaragozamarine.com.mx/?s=grillete&post_type=product", ""),
 ("Buy in Puerto Vallarta", "Used adult bicycle with a 44-tooth or larger chainring", 1, 100.00, N, "local", "", "Its crank is the rotor's ground bearing; its rear triangle holds the hub motor. Price is my guess."),
 ("Buy in Puerto Vallarta", "Bolts, U-bolts, timber for the ground frame, 10 AWG wire, lugs, safety flagging", 1, 80.00, N, "Home Depot Las Juntas", "", "Price is my allowance."),
]

rot = PR.evaluate(6, 1.2, 1.2, 0.20)
pred = {}
for name, k, f in (("measured-performance basis, dataset wind", PR.K_MID, 1.0), ("same, if the beach wind is 1.3× the dataset", PR.K_MID, 1.3),
                   ("same, if the beach wind is 1.6× the dataset", PR.K_MID, 1.6), ("if it performs like Daisy's light-wind point (2.2× better)", PR.K_HI, 1.0)):
    r = PR.evaluate(6, 1.2, 1.2, 0.20, k=k, wind_f=f); pred[name] = dict(avg_W=r["avg_W"], kWh_yr=r["kWh_yr"], hours=r["hours_frac"])
curve = [dict(v=v, rpm=PR.evaluate.__call__(6, 1.2, 1.2, 0.20)["at6"]["rpm"] * v / 6.0, P_el=min(PR.K_MID * rot["cp"] * 0.5 * PR.RHO * v**3 * rot["A"], PR.P_CAP)) for v in (3, 4, 5, 6, 7, 8, 9, 10)]
total = sum(q * u for _, _, q, u, *_ in BOM)
groups = {}
for g, item, q, u, st, where, url, note in BOM:
    groups.setdefault(g, []).append(dict(item=item, qty=q, unit=u, total=q * u, status=st, where=where, url=url, note=note))
shaft = json.load(open("out/proto_shaft_1.2_2.8_5.json"))
out = dict(rotor=rot, K=dict(lo=PR.K_LO, mid=PR.K_MID, hi=PR.K_HI), calibration=PR.cal, pred=pred, curve=curve, bom=groups, total=total,
           subtotals={g: sum(r["total"] for r in rows) for g, rows in groups.items()}, shaft=shaft,
           wind=dict(mean10=float(PR.W10.mean()), frac4=float((PR.W10 >= 4).mean()), frac6=float((PR.W10 >= 6).mean()), max=float(PR.W10.max())))
json.dump(out, open("out/proto_bom.json", "w"), indent=1, default=float)

md = ["# Punta Mita prototype: parts list and predictions", "",
      "A Daisy-type rotary kite ring: six rigid foam blades on a 2.4 m ring (4.8 m rotor) spin a rope shaft that turns an e-bike hub motor on the ground. Prices seen 22 Nov 2026.", "",
      "## What to expect", "",
      f"- Rotor model calibrated to the published Daisy field measurements: real machines delivered {PR.K_MID*100:.0f}% of what the rotor theory predicts, and every number here uses that factor.",
      f"- Punta Mita wind (NASA POWER, 2022–2024, 10 m): mean {PR.W10.mean():.1f} m/s; above 4 m/s {100*(PR.W10>=4).mean():.0f}% of hours; above 6 m/s {100*(PR.W10>=6).mean():.0f}% of hours.", "",
      "| Wind | Rotor rpm | Electrical power |", "|---|---|---|"]
md += [f"| {c['v']} m/s | {c['rpm']:.0f} | {c['P_el']:.0f} W |" for c in curve]
md += ["", "| Basis | Average power | Energy per year |", "|---|---|---|"]
md += [f"| {k} | {v['avg_W']:.0f} W | {v['kWh_yr']:.0f} kWh |" for k, v in pred.items()]
md += ["", f"## Parts list (about ${total:,.0f} in total)", ""]
for g, rows in groups.items():
    md += [f"### {g} (about ${sum(r['total'] for r in rows):,.0f})", "", "| Item | Qty | Unit | Total | Price status | Where | Note |", "|---|---|---|---|---|---|---|"]
    md += [f"| {('['+r['item']+']('+r['url']+')') if r['url'] else r['item']} | {r['qty']} | ${r['unit']:,.2f} | ${r['total']:,.0f} | {r['status']} | {r['where']} | {r['note']} |" for r in rows]
    md += [""]
md += ["## Geometry", "",
       "- Blades: 6 × 1.20 m span × 0.20 m chord, 25 mm foam shaped to a flat-bottomed aerofoil, a carbon tube glued in at quarter chord, taped skin. Each blade is tied at BOTH ends (inner end to the rotor ring, outer end by a bridle line); a blade held at one end only overstresses its spar above about 6 m/s.",
       "- Rings: 5 hoops of 2.33 m diameter, each from 6 tubes joined end to end with glued ferrules. The top hoop is the rotor ring.",
       "- Shaft: 6 lines, 5 bays of 2.8 m (14 m long), flown at about 30° so the rotor hub sits about 7 m up and the lowest blade tip about 5 m up.",
       "- Ground station: the bicycle lies with its crank axis pointing up the shaft. Three 2.4 m aluminium arms bolted to the crank form a six-point spider that the six lines tie to. Chainring (44T or more) → chain → 16T freewheel on the hub motor: about 3:1 step-up. Without the step-up the generator is under 30% efficient.",
       "- Electrical: hub motor 3 phase wires → rectifier → shunt → resistor. Expect about 12 V at 4 m/s and 19 V at 6 m/s.",
       "- Anchor: one aluminium tube buried crosswise 0.8 m deep in damp sand with a 3 mm strop round its middle. Design pull 1.3 kN at 12 m/s.", "",
       "## Simulation checks", "",
       "| Wind | Shaft torque | Shaft tension | Twist per bay | Line tension | Ring buckling safety factor | Result |", "|---|---|---|---|---|---|---|"]
for c in shaft["cases"]:
    if "fea" in c:
        md.append(f"| {c['v']} m/s ({c['basis']} torque) | {c['Q']:.0f} N·m | {c['F_ax']:.0f} N | {c['max_seg_twist']:.0f}° | {c['fea'].get('max_line_T', 0):.0f} N | {c['ring_buckling_SF']:.1f} | {'stable' if not c['fea']['collapsed'] else 'COLLAPSES'} |")
md += ["", "## Test plan", "",
       "1. Day 1: log wind on the beach at head height and on a pole, morning and afternoon. If it rarely passes 4 m/s, nothing below will turn.",
       "2. Fly the lifter kite alone on the 3 mm line and learn to launch and land it.",
       "3. Spin the ground station by hand: check freewheel direction, volts per rpm, and resistor heating.",
       "4. Rotor on a short shaft (one bay) at ground level in 4–6 m/s, then add bays.",
       "5. Record wind, rpm, volts and amps together; compare with the table above.", "",
       "## Safety", "",
       "- Blade tips reach about 30 m/s at 12 m/s wind. Rope off a 30 m radius downwind and keep people out; do not fly with beachgoers nearby.",
       "- Land it above 9 m/s or when squalls approach. The highest hour in three years of data was 17 m/s.",
       "- Stay below 150 m and check for helipads nearby; no Mexican kite rule was found, which is not a clearance.",
       "- Salt and sand: rinse the hub motor and bearings; keep the rectifier and shunt in a box.", ""]
open("PROTOTYPE.md", "w").write("\n".join(md))
print(f"total ${total:,.0f}", {g: round(v) for g, v in out["subtotals"].items()}); print(pred)
