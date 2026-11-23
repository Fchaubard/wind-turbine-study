"""CAD of machine v3 (10 m rigid wood rotor), with swept clearance of the BENT blade (17 m/s) against the legs at all yaw angles. Writes out/cad3/."""
import json, math, os, warnings
import numpy as np, cadquery as cq
import v3_rotor as Rt
warnings.filterwarnings("ignore"); os.makedirs("out/cad3", exist_ok=True); V = cq.Vector; parts = []
RT = json.load(open("out/v3_rotor.json")); D3 = json.load(open("out/v3_design.json")); e = D3["e"]
import os as _o
pick = dict(hub=float(_o.environ.get("V3_HUB", 12.0)), leg="3 in Sch 40", nbr=2); HUB, FOOT, CONE = pick["hub"], 2.0, Rt.CONE; AZ = HUB - .25; R = RT["R"]
LEG = {"2-1/2 in Sch 40": (.0730, .00516), "3 in Sch 40": (.0889, .00549), "4 in Sch 40": (.1143, .00602), "73 mm x 1.2 post tube": (.073, .0012)}[pick["leg"]]; NBR = pick["nbr"]
geo = Rt.geometry(RT["chord"][0], RT["chord"][1], RT["twist"][0], RT["twist"][1], RT["thick"][0], RT["thick"][1]); TIP = D3["blade"]["17"]["tip"]
feet = [np.array([FOOT * math.cos(a), FOOT * math.sin(a), 0.0]) for a in np.radians((90, 210, 330))]; apex = np.array([0, 0, AZ])
def clearance(over):
    best = 9.0
    for s in np.linspace(.6, R, 40):
        defl = TIP * (s / R)**2; c = geo(min(s, R * .985))[0]; x = -over - s * math.sin(CONE) + defl + .3 * c; rho = s * math.cos(CONE)
        for yaw in np.radians(np.arange(0, 360, 5)):
            n = np.array([math.cos(yaw), math.sin(yaw), 0])
            for f in feet:
                p = f + np.linspace(0, 1, 100)[:, None] * (apex - f); r = p - [0, 0, HUB]; a = r @ n; q = np.linalg.norm(r - a[:, None] * n, axis=1); best = min(best, float(np.hypot(a - x, q - rho).min()))
    return best - LEG[0] / 2
over = .6
while clearance(over) < .30: over += .05
over = round(over, 2); hub = np.array([-over, 0, HUB])
def tube(a, b, od, idd=0.0):
    a, b = V(*map(float, a)), V(*map(float, b)); d = b - a; s = cq.Solid.makeCylinder(od / 2, d.Length, a, d)
    return s.cut(cq.Solid.makeCylinder(idd / 2, d.Length, a, d)) if idd else s
def add(n, g, s, c, rho): parts.append(dict(name=n, group=g, solid=s, colour=c, rho=rho))
ST = 7850.0; od, idd = LEG[0], LEG[0] - 2 * LEG[1]
add("Concrete pad (yours)", "pad", cq.Solid.makeBox(4.6, 4.6, .25, V(-2.3, -2.3, -.26)), "#b9b5aa", 2400.0)
for i, f in enumerate(feet):
    add(f"Leg {i+1}", "tower", tube(f, apex, od, idd), "#6b7078", ST); add(f"Base plate {i+1}", "tower", cq.Solid.makeBox(.3, .3, .012, V(f[0] - .15, f[1] - .15, -.012)), "#3a3d42", ST)
for k in range(NBR):
    z = AZ * (k + 1) / (NBR + 1); pts = [f + (apex - f) * z / AZ for f in feet]
    for a, b in ((0, 1), (1, 2), (2, 0)): add(f"Brace {k+1}.{a+1}", "tower", tube(pts[a], pts[b], .0483, .0483 - .0074), "#8a8f96", ST)
H = (.1413, .1413 - .0131)
add("Yaw post", "head", tube(apex, apex + [0, 0, .25], *H), "#d85a30", ST); add("Head beam", "head", tube(hub + [.15, 0, -.08], [.3, 0, HUB - .08], *H), "#22252a", ST)
add("Non-rotating trailer spindle", "head", tube(hub, hub + [.40, 0, 0], .055), "#22252a", ST); add("Generator", "head", tube(hub + [.32, 0, -.42], hub + [.48, 0, -.42], .30), "#1d9e75", 3200.0)
add("Chain sprocket", "head", tube(hub + [.28, 0, 0], hub + [.29, 0, 0], .30, .05), "#e06c2f", ST)
add("Hub plate front", "rotor", cq.Solid.makeCylinder(.34, .012, V(*(hub + [-.09, 0, 0])), V(1, 0, 0)), "#3a3d42", ST); add("Hub plate back", "rotor", cq.Solid.makeCylinder(.34, .012, V(*(hub + [.08, 0, 0])), V(1, 0, 0)), "#3a3d42", ST)
tb = np.array([.3, 0, HUB - .08]); te = tb + [3.6, 0, 0]; add("Tail boom", "head", tube(tb, te, .0730, .0730 - .01402), "#3a3d42", ST); add("Tail vane", "head", cq.Solid.makeBox(1.8, .015, 1.4, V(te[0] - 1.8, -.0075, te[2] - .7)), "#c9a26b", 550.0)
def foil(tc, n=18):
    xs = (1 - np.cos(np.linspace(0, math.pi, n))) / 2; yt = 5 * tc * (.2969 * np.sqrt(xs) - .126 * xs - .3516 * xs**2 + .2843 * xs**3 - .1036 * xs**4); yc = .04 / .16 * (2 * .4 * xs - xs**2) * (xs < .4) + .04 / .36 * (1 - .8 + 2 * .4 * xs - xs**2) * (xs >= .4)
    up = np.column_stack([xs, yc + yt]); lo = np.column_stack([xs, yc - yt]); return np.vstack([up[::-1], lo[1:-1]])
def blade(i):
    a = 2 * math.pi * i / 3 + math.pi / 2; dr = np.array([-math.sin(CONE), math.cos(CONE) * math.cos(a), math.cos(CONE) * math.sin(a)]); tg = np.array([0, -math.sin(a), math.cos(a)]); ax = np.cross(dr, tg); wires = []
    for r in np.linspace(.55, R, 9):
        c, th, tc = geo(min(r, R * .985)); p = foil(tc) - [.3, 0]; ct, st = math.cos(th), math.sin(th); pts = [hub + dr * r + tg * c * (u * ct - v * st) + ax * c * (u * st + v * ct) for u, v in p]
        wires.append(cq.Wire.assembleEdges([cq.Edge.makeSpline([V(*q) for q in pts] + [V(*pts[0])])]))
    return cq.Solid.makeLoft(wires)
for i in range(3): add(f"Blade {i+1}", "rotor", blade(i), "#c9a26b", Rt.RHO_W)
asm = cq.Assembly(name="punta_mita_v3"); rows = []
for p in parts:
    asm.add(p["solid"], name="".join(ch if ch.isalnum() else "_" for ch in p["name"]), color=cq.Color(*[int(p["colour"][i:i + 2], 16) / 255 for i in (1, 3, 5)])); rows.append(dict(name=p["name"], group=p["group"], mass_kg=p["solid"].Volume() * p["rho"], valid=p["solid"].isValid()))
asm.export("out/cad3/punta_mita_v3.step"); cq.exporters.export(cq.Compound.makeCompound([p["solid"] for p in parts if p["group"] != "pad"]), "out/cad3/punta_mita_v3.stl", tolerance=.008, angularTolerance=.3)
M = {}; [M.__setitem__(r["group"], M.get(r["group"], 0) + r["mass_kg"]) for r in rows]; cl = clearance(over)
ck = [("Bent blade (17 m/s) to legs, all yaw", cl, .30), ("Blade tip above pad", HUB - R, 2.5), ("Tail vane forward edge past legs", 3.6 - 1.8 + .3, .5)]
for n, v, need in ck: print(f"{'OK  ' if v >= need else 'FAIL'} {n:42s}{v*1000:7.0f} mm (need {need*1000:.0f})")
print("pick:", HUB, pick["leg"], "braces", NBR, "overhang", over, "| solids", len(parts), "all valid", all(r["valid"] for r in rows), "| masses", {k: round(v) for k, v in M.items()})
json.dump(dict(hub=HUB, leg=pick["leg"], nbr=NBR, over=over, checks=[dict(check=a, m=b, need=c) for a, b, c in ck], masses=M, pick=pick, n=len(parts)), open("out/cad3/v3.json", "w"), indent=1, default=float)
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
fig = plt.figure(figsize=(6, 7), dpi=170); ax = fig.add_subplot(111, projection="3d")
for p in parts:
    vs, tr = p["solid"].tessellate(.015, .5); v = np.array([[q.x, q.y, q.z] for q in vs]); ax.add_collection3d(Poly3DCollection(v[np.array(tr)], facecolor=p["colour"], edgecolor="none", alpha=.95))
ax.set_xlim(-5, 6); ax.set_ylim(-5.5, 5.5); ax.set_zlim(-.3, HUB + 5.4); ax.set_box_aspect((11, 11, HUB + 5.7)); ax.view_init(10, -130); ax.set_axis_off(); fig.subplots_adjust(0, 0, 1, 1); fig.savefig("out/cad3/iso.png"); plt.close(fig)
