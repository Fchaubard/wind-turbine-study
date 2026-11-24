"""BLIMP TURBINE: gas-filled aerostat + Dandelion-type rotor + generator aloft + power tether + winch on the ocean pad. The aerostat is sized so buoyancy plus its own lift holds the tether at 50 degrees or steeper against rotor thrust at 10 m/s. It is reeled in for storms.
Hourly wind at height is interpolated between ERA5 10 m and 100 m (flat above 120 m, as the weather-model levels show). Compared with the 14 m tower Dandelion on the same wind. NASA's milder shear is shown as a second case. Launch, docking and tether dynamics are not simulated. Prices are budget estimates."""
import json, math, itertools, io, contextlib
import numpy as np
with contextlib.redirect_stdout(io.StringIO()):
    import zoo as Z
RHO, G = 1.18, 9.81; E = json.load(open("out/wind_altitude.json"))["era5"]; V10 = np.array(E["wind_speed_10m"], float); V100 = np.array(E["wind_speed_100m"], float); ok = np.isfinite(V10) & np.isfinite(V100) & (V10 > .05); V10, V100 = V10[ok], V100[ok]; D14 = json.load(open("out/dandelion_big_14_10.json")); P14 = D14["pick"]; LIFE14 = D14["usd"] * D14["W"] * 8.766 * 20 / 1000; COMMON = 2017.
def wind(z, src): return Z.WS * (min(z, 120) / 10)**.14 if src == "NASA" else V10 * (V100 / V10)**(np.log(min(z, 120) / 10) / np.log(10))
lo, hi = .01, .6; base = Z.WS * math.cos(math.radians(10))
for _ in range(50):
    k = .5 * (lo + hi); w = float(np.mean(np.minimum(k * .5 * RHO * math.pi * 49 * base**3, 2400) * (base >= 2.5))) * .95
    if w < D14["W"]: lo = k
    else: hi = k
def power(D, z, src, cap, av=.85): v = wind(z, src) * math.cos(math.radians(10)); return float(np.mean(np.minimum(k * .5 * RHO * math.pi * D * D / 4 * v**3, cap) * (v >= 2.5))) * av
def aerostat(D, z):
    mr = P14["mass"] * (D / 14)**2.5 + 35 + 8 * (D / 10)**2; L = z / math.sin(math.radians(50)); mt = .07 * L; T = .7 * .5 * RHO * 100 * math.pi * D * D / 4
    for Vb in np.geomspace(20, 12000, 90):
        A = Vb**(2 / 3); Bk = 1.02 * Vb - .25 * 4.84 * A - mr - mt
        if Bk <= .15 * (mr + mt): continue
        if Bk * G + .5 * RHO * 100 * .4 * A >= 1.2 * (T + .5 * RHO * 100 * .12 * A): return dict(V=float(Vb), env_m2=4.84 * A, payload=mr, tether_m=L, thrust=T)
    return None
GAS = {"helium, base": dict(gas=20., leak=.005, env=20., life=5), "helium, optimistic": dict(gas=10., leak=.002, env=10., life=8), "hydrogen, optimistic": dict(gas=2., leak=.003, env=10., life=8)}; R = []
for src, D, z, ng, (gn, g) in itertools.product(("ERA5", "NASA"), (4, 6, 8, 10, 14, 18), (30, 60, 100, 150), (1, 2, 4), GAS.items()):
    a = aerostat(D, z)
    if not a: continue
    W = power(D, z, src, 1200 * ng); rotor = 538 * (D / 10)**2.5; env = a["env_m2"] * g["env"]; gas = a["V"] * g["gas"]; teth = a["tether_m"] * 8; elec = 733 * ng; cap = COMMON - 733 + elec + rotor + env + gas + teth + 1500 + 800; yr = env / g["life"] + gas * g["leak"] * 365 + teth / 5 + .05 * rotor + 120; L = cap + yr * 19 + .3 * elec; R.append(dict(src=src, D=D, z=z, ng=ng, gas_type=gn, W=W, cap=cap, usd=L / (W * 8.766 * 20 / 1000), V=a["V"], env=env, gas=gas, tether=teth, rotor=rotor, yr=yr))
base_w = {s: float(np.mean(np.minimum(k * .5 * RHO * math.pi * 49 * (wind(10, s) * math.cos(math.radians(10)))**3, 2400) * (wind(10, s) * math.cos(math.radians(10)) >= 2.5))) * .95 for s in ("ERA5", "NASA")}; bu = {s: LIFE14 / (w * 8.766 * 20 / 1000) for s, w in base_w.items()}; print("14 m tower Dandelion on same wind:", {s: f"{base_w[s]:.0f} W, ${bu[s]:.0f}/MWh" for s in bu}); out = dict(tower=dict(W=base_w, usd=bu), best={})
for src in ("ERA5", "NASA"):
    for gn in GAS:
        b = min((r for r in R if r["src"] == src and r["gas_type"] == gn), key=lambda r: r["usd"]); out["best"][f"{src}|{gn}"] = b; print(f"{src}, {gn}: {b['D']} m rotor at {b['z']} m, {b['V']:.0f} m³ blimp, {b['W']:.0f} W, build ${b['cap']:,.0f}, upkeep ${b['yr']:,.0f}/yr, ${b['usd']:.0f}/MWh | envelope ${b['env']:,.0f}, gas ${b['gas']:,.0f}, tether ${b['tether']:,.0f}, rotor ${b['rotor']:,.0f}")
json.dump(out, open("out/blimp.json", "w"), indent=1, default=float)
