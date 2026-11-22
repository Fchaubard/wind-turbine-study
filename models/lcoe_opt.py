"""Global LCOE search: which wind-powered machine gives the lowest cost per MWh over life?

Four architectures, each with its design variables set free and chosen by a global optimiser
(scipy differential evolution) to minimise LCOE under the SAME finance (7 % WACC, 25 yr) and SAME site:
  hawt     conventional turbine: rated power, rotor diameter and hub height free (low specific power, tall tower)
  ring     fly-gen rotary kite ring (section 7 rotor, no shaft): unit size, altitude, elevation angle, rated wind,
           number of stacked rotors (spaced 1.5 D apart along the tether, 10 % wake loss per rotor downstream),
           wings per rotor and annulus width free
  flywing  fly-gen single rigid wing (Makani-type), Loyd drag mode with tether drag solved self-consistently
  pump     pumping kite (rigid or soft wing), Loyd lift mode with reel-in losses and 2x generator rating
Two sites: onshore 7.5 m/s at 90 m (the study's reference) and a floating-offshore site, 9.5 m/s at 100 m,
plus a sweep of onshore site wind (6 to 10.5 m/s) for the ring and the turbine.
Everything is concept-level (±30-40 %); the point is the ranking and where the money goes.
"""
import json, math, functools, copy, time
import numpy as np
from scipy.optimize import differential_evolution
import rotary as RT

RHO, G = 1.225, 9.81
DYN = dict(sig=3.5e9, rho=975, cost_kg=60.0)
SITES = {
    "onshore": dict(vmean=7.5, k=2.0, zref=90.0, alpha=0.14, offshore=False, label="Onshore, 7.5 m/s mean at 90 m"),
    "offshore": dict(vmean=9.5, k=2.2, zref=100.0, alpha=0.10, offshore=True, label="Floating offshore, 9.5 m/s mean at 100 m"),
}
FIN = dict(r=0.07, n=25)
AVAIL = dict(hawt=1.0, awe=0.92)      # the 5 MW reference already runs at CF 38 % with no availability factor; AWE gets 92 %
WINGS = dict(
    semi=dict(name="semi-rigid wing", cost=150.0, life=5.0, kg=1.6, LD=8.9, AR=7.0),
    rigid=dict(name="rigid composite wing", cost=1800.0, life=20.0, kg=25.0, LD=12.0, AR=12.0),
    soft=dict(name="soft kite", cost=150.0, life=3.0, kg=1.0, LD=5.5, AR=5.0),
)
DRIVE = dict(onwing=620.0, ground_fg=80.0, pump_gen=330.0, pump_store=60.0, tether_life=5.0, pump_tether_life=3.0)
AWE_SITE = dict(onshore=dict(floater_kW=0.0, found=(30_000, 25.0), bos_kW=250.0, opex_kW=0.0, fixed=8_000.0),
                offshore=dict(floater_kW=500.0, found=None, bos_kW=900.0, opex_kW=60.0, fixed=20_000.0))
OM = dict(frac=0.02)                  # generic O&M as a fraction of capex per year (AWE)
RING = dict(AR=7.0, CD0=0.025, CDt=0.03, eta=0.78, lifter_frac=0.15, spacing_D=1.5, wake=0.90)
N_OPTS = (6, 8, 10, 12)
BR_OPTS = (0.25, 0.30, 0.35, 0.40)
VS = np.linspace(0.25, 32, 256)


def crf():
    r, n = FIN["r"], FIN["n"]
    return r * (1 + r) ** n / ((1 + r) ** n - 1)


def weibull_pdf(site):
    k = site["k"]; c = site["vmean"] / math.gamma(1 + 1 / k)
    return (k / c) * (VS / c) ** (k - 1) * np.exp(-(VS / c) ** k)


def aep_kwh(site, Pv):
    return float(np.trapezoid(Pv * weibull_pdf(site), VS) * 8766 / 1e3)


def shear(site, v, z):
    return v * (z / site["zref"]) ** site["alpha"]


def finance(items, opex, aep, P):
    capex = sum(v for _, v in items)
    cf = aep / (P / 1e3 * 8766)
    return dict(items=items, capex=capex, opex=opex, aep_kwh=aep, cf=cf, capex_per_MW=capex / (P / 1e6),
                capex_per_avgMW=capex / (P / 1e6 * max(cf, 1e-9)), lcoe=(capex * crf() + opex) / max(aep, 1.0) * 1000)


def tether(F_peak, L, P_el=0.0, U_kV=25.0, J=1.5e6, sf=3.0):
    """Dyneema core at SF 3 on break for the dynamic peak load; optional aluminium conductors (2, at J A/m², U kV)."""
    A_s = F_peak * sf / DYN["sig"]
    m_s = A_s * DYN["rho"]
    A_al = 2 * (P_el / (0.95 * U_kV * 1e3)) / J if P_el > 0 else 0.0
    m_al = A_al * 2700
    A_tot = 1.1 * A_s + 1.8 * A_al                       # jacket; conductor insulation
    d = math.sqrt(4 * A_tot / math.pi)
    cost_m = (m_s * DYN["cost_kg"] + m_al * 4.0 + 20.0) * 2.2   # manufacturing, jacket, terminations
    return dict(d=d, kg_m=1.3 * m_s + m_al, cost_m=cost_m, cost=cost_m * L + 30_000)


# ============================================================ 1. HAWT with free P, D, H
def hawt(site, x, wing=None, detail=False):
    P_MW, D, H = x
    P = P_MW * 1e6; A = math.pi * D**2 / 4
    s, dD, dH = P / 5e6, D / 126, H / 90
    off = site["offshore"]
    blades = 1.0725e6 * dD**2.3                              # blade mass ~ D^2.3 (Fingersh 2006 advanced blade)
    tower = 1.2675e6 * dD**2 * dH                            # NREL: tower mass ~ swept area × hub height
    nacelle = 2.535e6 * (0.6 * s + 0.4 * s * dD)             # gearbox + generator ~ torque ~ P·D
    if off:
        found = 2000.0 * P / 1e3 * (0.5 + 0.5 * (dD**2 * dH / s) ** 0.6)   # floater + mooring: half per kW, half by overturning moment
        bos = 1500.0 * P / 1e3 * (0.7 + 0.3 * s ** -0.4)                    # array + export cable, substation, heavy-lift install
        opex = 90.0 * P / 1e3 * (0.7 + 0.3 * s ** -0.4)
    else:
        found = 0.75e6 * (dD**2 * dH) ** 0.4                 # NREL: foundation ~ (A·H)^0.40
        bos = 1.875e6 * (0.75 * s + 0.25 * (dD * dH) ** 1.17)   # electrical ~ P; assembly & install ~ (H·D)^1.17
        opex = 215e3 * (0.7 * s + 0.3 * s ** 0.6)            # part per kW, part per turbine
    items = [(f"Blades (3 × {D/2:.0f} m)", blades), (f"Tower ({H:.0f} m hub)", tower),
             (f"Nacelle: gearbox, generator, converter ({P/1e6:.1f} MW)", nacelle),
             ("Floating platform + mooring" if off else "Foundation", found), ("Balance of system", bos)]
    V = shear(site, VS, H)
    Pv = np.where((V >= 3) & (V <= 25), np.minimum(0.45 * 0.5 * RHO * V**3 * A, P), 0.0)
    f = finance(items, opex, aep_kwh(site, Pv) * AVAIL["hawt"], P)
    pen = max(0.0, (D / 2 + 25) - H) / 10 + max(0.0, D - 260) / 10
    f.update(obj=f["lcoe"] + 1e3 * pen, x=list(map(float, x)), P_MW=P_MW, specific_power=P / A, D=D, H=H,
             label=f"{P_MW:.1f} MW, {D:.0f} m rotor ({P/A:.0f} W/m²), {H:.0f} m hub")
    return f


# ============================================================ 2. fly-gen rotary ring
@functools.lru_cache(maxsize=None)
def ring_bem(beta_deg, LD, N, bR):
    R = 50.0; b = bR * R; c = b / RING["AR"]
    cd0 = RING["CD0"] * (8.9 / LD)                            # scale profile drag with the wing's L/D
    geo = dict(N=N, R=R, b=b, S=b * c, AR=RING["AR"], CD0=cd0, CDt=RING["CDt"])
    rb = RT.best_rotor(geo, math.radians(beta_deg))
    return float(rb["cp_on_V"]), float(rb["ct_on_Vn"]), float(rb["lam"])


def airborne_common(site, P, h, beta, wing, S_tot, span, F_ax, L_t, th, thrust_ci_frac, v_ci, m_extra=0.0):
    """airborne mass and the crosswind lift kite that holds it up at cut-in"""
    W = WINGS[wing]
    kg = W["kg"] * (span / 20) ** 0.5
    m_air = S_tot * kg + 1.5 * P / 1e3 + 0.5 * th["kg_m"] * L_t + m_extra
    q_ci = 0.5 * RHO * v_ci**2
    need = max(0.0, 1.3 * m_air * G - thrust_ci_frac)
    S_lift = max(need / (q_ci * 1.2 * 4.0), 0.03 * S_tot)
    return kg, m_air, S_lift


def ring(site, x, wing="semi", detail=False):
    P_MW, h, beta_deg, Vr, st, nc, bc = x
    st = int(round(st)); N = N_OPTS[int(round(nc)) - 1]; bR = BR_OPTS[int(round(bc)) - 1]
    P = P_MW * 1e6; beta = math.radians(beta_deg); W = WINGS[wing]
    cp, ct, lam = ring_bem(int(round(beta_deg)), W["LD"], N, bR)
    wk = RING["wake"]
    S_p = sum(wk ** k for k in range(st)); S_t = sum(wk ** (2 * k / 3) for k in range(st))   # downstream rotors see slower air
    cpe = cp * RING["eta"] * S_p                               # electrical Cp of the whole stack on one annulus area
    A = P / (cpe * 0.5 * RHO * Vr**3)
    R = math.sqrt(A / (2 * math.pi * bR)); b = bR * R; c = b / RING["AR"]
    Vn = Vr * math.cos(beta); Om = lam * Vn / R; tip = Om * (R + b / 2)
    thrust = ct * 0.5 * RHO * Vn**2 * A * S_t; F_ax = thrust * (1 + RING["lifter_frac"])
    L_main = h / math.sin(beta); L_sp = (st - 1) * RING["spacing_D"] * 2 * R
    U = min(66.0, max(20.0, 25.0 * math.sqrt(P_MW / 5)))
    th = tether(F_ax * 1.4, L_main, P_el=P, U_kV=U)
    seg_cost = seg_mass = 0.0                                  # tether between stacked rotors: carries only the rotors above it
    for k in range(1, st):
        frac = (st - k) / st
        tk = tether(F_ax * 1.4 * frac, RING["spacing_D"] * 2 * R, P_el=P * frac, U_kV=U)
        seg_cost += tk["cost"] - 30_000; seg_mass += tk["kg_m"] * RING["spacing_D"] * 2 * R
    L_t = L_main + L_sp; teth_cost = th["cost"] + seg_cost
    h_mean = h + 0.5 * L_sp * math.sin(beta); h_top = h + L_sp * math.sin(beta)
    D_t = 0.5 * RHO * Vr**2 * th["d"] * L_main * math.cos(beta) ** 2       # tether drag -> sag -> steeper effective angle
    sag = (math.cos(beta + math.atan(D_t / (2 * F_ax))) / math.cos(beta)) ** 3
    S_tot = N * b * c * st
    v_wing = math.hypot(Om * R, Vn)                                      # wing airspeed at rated: sets on-wing turbine size
    A_turb = P / (RING["eta"] * 0.5 * RHO * v_wing**3 * 0.40)             # on-wing turbine disc area (C_P 0.40)
    v_ci = 5.0 if wing == "rigid" else 4.0
    kg, m_air, S_lift = airborne_common(site, P, h, beta, wing, S_tot, b, F_ax, L_main, th, thrust * (v_ci / Vr) ** 2 * math.sin(beta), v_ci,
                                        m_extra=12.0 * A_turb + seg_mass)
    cost_m2 = W["cost"] * (b / 20) ** 0.3
    sc = AWE_SITE["offshore" if site["offshore"] else "onshore"]
    items = [
        (f"{N}×{st} {W['name']}s, {S_tot:,.0f} m² (span {b:.0f} m) @ ${cost_m2:,.0f}/m²", S_tot * cost_m2),
        (f"On-wing turbines ({A_turb:,.0f} m² of disc at {v_wing:.0f} m/s airspeed), generators, HV converters ({P/1e3:,.0f} kW)", DRIVE["onwing"] * P / 1e3 + 250.0 * A_turb),
        (f"Conductive tether {L_t:,.0f} m (Ø{th['d']*1e3:.0f} mm main, {U:.0f} kV)" + (f", {st} rotors spaced {RING['spacing_D']*2*R:,.0f} m" if st > 1 else ""), teth_cost),
        (f"Crosswind lift kite {S_lift:,.0f} m²", S_lift * 120 + 15_000),
        ("Ground: HV converter + grid connection", DRIVE["ground_fg"] * P / 1e3),
        ("Launch/land mast, yaw platform, controls", 150_000 + 65 * P / 1e3),
        ("Floating buoy + mooring (tension only)" if site["offshore"] else "Foundation / anchor (tension only)",
         sc["floater_kW"] * P / 1e3 if site["offshore"] else sc["found"][0] + sc["found"][1] * P / 1e3),
        ("Balance of system", sc["bos_kW"] * P / 1e3),
    ]
    capex = sum(v for _, v in items)
    opex = S_tot * cost_m2 / W["life"] + teth_cost / DRIVE["tether_life"] + OM["frac"] * capex + sc["fixed"] + sc["opex_kW"] * P / 1e3
    V = shear(site, VS, h_mean)
    Pv = np.where((V >= v_ci) & (V <= 28) & (VS <= 30), np.minimum(cpe * sag * 0.5 * RHO * V**3 * A, P), 0.0)
    f = finance(items, opex, aep_kwh(site, Pv) * AVAIL["awe"], P)
    pen = max(0.0, tip - 90) / 10 + max(0.0, b - 60) / 10 + max(0.0, R - 160) / 20 + max(0.0, th["d"] - 0.12) * 100 + max(0.0, h_top - 1100) / 50
    f.update(obj=f["lcoe"] + 1e3 * pen, x=list(map(float, x)), P_MW=P_MW, h=h_mean, h_low=h, h_top=h_top, L_t=L_t, R=R, span=b, S=S_tot, tip=tip,
             tether_d=th["d"], cp=cp, sag=sag, rpm=Om * 60 / 2 / math.pi, stack=st, N=N, bR=bR, v_wing=v_wing, A_turb=A_turb, U_kV=U,
             label=f"{P_MW:.1f} MW, {N}×{st} wings {b:.0f} m span on a {2*R:.0f} m ring" + (f", rotors {h:.0f}–{h_top:.0f} m" if st > 1 else f" at {h:.0f} m") + f", {beta_deg:.0f}° tether, rated at {Vr:.1f} m/s")
    return f


# ============================================================ 3. fly-gen rigid wing (Makani-type), Loyd drag mode
def loyd_solve(site, P, h, beta, W, eta, conductive, cycle=1.0):
    """Wing area S and tether for rated power P at rotor wind Vr, with tether drag solved self-consistently.
    Returns (S, LDe, va, F, th, k, L_t) where k·V³·S is electrical power at wind V."""
    CL = 1.0; CDw = 1.0 / W["LD"]
    L_t = h / math.sin(beta)
    S, d_t = 200.0, 0.03
    for _ in range(40):
        CDt = 0.25 * 1.0 * d_t * L_t / S
        LDe = CL / (CDw + CDt)
        k = cycle * eta * (2 / 27) * RHO * CL * LDe**2 * math.cos(beta) ** 3
        S_new = P / (k * loyd_solve.Vr**3)
        va = (2 / 3) * LDe * loyd_solve.Vr * math.cos(beta)
        F = 0.5 * RHO * va**2 * S_new * CL * 1.05
        th = tether(F * 1.3, L_t, P_el=P if conductive else 0.0)
        d_t = th["d"]
        if abs(S_new / S - 1) < 1e-6:
            S = S_new; break
        S = S_new
    return S, LDe, va, F, th, k, L_t


def flywing(site, x, wing="rigid", detail=False):
    P_MW, h, beta_deg, Vr = x
    P = P_MW * 1e6; beta = math.radians(beta_deg); W = WINGS[wing]
    loyd_solve.Vr = Vr
    S, LDe, va, F, th, k, L_t = loyd_solve(site, P, h, beta, W, eta=0.80, conductive=True)
    span = math.sqrt(S * W["AR"])
    v_ci = 5.0 if wing == "rigid" else 4.0
    kg, m_air, S_lift = airborne_common(site, P, h, beta, wing, S, span, F, L_t, th, F * (v_ci / Vr) ** 2 * math.sin(beta), v_ci)
    cost_m2 = W["cost"] * (span / 30) ** 0.3
    sc = AWE_SITE["offshore" if site["offshore"] else "onshore"]
    items = [
        (f"{W['name']} {S:,.0f} m², span {span:.0f} m, L/D {LDe:.1f} with tether @ ${cost_m2:,.0f}/m²", S * cost_m2),
        (f"On-wing turbines, generators, HV converters ({P/1e3:,.0f} kW)", DRIVE["onwing"] * P / 1e3),
        (f"Conductive tether {L_t:,.0f} m, Ø{th['d']*1e3:.0f} mm", th["cost"]),
        ("Ground: HV converter + grid connection", DRIVE["ground_fg"] * P / 1e3),
        ("Perch / launch-land tower, controls", 200_000 + 40 * P / 1e3),
        ("Floating buoy + mooring (tension only)" if site["offshore"] else "Foundation / anchor (tension only)",
         sc["floater_kW"] * P / 1e3 if site["offshore"] else sc["found"][0] + sc["found"][1] * P / 1e3),
        ("Balance of system", sc["bos_kW"] * P / 1e3),
    ]
    capex = sum(v for _, v in items)
    opex = S * cost_m2 / W["life"] + th["cost"] / DRIVE["tether_life"] + OM["frac"] * capex + sc["fixed"] + sc["opex_kW"] * P / 1e3
    V = shear(site, VS, h)
    Pv = np.where((V >= v_ci) & (V <= 25) & (VS <= 30), np.minimum(k * V**3 * S, P), 0.0)
    f = finance(items, opex, aep_kwh(site, Pv) * AVAIL["awe"], P)
    pen = max(0.0, span - 120) / 10 + max(0.0, va - 80) / 5 + max(0.0, th["d"] - 0.12) * 100
    f.update(obj=f["lcoe"] + 1e3 * pen, x=list(map(float, x)), P_MW=P_MW, h=h, L_t=L_t, S=S, span=span, va=va, LDe=LDe,
             tether_d=th["d"], label=f"{P_MW:.1f} MW, {S:,.0f} m² wing ({span:.0f} m span) at {h:.0f} m, {beta_deg:.0f}° tether, rated at {Vr:.1f} m/s, flies at {va:.0f} m/s")
    return f


# ============================================================ 4. pumping kite, Loyd lift mode
def pump(site, x, wing="rigid", detail=False):
    P_MW, h, beta_deg, Vr = x
    P = P_MW * 1e6; beta = math.radians(beta_deg); W = WINGS[wing]
    loyd_solve.Vr = Vr
    cyc = 0.55                                                     # net cycle: reel-in energy and time, rigid/fast reel-in
    S, LDe, va, F, th, k, L_t = loyd_solve(site, P, h, beta, W, eta=0.90, conductive=False, cycle=cyc)
    span = math.sqrt(S * W["AR"])
    v_ci = 5.0 if wing == "rigid" else 4.0
    kg, m_air, S_lift = airborne_common(site, P, h, beta, wing, S, span, F, L_t, th, F * (v_ci / Vr) ** 2 * math.sin(beta), v_ci)
    cost_m2 = W["cost"] * (span / 30) ** 0.3
    P_gen = P / cyc * 1.1                                          # reel-out peak the winch generator must be rated for
    sc = AWE_SITE["offshore" if site["offshore"] else "onshore"]
    items = [
        (f"{W['name']} {S:,.0f} m², span {span:.0f} m, L/D {LDe:.1f} with tether @ ${cost_m2:,.0f}/m²", S * cost_m2),
        (f"Tether {L_t:,.0f} m, Ø{th['d']*1e3:.0f} mm", th["cost"]),
        (f"Ground station: drum winch, generator rated {P_gen/1e3:,.0f} kW (reel-out peak), converter", DRIVE["pump_gen"] * P_gen / 1e3),
        ("Reel-in storage (supercap / battery)", DRIVE["pump_store"] * P / 1e3),
        ("Kite control pod / launch-land mast", 150_000 + 40 * P / 1e3),
        ("Floating buoy + mooring (tension only)" if site["offshore"] else "Foundation / anchor (tension only)",
         sc["floater_kW"] * P / 1e3 if site["offshore"] else sc["found"][0] + sc["found"][1] * P / 1e3),
        ("Balance of system", sc["bos_kW"] * P / 1e3),
    ]
    capex = sum(v for _, v in items)
    opex = S * cost_m2 / W["life"] + th["cost"] / DRIVE["pump_tether_life"] + OM["frac"] * capex + sc["fixed"] + sc["opex_kW"] * P / 1e3
    V = shear(site, VS, h)
    Pv = np.where((V >= v_ci) & (V <= 25) & (VS <= 30), np.minimum(k * V**3 * S, P), 0.0)
    f = finance(items, opex, aep_kwh(site, Pv) * AVAIL["awe"], P)
    pen = max(0.0, span - 120) / 10 + max(0.0, va - 80) / 5 + max(0.0, th["d"] - 0.12) * 100
    f.update(obj=f["lcoe"] + 1e3 * pen, x=list(map(float, x)), P_MW=P_MW, h=h, L_t=L_t, S=S, span=span, va=va, LDe=LDe,
             tether_d=th["d"], label=f"{P_MW:.1f} MW avg, {S:,.0f} m² wing ({span:.0f} m span) at {h:.0f} m, {beta_deg:.0f}° tether, rated at {Vr:.1f} m/s")
    return f


ARCH = dict(hawt=hawt, ring=ring, flywing=flywing, pump=pump)
BOUNDS = dict(hawt=[(2, 20), (100, 260), (80, 220)],
              ring=[(1, 40), (150, 1000), (15, 35), (7, 16), (0.5, 6.49), (0.5, 4.49), (0.5, 4.49)],
              flywing=[(1, 25), (150, 1000), (15, 35), (8, 16)],
              pump=[(1, 25), (150, 1000), (15, 35), (8, 16)])
CASES = [("hawt", None, "Conventional turbine, LCOE-optimised (rotor, hub height, rating free)"),
         ("ring", "semi", "Fly-gen rotary kite ring, semi-rigid wings"),
         ("ring", "rigid", "Fly-gen rotary kite ring, rigid wings"),
         ("flywing", "rigid", "Fly-gen rigid wing (Makani-type)"),
         ("pump", "rigid", "Pumping kite, rigid wing"),
         ("pump", "soft", "Pumping kite, soft kite")]


def optimise(site, arch, wing, seed=1, maxiter=150, popsize=20):
    fn = ARCH[arch]
    res = differential_evolution(lambda x: fn(site, x, wing)["obj"], BOUNDS[arch], seed=seed, maxiter=maxiter,
                                 popsize=popsize, tol=1e-7, polish=True)
    out = fn(site, res.x, wing, detail=True)
    out.update(arch=arch, wing=wing, site_label=site["label"])
    return out


def snapshot():
    return copy.deepcopy((WINGS, DRIVE, FIN, AVAIL, SITES, AWE_SITE, DYN, OM))


def restore(snap):
    for d, s in zip((WINGS, DRIVE, FIN, AVAIL, SITES, AWE_SITE, DYN, OM), snap):
        d.clear(); d.update(s)


def sensitivities(best):
    """One-at-a-time re-evaluation of the winning design (same geometry, same site unless noted)."""
    site = SITES[best["site"]]; fn = ARCH[best["arch"]]; x = best["x"]; w = best["wing"]
    base = fn(site, x, w)["lcoe"]
    rows = []
    def ev(name, lo_set, hi_set):
        vals = []
        for setter in (lo_set, hi_set):
            snap = snapshot(); setter()
            vals.append(fn(SITES[best["site"]], x, w)["lcoe"])
            restore(snap)
        rows.append(dict(name=name, lo=vals[0], hi=vals[1]))
    def setw(k, f): WINGS[w][k] = WINGS[w][k] * f
    ev("Wing cost ×0.5 / ×2", lambda: setw("cost", 0.5), lambda: setw("cost", 2.0))
    ev("Wing life ×1.5 / ×0.5", lambda: setw("life", 1.5), lambda: setw("life", 0.5))
    if best["arch"] in ("ring", "flywing"):
        ev("On-wing drive $400 / $900 per kW", lambda: DRIVE.update(onwing=400.0), lambda: DRIVE.update(onwing=900.0))
    else:
        ev("Winch generator $250 / $450 per kW", lambda: DRIVE.update(pump_gen=250.0), lambda: DRIVE.update(pump_gen=450.0))
    ev("Tether cost ×0.5 / ×2", lambda: DYN.update(cost_kg=30.0), lambda: DYN.update(cost_kg=120.0))
    ev("Tether life 8 yr / 3 yr", lambda: DRIVE.update(tether_life=8.0, pump_tether_life=5.0), lambda: DRIVE.update(tether_life=3.0, pump_tether_life=2.0))
    if best["arch"] == "ring":
        ev("Stacked-rotor wake loss 5 % / 15 % per rotor", lambda: RING.update(wake=0.95), lambda: RING.update(wake=0.85))
        RING["wake"] = 0.90
    ev("Wind shear exponent 0.20 / 0.10", lambda: SITES[best["site"]].update(alpha=0.20), lambda: SITES[best["site"]].update(alpha=0.10))
    ev("Site mean wind +1 / −1 m/s", lambda: SITES[best["site"]].update(vmean=SITES[best["site"]]["vmean"] + 1), lambda: SITES[best["site"]].update(vmean=SITES[best["site"]]["vmean"] - 1))
    ev("Availability 97 % / 85 %", lambda: AVAIL.update(awe=0.97), lambda: AVAIL.update(awe=0.85))
    ev("WACC 5 % / 9 %", lambda: FIN.update(r=0.05), lambda: FIN.update(r=0.09))
    ev("Life 30 yr / 20 yr", lambda: FIN.update(n=30), lambda: FIN.update(n=20))
    if site["offshore"]:
        ev("Offshore BOS $600 / $1,400 per kW", lambda: AWE_SITE["offshore"].update(bos_kW=600.0), lambda: AWE_SITE["offshore"].update(bos_kW=1400.0))
    return base, rows


def brief(r):
    return dict(lcoe=r["lcoe"], cf=r["cf"], capex_per_MW=r["capex_per_MW"], label=r["label"])


def main():
    t0 = time.time()
    out = dict(sites=SITES, finance=FIN, results=[])
    for sk in SITES:
        for arch, wing, name in CASES:
            r = optimise(SITES[sk], arch, wing)
            r.update(name=name, site=sk)
            out["results"].append(r)
            print(f"{sk:8s} {name[:52]:52s} LCOE ${r['lcoe']:5.1f}  CF {r['cf']:.2f}  $/MW {r['capex_per_MW']/1e6:.2f}M  $/avgMW {r['capex_per_avgMW']/1e6:.2f}M  | {r['label']}  [{time.time()-t0:.0f}s]", flush=True)
    # reference 5 MW turbine on each site for the ladder
    for sk in SITES:
        r = hawt(SITES[sk], [5.0, 126.0, 90.0 if sk == "onshore" else 100.0], detail=True)
        r.update(site=sk, arch="hawt_ref", wing=None, name="Conventional 5 MW turbine as built (126 m rotor, 90 m hub)", site_label=SITES[sk]["label"])
        out["results"].append(r)
        print(f"{sk:8s} reference 5 MW HAWT: LCOE ${r['lcoe']:.1f} CF {r['cf']:.2f}", flush=True)
    awe = [r for r in out["results"] if r["arch"] not in ("hawt", "hawt_ref")]
    for sk in SITES:
        best = min([r for r in awe if r["site"] == sk], key=lambda r: r["lcoe"])
        base, rows = sensitivities(best)
        out[f"sens_{sk}"] = dict(best=dict(name=best["name"], lcoe=base, label=best["label"]), rows=rows)
        print(sk, "sensitivities on", best["name"], flush=True)
        for row in rows:
            print(f"   {row['name']:44s} {row['lo']:5.1f} … {row['hi']:5.1f}")
    # ---- site sweep: best ring and best turbine, re-optimised for each onshore wind resource
    best = min([r for r in awe if r["site"] == "onshore"], key=lambda r: r["lcoe"])
    sweep = []
    for vm in (6.0, 7.5, 9.0, 10.5):
        s = dict(SITES["onshore"], vmean=vm, label=f"Onshore, {vm} m/s at 90 m")
        rr = optimise(s, best["arch"], best["wing"], maxiter=100); hh = optimise(s, "hawt", None, maxiter=100)
        sweep.append(dict(vmean=vm, ring=brief(rr), hawt=brief(hh)))
        print(f"site {vm} m/s: ring ${rr['lcoe']:.1f} ({rr['label']})  turbine ${hh['lcoe']:.1f} ({hh['label']})  [{time.time()-t0:.0f}s]", flush=True)
    out["site_sweep"] = sweep
    # ---- ladder: how low can it go (each step keeps the previous ones)
    site = SITES["onshore"]; fn = ARCH[best["arch"]]; w = best["wing"]
    ladder = [dict(name="Optimised design on the study site, base assumptions", **brief(best))]
    WINGS[w].update(cost=WINGS[w]["cost"] * 0.67, life=WINGS[w]["life"] * 1.6)
    DRIVE.update(onwing=400.0, tether_life=8.0); DYN["cost_kg"] = 40.0; AVAIL["awe"] = 0.97; AWE_SITE["onshore"]["bos_kW"] = 200.0
    r = fn(site, best["x"], w); ladder.append(dict(name="Stretch technology, same design: wings −33 % cost and +60 % life, on-wing drive $400/kW, tether −33 % and 8-yr life, 97 % availability, BOS $200/kW", **brief(r)))
    r = optimise(site, best["arch"], w, maxiter=100); ladder.append(dict(name="Stretch technology, design re-optimised", **brief(r)))
    FIN.update(n=30); r2 = fn(site, r["x"], w); ladder.append(dict(name="+ 30-year life for the ground hardware (wings and tether are replaced anyway)", **brief(r2)))
    FIN.update(r=0.05); r2 = fn(site, r["x"], w); ladder.append(dict(name="+ utility finance, 5 % WACC", **brief(r2)))
    s = dict(SITES["onshore"], vmean=10.5, label="Onshore, 10.5 m/s at 90 m")
    r3 = optimise(s, best["arch"], w, maxiter=100); ladder.append(dict(name="+ a 10.5 m/s site (Patagonia, Great Plains ridge, Horn of Africa class), re-optimised", **brief(r3)))
    snap_tech = snapshot()
    # the fairest comparison at the end of the ladder: the best turbine on the same 10.5 m/s site with the same finance
    h3 = optimise(s, "hawt", None, maxiter=100)
    out["ladder"] = ladder; out["ladder_hawt_end"] = brief(h3)
    for st_ in ladder: print(f"ladder  {st_['name'][:70]:70s} LCOE ${st_['lcoe']:.1f} CF {st_['cf']:.2f}  {st_['label']}")
    print(f"ladder  best turbine, same site and finance: ${h3['lcoe']:.1f}  {h3['label']}")
    restore(snap_tech)
    json.dump(out, open("out/lcoe_opt.json", "w"), indent=1, default=float)
    print(f"done in {time.time()-t0:.0f}s")


if __name__ == "__main__":
    main()
