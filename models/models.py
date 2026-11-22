"""
Analytical models for the windsock-concentrator idea and the crosswind-kite
alternative, plus BOM / cost / LCOE.  Reads FEA results from out/ if present.

Reference machine: NREL 5 MW reference turbine (D = 126 m, hub 90 m, rated 11.4 m/s).
"""
import json, math, os
import numpy as np

RHO = 1.225
D = 126.0                    # rotor / windsock mouth diameter (m)
A = math.pi * D**2 / 4       # 12,469 m^2
HUB = 90.0
V_RATED = 11.4
P_RATED = 5.0e6
BETZ = 16 / 27


def q(V):
    return 0.5 * RHO * V**2


# ---------------------------------------------------------------- concentrator
def throat_cp(eps=1.0, cpb=0.0, K=0.0):
    """Ideal-fluid energy balance for a sealed duct: mouth -> throat turbine -> (diffuser) -> exit.

    total pressure in  : p_inf + q
    turbine takes      : dp_T
    losses             : K * 1/2 rho v_t^2
    exit               : p_inf + cpb*q + 1/2 rho (eps v_t)^2       (eps = A_throat / A_exit)
    => dp_T/q = (1-cpb) - (eps^2+K) u^2      with u = v_t / V
    P/(q V A_t) = u * dp_T/q  -> maximise over u.
    NOTE the mouth area does not appear: the mouth only has to be big enough not to choke.
    """
    a = 1 - cpb
    b = eps**2 + K
    u = math.sqrt(a / (3 * b))
    cp_t = u * (a - b * u**2)
    return cp_t, u


SCENARIOS = {
    # name: (eps, cpb, K, description)
    "funnel_plain": (1.0, -0.25, 0.15, "Windsock funnel, open exit in the sock's wake"),
    "funnel_wind_lens": (1 / 3, -0.8, 0.30, "Funnel + 3:1 flanged diffuser ('wind lens'), best plausible"),
    "funnel_heroic": (1 / 4, -1.2, 0.20, "Heroic: 4:1 diffuser w/ BL suction + very low base pressure"),
}


def concentrator_power(V, dt_over_d, scen, cap=None):
    eps, cpb, K, _ = SCENARIOS[scen]
    cp_t, _ = throat_cp(eps, cpb, K)
    At = A * dt_over_d**2
    P = cp_t * q(V) * V * At
    return min(P, cap) if cap else P


def hawt_power(V, cp=0.45):
    if V < 3 or V > 25:
        return 0.0
    return min(cp * q(V) * V * A, P_RATED)


SOCK_CD = 1.35   # a closed cone/cup facing the wind: parachute-like (concave hemisphere 1.42)


def sock_drag(V):
    return SOCK_CD * q(V) * A


def hawt_thrust(V):
    if V <= V_RATED:
        return 0.80 * q(V) * A
    # pitch-regulated: thrust falls ~ like rated thrust * (V_r/V)
    return 0.80 * q(V_RATED) * A * (V_RATED / V) ** 1.0


# ---------------------------------------------------------------- crosswind kite
def loyd(Ak, V, CL=1.0, LD=5.0, beta_deg=28.0, eta=1.0):
    """Loyd (1980) crosswind power with optimal reel-out (V/3), elevation cos^3, cycle eff."""
    b = math.radians(beta_deg)
    return (4 / 27) * q(V) * V * Ak * CL * LD**2 * math.cos(b) ** 3 * eta


def shear(V_hub, z, alpha=0.14):
    return V_hub * (z / HUB) ** alpha


KITE = dict(CL=1.0, LD_soft=5.5, LD_rigid=10.0, beta=28.0, eta_cycle=0.62, z_op=250.0,
            tether_len=650.0)


def kite_area_for(P, V_hub=V_RATED, LD=KITE["LD_soft"]):
    Vz = shear(V_hub, KITE["z_op"])
    p1 = loyd(1.0, Vz, KITE["CL"], LD, KITE["beta"], KITE["eta_cycle"])
    return P / p1


def kite_tether(P, V_hub=V_RATED):
    Vz = shear(V_hub, KITE["z_op"]) * math.cos(math.radians(KITE["beta"]))
    v_reel = Vz / 3
    T = P / KITE["eta_cycle"] / v_reel * 0.8         # reel-out tension (reel-out power ~ P/eta)
    sigma_allow = 3.5e9 / 3.0                         # Dyneema SK78 ~3.5 GPa, SF 3 (fatigue/creep)
    Area = T / sigma_allow
    dia = math.sqrt(4 * Area / math.pi) / 0.75       # braid fill factor ~0.56 -> /0.75 on dia
    mass = Area / 0.56 * 0.56 * 975 * KITE["tether_len"]   # fibre mass (kg)
    return dict(T=T, v_reel=v_reel, dia_mm=dia * 1e3, mass_kg=mass)


# ---------------------------------------------------------------- energy
def aep(power_fn, vmean=7.5, k=2.0):
    """Annual energy (kWh) for a Weibull wind at hub with mean vmean."""
    c = vmean / math.gamma(1 + 1 / k)
    Vs = np.linspace(0.25, 30, 240)
    pdf = (k / c) * (Vs / c) ** (k - 1) * np.exp(-(Vs / c) ** k)
    P = np.array([power_fn(v) for v in Vs])
    return float(np.trapezoid(P * pdf, Vs) * 8766 / 1e3)


def crf(r=0.07, n=25):
    return r * (1 + r) ** n / ((1 + r) ** n - 1)


# ---------------------------------------------------------------- BOM
def load_json(path, default):
    try:
        with open(path) as fh:
            return json.load(fh)
    except FileNotFoundError:
        return default


def bom_hawt():
    capex = 1500 * 5000                 # $/kW installed, NREL Cost of Wind Energy Review range
    turbine = 0.65 * capex
    items = [
        ("Blades (3 x 61.5 m, ~17.7 t each)", 0.22 * turbine),
        ("Tower (tubular steel, ~350 t)", 0.26 * turbine),
        ("Nacelle: gearbox, generator, converter, bearings, yaw, pitch", 0.52 * turbine),
        ("Foundation", 0.10 * capex),
        ("Balance of system: roads, electrical, install, soft costs", 0.25 * capex),
    ]
    opex = 43 * 5000                    # $/kW-yr (NREL 2023 reference)
    return items, opex


def bom_windsock(dt_over_d, scen, fea_m, fea_f):
    R, r = D / 2, D / 2 * dt_over_d
    L = fea_m.get("L", D)
    slant = math.hypot(L, R - r)
    fabric_area = math.pi * (R + r) * slant * 1.08          # +8% seams/reinforcement
    grade = fea_m.get("fabric_grade", "PVC-polyester Type IV")
    fab_cost = fea_m.get("fabric_cost_m2", 32.0)
    ring_t = fea_f.get("ring_mass_t", 600.0)
    spoke_t = fea_f.get("spoke_mass_t", 250.0)
    tower_t = fea_f.get("tower_mass_t", 900.0)
    M_ratio = fea_f.get("base_moment_ratio_vs_hawt", 2.0)
    At = A * dt_over_d**2
    cp_t, _ = throat_cp(*SCENARIOS[scen][:3])
    P_gen = cp_t * q(V_RATED) * V_RATED * At
    turb_cost = (2500 if P_gen < 20e3 else 1100) * P_gen / 1e3 + 5000
    items = [
        (f"Membrane cone, {grade}, {fabric_area:,.0f} m2 fabricated", fabric_area * fab_cost),
        (f"Mouth ring, steel tube space-frame, {ring_t:,.0f} t @ $4.5k/t", ring_t * 4500),
        (f"Axial boom, 2 spoke hubs, 96 Dyneema spokes, rear yaw mast: {spoke_t:,.0f} t @ $4.5k/t", spoke_t * 4500),
        (f"Tower (larger: drag-driven), {tower_t:,.0f} t @ $4.0k/t", tower_t * 4000),
        (f"Foundation (scaled x{M_ratio:.1f} by overturning moment)", 0.10 * 1500 * 5000 * M_ratio),
        ("Yaw: front pivot bearing + 126 m-radius rear rail track & bogie", 1_200_000),
        ("Furling / reefing system (winches, battens, controls)", 350_000),
        (f"Throat turbine + generator ({P_gen/1e3:,.1f} kW, {2*r:.2f} m rotor)", turb_cost),
        ("Install, cranes, electrical, soft costs", 0.25 * 1500 * 5000 * 0.8),
    ]
    opex = 25_000 + 0.03 * fabric_area * fab_cost          # fabric replacement every ~12-15 yrs
    return items, opex, P_gen, fabric_area


def bom_kite(P=5e6, LD=KITE["LD_soft"]):
    Ak = kite_area_for(P, LD=LD)
    t = kite_tether(P)
    items = [
        (f"Soft ram-air/LEI 'spinnaker' kite, {Ak:,.0f} m2 (Dyneema-reinforced laminate) @ $140/m2", Ak * 140),
        ("Kite control pod (steering winches, avionics, power)", 250_000),
        (f"Tether, Dyneema SK78, {t['dia_mm']:.0f} mm x {KITE['tether_len']:.0f} m ({t['mass_kg']/1e3:.1f} t) @ $60/kg", t["mass_kg"] * 60),
        ("Ground station drum-winch + 5 MW generator + converter", 330 * 5000),
        ("Storage for reel-in phase (1 MWh Li-ion)", 300_000),
        ("Launch & land mast / mobile platform", 400_000),
        ("Foundation / ground anchor (tension only)", 250_000),
        ("Balance of system: electrical, install, soft costs", 0.25 * 1500 * 5000 * 0.6),
    ]
    # kite replaced every ~2 yr, tether every ~1 yr, plus O&M
    opex = Ak * 140 / 2 + t["mass_kg"] * 60 / 1.0 + 120_000
    return items, opex, Ak, t


def summarize(items, opex, aep_kwh):
    capex = sum(c for _, c in items)
    lcoe = (capex * crf() + opex) / max(aep_kwh, 1e-9) * 1000
    return dict(capex=capex, opex=opex, aep_kwh=aep_kwh, lcoe_usd_mwh=lcoe)


def main():
    os.makedirs("out", exist_ok=True)
    fea_m = load_json("out/fea_membrane.json", {})
    fea_f = load_json("out/fea_frame.json", {})
    res = {"inputs": dict(D=D, A=A, hub=HUB, V_rated=V_RATED, P_rated=P_RATED)}

    # 1) concentrator throat Cp for each scenario
    res["scenarios"] = {}
    for k, (eps, cpb, K, desc) in SCENARIOS.items():
        cp_t, u = throat_cp(eps, cpb, K)
        res["scenarios"][k] = dict(desc=desc, eps=eps, cpb=cpb, K=K, cp_throat=cp_t, u_throat=u,
                                   augmentation_vs_bare_rotor_same_size=cp_t / 0.45)

    # 2) sweep throat size: fraction of HAWT power
    ratios = np.geomspace(0.01, 1.0, 60)
    res["sweep"] = {"dt_over_d": ratios.tolist()}
    for k in SCENARIOS:
        res["sweep"][k] = [concentrator_power(V_RATED, x, k) / hawt_power(V_RATED) for x in ratios]
    res["sweep"]["user_hypothesis"] = [1.0 for _ in ratios]

    # 3) loads
    Vs = np.linspace(3, 50, 48)
    res["loads"] = dict(V=Vs.tolist(), sock_drag_MN=[sock_drag(v) / 1e6 for v in Vs],
                        hawt_thrust_MN=[hawt_thrust(v) / 1e6 if v <= 25 else 0.12 * q(v) * A * 0.03 / 1e6 * 10 for v in Vs])

    # 4) the punchline numbers at rated wind for the user's d/100 design
    for x in (0.01, 0.1):
        for k in SCENARIOS:
            res.setdefault("punch", {})[f"{k}@{x}"] = dict(
                P_kW=concentrator_power(V_RATED, x, k) / 1e3,
                frac_of_hawt=concentrator_power(V_RATED, x, k) / P_RATED,
                mdot_through_turbine_frac_of_mouth=throat_cp(*SCENARIOS[k][:3])[1] * x**2)

    # 5) kite
    res["kite"] = dict(
        area_soft_m2=kite_area_for(P_RATED, LD=KITE["LD_soft"]),
        area_rigid_m2=kite_area_for(P_RATED, LD=KITE["LD_rigid"]),
        tether=kite_tether(P_RATED), params=KITE,
        power_per_m2_soft_kW=loyd(1, shear(V_RATED, KITE["z_op"]), 1, KITE["LD_soft"], KITE["beta"], KITE["eta_cycle"]) / 1e3,
        power_per_m2_drag_sock_kW=(4 / 27) * SOCK_CD * q(V_RATED) * V_RATED / 1e3,
        hawt_power_per_m2_swept_kW=hawt_power(V_RATED) / A / 1e3,
        hawt_blade_area_m2=3 * 61.5 * 2.6,   # mean chord ~2.6 m
    )

    # 6) BOM + LCOE
    items, opex = bom_hawt()
    res["bom"] = {"HAWT 5 MW (reference)": dict(items=items, **summarize(items, opex, aep(hawt_power)))}
    for x, label in ((0.01, "Windsock d -> d/100 (your spec)"), (0.1, "Windsock d -> d/10 ('100x area')")):
        for scen in ("funnel_wind_lens",):
            items, opex, Pg, fab = bom_windsock(x, scen, fea_m, fea_f)
            fn = lambda v, x=x, scen=scen, Pg=Pg: 0.0 if v < 3 or v > 15 else concentrator_power(v, x, scen, cap=Pg)   # furled above 15 m/s (membrane FEA)
            res["bom"][label] = dict(items=items, P_rated_kW=Pg / 1e3, **summarize(items, opex, aep(fn)))
    items, opex, Ak, t = bom_kite()
    vfac = (KITE["z_op"] / HUB) ** 0.14
    fnk = lambda v: 0.0 if v * vfac < 4 or v * vfac > 28 else min(
        loyd(Ak, v * vfac, 1, KITE["LD_soft"], KITE["beta"], KITE["eta_cycle"]), P_RATED)
    res["bom"]["Crosswind spinnaker kite 5 MW"] = dict(items=items, kite_area=Ak, **summarize(items, opex, aep(fnk) * 0.93))
    for k, v in res["bom"].items():
        v["capex_per_kW"] = v["capex"] / (v.get("P_rated_kW", 5000))

    with open("out/models.json", "w") as fh:
        json.dump(res, fh, indent=1, default=float)
    # print a digest
    for k, s in res["scenarios"].items():
        print(f"{k:18s} Cp_throat={s['cp_throat']:.3f}  u_t/V={s['u_throat']:.2f}  aug={s['augmentation_vs_bare_rotor_same_size']:.2f}x")
    for k, s in res["punch"].items():
        print(f"{k:24s} P={s['P_kW']:9.1f} kW  frac={s['frac_of_hawt']:.5f}")
    print("kite", {k: v for k, v in res["kite"].items() if k != "params"})
    for k, v in res["bom"].items():
        print(f"{k:36s} capex=${v['capex']/1e6:6.2f}M  AEP={v['aep_kwh']/1e6:7.3f} GWh  LCOE=${v['lcoe_usd_mwh']:,.0f}/MWh  $/kW={v['capex_per_kW']:,.0f}")


if __name__ == "__main__":
    main()
