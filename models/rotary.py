"""
Rotary kite ring (Daisy-type) and ground carousel (KiteGen-type) models.

Rotary ring
  * rotor: N semi-rigid kite wings on a ring of radius R, axis tilted up at beta.
    Blade-element / annulus-momentum (BEM) with Prandtl tip+root loss and Buhl's
    high-induction correction; optimise tip-speed ratio and C_L.
  * TRPT shaft: stacked CFRP rings joined by Dyneema lines.  Torque is carried by
    twisting the line cage under axial tension:
        Q = F_ax * r^2 * sin(delta) / l_ax          (Tulloch et al., Energies 2023)
    ring loads -> polygon compression -> in-plane buckling sizing (3EI/r^3).
  * nonlinear FEA: dynamic-relaxation cable/truss model of the whole shaft
    with gravity, axial pull and torque; torque ramp to find over-twist collapse.
  * size sweep 50 kW .. 5 MW -> capex/MW, LCOE.  Single-cell innovations sweep.

Carousel
  * N kites on tethers from carts on a circular rail; each kite steers inside its
    wind window; orbit-averaged power with depowered return arc.
"""
import json, math, os
os.environ.setdefault("OMP_NUM_THREADS", "1")
import numpy as np
import models as Mo

RHO = 1.225
G = 9.81
V_RATED_HUB = 11.4
HUB = 90.0


# ============================================================ rotor (BEM)
def prandtl(N, dr, r, phi):
    f = N / 2 * dr / (r * max(math.sin(phi), 1e-3))
    return 2 / math.pi * math.acos(min(1.0, math.exp(-f)))


def rotor_point(lam, CL, geo, beta):
    """Return Cp (on wind V, annulus area) and Ct for given tip-speed ratio and CL."""
    N, R, b, S, AR = geo["N"], geo["R"], geo["b"], geo["S"], geo["AR"]
    CD = geo["CD0"] + CL**2 / (math.pi * 0.85 * AR) + geo["CDt"]
    A = 2 * math.pi * R * b
    cb = math.cos(beta)
    lo, hi = 0.0, 0.95
    for _ in range(60):                      # bisection on axial induction a (per unit V_n, q_n = 1/2 rho V_n^2)
        a = 0.5 * (lo + hi)
        phi = math.atan2(1 - a, lam)
        W2 = (1 - a) ** 2 + lam**2
        Fn = N * 0.5 * W2 * S * (CL * math.cos(phi) + CD * math.sin(phi))   # normalised by rho V_n^2
        F = prandtl(N, b / 2, R, phi) ** 2
        F = max(F, 0.05)
        if a <= 0.4:
            ct = 4 * a * (1 - a) * F
        else:
            ct = 8 / 9 + (4 * F - 40 / 9) * a + (50 / 9 - 4 * F) * a**2
        Fm = 0.5 * ct * A
        if Fm < Fn:
            lo = a
        else:
            hi = a
    phi = math.atan2(1 - a, lam)
    W2 = (1 - a) ** 2 + lam**2
    Ft = N * 0.5 * W2 * S * (CL * math.sin(phi) - CD * math.cos(phi))
    Fn = N * 0.5 * W2 * S * (CL * math.cos(phi) + CD * math.sin(phi))
    P = Ft * lam                               # normalised by rho V_n^3
    cp_n = P / (0.5 * A)
    return dict(a=a, cp_on_Vn=cp_n, cp_on_V=cp_n * cb**3, ct_on_Vn=Fn / (0.5 * A), lam=lam, CL=CL, LD=CL / CD)


def best_rotor(geo, beta):
    best = None
    for lam in np.linspace(2, 14, 49):
        for CL in np.linspace(0.4, 1.3, 19):
            r = rotor_point(lam, CL, geo, beta)
            if best is None or r["cp_on_V"] > best["cp_on_V"]:
                best = r
    return best


def shear(V, z, alpha=0.14):
    return V * (z / HUB) ** alpha


# ============================================================ TRPT shaft sizing
CFRP = dict(E=100e9, rho=1550, sig=600e6, cost_kg=45.0)
# ring materials: CFRP tube; pultruded GFRP tube; 6061-T6 aluminium tube (fatigue-limited allowable)
MAT = dict(cfrp=dict(CFRP, name="CFRP"), gfrp=dict(E=40e9, rho=1900, sig=350e6, cost_kg=12.0, name="GFRP pultrusion"),
           al=dict(E=70e9, rho=2700, sig=130e6, cost_kg=8.0, name="aluminium"))
def ring_mat(opt):
    return MAT[opt.get("ring_mat", "cfrp")]
DYN = dict(sig=3.5e9, rho=975, cost_kg=60.0, E=110e9)


def design(P_rated, opt):
    """Size a rotary-ring machine for P_rated at the rated hub wind. opt: dict of design choices."""
    beta = math.radians(opt["beta_deg"])
    N, AR = opt["N"], opt["AR"]
    b_over_R = opt["b_over_R"]
    R = 20.0
    for _ in range(40):
        b = b_over_R * R
        c = b / AR
        geo = dict(N=N, R=R, b=b, S=b * c, AR=AR, CD0=opt["CD0"], CDt=opt["CDt"])
        rb = best_rotor(geo, beta)
        L_s = (R * math.cos(beta) + opt["clearance"]) / math.sin(beta)
        if opt.get("flygen") and opt.get("alt_m"):        # fly-gen: tether length is free, fly the rotor at alt_m
            L_s = max(L_s, opt["alt_m"] / math.sin(beta))
        h = L_s * math.sin(beta)
        vr = opt.get("v_rated", V_RATED_HUB)
        if opt.get("v_rated_rotor"):                      # rate at a fixed rotor-height wind (altitude levers)
            vr = opt["v_rated_rotor"] / (h / HUB) ** 0.14
        V = shear(vr, h)
        A = 2 * math.pi * R * b
        P = rb["cp_on_V"] * 0.5 * RHO * V**3 * A * opt["eta_drive"] * opt["stack"]
        R *= (P_rated / P) ** 0.5 ** 1
        if abs(P / P_rated - 1) < 1e-4:
            break
    Vn = V * math.cos(beta)
    Omega = rb["lam"] * Vn / R
    thrust = rb["ct_on_Vn"] * 0.5 * RHO * Vn**2 * A * opt["stack"]
    F_ax = thrust * (1 + opt["lifter_frac"])
    Q = opt["SF_torque"] * P_rated / opt["eta_drive"] / Omega
    Q_shaft = P_rated / opt["eta_drive"] / Omega          # rated shaft torque (no SF)
    # --- TRPT geometry: l_ax = k_l * r, design twist delta
    k_l, dl = opt["k_l"], math.radians(opt["delta_deg"])
    r = Q * k_l / (F_ax * math.sin(dl))                 # from Q = F r^2 sin d / (k_l r)
    r = max(r, 1.0)
    l_ax = k_l * r
    n_seg = max(2, math.ceil(L_s / l_ax))
    l_ax = L_s / n_seg
    # re-evaluate twist actually needed with rounded spacing: sin d = Q l / (F r^2)
    sd = min(Q * l_ax / (F_ax * r**2), 0.99)
    dl_act = math.asin(sd)
    n = opt["n_lines"]
    ch = 2 * r * math.sin(dl_act / 2)
    Lt = math.hypot(l_ax, ch)
    T_line = F_ax / n * Lt / l_ax * opt["SF_line_dyn"]
    A_line = T_line * 3.0 / DYN["sig"]                   # SF 3 on break (creep/fatigue)
    m_lines = A_line * DYN["rho"] * Lt * n * n_seg
    # ring: node inward load, polygon compression, buckling-sized CFRP tube (D/t = 25)
    P_node = 2 * T_line * (ch / Lt) * math.sin(dl_act / 2)
    C_ring = P_node / (2 * math.sin(math.pi / n))
    nsp = opt["ring_spokes"]
    T_pre = 1.5 * P_node if nsp else 0.0                 # spoke pretension must exceed the inward line pull at each node
    if nsp:
        C_ring = C_ring + T_pre * (n / nsp) / (2 * math.sin(math.pi / nsp)) * (nsp / n)   # pretension adds rim compression
    w = C_ring / r
    kbuck = 3.0 if nsp == 0 else max(3.0, 0.5 * (nsp**2 / 4 - 1))     # spoked ring: buckles between spokes (0.5 knock-down)
    EI = 3.0 * w * r**3 / kbuck                          # SF 3 on in-plane ring buckling
    M = ring_mat(opt)
    D = max((8 * 25 * EI / (M["E"] * math.pi)) ** 0.25, 0.06)
    t = D / 25
    A_r = math.pi * D * t
    if C_ring / A_r > M["sig"] / 2.5:                    # strength governs
        A_r = C_ring * 2.5 / M["sig"]; t = A_r / (math.pi * D)
    m_ring = A_r * 2 * math.pi * r * M["rho"] * 1.25  # +25% joints/fittings
    if nsp:                                              # Dyneema spokes + small hub per ring
        m_ring += nsp * r * T_pre * 3 / DYN["sig"] * DYN["rho"] / 0.75 + 15 + 0.002 * r * r
    m_rings = m_ring * (n_seg + 1) + m_ring * (opt["top_ring_stiff"] ** 0.5 - 1)   # stiff rotor-hub ring on top
    if opt.get("flygen"):                               # no TRPT: single conductive tether, generators on the wings
        m_rings = 0.0
        m_lines = F_ax * 3 / DYN["sig"] * DYN["rho"] * L_s / 1.3
    # rotor: kites (semi-rigid) + rotor ring/bridles (+30% of shaft line mass)
    S_tot = N * b * c * opt["stack"]
    m_kites = S_tot * opt["kite_kg_m2"]
    shaft_weight = (m_rings + m_lines * 1.3) * G
    # lifter: hold shaft + kites (x1.3) at the rotor's cut-in wind, net of the rotor's own vertical thrust there
    v_ci = shear(5.0, h + 60)
    q_ci = 0.5 * RHO * v_ci**2
    Fz_rotor = thrust * (5.0 / vr) ** 2 * math.sin(beta)
    need = max(0.0, 1.3 * (shaft_weight + m_kites * G) - Fz_rotor)
    S_lift = max(need / (q_ci * 1.2 * opt["lifter_dyn"]), 0.05 * S_tot)
    return dict(P_rated=P_rated, R=R, b=b, c=c, N=N, S_kite=b * c, S_tot=S_tot, beta_deg=opt["beta_deg"],
                L_s=L_s, h=h, V_rotor=V, Omega=Omega, rpm=Omega * 60 / (2 * math.pi), tip_speed=Omega * (R + b / 2),
                rotor=rb, thrust=thrust, F_ax=F_ax, Q_design=Q, Q_shaft=Q_shaft, r_shaft=r, l_ax=l_ax, n_seg=n_seg,
                delta_deg=math.degrees(dl_act), v_rated_hub=vr, T_line=T_line, line_dia_mm=math.sqrt(4 * A_line / math.pi / 0.75) * 1e3,
                m_lines=m_lines, ring_D=D, ring_t=t, ring_C=C_ring, T_pre=T_pre, P_node=P_node, m_rings=m_rings, m_kites=m_kites,
                S_lift=S_lift, n_lines=n, opt=opt)


def power_curve(d):
    """Rotor at fixed optimal Cp up to rated, depowered above; kites land below 3.5 m/s at rotor height / above 25."""
    opt = d["opt"]
    A = 2 * math.pi * d["R"] * d["b"] * opt["stack"]
    cp = d["rotor"]["cp_on_V"] * opt["eta_drive"]
    def P(v_hub):
        v = shear(v_hub, d["h"])
        if v < 3.5 or v_hub > 25:
            return 0.0
        return min(cp * 0.5 * RHO * v**3 * A, d["P_rated"])
    return P


def bom_rotary(d):
    o = d["opt"]
    P = d["P_rated"]
    M = ring_mat(o)
    # direct drive: PM generator cost scales with rated torque (~$150/kN·m for recent 5-6 MW, 11 rpm DD turbines,
    # i.e. ~$130/kW at 11 rpm), converter $80/kW, mainframe/brake $40/kW
    drive_dd = 150.0 * d["Q_shaft"] / 1e3 + 120.0 * P / 1e3
    items = [
        (f"{d['N']}{'×'+str(o['stack']) if o['stack']>1 else ''} semi-rigid kite wings, {d['S_tot']:,.0f} m² @ ${o['kite_cost_m2']}/m²", d["S_tot"] * o["kite_cost_m2"]),
        (f"TRPT {M['name']} rings{' (spoked)' if o['ring_spokes'] else ''}: {d['n_seg']+1} × Ø{2*d['r_shaft']:.1f} m (tube {d['ring_D']*1000:.0f} mm), {d['m_rings']/1e3:.1f} t @ ${M['cost_kg']}/kg", d["m_rings"] * M["cost_kg"]),
        (f"TRPT + rotor lines, Dyneema, {d['n_lines']}×{d['n_seg']} × Ø{d['line_dia_mm']:.0f} mm, {d['m_lines']*1.3/1e3:.2f} t @ $60/kg", d["m_lines"] * 1.3 * DYN["cost_kg"]),
        (f"Lift kite {d['S_lift']:,.0f} m² ({'crosswind' if o['lifter_dyn']>1 else 'static'}) + line", d["S_lift"] * 120 + 15_000),
        ((f"On-wing turbines + generators + HV converters ({P/1e3:,.0f} kW)", o["drive_cost_kW"] * P / 1e3) if o.get("flygen")
         else (f"Ground station: direct-drive PM ring generator at {d['rpm']:.1f} rpm ({d['Q_shaft']/1e6:.1f} MN·m) + converter", drive_dd) if o.get("direct_drive")
         else (f"Ground station: gearbox {d['rpm']:.1f} rpm → generator, converter ({P/1e3:,.0f} kW)", o["drive_cost_kW"] * P / 1e3)),
        *( [(f"Conductive tether {d['L_s']:.0f} m (Al conductors in Dyneema)", 140 * d["L_s"] * P / 1e6 + 20_000)] if o.get("flygen") else [] ),
        ("Yaw turntable + bearing, ground frame", 60_000 + 25 * P / 1e3),
        ("Launch/land mast, control & sensors", 80_000 + 30 * P / 1e3),
        ("Foundation / anchor (tension only)", 30_000 + 25 * P / 1e3),
        ("Balance of system (electrical, roads, install, soft costs)", o["bos_kW"] * P / 1e3),
    ]
    capex = sum(c for _, c in items)
    opex = (d["S_tot"] * o["kite_cost_m2"] / o["kite_life_yr"]
            + d["m_lines"] * 1.3 * DYN["cost_kg"] / o["line_life_yr"]
            + 0.02 * capex + o["om_fixed"])
    return items, capex, opex


def evaluate(d):
    items, capex, opex = bom_rotary(d)
    Pc = power_curve(d)
    aep = Mo.aep(Pc) * d["opt"]["availability"]
    cf = aep / (d["P_rated"] / 1e3 * 8766)
    lcoe = (capex * Mo.crf() + opex) / aep * 1000
    return dict(items=items, capex=capex, opex=opex, aep_kwh=aep, cf=cf,
                capex_per_MW=capex / (d["P_rated"] / 1e6), capex_per_avgMW=capex / (d["P_rated"] / 1e6 * cf), lcoe=lcoe)


BASE = dict(N=8, AR=7, b_over_R=0.30, CD0=0.035, CDt=0.045, beta_deg=30, clearance=25, eta_drive=0.90,
            lifter_frac=0.15, SF_torque=1.6, k_l=1.6, delta_deg=32, n_lines=12, SF_line_dyn=1.4,
            kite_kg_m2=1.6, kite_cost_m2=250, stack=1, drive_cost_kW=380, bos_kW=300, kite_life_yr=3,
            line_life_yr=2, om_fixed=20_000, availability=0.93, ring_spokes=0, lifter_dyn=1.0, top_ring_stiff=8.0)


# ============================================================ nonlinear TRPT FEA (dynamic relaxation)
def trpt_fea(d, Q_apply, gravity=True, max_it=60000):
    """Cable + truss model: rings = polygon bars + skip-1 chords (bending proxy); lines = tension-only cables.
    Shaft axis inclined at beta. Bottom ring fixed. Top ring: axial pull F_ax along axis + torque Q_apply."""
    n, ns, r = d["n_lines"], d["n_seg"], d["r_shaft"]
    # rest length of lines = their design (twisted) length, so the design twist reproduces the design ring spacing
    l = math.hypot(d["l_ax"], 2 * r * math.sin(math.radians(d["delta_deg"]) / 2))
    beta = math.radians(d["beta_deg"])
    ex = np.array([math.cos(beta), 0, math.sin(beta)])           # shaft axis (downwind & up)
    ey = np.array([0, 1.0, 0]); ez = np.cross(ex, ey)
    X = []
    for k in range(ns + 1):
        for j in range(n):
            th = 2 * math.pi * j / n
            X.append(k * l * ex + r * (math.cos(th) * ey + math.sin(th) * ez))
    X = np.array(X)
    bars, kinds = [], []
    A_ring = math.pi * d["ring_D"] * d["ring_t"]
    M = ring_mat(d["opt"])
    EA_ring = M["E"] * A_ring
    A_line = (d["line_dia_mm"] / 1e3) ** 2 * math.pi / 4 * 0.75
    EA_line = DYN["E"] * A_line
    for k in range(ns + 1):
        for j in range(n):
            bars.append((k * n + j, k * n + (j + 1) % n)); kinds.append(0)
            bars.append((k * n + j, k * n + (j + 2) % n)); kinds.append(0)
    for k in range(ns):
        for j in range(n):
            bars.append((k * n + j, (k + 1) * n + j)); kinds.append(1)      # lines connect same index (untwisted at rest)
    nsp_fea = 0
    if d["opt"].get("ring_spokes", 0):                                  # bicycle-wheel rings: hub node + pretensioned spokes
        hubs0 = len(X)
        X = np.vstack([X, np.array([k * l * ex for k in range(ns + 1)])])
        for k in range(ns + 1):
            for j in range(n):
                bars.append((hubs0 + k, k * n + j)); kinds.append(2)
        nsp_fea = 1
    bars = np.array(bars); kinds = np.array(kinds)
    L0 = np.linalg.norm(X[bars[:, 1]] - X[bars[:, 0]], axis=1)
    eps_pre = (d.get("T_pre", 0.0) * d["opt"].get("ring_spokes", n) / n) / (DYN["E"] * max(d.get("T_pre", 0.0) * d["opt"].get("ring_spokes", n) / n * 3 / DYN["sig"], 4e-5)) if d.get("T_pre") else 0.0
    L0 = np.where(kinds == 2, L0 * (1 - eps_pre), L0)                     # spoke pretension via short rest length
    # lines get a small pre-stretch reference so they start taut
    T_pre = d.get("T_pre", 0.0) * d["opt"].get("ring_spokes", n) / n if d.get("T_pre") else 0.0
    A_sp = max(T_pre * 3 / DYN["sig"], 4e-5)
    EA = np.where(kinds == 0, EA_ring, np.where(kinds == 2, DYN["E"] * A_sp, EA_line))
    # skip-one chords stand in for ring bending: EA_chord * h^2 = E*I of the tube (h = chord offset from the rim)
    I_ring = math.pi / 8 * d["ring_D"] ** 3 * d["ring_t"]
    h_off = r * (math.cos(math.pi / n) - math.cos(2 * math.pi / n))
    chord = np.array([kinds[i] == 0 and abs(bars[i, 1] - bars[i, 0]) not in (1, n - 1) for i in range(len(bars))])
    EA = np.where(chord, M["E"] * I_ring / h_off**2, EA)
    top_bar = np.array([bars[i, 0] >= ns * n and bars[i, 0] < (ns + 1) * n and kinds[i] == 0 for i in range(len(bars))])
    EA = np.where(top_bar, EA * d["opt"].get("top_ring_stiff", 1.0), EA)     # rotor-hub ring at the top
    fixed = np.zeros(len(X), bool); fixed[:n] = True
    if nsp_fea:
        fixed[hubs0] = True
    top = np.arange(ns * n, (ns + 1) * n)
    m_bar = np.where(chord, 0.0, 1.0) * np.where(kinds == 0, A_ring * M["rho"] * 1.25, np.where(kinds == 2, A_sp * DYN["rho"], A_line * DYN["rho"] * 1.3)) * L0
    mass = np.zeros(len(X)); np.add.at(mass, bars[:, 0], m_bar / 2); np.add.at(mass, bars[:, 1], m_bar / 2)
    Fext = np.zeros_like(X)
    if gravity:
        Fext[:, 2] -= mass * G
    Fext[top] += d["F_ax"] / n * ex
    def apply_torque(x, Q):
        c = x[top].mean(0)
        rel = x[top] - c
        rel -= np.outer(rel @ ex, ex)
        tang = np.cross(ex, rel)
        rr = np.linalg.norm(rel, axis=1)[:, None]
        return Q / n * tang / (rr**2)
    # fictitious masses for DR
    kdiag = np.zeros(len(X)); np.add.at(kdiag, bars[:, 0], EA / L0); np.add.at(kdiag, bars[:, 1], EA / L0)
    mf = kdiag * 1.2 + 1.0
    x = X.copy(); v = np.zeros_like(x); KEp = 0
    ramp = 8000
    for it in range(max_it):
        Q = Q_apply * min(1.0, (it + 1) / ramp)
        dx = x[bars[:, 1]] - x[bars[:, 0]]
        L = np.linalg.norm(dx, axis=1)
        Tn = EA * (L - L0) / L0
        Tn = np.where((kinds >= 1) & (Tn < 0), 0.0, Tn)               # lines + spokes: tension only
        f = np.zeros_like(x)
        fb = (Tn / L)[:, None] * dx
        np.add.at(f, bars[:, 0], fb); np.add.at(f, bars[:, 1], -fb)
        f += Fext + 0
        f[top] += apply_torque(x, Q)
        f[fixed] = 0
        v += f / mf[:, None]
        KE = (mf[:, None] * v**2).sum()
        if KE < KEp:
            v[:] = 0; KE = 0
        KEp = KE
        x += v
        res = np.linalg.norm(f) / (d["F_ax"] + 1)
        if it > ramp + 200 and res < 1e-5:
            break
        if not np.isfinite(res) or np.abs(x).max() > 1e5:
            return dict(converged=False, collapsed=True, Q=Q_apply)
    edge_mask = np.array([kinds[i] == 0 and (abs(bars[i, 1] - bars[i, 0]) in (1, n - 1)) for i in range(len(bars))])
    # twist per segment (angle of node 0 around axis relative to ring below)
    twist = []
    for k in range(ns + 1):
        ring = x[k * n:(k + 1) * n]; c = ring.mean(0)  # noqa
        p = ring[0] - c; p -= (p @ ex) * ex
        twist.append(math.atan2(p @ ez, p @ ey))
    twist = np.unwrap(np.array(twist))
    seg_twist = np.degrees(np.diff(twist))
    axial_len = (x[top].mean(0) - x[:n].mean(0)) @ ex
    # collapse: rings touch (axial gap < 15% of radius) or no equilibrium
    gaps = np.diff([(x[k * n:(k + 1) * n].mean(0)) @ ex for k in range(ns + 1)])
    collapsed = bool(gaps.min() < 0.15 * r or res > 1e-2)
    return dict(converged=bool(res < 1e-3), collapsed=bool(collapsed), Q=Q_apply, res=float(res), iters=it,
                seg_twist_deg=seg_twist.tolist(), total_twist_deg=float(np.degrees(twist[-1])),
                max_line_T=float(Tn[kinds == 1].max()), min_line_T=float(Tn[kinds == 1].min()),
                max_ring_C=float(-Tn[(kinds == 0) & edge_mask].min()), max_chord_C=float(-Tn[(kinds == 0) & ~edge_mask].min()),
                max_spoke_T=float(Tn[kinds == 2].max()) if (kinds == 2).any() else 0.0, shortening=float(ns * l - axial_len), min_gap_m=float(gaps.min()),
                x=x, bars=bars, kinds=kinds)


# ============================================================ ground carousel
def carousel(Rc=450.0, n_kites=24, S=320.0, LD=5.5, CL=1.0, beta_deg=25.0, window_deg=60.0, V=None):
    """Orbit-averaged power of a ground carousel. Each kite flies crosswind; its tether can point anywhere
    within +-window of downwind.  Cart tangential speed vc is common to all carts (coupled ring)."""
    beta = math.radians(beta_deg)
    V = V or shear(V_RATED_HUB, 300)
    q = 0.5 * RHO * V**2
    best = None
    psis = np.radians(np.arange(0, 360, 3))
    for vc in np.linspace(0.5, V * 0.8, 40):
        Ps = []
        for psi in psis:          # cart heading measured from downwind
            pbest = -1e18
            for th in np.radians(np.linspace(-window_deg, window_deg, 25)):
                vr = vc * math.cos(psi - th)                 # cart speed along tether direction (reel-out analogue)
                Veff = V * math.cos(th) * math.cos(beta)
                if vr >= 0:
                    T = q * S * CL * (LD**2) * max(0.0, (1 - vr / Veff)) ** 2 * math.cos(th) ** 2 * math.cos(beta) ** 2 * (4 / 9) * (9 / 4)
                    p = T * vr
                else:                                       # tether opposes motion: depowered kite (CL 0.15, no crosswind)
                    T = q * S * 0.15 * (math.cos(th) + abs(vr) / V) ** 2
                    p = -T * abs(vr)
                pbest = max(pbest, p)
            Ps.append(pbest)
        Pm = float(np.mean(Ps)) * n_kites * 0.9          # 0.9 drivetrain
        if best is None or Pm > best["P"]:
            best = dict(P=Pm, vc=vc, P_psi=(np.array(Ps) * 0.9).tolist(), psi=np.degrees(psis).tolist())
    peak_T = q * S * CL * LD**2 * math.cos(beta) ** 2 * (1 - best["vc"] / (V * math.cos(beta))) ** 2
    best.update(V=V, Rc=Rc, n_kites=n_kites, S=S, LD=LD, peak_tether_T=peak_T)
    return best


def bom_carousel(c):
    P = c["P"]
    circ = 2 * math.pi * c["Rc"]
    items = [
        (f"Circular rail track Ø{2*c['Rc']:,.0f} m ({circ/1e3:.2f} km), lateral-load foundation @ $9k/m", circ * 9000),
        (f"{c['n_kites']} carts with on-board generators + power pickup", c["n_kites"] * 260_000),
        (f"{c['n_kites']} soft kites, {c['S']:.0f} m² each @ $140/m²", c["n_kites"] * c["S"] * 140),
        (f"{c['n_kites']} tethers, ~{c['peak_tether_T']/1e6:.2f} MN, 700 m Dyneema", c["n_kites"] * c["peak_tether_T"] * 3 / 3.5e9 * 975 * 700 * 60),
        ("Collector busbar, converter station", 180 * P / 1e3),
        ("Launch/land systems (per cart)", c["n_kites"] * 60_000),
        ("Balance of system", 300 * P / 1e3),
    ]
    capex = sum(v for _, v in items)
    opex = c["n_kites"] * c["S"] * 140 / 2 + 0.03 * capex
    return items, capex, opex


# ============================================================ main
def main():
    out = {}
    # ---- base design, size sweep
    sizes = [50e3, 100e3, 250e3, 500e3, 1e6, 2e6, 5e6, 7.5e6, 10e6]
    sweep = []
    for P in sizes:
        d = design(P, BASE); e = evaluate(d)
        sweep.append(dict(P=P, R=d["R"], L_s=d["L_s"], r_shaft=d["r_shaft"], m_rings=d["m_rings"], rpm=d["rpm"],
                          Q=d["Q_design"], cf=e["cf"], capex_per_MW=e["capex_per_MW"], capex_per_avgMW=e["capex_per_avgMW"], lcoe=e["lcoe"],
                          ring_share=d["m_rings"] * ring_mat(BASE)["cost_kg"] / e["capex"]))
        print(f"P={P/1e3:6.0f} kW R={d['R']:5.1f} Ls={d['L_s']:5.0f} r={d['r_shaft']:5.2f} rings={d['m_rings']/1e3:7.2f} t "
              f"rpm={d['rpm']:5.1f} cf={e['cf']:.2f} $/MW={e['capex_per_MW']/1e6:5.2f}M  $/avgMW={e['capex_per_avgMW']/1e6:5.2f}M LCOE={e['lcoe']:5.0f}", flush=True)
    out["sweep_base"] = sweep

    # ---- innovations: each a design lever, applied cumulatively at 1 MW and as a 5x1 MW farm cell
    levers = [
        ("Baseline Daisy-type ring (8 kites, 30° shaft)", {}),
        ("Spoked 'bicycle-wheel' TRPT rings (24 Dyneema spokes each)", dict(ring_spokes=24)),
        ("Crosswind (figure-8) lift kite: ~4× lift per m²", dict(lifter_dyn=4.0)),
        ("Lower shaft angle 30° → 22° (cos³β gain)", dict(beta_deg=22, clearance=25)),
        ("Higher-L/D wings: rigid-LE semi-rigid, cleaner rotor lines", dict(CD0=0.025, CDt=0.03)),
        ("Wider TRPT twist window 32° → 45°", dict(delta_deg=45)),
        ("Wider kite annulus b/R 0.30 → 0.40, 10 wings", dict(b_over_R=0.40, N=10)),
        ("Stacked rotors: 2 kite rings on one shaft", dict(stack=2)),
        ("Mass-produced wings $250 → $150/m², 5-yr life", dict(kite_cost_m2=150, kite_life_yr=5)),
        ("Rigid high-L/D wings (L/D≈14), $400/m², 10-yr life", dict(CD0=0.014, CDt=0.02, kite_cost_m2=400, kite_life_yr=10, kite_kg_m2=4.0)),
        ("18 lines per bay instead of 12", dict(n_lines=18)),
        ("Shared BOS / O&M in a wind-farm layout", dict(bos_kW=200, om_fixed=8_000)),
        ("Pultruded GFRP rings $12/kg instead of CFRP $45/kg (E 40 GPa, re-sized for buckling)", dict(ring_mat="gfrp")),
        ("Aluminium rings $8/kg (fatigue-limited allowable, E 70 GPa)", dict(ring_mat="al")),
        ("Lower specific power: rate the rotor at 10 m/s hub wind instead of 11.4 (higher CF)", dict(v_rated=10.0)),
        ("Direct-drive PM ring generator, no gearbox (cost ∝ torque, +3% efficiency)", dict(direct_drive=True, eta_drive=0.93, om_fixed=5_000)),
        ("Fly-gen: drop the TRPT, generate on the wings, conductive tether", dict(flygen=True, drive_cost_kW=620, eta_drive=0.78, line_life_yr=4)),
        ("Taller shaft: +60 m clearance to reach stronger wind", dict(clearance=85)),
        ("Shallower 18° shaft with the taller clearance", dict(beta_deg=18)),
        ("Fly-gen rotor at 500 m altitude, same rotor-height rated wind (CF gain; shear 0.14, long conductive tether)", dict(alt_m=500)),
        ("Fly-gen rotor at 800 m altitude", dict(alt_m=800)),
    ]
    opt = dict(BASE); lev_res = []; prev = None; h_prev = 0.0
    OPT_TRPT_box = [dict(BASE)]; LAST_P_box = [1e6]
    for name, ch in levers:
        trial = dict(opt); trial.update(ch)
        if "alt_m" in ch:                                 # keep the rotor-height rated wind of the previous kept design
            trial["v_rated_rotor"] = shear(trial.get("v_rated", V_RATED_HUB), h_prev)
        rows = []
        for P in sizes:
            d = design(P, trial); e = evaluate(d)
            rows.append((P, e["capex_per_MW"], e["capex_per_avgMW"], e["lcoe"], d, e))
        bestrow = min(rows, key=lambda r: r[3])
        P, cpm, cpa, lc, d, e = bestrow
        kept = prev is None or lc < prev
        reason = "" if kept else "higher LCOE"
        if kept and not trial.get("flygen"):              # every adopted lever must also pass the nonlinear TRPT FEA
            fchk = trpt_fea(d, d["Q_design"], max_it=60000)
            if fchk["collapsed"] or not fchk["converged"]:
                kept = False; reason = "TRPT over-twists in FEA" if fchk["collapsed"] else "TRPT FEA does not converge (marginal)"
        if kept:
            opt = trial; prev = lc; h_prev = d["h"]
            if not trial.get("flygen"):
                OPT_TRPT_box[0] = dict(trial); LAST_P_box[0] = P
        lev_res.append(dict(name=name, kept=kept, reason=reason, best_P=P, flygen=bool(trial.get("flygen")), h=d["h"], capex_per_MW=cpm, capex_per_avgMW=cpa, lcoe=lc, cf=e["cf"],
                            cp=float(d["rotor"]["cp_on_V"]), LD=float(d["rotor"]["LD"]),
                            sweep=[dict(P=r[0], capex_per_MW=r[1], capex_per_avgMW=r[2], lcoe=r[3]) for r in rows]))
        print(f"{'KEEP' if kept else 'DROP ('+reason+')'} {name:62s} best@{P/1e3:5.0f} kW  $/MW={cpm/1e6:.2f}M  $/avgMW={cpa/1e6:.2f}M  LCOE={lc:.0f}  Cp={d['rotor']['cp_on_V']:.3f} L/D={d['rotor']['LD']:.1f}", flush=True)
    out["levers"] = lev_res
    OPT_FINAL = dict(opt)
    OPT_TRPT = OPT_TRPT_box[0]; LAST_TRPT_P = LAST_P_box[0]
    out["trpt_best"] = dict(P=LAST_TRPT_P)

    # ---- chosen design for FEA + 3D: best size with all levers
    out["flygen_kept"] = bool(OPT_FINAL.get("flygen"))
    trpt_opt = dict(OPT_TRPT)
    Pbest = LAST_TRPT_P
    dsel = design(Pbest, trpt_opt); esel = evaluate(dsel)
    out["design"] = {k: (v if not isinstance(v, dict) else v) for k, v in dsel.items() if k != "opt"}
    out["design"]["opt"] = trpt_opt
    out["design_eval"] = esel
    # a 5 MW version (20 x 250 kW or single) for the like-for-like 5 MW comparison
    out["farm_5MW_units"] = int(round(5e6 / Pbest))

    # ---- nonlinear FEA on selected design
    fea = trpt_fea(dsel, dsel["Q_design"])
    print("FEA design torque:", {k: v for k, v in fea.items() if k not in ("x", "bars", "kinds", "seg_twist_deg")}, flush=True)
    # torque ramp to collapse
    ramp = []
    for mult in (1.0, 1.25, 1.5, 1.75, 2.0, 2.5, 3.0):
        r = trpt_fea(dsel, dsel["Q_design"] * mult, max_it=40000)
        ramp.append(dict(mult=mult, collapsed=r["collapsed"], twist=r.get("total_twist_deg"), max_seg=max(r["seg_twist_deg"]) if "seg_twist_deg" in r else None))
        print(" ramp", ramp[-1], flush=True)
        if r["collapsed"]:
            break
    out["fea"] = {k: v for k, v in fea.items() if k not in ("x", "bars", "kinds")}
    nsp = OPT_FINAL["ring_spokes"]; kb = 3.0 if nsp == 0 else max(3.0, 0.5 * (nsp**2 / 4 - 1))
    I_r = math.pi / 8 * dsel["ring_D"]**3 * dsel["ring_t"]
    C_cr = kb * ring_mat(trpt_opt)["E"] * I_r / dsel["r_shaft"]**2
    out["fea"]["ring_buckling_SF"] = C_cr / max(fea["max_ring_C"], 1.0)
    out["fea"]["ring_C_design"] = dsel["ring_C"]
    out["fea"]["ring_C_cr"] = C_cr
    print("ring buckling SF vs FEA compression:", C_cr / max(fea["max_ring_C"], 1.0), flush=True)
    out["fea_ramp"] = ramp
    out["fea_geom"] = dict(x=np.round(fea["x"], 3).tolist(), bars=fea["bars"].tolist(), kinds=fea["kinds"].tolist())
    # analytic check: torque from FEA twist
    sd = math.sin(math.radians(np.mean(fea["seg_twist_deg"])))
    out["fea_check"] = dict(Q_design=dsel["Q_design"], analytic_delta=dsel["delta_deg"], fea_mean_delta=float(np.mean(fea["seg_twist_deg"])))

    # ---- carousel
    c = carousel()
    items, capex, opex = bom_carousel(c)
    # carousel AEP: scale orbit power with V^3 up to rated cap
    Pr = c["P"]
    def Pc(v_hub):
        v = shear(v_hub, 300)
        if v < 4 or v_hub > 25:
            return 0.0
        return min(Pr * (v / c["V"]) ** 3, Pr)
    aep = Mo.aep(Pc) * 0.9
    cf = aep / (Pr / 1e3 * 8766)
    out["carousel"] = dict(c, items=items, capex=capex, opex=opex, aep_kwh=aep, cf=cf, capex_per_MW=capex / (Pr / 1e6),
                           capex_per_avgMW=capex / (Pr / 1e6 * cf), lcoe=(capex * Mo.crf() + opex) / aep * 1000)
    print(f"carousel P={Pr/1e6:.1f} MW vc={c['vc']:.1f} capex={capex/1e6:.1f}M $/MW={capex/(Pr/1e6)/1e6:.2f}M cf={cf:.2f} LCOE={out['carousel']['lcoe']:.0f}", flush=True)

    json.dump(out, open("out/rotary.json", "w"), indent=1, default=float)


if __name__ == "__main__":
    main()
