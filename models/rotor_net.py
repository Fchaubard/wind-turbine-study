"""Rotor net: split the same swept area into N identical rotors on one cable net and yawing tower, from 30 cm to one 10 m rotor. Hourly Punta Mita wind.
Small rotors: less material, but lower Cp, generator efficiency and more friction, wiring and salt replacement. Unit prices are three scenarios anchored on a $150 one-off 100 W, ~1 m turbine."""
import json, math, io, contextlib
import numpy as np
with contextlib.redirect_stdout(io.StringIO()):
    import zoo as Z
RHO, HUB, FIELD = 1.18, 12.0, .75; WS = Z.WS; DS = np.array([.3, .4, .6, .8, 1, 1.5, 2, 3, 4, 5, 7, 10.]); AREAS = (40., 78.5, 120.)
lg = lambda d, x, y: float(np.interp(math.log(d), np.log(x), y))
cp = lambda d: lg(d, (.3, .6, 1.2, 2.5, 5, 10), (.18, .22, .27, .31, .34, .36)); eg = lambda d: lg(d, (.3, 1, 5), (.55, .70, .80)); tsr = lambda d: lg(d, (.3, 1, 5), (3.5, 4.5, 6))
UNIT = {"Retail, buy today": lambda d: max(25., 150 * d**1.5), "Factory, 1,000+": lambda d: 1.2 + 18 * d * d, "Mass-made, millions": lambda d: .5 + 8 * d * d}
def W(d, A, s=1., cf=1., qf=1.):
    n = max(1, round(A / (math.pi * d * d / 4))); a = n * math.pi * d * d / 4; v = WS * (HUB / 10)**.14 * math.cos(math.radians(10)) * s; q = (.045 * d**2.5 + .0008) * qf; L = tsr(d)
    each = np.maximum(cp(d) * cf * FIELD * .5 * RHO * v**3 * a / n - q * L * v / (d / 2), 0) * eg(d) * .95 * (v <= 12); return n, a, float(np.minimum(each * n, 1200 * math.ceil(a / 80)).mean()) * .97
def econ(d, A, name, s=1., cf=1., qf=1., cost=1., y=20):
    n, a, P = W(d, A, s, cf, qf); u = UNIT[name](d) * cost; life = 7 if d < 2 else 12; repl = math.ceil(y / life) - 1; struct = 2000 * (a / 78.5)**.85 * cost; net = (0 if n == 1 else a / .75 * 4 + n * (.6 + .25 * d)) * cost; el = 500 * math.ceil(a / 80) * cost
    fixed = struct + net + el + 130 * (y - 1) + .3 * el; mwh = P * 8.766 * y / 1000; total = fixed + n * u * (1 + repl)
    return dict(d=d, A=a, n=n, W=P, capex=struct + net + el + n * u, usd=total / mwh if P > 1 else 1e7, breakeven80=(80 * mwh - fixed) / (n * (1 + repl)), breakeven10=(10 * mwh - fixed) / (n * (1 + repl)))
R = {k: [min((econ(float(d), A, k) for A in AREAS), key=lambda r: r["usd"]) for d in DS] for k in UNIT}
for k, x in R.items():
    print(k); [print(f" {r['d']:4.1f} m x{r['n']:5d} {r['A']:4.0f} m2 {r['W']:4.0f} W capex ${r['capex']:6.0f} ${r['usd']:5.0f}/MWh | unit must cost <${r['breakeven80']:.2f} for $80, <${r['breakeven10']:.2f} for $10") for r in x]
rng = np.random.default_rng(4); print("Monte Carlo, factory prices: share of 1000 cases where each size wins"); wins = np.zeros(len(DS)); med = np.zeros((1000, len(DS)))
for i in range(1000):
    s, cf, qf, c = rng.uniform(.85, 1.5), rng.uniform(.8, 1.15), rng.uniform(.5, 2), rng.uniform(.85, 1.5); med[i] = [econ(float(d), 78.5, "Factory, 1,000+", s, cf, qf, c)["usd"] for d in DS]; wins[med[i].argmin()] += 1
print({float(d): int(w / 10) for d, w in zip(DS, wins)}, "median", {float(d): int(m) for d, m in zip(DS, np.median(med, 0))})
json.dump(dict(R=R, wins=wins.tolist(), ds=DS.tolist()), open("out/rotor_net.json", "w"), indent=1)
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
C = {"Retail, buy today": "#c2552d", "Factory, 1,000+": "#2a6fb0", "Mass-made, millions": "#1d9e75"}; f, a = plt.subplots(figsize=(6, 7), dpi=170, facecolor="#faf9f5"); a.set_facecolor("#faf9f5")
for k, x in R.items(): a.plot(DS, [r["usd"] for r in x], color=C[k], lw=2, marker="o", ms=4, label=k)
a.axhline(80, color="#333", ls="--", lw=1); a.text(.31, 84, "Dandelion, $80".replace("$", r"\$"), fontsize=9); a.axhline(10, color="#888", ls=":", lw=1); a.text(.31, 10.6, "Target, $10".replace("$", r"\$"), fontsize=9)
a.set(xscale="log", yscale="log", ylim=(8, 2000), xlabel="Rotor diameter (m), same tower and hourly wind", ylabel=r"\$ per MWh, 20 years"); a.set_xticks([.3, .6, 1, 2, 5, 10]); a.set_xticklabels(["0.3", "0.6", "1", "2", "5", "10"]); a.grid(alpha=.2); a.spines[["top", "right"]].set_visible(False); a.legend(frameon=False, fontsize=9); a.set_title("Many small rotors vs one big rotor", loc="left", weight="bold", fontsize=15); f.tight_layout(); f.savefig("out/rotor_net.png")
