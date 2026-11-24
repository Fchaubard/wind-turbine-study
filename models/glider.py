"""GLIDER TURBINE: a controlled, tethered rigid wing carries a rotor and generator, holding station in the wind. Optional small balloon keeps it up in calm air; without it, the glider lands on the pad whenever wind cannot hold it. Hourly equilibrium: lift + buoyancy must hold the tether at the chosen angle against rotor thrust, wing drag and weight.
Also checks a tripod of legs deployed from the glider to a 4 m pad. Launch, docking transients and flight dynamics are not simulated. Prices are budget estimates."""
import json, math, itertools
import numpy as np
src_ = open("blimp.py").read(); exec(src_[:src_.index("GAS = {")])
WV = {"ERA5": None, "NASA": None}; CL = 1.1; WK = 1.2; R = []
GAS = {"no balloon, lands": None, "balloon, cheap helium": dict(gas=10., leak=.002, env=10., life=8), "balloon, normal helium": dict(gas=20., leak=.005, env=20., life=5)}
def balloon(need):
    for V in np.geomspace(5, 9000, 140):
        if 1.02 * V - .25 * 4.84 * V**(2 / 3) >= need: return float(V)
    return None
for src, D, z, th, sr, LD, (gn, g), wc in itertools.product(("NASA", "ERA5"), (6, 10, 14), (30, 60, 100, 150), (25, 35, 45), (.15, .25, .4, .6, .9), (10, 15), GAS.items(), (25, 60)):
    A = math.pi * D * D / 4; S = sr * A; L = z / math.sin(math.radians(th)); mr = P14["mass"] * (D / 14)**2.5 + 35 + 8 * (D / 10)**2; mt = .07 * L; ms = WK * S + 12; need = mr + mt + ms; tn = math.tan(math.radians(th))
    if g: V = balloon(1.1 * need); Ab = V**(2 / 3) if V else None
    else: V, Ab = 0., 0.
    if V is None: continue
    v = wind(z, src) * math.cos(math.radians(10)); q = .5 * RHO * v * v; net = ((1.02 * V - .25 * 4.84 * Ab - need) * G) if g else -need * G; fly = net + q * (CL * S + .4 * Ab) >= tn * q * (.7 * A + CL * S / LD + .12 * Ab); fly &= v <= 12.; tr = int(np.sum(fly[1:] != fly[:-1])) / (len(fly) / 8766) / 2; av = .9 if g else max(.75 - .0002 * tr, .3)
    for ng in (1, 2, 4):
        W = float(np.mean(np.minimum(k * .5 * RHO * A * v**3, 1200 * ng) * (v >= 2.5) * fly)) * av
        if W < 5: continue
        Td = 1.5 * math.hypot(.7 * .5 * RHO * 144 * A + CL * .5 * RHO * 144 * S / LD, CL * .5 * RHO * 144 * S); teth = L * 8 * max(1, Td / 12000); wing = S * wc + 900; rotor = 538 * (D / 10)**2.5; elec = 733 * ng; env = 4.84 * Ab * g["env"] if g else 0; gas = V * g["gas"] if g else 0; cap = COMMON - 733 + elec + rotor + wing + teth + env + gas + 1500 + 1500; yr = wing / 8 + teth / 5 + .05 * rotor + 120 + (env / g["life"] + gas * g["leak"] * 365 if g else 0) + (tr * 2 if not g else 0); life = cap + yr * 19 + .3 * elec; R.append(dict(src=src, D=D, z=z, angle=th, wing_m2=S, LD=LD, mode=gn, wing_cost=wc, ng=ng, W=W, capex=cap, usd=life / (W * 8.766 * 20 / 1000), fly_share=float(fly.mean()), landings=tr, V=V, yearly=yr, line_kN=Td / 1000))
T = {s: float(json.load(open("out/blimp.json"))["tower"]["usd"][s]) for s in ("NASA", "ERA5")}; out = dict(tower=T, best={}); print("tower Dandelion:", {k: round(v) for k, v in T.items()})
for s in ("NASA", "ERA5"):
    for m in GAS:
        for wc in (25, 60):
            b = min((r for r in R if r["src"] == s and r["mode"] == m and r["wing_cost"] == wc), key=lambda r: r["usd"]); out["best"][f"{s}|{m}|{wc}"] = b; print(f"{s}, {m}, wing ${wc}/m²: {b['D']} m rotor at {b['z']} m, tether {b['angle']}°, wing {b['wing_m2']:.0f} m², L/D {b['LD']}, balloon {b['V']:.0f} m³ | flies {b['fly_share']*100:.0f}% of hours, {b['landings']:.0f} landings/yr | {b['W']:.0f} W, build ${b['capex']:,.0f}, upkeep ${b['yearly']:,.0f}/yr, ${b['usd']:.0f}/MWh")
print("tripod from glider to a 4 m pad (feet 2 m from center): all three lines stay tight only if lift/thrust exceeds height/2:")
out["tripod"] = {}
for h in (15, 30, 60, 100):
    ratio = h / 2; A = math.pi * 49; wing = (ratio * .7 * A) / CL; out["tripod"][h] = dict(ratio=ratio, wing_m2=wing); print(f" {h} m high: lift must be {ratio:.0f}× rotor thrust, wing about {wing:,.0f} m² for a 14 m rotor")
json.dump(out, open("out/glider.json", "w"), indent=1, default=float)
