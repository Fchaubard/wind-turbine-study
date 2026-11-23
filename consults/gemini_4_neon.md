## 1. Plain Verdict: Is <$10/MWh Reachable at This Exact Site?

* **For electricity ($\text{MWh}_e$), shaft work, pumped water, compressed air, or RO hydraulic energy at the stated NASA POWER wind (39 W/m² at 50 m; ~32.5 W/m² at 10 m): NO.**
  * **Why:** At 32.5–39 W/m² and 25% net conversion, one square metre of swept area yields 71–85 kWh/yr. At $10/MWh, your *entire* annualized budget (CapEx depreciation + upkeep) is **$0.71–$0.85/m²/yr**. Even utility-scale onshore wind spends ~$10–$18/m²/yr and only reaches $25–$40/MWh because its sites have 300–450 W/m² (8–12× Punta Mita). In a tropical salt-spray hurricane zone, fixed annual upkeep alone ($100–$250/yr minimum for bearings, seals, paint, or UV-degraded fabric) requires 100–250 m² of swept area just to stay under $10/MWh *before spending $1 on CapEx*.
  * **Realistic floor at baseline reanalysis wind:** **~$30–$50/MWh$_e$** for electricity (already far cheaper than Punta Mita residential/DAC grid power at ~$250–$350/MWh$_e$).
* **For direct mechanical cooling / ice ($\text{MWh}_{\text{cool}}$): BORDERLINE at baseline (~$12–$35/MWh$_{\text{cool}}$), and YES (<$10/MWh$_{\text{cool}}$) if local sea-breeze / bluff-crest speedup is real.**
  * **Why:** Driving an open-shaft automotive A/C compressor directly from the rotor, using 27 °C Pacific seawater to cool the condenser, and freezing an insulated ice bank gives a **COP ≈ 2.6** multiplier (1 MWh shaft → 2.6 MWh cooling) while eliminating generator, inverter, MPPT, and lithium batteries. Keep energy currencies honest: $10/MWh$_{\text{cool}}$ equals ~$26/MWh$_{\text{mech}}$.
* **Five things that MUST be true to approach or beat $10/MWh:**
  1. **Local wind beats the 50 km reanalysis** (most likely lever): Exposed headland/bluff-crest sea breeze raises mean hub wind from 3.2 m/s (~32.5 W/m²) to **≥4.2–4.5 m/s (~70–85 W/m²)**—a 2.2–2.6× power jump ($P \propto v^3$).
  2. **Swept area ≥ 100–150 m²** (12–14 m rotor or large airborne sweep) to dilute fixed PTO and salt-corrosion upkeep below $2/m²/yr.
  3. **No custom low-RPM PMG and no industrial gearbox:** Generator cost scales with torque, not power; use rim-drive speedup, a scrap automotive differential, or direct shaft-to-compressor/pump PTO.
  4. **Manual hurricane retreat, not rigid 60 m/s survival:** Surviving Cat 4/5 gusts rigidly multiplies structural cost 5×. You must unclip sails, reel in kites, or tilt down the mast in <15 minutes.
  5. **Low recurring fabric wear:** Replacing UV-rotted sails/kites every 2–3 years quietly adds $15–$40/MWh. Either use 15–20 yr rigid fiberglass/wood blades or ultra-cheap (<$1/m²) sacrificial cloth.

**Baseline wind assumptions used below** (derived from prompt's 3.2 m/s at 10 m, 3.4 m/s at 50 m, 39 W/m² at 50 m; implies marine shear exponent $\alpha \approx 0.038$):
* 8–10 m height: **31–32.5 W/m²** (`39 × (3.2/3.4)^3 = 32.5`). Note: tall towers in open marine exposure have terrible ROI (+20% power from 10 m to 50 m for 5× tower cost).
* 80 m / 150 m height (airborne): **~41 / ~44.5 W/m²** `[uncertain—power-law extrapolation; a coastal sea-breeze low-level jet could push this to 70–100 W/m²]`.
* Note on wind distribution: Because $P \propto v^3$, ~77–80% of annual energy occurs during the ~33% of hours >4 m/s.
* All LCOEs use `(CapEx / Life + Yearly Upkeep) / Annual Output` (finance ignored, per prompt).

---

## 2 & 3. The 12 Best, Genuinely Different Ideas

### 1. 14 m Tensioned Bicycle-Wheel ("Chalk") Rim-Driven Sailwing HAWT on Pad Turntable (Electricity)
* **Mechanism:** A 14 m spoked-rim sailwing rotor sits on a 3.8 m rolled-angle steel turntable bolted to the 4×4 m pad; a rubber friction wheel rides the outer rim for a gearbox-free ~45:1 speedup directly into a high-RPM brushless truck alternator/PMG.
* **Why cheaper:** The 14 m outer rim *is* a giant pulley—tip speed (~16–20 m/s) spins a 15 cm PTO wheel at ~2,200 RPM, cutting shaft torque ~90× and eliminating both the gearbox and expensive low-RPM PMG. Pure-tension wire spokes minimize rotor mass; sails unclip in 5 min for hurricanes.
* **Swept area:** 154 m² (14 m dia, hub at 10 m, 3 m ground clearance).
* **Efficiency:** $C_p = 0.26$ (spoked-rim turbines measured at 0.25–0.33 in wind-tunnel/field tests; conservative here for ~0.04 wire-spoke drag and simple sails) × 0.85 rim-drive × 0.84 alternator/MPPT = **0.186 net wind-to-DC**.
* **Itemized CapEx ($2,700):** 3.8 m rolled-angle steel turntable ring + 4 hold-down caster assemblies bolted to pad ($550); welded steel A-frame mast + yaw tail/hand-crank ($650); 14 m bent EMT/aluminum rim + 24 stainless spoke cables + truck hub + 4 furlable Dacron sailwings ($950); rim-drive wheel PTO + brushless truck alternator + MPPT/dump load ($550).
* **Yearly upkeep:** **$220/yr** ($80/yr sails every 4 yr + $140/yr rubber drive wheel, bearings, salt rinse/paint) `[uncertain—salt slip/wear on rim tire]`.
* **Life:** 15 yr.
* **Annual output (at 32.5 W/m²):** **8.15 MWh$_e$/yr**.
* **Resulting $/MWh:** **$49/MWh$_e$** (`($180 + $220) / 8.15`).
* **Single most likely failure:** Slipping/chattering of the rim friction drive in wet salt spray, or rim buckling under asymmetric gust loads if spokes lose preload.
* **Cheapest test (<$200, 3 days):** Build a 2.5 m spoked EMT/bicycle-rim wheel with 3 tarp sail blades ($90) on a simple pipe stub; press a bicycle-wheel/scooter-tire PTO ($40) driving a drill-chuck/e-bike hub against the rim while spraying saltwater to measure traction, slip, RPM, and drag.

### 2. 10 m Pad-Mounted Sailwing HAWT → Direct Automotive A/C Compressor + Seawater-Cooled Ice Bank (Cooling/Ice)
* **Mechanism:** A 10 m sailwing rotor on a pad-bolted 3 m steel tripod drives an open-shaft automotive A/C compressor (via bevel gear/belt) rejecting heat into 27 °C seawater to freeze an insulated 2,000 L IBC-tote ice bank.
* **Why cheaper:** Removes generator, rectifier, MPPT, inverter, and batteries; insulated water/ice stores energy at ~$4/kWh$_{\text{th}}$ vs ~$150/kWh$_e$ for LiFePO4; refrigeration **COP ≈ 2.6** multiplies every shaft MWh into 2.6 MWh of Punta Mita's highest-value load (cooling/ice).
* **Swept area:** 78.5 m² (10 m dia, hub at 8.5 m, 3.5 m clearance above 3 m tripod for 360° yaw).
* **Efficiency:** $C_p = 0.25$ (sailwings measured 0.25–0.35) × 0.82 bevel/belt drive × 2.6 seawater-cooled R290/R134a piston compressor COP (measured 2.5–3.2 at 27 °C condensing / −4 °C evaporating; `[uncertain at variable low RPM]`) = **0.53 net wind-to-cooling** (0.205 mechanical).
* **Itemized CapEx ($2,700):** 3 m pad tripod + 5.5 m galvanized pipe mast + yaw swivel ($700); 10 m sailwing rotor + hub + furling tail ($650); vertical shaft + scrap car-diff bevel gear + V-belt/centrifugal clutch ($300); Sanden SD7H15 open compressor + CuNi/titanium seawater condenser coil + 2× insulated IBC-tote ice banks + TXV/refrigerant ($1,050).
* **Yearly upkeep:** **$220/yr** ($80/yr sails + $140/yr shaft seal, belts, condenser biofouling clean, paint).
* **Life:** 15 yr.
* **Annual output (at 31.5 W/m²):** **11.5 MWh$_{\text{cool}}$/yr** (4.44 MWh$_{\text{mech}}$/yr; ~120 tonnes ice/yr).
* **Resulting $/MWh:** **$35/MWh$_{\text{cool}}$** ($90/MWh$_{\text{mech}}$).
* **Single most likely failure:** Compressor shaft-seal refrigerant leak under belt side-load/salt corrosion, or stall/slugging at low wind speeds if clutch engagement isn't tuned.
* **Cheapest test (<$200, 3 days):** Buy a junkyard Sanden A/C compressor + condenser ($100) and spin it with a variable-speed drill/bicycle crank (200–1,200 RPM) in a bucket of seawater to measure minimum viable RPM, starting torque, and real COP into an ice chest.

### 3. 45 m² Autonomous Crosswind Pumping Kite (Yo-Yo AWE) → Direct Hydraulic / RO Feed
* **Mechanism:** A 45 m² used tandem paraglider/lightweight foil kite flies crosswind figure-8s at 100–180 m on a Dyneema tether anchored to the pad, reeling out under high tension to directly stroke a high-pressure RO plunger pump, then depowering to reel in.
* **Why cheaper:** Decouples swept area (~400 m²) from material area (45 m²); zero tower, zero foundation bending (pure tension into pad bolts), reaches higher altitude, direct hydraulic pumping removes generator/electronics, and hurricane retreat takes 3 minutes.
* **Swept area:** 45 m² kite area (~400 m² effective crosswind sweep).
* **Efficiency:** Crosswind harvesting factor $\zeta \approx 1.0$ on kite area (equivalent to $C_p \approx 0.11$ on 400 m² sweep; field-measured at $\zeta = 1.0\text{–}1.8$ in European pumping-kite trials, conservative here for tether drag, 30° elevation angle, reel-in duty cycle, and pump losses). Cut-in ~3.5 m/s retains ~80% of wind energy (`35.6 W/m²` usable of `44.5 W/m²` at 150 m `[uncertain]`).
* **Itemized CapEx ($4,600):** Used/sewn 45 m² foil/tandem paraglider ($1,100); 250 m 4 mm Dyneema tether + bridle ($300); pad winch frame + drum + one-way clutch + reel-in motor/battery ($1,400); ceramic-plunger RO feed pump + accumulator ($1,200); autonomous steering pod—Pixhawk/ESP32, IMU, 2 servos, sensors ($600). *(RO membranes add ~$800 if counting water plant.)*
* **Yearly upkeep:** **$680/yr** ($370/yr kite UV/wear every 3 yr + $120/yr tether + $190/yr pump seals/servos) `[uncertain—crash rate dominates]`.
* **Life:** 10 yr (ground station; kite/tether in upkeep).
* **Annual output (at 44.5 W/m², 80% >cut-in):** **14.0 MWh$_{\text{hyd}}$/yr** (~4,000 m³/yr RO fresh water with energy recovery).
* **Resulting $/MWh:** **$81/MWh$_{\text{hyd}}$** (`($460 + $680) / 14.0`).
* **Single most likely failure:** Autonomous flight-controller crash into the ocean/rocks during afternoon-to-evening sea-breeze lulls (destroying the kite and electronics).
* **Cheapest test (<$200, 3 days):** Borrow/buy a used 10–12 m² lightweight foil kite ($150) + handheld luggage scale ($15) on 50 m of Dyneema ($35); fly figure-8s from the pad during afternoon wind to verify minimum stay-aloft wind speed, line tension, and altitude wind speedup.

### 4. Passive Tethered Rotary Kite Train (TRPT / "Daisy Kite") + Black-Poly Solar Lifter Balloon (Mechanical)
* **Mechanism:** Three stacked 8 m soft-fabric rotary rings lifted to 60–100 m by a pilot kite + a $50 black-polyethylene solar hot-air balloon (tropical sun gives free daytime buoyancy to stop lull crashes!) transmit continuous rotary torque down triangulated Dyneema lines to a pad PTO.
* **Why cheaper:** Continuous rotary output with **zero flying electronics, zero servos, and zero cyclic reel-in losses**; hybrid solar-thermal lift solves airborne wind's #1 tropical low-wind crash mode while wind remains 100% of harvested power.
* **Swept area:** 130 m² wind-projected (three 8 m rings = 150 m² tilted ~30°).
* **Efficiency:** $C_p = 0.16$ (measured 0.15–0.22 on field TRPT prototypes) × 0.82 availability above 3 m/s (aided by solar lift) × 0.82 ground PTO = **0.108 net**.
* **Itemized CapEx ($2,250):** Ripstop fabric + sewing for 3 rings + pilot kite ($800); 6 m 1-mil black-poly solar balloon ($50); fiberglass tent/kite spars ($300); Dyneema torsion lines + swivels ($350); pad-bolted rotary hub/frame/PTO + manual reel-in winch ($750).
* **Yearly upkeep:** **$420/yr** ($300/yr fabric/balloon UV replacement every ~2.8 yr + $120/yr lines/swivels/bearings).
* **Life:** 10 yr.
* **Annual output (at 41 W/m² `[uncertain]`):** **5.04 MWh$_{\text{mech}}$/yr**.
* **Resulting $/MWh:** **$128/MWh$_{\text{mech}}$**.
* **Single most likely failure:** Torsional line twist-up/tangling when the sea breeze dies at dusk (once solar balloon cools) or shifts direction abruptly.
* **Cheapest test (<$200, 3 days):** Tape a 4 m black garbage-bag solar balloon ($20) to lift one 2 m fabric-and-fiberglass TRPT ring ($90) on 3× 40 m mason/Dyneema lines ($50) to a lazy-Susan/bike-hub ground PTO ($40); measure static lift in lull and ground shaft torque.

### 5. Guyed Troposkein Darrieus VAWT → Direct Hydraulic Paddle-Wheel ("Joule") Churn (Hot Water / Pool Heat)
* **Mechanism:** A 10 m tall × 8 m wide eggbeater (Troposkein) Darrieus VAWT made of bent aluminum/fiberglass strips spins a submerged stainless paddle-wheel churn inside an insulated tank on the pad. *(Note: requires 3 rock/sand guy anchors ~7 m outside the 4×4 m pad.)*
* **Why cheaper:** Omni-directional (zero yaw mechanism, captures 100% of wind rose); pure-tension blades minimize material; a fluid paddle churn's quadratic load ($\tau \propto \omega^2$) **automatically matches a wind rotor's optimal $C_p$ curve** at all wind speeds with 96%+ efficiency and zero generator/electronics; no UV-rotting fabric.
* **Swept area:** 53.3 m² (`~2/3 × 10 m × 8 m`).
* **Efficiency:** $C_p = 0.26$ (measured 0.32–0.38 on larger Sandia-style Troposkein rotors; conservative for low Reynolds number + small Savonius starter cups) × 0.96 shaft-to-heat = **0.25 net wind-to-heat**.
* **Itemized CapEx ($1,850):** Central steel pipe shaft + top/bottom bearings + 3 guy cables/anchors ($550); 3× bent aluminum/fiberglass Troposkein blades + Savonius starter + disc brake ($700); insulated 500 L tank + stainless paddle + copper heat-exchanger coil ($600).
* **Yearly upkeep:** **$100/yr** (bearings, grease, paint—no fabric, no electronics).
* **Life:** 20 yr.
* **Annual output (at 31 W/m²):** **3.62 MWh$_{\text{th}}$/yr**.
* **Resulting $/MWh:** **$53/MWh$_{\text{th}}$** *(caveat: low-grade heat has limited value in Punta Mita outside hotel DHW / winter pool heating)*.
* **Single most likely failure:** Self-start failure in 3–4 m/s winds (Darrieus dead-band) or blade fatigue cracking at the root clamps under cyclic 2P aerodynamic loads.
* **Cheapest test (<$200, 3 days):** Build a 2 m tall × 1.5 m wide 2-blade Troposkein from 2" aluminum flat-bar/fiberglass strip ($80) on a bike-hub shaft ($30) spinning a paint-mixer paddle in a 20 L insulated bucket ($30) with a thermometer ($15); verify self-start wind speed and $\Delta T$/hour.

### 6. Cretan 8 m Multi-Jib Cloth Sailmill → Direct Mechanical Diaphragm Pump (Pumped Water)
* **Mechanism:** An 8 m wheel of 8 triangular cloth jib sails strung on wire-braced EMT/bamboo spars turns a simple eccentric crank directly stroking a slow-speed PVC/rubber diaphragm water pump.
* **Why cheaper:** Starts pumping at ~2.0 m/s (high solidity = high starting torque), zero electronics, zero gearbox, 100% Puerto Vallarta hardware + local sailmaker build; sails reef/furl like a sailboat in 2 minutes before storms.
* **Swept area:** 50.3 m² (8 m dia, hub at 8 m on pad-bolted tripod).
* **Efficiency:** $C_p = 0.18$ (measured 0.16–0.20 in Cretan sailmill field tests) × 0.72 crank/diaphragm pump = **0.13 net wind-to-hydraulic**.
* **Itemized CapEx ($1,400):** Pad tripod + mast ($500); hub, 8 EMT spars, wire stays, 8 Dacron sails, tail ($550); eccentric crank + diaphragm pump + piping ($350).
* **Yearly upkeep:** **$140/yr** ($60/yr sails every 4 yr + $80/yr pump diaphragms/valves/grease).
* **Life:** 15 yr.
* **Annual output (at 31 W/m²):** **1.78 MWh$_{\text{hyd}}$/yr** (~65,000 m³/yr lifted 10 m).
* **Resulting $/MWh:** **$131/MWh$_{\text{hyd}}$**.
* **Single most likely failure:** Overspeed spar buckling in a sudden squall if sails aren't reefed (high solidity produces huge storm thrust).
* **Cheapest test (<$200, 3 days):** Build a 2.5 m 6-sail Cretan wheel from 1/2" EMT conduit, wire, and tarp ($110) on a trailer hub ($40) driving a bilge/diaphragm pump ($40); measure cut-in wind speed and flow rate at 3 m head.

### 7. Tensioned Multi-Rotor "Wind Curtain" (16 × 2.5 m Surplus E-Bike/Hoverboard Hubs on Fixed NNW Cable Net) (Electricity)
* **Mechanism:** Sixteen 2.5 m plywood/PVC rotors—each bolted directly to a $35 surplus 350 W BLDC hoverboard/e-bike hub motor—hang on a 10 × 10 m tensioned steel-cable grid fixed facing 325° (NNW, capturing the dominant 80% W–N wind arc with zero yaw), lowered like a volleyball net before hurricanes.
* **Why cheaper:** Exploits cube-square scaling ($D^3$ blade mass vs $D^2$ swept area: 16 small rotors use ~1/4 the blade mass of one 10 m rotor) and leverages mass-produced BLDC hub motors (~$0.10/W) with zero gearbox and zero yaw bearing.
* **Swept area:** 78.5 m² (`16 × 4.91 m²`).
* **Efficiency:** $C_p = 0.27$ (small rigid 3-blade rotors, measured 0.25–0.32) × 0.80 BLDC+rectifier × 0.58 fixed-heading directional capture (facing 325° into Punta Mita's wind rose) = **0.125 net wind-to-DC**.
* **Itemized CapEx ($2,150):** Two 12 m guyed poles or splayed pad V-frame ($700); steel cable net ($200); 16× used e-bike/hoverboard hub motors ($560); 16× DIY plywood/PVC blade sets ($320); 16× 3-phase bridge rectifiers + DC bus + MPPT ($370).
* **Yearly upkeep:** **$180/yr** (replace 2–3 salt-corroded hub motors/bearings + blade touchup/yr) `[uncertain—cheap unsealed hubs in salt spray]`.
* **Life:** 12 yr.
* **Annual output (at 32.5 W/m²):** **2.79 MWh$_e$/yr**.
* **Resulting $/MWh:** **$129/MWh$_e$**.
* **Single most likely failure:** Saltwater ingress seizing cheap unsealed e-bike hub bearings/stators within 6–12 months, or cable-net resonant vibration causing adjacent blades to clash.
* **Cheapest test (<$200, 3 days):** Buy 2 used hoverboard/e-bike hub motors ($70), bolt 2.2 m PVC/plywood blades onto them ($50), suspend on a tensioned wire between two posts ($40), wire through 3-phase bridge rectifiers ($15) into a 12 V battery/resistor load; measure voltage-vs-RPM cut-in and net stability.

### 8. Shared-Structure Beachfront Shade Palapa/Pergola with Curved Roof-Lip Accelerator + 6 Micro-Rotors (Electricity)
* **Mechanism:** Build a beachfront shade pergola on the 4×4 m pad (paid for by shade/real-estate value), shape its overhanging 6 m NW-facing roof edge as a smooth curved fairing to accelerate flow ~1.25× over the crest, and mount six 1.6 m direct-drive e-bike-hub rotors along the ridge.
* **Why cheaper:** Amortizing the tower/foundation into an existing or wanted shade structure drives marginal structural CapEx near zero, while the roof crest adds local flow acceleration.
* **Swept area:** 12.1 m² (`6 × 2.01 m²`).
* **Efficiency:** $C_p = 0.26$ × 0.80 elec × 0.65 directional = **0.135 net**, applied to accelerated local power density `32.5 × 1.25^3 = 63 W/m²` `[uncertain—unmeasured roof-lip speedup; turbulence can hurt Cp]`.
* **Itemized CapEx ($780 marginal; ~$2,800 full):** 6× used hub motors ($210); 6× blades/brackets ($210); curved sheet/canvas roof-lip fairing ($120); rectifiers/wiring/MPPT ($240).
* **Yearly upkeep:** **$75/yr** (1–2 hub bearings/motors/yr).
* **Life:** 10 yr.
* **Annual output (at 63 W/m² local):** **0.90 MWh$_e$/yr**.
* **Resulting $/MWh:** **$170/MWh$_e$ marginal** (~$390/MWh$_e$ full). *(Demonstrates that even a "free" tower loses if swept area is tiny.)*
* **Single most likely failure:** Roof-edge flow separation/turbulence destroys rotor $C_p$ and causes annoying vibration/hum directly overhead of people using the pergola.
* **Cheapest test (<$200, 3 days):** Tape a 1 m curved cardboard/corrugated-plastic lip ($30) onto an existing beachfront roof/wall edge and compare simultaneous wind speeds at the crest vs free-stream using two $35 handheld anemometers ($70 total) to verify whether ≥1.25× speedup actually exists.

### 9. Endless-Loop "Wind Clothesline" (3 × 25 m² Collapsing Spinnaker Chutes, Pad-to-Offshore-Buoy) (Mechanical)
* **Mechanism:** Three 25 m² ripstop/tarp parachutes ride an endless 120 m rope loop between a pad capstan winch and an offshore buoy aligned with the NW/WNW breeze: chutes open downwind to haul the rope, hit a far-end trip-stop to collapse, and feather back upwind.
* **Why cheaper:** Zero tower, zero rigid blades, zero electronics; pure fabric and rope deployable in 10 minutes and storable indoors before hurricanes.
* **Swept area:** 75 m² active (`3 × 25 m²`, spaced 35 m apart to avoid wake shadowing).
* **Efficiency:** Drag-device Betz limit is $\frac{4}{27} C_D \approx 0.21$ (for $C_D = 1.4$); minus return drag, turnaround, capstan friction, and fixed-axis alignment (~65% energy within ±45°) = **0.075 net** `[uncertain—unmeasured at multi-chute marine scale]`.
* **Itemized CapEx ($1,250):** 3× sewn ripstop/tarp chutes ($350); 250 m braided line ($200); offshore anchor/buoy/swivel pulley ($300); pad capstan winch + pump PTO ($400).
* **Yearly upkeep:** **$220/yr** ($175/yr UV/salt chute replacement every 2 yr + $45/yr rope/pulleys).
* **Life:** 8 yr.
* **Annual output (at 32.5 W/m²):** **1.60 MWh$_{\text{mech}}$/yr**.
* **Resulting $/MWh:** **$235/MWh$_{\text{mech}}$**.
* **Single most likely failure:** Chutes snagging/failing to collapse at the offshore turnaround pulley, or dipping into surf during wind lulls and ripping the line.
* **Cheapest test (<$200, 3 days):** Rig one 6 m² tarp chute ($40) on an 80 m paracord/polypropylene loop ($40) between two beach trees/stakes with cheap pulleys ($30) and a spring scale ($15); measure downwind pull vs upwind return drag and trip-release reliability.

### 10. Offshore-Moored Wind-Primary / Wave-Assisted Hybrid Pumping Spar (Pressurized Seawater / RO Feed)
* **Mechanism:** A buoyant spar moored 150 m offshore (clear of shore obstructions) carries a 6 × 5 m H-Darrieus VAWT driving a seawater piston pump while Pacific swell (1–2 m) heaves the spar against a submerged damping plate to stroke a parallel pump—both feeding one seabed PE hose back to the pad (wind ~69%, wave ~31%).
* **Why cheaper:** Buoyancy replaces a concrete foundation/tower; unobstructed open-water siting raises wind; Pacific swell keeps pressure up during wind lulls, raising utilization of the shared seabed hose and RO plant.
* **Swept area:** 30 m² wind VAWT + 4 m² heave plate.
* **Efficiency:** Wind $C_p = 0.24 \times 0.78$ pump = **0.187** at ~42 W/m² offshore `[uncertain]` → 2.06 MWh$_{\text{hyd}}$/yr; plus ~0.94 MWh$_{\text{hyd}}$/yr wave heave assist `[uncertain—~3% capture of local swell]` = **3.00 MWh$_{\text{hyd}}$/yr** total.
* **Itemized CapEx ($2,950):** Buoyant spar + mooring anchor/chain ($900); 6 × 5 m aluminum H-Darrieus ($850); dual marine piston pumps + check valves ($550); 180 m 1.5" HDPE seabed hose ($400); heave plate ($250).
* **Yearly upkeep:** **$350/yr** (barnacle/biofouling clearing, mooring shackles, seals, pre-hurricane tow/submerge) `[uncertain—marine O&M often exceeds estimate]`.
* **Life:** 10 yr.
* **Annual output:** **3.00 MWh$_{\text{hyd}}$/yr**.
* **Resulting $/MWh:** **$215/MWh$_{\text{hyd}}$**.
* **Single most likely failure:** Rapid tropical biofouling seizing underwater check valves/piston rods, or mooring line chafing through in storm surge.
* **Cheapest test (<$200, 3 days):** Tether a weighted 55-gallon drum spar + 1 m² plywood heave plate + PVC check-valve hand-pump ($150 total) 30 m offshore in surf/swell for 48 hours to measure real heave stroke, pumping pressure, and mooring load.

### 11. Direct Wind-Driven Isothermal Compressed Air + Submerged Ocean-Depth Air-Bag Storage (Pneumatic)
* **Mechanism:** A 10 m pad-mounted sailwing HAWT directly belt-drives a slow-speed twin-piston air compressor pumping air down a PE pipe into a weighted 10 m³ vinyl/Hypalon bladder anchored 20 m deep offshore (constant 3-bar hydrostatic pressure, near-isothermal ocean heat exchange), feeding direct compressed air for airlift pumping, aquaculture aeration, or pneumatic tools.
* **Why cheaper:** The ocean's hydrostatic head replaces steel pressure tanks and batteries with a cheap flexible bladder at constant delivery pressure.
* **Swept area:** 78.5 m² (10 m sailwing on pad tripod).
* **Efficiency:** $C_p = 0.25 \times 0.62$ low-pressure 3-bar compression (measured for industrial reciprocating heads) = **0.155 net wind-to-pneumatic**. *(Note: re-expanding through an air motor to electricity cuts this in half to ~0.07.)*
* **Itemized CapEx ($2,750):** Pad tripod + mast + 10 m sailwing ($1,350); belt drive + cast-iron twin-cylinder compressor pump head ($600); 150 m PE airline + submerged weighted 10 m³ PVC/Hypalon bladder + concrete sinkers ($800).
* **Yearly upkeep:** **$220/yr** ($80/yr sails + $140/yr compressor rings/valves/salt corrosion + subsea line check).
* **Life:** 12 yr.
* **Annual output (at 31.5 W/m²):** **3.36 MWh$_{\text{pneu}}$/yr**.
* **Resulting $/MWh:** **$134/MWh$_{\text{pneu}}$** (~$295/MWh$_e$ if re-expanded to electricity).
* **Single most likely failure:** Salt-laden intake air corroding compressor reed valves/cylinders, or underwater bladder chafing on rocks/reef and leaking.
* **Cheapest test (<$200, 3 days):** Run a used belt-driven compressor head ($100) with a bicycle/drill drive into a weighted 200 L heavy-duty vinyl dry-bag/drum ($50) sunk 5 m offshore via 30 m of garden/PE hose ($35) to verify minimum starting torque, 0.5-bar constant back-pressure, and leak rate.

### 12. Bluff-Edge Sited 12 m 2-Blade Teetering Wood/Fiberglass HAWT (Tilt-Down Gin-Pole Mast, Scrap-Diff Speedup) (Electricity)
* **Mechanism:** Moves off a sheltered shorepad to an exposed coastal bluff/headland crest (capturing ~1.25–1.35× ridge speedup) with a low-solidity ($\sigma \approx 0.03$), high-TSR ($\lambda = 7$) 2-blade carved-timber/fiberglass teetering rotor on a hinged tilt-down gin-pole mast (winches flat in 15 min for hurricanes), driving a 3.5 kW brushless truck alternator/PMG via a scrap automotive differential + V-belt (15:1 speedup; furling caps power at 3.5 kW to keep drivetrain cheap).
* **Why cheaper:** Eliminates recurring UV fabric replacement (20-year rigid epoxy/fiberglass blades cut upkeep in half!), delivers 40–50% higher $C_p$ than sailwings/VAWTs, scrap differential solves low-RPM torque cost, and bluff-crest siting multiplies available power ~2×.
* **Swept area:** 113 m² (12 m dia, hub at 12 m; requires off-pad guy anchors).
* **Efficiency:** $C_p = 0.36$ (well-measured 0.35–0.42 on 2-blade rigid fiberglass HAWTs) × 0.85 diff/belt × 0.82 alternator/MPPT = **0.25 net wind-to-DC**.
* **Itemized CapEx ($2,800):** 12 m hinged Sch-40/lattice tilt-down gin-pole mast + hand winch + guy anchors ($950); 2× 6 m laminated pine/cedar + fiberglass/epoxy blades + teetering hub + furling tail ($900); scrap car differential + V-belt 15:1 speedup + 3.5 kW brushless truck alternator + MPPT/dump load/cable ($950).
* **Yearly upkeep:** **$110/yr** (leading-edge tape every 3 yr, grease, belts, paint—zero fabric).
* **Life:** 20 yr.
* **Annual output:** **8.05 MWh$_e$/yr** at baseline 32.5 W/m²; **16.1 MWh$_e$/yr** at bluff-crest 65 W/m² (1.26× speedup `[uncertain—must measure on site]`).
* **Resulting $/MWh:** **$31/MWh$_e$** at baseline 32.5 W/m²; **$15.5/MWh$_e$** at bluff-crest 65 W/m². *(Paired with Idea #2's direct ice-bank chiller: ~$11/MWh$_{\text{cool}}$ at baseline, **~$5.5/MWh$_{\text{cool}}$** at bluff crest.)*
* **Single most likely failure:** Blade root fatigue/delamination from hand-layup imperfections, or failure to tilt the mast down in time before a fast-intensifying hurricane.
* **Cheapest test (<$200, 3 days):** Buy two $45 datalogging/handheld anemometers + a 6 m telescoping PVC/fiberglass pole ($40) and log 3 afternoons simultaneously on the pad vs the highest/most windward nearby headland crest—this immediately proves or kills the 1.25–1.35× speedup assumption (a 2×+ jump in power).

---

## 4. Rankings & What to Build First

### Rank A — Realistic $/MWh (at stated NASA POWER baseline: 31–44 W/m²)
| Rank | Idea | End Product | Baseline $/MWh | Notes |
|---:|---|---|---:|---|
| 1 | **#12** 12 m 2-Blade Teetering Rigid HAWT | Electricity | **$31/MWh$_e$** | Lowest high-exergy $/MWh; 20-yr rigid blades kill fabric upkeep |
| 2 | **#2** 10 m Sailwing → Direct A/C Ice Bank | Cooling/Ice | **$35/MWh$_{\text{cool}}$** | Lowest strictly on the 4×4 m pad; COP 2.6 + ice storage |
| 3 | **#1** 14 m Rim-Driven Sailwing on Pad Turntable | Electricity | **$49/MWh$_e$** | Biggest swept area on the 4×4 m pad; gearbox-free |
| 4 | **#5** Guyed Troposkein VAWT → Paddle Churn | Heat | **$53/MWh$_{\text{th}}$** | Very robust, but heat has low value in tropical Punta Mita |
| 5 | **#3** 45 m² Autonomous Pumping Kite → RO Pump | Hydraulic | **$81/MWh$_{\text{hyd}}$** | Kite UV wear + controller complexity hurt at 45 m² scale |
| 6 | **#4** TRPT Daisy-Kite + Solar Lifter Balloon | Mechanical | **$128/MWh$_{\text{mech}}$** | Lull/dusk tangle risk + UV fabric upkeep |
| 7 | **#7** 16-Rotor Cable "Wind Curtain" (E-Bike Hubs) | Electricity | **$129/MWh$_e$** | Fixed-heading cosine loss + salt-corroded cheap hubs |
| 8 | **#6** Cretan 8 m Sailmill → Diaphragm Pump | Hydraulic | **$131/MWh$_{\text{hyd}}$** | Dead simple & reliable, but low $C_p$ (0.13 net) |
| 9 | **#11** 10 m Sailwing → Subsea Air-Bag Storage | Pneumatic | **$134/MWh$_{\text{pneu}}$** | Low compression efficiency (~$295/MWh$_e$ if re-expanded) |
| 10 | **#8** Shared Shade Palapa + Roof-Lip Micro-Rotors | Electricity | **$170/MWh$_e$** | Marginal only (~$390 full); 12 m² swept area is too small |
| 11 | **#10** Offshore Wind/Wave Hybrid Pumping Spar | Hydraulic | **$215/MWh$_{\text{hyd}}$** | Marine O&M + biofouling crush small offshore hardware |
| 12 | **#9** Endless-Loop "Wind Clothesline" Chutes | Mechanical | **$235/MWh$_{\text{mech}}$** | Drag Betz limit + UV fabric wear kill lifetime cost |

### Rank B — Upside $/MWh (if local sea-breeze / bluff / jet hits 70–90 W/m², with optimal scaling/pairing)
1. **#2 Direct Wind-to-Ice Chiller** (paired with #1's 14 m rim-drive or #12's rigid blades): **$5–$10/MWh$_{\text{cool}}$** *(only credible path under $10/MWh)*
2. **#12 Bluff-Edge 12 m 2-Blade Teetering Rigid HAWT:** **$13–$16/MWh$_e$**
3. **#1 14 m Rim-Driven Bicycle-Wheel Sailwing HAWT:** **$19–$22/MWh$_e$** *(~$10/MWh$_{\text{cool}}$ driving a chiller)*
4. **#5 Guyed Troposkein VAWT → Hydraulic Churn:** **$16–$22/MWh$_{\text{th}}$** *(if resort DHW/pool load exists)*
5. **#3 Autonomous Pumping Kite** (scaled to 100 m² in a 90 W/m² coastal jet, 5-yr UV kite): **$20–$25/MWh$_{\text{hyd}}$**
6. **#4 TRPT Daisy-Kite + Solar Balloon** (scaled to 5 × 10 m rings): **$35/MWh$_{\text{mech}}$**
7. **#6 Cretan Sailmill → Direct Pump** (scaled to 12 m wheel): **$35/MWh$_{\text{hyd}}$**
8. **#11 Direct Compressed Air + Subsea Bladder** (14 m rotor): **$38/MWh$_{\text{pneu}}$**
9. **#7 Multi-Rotor Wind Curtain** (bluff-sited + weathervaning frame): **$40/MWh$_e$**
10. **#10 Offshore Wind/Wave Hybrid Spar** (scaled to 10 × 8 m VAWT): **$65/MWh$_{\text{hyd}}$**
11. **#8 Shared Shade Palapa + Roof-Lip Micro-Rotors** (15 m roofline): **$70/MWh$_e$** marginal
12. **#9 Endless-Loop Wind Clothesline** (5 × 40 m² chutes): **$70/MWh$_{\text{mech}}$**

### The ONE Thing I Would Build First (Next Week)
* **Day 1 mandatory prerequisite ($60):** Put a logging anemometer on a 6 m pole at the pad (and spot-check any nearby bluff crest at 2–5 PM). Knowing whether real wind is 3.2 m/s or 4.5 m/s shifts every $/MWh number by **2.8×**.
* **First prototype (Days 2–6): A 5 m scaled prototype of Idea #1 (Tensioned Bicycle-Wheel Rim-Driven Sailwing) driving Idea #2's PTO bench (swap between a $100 brushless alternator and a $100 junkyard Sanden A/C compressor freezing an insulated ice chest).**
  * **Why this first:** Unlike #12 (carving 6 m fiberglass blades takes weeks) or #3 (autonomous kite control takes months of crashes), a 5 m spoked EMT-rim sailwing can be welded and sewn in Puerto Vallarta in **4 days for ~$400**. It immediately validates the two highest-leverage breakthroughs—**gearbox-free rim-drive speedup** and **direct variable-RPM ice-making**—right on the 4×4 m pad. Once proven and backed by site wind logs, scale the rim to 12–14 m (#1/#2) or upgrade to 20-year rigid fiberglass blades (#12) to push toward $10/MWh$_{\text{cool}}$ / $15–$20/MWh$_e$.
