"""Parametric CAD of the Punta Mita sail windmill (CadQuery / OpenCascade).
Writes out/cad/sail_windmill.step (assembly), .stl, a parts list with masses, interference checks, and PNG views."""
import json, math, os, sys
import numpy as np
import cadquery as cq
from cad_params import P

os.makedirs("out/cad", exist_ok=True)
V = cq.Vector
STEEL, PLY, PE = 7850.0, 550.0, 950.0
parts = []          # (name, group, solid, colour, density)


def tube(p0, p1, od, idia=0.0):
    p0, p1 = V(*p0), V(*p1); d = p1 - p0
    s = cq.Solid.makeCylinder(od / 2, d.Length, p0, d)
    if idia > 0:
        s = s.cut(cq.Solid.makeCylinder(idia / 2, d.Length, p0, d))
    return s


def add(name, group, solid, colour, rho):
    parts.append(dict(name=name, group=group, solid=solid, colour=colour, rho=rho))


def spar_dir(i):
    """unit vector along spar i: in the rotor plane, coned upwind (-x) by cone_deg"""
    a = 2 * math.pi * i / P["n_sails"] + math.pi / 2
    c = P["cone"]
    return np.array([-math.sin(c), math.cos(c) * math.cos(a), math.cos(c) * math.sin(a)])


hub = np.array([P["hub_x"], 0.0, P["hub_z"]])
# ---- pole, splints, guys
for k in range(2):
    add(f"Pole tube {k+1}", "pole", tube((0, 0, k * P["pole_seg"]), (0, 0, (k + 1) * P["pole_seg"]), P["pole_od"], P["pole_id"]), "#6b7078", STEEL)
for k in range(P["n_splints"]):
    a = 2 * math.pi * k / P["n_splints"] + math.pi / 4; r = P["pole_od"] / 2 + P["spar_od"] / 2
    add(f"Joint splint {k+1}", "pole", tube((r * math.cos(a), r * math.sin(a), P["pole_seg"] - P["splint_len"] / 2), (r * math.cos(a), r * math.sin(a), P["pole_seg"] + P["splint_len"] / 2), P["spar_od"], P["spar_id"]), "#8a8f96", STEEL)
anchors = []
for az in P["guy_az"]:
    a = math.radians(az)
    for nm, z, r in (("top", P["guy_top_z"], P["guy_top_r"]), ("joint", P["guy_mid_z"], P["guy_mid_r"])):
        g = (r * math.cos(a), r * math.sin(a), 0.0); anchors.append(dict(name=f"{nm} guy {az:.0f}°", xyz=g, z=z))
        add(f"Guy cable, {nm}, {az:.0f}°", "guys", tube((P["pole_od"] / 2 * math.cos(a), P["pole_od"] / 2 * math.sin(a), z), g, P["guy_d"]), "#b0b4ba", STEEL)
pb = np.array([P["prop_base_x"], 0.0, 0.0]); pt = np.array([P["pole_od"] / 2 + 0.04, 0.0, P["prop_top_z"]]); pm = (pb + pt) / 2
add("Back-prop tube 1", "pole", tube(pb, pm, P["pole_od"], P["pole_id"]), "#6b7078", STEEL)
add("Back-prop tube 2", "pole", tube(pm, pt, P["pole_od"], P["pole_id"]), "#6b7078", STEEL)
ud = (pt - pb) / np.linalg.norm(pt - pb)
for k in range(2):
    off = np.array([0.0, (1 if k else -1) * (P["pole_od"] / 2 + P["spar_od"] / 2), 0.0])
    add(f"Prop joint splint {k+1}", "pole", tube(pm - ud * P["splint_len"] / 2 + off, pm + ud * P["splint_len"] / 2 + off, P["spar_od"], P["spar_id"]), "#8a8f96", STEEL)
anchors.append(dict(name="back-prop foot", xyz=pb.tolist(), z=P["prop_top_z"]))
# ---- rotor: hub discs, spars, bowsprit, stays, sails
for k, dx in enumerate((-P["spar_od"] / 2 - P["hub_disc_t"], P["spar_od"] / 2)):
    add(f"Plywood hub disc {k+1}", "rotor", cq.Solid.makeCylinder(P["hub_disc_d"] / 2, P["hub_disc_t"], V(*(hub + [dx, 0, 0])), V(1, 0, 0)), "#c9a26b", PLY)
tips = []
for i in range(P["n_sails"]):
    d = spar_dir(i); p0 = hub + d * P["spar_in"]; p1 = hub + d * P["R"]; tips.append(p1)
    add(f"Spar {i+1}", "rotor", tube(p0, p1, P["spar_od"], P["spar_id"]), "#3a3d42", STEEL)
bow = hub + np.array([-P["bowsprit_len"], 0, 0])
add("Bowsprit", "rotor", tube(hub + [-0.03, 0, 0], bow, P["spar_od"], P["spar_id"]), "#3a3d42", STEEL)
for i, t in enumerate(tips):
    add(f"Stay rope {i+1}", "rotor", tube(bow, t, P["stay_d"]), "#d9d2c0", 1100.0)
    if P.get("stay_mid"):
        add(f"Mid stay rope {i+1}", "rotor", tube(bow, hub + spar_dir(i) * 0.65 * P["R"], P["stay_d"]), "#d9d2c0", 1100.0)
for i in range(P["n_sails"]):
    d = spar_dir(i); dn = spar_dir(i - 1)                    # sail trails to the next spar round (clockwise seen from upwind)
    a = hub + d * P["sail_luff"][0]; b = hub + d * P["sail_luff"][1]
    c = hub + dn * P["R"] * P["sail_clew_r"] + np.array([P["sail_belly"], 0, 0])
    n = np.cross(b - a, c - a); n /= np.linalg.norm(n)
    face = cq.Face.makeFromWires(cq.Wire.makePolygon([V(*a), V(*b), V(*c), V(*a)]))
    add(f"Sail {i+1}", "sails", cq.Solid.extrudeLinear(face, V(*(n * 0.0015))), "#3b8bd4", 70.0)   # 105 g/m² tarp drawn 1.5 mm thick
# ---- drivetrain: bicycle bottom bracket at the pole top, its rear hub as the step-up shaft, hub motor below
bb = np.array([P["bb_x"], 0.0, P["hub_z"]])
add("Bottom bracket shell + crank axle", "drive", tube(bb + [-0.07, 0, 0], bb + [0.05, 0, 0], 0.040), "#22252a", STEEL)
add("Chainring 48T", "drive", tube(bb + [-0.004, 0, 0], bb + [0.0, 0, 0], P["chainring_d"], 0.05), "#e06c2f", STEEL)
jack = bb + np.array([0.0, 0.0, -P["chainstay"]])
add("Step-up hub (bike rear hub, rim removed)", "drive", tube(jack + [-0.02, 0, 0], jack + [0.115, 0, 0], 0.045), "#22252a", STEEL)
add("14T cog (chain 1 in)", "drive", tube(jack + [-0.004, 0, 0], jack + [0.0, 0, 0], P["jack_cog_small_d"], 0.03), "#e06c2f", STEEL)
add("28T cog (chain 2 out)", "drive", tube(jack + [-0.030, 0, 0], jack + [-0.026, 0, 0], P["jack_cog_big_d"], 0.03), "#e06c2f", STEEL)
mot = jack + np.array([0.0, 0.0, -P["motor_drop"]])
add("Hub motor (generator)", "drive", tube(mot + [-0.005, 0, 0], mot + [0.065, 0, 0], P["motor_hub_d"]), "#1d9e75", 3200.0)
add("Hub motor axle", "drive", tube(mot + [-0.03, 0, 0], mot + [P["motor_width"] - 0.03 + 0.03, 0, 0], 0.014), "#22252a", STEEL)
add("Hub motor rim 700C", "drive", tube(mot + [0.020, 0, 0], mot + [0.045, 0, 0], P["motor_rim_d"], P["motor_rim_d"] - 0.03), "#9aa0a6", 2700.0)
add("14T freewheel on motor", "drive", tube(mot + [-0.030, 0, 0], mot + [-0.026, 0, 0], P["motor_cog_d"], 0.03), "#e06c2f", STEEL)
for side, x in (("upwind", -0.035), ("downwind", P["motor_width"] - 0.03 + 0.005)):
    add(f"Bracket plate, {side} (2 × 15 mm plywood)", "drive",
        # plates hang from the bike's rear dropouts (step-up axle) and carry the motor axle; they stop below the crank's sweep
        cq.Workplane("XY").box(P["plate_t"], P["plate_w"], P["motor_drop"] + 0.16).val().translate(V(bb[0] + (x - P["plate_t"] / 2 if x < 0 else x + P["plate_t"] / 2), 0.0, (jack[2] + mot[2]) / 2)), "#c9a26b", PLY)
for z in P["standoff"]:
    add(f"Standoff to pole at {z:.2f} m", "drive", tube((P["bb_x"] + 0.14, 0.085, z), (-P["pole_od"] / 2, 0.0, z), P["spar_od"], P["spar_id"]), "#8a8f96", STEEL)

# ---- outputs: STEP assembly, STL, masses
asm = cq.Assembly(name="punta_mita_sail_windmill")
rows = []
for p in parts:
    asm.add(p["solid"], name=p["name"].replace(" ", "_").replace(",", "").replace("°", "deg").replace("(", "").replace(")", "").replace("×", "x"), color=cq.Color(*[int(p["colour"][i:i + 2], 16) / 255 for i in (1, 3, 5)]))
    vol = p["solid"].Volume(); bbx = p["solid"].BoundingBox()
    rows.append(dict(name=p["name"], group=p["group"], mass_kg=vol * p["rho"], bbox=[bbx.xmin, bbx.xmax, bbx.ymin, bbx.ymax, bbx.zmin, bbx.zmax]))
asm.save("out/cad/sail_windmill.step")
comp = cq.Compound.makeCompound([p["solid"] for p in parts])
cq.exporters.export(comp, "out/cad/sail_windmill.stl", tolerance=0.004, angularTolerance=0.3)

# ---- interference / clearance checks
def mind(a, b):
    return a.distToShape(b)[0] if hasattr(a, "distToShape") else None
from OCP.BRepExtrema import BRepExtrema_DistShapeShape
def dist(a, b):
    d = BRepExtrema_DistShapeShape(a.wrapped, b.wrapped); d.Perform(); return d.Value()
S = {p["name"]: p["solid"] for p in parts}
rotor_sweep = [p["solid"] for p in parts if p["group"] in ("rotor", "sails") and not p["name"].startswith(("Plywood", "Bowsprit"))]
checks = []
def sweep_clear(target_names, label, need):
    """clearance between the spinning rotor (all spar/sail/stay positions as modelled, 8-fold symmetric) and fixed parts"""
    d = min(dist(r, S[t]) for r in rotor_sweep for t in target_names)
    checks.append(dict(check=label, clearance_m=d, need_m=need, ok=bool(d >= need)))
sweep_clear(["Pole tube 2"], "Rotor to pole", 0.25)
sweep_clear(["Hub motor rim 700C"], "Rotor to hub-motor rim", 0.10)
sweep_clear(["Chainring 48T"], "Rotor to chainring", 0.03)
sweep_clear([p["name"] for p in parts if p["group"] == "guys"], "Rotor to guy cables", 0.25)
sweep_clear(["Back-prop tube 1", "Back-prop tube 2"], "Rotor to back-prop", 0.25)
d = dist(S["Hub motor rim 700C"], S["Pole tube 2"]); checks.append(dict(check="Hub-motor rim to pole", clearance_m=d, need_m=0.03, ok=bool(d >= 0.03)))
d = dist(S["Hub motor rim 700C"], S["Step-up hub (bike rear hub, rim removed)"]); checks.append(dict(check="Hub-motor rim to step-up hub", clearance_m=d, need_m=0.02, ok=bool(d >= 0.02)))
crank_gap = (bb[2] - 0.175) - (jack[2] + 0.08); checks.append(dict(check="Crank arm sweep to bracket plates", clearance_m=crank_gap, need_m=0.03, ok=bool(crank_gap >= 0.03)))
d = min(dist(S[f"Bracket plate, {s} (2 × 15 mm plywood)"], S["Hub motor rim 700C"]) for s in ("upwind", "downwind")); checks.append(dict(check="Bracket plates to hub-motor rim", clearance_m=d, need_m=0.01, ok=bool(d >= 0.01)))
tip_low = min(t[2] for t in tips); checks.append(dict(check="Lowest blade tip above the sand", clearance_m=tip_low, need_m=3.0, ok=bool(tip_low >= 3.0)))
spacing = 2 * math.pi * P["spar_in"] / P["n_sails"] - P["spar_od"]; checks.append(dict(check="Gap between spars at the hub disc", clearance_m=spacing, need_m=0.04, ok=bool(spacing >= 0.04)))
c1 = P["chainstay"]; c2 = P["motor_drop"]
def chain_links(c, d1, d2): return math.ceil((2 * c + math.pi * (d1 + d2) / 2 + (d1 - d2) ** 2 / (4 * c)) / 0.0127)
chains = dict(chain1_links=chain_links(c1, P["chainring_d"], P["jack_cog_small_d"]), chain2_links=chain_links(c2, P["jack_cog_big_d"], P["motor_cog_d"]), standard_chain_links=116)
groups = {}
for r in rows: groups[r["group"]] = groups.get(r["group"], 0.0) + r["mass_kg"]
rotor_mass = groups["rotor"] + groups["sails"]
json.dump(dict(params={k: v for k, v in P.items()}, parts=rows, group_mass_kg=groups, rotor_mass_kg=rotor_mass, checks=checks, chains=chains, anchors=anchors,
               tips=[t.tolist() for t in tips], hub=hub.tolist(), bow=bow.tolist()), open("out/cad/sail_windmill.json", "w"), indent=1, default=float)
print(f"{len(parts)} solids; masses kg:", {k: round(v, 1) for k, v in groups.items()}, "| rotor", round(rotor_mass, 1))
for c in checks: print(f"  {'OK  ' if c['ok'] else 'FAIL'} {c['check']:36s} {c['clearance_m']*1000:7.0f} mm (need {c['need_m']*1000:.0f})")
print("  chains:", chains)

# ---- renders
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
def render(fname, elev, azim, lim, groups_shown=None, title="", zoom=None):
    fig = plt.figure(figsize=(6, 6.4), dpi=170); ax = fig.add_subplot(111, projection="3d")
    for p in parts:
        if groups_shown and p["group"] not in groups_shown: continue
        vs, tris = p["solid"].tessellate(0.006, 0.4)
        v = np.array([[q.x, q.y, q.z] for q in vs])
        ax.add_collection3d(Poly3DCollection(v[np.array(tris)], facecolor=p["colour"], edgecolor="none", alpha=0.9 if p["group"] != "sails" else 0.8))
    (x0, x1), (y0, y1), (z0, z1) = lim
    ax.set_xlim(x0, x1); ax.set_ylim(y0, y1); ax.set_zlim(z0, z1); ax.set_box_aspect((x1 - x0, y1 - y0, z1 - z0)); ax.view_init(elev=elev, azim=azim); ax.set_axis_off()
    if title: fig.suptitle(title, fontsize=12, y=0.96)
    fig.subplots_adjust(0, 0, 1, 0.94); fig.savefig(fname); plt.close(fig)
render("out/cad/view_iso.png", 12, -128, ((-3.1, 3.1), (-3.1, 3.1), (0, 8.6)), title="Punta Mita sail windmill — CAD model (to scale)")
render("out/cad/view_front.png", 4, 180, ((-3.1, 3.1), (-3.1, 3.1), (0, 8.6)), title="Front view (looking downwind)")
render("out/cad/view_side.png", 2, -90, ((-2.2, 1.2), (-1.7, 1.7), (2.8, 8.6)), title="Side view: rotor coned 8° upwind of the pole")
render("out/cad/view_drive.png", 8, -120, ((-0.95, 0.35), (-0.65, 0.65), (4.85, 6.15)), groups_shown=("drive", "pole"), title="Drivetrain: crank → step-up hub → hub motor")
