"""One simulator for every wind-machine idea, on equal terms, in three years of hourly Punta Mita wind (speed AND direction).
Each concept: measured Cp and tip-speed ratio, swept area, number of rotors, hub height, yaw behaviour, drag, parts cost, wear.
The drivetrain (gear ratio, load resistance, reef speed) is optimised per concept, so no idea loses to a bad gear choice."""
import json, math
import numpy as np

RHO, KV, R_M, V_D, ALPHA = 1.18, 10.5, 0.14, 1.4, 0.14
K_T = 9.549 / KV
_d = json.load(open("out/puntamita_dir.json"))["properties"]["parameter"]
_k = sorted(_d["WS10M"]); WS = np.array([_d["WS10M"][t] for t in _k]); WD = np.array([_d["WD10M"][t] for t in _k])
_ok = (WS >= 0) & (WD >= 0); WS, WD = WS[_ok], WD[_ok]
VG = np.arange(0.0, 18.01, 0.25); LG = np.linspace(0.05, 1.8, 141)     # lambda as a fraction of 1.8 x the rotor's best
RATIOS = (1.0, 2.0, 3.43, 4.0, 6.86, 10.3, 13.7)
LOADS = (0.36, 0.48, 0.73, 0.97, 1.45, 2.9, 5.8, 11.6)


def wind_at(hub, yaw, facing=330.0, speedup=1.0):
    """hourly wind component the rotor sees. yaw: 'free' (tail, 10 deg mean error), 'omni' (vertical axis), 'fixed'."""
    v = WS * (hub / 10.0) ** ALPHA * speedup
    if yaw == "free": return v * math.cos(math.radians(10))
    if yaw == "omni": return v
    c = np.cos(np.radians(WD - facing)); return np.where(c > 0, v * c, 0.0)


def table(c, ratio, Rl, eta):
    """electrical W and amps per rotor vs wind, at the equilibrium of rotor torque and generator torque (constant drag included)"""
    A, R, cp0, l0 = c["area"], c["radius"], c["cp"] * c.get("field", 0.75), c["tsr"]
    Ls = LG * l0; x = (Ls - l0) / (l0 * c.get("width", 0.8)); cps = np.maximum(cp0 * (1 - x * x), 0.0)
    P, Am = np.zeros_like(VG), np.zeros_like(VG)
    for i, v in enumerate(VG):
        if v < 0.5: continue
        om = Ls * v / R; qr = cps * 0.5 * RHO * v**3 * A / om - c.get("q_rotor", 3.0)
        E = ratio * om * 60 / (2 * math.pi) / KV; I = np.maximum(E - V_D, 0.0) / (R_M + Rl); qg = (K_T * I + c.get("q_motor", 1.0)) * ratio / eta
        s = qr - qg
        if s.max() <= 0 or s[0] < 0 and s.max() < 0: continue
        j = len(s) - 1 - int(np.argmax((s > 0)[::-1]))        # highest-speed stable point
        P[i] = I[j] ** 2 * Rl; Am[i] = I[j]
    return P, Am


def evaluate(c, years=5):
    v = wind_at(c["hub"], c["yaw"], speedup=c.get("speedup", 1.0)); best = None
    if c.get("direct"):                                      # mechanical end use, no generator: delivered useful energy
        P = np.maximum(c["cp"] * c.get("field", 0.75) * c.get("eta_use", 0.6) * 0.5 * RHO * v**3 * c["area"], 0.0) * (v <= c.get("v_reef", 9.0))
        avg = float(P.mean()) * c.get("n", 1); ratio = Rl = None; vf = c.get("v_reef", 9.0)
    elif c.get("mppt"):                                      # charge controller holds the rotor at its best speed in every wind
        A, R, cp0, l0 = c["area"], c["radius"], c["cp"] * c.get("field", 0.75), c["tsr"]
        Ls = LG * l0; x = (Ls - l0) / (l0 * c.get("width", 0.8)); cps = np.maximum(cp0 * (1 - x * x), 0.0)
        for ratio_ in RATIOS:
            eta = 0.95 if ratio_ <= 4.0 else (0.90 if ratio_ <= 7 else 0.86); P = np.zeros_like(VG)
            for i, u in enumerate(VG):
                if u < 0.5 or u > c.get("v_reef", 12.0): continue
                om = Ls * u / R; q = (cps * 0.5 * RHO * u**3 * A / om - c.get("q_rotor", 3.0)) * eta / ratio_ - c.get("q_motor", 1.0)
                I = np.clip(q / K_T, 0.0, 30.0); E = ratio_ * om * 60 / (2 * math.pi) / KV
                ok = (q > 0) & (E > 8.0)
                if ok.any(): P[i] = float((((E - V_D) * I - I * I * R_M) * ok).max()) * 0.95
            a_ = float(np.interp(v, VG, P).mean()) * c.get("n", 1)
            if best is None or a_ > best[0]: best = (a_, ratio_, None, c.get("v_reef", 12.0))
        avg, ratio, Rl, vf = best
    else:
        for ratio_ in RATIOS:
            eta = 0.95 if ratio_ <= 4.0 else (0.90 if ratio_ <= 7 else 0.86)
            for Rl_ in LOADS:
                P, I = table(c, ratio_, Rl_, eta); n_res = max(1, round(2.9 / Rl_))
                limit = (I > 30.0) | (P > 270.0 * n_res)
                vf = float(VG[np.argmax(limit)]) if limit.any() else 18.0
                vf = min(vf, c.get("v_reef", 12.0))
                PP = np.where(VG < vf, P, 0.0); a = float(np.interp(v, VG, PP).mean()) * c.get("n", 1)
                if best is None or a > best[0]: best = (a, ratio_, Rl_, vf)
        avg, ratio, Rl, vf = best
    cost5 = c["capex"] + c.get("wear_per_year", 0.0) * (years - 1)
    mwh = avg * 8.766 * years / 1e6 * 1000 / 1000
    return dict(name=c["name"], avg_W=avg, kWh_yr=avg * 8.766, capex=c["capex"], cost5=cost5, usd_per_MWh=cost5 / (avg * 8.766 * years / 1000) if avg > 0 else None,
                ratio=ratio, R_load=Rl, v_reef=vf, cp=c["cp"], tsr=c["tsr"], yaw=c["yaw"], hub=c["hub"], area=c["area"] * c.get("n", 1), source=c.get("source", ""))


if __name__ == "__main__":
    base = dict(name="5 m sail rotor with tail vane", cp=0.23, tsr=1.4, area=math.pi * 2.5**2, radius=2.5, hub=6.0, yaw="free", capex=1199, wear_per_year=41)
    r = evaluate(base); print({k: (round(v, 2) if isinstance(v, float) else v) for k, v in r.items()})
    fx = dict(base, yaw="fixed", name="same, bolted facing 330°"); r = evaluate(fx); print(r["name"], round(r["avg_W"], 1), "W")
