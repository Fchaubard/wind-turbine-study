"""Audit of the sail windmill's energy estimate against things the optimiser ignored:
wind direction (the rotor is fixed on a propped pole), 6 m hub height, and drivetrain drag / start-up."""
import json, math, io, contextlib
import numpy as np
with contextlib.redirect_stdout(io.StringIO()):
    import sail_opt as S

d = json.load(open("out/puntamita_dir.json"))["properties"]["parameter"]
k = sorted(d["WS10M"]); ws = np.array([d["WS10M"][t] for t in k]); wd = np.array([d["WD10M"][t] for t in k])
ok = (ws >= 0) & (wd >= 0); ws, wd = ws[ok], wd[ok]; hr = np.array([int(t[-2:]) for t in k])[ok]
p = S.json.load(open("out/sail_opt.json"))["pick"]; cps, cts = S.curve(p["n"], p["k"]); DIA, RATIO, ETA, RL = p["dia"], p["ratio"], p["eta"], p["R_load"]
R = DIA / 2; A = math.pi * R * R


def power(v, q_rotor_loss=0.0, q_motor_loss=0.0):
    """equilibrium electrical power with constant drag torque at rotor and at motor (N·m)"""
    if v < 2.5 or v > p["v_furl"]: return 0.0
    qr = lambda l: float(np.interp(l, S.LAMS, cps)) * S.FIELD * 0.5 * S.RHO * v**3 * A / (l * v / R) - q_rotor_loss
    def qg(l):
        E = RATIO * l * v / R * 60 / (2 * math.pi) / S.KV; I = max(E - S.V_D, 0.0) / (S.R_M + RL)
        return (S.K_T * I + q_motor_loss) * RATIO / ETA, I
    lo, hi = 0.31, 3.59
    if qr(lo) < qg(lo)[0]: return 0.0
    for _ in range(40):
        m = 0.5 * (lo + hi)
        if qr(m) > qg(m)[0]: lo = m
        else: hi = m
    I = qg(lo)[1]; return I * I * RL


GRID = np.arange(0, 18.01, 0.1)
def table(qr=0.0, qm=0.0): return np.array([power(v, qr, qm) for v in GRID])
def avg(v, T): return float(np.interp(v, GRID, T).mean())
T0 = table(); out = {}
out["as reported (all wind, 10 m data)"] = avg(ws, T0)
hubf = (6 / 10) ** 0.14; out["+ 6 m hub (shear 0.14)"] = avg(ws * hubf, T0)
def fixed(az, T, f):
    c = np.cos(np.radians(wd - az)); return avg(np.where(c > 0, ws * f * c, 0.0), T)
scan = [(fixed(a, T0, hubf), a) for a in range(0, 360, 10)]; best, az = max(scan)
out[f"+ fixed rotor, best facing ({az}°)"] = best
out["+ free yaw with tail vane instead (10° avg error)"] = avg(ws * hubf * math.cos(math.radians(10)), T0)
Td = table(3.0, 1.0)
out["fixed rotor + drag (3 N·m bearings/chain, 1 N·m cogging)"] = fixed(az, Td, hubf)
out["tail vane + drag"] = avg(ws * hubf * math.cos(math.radians(10)), Td)
for n, v in out.items(): print(f"{n:58s} {v:6.1f} W   {v*8.766:6.0f} kWh/yr")
rose = np.histogram((wd + 22.5) % 360, bins=8, range=(0, 360), weights=ws**3)[0]; rose = rose / rose.sum()
print("share of wind energy by direction:", dict(zip("N NE E SE S SW W NW".split(), np.round(rose * 100).astype(int).tolist())))
print("share of hours by direction:", dict(zip("N NE E SE S SW W NW".split(), np.round(np.histogram((wd + 22.5) % 360, bins=8, range=(0, 360))[0] / len(wd) * 100).astype(int).tolist())))
print("afternoon (12-18h) mean wind", round(float(ws[(hr >= 12) & (hr < 18)].mean()), 2), "mean dir (circular)", round(float(np.degrees(np.arctan2(np.sin(np.radians(wd[(hr>=12)&(hr<18)])).mean(), np.cos(np.radians(wd[(hr>=12)&(hr<18)])).mean())) % 360)))
for qt in (1.0, 2.0, 4.0):
    pass
Q_start = float(np.interp(0.31, S.LAMS, cps)) * S.FIELD * 0.5 * S.RHO * A * R / 0.31
vs = math.sqrt((3.0 + 1.0 * RATIO / ETA) / Q_start)
print(f"start-up wind needed with that drag (rotor torque at λ 0.31): {vs:.1f} m/s; hours above it: {100*(ws*hubf>=vs).mean():.0f}%")
json.dump(dict(steps=out, best_az=az, rose=rose.tolist(), v_start=vs), open("out/energy_audit.json", "w"), indent=1)
