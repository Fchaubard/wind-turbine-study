"""Metronome Wing with self-consistent mass: simulate, size the spar from the loads, put that real spar mass back into the swing dynamics, repeat until it converges."""
import itertools, json
import numpy as np
import metronome as M
R = []
for Rr, c0, th, bt, wn in itertools.product((16, 22, 28), (.8, 1.2), (1.0, 1.19), (4, 8), (.8, 1.4)):
    r1 = max(1.5, .18 * Rr); mw = 1.5 * c0 * Rr / 12 * (Rr - r1) * .8; ms = 2.8 * Rr; ok = True; st = None
    for it in range(6):
        x = M.sim(float(Rr), r1, c0 * Rr / 12, th, bt, wn, mw, ms, 1500 * (Rr / 6)**2); st = M.size(float(Rr), x, th, 7.)
        if not st: ok = False; break
        new = st["spar_kg"]
        if abs(new - ms) / max(ms, 1) < .03: ms = new; break
        ms = .5 * ms + .5 * new
    if not ok: continue
    x = M.sim(float(Rr), r1, c0 * Rr / 12, th, bt, wn, mw, ms, 1500 * (Rr / 6)**2); st = M.size(float(Rr), x, th, 7.)
    if not st or abs(st["spar_kg"] - ms) / ms > .25: continue
    d = dict(R=Rr, c0=c0, th=th, beta=bt, wn=wn, vf=7.)
    for ng in (1, 2, 4, 8):
        W, cap, life, pad = M.econ(d, x, st, ng, 7.)
        if W > 1: R.append(dict(d, ng=ng, W=W, cap=cap, life=life, usd=life / (W * 8.766 * 20 / 1000), pad=pad, A=x["A"], S=x["S"], spar_used=ms, cp4=float(x["P"][2] / (.5 * M.RHO * 64 * x["A"])), **st))
    print("done", Rr, c0, th, bt, wn, flush=True)
R.sort(key=lambda r: r["usd"]); json.dump(R[:25], open("out/metronome2.json", "w"), indent=1, default=float); print(len(R), "converged designs"); seen = set()
for r in R:
    if r["R"] in seen: continue
    seen.add(r["R"]); print(f"R {r['R']} m | swept {r['A']:.0f} m², wing {r['S']:.1f} m², Cp {r['cp4']:.2f}, swing ±{r['th']:.2f} rad | {r['W']:.0f} W ${r['cap']:,.0f} ${r['usd']:.0f}/MWh | spar {r['spar_used']:.0f} kg, 17 m/s moment {r['M17']/1000:.0f} kNm, pad {r['pad']:.0f} t")
