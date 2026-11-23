"""Optimise the Punta Mita sail windmill for energy per dollar.
Free: rotor diameter, number of sails, sail width (solidity), chain ratio (one or two bicycle stages),
number of 2.9 ohm resistors in parallel, furling wind speed.
Limits: motor current <= 30 A, <= 270 W per resistor, chain safety factor >= 3, spar safety factor >= 1.5 (stayed).
Cost: itemised parts + sail replacement (tarp lasts about a year in tropical sun) over five years."""
import json, math, io, contextlib, itertools
import numpy as np
with contextlib.redirect_stdout(io.StringIO()):
    import concepts as CC

import sys
RHO, W10, KV, R_M, V_D = CC.RHO, CC.W10, CC.KV, CC.R_M, CC.V_D
SITE_MEAN = float(sys.argv[1]) if len(sys.argv) > 1 else None      # None = Punta Mita hourly record
YEARS = int(sys.argv[2]) if len(sys.argv) > 2 else 5
TAG = "" if SITE_MEAN is None and YEARS == 5 else f"_{SITE_MEAN or 'pm'}_{YEARS}"
if SITE_MEAN is not None:
    W10 = np.random.default_rng(1).weibull(2.0, 200000) * SITE_MEAN / math.gamma(1.5)
K_T = 9.549 / KV; FIELD = CC.FF["sail"]; FX = 18.5
LAMS = np.linspace(0.3, 3.6, 34)
OD, WALL = 29.5e-3, 1.2e-3; ID = OD - 2 * WALL
I_SP = math.pi * (OD**4 - ID**4) / 64; S_SP = I_SP / (OD / 2); A_SP = math.pi * (OD**2 - ID**2) / 4
FY, CHAIN_BREAK = 230e6, 8000.0
VBINS = np.arange(0.5, 18.01, 0.5); FRAC = np.array([float(((W10 >= v - 0.25) & (W10 < v + 0.25)).mean()) for v in VBINS])
RATIOS = {"48:14 (one chain)": (48 / 14, 0.95, 0.0), "52:13 (one chain)": (4.0, 0.95, 10.0), "48:14 then 28:14 (two chains)": (48 / 14 * 2, 0.90, 45.0),
          "48:14 then 42:14 (two chains)": (48 / 14 * 3, 0.90, 45.0)}


def curve(n, k):
    cps, cts = [], []
    for lam in LAMS:
        b = CC.bem(n, 1.0, 0.15, lambda r: 0.9 * (2 * math.pi * r / n) * k, 0.16, lams=[lam]); cps.append(max(b["cp"], 0.0)); cts.append(b["ct"])
    return np.array(cps), np.array(cts)


def operate(dia, cps, cts, v, ratio, eta, R_load):
    R = dia / 2; A = math.pi * R * R
    def qr(lam): return float(np.interp(lam, LAMS, cps)) * FIELD * 0.5 * RHO * v**3 * A / (lam * v / R)
    def qg(lam):
        E = ratio * lam * v / R * 60 / (2 * math.pi) / KV; I = max(E - V_D, 0.0) / (R_M + R_load)
        return K_T * I * ratio / eta, I
    lo, hi = 0.31, 3.59
    if qr(lo) < qg(lo)[0]:
        return dict(v=v, rpm=0.0, lam=0.0, P_el=0.0, I=0.0, V=0.0, Q=0.0, thrust=0.0)
    for _ in range(40):
        mid = 0.5 * (lo + hi)
        if qr(mid) > qg(mid)[0]: lo = mid
        else: hi = mid
    Q, I = qg(lo)
    return dict(v=float(v), rpm=lo * v / R * 60 / (2 * math.pi), lam=lo, P_el=I * I * R_load, I=I, V=I * R_load, Q=Q,
                thrust=float(np.interp(lo, LAMS, cts)) * 0.5 * RHO * v * v * A)


def checks(dia, n, o, n_res):
    R = dia / 2; F = o["thrust"] / n; th = math.atan(0.4)
    sig = math.hypot(F * 0.65 * 0.35 * R, o["Q"] / n * 0.5) / S_SP + (0.65 * F / math.tan(th)) / A_SP
    chain = o["Q"] / 0.097
    return dict(spar_SF=FY / max(sig, 1.0), chain_SF=CHAIN_BREAK / max(chain, 1.0), chain_N=chain, amps_ok=o["I"] <= 30.0, res_ok=o["P_el"] / n_res <= 270.0)


def cost(dia, n, k, n_res, extra):
    R = dia / 2; sail_area = n * 0.5 * (0.85 * R) * (0.9 * 2 * math.pi * R / n * k) * 1.15
    tarp_mx = 765 if sail_area <= 15 else (1229 if sail_area <= 26 else 2315)
    spar_len = 3.0 if R <= 2.9 else 6.0                         # one 3 m conduit per spar up to 2.9 m radius, else two sleeved
    conduit = (n + 1) * (1 if spar_len == 3.0 else 2) * 249
    pole = 2 * 545 if dia <= 5.2 else 3 * 545                   # 6 m pole, or 9 m for the biggest rotors
    local_mx = pole + 40 * 27 + 12 * 22 + conduit + tarp_mx + 2 * 219 + 599 + 199 + 1500 + 1850 + 495
    carry = 239.99 + 15 + 20.65 + (n_res + 1) * 10.55 + 117.30 + extra
    capex = carry + local_mx / FX
    tarp = tarp_mx / FX * (1.6 if SITE_MEAN and SITE_MEAN > 6 else 1.0)   # heavy-duty tarp on a windy site
    return capex, capex + (YEARS - 1) * tarp + 0.02 * capex * max(YEARS - 5, 0), sail_area   # yearly sail replacement; 2 %/yr parts after year 5


out = dict(runs=[]); best = None
for n, k in itertools.product((6, 8, 12), (0.30, 0.45, 0.60, 0.80)):
    cps, cts = curve(n, k)
    for dia, (rname, (ratio, eta, extra)), n_res, vf in itertools.product((3.0, 4.0, 5.0, 6.0), RATIOS.items(), (1, 2, 3, 4, 6, 8, 10), (7.0, 8.0, 10.0, 12.0, 14.0)):
        Rl = 2.9 / n_res; avg = 0.0; ok = True
        for v, fr in zip(VBINS, FRAC):
            if v < 2.5 or v > vf: continue
            o = operate(dia, cps, cts, v, ratio, eta, Rl)
            if o["P_el"] <= 0: continue
            c = checks(dia, n, o, n_res)
            if not (c["amps_ok"] and c["res_ok"] and c["chain_SF"] >= 3 and c["spar_SF"] >= 1.5): ok = False; break
            avg += o["P_el"] * fr
        if not ok: continue
        capex, cost5, area = cost(dia, n, k, n_res, extra)
        r = dict(n=n, k=k, dia=dia, ratio_name=rname, ratio=ratio, eta=eta, n_res=n_res, R_load=Rl, v_furl=vf, avg_W=avg, kWh_yr=avg * 8.766, capex=capex, cost5=cost5,
                 sail_area=area, kWh_per_usd=avg * 8.766 * YEARS / cost5, usd_per_MWh=cost5 / (avg * 8.766 * YEARS / 1000) if avg > 0 else 1e9, cp_max=float(cps.max()), lam_opt=float(LAMS[cps.argmax()]))
        out["runs"].append(r)
        if best is None or r["kWh_per_usd"] > best["kWh_per_usd"]: best = r; best_curves = (cps, cts)
runs = sorted(out["runs"], key=lambda r: -r["kWh_per_usd"])
print(f"{len(runs)} feasible designs")
seen = set()
for r in runs:
    key = (r["dia"], r["n"], r["k"], r["ratio_name"])
    if key in seen: continue
    seen.add(key)
    print(f"  {r['dia']:.0f} m  {r['n']:2d} sails  width {r['k']:.2f}  {r['ratio_name']:30s} {r['n_res']} res  furl {r['v_furl']:.0f}  Cp {r['cp_max']:.2f}@{r['lam_opt']:.1f}  avg {r['avg_W']:5.1f} W  capex ${r['capex']:.0f}  5-yr ${r['cost5']:.0f}  {r['kWh_per_usd']:.2f} kWh/$  ${r['usd_per_MWh']:.0f}/MWh")
    if len(seen) >= 14: break
base = [r for r in runs if r["dia"] == 4.0 and r["n"] == 8 and r["k"] == 0.45 and r["ratio_name"].startswith("48:14 (one") and r["n_res"] == 3]
base = max(base, key=lambda r: r["avg_W"]) if base else None
if base: print(f"previous design on the same cost basis: avg {base['avg_W']:.1f} W, 5-yr ${base['cost5']:.0f}, {base['kWh_per_usd']:.2f} kWh/$, ${base['usd_per_MWh']:.0f}/MWh")
cps, cts = best_curves
best["ops"] = []
for v in (3, 4, 5, 6, 7, 8, 10, 12):
    o = operate(best["dia"], cps, cts, v, best["ratio"], best["eta"], best["R_load"]); o.update(checks(best["dia"], best["n"], o, best["n_res"])); o["furled"] = v > best["v_furl"]; best["ops"].append(o)
    print(f"   {v:>2} m/s: {o['rpm']:4.0f} rpm  {o['V']:5.1f} V {o['I']:5.1f} A {o['P_el']:6.0f} W  thrust {o['thrust']:5.0f} N  spar SF {o['spar_SF']:.1f}  chain {o['chain_N']:.0f} N (SF {o['chain_SF']:.1f}) {'(furled above this)' if o['furled'] else ''}")
pick = max([r for r in runs if r["dia"] == 5.0 and r["n"] == 8 and r["k"] == 0.45], key=lambda r: r["kWh_per_usd"])
pc, pt = curve(pick["n"], pick["k"]); pick["ops"] = []
for v in (3, 4, 5, 6, 7, 8, 10, 12):
    o = operate(pick["dia"], pc, pt, v, pick["ratio"], pick["eta"], pick["R_load"]); o.update(checks(pick["dia"], pick["n"], o, pick["n_res"])); o["furled"] = v > pick["v_furl"]; pick["ops"].append(o)
print(f"pick: 5 m, {pick['ratio_name']}, {pick['n_res']} resistors, furl {pick['v_furl']}: {pick['avg_W']:.1f} W, capex ${pick['capex']:.0f}, ${pick['usd_per_MWh']:.0f}/MWh")
for o in pick["ops"]: print(f"   {o['v']:>4} m/s: {o['rpm']:4.0f} rpm {o['V']:5.1f} V {o['I']:5.1f} A {o['P_el']:6.0f} W thrust {o['thrust']:5.0f} N spar SF {o['spar_SF']:.1f} chain SF {o['chain_SF']:.1f} amps_ok {o['amps_ok']} res_ok {o['res_ok']}")
ladder = []
def pickrun(dia, rn, nres=None):
    c = [r for r in runs if r["dia"] == dia and r["n"] == 8 and r["k"] == 0.45 and r["ratio_name"].startswith(rn) and (nres is None or r["n_res"] == nres)]
    return max(c, key=lambda r: r["kWh_per_usd"]) if c else None
for label, r in (("4 m, one chain, three resistors (previous design)", base), ("4 m, two chains", pickrun(4.0, "48:14 then 28:14")), ("5 m, one chain", pickrun(5.0, "48:14 (one")),
                 ("5 m, two chains (the build)", pick), ("6 m, two chains, 9 m pole (stretch)", pickrun(6.0, "48:14 then 28:14"))):
    if r: ladder.append(dict(label=label, avg_W=r["avg_W"], kWh_yr=r["kWh_yr"], capex=r["capex"], cost5=r["cost5"], usd_per_MWh=r["usd_per_MWh"], kWh_per_usd=r["kWh_per_usd"], n_res=r["n_res"], v_furl=r["v_furl"]))
for l in ladder: print(f"ladder {l['label']:52s} {l['avg_W']:5.1f} W  capex ${l['capex']:.0f}  ${l['usd_per_MWh']:.0f}/MWh")
json.dump(dict(best=best, pick=pick, previous=base, ladder=ladder, top=[r for r in runs[:200]]), open(f"out/sail_opt{TAG}.json", "w"), indent=1, default=float)
