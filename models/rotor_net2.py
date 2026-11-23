"""Fair test at one swept area (78.5 m2). 'Everything goes right' gives small rotors the 10 m rotor's Cp and generator efficiency, zero friction, 20-year life and the Dandelion's light $800 structure."""
import math, json, io, contextlib
import numpy as np
with contextlib.redirect_stdout(io.StringIO()):
    import rotor_net as N
A = 78.5; v = N.WS * (12 / 10)**.14 * math.cos(math.radians(10))
def best(d, name):
    n = max(1, round(A / (math.pi * d * d / 4))); a = n * math.pi * d * d / 4; P = float(np.minimum(.36 * .75 * .5 * 1.18 * v**3 * a * .8 * .95 * (v <= 12), 1200).mean()) * .97; u = N.UNIT[name](d); fixed = 800 * (a / 78.5)**.85 + (0 if n == 1 else a / .75 * 4 + n * (.6 + .25 * d)) + 500 + 130 * 19 + 150; mwh = P * 8.766 * 20 / 1000
    return dict(d=d, n=n, W=P, usd=(fixed + n * u) / mwh, be10=(10 * mwh - fixed) / n, be80=(80 * mwh - fixed) / n, fixed=fixed, mwh=mwh)
S = {"Realistic, factory price": [N.econ(float(d), A, "Factory, 1,000+") for d in N.DS], "Realistic, mass-made": [N.econ(float(d), A, "Mass-made, millions") for d in N.DS], "Everything goes right, mass-made": [best(float(d), "Mass-made, millions") for d in N.DS]}
for k, x in S.items():
    print(k); [print(f" {r['d']:4.1f} m x{r['n']:5d} {r['W']:4.0f} W ${r['usd']:5.0f}/MWh") for r in x]
print("best-case unit price needed for $80:", {r["d"]: round(r["be80"], 2) for r in S["Everything goes right, mass-made"]}); print("for $10:", {r["d"]: round(r["be10"], 2) for r in S["Everything goes right, mass-made"]}); r = S["Everything goes right, mass-made"][-1]; print("fixed cost alone gives $/MWh:", round(r["fixed"] / r["mwh"]))
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
C = dict(zip(S, ("#2a6fb0", "#c2552d", "#1d9e75"))); f, a = plt.subplots(figsize=(6, 7.4), dpi=170, facecolor="#faf9f5"); a.set_facecolor("#faf9f5")
for k, x in S.items(): a.plot(N.DS, [r["usd"] for r in x], color=C[k], lw=2.2, marker="o", ms=4, label=k)
a.axhline(80, color="#333", ls="--", lw=1); a.text(.31, 70, r"Dandelion, \$80", fontsize=9); a.axhline(10, color="#888", ls=":", lw=1); a.text(.31, 10.8, r"Target, \$10", fontsize=9)
a.set(xscale="log", yscale="log", ylim=(8, 2500), xlabel="Rotor size (m). Same 78 m² total, 12 m tower", ylabel=r"\$ per MWh over 20 years"); a.set_xticks([.3, .6, 1, 2, 5, 10]); a.set_xticklabels(["0.3", "0.6", "1", "2", "5", "10"]); a.grid(alpha=.2); a.spines[["top", "right"]].set_visible(False); a.legend(frameon=False, fontsize=9, loc="upper right"); a.set_title("Many small rotors vs one big rotor", loc="left", weight="bold", fontsize=15); f.tight_layout(); f.savefig("out/rotor_net.png", facecolor=f.get_facecolor()); json.dump(S, open("out/rotor_net2.json", "w"), indent=1)
