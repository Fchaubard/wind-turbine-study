"""Re-costs the simulated kite seesaw if it only flies in winds where the flights stayed up (at least 95% survival), using saved flights. Launch and landing are not simulated. Prices are budget estimates."""
import json, io, contextlib, itertools
import numpy as np
with contextlib.redirect_stdout(io.StringIO()):
    import zoo as Z
F = json.load(open("out/seesaw.json"))["flight"]; ALL = [3.5, 4., 5., 6.]; R = []
for key, o in F.items():
    f, m = key.split("|"); f, m = float(f), int(m)
    for lo in (3.5, 4., 5.):
        VS = [x for x in ALL if x >= lo]; g = lambda k: np.array([o[str(x)][k] for x in VS])
        if g("surv").min() < .95: continue
        v = Z.WS[(Z.WS >= lo) & (Z.WS <= 6.)]; hrs = len(v) / len(Z.WS) * 8766 * .85
        for pairs, pr, li, ll, cf in itertools.product((1, 2, 4), (50, 150), (1500, 5000), (1500, 5000), (.15, .25, .35, .5, .75, 1.)):
            Pm = np.maximum(g("net"), 0) * 2 * pairs * .9 * .78; Pm = np.minimum(Pm, cf * Pm.max()); P = float(np.minimum(np.interp(v, VS, np.maximum(g("net"), 0) * 2 * pairs * .9 * .78), Pm.max()).mean()); av = float(np.interp(v, VS, g("av")).mean()); lam = float(np.interp(v, VS, g("lam")).mean()) * 2 * pairs; fly = hrs * av; mwh = P * hrs / 1e6; Tp = min(float(g("Tpk").max()), 170 * m * 12 * 1.3); Q = Tp * .15
            it = dict(kites=2 * pairs * m * pr, lines=2 * pairs * 120 * m, pods=2 * pairs * 450, drums_clutches=pairs * 400, gear=pairs * (250 + .08 * Q), fairleads=2 * pairs * 150, frame=250 + 150 * pairs, generator_inverter=350 + 500 * max(float(Pm.max()) / 1000, .5), sensors_wiring=240); cap = sum(it.values()); yr = it["kites"] * fly / li + .05 * lam * fly * pr + it["lines"] * fly / ll + .03 * (cap - it["kites"] - it["lines"]); L = cap + yr * 19 + .3 * (it["generator_inverter"] + it["pods"]); R.append(dict(gen_frac=cf, gen_kW=float(Pm.max()) / 1000, f=f, m=m, lo=lo, pairs=pairs, price=pr, life=li, line_life=ll, W=P * hrs / 8766, capex=cap, usd=L / (mwh * 20), crashes_yr=lam * fly, fly_h=fly, surv=float(g("surv").min()), items=it, yearly=yr))
json.dump(R, open("out/seesaw_window.json", "w"), indent=1, default=float); print(len(R), "safe-window designs")
for pr, li, ll in ((50, 5000, 5000), (50, 5000, 1500), (150, 5000, 5000), (150, 1500, 1500)):
    b = min((r for r in R if r["price"] == pr and r["life"] == li and r["line_life"] == ll), key=lambda r: r["usd"]); print(f"${pr} kite, kite {li} h, line {ll} h: {b['pairs']} pair(s) × {b['m']} kites, flies from {b['lo']} m/s, generator {b['gen_kW']:.1f} kW, {b['fly_h']:.0f} h/yr | {b['W']:.0f} W, build ${b['capex']:,.0f}, {b['crashes_yr']:.0f} crashes/yr | ${b['usd']:.0f}/MWh | upkeep ${b['yearly']:,.0f}/yr | " + ", ".join(f"{k} {v:.0f}" for k, v in b["items"].items()))
