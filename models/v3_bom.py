"""v3 cost and energy at each passing hub height. Same wind, Cp capped at .38, field factor .75, 1,200 W generator, shut down above 12 m/s. Prices: seen = read on a seller page; est = estimate."""
import json, math, io, contextlib
import numpy as np
with contextlib.redirect_stdout(io.StringIO()):
    import zoo4 as Z4
RT = json.load(open("out/v3_rotor.json")); FX = 18.5; A = math.pi * 25; CP = min(RT["peak_cp"], .38); L = RT["peak_tsr"]; IT = json.load(open("out/v3_iter.json"))
def W(hub, s=1.0, eta=.95 * .84 * .95, cap=1200., qd=14.):
    v = Z4.VG * s; return float(np.minimum(np.maximum(CP * .75 * .5 * 1.18 * v**3 * A - qd * L * v / 5, 0) * eta, cap) * (v <= 12) @ Z4.hist(hub, "free", 1.0)) * .97
def bom(hub):
    legm = 3 * math.hypot(hub - .25, 2); n6 = math.ceil(legm / 6)
    return [("Blades", "Pine planks 2x6 in x 8 ft, laminated (0.74 m3 with waste)", 57, 300, "MXN", "est"), ("Blades", "Marine epoxy, 3 gal", 3, 37, "USD", "seen"), ("Blades", "Glass cloth, 6 kg, leading edge and skin", 6, 179.2, "MXN", "seen"), ("Blades", "Hub plates 680 mm x 12 mm, M16 bolts (24)", 1, 3800, "MXN", "est"),
            ("Tower", f"3 in Sch 40 pipe, {legm:.0f} m", 1, legm * 680, "MXN", "est"), ("Tower", "1-1/2 in Sch 40 braces, 13 m", 1, 13 * 75 * 2, "MXN", "est"), ("Tower", "Head: 5 in Sch 40, 2.5 m; tail 2-1/2 in Sch 80, 4 m", 1, 2.5 * 1250 + 4 * 520, "MXN", "est"), ("Tower", "Welding, hinged feet, apex, galvanizing or zinc paint", 1, 14000, "MXN", "est"), ("Tower", "M20 stainless epoxy anchors (12)", 12, 260, "MXN", "est"),
            ("Drive", "7,000 lb idler hub, rotor bearing", 1, 112.17, "USD", "seen"), ("Drive", "7,000 lb idler hub, yaw bearing", 1, 112.17, "USD", "seen"), ("Drive", "Two spindles", 2, 45, "USD", "est"), ("Drive", "530 chain, 60T and 12T sprockets", 1, 2600, "MXN", "est"), ("Drive", "Disc brake, furl hinge, cable", 1, 2500, "MXN", "est"), ("Drive", "Truck shock absorber as yaw damper", 1, 800, "MXN", "est"),
            ("Electric", "48 V 1,200 W hub motor", 1, 239.99, "USD", "seen"), ("Electric", "1 kW wind MPPT controller", 1, 178.46, "USD", "seen"), ("Electric", "Rectifier", 1, 20.65, "USD", "seen"), ("Electric", "Dump resistors", 4, 10.55, "USD", "seen"), ("Electric", "Victron shunt", 1, 117.30, "USD", "seen"), ("Electric", "Cable, lugs, paint", 1, 2500, "MXN", "est"), ("Lift", "Hand winch, cable, gin pole", 1, 2500, "MXN", "est")]
def usd(r): return r[2] * r[3] / (FX if r[4] == "MXN" else 1)
def life(c, blades, elec, kw, y): wear = 130.; return (c + wear * (y - 1) + (blades + .3 * elec if y > 10 else 0)) / (kw * 8.766 * y / 1000)
res = []
for hub in (8.5, 10., 12.):
    B = bom(hub); c = sum(map(usd, B)); bl = sum(usd(r) for r in B if r[0] == "Blades"); el = sum(usd(r) for r in B if r[0] == "Electric"); a = W(hub); res.append(dict(hub=hub, capex=c, W=a, u20=life(c, bl, el, a, 20), u5=life(c, bl, el, a, 5), u20w=life(c, bl, el, W(hub, 1.3), 20), W13=W(hub, 1.3), seen=sum(usd(r) for r in B if r[5] == "seen"), bl=bl, el=el))
    cc = c - el + 320 * 2.04 + 40; h = W(hub, eta=.92 * .95, cap=5000., qd=18.); res[-1].update(heatW=h, heat20=life(cc, bl, 320 * 2.04, h, 20), heatcap=cc); print(f"hub {hub:4.1f}: ${c:,.0f} parts, {a:.0f} W, {a*8.766:.0f} kWh/yr | ${res[-1]['u20']:.0f}/MWh 20y, ${res[-1]['u5']:.0f} 5y, ${res[-1]['u20w']:.0f} at 1.3x | hot water {h:.0f} W ${res[-1]['heat20']:.0f}/MWh")
best = min(res, key=lambda r: r["u20"]); print("best hub", best["hub"]); json.dump(dict(all=res, best=best, items=[dict(group=r[0], item=r[1], qty=r[2], unit=r[3], cur=r[4], status=r[5], usd=usd(r)) for r in bom(best["hub"])]), open("out/v3_bom.json", "w"), indent=1)
