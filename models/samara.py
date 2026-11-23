"""MAPLE SEED ROTOR: one fabric blade plus counterweight on a teeter hinge, compared with the 2- and 3-blade versions on the same 14 m pad machine.
BEM with Prandtl tip loss and Buhl correction, tapered blade twisted for its design speed. Costs are relative to the structurally checked 14 m Dandelion:
spar bending load per blade rises as 3/B, so spar cost per blade rises as (3/B)^(2/3); fewer blades need a teeter hinge, counterweight and a 25% stronger tower for once-per-turn loads. Tip speed limit 60 m/s at 9 m/s wind."""
import json, math, itertools
import numpy as np
src = open("pinwheel.py").read(); exec(src[:src.index("LAMS =")])
b14 = json.load(open("out/dandelion_big_14_10.json")); P14 = b14["pick"]; LIFE = b14["usd"] * b14["W"] * 8.766 * 20 / 1000; R0 = 7.
def bem2(B, c75, ld, lam):
    c = c75 * .75 / RS * .5 + c75 * .5; s = B * c / (2 * math.pi * RS * R0); t = np.arctan(2 / (3 * ld * RS)) - math.radians(4); lr = lam * RS; a, ap = np.full(16, .25), np.full(16, .03)
    for _ in range(100):
        phi = np.arctan2(1 - a, lr * (1 + ap)); sp, cp = np.maximum(np.sin(phi), .02), np.cos(phi); cl, cd = polar(phi - t); cn, ct = cl * cp + cd * sp, cl * sp - cd * cp; F = np.maximum(2 / math.pi * np.arccos(np.clip(np.exp(-B / 2 * (1 - RS) / (RS * sp)), 0, 1)), .03); k = s * cn / (4 * F * sp * sp); an = k / (1 + k); CTl = s * (1 - a)**2 * cn / (sp * sp); hi = CTl > .96 * F
        an = np.where(hi, (18 * F - 20 - 3 * np.sqrt(np.maximum(CTl * (50 - 36 * F) + 12 * F * (3 * F - 4), 0))) / (36 * F - 50), an); apn = 1 / np.maximum(4 * F * sp * cp / np.maximum(s * ct, 1e-4) - 1, 1e-3) * (ct > 0); a = .7 * a + .3 * np.clip(an, 0, .95); ap = .7 * ap + .3 * np.clip(apn, 0, 1)
    phi = np.arctan2(1 - a, lr * (1 + ap)); W2 = (1 - a)**2 + (lr * (1 + ap))**2; cl, cd = polar(phi - t); return float(np.sum(2 * s * W2 * (cl * np.sin(phi) - cd * np.cos(phi)) * lam * RS * RS * .92 / 16))
def best(B):
    out = None
    for c75, ld in itertools.product((.3, .45, .6, .8, 1.0, 1.3, 1.7), (3, 4, 5, 6, 7, 8, 10)):
        cp, lam = max((bem2(B, c75, ld, l), l) for l in np.arange(max(ld - 2, 1), min(ld + 2.5, 12), .5))
        if lam * 9 > 60 or cp <= 0: continue
        area = B * c75 * R0; spar = P14["blade"] * .85 * (B / 3) * (3 / B)**(2 / 3); fab = area * 8; extra = 0 if B == 3 else (180 + .25 * P14["tower"]); out = max(out, dict(B=B, c=c75, ld=ld, lam=float(lam), cp=cp, spar=spar, fab=fab, extra=extra, area=area), key=lambda x: x["cp"] - .00002 * (x["spar"] + x["fab"] + x["extra"])) if out else dict(B=B, c=c75, ld=ld, lam=float(lam), cp=cp, spar=spar, fab=fab, extra=extra, area=area)
    return out
r3 = best(3); base_rotor = r3["spar"] + r3["fab"]; rows = []
for B in (1, 2, 3):
    r = best(B); W = b14["W"] * r["cp"] / r3["cp"]; life = LIFE + (r["spar"] + r["fab"] - base_rotor) * 1.3 + r["extra"]; r.update(W=W, life=life, capex=b14["capex"] + r["spar"] + r["fab"] - base_rotor + r["extra"], usd=life / (W * 8.766 * 20 / 1000)); rows.append(r)
    print(f"{B} blade(s): chord {r['c']} m, tip speed ratio {r['lam']}, Cp {r['cp']:.3f}, {W:.0f} W, ${r['capex']:,.0f}, ${r['usd']:.1f}/MWh")
json.dump(rows, open("out/samara.json", "w"), indent=1, default=float)
