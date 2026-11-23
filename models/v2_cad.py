"""CAD of machine v2, with a swept-rotor clearance check over all yaw angles. Writes out/cad2/."""
import json, math, os, warnings
import numpy as np, cadquery as cq
from v2_params import V2 as P
warnings.filterwarnings("ignore"); os.makedirs("out/cad2", exist_ok=True); V = cq.Vector; parts = []
def tube(a, b, od, idd=0.0):
    a, b = V(*map(float, a)), V(*map(float, b)); d = b - a; s = cq.Solid.makeCylinder(od / 2, d.Length, a, d)
    return s.cut(cq.Solid.makeCylinder(idd / 2, d.Length, a, d)) if idd else s
def add(n, g, s, c, rho): parts.append(dict(name=n, group=g, solid=s, colour=c, rho=rho))
ST = 7850.0; feet = [np.array([P["foot_r"] * math.cos(a), P["foot_r"] * math.sin(a), 0.0]) for a in np.radians((90, 210, 330))]; apex = np.array([0, 0, P["apex_z"]])

def clearance(over):
    """minimum distance from the rotor's swept envelope (spars + bellied sails) to any leg, over all yaw angles"""
    c, R = P["cone"], P["R"]; prof = []
    for s in np.linspace(P["spar_in"], R, 30): prof.append((-over - s * math.sin(c), s * math.cos(c)))
    cl = (-over - R * P["clew_r"] * math.sin(c) + P["belly"], R * P["clew_r"] * math.cos(c))
    for s in np.linspace(P["luff"][0], P["luff"][1], 12):
        for t in np.linspace(0, 1, 8): prof.append(((1 - t) * (-over - s * math.sin(c)) + t * cl[0], (1 - t) * s * math.cos(c) + t * cl[1]))
    prof = np.array(prof); best = 9.0; hubz = P["hub_z"]
    for yaw in np.radians(np.arange(0, 360, 5)):
        n = np.array([math.cos(yaw), math.sin(yaw), 0.0])
        for f in feet:
            pts = f + np.linspace(0, 1, 120)[:, None] * (apex - f); r = pts - np.array([0, 0, hubz]); a = r @ n; rho = np.linalg.norm(r - a[:, None] * n, axis=1)
            d = np.sqrt((a[:, None] - prof[:, 0][None])**2 + (rho[:, None] - prof[:, 1][None])**2); best = min(best, float(d.min()))
    return best - P["leg_od"] / 2
over = P["overhang"]
while clearance(over) < 0.30: over += 0.05
while over > 0.5 and clearance(over - 0.05) >= 0.30: over -= 0.05
P["overhang"] = round(over, 2); hub = np.array([-P["overhang"], 0, P["hub_z"]])
od, idd = P["leg_od"], P["leg_od"] - 2 * P["leg_w"]
for i, f in enumerate(feet):
    u = (apex - f) / np.linalg.norm(apex - f); L = np.linalg.norm(apex - f); n = math.ceil(L / 3.05)
    for k in range(n): add(f"Leg {i+1} tube {k+1}", "tower", tube(f + u * k * L / n, f + u * (k + 1) * L / n, od, idd), "#6b7078", ST)
    add(f"Base plate {i+1}", "tower", cq.Solid.makeBox(0.25, 0.25, 0.01, V(f[0] - .125, f[1] - .125, -0.01)), "#3a3d42", ST)
bo, bi = P["brace_od"], P["brace_od"] - 2 * P["brace_w"]
for z in P["brace_z"]:
    pts = [f + (apex - f) * z / P["apex_z"] for f in feet]
    for a, b in ((0, 1), (1, 2), (2, 0)): add(f"Brace at {z} m, {a+1}-{b+1}", "tower", tube(pts[a], pts[b], bo, bi), "#8a8f96", ST)
add("Yaw post + trailer hub", "head", tube(apex, apex + [0, 0, 0.22], P["head_od"], P["head_od"] - 2 * P["head_w"]), "#d85a30", ST)
add("Head beam", "head", tube(hub + [0.12, 0, -0.06], np.array([0.25, 0, P["hub_z"] - 0.06]), P["head_od"], P["head_od"] - 2 * P["head_w"]), "#22252a", ST)
add("Main shaft on trailer hub", "head", tube(hub, np.array([0.05, 0, P["hub_z"]]), 0.04), "#22252a", ST)
xs = hub[0] + 0.28; add("53T motorcycle sprocket", "head", tube((xs, 0, P["hub_z"]), (xs + .006, 0, P["hub_z"]), 0.215, .05), "#e06c2f", ST)
jz = P["hub_z"] - P["jack_drop"]; add("Jackshaft", "head", tube((xs - .03, 0, jz), (xs + .12, 0, jz), .025), "#22252a", ST)
add("14T sprocket", "head", tube((xs, 0, jz), (xs + .006, 0, jz), .06, .025), "#e06c2f", ST); add("48T ring", "head", tube((xs + .08, 0, jz), (xs + .084, 0, jz), .195, .03), "#e06c2f", ST)
mz = jz + P["motor_drop"] * 0.0 + 0.0; my = P["motor_drop"]
add("Hub motor (generator)", "head", tube((xs + .05, my, jz), (xs + .12, my, jz), .24), "#1d9e75", 3200.0)
for k, dx in enumerate((-P["spar_od"] / 2 - P["hub_t"], P["spar_od"] / 2)): add(f"Hub disc {k+1}", "rotor", cq.Solid.makeCylinder(P["hub_d"] / 2, P["hub_t"], V(*(hub + [dx, 0, 0])), V(1, 0, 0)), "#c9a26b", 550.0)
def sd(i):
    a = 2 * math.pi * i / P["n"] + math.pi / 2; c = P["cone"]; return np.array([-math.sin(c), math.cos(c) * math.cos(a), math.cos(c) * math.sin(a)])
bow = hub + [-P["bow"], 0, 0]; so, si = P["spar_od"], P["spar_od"] - 2 * P["spar_w"]
add("Bowsprit", "rotor", tube(hub + [-.03, 0, 0], bow, so, si), "#3a3d42", ST)
for i in range(P["n"]):
    d, dn = sd(i), sd(i - 1); add(f"Spar {i+1}", "rotor", tube(hub + d * P["spar_in"], hub + d * P["R"], so, si), "#3a3d42", ST)
    for fr, nm in ((1.0, "tip"), (0.65, "mid")): add(f"Stay {nm} {i+1}", "rotor", tube(bow, hub + d * P["R"] * fr, P["stay_d"]), "#d9d2c0", 1100.0)
    a, b, c = hub + d * P["luff"][0], hub + d * P["luff"][1], hub + dn * P["R"] * P["clew_r"] + [P["belly"], 0, 0]; n = np.cross(b - a, c - a); n /= np.linalg.norm(n)
    add(f"Sail {i+1}", "sails", cq.Solid.extrudeLinear(cq.Face.makeFromWires(cq.Wire.makePolygon([V(*a), V(*b), V(*c), V(*a)])), V(*(n * .0015))), "#3b8bd4", 70.0)
tb = np.array([0.25, 0, P["hub_z"] - .06]); te = tb + [P["tail_boom"], 0, 0]
add("Tail boom", "head", tube(tb, te, P["head_od"], P["head_od"] - 2 * P["head_w"]), "#3a3d42", ST); add("Tail vane", "head", cq.Solid.makeBox(P["tail_w"], .012, P["tail_h"], V(te[0] - P["tail_w"], -.006, te[2] - P["tail_h"] / 2)), "#c9a26b", 550.0)
asm = cq.Assembly(name="punta_mita_v2"); rows = []
for p in parts:
    asm.add(p["solid"], name="".join(ch if ch.isalnum() else "_" for ch in p["name"]), color=cq.Color(*[int(p["colour"][i:i + 2], 16) / 255 for i in (1, 3, 5)]))
    rows.append(dict(name=p["name"], group=p["group"], mass_kg=p["solid"].Volume() * p["rho"]))
asm.export("out/cad2/punta_mita_v2.step"); cq.exporters.export(cq.Compound.makeCompound([p["solid"] for p in parts]), "out/cad2/punta_mita_v2.stl", tolerance=.005, angularTolerance=.3)
G = {}; [G.__setitem__(r["group"], G.get(r["group"], 0) + r["mass_kg"]) for r in rows]
tl = P["hub_z"] - P["R"]; cl = clearance(P["overhang"])
# yaw balance: the tail must not hit a leg, and the sail tips must clear the pad
ck = [("Rotor swept envelope to legs, all yaw angles", cl, .30), ("Lowest blade tip above the pad", tl, 3.0), ("Tail vane to legs (below apex)", P["tail_boom"] - P["tail_w"] + .25, .5), ("Gap between spars at the hub", 2 * math.pi * P["spar_in"] / P["n"] - P["spar_od"], .04)]
for n_, v, need in ck: print(f"{'OK  ' if v >= need else 'FAIL'} {n_:48s}{v*1000:7.0f} mm (need {need*1000:.0f})")
print(len(parts), "solids; overhang", P["overhang"], "m; masses", {k: round(v) for k, v in G.items()})
json.dump(dict(params={k: v for k, v in P.items()}, checks=[dict(check=a, m=b, need=c) for a, b, c in ck], masses=G, n=len(parts)), open("out/cad2/v2.json", "w"), indent=1, default=float)
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
def render(fn, el, az, lim, groups=None):
    fig = plt.figure(figsize=(6, 7), dpi=170); ax = fig.add_subplot(111, projection="3d")
    for p in parts:
        if groups and p["group"] not in groups: continue
        vs, tr = p["solid"].tessellate(.01, .5); v = np.array([[q.x, q.y, q.z] for q in vs]); ax.add_collection3d(Poly3DCollection(v[np.array(tr)], facecolor=p["colour"], edgecolor="none", alpha=.92))
    (a, b), (c, d), (e, f) = lim; ax.set_xlim(a, b); ax.set_ylim(c, d); ax.set_zlim(e, f); ax.set_box_aspect((b - a, d - c, f - e)); ax.view_init(el, az); ax.set_axis_off(); fig.subplots_adjust(0, 0, 1, 1); fig.savefig(fn); plt.close(fig)
render("out/cad2/iso.png", 10, -130, ((-4, 4.5), (-4.2, 4.2), (0, 16)))
render("out/cad2/head.png", 14, -125, ((-1.3, 1.1), (-.8, .8), (11.2, 12.8)), ("head", "tower"))
