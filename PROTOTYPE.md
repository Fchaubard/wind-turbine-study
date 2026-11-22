# Punta Mita prototype: parts list and predictions

A Daisy-type rotary kite ring: six rigid foam blades on a 2.4 m ring (4.8 m rotor) spin a rope shaft that turns an e-bike hub motor on the ground. Prices seen 22 Nov 2026.

## What to expect

- Rotor model calibrated to the published Daisy field measurements: real machines delivered 27% of what the rotor theory predicts, and every number here uses that factor.
- Punta Mita wind (NASA POWER, 2022–2024, 10 m): mean 3.2 m/s; above 4 m/s 28% of hours; above 6 m/s 2% of hours.

| Wind | Rotor rpm | Electrical power |
|---|---|---|
| 3 m/s | 31 | 12 W |
| 4 m/s | 41 | 29 W |
| 5 m/s | 52 | 57 W |
| 6 m/s | 62 | 98 W |
| 7 m/s | 72 | 155 W |
| 8 m/s | 83 | 232 W |
| 9 m/s | 93 | 330 W |
| 10 m/s | 103 | 453 W |

| Basis | Average power | Energy per year |
|---|---|---|
| measured-performance basis, dataset wind | 21 W | 184 kWh |
| same, if the beach wind is 1.3× the dataset | 48 W | 424 kWh |
| same, if the beach wind is 1.6× the dataset | 89 W | 776 kWh |
| if it performs like Daisy's light-wind point (2.2× better) | 46 W | 404 kWh |

## Parts list (about $2,232 in total)

### Carry from the US (about $1,877)

| Item | Qty | Unit | Total | Price status | Where | Note |
|---|---|---|---|---|---|---|
| [Pultruded carbon tube 10 mm OD × 7.3 mm ID × 48 in (DragonPlate)](https://dragonplate.com/dragonplate-carbon-tube-394od-x-288id-x-48) | 40 | $21.06 | $842 | verified | DragonPlate | 6 blade spars + 5 rings × 6 tubes + 4 spares. $21.06 is the 10+ price. Confirm 40 are in stock before paying. |
| [Solid fibreglass rod 1/4 in × 48 in, cut into 10 cm ferrules to join ring tubes](https://intothewind.com/products/fiberglass-rod) | 3 | $15.00 | $45 | verified | Into The Wind | 6.35 mm rod inside a 7.3 mm bore: wrap with tape for a snug fit, glue one side. |
| [UHMWPE braided line 2.0 mm, 1,000 lb, 100 ft spool](https://www.emmakites.com/products/750lb-1000lb-uhmwpe-braided-line-spool) | 5 | $23.95 | $120 | verified | Emma Kites | 6 shaft lines × 14 m + blade bridles. Peak line load in the simulation is 131 N; safe working load is about 890 N. |
| [UHMWPE braided line 3 mm, 2,200 lb, 100 ft spool](https://www.emmakites.com/products/1500lb-2200lb-5500lb-uhmwpe-braided-line-spool) | 2 | $34.95 | $70 | verified | Emma Kites | Lifter line and anchor strop. |
| [Lifter kite: Jumbo Power Sled 36 (about 4 m², 5–20 mph)](https://intothewind.com/products/jumbo-power-sled-36) | 1 | $195.95 | $196 | verified | Into The Wind | Holds the shaft up. A Peter Lynn Pilot 8 m² ($260, ships from New Zealand) lifts twice as much if it can arrive in time. |
| [48 V 1,200 W direct-drive rear hub motor wheel, 700C](https://ebikeling.com/products/waterproof-48v-1200w-700c-direct-drive-front-rear-ebike-motor-wheel-only) | 1 | $239.99 | $240 | verified | ebikeling | Used as the generator. Order the REAR version and confirm it has a screw-on freewheel thread; about 7 kg in checked luggage. |
| Single-speed freewheel, 16 tooth, standard thread | 1 | $15.00 | $15 | not priced | any bike shop | Drives the hub motor from the chain. Price is my estimate. |
| [3-phase bridge rectifier, 90 A 1,000 V](https://windandsolar.com/products/3-phase-rectifier-90-amp) | 1 | $20.65 | $21 | verified | Missouri Wind and Solar | Bolt to an aluminium plate as a heat sink. |
| [300 W load resistor, 24 V version (2.9 ohm)](https://windandsolar.com/products/300-watt-divert-load-resistor) | 3 | $10.55 | $32 | verified | Missouri Wind and Solar | One alone for 6 m/s wind, two in series for light wind, two in parallel for strong wind. |
| [Victron SmartShunt 500 A (logs volts, amps, watt-hours to a phone)](https://shopsolarkits.com/products/victron-smartshunt) | 1 | $117.30 | $117 | verified | Shop Solar Kits | Works from 6.5 V, so it reads from about 4 m/s wind upward. |
| [Rigging swivel between lifter line and rotor hub](https://hownot2.com/products/swivel) | 1 | $79.95 | $80 | verified | HowNOT2 | Price seen; the 5 kN working load is from a search result, check the product page. |
| [Kestrel 1000 wind meter](https://kestrelinstruments.com/kestrel-1000-pocket-wind-meter) | 1 | $99.00 | $99 | verified | Kestrel | Or the Steren HER-445 locally (MX$495). |

### Buy in Puerto Vallarta (about $355)

| Item | Qty | Unit | Total | Price status | Where | Note |
|---|---|---|---|---|---|---|
| [Foamular F-250 XPS foam board 1 in × 1.22 × 2.44 m](https://www.homedepot.com.mx/p/owens-corning-foamular-1-pulgada-122-x-244-m-f-250-281354) | 2 | $26.97 | $54 | verified | Home Depot Las Juntas | Blades: 6 × 1.2 m × 0.20 m, plus spares. Store stock was not shown online. |
| [3M duct tape 48 mm × 55 m (blade skin and leading edge)](https://www.homedepot.com.mx/s/cinta%20ducto) | 2 | $10.76 | $22 | verified | Home Depot Las Juntas |  |
| [Epoxy resin + hardener, 250 ml each (bond spars into foam)](https://www.homedepot.com.mx/s/resina%20epoxica) | 1 | $23.68 | $24 | verified | Home Depot Las Juntas |  |
| [Rectangular aluminium tube 1 × 2 in × 3 m (ground spider arms and deadman anchor)](https://www.homedepot.com.mx/s/tubo%20aluminio) | 4 | $13.46 | $54 | verified | Home Depot Las Juntas | 3 arms cut to 2.4 m; the fourth is buried as the sand anchor. |
| [Stainless shackles 1/4 in and quick links](https://www.zaragozamarine.com.mx/?s=grillete&post_type=product) | 6 | $3.73 | $22 | verified | Zaragoza Marine |  |
| Used adult bicycle with a 44-tooth or larger chainring | 1 | $100.00 | $100 | not priced | local | Its crank is the rotor's ground bearing; its rear triangle holds the hub motor. Price is my guess. |
| Bolts, U-bolts, timber for the ground frame, 10 AWG wire, lugs, safety flagging | 1 | $80.00 | $80 | not priced | Home Depot Las Juntas | Price is my allowance. |

## Geometry

- Blades: 6 × 1.20 m span × 0.20 m chord, 25 mm foam shaped to a flat-bottomed aerofoil, a carbon tube glued in at quarter chord, taped skin. Each blade is tied at BOTH ends (inner end to the rotor ring, outer end by a bridle line); a blade held at one end only overstresses its spar above about 6 m/s.
- Rings: 5 hoops of 2.33 m diameter, each from 6 tubes joined end to end with glued ferrules. The top hoop is the rotor ring.
- Shaft: 6 lines, 5 bays of 2.8 m (14 m long), flown at about 30° so the rotor hub sits about 7 m up and the lowest blade tip about 5 m up.
- Ground station: the bicycle lies with its crank axis pointing up the shaft. Three 2.4 m aluminium arms bolted to the crank form a six-point spider that the six lines tie to. Chainring (44T or more) → chain → 16T freewheel on the hub motor: about 3:1 step-up. Without the step-up the generator is under 30% efficient.
- Electrical: hub motor 3 phase wires → rectifier → shunt → resistor. Expect about 12 V at 4 m/s and 19 V at 6 m/s.
- Anchor: one aluminium tube buried crosswise 0.8 m deep in damp sand with a 3 mm strop round its middle. Design pull 1.3 kN at 12 m/s.

## Simulation checks

| Wind | Shaft torque | Shaft tension | Twist per bay | Line tension | Ring buckling safety factor | Result |
|---|---|---|---|---|---|---|
| 4.0 m/s (model torque) | 25 N·m | 191 N | 16° | 32 N | 73.2 | stable |
| 6.0 m/s (model torque) | 57 N·m | 279 N | 25° | 47 N | 21.2 | stable |
| 6.0 m/s (calibrated torque) | 22 N·m | 279 N | 9° | 46 N | 73.2 | stable |
| 9.0 m/s (model torque) | 127 N·m | 477 N | 32° | 82 N | 7.1 | stable |
| 12.0 m/s (model torque) | 226 N·m | 755 N | 36° | 131 N | 3.5 | stable |

## Test plan

1. Day 1: log wind on the beach at head height and on a pole, morning and afternoon. If it rarely passes 4 m/s, nothing below will turn.
2. Fly the lifter kite alone on the 3 mm line and learn to launch and land it.
3. Spin the ground station by hand: check freewheel direction, volts per rpm, and resistor heating.
4. Rotor on a short shaft (one bay) at ground level in 4–6 m/s, then add bays.
5. Record wind, rpm, volts and amps together; compare with the table above.

## Safety

- Blade tips reach about 30 m/s at 12 m/s wind. Rope off a 30 m radius downwind and keep people out; do not fly with beachgoers nearby.
- Land it above 9 m/s or when squalls approach. The highest hour in three years of data was 17 m/s.
- Stay below 150 m and check for helipads nearby; no Mexican kite rule was found, which is not a clearance.
- Salt and sand: rinse the hub motor and bearings; keep the rectifier and shunt in a box.
