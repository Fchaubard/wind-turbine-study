"""Free-yaw option: a guyless tripod (no cable can cross the rotor as it swings). Pin-jointed leg forces for wind from any azimuth."""
import json, math
import numpy as np
from cad_params import P
A0 = json.load(open("out/energy_audit.json"))["steps"]; FEA = json.load(open("out/sail_fea.json"))
E, FY, g = 200e9, 230e6, 9.81; od, w = P["pole_od"], P["pole_wall"]; idd = od - 2 * w
Aa = math.pi / 4 * (od**2 - idd**2); I = math.pi / 64 * (od**4 - idd**4)
ZA, W = 5.7, (22 + 19 + 25) * g            # apex height; head + rotor + tail weight
rows = []
for Rb in (1.6, 2.0, 2.4, 2.8, 3.2):
    feet = [np.array([Rb * math.cos(a), Rb * math.sin(a), 0.0]) for a in np.radians((90, 210, 330))]; apex = np.array([0, 0, ZA]); L = np.linalg.norm(feet[0] - apex)
    U = np.column_stack([(f - apex) / L for f in feet]); res = {}
    for T, lab in ((1025.0, "12"), (2058.0, "17")):
        cmax = tmax = 0.0
        for az in np.radians(np.arange(0, 360, 5)):
            F = np.array([T * math.cos(az), T * math.sin(az), -W]); t = np.linalg.solve(U, -F)      # + = tension
            cmax = max(cmax, -t.min()); tmax = max(tmax, t.max())
        res[lab] = dict(comp=cmax, uplift=tmax * ZA / L, buck=math.pi**2 * E * I / L**2 / cmax, yld=FY * Aa / cmax)
    r_tip = Rb * (ZA - (P["hub_z"] - P["R"])) / ZA; overhang = max(r_tip + 0.25 - P["R"] * math.sin(P["cone"]) + P["sail_belly"], 0.3)
    rows.append(dict(Rb=Rb, L=L, overhang=overhang, **{f"{k}{l}": v for l, d in res.items() for k, v in d.items()}))
    print(f"base radius {Rb} m, legs {L:.2f} m: overhang needed {overhang:.2f} m | 12 m/s buckling SF {res['12']['buck']:.1f}, foot uplift {res['12']['uplift']/g:.0f} kg | 17 m/s buckling SF {res['17']['buck']:.1f}, uplift {res['17']['uplift']/g:.0f} kg")
base = 1125.0; tarp5 = 4 * 765 / 18.5
extra = (2 * 545 - 28 * 27 - 12 * 22) / 18.5 + 30 + 40          # 2 more post tubes, no guys, tail vane, yaw bearing (last two are allowances)
fx = A0["fixed rotor + drag (3 N·m bearings/chain, 1 N·m cogging)"]; ty = A0["tail vane + drag"]
c = dict(fixed_W=fx, yaw_W=ty, fixed_usd_MWh=(base + tarp5) / (fx * 8.766 * 5 / 1000), yaw_capex=base + extra, yaw_usd_MWh=(base + extra + tarp5) / (ty * 8.766 * 5 / 1000))
print(c); json.dump(dict(rows=rows, corrected=c), open("out/yaw_tower.json", "w"), indent=1)
