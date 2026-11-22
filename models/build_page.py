"""Collect results, render CFD field images, write web/index.html and OBJ exports."""
import base64, glob, io, json, math, os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

import models


def best_cfd():
    best = {}
    for f in glob.glob("out/lbm/*.json"):
        r = json.load(open(f))
        if r.get("diverged"):
            continue
        if r["case"] not in best or r["P"] > best[r["case"]]["P"]:
            best[r["case"]] = r
    return best


SEQ = LinearSegmentedColormap.from_list("seq", ["#0d366b", "#256abf", "#6da7ec", "#cde2fb", "#fcfcfb"][::-1])


def cfd_image(case, k):
    p = f"out/lbm/field_{case}_{k}.npz"
    if not os.path.exists(p):
        return None
    d = np.load(p)
    ux, uy, solid, act = d["ux"], d["uy"], d["solid"], d["act"]
    import lbm_cfd as L
    sl = (slice(L.XM - 70, L.XM + int(3.6 * L.D)), slice(L.YC - int(1.6 * L.D), L.YC + int(1.6 * L.D)))
    sp = np.hypot(ux, uy)[sl] / 0.08
    fig, ax = plt.subplots(figsize=(6.4, 3.0), dpi=130)
    im = ax.imshow(sp.T, origin="lower", cmap="RdBu_r", vmin=0, vmax=2.0, extent=[sl[0].start, sl[0].stop, sl[1].start, sl[1].stop], aspect="equal")
    Y, X = np.mgrid[sl[1], sl[0]]
    ax.streamplot(X, Y, ux[sl].T, uy[sl].T, density=1.3, color="#10202b", linewidth=0.45, arrowsize=0.5)
    s = np.ma.masked_where(~solid[sl], solid[sl])
    ax.imshow(s.T, origin="lower", cmap=LinearSegmentedColormap.from_list("k", ["#10202b", "#10202b"]), extent=[sl[0].start, sl[0].stop, sl[1].start, sl[1].stop])
    a = np.ma.masked_where(~act[sl], act[sl])
    ax.imshow(a.T, origin="lower", cmap=LinearSegmentedColormap.from_list("o", ["#eb6834", "#eb6834"]), extent=[sl[0].start, sl[0].stop, sl[1].start, sl[1].stop])
    ax.set_xticks([]); ax.set_yticks([])
    cb = fig.colorbar(im, ax=ax, fraction=0.03, pad=0.01); cb.set_label("|u| / V", fontsize=8); cb.ax.tick_params(labelsize=7)
    fig.tight_layout(pad=0.2)
    buf = io.BytesIO(); fig.savefig(buf, format="png"); plt.close(fig)
    with open(f"out/cfd_{case}.png", "wb") as fh:
        fh.write(buf.getvalue())
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


def export_obj():
    """OBJ exports: windsock assembly (deformed FEA membrane + frame tubes) and the kite."""
    os.makedirs("export", exist_ok=True)
    m = np.load("out/fea_membrane_mesh.npz"); fr = json.load(open("out/fea_frame.json"))
    H = 72.0
    lines, off = ["# Windsock concentrator, metres, z up, x downwind", "o membrane"], 1
    for p in m["x"]:
        lines.append(f"v {p[0]:.3f} {p[1]:.3f} {p[2] + H:.3f}")
    for t in m["T"]:
        lines.append(f"f {t[0] + off} {t[1] + off} {t[2] + off}")
    off += len(m["x"])
    nodes = np.array(fr["viz"]["nodes"])
    for a, b, g, u in fr["viz"]["elems"]:
        r = max(fr["sections"][g]["D"] / 2, 0.05)
        pa, pb = nodes[a], nodes[b]
        ax = pb - pa; L = np.linalg.norm(ax); ax /= L
        ref = np.array([0, 0, 1.0]) if abs(ax[2]) < 0.9 else np.array([1.0, 0, 0])
        e1 = np.cross(ax, ref); e1 /= np.linalg.norm(e1); e2 = np.cross(ax, e1)
        n = 10
        lines.append(f"o {g}_{a}_{b}")
        for end in (pa, pb):
            for k in range(n):
                th = 2 * math.pi * k / n
                v = end + r * (math.cos(th) * e1 + math.sin(th) * e2)
                lines.append(f"v {v[0]:.3f} {v[1]:.3f} {v[2]:.3f}")
        for k in range(n):
            a0, a1, b0, b1 = off + k, off + (k + 1) % n, off + n + k, off + n + (k + 1) % n
            lines.append(f"f {a0} {a1} {b1} {b0}")
        off += 2 * n
    # nozzle
    lines.append("o nozzle")
    xs = (63 - 6.3) / 63 * 126; n = 48
    for x, r in ((xs, 6.3), (126, 0.63)):
        for k in range(n):
            th = 2 * math.pi * k / n
            lines.append(f"v {x:.3f} {r * math.cos(th):.3f} {H + r * math.sin(th):.3f}")
    for k in range(n):
        lines.append(f"f {off + k} {off + (k + 1) % n} {off + n + (k + 1) % n} {off + n + k}")
    open("export/windsock_assembly.obj", "w").write("\n".join(lines))
    # kite
    A = json.load(open("out/models.json"))["kite"]["area_soft_m2"]
    span = math.sqrt(A * 1.6); chord = A / span; R = span / 2.2
    kl = ["# Crosswind soft kite, metres", "o kite"]; nS, nC = 40, 8
    for i in range(nS + 1):
        for j in range(nC + 1):
            s = (i / nS - 0.5) * 2.2
            kl.append(f"v {(j / nC - 0.3) * chord:.3f} {R * math.sin(s):.3f} {R * math.cos(s) - R + math.sin(j / nC * math.pi) * chord * 0.08:.3f}")
    for i in range(nS):
        for j in range(nC):
            a = i * (nC + 1) + j + 1; b = a + nC + 1
            kl.append(f"f {a} {b} {b + 1} {a + 1}")
    open("export/spinnaker_kite.obj", "w").write("\n".join(kl))
    # rotary kite ring: TRPT (deformed FEA geometry, as polylines) + wing panels
    rot = json.load(open("out/rotary.json")); D = rot["design"]; Gm = rot["fea_geom"]
    rl = ["# Rotary kite ring (TRPT from nonlinear FEA at design torque), metres, z up", "o trpt"]
    for p in Gm["x"]:
        rl.append(f"v {p[0]:.3f} {p[1]:.3f} {p[2]:.3f}")
    for (a_, b_), k in zip(Gm["bars"], Gm["kinds"]):
        rl.append(f"l {a_ + 1} {b_ + 1}")
    nv = len(Gm["x"]); n = D["n_lines"]; ns = D["n_seg"]
    xs = np.array(Gm["x"]); top = xs[ns * n:(ns + 1) * n].mean(0)
    be = math.radians(D["beta_deg"]); ax = np.array([math.cos(be), 0, math.sin(be)]); u = np.array([0, 1.0, 0]); w = np.cross(ax, u)
    rl.append("o wings")
    for s in range(int(D["opt"]["stack"])):
        hub = top + ax * (18 + s * 0.45 * D["R"])
        for i in range(D["N"]):
            th = (i + 0.5 * s) / D["N"] * 2 * math.pi; dr = math.cos(th) * u + math.sin(th) * w; tg = np.cross(ax, dr)
            c0 = hub + dr * D["R"]
            for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
                v = c0 + dr * sx * D["b"] / 2 + tg * sy * D["c"] / 2
                rl.append(f"v {v[0]:.3f} {v[1]:.3f} {v[2]:.3f}")
            rl.append(f"f {nv + 1} {nv + 2} {nv + 3} {nv + 4}"); nv += 4
    open("export/rotary_kite_ring.obj", "w").write("\n".join(rl))


def lbm3d_summary():
    """Stacked-rotor 3D LBM runs: per-rotor power relative to the isolated rotor, plus a centre-plane image."""
    if not os.path.exists("out/lbm3d_1_1.5.json"):
        return None
    single = json.load(open("out/lbm3d_1_1.5.json"))
    runs = [json.load(open(f)) for f in sorted(glob.glob("out/lbm3d_*.json")) if not f.endswith("lbm3d_1_1.5.json")]
    img = None
    p = "out/lbm3d_field_3_1.5.npz"
    if os.path.exists(p):
        d = np.load(p); sp = np.hypot(d["ux"], d["uz"]) / 0.06
        fig, ax = plt.subplots(figsize=(7.2, 3.6), dpi=130)
        im = ax.imshow(sp.T, origin="lower", cmap="RdBu_r", vmin=0.4, vmax=1.6, aspect="equal")
        a = np.ma.masked_where(~d["act"], d["act"])
        ax.imshow(a.T, origin="lower", cmap=LinearSegmentedColormap.from_list("o", ["#10202b", "#10202b"]))
        ax.set_xticks([]); ax.set_yticks([])
        cb = fig.colorbar(im, ax=ax, fraction=0.025, pad=0.01); cb.set_label("|u| / V", fontsize=8); cb.ax.tick_params(labelsize=7)
        fig.tight_layout(pad=0.2); buf = io.BytesIO(); fig.savefig(buf, format="png"); plt.close(fig)
        open("out/lbm3d_stack.png", "wb").write(buf.getvalue())
        img = "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()
    note = open("out/lbm3d_note.txt").read().strip() if os.path.exists("out/lbm3d_note.txt") else ""
    return dict(single=single, runs=runs, img=img, note=note)


def r_stack(r):
    return int(r.get("stack", 1))


def main():
    models.main()
    M = json.load(open("out/models.json"))
    mem = json.load(open("out/fea_membrane.json"))
    frame = json.load(open("out/fea_frame.json"))
    cfd = best_cfd()
    imgs = {k: cfd_image(k, v["k"]) for k, v in cfd.items()}
    rot = json.load(open("out/rotary.json"))
    import rotary as RT
    # add rotary + carousel to the BOM / comparison set
    de = rot["design_eval"]; dd = rot["design"]
    M["bom"]["Rotary kite ring, TRPT shaft (optimised, FEA-verified)"] = dict(items=de["items"], capex=de["capex"], opex=de["opex"], aep_kwh=de["aep_kwh"],
        lcoe_usd_mwh=de["lcoe"], capex_per_kW=de["capex"] / (dd["P_rated"] / 1e3), P_rated_kW=dd["P_rated"] / 1e3)
    car = rot["carousel"]
    M["bom"]["Ground carousel (KiteGen-type)"] = dict(items=car["items"], capex=car["capex"], opex=car["opex"], aep_kwh=car["aep_kwh"],
        lcoe_usd_mwh=car["lcoe"], capex_per_kW=car["capex"] / (car["P"] / 1e3), P_rated_kW=car["P"] / 1e3)
    base_row = rot["levers"][0]
    comp = []
    for name, b in M["bom"].items():
        Pk = b.get("P_rated_kW", 5000)
        cf = b["aep_kwh"] / (Pk * 8766)
        comp.append(dict(name=name, P_MW=Pk / 1e3, capex=b["capex"], capex_per_MW=b["capex"] / (Pk / 1e3), cf=cf,
                         capex_per_avgMW=b["capex"] / (Pk / 1e3) / max(cf, 1e-9), lcoe=b["lcoe_usd_mwh"]))
    fg = [l for l in rot["levers"] if l.get("flygen") and l["kept"]]
    if fg:
        f = fg[-1]
        comp.insert(len(comp) - 1, dict(name=f"Rotary kite ring, fly-gen (no shaft, {f['h']:.0f} m)", P_MW=f["best_P"] / 1e6, capex=f["capex_per_MW"] * f["best_P"] / 1e6,
                                        capex_per_MW=f["capex_per_MW"], cf=f["cf"], capex_per_avgMW=f["capex_per_avgMW"], lcoe=f["lcoe"]))
    comp.insert(len(comp) - 3, dict(name="Rotary kite ring, baseline Daisy-type", P_MW=base_row["best_P"] / 1e6, capex=base_row["capex_per_MW"] * base_row["best_P"] / 1e6,
                                    capex_per_MW=base_row["capex_per_MW"], cf=base_row["cf"], capex_per_avgMW=base_row["capex_per_avgMW"], lcoe=base_row["lcoe"]))
    LO = json.load(open("out/lcoe_opt.json"))
    on = [r for r in LO["results"] if r["site"] == "onshore"]
    ho = next(r for r in on if r["arch"] == "hawt"); bo = min((r for r in on if r["arch"] not in ("hawt", "hawt_ref")), key=lambda r: r["lcoe"])
    for nm, r in ((f"Conventional turbine, LCOE-optimised ({ho['D']:.0f} m rotor, {ho['H']:.0f} m hub)", ho),
                  (f"Rotary kite ring, LCOE-optimised fly-gen ({r_stack(bo)} stacked rotors at {bo['h']:.0f} m)", bo)):
        comp.append(dict(name=nm, P_MW=r["P_MW"], capex=r["capex"], capex_per_MW=r["capex_per_MW"], cf=r["cf"], capex_per_avgMW=r["capex_per_avgMW"], lcoe=r["lcoe"]))
    mm = np.load("out/fea_membrane_mesh.npz")
    fabric = [v for v in M["bom"]["Windsock d -> d/100 (your spec)"]["items"] if v[0].startswith("Membrane")][0][0]
    fabric_area = float(fabric.split(",")[-2].strip().split(" ")[0].replace(",", "")) if False else math.pi * (63 + 0.63) * math.hypot(126, 62.37) * 1.08
    rot.pop("fea_geom_full", None)
    T10 = json.load(open("out/target10.json")) if os.path.exists("out/target10.json") else None
    X3 = lbm3d_summary()
    PRO = json.load(open("out/proto_bom.json")) if os.path.exists("out/proto_bom.json") else None
    data = dict(proto=PRO, t10=T10, lbm3d=X3, models=M, mem=mem, frame=frame, cfd=cfd, cfdimg=imgs, fabric_area=fabric_area, rot=rot, comp=comp, lcoe=LO,
                mesh=dict(x=np.round(mm["x"], 2).tolist(), T=mm["T"].tolist(), s1=np.round(mm["s1"], 2).tolist()))
    tpl = open("web/template.html").read()
    html = tpl.replace("/*__DATA__*/null", json.dumps(data, separators=(",", ":"), default=float))
    open("web/index.html", "w").write(html)
    export_obj()
    print("page bytes", len(html), "cfd cases", list(cfd))


if __name__ == "__main__":
    main()
