"""Punta Mita prototype: a Daisy-type rotary kite ring with rigid foam blades and a ground generator.
1. calibrate the BEM rotor model against the published Daisy field measurements (Tulloch et al., Energies 2023)
2. sweep buildable rotor geometries in three years of hourly Punta Mita wind (NASA POWER)
3. size the rope shaft (TRPT) and check it with the nonlinear FEA; loads for lines, anchor, lifter
"""
import json, math, itertools
import numpy as np
import rotary as RT

RHO = 1.18                      # warm sea-level air
BETA = math.radians(30)         # shaft elevation
W10 = np.load("out/puntamita_w10.npy")

# ---------------------------------------------------------------- 1. calibration on Daisy (rigid rotor)
def geo(N, r_in, b, c, cd0=0.025, cdt=0.03):
    return dict(N=N, R=r_in + b / 2, b=b, S=b * c, AR=b / c, CD0=cd0, CDt=cdt)

DAISY = geo(3, 1.22, 1.0, 0.2)
rb = RT.best_rotor(DAISY, BETA)
A_d = 2 * math.pi * DAISY["R"] * DAISY["b"]
meas = [(5.3, 35.0), (6.1, 50.0), (2.7, 10.0)]
cal = []
for v, p in meas:
    pred = rb["cp_on_V"] * 0.5 * RHO * v**3 * A_d
    cal.append(dict(v=v, measured_W=p, model_mech_W=pred, ratio=p / pred))
K_LO = min(c["ratio"] for c in cal[:2]); K_MID = float(np.mean([c["ratio"] for c in cal[:2]])); K_HI = cal[2]["ratio"]
print(f"Daisy model: Cp {rb['cp_on_V']:.3f} (λ {rb['lam']:.1f}, CL {rb['CL']:.2f}), area {A_d:.1f} m²")
for c in cal: print(f"  {c['v']} m/s: measured {c['measured_W']:.0f} W, model mechanical {c['model_mech_W']:.0f} W, ratio {c['ratio']:.2f}")
print(f"calibration factor (electrical out / model mechanical): low {K_LO:.2f}, mid {K_MID:.2f}, light-wind point {K_HI:.2f}")

# ---------------------------------------------------------------- 2. design sweep
P_CAP = 500.0                   # generator / test-load cap, W
V_CUT_IN, V_STOW = 3.0, 12.0    # below: will not turn usefully; above: land it


def evaluate(N, r_in, b, c, k=K_MID, wind_f=1.0):
    g = geo(N, r_in, b, c)
    r = RT.best_rotor(g, BETA)
    A = 2 * math.pi * g["R"] * b
    w = W10 * wind_f
    P = np.where((w >= V_CUT_IN) & (w <= V_STOW), np.minimum(k * r["cp_on_V"] * 0.5 * RHO * w**3 * A, P_CAP), 0.0)
    def at(v):
        Vn = v * math.cos(BETA); Om = r["lam"] * Vn / g["R"]
        Pm = r["cp_on_V"] * 0.5 * RHO * v**3 * A
        return dict(v=v, rpm=Om * 60 / (2 * math.pi), tip=Om * (r_in + b), P_el=min(k * Pm, P_CAP), Q=Pm / Om,
                    thrust=r["ct_on_Vn"] * 0.5 * RHO * Vn**2 * A)
    return dict(N=N, r_in=r_in, b=b, c=c, R_out=r_in + b, A=A, S=N * b * c, cp=r["cp_on_V"], lam=r["lam"], CL=r["CL"],
                avg_W=float(P.mean()), kWh_yr=float(P.mean() * 8.766), hours_frac=float((P > 0).mean()),
                at4=at(4.0), at6=at(6.0), at10=at(10.0), at12=at(12.0))


rows = []
for N, r_in, b, c in itertools.product((3, 4, 6), (1.2, 1.8, 2.4), (1.0, 1.2), (0.20, 0.25, 0.30)):
    rows.append(evaluate(N, r_in, b, c))
rows.sort(key=lambda r: -r["avg_W"])
print("\ntop designs by average power (mid calibration, dataset wind):")
for r in rows[:8]:
    print(f"  N={r['N']} r_in={r['r_in']} b={r['b']} c={r['c']}  dia {2*r['R_out']:.1f} m  area {r['A']:.1f} m²  Cp {r['cp']:.3f} λ {r['lam']:.1f}  avg {r['avg_W']:.1f} W  "
          f"@6 m/s: {r['at6']['P_el']:.0f} W {r['at6']['rpm']:.0f} rpm  @12: thrust {r['at12']['thrust']:.0f} N tip {r['at12']['tip']:.0f} m/s")
json.dump(dict(calibration=cal, K=dict(lo=K_LO, mid=K_MID, hi=K_HI), daisy_model=dict(cp=rb["cp_on_V"], lam=rb["lam"]), sweep=rows), open("out/proto_sweep.json", "w"), indent=1, default=float)
