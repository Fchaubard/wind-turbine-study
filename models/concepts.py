"""Punta Mita prototype shoot-out: every simple wind machine worth building on a beach, in the same wind,
with the same generator kit, ranked by energy per dollar.
Rotor aerodynamics: multi-annulus blade-element momentum (reusing rotary.rotor_point per annulus) for the
horizontal-axis rotors; published test coefficients for drag machines. Each concept carries a 'field factor'
(measured electrical / ideal rotor power) so nothing is credited with theory it has not shown in tests."""
import json, math, sys
import numpy as np
import rotary as RT

RHO = 1.18
W10 = np.load("out/puntamita_w10.npy")
GEN_KIT = 240 + 21 + 32 + 117 + 15          # hub motor wheel, rectifier, 3 resistors, power logger, freewheel
KV, R_M, V_D = 10.5, 0.14, 1.4               # hub motor rpm/V, ohm; rectifier drop
# field factors: overridden from out/field_factors.json when the literature check comes back
FF = dict(sail=0.60, rigid=0.60, savonius=0.60, kite_ring=None, drag=0.60)
try:
    FF.update(json.load(open("out/field_factors.json")))
except FileNotFoundError:
    pass


def bem(N, R, r_hub, chord, cd0, n_ann=14, beta=0.0):
    """Standard blade-element momentum rotor (wake rotation, Prandtl tip + hub loss, Glauert high-induction
    correction), ideal pitch (best CL per annulus up to 1.2). Returns the best Cp on swept disc area over tip-speed ratio."""
    edges = np.linspace(r_hub, R, n_ann + 1); best = None
    for lam in np.linspace(0.6, 9, 43):
        cp = ct = 0.0
        for r0, r1 in zip(edges[:-1], edges[1:]):
            r = 0.5 * (r0 + r1); dr = r1 - r0; x = lam * r / R; sig = N * chord(r) / (2 * math.pi * r)
            bq = (0.0, 0.0)
            for CL in (0.5, 0.7, 0.9, 1.1, 1.2):
                CD = cd0 * (1 + 0.6 * (CL - 0.8) ** 2 / 0.16)
                a_, ap = 0.3, 0.0
                for _ in range(80):
                    phi = math.atan2(1 - a_, (1 + ap) * x); sp, cph = max(math.sin(phi), 1e-4), math.cos(phi)
                    F = (2 / math.pi * math.acos(min(1, math.exp(-N * (R - r) / (2 * r * sp))))) * (2 / math.pi * math.acos(min(1, math.exp(-N * (r - r_hub * 0.5) / (2 * r * sp)))))
                    F = max(F, 0.05)
                    Cn = CL * cph + CD * sp; Ctg = CL * sp - CD * cph
                    k = sig * Cn / (4 * F * sp * sp)
                    an = k / (1 + k)
                    if an > 0.4:                                   # Glauert / Buhl
                        CT = sig * (1 - a_) ** 2 * Cn / (sp * sp)
                        an = (18 * F - 20 - 3 * math.sqrt(max(CT * (50 - 36 * F) + 12 * F * (3 * F - 4), 0))) / (36 * F - 50)
                    kp = sig * Ctg / (4 * F * sp * cph)
                    apn = kp / (1 - kp) if kp < 0.9 else 0.0
                    a_ = 0.5 * a_ + 0.5 * min(max(an, 0), 0.95); ap = 0.5 * ap + 0.5 * max(apn, -0.5)
                W2 = (1 - a_) ** 2 + ((1 + ap) * x) ** 2
                dq = N * 0.5 * W2 * chord(r) * Ctg * r * dr           # torque / (rho V^2)
                dt = N * 0.5 * W2 * chord(r) * Cn * dr
                if dq * lam / R > bq[0]:
                    bq = (dq * lam / R, dt)
            cp += bq[0] / (0.5 * math.pi * R * R); ct += bq[1] / (0.5 * math.pi * R * R)
        if best is None or cp > best["cp"]:
            best = dict(cp=cp, ct=ct, lam=lam)
    return best


def gen_eff(P_mech, rotor_rpm, ratio):
    """chain (0.95) -> hub motor copper loss -> rectifier drop"""
    if P_mech <= 0 or rotor_rpm <= 0:
        return 0.0
    P = 0.95 * P_mech; E = ratio * rotor_rpm / KV; I = P / E
    return max(P - I * I * R_M - V_D * I, 0.0) / P_mech


def energy(cp_mech, area, lam, R_tip, field, ratio, v_in, v_out=12.0, cap=1200.0):
    """Annual energy in the Punta Mita hourly record. field = everything between ideal rotor power and shaft power."""
    tot = 0.0; curve = {}
    for v in np.arange(0.5, 18.01, 0.5):
        Pm = field * cp_mech * 0.5 * RHO * v**3 * area if v_in <= v <= v_out else 0.0
        rpm = lam * v / R_tip * 60 / (2 * math.pi)
        Pe = min(Pm * gen_eff(Pm, rpm, ratio), cap)
        frac = float(((W10 >= v - 0.25) & (W10 < v + 0.25)).mean())
        tot += Pe * frac; curve[float(v)] = dict(P_el=Pe, rpm=rpm)
    return tot, curve


def best_ratio(cp, area, lam, R_tip, field, v_in):
    return max(((energy(cp, area, lam, R_tip, field, g, v_in)[0], g) for g in (1.0, 2.0, 3.14, 4.4)))[1]


C = []
def add(name, kind, cp, lam, R_tip, area, field, v_in, parts, notes, thrust_ct=0.8, hub_h=5.0):
    g = best_ratio(cp, area, lam, R_tip, field, v_in)
    avg, curve = energy(cp, area, lam, R_tip, field, g, v_in)
    cost = GEN_KIT + sum(p[1] for p in parts)
    thrust12 = thrust_ct * 0.5 * RHO * 144 * area
    C.append(dict(name=name, kind=kind, cp_rotor=cp, lam=lam, dia=2 * R_tip, area=area, field=field, ratio=g, cut_in=v_in,
                  avg_W=avg, kWh_yr=avg * 8.766, P4=curve[4.0]["P_el"], P6=curve[6.0]["P_el"], P8=curve[8.0]["P_el"], rpm6=curve[6.0]["rpm"],
                  cost=cost, parts=parts, kWh_per_usd_5yr=avg * 8.766 * 5 / cost, usd_per_MWh_5yr=cost / (avg * 8.766 * 5 / 1000) if avg > 0 else None,
                  thrust12_N=thrust12, base_moment12_Nm=thrust12 * hub_h, notes=notes))


POLE = [("Pole: 2 x galvanised post tube 73 mm x 3.05 m (MX$545 each), sleeved", 1090 / 18.5), ("Guys: 30 m of 3/16 in steel cable (MX$27/m), clamps, 3 buried anchors", (810 + 300) / 18.5),
        ("Used bicycle (bearing + chain drive), bolts, plywood hub disc (MX$599)", 100 + 30 + 599 / 18.5)]
# 1-3. cloth sail windmills (Cretan type): triangular sails, chord grows with radius
for dia, n in ((3.0, 6), (4.0, 8), (5.0, 8)):
    R = dia / 2; b = bem(n, R, 0.15 * R, lambda r, R=R, n=n: 0.9 * (2 * math.pi * r / n) * 0.45, cd0=0.16)
    add(f"Sail windmill on a pole, {dia:.0f} m, {n} cloth sails", "sail", b["cp"], b["lam"], R, math.pi * R * R, FF["sail"], 2.5,
        POLE + [(f"{n} spars: 1 in steel conduit 3 m (MX$249 each), bowsprit + stay ropes", (249 * (n + 1) + 219) / 18.5), ("Sails: polyethylene tarp 4.87 x 3.65 m (MX$765), cord", (765 + 109) / 18.5)],
        "Spars need a bowsprit with a stay rope to each tip (unstayed conduit yields above about 8 m/s). Furl or untie sails above 10 m/s.", b["ct"])
# 4-5. rigid-blade rotors on a pole: carved foam / PVC-pipe blades
for dia, n, cd0, nm in ((2.4, 3, 0.08, "PVC-pipe blades"), (3.6, 3, 0.06, "foam + carbon-spar blades")):
    R = dia / 2; b = bem(n, R, 0.12 * R, lambda r, R=R: 0.16 * R * (1.3 - r / R), cd0=cd0)
    add(f"3-blade rotor on a pole, {dia:.1f} m, {nm}", "rigid", b["cp"], b["lam"], R, math.pi * R * R, FF["rigid"], 3.0,
        POLE + [("blades, hub plate, tail vane", 90.0 if dia < 3 else 190.0)], "Fast tips (noise, injury risk); needs a furling tail or brake.", b["ct"])
# 6-7. Savonius S-rotors (published Cp about 0.15-0.2 at tip-speed ratio about 0.8-1)
for h, d, nm, cost in ((1.8, 0.9, "two split 200 L drums stacked", 90.0), (3.0, 1.5, "tarp on a plywood-and-conduit frame", 130.0)):
    add(f"Savonius S-rotor, {h} m × {d} m, {nm}", "savonius", 0.22, 0.9, d / 2, h * d, FF["savonius"], 3.0,
        [("frame, bearings, guy lines", 120.0), ("rotor: " + nm, cost)], "Any wind direction, no yaw; very slow, needs a big step-up.", 1.1, 2.5)
# 8. flat-sheet drag carousel (panemone): what 'a sheet that catches the wind' can do at best
add("Drag carousel: 4 flapping tarp panels, 3 m × 2 m", "drag", 0.06, 0.4, 1.5, 3.0 * 2.0, FF["drag"], 3.5,
    [("frame, bearings, guy lines", 120.0), ("tarp panels and hinges", 60.0)], "The 'catch the wind' machine. Simple, but the panels fight the wind half the turn.", 1.2, 2.5)
# 9. kite ring from proto.py (calibrated to Daisy field data), for reference
try:
    P = json.load(open("out/proto_bom.json")); r = P["rotor"]
    C.append(dict(name="Kite ring on a rope shaft with lifter kite, 4.8 m", kind="kite_ring", cp_rotor=r["cp"], lam=r["lam"], dia=4.8, area=r["A"], field=P["K"]["mid"], ratio=3.14, cut_in=3.0,
                  avg_W=r["avg_W"], kWh_yr=r["kWh_yr"], P4=r["at4"]["P_el"], P6=r["at6"]["P_el"], P8=None, rpm6=r["at6"]["rpm"], cost=P["total"], parts=[],
                  kWh_per_usd_5yr=r["kWh_yr"] * 5 / P["total"], usd_per_MWh_5yr=P["total"] / (r["kWh_yr"] * 5 / 1000), thrust12_N=r["at12"]["thrust"], base_moment12_Nm=0.0,
                  notes="Tension only, no tower; hardest to launch. Field factor is electrical/ideal, from Daisy tests."))
except FileNotFoundError:
    pass
C.sort(key=lambda c: -c["kWh_per_usd_5yr"])
json.dump(dict(field_factors=FF, gen_kit=GEN_KIT, concepts=C), open("out/concepts.json", "w"), indent=1, default=float)
print(f"{'concept':58s} {'Cp':>5s} {'λ':>4s} {'gear':>5s} {'W@4':>5s} {'W@6':>5s} {'avg W':>6s} {'kWh/yr':>7s} {'cost':>6s} {'kWh/$ 5y':>8s} {'$/MWh':>7s}")
for c in C:
    print(f"{c['name'][:58]:58s} {c['cp_rotor']:5.2f} {c['lam']:4.1f} {c['ratio']:5.1f} {c['P4']:5.0f} {c['P6']:5.0f} {c['avg_W']:6.1f} {c['kWh_yr']:7.0f} {c['cost']:6.0f} {c['kWh_per_usd_5yr']:8.2f} {c['usd_per_MWh_5yr']:7.0f}")
