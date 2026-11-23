"""Final order list and build guide for the chosen Punta Mita prototype: a 4 m cloth-sail windmill on a guyed pole.
Reads out/sail_design.json (whole-system simulation) -> out/sail_bom.json + SAIL_WINDMILL.md"""
import json

FX = 18.5   # MXN per USD, rough
OPT = json.load(open("out/sail_opt.json")); D = OPT["pick"]
CAD = json.load(open("out/cad/sail_windmill.json")); FEA = json.load(open("out/sail_fea.json"))
FEA_ROWS = []
for c in FEA["cases"]:
    cands = [(w["SF"], g + " stress") for g, w in c["worst"].items()] + [(v, k + " buckling") for k, v in c["buckling_SF"].items()]
    sf, where = min(cands); pf = c["reactions_N"]["pole foot"]; bf = c["reactions_N"]["back-prop foot"]
    FEA_ROWS.append(f"| {c['name']} | {c['thrust_N']:.0f} N | {sf:.1f} | {where} | {'up' if pf[2] < 0 else 'down'} {abs(pf[2])/9.81:.0f} kg | {'down' if bf[2] > 0 else 'up'} {abs(bf[2])/9.81:.0f} kg, sideways {abs(bf[0])/9.81:.0f} kg |")
HD = "https://www.homedepot.com.mx"
# (group, item, qty, unit price, currency, status, url, note)
BOM = [
 ("Bring with you (order now, US)", "48 V 1,200 W direct-drive REAR hub motor wheel, 700C (ebikeling)", 1, 239.99, "USD", "seen", "https://ebikeling.com/products/waterproof-48v-1200w-700c-direct-drive-front-rear-ebike-motor-wheel-only", "The generator. Must be the rear version with a screw-on freewheel thread; ask the seller before paying. About 7 kg."),
 ("Bring with you (order now, US)", "Single-speed freewheel, 14 tooth, standard 1.37 in thread, plus one spare bicycle chain", 1, 30.00, "USD", "estimate", "", "Any bike shop. The freewheel goes on the hub motor; the spare chain is the second stage."),
 ("Bring with you (order now, US)", "3-phase bridge rectifier 90 A", 1, 20.65, "USD", "seen", "https://windandsolar.com/products/3-phase-rectifier-90-amp", "Bolt to a metal plate."),
 ("Bring with you (order now, US)", "300 W load resistor, 24 V version (2.9 ohm)", 4, 10.55, "USD", "seen", "https://windandsolar.com/products/300-watt-divert-load-resistor", "Two wired in parallel (1.45 ohm) is the best match; the others let you try three or four in parallel and act as spares."),
 ("Bring with you (order now, US)", "Victron SmartShunt 500 A power logger", 1, 117.30, "USD", "seen", "https://shopsolarkits.com/products/victron-smartshunt", "Reads volts, amps and watt-hours on your phone from 6.5 V up."),
 ("Home Depot Las Juntas, Puerto Vallarta", "Galvanised post tube 73 mm × 3.05 m (Tauro)", 4, 545, "MXN", "seen", HD + "/p/tauro-tuberia-para-postes-73-mm-std-305-m-851969", "Two make the 6.1 m pole, two make the back-prop that leans against it from 2.2 m behind. Each pair is joined with conduit splints and U-bolts."),
 ("Home Depot Las Juntas, Puerto Vallarta", "Galvanised steel cable 3/16 in, per metre", 28, 27, "MXN", "seen", HD + "/p/fiero-cable-de-acero-galvanizado-3-16-venta-por-metro-lineal-cab-3-16r-466137", "Four side guys only (two from the top, two from the joint). No cable may cross the rotor. Rated 1,360 kg; peak simulated load is about 35 kg."),
 ("Home Depot Las Juntas, Puerto Vallarta", "Cable clamps 3/16 in, pack of 2", 12, 22, "MXN", "seen", HD + "/p/fiero-accesorio-para-cable-3-16-hierro-2-piezas-nudo-3-16-237091", "Check the photo matches a U-bolt cable clamp."),
 ("Home Depot Las Juntas, Puerto Vallarta", "Steel conduit, thin wall, 1 in × 3 m", 11, 249, "MXN", "seen", HD + "/p/rymco-tubo-conduit-metal-pared-delgada-1-pulgada-sin-rosca-830785", "Eight spars cut to 2.5 m, one bowsprit, six 1 m joint splints, two standoffs. Offcuts become stakes."),
 ("Home Depot Las Juntas, Puerto Vallarta", "Polyethylene tarp 4.87 × 3.65 m, general use", 1, 765, "MXN", "seen", HD + "/p/everbilt-lona-para-pintar-uso-general-487-x-365-m-polietileno-impermeable-152699-152699", "Eight triangular sails, about 1.6 m² each."),
 ("Home Depot Las Juntas, Puerto Vallarta", "Polyester braided rope 6.3 mm × 30 m", 3, 219, "MXN", "seen", HD + "/p/cuerda-de-poliester-trenzada-63-mm-304-m-mfp4100-992046", "Two stays per spar (to the tip and to two-thirds span), sail sheets, lashings."),
 ("Home Depot Las Juntas, Puerto Vallarta", "Plywood 15 mm, 1.22 × 2.44 m", 1, 599, "MXN", "seen", HD + "/p/marini-triplay-cdx-15-mm-para-construccion-165700", "Two 50 cm hub discs that sandwich the spars, two 10 × 58 cm doubled plates that carry the hub motor, a 40 cm pad under the back-prop foot, the electronics board."),
 ("Home Depot Las Juntas, Puerto Vallarta", "Duct tape 48 mm × 55 m", 1, 199, "MXN", "seen", HD + "/s/cinta%20ducto", "Sail edges and chafe points."),
 ("Home Depot Las Juntas, Puerto Vallarta", "U-bolts, M8 bolts, washers, 10 AWG wire (15 m), lugs", 1, 1500, "MXN", "estimate", "", "My allowance."),
 ("Puerto Vallarta, other", "Used adult bicycle with a 48-tooth chainring and a 7-speed rear cluster (14 to 28 teeth)", 1, 1850, "MXN", "estimate", "", "Its crank is the rotor shaft and its own rear wheel is the step-up shaft: chain one runs chainring to the 14-tooth cog, chain two runs from the 28-tooth cog to the hub motor. Price is my guess."),
 ("Home Depot Las Juntas, Puerto Vallarta", "Timber 2 × 6 in, 1 m lengths, for buried anchors", 4, 120, "MXN", "estimate", "", "One under the pole foot (it is pulled upward in strong wind), one behind the prop foot, one per side-guy pair."),
 ("Puerto Vallarta, other", "Steren HER-445 digital anemometer", 1, 495, "MXN", "seen", "https://www.steren.com.mx/catalogsearch/result/?q=anemometro", ""),
]
rows = []; total = 0.0
for g, item, q, u, cur, st, url, note in BOM:
    usd = q * u / (FX if cur == "MXN" else 1.0); total += usd
    rows.append(dict(group=g, item=item, qty=q, unit=u, cur=cur, usd=usd, status=st, url=url, note=note))
groups = {}
for r in rows: groups.setdefault(r["group"], []).append(r)
ops = {int(o["v"]): o for o in D["ops"]}
kwh5 = D["kWh_yr"] * 5; sails5 = 4 * 765 / FX
out = dict(cad=dict(checks=CAD["checks"], masses=CAD["group_mass_kg"], rotor_mass=CAD["rotor_mass_kg"], chains=CAD["chains"]), fea_rows=FEA_ROWS, ladder=OPT["ladder"], stretch=OPT["best"], sails5=sails5, design=D, rows=rows, total=total, subtotals={g: sum(r["usd"] for r in v) for g, v in groups.items()}, usd_per_MWh_5yr=(total + sails5) / (kwh5 / 1000), kWh_per_usd_5yr=kwh5 / (total + sails5), fx=FX)
json.dump(out, open("out/sail_bom.json", "w"), indent=1, default=float)

md = ["# Punta Mita prototype: 5 m cloth-sail windmill on a pole", "",
 "Chosen after simulating nine concepts in three years of hourly Punta Mita wind (see `results/concepts.json`). Prices seen 22 Nov 2026; Home Depot prices are the online prices.", "",
 "![CAD model](cad/view_iso.png)", "",
 "## What the simulation predicts", "",
 f"Whole system: rotor → two bicycle chains (48:14, then 28:14, 6.9:1 overall) → hub motor → rectifier → two 2.9 Ω resistors in parallel. At each wind speed the machine settles where rotor torque equals generator torque.", "",
 "| Wind | Rotor speed | Volts | Amps | Electrical power | Pole thrust | Chain tension |", "|---|---|---|---|---|---|---|"]
for v in (3, 4, 5, 6, 7):
    o = ops[v]; md.append(f"| {v} m/s{' (reefed above 7)' if o['furled'] else ''} | {o['rpm']:.0f} rpm | {o['V']:.0f} V | {o['I']:.0f} A | {o['P_el']:.0f} W | {o['thrust']:.0f} N | {o['chain_N']:.0f} N |")
md += ["", f"- Year-round at Punta Mita (dataset wind): **{D['avg_W']:.0f} W average, {D['kWh_yr']:.0f} kWh a year**.",
 f"- Parts: **about ${total:,.0f}**, plus about ${sails5:,.0f} for four replacement tarps (sails last about a year in the sun). Over five years that is {kwh5/1000:.1f} MWh, about **${(total+sails5)/(kwh5/1000):,.0f} per MWh**.",
 "- Optimised over rotor size, number and width of sails, gearing, load and reefing speed (2,009 feasible combinations). The second chain is what matters: it lets a bigger rotor load the generator properly.",
 f"- Stretch version: a 6 m rotor on a 9 m pole makes about {OPT['best']['avg_W']:.0f} W average (${OPT['best']['usd_per_MWh']:,.0f} per MWh) but is a much bigger thing to raise; build the 5 m first.",
 "- Uncertainty: rotor efficiency is taken from published sail-rotor tests (20–30% of the wind's power) with a 0.75 site factor; the wind is a 50 km reanalysis grid, not your beach. Expect the real figure within roughly half to double.", "",
 f"## Order list (about ${total:,.0f})", ""]
for g, v in groups.items():
    md += [f"### {g} (about ${sum(r['usd'] for r in v):,.0f})", "", "| Item | Qty | Unit price | Price | Note |", "|---|---|---|---|---|"]
    md += [f"| {('['+r['item']+']('+r['url']+')') if r['url'] else r['item']} | {r['qty']} | {'MX$' if r['cur']=='MXN' else '$'}{r['unit']:,.2f} | {r['status']} | {r['note']} |" for r in v] + [""]
md += ["## CAD and structural check", "",
 "The whole machine is modelled in CAD (`cad/sail_windmill.step`, 62 solids, built by `models/cad_model.py`) and analysed as a 3D frame with tension-only cables (`models/sail_fea.py`). Both read the same dimensions file.", "",
 "The CAD model changed the design three times: the upwind guy cable passed through the spinning rotor (now a back-prop behind the pole and side guys only); the rotor is coned 8° upwind so the spars clear the hub-motor rim by 184 mm; the motor bracket was moved below the crank arm's sweep.", "",
 "| Fit check | Clearance | Needed |", "|---|---|---|"] + [f"| {c['check']} | {c['clearance_m']*1000:.0f} mm | {c['need_m']*1000:.0f} mm |" for c in CAD["checks"]] + ["",
 "| Load case | Thrust | Lowest safety factor | Where | Pole foot | Prop foot |", "|---|---|---|---|---|---|"] + FEA_ROWS + ["",
 f"- Airborne mass: rotor {CAD['rotor_mass_kg']:.0f} kg, drivetrain {CAD['group_mass_kg']['drive']:.0f} kg, pole and prop {CAD['group_mass_kg']['pole']:.0f} kg.",
 "- The pole foot is pulled UP in strong wind and the prop foot pushed down and back. Both need real anchors (below).",
 "- Not modelled: bolted joints and the plywood hub themselves, fatigue, gusts as dynamics, sand strength. Safety factors are on steel yield (230 MPa) and Euler buckling.", "",
 "## Build", "",
 "1. **Hub.** Cut two 50 cm plywood discs. Clamp the eight 2.5 m conduit spars between them like wheel spokes (45° apart) with U-bolts, inner ends 15 cm from centre. Bolt the disc pair to the bicycle's right crank and chainring so the crank axle is the rotor shaft.",
 "2. **Bowsprit and stays.** Fix a 1.0 m conduit to the hub centre pointing upwind. Run two ropes from its tip to each spar: one to the tip, one to two-thirds span. Tension them until every spar tip sits 35 cm upwind of the hub plane (8° of coning). The strength and clearance checks assume this.",
 "3. **Sails.** Cut eight right triangles from the tarp: 2.3 m along the spar, 1.4 m along the foot. Tape and fold the edges. Lash the long edge to a spar; tie the free corner to the next spar's tip with a 0.3 m sheet so the sail can belly. Loose sails outperform tight ones.",
 "4. **Drivetrain.** Keep the bicycle frame whole, hung on the upwind face of the pole with the crank at the top (two conduit standoffs U-bolted to the pole at 5.90 m and 5.15 m). Cut the rim off the bike's rear wheel so only the hub and cog cluster remain. The hub motor sits 42 cm below that hub on two doubled-plywood plates bolted to the rear dropouts. Chain one: 48-tooth chainring to the 14-tooth cog of the bike's own rear wheel (tyre off; lock the derailleur or shorten the chain). Chain two: from the 28-tooth cog of that same cluster to the 14-tooth freewheel on the hub motor wheel, which you clamp behind the rear wheel on a plywood-and-conduit bracket with the sprockets in line. Overall 6.9:1. Check both freewheels drive in the direction the sails turn.",
 "5. **Tower.** Pole: two post tubes butted end to end with four 1 m conduit splints clamped round the joint by U-bolts. Back-prop: the same, with two splints. The prop leans from a foot 2.2 m directly downwind of the pole to the pole at 5.7 m, lashed and U-bolted there. Side guys only: two from 5.8 m and two from the joint, straight out to each side, 4.5 m and 2.6 m from the pole. Nothing may cross in front of the pole: the rotor sweeps there.",
 "5b. **Anchors.** Pole foot: bolt it to a 1 m timber buried 0.8 m deep; in a 12 m/s gust it is pulled up with about 180 kg. Prop foot: a 40 cm plywood pad on firm sand with a buried timber behind it; it pushes down with about 280 kg and back with about 105 kg. Side guys: a buried timber each side.",
 "6. **Electrics.** Three motor phase wires down the pole → rectifier → shunt → two resistors in parallel, on a plywood board in the shade. Resistors get hot: keep them off anything that burns.",
 "7. **Raising.** Assemble flat on the sand with sails off, walk the pole up with two people on guys, tension, then tie the sails on from a ladder or lower the pole to rig them.", "",
 "## Test plan", "",
 "1. Log wind at head height and at the top of the pole for two afternoons before building.",
 "2. Spin the rotor by hand with sails off: confirm volts rise with speed (about 0.6 V per rotor rpm) and the freewheel direction is right.",
 "3. First run with four sails in 4–5 m/s; then all eight.",
 "4. Record wind, volts, amps for ten minutes at each wind speed and compare with the table above. Try two and four resistors in parallel to see the match change.", "",
 "## Safety", "",
 "- Reef (wrap each sail round its spar) above 7 m/s, when the two load resistors reach their heat limit (use four in parallel to run to about 9 m/s), and before leaving it unattended. The highest hour in three years of data was 17 m/s.",
 "- Blade tips are 3.5 m above the sand and move at about 10 m/s in a 6 m/s breeze: rope off the area under and downwind of the rotor.",
 "- With no load connected the rotor overspeeds: always connect the resistors before untying the sails.",
 "- Rinse salt off the hub motor and chain; keep the rectifier and shunt dry.", ""]
open("SAIL_WINDMILL.md", "w").write("\n".join(md))
print(f"total ${total:,.0f}", {g: round(v) for g, v in out["subtotals"].items()}, f"avg {D['avg_W']:.1f} W, {D['kWh_yr']:.0f} kWh/yr, ${out['usd_per_MWh_5yr']:,.0f}/MWh, R {D['R_load']}, furl {D['v_furl']}")
