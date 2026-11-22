"""Sail windmill for Punta Mita: whole-system simulation and structural checks.
Rotor Cp(lambda) from blade-element momentum -> bicycle chain -> e-bike hub motor -> rectifier -> fixed resistor.
For every wind speed the operating rpm is where rotor torque equals generator torque, so the power curve is what
the real, uncontrolled machine would do, not the rotor's best case. Then loads on spars, stays, chain, pole and guys."""
import json, math, sys, io, contextlib
import numpy as np
with contextlib.redirect_stdout(io.StringIO()):
    import concepts as CC

RHO = CC.RHO; W10 = CC.W10; KV, R_M, V_D = CC.KV, CC.R_M, CC.V_D
K_T = 9.549 / KV                         # N·m per A
FIELD = CC.FF["sail"]
LAMS = np.linspace(0.3, 3.6, 34)
# 1 in thin-wall steel conduit (OD 29.5 mm, wall 1.2 mm): section properties
OD, WALL = 29.5e-3, 1.2e-3; ID = OD - 2 * WALL
I_SP = math.pi * (OD**4 - ID**4) / 64; S_SP = I_SP / (OD / 2); A_SP = math.pi * (OD**2 - ID**2) / 4
FY = 230e6; E_ST = 200e9
CHAIN_BREAK = 8000.0                     # N, ordinary 1/2 x 1/8 in bicycle chain (typical minimum)
MOTOR_T, MOTOR_I = 30.0, 30.0            # N·m and A the hub motor is rated for


def rotor_curve(dia, n):
    R = dia / 2; chord = lambda r: 0.9 * (2 * math.pi * r / n) * 0.45
    cps, cts = [], []
    for lam in LAMS:
        b = CC.bem(n, R, 0.15 * R, chord, 0.16, lams=[lam]); cps.append(max(b["cp"], 0.0)); cts.append(b["ct"])
    return np.array(cps), np.array(cts)


def operate(dia, cps, cts, v, ratio, R_load):
    """Equilibrium of rotor torque and generator torque at wind v. Returns dict (rpm, lambda, electrical W, loads)."""
    R = dia / 2; A = math.pi * R * R
    def q_rotor(lam):
        cp = float(np.interp(lam, LAMS, cps)) * FIELD
        return cp * 0.5 * RHO * v**3 * A / (lam * v / R) if lam > 0 else 0.0
    def q_gen(lam):
        rpm_g = ratio * lam * v / R * 60 / (2 * math.pi); E = rpm_g / KV
        I = max(E - V_D, 0.0) / (R_M + R_load)
        return K_T * I * ratio / 0.95, I, E
    lo, hi = 0.31, 3.59
    if q_rotor(lo) < q_gen(lo)[0]:
        return dict(v=v, rpm=0.0, lam=0.0, P_el=0.0, I=0.0, V=0.0, Q=0.0, thrust=0.9 * 0.5 * RHO * v * v * A * 0.5)
    for _ in range(50):
        mid = 0.5 * (lo + hi)
        if q_rotor(mid) > q_gen(mid)[0]: lo = mid
        else: hi = mid
    lam = lo; Qg, I, E = q_gen(lam)
    return dict(v=v, rpm=lam * v / R * 60 / (2 * math.pi), lam=lam, P_el=I * I * R_load, I=I, V=I * R_load, Q=Qg,
                thrust=float(np.interp(lam, LAMS, cts)) * 0.5 * RHO * v * v * A)


def annual(dia, cps, cts, ratio, R_load, v_furl):
    tot = 0.0
    for v in np.arange(0.5, 18.01, 0.5):
        frac = float(((W10 >= v - 0.25) & (W10 < v + 0.25)).mean())
        if 2.5 <= v <= v_furl:
            tot += operate(dia, cps, cts, v, ratio, R_load)["P_el"] * frac
    return tot


def structure(dia, n, op):
    """Loads at one operating point. Spar: 1 in conduit, hub to tip, with a stay from a bowsprit (0.4 R) to its tip."""
    R = dia / 2; F = op["thrust"] / n; th = math.atan(0.4)
    M_stayed = F * 0.65 * 0.35 * R                       # point load at 0.65 R on a hub-to-tip span
    M_unstayed = F * 0.65 * R
    T_stay = 0.65 * F / math.sin(th); C_spar = T_stay * math.cos(th)
    M_inplane = op["Q"] / n * 0.5                        # torque shared by the spars; sheets tie each tip to the next spar
    sig = (math.hypot(M_stayed, M_inplane)) / S_SP + C_spar / A_SP
    euler = math.pi**2 * E_ST * I_SP / R**2
    chain = op["Q"] / 0.097                               # 48-tooth chainring, pitch radius 97 mm
    guy = op["thrust"] / math.cos(math.radians(45))       # one windward guy at 45 degrees takes the thrust
    return dict(spar_stress_MPa=sig / 1e6, spar_SF=FY / sig if sig > 0 else 99, unstayed_stress_MPa=M_unstayed / S_SP / 1e6, stay_N=T_stay, spar_compression_N=C_spar,
                euler_SF=euler / max(C_spar, 1), bowsprit_N=n * 0.65 * F, chain_N=chain, chain_SF=CHAIN_BREAK / max(chain, 1), guy_N=guy,
                motor_torque=op["Q"] * 0.95 / RATIO, motor_ok=bool(op["Q"] * 0.95 / RATIO <= MOTOR_T and op["I"] <= MOTOR_I))


RATIO = 48 / 14
out = dict(field=FIELD, ratio=RATIO, designs=[])
for dia, n in ((3.0, 8), (3.5, 8), (4.0, 8), (5.0, 8)):
    cps, cts = rotor_curve(dia, n)
    best = None
    for Rl in (0.48, 0.725, 0.97, 1.45, 2.9, 5.8):
        for vf in (8.0, 10.0, 12.0):
            ops = [operate(dia, cps, cts, v, RATIO, Rl) for v in (3, 4, 5, 6, 7, 8, 10, 12)]
            st = {o["v"]: structure(dia, n, o) for o in ops}
            ok = all(st[v]["chain_SF"] >= 3 and st[v]["spar_SF"] >= 1.5 for v in st if v <= vf)
            a = annual(dia, cps, cts, RATIO, Rl, vf)
            if ok and (best is None or a > best["avg_W"]):
                best = dict(dia=dia, n=n, R_load=Rl, v_furl=vf, avg_W=a, kWh_yr=a * 8.766, ops=ops, struct=st, cp_max=float(cps.max()), lam_opt=float(LAMS[cps.argmax()]))
    out["designs"].append(best)
    if best is None:
        print(f"{dia} m: no load/furl combination passes the structural limits"); continue
    print(f"\n{dia:.0f} m, {n} sails: rotor Cp max {best['cp_max']:.2f} at λ {best['lam_opt']:.1f}; best resistor {best['R_load']} ohm, furl above {best['v_furl']:.0f} m/s → {best['avg_W']:.1f} W average, {best['kWh_yr']:.0f} kWh/yr")
    for o in best["ops"]:
        s = best["struct"][o["v"]]
        print(f"  {o['v']:>2} m/s: {o['rpm']:4.0f} rpm λ {o['lam']:.2f}  {o['V']:5.1f} V {o['I']:5.1f} A  {o['P_el']:6.0f} W | thrust {o['thrust']:5.0f} N  spar {s['spar_stress_MPa']:4.0f} MPa (SF {s['spar_SF']:.1f}; unstayed {s['unstayed_stress_MPa']:.0f})  "
              f"stay {s['stay_N']:4.0f} N  chain {s['chain_N']:5.0f} N (SF {s['chain_SF']:.1f})  guy {s['guy_N']:5.0f} N  motor {'ok' if s['motor_ok'] else 'OVER'}")
json.dump(out, open("out/sail_design.json", "w"), indent=1, default=float)
